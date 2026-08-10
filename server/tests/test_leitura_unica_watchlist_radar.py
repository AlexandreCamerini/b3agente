"""ACEITE — um ativo, uma leitura: Watchlist e Radar nunca se contradizem.

O DEFEITO que originou estes guardiões (09/08/2026, domingo): TIMS3 aparecia
como "Estudar baixa · Setup 9.3" na Watchlist e "Estudar alta · Reversão de
sobrevenda" no Radar, ao mesmo tempo, na mesma tela do mesmo usuário.

A causa NÃO era duplicação de cálculo — o Snapshot Técnico Único está íntegro e
os dois caminhos chegam à mesma `technical_snapshot.build`. A causa era o
`/api/scan` bifurcar em dois caminhos de DADO com idades diferentes:

  • `?tickers=…` (Watchlist) recalcula a cada request;
  • sem `tickers` (Radar) servia o payload armazenado do dia — e
    `get_stored` não tinha NENHUMA política de validade, só checava se o dict
    tinha `results`. Sábado e domingo não rodam varredura, então a leitura de
    sexta 08:45 (que enxergou até a quinta) era servida indefinidamente,
    enquanto a Watchlist já lia o fechamento de sexta.

`test_snapshot_consistency.py` trava a coerência N1×N2×N3 DENTRO de um
snapshot. Estes testes travam a outra metade: dois snapshots de instantes
diferentes servidos SIMULTANEAMENTE para o mesmo ticker.

O `snapshotId` é o instrumento certo para afirmar isso — ele existe justamente
para provar ao usuário que duas camadas leram os mesmos dados.
"""
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

import pytest

from app import candle_cache, db, radar_daily, scanner, technical_snapshot
from app.radar_daily import BRT


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


@pytest.fixture(autouse=True)
def _sem_l2():
    """Desliga o L2 (SQLite) do candle_cache durante estes testes.

    `candle_cache.reset()` limpa só o L1. Com o L2 ligado, a 2ª varredura
    reidrata a série ANTIGA do disco e — por causa do `_MIN_DELTA_INTERVAL` de
    45 s — nem vai ao provedor: as duas leituras saíam idênticas e o teste
    passava ou falhava conforme a ORDEM da suíte. Desligar também evita gravar
    candles falsos no banco de desenvolvimento.
    """
    antes = candle_cache._DB_ENABLED
    candle_cache._DB_ENABLED = False
    try:
        yield
    finally:
        candle_cache._DB_ENABLED = antes


def _reset_caches():
    candle_cache.reset()
    scanner.reset()
    technical_snapshot.reset()


def _serie(n=260, extra_queda=0):
    """Série diária determinística. `extra_queda` acrescenta pregões de baixa
    forte — é o que simula "um novo candle fechou desde a varredura"."""
    out = []
    for i in range(n):
        v = 10.0 + i * 0.1
        out.append({"date": f"2026-01-01+{i}", "time": 1700000000 + i * 86400,
                    "open": v, "high": v * 1.01, "low": v * 0.99,
                    "close": v, "volume": 1_000_000})
    base = 10.0 + (n - 1) * 0.1
    for j in range(extra_queda):
        v = base * (0.94 ** (j + 1))
        out.append({"date": f"2026-01-01+{n + j}", "time": 1700000000 + (n + j) * 86400,
                    "open": v * 1.03, "high": v * 1.04, "low": v * 0.98,
                    "close": v, "volume": 3_000_000})
    return out


def _fetch(serie):
    def go(symbol, rng=None):
        async def _():
            return {"candles": list(serie), "currency": "BRL"}
        return _()
    return go


def _envelhece(conn, period, dias=10):
    """Reescreve o carimbo da leitura armazenada para `dias` atrás.

    É assim que se reproduz o domingo do defeito sem depender do relógio: um
    carimbo de 10 dias atrás está SEMPRE antes do último fechamento de pregão,
    qualquer que seja o dia em que a suíte rode."""
    bruto = db.kv_get(conn, "radarDaily:" + period, user_id=None)
    velho = datetime.now(BRT) - timedelta(days=dias)
    bruto["scanAt"] = velho.isoformat()
    bruto["scanAtLabel"] = velho.strftime("%d/%m %H:%M")
    db.kv_set(conn, "radarDaily:" + period, bruto, user_id=None)
    return bruto


def _leitura(payload, ticker):
    for r in (payload or {}).get("results") or []:
        if r.get("ticker") == ticker:
            return r
    return None


# ---------------------------------------------------------------------------
# A INVARIANTE: mesmo ticker, duas telas, um snapshot só.
# ---------------------------------------------------------------------------

def test_radar_nao_serve_leitura_que_um_pregao_ja_invalidou():
    """O defeito reportado, reproduzido.

    Radar guarda a leitura da série A; um pregão fecha (série B); a Watchlist
    recalcula e lê B. O Radar NÃO pode continuar servindo A — o usuário veria
    dois vereditos do mesmo papel lado a lado.
    """
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    try:
        _reset_caches()
        c = _conn()
        # 1) varredura do dia, com a série "antiga"
        antiga = _run(scanner.run_scan(period="1y", fetch=_fetch(_serie())))
        radar_daily.store_result(c, "1y", antiga, origem="automática")
        _envelhece(c, "1y")           # o carimbo passa a ser de 10 dias atrás

        # 2) pregões novos fecharam: a Watchlist recalcula e vê outra coisa
        _reset_caches()
        nova = _run(scanner.run_scan(period="1y", universe="AAAA3",
                                     fetch=_fetch(_serie(extra_queda=6))))
        viva = _leitura(nova, "AAAA3")
        assert viva and viva.get("snapshotId")

        # 3) o que o Radar serve AGORA não pode ser a leitura vencida
        servido = radar_daily.get_stored(c, "1y")
        antiga_lida = _leitura(antiga, "AAAA3")
        assert antiga_lida["snapshotId"] != viva["snapshotId"], \
            "pré-condição do teste: as duas séries têm que gerar leituras diferentes"
        if servido is not None:
            assert _leitura(servido, "AAAA3")["snapshotId"] == viva["snapshotId"], (
                "o Radar está servindo uma leitura que um pregão já invalidou "
                "enquanto a Watchlist mostra outra — é o defeito do TIMS3")
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_leitura_recalculada_por_uma_tela_e_herdada_pelas_outras():
    """"Repositório único": atualizou o ativo numa tela, todas herdam.

    Sem isto, durante o pregão a Watchlist recalcula (candle do dia em
    formação, que o diário mantém de propósito) e o Radar segue exibindo o
    retrato das 08:45 — contradição dentro do MESMO dia, que a política de
    validade por fechamento não pega.
    """
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    try:
        _reset_caches()
        c = _conn()
        antiga = _run(scanner.run_scan(period="1y", fetch=_fetch(_serie())))
        radar_daily.store_result(c, "1y", antiga, origem="automática")

        _reset_caches()
        nova = _run(scanner.run_scan(period="1y", universe="AAAA3",
                                     fetch=_fetch(_serie(extra_queda=6))))
        viva = _leitura(nova, "AAAA3")

        radar_daily.merge_leituras(c, "1y", nova.get("results"))

        armazenado = radar_daily.get_bruto(c, "1y")
        herdada = _leitura(armazenado, "AAAA3")
        assert herdada["snapshotId"] == viva["snapshotId"], \
            "o Radar não herdou a leitura que a Watchlist acabou de calcular"
        assert herdada["veredito"] == viva["veredito"]
        # o ativo que ninguém recalculou continua intacto
        assert _leitura(armazenado, "BBBB3")["snapshotId"] == _leitura(antiga, "BBBB3")["snapshotId"]
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_ranking_do_radar_continua_ordenado_apos_herdar():
    """A herda não pode desordenar o Radar — ele é rankeado por confluência."""
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3,CCCC3"
    try:
        _reset_caches()
        c = _conn()
        antiga = _run(scanner.run_scan(period="1y", fetch=_fetch(_serie())))
        radar_daily.store_result(c, "1y", antiga, origem="automática")
        _reset_caches()
        nova = _run(scanner.run_scan(period="1y", universe="BBBB3",
                                     fetch=_fetch(_serie(extra_queda=6))))
        radar_daily.merge_leituras(c, "1y", nova.get("results"))
        confs = [(r.get("confluencia") or 0) for r in radar_daily.get_bruto(c, "1y")["results"]]
        assert confs == sorted(confs, reverse=True), "ranking do Radar saiu da ordem"
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


# ---------------------------------------------------------------------------
# A política de validade, isolada (pura, sem relógio real)
# ---------------------------------------------------------------------------

def test_leitura_vence_quando_um_pregao_fecha_depois_dela():
    sexta_0845 = datetime(2026, 8, 7, 8, 45, tzinfo=BRT)
    # domingo à noite: o pregão de sexta FECHOU depois da varredura das 08:45
    domingo = datetime(2026, 8, 9, 19, 50, tzinfo=BRT)
    assert radar_daily.esta_vencida(sexta_0845.isoformat(), now=domingo) is True, \
        "é exatamente o domingo em que TIMS3 divergiu"


def test_leitura_do_dia_continua_valida_antes_do_fechamento():
    sexta_0845 = datetime(2026, 8, 7, 8, 45, tzinfo=BRT)
    sexta_1000 = datetime(2026, 8, 7, 10, 0, tzinfo=BRT)
    assert radar_daily.esta_vencida(sexta_0845.isoformat(), now=sexta_1000) is False, \
        "durante o próprio pregão a varredura das 08:45 ainda é a leitura do dia"


def test_leitura_de_sexta_vence_na_abertura_de_segunda():
    sexta_0845 = datetime(2026, 8, 7, 8, 45, tzinfo=BRT)
    segunda_0800 = datetime(2026, 8, 10, 8, 0, tzinfo=BRT)
    assert radar_daily.esta_vencida(sexta_0845.isoformat(), now=segunda_0800) is True, \
        "o candle de sexta fechou e não está na leitura armazenada"


def test_carimbo_ausente_ou_ilegivel_conta_como_vencida():
    for ruim in (None, "", "ontem", "2026-13-45T99:99"):
        assert radar_daily.esta_vencida(ruim) is True, \
            "sem carimbo confiável, servir o armazenado é afirmar o que não se sabe"


def test_rota_scan_watchlist_propaga_a_leitura_para_o_radar():
    """A rota de verdade, não só as funções.

    O `?tickers=` é o caminho da Watchlist; ele tem que deixar a leitura nova
    disponível para o Radar. Guardião de fiação: já houve correção certa na
    função e esquecida na rota.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert "radar_daily.merge_leituras" in src, "a rota não propaga a leitura da Watchlist"
    assert 'origem="revalidação"' in src, "a rota não recomputa o Radar vencido"
    # o ramo do Radar tem que consultar a validade ANTES de servir
    assert src.index("radar_daily.get_stored") < src.index('origem="revalidação"')


def test_radar_nao_mistura_variacao_do_dia_com_variacao_do_periodo():
    """Guardião do 2º defeito: −0,74% (dia) × −11,72% (ano) no mesmo slot.

    O Radar injetava `variacaoPeriodoPct` onde a Watchlist põe a variação
    diária — mesmo componente, mesmo `pct()`, sem rótulo. São grandezas
    diferentes; ou vêm da mesma fonte, ou dizem de que janela falam.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[2] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "change: r.variacaoPeriodoPct" not in src, \
        "voltou a passar a variação do PERÍODO como se fosse a do DIA"
    assert "changePeriodo" in src, "sem o campo próprio, a variação do período volta a se disfarçar"
    assert "no período · fechamento" in src, "a variação do período tem que dizer de que janela é"


def test_get_stored_recusa_o_vencido_e_serve_o_valido():
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        _reset_caches()
        c = _conn()
        payload = _run(scanner.run_scan(period="1y", fetch=_fetch(_serie())))
        radar_daily.store_result(c, "1y", payload, origem="automática")
        assert radar_daily.get_stored(c, "1y") is not None, "recém-gravado é válido"
        _envelhece(c, "1y")
        assert radar_daily.get_stored(c, "1y") is None, \
            "vencido não é servido — quem chamou recomputa"
        assert radar_daily.get_bruto(c, "1y") is not None, \
            "o bruto continua acessível (a herança escreve nele)"
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)
