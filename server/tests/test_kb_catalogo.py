"""Fase 38 (KB Didática ampliada) — `GET /api/kb/catalogo`.

O que estes guardiões travam, e por quê:

  • ROTA PÚBLICA, SEM CUSTO. Nenhuma conta exigida — mesmo perfil de
    `GET /api/kb/buscar`, já em produção (T-38-03 do threat model: aceito por
    ser puro-memória, 83 itens curtos, zero I/O externo).
  • FORMA EXATA (D-04). `{"modo", "familias", "verbetes"}` — nada a mais.
    `familias` é sempre as 9, na ordem de `kb.FAMILIAS`. Cada verbete tem
    `id, familia, titulo, texto, veja, termos`, `titulo`/`texto` nunca vazios.
  • MODO RESOLVIDO IGUAL À ROTA IRMÃ (T-38-01): `?modo=operador` vira
    operador; qualquer outro valor (incluindo ausente ou lixo) cai para
    educacional — allowlist implícita de 2 valores.
  • DEGRADAÇÃO HONESTA (T-38-04, princípio 4 do CLAUDE.md): com
    `B3_DIDATICA_OFF=1`, os 9 verbetes derivados de `conceitos.py` perdem o
    texto e são EXCLUÍDOS — nunca servidos com corpo vazio.
  • NADA DA CONFIG VAZA (T-38-02): a rota lê só `appMode` da config; a
    resposta nunca ecoa a config inteira.
  • ROTA IRMÃ INTACTA (T-38-05, D-02/D-03): `/api/kb/buscar` continua
    limitada a 5 resultados — mudança desta fase é só aditiva (`titulo`).
"""
import os

import pytest
from fastapi.testclient import TestClient

from app import kb
from app.main import app


@pytest.fixture(autouse=True)
def _flags_limpas():
    chaves = ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF")
    antes = {k: os.environ.get(k) for k in chaves}
    for k in chaves:
        os.environ.pop(k, None)
    yield
    for k, v in antes.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def test_catalogo_sem_auth_devolve_83_verbetes_e_9_familias(cli):
    r = cli.get("/api/kb/catalogo")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"modo", "familias", "verbetes"}
    assert body["modo"] == "educacional"
    assert len(body["verbetes"]) == 83
    assert len(body["familias"]) == 9
    assert body["familias"] == [{"id": fid, "rotulo": rotulo} for fid, rotulo in kb.FAMILIAS]


def test_todo_verbete_servido_tem_forma_completa(cli):
    body = cli.get("/api/kb/catalogo").json()
    for v in body["verbetes"]:
        assert set(v.keys()) == {"id", "familia", "titulo", "texto", "veja", "termos"}
        assert isinstance(v["titulo"], str) and v["titulo"].strip(), \
            f"{v['id']} servido com titulo vazio"
        assert isinstance(v["texto"], str) and v["texto"].strip(), \
            f"{v['id']} servido com texto vazio"
        assert isinstance(v["termos"], list) and v["termos"], \
            f"{v['id']} servido sem termos"


def test_veja_de_verbete_servido_nunca_e_link_morto(cli):
    body = cli.get("/api/kb/catalogo").json()
    ids = {v["id"] for v in body["verbetes"]}
    for v in body["verbetes"]:
        for alvo in v["veja"]:
            assert alvo in ids, f"{v['id']} referencia '{alvo}' em veja, ausente do catálogo servido"


def test_modo_operador_resolve_titulo_diferente(cli):
    r = cli.get("/api/kb/catalogo", params={"modo": "operador"})
    assert r.status_code == 200
    body = r.json()
    assert body["modo"] == "operador"
    estado = next(v for v in body["verbetes"] if v["id"] == "estado-atingido")
    assert estado["titulo"] == "Gatilho atingido"


def test_modo_desconhecido_cai_para_educacional(cli):
    r = cli.get("/api/kb/catalogo", params={"modo": "xpto"})
    assert r.status_code == 200
    assert r.json()["modo"] == "educacional"


def test_didatica_desligada_exclui_verbetes_derivados_de_conceitos(cli, monkeypatch):
    monkeypatch.setenv("B3_DIDATICA_OFF", "1")
    r = cli.get("/api/kb/catalogo")
    assert r.status_code == 200
    body = r.json()
    assert len(body["verbetes"]) == 74
    ids = {v["id"] for v in body["verbetes"]}
    conceito_ids = set(kb._FAMILIA_DO_CONCEITO.keys())
    assert conceito_ids.isdisjoint(ids), \
        "verbetes derivados de conceitos.py deveriam sumir, não servir texto vazio"
    assert all(v["texto"] for v in body["verbetes"]), \
        "nenhum verbete servido pode ter texto vazio (princípio 4)"


def test_config_nao_vaza_alem_do_appmode(cli):
    """T-38-02: a resposta é sempre {modo, familias, verbetes} — nada da
    config do escopo é ecoado."""
    r = cli.get("/api/kb/catalogo")
    assert set(r.json().keys()) == {"modo", "familias", "verbetes"}


def test_kb_buscar_continua_limitado_a_5_resultados(cli):
    r = cli.get("/api/kb/buscar", params={"q": "setup"})
    assert r.status_code == 200
    assert len(r.json()["resultados"]) <= 5
