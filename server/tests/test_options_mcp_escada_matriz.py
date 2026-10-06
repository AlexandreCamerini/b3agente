"""Fase 48 (Plano 07, 2026-10-05) — `POST /api/options/mcp/escada-matriz`.

Trava, OFFLINE: custo 2N+1 declarado == gasto; reserva em 2 etapas; recusa
antes da rede; vencimento inexistente nao vira chamada; falha de tool por
vencimento vira linha "—" com motivo sem apagar os outros; servico fora do ar
encerra a rota (sem 200 parcial); sessao obrigatoria; posicao vem do servidor.
Esqueleto de fixtures herdado de `test_options_mcp_api.py`.
"""
from __future__ import annotations

import sys

import pytest

from app import mcp_client, store
from tests.test_options_mcp_api import (  # noqa: F401  (fixture autouse + helpers)
    _BASE, _VENCIMENTOS, _auth, _client, _isolado, _nomes, _registra, _reservado,
    _usado)

ROTA = "/api/options/mcp/escada-matriz"


def _item(tipo, strike, premio, negocios=300, venc="2026-09-19"):
    return {"contrato": f"X{tipo[0]}{int(strike * 10)}", "tipo": tipo,
            "strike": strike, "premio": premio, "delta": 0.3,
            "total_negocios": negocios, "dt_vencimento": venc,
            "dt_pregao": "2026-08-28", "preco_objeto": 38.42}


def _cadeia(tipo, venc):
    if tipo == "PUT":
        it = [_item("PUT", k, p, venc=venc) for k, p in
              ((38.0, 1.1), (37.0, 0.7), (36.0, 0.4), (35.0, 0.25), (34.0, 0.12))]
        it.append(_item("PUT", 37.5, 0.9, negocios=10, venc=venc))  # nao operavel
    else:
        it = [_item("CALL", k, p, venc=venc) for k, p in
              ((39.0, 0.9), (40.0, 0.5), (41.0, 0.3), (42.0, 0.15), (43.0, 0.08))]
    return {"ticker": "PETR4", "trading_date": "2026-08-28",
            "underlying_price": 38.42, "options": it, "returned": len(it),
            "data_freshness": {"quotes": "em_dia", "quotes_age_hours": 12}}


def _roteador(erros=None):
    erros = erros or {}

    def _rota(nome, args):
        args = args or {}
        if nome == "propose_option_setups":
            return _BASE
        if nome == "get_option_chain":
            chave = args.get("expiration")
            if chave in erros:
                return erros[chave]
            return _cadeia(args["kind"], chave)
        return {}
    return _rota


def _espiao(monkeypatch, roteador=None, cache=False):
    roteador = roteador or _roteador()
    chamadas = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        v = roteador(nome, args)
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, cache)

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


def _com_posicao(main, uid, qty=1000, avg=38.0):
    store.put(main._conn, "positions",
              [{"t": "PETR4", "qty": qty, "avg": avg}], user_id=uid)


def _post(c, p, **corpo):
    return c.post(ROTA, json=dict({"ticker": "PETR4"}, **corpo),
                  headers=_auth(p["token"]))


def test_sem_sessao_401_antes_da_rede(monkeypatch):
    c, _ = _client(monkeypatch)
    chamadas = _espiao(monkeypatch)
    assert c.post(ROTA, json={"ticker": "PETR4"}).status_code == 401
    assert chamadas == []


def test_ticker_ausente_422(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    r = c.post(ROTA, json={}, headers=_auth(p["token"]))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "ticker_ausente"
    assert chamadas == []


def test_custo_2n_mais_1_declarado_igual_ao_gasto(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _com_posicao(main, uid)
    chamadas = _espiao(monkeypatch)

    r = _post(c, p)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert len(chamadas) == 7 == corpo["chamadasPrevistas"]
    assert chamadas[0] == ("propose_option_setups", {"ticker": "PETR4"})
    assert _nomes(chamadas).count("get_option_chain") == 6
    for venc in _VENCIMENTOS:
        for tipo in ("PUT", "CALL"):
            assert ("get_option_chain", {"ticker": "PETR4", "expiration": venc,
                                         "kind": tipo, "limit": 200}) in chamadas
    assert _usado(main, uid) == 7
    assert _reservado(main, uid) == 0
    assert corpo["vencimentosConsiderados"] == _VENCIMENTOS


def test_formato_da_matriz_3_objetivos_3_degraus(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    _com_posicao(main, p["user"]["id"])
    _espiao(monkeypatch)

    corpo = _post(c, p).json()
    assert set(corpo["matriz"]) == {"proteger", "renda", "collar"}
    for obj, linhas in corpo["matriz"].items():
        assert [l["vencimento"] for l in linhas] == _VENCIMENTOS
        for l in linhas:
            assert len(l["celulas"]) == 3
            assert l["motivo"] is None
    cel = corpo["matriz"]["proteger"][0]["celulas"]
    assert all(x["id"] for x in cel)
    # contrato nao operavel (10 negocios) nunca vira degrau
    assert all("375" not in str(x["id"]) for x in cel)
    assert corpo["frescor"]["medido"] is True
    assert corpo["precoObjeto"] == 38.42
    assert corpo["fonte"] and corpo["at"]


def test_vencimento_pedido_inexistente_nao_vira_chamada(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _com_posicao(main, uid)
    chamadas = _espiao(monkeypatch)

    corpo = _post(c, p, expirations=[_VENCIMENTOS[0], _VENCIMENTOS[2],
                                     "2030-01-01"]).json()
    assert corpo["vencimentosConsiderados"] == [_VENCIMENTOS[0], _VENCIMENTOS[2]]
    assert corpo["chamadasPrevistas"] == 5 == len(chamadas)
    assert _usado(main, uid) == 5


def test_sem_vencimento_vazio_custa_1(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch,
                       lambda n, a: dict(_BASE, expirations=[]))
    corpo = _post(c, p).json()
    assert corpo["chamadasPrevistas"] == 1 and len(chamadas) == 1
    assert all(v == [] for v in corpo["matriz"].values())
    assert corpo["motivo"]
    assert _usado(main, uid) == 1


def test_teto_de_seis_vencimentos(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    muitos = [f"2026-{m:02d}-19" for m in range(1, 10)]
    chamadas = _espiao(monkeypatch, lambda n, a: (
        dict(_BASE, expirations=muitos) if n == "propose_option_setups"
        else _cadeia(a["kind"], a["expiration"])))
    corpo = _post(c, p).json()
    assert len(corpo["vencimentosConsiderados"]) == 6
    assert corpo["chamadasPrevistas"] == 13 == len(chamadas)


def test_cache_nao_gasta_cap_e_devolve_reserva(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, cache=True)
    assert _post(c, p).status_code == 200
    assert _usado(main, uid) == 0
    assert _reservado(main, uid) == 0


def test_cota_so_cobre_a_primeira_etapa_recusa_antes_da_rede(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "2")
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)
    r = _post(c, p)
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "mcp_cota"
    assert _nomes(chamadas) == ["propose_option_setups"]
    assert _usado(main, uid) == 1
    assert _reservado(main, uid) == 0


def test_erro_de_tool_em_um_vencimento_nao_apaga_os_outros(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    _com_posicao(main, p["user"]["id"])
    _espiao(monkeypatch, _roteador(
        erros={_VENCIMENTOS[1]: mcp_client.McpErroDeTool("vencimento sem dado")}))

    r = _post(c, p)
    assert r.status_code == 200, r.text
    m = r.json()["matriz"]
    for obj in ("proteger", "renda", "collar"):
        ruim = m[obj][1]
        assert ruim["vencimento"] == _VENCIMENTOS[1]
        assert ruim["motivo"] == "vencimento sem dado"
        assert len(ruim["celulas"]) == 3
        assert all(x["id"] is None and x["total"] is None
                   and x["motivo"] == "vencimento sem dado"
                   for x in ruim["celulas"])
    assert all(x["id"] for x in m["proteger"][0]["celulas"])
    assert all(x["id"] for x in m["proteger"][2]["celulas"])


def test_servico_fora_do_ar_no_meio_do_laco_encerra_sem_200_parcial(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _com_posicao(main, uid)
    _espiao(monkeypatch, _roteador(
        erros={_VENCIMENTOS[1]: mcp_client.McpIndisponivel("fora do ar")}))
    r = _post(c, p)
    assert r.status_code >= 500 or r.status_code == 503, r.text
    assert _reservado(main, uid) == 0


def test_sem_posicao_devolve_celulas_vazias_com_motivo(monkeypatch):
    """Lastro vem do servidor: sem posicao no escopo, nenhum degrau, nunca 0."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)
    m = _post(c, p).json()["matriz"]
    for linhas in m.values():
        for l in linhas:
            assert all(x["id"] is None and x["motivo"] for x in l["celulas"])


def test_posicao_do_corpo_e_ignorada(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch)
    m = _post(c, p, posicao={"t": "PETR4", "qty": 9999, "avg": 30}).json()["matriz"]
    assert all(x["id"] is None for l in m["proteger"] for x in l["celulas"])
