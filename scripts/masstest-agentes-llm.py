#!/usr/bin/env python3
"""Teste massivo dos agentes de NARRAÇÃO LLM do BolsIA (N2 · /api/analyze).
CUSTA TOKEN REAL — cada ticker×modo é uma chamada de LLM. BYOK: você fornece o
provedor/modelo/chave; o backend chama a LLM. Controle o custo pelo nº de tickers
e --limit. Sai 0 se todos os invariantes DUROS passam, 1 se algum falha.

Requisitos (env):
    BOLSIA_PROVIDER   anthropic | openai | google | local
    BOLSIA_MODEL      id do modelo (ex.: claude-opus-4-8, gpt-4o, gemini-1.5-pro)
    BOLSIA_API_KEY    sua chave do provedor (BYOK)
    BOLSIA_API_URL    (opcional) default https://b3agente-production.up.railway.app
    BOLSIA_BASE_URL   (opcional) base p/ provider openai-compatible/local
    BOLSIA_AUTH       (opcional) valor do header Authorization p/ usar skill/perfil
                      do SEU escopo; sem ele, o backend usa os defaults canônicos.

Uso:
    BOLSIA_PROVIDER=anthropic BOLSIA_MODEL=claude-opus-4-8 BOLSIA_API_KEY=sk-... \
        python3 scripts/masstest-agentes-llm.py                    # 6 tickers × 2 modos
    ... python3 scripts/masstest-agentes-llm.py PETR4 VALE3 --modes estudo --limit 2

Invariantes DUROS (falham o teste): vocabulário de decisão por modo · sem verbo
de ordem no Estudo · formatação normalizada (subconjunto do front) · contrato de
KPIs (enums válidos, markdown não-vazio) · teto de convicção (≤ Médio no N2) ·
geometria stop/alvo coerente com a direção · stop/alvo na faixa plausível.
MOLES (só avisam): Estudo fecha com veredito canônico · números do corpo dentro
do pacote técnico (anti-alucinação) · assertividade (direção declarada).
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

BASE = os.environ.get("BOLSIA_API_URL", "https://b3agente-production.up.railway.app").rstrip("/")
PROVIDER = os.environ.get("BOLSIA_PROVIDER")
MODEL = os.environ.get("BOLSIA_MODEL")
API_KEY = os.environ.get("BOLSIA_API_KEY")
BASE_URL = os.environ.get("BOLSIA_BASE_URL")
AUTH = os.environ.get("BOLSIA_AUTH")

# Espelham skill_ref.vocab / CONCLUSOES_EDU / CONCLUSOES (fonte canônica).
VOCAB = {
    "operador": {"COMPRAR", "VENDER", "AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR", "Reduzir risco"},
    "estudo": {"Estudar alta", "Estudar baixa", "Monitorar", "Aguardar", "Não operar", "Reduzir risco"},
}
CONV_OK = {"Médio", "Baixo"}          # N2 impõe teto ≤ Médio (timeframe único)
DIRECAO_OK = {"Alta", "Baixa", "Lateral"}
QUALID_OK = {"Excelente", "Boa", "Regular", "Ruim"}
CONCLUSOES_EDU = [
    "A leitura técnica é clara e favorece a tese de estudo",
    "O cenário de estudo é promissor, mas ainda exige confirmação",
    "Os sinais são conflitantes. A leitura de estudo é aguardar",
    "Não há, neste momento, uma leitura de estudo com vantagem estatística clara",
]
CONCLUSOES_PRO = [
    "A operação está tecnicamente validada",
    "O cenário é promissor, mas ainda exige confirmação",
    "Os sinais são conflitantes. A melhor decisão é aguardar",
    "Não há uma operação com vantagem estatística clara neste momento",
]
ORDEM = [r"\bcompre\b", r"\bcomprem\b", r"\bvenda\s+(agora|j[áa]|imediata)",
         r"\bentre\s+agora\b", r"\bdeve\s+comprar\b", r"\bdeve\s+vender\b",
         r"\brecomendo\s+(comprar|vender)\b"]
BAD_MD = ["***", "___", "](", "|--", "```", "~~", "__"]   # dialeto que o normalize_markdown deveria ter tirado


def _get(url):
    req = urllib.request.Request(url)
    if AUTH:
        req.add_header("Authorization", AUTH)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def _post(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    if AUTH:
        req.add_header("Authorization", AUTH)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def faixa_precos(tech):
    lows = [c.get("low") for c in (tech.get("candles") or []) if isinstance(c.get("low"), (int, float))]
    highs = [c.get("high") for c in (tech.get("candles") or []) if isinstance(c.get("high"), (int, float))]
    if not lows or not highs:
        return None, None
    return min(lows), max(highs)


def check(ticker, mode, tech, res, hard, soft):
    def H(cond, msg):
        if not cond:
            hard.append(f"{ticker}/{mode}: {msg}")

    def S(cond, msg):
        if not cond:
            soft.append(f"{ticker}/{mode}: {msg}")

    k = res.get("kpis") or {}
    md = res.get("markdown") or ""
    prop = res.get("proposal") or {}
    lo, hi = faixa_precos(tech)

    # contrato de KPIs
    H(k.get("direcao") in DIRECAO_OK, f"direcao inválida: {k.get('direcao')!r}")
    H(k.get("conviccao") in (CONV_OK | {"Alto", "Muito Alto"}), f"conviccao inválida: {k.get('conviccao')!r}")
    H(k.get("qualidade") in QUALID_OK, f"qualidade inválida: {k.get('qualidade')!r}")
    H(bool(md.strip()), "markdown vazio")

    # vocabulário de decisão por modo
    rec = k.get("recomendacao")
    H(rec in VOCAB[mode], f"recomendacao {rec!r} fora do vocabulário do modo {mode}")

    # teto de convicção do N2 (timeframe único ⇒ ≤ Médio)
    H(k.get("conviccao") in CONV_OK, f"conviccao {k.get('conviccao')!r} acima do teto (esperado ≤ Médio)")

    # sem verbo de ordem no Estudo
    if mode == "estudo":
        low = md.lower()
        for pat in ORDEM:
            H(not re.search(pat, low), f"verbo de ordem no corpo do Estudo: /{pat}/")

    # formatação normalizada (o servidor deveria ter reduzido ao subconjunto)
    for bad in BAD_MD:
        H(bad not in md, f"dialeto não-normalizado no markdown: {bad!r}")

    # geometria stop/alvo coerente + faixa plausível
    st, av = prop.get("stop"), prop.get("alvo")
    if isinstance(st, (int, float)) and isinstance(av, (int, float)):
        alta = rec in ("Estudar alta", "COMPRAR") or (k.get("direcao") == "Alta")
        baixa = rec in ("Estudar baixa", "VENDER") or (k.get("direcao") == "Baixa")
        if alta:
            H(av > st, f"geometria alta incoerente: alvo {av} <= stop {st}")
        if baixa:
            H(av < st, f"geometria baixa incoerente: alvo {av} >= stop {st}")
        if lo and hi:
            for nome, v in (("stop", st), ("alvo", av)):
                H(lo * 0.85 <= v <= hi * 1.15, f"{nome} {v} fora da faixa plausível [{lo:.2f},{hi:.2f}]")

    # MOLE: Estudo/Operador fecha com veredito canônico
    conclusoes = CONCLUSOES_EDU if mode == "estudo" else CONCLUSOES_PRO
    S(any(c in md for c in conclusoes), "não fecha com veredito canônico (mole)")

    # MOLE: assertividade — direção declarada no corpo
    S(any(w in md.lower() for w in ("alta", "baixa", "lateral", "aguard", "não operar", "nao operar")),
      "corpo não declara direção clara (mole)")

    # MOLE: anti-alucinação — PREÇOS citados no corpo devem existir no pacote
    # técnico. Monta o universo legítimo (OHLC dos candles + indicadores + stop/
    # alvo) e só cobra os números com MAGNITUDE de preço — valores pequenos são
    # risco/ATR/distância/capital, não preço (evita falso positivo).
    if lo and hi:
        legit = set()
        for c in (tech.get("candles") or []):
            for kk in ("open", "high", "low", "close"):
                if isinstance(c.get(kk), (int, float)):
                    legit.add(round(c[kk], 2))
        for v in (tech.get("indicators") or {}).values():
            if isinstance(v, (int, float)):
                legit.add(round(v, 2))
        for v in (prop.get("stop"), prop.get("alvo")):
            if isinstance(v, (int, float)):
                legit.add(round(v, 2))
        for m in re.findall(r"R\$\s*(\d[\d.]*,\d{2}|\d+\.\d{2})", md):
            v = float(m.replace(".", "").replace(",", ".")) if m.count(",") == 1 else float(m.replace(",", ""))
            if not (lo * 0.7 <= v <= hi * 1.3):
                continue  # fora da banda de preço = capital/risco/ATR/montante, não preço
            if not any(abs(v - g) <= max(0.02, g * 0.005) for g in legit):
                S(False, f"preço R$ {m} não consta no pacote técnico (mole)")


def main():
    if not (PROVIDER and MODEL and (API_KEY or "")):
        print("ERRO: defina BOLSIA_PROVIDER, BOLSIA_MODEL e BOLSIA_API_KEY (BYOK).")
        return 2
    args = [a for a in sys.argv[1:]]
    modes = ["estudo", "operador"]
    period = "1mo"
    limit = None
    tickers = []
    i = 0
    def _val(flag):
        if i + 1 >= len(args):
            print(f"ERRO: {flag} exige um valor."); sys.exit(2)
        return args[i + 1]
    while i < len(args):
        a = args[i]
        if a == "--modes":
            modes = _val(a).split(","); i += 2
        elif a == "--period":
            period = _val(a); i += 2
        elif a == "--limit":
            v = _val(a)
            if not v.isdigit():
                print(f"ERRO: --limit precisa ser um número inteiro (recebi {v!r}). "
                      "Provável paste grudado — limpe a linha (Ctrl-U) e cole de novo."); sys.exit(2)
            limit = int(v); i += 2
        else:
            tickers.append(a.upper()); i += 1
    if not tickers:
        tickers = ["PETR4", "VALE3", "ITUB4", "MGLU3", "BBAS3", "WEGE3"]
    if limit:
        tickers = tickers[:limit]

    config = {"provider": PROVIDER, "model": MODEL, "candlePeriod": period}
    config["apiKey"] = API_KEY
    if BASE_URL:
        config["baseUrl"] = BASE_URL

    n_calls = len(tickers) * len(modes)
    print(f"Alvo: {BASE} · provedor: {PROVIDER}/{MODEL} · período: {period}")
    print(f"Tickers: {', '.join(tickers)} · modos: {', '.join(modes)}")
    print(f"⚠️  {n_calls} chamadas de LLM (custo real). Ctrl-C para abortar.\n")

    hard, soft = [], []
    ok = 0
    for t in tickers:
        try:
            tech = _get(f"{BASE}/api/technicals/{t}?period={period}")
        except Exception as ex:  # noqa: BLE001
            hard.append(f"{t}: /api/technicals falhou: {ex}"); continue
        for mode in modes:
            cfg = dict(config, appMode=("operador" if mode == "operador" else "estudo"))
            try:
                res = _post(f"{BASE}/api/analyze/{t}", {"config": cfg})
            except urllib.error.HTTPError as ex:
                hard.append(f"{t}/{mode}: HTTP {ex.code} {ex.read()[:160]!r}"); continue
            except Exception as ex:  # noqa: BLE001
                hard.append(f"{t}/{mode}: analyze falhou: {ex}"); continue
            before = len(hard)
            check(t, mode, tech, res, hard, soft)
            status = "PASS" if len(hard) == before else "FALHA"
            print(f"  {status}  {t}/{mode:8s}  → {(res.get('kpis') or {}).get('recomendacao')!r}"
                  f" · conv {(res.get('kpis') or {}).get('conviccao')!r}")
            if len(hard) == before:
                ok += 1

    print(f"\n=== RESULTADO ===  {ok}/{n_calls} análises sem violação dura")
    if hard:
        print(f"\n[{len(hard)}] VIOLAÇÕES DURAS:")
        for h in hard:
            print("   ✗", h)
    if soft:
        print(f"\n[{len(soft)}] avisos (moles):")
        for s in soft[:20]:
            print("   ·", s)
        if len(soft) > 20:
            print(f"   ... +{len(soft) - 20}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
