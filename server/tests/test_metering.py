"""FASE 3 (item 2) — metering da IA gerenciada: cota diária, reset por dia e
rate limit por usuário, isolados por escopo. Stdlib; roda standalone e via pytest.

2026-09-10 (auditoria A-07) — acrescentados os testes de RESERVA: a corrida
reproduzida pela auditoria (três concorrentes com `used=quota-1` passando
todas) e a propriedade que não pode quebrar junto com a correção, "falha não
gasta cota".
"""
import os
import tempfile
import threading
import time

from app import db, metering


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_meter_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _fresh_db_threads():
    """A-07: `db.connect` devolve conexão sqlite AMARRADA à thread que a criou
    — usá-la em outra levanta ProgrammingError e o teste de corrida morreria
    sem testar nada. `db.shared()` é o que `main.py` usa: uma conexão real por
    thread, que é justamente o arranjo onde a corrida existe."""
    d = tempfile.mkdtemp(prefix="b3_meter_cc_")
    conn = db.shared(os.path.join(d, "b3_agente.db"))
    db.init_db(conn)
    return conn


def test_cota_diaria_consome_e_bloqueia():
    conn = _fresh_db()
    uid = "u1"
    for _ in range(3):
        ok, reason = metering.check(conn, uid, quota=3, rate_per_min=100)
        assert ok, reason
        metering.consume(conn, uid)
    # 4ª: cota estourada
    ok, reason = metering.check(conn, uid, quota=3, rate_per_min=100)
    assert ok is False
    assert "limite diário" in reason
    snap = metering.snapshot(conn, uid, 3)
    assert snap["used"] == 3 and snap["remaining"] == 0
    conn.close()


def test_cota_isolada_por_usuario():
    conn = _fresh_db()
    metering.check(conn, "a", quota=2, rate_per_min=100); metering.consume(conn, "a")
    metering.check(conn, "a", quota=2, rate_per_min=100); metering.consume(conn, "a")
    # A estourou; B intacto
    assert metering.check(conn, "a", quota=2, rate_per_min=100)[0] is False
    assert metering.check(conn, "b", quota=2, rate_per_min=100)[0] is True
    assert metering.snapshot(conn, "b", 2)["used"] == 0
    conn.close()


def test_reset_diario():
    conn = _fresh_db()
    uid = "u2"
    # simula uso de ONTEM gravado direto no kv
    db.kv_set(conn, "aiUsage", {"day": "2000-01-01", "count": 99, "rl": []}, user_id=uid)
    # _load deve resetar porque o dia mudou
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=100)
    assert ok is True
    assert metering.snapshot(conn, uid, 5)["used"] == 0
    conn.close()


def test_rate_limit_por_minuto():
    conn = _fresh_db()
    uid = "u3"
    t0 = 1_000_000.0
    # 3 permitidas na janela; a 4ª no mesmo segundo bloqueia
    for i in range(3):
        ok, _ = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + i * 0.1)
        assert ok is True
    ok, reason = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + 0.4)
    assert ok is False and "Muitas análises" in reason
    # 61s depois a janela deslizou => liberado de novo
    ok, _ = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + 61)
    assert ok is True
    conn.close()


def test_quota_none_ilimitada():
    conn = _fresh_db()
    uid = "u4"
    for _ in range(50):
        ok, _ = metering.check(conn, uid, quota=None, rate_per_min=1000)
        assert ok is True
        metering.consume(conn, uid)
    assert metering.snapshot(conn, uid, None)["remaining"] is None
    conn.close()


# ---------------------------------------------------------------------------
# A-07 (auditoria 2026-09-10) — reserva atômica.
# ---------------------------------------------------------------------------
def _corrida(conn, uid, *, quota, n=3, espera=0.25, cap_global=None):
    """Dispara `n` requisições concorrentes que fazem check → espera → consume.
    A espera É o defeito: na rota real é o fetch de candles + a chamada ao
    modelo (até 60 s). Barreira para que TODO check aconteça antes de qualquer
    consume — é esse intercalamento que a auditoria reproduziu."""
    barreira = threading.Barrier(n)
    passaram = []
    trava = threading.Lock()

    def req():
        barreira.wait()
        ok, _ = metering.check(conn, uid, quota=quota, rate_per_min=1000,
                               cap_global=cap_global)
        if not ok:
            return
        with trava:
            passaram.append(1)
        time.sleep(espera)
        metering.consume(conn, uid)

    ts = [threading.Thread(target=req) for _ in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return len(passaram)


def test_a07_corrida_tres_concorrentes_nao_estouram_a_cota():
    """Reprodução da auditoria: `used=4 quota=5`, três concorrentes. ANTES da
    reserva as três passavam no check e o estado final era `used=6` (o global
    dizia 7 — o read-modify-write de `consume` ainda perdia uma atualização,
    mascarando o estouro). Com reserva + trava, só uma passa."""
    conn = _fresh_db_threads()
    uid = "u_corrida"
    for _ in range(4):
        metering.consume(conn, uid)
    assert metering.used(conn, uid) == 4

    passaram = _corrida(conn, uid, quota=5)
    assert passaram == 1, "só cabia UMA análise: as outras duas tinham de ser barradas no check"
    assert metering.used(conn, uid) == 5, "cota diária estourou"
    assert metering.global_snapshot(conn, 5)["used"] == 5, \
        "contador global divergiu do do usuário (atualização perdida)"


def test_a07_corrida_respeita_o_teto_global():
    """O mesmo buraco existia no `cap_global`: `check` LIA o global e não
    reservava nada nele, então N usuários diferentes furavam o teto do
    servidor juntos. Usuários distintos, cota individual folgada, teto global
    com uma vaga só."""
    conn = _fresh_db_threads()
    barreira = threading.Barrier(3)
    passaram = []
    trava = threading.Lock()

    def req(uid):
        barreira.wait()
        ok, _ = metering.check(conn, uid, quota=100, rate_per_min=1000, cap_global=1)
        if not ok:
            return
        with trava:
            passaram.append(uid)
        time.sleep(0.25)
        metering.consume(conn, uid)

    ts = [threading.Thread(target=req, args=(u,)) for u in ("g1", "g2", "g3")]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert len(passaram) == 1, "três usuários passaram num teto global de 1"
    assert metering.global_snapshot(conn, 1)["used"] == 1


def test_a07_falha_nao_gasta_cota():
    """A propriedade que a correção NÃO pode quebrar: `check` reserva, mas o
    modelo que não responde nunca chama `consume` — e a conta não pode ficar
    com cota debitada. `used` (confirmado) segue em zero."""
    conn = _fresh_db()
    uid = "u_falha"
    for _ in range(3):
        ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000)
        assert ok is True
        # ...e aqui o LLM estoura. Nenhum consume.
    assert metering.used(conn, uid) == 0, "falha gastou cota"
    assert metering.month_used(conn, uid) == 0, "falha queimou o balde MENSAL do plano"
    assert metering.global_snapshot(conn, 5)["used"] == 0, "falha gastou o teto global"
    assert metering.reservado(conn, uid) == 3, "a reserva tem de estar de pé enquanto vale"


def test_a07_reserva_bloqueia_enquanto_vale_e_expira_depois():
    """A reserva é devolvida por EXPIRAÇÃO (nenhum caller chama `liberar`
    hoje). Dentro da janela ela barra; passada a janela, a cota volta inteira
    — nunca fica gasta."""
    conn = _fresh_db()
    uid = "u_ttl"
    t0 = 1_000_000.0
    for i in range(5):
        ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000, _now=t0 + i)
        assert ok is True
    ok, reason = metering.check(conn, uid, quota=5, rate_per_min=1000, _now=t0 + 5)
    assert ok is False and "limite diário" in reason, \
        "cinco reservas vivas e a sexta passou — a reserva não está sendo contada"
    assert metering.used(conn, uid) == 0, "bloquear por reserva não pode debitar cota"

    # a janela conta de CADA reserva: a última nasceu em t0+4
    depois = t0 + 4 + metering.RESERVA_TTL_S + 1
    assert metering.reservado(conn, uid, _now=depois) == 0
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000, _now=depois)
    assert ok is True, "reserva expirada continuou bloqueando — cota ficou presa"


def test_a07_consume_liquida_a_reserva_e_nao_debita_em_dobro():
    """Reserva não é contagem: `check` + `consume` do mesmo request valem UMA
    análise, não duas. Se `consume` não liquidasse a reserva, a conta perderia
    o dobro do que usou."""
    conn = _fresh_db()
    uid = "u_liq"
    ok, _ = metering.check(conn, uid, quota=10, rate_per_min=1000)
    assert ok is True and metering.reservado(conn, uid) == 1
    metering.consume(conn, uid)
    assert metering.used(conn, uid) == 1
    assert metering.reservado(conn, uid) == 0, "a reserva do request liquidado ficou pendurada"
    # 10 checks + 10 consumes => exatamente 10, nem 20
    for _ in range(9):
        ok, _ = metering.check(conn, uid, quota=10, rate_per_min=1000)
        assert ok is True
        metering.consume(conn, uid)
    assert metering.used(conn, uid) == 10
    assert metering.check(conn, uid, quota=10, rate_per_min=1000)[0] is False


def test_a07_consume_parcial_liquida_so_o_que_consumiu():
    """O /api/scan/deep reserva `custo=n` e consome 1 por ticker que deu certo
    ("consumir menos que o checado é sempre permitido"). O que foi consumido
    vira confirmado; o resto segue reservado até expirar — nunca vira gasto."""
    conn = _fresh_db()
    uid = "u_deep"
    ok, _ = metering.check(conn, uid, quota=20, rate_per_min=1000, custo=10)
    assert ok is True and metering.reservado(conn, uid) == 10
    for _ in range(4):                       # 4 dos 10 tickers responderam
        metering.consume(conn, uid)
    assert metering.used(conn, uid) == 4
    assert metering.reservado(conn, uid) == 6
    # 4 gastos + 6 reservados = 10 comprometidos de 20: um segundo deep de 10
    # cabe EXATO, de 11 não cabe. Sem a reserva, 11 caberiam (só os 4 contavam).
    assert metering.check(conn, uid, quota=20, rate_per_min=1000, custo=11)[0] is False
    assert metering.check(conn, uid, quota=20, rate_per_min=1000, custo=10)[0] is True


def test_a07_liberar_devolve_reserva_sem_gastar_cota():
    """`liberar()` é o estorno IMEDIATO — o caminho correto de devolução, para
    quando o estorno eager entrar nos callers. Contrato: devolve reserva e
    NUNCA toca o confirmado."""
    conn = _fresh_db()
    uid = "u_lib"
    metering.check(conn, uid, quota=5, rate_per_min=1000, custo=3)
    assert metering.reservado(conn, uid) == 3
    assert metering.liberar(conn, uid, custo=3) == 0
    assert metering.used(conn, uid) == 0, "liberar debitou cota"
    assert metering.month_used(conn, uid) == 0, "liberar tocou o balde mensal"
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000, custo=5)
    assert ok is True, "a cota não voltou inteira depois do estorno"


def test_a07_check_negado_nao_reserva():
    """Check que devolve False não pode deixar reserva para trás — senão uma
    recusa por rate limit comeria cota de quem esperou o minuto passar."""
    conn = _fresh_db()
    uid = "u_neg"
    t0 = 1_000_000.0
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1, _now=t0)
    assert ok is True
    ok, reason = metering.check(conn, uid, quota=5, rate_per_min=1, _now=t0 + 0.1)
    assert ok is False and "Muitas análises" in reason
    assert metering.reservado(conn, uid, _now=t0 + 0.2) == 1, \
        "a recusa por rate limit reservou mesmo assim"


def test_a07_registro_antigo_sem_reserva_nao_quebra():
    """Registro gravado ANTES desta correção não tem `resv`; e um valor
    corrompido não pode derrubar toda rota de IA do produto."""
    conn = _fresh_db()
    uid = "u_legado"
    hoje = metering._today()
    db.kv_set(conn, "aiUsage", {"day": hoje, "count": 2, "rl": []}, user_id=uid)
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000)
    assert ok is True
    db.kv_set(conn, "aiUsage", {"day": hoje, "count": 2, "rl": [], "resv": "lixo"},
              user_id=uid)
    assert metering.reservado(conn, uid) == 0
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=1000)
    assert ok is True
    db.kv_set(conn, "aiUsage",
              {"day": hoje, "count": 2, "rl": [], "resv": [None, "x", True]},
              user_id=uid)
    assert metering.reservado(conn, uid) == 0, "entrada torta virou reserva válida"


def test_a07_trava_existe_e_e_reentrante():
    """Guardião de desenho: a atomicidade depende da trava de PROCESSO. Se
    alguém remover `METERING_LOCK` achando que o SQLite resolve, este teste
    cai — e a nota de limite (um único processo uvicorn) fica registrada."""
    assert isinstance(metering.METERING_LOCK, type(threading.RLock()))
    with metering.METERING_LOCK:
        with metering.METERING_LOCK:       # RLock: reentrante, não trava em si
            pass
    src = open(os.path.join(os.path.dirname(__file__), "..", "app", "metering.py"),
               encoding="utf-8").read()
    assert src.count("with METERING_LOCK:") >= 3, \
        "check/consume/liberar precisam do read-modify-write sob a MESMA trava"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE METERING PASSARAM")
