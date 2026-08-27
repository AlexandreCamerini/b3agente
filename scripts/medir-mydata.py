#!/usr/bin/env python3
"""Medição do volume de chamadas ao hub `mydata` (cvm-financas) que as duas
fatias já migradas nesta fase — COTAHIST diário (`mydata_client.get_history`)
e cadeia de opções (`options_provider_mydata.get_options`) — custam, contra o
limite da chave de produção (60/min · 2.000/dia).

Este script NÃO toca produção: não importa o módulo de entrada do FastAPI,
não abre o banco (nenhuma leitura da variável de caminho do SQLite), não
escreve em `/data`, e nunca chama `candle_cache.configure_db` — o cache L2
persistente fica sempre desligado (modo memória-apenas do próprio módulo).

Fases (selecionáveis por `--fases`; default só `projecao`):
  projecao — 100% offline, ZERO rede. Mede o custo unitário EXECUTANDO o
             código real (`mydata_client.get_history`/`get_vencimentos`/
             `get_options_chain`, via `options_provider_mydata.get_options`)
             com um `fetch_json` fake injetado que CONTA chamadas — não lê o
             código e estima. Projeta três cenários sobre o universo REAL do
             Radar (`scanner.get_universe()`) e emite um veredito explícito
             contra 60/min e 2.000/dia.
  vivo     — rede REAL contra o hub, só com `--vivo` explícito (T-09-18: não
             gasta cota da chave de produção por acidente). Amostra pequena
             (`--amostra`, default 5 tickers × 2 rotas). Exige MYDATA_TOKEN
             no ambiente — ausente, sai com código 2 e NÃO simula.

Uso:
    server/.venv/bin/python scripts/medir-mydata.py --fases projecao
    server/.venv/bin/python scripts/medir-mydata.py --fases projecao,vivo --vivo --amostra 5 --saida /tmp/medicao-mydata.json

Saída: tabelas Markdown no stdout + JSON bruto opcional (`--saida`). O token
NUNCA é impresso, nem inteiro nem parcial — só o cabeçalho de cota
(`X-Quota-Limite`/`X-Quota-Restante`) devolvido pelo hub.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "server"))

from app import candle_cache, mydata_budget, mydata_client  # noqa: E402
from app import options_provider_mydata, scanner  # noqa: E402  (o universo REAL do Radar)

# Espelho de server/app/agent.py:INTERVAL_S_DEFAULT (300s) e da resolução por
# env que `scheduler_loop` faz (B3_AGENT_INTERVAL_S). NÃO importamos
# `agent.py` aqui de propósito — ele puxa módulos de persistência de sessão
# de usuário que este script declara não tocar; o número é uma CONSTANTE
# pública do módulo, copiada, não recalculada.
AGENT_INTERVAL_S_DEFAULT = 300

# Espelho de server/app/scanner.py:MIN_FETCH_GAP_S — o espaçamento mínimo
# GLOBAL (gate_lock serializa TODAS as chamadas reais, independente do
# semáforo de concorrência) entre chamadas reais ao provedor de candle
# durante uma varredura do Radar.
SCANNER_MIN_FETCH_GAP_S = scanner.MIN_FETCH_GAP_S

# Token fictício, só para satisfazer o guard `if not _token()` das funções de
# mydata_client durante a fase `projecao` — nunca chega à rede porque TODO
# fetch_json usado nesta fase é um fake local. Nunca impresso.
_FAKE_TOKEN_PROJECAO = "medicao-offline-sem-rede-nao-e-chave-real"


# ---------------------------------------------------------------------------
# Fase PROJEÇÃO — offline, determinística, ZERO rede
# ---------------------------------------------------------------------------
def _linha_candle_fake(i: int) -> dict:
    return {
        "dt_pregao": f"2026-01-{(i % 27) + 1:02d}",
        "preco_abertura": 10.0, "preco_maximo": 10.5, "preco_minimo": 9.5,
        "preco_fechamento": 10.2, "quantidade_negociada": 1000,
    }


def _venc_fake() -> dict:
    return {"dt_vencimento": "2026-02-20", "vence_no_pregao": False}


def _linha_opcao_fake(i: int) -> dict:
    return {
        "contrato": f"PETRA{i}20026", "tipo": "call", "strike": 30.0,
        "premio": 1.5, "melhor_oferta_compra": 1.4, "melhor_oferta_venda": 1.6,
        "quantidade_negociada": 100, "volatilidade_implicita": 0.25,
        "preco_objeto": 30.5, "dt_pregao": "2026-01-15",
        "situacao_sigma": "ok", "preco_teorico": 1.55,
        "delta": 0.5, "gamma": 0.02, "vega": 0.1, "theta": -0.01, "rho": 0.03,
        "dt_vencimento": "2026-02-20", "taxa_livre_risco": 0.1,
        "estilo_exercicio": "europeia",
    }


class _ContadorPaginas:
    """fetch_json fake: conta chamadas HTTP e simula N páginas encadeadas via
    `proximo_cursor` — reusa a MESMA forma de envelope que
    `mydata_client._paginar` espera (`{"dados": [...], "proximo_cursor": ...}`),
    então o código real de paginação roda sem saber que é fake."""

    def __init__(self, n_paginas: int, linha_fn=_linha_candle_fake):
        self.n_paginas = max(1, n_paginas)
        self.linha_fn = linha_fn
        self.chamadas = 0

    async def __call__(self, path: str, params: dict) -> dict:
        self.chamadas += 1
        dados = [self.linha_fn(self.chamadas)]
        proximo = "cursor-fake" if self.chamadas < self.n_paginas else None
        return {"dados": dados, "proximo_cursor": proximo}


async def _medir_custo_candle(rng: str, n_paginas: int) -> int:
    """Executa `mydata_client.get_history` de verdade, com `fetch_json` fake
    injetado — mede quantas chamadas HTTP o range custa."""
    contador = _ContadorPaginas(n_paginas)
    await mydata_client.get_history("PETR4", rng=rng, interval="1d", fetch_json=contador)
    return contador.chamadas


async def _medir_custo_cadeia(n_paginas_cadeia: int) -> int:
    """1 chamada de vencimentos (sem paginação) + N páginas de cadeia.

    `options_provider_mydata.get_options()` não aceita `fetch_json`
    injetável — chama `mydata_client.get_vencimentos`/`get_options_chain`
    sem esse parâmetro, e ambos caem no default do módulo
    (`fetch_json or _fetch_json`), resolvido pelo NOME `_fetch_json` no
    namespace do módulo EM TEMPO DE CHAMADA. Substituir o atributo do módulo
    intercepta os dois sem mudar nenhuma assinatura pública — mesmo truque
    que os guardiões offline de `test_options_provider_mydata.py` já usam.
    """
    original = mydata_client._fetch_json
    contagem_venc = {"n": 0}
    contador_cadeia = _ContadorPaginas(n_paginas_cadeia, linha_fn=_linha_opcao_fake)

    async def _fake(path: str, params: dict) -> dict:
        if path.endswith("/vencimentos"):
            contagem_venc["n"] += 1
            return {"dados": [_venc_fake()]}
        return await contador_cadeia(path, params)

    mydata_client._fetch_json = _fake
    options_provider_mydata._cache.clear()  # evita servir do TTL entre medições
    try:
        payload = await options_provider_mydata.get_options("PETR4")
        if payload.get("providerStatus") != "ok":
            raise RuntimeError(f"medição de cadeia (fake) não devolveu 'ok': {payload}")
    finally:
        mydata_client._fetch_json = original
    return contagem_venc["n"] + contador_cadeia.chamadas


def _pico_burst(n_chamadas: int, gap_s: float) -> int:
    """Quantas chamadas cabem em QUALQUER janela de 60s quando espaçadas por
    `gap_s` segundos por um gate GLOBAL sequencial (mesmo padrão de
    `scanner.py:throttled`, que serializa TODAS as chamadas reais via
    `gate_lock`, independente do semáforo de concorrência). Uma rajada menor
    que a capacidade da janela cabe inteira num minuto só."""
    if gap_s <= 0:
        return n_chamadas
    capacidade_60s = int(60.0 / gap_s) + 1
    return min(n_chamadas, capacidade_60s)


def _intervalo_minimo_seguro_s(quota_min: int) -> Optional[float]:
    """Espaçamento mínimo entre chamadas reais ao mydata — o análogo de
    `MIN_FETCH_GAP_S` de `scanner.py` (hoje 0.15s, dimensionado para
    Yahoo/brapi) — que mantém o pico de qualquer janela de 60s dentro da cota
    do MINUTO da chave mydata."""
    if quota_min <= 0:
        return None
    return round(60.0 / quota_min, 3)


def _veredito(total: float, cota: float) -> str:
    if not cota or total > cota:
        return "NÃO CABE"
    folga_pct = (cota - total) / cota * 100
    if folga_pct < 20:
        return "CABE COM FOLGA < 20%"
    return "CABE"


async def fase_projecao(args) -> dict:
    print("\n## Fase `projecao` — custo offline, ZERO rede\n")

    token_original = os.environ.get("MYDATA_TOKEN")
    os.environ["MYDATA_TOKEN"] = _FAKE_TOKEN_PROJECAO
    try:
        universo = scanner.get_universe()
        origem = ("B3_SCAN_UNIVERSE (env)" if (os.environ.get("B3_SCAN_UNIVERSE") or "").strip()
                   else "default (scanner.DEFAULT_UNIVERSE)")
        universo_n = len(universo)
        print(f"Universo real do Radar (`scanner.get_universe()`): {universo_n} ativos "
              f"(origem: {origem}).")

        full_range, recent_range = candle_cache.ranges_for("1d")

        custo_carga_1p = await _medir_custo_candle(full_range, 1)
        custo_carga_3p = await _medir_custo_candle(full_range, 3)
        custo_delta_1p = await _medir_custo_candle(recent_range, 1)
        custo_delta_3p = await _medir_custo_candle(recent_range, 3)

        print("\n### Custos unitários medidos — candle (`mydata_client.get_history`)\n")
        print("| Range | Sem paginação (1 página fake) | Com paginação (3 páginas fake) |")
        print("|---|---|---|")
        print(f"| carga cheia ({full_range}) | {custo_carga_1p} | {custo_carga_3p} |")
        print(f"| delta ({recent_range}) | {custo_delta_1p} | {custo_delta_3p} |")
        print(f"\n(teto real de páginas por chamada lógica: "
              f"`mydata_client.PAGINAS_MAX` = {mydata_client.PAGINAS_MAX}; as medições acima "
              f"usam 1 e 3 páginas fake, bem abaixo do teto, só para expor o comportamento "
              f"com e sem paginação.)")

        custo_cadeia_1p = await _medir_custo_cadeia(1)
        custo_cadeia_3p = await _medir_custo_cadeia(3)
        print("\n### Custo unitário medido — cadeia de opções (`options_provider_mydata.get_options`)\n")
        print("| Sem paginação (1 página fake da cadeia) | Com paginação (3 páginas fake) |")
        print("|---|---|")
        print(f"| {custo_cadeia_1p} (1 vencimentos + {custo_cadeia_1p - 1} cadeia) | {custo_cadeia_3p} |")
    finally:
        if token_original is None:
            os.environ.pop("MYDATA_TOKEN", None)
        else:
            os.environ["MYDATA_TOKEN"] = token_original

    quota_min = mydata_budget.quota_min()
    quota_dia = mydata_budget.quota_dia()

    # -- Cenário FRIO: redeploy do Railway com L2 vazio, carga cheia do
    #    universo inteiro de uma vez. --------------------------------------
    chamadas_frio = universo_n * custo_carga_1p
    pico_min_frio = _pico_burst(chamadas_frio, SCANNER_MIN_FETCH_GAP_S)

    # -- Cenário MORNO: delta do universo inteiro. ------------------------
    # ACHADO (Rule 1 — premissa do plano não bateu com o código): o texto do
    # plano descreve a cadência como "interval_s do scheduler_loop" (300s),
    # mas essa passada NÃO existe a cada tick do scheduler — o único ponto
    # que varre o universo INTEIRO (`scanner.run_scan`) é
    # `radar_daily.maybe_run`, gated por `pregao.is_trading_day()`, rodando
    # 1x POR DIA ÚTIL às `B3_RADAR_DAILY_HHMM` (default 08:45). O
    # `scheduler_loop` a cada 300s toca candles de POSIÇÃO/pendência do
    # usuário (conjunto pequeno, spot via brapi/Yahoo — não mydata) e o
    # intraday GLOBAL (Yahoo, ADR-001 intocada) — nenhum dos dois é "delta
    # do universo inteiro" no candle mydata. Reportamos os DOIS números:
    # o REAL (observado no código) e o LITERAL do texto do plano (rotulado
    # como hipótese não observada), para não subestimar nem inflar o risco.
    ciclos_dia_morno_real = 1
    chamadas_por_ciclo_morno = universo_n * custo_delta_1p
    chamadas_dia_morno_real = ciclos_dia_morno_real * chamadas_por_ciclo_morno
    pico_min_morno = _pico_burst(chamadas_por_ciclo_morno, SCANNER_MIN_FETCH_GAP_S)

    interval_scheduler_s = int(os.environ.get("B3_AGENT_INTERVAL_S") or AGENT_INTERVAL_S_DEFAULT)
    ciclo_efetivo_s = max(interval_scheduler_s, candle_cache._MIN_DELTA_INTERVAL)
    ciclos_dia_morno_literal = int(86400 / ciclo_efetivo_s)
    chamadas_dia_morno_literal = ciclos_dia_morno_literal * chamadas_por_ciclo_morno

    # -- Cenário OPÇÕES: cadeias abertas por usuário, TTL de 300s
    #    absorvendo repetição. -------------------------------------------
    cadeias_dia = max(0, args.cadeias_dia)
    chamadas_dia_opcoes = cadeias_dia * custo_cadeia_1p
    # ACHADO (arquitetura, não Rule 1 — nada a corrigir neste plano):
    # `options_provider.py`/`options_provider_mydata.py` NUNCA chamam
    # `mydata_budget.pode_gastar`/`debita` (confirmado por leitura — só
    # `candle_provider.get_history()` tem gate por elo, Plano 09-02). Opções
    # não têm NENHUM teto de taxa no código: o pico/min é limitado só pela
    # concorrência REAL de usuários abrindo cadeias distintas, que este
    # script não mede (sem dado de uso real). Reportar um número aqui seria
    # inventar valor (princípio 4 do CLAUDE.md) — o campo fica `None`,
    # nomeado como achado.
    pico_min_opcoes = None

    print("\n### Projeção — três cenários\n")
    print("| Cenário | chamadas/dia | pico chamadas/min |")
    print("|---|---|---|")
    print(f"| frio (redeploy, L2 vazio) | {chamadas_frio} (evento único) | {pico_min_frio} |")
    print(f"| morno (delta universo, REAL: radar_daily 1x/dia útil) | {chamadas_dia_morno_real} | {pico_min_morno} |")
    print(f"| morno (LEITURA LITERAL do plano — NÃO observada no código, "
          f"cadência de scheduler {interval_scheduler_s}s) | {chamadas_dia_morno_literal} | {pico_min_morno} |")
    print(f"| opções (cadeias/dia={cadeias_dia}, custo/cadeia={custo_cadeia_1p}) | "
          f"{chamadas_dia_opcoes} | não limitado pelo código (achado de arquitetura — ver acima) |")

    total_dia = chamadas_frio + chamadas_dia_morno_real + chamadas_dia_opcoes
    total_pico_min = pico_min_frio + pico_min_morno  # opções fica de fora (sem número — ver achado)

    veredito_dia = _veredito(total_dia, quota_dia)
    veredito_pico = _veredito(total_pico_min, quota_min)
    veredito_geral = "NÃO CABE" if "NÃO CABE" in (veredito_dia, veredito_pico) else (
        veredito_dia if veredito_dia != "CABE" else veredito_pico)

    intervalo_min_seguro = _intervalo_minimo_seguro_s(quota_min)

    print("\n### Comparação contra a cota\n")
    print(f"- Cota da chave: **60/min · 2.000/dia** "
          f"(`mydata_budget.quota_min()`={quota_min}, `mydata_budget.quota_dia()`={quota_dia}).")
    print(f"- Soma dos três cenários (frio + morno REAL + opções), chamadas/dia: "
          f"**{total_dia}** de {quota_dia}/dia → **{veredito_dia}**.")
    print(f"- Soma do pico/min (frio + morno; opções sem número, ver achado acima): "
          f"**{total_pico_min}** de {quota_min}/min → **{veredito_pico}**.")
    print(f"- **VEREDITO: {veredito_geral}** (60/min · 2.000/dia)")
    print(f"- `intervaloMinimoSeguro`: {intervalo_min_seguro}s de espaçamento mínimo entre "
          f"chamadas reais ao mydata para manter o pico de qualquer janela de 60s dentro da "
          f"cota do minuto (hoje `scanner.MIN_FETCH_GAP_S`={SCANNER_MIN_FETCH_GAP_S}s — "
          f"dimensionado para Yahoo/brapi, não para o teto mais apertado do mydata).")

    return {
        "universoN": universo_n, "origemUniverso": origem,
        "custosUnitarios": {
            "cargaCheia1pag": custo_carga_1p, "cargaCheia3pag": custo_carga_3p,
            "delta1pag": custo_delta_1p, "delta3pag": custo_delta_3p,
            "cadeia1pag": custo_cadeia_1p, "cadeia3pag": custo_cadeia_3p,
        },
        "cenarios": {
            "frio": {"chamadasEvento": chamadas_frio, "picoMin": pico_min_frio},
            "mornoReal": {"chamadasDia": chamadas_dia_morno_real, "picoMin": pico_min_morno,
                          "ciclosDia": ciclos_dia_morno_real},
            "mornoLiteralPlano": {"chamadasDia": chamadas_dia_morno_literal, "picoMin": pico_min_morno,
                                  "ciclosDia": ciclos_dia_morno_literal, "intervalSchedulerS": interval_scheduler_s},
            "opcoes": {"chamadasDia": chamadas_dia_opcoes, "picoMin": pico_min_opcoes,
                       "cadeiasDia": cadeias_dia},
        },
        "quotaMin": quota_min, "quotaDia": quota_dia,
        "totalDia": total_dia, "totalPicoMin": total_pico_min,
        "veredito": veredito_geral, "veredictoDia": veredito_dia, "veredictoPico": veredito_pico,
        "intervaloMinimoSeguroS": intervalo_min_seguro,
    }


# ---------------------------------------------------------------------------
# Fase VIVO — rede real, só com --vivo explícito
# ---------------------------------------------------------------------------
async def fase_vivo(args) -> Optional[dict]:
    if not args.vivo:
        print("\nFase `vivo` pedida sem `--vivo` explícito — RECUSADA (T-09-18: nunca gasta "
              "cota da chave de produção por acidente). Rode com `--fases vivo --vivo` para "
              "confirmar o gasto (~10 chamadas com --amostra 5, ~0,5% da cota diária).")
        return None

    if not mydata_client.tem_token():
        print("\nERRO: MYDATA_TOKEN ausente no ambiente. A perna ao vivo não roda sem a chave "
              "de produção (prefixo público f00b4554; exporte a chave completa só no shell "
              "local — nunca commitar).")
        sys.exit(2)

    print(f"\n## Fase `vivo` — amostra de {args.amostra} tickers × 2 rotas, rede REAL\n")
    amostra = list(scanner.get_universe())[: max(1, args.amostra)]
    resultados = []
    quota_antes = dict(mydata_client.LAST_QUOTA)

    for t in amostra:
        for rota, path, params in (
            ("cotacoes", f"/v1/cotacoes/{t}", {"limite": 5}),
            ("opcoes/vencimentos", f"/v1/opcoes/{t}/vencimentos", {}),
        ):
            t0 = time.perf_counter()
            erro = None
            payload = {}
            try:
                payload = await mydata_client._fetch_json(path, params)
            except mydata_client.MydataIndisponivel as e:
                erro = str(e)
            except RuntimeError as e:  # token ausente/coerção — não deveria ocorrer aqui
                erro = str(e)
            ms = round((time.perf_counter() - t0) * 1000)
            linhas = payload.get("dados") if isinstance(payload, dict) else None
            linhas = linhas if isinstance(linhas, list) else []
            precos_presentes = (
                any(l.get("preco_fechamento") is not None for l in linhas)
                if rota == "cotacoes" and linhas else None
            )
            reg = {
                "ticker": t, "rota": rota, "ms": ms, "nLinhas": len(linhas),
                "precosPresentes": precos_presentes,
                "quotaLimite": mydata_client.LAST_QUOTA.get("X-Quota-Limite"),
                "quotaRestante": mydata_client.LAST_QUOTA.get("X-Quota-Restante"),
                "erro": erro,
            }
            resultados.append(reg)
            print(f"  {t:<7} {rota:<20} → {ms}ms  linhas={len(linhas)}  "
                  f"quotaRestante={reg['quotaRestante']}  "
                  f"precosPresentes={precos_presentes}  {erro or ''}")
            await asyncio.sleep(0.2)

    # GUARDA DE ESCOPO DE CHAVE (T-09-guard do plano): 200 com dados não
    # vazios mas preco_fechamento ausente em TODAS as linhas de cotações é o
    # sintoma documentado de chave sem `fonte:b3`, não ausência de dado.
    cotacoes_com_dado = [r for r in resultados if r["rota"] == "cotacoes" and r["nLinhas"] > 0]
    achado_escopo = None
    if cotacoes_com_dado and not any(r["precosPresentes"] for r in cotacoes_com_dado):
        achado_escopo = (
            "ACHADO: respostas 200 com linhas não vazias mas SEM preco_fechamento em nenhuma "
            "— sintoma documentado de chave sem escopo `fonte:b3` (contrato-consumidor.md), "
            "não ausência de dado.")
        print(f"\n{achado_escopo}")

    n_chamadas_feitas = len(resultados)
    quota_restante_final = mydata_client.LAST_QUOTA.get("X-Quota-Restante")
    reconciliacao = {
        "quotaAntes": quota_antes, "quotaDepois": dict(mydata_client.LAST_QUOTA),
        "chamadasFeitas": n_chamadas_feitas,
    }
    print(f"\nReconciliação: {n_chamadas_feitas} chamadas feitas nesta amostra. "
          f"X-Quota-Restante antes={quota_antes.get('X-Quota-Restante')} → "
          f"depois={quota_restante_final}.")

    return {
        "amostra": amostra, "resultados": resultados,
        "achadoEscopoChave": achado_escopo, "reconciliacao": reconciliacao,
    }


async def main():
    ap = argparse.ArgumentParser(
        description="Medição de volume de chamadas ao mydata: projeção offline + amostra ao vivo (--vivo).")
    ap.add_argument("--fases", default="projecao", help="projecao,vivo (default: projecao)")
    ap.add_argument("--vivo", action="store_true",
                     help="confirma explicitamente a fase `vivo` (gasta cota real da chave)")
    ap.add_argument("--amostra", type=int, default=5, help="tickers na amostra ao vivo (default 5)")
    ap.add_argument("--cadeias-dia", dest="cadeias_dia", type=int, default=200,
                     help="cadeias de opções abertas/dia no cenário de projeção (default 200)")
    ap.add_argument("--saida", default="", help="caminho para JSON bruto (opcional)")
    args = ap.parse_args()

    fases = [f.strip() for f in args.fases.split(",") if f.strip()]
    rel = {
        "quando_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fases": fases,
    }
    print(f"# Medição mydata (rate-limit) — {rel['quando_utc']}")

    if "projecao" in fases:
        rel["projecao"] = await fase_projecao(args)

    if "vivo" in fases:
        rel["vivo"] = await fase_vivo(args)

    if args.saida:
        with open(args.saida, "w") as f:
            json.dump(rel, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nJSON bruto: {args.saida}")


if __name__ == "__main__":
    asyncio.run(main())
