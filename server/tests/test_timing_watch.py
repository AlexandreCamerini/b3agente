"""Fase 0b — o vigia do gatilho (push de condição atingida).

Um push é a única coisa do app que interrompe a pessoa FORA do app, sem o
contexto da tela. Num produto de mercado isso é a superfície mais perigosa que
existe, e cada teste aqui trava uma regra que uma revisão de risco impôs.

Os três que o supervisor condicionou à aprovação:
  (a) sem consentimento SERVER-SIDE, zero push — e a preferência é lida de
      onde ela realmente mora, não de `config` (que no iPhone é local);
  (b) reinício do processo com o kv preservado NÃO reemite o mesmo evento;
  (c) o teto é por (usuário, ticker, dia) E por usuário/dia, provado com a
      sequência armado → gatilho → armado → gatilho em barras distintas —
      que é o caso que o dedupe por `asOf` deixa passar de propósito.
"""
import asyncio
import os
import tempfile
from datetime import datetime

import pytest

from app import db, intraday, push, store, timing_watch

HOJE = "2026-08-05"
AGORA = datetime(2026, 8, 5, 14, 30, tzinfo=intraday.BRT)   # pregão aberto


@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as d:
        c = db.connect(os.path.join(d, "b3.db"))
        yield c
        c.close()


@pytest.fixture(autouse=True)
def _sem_kill():
    os.environ.pop("B3_TIMING_PUSH_KILL", None)
    # `_ULTIMA_BARRA` é estado de MÓDULO (por processo, de propósito: é o que
    # evita revarrer a mesma barra). Entre testes ele precisa ser zerado, ou um
    # teste envenena o seguinte com a barra que ele já marcou.
    timing_watch._ULTIMA_BARRA["asOf"] = None
    yield
    os.environ.pop("B3_TIMING_PUSH_KILL", None)
    timing_watch._ULTIMA_BARRA["asOf"] = None


def _radar(*tickers):
    return {"results": [{"ticker": t, "veredito": "Estudar alta",
                         "plano": {"decisao": "COMPRAR", "lado": "alta",
                                   "entrada": 38.5, "stop": 36.2,
                                   "riscoPorAcao": 2.3, "setup": "rompimento"}}
                        for t in tickers]}


def _intra(closes: dict, hora="14:15", dia=HOJE, at=None):
    """Espelha o formato REAL de `intraday.run_pass`: `resultados` é uma LISTA
    com `ticker` dentro (não um dict indexado), e `at` é o carimbo isoformat da
    passada — sem ele `passada_fresca` devolve False e todo estado vira
    `sem_dado`, que é o bug que este fixture já escondeu uma vez."""
    as_of = f"{dia} {hora}"
    return {"at": (at or AGORA.replace(minute=25)).isoformat(),
            "asOf": as_of, "atLabel": hora,
            "resultados": [{"ticker": t, "close": c, "asOf": as_of,
                            "cobertura": 1.0, "lacuna": False,
                            "barraEmFormacao": False}
                           for t, c in closes.items()]}


class _Espiao:
    def __init__(self):
        self.enviados = []

    async def __call__(self, uid, titulo, corpo, tickers):
        self.enviados.append({"uid": uid, "titulo": titulo, "corpo": corpo,
                              "tickers": tickers})


def _com_push(conn, uid, gatilho=True, universo=("PETR4",)):
    push.register_token(conn, uid, "tok-" + uid)
    push.set_prefs(conn, uid, {"gatilho": gatilho, "universo": list(universo)})


def _rodar(conn, radar, intra, espiao):
    return asyncio.run(timing_watch.rodar(conn, radar, intra, espiao, agora=AGORA))


# ------------------------------------------------------ (a) consentimento
def test_sem_consentimento_server_side_nenhum_push(conn):
    """A preferência é lida de `pushPrefs`, não de `config`. No iPhone a config
    é LOCAL — o servidor nunca a vê, e era por isso que o interruptor não
    desligava nada."""
    _com_push(conn, "u1", gatilho=False)
    # e a `config` do MESMO usuário dizendo que sim: não pode valer
    store.set_config(conn, {"notif": {"enabled": True, "gatilho": True}}, user_id="u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert e.enviados == []


def test_sem_aparelho_registrado_nenhum_push(conn):
    push.set_prefs(conn, "u1", {"gatilho": True, "universo": ["PETR4"]})  # sem token
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert e.enviados == []


def test_universo_envelhecido_nao_gera_push(conn):
    """Aparelho que parou de abrir o app não segue pushando sobre a lista de
    ontem — `universo_valido` já expira, aqui o vigia respeita."""
    _com_push(conn, "u1")
    p = push.prefs_for(conn, "u1")
    p["at"] = "2020-01-01T00:00:00"
    db.kv_set(conn, "pushPrefs", p, user_id="u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert e.enviados == []


def test_com_consentimento_avisa_uma_vez(conn):
    _com_push(conn, "u1")
    e = _Espiao()
    n = _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert n == 1 and len(e.enviados) == 1
    assert e.enviados[0]["tickers"] == ["PETR4"]


# ------------------------------------------------- (b) reinício do processo
def test_reinicio_com_kv_preservado_nao_reemite(conn):
    """Simula o deploy: o kv sobrevive, o processo não. O estado do vigia mora
    no kv exatamente por isso — em memória, todo deploy reemitiria tudo."""
    _com_push(conn, "u1")
    radar, intra = _radar("PETR4"), _intra({"PETR4": 39.0})
    e1 = _Espiao()
    _rodar(conn, radar, intra, e1)
    assert len(e1.enviados) == 1
    # "reinício": módulo recarregado, nada em memória — só o kv permanece
    import importlib
    importlib.reload(timing_watch)
    e2 = _Espiao()
    _rodar(conn, radar, intra, e2)
    assert e2.enviados == [], "o mesmo evento foi reemitido depois do reinício"


def test_estado_so_e_gravado_quando_muda(conn):
    """Um kv_set por usuário por tick seria um commit por usuário na conexão
    SQLite compartilhada com a API inteira, ~96×/usuário/dia."""
    _com_push(conn, "u1")
    radar, intra = _radar("PETR4"), _intra({"PETR4": 37.0})   # armado, sem evento
    _rodar(conn, radar, intra, _Espiao())
    antes = db.kv_get(conn, "timingWatch", None, user_id="u1")
    escritas = []
    orig = db.kv_set

    def _espiao_set(c, k, v, user_id=None):
        if k == "timingWatch":
            escritas.append(v)
        return orig(c, k, v, user_id=user_id)
    db.kv_set = _espiao_set
    try:
        _rodar(conn, radar, intra, _Espiao())   # nada mudou
    finally:
        db.kv_set = orig
    assert escritas == [], "gravou sem nada ter mudado"
    assert db.kv_get(conn, "timingWatch", None, user_id="u1") == antes


# ------------------------------------------------------------ (c) os tetos
def test_oscilacao_em_torno_da_entrada_avisa_UMA_vez_no_dia(conn):
    """armado → gatilho → armado → gatilho em quatro barras distintas. Cada uma
    tem `asOf` diferente e passaria pelo dedupe por barra legitimamente — é
    exatamente o caso que exige teto por (usuário, ticker, DIA)."""
    _com_push(conn, "u1")
    e = _Espiao()
    radar = _radar("PETR4")
    for hora, close in (("14:00", 37.0), ("14:15", 39.0), ("14:30", 37.0), ("14:45", 39.0)):
        _rodar(conn, radar, _intra({"PETR4": close}, hora=hora), e)
    assert len(e.enviados) == 1, f"avisou {len(e.enviados)}× sobre o mesmo ativo no mesmo dia"


def test_gatilho_que_permanece_nao_reavisa(conn):
    _com_push(conn, "u1")
    e = _Espiao()
    radar = _radar("PETR4")
    _rodar(conn, radar, _intra({"PETR4": 39.0}, hora="14:15"), e)
    _rodar(conn, radar, _intra({"PETR4": 39.2}, hora="14:30"), e)
    assert len(e.enviados) == 1


def test_teto_por_usuario_por_dia(conn):
    universo = [f"AAA{i}" for i in range(timing_watch.MAX_POR_DIA + 3)]
    _com_push(conn, "u1", universo=universo)
    e = _Espiao()
    # um por vez, em barras distintas, para não cair na agregação
    for i, t in enumerate(universo):
        hora = "1%d:15" % (i % 10)
        _rodar(conn, _radar(t), _intra({t: 39.0}, hora=hora), e)
    total = sum(len(x["tickers"]) for x in e.enviados)
    assert total == timing_watch.MAX_POR_DIA


def test_virada_do_dia_libera_de_novo(conn):
    _com_push(conn, "u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    est = db.kv_get(conn, "timingWatch", None, user_id="u1")
    est["dia"] = "2026-08-04"                      # "ontem"
    db.kv_set(conn, "timingWatch", est, user_id="u1")
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert len(e.enviados) == 2


# --------------------------------------------- honestidade da mensagem
def test_titulo_carrega_a_hora_da_barra(conn):
    """ADR-001: afirmação de timing carrega o carimbo. No iOS o TÍTULO é a
    única parte garantida na tela de bloqueio — o corpo trunca, então carimbo
    no corpo é carimbo que some."""
    _com_push(conn, "u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}, hora="14:15"), e)
    assert "14:15" in e.enviados[0]["titulo"]
    assert "PETR4" in e.enviados[0]["titulo"]


def test_corpo_usa_a_frase_canonica_e_diz_que_nada_foi_comprado(conn):
    from app import skill_ref
    _com_push(conn, "u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}, hora="14:15"), e)
    corpo = e.enviados[0]["corpo"]
    assert skill_ref.timing_txt("educacional", "gatilho", "14:15") in corpo
    assert "Nada foi comprado" in corpo
    assert "pode ter mudado" in corpo   # a idade e a reversibilidade do dado


def test_vocabulario_e_de_ESTUDO_mesmo_para_quem_esta_no_operador(conn):
    """Canal interruptivo, fora do app, sem contexto de tela, não é lugar para
    a linguagem mais assertiva. Quem está no Operador tem o app."""
    _com_push(conn, "u1")
    push.set_prefs(conn, "u1", {"modo": "operador"})
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    corpo = e.enviados[0]["corpo"]
    assert "condição de estudo" in corpo.lower()
    assert "gatilho de entrada atingido" not in corpo.lower()


def test_falha_na_varredura_nao_queima_a_barra(conn):
    """Marcar a barra como varrida ANTES de varrer faria uma falha transitória
    (kv, radar malformado) apagar os gatilhos daquela barra em silêncio, sem
    nova tentativa no próximo tick."""
    _com_push(conn, "u1")
    intra = _intra({"PETR4": 39.0})

    async def _explode(*a, **k):
        raise RuntimeError("kv fora do ar")
    orig = timing_watch.rodar
    timing_watch.rodar = _explode
    try:
        assert asyncio.run(timing_watch.maybe_run(conn, _radar("PETR4"), intra,
                                                  _Espiao(), agora=AGORA)) == 0
    finally:
        timing_watch.rodar = orig
    e = _Espiao()
    n = asyncio.run(timing_watch.maybe_run(conn, _radar("PETR4"), intra, e, agora=AGORA))
    assert n == 1 and len(e.enviados) == 1, "a barra foi queimada pela falha"


def test_mesma_barra_nao_e_varrida_duas_vezes(conn):
    """A passada intraday roda a cada ~4 min; a barra de 15m muda de 15 em 15.
    Sem gate por `asOf` o vigia varreria ~3× por barra — inofensivo, mas é
    trabalho jogado fora, e o comentário que dizia o contrário era falso."""
    _com_push(conn, "u1")
    e = _Espiao()
    intra = _intra({"PETR4": 39.0})
    n1 = asyncio.run(timing_watch.maybe_run(conn, _radar("PETR4"), intra, e, agora=AGORA))
    n2 = asyncio.run(timing_watch.maybe_run(conn, _radar("PETR4"), intra, e, agora=AGORA))
    assert n1 == 1 and n2 == 0


def test_abertura_com_varios_ativos_agrega_em_UMA_mensagem(conn):
    """Na primeira barra do dia vários ativos abrem já além da entrada. N
    banners simultâneos sobre cruzamentos que aconteceram antes de a pessoa
    acordar para o pregão é assédio, não serviço."""
    _com_push(conn, "u1", universo=["PETR4", "VALE3", "BBAS3"])
    e = _Espiao()
    _rodar(conn, _radar("PETR4", "VALE3", "BBAS3"),
           _intra({"PETR4": 39.0, "VALE3": 39.0, "BBAS3": 39.0}), e)
    assert len(e.enviados) == 1
    assert len(e.enviados[0]["tickers"]) == 3
    assert "3 ativos" in e.enviados[0]["titulo"]


# ------------------------------------------------ estados que NÃO notificam
def test_esticado_nao_notifica_e_consome_a_vaga_do_dia(conn):
    """Entre a barra fechar e o push chegar correm ~15 min de atraso do feed
    mais o intervalo do laço. Se nesse tempo o preço esticou, avisar seria
    convocar a pessoa para uma entrada que o próprio app desaconselha."""
    _com_push(conn, "u1")
    e = _Espiao()
    # 41,0 com entrada 38,5 e risco 2,3 ⇒ excedente 2,5 > 0,5R ⇒ esticado
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 41.0}), e)
    assert e.enviados == []


def test_armado_e_sem_plano_nao_notificam(conn):
    _com_push(conn, "u1", universo=["PETR4", "XPTO3"])
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 37.0}), e)
    assert e.enviados == []


def test_barra_do_pregao_anterior_nao_notifica(conn):
    """Nos primeiros minutos do dia a última barra FECHADA ainda é a de ontem.
    Sem esta guarda, todo mundo receberia 'condição atingida' na abertura por
    um cruzamento do pregão anterior."""
    _com_push(conn, "u1")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}, dia="2026-08-04"), e)
    assert e.enviados == []


def test_fora_do_pregao_o_hook_nem_roda(conn):
    _com_push(conn, "u1")
    e = _Espiao()
    noite = datetime(2026, 8, 5, 22, 0, tzinfo=intraday.BRT)
    n = asyncio.run(timing_watch.maybe_run(conn, _radar("PETR4"),
                                           _intra({"PETR4": 39.0}), e, agora=noite))
    assert n == 0 and e.enviados == []


# --------------------------------------------------------- kill switch
def test_kill_switch_desliga_a_classe_inteira(conn):
    _com_push(conn, "u1")
    os.environ["B3_TIMING_PUSH_KILL"] = "1"
    e = _Espiao()
    n = _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert n == 0 and e.enviados == []


# -------------------------------------------------- isolamento entre usuários
def test_um_usuario_nao_consome_o_teto_do_outro(conn):
    _com_push(conn, "u1")
    _com_push(conn, "u2")
    e = _Espiao()
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), e)
    assert sorted(x["uid"] for x in e.enviados) == ["u1", "u2"]


def test_falha_no_envio_de_um_usuario_nao_derruba_o_resto(conn):
    _com_push(conn, "u1")
    _com_push(conn, "u2")
    vistos = []

    async def _instavel(uid, titulo, corpo, tickers):
        if uid == "u1":
            raise RuntimeError("APNs fora do ar")
        vistos.append(uid)
    _rodar(conn, _radar("PETR4"), _intra({"PETR4": 39.0}), _instavel)
    assert vistos == ["u2"]
