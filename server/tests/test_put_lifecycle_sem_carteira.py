"""server/tests/test_put_lifecycle_sem_carteira.py — guardião do ciclo de
vida da sugestão de put (Fase 11, Plano 03, Task 1).

Materializa a decisão A-11-01 (`11-01-PLAN.md`): a simulação do ciclo de
vida vive inteiramente nas colunas de `put_suggestions`, nunca na carteira
real do usuário (`optionPositions`/`cash`/`history` — as mesmas três seções
que compõem a superfície exportada para o front). Prova por COMPORTAMENTO,
não por diff (D-10-M, mesma postura de `test_put_bridge_sem_superficie.py`
da Fase 10): monta uma carteira de verdade com `db.kv_set` DIRETO —
bypassando `store.buy_option`/`sell_option`/`close_option_vencida`/
`set_option_position` de propósito, para pegar qualquer via de escrita,
conhecida ou não (A-11-11) —, roda um ciclo de vida completo de 4 rodadas e
exige igualdade estrutural das três seções antes/depois. Também prova
ausência de estado inválido gravável (produto cartesiano de transições),
ausência de linha em limbo silencioso, e ausência de qualquer superfície
nova (rota, ranking do Radar).

Afrouxar ou apagar este arquivo é reverter PUTLIFE-02/PUT-03, não limpar
teste morto.
"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timedelta, timezone

import pytest

from app import candle_cache, db, put_lifecycle, put_suggestions, signal_ledger, store

RAIZ = pathlib.Path(__file__).resolve().parents[2]  # raiz do repositório


# --------------------------------------------------------------------------- #
# Helpers compartilhados (copiados do molde da Fase 10,
# `test_put_bridge_sem_superficie.py` — não importados entre arquivos de
# teste, esse não é o padrão local)
# --------------------------------------------------------------------------- #

def _sem_comentarios(texto: str, linguagem: str) -> str:
    """Remove comentários antes de contar ocorrências — sem isso o próprio
    comentário que explica a regra faria o teste passar/falhar sozinho
    (D-10-N). Heurística de linha (não um parser completo)."""
    linhas_saida: list[str] = []
    dentro_bloco = False
    for linha in texto.splitlines():
        if linguagem == "python":
            if dentro_bloco:
                pass
            m = re.search(r"(^|\s)#", linha)
            if m:
                linha = linha[: m.start()]
        elif linguagem == "js":
            if dentro_bloco:
                fim = linha.find("*/")
                if fim == -1:
                    linhas_saida.append("")
                    continue
                linha = linha[fim + 2 :]
                dentro_bloco = False
            m = re.search(r"(^|\s)//", linha)
            if m:
                linha = linha[: m.start()]
            linha = re.sub(r"/\*.*?\*/", "", linha)
            if "/*" in linha:
                idx = linha.find("/*")
                linha = linha[:idx]
                dentro_bloco = True
        linhas_saida.append(linha)
    return "\n".join(linhas_saida)


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


def _linha_valida(**overrides) -> dict:
    linha = {
        "user_id": "u1",
        "ticker": "PETR4",
        "data_pregao": "2026-08-28",
        "setup": "IFR2 (baixa)",
        "lado": "baixa",
        "contrato": "PETRR100",
        "strike": 34.5,
        "vencimento": "2026-09-19",
        "estilo_exercicio": "americano",
        "iv": 0.32,
        "delta": -0.42,
        "premio": None,
        "volume": 250,
        "spot": 36.2,
        "fonte": "mydata",
    }
    linha.update(overrides)
    return linha


def _registrar(conn, **overrides) -> int:
    assert put_suggestions.registrar(conn, _linha_valida(**overrides)) == 1
    return put_suggestions.listar(conn)[0]["id"]


def _popula_cache(ticker: str, candles: list, interval: str = "1d") -> None:
    candle_cache._CACHE[candle_cache._key(ticker, interval)] = {
        "candles": candles, "at": "2026-08-28T09:45:00Z",
    }


def _estado_atual(conn, linha_id: int) -> str:
    linha = next(l for l in put_suggestions.listar(conn) if l["id"] == linha_id)
    return linha["estado"]


@pytest.fixture(autouse=True)
def _cache_limpo():
    candle_cache.reset()
    yield
    candle_cache.reset()


# --------------------------------------------------------------------------- #
# Bloco A — leitura de fonte (estrutural)
# --------------------------------------------------------------------------- #

CAMINHO_PUT_LIFECYCLE = RAIZ / "server" / "app" / "put_lifecycle.py"
CAMINHO_PUT_SUGGESTIONS = RAIZ / "server" / "app" / "put_suggestions.py"
CAMINHO_AGENT = RAIZ / "server" / "app" / "agent.py"

TOKENS_A1 = ("buy_option", "sell_option", "close_option_vencida", "set_option_position", "optionPositions")
TOKENS_A3 = ("web/", "skill_ref", "defaults")
TOKENS_A4 = ("options_provider", "mydata_client", "candle_provider", "httpx", "B3_OPTIONS_PROVIDER")

PADRAO_IMPORT_STORE = re.compile(r"(^|\n)\s*(from \.store\b|from \. import store\b|import store\b)")


@pytest.mark.parametrize("caminho", [CAMINHO_PUT_LIFECYCLE, CAMINHO_PUT_SUGGESTIONS])
def test_a1_nenhuma_funcao_de_escrita_de_opcao_mencionada(caminho):
    texto = caminho.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, "python")
    achados = {tok: filtrado.count(tok) for tok in TOKENS_A1 if filtrado.count(tok) > 0}
    assert not achados, (
        f"PUTLIFE-02: {caminho.name} não pode mencionar função de escrita da "
        f"carteira real, nem em docstring — achado(s): {achados}"
    )


@pytest.mark.parametrize("caminho", [CAMINHO_PUT_LIFECYCLE, CAMINHO_PUT_SUGGESTIONS])
def test_a2_nenhum_import_de_store(caminho):
    texto = caminho.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, "python")
    assert not PADRAO_IMPORT_STORE.search(filtrado), (
        f"PUTLIFE-02: {caminho.name} não pode importar `store` — a carteira "
        f"real fica estruturalmente inalcançável a partir daqui"
    )


@pytest.mark.parametrize("caminho", [CAMINHO_PUT_LIFECYCLE, CAMINHO_PUT_SUGGESTIONS])
def test_a3_nenhuma_mencao_a_superficie_visivel(caminho):
    texto = caminho.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, "python")
    achados = {tok: filtrado.count(tok) for tok in TOKENS_A3 if filtrado.count(tok) > 0}
    assert not achados, (
        f"PUT-03 (extensão para módulos novos): {caminho.name} não pode "
        f"mencionar front/vocabulário visível — achado(s): {achados}"
    )


def test_a4_put_lifecycle_nao_menciona_fonte_de_rede():
    texto = CAMINHO_PUT_LIFECYCLE.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, "python")
    achados = {tok: filtrado.count(tok) for tok in TOKENS_A4 if filtrado.count(tok) > 0}
    assert not achados, (
        f"PUTLIFE: put_lifecycle.py não pode acessar rede nem ler o seletor "
        f"de provedor — achado(s): {achados}"
    )


def test_a5_agent_py_nao_ganha_telemetria_de_ciclo_de_vida():
    texto = CAMINHO_AGENT.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, "python")
    assert "putLifecycle" not in filtrado, (
        "PUTLIFE: agent.py não pode ganhar nenhuma chave de telemetria do "
        "ciclo de vida no snapshot de status"
    )


# --------------------------------------------------------------------------- #
# Bloco B — comportamento (a prova que importa)
# --------------------------------------------------------------------------- #

def test_b1_carteira_intocada_em_ciclo_completo(tmp_path):
    conn = _conn(tmp_path, "b1.db")
    uid = "u-carteira-real"

    cash_inicial = 8500.0
    positions_inicial = [{"ticker": "VALE3", "qty": 100, "avg": 68.5, "abertaEm": "20/08/2026 10:00"}]
    history_inicial = [
        {"date": "27/08/2026 10:00", "type": "COMPRA", "t": "VALE3", "kind": "acao",
         "qty": 100, "price": 68.5, "pnl": None, "origem": "manual"},
        {"date": "20/08/2026 09:30", "type": "VENDA", "t": "PETR4", "kind": "acao",
         "qty": 50, "price": 32.1, "pnl": 120.5, "origem": "manual"},
    ]
    option_positions_inicial = [{
        "id": "PETRR050", "underlying": "PETR4", "optionType": "put", "strike": 30.0,
        "expiration": "2026-10-17", "qty": 100, "avg": 1.05, "stop": None, "alvo": None,
        "abertaEm": "01/08/2026 09:00", "ivEntrada": 0.28, "deltaEntrada": -0.35, "hv21Entrada": 0.30,
    }]

    # Escrita DIRETA via db.kv_set — nunca store.buy_option/sell_option/etc
    # (A-11-11: prova sobre o ESTADO, pega qualquer via de escrita).
    db.kv_set(conn, "cash", cash_inicial, user_id=uid)
    db.kv_set(conn, "positions", positions_inicial, user_id=uid)
    db.kv_set(conn, "history", history_inicial, user_id=uid)
    db.kv_set(conn, "optionPositions", option_positions_inicial, user_id=uid)

    cash_antes = store.get(conn, "cash", user_id=uid)
    positions_antes = store.get(conn, "positions", user_id=uid)
    history_antes = store.get(conn, "history", user_id=uid)
    opcoes_antes = store.get(conn, "optionPositions", user_id=uid)
    cash_antes_json = json.dumps(cash_antes, sort_keys=True)
    positions_antes_json = json.dumps(positions_antes, sort_keys=True)
    history_antes_json = json.dumps(history_antes, sort_keys=True)
    opcoes_antes_json = json.dumps(opcoes_antes, sort_keys=True)

    linha_id = _registrar(
        conn, user_id=uid, ticker="PETR4", contrato="PETRR100",
        strike=34.5, vencimento="2026-09-19", premio=1.15,
    )

    _popula_cache("PETR4", [
        {"date": "2026-08-29", "close": 30.0},
        {"date": "2026-08-30", "close": 29.0},
        {"date": "2026-09-19", "close": 28.0},
    ])

    trajetoria = ["armada"]
    for data_rodada in ("2026-08-28", "2026-08-29", "2026-08-30", "2026-09-19"):
        ano, mes, dia = (int(p) for p in data_rodada.split("-"))
        put_lifecycle.run_diario(conn, now=datetime(ano, mes, dia, 12, 0, tzinfo=put_lifecycle.BRT))
        trajetoria.append(_estado_atual(conn, linha_id))

    # armada → executada_simulada → monitorada → monitorada (remarcação) → fechada
    assert trajetoria == ["armada", "executada_simulada", "monitorada", "monitorada", "fechada"]

    linha_final = next(l for l in put_suggestions.listar(conn) if l["id"] == linha_id)
    assert linha_final["precoFechamento"] == 6.5   # max(0, 34.5 - 28.0)
    assert linha_final["pnlPorAcao"] == 5.35        # round(6.5 - 1.15, 2)
    assert linha_final["motivoFechamento"] == "vencimento"

    cash_depois = store.get(conn, "cash", user_id=uid)
    positions_depois = store.get(conn, "positions", user_id=uid)
    history_depois = store.get(conn, "history", user_id=uid)
    opcoes_depois = store.get(conn, "optionPositions", user_id=uid)

    assert cash_depois == cash_antes
    assert positions_depois == positions_antes
    assert history_depois == history_antes
    assert opcoes_depois == opcoes_antes

    # Defesa extra contra igualdade frouxa por mutação in-place (A-11-11).
    assert json.dumps(cash_depois, sort_keys=True) == cash_antes_json
    assert json.dumps(positions_depois, sort_keys=True) == positions_antes_json
    assert json.dumps(history_depois, sort_keys=True) == history_antes_json
    assert json.dumps(opcoes_depois, sort_keys=True) == opcoes_antes_json


def test_b2_carteira_intocada_no_ramo_sem_execucao(tmp_path):
    conn = _conn(tmp_path, "b2.db")
    uid = "u-sem-execucao"

    cash_inicial = 5000.0
    positions_inicial = [{"ticker": "ITUB4", "qty": 200, "avg": 30.0}]
    history_inicial = [
        {"date": "15/08/2026 11:00", "type": "COMPRA", "t": "ITUB4", "kind": "acao",
         "qty": 200, "price": 30.0, "pnl": None, "origem": "manual"},
    ]
    option_positions_inicial = [{
        "id": "VALER100", "underlying": "VALE3", "optionType": "put", "strike": 60.0,
        "expiration": "2026-11-21", "qty": 100, "avg": 2.10, "stop": None, "alvo": None,
        "abertaEm": "10/08/2026 09:00", "ivEntrada": 0.31, "deltaEntrada": -0.40, "hv21Entrada": 0.33,
    }]

    db.kv_set(conn, "cash", cash_inicial, user_id=uid)
    db.kv_set(conn, "positions", positions_inicial, user_id=uid)
    db.kv_set(conn, "history", history_inicial, user_id=uid)
    db.kv_set(conn, "optionPositions", option_positions_inicial, user_id=uid)

    antes = {
        chave: json.dumps(store.get(conn, chave, user_id=uid), sort_keys=True)
        for chave in ("cash", "positions", "history", "optionPositions")
    }

    # `premio` ausente de propósito: nunca há entrada real, o ramo correto é
    # "vence sem uso", nunca inventa preço (princípio 4 do CLAUDE.md).
    linha_id = _registrar(
        conn, user_id=uid, ticker="BBAS3", contrato="BBASR050",
        strike=25.0, vencimento="2026-09-05", premio=None,
    )

    put_lifecycle.run_diario(conn, now=datetime(2026, 9, 5, 12, 0, tzinfo=put_lifecycle.BRT))

    linha = next(l for l in put_suggestions.listar(conn) if l["id"] == linha_id)
    assert linha["estado"] == "expirada_sem_uso"
    assert linha["pnlPorAcao"] is None

    depois = {
        chave: json.dumps(store.get(conn, chave, user_id=uid), sort_keys=True)
        for chave in ("cash", "positions", "history", "optionPositions")
    }
    assert depois == antes


def test_b3_nenhuma_linha_em_limbo_apos_rodada_mista(tmp_path):
    conn = _conn(tmp_path, "b3.db")
    agora = datetime.now(put_lifecycle.BRT)
    hoje_brt = agora.date().isoformat()
    ontem = (agora - timedelta(days=1)).date().isoformat()
    venc_futuro = (agora + timedelta(days=90)).date().isoformat()

    # Linha A: candle disponível -> avança HOJE (executada_simulada -> monitorada)
    id_a = _registrar(
        conn, user_id="u1", ticker="PETR4", contrato="PETRR200",
        data_pregao=hoje_brt, vencimento=venc_futuro,
    )
    assert put_suggestions.transicionar(conn, id_a, "executada_simulada", {"preco_entrada": 1.10}) == 1
    _popula_cache("PETR4", [{"date": ontem, "close": 30.0}])

    # Linha B: SEM candle disponível -> vira pendência, nunca some em silêncio
    id_b = _registrar(
        conn, user_id="u2", ticker="MGLU3", contrato="MGLUR050",
        data_pregao=hoje_brt, vencimento=venc_futuro,
    )
    assert put_suggestions.transicionar(conn, id_b, "executada_simulada", {"preco_entrada": 0.80}) == 1
    # nenhum candle populado para MGLU3 — cache fica vazio de propósito

    # Linha C: já terminal — nunca é lida por `listar_abertas`, não avança
    id_c = _registrar(
        conn, user_id="u3", ticker="VALE3", contrato="VALER100",
        data_pregao=hoje_brt, vencimento=hoje_brt,
    )
    assert put_suggestions.transicionar(conn, id_c, "executada_simulada", {"preco_entrada": 1.5}) == 1
    assert put_suggestions.transicionar(conn, id_c, "fechada", {
        "preco_fechamento": 0.0, "motivo_fechamento": "vencimento", "pnl_por_acao": -1.5,
    }) == 1

    put_lifecycle.run_diario(conn)  # sem `now`: usa o relógio real (hoje de verdade)

    hoje_utc = datetime.now(timezone.utc).date().isoformat()
    for linha in put_suggestions.listar(conn):
        avancou_hoje = isinstance(linha.get("estadoEm"), str) and linha["estadoEm"][:10] == hoje_utc
        tem_pendencia = linha.get("pendenteDesde") is not None
        eh_terminal = linha["estado"] in put_suggestions.TERMINAIS
        assert eh_terminal or avancou_hoje or tem_pendencia, (
            f"PUTLIFE-04: linha {linha['id']} (estado={linha['estado']}) "
            f"ficou em limbo silencioso — nem terminal, nem avançou hoje, "
            f"nem tem pendência datada"
        )

    linha_b_final = next(l for l in put_suggestions.listar(conn) if l["id"] == id_b)
    assert linha_b_final["estado"] == "executada_simulada"  # não avançou
    assert linha_b_final["pendenteDesde"] is not None        # mas está rastreada


def test_b4_transicoes_nao_declaradas_sao_recusadas_produto_cartesiano(tmp_path):
    conn = _conn(tmp_path, "b4.db")
    tickers_por_estado = {
        "armada": "PETR4",
        "expirada_sem_uso": "VALE3",
        "executada_simulada": "ITUB4",
        "monitorada": "BBDC4",
        "fechada": "ABEV3",
    }
    caminho_ate_estado = {
        "armada": (),
        "expirada_sem_uso": ("expirada_sem_uso",),
        "executada_simulada": ("executada_simulada",),
        "monitorada": ("executada_simulada", "monitorada"),
        "fechada": ("executada_simulada", "fechada"),
    }

    for origem in put_suggestions.ESTADOS:
        linha_id = _registrar(conn, ticker=tickers_por_estado[origem], contrato=f"C{origem[:8].upper()}")
        for passo in caminho_ate_estado[origem]:
            assert put_suggestions.transicionar(conn, linha_id, passo) == 1
        assert _estado_atual(conn, linha_id) == origem

        permitidos = put_suggestions.TRANSICOES.get(origem, ())
        for destino in put_suggestions.ESTADOS:
            if destino in permitidos:
                continue
            resultado = put_suggestions.transicionar(conn, linha_id, destino)
            assert resultado == 0, f"PUTLIFE-01: {origem} -> {destino} deveria ser recusado"
            assert _estado_atual(conn, linha_id) == origem, (
                f"PUTLIFE-01: estado mudou apesar da transição {origem} -> {destino} "
                f"ter sido recusada"
            )


def test_b4_estado_inexistente_e_recusado(tmp_path):
    conn = _conn(tmp_path, "b4b.db")
    linha_id = _registrar(conn, ticker="WEGE3", contrato="WEGER01")
    assert put_suggestions.transicionar(conn, linha_id, "estado_que_nao_existe") == 0
    assert _estado_atual(conn, linha_id) == "armada"


def test_b5_nenhuma_rota_nova_de_ciclo_de_vida():
    from app import main

    termos = ("lifecycle", "ciclo", "put")
    paths_suspeitos = [
        r.path for r in main.app.routes
        if any(termo in getattr(r, "path", "").lower() for termo in termos)
    ]
    assert not paths_suspeitos, (
        f"PUTLIFE: nenhuma rota pode servir o ciclo de vida da sugestão de "
        f"put — path(s) suspeito(s): {paths_suspeitos}"
    )


def test_b6_agregacoes_do_adr017_seguem_cegas_apos_ciclo_rodando(tmp_path):
    conn = _conn(tmp_path, "b6.db")

    linha_id = _registrar(conn, user_id="u1", ticker="PETR4", contrato="PETRR300", premio=1.15)
    put_lifecycle.run_diario(conn, now=datetime(2026, 8, 28, 12, 0, tzinfo=put_lifecycle.BRT))
    assert _estado_atual(conn, linha_id) == "executada_simulada"

    cumulativo = signal_ledger.agregar_cumulativo(conn)
    janela = signal_ledger.agregar_janela(conn, 2026)

    assert cumulativo.get("porSetup") == {}, (
        f"PUT-03/PUTLIFE: agregar_cumulativo não pode enxergar linha de put "
        f"com o ciclo de vida rodando — porSetup={cumulativo.get('porSetup')}"
    )
    assert janela.get("porSetup") == {}, (
        f"PUT-03/PUTLIFE: agregar_janela não pode enxergar linha de put com "
        f"o ciclo de vida rodando — porSetup={janela.get('porSetup')}"
    )
