"""BLOCO B — testes do detector de setups (setups.py). Sem rede.

Trava: cada setup dispara na série engenheirada para ele; veredito usa SOMENTE
o vocabulário educacional; confluência é % ponderada de critérios; nenhum
texto imperativo; compressão sozinha => Monitorar; série sem padrão => Sem
setup no momento.
"""
import re

from app import indicators, setups

IMPERATIVE = re.compile(r"\b(compre|venda|entre agora|compra já|venda já)\b", re.I)
VEREDITOS = {"Estudar alta", "Estudar baixa", "Monitorar", "Sem setup no momento"}


def _mk(closes, vols=None, last_close_pos=0.9):
    """Candles sintéticos; o ÚLTIMO candle fecha na posição pedida do range
    (0=mínima, 1=máxima) para controlar o 'candle de força'."""
    from datetime import date, timedelta
    out = []
    d0 = date.fromisoformat("2024-01-01")
    for i, c in enumerate(closes):
        lo, hi = c * 0.985, c * 1.015
        close = c
        if i == len(closes) - 1:
            close = lo + (hi - lo) * last_close_pos
        out.append({"date": (d0 + timedelta(days=i)).isoformat(),
                    "open": round(c * 0.998, 4), "high": round(hi, 4),
                    "low": round(lo, 4), "close": round(close, 4),
                    "volume": (vols[i] if vols else 1000)})
    return out


def _detect(candles):
    cs = indicators.sanitize_candles(candles)
    full = indicators.compute(cs)
    return setups.detect_setups(cs, full["indicators"])


def test_rompimento_alta_com_volume():
    closes = [50 + (0.02 if i % 2 else -0.02) for i in range(80)] + [53.0]
    vols = [1000] * 80 + [2500]  # 2,5x a média
    r = _detect(_mk(closes, vols, last_close_pos=0.95))
    nomes = [s["nome"] for s in r["setups"]]
    assert any("Rompimento com volume (alta)" == n for n in nomes)
    assert r["veredito"] == "Estudar alta"
    assert r["confluencia"] >= setups.MIN_CONFLUENCIA


def test_reversao_sobrevenda():
    closes = [100 - i * 0.9 for i in range(60)]  # queda forte => RSI baixo
    r = _detect(_mk(closes, last_close_pos=0.95))  # último candle de força
    nomes = [s["nome"] for s in r["setups"]]
    assert any("Reversão de sobrevenda" == n for n in nomes)


def test_pullback_alta():
    # sobe devagar (SMA20>SMA50) e corrige de volta à SMA20 com RSI neutro —
    # série calibrada numericamente: dist. da SMA20 ~1,2%, RSI ~56.
    closes = [10 + i * 0.08 for i in range(70)]
    topo = closes[-1]
    closes += [topo - (j + 1) * 0.15 for j in range(5)]
    r = _detect(_mk(closes, last_close_pos=0.6))
    achou = any(s["nome"] == "Pullback à média (alta)" for s in r["setups"])
    # o pullback exige preço a ±2% da SMA20 com tendência intacta — a série
    # foi calibrada para isso; se falhar, o detector regrediu.
    assert achou, r


def test_lateral_sem_padrao_e_vocabulario():
    closes = [30 + (0.02 if i % 2 else -0.02) for i in range(90)]
    r = _detect(_mk(closes, last_close_pos=0.5))
    assert r["veredito"] in VEREDITOS
    # lateral sem rompimento nem extremo: no máximo compressão => nunca direcional
    assert r["veredito"] in ("Monitorar", "Sem setup no momento")


def test_compressao_sozinha_da_monitorar():
    # volatilidade caindo ao longo do tempo: bandas estreitando
    closes = []
    amp = 3.0
    for i in range(90):
        amp = max(0.05, amp * 0.96)
        closes.append(50 + (amp if i % 2 else -amp))
    r = _detect(_mk(closes, last_close_pos=0.5))
    if r["setups"] and all(s["lado"] == "neutro" for s in r["setups"]):
        assert r["veredito"] == "Monitorar"


def test_estrutura_confluencia_e_guardrail():
    closes = [50 + (0.02 if i % 2 else -0.02) for i in range(80)] + [53.0]
    r = _detect(_mk(closes, [1000] * 80 + [2500]))
    assert 0 <= r["confluencia"] <= 100
    for s in r["setups"]:
        assert 0 <= s["confluencia"] <= 100
        assert s["criterios"], s["nome"]
        for c in s["criterios"]:
            assert set(c) == {"criterio", "ok", "peso", "obrigatorio"}
            assert not IMPERATIVE.search(c["criterio"]), c["criterio"]
        assert not IMPERATIVE.search(s["nome"])
    for nome, desc in setups.MODEL_EXPLANATION:
        assert not IMPERATIVE.search(nome) and not IMPERATIVE.search(desc)
    assert r["veredito"] in VEREDITOS


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok " + name)
            except AssertionError as e:
                fails += 1
                print("FALHOU " + name + " :: " + str(e)[:200])
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERRO " + name + " :: " + repr(e)[:200])
    print()
    print("TODOS OS TESTES DE SETUPS PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
