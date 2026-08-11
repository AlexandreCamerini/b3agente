"""ADR-008, Fase 6 (qa/43) — a didática DECLARA fonte e idade do dado.

O que este guardião protege: quando o texto fala de frescor/atraso, ele nomeia
a fonte (intraday = Yahoo; diário/spot = brapi com Yahoo de reserva) e mantém
a regra da camada de entendimento: fonte indisponível se declara, nunca se
estima. Reversão deliberada atualiza este guardião com nota — não se apaga.
"""
from app import assistente, conceitos


def test_assistente_declara_fonte_por_superficie():
    txt = assistente._regras("estudo") + assistente._regras("operador")
    assert "Yahoo Finance" in txt            # intraday nomeado
    assert "brapi" in txt                    # diário/spot nomeado
    assert "reserva" in txt                  # backup declarado
    assert "DECLARA" in txt                  # regra: declarar, não estimar


def test_conceitos_nomeiam_a_fonte_do_intraday():
    todos = str(conceitos.CONCEITOS)
    assert "Yahoo Finance" in todos
