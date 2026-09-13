"""FIX (thread-safety) — regressão do 500 em produção.

Reproduz o cenário real: o FastAPI roda dependências síncronas (current_scope)
num POOL de threads. Com a conexão global antiga, resolve_session explodia com
`sqlite3.ProgrammingError: SQLite objects created in a thread can only be used
in that same thread`. Com db.shared() (uma conexão por thread), o mesmo fluxo
funciona de qualquer thread — inclusive escrita concorrente (WAL+busy_timeout).

NOTA (2026-09-13): estes testes dependem de timing real de thread/SQLite e
foram observados falhando intermitentemente quando a suíte COMPLETA roda sob
carga externa pesada — em particular, múltiplas sessões rodando
`bash scripts/executar.sh --testes` ao mesmo tempo na mesma máquina (ambiente
com vários worktrees/sessões concorrentes), o que nesse mesmo episódio também
esgotou o disco (ENOSPC). Investigado a partir de uma falha observada em
`test_opcoes_dsl.py` (teste sem nenhuma relação de código com thread-safety)
na suíte completa: reproduzida em worktree isolado, sem qualquer outra carga
conhecida, a suíte passou 100% duas vezes seguidas e na terceira falhou este
arquivo — nunca o mesmo teste duas vezes. Rodando só este arquivo,
isoladamente, 15/15 execuções passaram em ~0,15s cada. Ou seja: não é
poluição de estado entre módulos de teste (não é ordem-dependente), é
sensibilidade a contenção externa (CPU e/ou disco) — cada teste cria seu
próprio SQLite temporário via `tempfile.mkdtemp()` e nada limpa isso entre
execuções, o que acumula com múltiplas sessões rodando a suíte em paralelo.
Se este arquivo (ou qualquer teste que passe por TestClient/`current_scope`,
que roda no mesmo pool de threads sobre `db.shared()`) falhar de forma
isolada e não reproduzir sozinho, é este mecanismo — não um bug de lógica.
Não mitigado no código (retry/timeout maior seria defensivo sem confirmação
da causa exata); decisão registrada em 2026-09-13: documentar e não alterar
comportamento.
"""
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from app import auth, db, store


def _tmp_db():
    d = tempfile.mkdtemp()
    return os.path.join(d, "b3_agente.db")


def test_shared_connection_works_across_threads():
    path = _tmp_db()
    conn = db.shared(path)
    store.ensure_defaults(conn)                      # thread principal
    user = auth.register_email(conn, "t@x.com", "senha-forte-1", "T")
    token = auth.create_session(conn, user["id"])

    def worker(_i):
        # exatamente o que current_scope faz por requisição, em outra thread
        u = auth.resolve_session(conn, token)
        assert u is not None and u["id"] == user["id"]
        return True

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(worker, range(32)))    # levantaria ProgrammingError antes do fix
    assert all(results)


def test_shared_connection_concurrent_writes():
    path = _tmp_db()
    conn = db.shared(path)
    store.ensure_defaults(conn)

    def writer(i):
        db.kv_set(conn, "k" + str(i % 4), {"i": i}, user_id="u" + str(i % 2))
        return db.kv_get(conn, "k" + str(i % 4), user_id="u" + str(i % 2)) is not None

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(writer, range(64)))
    assert all(results)


def test_shared_data_visible_between_threads():
    """Escreve numa thread, lê noutra: WAL garante visibilidade após commit."""
    path = _tmp_db()
    conn = db.shared(path)
    store.ensure_defaults(conn)

    with ThreadPoolExecutor(max_workers=1) as ex:
        ex.submit(db.kv_set, conn, "cross", {"ok": True}, None).result()
    assert db.kv_get(conn, "cross") == {"ok": True}   # lida na thread principal
