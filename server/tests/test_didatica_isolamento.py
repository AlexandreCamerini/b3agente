"""Camada de entendimento (Fase 1) — ISOLAMENTO e persistência.

A promessa central da spec é "o modo Operador fica intacto". Inspeção visual
não prova isso; estes testes provam.

A garantia aqui é ESTRUTURAL, não comportamental: a didática mora em rotas
NOVAS (`/api/conceitos`, `/api/conceito/{id}`) e `/api/timing` não foi tocado.
Por isso o guardião consegue ser tão forte — ele congela o contrato de saída do
timing e falha se qualquer campo novo vazar para lá, em qualquer modo.
"""
import os
import tempfile

import pytest

from app import conceitos, db, defaults, push, store, timing

# Contrato de saída do /api/timing ANTES da camada de entendimento existir.
# Campo novo aqui é mudança de contrato — se for intencional, mude a lista e
# diga por quê no commit. Se não for, é vazamento da didática.
CHAVES_TIMING = {
    "ticker", "modo", "estado", "frase", "ressalvas", "contexto15m",
    "vereditoDiario", "lado", "decisaoDiaria", "entrada", "stop",
    "riscoPorAcao", "setup", "fechamento15m", "asOf", "barraEmFormacao",
    "lacuna", "cobertura", "distancia", "distanciaEmR", "excedente",
    "excedenteEmR", "motivo", "foraDoPregao", "barraDeOutroDia",
}


@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as d:
        c = db.connect(os.path.join(d, "b3.db"))
        yield c
        c.close()


def _radar(entrada=38.0, stop=36.0):
    return {"results": [{"ticker": "PETR4", "veredito": "Estudar alta",
                         "plano": {"decisao": "COMPRAR", "lado": "alta",
                                   "entrada": entrada, "stop": stop,
                                   "riscoPorAcao": entrada - stop,
                                   "setup": "rompimento"}}]}


def _intra(close, as_of, at="2026-08-05T14:25:00-03:00"):
    """Formato REAL de `intraday.run_pass`: `resultados` é LISTA com `ticker`
    dentro, e `at` é o carimbo da passada (sem ele, `passada_fresca` é False e
    tudo vira `sem_dado` — o fixture mentiria em silêncio)."""
    return {"at": at, "asOf": as_of,
            "resultados": [{"ticker": "PETR4", "close": close, "asOf": as_of,
                            "cobertura": 1.0, "lacuna": False,
                            "barraEmFormacao": False}]}


# ------------------------------------------------------- isolamento do timing
@pytest.mark.parametrize("modo", ["operador", "estudo"])
def test_timing_nao_ganhou_campo_nenhum_com_a_didatica(modo):
    from datetime import datetime
    from app import intraday
    agora = datetime(2026, 8, 5, 14, 30, tzinfo=intraday.BRT)
    r = timing.montar(_radar(), _intra(37.4, "2026-08-05 14:15"), "PETR4", modo, agora=agora)
    extras = set(r) - CHAVES_TIMING
    assert extras == set(), f"campo novo vazou para /api/timing: {extras}"
    assert "conceito" not in r and "didatica" not in r


def test_didatica_desligada_nao_muda_o_timing():
    """A chave de desligamento é da camada nova; ligá-la não pode alterar por
    tabela o que o timing responde."""
    from datetime import datetime
    from app import intraday
    import os
    agora = datetime(2026, 8, 5, 14, 30, tzinfo=intraday.BRT)
    args = (_radar(), _intra(37.4, "2026-08-05 14:15"), "PETR4", "operador")
    antes = timing.montar(*args, agora=agora)
    os.environ["B3_DIDATICA_OFF"] = "1"
    try:
        assert timing.montar(*args, agora=agora) == antes
        assert conceitos.montar("gatilho", "operador", None) is None
    finally:
        os.environ.pop("B3_DIDATICA_OFF", None)


# ------------------------------------------------- persistência de conceitos
def test_conceitos_vistos_nasce_vazio_e_e_uniao_nunca_substituicao(conn):
    store.ensure_defaults(conn)
    assert store.get(conn, "config")["conceitosVistos"] == []
    store.set_config(conn, {"conceitosVistos": ["gatilho"]})
    # segundo aparelho marca OUTRO conceito e manda só o dele: não pode apagar
    store.set_config(conn, {"conceitosVistos": ["stop"]})
    assert store.get(conn, "config")["conceitosVistos"] == ["gatilho", "stop"]
    # repetido não duplica
    store.set_config(conn, {"conceitosVistos": ["gatilho"]})
    assert store.get(conn, "config")["conceitosVistos"] == ["gatilho", "stop"]


def test_notif_gatilho_nasce_desligada_e_e_aceita_pelo_set_config(conn):
    """Classe nova de alerta é opt-in. E a chave precisa estar na allowlist do
    set_config — fora dela, o PUT /api/config a descarta em SILÊNCIO (é o
    padrão de erro que já queimou o `agent.*`)."""
    store.ensure_defaults(conn)
    assert store.get(conn, "config")["notif"]["gatilho"] is False
    assert defaults.default_state()["config"]["notif"]["gatilho"] is False
    store.set_config(conn, {"notif": {"gatilho": True}})
    assert store.get(conn, "config")["notif"]["gatilho"] is True
    # e não atropelou as classes antigas
    assert store.get(conn, "config")["notif"]["stop"] is True


# ------------------------------------ Fase 0a: preferências do push no SERVIDOR
def test_push_prefs_nascem_opt_in_desligado(conn):
    """NOTA (quick task 260824-kc2, 2026-08-24) — o guardião MUDOU DE LADO em
    parte, e a distinção é a decisão de produto, não um detalhe:

      - classe de alerta genuinamente NOVA nasce DESLIGADA (opt-in). `gatilho`
        é o exemplo vivo e continua `False` — nada aqui regride.
      - CONTROLE de alerta que já EXISTIA e já chegava a todo mundo com token
        nasce LIGADO. `radar`/`execucao`/`protecao` são esse caso: até
        2026-08-24 os três call sites não consultavam preferência nenhuma, e
        nascer `False` TIRARIA notificação de quem a recebe hoje (decisão do
        Alex, travada).

    Por isso o nome do teste continua verdadeiro para o opt-in e as três
    classes ganharam asserção própria aqui em vez de arquivo separado — a
    tensão entre as duas regras tem que ficar visível no MESMO lugar."""
    p = push.prefs_for(conn, "u1")
    assert p["gatilho"] is False and p["universo"] == [] and p["modo"] == "estudo"
    assert p["radar"] is True and p["execucao"] is True and p["protecao"] is True


def test_push_prefs_gravam_consentimento_modo_e_universo(conn):
    p = push.set_prefs(conn, "u1", {"gatilho": True, "modo": "operador",
                                    "universo": ["petr4", "VALE3", "PETR4", ""]})
    assert p["gatilho"] is True and p["modo"] == "operador"
    assert p["universo"] == ["PETR4", "VALE3"]          # normaliza e deduplica
    assert push.prefs_for(conn, "u1")["universo"] == ["PETR4", "VALE3"]


def test_push_prefs_ignoram_chave_desconhecida_e_modo_invalido(conn):
    p = push.set_prefs(conn, "u1", {"gatilho": True, "modo": "xpto", "admin": True})
    assert p["modo"] == "estudo" and "admin" not in p


def test_universo_envelhece_e_para_de_valer(conn):
    import time
    p = push.set_prefs(conn, "u1", {"universo": ["PETR4"]})
    assert push.universo_valido(p) == ["PETR4"]
    futuro = time.time() + (push.VALIDADE_DIAS + 1) * 86400
    assert push.universo_valido(p, agora=futuro) == [], \
        "aparelho que parou de abrir o app não pode seguir gerando push sobre lista congelada"


def test_universo_sem_carimbo_nao_vale(conn):
    assert push.universo_valido({"universo": ["PETR4"], "at": None}) == []
    assert push.universo_valido({"universo": ["PETR4"], "at": "lixo"}) == []


def test_prefs_de_um_usuario_nao_vazam_para_outro(conn):
    push.set_prefs(conn, "u1", {"gatilho": True, "universo": ["PETR4"]})
    assert push.prefs_for(conn, "u2")["gatilho"] is False
    assert push.prefs_for(conn, "u2")["universo"] == []
