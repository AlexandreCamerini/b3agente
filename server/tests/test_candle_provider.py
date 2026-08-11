"""ADR-001 (Decisões 1 e 5) — fronteira do provedor de candles e instrumentação.

O que estes testes protegem:
  • trocar de fonte é CONFIGURAÇÃO (env), não refatoração — é o que torna o
    risco de depender do Yahoo sem contrato reversível barato;
  • o plano B falha ALTO e explica o que falta, em vez de existir meia-boca;
  • o gatilho do plano B é um NÚMERO observável (taxa de FALHA > 2% em 3
    pregões), não uma impressão — sem isso, "temos plano B" é conversa;
  • FALHA inclui 200 com série VAZIA, não só não-200 — foi assim que o feed
    de B3 sumiu em 31/07/2026, sem levantar um único erro.
Offline: o provedor é injetável.
"""
import asyncio

import pytest

from app import candle_provider as cp


class _Fake(cp.CandleProvider):
    nome = "yahoo"   # se passa pelo memo de get_provider()

    def __init__(self, erro_em=(), vazio_em=()):
        self.chamadas = []
        self.erro_em = set(erro_em)
        self.vazio_em = set(vazio_em)   # 200 com série VAZIA — o caso de 31/07

    async def history(self, ticker, rng, interval="1d"):
        self.chamadas.append((ticker, rng, interval))
        if ticker in self.erro_em:
            raise RuntimeError("provedor fora do ar")
        if ticker in self.vazio_em:
            return {"t": ticker, "currency": "BRL", "candles": []}
        return {"t": ticker, "currency": "BRL",
                "candles": [{"date": "2026-07-30", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10}]}


def _limpa():
    cp.set_provider(None)
    cp.set_fallback(None)
    cp.reset()


def test_ponto_unico_delega_ao_provedor_ativo():
    _limpa()
    fake = _Fake()
    cp.set_provider(fake)
    try:
        out = asyncio.run(cp.get_history("PETR4", rng="1d", interval="15m"))
        assert out["t"] == "PETR4"
        assert fake.chamadas == [("PETR4", "1d", "15m")]
    finally:
        _limpa()


def test_provedor_vem_do_ambiente(monkeypatch):
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "yahoo")
    assert cp.get_provider().nome == "yahoo"
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    assert cp.get_provider().nome == "brapi"      # troca sem tocar em código
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "inexistente")
    with pytest.raises(ValueError, match="desconhecido"):
        cp.get_provider()
    monkeypatch.delenv("B3_CANDLE_PROVIDER")
    _limpa()
    assert cp.get_provider().nome == "yahoo"      # default


def test_plano_b_falha_alto_e_diz_o_que_falta(monkeypatch):
    """GUARDIÃO ATUALIZADO COM NOTA (11/08/2026, ADR-008/qa-43 Fase 1): o
    BrapiProvider deixou de ser stub e virou implementação real — a exceção
    mudou de NotImplementedError para as falhas-altas do cliente. A REGRA
    protegida é a mesma: silêncio aqui viraria 'sem histórico disponível'
    genérico. Dois gritos distintos:
      • pedido fora do plano gratuito → ForaDoPlano SEM tocar a rede
        (recusa da brapi debita cota — medição de 11/08);
      • sem BRAPI_TOKEN → RuntimeError dizendo exatamente o que falta."""
    from app import brapi
    with pytest.raises(brapi.ForaDoPlano) as e:
        asyncio.run(cp.BrapiProvider().history("PETR4", "1d", "15m"))
    assert "plano" in str(e.value)

    monkeypatch.delenv("BRAPI_TOKEN", raising=False)
    with pytest.raises(RuntimeError) as e:
        asyncio.run(cp.BrapiProvider().history("PETR4", "1mo", "1d"))
    msg = str(e.value)
    assert "BRAPI_TOKEN" in msg and "ADR-008" in msg


def test_instrumentacao_conta_requisicoes_e_erros():
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        for _ in range(3):
            asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        snap = cp.snapshot()
        assert snap["requisicoes"] == 4 and snap["erros"] == 1
        dia = list(snap["porDia"].values())[0]
        assert dia["15m"]["req"] == 4 and dia["15m"]["velas"] == 3
        assert dia["15m"]["msMedio"] >= 0
    finally:
        _limpa()


def test_gatilho_do_plano_b_e_um_numero():
    """2% de não-200 em 3 pregões reabre a Decisão 1 do ADR-001. Abaixo de 50
    requisições não alerta — amostra pequena viraria alarme falso a cada deploy."""
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        for _ in range(99):
            asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        assert cp.snapshot()["alerta"] is False          # 0 falhas
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["requisicoes"] == 100 and s["taxaFalha"] == 0.01
        assert s["alerta"] is False                      # 1% < limiar
        for _ in range(2):
            with pytest.raises(RuntimeError):
                asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["taxaFalha"] > cp._LIMIAR_ERRO and s["alerta"] is True
    finally:
        _limpa()


def test_amostra_pequena_nao_dispara_alarme():
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}))
    try:
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["taxaFalha"] == 1.0 and s["alerta"] is False   # 1 requisição só
    finally:
        _limpa()


def test_resposta_vazia_conta_como_falha():
    """REGRESSÃO de 31/07/2026 — o pregão em que o alarme foi cego.

    Naquele dia o Yahoo devolveu HTTP 200 em 360 requisições seguidas, com
    `marketState: REGULAR` e ZERO velas de B3, por 2 horas de mercado aberto,
    enquanto entregava AAPL em tempo real. Contando só não-200, a taxa ficava
    em 0,00 e o alerta em `false`: a produção passaria o pregão sem dado
    intraday e o painel diria que estava tudo bem.
    """
    _limpa()
    cp.set_provider(_Fake(vazio_em={"PETR4"}))
    try:
        for _ in range(60):
            out = asyncio.run(cp.get_history("PETR4", "1d", "15m"))
            assert out["candles"] == []          # 200, sem exceção, série vazia
        s = cp.snapshot()
        assert s["erros"] == 0, "não houve não-200 — era exatamente esse o disfarce"
        assert s["vazios"] == 60
        assert s["falhas"] == 60 and s["taxaFalha"] == 1.0
        assert s["alerta"] is True, "o gatilho do plano B TEM que disparar nesse cenário"
    finally:
        _limpa()


def test_snapshot_mostra_a_idade_da_serie():
    """Diagnóstico direto: uma última vela de ontem durante o pregão é feed
    morto, qualquer que seja o status HTTP."""
    _limpa()
    cp.set_provider(_Fake())
    try:
        asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        dia = list(cp.snapshot()["porDia"].values())[0]
        assert dia["15m"]["ultimaVela"] == "2026-07-30"
    finally:
        _limpa()


def test_mistura_de_erro_e_vazio_soma_na_mesma_taxa():
    _limpa()
    cp.set_provider(_Fake(erro_em={"RUIM3"}, vazio_em={"VAZIO3"}))
    try:
        for _ in range(48):
            asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        asyncio.run(cp.get_history("VAZIO3", "1d", "15m"))
        with pytest.raises(RuntimeError):
            asyncio.run(cp.get_history("RUIM3", "1d", "15m"))
        s = cp.snapshot()
        assert s["requisicoes"] == 50 and s["erros"] == 1 and s["vazios"] == 1
        assert s["falhas"] == 2 and s["taxaFalha"] == 0.04
        assert s["alerta"] is True          # 4% > 2%
    finally:
        _limpa()


# ---------------------------------------------------------------------------
# ADR-008 (Fase 3) — roteamento por plano/orçamento e failover por requisição
# ---------------------------------------------------------------------------
class _FakeNome(_Fake):
    """_Fake com nome configurável (primário 'brapi' e backup 'yahoo')."""

    def __init__(self, nome, **kw):
        super().__init__(**kw)
        self.nome = nome


def _dupla(monkeypatch, *, prim_kw=None, fb_kw=None, pode_gastar=True):
    """Monta primário 'brapi' + backup 'yahoo' com orçamento controlado."""
    from app import brapi_budget as bb
    _limpa()
    # o memo de get_provider() só mantém o injetado se o nome casa com a env
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    prim = _FakeNome("brapi", **(prim_kw or {}))
    fb = _FakeNome("yahoo", **(fb_kw or {}))
    cp.set_provider(prim)
    cp.set_fallback(fb)
    monkeypatch.setattr(bb, "pode_gastar", lambda fatia, now=None: pode_gastar)
    debitos = []
    monkeypatch.setattr(bb, "debita", lambda fatia, n=1, now=None: debitos.append(fatia))
    return prim, fb, debitos


def test_intraday_vai_direto_ao_backup_sem_cota_nem_falha(monkeypatch):
    """Plano gratuito não tem intraday: o pedido nem encosta na brapi —
    recusa DEBITARIA cota (medição 11/08) e contaria falha falsa no gatilho."""
    prim, fb, debitos = _dupla(monkeypatch)
    try:
        out = asyncio.run(cp.get_history("PETR4", "1d", "15m"))
        assert out["source"] == "yahoo" and out["candles"]
        assert prim.chamadas == [] and len(fb.chamadas) == 1
        assert debitos == []
        assert "brapi" not in cp.snapshot()["porProvedor"]
    finally:
        _limpa()


def test_range_longo_vai_direto_ao_backup(monkeypatch):
    """Warmup 2y/1y é do Yahoo em definitivo (free permite até 3mo)."""
    prim, fb, _ = _dupla(monkeypatch)
    try:
        out = asyncio.run(cp.get_history("PETR4", "2y", "1d"))
        assert out["source"] == "yahoo" and prim.chamadas == []
    finally:
        _limpa()


def test_pedido_dentro_do_plano_debita_e_sai_com_source_brapi(monkeypatch):
    prim, fb, debitos = _dupla(monkeypatch)
    try:
        out = asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        assert out["source"] == "brapi" and fb.chamadas == []
        assert debitos == ["delta"]
    finally:
        _limpa()


def test_falha_do_primario_cai_no_backup_na_mesma_requisicao(monkeypatch):
    prim, fb, _ = _dupla(monkeypatch, prim_kw={"erro_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        assert out["source"] == "yahoo" and out["candles"]
        pp = cp.snapshot()["porProvedor"]
        assert pp["brapi"]["falhas"] == 1 and pp["yahoo"]["falhas"] == 0
    finally:
        _limpa()


def test_serie_vazia_do_primario_cai_no_backup(monkeypatch):
    """O modo de falha de 31/07 (200 com zero velas) também aciona o backup."""
    prim, fb, _ = _dupla(monkeypatch, prim_kw={"vazio_em": {"PETR4"}})
    try:
        out = asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        assert out["source"] == "yahoo" and out["candles"]
        assert cp.snapshot()["porProvedor"]["brapi"]["vazios"] == 1
    finally:
        _limpa()


def test_orcamento_esgotado_poupa_a_brapi(monkeypatch):
    prim, fb, debitos = _dupla(monkeypatch, pode_gastar=False)
    try:
        out = asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        assert out["source"] == "yahoo" and prim.chamadas == []
        assert debitos == []
    finally:
        _limpa()


def test_sem_backup_orcamento_nao_vira_sem_dado(monkeypatch):
    """Proteção de cota não pode negar dado quando não há alternativa."""
    from app import brapi_budget as bb
    _limpa()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    prim = _FakeNome("brapi")
    cp.set_provider(prim)
    cp.set_fallback(None)
    monkeypatch.setenv("B3_CANDLE_FALLBACK", "")     # backup desligado
    monkeypatch.setattr(bb, "pode_gastar", lambda fatia, now=None: False)
    try:
        out = asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        assert out["source"] == "brapi" and len(prim.chamadas) == 1
    finally:
        monkeypatch.delenv("B3_CANDLE_FALLBACK", raising=False)
        _limpa()


def test_alerta_mede_o_primario_nao_a_media(monkeypatch):
    """Com backup saudável, a média global esconderia o primário caindo —
    60 falhas brapi + 60 sucessos yahoo dão 50% global, e o alerta TEM que
    disparar olhando só o primário (100% de falha)."""
    prim, fb, _ = _dupla(monkeypatch, prim_kw={"erro_em": {"PETR4"}})
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    try:
        for _ in range(60):
            asyncio.run(cp.get_history("PETR4", "1mo", "1d"))
        s = cp.snapshot()
        assert s["porProvedor"]["brapi"]["taxaFalha"] == 1.0
        assert s["porProvedor"]["yahoo"]["taxaFalha"] == 0.0
        assert s["alerta"] is True
    finally:
        monkeypatch.delenv("B3_CANDLE_PROVIDER", raising=False)
        _limpa()


# ---------------------------------------------------------------------------
# ADR-008 (Fase 5) — spot atrás da mesma fronteira
# ---------------------------------------------------------------------------
def _spot_env(monkeypatch, *, token=True, pode_gastar=True):
    from app import brapi, brapi_budget as bb
    _limpa()
    brapi.reset_quote_cache()
    monkeypatch.setenv("B3_CANDLE_PROVIDER", "brapi")
    if token:
        monkeypatch.setenv("BRAPI_TOKEN", "tok-teste")
    else:
        monkeypatch.delenv("BRAPI_TOKEN", raising=False)
    monkeypatch.setattr(bb, "pode_gastar", lambda fatia, now=None: pode_gastar)
    debitos = []
    monkeypatch.setattr(bb, "debita", lambda fatia, n=1, now=None: debitos.append(fatia))
    return debitos


def test_spot_brapi_debita_fatia_spot_e_carimba_source(monkeypatch):
    from app import brapi
    debitos = _spot_env(monkeypatch)

    async def fake_fetch(symbol, params):
        assert params == {}          # spot puro: sem range/interval
        return {"results": [{"symbol": symbol, "longName": "Petrobras PN",
                             "regularMarketPrice": 42.23,
                             "regularMarketPreviousClose": 40.87,
                             "currency": "BRL"}]}
    monkeypatch.setattr(brapi, "_fetch_json", fake_fetch)
    try:
        q = asyncio.run(cp.get_quote("PETR4"))
        assert q["source"] == "brapi" and q["price"] == 42.23
        assert q["previousClose"] == 40.87 and q["name"] == "Petrobras PN"
        assert debitos == ["spot"]
        # segunda chamada: cache compartilhado absorve — sem novo débito
        q2 = asyncio.run(cp.get_quote("PETR4"))
        assert q2["price"] == 42.23 and debitos == ["spot"]
    finally:
        brapi.reset_quote_cache()
        _limpa()


def test_spot_sem_orcamento_cai_no_backup_sem_debitar(monkeypatch):
    from app import brapi, yahoo
    debitos = _spot_env(monkeypatch, pode_gastar=False)

    async def fake_yahoo(t):
        return {"t": t, "price": 10.0, "change": 1.0,
                "previousClose": 9.9, "currency": "BRL"}
    monkeypatch.setattr(yahoo, "get_quote", fake_yahoo)
    try:
        q = asyncio.run(cp.get_quote("WEGE3"))
        assert q["source"] == "yahoo" and q["price"] == 10.0
        assert debitos == []
    finally:
        brapi.reset_quote_cache()
        _limpa()


def test_spot_sem_token_vai_direto_ao_backup(monkeypatch):
    from app import brapi, yahoo
    debitos = _spot_env(monkeypatch, token=False)

    async def fake_yahoo(t):
        return {"t": t, "price": 5.5, "change": 0.0,
                "previousClose": 5.5, "currency": "BRL"}
    monkeypatch.setattr(yahoo, "get_quote", fake_yahoo)
    try:
        q = asyncio.run(cp.get_quote("ITSA4"))
        assert q["source"] == "yahoo" and debitos == []
    finally:
        brapi.reset_quote_cache()
        _limpa()


def test_spot_em_lote_mistura_cache_brapi_e_batch_yahoo(monkeypatch):
    from app import brapi, yahoo
    debitos = _spot_env(monkeypatch)

    async def fake_fetch(symbol, params):
        if symbol == "PETR4":
            return {"results": [{"symbol": symbol, "regularMarketPrice": 42.0,
                                 "regularMarketPreviousClose": 41.0, "currency": "BRL"}]}
        raise brapi.BrapiIndisponivel("fora do ar p/ " + symbol)
    monkeypatch.setattr(brapi, "_fetch_json", fake_fetch)

    async def fake_batch(ts):
        return {t: {"t": t, "price": 7.7, "change": 0.5,
                    "previousClose": 7.6, "currency": "BRL"} for t in ts}
    monkeypatch.setattr(yahoo, "get_quotes", fake_batch)
    try:
        out = asyncio.run(cp.get_quotes(["PETR4", "VALE3"]))
        assert out["PETR4"]["source"] == "brapi" and out["PETR4"]["price"] == 42.0
        assert out["VALE3"]["source"] == "yahoo" and out["VALE3"]["price"] == 7.7
        # débito só para o que a brapi de fato buscou (VALE3 falhou mas debitou
        # a tentativa — comportamento honesto: a requisição saiu)
        assert debitos == ["spot", "spot"]
    finally:
        brapi.reset_quote_cache()
        _limpa()


def test_spot_primario_yahoo_preserva_comportamento(monkeypatch):
    from app import yahoo
    _limpa()

    async def fake_yahoo(t):
        return {"t": t, "price": 1.0, "change": 0.0,
                "previousClose": 1.0, "currency": "BRL"}
    monkeypatch.setattr(yahoo, "get_quote", fake_yahoo)
    try:
        q = asyncio.run(cp.get_quote("PETR4"))
        assert q["source"] == "yahoo" and q["price"] == 1.0
    finally:
        _limpa()
