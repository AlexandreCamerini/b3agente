"""quick 261013-cqk (2026-10-13) — regra de proximidade do plano (D1).

Fração do caminho PM->stop / PM->alvo >= LIMIAR_PROXIMIDADE; fallback na régua
stop->alvo quando o caminho não existe. Calculada só no backend."""
import pytest

from app import cartao_posicao

CASOS = [
    (20, 16, 30, 17, "perto_stop"),
    (20, 16, 30, 17.05, None),
    (20, 16, 30, 16, "perto_stop"),
    (20, 16, 30, 27.5, "perto_alvo"),
    (20, 16, 30, 27.4, None),
    (20, 16, 30, 30, "perto_alvo"),
    (20, 16, 30, 20, None),
    (20, 22, 30, 23, "perto_stop"),
    (20, 22, 30, 25, None),
    (20, 22, 30, 28, "perto_alvo"),
    (20, 20, 30, 22.5, "perto_stop"),
    (20, 20, 30, 23, None),
    (30, 20, 28, 27, "perto_alvo"),
    (40, 20, 24, 24, "perto_stop"),
    (20, 16, 30, None, None),
    (20, 16, None, 17, None),
    (20, None, 30, 28, None),
    (20, None, None, 17, None),
    (20, 16, 30, 15, None),
    (20, 16, 30, 31, None),
    (20, 25, 25, 25, None),
    (None, 16, 30, 17, None),
    ("abc", 16, 30, 17, None),
    (30, 20, 30, 29, "perto_alvo"),
    (30, 20, 30, 30, "perto_alvo"),
]


def _leitura(avg, stop, alvo, preco):
    pos = {"t": "PETR4", "qty": 100, "avg": avg, "stop": stop, "alvo": alvo}
    return cartao_posicao.leitura_plano(pos, preco, [], "educacional")


@pytest.mark.parametrize("avg,stop,alvo,preco,esperado", CASOS)
def test_proximidade_tabela(avg, stop, alvo, preco, esperado):
    assert _leitura(avg, stop, alvo, preco)["proximidade"] == esperado


def test_limiar_constante_unica(monkeypatch):
    assert cartao_posicao.LIMIAR_PROXIMIDADE == 0.75
    assert _leitura(20, 16, 30, 17)["proximidade"] == "perto_stop"
    monkeypatch.setattr(cartao_posicao, "LIMIAR_PROXIMIDADE", 0.9)
    assert _leitura(20, 16, 30, 17)["proximidade"] is None


def test_chaves_antigas_preservadas():
    r = _leitura(20, 16, 30, 17)
    for k in ("posicaoNoPlano", "distStopPct", "distAlvoPct", "rr", "resultado",
              "variacaoPct", "resultadoNoStop", "resultadoNoAlvo", "plano", "preco"):
        assert k in r
    assert "proximidade" in r


@pytest.mark.parametrize("v", [float("inf"), float("nan")])
def test_nao_finito_vira_none(v):
    assert _leitura(20, 16, 30, v)["proximidade"] is None
    assert _leitura(v, 16, 30, 17)["proximidade"] is None
