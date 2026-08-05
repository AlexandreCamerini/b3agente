"""F1 — timing de entrada (timing.py). O que estes testes protegem:

  • o timing é DETERMINÍSTICO: plano diário × barra 15m FECHADA, sem LLM;
  • ADR-002 Decisão 4: o veredito/confluência 15m NUNCA é gate — só contexto
    com a ressalva de calibragem;
  • Princípio 8 (não perseguir): além de 0,5R do gatilho => `esticado`;
  • série 15m com lacuna severa NÃO sustenta gatilho nem promove
    multiTimeframe (ADR-001 item 1d: série furada mente com cara de certa);
  • o vocabulário por modo vem do canônico (skill_ref.TIMING) — estudo sem
    verbo de ordem, mesa direta;
  • enriquecer_contexto é PURA: nunca muta o contexto do cache de snapshot.
"""
from datetime import datetime, timedelta, timezone

from app import intraday, skill_ref, timing

BRT = timezone(timedelta(hours=-3))

PLANO_COMPRA = {"decisao": "COMPRAR", "lado": "alta", "setup": "IFR2",
                "entrada": 40.0, "stop": 38.0, "alvo1": 42.0, "alvo2": 44.0,
                "riscoPorAcao": 2.0, "motivo": "x"}
PLANO_VENDA = {"decisao": "VENDER", "lado": "baixa", "setup": "PFR",
               "entrada": 40.0, "stop": 42.0, "alvo1": 38.0, "alvo2": 36.0,
               "riscoPorAcao": 2.0, "motivo": "x"}


def _r15(close, lacuna=False, cobertura=1.0, as_of="2026-08-03 15:15"):
    return {"ticker": "AAAA3", "close": close, "asOf": as_of,
            "barraEmFormacao": "2026-08-03 15:17", "lacuna": lacuna,
            "cobertura": cobertura, "veredito": "compra", "confluencia": 80,
            "melhorSetup": "IFR2"}


# ------------------------------ avaliar (núcleo puro) -----------------------

def test_sem_plano_quando_radar_nao_tem_decisao_operavel():
    for plano in (None, {"decisao": "AGUARDAR CONFIRMAÇÃO"},
                  {"decisao": "NÃO OPERAR", "motivo": "sem vantagem"},
                  {"decisao": "COMPRAR", "entrada": None, "riscoPorAcao": 2.0}):
        assert timing.avaliar(plano, _r15(39.0))["estado"] == "sem_plano"


def test_sem_dado_quando_passada_velha_ou_ausente():
    assert timing.avaliar(PLANO_COMPRA, None)["estado"] == "sem_dado"
    assert timing.avaliar(PLANO_COMPRA, _r15(41.0), passada_ok=False)["estado"] == "sem_dado"


def test_lacuna_severa_nao_sustenta_gatilho():
    r = timing.avaliar(PLANO_COMPRA, _r15(41.0, lacuna=True, cobertura=0.5))
    assert r["estado"] == "sem_dado"
    assert "lacuna severa" in r["motivo"]
    # lacuna LEVE (cobertura acima do piso) não bloqueia — só vira ressalva
    assert timing.avaliar(PLANO_COMPRA, _r15(41.0, lacuna=True, cobertura=0.9))["estado"] == "gatilho"


def test_armado_antes_do_gatilho_com_distancia_em_r():
    r = timing.avaliar(PLANO_COMPRA, _r15(39.0))
    assert r["estado"] == "armado"
    assert r["distancia"] == 1.0 and r["distanciaEmR"] == 0.5


def test_gatilho_na_barra_fechada_compra_e_venda():
    r = timing.avaliar(PLANO_COMPRA, _r15(40.5))
    assert r["estado"] == "gatilho" and r["excedenteEmR"] == 0.25
    r = timing.avaliar(PLANO_VENDA, _r15(39.5))
    assert r["estado"] == "gatilho"
    # venda NÃO dispara com preço subindo (lado importa)
    assert timing.avaliar(PLANO_VENDA, _r15(41.0))["estado"] == "armado"


def test_esticado_alem_de_meio_r_nao_perseguir():
    # risco 2.0 => zona = 1.0 além da entrada; 41.01 excede
    assert timing.avaliar(PLANO_COMPRA, _r15(41.01))["estado"] == "esticado"
    # exatamente na borda ainda é gatilho (<=)
    assert timing.avaliar(PLANO_COMPRA, _r15(41.0))["estado"] == "gatilho"


# ------------------------------ montar (vocabulário por modo) ---------------

def _radar(plano=PLANO_COMPRA):
    return {"results": [{"ticker": "AAAA3", "veredito": "compra", "plano": plano}]}


def _intra(close=40.5, at=None, **kw):
    return {"at": (at or datetime.now(BRT)).isoformat(),
            "resultados": [_r15(close, **kw)]}


def test_montar_estudo_sem_verbo_de_ordem_e_com_hora_da_barra():
    r = timing.montar(_radar(), _intra(), "AAAA3", "estudo")
    assert r["estado"] == "gatilho"
    assert r["frase"] == skill_ref.timing_txt("educacional", "gatilho", "15:15")
    assert "15:15" in r["frase"]
    for verbo in ("COMPRAR", "compre", "venda ", "entre agora"):
        assert verbo not in r["frase"]
    # honestidade: ressalva do atraso sempre presente
    assert any("atraso" in s for s in r["ressalvas"])


def test_montar_operador_fala_como_mesa():
    r = timing.montar(_radar(), _intra(), "AAAA3", "operador")
    assert r["frase"] == skill_ref.timing_txt("operador", "gatilho", "15:15")
    assert "ATINGIDO" in r["frase"]


def test_montar_contexto_15m_carrega_ressalva_de_calibragem():
    # ADR-002 Decisão 4: o veredito 15m é contexto, nunca critério
    r = timing.montar(_radar(), _intra(), "AAAA3", "estudo")
    assert r["contexto15m"]["aviso"] == timing.RESSALVA_CALIBRAGEM
    assert r["contexto15m"]["veredito"] == "compra"


def test_montar_passada_velha_vira_sem_dado():
    velha = _intra(at=datetime.now(BRT) - timedelta(seconds=intraday.FRESCURA_MAX_S + 60))
    r = timing.montar(_radar(), velha, "AAAA3", "estudo")
    assert r["estado"] == "sem_dado"


# --- fora do pregão: passada velha é o NORMAL, não avaria --------------------
# Das 18h às 10h a passada intraday está velha por definição. O estado segue
# `sem_dado` (não há timing a ler), mas acusar "sem dado confiável" fazia o card
# noturno parecer quebrado todo dia.

def test_avaliar_fora_do_pregao_marca_o_motivo_certo():
    r = timing.avaliar(PLANO_COMPRA, _r15(41.0), passada_ok=False, pregao_aberto=False)
    assert r["estado"] == "sem_dado"
    assert r["foraDoPregao"] is True
    assert "Fora do pregão" in r["motivo"]


def test_avaliar_dentro_do_pregao_passada_velha_segue_sendo_falta_de_dado():
    r = timing.avaliar(PLANO_COMPRA, _r15(41.0), passada_ok=False, pregao_aberto=True)
    assert r["estado"] == "sem_dado"
    assert not r.get("foraDoPregao")
    assert "fresca" in r["motivo"]


def test_montar_fora_do_pregao_troca_frase_e_ressalva():
    noite = datetime(2026, 8, 5, 2, 0, tzinfo=BRT)          # quarta, 2h da manhã
    velha = _intra(at=noite - timedelta(hours=8))
    r = timing.montar(_radar(), velha, "AAAA3", "estudo", agora=noite)
    assert r["estado"] == "sem_dado" and r["foraDoPregao"] is True
    assert "Fora do pregão" in r["frase"]
    assert "15:15" in r["frase"]                             # a hora da última barra
    assert any("Mercado fechado" in s for s in r["ressalvas"])
    # a ressalva de atraso do feed some: com o mercado fechado ela insinuaria
    # que existiria barra nova se o feed fosse melhor
    assert timing.RESSALVA_ATRASO not in r["ressalvas"]


def test_montar_dentro_do_pregao_mantem_a_frase_antiga():
    meio_dia = datetime(2026, 8, 5, 14, 0, tzinfo=BRT)
    velha = _intra(at=meio_dia - timedelta(seconds=intraday.FRESCURA_MAX_S + 60))
    r = timing.montar(_radar(), velha, "AAAA3", "estudo", agora=meio_dia)
    assert r["estado"] == "sem_dado" and not r.get("foraDoPregao")
    assert r["frase"] == skill_ref.timing_txt("educacional", "sem_dado")
    assert timing.RESSALVA_ATRASO in r["ressalvas"]


def test_montar_ativo_fora_do_radar():
    r = timing.montar({"results": []}, _intra(), "AAAA3", "estudo")
    assert r["estado"] == "sem_plano"
    assert "Radar" in r["motivo"]


# ------------------------------ enriquecer_contexto (A6b) -------------------

def test_enriquecer_promove_multitimeframe_e_nao_muta_o_original():
    ctx = {"dataQuality": {"multiTimeframe": False}, "close": 40.0}
    novo = timing.enriquecer_contexto(ctx, _r15(40.5), True)
    assert novo["dataQuality"]["multiTimeframe"] is True
    assert novo["intraday15m"]["close"] == 40.5
    assert novo["intraday15m"]["aviso"] == timing.RESSALVA_CALIBRAGEM
    # o contexto ORIGINAL (cache de snapshot compartilhado) ficou intacto
    assert ctx["dataQuality"]["multiTimeframe"] is False
    assert "intraday15m" not in ctx


def test_enriquecer_lacuna_severa_anexa_mas_nao_promove():
    ctx = {"dataQuality": {"multiTimeframe": False}}
    novo = timing.enriquecer_contexto(ctx, _r15(40.5, lacuna=True, cobertura=0.5), True)
    assert novo["dataQuality"]["multiTimeframe"] is False  # série furada não confirma
    assert novo["intraday15m"]["lacuna"] is True           # mas o contexto é honesto


def test_enriquecer_sem_passada_fresca_devolve_intacto():
    ctx = {"dataQuality": {}}
    assert timing.enriquecer_contexto(ctx, _r15(40.5), False) is ctx
    assert timing.enriquecer_contexto(ctx, None, True) is ctx


# ------------------------------ frescura da passada -------------------------

def test_passada_fresca_por_idade():
    agora = datetime(2026, 8, 3, 15, 30, tzinfo=BRT)
    ok = {"at": (agora - timedelta(minutes=20)).isoformat(), "resultados": []}
    velha = {"at": (agora - timedelta(minutes=45)).isoformat(), "resultados": []}
    assert intraday.passada_fresca(ok, agora=agora) is True
    assert intraday.passada_fresca(velha, agora=agora) is False
    assert intraday.passada_fresca(None, agora=agora) is False
    assert intraday.passada_fresca({"at": "não-é-data"}, agora=agora) is False
