"""Fase 27 (decisão D1 do Alex, 2026-09-13) — leitura técnica INTERNA da aba
Opções: tendência, volatilidade, suporte/resistência e a evolução de sete
pregões, a partir do Snapshot Técnico Único que o app já constrói.

POR QUE ESTE MÓDULO EXISTE
--------------------------
Até hoje, a aba Opções só sabia do comportamento do ativo se gastasse chamada
do serviço de opções — e o número de HOJE, sozinho, não responde a pergunta
que a pessoa faz na frente da tela ("a volatilidade subiu ou desabou nesta
semana?"). O motor que já alimenta Radar e Watchlist responde as duas coisas
de graça: custo ZERO, sem LLM, sem rede externa, determinístico.

É o princípio 5 do CLAUDE.md aplicado à aba: **o número é do motor, a IA só
interpreta.** Se a leitura técnica viesse de um serviço que cobra por consulta,
a tela teria de escolher entre gastar cota a cada abertura ou mostrar menos —
e a segunda opção é a que produz a tela muda de hoje.

A DIVISÃO DE TRABALHO (é a régua para quem acrescentar campo depois)
--------------------------------------------------------------------
· **Motor interno (aqui)** responde o que é do ATIVO: tendência, volatilidade
  histórica, suporte/resistência, evolução em sete pregões.
· **Serviço MCP** responde o que é da OPÇÃO: cadeia, vencimentos, estruturas
  operáveis, payoff, avaliação de setup. É o que só ele sabe.

Quem for acrescentar um campo novo decide por esta régua, não por
conveniência de qual chamada já está aberta.

ISTO EMENDA O ADR-027
---------------------
O ADR-027 fechou a fronteira entre a aba e o núcleo do app. A decisão D1 a
atravessa **deliberadamente**, e o registro é a "Emenda 2" no próprio ADR —
não uma nota de rodapé aqui. O que NÃO muda: o isolamento de FRONT
(`web/src/opcoes/*` não importa `App.jsx`) continua; a Decisão 2 ("fato ×
juízo") continua; e o §3.3 (custo de MCP só em clique explícito) fica mais
FORTE, não mais fraco — esta leitura existe justamente para a tela abrir sem
gastar.

PUREZA É PROPRIEDADE VERIFICADA, NÃO PROMESSA
---------------------------------------------
Este módulo recebe um snapshot já construído e não chama rede, não importa
`mcp_client`, `httpx`, `candle_provider`, `main` nem `options_mcp_api`. Um
teste de `ast` sobre este arquivo trava isso
(`test_modulo_nao_importa_rede_nem_o_servico_de_opcoes`): "custo zero" tem de
ser propriedade do grafo de imports, não frase de docstring.
"""
from __future__ import annotations

from typing import Optional

from . import regime

# Uma SEMANA de pregões. É a menor janela em que "a volatilidade subiu ou
# desabou" é visível (27-CONTEXT, D4): o número de hoje sozinho não distingue
# um ativo que acordou agitado de um que está assim há um mês. Sete também é
# o que cabe numa régua de 375 px sem virar gráfico — e o protótipo aprovado
# pelo Alex fixou exatamente sete segmentos.
PREGOES_DA_REGUA = 7

# Motivos em constante de módulo (padrão do 27-01, `MOTIVO_FORA_DO_SERVICO`):
# princípio 4 do CLAUDE.md — ausência vira travessão COM MOTIVO, nunca 0 — sem
# o mesmo texto redigitado em dois lugares.
MOTIVO_SEM_SERIE = (
    "Sem série de pregões neste snapshot: a régua não foi montada."
)
MOTIVO_REGUA_CURTA = (
    "Histórico curto: a régua mostra os %d pregões fechados que existem, "
    "não os %d de uma semana cheia."
)
MOTIVO_PREGAO_SEM_FECHAMENTO = (
    "%d pregão(ões) sem preço de fechamento foram PULADOS — nenhum deles foi "
    "preenchido por estimativa."
)
MOTIVO_SEM_PROFUNDIDADE = (
    "O snapshot não informa quantos pregões de histórico existem: cada pregão "
    "foi classificado sem esse filtro, e nenhuma profundidade foi inventada."
)
MOTIVO_PROFUNDIDADE_INCOERENTE = (
    "A profundidade de histórico declarada é menor que a janela exibida: os "
    "pregões mais antigos da régua ficaram sem filtro de janela."
)
MOTIVO_SEM_VOLATILIDADE = (
    "Este snapshot não traz volatilidade histórica medida — e nada é "
    "recalculado aqui."
)
MOTIVO_SEM_NIVEIS = (
    "Este snapshot não traz suporte/resistência calculados."
)
MOTIVO_SEM_TENDENCIA = (
    "Sem média de referência no snapshot: a direção não é afirmável."
)
MOTIVO_SEM_CARIMBO = (
    "Snapshot sem identidade: não dá para dizer de qual apuração esta leitura "
    "veio."
)


# --------------------------------------------------------------------------- #
# util
# --------------------------------------------------------------------------- #

def _num(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _da_cauda(serie, i: int, tamanho: int):
    """Valor de `serie` na posição `i` de uma janela de `tamanho` ALINHADA PELO
    FIM.

    O alinhamento é pelo fim e não pelo começo de propósito: o índice que
    importa é "hoje", e um snapshot em que uma série venha um elemento mais
    curta que as outras deve perder o pregão mais ANTIGO, nunca deslocar o
    mais recente — deslocar o recente trocaria o veredito de hoje pelo de
    ontem, em silêncio.
    """
    if not isinstance(serie, (list, tuple)):
        return None
    j = len(serie) - tamanho + i
    if j < 0 or j >= len(serie):
        return None
    return serie[j]


# --------------------------------------------------------------------------- #
# 1) a régua de sete pregões
# --------------------------------------------------------------------------- #

def regua(snap: dict) -> dict:
    """Estado de regime de cada um dos últimos `PREGOES_DA_REGUA` pregões
    FECHADOS, do mais antigo para hoje.

    Devolve `{"itens": [...], "motivo": str|None}`. Cada item é
    `{"data", "regime", "direcao", "forca", "adx14", "base", "confiavel",
    "hoje"}`, e `hoje` é `True` só no último.

    **Esta função NÃO reimplementa a combinação direção × força.** Ela monta um
    snapshot-sombra mínimo por índice e chama `regime.classificar` nele, um
    pregão por vez. Reimplementar o cruzamento aqui criaria a SEGUNDA régua de
    regime do app — exatamente a classe de defeito que o Snapshot Técnico Único
    existe para matar (dois lugares respondendo "qual é o regime da PETR4?" e
    divergindo num dia de fronteira). Se o limiar de ADX mudar, ele muda num
    lugar só, e esta régua acompanha sem tocar em nada.

    **A profundidade de histórico de cada pregão (`n_i`) é o ponto delicado.**
    `snap["indicators"]` é a CAUDA do período pedido (~126 velas no padrão da
    tela), enquanto `context.historyStats.candlesAvailable` conta a série
    INTEIRA que foi buscada — o range de fetch é fixo em 2 anos, qualquer que
    seja o período exibido. Usar a posição na cauda (`i + 1`) como profundidade
    daria 120–126 para os sete segmentos: abaixo do piso da SMA200, ou seja,
    TODOS cairiam em `base="sma50"`/`confiavel=False`, enquanto a linha de
    tendência logo acima — que passa o snapshot inteiro para a MESMA
    `classificar`, com ~500 — diria `sma200`/`confiavel=True`. Dois vereditos
    contraditórios sobre o mesmo dia, na mesma tela.

    Fórmula correta, com `L` = tamanho da janela e `i` o índice dentro dela:
    `n_i = max(0, candlesAvailable - (L - 1 - i))` — a profundidade que existia
    NAQUELE pregão. Em `i = L-1` ela vale exatamente `candlesAvailable`, e é
    por isso que o último item da régua sai idêntico a `classificar(snap)`.

    Quando `candlesAvailable` não existe, a profundidade viaja como `None` — a
    `classificar` já lê isso como "não sei, use a SMA200 se houver" — e o
    envelope registra o motivo. Nunca se inventa uma profundidade.
    """
    snap = snap or {}
    candles = snap.get("candles") or []
    ind = snap.get("indicators") or {}
    stats = (snap.get("context") or {}).get("historyStats") or {}
    disponivel = stats.get("candlesAvailable")
    try:
        disponivel = int(disponivel) if disponivel is not None else None
    except (TypeError, ValueError):
        disponivel = None

    motivos: list = []
    if not candles:
        return {"itens": [], "motivo": MOTIVO_SEM_SERIE}

    L = len(candles)
    janela = min(PREGOES_DA_REGUA, L)
    sem_fechamento = 0
    incoerente = False
    itens: list = []

    for i in range(L - janela, L):
        candle = candles[i] if isinstance(candles[i], dict) else {}
        fechamento = _num(candle.get("close"))
        if fechamento is None:
            # Série saneada não deveria produzir isto; se produzir, o pregão é
            # PULADO e declarado — preencher seria inventar um dia de mercado.
            sem_fechamento += 1
            continue
        if disponivel is None:
            n_i = None
        else:
            # n_i = candlesAvailable - (L - 1 - i): a profundidade de histórico
            # que existia NAQUELE pregão (ver a docstring — é a correção C7).
            n_i = max(0, disponivel - (L - 1 - i))
            if n_i == 0:
                incoerente = True
        sombra = {
            "close": fechamento,
            "summary": {
                "sma200": _da_cauda(ind.get("sma200"), i, L),
                "sma50": _da_cauda(ind.get("sma50"), i, L),
                "adx14": _da_cauda(ind.get("adx14"), i, L),
            },
            "context": {"historyStats": {"candlesAvailable": n_i}},
        }
        estado = regime.classificar(sombra)
        itens.append({
            "data": candle.get("date"),
            "regime": estado["regime"],
            "direcao": estado["direcao"],
            "forca": estado["forca"],
            "adx14": estado["adx14"],
            "base": estado["base"],
            "confiavel": estado["confiavel"],
            "hoje": False,
        })

    if itens:
        itens[-1]["hoje"] = True

    if len(itens) < PREGOES_DA_REGUA:
        motivos.append(MOTIVO_REGUA_CURTA % (len(itens), PREGOES_DA_REGUA))
    if sem_fechamento:
        motivos.append(MOTIVO_PREGAO_SEM_FECHAMENTO % sem_fechamento)
    if disponivel is None:
        motivos.append(MOTIVO_SEM_PROFUNDIDADE)
    if incoerente:
        motivos.append(MOTIVO_PROFUNDIDADE_INCOERENTE)

    return {"itens": itens, "motivo": " ".join(motivos) or None}


# --------------------------------------------------------------------------- #
# 2) a leitura completa (quatro blocos + carimbo)
# --------------------------------------------------------------------------- #

def _bloco_tendencia(snap: dict) -> dict:
    """`regime.classificar(snap)` inteiro — o regime de HOJE — mais as médias
    que a tela usa para mostrar em que base o filtro se apoiou.

    As médias saem do `summary` do snapshot tal e qual. O app calcula SMA de
    20/50/200 e EMA de 9/21; não existe "sma9"/"sma21" em lugar nenhum do
    motor, então expor esse par seria expor um campo que nunca tem valor.
    O `base` do `classificar` diz qual dessas médias decidiu a direção
    ("sma200" ou "sma50"), e é esse o dado que a tela precisa para não afirmar
    tendência confiável apoiada numa janela curta.
    """
    estado = dict(regime.classificar(snap))
    summ = (snap or {}).get("summary") or {}
    trend = ((snap or {}).get("context") or {}).get("trend") or {}
    estado["medias"] = {
        "sma20": _num(summ.get("sma20")),
        "sma50": _num(summ.get("sma50")),
        "sma200": _num(summ.get("sma200")),
        "ema9": _num(trend.get("ema9")),
        "ema21": _num(trend.get("ema21")),
    }
    estado["motivo"] = None if estado.get("base") else MOTIVO_SEM_TENDENCIA
    return estado


def _bloco_volatilidade(snap: dict) -> dict:
    """HV21/HV63/ATR% LIDOS do `context["volatility"]` que o Snapshot Técnico
    Único já produziu. **Nada é recalculado aqui, e isso é deliberado.**

    O `options_api._technical_context` faz o contrário: refaz a volatilidade
    histórica por conta própria, sobre uma série que ele mesmo busca. É a
    duplicação a NÃO repetir — duas contas da mesma grandeza sobre séries
    potencialmente diferentes é como nasce a divergência que ninguém consegue
    explicar na frente do usuário.

    `unidade` é **contrato, não anotação**, e sai SEMPRE — inclusive quando os
    valores são `None`. Razão concreta: o `hv21Pct` do `technical_models` está
    em PERCENTUAL (31.4 = 31,4%), enquanto o `hv21` que o serviço de opções
    devolve está em FRAÇÃO (0.31) e a tela o converte antes de exibir. Os dois
    números vão ficar lado a lado no mesmo ecrã. Sem o campo, a tela teria de
    adivinhar entre percentual e fração — e é assim que se erra 10× em
    silêncio, sem nenhum teste vermelho. É por este campo que o consumidor
    escolhe o formatador; um `unidade` que ninguém consome seria decoração, e
    decoração não impede erro nenhum.
    """
    vol = ((snap or {}).get("context") or {}).get("volatility")
    vol = vol if isinstance(vol, dict) else {}
    bloco = {
        "hv21Pct": _num(vol.get("hv21Pct")),
        "hv63Pct": _num(vol.get("hv63Pct")),
        "atr14Pct": _num(vol.get("atr14Pct")),
        # Unidade das TRÊS grandezas acima. Sempre presente — ver docstring.
        "unidade": "pct",
        "motivo": None,
    }
    if bloco["hv21Pct"] is None and bloco["hv63Pct"] is None:
        bloco["motivo"] = MOTIVO_SEM_VOLATILIDADE
    return bloco


def _bloco_niveis(snap: dict) -> dict:
    """`context["levels"]` verbatim — supports, resistances, o mais próximo de
    cada lado e as distâncias que o `technical_models` já calculou. Cópia rasa
    para que quem consome não consiga mutar o snapshot cacheado."""
    niveis = ((snap or {}).get("context") or {}).get("levels")
    if isinstance(niveis, dict) and niveis:
        return dict(niveis)
    return {
        "supports": None, "resistances": None,
        "nearestSupport": None, "nearestResistance": None,
        "distanceToSupportPct": None, "distanceToResistancePct": None,
        "motivo": MOTIVO_SEM_NIVEIS,
    }


def _carimbo(snap: dict) -> dict:
    """Princípio 3 do CLAUDE.md: a tela diz DE ONDE veio e DE QUANDO é.

    `snapshotId` é o que amarra esta leitura ao que o Radar e o painel técnico
    mostram — se os dois exibem o mesmo id, são os mesmos dados. `source` e
    `cacheStatus` dizem se o dado veio do provedor agora ou de cache, e
    `asOf` é o último pregão FECHADO (nunca "o agora").
    """
    snap = snap or {}
    bloco = {
        "snapshotId": snap.get("snapshotId"),
        "asOf": snap.get("asOf"),
        "generatedAt": snap.get("generatedAt"),
        "source": snap.get("source"),
        "cacheStatus": snap.get("cacheStatus"),
        "motivo": None,
    }
    if not bloco["snapshotId"] or not bloco["asOf"]:
        bloco["motivo"] = MOTIVO_SEM_CARIMBO
    return bloco


def leitura(snap: dict) -> dict:
    """A leitura técnica completa de um ativo para a aba Opções.

    `{"tendencia", "volatilidade", "niveis", "regua", "carimbo"}` — quatro
    blocos e a proveniência. Qualquer bloco cujo insumo não exista sai com os
    campos em `None` e um `motivo` legível ao lado: princípio 4 do CLAUDE.md,
    ausência com motivo, nunca `0` e nunca `"lateral"` por default.

    Puro: não muta o snapshot recebido (ele é cacheado por fingerprint em
    `technical_snapshot` e é o MESMO objeto que o Radar e a Watchlist leem).
    """
    snap = snap or {}
    return {
        "tendencia": _bloco_tendencia(snap),
        "volatilidade": _bloco_volatilidade(snap),
        "niveis": _bloco_niveis(snap),
        "regua": regua(snap),
        "carimbo": _carimbo(snap),
    }
