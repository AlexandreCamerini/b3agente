"""Debug n3-carteira-stopalvo-502 (2026-10-15): o except do `scan_deep.run_deep`
engolia a falha da IA sem rastro (scan/deep voltava 200 em <1s com a IA fora).
Guardião: a falha de 1 ativo deixa UMA linha `[ia-falha]` sem segredo, vai para
`errors` e não derruba os demais."""
import asyncio

from app import scan_deep

SEGREDO = "sk-ant-api03-SEGREDOQUENAOPODEVAZAR123"


def test_falha_do_deep_loga_ia_falha_sem_segredo(capsys):
    payload = {"results": [
        {"ticker": "AAAA3", "confluencia": 2},
        {"ticker": "BBBB3", "confluencia": 1},
    ]}

    async def deep_call(item):
        if item["ticker"] == "AAAA3":
            raise RuntimeError(f"401 invalid x-api-key {SEGREDO}")
        return {"ok": True}

    scan_deep._DEEP_CACHE.clear()
    out = asyncio.run(scan_deep.run_deep(payload, 5, "1y", deep_call))
    log = capsys.readouterr().out
    assert log.count("[ia-falha] rota=scan/deep t=AAAA3") == 1
    assert SEGREDO not in log
    assert [e["ticker"] for e in out["errors"]] == ["AAAA3"]
    assert out["analisados"] == 1
    scan_deep._DEEP_CACHE.clear()
