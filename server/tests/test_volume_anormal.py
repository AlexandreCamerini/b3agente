"""Guardião do indicador de VOLUME ANORMAL (indicators.volume_anormal /
volume_state / campos vol* do summary), 2026-09-07.

Origem: pergunta sobre mapear "carteiras baleias" com o mydata. O COTAHIST
é agregado por papel/pregão — o dado permite detectar que houve dinheiro
grande no papel, nunca quem. Este guardião trava: (1) nada de número
fabricado (janela curta, média zero, volume atual zero → None); (2) a
aritmética da razão e do z; (3) os cortes categóricos; (4) integração
aditiva no compute()/slice_tail sem quebrar chaves antigas; (5) o nome do
campo não vira narrativa de causa ("baleia" não aparece no contrato).
"""
from app import indicators as ind


def _candles(vols, close_step=0.0, base=10.0):
    out = []
    for i, v in enumerate(vols):
        c = base + close_step * i
        out.append({"date": "d%d" % i, "open": c, "high": c + 0.2, "low": c - 0.2, "close": c, "volume": v})
    return out


def test_serie_curta_respeita_o_minimo():
    # indicador: precisa de VOL_MIN_CANDLES (10) anteriores com negócio
    r, z, n = ind.volume_anormal([100] * 20)
    assert all(r[i] is None for i in range(ind.VOL_MIN_CANDLES))
    assert r[ind.VOL_MIN_CANDLES] == 1.0 and n[ind.VOL_MIN_CANDLES] == ind.VOL_MIN_CANDLES
    assert all(x is None for x in z), "z só com janela cheia (20) — aqui nunca chega"
    r, z, n = ind.volume_anormal([], 20)
    assert r == [] and z == [] and n == []
    # estrito: com minimo=p, nenhum dos 20 primeiros tem 20 anteriores
    r, _, _ = ind.volume_anormal([100] * 20, 20, minimo=20)
    assert all(x is None for x in r)


def test_razao_e_z_corretos():
    vols = [100.0] * 20 + [300.0]
    r, z, _ = ind.volume_anormal(vols, 20)
    assert r[-1] == 3.0
    assert z[-1] is None, "janela constante tem desvio 0 → z ausente, razão continua válida"
    # janela com dispersão: média 100, desvio populacional 10 (metade 90, metade 110)
    vols = [90.0, 110.0] * 10 + [130.0]
    r, z, _ = ind.volume_anormal(vols, 20)
    assert abs(r[-1] - 1.3) < 1e-9
    assert abs(z[-1] - 3.0) < 1e-9


def test_janela_exclui_o_candle_atual():
    # se o atual entrasse na média, 300/(2100/21)=3.0 viraria 300/((2000+300)/21)≈2.74
    vols = [100.0] * 20 + [300.0]
    r, _, _ = ind.volume_anormal(vols, 20)
    assert r[-1] == 3.0


def test_media_zero_e_volume_atual_zero_dao_none():
    r, z, n = ind.volume_anormal([0] * 20 + [500], 20)
    assert r[-1] is None and z[-1] is None and n[-1] == 0, "papel sem negócio na janela: sem razão, sem número inventado"
    r, z, _ = ind.volume_anormal([100] * 20 + [0], 20)
    assert r[-1] is None, "volume atual 0 é 'ausente' (convenção de _pos), não 'razão 0'"
    r, z, _ = ind.volume_anormal([100] * 20 + [None], 20)
    assert r[-1] is None


def test_zeros_na_janela_ficam_fora_da_media():
    # 20 anteriores: 10 com negócio (100) e 10 zerados → média 100 sobre n=10, não 50 sobre 20
    vols = [100.0, 0.0] * 10 + [200.0]
    r, z, n = ind.volume_anormal(vols)
    assert r[-1] == 2.0 and n[-1] == 10
    assert z[-1] is None, "janela não está cheia (n=10 < 20) → z ausente"
    # com um zero a mais cai abaixo do mínimo do indicador → None
    vols = [100.0, 0.0] * 9 + [0.0, 0.0] + [200.0]
    r, _, n = ind.volume_anormal(vols)
    assert r[-1] is None and n[-1] == 9


def test_volume_relativo_e_a_mesma_aritmetica_do_ultimo_candle():
    vols = [90.0, 110.0] * 10 + [130.0]
    vr = ind.volume_relativo(vols)
    r, z, n = ind.volume_anormal(vols)
    assert vr["ratio"] == r[-1] and vr["z"] == z[-1] and vr["n"] == n[-1] == 20
    assert vr["media"] == 100.0
    assert ind.volume_relativo([]) == {"ratio": None, "z": None, "media": None, "n": 0}
    # minimo=1 (setups/technical_models): série curta ainda produz razão
    assert ind.volume_relativo([100.0, 300.0], minimo=1)["ratio"] == 3.0
    assert ind.volume_relativo([100.0, 300.0])["ratio"] == 3.0  # default também é 1
    assert ind.volume_relativo([100.0, 300.0], minimo=ind.VOL_MIN_CANDLES)["ratio"] is None


def test_fonte_unica_setups_contexto_ia_e_summary_batem():
    """Antes da unificação os três divergiam neste cenário: setups 2,5×,
    technical_models 2,33× (média de 21 com o pico dentro), summary 2,5×."""
    from app import setups, technical_models
    cs = _candles([1000.0] * 80 + [2500.0], close_step=0.05)
    full = ind.compute(cs)
    assert full["summary"]["volRatio20"] == 2.5
    ctx_setups = setups._ctx(cs, full["indicators"])
    assert ctx_setups["vol_ratio"] == 2.5
    ctx_ia = technical_models.build_context("TESTE4", None, cs, model="completo")
    vol = ctx_ia["volume"]
    assert vol["relativeVolume"] == 2.5
    assert vol["avgVolume20"] == 1000 and vol["volumeJanela"] == 20
    assert vol["volumeState"] == "anormal"
    assert "avgVolume21" not in vol
    assert ctx_ia["families"]["volume"]["volumeRelativo"] == 2.5


def test_serie_curta_setups_calcula_summary_nao_rotula():
    # 5 candles (histórico curto): setups ainda tem razão (minimo=1); o estado do
    # summary fica None porque 4 candles de referência não sustentam "anormal".
    from app import setups
    cs = _candles([100.0] * 4 + [300.0])
    full = ind.compute(cs)
    assert setups._ctx(cs, full["indicators"])["vol_ratio"] == 3.0
    s = full["summary"]
    assert s["volRatio20"] is None and s["volState"] is None and s["volJanela"] == 4


def test_volume_state_cortes():
    assert ind.volume_state(None) is None
    assert ind.volume_state(2.0) == "anormal"
    assert ind.volume_state(1.99) == "acima"
    assert ind.volume_state(1.5) == "acima"
    assert ind.volume_state(1.49) == "normal"
    assert ind.volume_state(0.51) == "normal"
    assert ind.volume_state(0.5) == "abaixo"


def test_compute_expoe_series_e_summary_aditivos():
    cs = _candles([100.0] * 60 + [250.0], close_step=0.1)
    full = ind.compute(cs)
    # séries alinhadas
    assert len(full["indicators"]["volRatio20"]) == len(cs)
    assert len(full["indicators"]["volZ20"]) == len(cs)
    assert full["indicators"]["volRatio20"][-1] == 2.5
    # summary
    s = full["summary"]
    assert s["volRatio20"] == 2.5
    assert s["volState"] == "anormal"
    assert s["volAnormal"] is True
    assert s["volDirecao"] == "alta"
    assert s["volJanela"] == 20
    # chaves antigas continuam lá (contrato aditivo, regime.py/scanner.py leem estas)
    for k in ("close", "rsi14", "rsiState", "macdState", "trend", "atr14", "adx14", "adxState"):
        assert k in s
    # o contrato não rotula causa
    assert not any("baleia" in k.lower() for k in list(s) + list(full["indicators"]))


def test_summary_le_o_ultimo_candle_nao_o_ultimo_valido():
    # ontem foi anormal, hoje o volume ainda é 0 (barra sem negócio) → hoje é "sem dado"
    cs = _candles([100.0] * 40 + [400.0, 0.0])
    s = ind.compute(cs)["summary"]
    assert s["volRatio20"] is None and s["volState"] is None
    assert s["volAnormal"] is False and s["volDirecao"] is None


def test_direcao_segue_o_preco_do_candle():
    cs = _candles([100.0] * 30 + [300.0], close_step=-0.1)
    assert ind.compute(cs)["summary"]["volDirecao"] == "baixa"
    cs = _candles([100.0] * 30 + [300.0], close_step=0.0)
    assert ind.compute(cs)["summary"]["volDirecao"] == "neutro"


def test_slice_tail_mantem_alinhamento():
    cs = _candles([100.0 + (i % 3) * 10 for i in range(80)] + [500.0])
    full = ind.compute(cs)
    sl = ind.slice_tail(cs, full["indicators"], full["summary"], 22)
    assert len(sl["indicators"]["volRatio20"]) == 22
    assert sl["indicators"]["volRatio20"][-1] == full["indicators"]["volRatio20"][-1]
    assert sl["summary"]["volState"] == "anormal"


def test_sanitize_nao_inventa_volume():
    # volume ausente/negativo vira 0 no sanitize → janela toda 0 → razão None
    raw = [{"close": 10, "volume": None}] * 25 + [{"close": 10, "volume": 900}]
    cs = ind.sanitize_candles(raw)
    assert ind.compute(cs)["summary"]["volRatio20"] is None


def test_verbete_kb_volume_anormal_responde_baleia_sem_llm():
    """A pergunta que originou o indicador cai na KB (0 custo, sem LLM) e
    recebe a LIMITAÇÃO do dado, não uma narrativa de causa."""
    from app import kb
    v = kb.verbete("ind-volume-anormal")
    assert v is not None and v["familia"] == "indicadores"
    for pergunta in ("o que é volume anormal?", "o que são carteiras baleias?",
                     "como o app detecta baleia no papel"):
        r = kb.resolver(pergunta)
        assert r is not None and r["id"] == "ind-volume-anormal", pergunta
        assert r["fonte"] == "kb"
    for modo in ("educacional", "operador"):
        txt = v["texto"][modo]
        assert "não" in txt.lower() or "nunca" in txt.lower()
        assert "quem" in txt.lower(), "tem que dizer que o dado não identifica QUEM"
        # cortes interpolados das constantes, não hardcoded
        assert "2×" in txt and "1,5×" in txt and "0,5×" in txt
        assert str(ind.VOL_MIN_CANDLES) in txt
    assert set(v["veja"]) <= {x["id"] for x in kb.catalogo()}
    assert "ind-volume-anormal" in kb.verbete("ind-volume-relativo")["veja"]
    assert "ind-volume-anormal" in kb.verbete("familia-volume")["veja"]


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print("ok", name)
            except Exception as e:  # noqa: BLE001
                fails += 1; print("FALHOU", name, "->", repr(e))
    print("TODOS OS TESTES DE VOLUME ANORMAL PASSARAM" if fails == 0 else "%d TESTE(S) FALHARAM" % fails)
    sys.exit(0 if fails == 0 else 1)
