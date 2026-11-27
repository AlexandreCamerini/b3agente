"""Quick 261127 — legibilidade do push no iPhone (melhorias 1, 2 e 3).

Critérios de aceite verificáveis do diagnóstico:
  B1  título ≤40 e corpo ≤110 por tipo de push; vírgula decimal pt-BR;
      "(simulado/simulada)" continua no título das ordens.
  B2  `thread-id` = ticker quando há `t`; `subtitle` só com nome da tabela fixa.
  B3  `interruption-level` por kind (nunca time-sensitive); `apns-expiration`
      só no timing.
Nada aqui dispara push real: o cliente HTTP é um espião.
"""
import asyncio
import json
import os
import tempfile
import time

import pytest

from app import db, push, radar_daily, skill_ref, timing_watch

TITULO_MAX, CORPO_MAX = 40, 110


# ------------------------------------------------------------------ B1 ------
@pytest.mark.parametrize("modo", ["operador", "educacional"])
@pytest.mark.parametrize("tag", ["stop", "alvo", "entrada-auto", "pendente-executada", "pendente-cancelada"])
def test_titulos_das_ordens_cabem_e_dizem_simulado(modo, tag):
    # ticker mais longo plausível: 6 caracteres (ex.: BOVA11)
    t = skill_ref.push_titulo(modo, tag, "BOVA11")
    assert len(t) <= TITULO_MAX, (modo, tag, len(t), t)
    assert "simulad" in t.lower() or tag == "entrada-auto" and "simulad" in t.lower()


@pytest.mark.parametrize("modo", ["operador", "educacional"])
def test_corpo_de_stop_tem_virgula_decimal_e_cabe(modo):
    c = skill_ref.push_corpo(modo, "stop", {"preco": 36.2, "pnl": -184.0}, "fallback")
    assert "36,20" in c and "36.20" not in c
    assert "-R$ 184,00" in c
    assert len(c) <= CORPO_MAX


@pytest.mark.parametrize("modo", ["operador", "educacional"])
def test_corpo_de_alvo_mostra_sinal_do_resultado(modo):
    c = skill_ref.push_corpo(modo, "alvo", {"preco": 45.0, "pnl": 1234.5}, "x")
    assert "+R$ 1.234,50" in c and len(c) <= CORPO_MAX


@pytest.mark.parametrize("modo", ["operador", "educacional"])
def test_corpo_de_entrada_automatica(modo):
    c = skill_ref.push_corpo(modo, "entrada-auto", {"preco": 62.4, "qty": 100, "pctCaixa": 10.0}, "x")
    assert "62,40" in c and "100" in c and "10%" in c
    assert len(c) <= CORPO_MAX


def test_corpo_sem_numero_cai_no_texto_do_evento_cortado():
    longo = "x" * 300
    c = skill_ref.push_corpo("operador", "stop", {"preco": None, "pnl": 1.0}, longo)
    assert len(c) <= CORPO_MAX and c.endswith("…")
    # tag sem frase também degrada, nunca placeholder cru
    assert "{" not in skill_ref.push_corpo("educacional", "pendente-executada", {}, "Pendente executada.")


def test_timing_titulo_e_corpo_cabem_com_ticker_de_6_letras():
    novos = [("BOVA11", {"asOf": "2026-11-27T11:15:00-03:00"})]
    titulo, corpo = timing_watch.mensagem(novos)
    assert len(titulo) <= TITULO_MAX, (len(titulo), titulo)
    assert len(corpo) <= CORPO_MAX, (len(corpo), corpo)
    assert "Nada foi comprado" in corpo and "pode ter mudado" in corpo


def test_timing_agregado_cabe_mesmo_com_muitos_ativos():
    novos = [(t, {"asOf": "2026-11-27T10:15:00-03:00"})
             for t in ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "MGLU3"]]
    titulo, corpo = timing_watch.mensagem(novos)
    assert len(titulo) <= TITULO_MAX and len(corpo) <= CORPO_MAX, (titulo, corpo)
    assert "+3" in corpo


def test_radar_corpo_cabe_com_3_destaques():
    body = radar_daily.push_body({"results": (
        [{"ticker": "VALE3", "confluencia": 100, "veredito": "Estudar baixa"},
         {"ticker": "PETR4", "confluencia": 86, "veredito": "Estudar alta"},
         {"ticker": "ITUB4", "confluencia": 71, "veredito": "Monitorar"}]
        + [{"ticker": f"AAAA{i}", "confluencia": 0, "veredito": "x"} for i in range(1, 72)])})
    assert len(body) <= CORPO_MAX, (len(body), body)
    assert len(skill_ref.PUSH_RADAR["titulo"]) <= TITULO_MAX


def test_radar_corpo_vazio_cabe():
    body = radar_daily.push_body({"results": [{"ticker": "V", "confluencia": 0, "veredito": "x"}] * 74})
    assert len(body) <= CORPO_MAX


# --------------------------------------------------------------- B2 + B3 ----
class _Resp:
    status_code = 200

    def json(self):
        return {}


class _Cli:
    def __init__(self):
        self.chamadas = []

    async def post(self, url, headers=None, content=None):
        self.chamadas.append({"headers": headers, "payload": json.loads(content)})
        return _Resp()


def _enviar(monkeypatch, extra, **kw):
    for k, v in (("APNS_TEAM_ID", "T"), ("APNS_KEY_ID", "K"), ("APNS_AUTH_KEY", "-----BEGIN x"), ("APNS_TOPIC", "com.x")):
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(push, "_jwt", lambda: "jwt")
    conn = db.connect(os.path.join(tempfile.mkdtemp(prefix="b3_push_leg_"), "b3.db"))
    push.register_token(conn, "u1", "tok1")
    cli = _Cli()
    asyncio.run(push.send_to_user(conn, "u1", "t", "b", client=cli, extra=extra, **kw))
    return cli.chamadas[0]


def test_thread_id_e_o_ticker_e_subtitle_vem_da_tabela(monkeypatch):
    ch = _enviar(monkeypatch, {"kind": "ordem", "t": "PETR4"})
    aps = ch["payload"]["aps"]
    assert aps["thread-id"] == "PETR4"
    assert aps["alert"]["subtitle"] == "PETR4 · Petrobras PN"


def test_ticker_fora_do_catalogo_nao_inventa_nome(monkeypatch):
    ch = _enviar(monkeypatch, {"kind": "ordem", "t": "ZZZZ9"})
    aps = ch["payload"]["aps"]
    assert aps["thread-id"] == "ZZZZ9"          # agrupa mesmo sem nome
    assert "subtitle" not in aps["alert"]        # nunca inventa o nome


def test_sem_ticker_sem_thread_id_nem_subtitle(monkeypatch):
    aps = _enviar(monkeypatch, {"kind": "fechamento"})["payload"]["aps"]
    assert "thread-id" not in aps and "subtitle" not in aps["alert"]


@pytest.mark.parametrize("kind,nivel", [
    ("ordem", "active"), ("operador", "active"),
    ("timing", "passive"), ("radar", "passive"), ("fechamento", "passive")])
def test_interruption_level_por_kind(monkeypatch, kind, nivel):
    assert _enviar(monkeypatch, {"kind": kind})["payload"]["aps"]["interruption-level"] == nivel


def test_kind_desconhecido_ou_teste_nao_manda_nivel_e_nunca_time_sensitive(monkeypatch):
    for extra in (None, {"kind": "admin_kill_switch"}):
        assert "interruption-level" not in _enviar(monkeypatch, extra)["payload"]["aps"]
    assert all(v.get("nivel") != "time-sensitive" for v in push.ENTREGA_POR_KIND.values())


def test_apns_expiration_so_no_timing(monkeypatch):
    antes = int(time.time())
    h = _enviar(monkeypatch, {"kind": "timing", "t": "PETR4"})["headers"]
    exp = int(h["apns-expiration"])
    assert antes + 1700 <= exp <= antes + 1900          # ~30 min
    for kind in ("ordem", "radar", "fechamento"):
        assert "apns-expiration" not in _enviar(monkeypatch, {"kind": kind})["headers"]
