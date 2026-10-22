"""FASE 7 (F7.1) — plano operacional determinístico do Modo Operador.

Regras trancadas (persona analise-tecnica-b3, aplicadas objetivamente):
  • R:R mínimo 1,5:1 no alvo final ⇒ abaixo disso, NÃO OPERAR;
  • gatilho rompido além de 0,5R ⇒ não perseguir (NÃO OPERAR);
  • rompido dentro da zona ⇒ entrada a mercado com R:R RECALCULADO do preço real;
  • compressão (neutro) ⇒ AGUARDAR CONFIRMAÇÃO; sem setup ⇒ NÃO OPERAR;
  • stop é SEMPRE a invalidação do setup (nunca arbitrário);
  • geometria incoerente (stop do lado errado) ⇒ NÃO OPERAR.
Stdlib-only; roda standalone e via pytest.

Fase 50 (D-01/D-02/D-04): o lado de ALTA sai de setups.marcos_do_plano — stop =
invalidação − 0,1×ATR, alvo na primeira resistência relevante (ou entrada+2R),
alvo único; sem ATR o plano é NÃO OPERAR. O lado de BAIXA segue a regra antiga.
Os casos de alta abaixo passam `niveis` (ATR 0,50) e foram atualizados, não apagados.
"""
from app import setups

# Fase 50: ATR(14) = 0,50 sem resistências — o alvo cai na projeção de 2R.
NIVEIS = {"atr": 0.50, "suportes": [], "resistencias": []}


def _setup(lado="alta", gatilho=38.55, invalidacao=37.60, alvo=None, nome="IFR2 (Larry Connors)"):
    return {"nome": nome, "lado": lado, "gatilho": gatilho, "invalidacao": invalidacao,
            "alvoSugerido": alvo, "confluencia": 72, "criterios": []}


def test_compra_no_rompimento_com_rr_ok():
    p = setups.plano_operacional(_setup(), close=38.29, niveis=NIVEIS)  # abaixo do gatilho
    assert p["decisao"] == setups.DECISAO_COMPRAR
    assert p["tipo"].startswith("no rompimento")
    # Fase 50 (D-01/D-02): stop 37,60 → 37,55 (folga 0,1×ATR); 1R/2R medidos do
    # novo risco (1,00): 39,50/40,45 → 39,55/40,55; atualizado, não apagado.
    assert p["entrada"] == 38.55 and p["stop"] == 37.55
    assert p["alvo1"] == 39.55 and p["alvo2"] == 40.55 and p["alvo"] == 40.55
    assert p["rr1"] == 1.0 and p["rr2"] == 2.0
    assert p["riscoPorAcao"] == 1.0
    assert p["gatilho"] == 38.55 and p["invalidacao"] == 37.60
    assert "R:R 2.0:1" in p["motivo"].replace(",", ".")


def test_venda_espelhada():
    p = setups.plano_operacional(_setup(lado="baixa", gatilho=37.60, invalidacao=38.55), close=37.90)
    assert p["decisao"] == setups.DECISAO_VENDER
    assert p["stop"] == 38.55 and p["alvo2"] == 35.70    # 2R para baixo


def test_rr_abaixo_do_minimo_nao_opera():
    # Fase 50 (D-02): o `alvoSugerido` do setup deixou de mandar na alta; o teto
    # vem da primeira resistência. Resistência em 39,30 ⇒ R:R 0,75 < 1,5 ⇒ corta
    # ("teto próximo demais"; antes: "vantagem estatística"). Atualizado, não apagado.
    niveis = {**NIVEIS, "resistencias": [39.30]}
    p = setups.plano_operacional(_setup(alvo=39.50), close=38.00, niveis=niveis)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "Teto próximo demais" in p["motivo"]


def test_gatilho_rompido_dentro_da_zona_entra_a_mercado_com_rr_real():
    # close 38.90 = gatilho + 0.35 (0,37R, dentro de 0,5R) ⇒ entrada a mercado,
    # DESDE que o R:R recalculado do preço real ainda passe (alvo largo: 41.20).
    # Fase 50 (D-02): o alvo largo agora é uma resistência em 41,20 (não mais o
    # alvoSugerido); stop 37,55 ⇒ R:R (41,20-38,90)/1,35 ≈ 1,70. Atualizado.
    niveis = {**NIVEIS, "resistencias": [41.20]}
    p = setups.plano_operacional(_setup(alvo=41.20), close=38.90, niveis=niveis)
    assert p["decisao"] == setups.DECISAO_COMPRAR
    assert p["tipo"].startswith("a mercado")
    assert p["entrada"] == 38.90
    assert p["rr2"] >= 1.5


def test_perseguicao_de_preco_corta_pelo_rr_real():
    # dentro da zona, mas o R:R do preço real ficou < 1,5 ⇒ NÃO OPERAR
    # Fase 50: com niveis (antes passava pelo motivo errado, sem ATR). Resistência
    # em 39,90 ⇒ R:R do preço real (39,90-38,90)/1,35 ≈ 0,74 < 1,5 ⇒ NÃO OPERAR.
    niveis = {**NIVEIS, "resistencias": [39.90]}
    p = setups.plano_operacional(_setup(), close=38.90, niveis=niveis)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "Teto próximo demais" in p["motivo"]


def test_esticado_alem_da_zona_nao_persegue():
    # close 39.20 = gatilho + 0.65 (>0,5R = 0.475) ⇒ esticado
    # Fase 50: precisa de `niveis` — sem ATR o motor recusa antes da perseguição.
    p = setups.plano_operacional(_setup(alvo=45.00), close=39.20, niveis=NIVEIS)
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
    sres["niveis"] = NIVEIS  # Fase 50: detect_setups anexa os níveis; o plano os repassa
    p = setups.plano_do_resultado(sres, close=38.29)
    assert p["decisao"] == setups.DECISAO_COMPRAR and p["setup"].startswith("IFR2")
    # só neutro ⇒ AGUARDAR; vazio ⇒ NÃO OPERAR
    assert setups.plano_do_resultado({"setups": [{"nome": "C", "lado": "neutro"}]})["decisao"] == setups.DECISAO_AGUARDAR
    assert setups.plano_do_resultado({"setups": []})["decisao"] == setups.DECISAO_NAO_OPERAR


def test_plano_nao_flipa_contra_o_lado_dominante():
    """P1 (medido em produção, VALE3): o melhor direcional é BAIXA (define o
    veredito 'Estudar baixa'), mas não tem níveis; um setup de ALTA abaixo tem.
    O plano NÃO pode virar COMPRAR contra a confluência (Princípios 9 e 4) —
    fica no lado dominante: VENDER se houver níveis, senão AGUARDAR."""
    # dominante baixa SEM níveis + alta COM níveis abaixo ⇒ nunca COMPRAR
    sres = {"setups": [
        {"nome": "Pullback à média", "lado": "baixa", "confluencia": 100},  # topo, sem níveis
        {"nome": "Setup 9.2", "lado": "alta", "confluencia": 86,
         "gatilho": 78.0, "invalidacao": 74.0, "alvoSugerido": 84.0},
    ]}
    p = setups.plano_do_resultado(sres, close=75.24)
    assert p["decisao"] != setups.DECISAO_COMPRAR
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR   # lado dominante sem níveis executáveis
    # dominante baixa COM níveis ⇒ VENDER (não COMPRAR do setup de alta)
    sres2 = {"setups": [
        {"nome": "123 de topo", "lado": "baixa", "confluencia": 100,
         "gatilho": 74.0, "invalidacao": 78.0, "alvoSugerido": 66.0},
        {"nome": "Setup 9.2", "lado": "alta", "confluencia": 86,
         "gatilho": 78.0, "invalidacao": 74.0, "alvoSugerido": 84.0},
    ]}
    assert setups.plano_do_resultado(sres2, close=75.24)["decisao"] == setups.DECISAO_VENDER


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
