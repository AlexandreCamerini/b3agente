"""Fase 50: I/O fino em volta do motor puro de marcos (setups.marcos_*).
Nenhuma aritmética aqui.

Busca o snapshot canônico (mesmo das rotas de Opções/Radar), escolhe o setup
DO SERVIDOR e delega a conta a `setups.marcos_do_plano`/`marcos_da_posicao`.
Números de gatilho/invalidação vindos do cliente nunca entram (T-50-13).
"""
from . import candle_provider, setups, technical_snapshot
from . import candles as candles_mod


async def snapshot_canonico(t):
    """Snapshot no período canônico; qualquer falha -> None (nunca inventa)."""
    try:
        p = candles_mod.normalize_period(None)
        return await technical_snapshot.get(t, p, lambda rng: candle_provider.get_history(t, rng=rng))
    except Exception:
        return None


def _carimbo(snap, fonte):
    return {"snapshotId": snap.get("snapshotId"), "snapshotAt": snap.get("asOf") or snap.get("generatedAt"),
            "fonte": fonte}


def _niveis(snap):
    return ((snap or {}).get("setups") or {}).get("niveis") or {}


def marcos_de_setup(snap, nome_setup, preco):
    """Marcos do setup `nome_setup` (compra) medidos no PREÇO EXECUTADO."""
    achado = next((s for s in ((snap.get("setups") or {}).get("setups") or [])
                   if s.get("nome") == nome_setup and s.get("lado") == "alta" and not s.get("aposentado")), None)
    if not achado:
        data = str(snap.get("asOf") or snap.get("generatedAt") or "")[:10] or "data desconhecida"
        m = {**setups._marcos_vazio("O setup %s não está ativo no snapshot de %s — sem plano do motor para gravar." % (nome_setup, data), "alta"),
             "gatilho": None, "invalidacao": None}
    else:
        m = setups.marcos_do_plano("alta", achado.get("gatilho"), achado.get("invalidacao"),
                                   close=preco, niveis=_niveis(snap))
        m = {**m, "gatilho": achado.get("gatilho"), "invalidacao": achado.get("invalidacao")}
    return {**m, **_carimbo(snap, "setup")}


def marcos_para_posicao(snap, preco, avg=None):
    m = setups.marcos_da_posicao(preco, _niveis(snap), avg=avg)
    return {**m, **_carimbo(snap, "posicao")}
