"""Quick 261021-spd (W2 da revisão): /api/cycle não pode dizer "Ciclo executado."
quando `run_cycle_for` pulou porque outro ciclo da mesma conta já rodava
(princípio 9 — estado correto, nunca inventado). O `skipped` do motor vira
`cicloEmAndamento` + `mensagem` na resposta; o iPhone logado repassa os dois."""
from .test_execucao_fora_pregao_rotas import _cliente, _registrar, _app_main_isolado  # noqa: F401


def test_api_cycle_repassa_ciclo_em_andamento(monkeypatch):
    client, m = _cliente(monkeypatch)
    h, _uid = _registrar(client, "w2@ciclo-em-andamento.dev", m=m)

    async def pulou(*a, **k):
        return {"events": [], "executed": 0, "skipped": "ciclo já em andamento"}
    monkeypatch.setattr(m.agent_mod, "run_cycle_for", pulou)
    r = client.post("/api/cycle", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["cicloEmAndamento"] is True
    assert "em andamento" in j["mensagem"] and "nada novo foi executado" in j["mensagem"]
    assert "mercadoFechado" not in j


def test_api_cycle_normal_sem_flag(monkeypatch):
    client, m = _cliente(monkeypatch)
    h, _uid = _registrar(client, "w2b@ciclo-em-andamento.dev", m=m)

    async def rodou(*a, **k):
        return {"events": [], "executed": 0}
    monkeypatch.setattr(m.agent_mod, "run_cycle_for", rodou)
    j = client.post("/api/cycle", headers=h).json()
    assert "cicloEmAndamento" not in j and "mensagem" not in j
