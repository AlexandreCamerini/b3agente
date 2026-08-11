"""Camada de ENTENDIMENTO — catálogo determinístico de conceitos.

Por que existe: havia didática para o que a LLM escreve e NENHUMA para o que o
app afirma sozinho. Timing, R, confluência, fundamento e barra de 15m são
determinísticos — nenhuma LLM os produziu, então nenhuma LLM os explica. Este
módulo é a fonte única desse texto, no mesmo padrão de `skill_ref.TIMING`:
o backend serve a frase pronta, o front nunca compõe vocabulário.

Três decisões que moldam o formato:

  • ORDEM DAS RESPOSTAS. "O que NÃO acontece" vem PRIMEIRO. Para quem acabou
    de ver "condição atingida" (ou pior, recebeu uma notificação), a primeira
    pergunta é "o app comprou alguma coisa?" — essa resposta não pode ser a
    terceira.
  • ANCORADO NO DADO EM EXIBIÇÃO. Cada parágrafo pode citar `{campos}` do card
    naquele instante. Campo ausente NÃO vira estimativa: o parágrafo inteiro
    é descartado (Princípio 1 — nenhum número inventado).
  • MESMA LEI DE VOCABULÁRIO. O modo entra por `{rotulo*}` e pelo título; o
    corpo é um só. No Estudo descreve condição, sem verbo de ordem; no
    Operador fala como mesa. Guardião: test_guardrail_imperativo.

Custo: zero. Nenhuma chamada de LLM em nenhum caminho deste módulo — a camada
paga (assistente) é outra, e opt-in.
"""
from __future__ import annotations

import os
from typing import Optional

# --- Chaves de desligamento (independentes, sem rebuild do app) --------------
# Se a camada sair errada em produção, o caminho de volta é uma variável de
# ambiente no Railway, não um build de iOS (que leva um ciclo de TestFlight).


def didatica_ligada() -> bool:
    return os.environ.get("B3_DIDATICA_OFF") != "1"


def assistente_ligado() -> bool:
    return os.environ.get("B3_ASSISTENTE_OFF") != "1"


# --- Rótulos por modo (o que o card mostra em cada estado) -------------------
# Espelham TIMING_STYLE do App.jsx; ficam aqui para o texto do conceito citar o
# rótulo que o usuário está VENDO, e não um sinônimo.
ROTULOS = {
    "educacional": {"rotuloArmado": "CONDIÇÃO ARMADA", "rotuloAtingido": "CONDIÇÃO ATINGIDA",
                    "nivel": "nível"},
    "operador": {"rotuloArmado": "PLANO ARMADO", "rotuloAtingido": "GATILHO ATINGIDO",
                 "nivel": "gatilho"},
}


# --- Catálogo ---------------------------------------------------------------
# `campos` é ALLOWLIST, não documentação: só estas chaves de `dados` entram na
# interpolação, e os rótulos do modo são aplicados DEPOIS delas. Sem isso, um
# chamador que mandasse `{"rotuloAtingido": "COMPRE AGORA"}` reescreveria o
# vocabulário canônico por um dict — e o guardião de verbo de ordem, que varre
# o catálogo estático, não teria como pegar.
#
# Parágrafo com placeholder de campo ausente some — nunca aparece com lacuna.
# Parágrafo escrito como `(("estado",...), "texto")` só entra naqueles estados:
# `excedenteEmR` volta em DOIS estados (timing.py:126 esticado, :130 gatilho) e
# eles pedem leituras OPOSTAS. Um parágrafo só para os dois dizia "movimento
# esticado, não persiga" no instante exato em que a condição acabou de valer.
#
# `resumido=True` (perfil intermediário/avançado) corta a DEFINIÇÃO genérica e
# preserva os parágrafos ancorados nos números daquele card — quem já sabe o
# que é um gatilho é justamente quem não precisa do texto de manual. "O que NÃO
# acontece" e "o que acontece" ficam íntegros nos dois níveis: ali moram o
# enquadramento regulatório e a idade do dado, que não se graduam por
# experiência declarada.
CONCEITOS = {
    "gatilho": {
        "titulo": {"educacional": "A condição de estudo (o “gatilho”)",
                   "operador": "O gatilho de entrada"},
        "campos": ("ticker", "entrada", "stop", "distancia", "distanciaEmR",
                   "excedenteEmR", "hora", "lado"),
        "naoAcontece": [
            "O app não compra nem vende nada. Nenhuma ordem sai daqui para uma "
            "corretora: a carteira é simulada e a execução continua sendo sua.",
            "Chegar ao gatilho também não afirma que o preço vai subir ou cair. "
            "É uma condição do plano que passou a valer — não uma previsão, e "
            "muito menos uma promessa de resultado.",
        ],
        "oQueE": [
            "Gatilho é um preço combinado ANTES, quando ninguém está com pressa. "
            "Enquanto o preço não chega lá, o plano fica esperando; ao chegar, a "
            "condição que o plano pedia aconteceu.",
            "No plano de hoje para {ticker}, esse preço é {entrada}.",
            "Ele não é palpite: sai do plano diário calculado pelo app, o mesmo "
            "cálculo que põe o stop em {stop} — o preço em que a ideia deixa de "
            "valer e a perda é cortada.",
        ],
        "oQueAcontece": [
            "Quando uma vela de 15 minutos FECHA no gatilho ou além dele, o card "
            "troca de “{rotuloArmado}” para “{rotuloAtingido}”. Só isso: o card "
            "muda de estado.",
            "Vale por vela FECHADA, não por qualquer toque no preço. Preço que "
            "encosta no gatilho e volta atrás dentro da mesma vela não cumpre a "
            "condição — foi ruído, não rompimento.",
            "A leitura tem a idade da vela: o feed intraday (Yahoo Finance) tem "
            "cerca de 15 minutos de atraso medido. O que você vê já aconteceu; "
            "nunca é agora.",
            (("armado",),
             "Neste momento falta {distancia} até o {nivel} — {distanciaEmR} na "
             "régua de risco deste plano."),
            (("gatilho",),
             "Foi o que acabou de ocorrer aqui: a vela fechou {excedenteEmR} "
             "além do {nivel}, ainda dentro da margem que o plano considera "
             "válida. A condição valeu — o que fazer com ela continua sendo "
             "decisão sua."),
            (("esticado",),
             "Aqui o preço passou {excedenteEmR} do {nivel} — longe demais. O "
             "app chama isso de “movimento esticado” e trata como motivo para "
             "não perseguir preço: entrar agora significaria arriscar mais para "
             "ganhar menos do que o plano previa."),
        ],
        "veja": ["r", "stop", "barra15m"],
    },

    # ------------------------------------------------------------------ risco
    "stop": {
        "titulo": {"educacional": "O stop", "operador": "O stop"},
        "campos": ("ticker", "entrada", "stop", "riscoPorAcao", "precoAtual"),
        "naoAcontece": [
            "O app não vende sozinho ao tocar no stop. Aqui ele é uma linha de "
            "estudo: quem executa, e quando, é você — na sua corretora.",
            "Stop também não é uma aposta de que o preço vai cair até lá. É o "
            "ponto onde a ideia que motivou a entrada deixa de fazer sentido.",
        ],
        "oQueE": [
            "Stop é o preço em que você admite que errou — decidido ANTES de "
            "entrar, quando a cabeça está fria e não há dinheiro em jogo.",
            "Neste plano ele está em {stop}.",
            "Ele é técnico, não um percentual redondo: fica logo além do nível "
            "que sustentava a tese (um suporte, o extremo do movimento). Se o "
            "preço passa dali, a leitura foi invalidada pelo mercado — não é "
            "questão de opinião.",
        ],
        "oQueAcontece": [
            "A distância entre a entrada e o stop é o seu risco por ação: "
            "{riscoPorAcao}. É esse número que decide QUANTAS ações cabem no "
            "seu limite de perda — e não o contrário.",
            "Stop mais largo não é mais seguro: significa perder mais por ação "
            "se der errado, então a posição tem que ser menor para o risco "
            "total continuar igual.",
            "Operar sem stop não elimina o risco; só troca uma perda medida por "
            "uma perda que você não escolheu.",
        ],
        "veja": ["r", "gatilho", "alvo"],
    },
    "alvo": {
        "titulo": {"educacional": "O alvo", "operador": "O alvo"},
        "campos": ("ticker", "entrada", "stop", "alvo", "rr"),
        "naoAcontece": [
            "O app não realiza lucro sozinho, e o alvo não é uma previsão de "
            "onde o preço vai chegar. Nada aqui promete resultado.",
        ],
        "oQueE": [
            "Alvo é onde o plano prevê encerrar a operação no cenário em que "
            "ele dá certo. Serve para responder, ANTES de entrar, se vale a "
            "pena arriscar.",
            "Neste plano ele está em {alvo}.",
        ],
        "oQueAcontece": [
            "O alvo só tem sentido junto com o stop: a razão entre o que se "
            "pode ganhar e o que se pode perder é o R:R. Abaixo de {rrMin}:1 o "
            "app trata o plano como não operável — arriscar 1 para ganhar menos "
            "de {rrMin} não compensa nem quando a leitura está certa.",
            "Aqui essa razão é {rr}.",
            "Alvo distante demais melhora o R:R no papel e piora a chance de "
            "ser alcançado. Por isso ele sai de um nível técnico — a próxima "
            "resistência, a projeção do movimento — e não de um desejo.",
        ],
        "veja": ["r", "stop"],
    },
    "r": {
        "titulo": {"educacional": "O “R” (a régua do risco)",
                   "operador": "O “R” (a régua do risco)"},
        "campos": ("ticker", "entrada", "stop", "riscoPorAcao", "distanciaEmR"),
        "naoAcontece": [
            "R não é dinheiro nem porcentagem da carteira. É uma unidade de "
            "medida — e por isso não diz quanto você vai ganhar.",
        ],
        "oQueE": [
            "1R é o seu risco naquela operação: a distância entre a entrada e o "
            "stop. Todo o resto do plano é medido nessa régua.",
            "Neste plano, 1R vale {riscoPorAcao} por ação.",
            # Sem cifrão de propósito: o guardião do catálogo genérico proíbe
            # "R$" ali, porque cifrão no texto sem card é sinal de número de
            # ativo vazando. Exemplo ilustrativo escreve o valor por extenso.
            "Falar em R em vez de reais permite comparar planos de ativos "
            "diferentes na mesma escala: “ganhei 2R” quer dizer o mesmo num "
            "papel de 15 reais e num de 90.",
        ],
        "oQueAcontece": [
            "Quando o card diz “a 0,9R do nível”, está dizendo que falta quase "
            "um risco inteiro de distância até lá — não que o preço subiu 0,9%.",
            "É também como o app decide que um movimento esticou: passar mais "
            "de {zona}R além do gatilho já é perseguir preço.",
            "E é a régua da sua disciplina: se cada perda é 1R, uma sequência "
            "ruim tem tamanho previsível — o que não acontece quando cada "
            "operação arrisca um valor diferente.",
        ],
        "veja": ["stop", "alvo", "gatilho"],
    },

    # ---------------------------------------------------------------- leitura
    "confluencia": {
        "titulo": {"educacional": "A confluência (%)", "operador": "A confluência (%)"},
        "campos": ("ticker", "confluencia", "melhorSetup"),
        "naoAcontece": [
            "Confluência NÃO é probabilidade de dar certo. 100% não significa "
            "100% de chance de acerto — significa que o ativo bate com todas as "
            "condições daquele padrão histórico, e nada além disso.",
            "Ela também não é um veredito por si só: o plano sai da leitura "
            "inteira, não desse número.",
        ],
        "oQueE": [
            "Confluência mede QUANTAS condições de um setup clássico o ativo "
            "cumpre agora. Cada setup tem uma lista (estrutura de preço, "
            "volume, momentum, volatilidade); a porcentagem é quanto dessa "
            "lista está marcada.",
            "Aqui ela está em {confluencia}, no padrão “{melhorSetup}”.",
        ],
        "oQueAcontece": [
            "Confluência alta quer dizer que os indicadores CONCORDAM entre si. "
            "É o oposto do erro mais comum de iniciante: decidir por um "
            "indicador isolado, que sempre encontra alguém discordando.",
            "Confluência baixa não é sinal contrário — é sinal de que ainda não "
            "há tese formada. Nesses casos o plano costuma ser aguardar.",
            "O número olha o passado do ativo, não o futuro do mercado. Notícia, "
            "resultado e evento societário não estão nele.",
        ],
        # `fundamento` entra na cadeia porque o setor "analise" (toque longo na
        # linha de chips) abre AQUI: sem esse elo, o fundamento só seria
        # alcançável acertando o dedo no chip pequeno — o mais interno.
        "veja": ["fundamento", "gatilho"],
    },
    "fundamento": {
        "titulo": {"educacional": "O fundamento (A, B ou C)",
                   "operador": "O fundamento (A, B ou C)"},
        "campos": ("ticker", "fundamento"),
        "naoAcontece": [
            "Fundamento A não é sinal de compra, e C não é sinal de venda. Ele "
            "nunca dispara entrada nem saída — quem faz isso é a leitura "
            "técnica, com o gatilho.",
        ],
        "oQueE": [
            "É uma nota da QUALIDADE da empresa por trás do papel, em três "
            "pilares: preço em relação ao lucro, rentabilidade e endividamento.",
            "Aqui a nota é {fundamento}.",
            "A (sólido) = pelo menos 2 pilares bons; B (regular) = 1; C (fraco) "
            "= nenhum. Pilar sem dado público não pontua nem penaliza — e com "
            "menos de dois pilares o app mostra “sem dado” em vez de inventar "
            "uma letra.",
            "A comparação é dentro do SETOR, não contra um número único: um "
            "banco e uma empresa de tecnologia têm faixas de preço/lucro "
            "normais bem diferentes, e cobrar a mesma régua das duas premiaria "
            "a barata só por ser barata. Em banco, o endividamento nem entra: "
            "o passivo dele é matéria-prima, não dívida.",
        ],
        "oQueAcontece": [
            "Ele funciona como freio, nunca como acelerador: fundamento fraco "
            "REBAIXA a confiança de um plano técnico; fundamento forte NÃO a "
            "promove.",
            "A razão é de escala de tempo: qualidade de empresa se mede em "
            "anos, e o plano deste card se mede em dias. Uma empresa excelente "
            "pode estar num péssimo momento de preço, e o contrário também.",
        ],
        "veja": ["confluencia"],
    },
    "barra15m": {
        "titulo": {"educacional": "A barra de 15 minutos",
                   "operador": "A barra de 15 minutos"},
        "campos": ("ticker", "hora", "asOf"),
        "naoAcontece": [
            "O app não mostra o preço em tempo real, e nenhuma tela aqui "
            "atualiza a cada segundo. Assumir que é agora é o erro que faz "
            "alguém decidir com um dado de quinze minutos atrás achando que é "
            "de trinta segundos.",
        ],
        "oQueE": [
            "Uma barra (ou vela) de 15 minutos resume tudo o que aconteceu com "
            "o preço num intervalo de 15 minutos: onde abriu, onde fechou, e os "
            "extremos que tocou no caminho.",
            "A do card fechou às {hora}.",
            "O app só usa barras FECHADAS. A que está em formação ainda pode "
            "virar qualquer coisa até o relógio bater — e mudar de ideia a cada "
            "oscilação dentro dela é o que transforma um plano em impulso.",
        ],
        "oQueAcontece": [
            "Some a isso o atraso do feed intraday (Yahoo Finance), de cerca "
            "de 15 minutos medidos: o que a tela afirma já aconteceu, e pode "
            "ter mudado.",
            "Por isso toda afirmação de timing no app carrega a hora da barra. "
            "Se um dia você vir uma sem carimbo, desconfie dela.",
            "Nada disso invalida o estudo — invalida só a pretensão de reagir "
            "ao segundo. O plano é diário; a barra serve para dizer se a "
            "condição dele ocorreu, não para operar o minuto.",
        ],
        "veja": ["gatilho"],
    },
}


# --- Formatação pt-BR -------------------------------------------------------
def _num(v) -> Optional[str]:
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    return ("R$ %.2f" % float(v)).replace(".", ",")


def _emr(v) -> Optional[str]:
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    return ("%.1fR" % float(v)).replace(".", ",")


def _pct(v) -> Optional[str]:
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    return ("%.0f%%" % float(v))


def _num_positivo(v) -> Optional[str]:
    """Risco por ação NUNCA é negativo. Achado na verificação ao vivo: com o
    stop já acima do preço médio (stop no lucro, que o trailing produz), a
    conta `avg - stop` fica negativa e o card dizia "1R vale R$ -4,12 por
    ação" — número sem significado, no conceito que ensina a medir risco.
    Invariante de domínio, então mora aqui: valor não-positivo não formata, e
    o parágrafo que dependia dele desaparece."""
    if not isinstance(v, (int, float)) or isinstance(v, bool) or float(v) <= 0:
        return None
    return _num(v)


def _rr(v) -> Optional[str]:
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    return ("%.1f:1" % float(v)).replace(".", ",")


_FORMATADORES = {"entrada": _num, "stop": _num, "distancia": _num, "alvo": _num,
                 "precoAtual": _num, "riscoPorAcao": _num_positivo,
                 "distanciaEmR": _emr, "excedenteEmR": _emr,
                 "confluencia": _pct, "rr": _rr}


def _constantes() -> dict:
    """Números do PRODUTO que o texto cita, lidos da fonte canônica.

    Nunca literais: o R:R mínimo já viveu como "1,5" em quatro lugares e a
    auditoria de 2026-07 existiu para matar essa classe de divergência. Se o
    produto mudar o limiar, o texto didático acompanha sozinho."""
    from .setups import ZONA_PERSEGUICAO
    from . import skill_ref
    return {"rrMin": skill_ref.RR_MIN_TXT,
            "zona": ("%g" % ZONA_PERSEGUICAO).replace(".", ",")}


def _valores(modo: str, dados: Optional[dict], campos) -> dict:
    """Números do card (formatados) + rótulos do modo.

    Duas defesas, nesta ordem: `campos` é ALLOWLIST (chave fora dela nunca
    chega à interpolação) e os rótulos do modo entram POR ÚLTIMO — nenhum
    chamador reescreve o vocabulário canônico. Valor que não formata (None,
    texto vazio, tipo errado) fica de fora: é o que faz o parágrafo que
    dependia dele desaparecer em vez de mentir."""
    out = {}
    permitidos = set(campos or ())
    for k, v in (dados or {}).items():
        if k not in permitidos:
            continue
        fmt = _FORMATADORES.get(k)
        txt = fmt(v) if fmt else (str(v) if isinstance(v, (str, int, float)) and str(v) != "" else None)
        if txt:
            out[k] = txt
    out.update(ROTULOS.get(modo) or ROTULOS["educacional"])
    out.update(_constantes())
    return out


def _render(paragrafos, valores: dict, estado: Optional[str] = None) -> list:
    """Interpola os parágrafos, descartando (a) o que dependeria de campo
    ausente e (b) o que é de outro estado do timing."""
    out = []
    for p in paragrafos:
        if isinstance(p, tuple):
            estados, p = p
            if estado not in estados:
                continue
        try:
            out.append(p.format(**valores))
        except (KeyError, IndexError):
            continue  # campo ausente ⇒ o parágrafo inteiro sai (nunca estima)
    return out


def montar(cid: str, modo: str = "educacional", dados: Optional[dict] = None,
           resumido: bool = False) -> Optional[dict]:
    """Conceito pronto para exibição, no vocabulário do modo e com os números
    daquele card. `None` quando o id não existe ou a camada está desligada."""
    if not didatica_ligada():
        return None
    c = CONCEITOS.get(cid)
    if not c:
        return None
    voc = modo if modo in ROTULOS else "educacional"
    valores = _valores(voc, dados, c.get("campos"))
    estado = (dados or {}).get("estado")

    o_que_e = _render(c["oQueE"], valores, estado)
    if resumido and len(o_que_e) > 1:
        # Corta a DEFINIÇÃO genérica (o 1º parágrafo) e mantém o que está
        # ancorado nos números deste card. O inverso — que era o que estava
        # aqui — entregava texto de manual justo a quem menos precisa dele.
        o_que_e = o_que_e[1:]
    return {
        "id": cid,
        "titulo": c["titulo"][voc],
        "naoAcontece": _render(c["naoAcontece"], valores, estado),
        "oQueE": o_que_e,
        "oQueAcontece": _render(c["oQueAcontece"], valores, estado),
        # Só aponta para conceito que EXISTE — "veja também" com id fantasma
        # vira link morto que responde 404 na cara do usuário.
        "veja": [v for v in (c.get("veja") or []) if v in CONCEITOS],
    }


# --- Registro de SETORES (toque longo) ---------------------------------------
# O gesto do front declara REGIÕES; quem decide o que cada região explica é
# este registro. Motivo (spec do toque longo): a restrição mais cara do projeto
# é o build iOS — com o mapeamento aqui, repontear um setor ou mudar o
# encadeamento é deploy do Railway; só região NOVA na tela exige
# `instalar.sh --iphone`. Ele também é a allowlist de `tela: "setor:<id>"` no
# /api/assistente: id fora daqui é 400, nunca prompt.
#
# `risco` e `alvo` são setores distintos da MESMA régua: o front declara o id
# conforme o número que a régua está exibindo (régua só com alvo É o setor
# alvo) — regra herdada do guardião "a régua com só alvo não oferece um '?'
# que explica o stop".
SETORES = {
    "timing": "gatilho",        # o badge inteiro do timing de entrada
    "barra": "barra15m",        # o carimbo da hora, DENTRO do badge (mais interno)
    "analise": "confluencia",   # a linha de chips da análise
    "fundamento": "fundamento", # o chip do fundamento, DENTRO da linha (mais interno)
    "risco": "stop",            # a régua de posição exibindo stop
    "alvo": "alvo",             # a régua de posição exibindo só alvo
    "r": "r",                   # a linha do R:R
}


def setores() -> dict:
    """setorId → conceito primário. Vazio com a camada desligada — o front usa
    a ausência para não armar o gesto."""
    if not didatica_ligada():
        return {}
    # Só aponta para conceito que EXISTE — a mesma regra do "veja também".
    return {s: cid for s, cid in SETORES.items() if cid in CONCEITOS}


# Telas que o PET conhece — allowlist de `tela: "pet:<id>"` no /api/assistente,
# irmã da SETORES. F4: o pet passou a existir em TODAS as abas do app — tela
# nova entra AQUI antes de existir no front.
PET_TELAS = ("mercado", "carteira", "evolucao", "radar", "agente", "historico", "perfil")


def catalogo(modo: str = "educacional", resumido: bool = False) -> list:
    """Todos os conceitos SEM dados do card (texto genérico). Serve o prefixo
    estável do assistente e a tela de ajuda; a versão ancorada vem de montar."""
    if not didatica_ligada():
        return []
    return [montar(cid, modo, None, resumido) for cid in CONCEITOS]


def ids() -> list:
    return list(CONCEITOS)
