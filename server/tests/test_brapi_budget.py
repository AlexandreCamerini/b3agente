"""ADR-008, Fase 2 (qa/43) — orçamento de requisições da brapi.

O que estes testes protegem:
  • a cota de 15.000/mês é finita e recusa DEBITA cota — o controle é local e
    ANTES da chamada, então o contador tem que ser confiável;
  • consumo só em DIA COM PREGÃO (calendário da B3, sem feriado) até 17:15
    BRT — janela mais larga que a de execução, p/ caber o delta de fechamento;
  • fatia estourada consome da reserva; reserva esgotada bloqueia a fatia;
  • SOFT STOP a 80% (degradado → TTL alonga) e HARD STOP no teto do dia;
  • o contador sobrevive a restart (persistência no kv do SQLite);
  • o teto acompanha B3_BRAPI_COTA_MES sem deploy.
Offline: relógio injetado; SQLite em memória.
"""
import concurrent.futures
import sqlite3
import threading
import time
from datetime import datetime

import pytest

from app import brapi_budget as bb

TER_11H = datetime(2026, 8, 11, 11, 0, tzinfo=bb.BRT)    # terça, pregão aberto
TER_17H10 = datetime(2026, 8, 11, 17, 10, tzinfo=bb.BRT)  # janela do delta
TER_18H = datetime(2026, 8, 11, 18, 0, tzinfo=bb.BRT)     # pós-janela
SAB_11H = datetime(2026, 8, 15, 11, 0, tzinfo=bb.BRT)     # sábado


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    bb.reset()
    bb.configure_db(None, enabled=False)
    monkeypatch.delenv("B3_BRAPI_COTA_MES", raising=False)
    yield
    bb.reset()
    bb.configure_db(None, enabled=False)


def test_teto_e_fatias_derivam_da_cota():
    assert bb.teto_dia() == 15000 // 21 == 714
    assert bb.fatia_limite("spot") == int(714 * 400 / 700) == 408
    assert bb.fatia_limite("delta") == int(714 * 150 / 700) == 153
    soma = sum(bb.fatia_limite(f) for f in ("spot", "delta", "fund"))
    assert bb._reserva_limite() == 714 - soma > 0


def test_cota_ajustavel_por_env_sem_deploy(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "2100")
    assert bb.teto_dia() == 100
    assert bb.fatia_limite("spot") == int(100 * 400 / 700)


def test_janela_de_pregao():
    assert bb.em_pregao(TER_11H) is True
    assert bb.em_pregao(TER_17H10) is True       # delta pós-fechamento cabe
    assert bb.em_pregao(TER_18H) is False
    assert bb.em_pregao(SAB_11H) is False


def test_orcamento_nao_libera_gasto_em_feriado():
    """2026-08-17: o dia útil passou a vir de `pregao.is_trading_day`, então
    feriado da B3 deixa de autorizar consumo. Antes, `em_pregao` só olhava
    weekday e o comentário assumia que "feriado não gera demanda" — assumia
    errado, porque o laço do agente também ignorava feriado e rodava o dia
    inteiro."""
    from datetime import datetime
    natal_11h = datetime(2026, 12, 25, 11, 0, tzinfo=bb.BRT)   # sexta-feira
    assert bb.em_pregao(natal_11h) is False
    assert bb.pode_gastar("spot", now=natal_11h) is False


def test_janela_do_orcamento_e_MAIS_LARGA_que_a_de_execucao():
    """Distinção deliberada, e o `test_janela_de_pregao` acima é quem a protege:
    executar ordem para às 16:55 (`pregao.in_market_hours`), mas o ORÇAMENTO vai
    até 17:15 porque a passada de delta busca o preço de FECHAMENTO — gasto
    legítimo, na única hora em que aquele dado existe. Achatar as duas janelas
    numa só quebra o delta pós-fechamento."""
    from app import pregao
    assert pregao.in_market_hours(TER_17H10) is False   # não executa ordem
    assert bb.em_pregao(TER_17H10) is True              # mas pode gastar cota


def test_fora_da_janela_nao_gasta():
    assert bb.pode_gastar("spot", now=TER_18H) is False
    assert bb.pode_gastar("spot", now=SAB_11H) is False
    assert bb.pode_gastar("spot", now=TER_11H) is True


def test_fatia_estourada_consome_reserva_e_depois_bloqueia(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "210")   # teto 10: spot 5, delta 2, fund 0
    lim_spot = bb.fatia_limite("spot")
    reserva = bb._reserva_limite()
    for _ in range(lim_spot):
        assert bb.pode_gastar("spot", now=TER_11H)
        bb.debita("spot", now=TER_11H)
    # fatia cheia → passa a consumir reserva
    for _ in range(reserva):
        assert bb.pode_gastar("spot", now=TER_11H)
        bb.debita("spot", now=TER_11H)
    assert bb.pode_gastar("spot", now=TER_11H) is False   # reserva esgotada


def test_hard_stop_no_teto_do_dia(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "210")   # teto 10
    for _ in range(bb.teto_dia()):
        bb.debita("delta", now=TER_11H)
    assert bb.pode_gastar("delta", now=TER_11H) is False
    assert bb.pode_gastar("spot", now=TER_11H) is False   # teto vale p/ o dia


def test_soft_stop_degrada_aos_80_por_cento(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "2100")  # teto 100: spot 57
    lim = bb.fatia_limite("spot")
    quase = int(lim * 0.8)           # ainda ABAIXO do limiar (80% exato de 57 é 45,6)
    for _ in range(quase):
        bb.debita("spot", now=TER_11H)
    assert bb.degradado("spot", now=TER_11H) is False
    bb.debita("spot", now=TER_11H)   # cruza os 80%
    assert bb.degradado("spot", now=TER_11H) is True
    assert bb.pode_gastar("spot", now=TER_11H) is True    # degrada, não bloqueia


def test_contador_sobrevive_a_restart():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    bb.configure_db(conn)
    bb.debita("spot", n=7, now=TER_11H)
    bb.reset()                                   # "restart": memória zera
    bb.configure_db(conn)
    snap = bb.snapshot(now=TER_11H)
    assert snap["fatias"]["spot"]["gasto"] == 7  # veio do kv, não da memória
    assert snap["total"] == 7


def test_dia_novo_zera_o_contador():
    bb.debita("spot", n=5, now=TER_11H)
    qua = datetime(2026, 8, 12, 11, 0, tzinfo=bb.BRT)
    assert bb.snapshot(now=qua)["total"] == 0


def test_snapshot_expoe_previsao_e_verdade_do_header(monkeypatch):
    from app import brapi
    monkeypatch.setitem(brapi.LAST_RATELIMIT, "x-ratelimit-remaining", "14980")
    bb.debita("spot", now=TER_11H)
    s = bb.snapshot(now=TER_11H)
    assert s["fatias"]["spot"]["gasto"] == 1 and s["tetoDia"] == 714
    assert s["headerRateLimit"]["x-ratelimit-remaining"] == "14980"
    assert s["emPregao"] is True


# ---------------------------------------------------------------------------
# Controle de utilização: intervalo → projeção mensal (determinística)
# ---------------------------------------------------------------------------
def test_projecao_e_pura_e_deterministica():
    # ATUALIZADO EM 2026-08-17: a janela do SPOT deixou de ser 7,25 h fixas
    # (26100 s, herdadas da janela do orçamento) e passa a ser a de NEGOCIAÇÃO
    # de verdade — 10:00–16:55 = 24900 s —, porque é só nela que o laço
    # atualiza spot. Eram 1.200 s a mais por pregão, deixando a projeção ~5%
    # pessimista. Os números caíram na mesma proporção; a intenção do teste
    # (projeção pura e determinística) não mudou.
    p = bb.projecao(300, universo_n=65, cota=15000)
    # spot: 65 × (24900//300=83) × 21 = 113295; delta: 65×21=1365; fund: 1365//7=195
    assert p["detalhe"] == {"spot": 113295, "delta": 1365, "fundamentos": 195}
    assert p["chamadasMes"] == 114855
    assert p["cabeNaCota"] is False
    assert p["percentualDaCota"] == round(114855 / 15000 * 100, 1)
    # intervalo mínimo seguro: refresh_max = (15000−1560)/(65×21) ≈ 9,84/pregão
    # → 24900/9,84 ≈ 2530s (+1). Caiu junto com a janela (era ~2652 com 26100s).
    assert 2500 < p["intervaloMinimoSeguro"] < 2600
    # e o mínimo seguro de fato cabe
    p2 = bb.projecao(p["intervaloMinimoSeguro"], universo_n=65, cota=15000)
    assert p2["cabeNaCota"] is True


def test_projecao_universo_zero_nao_divide_por_zero():
    p = bb.projecao(300, universo_n=0, cota=15000)
    assert p["chamadasMes"] == 0 and p["cabeNaCota"] is True
    assert p["intervaloMinimoSeguro"] is None


def test_intervalo_configuravel_persiste_e_alimenta_snapshot():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    bb.configure_db(conn)
    assert bb.spot_intervalo_s() == 300          # default
    bb.set_spot_intervalo(600)
    bb.reset()                                    # "restart"
    bb.configure_db(conn)
    assert bb.spot_intervalo_s() == 600          # veio do kv
    s = bb.snapshot(now=TER_11H)
    assert s["spotIntervaloS"] == 600
    assert s["projecaoMes"]["intervaloS"] == 600
    assert s["projecaoMes"]["chamadasMes"] == bb.projecao(600, bb._universo_n())["chamadasMes"]


def test_intervalo_minimo_de_30s():
    assert bb.set_spot_intervalo(5) == 30


# ---------------------------------------------------------------------------
# A-11 (auditoria de 2026-09-10): trava + `reservar()` portados do irmão
# `mydata_budget.py`, que fechou esta classe no WR-01.
#
# Estes guardiões são de DEFESA EM PROFUNDIDADE, não de defeito ativo: a
# verificação adversarial da auditoria rodou 50 chamadas concorrentes contra o
# contador SEM trava e não corrompeu nada, porque nenhum call site real tem
# ponto de espera entre a checagem e o débito. O que eles travam é a simetria
# entre os dois módulos de orçamento — com um irmão travado e o outro não, o
# próximo refactor que meta um await no meio reintroduz o problema calado.
# Mesma técnica e mesmas asserções de `test_mydata_budget.py`.
# ---------------------------------------------------------------------------
def test_debitos_concorrentes_nao_perdem_incremento(monkeypatch):
    """`_estado["total"] += n` e o dict de fatias são read-modify-write. Este
    teste é o ESPELHO do guardião do irmão (`test_mydata_budget.py`) e passa
    com e sem a trava — medido: 200 rodadas da corrida sem trava, zero
    incremento perdido, porque `debita()` não tem ponto de espera por dentro.
    Fica como guardião de SIMETRIA (os dois módulos travam o mesmo estado); a
    prova da atomicidade está no teste seguinte, que injeta a pausa."""
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "210000")   # teto do dia = 10.000
    barreira = threading.Barrier(8)

    def _debita_um():
        barreira.wait(timeout=5)
        bb.debita("spot", n=1, now=TER_11H)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda _: _debita_um(), range(8)))

    s = bb.snapshot(now=TER_11H)
    assert s["total"] == 8
    assert s["fatias"]["spot"]["gasto"] == 8


def test_reservar_e_atomico_onde_o_par_separado_estoura_a_cota(monkeypatch):
    """O guardião que de fato PROVA a trava.

    A auditoria derrubou a consequência do A-11: sem ponto de espera entre a
    checagem e o débito, a corrida é INERTE (50 chamadas concorrentes, zero
    corrupção — reproduzido aqui em 200 rodadas). Então um teste que só dispare
    duas threads passa com e sem trava e não prova nada.

    Este injeta exatamente a pausa que o código hoje NÃO tem e que o próximo
    refactor introduz (um await/IO entre checar e debitar) e compara os dois
    caminhos sob a MESMA pausa:
      • par separado `pode_gastar()` + `debita()` → as duas threads veem vaga e
        as duas debitam: 2 requisições com teto de 1 (medido: 20/20 rodadas);
      • `reservar()` → UMA True, UMA False, total 1 (medido: 0/20 estouros).
    Com a cota real (15.000/mês) isso é cota queimada além do teto do dia, que
    é justamente o que o orçamento existe para impedir."""
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "21")   # teto do dia = 1
    assert bb.teto_dia() == 1

    real_pode = bb.pode_gastar

    def pode_gastar_com_pausa(fatia, now=None):
        r = real_pode(fatia, now=now)
        time.sleep(0.02)          # a janela que o refactor futuro abre
        return r
    monkeypatch.setattr(bb, "pode_gastar", pode_gastar_com_pausa)

    def _corrida(fn):
        bb.reset()
        barreira = threading.Barrier(2)

        def _r():
            barreira.wait(timeout=5)
            return fn("spot", now=TER_11H)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f1, f2 = ex.submit(_r), ex.submit(_r)
            res = sorted([f1.result(), f2.result()])
        return res, bb.snapshot(now=TER_11H)["total"]

    def par_separado(fatia, n=1, now=None):
        if not bb.pode_gastar(fatia, now=now):
            return False
        bb.debita(fatia, n=n, now=now)
        return True

    res_par, total_par = _corrida(par_separado)
    assert res_par == [True, True], "o par separado é o caminho que estoura"
    assert total_par == 2 > bb.teto_dia(), "duas requisições com teto de uma"

    res_res, total_res = _corrida(bb.reservar)
    assert res_res == [False, True], "reservar: uma ganha a vaga, a outra recusa"
    assert total_res == 1, "nunca debita quando devolve False"


def test_reservar_equivale_a_pode_gastar_mais_debita(monkeypatch):
    """Guardião de EQUIVALÊNCIA: `reservar()` não pode ter inventado política
    nova — é exatamente o par antigo, junto. Mesmo débito, mesma fatia."""
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "21000")   # teto do dia = 1.000
    assert bb.reservar("spot", now=TER_11H) is True
    s = bb.snapshot(now=TER_11H)
    assert s["total"] == 1 and s["fatias"]["spot"]["gasto"] == 1

    bb.reset()
    assert bb.pode_gastar("spot", now=TER_11H) is True
    bb.debita("spot", now=TER_11H)
    s2 = bb.snapshot(now=TER_11H)
    assert (s2["total"], s2["fatias"]["spot"]["gasto"]) == (1, 1)


def test_reservar_respeita_o_gate_de_pregao_sem_debitar():
    """Fora da janela de consumo `pode_gastar()` é False — `reservar()` herda
    isso e NÃO pode debitar (o gate de pregão é a primeira linha de defesa da
    cota)."""
    assert bb.reservar("spot", now=TER_18H) is False
    assert bb.snapshot(now=TER_18H)["total"] == 0
    assert bb.reservar("spot", now=SAB_11H) is False
    assert bb.snapshot(now=SAB_11H)["total"] == 0


def test_reservar_cai_na_reserva_quando_a_fatia_enche(monkeypatch):
    """A política de fatia→reserva é de `debita()`; `reservar()` a herda sem
    reimplementar."""
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "21000")   # teto 1.000
    limite_fund = bb.fatia_limite("fund")
    for _ in range(limite_fund):
        assert bb.reservar("fund", now=TER_11H) is True
    assert bb.snapshot(now=TER_11H)["fatias"]["fund"]["gasto"] == limite_fund

    assert bb.reservar("fund", now=TER_11H) is True     # agora vai p/ reserva
    assert bb.snapshot(now=TER_11H)["fatias"]["reserva"]["gasto"] == 1
    assert bb.snapshot(now=TER_11H)["fatias"]["fund"]["gasto"] == limite_fund


def test_trava_e_reentrante_como_no_irmao():
    """`reservar()` chama `pode_gastar()`/`debita()` por dentro da própria
    trava — com `Lock` em vez de `RLock` isso travaria o processo. Guardião do
    tipo, não do comportamento: um `Lock` passaria nos testes acima só porque
    eles não aninham."""
    assert isinstance(bb.BRAPI_BUDGET_LOCK, type(threading.RLock()))
    with bb.BRAPI_BUDGET_LOCK:
        with bb.BRAPI_BUDGET_LOCK:      # reentrada: não pode bloquear
            assert True
