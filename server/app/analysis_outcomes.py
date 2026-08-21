"""qa/30 (Fase A) — autoavaliação da IA: cada análise (N1/scanDeep e
N2/analyze) que produz stop/alvo grava o que recomendou; um job diário
(encaixado no MESMO scheduler_loop do agent.py, sem scheduler novo — igual ao
padrão do radar_daily) confere, num prazo FIXO de 10 pregões, se o ativo
bateu o alvo, o stop, ou fechou o prazo sem decisão.

Escopo (decidido com o Alex): SÓ autoavaliação da IA aqui. Trades reais
(registro manual, mock modo-operador.html tela 4) é feature separada
(qa/30 Fase B), com seu próprio armazenamento — não usa nada deste módulo.

Puro/testável onde possível: `_avaliar_entry` não faz I/O (candles injetados);
`avaliar_pendentes`/`maybe_run` recebem `fetch` por injeção (mesmo padrão do
radar_daily.maybe_run), sem import direto de yahoo.py aqui.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db

BRT = timezone(timedelta(hours=-3))
HORIZON_PREGOES = 10   # decidido com o Alex: prazo FIXO, não "até bater stop/alvo"
CAP = 500               # teto de registros por escopo (evita blob JSON gigante no kv)
MAX_DIAS = 180          # prune por idade — o que vier primeiro entre CAP e MAX_DIAS

RESULTADOS_SUCESSO = ("alvo", "expirou_pos")
RESULTADOS_FALHA = ("stop", "expirou_neg")
RESULTADOS_NEUTROS = ("sem_gatilho",)
# ADR-015 / ADR15-02: desfecho que NÃO é sucesso nem falha — o preço nunca
# chegou ao gatilho dentro do prazo, então o trade não existiu. Contá-lo como
# perda inflaria a taxa de stop pelo mesmo tipo de viés que o ADR-015
# corrige. Quem conta "resolvidos" precisa excluí-lo — hoje são DOIS
# consumidores (compute_stats e automacao.correlacao_analise_operacao).

ANCORAS = ("gatilho", "mercado", "preco")
# ADR-015 / ADR15-02: é a âncora que DE FATO resolveu o registro, carimbada
# na resolução. NÃO confundir com `metodologiaVersao` (abaixo), que diz
# quais campos foram GRAVADOS: um registro N2 é versão 2 e resolve com
# âncora `preco`. Sem esse carimbo, o agregado do Plano 03 misturaria
# registro ancorado no gatilho com registro ancorado no preço sob o mesmo
# rótulo `metodologia: 2` — a mistura que o 06-CONTEXT.md proíbe
# explicitamente.

# qa/35 (P2, decidido com o Alex): células de segmentação com amostra menor
# que isto mostram "n insuficiente" em vez de porcentagem enganosa.
MIN_N = 10

METODOLOGIA_ATUAL = 2
# ADR-015 / ADR15-01: `metodologiaVersao` declara QUAIS CAMPOS o registro
# carrega no momento da GRAVAÇÃO — versão 1 (implícita, campo ausente) é o
# formato anterior ao ADR-015, sem `entrada`; versão 2 é o formato do
# ADR15-01 em diante, que carrega `entrada`/`entradaAMercado` quando o plano
# determinístico os definiu (N1) ou fica None quando não (N2, sem plano em
# escopo). Ele NÃO diz qual âncora resolveu o registro — isso é carimbado na
# RESOLUÇÃO pelo campo `ancora` (Plano 02, ADR15-02), porque um registro N2 é
# versão 2 e mesmo assim resolve pela âncora de PREÇO, não de gatilho.
# Confundir os dois é reintroduzir, com outro nome, a mistura de
# metodologias que o ADR-015 existe para corrigir. Registro antigo sem o
# campo NUNCA é reescrito para ganhá-lo — default 1 é só para leitura.


def _metodologia(entry: dict) -> int:
    """Versão de metodologia de UM registro, com default para formato antigo
    (campo ausente = versão 1, anterior ao ADR15-01). Puro; consumido pelos
    Planos 02/03 para nunca misturar metodologias no mesmo agregado."""
    return int(entry.get("metodologiaVersao") or 1)


def normalizar_confianca(valor) -> Optional[str]:
    """Escala única de confiança declarada pela IA: N1 usa `confianca`
    (baixa|moderada, teto sem 2º timeframe); N2 usa `conviccao`
    (Muito Alto|Alto|Médio|Baixo). Puro; devolve alta|moderada|baixa ou None."""
    v = str(valor or "").strip().lower()
    if not v:
        return None
    if v in ("muito alto", "alto", "alta"):
        return "alta"
    if v in ("médio", "medio", "moderada", "moderado"):
        return "moderada"
    if v in ("baixo", "baixa"):
        return "baixa"
    return None

# Telemetria em memória (mesmo padrão de radar_daily.LAST_DAILY — aparece no
# status_snapshot da Observabilidade).
LAST_EVAL = {"date": None, "avaliadas": 0, "erro": None}


def _key() -> str:
    return "analysisOutcomes"


def registrar(conn, *, ticker: str, modo: Optional[str], tipo: str, modelo: str,
              setup: Optional[str], recomendacao: Optional[str],
              stop: Optional[float], alvo: Optional[float], preco: Optional[float],
              snapshot_id: Optional[str], confianca=None, user_id=None,
              regime: Optional[str] = None,
              entrada: Optional[float] = None, alvo2: Optional[float] = None,
              rr2: Optional[float] = None, confluencia: Optional[int] = None,
              entrada_a_mercado: Optional[bool] = None) -> None:
    """Grava 1 análise (N1 ou N2) pra avaliação futura. Só faz sentido quando
    stop/alvo/preço estão definidos (sem risco não dá pra medir R-multiple nem
    decidir lado da operação) — o chamador filtra ANTES de chamar aqui.
    Nunca levanta: best-effort, o chamador decide se loga a falha.

    `regime` (qa/44, Refactor B / ADR-009→B): regime de mercado NO MOMENTO da
    análise (saída de `regime.classificar()["regime"]`), gravado pelo chamador
    — este módulo não importa `regime.py` para não acoplar avaliação a
    seleção. None = análise anterior ao B ou fluxo sem snapshot técnico
    (retrocompatível: cai na célula "—" em compute_stats)."""
    if stop is None or alvo is None or preco is None or stop == alvo:
        return
    entry = {
        "id": uuid.uuid4().hex,
        "ticker": ticker, "modo": modo or "estudo", "tipo": tipo, "modelo": modelo,
        "setup": setup, "recomendacao": recomendacao,
        "stopProposto": float(stop), "alvoProposto": float(alvo), "precoNaAnalise": float(preco),
        "snapshotId": snapshot_id,
        # qa/35 (P2c): confiança DECLARADA pela IA na hora da análise — vira a
        # base da calibração (declarada × acerto real). None = IA não declarou.
        "confianca": normalizar_confianca(confianca),
        # qa/44 (B, ADR-009): regime de mercado no momento da análise — a
        # chave que falta pro loop de validação segmentar por regime.
        "regime": regime,
        # ADR-015 / ADR15-01: campos que faltavam para ancorar a avaliação no
        # gatilho do plano determinístico, não no ruído entre close e
        # gatilho. Motivo verificado: 0 de 159 registros resolvidos em
        # produção tinham `entrada` — sem ele `_avaliar_entry` mede a
        # distância close↔gatilho, não a qualidade do motor. `entrada`/
        # `alvo2`/`rr2` vêm do plano determinístico (N1); `confluencia` é
        # descritiva do snapshot e existe também no N2. `entradaAMercado` é
        # tri-estado deliberado: None = não sabemos (N2 ou registro sem
        # plano), False = entrada no rompimento do gatilho, True = entrada a
        # mercado (setups.py:602-612, `plano["tipo"]` já rompido dentro da
        # zona de perseguição) — sem esse marcador o Plano 02 exigiria toque
        # de gatilho num plano cuja entrada já é imediata, descartando
        # silenciosamente o caso ADVERSO (gap contra a posição) do
        # denominador.
        "entrada": None if entrada is None else float(entrada),
        "alvo2": None if alvo2 is None else float(alvo2),
        "rr2": None if rr2 is None else float(rr2),
        "confluencia": None if confluencia is None else int(confluencia),
        "entradaAMercado": None if entrada_a_mercado is None else bool(entrada_a_mercado),
        "metodologiaVersao": METODOLOGIA_ATUAL,
        "criadoEm": datetime.now(timezone.utc).isoformat(),
        "prazoPregoes": HORIZON_PREGOES,
        "resultado": "pendente",
        "precoResolucao": None, "rMultiple": None, "resolvidoEm": None,
    }
    outcomes = db.kv_get(conn, _key(), [], user_id=user_id) or []
    outcomes.append(entry)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_DIAS)).isoformat()
    outcomes = [o for o in outcomes if (o.get("criadoEm") or "") >= cutoff]
    if len(outcomes) > CAP:
        outcomes = outcomes[-CAP:]
    db.kv_set(conn, _key(), outcomes, user_id=user_id)


def _celula(resolvidos: list) -> dict:
    """Métricas de UMA célula de segmentação (qa/35 P2). Puro. Abaixo de
    MIN_N devolve n + insuficiente=True e NENHUMA porcentagem — regra do
    Alex: amostra pequena não vira % enganosa."""
    n = len(resolvidos)
    if n < MIN_N:
        return {"n": n, "insuficiente": True, "taxaAcerto": None, "rMedio": None}
    sucesso = [o for o in resolvidos if o.get("resultado") in RESULTADOS_SUCESSO]
    r_vals = [o["rMultiple"] for o in resolvidos if o.get("rMultiple") is not None]
    return {
        "n": n, "insuficiente": False,
        "taxaAcerto": round(100 * len(sucesso) / n, 1),
        "rMedio": round(sum(r_vals) / len(r_vals), 2) if r_vals else None,
    }


def compute_stats(outcomes: list, modo: Optional[str] = None, tipo: Optional[str] = None) -> dict:
    """Agrega taxa de acerto / R médio / recorte por setup — usado pelo painel
    'Eficiência da IA'. Puro (sem I/O). qa/35 (P2, camadas a+c decididas com o
    Alex): + expectância (R médio por análise), profit factor e calibração da
    confiança declarada (alta×moderada×baixa) e por decisão. TODO cálculo aqui
    em Python — a LLM não calcula nada."""
    filtrado = [o for o in (outcomes or [])
                if (modo is None or o.get("modo") == modo) and (tipo is None or o.get("tipo") == tipo)]
    # ADR15-02: `sem_gatilho` (RESULTADOS_NEUTROS) sai de `resolvidos` — o
    # gatilho não foi tocado dentro do prazo, o trade não existiu; não é
    # acerto nem erro, e contá-lo como falha reproduziria, com outro nome, o
    # viés de stop fantasma que o ADR-015 corrige. Como os neutros saem
    # daqui, todas as segmentações/curva de R abaixo já ficam limpas por
    # construção (todas iteram sobre `resolvidos`).
    resolvidos = [o for o in filtrado
                  if o.get("resultado") not in (None, "pendente") and o.get("resultado") not in RESULTADOS_NEUTROS]
    pendentes = [o for o in filtrado if o.get("resultado") == "pendente"]
    nao_acionados = [o for o in filtrado if o.get("resultado") in RESULTADOS_NEUTROS]  # -> "naoAcionados" no retorno
    sucesso = [o for o in resolvidos if o.get("resultado") in RESULTADOS_SUCESSO]
    r_valores = [o["rMultiple"] for o in resolvidos if o.get("rMultiple") is not None]
    por_setup: dict = {}
    for o in resolvidos:
        s = o.get("setup") or "—"
        d = por_setup.setdefault(s, {"acerto": 0, "total": 0})
        d["total"] += 1
        if o.get("resultado") in RESULTADOS_SUCESSO:
            d["acerto"] += 1

    # --- qa/35 P2a: expectância -------------------------------------------------
    # Expectância por análise = média dos R-múltiplos (o rMedio de sempre, agora
    # nomeado como o que é). Profit factor = soma dos R positivos / |soma dos
    # negativos|. Com menos de MIN_N avaliadas, tudo vira "n insuficiente".
    suficiente = len(resolvidos) >= MIN_N
    r_pos = sum(r for r in r_valores if r > 0)
    r_neg = sum(r for r in r_valores if r < 0)
    profit_factor = None
    if suficiente and r_valores:
        if r_neg == 0:
            profit_factor = None if r_pos == 0 else float("inf")
        else:
            profit_factor = round(r_pos / abs(r_neg), 2)
    expectancia = round(sum(r_valores) / len(r_valores), 2) if (suficiente and r_valores) else None

    # --- qa/35 P2c: calibração --------------------------------------------------
    # A confiança que a IA DECLAROU bate com o acerto real? Célula por nível
    # declarado (alta/moderada/baixa; "—" = análises antigas sem o campo) e por
    # decisão (recomendacao). Cada célula respeita MIN_N.
    por_confianca: dict = {}
    por_decisao: dict = {}
    for o in resolvidos:
        por_confianca.setdefault(o.get("confianca") or "—", []).append(o)
        por_decisao.setdefault((o.get("recomendacao") or "—").strip() or "—", []).append(o)

    # --- qa/44 (B, ADR-009): segmentação por regime de mercado -----------------
    # Reusa _celula (mesma régua de MIN_N das demais segmentações). Registros
    # sem regime (anteriores ao B) caem em "—", sem quebrar a agregação —
    # retrocompatibilidade explícita, não acidente. `porSetupRegime` responde
    # a pergunta que o CLAUDE.md/skill exigem: "este setup tem expectância
    # positiva em tendência mas negativa em lateral?" — setup ausente (N2, que
    # não tem roster de setups) também normaliza para "—".
    por_regime: dict = {}
    por_setup_regime: dict = {}
    for o in resolvidos:
        rg = o.get("regime") or "—"
        por_regime.setdefault(rg, []).append(o)
        chave = f"{o.get('setup') or '—'} @ {rg}"
        por_setup_regime.setdefault(chave, []).append(o)

    # --- qa/37 P2e: curva de R acumulado + drawdown -----------------------------
    # Ordena os avaliados por data de resolução e soma os R-múltiplos → a curva
    # de R acumulado (equity curve em R). Drawdown máximo = maior queda do pico
    # até um vale posterior, em R. Só R interno — nenhum dado externo (o "vs
    # IBOV" foi descartado: R-múltiplo de análise não compara com retorno de
    # índice). A curva aparece com qualquer nº de pontos; o drawdown numérico
    # respeita MIN_N (amostra pequena não vira métrica enganosa).
    ordenados = sorted(
        [o for o in resolvidos if o.get("rMultiple") is not None],
        key=lambda o: (o.get("resolvidoEm") or "", o.get("criadoEm") or ""))
    curva_r = []
    acc = pico = 0.0
    dd_max = 0.0
    for o in ordenados:
        acc = round(acc + o["rMultiple"], 2)
        curva_r.append(acc)
        pico = max(pico, acc)
        dd_max = max(dd_max, pico - acc)
    drawdown_max = round(dd_max, 2) if suficiente and curva_r else None
    r_acumulado = curva_r[-1] if curva_r else None

    return {
        "totalAnalises": len(filtrado),
        "avaliadas": len(resolvidos),
        "pendentes": len(pendentes),
        # ADR15-02: gatilho não tocado dentro do prazo = o trade não
        # existiu; não é acerto nem erro, e por isso fica FORA de
        # avaliadas/taxaAcerto/expectância — visível aqui em separado.
        "naoAcionados": len(nao_acionados),
        "taxaAcerto": round(100 * len(sucesso) / len(resolvidos), 1) if resolvidos else None,
        "rMedio": round(sum(r_valores) / len(r_valores), 2) if r_valores else None,
        "porSetup": por_setup,
        # qa/35 P2 (a+c) — minN vai junto pro painel explicar a régua.
        "minN": MIN_N,
        "expectancia": expectancia,
        "profitFactor": ("inf" if profit_factor == float("inf") else profit_factor),
        "expectanciaInsuficiente": not suficiente,
        "porConfianca": {k: _celula(v) for k, v in por_confianca.items()},
        "porDecisao": {k: _celula(v) for k, v in por_decisao.items()},
        # qa/44 (B, ADR-009): recorte por regime e por (setup × regime).
        "porRegime": {k: _celula(v) for k, v in por_regime.items()},
        "porSetupRegime": {k: _celula(v) for k, v in por_setup_regime.items()},
        # qa/37 P2e: curva de R acumulado (para o gráfico) + drawdown máximo.
        "curvaR": curva_r,
        "rAcumulado": r_acumulado,
        "drawdownMax": drawdown_max,
    }


def outcomes_de_todos_os_usuarios(conn) -> list:
    """ADR-012 (Fase 3): outcomes CRUS de todos os escopos concatenados — para
    módulos que precisam cruzar por `snapshotId` (ver automacao.py). Sem
    MIN_N nem agregação; quem chama decide o que fazer com a granularidade
    individual. Não identifica usuário (outcomes não carregam `user_id`)."""
    todos: list = []
    for uid in _scopes_com_outcomes(conn):
        todos.extend(db.kv_get(conn, _key(), [], user_id=uid) or [])
    return todos


def compute_stats_all_users(conn, modo: Optional[str] = None, tipo: Optional[str] = None) -> dict:
    """ADR-012 (Fase 1): agregado cross-usuário pro portal admin. Reaproveita
    `outcomes_de_todos_os_usuarios` e `compute_stats` (puro, já testado) por
    cima da concatenação. NUNCA devolve `user_id` nem a lista bruta de
    outcomes — só o dict agregado, que já respeita MIN_N por célula (evita
    reidentificar usuário por amostra pequena). Chamador (endpoint admin) não
    deve expor outcomes crus."""
    return compute_stats(outcomes_de_todos_os_usuarios(conn), modo=modo, tipo=tipo)


def to_csv(outcomes: list) -> str:
    """Export CSV das análises registradas (qa/35 P2) — colunas fixas, uma
    linha por análise; célula vazia = dado indisponível (nunca inferido)."""
    cols = ("id", "ticker", "modo", "tipo", "modelo", "setup", "recomendacao",
            "confianca", "stopProposto", "alvoProposto", "precoNaAnalise",
            "snapshotId", "criadoEm", "prazoPregoes", "resultado",
            "precoResolucao", "rMultiple", "resolvidoEm",
            # ADR15-01: colunas novas SEMPRE no fim — quem consome o CSV
            # posicionalmente não pode quebrar. Registro antigo (sem estas
            # chaves) exporta célula vazia via esc(None), nunca valor inferido.
            "entrada", "alvo2", "rr2", "confluencia", "entradaAMercado",
            "metodologiaVersao",
            # ADR15-02: `ancora` (gatilho|mercado|preco) entrou no fim,
            # depois de `metodologiaVersao`, pelo mesmo motivo — não quebra
            # consumidor posicional. Registro ainda pendente (não resolvido)
            # não tem `ancora` gravado, exporta célula vazia.
            "ancora")

    def esc(v) -> str:
        if v is None:
            return ""
        s = str(v)
        return '"' + s.replace('"', '""') + '"' if any(ch in s for ch in ",\"\n") else s

    linhas = [",".join(cols)]
    for o in (outcomes or []):
        linhas.append(",".join(esc(o.get(c)) for c in cols))
    return "\n".join(linhas) + "\n"


def _scopes_com_outcomes(conn) -> list:
    """user_id de cada escopo com analysisOutcomes gravado + o escopo legado
    (global, user_id=None) quando existir — mesmo padrão de
    agent.list_server_users (varre o kv por sufixo de chave)."""
    rows = conn.execute(
        "SELECT key FROM kv WHERE key LIKE 'u:%:analysisOutcomes' OR key = 'analysisOutcomes'"
    ).fetchall()
    out = []
    for (key,) in rows:
        if key == "analysisOutcomes":
            out.append(None)
        else:
            out.append(key[len("u:"):-len(":analysisOutcomes")])
    return out


def _pregoes_apos(candles: list, criado_em: str) -> list:
    """Candles com data ESTRITAMENTE depois do dia da análise, em ordem
    cronológica (o dia da própria análise nunca conta como pregão decorrido)."""
    dia = (criado_em or "")[:10]
    janela = [c for c in (candles or []) if c.get("date") and c["date"] > dia]
    return sorted(janela, key=lambda c: c["date"])


def _avaliar_entry(entry: dict, candles: list) -> Optional[dict]:
    """Decide o resultado de UMA análise pendente dado o histórico de candles
    do ativo. Retorna None se o prazo (10 pregões, contado a partir do dia da
    análise — decisão "prazo FIXO" com o Alex) ainda não completou — mantém
    pendente. Sem I/O (candles injetados) — testável isoladamente.

    ADR-015 / ADR15-02: três caminhos, cada um com a âncora carimbada em
    `ancora` no dict devolvido:
    - `"preco"` — caminho LEGADO (registro sem `metodologiaVersao`, sem
      `entrada`) e também o registro N2 (versão 2 mas sem `entrada`, porque
      N2 não tem plano determinístico em escopo): a barreira já está aberta
      no candle 0, `preco0 = precoNaAnalise`. Byte-a-byte o comportamento
      anterior a este plano — não convertido por inferência, porque
      reconstruir `entrada` reintroduziria o viés que a mudança elimina.
    - `"gatilho"` — plano "no rompimento do gatilho" (tipo default de
      `setups.plano_operacional`): a barreira só abre depois de um candle
      TOCAR `entrada`; se nenhum candle do prazo tocar, o resultado é
      `"sem_gatilho"` (o trade nunca existiu — não é stop nem alvo).
    - `"mercado"` — plano "a mercado (gatilho já rompido, dentro da zona)":
      a entrada já é imediata (`setups.py:602-612` põe `entrada = close`),
      então a barreira abre no candle 0 sem exigir toque — um gap contra a
      posição no primeiro candle é `"stop"`, NUNCA `"sem_gatilho"` (senão o
      caso adverso sairia do denominador, o viés otimista oposto ao que o
      ADR-015 corrige).
    """
    janela = _pregoes_apos(candles, entry["criadoEm"])
    prazo = entry.get("prazoPregoes") or HORIZON_PREGOES
    if len(janela) < prazo:
        return None

    stop, alvo = entry["stopProposto"], entry["alvoProposto"]
    lado_compra = alvo > stop  # geometria do plano garante isso (setups.py: stop sempre do lado oposto ao alvo)

    entrada = entry.get("entrada")
    v2_com_entrada = _metodologia(entry) >= 2 and entrada is not None
    if not v2_com_entrada:
        ancora = "preco"  # legado e N2 (versão 2 sem plano determinístico em escopo)
    elif entry.get("entradaAMercado") is True:
        ancora = "mercado"
    else:
        # `entradaAMercado` ausente/None num registro com `entrada` cai em
        # "gatilho" — é o tipo default de `setups.plano_operacional` ("no
        # rompimento do gatilho") e é a escolha conservadora (exige
        # evidência de toque em vez de presumir entrada imediata).
        ancora = "gatilho"

    preco0 = float(entrada) if ancora in ("gatilho", "mercado") else entry["precoNaAnalise"]

    if ancora == "gatilho":
        i0 = None
        for i, c in enumerate(janela[:prazo]):
            hi, lo = c.get("high"), c.get("low")
            if hi is None or lo is None:
                continue
            tocou = (hi >= entrada) if lado_compra else (lo <= entrada)
            if tocou:
                i0 = i
                break
        if i0 is None:
            return {"resultado": "sem_gatilho", "precoResolucao": None,
                     "resolvidoEm": janela[prazo - 1]["date"], "rMultiple": None,
                     "ancora": "gatilho"}
    else:
        # "mercado"/"preco": em plano "a mercado" a entrada é IMEDIATA
        # (setups.py:602-612 põe entrada = close); exigir toque faria o gap
        # adverso do candle seguinte virar sem_gatilho e sair do
        # denominador — viés otimista, o oposto do objetivo do ADR-015.
        i0 = 0

    resultado = preco_resolucao = resolvido_em = None
    for c in janela[i0:prazo]:
        hi, lo = c.get("high"), c.get("low")
        if hi is None or lo is None:
            continue
        bateu_stop = (lo <= stop) if lado_compra else (hi >= stop)
        bateu_alvo = (hi >= alvo) if lado_compra else (lo <= alvo)
        if bateu_stop:  # cenário conservador quando os dois batem no mesmo candle
            resultado, preco_resolucao, resolvido_em = "stop", stop, c["date"]
            break
        if bateu_alvo:
            resultado, preco_resolucao, resolvido_em = "alvo", alvo, c["date"]
            break
    if resultado is None:
        c = janela[prazo - 1]
        # qa/39: candle de expiração sem close (dado sujo) → mantém pendente
        # (o loop de stop/alvo já protege high/low; este ramo não protegia).
        if c.get("close") is None:
            return None
        fechou_a_favor = (c["close"] >= preco0) == lado_compra
        resultado = "expirou_pos" if fechou_a_favor else "expirou_neg"
        preco_resolucao, resolvido_em = c["close"], c["date"]
    risco = abs(preco0 - stop)
    ganho = (preco_resolucao - preco0) if lado_compra else (preco0 - preco_resolucao)
    r_multiple = round(ganho / risco, 2) if risco else None
    return {"resultado": resultado, "precoResolucao": preco_resolucao,
            "resolvidoEm": resolvido_em, "rMultiple": r_multiple, "ancora": ancora}


async def avaliar_pendentes(conn, fetch) -> int:
    """Varre TODOS os escopos com outcomes pendentes, busca candles (via
    `fetch(ticker, rng=...)`, injetado — mesmo padrão do radar_daily.maybe_run)
    e resolve o que já completou o prazo. Retorna nº de entradas avaliadas."""
    total = 0
    for uid in _scopes_com_outcomes(conn):
        outcomes = db.kv_get(conn, _key(), [], user_id=uid) or []
        pendentes = [o for o in outcomes if o.get("resultado") == "pendente"]
        if not pendentes:
            continue
        por_ticker: dict = {}
        for o in pendentes:
            por_ticker.setdefault(o["ticker"], []).append(o)
        mudou = False
        for ticker, entries in por_ticker.items():
            try:
                hist = await fetch(ticker, rng="6mo")
            except Exception:  # noqa: BLE001 — 1 ativo sem cotação não trava os demais
                continue
            candles = (hist or {}).get("candles") or []
            for entry in entries:
                r = _avaliar_entry(entry, candles)
                if r:
                    entry.update(r)
                    mudou = True
                    total += 1
        if mudou:
            db.kv_set(conn, _key(), outcomes, user_id=uid)
    return total


def _hoje() -> str:
    return datetime.now(BRT).date().isoformat()


def last_run_date(conn) -> Optional[str]:
    """qa/42 (FinOps): gate PERSISTIDO (mesmo padrão de
    radar_daily.last_run_date). O `LAST_EVAL` em memória zera a cada deploy —
    o job inteiro rodava de novo, e ele baixa 6 meses de candles por ticker
    pendente POR USUÁRIO. Em dia de vários deploys, era Nx a mesma rede."""
    return db.kv_get(conn, "analysisOutcomesLastRun", None, user_id=None)


async def maybe_run(conn, fetch, cache_conn=None) -> Optional[int]:
    """Hook do scheduler: roda no máximo 1x/dia (mesmo padrão de
    radar_daily.maybe_run) — não precisa de horário fixo, só de rodar depois
    do fechamento do pregão pelo menos uma vez por dia.
    qa/42: o gate é persistido (kv), não só memória — deploy não re-executa.

    `cache_conn` (ADR-012, opcional — conexão de analytics.db): quando
    presente, recalcula o agregado cross-usuário do portal admin no MESMO
    job, sem scheduler novo — o admin nunca vê cálculo síncrono pesado numa
    request GET."""
    if LAST_EVAL["date"] == _hoje() or last_run_date(conn) == _hoje():
        return None
    try:
        n = await avaliar_pendentes(conn, fetch)
        LAST_EVAL.update(date=_hoje(), avaliadas=n, erro=None)
        db.kv_set(conn, "analysisOutcomesLastRun", _hoje(), user_id=None)
        if cache_conn is not None:
            try:
                from . import analytics as analytics_mod  # import local: sem ciclo de import
                analytics_mod.set_cache(cache_conn, "ia_eficiencia", compute_stats_all_users(conn))
            except Exception as e:  # noqa: BLE001 — cache nunca derruba a avaliação que já rodou
                print(f"[analysis-outcomes] refresh do cache admin falhou: {e}")
        return n
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_EVAL["erro"] = str(e)[:200]
        print(f"[analysis-outcomes] avaliação falhou: {e}")
        return None
