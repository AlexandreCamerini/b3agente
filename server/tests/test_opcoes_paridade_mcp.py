"""aba-opcoes F3 — paridade entre a matemática do Boris (`opcoes_payoff`) e a
do serviço MCP (`evaluate_option_structure`), campo a campo.

**Por que este arquivo existe:** o ADR-027, Decisão 3, deixou os dois motores
vivos lado a lado e fixou o gatilho da consolidação futura. Enquanto os dois
existirem, a única garantia de que a tela não mostra duas contas diferentes
para a mesma estrutura é esta comparação — e ela tem de ser exercida, não
prometida.

**Sobre a fixture** (`fixtures/mcp_evaluate_petr4.json`): ela é DERIVADA.
Os strikes, prêmios e deltas foram escolhidos (trava de alta em PETR4, débito,
2 pernas); todo o resto — custo, extremos, breakevens, delta somado, curva e
cenários — saiu de `opcoes_payoff` e foi gravado no VOCABULÁRIO do serviço.
Fixture inventada com números impossíveis provaria nada: passaria por
coerência consigo mesma. O que a fixture trava é a TRADUÇÃO (campo do serviço
= campo do Boris) e a forma da resposta. Quem prova o contrato de verdade é
`test_paridade_viva`, que chama o serviço e pula sem credencial (D-24.7).

`test_divergencia_e_detectada` é o contra-guardião: sem ele, uma comparação
que não compara nada passaria em silêncio para sempre.
"""
from __future__ import annotations

import json
import os
import pathlib

import pytest

from app import opcoes_payoff

_FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "mcp_evaluate_petr4.json"

# Mapa de paridade, na direção serviço → Boris. Vale para os dois testes (o de
# fixture e o vivo) — é ele, e não o payload, que este arquivo guarda.
_LADO = {"buy": "compra", "sell": "venda"}
_TIPO = {"CALL": "CALL", "PUT": "PUT", "STOCK": "ACAO"}
_FLUXO = {"debit": "debito", "credit": "credito", "flat": "neutro"}

# `rel=1e-9` e não igualdade exata: os dois motores arredondam em pontos
# diferentes do cálculo, e exigir o bit idêntico transformaria este guardião
# num detector de ponto flutuante em vez de um detector de divergência de
# fórmula.
_TOL = 1e-9


def _fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _pernas_em_portugues(legs) -> list:
    """Perna do serviço → perna do `opcoes_payoff`. É a tradução inteira: se
    um campo mudar de nome no contrato, é aqui que quebra, e não no meio de
    uma asserção numérica que pareceria erro de conta."""
    fora = []
    for leg in legs or []:
        fora.append({
            "contrato": leg.get("contract"),
            "tipo": _TIPO.get(str(leg.get("kind") or "").upper()),
            "lado": _LADO.get(str(leg.get("side") or "").lower()),
            "strike": leg.get("strike"),
            "premio": leg.get("premium"),
            "quantidade": leg.get("quantity") if leg.get("quantity") is not None else 1,
            "delta": leg.get("delta"),
        })
    return fora


def _comparar(servico: dict) -> dict:
    """Roda `perfil_da_estrutura` sobre as pernas do serviço e confere campo a
    campo. Levanta `AssertionError` na primeira divergência — é o corpo dos
    três testes abaixo, inclusive o que EXIGE a falha."""
    pernas = _pernas_em_portugues(servico.get("legs"))
    assert pernas, "resposta do serviço sem pernas: não há o que comparar"
    perfil = opcoes_payoff.perfil_da_estrutura(pernas)

    assert perfil["custo_liquido"] == pytest.approx(servico["net_cost"], rel=_TOL), \
        "custo_liquido x net_cost divergiram — é a conta que decide quanto sai do bolso"
    assert perfil["fluxo"] == _FLUXO[servico["flow"]], \
        "fluxo x flow divergiram: débito virando crédito inverte o sinal da operação"

    for nosso, deles in (("ganho_maximo", "max_gain"), ("perda_maxima", "max_loss")):
        if servico[deles] is None:
            assert perfil[nosso] is None, (
                f"{deles} é null (ilimitado) e {nosso} veio com número — "
                f"um teto inventado onde não há teto")
        else:
            assert perfil[nosso] is not None, (
                f"{deles} tem número e {nosso} veio None — o Boris declarou "
                f"ilimitado o que o serviço limitou")
            assert perfil[nosso] == pytest.approx(servico[deles], rel=_TOL), \
                f"{nosso} x {deles} divergiram"

    assert perfil["ganho_ilimitado"] is bool(servico["unlimited_gain"])
    assert perfil["perda_ilimitada"] is bool(servico["unlimited_loss"]), \
        "perda ilimitada x limitada é a diferença entre 'perde o prêmio' e 'perde a conta'"

    assert len(perfil["breakevens"]) == len(servico["breakevens"]), \
        "número de breakevens diferente — estrutura lida com outro formato"
    for nosso, deles in zip(perfil["breakevens"], servico["breakevens"]):
        assert nosso == pytest.approx(deles, rel=_TOL), "breakeven divergiu"

    assert perfil["delta_total"]["valor"] == pytest.approx(servico["net_delta"], rel=_TOL), \
        "delta_total.valor x net_delta divergiram"

    return perfil


# ─────────────────────────────────────────────────────────── fixture ──────
def test_paridade_campo_a_campo():
    """Custo, extremos, ilimitados, breakevens e delta somado: a mesma
    estrutura, os dois motores, o mesmo número."""
    _comparar(_fixture())


def test_paridade_curva_ponto_a_ponto():
    """A curva não é decoração: é o que a tela desenha. Um ponto fora do lugar
    move o desenho sem mover nenhum dos números do resumo."""
    servico = _fixture()
    perfil = _comparar(servico)

    curva, payoff = perfil["curva"], servico["payoff"]
    assert len(curva) == len(payoff), (
        f"a curva do Boris tem {len(curva)} pontos e o payoff do serviço "
        f"{len(payoff)} — os dois avaliam nos mesmos preços (zero e os strikes)")
    for ponto, deles in zip(curva, payoff):
        assert ponto["preco_objeto"] == pytest.approx(deles["underlying"], rel=_TOL)
        assert ponto["resultado"] == pytest.approx(deles["result"], rel=_TOL)


def test_divergencia_e_detectada():
    """Contra-guardião: um centavo a mais no `net_cost` da fixture TEM de
    reprovar. Sem esta prova, `_comparar` poderia estar comparando nada — e
    dois motores divergindo em produção passariam com a suíte verde."""
    adulterada = _fixture()
    adulterada["net_cost"] = adulterada["net_cost"] + 0.01

    with pytest.raises(AssertionError):
        _comparar(adulterada)


def test_fixture_declara_a_forma_do_contrato():
    """A fixture é DERIVADA, mas a forma dela é o contrato do serviço. Campo
    que sumir daqui é campo que a rota `/possibilidades` repassaria como
    `None` sem ninguém notar."""
    servico = _fixture()
    for campo in ("ticker", "trading_date", "underlying_price", "legs",
                  "net_cost", "flow", "max_gain", "max_loss", "unlimited_gain",
                  "unlimited_loss", "breakevens", "net_delta", "payoff",
                  "scenarios", "sessions_to_nearest_expiry"):
        assert campo in servico, f"a fixture perdeu o campo `{campo}` do contrato"
    assert servico["trading_date"], "fixture sem pregão: dado sem carimbo não é dado"


# ─────────────────────────────────────────────────────────────── vivo ─────
@pytest.mark.skipif(not os.environ.get("MCP_CLIENT_SECRET"),
                    reason="exige credencial do serviço (MCP_CLIENT_SECRET)")
def test_paridade_viva():
    """A MESMA comparação contra o serviço de verdade — é este que o smoke de
    staging executa (D-24.7). Sem segredo no ambiente, pula: um teste de rede
    que falha por falta de credencial vira ruído e treina a equipe a ignorar
    vermelho."""
    import asyncio

    from app import mcp_client

    ticker = os.environ.get("MCP_PARIDADE_TICKER", "PETR4")

    async def _do_servico() -> dict:
        cadeia, _ = await mcp_client.call_tool(
            "get_option_chain", {"ticker": ticker, "kind": "CALL", "limit": 50})
        candidatas = [
            o for o in (cadeia.get("options") or [])
            if isinstance(o, dict) and o.get("contrato") and o.get("dt_vencimento")
            and isinstance(o.get("premio"), (int, float)) and o.get("premio") > 0
            and isinstance(o.get("strike"), (int, float))
        ]
        assert candidatas, f"cadeia de {ticker} sem contrato com prêmio — nada a avaliar"

        venc = candidatas[0]["dt_vencimento"]
        do_venc = sorted((o for o in candidatas if o.get("dt_vencimento") == venc),
                         key=lambda o: o["strike"])
        assert len(do_venc) >= 2, f"vencimento {venc} com menos de 2 strikes negociados"

        pernas = [
            {"contract": do_venc[0]["contrato"], "side": "buy", "quantity": 1},
            {"contract": do_venc[-1]["contrato"], "side": "sell", "quantity": 1},
        ]
        avaliacao, _ = await mcp_client.call_tool(
            "evaluate_option_structure", {"ticker": ticker, "legs": pernas})
        return avaliacao

    servico = asyncio.run(_do_servico())
    perfil = _comparar(servico)

    for ponto, deles in zip(perfil["curva"], servico.get("payoff") or []):
        assert ponto["resultado"] == pytest.approx(deles["result"], rel=_TOL)
