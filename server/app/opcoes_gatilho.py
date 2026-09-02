"""Gatilho puro: traduz o plano do Radar (`setups.plano_do_resultado`) numa
decisão de avaliar estrutura de opções (Fase 15, Plano 02, ENG-06).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio interna,
mesma disciplina de `opcoes_lastreadas.py`/`setups.py`.

QUEM decide QUANDO avaliar uma proposta continua sendo o motor de setups
técnicos que já está em produção (Radar / setups.py / indicators.py) — este
módulo só lê o plano que ele já produz, nunca calcula indicador próprio nem
aceita sinal de origem externa. Ver os comentários logo abaixo para o
racional completo por trás da proibição de uma segunda fonte de gatilho.
"""
# Racional ENG-06: o motor técnico do Boris (Radar, setups.py/indicators.py)
# é a ÚNICA fonte do gatilho. A DSL de setups declarativa do repositório
# externo b-mcp (~/dev/MCP/servers/mydata/setups.py) NÃO é portada nem
# importada aqui — o sinal ingênuo de confluência daquele motor já foi
# medido perdendo dinheiro e corrigido em ADR-016/017 (ver PROJECT.md).
# Reintroduzi-la sem passar pelo mesmo processo de validação
# (scripts/backtest_sinal.py) traria de volta um defeito de produto já
# fechado. O guardião de testes desta suíte reprova qualquer import, string
# ou arquivo que traga essa DSL de volta para dentro do app.

from .setups import DECISAO_VENDER, DECISAO_AGUARDAR, DECISAO_NAO_OPERAR

# Constantes públicas — a Fase 16 mapeia viés -> estrutura concreta (venda
# coberta, put, collar) usando estas, nunca um literal solto.
VIES_PROTECAO = "protecao"
VIES_PREMIO = "premio"

# Reusa a MESMA chave de motivo já traduzida por skill_ref.opcoes_lastreadas_txt.
MOTIVO_SEM_SETUP = "sem_setup"

_LADO_BAIXA = "baixa"
_LADO_NEUTRO = "neutro"


def do_plano(plano):
    """Traduz o plano do Radar (dict com `decisao`/`lado`, produzido por
    `setups.plano_do_resultado`/`setups.plano_operacional`) na decisão de
    avaliar uma estrutura de opções.

    Mesma ordem de avaliação que `opcoes_lastreadas.propor()` já usa em
    produção — decisão de venda ou lado de queda vence primeiro (viés de
    proteção); decisão de aguardar confirmação/não operar ou lado neutro
    vem em seguida (viés de prêmio); qualquer outro caso — inclusive plano
    ausente, vazio, não-dict ou com decisão desconhecida — não avalia
    nenhuma estrutura. `vies` é deliberadamente abstrato: quem mapeia viés
    para estrutura concreta é a Fase 16.

    Devolve sempre `{"avaliar": bool, "vies": "protecao"|"premio"|None,
    "motivo": str}`; `avaliar is True` se e somente se `vies is not None`.
    Entrada não-dict (None, str, int, ...) nunca levanta exceção — plano
    ausente é estado normal (papel sem setup no momento), não erro.
    """
    if not isinstance(plano, dict):
        return {"avaliar": False, "vies": None, "motivo": MOTIVO_SEM_SETUP}

    decisao = plano.get("decisao")
    lado = plano.get("lado")

    if decisao == DECISAO_VENDER or lado == _LADO_BAIXA:
        # Risco de queda sobre a posição existente: proteger.
        return {"avaliar": True, "vies": VIES_PROTECAO, "motivo": VIES_PROTECAO}
    if decisao in (DECISAO_AGUARDAR, DECISAO_NAO_OPERAR) or lado == _LADO_NEUTRO:
        # Sem alta a preservar no momento: gerar prêmio.
        return {"avaliar": True, "vies": VIES_PREMIO, "motivo": VIES_PREMIO}

    # Decisão de compra/lado de alta: avaliar estrutura aqui contrariaria a
    # leitura técnica que o motor já fez (mesmo racional de propor()).
    # Decisão/lado desconhecidos ou plano vazio caem no mesmo motivo, nunca
    # num viés por default.
    return {"avaliar": False, "vies": None, "motivo": MOTIVO_SEM_SETUP}
