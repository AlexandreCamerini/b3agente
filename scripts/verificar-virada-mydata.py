#!/usr/bin/env python3
"""Checklist AO VIVO da virada de produção para o mydata (Plano 09-06, Task 3,
passos 6-15). Roda DEPOIS que você já mudou as env vars no Railway
(MYDATA_TOKEN, B3_CANDLE_PROVIDER=mydata e, opcionalmente, B3_OPTIONS_PROVIDER
=mydata) e o redeploy terminou.

Este script NÃO toca produção: só faz GET contra a API pública já no ar
(read-only). Não muda nenhuma env var, não faz deploy, não envia ordem. A
seção `/api/obs/usage` é admin-gated — passe um token de sessão de admin
(nunca senha) via --admin-token ou env BORIS_ADMIN_TOKEN; sem token, essa
seção é pulada com aviso, o resto do checklist roda igual.

Uso:
    server/.venv/bin/python scripts/verificar-virada-mydata.py
    server/.venv/bin/python scripts/verificar-virada-mydata.py --admin-token "$BORIS_ADMIN_TOKEN"
    server/.venv/bin/python scripts/verificar-virada-mydata.py --base-url https://boris.semente.dev --ticker-extra WEGE3

Saída: um relatório por passo (PASS/WARN/FAIL/MANUAL) e um resumo final.
Exit code: 0 se nenhum FAIL, 1 caso contrário. WARN/MANUAL não afetam o exit code.
"""
import argparse
import asyncio
import os
import sys

import httpx

DEFAULT_BASE_URL = "https://boris.semente.dev"
TIMEOUT_S = 20.0

# cores só quando for terminal interativo — nunca no log de CI
_TTY = sys.stdout.isatty()
_OK = "\033[32mPASS\033[0m" if _TTY else "PASS"
_WARN = "\033[33mWARN\033[0m" if _TTY else "WARN"
_FAIL = "\033[31mFAIL\033[0m" if _TTY else "FAIL"
_MANUAL = "\033[36mMANUAL\033[0m" if _TTY else "MANUAL"

_RESULTS = []  # (status, titulo, detalhe)


def _registrar(status: str, titulo: str, detalhe: str = ""):
    _RESULTS.append((status, titulo, detalhe))
    linha = f"[{status}] {titulo}"
    print(linha)
    if detalhe:
        for l in detalhe.splitlines():
            print(f"       {l}")


async def _get(client: httpx.AsyncClient, path: str, **params):
    try:
        r = await client.get(path, params=params or None, timeout=TIMEOUT_S)
        return r
    except httpx.HTTPError as e:
        return e


async def passo_6_health(client, base_url: str):
    r = await _get(client, "/api/health")
    if isinstance(r, Exception):
        _registrar(_FAIL, "Passo 6 — /api/health", f"erro de rede: {r!r}")
        return
    if r.status_code != 200:
        _registrar(_FAIL, "Passo 6 — /api/health", f"HTTP {r.status_code}: {r.text[:200]}")
        return
    try:
        data = r.json()
    except ValueError:
        _registrar(_FAIL, "Passo 6 — /api/health", f"corpo não-JSON: {r.text[:200]}")
        return
    ok = bool(data.get("ok"))
    build = data.get("build")
    status = _OK if ok else _FAIL
    _registrar(status, "Passo 6 — /api/health", f"ok={ok} build={build}")


async def passo_7_obs_usage(client, admin_token: str | None):
    if not admin_token:
        _registrar(_WARN, "Passo 7 — /api/obs/usage (candles.*)",
                    "sem --admin-token: passo pulado. Confira manualmente: "
                    "candles.provedor==\"mydata\", candles.fallbacks==[\"brapi\",\"yahoo\"], "
                    "candles.orcamentoMydata presente, candles.porProvedor.mydata.taxaFalha baixa.")
        return None
    r = await _get(client, "/api/obs/usage")
    if isinstance(r, Exception):
        _registrar(_FAIL, "Passo 7 — /api/obs/usage", f"erro de rede: {r!r}")
        return None
    if r.status_code == 403:
        _registrar(_FAIL, "Passo 7 — /api/obs/usage",
                    "HTTP 403 — token sem a permissão observabilidade.ver, ou expirado.")
        return None
    if r.status_code != 200:
        _registrar(_FAIL, "Passo 7 — /api/obs/usage", f"HTTP {r.status_code}: {r.text[:200]}")
        return None
    data = r.json()
    candles = (data or {}).get("candles") or {}
    provedor = candles.get("provedor")
    fallbacks = candles.get("fallbacks")
    orcamento = candles.get("orcamentoMydata")
    taxa_falha = ((candles.get("porProvedor") or {}).get("mydata") or {}).get("taxaFalha")
    detalhe = (f"provedor={provedor} fallbacks={fallbacks}\n"
               f"orcamentoMydata={orcamento}\n"
               f"porProvedor.mydata.taxaFalha={taxa_falha}")
    if provedor == "mydata" and orcamento is not None:
        _registrar(_OK, "Passo 7 — /api/obs/usage (candles.*)", detalhe)
    else:
        _registrar(_WARN, "Passo 7 — /api/obs/usage (candles.*)",
                    detalhe + "\n(provedor não é mydata ainda, ou orcamentoMydata ausente — "
                    "confirme se a env var já foi religada e o redeploy terminou)")
    return orcamento


async def passo_8_card_petr4(client):
    r = await _get(client, "/api/quotes", symbols="PETR4")
    if isinstance(r, Exception) or r.status_code != 200:
        _registrar(_FAIL, "Passo 8 — card PETR4 (/api/quotes)",
                    f"erro: {r if isinstance(r, Exception) else r.status_code}")
        return
    quotes = (r.json() or {}).get("quotes") or {}
    q = quotes.get("PETR4") or {}
    fonte = q.get("source")
    preco = q.get("price")
    rh = await _get(client, "/api/history/PETR4", range="1mo", interval="1d")
    hist_ok, hist_fonte, n_candles = False, None, 0
    if not isinstance(rh, Exception) and rh.status_code == 200:
        hd = rh.json() or {}
        hist_fonte = hd.get("source")
        n_candles = len(hd.get("candles") or [])
        hist_ok = n_candles > 0
    detalhe = f"quote: source={fonte} price={preco}\nhistory(1d): source={hist_fonte} candles={n_candles}"
    if hist_ok:
        _registrar(_OK, "Passo 8 — card PETR4 (histórico carrega)", detalhe)
    else:
        _registrar(_FAIL, "Passo 8 — card PETR4 (histórico carrega)", detalhe)


async def passo_9_ticker_fora_catalogo(client, ticker: str):
    r = await _get(client, "/api/history/" + ticker, range="1mo", interval="1d")
    if isinstance(r, Exception):
        _registrar(_FAIL, f"Passo 9 — ticker fora do catálogo ({ticker})", f"erro de rede: {r!r}")
        return
    if r.status_code != 200:
        _registrar(_FAIL, f"Passo 9 — ticker fora do catálogo ({ticker})", f"HTTP {r.status_code}: {r.text[:200]}")
        return
    d = r.json() or {}
    n = len(d.get("candles") or [])
    status = _OK if n > 0 else _FAIL
    _registrar(status, f"Passo 9 — ticker fora do catálogo ({ticker})",
               f"source={d.get('source')} candles={n}")


async def passo_10_intraday(client):
    r = await _get(client, "/api/history/PETR4", range="5d", interval="15m")
    if isinstance(r, Exception):
        _registrar(_FAIL, "Passo 10 — intraday (15m) continua no Yahoo", f"erro de rede: {r!r}")
        return
    if r.status_code != 200:
        _registrar(_FAIL, "Passo 10 — intraday (15m) continua no Yahoo", f"HTTP {r.status_code}: {r.text[:200]}")
        return
    d = r.json() or {}
    fonte = d.get("source")
    n = len(d.get("candles") or [])
    # ADR-001 não reaberta nesta fase: intraday nunca deveria vir do mydata.
    if fonte == "mydata":
        _registrar(_FAIL, "Passo 10 — intraday (15m) continua no Yahoo",
                    f"source={fonte} — ADR-001 violada, mydata não deveria servir intraday")
        return
    status = _OK if n > 0 else _WARN
    _registrar(status, "Passo 10 — intraday (15m) continua no Yahoo", f"source={fonte} candles={n}")


async def passo_11_gasto_minuto(orcamento):
    if orcamento is None:
        _registrar(_MANUAL, "Passo 11 — orcamentoMydata.gastoMinuto < 60",
                    "sem --admin-token, não deu para checar automaticamente — confira em /api/obs/usage")
        return
    gasto = (orcamento or {}).get("gastoMinuto")
    if gasto is None:
        _registrar(_WARN, "Passo 11 — orcamentoMydata.gastoMinuto < 60", "campo ausente no payload")
        return
    status = _OK if gasto < 60 else _FAIL
    _registrar(status, "Passo 11 — orcamentoMydata.gastoMinuto < 60", f"gastoMinuto={gasto}")


async def passo_12_13_opcoes(client):
    r = await _get(client, "/api/options/expirations/PETR4")
    if isinstance(r, Exception) or r.status_code != 200:
        _registrar(_FAIL, "Passo 12 — vencimentos de opções (PETR4)",
                    f"erro: {r if isinstance(r, Exception) else r.status_code}")
        return
    d = r.json() or {}
    vencs = d.get("expirations") or []
    fonte = d.get("source")
    status = _OK if vencs else _WARN
    _registrar(status, "Passo 12 — vencimentos de opções (PETR4)",
               f"source={fonte} n_vencimentos={len(vencs)}")
    if not vencs:
        return

    rc = await _get(client, "/api/options/chain/PETR4", expiration=vencs[0])
    if isinstance(rc, Exception) or rc.status_code != 200:
        _registrar(_FAIL, "Passo 13 — cadeia de opções (PETR4)",
                    f"erro: {rc if isinstance(rc, Exception) else rc.status_code}")
        return
    cd = rc.json() or {}
    puts = cd.get("puts") or []
    calls = cd.get("calls") or []
    total = puts + calls
    com_iv = sum(1 for c in total if c.get("impliedVolatility") is not None)
    detalhe = (f"source={cd.get('source')} vencimento={vencs[0]} "
               f"contratos={len(total)} (puts={len(puts)} calls={len(calls)}) "
               f"com_iv={com_iv}/{len(total) or 1}")
    status = _OK if total else _WARN
    _registrar(status, "Passo 13 — cadeia de opções (PETR4)", detalhe)

    rg = await _get(client, "/api/options/gate/PETR4")
    if not isinstance(rg, Exception) and rg.status_code == 200:
        gd = rg.json() or {}
        _registrar(_OK if gd else _WARN, "Passo 13b — gate de liquidez (linha de opções no card)",
                   f"resultado={gd}")


def passos_manuais():
    _registrar(_MANUAL, "Passo 14 — falha de opções bloqueia compra simulada",
               "Forçar uma falha (ex.: revogar a chave temporariamente) não é seguro para "
               "este script automatizar. Confirme manualmente que providerStatus=\"degraded\" "
               "bloqueia a compra simulada, nunca inventa uma cadeia (D-04, ADR-004).")
    _registrar(_MANUAL, "Passo 15 — números da carteira intocados",
               "Requer sessão de usuário autenticada (login), fora do escopo deste script. "
               "Confirme manualmente: saldo, posições, preço médio e P&L iguais aos de antes "
               "da virada — candle é insumo, nenhum cálculo de carteira deveria se mover.")


async def main_async(base_url: str, admin_token: str | None, ticker_extra: str):
    headers = {}
    if admin_token:
        headers["Authorization"] = f"Bearer {admin_token}"
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        await passo_6_health(client, base_url)
        orcamento = await passo_7_obs_usage(client, admin_token)
        await passo_8_card_petr4(client)
        await passo_9_ticker_fora_catalogo(client, ticker_extra)
        await passo_10_intraday(client)
        await passo_11_gasto_minuto(orcamento)
        await passo_12_13_opcoes(client)
    passos_manuais()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"default: {DEFAULT_BASE_URL}")
    ap.add_argument("--admin-token", default=os.environ.get("BORIS_ADMIN_TOKEN"),
                     help="token de sessão de admin (nunca senha); ou env BORIS_ADMIN_TOKEN")
    ap.add_argument("--ticker-extra", default="WEGE3",
                     help="ticker fora do catálogo padrão pro passo 9 (default: WEGE3)")
    args = ap.parse_args()

    print(f"== Checklist ao vivo da virada mydata — {args.base_url} ==\n")
    asyncio.run(main_async(args.base_url, args.admin_token, args.ticker_extra))

    n_fail = sum(1 for s, _, _ in _RESULTS if s == _FAIL)
    n_warn = sum(1 for s, _, _ in _RESULTS if s == _WARN)
    n_manual = sum(1 for s, _, _ in _RESULTS if s == _MANUAL)
    n_ok = sum(1 for s, _, _ in _RESULTS if s == _OK)
    print(f"\n== Resumo: {n_ok} PASS · {n_warn} WARN · {n_fail} FAIL · {n_manual} MANUAL ==")
    if n_fail:
        print("Pelo menos um FAIL — não considere a virada validada até investigar.")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
