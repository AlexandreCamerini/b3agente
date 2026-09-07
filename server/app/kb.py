"""Base de conhecimento determinística da B3 (Fase F2 do plano do assistente,
roteamento de F3).

O que este módulo é:

  • DETERMINÍSTICO E GRÁTIS. Nenhuma chamada de LLM em nenhum caminho deste
    módulo. `catalogo()`/`verbete()`/`buscar()`/`resolver()` respondem na
    hora, para anônimo, sem custo — a mesma filosofia de `conceitos.py`.
  • REFERÊNCIA, NÃO CÓPIA (decisão D4 do plano). Onde o texto já existe em
    `conceitos.py` (gatilho, stop, alvo, r, confluência, fundamento,
    barra15m), a KB deriva de `conceitos.montar(...)` — o MESMO texto que a
    folha "?" do app mostra — em vez de reescrever. Onde o número já é
    canônico em `skill_ref.py` (RR_MIN/RR_IDEAL, FUND_*) ou é o estado real
    de `timing.py`, a KB interpola a partir de lá. Só os verbetes que não têm
    fonte determinística no código (definição textual de indicador, glossário
    de mercado) têm prosa própria, escrita seguindo a mesma lei de
    vocabulário do resto do produto.
  • CATÁLOGO + ROTEAMENTO. `catalogo()`/`verbete()`/`buscar()` (Fase F2) dão
    acesso ao catálogo; `resolver()` (Fase F3) é o crivo de confiança que
    `/api/assistente` consulta ANTES de chamar a LLM — `None` quando a KB não
    cobre a pergunta com segurança, verbete formatado (`fonte: "kb"`) quando
    cobre. A rota `GET /api/kb/buscar` usa `buscar()` + `formatar()`
    diretamente (busca pública, sem o corte de confiança de `resolver()`).

Formato de um verbete (dict):
    id       — string curta e estável, kebab-case (ex.: "ind-rsi").
    termos   — tupla de strings de busca que levam ao verbete (sinônimos,
               abreviações, nome do campo no app).
    familia  — uma das 9 categorias do plano F2: "indicadores", "estrutura",
               "familias", "modelos", "setups", "plano_risco", "fundamentos",
               "mercado_b3", "estados_app".
    texto    — dict {"educacional": "...", "operador": "..."}. Modo Estudo
               nunca usa verbo de ordem; modo Operador fala como mesa. Nenhum
               texto promete resultado.
    veja     — lista de outros `id`s relacionados (navegação "veja também",
               mesmo padrão de `conceitos.CONCEITOS[...]["veja"]"). Todo id
               citado aqui EXISTE no catálogo — sem link morto.

Funções públicas:
    catalogo() -> list[dict]        todos os verbetes (teste de espelho e API).
    verbete(id) -> dict | None      um verbete pelo id.
    buscar(pergunta, limite) -> list[dict]   busca por pontuação, sem corte de
                                              confiança (rota pública de busca).
    formatar(verbete, modo) -> dict          verbete pronto para a API (texto
                                              só do modo pedido + `veja`).
    resolver(pergunta, modo) -> dict | None  decide se a KB cobre a pergunta
                                              com confiança suficiente para
                                              dispensar a LLM (Fase F3).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from . import conceitos, mercado_ref, skill_ref
from .technical_models import MODELS


def _normalizar(s) -> str:
    """Minúsculas, sem acento. Mesma normalização de `kpi._strip`, reescrita
    aqui para a KB não depender de uma função privada de outro módulo."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


# =============================================================================
# 1) Verbetes derivados de `conceitos.py` — REFERÊNCIA, não cópia (D4).
# =============================================================================
# `dados=None` produz a versão GENÉRICA (sem números de nenhum ativo): mesma
# lógica de `conceitos.catalogo()`. Parágrafo que citaria um campo do card
# (ex. "{entrada}") desaparece — não porque foi omitido aqui, mas porque
# `conceitos._render` já descarta parágrafo com placeholder ausente
# (Princípio 1: nunca estimar). O resultado é só a parte "de manual" do
# conceito, que é exatamente o que um verbete de glossário deve ser.
_FAMILIA_DO_CONCEITO = {
    "gatilho": "plano_risco",
    "stop": "plano_risco",
    "alvo": "plano_risco",
    "r": "plano_risco",
    "diversificacao": "plano_risco",
    "confluencia": "setups",
    "fundamento": "fundamentos",
    "barra15m": "estados_app",
}


def _de_conceito(cid: str) -> dict:
    c = conceitos.CONCEITOS[cid]
    texto = {}
    for modo in ("educacional", "operador"):
        m = conceitos.montar(cid, modo, None, resumido=False)
        partes = []
        if m:
            partes = list(m["naoAcontece"]) + list(m["oQueE"]) + list(m["oQueAcontece"])
        texto[modo] = " ".join(partes)
    termos = {cid, c["titulo"]["educacional"], c["titulo"]["operador"]}
    return {
        "id": cid,
        "termos": tuple(sorted(t for t in termos if t)),
        "familia": _FAMILIA_DO_CONCEITO[cid],
        "texto": texto,
        # Reaproveita o "veja também" que conceitos.py já mantém sem link
        # morto (todos os ids referenciados também nascem verbetes aqui).
        "veja": list(c.get("veja") or []),
    }


def _conceitos_verbetes() -> list:
    return [_de_conceito(cid) for cid in _FAMILIA_DO_CONCEITO]


# =============================================================================
# 2) Verbetes derivados de `timing.py` (via `skill_ref.TIMING`) — os ESTADOS
#    reais do app, um por um, com a MESMA frase canônica que o card mostra.
# =============================================================================
_ESTADOS_TIMING = {
    "estado-sem-plano": ("sem_plano", ("sem plano", "sem_plano", "radar sem plano",
                                       "nenhum plano operável")),
    "estado-sem-dado": ("sem_dado", ("sem dado", "sem_dado", "timing indisponível",
                                     "sem passada intraday")),
    "estado-armado": ("armado", ("armado", "plano armado", "condição armada")),
    "estado-atingido": ("gatilho", ("atingido", "gatilho atingido", "condição atingida",
                                    "condição de estudo atingida")),
    "estado-esticado": ("esticado", ("esticado", "movimento esticado",
                                     "não perseguir preço", "perseguir preço")),
}


def _de_timing(vid: str) -> dict:
    estado, termos = _ESTADOS_TIMING[vid]
    return {
        "id": vid,
        "termos": tuple(termos),
        "familia": "estados_app",
        "texto": {
            "educacional": skill_ref.timing_txt("educacional", estado),
            "operador": skill_ref.timing_txt("operador", estado),
        },
        "veja": ["barra15m", "gatilho"],
    }


def _timing_verbetes() -> list:
    return [_de_timing(vid) for vid in _ESTADOS_TIMING]


# =============================================================================
# 3) Indicadores — definição textual (a skill `analise-tecnica-b3` é a fonte
#    editorial; nenhum destes é calculado por `conceitos.py`, então não há o
#    que referenciar de lá — só `indicators.py`/`technical_models.py` para os
#    NÚMEROS que o pacote técnico já produz, citados aqui em prosa).
# =============================================================================
_INDICADORES = [
    {
        "id": "ind-rsi",
        "termos": ("rsi", "ifr", "índice de força relativa", "rsi14", "sobrecomprado",
                   "sobrevendido"),
        "texto": {
            "educacional": (
                "RSI (ou IFR, Índice de Força Relativa) não diz que o preço vai virar — "
                "ele só mede se as últimas variações foram mais de alta ou mais de baixa, "
                "numa escala de 0 a 100. Acima de 70 o app chama de 'sobrecomprado' "
                "(sequência recente puxada por alta); abaixo de 30, 'sobrevendido' "
                "(puxada por baixa). Sozinho ele não fecha leitura nenhuma: o app nunca "
                "conclui por RSI isolado, porque um ativo em tendência forte pode ficar "
                "sobrecomprado por muitas semanas sem reverter."
            ),
            "operador": (
                "RSI acima de 70 é sobrecomprado, abaixo de 30 é sobrevendido — extremo "
                "de curto prazo, não sinal isolado de reversão. Peso na leitura vem da "
                "confluência com estrutura e volume, nunca do RSI sozinho."
            ),
        },
        "veja": ["familia-momentum", "setup-ifr2"],
    },
    {
        "id": "ind-macd",
        "termos": ("macd", "linha macd", "sinal macd", "histograma macd",
                   "convergência e divergência de médias móveis"),
        "texto": {
            "educacional": (
                "MACD compara duas médias móveis exponenciais (mais rápida menos mais "
                "lenta) para medir se o movimento está acelerando ou perdendo força. Tem "
                "três partes: a linha MACD, a linha de sinal (uma média da própria linha "
                "MACD) e o histograma (a diferença entre as duas). O app usa sobretudo o "
                "histograma: positivo indica força predominante de alta; negativo, de "
                "baixa; o cruzamento entre linha e sinal marca mudança de fôlego, não uma "
                "ordem para agir."
            ),
            "operador": (
                "Histograma MACD positivo = força de alta; negativo = força de baixa. "
                "Cruzamento linha × sinal marca virada de momentum. É o sinal principal da "
                "família momentum, mas entra em confluência com estrutura e volume."
            ),
        },
        "veja": ["familia-momentum"],
    },
    {
        "id": "ind-atr",
        "termos": ("atr", "atr14", "average true range", "amplitude média real",
                   "atr14pct"),
        "texto": {
            "educacional": (
                "ATR não mede direção — mede o TAMANHO médio da movimentação do ativo "
                "em cada candle, incluindo gaps. Serve para calibrar o resto do plano: "
                "quanto maior o ATR, mais largo tende a ser um stop técnico coerente (para "
                "não ser removido por ruído normal do papel) e mais distante um alvo "
                "razoável. O app usa o ATR como referência de stop quando não há um nível "
                "de estrutura mais próximo, e como base da projeção 2×risco de vários "
                "setups."
            ),
            "operador": (
                "ATR é a régua de ruído do papel: calibra distância de stop, viabilidade de "
                "alvo e risco de ser tirado por oscilação normal. Não indica direção."
            ),
        },
        "veja": ["ind-volatilidade-historica", "familia-volatilidade"],
    },
    {
        "id": "ind-adx",
        "termos": ("adx", "adx14", "índice direcional médio", "di+", "di-", "di plus",
                   "di minus", "força de tendência"),
        "texto": {
            "educacional": (
                "ADX mede a FORÇA de uma tendência, não a direção dela — para a direção, o "
                "app olha o DI+ (pressão compradora) contra o DI- (pressão vendedora). "
                "ADX abaixo de 20 costuma indicar mercado lateral, sem tendência definida; "
                "acima de 25, tendência definida (o setup Ponto Contínuo exige esse piso "
                "para considerar a tendência confiável). ADX alto não diz se a tendência é "
                "de alta ou de baixa — só que ela existe e tem força."
            ),
            "operador": (
                "ADX ≥ 25 = tendência definida; < 20 = lateral. DI+ e DI- dão o lado. É "
                "filtro de tendência, não gatilho por si só."
            ),
        },
        "veja": ["familia-tendencia", "setup-ponto-continuo"],
    },
    {
        "id": "ind-medias-rapidas",
        "termos": ("ema9", "ema21", "mme9", "mme21", "média móvel exponencial",
                   "médias rápidas"),
        "texto": {
            "educacional": (
                "EMA9 e EMA21 são médias móveis EXPONENCIAIS de curto prazo — dão mais "
                "peso aos candles mais recentes que uma média simples, então reagem mais "
                "rápido a mudança de direção. O app compara o preço com as duas (e com a "
                "SMA50) para classificar o viés estrutural do ativo; a virada da EMA9 é o "
                "gatilho do Setup 9.1, e o espaço entre preço e EMA9/EMA21 é o que o Setup "
                "9.2/9.3 chamam de 'tendência preservada' numa correção de 1 ou 2 candles."
            ),
            "operador": (
                "EMA9/EMA21: médias curtas, reagem rápido. Preço acima das duas (e da "
                "SMA50) = viés de alta; abaixo das duas = viés de baixa. Base da família "
                "9.x (Stormer)."
            ),
        },
        "veja": ["familia-tendencia", "setup-9-1", "setup-9-2", "setup-9-3"],
    },
    {
        "id": "ind-medias-lentas",
        "termos": ("sma50", "sma200", "mma50", "mma200", "média móvel simples",
                   "médias lentas"),
        "texto": {
            "educacional": (
                "SMA50 e SMA200 são médias móveis SIMPLES de médio/longo prazo — cada "
                "candle pesa igual, então elas reagem mais devagar que as EMAs curtas e "
                "servem para descrever a tendência de fundo, não o solavanco do dia. O "
                "IFR2 exige preço acima da SMA200 como filtro: só estuda repique de "
                "sobrevenda a favor da tendência de longo prazo, nunca contra ela."
            ),
            "operador": (
                "SMA50/SMA200: tendência de fundo. Preço acima da SMA200 é o filtro do "
                "IFR2; SMA20×SMA50 dá o viés de vários setups da família 9.x/PFR/123."
            ),
        },
        "veja": ["familia-tendencia", "setup-ifr2"],
    },
    {
        "id": "ind-vwap",
        "termos": ("vwap", "preço médio ponderado por volume"),
        "texto": {
            "educacional": (
                "VWAP é o preço médio do dia, ponderado pelo volume negociado em cada "
                "faixa — não é uma média simples do preço, é uma média de ONDE o volume "
                "realmente aconteceu. Mesas usam o VWAP como referência de 'preço justo do "
                "dia': operar acima dele costuma ser lido como força compradora "
                "intradiária; abaixo, força vendedora. O app não expõe VWAP nas telas de "
                "hoje — o glossário existe para quando a pessoa encontrar o termo em outro "
                "lugar."
            ),
            "operador": (
                "VWAP: preço médio ponderado por volume do pregão, referência intradiária "
                "de preço justo. Não é um campo calculado nas telas atuais do app."
            ),
        },
        "veja": ["ind-volume-relativo"],
    },
    {
        "id": "ind-estocastico",
        "termos": ("estocástico", "estocastico", "%k", "%d", "stochastic", "stoch"),
        "texto": {
            "educacional": (
                "O estocástico compara o fechamento atual com a faixa de máxima/mínima "
                "recente, também numa escala de 0 a 100, em duas linhas (%K, mais rápida, "
                "e %D, sua média). Acima de 80 é extremo de alta; abaixo de 20, extremo de "
                "baixa. O app usa o CRUZAMENTO entre %K e %D, num extremo, como um dos "
                "critérios do setup de reversão — nunca isolado, sempre junto com o RSI e "
                "a força do candle."
            ),
            "operador": (
                "Estocástico: %K cruzando %D em extremo (>80 ou <20) é critério de "
                "reversão, sempre combinado com RSI e força do candle — nunca sozinho."
            ),
        },
        "veja": ["familia-momentum", "ind-rsi"],
    },
    {
        "id": "ind-obv",
        "termos": ("obv", "on balance volume", "volume acumulado", "obvslope21pct"),
        "texto": {
            "educacional": (
                "OBV soma o volume dos candles de alta e subtrai o volume dos candles de "
                "baixa, num total acumulado — a ideia é enxergar se o dinheiro grande está "
                "entrando ou saindo do papel, mesmo quando o preço ainda não confirmou. O "
                "app olha a INCLINAÇÃO do OBV recente (subindo, descendo ou estável) para "
                "dizer se o volume está confirmando ou negando o movimento do preço."
            ),
            "operador": (
                "OBV: volume acumulado por direção do candle. Inclinação do OBV confirma "
                "(ou nega) o movimento de preço — rompimento sem OBV a favor pesa contra a "
                "confirmação."
            ),
        },
        "veja": ["familia-volume", "ind-volume-relativo"],
    },
    {
        "id": "ind-volume-relativo",
        "termos": ("volume relativo", "volume vs média", "relativevolume"),
        "texto": {
            "educacional": (
                "Volume relativo compara o volume do candle mais recente com a média dos "
                "últimos 20 — 1,0 é 'na média'; 1,5 é '50% acima da média'. O app pede "
                "volume relativo de pelo menos 1,5× para considerar um rompimento "
                "confirmado (setup 'Rompimento com volume'): sem esse reforço, o movimento "
                "conta como não confirmado, e o Princípio 5 da metodologia trata "
                "rompimento sem volume como leitura mais fraca."
            ),
            "operador": (
                "Volume relativo ≥ 1,5× a média de 20 candles confirma rompimento. Abaixo "
                "disso, o app não conta o rompimento como confirmado por volume."
            ),
        },
        "veja": ["familia-volume", "estr-rompimento"],
    },
    {
        "id": "ind-volatilidade-historica",
        "termos": ("volatilidade histórica", "hv", "hv21", "hv63",
                   "desvio padrão dos retornos"),
        "texto": {
            "educacional": (
                "Volatilidade histórica mede o quanto o preço OSCILOU no passado recente, "
                "em termos estatísticos (o desvio padrão dos retornos diários, anualizado "
                "em percentual) — não prevê o quanto vai oscilar amanhã, só descreve o "
                "regime recente. O app calcula em duas janelas (21 e 63 candles) para "
                "notar se a volatilidade está subindo ou caindo, junto com o ATR% e a "
                "largura das Bandas de Bollinger."
            ),
            "operador": (
                "HV21/HV63: desvio padrão anualizado dos retornos, duas janelas. Descreve "
                "regime de volatilidade — não é previsão."
            ),
        },
        "veja": ["ind-atr", "familia-volatilidade"],
    },
]


# =============================================================================
# 4) Estrutura de preço.
# =============================================================================
_ESTRUTURA = [
    {
        "id": "estr-topo-fundo",
        "termos": ("topo", "fundo", "topos e fundos", "máxima local", "mínima local",
                   "swing high", "swing low"),
        "texto": {
            "educacional": (
                "Topo é uma máxima local: um candle mais alto que os vizinhos dos dois "
                "lados, seguido de recuo. Fundo é o espelho — uma mínima local seguida de "
                "recuperação. São a base geométrica da leitura de estrutura: séries de "
                "fundos cada vez mais altos descrevem tendência de alta; topos cada vez "
                "mais baixos, tendência de baixa. O setup 123 usa exatamente essa "
                "sequência (fundo, topo, fundo mais alto) como padrão objetivo."
            ),
            "operador": (
                "Topo/fundo: extremo local cercado por candles menores/maiores nos dois "
                "lados. Sequência de fundos ascendentes = estrutura de alta; de topos "
                "descendentes = estrutura de baixa."
            ),
        },
        "veja": ["estr-pivo", "setup-123"],
    },
    {
        "id": "estr-suporte",
        "termos": ("suporte", "suportes", "nearestsupport"),
        "texto": {
            "educacional": (
                "Suporte é uma faixa de preço onde, no histórico recente, apareceu "
                "demanda suficiente para deter quedas — o app monta essa faixa agrupando "
                "as mínimas recentes que ficam abaixo do preço atual. Não é uma garantia "
                "de que o preço vai parar ali de novo: é só o nível onde parou antes, e "
                "por isso o app usa o suporte mais próximo como referência de stop quando "
                "não há um cálculo por ATR mais estreito."
            ),
            "operador": (
                "Suporte: agrupamento das mínimas recentes abaixo do preço atual. "
                "Referência de stop quando mais próximo que o ATR."
            ),
        },
        "veja": ["estr-resistencia", "stop"],
    },
    {
        "id": "estr-resistencia",
        "termos": ("resistência", "resistencia", "resistências", "nearestresistance"),
        "texto": {
            "educacional": (
                "Resistência é o espelho do suporte: uma faixa onde apareceu oferta "
                "suficiente para conter avanços, montada a partir das máximas recentes "
                "acima do preço atual. O app usa a resistência mais próxima como "
                "referência de alvo quando não há um cálculo por ATR mais distante."
            ),
            "operador": (
                "Resistência: agrupamento das máximas recentes acima do preço atual. "
                "Referência de alvo quando mais próxima que a projeção por ATR."
            ),
        },
        "veja": ["estr-suporte", "alvo"],
    },
    {
        "id": "estr-congestao",
        "termos": ("congestão", "congestao", "lateralização", "consolidação"),
        "texto": {
            "educacional": (
                "Congestão é a fase em que o preço fica preso entre um suporte e uma "
                "resistência próximos, sem tendência definida — candles pequenos, sem "
                "direção clara. Costuma ser o terreno onde o setup de Compressão de "
                "volatilidade aparece (largura das Bandas de Bollinger no menor quartil do "
                "período): não indica para qual lado vai o próximo movimento, só que a "
                "faixa está estreita."
            ),
            "operador": (
                "Congestão: preço preso entre suporte e resistência próximos, sem "
                "direção. Contexto, não sinal — o lado só se define no rompimento."
            ),
        },
        "veja": ["estr-rompimento", "familia-volatilidade"],
    },
    {
        "id": "estr-rompimento",
        "termos": ("rompimento", "breakout"),
        "texto": {
            "educacional": (
                "Rompimento é o fechamento de uma vela além de um nível de referência — "
                "um suporte, uma resistência, ou o extremo de um período. O app só conta "
                "rompimento por vela FECHADA, nunca por um toque dentro da vela: preço que "
                "encosta no nível e volta atrás na mesma vela é ruído, não rompimento. "
                "Ganha força quando confirmado por volume acima de 1,5× a média."
            ),
            "operador": (
                "Rompimento: fechamento de vela além do nível — nunca por toque "
                "intracandle. Confirmação exige volume ≥ 1,5× a média de 20."
            ),
        },
        "veja": ["estr-falso-rompimento", "estr-reteste", "ind-volume-relativo"],
    },
    {
        "id": "estr-reteste",
        "termos": ("reteste", "retest"),
        "texto": {
            "educacional": (
                "Reteste é quando o preço volta ao nível recém-rompido, do lado de fora, "
                "antes de retomar a direção do rompimento — funciona como uma segunda "
                "confirmação de que o nível trocou de papel (uma resistência rompida vira "
                "suporte, e vice-versa). O app não tem um setup dedicado ao reteste hoje; "
                "o termo existe no glossário porque aparece na leitura de estrutura de "
                "vários setups (123, Ponto Contínuo)."
            ),
            "operador": (
                "Reteste: volta ao nível rompido, do lado de fora, antes de retomar a "
                "direção. Confirma a troca de papel do nível (resistência ↔ suporte)."
            ),
        },
        "veja": ["estr-rompimento", "estr-falso-rompimento"],
    },
    {
        "id": "estr-falso-rompimento",
        "termos": ("falso rompimento", "fakeout", "rompimento falso"),
        "texto": {
            "educacional": (
                "Falso rompimento é um fechamento além do nível que não se sustenta: o "
                "preço volta para dentro da faixa em poucas velas, sem confirmar a direção "
                "que prometia. É o motivo pelo qual o app exige VELA FECHADA (nunca um "
                "toque) para validar rompimento e gatilho — e por que volume baixo no "
                "rompimento é tratado como sinal mais fraco, não como confirmação."
            ),
            "operador": (
                "Falso rompimento: fechamento além do nível que reverte em poucas velas. "
                "Vela fechada + volume são os dois filtros que reduzem esse risco."
            ),
        },
        "veja": ["estr-rompimento", "barra15m"],
    },
    {
        "id": "estr-gap",
        "termos": ("gap", "gap de alta", "gap de baixa", "abertura em gap"),
        "texto": {
            "educacional": (
                "Gap é a diferença entre o fechamento de uma vela e a abertura da vela "
                "seguinte, sem negociação registrada nesse intervalo — comum na abertura "
                "do pregão, após uma notícia ou resultado. Pode indicar força "
                "(gap de continuação, a favor da tendência) ou exaustão de um movimento "
                "(gap de esgotamento, no fim de uma sequência longa); o contexto em que "
                "aparece pesa mais que o gap isolado."
            ),
            "operador": (
                "Gap: salto entre fechamento e abertura seguinte, sem negociação no meio. "
                "Continuação ou exaustão depende do contexto — nunca lido isolado."
            ),
        },
        "veja": ["familia-price-action"],
    },
    {
        "id": "estr-pivo",
        "termos": ("pivô", "pivo", "pivôs", "ponto de pivô"),
        "texto": {
            "educacional": (
                "Pivô é um ponto de inflexão objetivo da série: um candle cuja máxima (ou "
                "mínima) é maior (ou menor) que a dos candles vizinhos dos dois lados — a "
                "mesma definição de topo/fundo, só que usada como peça de construção de "
                "estrutura. O setup 123 encadeia três pivôs (fundo, topo, fundo mais alto, "
                "ou o espelho) para montar o padrão."
            ),
            "operador": (
                "Pivô: máxima ou mínima cercada por candles menores/maiores dos dois "
                "lados. Peça de construção do setup 123."
            ),
        },
        "veja": ["estr-topo-fundo", "setup-123"],
    },
]


# =============================================================================
# 5) As 5 famílias de `technical_models._families`.
# =============================================================================
_FAMILIAS = [
    {
        "id": "familia-tendencia",
        "termos": ("família tendência", "tendencia", "viés estrutural"),
        "texto": {
            "educacional": (
                "A família Tendência lê o preço contra as médias (EMA9, EMA21, SMA50) "
                "para definir o viés estrutural — alta, baixa ou neutro — e usa o ADX para "
                "medir a FORÇA dessa tendência, separado da direção. É uma das 4 famílias "
                "'direcionais' que entram na confluência entre famílias do pacote técnico."
            ),
            "operador": (
                "Tendência: preço × médias define o viés; ADX mede a força. Uma das 4 "
                "famílias direcionais da confluência."
            ),
        },
        "veja": ["ind-medias-rapidas", "ind-medias-lentas", "ind-adx"],
    },
    {
        "id": "familia-momentum",
        "termos": ("família momentum", "momentum"),
        "texto": {
            "educacional": (
                "A família Momentum usa o histograma do MACD como sinal principal (positivo "
                "= força de alta, negativo = força de baixa) e o RSI/estocástico para "
                "marcar extremos e divergências. É uma das 4 famílias direcionais da "
                "confluência entre famílias."
            ),
            "operador": (
                "Momentum: histograma MACD é o sinal principal; RSI/estocástico marcam "
                "extremo e divergência. Uma das 4 famílias direcionais."
            ),
        },
        "veja": ["ind-macd", "ind-rsi", "ind-estocastico"],
    },
    {
        "id": "familia-price-action",
        "termos": ("família price action", "price action", "leitura de candles"),
        "texto": {
            "educacional": (
                "A família Price Action lê os padrões de candle da janela recente (doji, "
                "martelo, estrela cadente, engolfo) e a posição do preço frente aos níveis "
                "de suporte/resistência — o CONTEXTO em que um padrão aparece pesa mais do "
                "que o padrão isolado. É uma das 4 famílias direcionais da confluência."
            ),
            "operador": (
                "Price action: padrões de candle + posição frente a níveis. Contexto pesa "
                "mais que o padrão isolado. Uma das 4 famílias direcionais."
            ),
        },
        "veja": ["estr-gap", "estr-suporte", "estr-resistencia"],
    },
    {
        "id": "familia-volume",
        "termos": ("família volume", "volume"),
        "texto": {
            "educacional": (
                "A família Volume usa o OBV e o volume relativo para CONFIRMAR ou NEGAR o "
                "movimento de preço — rompimento sem volume não se confirma. É uma das 4 "
                "famílias direcionais da confluência entre famílias."
            ),
            "operador": (
                "Volume: OBV + volume relativo confirmam ou negam o preço. Uma das 4 "
                "famílias direcionais."
            ),
        },
        "veja": ["ind-obv", "ind-volume-relativo"],
    },
    {
        "id": "familia-volatilidade",
        "termos": ("família volatilidade", "volatilidade"),
        "texto": {
            "educacional": (
                "A família Volatilidade usa o ATR% e a largura das Bandas de Bollinger "
                "para descrever o REGIME do ativo — compressão, normal ou expansão — e "
                "calibrar stop e ruído esperado. Ao contrário das outras 4, ela NÃO entra "
                "na contagem de famílias direcionais: volatilidade mede intensidade, não "
                "diz se o próximo movimento é de alta ou de baixa."
            ),
            "operador": (
                "Volatilidade: ATR% + largura de banda dão o regime (compressão × "
                "expansão). Calibra stop e ruído — não conta como família direcional."
            ),
        },
        "veja": ["ind-atr", "ind-volatilidade-historica"],
    },
]


# =============================================================================
# 6) Os 9 modelos de `technical_models.MODELS` — id = "modelo-<chave>" (é o
#    critério que o teste de espelho usa: chave nova em MODELS sem
#    "modelo-<chave>" aqui falha o teste).
# =============================================================================
_MODELOS_EXTRA = {
    "completo": (
        "Combina as sete leituras — tendência, price action, momentum, volume, "
        "volatilidade, suportes/resistências e (quando disponível) opções — sem "
        "recortar nenhuma. É o modelo padrão do Radar.",
        "Usa todos os blocos do pacote técnico. Nada fica de fora por escolha do "
        "modelo; o recorte é só o que os DADOS não têm.",
    ),
    "tendencia": (
        "Olha médias móveis e a estrutura de topos/fundos para a direção "
        "predominante; ignora o detalhe de candle a candle e o volume como foco "
        "central — eles entram só como apoio.",
        "Direção predominante via médias + estrutura de topos/fundos. Detalhe de "
        "candle e volume ficam de apoio, não de foco.",
    ),
    "price_action": (
        "Olha candles, amplitude, fechamentos, suportes, resistências e rejeições; "
        "ignora indicadores derivados (RSI, MACD) como centro da leitura — eles não "
        "desaparecem do pacote, só não guiam a conclusão deste modelo.",
        "Leitura pelo preço puro: candle, amplitude, níveis. Indicadores derivados "
        "ficam de fora do centro da leitura.",
    ),
    "momentum": (
        "Olha RSI, MACD, estocástico e a aceleração do movimento; ignora a "
        "estrutura de preço bruta como critério principal.",
        "RSI, MACD, estocástico e aceleração. Estrutura de preço não é o critério "
        "principal aqui.",
    ),
    "volume": (
        "Olha volume relativo, OBV e a confirmação (ou não) do movimento de preço "
        "pelo volume; ignora a direção do preço isolada — só confirma ou nega o "
        "que o preço já indicou.",
        "Volume relativo + OBV. Confirma ou nega o movimento — não aponta direção "
        "sozinho.",
    ),
    "volatilidade": (
        "Olha ATR, volatilidade histórica e o regime de amplitude; ignora direção "
        "por definição — volatilidade mede intensidade do movimento, não o lado "
        "dele.",
        "ATR, HV, regime de amplitude. Nunca indica direção, só intensidade.",
    ),
    "suporte_resistencia": (
        "Olha os níveis recentes de suporte/resistência, a distância do preço até "
        "eles e os pontos de invalidação; ignora indicadores de momentum como "
        "critério de entrada.",
        "Níveis, distância e invalidação. Momentum não é critério de entrada "
        "aqui.",
    ),
    "swing_trade": (
        "Olha a leitura de alguns dias/semanas, com stop referenciado em ATR e "
        "níveis técnicos; ignora o ruído intradiário — não é o modelo para leitura "
        "de minuto a minuto.",
        "Dias/semanas, stop por ATR + níveis técnicos. Ignora ruído intradiário.",
    ),
    "opcoes": (
        "Olha o ativo-objeto e a disponibilidade da cadeia de opções na fonte de "
        "dados; ignora prêmio e gregas quando a fonte não os fornece — declara a "
        "ausência em vez de estimar (Princípio 1).",
        "Ativo-objeto + disponibilidade de cadeia. Prêmio/gregas ausentes são "
        "declarados, nunca estimados.",
    ),
}


def _modelo_verbete(chave: str) -> dict:
    m = MODELS[chave]
    edu, ope = _MODELOS_EXTRA[chave]
    return {
        "id": "modelo-" + chave,
        "termos": (chave, m["label"], "modelo " + m["label"].lower()),
        "familia": "modelos",
        "texto": {
            "educacional": (m["description"] + " " + edu).strip(),
            "operador": (m["description"] + " " + ope).strip(),
        },
        "veja": [],
    }


def _modelos_verbetes() -> list:
    # Só gera verbete para chave com entrada CURADA em `_MODELOS_EXTRA` — de
    # propósito, sem fallback genérico. Se `technical_models.MODELS` ganhar
    # uma chave nova sem alguém escrever o par (educacional, operador) aqui,
    # o verbete simplesmente não nasce, e `test_kb_espelho.py` denuncia a
    # lacuna (verificado manualmente ao escrever esta fase: uma chave fake
    # em MODELS sem entrada em `_MODELOS_EXTRA` faz o teste falhar).
    return [_modelo_verbete(chave) for chave in MODELS if chave in _MODELOS_EXTRA]


# =============================================================================
# 7) Os 9 setups de `setups.py`. `termos` inclui o NOME BASE literal (sem o
#    %s de lado/direção) que `_mk(...)` produz — é o que o teste de espelho
#    casa contra `setups.py` (ver test_kb_espelho.py).
# =============================================================================
_SETUPS = [
    {
        "id": "setup-9-1",
        "termos": ("Setup 9.1", "setup 9.1", "9.1", "virada da mme9"),
        "texto": {
            "educacional": (
                "Setup 9.1 (Stormer) estuda a VIRADA da média móvel de 9 períodos: os "
                "últimos três valores da EMA9 mudam de direção e o fechamento fica do "
                "lado novo. O gatilho de estudo é a máxima (ou mínima, na venda) da vela "
                "da virada; a invalidação é o extremo oposto da MESMA vela — se o preço "
                "voltar até lá, a virada não se sustentou."
            ),
            "operador": (
                "Setup 9.1: virada da EMA9 (3 valores) + fechamento do lado da virada. "
                "Gatilho no extremo da vela da virada; invalidação no extremo oposto da "
                "mesma vela; volume ≥ média de 20 reforça."
            ),
        },
        "veja": ["ind-medias-rapidas", "gatilho", "stop"],
    },
    {
        "id": "setup-9-2",
        "termos": ("Setup 9.2", "setup 9.2", "9.2", "correção de 1 candle"),
        "texto": {
            "educacional": (
                "Setup 9.2 (Stormer) estuda uma correção de UM candle dentro de uma "
                "tendência que a EMA9 ainda sustenta: a média continua subindo (ou "
                "caindo, na venda) e só o candle mais recente fechou contra ela. Gatilho e "
                "invalidação ficam nos extremos desse mesmo candle de correção."
            ),
            "operador": (
                "Setup 9.2: EMA9 a favor + 1 candle de correção contra a direção. Gatilho "
                "e invalidação nos extremos do candle de correção."
            ),
        },
        "veja": ["setup-9-1", "setup-9-3"],
    },
    {
        "id": "setup-9-3",
        "termos": ("Setup 9.3", "setup 9.3", "9.3", "retomada após correção"),
        "texto": {
            "educacional": (
                "Setup 9.3 (Stormer) estuda a RETOMADA depois de uma correção: a EMA9 "
                "segue a favor, houve correção no candle anterior e o candle mais recente "
                "já fechou de volta na direção da tendência. A invalidação fica na mínima "
                "(ou máxima) dos dois últimos candles — o ponto que a correção não devia "
                "ter passado."
            ),
            "operador": (
                "Setup 9.3: EMA9 a favor + correção no candle anterior + retomada no "
                "candle atual. Invalidação na mínima/máxima dos 2 últimos candles."
            ),
        },
        "veja": ["setup-9-1", "setup-9-2"],
    },
    {
        "id": "setup-ifr2",
        "termos": ("IFR2", "ifr2", "rsi2", "rsi(2)", "larry connors", "reversão à média"),
        "texto": {
            "educacional": (
                "O princípio geral por trás deste setup é a reversão à média: depois de "
                "um movimento extremo de curtíssimo prazo, o preço tende a voltar em "
                "direção à sua média — é tendência estatística, nunca certeza. "
                "IFR2 (Larry Connors) mede esse exagero pelo RSI de 2 períodos em 25 ou "
                "menos (extremo em 10 ou menos reforça), "
                "com o preço acima da SMA200 como filtro — a média de longo prazo mantém "
                "a leitura a favor da tendência, nunca contra ela. É um setup de FECHAMENTO, não de "
                "rompimento: a condição já vale no próprio fechamento, sem esperar romper "
                "nível nenhum. A saída didática é a máxima dos dois candles anteriores; "
                "como o método original não usa stop, a invalidação aqui é uma referência "
                "por ATR, não um nível de estrutura."
            ),
            "operador": (
                "IFR2: RSI(2) ≤ 25 + preço > SMA200. Setup de fechamento, sem rompimento. "
                "Saída na máxima dos 2 candles anteriores; invalidação por ATR (Connors "
                "não usa stop clássico)."
            ),
        },
        "veja": ["ind-rsi", "ind-medias-lentas"],
    },
    {
        "id": "setup-pfr",
        "termos": ("PFR", "pfr"),
        "texto": {
            "educacional": (
                "PFR (Stormer) estuda uma mínima mais baixa que as duas anteriores, "
                "seguida de fechamento ACIMA do fechamento anterior — força e reversão no "
                "mesmo candle (o espelho, na venda, usa máxima mais alta e fechamento "
                "abaixo). Gatilho e invalidação ficam nos extremos desse candle."
            ),
            "operador": (
                "PFR: mínima mais baixa que as 2 anteriores + fechamento acima do "
                "anterior (espelho na venda). Gatilho/invalidação nos extremos do candle."
            ),
        },
        "veja": ["estr-topo-fundo"],
    },
    {
        "id": "setup-123",
        "termos": ("123", "123 de fundo", "123 de topo", "um dois três"),
        "texto": {
            "educacional": (
                "123 (clássico) estuda a estrutura de três pivôs: fundo (1), topo (2), "
                "fundo mais alto (3) — na compra; o espelho (topo, fundo, topo mais baixo) "
                "na venda. O gatilho de estudo é o rompimento do ponto 2; a invalidação é "
                "o ponto 3, que a tese não pode romper na direção contrária."
            ),
            "operador": (
                "123: fundo(1)-topo(2)-fundo mais alto(3), gatilho no rompimento do ponto "
                "2, invalidação no ponto 3. Espelho no topo para o lado vendedor."
            ),
        },
        "veja": ["estr-pivo", "estr-topo-fundo"],
    },
    {
        "id": "setup-ponto-continuo",
        "termos": ("Ponto Contínuo", "ponto continuo", "dunnigan"),
        "texto": {
            "educacional": (
                "Ponto Contínuo (Dunnigan) estuda a correção até a EMA21 dentro de uma "
                "tendência definida: ADX de 25 ou mais, DI dominante na direção do "
                "estudo, e o preço tocando (ou chegando a 1% de) a EMA21. Gatilho e "
                "invalidação ficam nos extremos do candle do toque."
            ),
            "operador": (
                "Ponto Contínuo: ADX ≥ 25 + DI dominante + preço na EMA21 (toque ou ±1%). "
                "Gatilho/invalidação nos extremos do candle do toque."
            ),
        },
        "veja": ["ind-adx", "ind-medias-rapidas"],
    },
    {
        "id": "setup-inside-bar",
        "termos": ("Inside Bar", "inside bar", "candle contido"),
        "texto": {
            "educacional": (
                "Inside Bar estuda um candle inteiramente contido no anterior (máxima e "
                "mínima dentro da faixa do candle-mãe) — compressão que costuma anteceder "
                "o próximo impulso. Só conta com uma tendência definida (SMA20 × SMA50) "
                "dando o lado do estudo; gatilho e invalidação ficam nos extremos do "
                "candle-MÃE, não do inside bar."
            ),
            "operador": (
                "Inside Bar: candle contido no anterior + tendência definida dando o "
                "lado. Gatilho/invalidação nos extremos do candle-mãe."
            ),
        },
        "veja": ["estr-congestao"],
    },
    {
        "id": "setup-9-4-larry-williams",
        "termos": ("Máx/Mín de Larry Williams — 9.4", "Máx/Mín de Larry Williams (9.4)",
                   "9.4", "larry williams", "máximas e mínimas de larry williams"),
        "texto": {
            "educacional": (
                "9.4 (Máximas e Mínimas de Larry Williams) estuda, dentro de uma correção "
                "em tendência, o candle que fez a mínima mais baixa dos últimos candles "
                "(ou a máxima mais alta, na venda) e espera o rompimento do extremo "
                "OPOSTO desse mesmo candle como gatilho. A invalidação é o extremo que "
                "definiu a referência — se o preço passar por ele antes de romper o "
                "gatilho, a leitura para."
            ),
            "operador": (
                "9.4 (Larry Williams): candle de referência = mínima mais baixa da "
                "correção; gatilho no rompimento do extremo oposto dele; invalidação no "
                "extremo que definiu a referência."
            ),
        },
        "veja": ["estr-topo-fundo"],
    },
]


# =============================================================================
# 8) Plano e risco — números canônicos de `skill_ref.py`/`setups.py`.
# =============================================================================
_PLANO_RISCO_EXTRA = [
    {
        "id": "risco-rr",
        "termos": ("r:r", "rr", "relação risco retorno", "risco retorno",
                   "risco:retorno"),
        "texto": {
            "educacional": (
                "R:R compara o que se arrisca (distância até o stop) com o que se "
                "projeta ganhar (distância até o alvo), na mesma régua de R. Abaixo de "
                + skill_ref.RR_MIN_TXT + ":1 o app trata o plano como não operável — "
                "arriscar 1 para ganhar menos que isso não compensa nem quando a leitura "
                "está certa. O ideal declarado é " + skill_ref.RR_IDEAL_TXT + ":1 ou mais."
            ),
            "operador": (
                "R:R mínimo " + skill_ref.RR_MIN_TXT + ":1; abaixo disso, NÃO OPERAR. "
                "Ideal ≥ " + skill_ref.RR_IDEAL_TXT + ":1."
            ),
        },
        "veja": ["r", "stop", "alvo"],
    },
    {
        "id": "risco-dimensionamento",
        "termos": ("dimensionamento", "tamanho da posição", "quantas ações",
                   "sizing"),
        "texto": {
            "educacional": (
                "Dimensionar é decidir QUANTAS ações cabem numa operação a partir do "
                "risco por ação (1R) e do limite de perda que a pessoa aceita correr — "
                "nunca o contrário, de escolher o tamanho e só depois olhar o risco. O "
                "app calcula o risco por ação de cada plano; quantas ações entram é "
                "decisão de quem opera, na corretora dele — o resultado do Radar é "
                "compartilhado entre usuários, e o capital de cada pessoa não faz parte "
                "desse cálculo do servidor."
            ),
            "operador": (
                "Sizing = risco por ação (1R) ÷ limite de perda aceito. Fica no cliente: "
                "o Radar é compartilhado e não carrega capital de ninguém."
            ),
        },
        "veja": ["r", "stop"],
    },
    {
        "id": "risco-invalidacao",
        "termos": ("invalidação", "invalidacao", "o que invalida a tese"),
        "texto": {
            "educacional": (
                "Invalidação é o nível ou condição que, se ocorrer, diz que a ideia por "
                "trás da entrada deixou de fazer sentido — na prática, é o mesmo preço do "
                "stop técnico, só que descrito pelo MOTIVO em vez do número. Todo plano do "
                "app declara essa condição antes de qualquer entrada; sem ela, não há "
                "plano executável, e o app trata como 'não operar' em vez de inventar um "
                "nível."
            ),
            "operador": (
                "Invalidação = a condição/nível que derruba a tese, sempre declarada "
                "antes da entrada. Mesmo preço do stop, framing pelo motivo."
            ),
        },
        "veja": ["stop", "gatilho"],
    },
]


# =============================================================================
# 9) Fundamentos — thresholds canônicos de `skill_ref.FUND_*`.
# =============================================================================
_FUNDAMENTOS_EXTRA = [
    {
        "id": "fund-pl",
        "termos": ("p/l", "pl", "preço sobre lucro", "preço/lucro", "valuation"),
        "texto": {
            "educacional": (
                "P/L (preço sobre lucro) compara o preço da ação com o lucro que a "
                "empresa gera por ação — quanto tempo, em anos de lucro atual, o mercado "
                "está cobrando pelo papel. No pilar de valuation do fundamento, o app "
                "considera saudável um P/L entre 0 e " + str(int(skill_ref.FUND_PL_MAX))
                + "; fora dessa faixa (negativo ou muito alto) o pilar não pontua. A "
                "comparação certa é dentro do SETOR: bancos e empresas de tecnologia têm "
                "faixas normais de P/L bem diferentes."
            ),
            "operador": (
                "P/L: valuation. Pontua entre 0 e " + str(int(skill_ref.FUND_PL_MAX))
                + "; fora da faixa, não pontua. Comparação dentro do setor."
            ),
        },
        "veja": ["fundamento"],
    },
    {
        "id": "fund-roe",
        "termos": ("roe", "rentabilidade", "retorno sobre patrimônio",
                   "retorno sobre o patrimônio líquido"),
        "texto": {
            "educacional": (
                "ROE (retorno sobre patrimônio) mede quanto lucro a empresa gera para "
                "cada real de patrimônio líquido dos acionistas — é a nota de "
                "rentabilidade do negócio, não do preço da ação. No pilar de "
                "rentabilidade do fundamento, o app exige ROE de pelo menos "
                + str(int(skill_ref.FUND_ROE_MIN * 100))
                + "% E margem líquida positiva juntos: só o ROE alto, sem lucro real, não "
                "pontua sozinho."
            ),
            "operador": (
                "ROE ≥ " + str(int(skill_ref.FUND_ROE_MIN * 100))
                + "% E margem líquida > 0 para pontuar o pilar de rentabilidade."
            ),
        },
        "veja": ["fundamento"],
    },
    {
        "id": "fund-divida-ebitda",
        "termos": ("dívida/ebitda", "divida ebitda", "alavancagem", "endividamento"),
        "texto": {
            "educacional": (
                "Dívida líquida sobre EBITDA mede quantos anos de geração de caixa "
                "operacional a empresa levaria para quitar sua dívida líquida — quanto "
                "menor, mais sólida a estrutura de capital. No pilar de solidez do "
                "fundamento, o app considera saudável até "
                + str(skill_ref.FUND_DIVIDA_EBITDA_MAX)
                + "× o EBITDA; em bancos e financeiras a métrica não entra (o passivo "
                "delas é matéria-prima do negócio, não dívida no sentido usual)."
            ),
            "operador": (
                "Dívida líquida/EBITDA ≤ " + str(skill_ref.FUND_DIVIDA_EBITDA_MAX)
                + "× pontua o pilar de solidez. Financeiras: pilar neutro, sem dado."
            ),
        },
        "veja": ["fundamento"],
    },
]


# =============================================================================
# 10) Mercado B3 — vocabulário geral (glossário, não campo calculado).
# =============================================================================
_MERCADO_B3 = [
    {
        "id": "mkt-ticker",
        "termos": ("ticker", "código de negociação", "código do ativo"),
        "texto": {
            "educacional": (
                "Ticker é o código de negociação do papel na B3 — a chave que o app usa "
                "para buscar cotação e candles. O número final costuma indicar o tipo de "
                "ação: '3' geralmente é ordinária (ON, com direito a voto), '4' "
                "preferencial (PN); '11' aparece em units, ETFs e alguns fundos."
            ),
            "operador": (
                "Ticker: código B3 do papel. Sufixo numérico indica o tipo (3=ON, "
                "4=PN, 11=unit/ETF/fundo, entre outros)."
            ),
        },
        "veja": ["mkt-lote"],
    },
    {
        "id": "mkt-lote",
        "termos": ("lote", "lote padrão", "mercado fracionário"),
        "texto": {
            "educacional": (
                "Lote-padrão é a quantidade de referência para negociar um ativo na B3 — "
                "hoje, 100 ações. Quantidades menores que o lote-padrão negociam no "
                "mercado FRACIONÁRIO (o ticker ganha o sufixo 'F', ex. PETR4F), com preço "
                "e liquidez próprios, geralmente um pouco piores que o lote-padrão."
            ),
            "operador": (
                "Lote-padrão B3: 100 ações. Abaixo disso, mercado fracionário (sufixo F), "
                "com liquidez própria."
            ),
        },
        "veja": ["mkt-liquidez"],
    },
    {
        "id": "mkt-pregao",
        "termos": ("pregão", "pregao", "horário de negociação", "mercado aberto",
                   "mercado fechado"),
        "texto": {
            "educacional": (
                "Pregão é o período em que a B3 está aberta para negociação. Fora dele "
                "(à noite, fim de semana, feriado) não nasce candle novo, e o app trata "
                "isso como o normal do horário — não como uma falha do feed."
            ),
            "operador": (
                "Pregão: janela de negociação da B3. Fora dele, sem candle novo por "
                "definição — não é falha de feed."
            ),
        },
        "veja": ["estado-sem-dado", "barra15m"],
    },
    {
        "id": "mkt-liquidez",
        "termos": ("liquidez", "baixa liquidez", "volume financeiro"),
        "texto": {
            "educacional": (
                "Liquidez é o quanto um ativo negocia por dia — em quantidade de negócios "
                "e em volume financeiro. Papel de baixa liquidez tem o preço mais fácil de "
                "mover com pouca ordem e a execução mais incerta (o preço que aparece na "
                "tela pode não ser o preço que se consegue de fato); é um dos motivos que "
                "levam o app a declarar dado insuficiente em vez de forçar uma leitura."
            ),
            "operador": (
                "Liquidez: negócios/dia e volume financeiro. Baixa liquidez = spread "
                "maior e execução mais incerta."
            ),
        },
        "veja": ["mkt-lote"],
    },
    {
        "id": "mkt-etf",
        "termos": ("etf", "fundo de índice"),
        "texto": {
            "educacional": (
                "ETF é um fundo de índice negociado em bolsa como se fosse uma ação — "
                "comprando uma cota, a pessoa ganha exposição a uma cesta inteira de "
                "ativos numa única ordem (ex.: BOVA11 replica o Ibovespa). O app lê o "
                "candle do ETF do mesmo jeito que o de uma ação; a diferença fica na "
                "composição por trás do papel, que o app não decompõe."
            ),
            "operador": (
                "ETF: fundo de índice, negociado como ação. Exposição a uma cesta numa "
                "ordem só."
            ),
        },
        "veja": ["mkt-ticker"],
    },
    {
        "id": "mkt-opcao",
        "termos": ("opção", "opcao", "opções", "série", "strike", "vencimento",
                   "call", "put"),
        "texto": {
            "educacional": (
                "Opção é um contrato que dá o DIREITO (não a obrigação) de comprar (call) "
                "ou vender (put) um ativo-objeto a um preço combinado (strike) até uma "
                "data (vencimento) — a série é o código que identifica esse tipo+strike+"
                "vencimento. O modelo 'Opções' do app hoje registra se a cadeia de opções "
                "do ativo-objeto está disponível na fonte de dados; não calcula prêmio nem "
                "gregas — quando a fonte não traz esse dado, o app declara a ausência em "
                "vez de estimar."
            ),
            "operador": (
                "Opção: direito de comprar (call)/vender (put) a um strike até o "
                "vencimento; série identifica o contrato. O app checa disponibilidade da "
                "cadeia, não calcula prêmio/gregas."
            ),
        },
        "veja": ["modelo-opcoes"],
    },
    {
        "id": "mkt-carteira-simulada",
        "termos": ("carteira simulada", "carteira", "dinheiro simulado", "posição",
                   "posições"),
        "texto": {
            "educacional": (
                "A carteira do app é SIMULADA: registra posições, preço médio e "
                "resultado de um plano hipotético para efeito de estudo, sem ligação "
                "nenhuma com corretora — nenhuma ordem sai daqui para o mercado real. "
                "Serve para a pessoa acompanhar o que teria acontecido seguindo (ou não) "
                "o plano, com dinheiro que não existe."
            ),
            "operador": (
                "Carteira simulada: posições e resultado hipotéticos. Nenhuma execução "
                "real; nenhuma ordem sai do app."
            ),
        },
        "veja": [],
    },
    {
        "id": "mkt-tipos-ordem",
        "termos": ("tipos de ordem", "ordem limitada", "ordem a mercado",
                   "ordem stop", "como enviar uma ordem"),
        "texto": {
            "educacional": (
                "A B3 (sistema PUMA) reconhece " + str(len(mercado_ref.TIPOS_ORDEM_OFICIAIS))
                + " tipos de ordem; os dois que aparecem mais na rotina de quem está "
                "começando são a ORDEM LIMITADA (define um preço máximo de compra ou "
                "mínimo de venda — só executa nesse preço ou melhor, mas pode não "
                "executar se o mercado não chegar lá) e a ORDEM A MERCADO (executa "
                "imediatamente pelo melhor preço disponível no momento, sem garantia "
                "de qual será esse preço). Existe também a ORDEM STOP, que fica "
                "inativa até o preço tocar um gatilho definido — aí vira ordem "
                "limitada ou a mercado, dependendo do tipo. O simulador do app não "
                "manda ordem nenhuma para a B3; a carteira é hipotética."
            ),
            "operador": (
                "Tipos de ordem B3 (PUMA): Limitada (preço-teto/piso, pode não "
                "executar), A Mercado (executa já, preço não garantido), Stop "
                "(inativa até tocar gatilho, daí vira limitada/mercado). Outros "
                "tipos oficiais: A Mercado com Proteção, Stop com Proteção, Direta, "
                "RLP. Carteira do app é simulada — nenhuma ordem sai daqui."
            ),
        },
        "veja": ["mkt-carteira-simulada"],
    },
    {
        "id": "mkt-day-trade-swing",
        "termos": ("day trade", "swing trade", "diferença entre day trade e swing",
                   "operar no mesmo dia"),
        "texto": {
            "educacional": (
                "A diferença entre day trade e swing trade é só o TEMPO entre compra "
                "e venda. Day trade é comprar e vender o MESMO ativo no MESMO dia — "
                "zera a posição antes do pregão fechar. Swing trade é manter a "
                "posição de um dia para o outro, por qualquer período. Essa distinção "
                "importa além da estratégia: a Receita Federal tributa os dois "
                "regimes com regras e alíquotas diferentes (ver tributação de ações)."
            ),
            "operador": (
                "Day trade: compra e venda do mesmo papel no mesmo pregão, zera no "
                "dia. Swing trade: posição carregada de um dia para outro. Regimes "
                "fiscais diferentes — ver mkt-tributacao."
            ),
        },
        "veja": ["mkt-tributacao"],
    },
    {
        "id": "mkt-tributacao",
        "termos": ("tributação", "tributacao", "imposto de renda ações",
                   "imposto sobre ações", "darf", "ir sobre ações",
                   "isenção de imposto ações"),
        "texto": {
            "educacional": (
                "Imposto de Renda sobre ações tem regra separada por regime. No "
                "SWING TRADE, a alíquota é " + str(mercado_ref.SWING_ALIQUOTA_PCT)
                + "% sobre o lucro, com isenção quando a SOMA DAS VENDAS do mês fica "
                "até R$ " + f"{mercado_ref.SWING_ISENCAO_TETO_VENDAS_MES:,.0f}".replace(",", ".")
                + " — repare que o teto é sobre o total vendido, não sobre o lucro; é "
                "o erro mais comum. No DAY TRADE, a alíquota é "
                + str(mercado_ref.DAY_TRADE_ALIQUOTA_PCT)
                + "% sobre o lucro do dia, sem isenção nenhuma, qualquer valor. Nos "
                "dois casos, quando há imposto devido, o recolhimento é feito por "
                "DARF (código " + mercado_ref.DARF_CODIGO + "), com prazo "
                + mercado_ref.DARF_PRAZO_TXT
                + " — a corretora não recolhe isso automaticamente, é uma "
                "responsabilidade de quem investe. A carteira do app é simulada e "
                "não gera obrigação fiscal nenhuma; isto é só para entender como "
                "funcionaria numa operação real."
            ),
            "operador": (
                "Ações: swing " + str(mercado_ref.SWING_ALIQUOTA_PCT) + "% sobre "
                "lucro, isento até R$ "
                + f"{mercado_ref.SWING_ISENCAO_TETO_VENDAS_MES:,.0f}".replace(",", ".")
                + " em VENDAS/mês (não lucro). Day trade "
                + str(mercado_ref.DAY_TRADE_ALIQUOTA_PCT)
                + "% sobre lucro, sem isenção. DARF " + mercado_ref.DARF_CODIGO + ", "
                + mercado_ref.DARF_PRAZO_TXT + ". Apuração é responsabilidade de quem "
                "investe, corretora não recolhe sozinha. Carteira do app: simulada, "
                "sem efeito fiscal."
            ),
        },
        "veja": ["mkt-day-trade-swing", "mkt-proventos", "mkt-carteira-simulada"],
    },
    {
        "id": "mkt-proventos",
        "termos": ("dividendo", "dividendos", "jcp", "juros sobre capital próprio",
                   "provento", "proventos"),
        "texto": {
            "educacional": (
                "Dividendo e JCP (juros sobre capital próprio) são duas formas da "
                "empresa distribuir lucro a quem tem ação — o mecanismo em si não "
                "depende da estratégia (vale tanto para quem opera quanto para quem só "
                "carrega o papel). A tributação de proventos mudou em 2026 (Lei "
                "Complementar 224/2025) e ficou mais complexa do que caberia resumir "
                "aqui com segurança: há faixas de retenção, teto por empresa e regra "
                "de transição para o que já tinha sido aprovado antes da lei. Em vez "
                "de arriscar um número desatualizado, o caminho mais seguro é "
                "conferir a regra em vigor diretamente na Receita Federal ou com um "
                "contador antes de decidir algo com base nisso."
            ),
            "operador": (
                "Dividendo/JCP: distribuição de lucro ao acionista. Tributação mudou "
                "em 2026 (LC 224/2025) — faixas, teto por empresa e transição, "
                "demais complexa para resumir em um número fixo aqui. Confirmar regra "
                "vigente na Receita Federal/contador antes de decisão real."
            ),
        },
        "veja": ["mkt-tributacao"],
    },
    {
        "id": "mkt-liquidacao",
        "termos": ("liquidação", "liquidacao", "d+2", "quando o dinheiro cai",
                   "prazo de liquidação"),
        "texto": {
            "educacional": (
                "Liquidação é o prazo entre fechar uma operação na bolsa e o dinheiro "
                "(ou o ativo) efetivamente mudar de dono. Hoje esse prazo é D+"
                + str(mercado_ref.LIQUIDACAO_DIAS_HOJE)
                + " — quem vende uma ação só vê o dinheiro disponível " +
                str(mercado_ref.LIQUIDACAO_DIAS_HOJE) + " dias úteis depois do "
                "pregão em que a venda aconteceu, não no mesmo dia. A B3 tem um "
                "projeto para reduzir esse prazo (D+1), mas é apenas um " +
                mercado_ref.LIQUIDACAO_D1_STATUS_TXT + " — o prazo real hoje continua "
                "sendo D+" + str(mercado_ref.LIQUIDACAO_DIAS_HOJE) + "."
            ),
            "operador": (
                "Liquidação hoje: D+" + str(mercado_ref.LIQUIDACAO_DIAS_HOJE)
                + " (dinheiro/ativo só disponível 2 dias úteis após o pregão). D+1 é "
                + mercado_ref.LIQUIDACAO_D1_STATUS_TXT + " — não vigente ainda."
            ),
        },
        "veja": [],
    },
    {
        "id": "mkt-termo-futuro",
        "termos": ("mercado a termo", "mercado futuro", "contrato futuro",
                   "termo x futuro"),
        "texto": {
            "educacional": (
                "Mercado à vista (o que o app simula) é comprar/vender o ativo para "
                "liquidação quase imediata. Mercado a TERMO e mercado FUTURO são "
                "diferentes: nos dois, compra e venda são combinadas hoje para "
                "liquidar numa data futura — a diferença entre eles é que o termo tem "
                "vencimento livremente negociado entre as partes, e o futuro segue "
                "vencimentos padronizados pela bolsa, com ajuste diário de ganhos e "
                "perdas até lá. São instrumentos mais avançados, usados sobretudo "
                "para proteção (hedge) ou alavancagem — fora do que a carteira "
                "simulada do app registra hoje."
            ),
            "operador": (
                "À vista (o que o app simula): liquidação quase imediata. Termo: "
                "vencimento livre entre as partes. Futuro: vencimento padronizado, "
                "ajuste diário. Hedge/alavancagem — fora do escopo da carteira "
                "simulada."
            ),
        },
        "veja": ["mkt-carteira-simulada"],
    },
    {
        "id": "mkt-ipo",
        "termos": ("ipo", "abertura de capital", "oferta pública inicial",
                   "estreia na bolsa"),
        "texto": {
            "educacional": (
                "IPO (Initial Public Offering, ou oferta pública inicial) é o "
                "momento em que uma empresa vende ações ao público pela primeira vez "
                "e passa a ser negociada na bolsa. Antes do IPO, o papel simplesmente "
                "não existe na B3 — o app só consegue acompanhar um ativo depois "
                "dessa estreia. Ação recém-listada costuma ter histórico de preço "
                "curto, o que deixa indicadores que dependem de muitos candles "
                "(médias longas, por exemplo) menos confiáveis por um tempo."
            ),
            "operador": (
                "IPO: primeira venda pública das ações, início da negociação em "
                "bolsa. Antes disso, o ticker não existe na B3. Papel recém-listado: "
                "histórico curto, indicadores de janela longa menos confiáveis."
            ),
        },
        "veja": ["mkt-ticker"],
    },
    {
        "id": "mkt-indices",
        "termos": ("ibovespa", "ibov", "ifix", "índice da bolsa", "indice da bolsa",
                   "o que é o ibovespa"),
        "texto": {
            "educacional": (
                "Um índice de bolsa mede o desempenho médio de uma cesta de ativos, "
                "servindo de termômetro do mercado. O IBOVESPA (IBOV) é o principal "
                "índice de ações da B3, formado pelas ações mais negociadas; o IFIX "
                "é o equivalente para fundos imobiliários. Nenhum índice é um ativo "
                "que se compra diretamente — quem quer exposição a ele costuma usar "
                "um ETF que o replica (ex.: BOVA11 para o Ibovespa)."
            ),
            "operador": (
                "Índice = termômetro de uma cesta de ativos. IBOV: principal índice "
                "de ações da B3. IFIX: equivalente para FIIs. Não se compra o índice "
                "direto — via ETF que replica (ex.: BOVA11)."
            ),
        },
        "veja": ["mkt-etf"],
    },
]


# =============================================================================
# 11) KPIs de `kpi._MAPS` — os campos de enum que a leitura da IA normaliza
#     para a UI. `_MAPS` é sobre normalização de VALORES (acento/caixa →
#     rótulo canônico), não sobre conceito de negócio em si — mas os quatro
#     CAMPOS que ele normaliza (direção, convicção, qualidade, recomendação)
#     são os mesmos que a UI expõe como chips, então cada um ganha verbete
#     próprio aqui (id = "kpi-<campo>", o critério que o teste de espelho usa).
# =============================================================================
_KPIS = [
    {
        "id": "kpi-direcao",
        "termos": ("direção", "direcao", "viés", "vies", "alta baixa lateral"),
        "texto": {
            "educacional": (
                "Direção é o VIÉS que a leitura encontrou no momento — Alta, Baixa ou "
                "Lateral — e nasce da combinação entre tendência, estrutura e momentum, "
                "nunca de um indicador isolado. Não é uma previsão do que o preço vai "
                "fazer a seguir, é a leitura do que ele já vem fazendo."
            ),
            "operador": (
                "Direção: Alta | Baixa | Lateral. Combinação de tendência, estrutura e "
                "momentum — nunca um indicador isolado."
            ),
        },
        "veja": ["familia-tendencia"],
    },
    {
        "id": "kpi-conviccao",
        "termos": ("convicção", "conviccao", "confiança", "nível de confiança"),
        "texto": {
            "educacional": (
                "Convicção é o nível de confiança da leitura — Muito Alto, Alto, Médio "
                "ou Baixo — e só sobe quando há confluência real entre estrutura, "
                "tendência, volume, momentum, volatilidade, R:R e confirmação em mais de "
                "um horizonte de tempo. Sem um segundo horizonte de tempo confiável, o "
                "teto é 'Médio' — convicção nunca é medida de certeza sobre o resultado."
            ),
            "operador": (
                "Convicção: Muito Alto | Alto | Médio | Baixo. Teto 'Médio' sem "
                "confirmação multi-timeframe. Não é certeza de resultado."
            ),
        },
        "veja": ["kpi-direcao"],
    },
    {
        "id": "kpi-qualidade",
        "termos": ("qualidade", "qualidade da leitura", "qualidade da análise"),
        "texto": {
            "educacional": (
                "Qualidade é uma nota resumida — Excelente, Boa, Regular ou Ruim — para "
                "o conjunto da leitura daquele instante: o quanto os dados e os critérios "
                "sustentam a conclusão. Não é a mesma coisa que o Fundamento (que avalia "
                "o NEGÓCIO por trás do papel, com regra objetiva própria) nem que a "
                "Convicção (que mede confiança na leitura técnica)."
            ),
            "operador": (
                "Qualidade: Excelente | Boa | Regular | Ruim. Nota da leitura do "
                "instante — diferente de Fundamento (negócio) e de Convicção (confiança)."
            ),
        },
        "veja": ["fundamento", "kpi-conviccao"],
    },
    {
        "id": "kpi-recomendacao",
        "termos": ("recomendação", "recomendacao", "decisão", "decisao", "veredito"),
        "texto": {
            "educacional": (
                "Recomendação é o VEREDITO da leitura, no vocabulário de estudo: "
                "'Estudar alta', 'Estudar baixa', 'Monitorar', 'Aguardar', 'Não operar' "
                "ou 'Reduzir risco' — nunca 'comprar'/'vender'. É um plano educacional "
                "para o simulador, não uma recomendação de investimento."
            ),
            "operador": (
                "Recomendação (mesa): COMPRAR | VENDER | AGUARDAR CONFIRMAÇÃO | NÃO "
                "OPERAR, com 'Reduzir risco' como extensão de saída parcial."
            ),
        },
        "veja": ["gatilho"],
    },
]


# =============================================================================
# Catálogo consolidado.
# =============================================================================
def _marcar_familia(itens: list, familia: str) -> list:
    """As listas literais acima (_INDICADORES, _ESTRUTURA, ...) não repetem a
    chave `familia` em cada dict — ela é a mesma para todos os itens da
    lista, então entra uma vez só aqui, por grupo."""
    out = []
    for it in itens:
        v = dict(it)
        v["familia"] = familia
        out.append(v)
    return out


def _construir() -> list:
    out = []
    out += _conceitos_verbetes()
    out += _timing_verbetes()
    out += _marcar_familia(_INDICADORES, "indicadores")
    out += _marcar_familia(_ESTRUTURA, "estrutura")
    out += _marcar_familia(_FAMILIAS, "familias")
    out += _modelos_verbetes()
    out += _marcar_familia(_SETUPS, "setups")
    out += _marcar_familia(_PLANO_RISCO_EXTRA, "plano_risco")
    out += _marcar_familia(_FUNDAMENTOS_EXTRA, "fundamentos")
    out += _marcar_familia(_MERCADO_B3, "mercado_b3")
    out += _marcar_familia(_KPIS, "estados_app")
    return out


def catalogo() -> list:
    """Todos os verbetes da KB. Reconstrói a cada chamada (o custo é
    desprezível para o tamanho deste catálogo) para refletir o estado atual
    de `conceitos.didatica_ligada()` e de `skill_ref`/`MODELS`/`timing`
    sem exigir reimport — mesma filosofia de `conceitos.catalogo()`."""
    return _construir()


def verbete(vid: str) -> Optional[dict]:
    """Um verbete pelo id, ou None se não existir."""
    for v in catalogo():
        if v["id"] == vid:
            return v
    return None


def _bate_como_palavra(termo_normalizado: str, texto_normalizado: str) -> bool:
    """`termo` aparece em `texto` com fronteira de palavra dos dois lados —
    não como substring cru. Sem isso, o termo de 1 caractere "r" (do verbete
    "r", a régua de risco) "batia" dentro de "rsi" e vencia "ind-rsi" numa
    busca por "o que é RSI" — achado ao escrever o teste `buscar` desta
    fase."""
    if not termo_normalizado:
        return False
    return re.search(r"(?<!\w)" + re.escape(termo_normalizado) + r"(?!\w)",
                     texto_normalizado) is not None


def _pontuar(v: dict, q_normalizado: str) -> int:
    """Pontuação de um verbete contra uma pergunta JÁ normalizada: soma do
    comprimento (em caracteres) dos termos que aparecem como PALAVRA/FRASE
    inteira (fronteira de palavra — ver `_bate_como_palavra`), mais o bônus do
    próprio `id` se ele também aparece. Termo mais longo e específico pesa
    mais. Extraída de `buscar()` para `resolver()` (Fase F3) reusar o mesmo
    critério sem duplicar a lógica."""
    pontos = 0
    for termo in v["termos"]:
        t = _normalizar(termo)
        if _bate_como_palavra(t, q_normalizado):
            pontos += len(t)
    vid = _normalizar(v["id"])
    if _bate_como_palavra(vid, q_normalizado):
        pontos += len(vid)
    return pontos


def buscar(pergunta: str, limite: int = 5) -> list:
    """Busca determinística por termo/pergunta.

    Não é tokenização nem sinônimo de snapshot — é pontuação por termo batido
    como palavra/frase inteira (`_pontuar`). Serve à rota pública
    `GET /api/kb/buscar` (Fase F3): aqui não há corte de confiança, é busca —
    quem decide "a KB cobre isso o bastante para dispensar a LLM" é
    `resolver()`, com critério mais estrito."""
    q = _normalizar(pergunta)
    if not q:
        return []
    pontuados = [(p, v) for v in catalogo() if (p := _pontuar(v, q))]
    pontuados.sort(key=lambda par: -par[0])
    return [v for _, v in pontuados[:limite]]


def formatar(v: dict, modo: str) -> dict:
    """Um verbete, pronto para a API: só o texto do MODO pedido (nunca os
    dois — o caminho antigo do `assistente.py` decide o vocabulário uma vez,
    a KB segue a mesma regra) e o `veja` para navegação."""
    voc = "operador" if modo == "operador" else "educacional"
    return {
        "id": v["id"],
        "familia": v.get("familia"),
        "texto": v["texto"].get(voc) or v["texto"].get("educacional") or "",
        "veja": list(v.get("veja") or []),
    }


# =============================================================================
# Roteamento KB → LLM (Fase F3). `resolver()` é o crivo de CONFIANÇA que
# `/api/assistente` consulta antes de gastar com a LLM: None significa "a KB
# não cobre isto com segurança", nunca "não encontrei nada parecido" — os dois
# casos são bem diferentes (o segundo ainda arriscaria responder errado).
# =============================================================================
_CONFIANCA_MIN = 3  # abaixo disso (ex.: sigla de 1-2 letras) o match é ruído

# Preço com duas casas decimais (formato de centavos em R$, ex. "43,09" ou
# "128.50"). Uma pergunta que cita um número assim está presumivelmente sobre
# um valor ESPECÍFICO da tela do usuário (entrada, gatilho, stop...) — a KB é
# glossário genérico, não tem preço de ativo nenhum, então essa pergunta
# precisa da LLM, que recebe o snapshot. Deliberadamente NÃO pega números
# curtos como "9.1" (nome de setup) ou "200" (SMA200): só o padrão de centavos.
_PRECO_RE = re.compile(r"\d+[.,]\d{2}(?!\d)")


def _pergunta_cita_numero_especifico(pergunta: str) -> bool:
    return bool(_PRECO_RE.search(str(pergunta or "")))


def resolver(pergunta: str, modo: str = "educacional") -> Optional[dict]:
    """Decide se a KB responde `pergunta` sem LLM. Devolve o verbete formatado
    (com `fonte: "kb"`) quando a confiança é suficiente; `None` quando não —
    o chamador (`/api/assistente`) cai para a LLM nesse caso, nunca força uma
    resposta fraca."""
    if _pergunta_cita_numero_especifico(pergunta):
        return None
    q = _normalizar(pergunta)
    if not q:
        return None
    pontuados = [(p, v) for v in catalogo() if (p := _pontuar(v, q)) >= _CONFIANCA_MIN]
    if not pontuados:
        return None
    pontuados.sort(key=lambda par: -par[0])
    _, v = pontuados[0]
    out = formatar(v, modo)
    out["fonte"] = "kb"
    return out
