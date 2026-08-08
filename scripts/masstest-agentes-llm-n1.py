#!/usr/bin/env python3
"""Teste massivo do agente de narração LLM N1 (Radar deep · /api/scan/deep).
CUSTA TOKEN REAL — 1 chamada por ticker do top-N. BYOK (ver masstest-agentes-llm.py
para as env vars). Controle o custo pelo --topn. Sai 0 se os invariantes DUROS
passam, 1 se algum falha.

    BOLSIA_PROVIDER=anthropic BOLSIA_MODEL=claude-opus-4-8 BOLSIA_API_KEY=sk-... \
        python3 scripts/masstest-agentes-llm-n1.py            # topN 3, estudo+operador
    ... python3 scripts/masstest-agentes-llm-n1.py --topn 2 --modes operador

DUROS: planoEstudo no vocabulário do modo · confianca ≤ moderada (teto do N1) ·
parseFalhou falso · contrato (leituraSetups lista, cenarios com alta/baixa/neutro,
modelosUtilizados não-vazio, resumo não-vazio) · sem verbo de ordem no Estudo ·
COERÊNCIA: planoEstudo não contradiz o lado do melhorSetup determinístico.
MOLES: operador fecha o resumo com conclusão canônica.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

BASE = os.environ.get("BOLSIA_API_URL", "https://boris.semente.dev").rstrip("/")
PROVIDER = os.environ.get("BOLSIA_PROVIDER")
MODEL = os.environ.get("BOLSIA_MODEL")
API_KEY = os.environ.get("BOLSIA_API_KEY")
BASE_URL = os.environ.get("BOLSIA_BASE_URL")
AUTH = os.environ.get("BOLSIA_AUTH")

VOCAB = {
    "operador": {"COMPRAR", "VENDER", "AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR"},
    "estudo": {"Estudar alta", "Estudar baixa", "Monitorar", "Aguardar", "Não operar"},
}
CONF_OK = {"baixa", "moderada"}                 # teto do N1 (DEEP_FORMAT)
BULL = {"Estudar alta", "COMPRAR"}
BEAR = {"Estudar baixa", "VENDER"}
CONCLUSOES_PRO = ["tecnicamente validada", "promissor, mas ainda exige confirmação",
                  "conflitantes. A melhor decisão é aguardar", "vantagem estatística clara neste momento"]
ORDEM = [r"\bcompre\b", r"\bcomprem\b", r"\bvenda\s+(agora|j[áa]|imediata)",
         r"\bentre\s+agora\b", r"\bdeve\s+comprar\b", r"\bdeve\s+vender\b",
         r"\brecomendo\s+(comprar|vender)\b"]


def _post(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    if AUTH:
        req.add_header("Authorization", AUTH)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def lado_deterministico(melhor_setup):
    s = (melhor_setup or "").lower()
    if "(alta)" in s:
        return "alta"
    if "(baixa)" in s:
        return "baixa"
    return None


def check(mode, row, hard, soft):
    t = row.get("ticker")
    d = row.get("deep") or {}

    def H(cond, msg):
        if not cond:
            hard.append(f"{t}/{mode}: {msg}")

    def S(cond, msg):
        if not cond:
            soft.append(f"{t}/{mode}: {msg}")

    H(not d.get("parseFalhou"), "parseFalhou=True (resposta do modelo não parseou)")
    pe = d.get("planoEstudo")
    H(pe in VOCAB[mode], f"planoEstudo {pe!r} fora do vocabulário do modo {mode}")
    H(d.get("confianca") in CONF_OK, f"confianca {d.get('confianca')!r} acima do teto (≤ moderada)")
    H(bool((d.get("resumo") or "").strip()), "resumo vazio")
    H(isinstance(d.get("leituraSetups"), list), "leituraSetups não é lista")
    cen = d.get("cenarios") or {}
    H(all(k in cen for k in ("alta", "baixa", "neutro")), f"cenarios sem alta/baixa/neutro: {list(cen)}")
    H(bool(d.get("modelosUtilizados")), "modelosUtilizados vazio (o app ensina, não opina)")

    # texto agregado para varreduras
    blob = " ".join([str(d.get("resumo") or ""), json.dumps(cen, ensure_ascii=False),
                     json.dumps(d.get("leituraSetups") or [], ensure_ascii=False),
                     json.dumps(d.get("riscos") or [], ensure_ascii=False),
                     str(d.get("invalidacao") or "")]).lower()
    if mode == "estudo":
        for pat in ORDEM:
            H(not re.search(pat, blob), f"verbo de ordem no N1 do Estudo: /{pat}/")

    # COERÊNCIA com o determinístico: planoEstudo não contradiz o melhorSetup
    lado = lado_deterministico(row.get("melhorSetup"))
    if lado == "alta":
        H(pe not in BEAR, f"planoEstudo {pe!r} contradiz melhorSetup de ALTA ({row.get('melhorSetup')!r})")
    elif lado == "baixa":
        H(pe not in BULL, f"planoEstudo {pe!r} contradiz melhorSetup de BAIXA ({row.get('melhorSetup')!r})")

    # MOLE: operador fecha o resumo com conclusão canônica
    if mode == "operador":
        S(any(c.lower() in str(d.get("resumo") or "").lower() for c in CONCLUSOES_PRO),
          "resumo do operador não fecha com conclusão canônica (mole)")


def main():
    if not (PROVIDER and MODEL and (API_KEY or "")):
        print("ERRO: defina BOLSIA_PROVIDER, BOLSIA_MODEL e BOLSIA_API_KEY (BYOK).")
        return 2
    args = sys.argv[1:]
    modes = ["estudo", "operador"]
    period = "1mo"
    topn = 3
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--modes":
            modes = args[i + 1].split(","); i += 2
        elif a == "--period":
            period = args[i + 1]; i += 2
        elif a == "--topn":
            v = args[i + 1]
            if not v.isdigit():
                print(f"ERRO: --topn precisa ser inteiro (recebi {v!r})."); return 2
            topn = int(v); i += 2
        else:
            print(f"ERRO: argumento desconhecido {a!r}."); return 2

    config = {"provider": PROVIDER, "model": MODEL, "candlePeriod": period, "apiKey": API_KEY}
    if BASE_URL:
        config["baseUrl"] = BASE_URL

    print(f"Alvo: {BASE} · {PROVIDER}/{MODEL} · período {period} · topN {topn}")
    print(f"⚠️  até {topn * len(modes)} chamadas de LLM (custo real). Ctrl-C para abortar.\n")

    hard, soft = [], []
    total = 0
    for mode in modes:
        body = {"config": dict(config, appMode=("operador" if mode == "operador" else "estudo")),
                "appMode": ("operador" if mode == "operador" else "estudo"),
                "period": period, "topN": topn}
        try:
            resp = _post(f"{BASE}/api/scan/deep", body)
        except urllib.error.HTTPError as ex:
            hard.append(f"{mode}: HTTP {ex.code} {ex.read()[:160]!r}"); continue
        except Exception as ex:  # noqa: BLE001
            hard.append(f"{mode}: scan/deep falhou: {ex}"); continue
        rows = resp.get("results") or []
        for e in (resp.get("errors") or []):
            hard.append(f"{e.get('ticker')}/{mode}: erro no deep: {e.get('erro')}")
        for row in rows:
            total += 1
            before = len(hard)
            check(mode, row, hard, soft)
            d = row.get("deep") or {}
            status = "PASS" if len(hard) == before else "FALHA"
            print(f"  {status}  {row.get('ticker')}/{mode:8s} → {d.get('planoEstudo')!r}"
                  f" · conf {d.get('confianca')!r} · setup {row.get('melhorSetup')!r}")

    print(f"\n=== RESULTADO ===  {total} análises N1 · {len(hard)} violações duras")
    if hard:
        print("\nVIOLAÇÕES DURAS:")
        for h in hard:
            print("   ✗", h)
    if soft:
        print(f"\n[{len(soft)}] avisos (moles):")
        for s in soft[:20]:
            print("   ·", s)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
