"""ACEITE — a análise da IA é reaproveitada enquanto a PERGUNTA for a mesma.

Dois objetivos no mesmo mecanismo:

  • COERÊNCIA (o que mais importa): antes, o `snapshotId` da análise era
    gravado e NUNCA comparado com o snapshot atual. Uma leitura de outro
    pregão ficava no card ao lado do veredito determinístico fresco, sem nada
    dizendo a idade dela — duas verdades sobre o mesmo ativo na mesma tela.
  • CUSTO: repetir a mesma pergunta não repaga.

A identidade é o HASH DO PROMPT FINAL, não uma lista de campos. Uma lista
envelheceria no dia em que alguém somasse um campo ao prompt e esquecesse de
somá-lo à chave — e o sintoma seria exatamente o defeito que estamos travando.
Por isso os testes abaixo variam CADA peça da personalização e exigem que a
impressão mude: é o que garante que reaproveitar nunca degrada a análise.
"""
import json

from app import llm

CONFIG = {"provider": "openai", "model": "gpt-4o-mini", "candlePeriod": "1y"}
SKILL = {"text": "Você é um operador sênior da B3."}
PROFILE = {"risco": "conservador", "horizonte": "swing", "toleranciaPerdaPct": 2,
           "objetivo": "crescimento", "experiencia": "iniciante"}
ACCOUNT = {"cash": 10000, "budget": 10000}
CONTEXT = {
    "snapshotId": "abc12345",
    "snapshotAt": "2026-08-07",
    "dataQuality": {"multiTimeframe": False},
    "setupsRadar": {"veredito": "Estudar alta", "confluencia": 100},
    "quote": {"price": 18.76, "change": -0.74},
    "resumo": "tendência de alta com pullback",
}


def _fp(**troca):
    base = {"config": CONFIG, "skill": SKILL, "profile": PROFILE, "account": ACCOUNT,
            "ticker": "PETR4", "context": CONTEXT, "modo": "estudo"}
    base.update(troca)
    return llm.prompt_fingerprint(base["config"], base["skill"], base["profile"],
                                  base["account"], base["ticker"], base["context"],
                                  modo=base["modo"])


def _com(d: dict, **campos) -> dict:
    novo = json.loads(json.dumps(d))
    novo.update(campos)
    return novo


# --------------------------------------------------------------------------
# Mesma pergunta ⇒ mesma impressão (é o que autoriza reaproveitar)
# --------------------------------------------------------------------------

def test_pergunta_identica_gera_a_mesma_impressao():
    assert _fp() == _fp(), "sem estabilidade não há reuso possível"


def test_impressao_e_curta_e_serializavel():
    fp = _fp()
    assert isinstance(fp, str) and 8 <= len(fp) <= 32, "vai viajar no payload e no kv"


# --------------------------------------------------------------------------
# Qualquer peça da PERSONALIZAÇÃO muda ⇒ a impressão muda ⇒ refaz.
# Cada teste aqui é uma forma de o reuso degradar a análise, e não vai poder.
# --------------------------------------------------------------------------

def test_snapshot_novo_vence_a_analise():
    """O caso do defeito: um candle fechou, a leitura anterior não vale mais."""
    assert _fp() != _fp(context=_com(CONTEXT, snapshotId="zzz99999"))


def test_perfil_de_risco_diferente_gera_analise_diferente():
    """Perfil entra no prompt (`llm._profile_line`). Servir a leitura de um
    conservador a um arrojado é perder exatamente a personalização que o
    reuso não pode custar."""
    arrojado = _com(PROFILE, risco="arrojado", toleranciaPerdaPct=8, experiencia="avancado")
    assert _fp() != _fp(profile=arrojado)


def test_conta_diferente_gera_analise_diferente():
    assert _fp() != _fp(account=_com(ACCOUNT, cash=250000, budget=250000))


def test_posicao_do_usuario_muda_a_leitura():
    """Reanálise SITUADA: quem está comprado recebe outra leitura."""
    comprado = _com(CONTEXT, userPosition={"qty": 300, "avg": 36.8, "stop": 34, "alvo": 45})
    assert _fp() != _fp(context=comprado)


def test_modo_estudo_e_operador_sao_leituras_diferentes():
    assert _fp(modo="estudo") != _fp(modo="operador")


def test_modelo_de_ia_diferente_gera_analise_diferente():
    """A mesma pergunta a outro modelo é outra resposta — inclusive quando um
    usuário traz a própria chave (BYOK) e o outro usa a gerenciada."""
    assert _fp() != _fp(config=_com(CONFIG, model="gpt-4o"))
    assert _fp() != _fp(config=_com(CONFIG, provider="anthropic"))


def test_skill_diferente_gera_analise_diferente():
    assert _fp() != _fp(skill={"text": "Outra instrução completamente diferente."})


def test_cotacao_ao_vivo_entra_na_identidade():
    """O preço viaja no prompt. Reaproveitar através de uma mudança de preço
    exibiria stop/alvo calculados sobre outro número."""
    assert _fp() != _fp(context=_com(CONTEXT, quote={"price": 22.10, "change": 4.2}))


# --------------------------------------------------------------------------
# Fiação da rota (guardião: já houve correção certa na função e esquecida lá)
# --------------------------------------------------------------------------

def test_rota_n2_decide_o_reuso_antes_de_chamar_a_ia():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert "llm.prompt_fingerprint" in src, "a rota não calcula a identidade da pergunta"
    assert src.index("llm.prompt_fingerprint") < src.index("llm.analyze_structured"), \
        "a decisão de reusar tem que vir ANTES de gastar a chamada"
    assert '"promptFp": prompt_fp' in src, "a impressão precisa voltar no payload guardado"
    assert '"reaproveitada": True' in src


def test_servidor_consulta_a_propria_copia_na_web():
    """Confiar só no `promptFp` que o cliente manda quebraria na web: o
    `A.analyze` é memoizado sem `analysis` nas dependências e enviaria uma
    impressão velha — reuso perdido em silêncio."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert 'store.get(_conn, "analyses", user_id=scope)' in src
    assert "fp_conhecida" in src


def test_os_dois_stores_mandam_a_impressao():
    """Paridade device × server: método novo entra nos DOIS. Sem isto o iOS
    ficava de fora do reuso E do vencimento — e é lá que o app roda."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[2] / "web" / "src" / "persistence.js").read_text(encoding="utf-8")
    assert src.count("promptFp") >= 4, "esperado: envio + fallback local nos dois stores"
    assert "reaproveitada" in src, "o device precisa saber manter a cópia dele"
    # o deviceStore descartava a rastreabilidade ao guardar
    assert "snapshotId: r.snapshotId || null" in src, \
        "o aparelho voltou a guardar análise sem marca de idade"


def test_analyze_structured_usa_o_mesmo_montador_do_fingerprint():
    """Se os dois montarem o prompt por caminhos separados, a impressão deixa
    de descrever a pergunta real e o reuso passa a servir texto errado."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "llm.py").read_text(encoding="utf-8")
    assert src.count("_structured_prompts(") >= 3, \
        "esperado: a definição + uso no fingerprint + uso no analyze_structured"


# ---------------------------------------------------------------------------
# A ROTA de verdade, ponta a ponta, com a IA substituída por um contador.
# Sem isto ficaria só a promessa de que a fiação está certa.
# ---------------------------------------------------------------------------

def test_rota_reaproveita_e_so_chama_a_ia_quando_a_pergunta_muda(monkeypatch):
    from fastapi.testclient import TestClient
    from app import candle_provider, db, main, store, technical_snapshot, yahoo

    T = "ZZZZ9"
    chamadas = {"n": 0}

    def _candles(_symbol, rng=None, **_kw):
        async def go():
            cs = [{"date": f"2026-01-01+{i}", "open": 10 + i * 0.1, "high": 10.2 + i * 0.1,
                   "low": 9.8 + i * 0.1, "close": 10 + i * 0.1, "volume": 1_000_000}
                  for i in range(260)]
            return {"candles": cs, "currency": "BRL"}
        return go()

    async def _quote(_t):
        return {"price": 35.9, "change": -0.4}          # fixo: preço entra na identidade

    async def _fake_llm(*_a, **_k):
        chamadas["n"] += 1
        return {"kpis": {"recomendacao": "Aguardar", "conviccao": "Médio"},
                "detail": {}, "proposal": {}, "markdown": "leitura " + str(chamadas["n"]),
                "text": "leitura " + str(chamadas["n"])}

    monkeypatch.setattr(candle_provider, "get_history", _candles)
    monkeypatch.setattr(yahoo, "get_quote", _quote)
    monkeypatch.setattr(main.llm, "analyze_structured", _fake_llm)
    technical_snapshot.reset()

    try:
        with TestClient(main.app) as c:
            r1 = c.post(f"/api/technical/analyze/{T}", json={"model": "completo"}).json()
            assert chamadas["n"] == 1, "a 1ª leitura tem que gastar IA"
            assert r1.get("promptFp"), "a identidade da pergunta precisa voltar no payload"
            assert not r1.get("reaproveitada")

            r2 = c.post(f"/api/technical/analyze/{T}", json={"model": "completo"}).json()
            assert chamadas["n"] == 1, "MESMA pergunta chamou a IA de novo"
            assert r2.get("reaproveitada") is True
            assert r2.get("markdown") == r1.get("markdown"), \
                "reaproveitar tem que devolver a MESMA leitura — senão vira outra verdade"
            assert r2.get("promptFp") == r1.get("promptFp")

            r3 = c.post(f"/api/technical/analyze/{T}",
                        json={"model": "completo",
                              "profile": {"risco": "arrojado", "toleranciaPerdaPct": 9}}).json()
            assert chamadas["n"] == 2, "perfil novo tem que refazer a leitura"
            assert not r3.get("reaproveitada")
    finally:
        analyses = store.get(main._conn, "analyses", user_id=None) or {}
        analyses.pop(T, None)
        db.kv_set(main._conn, "analyses", analyses, user_id=None)
        technical_snapshot.reset()


# ---------------------------------------------------------------------------
# UMA FONTE PARA O QUE É EXPOSTO. Guardiões de UI (o projeto trava invariantes
# de front por leitura do fonte — mesmo padrão de `test_run_daily_usa_o_push_body`).
# ---------------------------------------------------------------------------

def _app_jsx() -> str:
    import pathlib
    return (pathlib.Path(__file__).resolve().parents[2] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")


def test_manchete_nunca_cai_na_recomendacao_da_ia():
    """A Watchlist caía em `kp.recomendacao` quando não havia plano; o Radar
    sempre usou o motor. Mesmo ativo, mesmo lugar da tela, fontes diferentes."""
    src = _app_jsx()
    assert "rotuloDec || (kp.recomendacao" not in src, \
        "a manchete voltou a ter duas fontes conforme a tela"
    assert "const decM = rotuloDec || null;" in src


def test_ausencia_de_plano_e_dita_e_nao_preenchida():
    src = _app_jsx()
    assert "Sem leitura do motor para este ativo agora" in src, \
        "sem plano, o espaço não pode ficar mudo nem ser preenchido com opinião da IA"


def test_analise_de_outro_snapshot_e_marcada():
    src = _app_jsx()
    assert "anVencida" in src
    assert "A leitura da IA abaixo é de outro momento do mercado" in src


def test_botao_de_compra_nao_carrega_uma_segunda_recomendacao():
    src = _app_jsx()
    assert "(leitura: " not in src, \
        "voltou a haver duas recomendações no mesmo card"
