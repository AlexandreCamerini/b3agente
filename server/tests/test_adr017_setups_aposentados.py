"""ADR-017 (Bloco 0, 2026-08-20) — faixa catastrófica do backtest de 15 anos
(ADR-016) aposentada do motor de decisão. "Aposentado" != apagado: o setup
continua aparecendo (educacional, com o número), mas para de:
  (a) definir `melhor`/`veredito` em `setups.detect_setups`;
  (b) virar base de `setups.plano_do_resultado` (o plano COMPRAR/VENDER);
  (c) contar como `gatilhoAlinhado` em `regime._gatilho_alinhado`.
Critério da tabela completa: docs/adr/017-revisao-de-setups-e-selecao-dinamica.md.
"""
from app import regime, setups

APOSENTADOS_ESPERADOS = {
    "Ponto Contínuo (alta)", "Ponto Contínuo (baixa)",
    "Setup 9.2 (alta)", "Setup 9.2 (baixa)",
    "Inside Bar (baixa)",
    "Máx/Mín de Larry Williams — 9.4 (baixa)",
}


def test_lista_de_aposentados_bate_com_o_adr():
    assert setups.SETUPS_APOSENTADOS == APOSENTADOS_ESPERADOS


def _setup(nome, lado, confluencia, aposentado, gatilho=11.0, invalidacao=10.0):
    return {"nome": nome, "lado": lado, "confluencia": confluencia,
            "aposentado": aposentado, "gatilho": gatilho, "invalidacao": invalidacao,
            "alvoSugerido": None, "criterios": [], "referencia": "teste", "backtestavel": True}


def test_plano_do_resultado_ignora_aposentado_mesmo_com_confluencia_maior():
    # Setup 9.2 (aposentado) tem confluência maior E vem primeiro na lista —
    # sem o filtro, ele "venceria" por ser o direcionais[0].
    sres = {"setups": [
        _setup("Setup 9.2 (alta)", "alta", 100, True, gatilho=12.0, invalidacao=11.0),
        _setup("IFR2 (alta)", "alta", 80, False, gatilho=11.0, invalidacao=10.0),
    ]}
    plano = setups.plano_do_resultado(sres)
    assert plano["setup"] == "IFR2 (alta)"


def test_plano_do_resultado_sem_setup_operavel_nao_opera():
    sres = {"setups": [_setup("Setup 9.2 (alta)", "alta", 100, True)]}
    plano = setups.plano_do_resultado(sres)
    assert plano["decisao"] == "NÃO OPERAR"


def test_gatilho_alinhado_ignora_aposentado():
    resultado = {"setups": [_setup("Ponto Contínuo (alta)", "alta", 100, True)]}
    reg = {"regime": "tendencia_alta", "direcao": "alta"}
    assert regime._gatilho_alinhado(resultado, reg) is False


def test_gatilho_alinhado_conta_setup_operavel_normalmente():
    resultado = {"setups": [
        _setup("Ponto Contínuo (alta)", "alta", 100, True),
        _setup("IFR2 (alta)", "alta", 80, False),
    ]}
    reg = {"regime": "tendencia_alta", "direcao": "alta"}
    assert regime._gatilho_alinhado(resultado, reg) is True
