import asyncio
from app import db, push


def _conn(tmp_path):
    return db.connect(str(tmp_path / "t.db")) if hasattr(db, "connect") else None


def test_info_vazio_e_historico(tmp_path, monkeypatch):
    c = _conn(tmp_path)
    for k in ("APNS_TEAM_ID", "APNS_KEY_ID", "APNS_AUTH_KEY", "APNS_TOPIC"):
        monkeypatch.delenv(k, raising=False)
    i = push.info_for(c, "u1")
    assert i["configurado"] is False and i["aparelhos"] == 0 and i["ultimos"] == []
    assert i["ultimoOk"] is None
    push._registrar_envio(c, "u1", "T", "B", 0, 1, ["x: HTTP 400 BadDeviceToken"])
    push._registrar_envio(c, "u1", "T2", "B2", 1, 1, [])
    i = push.info_for(c, "u1")
    assert [e["titulo"] for e in i["ultimos"]] == ["T2", "T"]
    assert i["ultimos"][1]["erro"] and i["ultimos"][0]["erro"] is None
    assert i["ultimoOk"] is not None


def test_historico_capado(tmp_path):
    c = _conn(tmp_path)
    for n in range(push.HISTORICO_MAX + 5):
        push._registrar_envio(c, "u1", f"t{n}", "", 1, 1, [])
    assert len(push.info_for(c, "u1")["ultimos"]) == push.HISTORICO_MAX
