"""Guardião (260911-dtx, achado D-2 PARTE 2): a aritmética de DIAS ATÉ O
VENCIMENTO usava `date.today()` sem fuso em seis pontos. Produção roda no
Railway com o container em UTC, então das 21:00 às 23:59 BRT o "hoje" já virou
e todo prazo sai UM DIA A MENOS.

Diferença para a parte 1 (`test_fuso_carimbos_visiveis.py`): lá o defeito era
cosmético (a string que a tela exibe). Aqui ele MUDA DECISÃO:

  • `opcoes_lastreadas.propor` recusa o candidato fora da faixa
    `_PRAZO_MIN_DIAS (15) <= dias <= _PRAZO_MAX_DIAS (60)`. Um contrato que
    vence em exatamente 15 dias é candidato às 20:59 BRT e deixa de ser às
    21:01 — a proposta some da tela sem NADA ter mudado no mercado. Na borda
    dos 60 o erro é o oposto e pior: um contrato de 61 dias reais entrava como
    se tivesse 60.
  • `options_api._days_to` alimenta `daysToExpiration`, que liga o `riskFlag`
    de "vencimento curto" (<= 21 dias): um contrato de 22 dias reais ganhava a
    bandeira que não é dele.

O instante cravado é 01:30 UTC do dia 10 = 22:30 BRT do dia 9 — UTC e BRT em
DIAS diferentes, que é o que prova a correção; um teste que só confere a hora
passaria com o código defeituoso. Mesmo padrão de `test_store_now_str_brt.py`.

DESENHO DELIBERADO — a prova de impacto no gate é montada pelo CAMINHO REAL
(`TestClient` → rota → `opcoes_lastreadas.propor` de verdade), nunca por mock
da função de prazo. `propor`/`proposta_fechar`/`_dias_ate` recebem `hoje` por
ARGUMENTO justamente porque `opcoes_lastreadas` é módulo PURO sob guardião de
fronteira (`test_opcoes_fronteira.py`): relógio dentro dele é proibido. Por
isso a correção deste achado é toda nos CHAMADORES (`main._hoje_brt()`), e o
espião abaixo checa o ARGUMENTO que o chamador passou, sem substituir a regra
de prazo.
"""
import ast
import asyncio
import datetime as dt
import pathlib
import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import (
    candle_provider,
    mydata_client,
    opcoes_lastreadas,
    options_api,
    options_provider_mock,
    store,
    technical_snapshot,
)
from app.main import app, _conn

# 01:30 UTC do dia 10 é 22:30 BRT do dia 9 — o instante que de fato separa os
# dois dias. Com o relógio naive (UTC, o defeito) o "hoje" é 10/09; com BRT (a
# correção) é 09/09.
_INSTANTE_UTC = datetime(2026, 9, 10, 1, 30, tzinfo=timezone.utc)
_HOJE_BRT = date(2026, 9, 9)
_HOJE_NAIVE_UTC = date(2026, 9, 10)   # o que `date.today()` devolveria no container


class _RelogioViradoEmUtc(datetime):
    """Substitui `datetime` nos módulos sob teste. Herda de `datetime` (não um
    objeto solto) para que `strftime`/`astimezone`/`fromisoformat` continuem
    funcionando sem reimplementação.

    O ramo `tz is None` devolve o instante NAIVE em UTC — exatamente o que
    `datetime.now()`/`date.today()` devolvem hoje no container do Railway. É
    esse ramo que reproduz o defeito se o código for revertido.
    """

    @classmethod
    def now(cls, tz=None):
        return _INSTANTE_UTC.astimezone(tz) if tz is not None else _INSTANTE_UTC.replace(tzinfo=None)


def _venc(dias_de_brasilia: int) -> str:
    """Vencimento a N dias corridos contados do dia de BRASÍLIA."""
    return (_HOJE_BRT + dt.timedelta(days=dias_de_brasilia)).isoformat()


def _dias_pelo_relogio_naive(vencimento: str) -> int:
    """Quantos dias o cálculo DEFEITUOSO (naive/UTC) enxergaria — usado para
    documentar, dentro do próprio teste, que os dois lados discordam."""
    return (date.fromisoformat(vencimento) - _HOJE_NAIVE_UTC).days


# ---------------------------------------------------------------------------
# (a) options_api._days_to — o prazo isolado
# ---------------------------------------------------------------------------
def test_days_to_conta_do_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(options_api, "datetime", _RelogioViradoEmUtc)
    vencimento = _venc(15)
    assert options_api._days_to(vencimento) == 15, (
        "22:30 BRT do dia 9 ainda é o dia 9 — o prazo não pode encurtar "
        "porque o container do Railway já virou a meia-noite UTC")
    assert _dias_pelo_relogio_naive(vencimento) == 14, (
        "se este assert cair, o instante cravado deixou de separar UTC e BRT "
        "em dias diferentes e o teste acima virou tautologia")


def test_hoje_brt_do_options_api_e_o_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(options_api, "datetime", _RelogioViradoEmUtc)
    assert options_api.hoje_brt() == _HOJE_BRT


# ---------------------------------------------------------------------------
# Fiação da prova de IMPACTO NO GATE — caminho real, provider mock, sem rede
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _mock_provider(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    """Nem cotação nem candle saem para a rede: o spot vem do próprio payload
    do provider mock (`underlyingPrice`) e o contexto técnico é sintético."""
    async def _quote(ticker):
        return {"price": options_provider_mock.MOCK_SPOT.get(ticker, 38.0)}

    async def _history(ticker, rng="1y", interval="1d"):
        return {"t": ticker, "candles": []}

    async def _snapshot(ticker, period, loader, interval="1d"):
        # setups VAZIO => `plano_do_resultado` devolve NÃO OPERAR => o motor
        # propõe call_coberta (sem alta a preservar), que só depende do lastro.
        return {"setups": {"setups": []}, "close": 38.0}

    monkeypatch.setattr(candle_provider, "get_quote", _quote)
    monkeypatch.setattr(candle_provider, "get_history", _history)
    monkeypatch.setattr(technical_snapshot, "get", _snapshot)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _globais_da_rota_de_proposta():
    """Dict de globais do módulo que REALMENTE atende `/api/options/proposta`.

    NÃO use `from app import main` para patchar o relógio da rota:
    `test_admin_summary.py` re-importa `app.main` (`sys.modules.pop` +
    `importlib.import_module`) e restaura só `sys.modules["app.main"]` — o
    atributo `main` do PACOTE `app` continua apontando para o módulo NOVO,
    enquanto o objeto `app` (FastAPI) que este teste exercita é o do módulo
    ORIGINAL. Patchar o módulo errado faz o instante cravado não alcançar a
    rota, e o resultado passa a depender da ORDEM DE COLETA do pytest (o
    guardião passava sozinho e falhava na suíte inteira). Os globais da
    própria função-rota são a única referência que não erra.
    """
    for rota in app.routes:
        endpoint = getattr(rota, "endpoint", None)
        if getattr(endpoint, "__name__", None) == "options_proposta":
            return endpoint.__globals__
    raise AssertionError(
        "rota `options_proposta` não encontrada em app.routes — o guardião "
        "perdeu o ponto de ancoragem do relógio")


@pytest.fixture
def relogio_virado(monkeypatch):
    """Crava o MESMO instante nos três lugares que leem o relógio no caminho
    da proposta: a rota (`main`), o cálculo de prazo (`options_api`) e o
    calendário do provider mock."""
    globais_main = _globais_da_rota_de_proposta()

    # Falha LEGÍVEL em vez de KeyError/AttributeError cru: se o nome
    # `datetime` sumiu, é porque o helper BRT foi removido e o código voltou
    # ao `date.today()` naive — que é exatamente o defeito de 260911-dtx.
    _erro = ("perdeu o nome `datetime` — o helper de fuso BRT foi removido e "
             "o código voltou ao relógio naive (`date.today()`)")
    assert "datetime" in globais_main, f"app.main {_erro}"
    for modulo in (options_api, options_provider_mock):
        assert hasattr(modulo, "datetime"), f"{modulo.__name__}.py {_erro}"

    monkeypatch.setitem(globais_main, "datetime", _RelogioViradoEmUtc)
    monkeypatch.setattr(options_api, "datetime", _RelogioViradoEmUtc)
    monkeypatch.setattr(options_provider_mock, "datetime", _RelogioViradoEmUtc)


@pytest.fixture
def vencimento_pinado(monkeypatch):
    """Pina a ÚNICA expiração oferecida pelo provider mock. Devolve um
    fabricante: `pinar(15)` => vencimento a 15 dias do dia de BRASÍLIA."""
    def pinar(dias_de_brasilia: int) -> str:
        alvo = _HOJE_BRT + dt.timedelta(days=dias_de_brasilia)
        monkeypatch.setattr(
            options_provider_mock, "_proximas_terceiras_sextas",
            lambda hoje, n=3: [alvo])
        return alvo.isoformat()
    return pinar


@pytest.fixture
def espia_hoje(monkeypatch):
    """Espião de ARGUMENTO: registra o `hoje` que o chamador passou e delega
    para a função REAL. Nada da regra de prazo é substituído — é `propor()` de
    verdade que aceita ou recusa o candidato."""
    capturado = {}
    real_propor = opcoes_lastreadas.propor
    real_fechar = opcoes_lastreadas.proposta_fechar

    def _spy_propor(*args, **kwargs):
        capturado["propor"] = args[7] if len(args) > 7 else kwargs.get("hoje")
        return real_propor(*args, **kwargs)

    def _spy_fechar(*args, **kwargs):
        capturado["fechar"] = args[3] if len(args) > 3 else kwargs.get("hoje")
        return real_fechar(*args, **kwargs)

    monkeypatch.setattr(opcoes_lastreadas, "propor", _spy_propor)
    monkeypatch.setattr(opcoes_lastreadas, "proposta_fechar", _spy_fechar)
    return capturado


def _novo_escopo(cli, slug):
    email = f"fuso-dtx-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _seed_posicao(user_id, qty=300, price=30.0):
    store.buy(_conn, "PETR4", qty, price, user_id=user_id)


def _liga_operador(user_id):
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                             "appMode": "operador"}, user_id=user_id)


# ---------------------------------------------------------------------------
# (b) A PROVA QUE DECIDE: impacto no gate de prazo, pelo caminho real
# ---------------------------------------------------------------------------
def test_gate_aceita_contrato_na_borda_do_prazo_minimo_contado_em_brasilia(
        cli, relogio_virado, vencimento_pinado, espia_hoje):
    """Contrato a EXATAMENTE `_PRAZO_MIN_DIAS` dias do dia de Brasília: com o
    relógio naive (UTC) ele valia 14 dias e a rota devolvia
    `sem_vencimento_elegivel` — a proposta sumia da tela às 21:00 e voltava à
    meia-noite, sem nada ter mudado no mercado."""
    vencimento = vencimento_pinado(opcoes_lastreadas._PRAZO_MIN_DIAS)
    assert _dias_pelo_relogio_naive(vencimento) == opcoes_lastreadas._PRAZO_MIN_DIAS - 1, (
        "o cenário só prova alguma coisa se o cálculo naive ficar ABAIXO do "
        "piso enquanto o de Brasília fica exatamente NO piso")

    uid, headers = _novo_escopo(cli, "min")
    _seed_posicao(uid)
    r = cli.get("/api/options/proposta/PETR4", headers=headers)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["motivo"] != "sem_vencimento_elegivel", (
        "contrato a 15 dias de Brasília foi RECUSADO pelo gate de prazo — o "
        "'hoje' da rota voltou a ser o dia do container (UTC)")
    assert body["motivo"] == "call_coberta"
    assert body["proposta"] is not None
    assert body["proposta"]["expiration"] == vencimento
    # O chamador — não a função de prazo — é quem tinha o defeito.
    assert espia_hoje["propor"] == _HOJE_BRT


def test_gate_recusa_contrato_um_dia_alem_do_prazo_maximo_contado_em_brasilia(
        cli, relogio_virado, vencimento_pinado, espia_hoje):
    """Borda dos 60, onde o erro é o OPOSTO e mais grave: um contrato de 61
    dias reais era contado como 60 e ENTRAVA como candidato — o gate aceitando
    o que a regra exclui."""
    vencimento = vencimento_pinado(opcoes_lastreadas._PRAZO_MAX_DIAS + 1)
    assert _dias_pelo_relogio_naive(vencimento) == opcoes_lastreadas._PRAZO_MAX_DIAS

    uid, headers = _novo_escopo(cli, "max")
    _seed_posicao(uid)
    r = cli.get("/api/options/proposta/PETR4", headers=headers)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["motivo"] == "sem_vencimento_elegivel", (
        "contrato a 61 dias de Brasília foi ACEITO pelo gate de prazo — o "
        "relógio naive encolheu o prazo e fez o teto de 60 dias vazar")
    assert body["proposta"] is None
    assert espia_hoje["propor"] == _HOJE_BRT


def test_proposta_de_fechamento_tambem_recebe_o_dia_de_brasilia(
        cli, relogio_virado, vencimento_pinado, espia_hoje):
    """Terceiro chamador (`proposta_fechar`, ramo da posição lastreada já
    aberta): mesmo `hoje`, caminho distinto do ramo de proposta nova."""
    vencimento_pinado(30)
    uid, headers = _novo_escopo(cli, "fechar")
    _seed_posicao(uid)
    _liga_operador(uid)

    chain = cli.get("/api/options/chain/PETR4").json()
    contrato = chain["calls"][0]
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text

    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200, r.text
    assert espia_hoje["fechar"] == _HOJE_BRT, (
        "o ramo de FECHAMENTO voltou a passar o dia do container para o "
        "motor puro")


# ---------------------------------------------------------------------------
# (c) riskFlag de 21 dias — pelo caminho real da rota de análise
# ---------------------------------------------------------------------------
def test_risk_flag_de_vencimento_curto_usa_o_prazo_de_brasilia(
        cli, relogio_virado, vencimento_pinado):
    """22 dias reais NÃO são "vencimento curto" (<= 21). Com o relógio naive o
    contrato valia 21 dias e ganhava uma bandeira de risco que não é dele —
    theta exagerado sobre um prazo que o usuário não tem."""
    vencimento = vencimento_pinado(22)
    assert _dias_pelo_relogio_naive(vencimento) == 21

    chain = cli.get("/api/options/chain/PETR4").json()
    contrato = chain["calls"][0]
    assert contrato["daysToExpiration"] == 22

    r = cli.post("/api/options/analyze", json={
        "ticker": "PETR4", "expiration": vencimento,
        "contractSymbol": contrato["contractSymbol"],
    })
    assert r.status_code == 200, r.text
    flags = r.json()["riskFlags"]
    assert not any("Vencimento curto" in f for f in flags), (
        f"bandeira de vencimento curto num contrato de 22 dias: {flags}")


# ---------------------------------------------------------------------------
# (d) mydata_client — a janela `de` do histórico
# ---------------------------------------------------------------------------
def test_janela_de_historico_do_mydata_parte_do_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(mydata_client, "datetime", _RelogioViradoEmUtc)
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")

    chamadas = []

    async def fetch_json(path, params):
        chamadas.append((path, dict(params)))
        return {"dados": [], "proximo_cursor": None}

    asyncio.run(mydata_client.get_history("PETR4", rng="1mo", fetch_json=fetch_json))

    esperado = (_HOJE_BRT - dt.timedelta(days=mydata_client.RANGE_DIAS["1mo"])).isoformat()
    assert chamadas[0][1]["de"] == esperado, (
        "a janela do acervo partia do dia do container (UTC), pedindo ao hub "
        "um dia a menos do que o range nomeia")


# ---------------------------------------------------------------------------
# (e) Guardiões ESTRUTURAIS de CLASSE — o defeito não volta por um sexto ponto
# ---------------------------------------------------------------------------
_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"

# Os quatro módulos PUROS de opções não entram nesta lista de propósito: eles
# não podem nem referenciar relógio (guardião abaixo), então não têm o que
# corrigir — a fronteira deles é o que torna o `hoje` injetável.
_MODULOS_COM_PRAZO = (
    "options_api", "main", "mydata_client", "options_provider_mock",
)

_MODULOS_PUROS_DE_OPCOES = (
    "opcoes_lastreadas", "opcoes_motor", "opcoes_payoff", "opcoes_gatilho",
)


def _chamadas_de_atributo(caminho: pathlib.Path) -> list[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    return [
        no.func.attr for no in ast.walk(arvore)
        if isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
    ]


@pytest.mark.parametrize("nome_modulo", _MODULOS_COM_PRAZO)
def test_nenhum_modulo_de_prazo_volta_a_chamar_today(nome_modulo):
    """`today()` é sempre naive — não existe forma de chamá-lo com fuso. Num
    container em UTC ele é simplesmente o dia errado por 3 horas todo dia."""
    chamadas = _chamadas_de_atributo(_APP_DIR / f"{nome_modulo}.py")
    assert "today" not in chamadas, (
        f"{nome_modulo}.py voltou a chamar `today()` — use o helper BRT do "
        f"próprio módulo (`hoje_brt()` / `_hoje_brt()`). Em produção (Railway, "
        f"UTC) `today()` adianta o dia das 21:00 às 23:59 BRT e encurta todo "
        f"prazo até o vencimento em um dia.")


@pytest.mark.parametrize("nome_modulo", _MODULOS_PUROS_DE_OPCOES)
def test_modulos_puros_de_opcoes_continuam_sem_relogio(nome_modulo):
    """A correção do 260911-dtx é toda nos CHAMADORES. Se alguém "resolver" o
    fuso importando relógio para dentro do motor, a pureza que o guardião de
    fronteira protege (`test_opcoes_fronteira.py`) cai junto — e `propor()`
    deixa de ser reproduzível fora do processo do Boris."""
    chamadas = _chamadas_de_atributo(_APP_DIR / f"{nome_modulo}.py")
    ofensores = {c for c in chamadas if c in {"today", "now", "utcnow"}}
    assert not ofensores, (
        f"{nome_modulo}.py passou a ler relógio ({sorted(ofensores)}) — estes "
        f"módulos recebem `hoje` por ARGUMENTO por desenho; o dia tem que "
        f"continuar vindo do chamador.")


def test_assinaturas_que_injetam_hoje_seguem_congeladas():
    """Se `hoje` sair da assinatura, a correção deste achado deixa de ser
    testável pelo caminho real e o motor puro perde a única porta pela qual o
    tempo pode entrar nele."""
    import inspect

    assert list(inspect.signature(opcoes_lastreadas.propor).parameters) == [
        "underlying", "chain", "spot", "plano", "posicao", "cash", "modo",
        "hoje", "multiperna"]
    assert list(inspect.signature(opcoes_lastreadas.proposta_fechar).parameters) == [
        "pos_opcao", "chain", "modo", "hoje"]
    assert list(inspect.signature(opcoes_lastreadas._dias_ate).parameters) == [
        "expiration", "hoje"]
