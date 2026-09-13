"""Fase 27 (decisão D1) — `GET /api/options/tecnico/{ticker}` pelo caminho
HTTP completo, OFFLINE.

O que este arquivo trava, em uma frase cada:

  · a rota responde os QUATRO blocos + carimbo, e a régua vem com sete
    pregões, o último marcado como hoje;
  · **custo ZERO de MCP, provado e não prometido** — uma bomba na porta ÚNICA
    de saída para o serviço (`mcp_client.call_tool`) explode se alguém puxar
    uma chamada paga para dentro desta rota. A bomba é na PORTA e não numa
    rota específica, de propósito: continua valendo se a chamada de cima
    mudar de nome;
  · `custoMcp: 0` viaja na resposta — é dele que a tela tira o rótulo
    "grátis" do controle, e sem ele o front inventaria o rótulo;
  · é o MESMO Snapshot Técnico Único de `/api/technicals/{ticker}` (mesmo
    `snapshotId`): se esses dois divergissem, a aba Opções e o painel técnico
    diriam coisas diferentes sobre o mesmo ativo no mesmo dia;
  · ticker sem histórico vira 502 com a mensagem do molde; ticker curto vira
    400 — nenhum dos dois vira 500, e nenhum dos dois inventa número.

Esqueleto de isolamento herdado de `test_fase3_proveniencia_technicals.py`
(B3_DB_PATH temporário + reset dos caches de candle/snapshot). Nenhum teste
toca rede: o histórico entra por monkeypatch de `candle_provider.get_history`.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import candle_cache, mcp_client, technical_snapshot


def _reset_caches():
    candle_cache.reset()
    technical_snapshot.reset()


@pytest.fixture(autouse=True)
def _isolado():
    _reset_caches()
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)
    _reset_caches()


def _client(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_opcoes_tecnico_rota_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _mk_candles(n=300):
    """Série longa o bastante para a SMA200 existir — é o que torna a régua
    `confiavel=True` e prova que a profundidade não veio da cauda."""
    return [{"date": "2026-01-01+%d" % i, "open": 10 + i * 0.1, "high": 10.2 + i * 0.1,
             "low": 9.8 + i * 0.1, "close": 10 + i * 0.1, "volume": 1_000_000}
            for i in range(n)]


def _com_historico(monkeypatch, main, candles=None, source="yahoo"):
    cs = _mk_candles() if candles is None else candles

    def _hist(_symbol, rng=None, **_kw):
        async def go():
            return {"candles": cs, "currency": "BRL", "source": source}
        return go()

    monkeypatch.setattr(main.candle_provider, "get_history", _hist)


# --------------------------------------------------------------------------- #
# 1) o contrato da resposta
# --------------------------------------------------------------------------- #

def test_rota_responde_os_quatro_blocos_e_o_carimbo(monkeypatch):
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    r = c.get("/api/options/tecnico/PETR4")
    assert r.status_code == 200, r.text
    b = r.json()
    for bloco in ("tendencia", "volatilidade", "niveis", "regua", "carimbo"):
        assert bloco in b, f"resposta sem o bloco {bloco}"
    assert b["t"] == "PETR4"
    assert b["carimbo"]["snapshotId"]
    assert b["carimbo"]["asOf"]
    assert b["carimbo"]["source"] == "yahoo"


def test_regua_vem_com_sete_pregoes_e_so_o_ultimo_e_hoje(monkeypatch):
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    regua = c.get("/api/options/tecnico/PETR4").json()["regua"]
    assert len(regua["itens"]) == 7
    assert [i["hoje"] for i in regua["itens"]] == [False] * 6 + [True]
    assert regua["motivo"] is None, "régua cheia não deveria carregar motivo"


def test_volatilidade_declara_a_unidade_na_resposta_http(monkeypatch):
    """O campo é contrato consumido pela tela: é por ele que o formatador é
    escolhido. O `hv21Pct` daqui é PERCENTUAL; o `hv21` do serviço de opções
    é FRAÇÃO, e os dois convivem no mesmo ecrã."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    v = c.get("/api/options/tecnico/PETR4").json()["volatilidade"]
    assert v["unidade"] == "pct"
    assert "hv21Pct" in v and "hv63Pct" in v


def test_tendencia_e_a_regua_concordam_sobre_hoje(monkeypatch):
    """**C7 pelo caminho HTTP.** O último segmento da régua e a linha de
    tendência são o MESMO dia — se divergirem, a tela mostra dois vereditos
    contraditórios lado a lado."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    b = c.get("/api/options/tecnico/PETR4").json()
    ultimo = b["regua"]["itens"][-1]
    for campo in ("regime", "direcao", "forca", "base", "confiavel"):
        assert ultimo[campo] == b["tendencia"][campo], f"divergência em {campo}"


# --------------------------------------------------------------------------- #
# 2) custo ZERO de MCP — provado, não prometido
# --------------------------------------------------------------------------- #

def test_a_rota_nao_chama_o_servico_de_opcoes(monkeypatch):
    """A bomba vai na porta ÚNICA de saída (`mcp_client.call_tool`), não numa
    rota específica: assim ela continua valendo se a chamada de cima mudar de
    nome. Se um dia alguém "enriquecer" esta leitura com um dado do serviço,
    o orçamento de chamadas passa a ser gasto por ABRIR a aba, sem clique de
    ninguém — exatamente o que o ADR-027 §3.3 proíbe."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)

    def _bomba(*a, **k):
        raise AssertionError("/api/options/tecnico chamou o serviço de opções")

    monkeypatch.setattr(mcp_client, "call_tool", _bomba)
    r = c.get("/api/options/tecnico/PETR4")
    assert r.status_code == 200, r.text
    assert r.json()["custoMcp"] == 0


def test_custo_mcp_e_fonte_viajam_na_resposta(monkeypatch):
    """`custoMcp: 0` é CONTRATO: é dele que sai o rótulo "grátis" do controle
    (SC-4). Com o custo na resposta, o front não precisa — nem pode — inventar
    o rótulo por conta própria."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    b = c.get("/api/options/tecnico/PETR4").json()
    assert b["custoMcp"] == 0
    assert b["fonte"] == "motor interno"
    assert b["degradado"] is False


def test_a_rota_le_o_mesmo_snapshot_que_technicals(monkeypatch):
    """Mesmo motor, mesmo `snapshotId`. Se estes dois divergissem, a aba
    Opções e o painel técnico afirmariam coisas diferentes sobre o mesmo ativo
    no mesmo dia — a contradição entre camadas que o STU existe para matar."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    tecnico = c.get("/api/options/tecnico/PETR4").json()
    painel = c.get("/api/technicals/PETR4").json()
    assert tecnico["carimbo"]["snapshotId"] == painel["snapshotId"]
    assert tecnico["carimbo"]["asOf"] == painel["snapshotAt"]


# --------------------------------------------------------------------------- #
# 3) estados de falha — declarados, nunca 500 e nunca inventados
# --------------------------------------------------------------------------- #

def test_ticker_sem_historico_vira_502_com_a_mensagem_do_molde(monkeypatch):
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main, candles=[])
    r = c.get("/api/options/tecnico/VALE3")
    assert r.status_code == 502, r.text
    assert "Sem historico para VALE3" in r.text


def test_ticker_curto_vira_400_antes_de_qualquer_fetch(monkeypatch):
    c, main = _client(monkeypatch)

    def _explode(*a, **k):
        raise AssertionError("a rota buscou histórico para um ticker inválido")

    monkeypatch.setattr(main.candle_provider, "get_history", _explode)
    r = c.get("/api/options/tecnico/AB")
    assert r.status_code == 400, r.text


def test_serie_curta_devolve_regua_curta_com_motivo_e_nao_500(monkeypatch):
    """Princípio 4 do CLAUDE.md pelo caminho HTTP: menos pregões e um motivo
    legível, nunca itens preenchidos nem erro opaco."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main, candles=_mk_candles(4))
    r = c.get("/api/options/tecnico/BBAS3")
    assert r.status_code == 200, r.text
    regua = r.json()["regua"]
    assert len(regua["itens"]) == 4
    assert regua["motivo"]


def test_rota_anonima_responde_sem_exigir_sessao(monkeypatch):
    """`current_scope` e não `require_user`, pela mesma razão de
    `/api/technicals/{ticker}`: é o MESMO dado de mercado público, e nenhum
    dado de conta viaja na resposta. Duas réguas de acesso para a mesma
    informação seriam o defeito."""
    c, main = _client(monkeypatch)
    _com_historico(monkeypatch, main)
    r = c.get("/api/options/tecnico/PETR4")  # sem Authorization
    assert r.status_code == 200, r.text
    assert "scope" not in r.json()
