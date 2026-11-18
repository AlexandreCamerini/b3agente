"""Fase 51 plano 03 — consentimento do push de fechamento e teto de engajamento.

Guardião do opt-in seguro (D-13): conta existente NÃO recebe sem decidir; conta
nova nasce ligada; o consentimento só é gravado por `push.decidir_fechamento`
(nunca por `set_prefs`, logo nunca por `POST /api/push/register-token`)."""
import os
import tempfile

import pytest

from app import auth, db, push


def _conn():
    return db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))


def test_conta_sem_prefs_le_fechamento_desligado_e_nao_decidido():
    c = _conn()
    p = push.prefs_for(c, "u1")
    assert p["fechamento"] is False and p["fechamentoDecidido"] is False
    assert push.estado_fechamento(c, "u1") == {"ligado": False, "decidido": False}


def test_prefs_antigas_nao_ligam_o_fechamento():
    c = _conn()
    db.kv_set(c, "pushPrefs", {"radar": False}, user_id="u1")
    assert push.prefs_for(c, "u1")["fechamento"] is False
    assert push.quer_fechamento(c, "u1") is False


def test_set_prefs_descarta_as_chaves_de_consentimento():
    c = _conn()
    push.set_prefs(c, "u1", {"fechamento": True})
    push.set_prefs(c, "u1", {"fechamento": False, "fechamentoDecidido": True})
    assert push.estado_fechamento(c, "u1") == {"ligado": False, "decidido": False}
    assert "fechamento" not in push.PREFS_BOOLS
    assert "fechamentoDecidido" not in push.PREFS_BOOLS


def test_decidir_fechamento_e_set_prefs_posterior_preserva():
    c = _conn()
    push.decidir_fechamento(c, "u1", False)
    assert push.estado_fechamento(c, "u1") == {"ligado": False, "decidido": True}
    push.set_prefs(c, "u1", {"radar": False})
    assert push.estado_fechamento(c, "u1") == {"ligado": False, "decidido": True}
    push.decidir_fechamento(c, "u1", True)
    push.set_prefs(c, "u1", {"fechamento": False})
    assert push.quer_fechamento(c, "u1") is True


def test_quer_fechamento_e_fail_closed(monkeypatch):
    c = _conn()
    push.decidir_fechamento(c, "u1", True)
    assert push.quer_fechamento(c, "u1") is True

    def boom(*a, **k):
        raise RuntimeError("kv corrompido")
    monkeypatch.setattr(push, "prefs_for", boom)
    assert push.quer_fechamento(c, "u1") is False


def test_conta_nova_email_nasce_ligada_e_decidida():
    c = _conn()
    u = auth.register_email(c, "novo@example.com", "senha-forte-123")
    assert push.estado_fechamento(c, u["id"]) == {"ligado": True, "decidido": True}


def test_conta_nova_oauth_nasce_ligada_e_decidida():
    c = _conn()
    u = auth.upsert_oauth_user(c, "google", "sub-123", "oauth@example.com",
                               "Fulano", True)
    assert push.estado_fechamento(c, u["id"]) == {"ligado": True, "decidido": True}


def test_falha_no_push_nao_derruba_criacao_de_conta(monkeypatch):
    c = _conn()

    def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(push, "decidir_fechamento", boom)
    u = auth.register_email(c, "outro@example.com", "senha-forte-123")
    assert u and push.estado_fechamento(c, u["id"])["ligado"] is False


def test_reservar_engajamento_teto_de_dois_e_zera_no_dia_seguinte():
    c = _conn()
    assert push.reservar_engajamento(c, "u1", "2026-11-17", "radar") is True
    assert push.reservar_engajamento(c, "u1", "2026-11-17", "fechamento") is True
    assert push.reservar_engajamento(c, "u1", "2026-11-17", "outro") is False
    assert push.reservar_engajamento(c, "u1", "2026-11-17", "fechamento") is False
    assert push.reservar_engajamento(c, "u1", "2026-11-18", "fechamento") is True
    # escopo por conta
    assert push.reservar_engajamento(c, "u2", "2026-11-17", "radar") is True
