"""FASE 6 (fix 5) — push/APNs: tradução de `reason` em instrução exata e
política de descarte de tokens. Motivo: tokens rejeitados com
BadEnvironmentKeyInToken (chave .p8 restrita a um ambiente ≠ do host em uso)
apareciam sem explicação e sem caminho de correção.

Stdlib-only (as funções são puras + kv); roda standalone e via pytest.
"""
import os
import tempfile

from app import db
from app import push


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_push_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def test_bad_environment_key_tem_instrucao_exata():
    txt = push.explain_reason("BadEnvironmentKeyInToken")
    assert "RESTRITA" in txt or "restrita" in txt.lower()
    assert "APNS_SANDBOX" in txt
    assert "Sandbox & Production" in txt          # caminho no portal Apple
    # esse reason é problema da CHAVE, não do token: NÃO descarta o aparelho
    assert "BadEnvironmentKeyInToken" not in push._DROP_TOKEN_REASONS


def test_bad_device_token_explica_ambiente_e_descarta():
    txt = push.explain_reason("BadDeviceToken")
    assert "ambiente" in txt.lower() and "APNS_SANDBOX" in txt
    assert "BadDeviceToken" in push._DROP_TOKEN_REASONS
    assert "Unregistered" in push._DROP_TOKEN_REASONS
    assert "DeviceTokenNotForTopic" in push._DROP_TOKEN_REASONS


def test_reasons_de_configuracao_apontam_a_variavel():
    assert "APNS_TOPIC" in push.explain_reason("BadTopic")
    assert "APNS_TEAM_ID" in push.explain_reason("InvalidProviderToken")
    assert push.explain_reason("ReasonInexistente") == ""
    assert push.explain_reason(None) == ""


def test_env_label_reflete_a_variavel():
    old = os.environ.pop("APNS_SANDBOX", None)
    try:
        assert push.env_label() == "produção"
        os.environ["APNS_SANDBOX"] = "1"
        assert "sandbox" in push.env_label()
    finally:
        if old is None:
            os.environ.pop("APNS_SANDBOX", None)
        else:
            os.environ["APNS_SANDBOX"] = old


def test_registro_de_tokens_dedup_e_cap():
    conn = _fresh_db()
    for i in range(7):
        push.register_token(conn, "u1", f"tok{i}")
    push.register_token(conn, "u1", "tok6")      # duplicado não re-entra
    toks = push.tokens_for(conn, "u1")
    assert len(toks) == 5 and toks[-1] == "tok6"  # cap 5, mais recentes


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE REASONS DO PUSH PASSARAM")
