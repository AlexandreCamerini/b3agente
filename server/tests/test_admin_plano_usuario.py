"""24-17 (pedido do Alex, 2026-09-12) — mudar o PLANO de uma conta pelo portal.

Contexto que este arquivo trava, para ninguém desfazer sem ler a razão:

`pro` é, nas palavras do próprio `server/app/plan.py`, "estado alcançável só
por atribuição manual (`users.plan`), não por compra" — e até 2026-09-12 a
única porta era editar o SQLite do container (`scripts/plano-da-conta.sh`).
Serve para a conta do dono; não serve para mais ninguém. `POST
/api/admin/users/{id}/plan` é o eixo COMERCIAL (ADR-010) ao lado do eixo de
governança que a rota de papéis já controlava (ADR-013).

O que está travado aqui:
  - o gate é `usuarios.gerenciar`, NÃO "qualquer admin" — por isso o caso do
    titular de OUTRA permissão administrativa (prompts) tomando 403;
  - plano inválido é recusado pelo BACKEND, nomeando os aceitos: a UI recusar
    não vale, porque a UI não é o único cliente possível da rota;
  - a mudança fica na auditoria, com quem fez, o valor anterior e o novo — é a
    mitigação que o ADR-013 escolheu para escrita administrativa;
  - **mudar o PRÓPRIO plano é permitido, e isso é decisão, não descuido**:
    quem tem `usuarios.gerenciar` já pode conceder a si mesmo qualquer papel
    de governança pela rota irmã, e o registro com o nome de quem clicou é a
    mitigação dessa classe inteira. Um freio só aqui seria regra inventada e
    assimétrica com o que existe ao lado. O teste existe para que "consertar"
    isso exija apagar um teste com a razão escrita;
  - a lista de planos vem de `plan.PLANOS_POR_ID` — nenhuma segunda cópia, nem
    no `main.py`, nem na UI.

Isolamento igual a `test_adr013_rbac.py` (B3_DB_PATH temporário + reset dos
caches em memória entre testes).
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import plan


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_plano_admin_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _eventos_de_plano(c, headers, user_id=None):
    eventos = c.get("/api/admin/audit", headers=headers).json()["eventos"]
    return [
        e for e in eventos
        if e["entity"] == "user_plan" and (user_id is None or e["entityId"] == user_id)
    ]


# --------------------------------- o gate ------------------------------------
def test_sem_sessao_401(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    r = c.post(f"/api/admin/users/{admin['user']['id']}/plan", json={"plano": "pro"})
    assert r.status_code == 401, r.text


def test_usuario_comum_403(monkeypatch):
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    r = c.post(f"/api/admin/users/{comum['user']['id']}/plan",
               json={"plano": "pro"}, headers=_auth(comum["token"]))
    assert r.status_code == 403, r.text


def test_outra_permissao_admin_nao_basta(monkeypatch):
    """Prova que o gate é `usuarios.gerenciar`, não "tem algum papel admin".
    Sem esta asserção, trocar a dependency por `require_any_admin_permission`
    passaria despercebido — e um editor de prompts promoveria contas."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    editor = _registra(c, "editor@teste.com")
    h_admin = _auth(admin["token"])
    r = c.post(f"/api/admin/users/{editor['user']['id']}/roles",
               json={"role": "prompts", "acao": "conceder"}, headers=h_admin)
    assert r.status_code == 200, r.text
    # o editor É admin de alguma coisa (vê a auditoria), mas não desta
    assert c.get("/api/admin/audit", headers=_auth(editor["token"])).status_code == 200
    r = c.post(f"/api/admin/users/{editor['user']['id']}/plan",
               json={"plano": "pro"}, headers=_auth(editor["token"]))
    assert r.status_code == 403, r.text
    assert "usuarios.gerenciar" in r.text


# ------------------------------ o caminho feliz -------------------------------
def test_admin_muda_o_plano_de_outra_conta_e_persiste(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    h = _auth(admin["token"])
    assert main.db.get_user_by_id(main._conn, alvo["user"]["id"])["plan"] == "free"

    r = c.post(f"/api/admin/users/{alvo['user']['id']}/plan", json={"plano": "pro"}, headers=h)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["ok"] is True
    assert corpo["userId"] == alvo["user"]["id"]
    assert corpo["plano"] == "pro"
    # relido do banco: a rota mudou o dado, não só a resposta
    assert main.db.get_user_by_id(main._conn, alvo["user"]["id"])["plan"] == "pro"


def test_volta_para_free(monkeypatch):
    """Promover sem poder despromover deixaria a única saída de novo no
    SQLite do container, que é o estado que este plano encerra."""
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    h = _auth(admin["token"])
    uid = alvo["user"]["id"]
    c.post(f"/api/admin/users/{uid}/plan", json={"plano": "pro"}, headers=h)
    r = c.post(f"/api/admin/users/{uid}/plan", json={"plano": "free"}, headers=h)
    assert r.status_code == 200, r.text
    assert main.db.get_user_by_id(main._conn, uid)["plan"] == "free"


def test_usuario_inexistente_404(monkeypatch):
    """O 404 tem de vir da ROTA dizendo "usuário não encontrado", não do
    catch-all `_api_inexistente` — que também responde 404 e faria este teste
    passar com a rota ainda inexistente (foi o que aconteceu na medição RED:
    este era um dos 3 que passavam antes da correção). Por isso a asserção
    também olha o texto."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    r = c.post("/api/admin/users/nao-existe-esse-id/plan",
               json={"plano": "pro"}, headers=_auth(admin["token"]))
    assert r.status_code == 404, r.text
    assert "rota_inexistente" not in r.text, "404 do catch-all não conta — a rota precisa existir"
    assert "não encontrado" in r.text.lower() or "nao encontrado" in r.text.lower(), r.text


@pytest.mark.parametrize("plano", ["premium", "", "PRO", " pro", None, 3, ["pro"], {"id": "pro"}])
def test_plano_invalido_400_nomeando_os_aceitos(monkeypatch, plano):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    uid = alvo["user"]["id"]
    r = c.post(f"/api/admin/users/{uid}/plan", json={"plano": plano}, headers=_auth(admin["token"]))
    assert r.status_code == 400, f"{plano!r} deveria ser recusado, veio {r.status_code}: {r.text}"
    texto = r.text
    for aceito in plan.PLANOS_POR_ID:
        assert aceito in texto, f"o 400 precisa nomear os planos aceitos; faltou {aceito!r}: {texto}"
    # e nada mudou no banco
    assert main.db.get_user_by_id(main._conn, uid)["plan"] == "free"


def test_corpo_vazio_400(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    r = c.post(f"/api/admin/users/{alvo['user']['id']}/plan", json={}, headers=_auth(admin["token"]))
    assert r.status_code == 400, r.text


# -------------------------------- auditoria -----------------------------------
def test_grava_um_evento_user_plan_com_anterior_e_novo(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    h = _auth(admin["token"])
    uid = alvo["user"]["id"]
    c.post(f"/api/admin/users/{uid}/plan", json={"plano": "pro"}, headers=h)

    ev = _eventos_de_plano(c, h, uid)
    assert len(ev) == 1, f"uma mudança, um evento — veio {len(ev)}"
    assert ev[0]["field"] == "plan"
    assert ev[0]["oldValue"] == "free"
    assert ev[0]["newValue"] == "pro"


def test_evento_de_plano_e_visivel_para_quem_tem_a_permissao(monkeypatch):
    """`entidades_visiveis` filtra o audit log por `ENTIDADES_POR_PERMISSAO`.
    Sem `user_plan` nesse mapa, o evento é gravado e some da tela — inclusive
    para quem o produziu."""
    from app import rbac
    assert "user_plan" in rbac.ENTIDADES_POR_PERMISSAO["usuarios.gerenciar"]

    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    gestor = _registra(c, "gestor@teste.com")
    h_admin = _auth(admin["token"])
    c.post(f"/api/admin/users/{gestor['user']['id']}/roles",
           json={"role": "usuarios", "acao": "conceder"}, headers=h_admin)
    h_gestor = _auth(gestor["token"])
    alvo = _registra(c, "cliente@teste.com")
    r = c.post(f"/api/admin/users/{alvo['user']['id']}/plan", json={"plano": "pro"}, headers=h_gestor)
    assert r.status_code == 200, r.text
    assert _eventos_de_plano(c, h_gestor, alvo["user"]["id"]), \
        "quem tem usuarios.gerenciar precisa VER o evento que acabou de produzir"


def test_editor_de_prompts_nao_ve_evento_de_plano(monkeypatch):
    """O outro lado do filtro: entidade nova não pode vazar para quem
    administra outra área (achado de 2026-08-20, ADR-013)."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    editor = _registra(c, "editor@teste.com")
    h_admin = _auth(admin["token"])
    c.post(f"/api/admin/users/{editor['user']['id']}/roles",
           json={"role": "prompts", "acao": "conceder"}, headers=h_admin)
    alvo = _registra(c, "cliente@teste.com")
    c.post(f"/api/admin/users/{alvo['user']['id']}/plan", json={"plano": "pro"}, headers=h_admin)
    assert _eventos_de_plano(c, _auth(editor["token"])) == []


# -------------------- decisão: mudar o PRÓPRIO plano vale --------------------
def test_mudar_o_proprio_plano_e_permitido_e_fica_auditado(monkeypatch):
    """DECISÃO, não descuido (2026-09-12). Quem tem `usuarios.gerenciar` já
    concede a si mesmo qualquer papel de governança pela rota irmã; o registro
    com o nome de quem clicou é a mitigação que o ADR-013 escolheu para essa
    classe. Um freio só aqui seria assimétrico com o que existe ao lado.

    Se alguém quiser mudar isso, que mude a rota de papéis junto — e apague
    este teste conscientemente, em vez de "consertar" um comportamento sem ler
    a razão."""
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    uid = admin["user"]["id"]

    r = c.post(f"/api/admin/users/{uid}/plan", json={"plano": "pro"}, headers=h)
    assert r.status_code == 200, r.text
    assert main.db.get_user_by_id(main._conn, uid)["plan"] == "pro"

    ev = _eventos_de_plano(c, h, uid)
    assert len(ev) == 1
    assert ev[0]["actorUserId"] == uid, "o registro precisa dizer QUEM promoveu — inclusive a si mesmo"
    assert ev[0]["oldValue"] == "free" and ev[0]["newValue"] == "pro"


# ------------------------- fonte única da lista de planos ---------------------
def test_planos_disponiveis_vem_do_plan_py(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    data = c.get("/api/admin/users", headers=_auth(admin["token"])).json()
    assert data["planosDisponiveis"] == list(plan._ORDEM_PLANO)
    assert set(data["planosDisponiveis"]) == set(plan.PLANOS_POR_ID)


def test_plano_aparece_em_cada_usuario_listado(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    alvo = _registra(c, "cliente@teste.com")
    h = _auth(admin["token"])
    c.post(f"/api/admin/users/{alvo['user']['id']}/plan", json={"plano": "pro"}, headers=h)
    usuarios = c.get("/api/admin/users", headers=h).json()["usuarios"]
    por_id = {u["id"]: u for u in usuarios}
    assert por_id[alvo["user"]["id"]]["plan"] == "pro"
    assert por_id[admin["user"]["id"]]["plan"] == "free"


def test_main_py_nao_escreve_lista_literal_de_planos(monkeypatch):
    """A fonte dos ids é `plan.py`. Uma lista literal no `main.py` seria a
    segunda cópia, e ela não acompanharia o dia em que existir um terceiro
    plano — o mesmo defeito que a UI evita lendo `planosDisponiveis`."""
    from pathlib import Path
    fonte = Path(__file__).resolve().parents[1] / "app" / "main.py"
    texto = fonte.read_text(encoding="utf-8")
    import re
    literais = re.findall(r'\[\s*"(?:free|pro)"\s*,\s*"(?:free|pro)"\s*\]', texto)
    assert literais == [], f"lista literal de planos em main.py: {literais}"
    # sanidade: a regex reprova de fato o defeito que ela existe para pegar
    assert re.findall(r'\[\s*"(?:free|pro)"\s*,\s*"(?:free|pro)"\s*\]', 'PLANOS = ["free", "pro"]')


# --------------------- a reversão fica registrada, não apagada ---------------
def test_a_rota_de_papeis_registra_a_reversao_com_data():
    """A docstring de `POST .../roles` dizia "Sem override de plano nesta
    rodada (decisão do Alex, ADR-013)". A decisão mudou em 2026-09-12 e a nota
    foi ATUALIZADA, não apagada — o repositório registra reversão deliberada
    (guardrail do CLAUDE.md)."""
    from app import main as main_mod
    doc = main_mod.admin_users_roles_post.__doc__ or ""
    assert "2026-09-12" in doc, "a reversão precisa estar datada na docstring"
    assert "plan" in doc, "a docstring precisa apontar a rota irmã que passou a existir"
    assert "ADR-013" in doc, "o registro antigo não se apaga"
