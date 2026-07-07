# FASE 4 (Bloco 2) — SIWA (Sign in with Apple): exchange no login + revoke na
# exclusão de conta (5.1.1(v)). Testa os caminhos PUROS (sem rede/httpx) e o
# wiring do main.py por texto — verde em qualquer ambiente.
import asyncio
import os
import sqlite3

from app import db, siwa

MAIN_PY = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _clear_env():
    for k in ("SIWA_KEY_ID", "SIWA_PRIVATE_KEY", "APNS_TEAM_ID", "APPLE_CLIENT_ID"):
        os.environ.pop(k, None)


def test_configured_exige_as_4_envs():
    _clear_env()
    assert siwa.configured() is False
    os.environ.update(SIWA_KEY_ID="k", SIWA_PRIVATE_KEY="p", APNS_TEAM_ID="t")
    assert siwa.configured() is False  # falta APPLE_CLIENT_ID
    os.environ["APPLE_CLIENT_ID"] = "com.alexandrecamerini.bolsia"
    assert siwa.configured() is True
    _clear_env()


def test_exchange_sem_code_ou_sem_config_nao_explode():
    _clear_env()
    c = _conn()
    r = asyncio.run(siwa.exchange_and_store(c, "u1", ""))
    assert r["ok"] is False and "authorizationCode" in r["motivo"]
    r = asyncio.run(siwa.exchange_and_store(c, "u1", "code-abc"))
    assert r["ok"] is False and "não configurado" in r["motivo"]
    assert db.kv_get(c, siwa.KV_KEY, user_id="u1") is None  # nada gravado


def test_revoke_sem_token_e_ok_e_nao_bloqueia_exclusao():
    _clear_env()
    c = _conn()
    r = asyncio.run(siwa.revoke_for_user(c, "u1"))
    assert r["ok"] is True and "sem token" in r["motivo"]
    # token armazenado mas servidor sem config: reporta, não explode
    db.kv_set(c, siwa.KV_KEY, "refresh-xyz", user_id="u1")
    r = asyncio.run(siwa.revoke_for_user(c, "u1"))
    assert r["ok"] is False and "não está configurado" in r["motivo"]


def test_wiring_main_py():
    src = open(MAIN_PY, encoding="utf-8").read()
    assert "from . import siwa" in src
    # login: hint de nome (Apple só manda no 1º consentimento) + exchange do code
    assert 'body.get("name")' in src and "siwa.exchange_and_store" in src
    # exclusão: revoke ANTES da limpeza, resultado exposto no payload
    i_rev, i_del = src.find("siwa.revoke_for_user"), src.find("store.delete_user_data")
    assert 0 < i_rev < i_del, "revoke deve acontecer antes de apagar os dados"
    assert '"siwaRevoke": revoke' in src
    # segurança: token de refresh nunca em print/log
    assert "refresh_token" not in [l for l in src.splitlines() if "print(" in l]
