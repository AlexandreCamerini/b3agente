"""Fase 27 (decisão D1) — a leitura técnica interna da aba Opções e a régua
de 7 pregões, testadas em SNAPSHOTS SINTÉTICOS montados à mão.

Nenhum teste deste arquivo toca rede, `candle_cache` ou o serviço de opções:
`opcoes_tecnico` é puro por desenho (recebe um snapshot já construído) e é
justamente essa pureza que torna a régua testável índice a índice.

O QUE ESTES GUARDIÕES REPROVAM, em uma frase cada:

  · **C7 — dois vereditos contraditórios sobre o mesmo dia.** O último
    segmento da régua tem de ser IDÊNTICO ao `regime.classificar(snap)` que a
    linha de tendência mostra logo acima. A armadilha concreta: passar `i + 1`
    como profundidade de histórico faria TODOS os sete segmentos caírem em
    `base="sma50"`/`confiavel=False` (a cauda do STU tem ~126 velas, o filtro
    de SMA200 exige 200), enquanto a linha de cima — que lê a série inteira,
    com `candlesAvailable` de ~500 — diria `sma200`/`confiavel=True`. Mesma
    função, mesmo dia, mesma tela, dois vereditos.

  · **A régua que repete o último valor sete vezes.** O par ADX-alto ×
    ADX-baixo e o teste de série variável provam que cada segmento lê o SEU
    índice, e não o resumo de hoje sete vezes.

  · **O erro de 10× em silêncio.** `unidade` é contrato, não anotação: ela
    sai SEMPRE, inclusive quando os valores são `None`. O `hv21Pct` do
    `technical_models` está em PERCENTUAL; o `hv21` que o serviço de opções
    devolve está em FRAÇÃO, e os dois convivem na mesma tela.

  · **Princípio 4 do CLAUDE.md.** Insumo ausente vira `None` com `motivo`
    legível — nunca `0`, nunca `"lateral"` por default.
"""
from __future__ import annotations

import pytest

from app import opcoes_tecnico, regime


# --------------------------------------------------------------------------- #
# fábrica de snapshot sintético
# --------------------------------------------------------------------------- #

def _serie(valor, n: int) -> list:
    """Série de `n` posições: escalar vira constante, lista vem como está."""
    if isinstance(valor, (list, tuple)):
        return list(valor)
    return [valor] * n


def _snap(n: int = 7, *, disponivel=500, closes=None, sma200=30.0, sma50=32.0,
          adx=30.0, volatility="default", levels="default", history_stats=True,
          carimbo=True) -> dict:
    """Snapshot mínimo com as MESMAS chaves que `technical_snapshot.build`
    garante — e só elas. Ausência é declarada por argumento (`None`), nunca
    por omissão acidental."""
    closes = closes if closes is not None else [35.0 + i for i in range(n)]
    candles = [
        {"date": "2026-09-%02d" % (i + 1), "open": c, "high": c + 1.0,
         "low": c - 1.0, "close": c, "volume": 1_000_000}
        for i, c in enumerate(closes)
    ]
    ind = {
        "sma200": _serie(sma200, n),
        "sma50": _serie(sma50, n),
        "adx14": _serie(adx, n),
    }
    ctx: dict = {}
    if history_stats:
        ctx["historyStats"] = {"candlesAvailable": disponivel}
    if volatility == "default":
        volatility = {"atr14": 0.85, "atr14Pct": 2.1, "hv21Pct": 31.4,
                      "hv63Pct": 28.0, "bollingerUpper": 41.0,
                      "bollingerLower": 33.0}
    if volatility is not None:
        ctx["volatility"] = volatility
    if levels == "default":
        levels = {"supports": [33.2, 31.0], "resistances": [41.0],
                  "nearestSupport": 33.2, "nearestResistance": 41.0,
                  "distanceToSupportPct": 4.1, "distanceToResistancePct": 3.9}
    if levels is not None:
        ctx["levels"] = levels
    snap = {
        "ticker": "PETR4",
        "candles": candles,
        "indicators": ind,
        "summary": {
            "sma20": 34.0,
            "sma50": ind["sma50"][-1],
            "sma200": ind["sma200"][-1],
            "adx14": ind["adx14"][-1],
        },
        "close": candles[-1]["close"],
        "context": ctx,
    }
    if carimbo:
        snap.update({
            "snapshotId": "a1b2c3d4",
            "asOf": candles[-1]["date"],
            "generatedAt": "2026-09-13T10:00:00",
            "source": "yahoo",
            "cacheStatus": "fresh",
        })
    return snap


# --------------------------------------------------------------------------- #
# 1) a constante e a forma da régua
# --------------------------------------------------------------------------- #

def test_pregoes_da_regua_e_sete():
    """Uma semana de pregões é a menor janela em que "a volatilidade subiu ou
    desabou" é visível (D4). O número solto de hoje não responde isso."""
    assert opcoes_tecnico.PREGOES_DA_REGUA == 7


def test_regua_devolve_sete_itens_do_mais_antigo_para_hoje():
    r = opcoes_tecnico.regua(_snap(40))
    itens = r["itens"]
    assert len(itens) == 7
    datas = [i["data"] for i in itens]
    assert datas == sorted(datas), "a régua tem de sair do mais antigo para o mais recente"
    assert datas[-1] == _snap(40)["candles"][-1]["date"]


def test_so_o_ultimo_item_e_hoje():
    itens = opcoes_tecnico.regua(_snap(40))["itens"]
    assert [i["hoje"] for i in itens] == [False] * 6 + [True]


def test_cada_item_tem_o_contrato_completo():
    for item in opcoes_tecnico.regua(_snap(40))["itens"]:
        for campo in ("data", "regime", "direcao", "forca", "confiavel", "hoje"):
            assert campo in item, f"item da régua sem o campo {campo}"


def test_todo_regime_da_regua_pertence_a_regime_REGIMES():
    """Nenhum rótulo inventado: a régua alimenta `regime.classificar`, ela não
    tem vocabulário próprio."""
    variado = [8.0, 12.0, 19.0, 21.0, 24.0, 27.0, 33.0]
    itens = opcoes_tecnico.regua(_snap(7, adx=variado))["itens"]
    assert {i["regime"] for i in itens} <= set(regime.REGIMES)


# --------------------------------------------------------------------------- #
# 2) C7 — a régua e a linha de tendência nunca se contradizem
# --------------------------------------------------------------------------- #

def test_ultimo_item_da_regua_e_identico_ao_classificar_do_snapshot():
    """**C7.** Se estes dois divergirem, a tela mostra dois vereditos sobre o
    MESMO dia, vindos da MESMA função. É pior do que não mostrar régua."""
    snap = _snap(126, disponivel=500)
    hoje = regime.classificar(snap)
    ultimo = opcoes_tecnico.regua(snap)["itens"][-1]
    for campo in ("regime", "direcao", "forca", "base", "confiavel"):
        assert ultimo[campo] == hoje[campo], (
            f"régua e linha de tendência discordam em {campo}: "
            f"{ultimo[campo]!r} × {hoje[campo]!r}"
        )


def test_profundidade_vem_de_candles_available_e_nao_do_indice_na_cauda():
    """**Não-vacuidade de C7.** `snap["indicators"]` é a CAUDA (126 velas do
    período padrão); `candlesAvailable` conta a série INTEIRA buscada (o
    `FETCH_RANGE` é fixo em 2y). Passar `i + 1` daria 120–126 de profundidade
    para os sete segmentos — abaixo de `MIN_CANDLES_SMA200` — e TODOS
    cairiam em `sma50`/`confiavel=False`. Trocar a fórmula de volta faz este
    teste falhar."""
    snap = _snap(126, disponivel=500)
    itens = opcoes_tecnico.regua(snap)["itens"]
    assert itens[-1]["confiavel"] is True
    assert itens[-1]["base"] == "sma200"
    assert all(i["base"] == "sma200" for i in itens), (
        "algum segmento degradou para sma50 apesar de ~500 pregões de histórico"
    )


def test_profundidade_decresce_um_por_pregao_recuado():
    """A profundidade de um pregão anterior é a de hoje menos os pregões que
    vieram depois — medida, nunca inventada. Com 202 velas disponíveis, os
    segmentos mais antigos cruzam para baixo do piso da SMA200."""
    snap = _snap(126, disponivel=202)
    itens = opcoes_tecnico.regua(snap)["itens"]
    # hoje=202, ontem=201, anteontem=200 → sma200; 199 e abaixo → sma50.
    assert [i["base"] for i in itens] == ["sma50"] * 4 + ["sma200"] * 3
    assert [i["confiavel"] for i in itens] == [False] * 4 + [True] * 3


# --------------------------------------------------------------------------- #
# 3) a régua lê o índice certo de cada série (e não o resumo de hoje 7×)
# --------------------------------------------------------------------------- #

def test_adx_acima_do_limiar_produz_tendencia_alta_no_ultimo_item():
    snap = _snap(20, sma200=30.0, adx=31.0)   # close 35+ > sma200 → alta
    assert opcoes_tecnico.regua(snap)["itens"][-1]["regime"] == "tendencia_alta"


def test_adx_abaixo_do_limiar_produz_lateral_no_ultimo_item():
    """MESMO snapshot, só o ADX muda. É o par que reprova a régua que repete
    `classificar(snap)` sete vezes — ela passaria nos dois testes acima
    isoladamente, mas não no de série variável abaixo."""
    snap = _snap(20, sma200=30.0, adx=11.0)
    assert opcoes_tecnico.regua(snap)["itens"][-1]["regime"] == "lateral"


def test_serie_variavel_produz_segmentos_DIFERENTES():
    """**Não-vacuidade.** Trocar o corpo da régua por "repete
    `classificar(snap)` sete vezes" faz os sete itens ficarem idênticos, e
    este teste falha."""
    variado = [8.0, 9.0, 10.0, 11.0, 30.0, 31.0, 32.0]
    itens = opcoes_tecnico.regua(_snap(7, sma200=30.0, adx=variado))["itens"]
    assert [i["regime"] for i in itens] == (
        ["lateral"] * 4 + ["tendencia_alta"] * 3
    )
    assert len({i["regime"] for i in itens}) == 2


# --------------------------------------------------------------------------- #
# 4) degradação declarada — princípio 4 do CLAUDE.md
# --------------------------------------------------------------------------- #

def test_serie_curta_devolve_menos_itens_e_motivo_nao_nulo():
    """Menos de 7 pregões fechados: itens a menos, NUNCA itens preenchidos."""
    leitura = opcoes_tecnico.leitura(_snap(3))
    assert len(leitura["regua"]["itens"]) == 3
    assert leitura["regua"]["motivo"], "régua curta sem motivo é ausência sem explicação"


def test_indice_sem_sma_e_sem_adx_sai_indefinido_e_nao_confiavel():
    """A `classificar` já degrada assim; a régua não corrige nem esconde."""
    itens = opcoes_tecnico.regua(_snap(7, sma200=None, sma50=None, adx=None))["itens"]
    assert all(i["regime"] == "indefinido" for i in itens)
    assert all(i["confiavel"] is False for i in itens)
    assert all(i["direcao"] is None and i["forca"] is None for i in itens)


def test_sem_candles_a_regua_nao_inventa_itens():
    snap = _snap(7)
    snap["candles"] = []
    r = opcoes_tecnico.regua(snap)
    assert r["itens"] == []
    assert r["motivo"]


def test_pregao_sem_fechamento_e_pulado_e_entra_no_motivo():
    snap = _snap(7)
    snap["candles"][2]["close"] = None
    r = opcoes_tecnico.regua(snap)
    assert len(r["itens"]) == 6, "pregão sem fechamento foi PREENCHIDO em vez de pulado"
    assert r["motivo"]
    assert snap["candles"][2]["date"] not in [i["data"] for i in r["itens"]]


def test_candles_available_ausente_vira_motivo_e_nao_profundidade_inventada():
    """Sem `historyStats`, a profundidade viaja como `None` — a `classificar`
    já trata "não sei" como "use a SMA200 se houver". O que NÃO se faz é
    inventar um número."""
    r = opcoes_tecnico.regua(_snap(30, history_stats=False))
    assert len(r["itens"]) == 7
    assert r["motivo"], "profundidade desconhecida tem de ser declarada"
    assert all(i["base"] == "sma200" for i in r["itens"])


# --------------------------------------------------------------------------- #
# 5) leitura() — os quatro blocos e o carimbo
# --------------------------------------------------------------------------- #

def test_leitura_tem_os_quatro_blocos_e_o_carimbo():
    l = opcoes_tecnico.leitura(_snap(30))
    assert set(l) == {"tendencia", "volatilidade", "niveis", "regua", "carimbo"}


def test_tendencia_e_o_classificar_inteiro_mais_as_medias():
    snap = _snap(30)
    t = opcoes_tecnico.leitura(snap)["tendencia"]
    hoje = regime.classificar(snap)
    for campo, valor in hoje.items():
        assert t[campo] == valor, f"tendência divergiu de classificar em {campo}"
    assert t["medias"]["sma200"] == snap["summary"]["sma200"]
    assert t["medias"]["sma50"] == snap["summary"]["sma50"]


def test_volatilidade_e_lida_do_contexto_sem_recalcular():
    snap = _snap(30)
    v = opcoes_tecnico.leitura(snap)["volatilidade"]
    assert v["hv21Pct"] == snap["context"]["volatility"]["hv21Pct"]
    assert v["hv63Pct"] == snap["context"]["volatility"]["hv63Pct"]
    assert v["atr14Pct"] == snap["context"]["volatility"]["atr14Pct"]
    assert v["motivo"] is None


def test_unidade_pct_esta_sempre_presente_inclusive_sem_volatilidade():
    """**Contrato, não anotação.** É por este campo que o 27-04 escolhe o
    formatador: o `hv21Pct` daqui é PERCENTUAL, o `hv21` do serviço de opções
    é FRAÇÃO, e os dois aparecem no mesmo ecrã. Um bloco sem `unidade` faria
    a tela adivinhar — é assim que se erra 10× em silêncio."""
    com = opcoes_tecnico.leitura(_snap(30))["volatilidade"]
    sem = opcoes_tecnico.leitura(_snap(30, volatility=None))["volatilidade"]
    assert com["unidade"] == "pct"
    assert sem["unidade"] == "pct"
    assert sem["hv21Pct"] is None and sem["hv63Pct"] is None
    assert sem["motivo"], "volatilidade ausente sem motivo é 'não sei' calado"


def test_volatilidade_ausente_nunca_vira_zero():
    """Princípio 4: travessão com motivo, nunca 0."""
    v = opcoes_tecnico.leitura(_snap(30, volatility={}))["volatilidade"]
    assert v["hv21Pct"] is None
    assert v["hv21Pct"] != 0
    assert v["motivo"]


def test_niveis_saem_verbatim_do_contexto():
    snap = _snap(30)
    assert opcoes_tecnico.leitura(snap)["niveis"] == snap["context"]["levels"]


def test_niveis_ausentes_viram_none_com_motivo():
    n = opcoes_tecnico.leitura(_snap(30, levels=None))["niveis"]
    assert n["nearestSupport"] is None and n["nearestResistance"] is None
    assert n["motivo"]


def test_carimbo_traz_proveniencia_e_horario():
    snap = _snap(30)
    c = opcoes_tecnico.leitura(snap)["carimbo"]
    assert c["snapshotId"] == snap["snapshotId"]
    assert c["asOf"] == snap["asOf"]
    assert c["generatedAt"] == snap["generatedAt"]
    assert c["source"] == snap["source"]
    assert c["cacheStatus"] == snap["cacheStatus"]


def test_carimbo_sem_snapshot_id_declara_o_motivo():
    l = opcoes_tecnico.leitura(_snap(30, carimbo=False))
    assert l["carimbo"]["snapshotId"] is None
    assert l["carimbo"]["motivo"]


def test_leitura_de_snapshot_vazio_nao_explode():
    """Rota que degrada, não rota que cai em 500."""
    l = opcoes_tecnico.leitura({})
    assert l["regua"]["itens"] == []
    assert l["regua"]["motivo"]
    assert l["volatilidade"]["unidade"] == "pct"
    assert l["tendencia"]["regime"] == "indefinido"


# --------------------------------------------------------------------------- #
# 6) fronteira do módulo
# --------------------------------------------------------------------------- #

def test_modulo_nao_importa_rede_nem_o_servico_de_opcoes():
    """`opcoes_tecnico` nasce PURO e fica puro: sem `httpx`, sem `mcp`, sem
    `mcp_client`, sem `candle_provider`. Custo zero não é promessa da
    docstring — é propriedade do grafo de imports."""
    import ast
    import pathlib

    fonte = pathlib.Path(opcoes_tecnico.__file__).read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.module:
                importados.add(no.module.split(".")[0])
            importados.update(a.name for a in no.names)
    proibidos = {"httpx", "httpx2", "mcp", "mcp_client", "requests", "asyncio",
                 "candle_provider", "candle_cache", "options_mcp_api", "main"}
    assert not (importados & proibidos), (
        f"opcoes_tecnico deixou de ser puro: importa {sorted(importados & proibidos)}"
    )


@pytest.mark.parametrize("chamada", [opcoes_tecnico.regua, opcoes_tecnico.leitura])
def test_funcoes_nao_mutam_o_snapshot_recebido(chamada):
    """O snapshot é cacheado por fingerprint em `technical_snapshot` — mutá-lo
    contaminaria o Radar e a Watchlist, que leem o MESMO objeto."""
    import copy

    snap = _snap(30)
    antes = copy.deepcopy(snap)
    chamada(snap)
    assert snap == antes
