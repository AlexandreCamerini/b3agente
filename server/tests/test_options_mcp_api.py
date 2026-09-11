"""aba-opcoes F3 — as quatro rotas novas (`/cadeia`, `/operaveis`,
`POST /proposta`, `POST /possibilidades`) pelo caminho HTTP completo, OFFLINE.

O que este arquivo trava, em uma frase cada:
  - rota anônima não toca o serviço (o teto de 2.000/dia é do SERVIDOR);
  - `options`/`matched`/`returned`/`truncated` viajam VERBATIM — engolir o
    `truncated` faria a tela afirmar sobre a cadeia inteira tendo visto metade;
  - pedido torto (`kind`, `limit`, `lote`, tese ausente) é 422 ANTES da rede;
  - `/operaveis` manda o critério do BORIS ao serviço e o declara na resposta;
  - tool que não anexa frescor responde `medido: false` — "não medido" nunca
    pode passar por "em dia" (ADR-027, Decisão 8);
  - `setups: []` com `reason` é 200 com o motivo byte a byte, não erro;
  - `/possibilidades` gasta exatamente 2×N+1, e `chamadasPrevistas` diz o
    mesmo número que a UI mostra antes de disparar;
  - vencimento que não monta NÃO gasta a segunda chamada;
  - cota que só cobre a primeira etapa recusa depois dela e antes de avaliar;
  - o reservado e não consumido VOLTA (senão duas consultas por cache produzem
    um falso "cota esgotada" — a classe do achado A-07);
  - `emReais` multiplica pelo lote, preserva `null` e NÃO conhece breakeven,
    que segue em preço do objeto;
  - serviço fora do ar no meio do laço é 503, não 200 parcial; erro de tool em
    UM vencimento não apaga os outros.

Isolamento e esqueleto herdados de `test_options_mcp_leitura.py` (B3_DB_PATH
temporário + reset dos caches em memória). Nenhum teste depende de rede nem de
credencial real.
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import pathlib
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, mcp_client, metering, options_mcp_api


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed

    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    mcp_client.reset_cache()
    for env in ("B3_MCP_COTA_USUARIO_DIA", "B3_MCP_RATE_MIN",
                "B3_MCP_COTA_GLOBAL_DIA", "MCP_URL"):
        monkeypatch.delenv(env, raising=False)
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    mcp_client.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_mcp_api_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email="dono@teste.com", senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _usado(main, uid):
    return metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp())


def _reservado(main, uid):
    return metering.reservado(main._conn, uid, section="mcpUsage",
                              _dia=options_mcp_api._dia_sp())


# ------------------------------------------------------------- payloads ---
_VENCIMENTOS = ["2026-09-19", "2026-10-17", "2026-11-21"]

_CADEIA = {
    "ticker": "PETR4", "trading_date": "2026-08-28", "underlying_price": 38.42,
    "matched": 84, "returned": 2,
    "options": [
        {"contrato": "PETRI380", "tipo": "CALL", "strike": 38.0, "premio": 1.2,
         "delta": 0.62, "total_negocios": 412, "dt_vencimento": "2026-09-19",
         "dt_pregao": "2026-08-28", "preco_objeto": 38.42},
        {"contrato": "PETRI400", "tipo": "CALL", "strike": 40.0, "premio": 0.58,
         "delta": 0.34, "total_negocios": 208, "dt_vencimento": "2026-09-19",
         "dt_pregao": "2026-08-28", "preco_objeto": 38.42},
    ],
    "truncated": ("82 contratos ficaram de fora; peça um vencimento específico "
                  "ou aumente o limite"),
    "data_freshness": {"quotes": "em_dia", "quotes_age_hours": 12,
                       "instrument_registry": "em_dia"},
}

_OPERAVEIS = {
    "ticker": "PETR4", "trading_date": "2026-08-28",
    "criteria": "delta entre 0,25 e 0,55 e ao menos 100 negócios no pregão",
    "options": [_CADEIA["options"][0]],
    "excluded": 71,
    "note": "contratos sem negócio no pregão não entram na lista",
}

_BASE = {
    "ticker": "PETR4", "trading_date": "2026-08-28", "underlying_price": 38.42,
    "behavior": {"trend": "alta", "rsi14": 58.2, "close": 38.42},
    "catalog": [{"kind": "trava_de_alta", "name": "Trava de alta",
                 "thesis": ["alta moderada"], "summary": "risco limitado",
                 "risk": "perde o prêmio"}],
    "expirations": list(_VENCIMENTOS),
    "next_step": "escolha um vencimento",
}

# A avaliação é a MESMA fixture do teste de paridade — números derivados de
# `opcoes_payoff`, internamente coerentes. Reusá-la aqui garante que o que a
# rota repassa é a forma que o outro guardião compara campo a campo.
_AVALIACAO = json.loads(
    (pathlib.Path(__file__).resolve().parent / "fixtures" /
     "mcp_evaluate_petr4.json").read_text(encoding="utf-8"))


def _setup(vencimento: str) -> dict:
    return {
        "kind": "trava_de_alta", "name": f"trava de alta {vencimento}",
        "expiration": vencimento,
        "legs": [
            {"contract": "PETRI380", "side": "buy", "quantity": 1,
             "kind": "CALL", "strike": 38.0, "premium": 1.2, "delta": 0.62},
            {"contract": "PETRI400", "side": "sell", "quantity": 1,
             "kind": "CALL", "strike": 40.0, "premium": 0.58, "delta": 0.34},
        ],
        "net_cost": 0.62, "flow": "debit", "max_gain": 1.38, "max_loss": 0.62,
        "unlimited_gain": False, "unlimited_loss": False, "breakevens": [38.62],
    }


def _proposta(vencimento) -> dict:
    return {"ticker": "PETR4", "trading_date": "2026-08-28",
            "underlying_price": 38.42, "direction": "bullish", "kind": None,
            "setups": [_setup(vencimento or _VENCIMENTOS[0])],
            "note": "prêmios do fechamento do pregão anterior"}


def _roteador(*, base=None, com_tese=None, por_vencimento=None, avaliacao=None):
    """Despacha pelo NOME da tool E pela FORMA do pedido.

    `propose_option_setups` tem duas formas no contrato — sem tese devolve
    catálogo e vencimentos; com tese devolve estruturas — e metade das
    afirmações deste arquivo é justamente sobre qual das duas aconteceu.
    Espião que despacha só por nome não conseguiria distingui-las.
    """
    base = _BASE if base is None else base
    por_vencimento = por_vencimento or {}
    avaliacao = _AVALIACAO if avaliacao is None else avaliacao

    def _rota(nome, args):
        args = args or {}
        if nome == "propose_option_setups":
            if not args.get("direction") and not args.get("kind"):
                return base
            venc = args.get("expiration")
            if venc in por_vencimento:
                return por_vencimento[venc]
            return _proposta(venc) if com_tese is None else com_tese
        if nome == "evaluate_option_structure":
            return avaliacao
        if nome == "get_option_chain":
            return _CADEIA
        if nome == "find_tradable_options":
            return _OPERAVEIS
        return {}

    return _rota


def _espiao(monkeypatch, roteador=None, cache: bool = False):
    """Substitui `mcp_client.call_tool` e registra `(nome, args)` de cada
    chamada. Valor `Exception` é levantado; qualquer outro vira `dados`."""
    roteador = _roteador() if roteador is None else roteador
    chamadas: list = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        v = roteador(nome, args)
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, cache)

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


def _nomes(chamadas):
    return [n for n, _a in chamadas]


def _corpo_possibilidades(**extra):
    return dict({"ticker": "PETR4", "direction": "bullish", "lote": 100}, **extra)


# ══════════════════════════════════════════════════════════════════ 401 ═══
def test_as_quatro_rotas_sem_sessao_sao_401_antes_da_rede(monkeypatch):
    """O teto de 2.000 chamadas/dia é do SERVIDOR: rota anônima aqui deixa
    qualquer um queimar a cota de toda a base."""
    c, _ = _client(monkeypatch)
    chamadas = _espiao(monkeypatch)

    assert c.get("/api/options/mcp/cadeia/PETR4").status_code == 401
    assert c.get("/api/options/mcp/operaveis/PETR4").status_code == 401
    assert c.post("/api/options/mcp/proposta",
                  json={"ticker": "PETR4", "direction": "bullish"}).status_code == 401
    assert c.post("/api/options/mcp/possibilidades",
                  json=_corpo_possibilidades()).status_code == 401
    assert chamadas == [], "rota anônima chegou a tocar o serviço"


# ═══════════════════════════════════════════════════════════════ cadeia ═══
def test_cadeia_devolve_cadeia_e_truncado_verbatim_com_frescor_medido(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)

    r = c.get("/api/options/mcp/cadeia/petr4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()

    assert corpo["opcoes"] == _CADEIA["options"], "a rota mexeu na cadeia"
    assert corpo["encontrados"] == 84 and corpo["retornados"] == 2
    assert corpo["truncado"] == _CADEIA["truncated"], (
        "o aviso de truncamento foi engolido — sem ele a tela afirma sobre a "
        "cadeia inteira tendo visto uma parte")
    assert corpo["ticker"] == "PETR4", "ticker minúsculo na URL não foi normalizado"
    assert corpo["pregao"] == "2026-08-28"
    assert corpo["precoObjeto"] == 38.42
    assert corpo["fonte"] == "mcp.semente.dev"
    assert corpo["at"].endswith(" BRT")

    # `get_option_chain` ANEXA `data_freshness`: aqui o frescor é medido de
    # verdade, com a idade que o serviço mandou — não um 0 de consolação.
    assert corpo["frescor"]["medido"] is True
    assert corpo["frescor"]["bloqueia"] is False
    assert corpo["frescor"]["classes"][0]["idadeHoras"] == 12

    # chave omitida ≠ chave com `None`: `expiration: None` seria um filtro
    # nulo explícito, que não é o mesmo que "todos os vencimentos"
    assert chamadas == [("get_option_chain", {"ticker": "PETR4", "limit": 50})]
    assert _usado(main, uid) == 1


def test_cadeia_repassa_filtros_normalizados(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    r = c.get("/api/options/mcp/cadeia/PETR4?kind=call&expiration=2026-09-19&limit=10",
              headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert chamadas[0][1] == {"ticker": "PETR4", "limit": 10,
                              "expiration": "2026-09-19", "kind": "CALL"}


@pytest.mark.parametrize("query,code", [
    ("kind=banana", "kind_invalido"),
    ("limit=0", "limite_invalido"),
    ("limit=999", "limite_invalido"),
])
def test_cadeia_com_pedido_torto_e_422_antes_da_rede(monkeypatch, query, code):
    """Recusar cedo é o mesmo princípio do `_cap_check`: pedido que o serviço
    recusaria não pode custar uma chamada do teto compartilhado."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)

    r = c.get(f"/api/options/mcp/cadeia/PETR4?{query}", headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == code
    assert chamadas == [], "pedido inválido tocou o serviço"
    assert _usado(main, uid) == 0 and _reservado(main, uid) == 0


# ════════════════════════════════════════════════════════════ operáveis ═══
def test_operaveis_manda_o_criterio_do_boris_e_o_declara_na_resposta(monkeypatch):
    """D-24.4: `min_trades`/`delta_min`/`delta_max` são escolha do BORIS, não
    do serviço. Número escondido vira "a peneira sumiu com o meu strike" sem
    ninguém conseguir explicar por quê."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    r = c.get("/api/options/mcp/operaveis/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()

    nome, args = chamadas[0]
    assert nome == "find_tradable_options"
    assert args["min_trades"] == 100
    assert args["delta_min"] == 0.25
    assert args["delta_max"] == 0.55

    assert corpo["criterioAplicado"] == {"minNegocios": 100, "deltaMin": 0.25,
                                         "deltaMax": 0.55}
    assert corpo["criterio"] == _OPERAVEIS["criteria"], "critério do serviço reescrito"
    assert corpo["opcoes"] == _OPERAVEIS["options"]
    assert corpo["excluidos"] == 71
    assert corpo["nota"] == _OPERAVEIS["note"]


def test_operaveis_declara_frescor_nao_medido(monkeypatch):
    """`find_tradable_options` não anexa `data_freshness`. "Não medido" tem de
    aparecer como não medido: silêncio aqui é lido como "em dia" por quem
    olha (ADR-027, Decisão 8)."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)

    corpo = c.get("/api/options/mcp/operaveis/PETR4",
                  headers=_auth(p["token"])).json()
    assert corpo["frescor"]["medido"] is False
    assert corpo["frescor"]["bloqueia"] is True
    assert corpo["frescor"]["warning"] == options_mcp_api.AVISO_FRESCOR_SEM_ANEXO
    assert corpo["frescor"]["classes"] == []


# ════════════════════════════════════════════════════════════ proposta ════
def test_proposta_sem_tese_e_422_antes_da_rede(monkeypatch):
    """O serviço não escolhe direção, e esta camada menos ainda — devolver uma
    estrutura qualquer seria o app decidindo por quem opera."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    r = c.post("/api/options/mcp/proposta", json={"ticker": "PETR4"},
               headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "tese_ausente"
    assert chamadas == [], "pedido sem tese tocou o serviço"


def test_proposta_sem_estrutura_e_200_com_motivo_verbatim(monkeypatch):
    """[R-15]: cadeia que não preenche a perna é ESTADO a exibir, não erro. O
    serviço explica em PT-BR, e o texto chega byte a byte."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    motivo = ("nenhum strike acima de 38,42 teve negócio no pregão; a trava de "
              "alta precisa de duas pernas com prêmio")
    _espiao(monkeypatch, _roteador(com_tese={
        "ticker": "PETR4", "trading_date": "2026-08-28", "setups": [],
        "reason": motivo}))

    r = c.post("/api/options/mcp/proposta",
               json={"ticker": "PETR4", "direction": "bullish"},
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["estruturas"] == []
    assert corpo["motivo"] == motivo, "motivo do serviço reescrito"
    assert corpo["emReais"] is None, "sem estrutura não há dinheiro a converter"


def test_proposta_com_lote_converte_a_estrutura_unica(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)

    corpo = c.post("/api/options/mcp/proposta",
                   json={"ticker": "PETR4", "direction": "bullish", "lote": 100},
                   headers=_auth(p["token"])).json()
    assert corpo["estruturas"][0]["breakevens"] == [38.62], (
        "breakeven saiu de preço do objeto — ×100 viraria um número sem "
        "significado que a tela mostraria como reais")
    assert corpo["emReais"]["custoLiquido"] == pytest.approx(62.0)
    # `propose_option_setups` não devolve `scenarios`; lista vazia, nunca
    # cenário inventado
    assert corpo["emReais"]["cenarios"] == []


# ═══════════════════════════════════════════════════════ possibilidades ═══
def test_possibilidades_com_3_vencimentos_faz_2n_mais_1_chamadas(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()

    assert len(chamadas) == 7, (
        f"o custo declarado é 2×3+1=7 e foram {len(chamadas)} chamadas: "
        f"{_nomes(chamadas)}")
    assert corpo["chamadasPrevistas"] == 7, (
        "a rota anuncia um número e gasta outro — a UI mostra esse mesmo "
        "campo ANTES de disparar")
    assert _nomes(chamadas)[0] == "propose_option_setups"
    assert chamadas[0][1] == {"ticker": "PETR4"}, (
        "a primeira chamada é a que descobre os vencimentos; com tese ela "
        "devolveria estruturas em vez de `expirations`")
    assert corpo["vencimentosDisponiveis"] == _VENCIMENTOS
    assert corpo["vencimentosConsiderados"] == _VENCIMENTOS
    assert [i["vencimento"] for i in corpo["possibilidades"]] == _VENCIMENTOS
    assert corpo["lote"] == 100
    assert _usado(main, uid) == 7
    assert _reservado(main, uid) == 0, "sobrou reserva presa depois da resposta"


def test_vencimentos_pedidos_sao_intersectados_e_limitados_a_seis(monkeypatch):
    """Vencimento que a cadeia não tem não vira chamada: gastaria cap para o
    serviço responder que não existe. E o teto de 6 protege a sessão da
    pessoa — o custo cresce linear com N ([R-13])."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    muitos = [f"2026-{m:02d}-19" for m in range(1, 13)]
    chamadas = _espiao(monkeypatch, _roteador(base=dict(_BASE, expirations=muitos)))

    corpo = c.post("/api/options/mcp/possibilidades",
                   json=_corpo_possibilidades(expirations=muitos + ["2030-01-01"]),
                   headers=_auth(p["token"])).json()
    assert corpo["vencimentosConsiderados"] == muitos[:6]
    assert "2030-01-01" not in corpo["vencimentosConsiderados"]
    assert corpo["chamadasPrevistas"] == 13
    assert len(chamadas) == 13


def test_sem_vencimento_aberto_e_200_sem_segunda_etapa(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch, _roteador(base=dict(_BASE, expirations=[])))

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["possibilidades"] == []
    assert corpo["motivo"] == options_mcp_api.MOTIVO_SEM_VENCIMENTO
    assert corpo["chamadasPrevistas"] == 1
    assert len(chamadas) == 1
    assert _reservado(main, uid) == 0


def test_vencimento_que_nao_monta_nao_gasta_a_avaliacao(monkeypatch):
    """Avaliar o que não existe gastaria cap por nada. Consumir MENOS que o
    reservado é sempre permitido; o contrário nunca foi."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    motivo = "não há strike com prêmio acima de 38,42 neste vencimento"
    chamadas = _espiao(monkeypatch, _roteador(por_vencimento={
        _VENCIMENTOS[1]: {"ticker": "PETR4", "setups": [], "reason": motivo}}))

    corpo = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
                   headers=_auth(p["token"])).json()

    vazio = corpo["possibilidades"][1]
    assert vazio["vencimento"] == _VENCIMENTOS[1]
    assert vazio["estrutura"] is None
    assert vazio["emReais"] is None
    assert vazio["motivo"] == motivo, "motivo do serviço reescrito"
    assert corpo["possibilidades"][0]["estrutura"] is not None
    assert corpo["possibilidades"][2]["estrutura"] is not None

    assert len(chamadas) == 6, (
        f"o vencimento sem estrutura foi avaliado mesmo assim: {_nomes(chamadas)}")
    assert _nomes(chamadas).count("evaluate_option_structure") == 2
    assert _usado(main, uid) == 6
    assert corpo["chamadasPrevistas"] == 7, (
        "`chamadasPrevistas` é a PREVISÃO mostrada antes de disparar; o gasto "
        "real pode ser menor, nunca maior")


def test_cota_que_so_cobre_a_primeira_etapa_recusa_antes_de_avaliar(monkeypatch):
    """D-24.1: reservar o teto (13) recusaria quem tem cota de sobra, e
    reservar 1 para gastar 7 faria o cap mentir. Com a cota em 2, a primeira
    etapa passa e a segunda recusa — antes da rede, não depois."""
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "2")
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "mcp_cota"
    assert _nomes(chamadas) == ["propose_option_setups"], (
        "a segunda etapa tocou o serviço com a cota estourada")
    assert "evaluate_option_structure" not in _nomes(chamadas)
    assert _usado(main, uid) == 1, "a primeira chamada aconteceu e foi cobrada"
    assert _reservado(main, uid) == 0, "o 402 saiu com reserva presa"


def test_duas_consultas_por_cache_nao_produzem_falso_esgotado(monkeypatch):
    """A classe de defeito do A-07, agora na rota de custo variável: com a
    cota em 7 e 3 vencimentos, a consulta reserva 1+6=7 e consome 0 (tudo
    cache). Sem a devolução do saldo, a SEGUNDA consulta recusaria com
    "Cota do dia da aba Opções esgotada" tendo `usado: 0` no mesmo corpo."""
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "7")
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, cache=True)

    for n in (1, 2):
        r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
                   headers=_auth(p["token"]))
        assert r.status_code == 200, (
            f"a {n}ª consulta respondeu {r.status_code} ({r.text}) — nenhuma "
            f"chamada ao serviço aconteceu (tudo cache) e o confirmado é "
            f"{_usado(main, uid)}/7: este 402 é um falso esgotado, feito da "
            f"reserva não consumida")
        assert _usado(main, uid) == 0, "acerto de cache cobrou cap"
        assert _reservado(main, uid) == 0, (
            f"reserva acumulada depois da {n}ª consulta — é assim que o falso "
            f"esgotado se forma")


def test_cenarios_nomeados_viajam_para_a_avaliacao(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    c.post("/api/options/mcp/possibilidades",
           json=_corpo_possibilidades(alvo=41.0, stop=36.5,
                                      expirations=[_VENCIMENTOS[0]]),
           headers=_auth(p["token"]))

    args = [a for n, a in chamadas if n == "evaluate_option_structure"][0]
    assert args["scenarios"] == [{"name": "alvo", "underlying": 41.0},
                                 {"name": "stop", "underlying": 36.5}]
    assert args["legs"] == [{"contract": "PETRI380", "side": "buy", "quantity": 1},
                            {"contract": "PETRI400", "side": "sell", "quantity": 1}]


@pytest.mark.parametrize("valor", [0, -1, 1.5, "cem", True, None])
def test_lote_invalido_e_422_antes_da_rede(monkeypatch, valor):
    """D-24.3: lote é número de AÇÕES, inteiro ≥ 1. `True` entra na lista
    porque `bool` é subclasse de `int` — sem a recusa explícita viraria lote
    de 1 ação silenciosamente."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    corpo = dict(_corpo_possibilidades(), lote=valor)
    r = c.post("/api/options/mcp/possibilidades", json=corpo,
               headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "lote_invalido"
    assert chamadas == [], "lote inválido tocou o serviço"


def test_lote_nao_precisa_ser_multiplo_de_cem(monkeypatch):
    """Recusar 150 seria inventar uma regra que a B3 não aplica uniformemente
    — o tamanho do contrato é da SÉRIE (D-24.3)."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)

    r = c.post("/api/options/mcp/possibilidades",
               json=_corpo_possibilidades(lote=150, expirations=[_VENCIMENTOS[0]]),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["lote"] == 150


@pytest.mark.parametrize("campo", ["alvo", "stop"])
def test_cenario_com_preco_impossivel_e_422(monkeypatch, campo):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)

    r = c.post("/api/options/mcp/possibilidades",
               json=_corpo_possibilidades(**{campo: 0}), headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "cenario_invalido"
    assert chamadas == []


# ══════════════════════════════════════════════════════════════ reais ═════
def test_em_reais_multiplica_pelo_lote_e_preserva_o_null(monkeypatch):
    """`max_gain: null` é GANHO ILIMITADO. Virar 0 aqui faria a tela dizer
    "não ganha nada" sobre a estrutura de ganho sem teto."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    ilimitada = dict(_AVALIACAO, max_gain=None, unlimited_gain=True)
    _espiao(monkeypatch, _roteador(avaliacao=ilimitada))

    corpo = c.post("/api/options/mcp/possibilidades",
                   json=_corpo_possibilidades(expirations=[_VENCIMENTOS[0]]),
                   headers=_auth(p["token"])).json()
    em_reais = corpo["possibilidades"][0]["emReais"]

    assert em_reais["lote"] == 100
    assert em_reais["custoLiquido"] == pytest.approx(_AVALIACAO["net_cost"] * 100)
    assert em_reais["perdaMaxima"] == pytest.approx(_AVALIACAO["max_loss"] * 100)
    assert em_reais["ganhoMaximo"] is None, "ganho ilimitado virou número"


def test_em_reais_nao_conhece_breakeven_e_o_preco_continua_preco(monkeypatch):
    """D-24.2 por DESENHO, não por proibição: breakeven é PREÇO DO OBJETO, e
    ×lote viraria um número sem significado exibido como reais. Ele fica fora
    do bloco, na estrutura, no valor do serviço."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)

    corpo = c.post("/api/options/mcp/possibilidades",
                   json=_corpo_possibilidades(alvo=41.0,
                                              expirations=[_VENCIMENTOS[0]]),
                   headers=_auth(p["token"])).json()
    item = corpo["possibilidades"][0]

    assert not [k for k in item["emReais"] if "breakeven" in k.lower()], \
        f"`emReais` ganhou chave de breakeven: {sorted(item['emReais'])}"
    assert item["estrutura"]["breakevens"] == _AVALIACAO["breakevens"], \
        "breakeven foi multiplicado pelo lote — 38,62 viraria R$ 3.862"
    # o cenário leva o preço VERBATIM e só o resultado em reais
    cenario = item["emReais"]["cenarios"][0]
    assert cenario["underlying"] == _AVALIACAO["scenarios"]["scenarios"][0]["underlying"]
    assert cenario["resultado"] == pytest.approx(
        _AVALIACAO["scenarios"]["scenarios"][0]["result"] * 100)


def test_em_reais_e_puro_e_devolve_none_para_o_que_nao_e_numero():
    """Unidade, por import direto (D-24.2): o helper não tem rede, não tem
    banco e não tem relógio — o que entra torto sai `None`, nunca 0."""
    fora = options_mcp_api._em_reais(
        {"net_cost": 0.62, "max_gain": None, "max_loss": "indefinido",
         "scenarios": {"scenarios": [{"name": "alvo", "underlying": 41.0,
                                      "result": 1.38},
                                     {"name": "torto", "underlying": None,
                                      "result": True}]}},
        100)
    assert fora["custoLiquido"] == pytest.approx(62.0)
    assert fora["ganhoMaximo"] is None
    assert fora["perdaMaxima"] is None, "texto do serviço virou número"
    assert fora["cenarios"][0]["resultado"] == pytest.approx(138.0)
    assert fora["cenarios"][0]["underlying"] == 41.0, "preço do cenário foi multiplicado"
    assert fora["cenarios"][1]["resultado"] is None, "booleano virou 100 reais"
    assert fora["lote"] == 100


# ═════════════════════════════════════════════════ razão ganho/perda ══════
# F-01 do `24-VERIFICATION.md` (plano 24-06): o critério 1 do ROADMAP termina
# em "breakevens e razão ganho/perda", e a razão não existia em lugar nenhum.
# O que estes testes travam não é a divisão — é o que acontece quando ela NÃO
# existe: ganho sem teto, perda sem piso, campo ausente e perda zero. Um
# número inventado em qualquer um dos quatro seria pior do que a ausência
# anterior, porque a pessoa compara 2,3 com 1,5 e decide.
def test_razao_ganho_perda_nao_recebe_lote():
    """Adimensional por DESENHO: multiplicar os dois lados pelo mesmo lote não
    muda a razão, e um parâmetro que não muda o resultado é convite a
    multiplicá-lo por engano — o defeito irmão do breakeven × lote (D-24.2).
    A assinatura é o que torna esse engano impossível."""
    assert list(inspect.signature(
        options_mcp_api._razao_ganho_perda).parameters) == ["dados"]


def test_razao_ganho_perda_no_caso_normal():
    """O cenário do achado F-01: trava de alta que paga 0,67 por 1 de risco —
    o número que decide se vale montar, e que a tela nunca dizia."""
    assert options_mcp_api._razao_ganho_perda(
        {"max_gain": 0.80, "max_loss": -1.20}) == {"valor": 0.67, "motivo": None}
    # sinal não importa: o serviço pode mandar a perda positiva ou negativa,
    # e a razão é entre MAGNITUDES.
    assert options_mcp_api._razao_ganho_perda(
        {"max_gain": 1.38, "max_loss": 0.62})["valor"] == pytest.approx(2.23)


@pytest.mark.parametrize("dados,constante", [
    # ganho sem teto: dividir por um `max_gain` que o serviço declarou ausente
    # daria "não ganha nada" sobre a estrutura de ganho ilimitado
    ({"max_gain": None, "max_loss": -1.2, "unlimited_gain": True},
     "RAZAO_GANHO_ILIMITADO"),
    ({"max_gain": 1.2, "max_loss": None, "unlimited_loss": True},
     "RAZAO_PERDA_ILIMITADA"),
    # campo ausente e campo que não é número — `True` é o caso que um
    # `isinstance(x, (int, float))` ingênuo deixaria passar como 1
    ({"max_gain": 1.2}, "RAZAO_SEM_DADO"),
    ({"max_gain": None, "max_loss": -1.2}, "RAZAO_SEM_DADO"),
    ({"max_gain": True, "max_loss": 1.0}, "RAZAO_SEM_DADO"),
    ({"max_gain": 1.2, "max_loss": "indefinido"}, "RAZAO_SEM_DADO"),
    # divisão por zero: o número que mais engana na tela
    ({"max_gain": 1.38, "max_loss": 0}, "RAZAO_PERDA_ZERO"),
    ({"max_gain": 1.38, "max_loss": -0.0}, "RAZAO_PERDA_ZERO"),
])
def test_razao_indefinida_e_none_com_motivo_nunca_numero(dados, constante):
    fora = options_mcp_api._razao_ganho_perda(dados)
    assert fora["valor"] is None, (
        "razão que não existe virou número — é a classe de fabricação que o "
        "critério 2 do ROADMAP proíbe")
    assert fora["motivo"] == getattr(options_mcp_api, constante)


def test_os_quatro_motivos_da_razao_estao_em_avisos():
    """[R-12]: texto fixo que chega ao usuário entra na superfície varrida
    pelo `test_guardrail_imperativo` na fase que o cria."""
    for nome in ("RAZAO_GANHO_ILIMITADO", "RAZAO_PERDA_ILIMITADA",
                 "RAZAO_SEM_DADO", "RAZAO_PERDA_ZERO"):
        assert getattr(options_mcp_api, nome) in options_mcp_api.AVISOS, nome


def test_razao_chega_na_proposta_fora_do_bloco_de_reais(monkeypatch):
    """No MESMO nível de `emReais`, e nunca DENTRO dele: razão é adimensional,
    `emReais` é dinheiro. Dobrar o lote não pode mexer nela."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)

    def _pede(lote):
        return c.post("/api/options/mcp/proposta",
                      json={"ticker": "PETR4", "direction": "bullish", "lote": lote},
                      headers=_auth(p["token"])).json()

    corpo = _pede(100)
    assert corpo["razaoGanhoPerda"]["valor"] == pytest.approx(2.23)
    assert corpo["razaoGanhoPerda"]["motivo"] is None
    assert not [k for k in corpo["emReais"] if "razao" in k.lower()], (
        f"a razão entrou no bloco de reais: {sorted(corpo['emReais'])}")

    dez_vezes = _pede(1000)
    assert dez_vezes["emReais"]["custoLiquido"] == pytest.approx(620.0)
    assert dez_vezes["razaoGanhoPerda"] == corpo["razaoGanhoPerda"], (
        "a razão mudou com o lote — alguém a multiplicou")


def test_razao_chega_em_cada_item_de_possibilidades(monkeypatch):
    """Item com estrutura tem razão; item que não montou tem `None` — e não um
    objeto de razão sobre estrutura nenhuma."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    vazio = {"ticker": "PETR4", "trading_date": "2026-08-28", "setups": [],
             "reason": "a cadeia deste vencimento não tem prêmio na segunda perna"}
    _espiao(monkeypatch, _roteador(por_vencimento={_VENCIMENTOS[1]: vazio}))

    corpo = c.post("/api/options/mcp/possibilidades",
                   json=_corpo_possibilidades(), headers=_auth(p["token"])).json()
    por_venc = {i["vencimento"]: i for i in corpo["possibilidades"]}

    com_estrutura = por_venc[_VENCIMENTOS[0]]
    assert com_estrutura["razaoGanhoPerda"]["valor"] == pytest.approx(2.23)
    assert not [k for k in com_estrutura["emReais"] if "razao" in k.lower()]
    assert por_venc[_VENCIMENTOS[1]]["razaoGanhoPerda"] is None


def test_razao_de_estrutura_sem_teto_de_ganho_vai_com_motivo_ate_a_tela(monkeypatch):
    """O caminho completo do caso perigoso: o serviço diz "sem teto", e o que
    chega à tela é o motivo, não um número."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    ilimitada = dict(_AVALIACAO, max_gain=None, unlimited_gain=True)
    _espiao(monkeypatch, _roteador(avaliacao=ilimitada))

    corpo = c.post("/api/options/mcp/possibilidades",
                   json=_corpo_possibilidades(expirations=[_VENCIMENTOS[0]]),
                   headers=_auth(p["token"])).json()
    razao = corpo["possibilidades"][0]["razaoGanhoPerda"]
    assert razao["valor"] is None
    assert razao["motivo"] == options_mcp_api.RAZAO_GANHO_ILIMITADO


# ═══════════════════════════════════════════════════════════ degradação ═══
def test_servico_indisponivel_no_meio_do_laco_vira_503(monkeypatch):
    """Serviço fora do ar não é condição de UM vencimento: é de todos. Uma
    resposta 200 parcial esconderia que o serviço parou no meio."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, _roteador(por_vencimento={
        _VENCIMENTOS[1]: mcp_client.McpIndisponivel("timeout ao falar com o serviço")}))

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 503, r.text
    assert r.json()["detail"]["code"] == "mcp_indisponivel"
    # o texto ao usuário não carrega nome de credencial nem número interno
    assert "timeout" not in r.json()["detail"]["message"].lower()
    assert _reservado(main, uid) == 0, "o 503 saiu com reserva presa"


def test_erro_de_tool_em_um_vencimento_nao_apaga_os_outros(monkeypatch):
    """Erro de tool é sobre AQUELE pedido. Derrubar a consulta inteira por
    causa de um vencimento jogaria fora as outras duas estruturas já pagas."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, _roteador(por_vencimento={
        _VENCIMENTOS[1]: mcp_client.McpErroDeTool(
            "vencimento 2026-10-17 sem cotação no pregão",
            available=None, hint="tente outro vencimento")}))

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    itens = r.json()["possibilidades"]

    assert itens[1]["estrutura"] is None
    assert itens[1]["erro"] == "vencimento 2026-10-17 sem cotação no pregão"
    assert itens[0]["estrutura"] is not None and itens[0]["erro"] is None
    assert itens[2]["estrutura"] is not None and itens[2]["erro"] is None


def test_falha_na_primeira_etapa_vira_422_sem_segunda_etapa(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch, _roteador(base=mcp_client.McpErroDeTool(
        "ticker sem cotações", available=None, hint="confira o código")))

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "mcp_erro_de_tool"
    assert len(chamadas) == 1
    # 2026-09-11 (24-07, F-04): era `== 0` com a mensagem "chamada que
    # levantou cobrou cap". A decisão do Alex inverteu a regra — a recusa da
    # tool é viagem que o serviço já cobrou, e passou a debitar 1. O que este
    # teste guarda (a segunda etapa NÃO acontece, e nada fica preso) não
    # mudou; o número mudou porque o critério mudou, com guardião próprio em
    # `test_f04_seis_evaluate_recusados_com_propose_em_cache_debitam_seis`.
    assert _usado(main, uid) == 1, "a recusa da tool não debitou a viagem"
    assert _reservado(main, uid) == 0


# ══════════════════════════════════════════════ 24-07 — achado F-04 ═══════
# O cenário MEDIDO pelo verificador, virado em teste. O serviço conta toda
# `tools/call` no porteiro, antes de executar a tool; o Boris debitava só no
# sucesso. Decisão do Alex em 2026-09-11: cobrar a viagem que a tool recusou.
#
# O que a verificação mediu (24-VERIFICATION.md, F-04), num ticker cuja cadeia
# não traz `preco_objeto` e cujo `evaluate` recusa em todos os vencimentos:
#
#   requisição 1: 13 chamadas reais; cap do usuário debitado 7
#   requisição 2 (dentro do TTL de 15 min): base e os 6 `propose` vêm do
#     cache; os 6 `evaluate` NÃO estão em cache (recusa nunca entra no cache)
#     → 6 chamadas reais cobradas pelo serviço, 0 debitadas do usuário
#
# Repetir o botão ~330 vezes esgotava os 2.000/dia de TODA a base sem mover o
# contador de 60/dia de ninguém. É esse 0 que estes testes transformam em 6.
_SEIS_VENCIMENTOS = ["2026-09-19", "2026-10-17", "2026-11-21",
                     "2026-12-19", "2027-01-16", "2027-02-20"]


def _espiao_cache_por_tool(monkeypatch, roteador, cache: dict):
    """Como `_espiao`, mas com o flag de cache POR TOOL — o cenário do F-04 é
    exatamente o MISTO: `propose` servido do cache (0 rede, 0 cap) e
    `evaluate` indo à rede para ser recusado."""
    chamadas: list = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        v = roteador(nome, args)
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, bool(cache.get(nome, False)))

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


def _recusa_da_cadeia_sem_objeto():
    return mcp_client.McpErroDeTool(
        "leg PETRI380: the chain carries no underlying price for this expiration",
        available=None, hint=None)


def test_f04_seis_evaluate_recusados_com_propose_em_cache_debitam_seis(monkeypatch):
    """**O teste que mede o defeito relatado.** Sem a correção, `used` fica em
    0: os 7 `propose` vêm do cache (não tocam a rede, não devem cobrar mesmo)
    e as 6 recusas de `evaluate` tocavam a rede sem debitar nada."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao_cache_por_tool(
        monkeypatch,
        _roteador(base=dict(_BASE, expirations=list(_SEIS_VENCIMENTOS)),
                  avaliacao=_recusa_da_cadeia_sem_objeto()),
        cache={"propose_option_setups": True})

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()

    # o fan-out aconteceu inteiro: 1 base + 6 propose + 6 evaluate
    assert len(chamadas) == 13, _nomes(chamadas)
    assert _nomes(chamadas).count("evaluate_option_structure") == 6
    assert corpo["chamadasPrevistas"] == 13
    assert all(i["estrutura"] is None and i["erro"] for i in corpo["possibilidades"]), \
        "os seis vencimentos deveriam ter sido recusados pela tool"

    assert _usado(main, uid) == 6, (
        "as seis recusas de `evaluate` não debitaram o cap: são seis chamadas "
        "REAIS, já cobradas do teto compartilhado de 2.000/dia pelo serviço, "
        "e zero no contador de 60/dia de quem as provocou (achado F-04)")
    assert corpo["cap"]["usado"] == 6, "o bloco `cap` da resposta contradiz o débito"
    assert _reservado(main, uid) == 0, "a resposta saiu com reserva presa"


def test_f04_reserva_de_doze_com_seis_recusas_devolve_seis(monkeypatch):
    """Cobrar a recusa não pode desarrumar a contabilidade da `_Reserva`:
    devolver a MENOS prende cota (o defeito A-07), devolver a MAIS é cota de
    graça. Com 1+12 reservados e 6 consumidos, as devoluções são 6 (etapa 2,
    que sai primeiro) e 1 (etapa 1) — aritmética fechada."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]

    reservas, consumos, devolucoes = [], [], []
    check_real, consume_real, liberar_real = (metering.check, metering.consume,
                                              metering.liberar)

    def _check(conn, user_id, **kw):
        ok, motivo = check_real(conn, user_id, **kw)
        if ok:
            reservas.append(max(1, int(kw.get("custo") or 1)))
        return ok, motivo

    def _consume(conn, user_id, **kw):
        consumos.append(max(1, int(kw.get("custo") or 1)))
        return consume_real(conn, user_id, **kw)

    def _liberar(conn, user_id, **kw):
        devolucoes.append(max(1, int(kw.get("custo") or 1)))
        return liberar_real(conn, user_id, **kw)

    monkeypatch.setattr(metering, "check", _check)
    monkeypatch.setattr(metering, "consume", _consume)
    monkeypatch.setattr(metering, "liberar", _liberar)
    _espiao_cache_por_tool(
        monkeypatch,
        _roteador(base=dict(_BASE, expirations=list(_SEIS_VENCIMENTOS)),
                  avaliacao=_recusa_da_cadeia_sem_objeto()),
        cache={"propose_option_setups": True})

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text

    assert reservas == [1, 12], f"as duas etapas do D-24.1 mudaram: {reservas}"
    assert sum(consumos) == 6, f"consumo diferente das 6 recusas: {consumos}"
    assert devolucoes == [6, 1], (
        f"devoluções {devolucoes} — o `with` interno sai primeiro e devolve "
        f"12−6=6; o externo devolve 1 (o `propose` base veio do cache)")
    assert sum(devolucoes) == sum(reservas) - sum(consumos), (
        "aritmética aberta: sobra presa (a menos) ou cota de graça (a mais)")
    assert _usado(main, uid) == 6
    assert _reservado(main, uid) == 0


def test_f04_o_422_de_erro_de_tool_diz_que_cobrou(monkeypatch):
    """Cobrar sem dizer que cobrou é a parte do defeito que o usuário enxerga:
    a cota dele cai e a tela mostra só "o serviço recusou"."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, _roteador(base=mcp_client.McpErroDeTool(
        "ticker sem cotações", available=None, hint="confira o código")))

    r = c.post("/api/options/mcp/possibilidades", json=_corpo_possibilidades(),
               headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "mcp_erro_de_tool"
    assert detalhe["cobrado"] is True, (
        "o 422 não declara que a tentativa consumiu cota — o front decide a "
        "linha de aviso por este campo, nunca por raspagem da mensagem")
    assert detalhe["nota"] == options_mcp_api.AVISO_RECUSA_COBRADA
    assert options_mcp_api.AVISO_RECUSA_COBRADA in options_mcp_api.AVISOS, \
        "texto fixo novo fora da varredura do guardião imperativo ([R-12])"
    # e o que o 422 AFIRMA é o que de fato aconteceu no contador
    assert _usado(main, uid) == 1, "o corpo diz 'cobrado' e o cap não moveu"
