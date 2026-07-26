#!/usr/bin/env python3
"""Teste massivo dos agentes DETERMINÍSTICOS do BolsIA (scanner/setups/plano/
fundamento) contra produção — GRÁTIS, sem custo de LLM. Varre o universo inteiro
em vários timeframes (force=1) e valida os invariantes que a skill
analise-tecnica-b3 e o produto exigem. Sai 0 se tudo passa, 1 se há violação —
serve de gate pré-deploy.

    python3 scripts/masstest-agentes.py                 # produção, 1mo/3mo/6mo/1y
    BOLSIA_API_URL=http://localhost:8000 python3 scripts/masstest-agentes.py 1mo 1y

Invariantes cobertos (por ativo × timeframe):
  vocabulário de veredito/decisão · coerência veredito↔plano (Princípio 9) ·
  lado do plano == decisão · geometria (stop no lado certo, alvos ordenados,
  riscoPorAcao) · R:R final ≥ 1,5 (Princípio 5) · confluência 0–100 ·
  melhorSetup presente em veredito direcional · score de fundamento recomputável ·
  snapshotAt e close válidos.
"""
import json
import os
import sys
import urllib.request
import collections

BASE = os.environ.get("BOLSIA_API_URL", "https://b3agente-production.up.railway.app").rstrip("/")
PERIODS = sys.argv[1:] or ["1mo", "3mo", "6mo", "1y"]
VEREDITOS = {"Estudar alta", "Estudar baixa", "Monitorar", "Aguardar",
             "Não operar", "Sem setup no momento"}
DECISOES = {"COMPRAR", "VENDER", "AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR", "Reduzir risco"}
OPERAVEIS = {"COMPRAR", "VENDER"}
viol = collections.defaultdict(list)   # tipo -> [(period, ticker, detalhe)]
stats = collections.Counter()


def fetch(period):
    with urllib.request.urlopen(f"{BASE}/api/scan?period={period}&force=1", timeout=120) as r:
        return json.load(r)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def check(period, x):
    t = x.get("ticker")
    ver = x.get("veredito")
    pl = x.get("plano") or {}
    dec = pl.get("decisao")
    stats["ativos"] += 1

    if ver not in VEREDITOS:
        viol["vocab_veredito"].append((period, t, ver))
    if dec not in DECISOES:
        viol["vocab_decisao"].append((period, t, dec))

    # coerência veredito<->plano (P1: plano segue o lado dominante)
    if ver == "Estudar baixa" and dec == "COMPRAR":
        viol["coerencia_baixa_COMPRAR"].append((period, t, ""))
    if ver == "Estudar alta" and dec == "VENDER":
        viol["coerencia_alta_VENDER"].append((period, t, ""))

    lado = pl.get("lado")
    if dec == "COMPRAR" and lado != "alta":
        viol["lado_COMPRAR_nao_alta"].append((period, t, lado))
    if dec == "VENDER" and lado != "baixa":
        viol["lado_VENDER_nao_baixa"].append((period, t, lado))

    if dec in OPERAVEIS:
        stats["operaveis"] += 1
        e, s, a1, a2 = (num(pl.get("entrada")), num(pl.get("stop")),
                        num(pl.get("alvo1")), num(pl.get("alvo2")))
        rr2 = num(pl.get("rr2"))
        risco = num(pl.get("riscoPorAcao"))
        if None in (e, s, a1, a2):
            viol["geo_niveis_faltando"].append((period, t, {k: pl.get(k) for k in ("entrada", "stop", "alvo1", "alvo2")}))
        else:
            if any(v <= 0 for v in (e, s, a1, a2)):
                viol["geo_nivel_nao_positivo"].append((period, t, (e, s, a1, a2)))
            if dec == "COMPRAR":
                if not (s < e):
                    viol["geo_stop_lado_errado"].append((period, t, f"COMPRAR stop {s} >= entrada {e}"))
                if not (a1 > e):
                    viol["geo_alvo1_lado_errado"].append((period, t, f"COMPRAR alvo1 {a1} <= entrada {e}"))
                if not (a2 > a1):
                    viol["geo_alvo2_ordem"].append((period, t, f"alvo2 {a2} <= alvo1 {a1}"))
            else:
                if not (s > e):
                    viol["geo_stop_lado_errado"].append((period, t, f"VENDER stop {s} <= entrada {e}"))
                if not (a1 < e):
                    viol["geo_alvo1_lado_errado"].append((period, t, f"VENDER alvo1 {a1} >= entrada {e}"))
                if not (a2 < a1):
                    viol["geo_alvo2_ordem"].append((period, t, f"alvo2 {a2} >= alvo1 {a1}"))
            if risco is not None and abs(risco - abs(e - s)) > max(0.01, abs(e - s) * 0.02):
                viol["geo_risco_por_acao"].append((period, t, f"risco {risco} != |e-s| {abs(e - s):.2f}"))
            if rr2 is not None and rr2 < 1.5:
                viol["rr2_abaixo_1.5"].append((period, t, f"rr2={rr2}"))

    conf = num(x.get("confluencia"))
    if conf is None or not (0 <= conf <= 100):
        viol["confluencia_fora_faixa"].append((period, t, conf))
    if ver in ("Estudar alta", "Estudar baixa") and not x.get("melhorSetup"):
        viol["direcional_sem_melhorSetup"].append((period, t, ver))

    f = x.get("fundamento")
    if f:
        sc = f.get("score")
        if sc not in ("A", "B", "C", None):
            viol["fund_score_invalido"].append((period, t, sc))
        pil = []
        if f.get("pl") is not None:
            pil.append(0 < f["pl"] <= 20)
        if f.get("roe") is not None or f.get("margemLiquida") is not None:
            pil.append((f.get("roe") or 0) >= 0.10 and (f.get("margemLiquida") or 0) > 0)
        if f.get("dividaEbitda") is not None:
            pil.append(f["dividaEbitda"] <= 3.0)
        esperado = None if len(pil) < 2 else ("A" if sum(pil) >= 2 else ("B" if sum(pil) == 1 else "C"))
        if sc != esperado:
            viol["fund_score_incoerente"].append((period, t, f"score={sc} esperado={esperado} pilares={pil}"))

    if not x.get("snapshotAt"):
        viol["sem_snapshotAt"].append((period, t, ""))
    if (num(x.get("close")) or 0) <= 0:
        viol["close_invalido"].append((period, t, x.get("close")))


def main():
    print(f"Alvo: {BASE} · períodos: {', '.join(PERIODS)}")
    for p in PERIODS:
        try:
            d = fetch(p)
        except Exception as ex:  # noqa: BLE001
            viol["fetch_falhou"].append((p, "-", str(ex)))
            continue
        r = d.get("results") or []
        stats[f"periodo_{p}"] = len(r)
        for x in r:
            check(p, x)

    print("\n=== COBERTURA ===")
    print(f"ativos-checagem: {stats['ativos']} · planos operáveis: {stats['operaveis']}")
    for p in PERIODS:
        print(f"  {p}: {stats.get('periodo_' + p, 0)} ativos")

    print("\n=== VIOLAÇÕES ===")
    if not viol:
        print("NENHUMA — todos os invariantes passaram ✓")
        return 0
    for tipo in sorted(viol, key=lambda k: -len(viol[k])):
        casos = viol[tipo]
        print(f"\n[{len(casos)}] {tipo}")
        for period, t, det in casos[:8]:
            print(f"    {period} {t}: {det}")
        if len(casos) > 8:
            print(f"    ... +{len(casos) - 8}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
