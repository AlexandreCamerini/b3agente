"""Fase 1 da auditoria de UX do Boris (2026-08-08) — o "resumo" automático
deixou de ser a superfície principal na UI (o Alex achava que "não fazia
muito sentido"); no lugar, cada tela do pet passa a sugerir 2-3 perguntas
prontas, clicáveis, para abrir a conversa. Este guardião trava o contrato
NOVO de `/api/pet/resumo`, sem tocar no contrato antigo (`fala`/`itens`
continuam existindo — ver test_pet.py/test_pet_todas_telas.py):

  • TODA tela registrada (`conceitos.PET_TELAS`) devolve `perguntas`: lista
    não vazia de strings — sem isso a UI nova não teria o que mostrar no
    lugar do resumo.
  • O VOCABULÁRIO SEGUE O MODO — a mesma lei de `skill_ref.vocab` que rege
    `fala`/`assistente.py` também vale aqui: perguntas de Estudo e de
    Operador para a MESMA tela não podem ser idênticas (senão a
    diferenciação Estudo×Operador, requisito do produto, não chegou até a
    sugestão de pergunta).
"""
import pytest
from fastapi.testclient import TestClient

from app import conceitos
from app.main import app


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("aba", conceitos.PET_TELAS)
def test_toda_tela_tem_perguntas_sugeridas(cli, aba):
    r = cli.get("/api/pet/resumo", params={"modo": "estudo", "tela": aba})
    assert r.status_code == 200
    perguntas = r.json().get("perguntas")
    assert isinstance(perguntas, list) and len(perguntas) >= 1
    assert all(isinstance(p, str) and p.strip() for p in perguntas)


@pytest.mark.parametrize("aba", conceitos.PET_TELAS)
def test_perguntas_mudam_entre_estudo_e_operador(cli, aba):
    estudo = cli.get("/api/pet/resumo", params={"modo": "estudo", "tela": aba}).json()["perguntas"]
    operador = cli.get("/api/pet/resumo", params={"modo": "operador", "tela": aba}).json()["perguntas"]
    assert estudo != operador, f"pet:{aba} sugere as MESMAS perguntas nos dois modos"
