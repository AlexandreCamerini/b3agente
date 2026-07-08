"""FASE 7 (F7.1) — plano operacional determinístico do Modo Operador.

Regras trancadas (persona analise-tecnica-b3, aplicadas objetivamente):
  • R:R mínimo 1,5:1 no alvo final ⇒ abaixo disso, NÃO OPERAR;
  • gatilho rompido além de 0,5R ⇒ não perseguir (NÃO OPERAR);
  • rompido dentro da zona ⇒ entrada a mercado com R:R RECALCULADO do preço real;
  • compressão (neutro) ⇒ AGUARDAR CONFIRMAÇÃO; sem setup ⇒ NÃO OPERAR;
  • stop é SEMPRE a invalidação do setup (nunca arbitrário);
  • geometria incoerente (stop do lado errado) ⇒ NÃO OPERAR.
Stdlib-only; roda standalone e via pytest.
"""
from app import setups


def _setup(lado="alta", gatilho=38.55, invalidacao=37.60, alvo=None, nome="IFR2 (Larry Connors)"):
    return {"nome": nome, "lado": lado, "gatilho": gatilho, "invalidacao": invalidacao,
            "alvoSugerido": alvo, "confluencia": 72, "criterios": []}


def test_compra_no_rompimento_com_rr_ok():
    p = setups.plano_operacional(_setup(), close=38.29)  # abaixo do gatilho
    assert p["decisao"] == setups.DECISAO_COMPRAR
    assert p["tipo"].startswith("no rompimento")
    assert p["entrada"] == 38.55 and p["stop"] == 37.60
    assert p["alvo1"] == 39.50 and p["alvo2"] == 40.45   # 1R e 2R do gatilho
    assert p["rr1"] == 1.0 and p["rr2"] == 2.0
    assert p["riscoPorAcao"] == 0.95
    assert "R:R 2.0:1" in p["motivo"].replace(",", ".")


def test_venda_espelhada():
    p = setups.plano_operacional(_setup(lado="baixa", gatilho=37.60, invalidacao=38.55), close=37.90)
    assert p["decisao"] == setups.DECISAO_VENDER
    assert p["stop"] == 38.55 and p["alvo2"] == 35.70    # 2R para baixo


def test_rr_abaixo_do_minimo_nao_opera():
    # alvo explícito do setup a apenas 1R ⇒ rr2 = 1.0 < 1.5 ⇒ corta
    p = setups.plano_operacional(_setup(alvo=39.50), close=38.00)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "vantagem estatística" in p["motivo"]


def test_gatilho_rompido_dentro_da_zona_entra_a_mercado_com_rr_real():
    # close 38.90 = gatilho + 0.35 (0,37R, dentro de 0,5R) ⇒ entrada a mercado,
    # DESDE que o R:R recalculado do preço real ainda passe (alvo largo: 41.20).
    p = setups.plano_operacional(_setup(alvo=41.20), close=38.90)
    assert p["decisao"] == setups.DECISAO_COMPRAR
    assert p["tipo"].startswith("a mercado")
    assert p["entrada"] == 38.90
    assert p["rr2"] >= 1.5  # (41.20-38.90)/1.30 ≈ 1.77


def test_perseguicao_de_preco_corta_pelo_rr_real():
    # dentro da zona, mas o R:R do preço real ficou < 1,5 ⇒ NÃO OPERAR
    p = setups.plano_operacional(_setup(), close=38.90)  # rr2 real ≈ 1.19
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR


def test_esticado_alem_da_zona_nao_persegue():
    # close 39.20 = gatilho + 0.65 (>0,5R = 0.475) ⇒ esticado
    p = setups.plano_operacional(_setup(alvo=45.00), close=39.20)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "esticado" in p["motivo"]


def test_neutro_aguarda_confirmacao():
    p = setups.plano_operacional({"nome": "Compressão", "lado": "neutro"}, close=10.0)
    assert p["decisao"] == setups.DECISAO_AGUARDAR
    assert "rompimento" in p["motivo"]


def test_geometria_incoerente_nao_opera():
    # compra com stop ACIMA do gatilho é plano impossível
    p = setups.plano_operacional(_setup(gatilho=37.60, invalidacao=38.55), close=37.00)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR


def test_sem_setup_ou_sem_numeros_nao_opera():
    assert setups.plano_operacional(None)["decisao"] == setups.DECISAO_NAO_OPERAR
    p = setups.plano_operacional(_setup(gatilho=None), close=10)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR


def test_plano_do_resultado_prioriza_direcional():
    sres = {"setups": [
        {"nome": "Compressão", "lado": "neutro", "confluencia": 80},
        _setup(),
    ]}
    p = setups.plano_do_resultado(sres, close=38.29)
    assert p["decisao"] == setups.DECISAO_COMPRAR and p["setup"].startswith("IFR2")
    # só neutro ⇒ AGUARDAR; vazio ⇒ NÃO OPERAR
    assert setups.plano_do_resultado({"setups": [{"nome": "C", "lado": "neutro"}]})["decisao"] == setups.DECISAO_AGUARDAR
    assert setups.plano_do_resultado({"setups": []})["decisao"] == setups.DECISAO_NAO_OPERAR


def test_vocabulario_do_modo_estudo_intocado():
    # guardrail: detect_setups segue com o veredito EDUCACIONAL — o plano é
    # um campo paralelo e não altera o shape/vocabulário existente.
    r = setups.detect_setups([], {})
    assert r["veredito"] in ("Estudar alta", "Estudar baixa", "Monitorar", "Sem setup no momento")
    assert "plano" not in r


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DO PLANO OPERACIONAL PASSARAM")
