"""diagnosticar_apns.py — confere a credencial do APNs ponta a ponta, sem expor segredo.

Chamado por scripts/diagnosticar-apns.sh (que lê as variáveis do Railway e as
entrega por stdin, em JSON). Também roda sozinho com as variáveis no ambiente:

    server/.venv/bin/python scripts/diagnosticar_apns.py --from-env

O que confere, em ordem:
  1. presença de APNS_TEAM_ID, APNS_KEY_ID, APNS_AUTH_KEY, APNS_TOPIC (e o valor de APNS_SANDBOX);
  2. formato e valor esperado de Team ID, Key ID e topic;
  3. APNS_AUTH_KEY: PEM legível como chave EC P-256 (e detecta "\\n" literal colado);
  4. impressão digital da chave PÚBLICA derivada (SHA-256 da SPKI) — identifica a
     chave sem revelar nada;
  5. se APNS_AUTH_KEY é na verdade a chave do Sign in with Apple (SIWA_PRIVATE_KEY);
  6. arquivos AuthKey_*.p8 locais (Downloads, Desktop, Documents, iCloud Drive):
     qual Key ID corresponde à chave configurada;
  7. PROVA na Apple: assina o JWT como o servidor (push._jwt) e faz um POST para um
     token de aparelho FALSO (64 zeros) nos hosts de produção e sandbox. A Apple
     valida o JWT antes do token do aparelho:
        400 BadDeviceToken          → credencial OK (nenhum push é entregue)
        403 InvalidProviderToken    → Team ID / Key ID / .p8 não batem entre si
        403 BadEnvironmentKeyInToken→ a chave é restrita ao outro ambiente
        400 TopicDisallowed / DeviceTokenNotForTopic → APNS_TOPIC errado

NUNCA imprime a chave privada nem parte dela. Saída 0 = tudo certo; 1 = há falha.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys
import time

TEAM_ESPERADO = "LC65399YC9"
TOPIC_ESPERADO = "com.alexandrecamerini.bolsia"
TOKEN_FALSO = "0" * 64
HOSTS = {
    "produção": "https://api.push.apple.com",
    "sandbox": "https://api.sandbox.push.apple.com",
}

VERDE, VERMELHO, AMARELO, NEGRITO, FIM = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"
FALHAS: list[str] = []


def ok(msg: str) -> None:
    print(f"  {VERDE}[OK]{FIM} {msg}")


def falha(msg: str) -> None:
    FALHAS.append(msg)
    print(f"  {VERMELHO}[X]{FIM} {msg}")


def aviso(msg: str) -> None:
    print(f"  {AMARELO}[!]{FIM} {msg}")


def secao(msg: str) -> None:
    print(f"\n{NEGRITO}== {msg} =={FIM}")


def normalizar_pem(raw: str) -> tuple[str, bool]:
    """Devolve (pem, tinha_barra_n_literal). Railway às vezes recebe o PEM com
    '\\n' literal no lugar de quebra de linha; a lib de cripto recusa ou o servidor
    assina com outra coisa."""
    literal = "\\n" in raw and "\n" not in raw.strip()
    pem = raw.replace("\\n", "\n") if literal else raw
    return pem.strip() + "\n", literal


def carregar_chave(pem: str):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    chave = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(chave, ec.EllipticCurvePrivateKey):
        raise ValueError(f"não é chave EC (tipo {type(chave).__name__})")
    if chave.curve.name != "secp256r1":
        raise ValueError(f"curva {chave.curve.name}, o APNs exige P-256 (secp256r1)")
    return chave


def impressao(chave) -> str:
    from cryptography.hazmat.primitives import serialization

    spki = chave.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return hashlib.sha256(spki).hexdigest()[:16]


def p8_locais() -> dict[str, str]:
    """Key ID (do nome AuthKey_XXXXXXXXXX.p8) → impressão da chave pública."""
    home = os.path.expanduser("~")
    raizes = [
        os.path.join(home, "Downloads"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Library", "Mobile Documents", "com~apple~CloudDocs"),
    ]
    achados: dict[str, str] = {}
    # Só a raiz e 2 níveis abaixo: glob recursivo em Documents/iCloud Drive
    # varre milhares de arquivos e pode travar esperando download do iCloud.
    padroes = ("AuthKey_*.p8", "*/AuthKey_*.p8", "*/*/AuthKey_*.p8")
    candidatos = [c for raiz in raizes for p in padroes for c in glob.glob(os.path.join(raiz, p))]
    for caminho in candidatos:
            m = re.search(r"AuthKey_([A-Z0-9]{10})\.p8$", caminho)
            if not m:
                continue
            try:
                with open(caminho, encoding="utf-8") as f:
                    achados[m.group(1)] = impressao(carregar_chave(f.read()))
            except Exception:
                achados.setdefault(m.group(1), "ilegível")
    return achados


def sondar_apple(team: str, kid: str, pem: str, topic: str) -> dict[str, tuple[int, str]]:
    import httpx
    import jwt

    token = jwt.encode({"iss": team, "iat": int(time.time())}, pem, algorithm="ES256", headers={"kid": kid})
    headers = {
        "authorization": f"bearer {token}",
        "apns-topic": topic,
        "apns-push-type": "alert",
        "apns-priority": "5",
    }
    corpo = {"aps": {"alert": {"title": "diagnóstico", "body": "não entregue"}}}
    resultado: dict[str, tuple[int, str]] = {}
    for nome, host in HOSTS.items():
        try:  # cliente dentro do try: falha de TLS/certificado/rede vira diagnóstico, não traceback
            with httpx.Client(http2=True, timeout=15) as cli:
                r = cli.post(f"{host}/3/device/{TOKEN_FALSO}", headers=headers, json=corpo)
            try:
                motivo = (r.json() or {}).get("reason", "")
            except Exception:
                motivo = r.text[:80]
            resultado[nome] = (r.status_code, motivo)
        except Exception as e:  # rede bloqueada, DNS, TLS
            resultado[nome] = (0, f"{type(e).__name__}: {e}"[:120])
    return resultado


def interpretar(ambiente: str, status: int, motivo: str) -> tuple[bool, str]:
    if status == 400 and motivo == "BadDeviceToken":
        return True, "credencial ACEITA pela Apple (o 400 é do token de aparelho falso, esperado)"
    if motivo == "InvalidProviderToken":
        return False, "Apple RECUSOU o JWT: Team ID, Key ID e .p8 não pertencem à mesma chave (ou a chave foi revogada / não tem APNs)"
    if motivo == "BadEnvironmentKeyInToken":
        return False, f"a chave é RESTRITA ao outro ambiente — não vale para {ambiente}"
    if motivo in ("TopicDisallowed", "DeviceTokenNotForTopic", "BadTopic", "MissingTopic"):
        return False, f"APNS_TOPIC recusado ({motivo})"
    if motivo == "ExpiredProviderToken":
        return False, "JWT expirado — relógio desta máquina fora de hora?"
    if status == 0:
        return False, f"sem resposta da Apple ({motivo})"
    return False, f"resposta inesperada {status} {motivo}"


def main() -> int:
    if "--from-env" in sys.argv:
        vars_ = dict(os.environ)
    else:
        bruto = sys.stdin.read()
        try:
            vars_ = json.loads(bruto)
        except json.JSONDecodeError:
            print("entrada não é JSON (esperado: saída de `railway variables --json`)")
            return 1

    secao("1/5 · Variáveis presentes")
    team = (vars_.get("APNS_TEAM_ID") or "").strip()
    kid = (vars_.get("APNS_KEY_ID") or "").strip()
    topic = (vars_.get("APNS_TOPIC") or "").strip()
    raw = vars_.get("APNS_AUTH_KEY") or ""
    sandbox = (vars_.get("APNS_SANDBOX") or "").strip()
    for nome, valor in (("APNS_TEAM_ID", team), ("APNS_KEY_ID", kid), ("APNS_TOPIC", topic), ("APNS_AUTH_KEY", raw)):
        (ok if valor else falha)(f"{nome} {'presente' if valor else 'AUSENTE'}")
    ambiente_servidor = "sandbox" if sandbox == "1" else "produção"
    print(f"  servidor fala com: {ambiente_servidor} (APNS_SANDBOX={'1' if sandbox == '1' else 'ausente'}) — TestFlight/App Store exigem produção")
    if sandbox == "1":
        falha("APNS_SANDBOX=1: build do TestFlight gera token de PRODUÇÃO; remova a variável")

    secao("2/5 · Formato e valores esperados")
    if team:
        if team == TEAM_ESPERADO:
            ok(f"APNS_TEAM_ID = {team}")
        else:
            falha(f"APNS_TEAM_ID = {team}, esperado {TEAM_ESPERADO} (Membership da conta)")
    if kid:
        if re.fullmatch(r"[A-Z0-9]{10}", kid):
            ok(f"APNS_KEY_ID = {kid} (formato ok)")
        else:
            falha(f"APNS_KEY_ID = {kid!r} fora do formato (10 caracteres A-Z/0-9; espaço ou aspas coladas?)")
    if topic:
        (ok if topic == TOPIC_ESPERADO else falha)(f"APNS_TOPIC = {topic}" + ("" if topic == TOPIC_ESPERADO else f", esperado {TOPIC_ESPERADO}"))

    secao("3/5 · A chave .p8 (APNS_AUTH_KEY)")
    chave = None
    pem = ""
    if raw:
        if not raw.strip().startswith("-----BEGIN"):
            falha("APNS_AUTH_KEY não começa com -----BEGIN (é um caminho de arquivo? no Railway precisa ser o PEM inteiro)")
        pem, literal = normalizar_pem(raw)
        if literal:
            falha("APNS_AUTH_KEY tem '\\n' LITERAL no lugar de quebras de linha — o servidor lê assim; recole o PEM")
        try:
            chave = carregar_chave(pem)
            ok("PEM legível: chave EC P-256")
        except Exception as e:
            falha(f"PEM ilegível: {e}")
    fp = impressao(chave) if chave else ""
    if fp:
        print(f"  impressão da chave pública configurada: {fp}")

    secao("4/5 · De qual chave é este .p8?")
    if chave:
        siwa_raw = vars_.get("SIWA_PRIVATE_KEY") or ""
        if siwa_raw:
            try:
                fp_siwa = impressao(carregar_chave(normalizar_pem(siwa_raw)[0]))
                if fp_siwa == fp:
                    falha(f"APNS_AUTH_KEY é a MESMA chave do Sign in with Apple (SIWA_KEY_ID={vars_.get('SIWA_KEY_ID', '?')}) — "
                          "a chave do SIWA não tem APNs")
                else:
                    ok("APNS_AUTH_KEY não é a chave do SIWA")
            except Exception:
                aviso("SIWA_PRIVATE_KEY presente mas ilegível — comparação pulada")
        locais = p8_locais()
        if not locais:
            aviso("nenhum AuthKey_*.p8 em Downloads/Desktop/Documents/iCloud Drive — não dá para cruzar com arquivos")
        else:
            casou = [k for k, v in locais.items() if v == fp]
            print(f"  arquivos .p8 locais: {', '.join(sorted(locais))}")
            if casou:
                dono = casou[0]
                if dono == kid:
                    ok(f"o .p8 configurado é o AuthKey_{dono}.p8 — bate com APNS_KEY_ID")
                else:
                    falha(f"o .p8 configurado é o AuthKey_{dono}.p8, mas APNS_KEY_ID = {kid} → troque APNS_KEY_ID para {dono} "
                          f"(se essa chave tiver APNs) ou cole o AuthKey_{kid}.p8")
            elif kid in locais:
                falha(f"existe AuthKey_{kid}.p8 local, mas NÃO é o conteúdo de APNS_AUTH_KEY → recole com scripts/configurar-apns.sh")
            else:
                aviso("o .p8 configurado não corresponde a nenhum arquivo local")

    secao("5/5 · Prova na Apple (token de aparelho falso, nenhum push entregue)")
    if not (team and kid and topic and chave):
        falha("prova pulada: falta variável ou a chave é ilegível")
    else:
        resp = sondar_apple(team, kid, pem, topic)
        for amb, (status, motivo) in resp.items():
            aceito, texto = interpretar(amb, status, motivo)
            linha = f"{amb}: HTTP {status} {motivo} → {texto}"
            if aceito:
                ok(linha)
            elif amb == ambiente_servidor:
                falha(linha)
            else:
                aviso(linha + "  (não é o ambiente em uso)")

    print()
    if FALHAS:
        print(f"{VERMELHO}{NEGRITO}{len(FALHAS)} problema(s):{FIM}")
        for f in FALHAS:
            print(f"  - {f}")
        return 1
    print(f"{VERDE}{NEGRITO}Credencial do APNs válida para {ambiente_servidor}.{FIM} Se o push ainda falha, o problema é o token do aparelho (reative o push no iPhone).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
