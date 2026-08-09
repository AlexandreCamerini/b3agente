"""Constantes de mecânica/tributação do mercado B3 — fonte única dos números
que a REGULAÇÃO pode mudar (alíquota, teto de isenção, prazo de liquidação),
no mesmo espírito de `skill_ref.RR_MIN`/`FUND_PL_MAX`: um lugar só para
atualizar, nunca busca-e-troca em prosa espalhada pela KB (`kb.py`).

Pesquisado de fontes oficiais em 2026-08-08 (sessão que gerou a memória
`kb-mecanica-b3-plano.md`) e implementado em 2026-08-09. Nenhum número aqui é
estimado — o mesmo princípio de `skill_ref.py` ("nunca invente") vale para
regra tributária: se a lei mudar, este módulo muda ANTES de qualquer verbete,
porque é daqui que eles derivam (nunca hardcoded em prosa).

Duas leis citadas abaixo (LC 224/2025, LC 15.270/2025) são RECENTES — antes de
confiar cegamente nestes números numa data muito posterior à pesquisa, vale
reconfirmar que não sofreram ajuste regulatório.
"""

# --- Tributação de ações (Imposto de Renda) — regra estável ------------------
# Fonte: B3 Borainvestir, "Comprou ou vendeu ações? Veja como declarar swing
# trade, day trade e proventos no Imposto de Renda".
SWING_ALIQUOTA_PCT = 15.0
# Isenção é sobre a SOMA DE VENDAS do mês (não sobre o lucro) — erro comum.
SWING_ISENCAO_TETO_VENDAS_MES = 20_000.0
DAY_TRADE_ALIQUOTA_PCT = 20.0  # sobre o lucro líquido mensal; SEM isenção, qualquer valor
DARF_CODIGO = "6015"
DARF_PRAZO_TXT = "até o último dia útil do mês seguinte ao da operação"
# "Dedo-duro" (IRRF retido na fonte pela corretora, antecipação do imposto):
IRRF_DEDO_DURO_SWING_PCT = 0.005       # sobre o valor da VENDA
IRRF_DEDO_DURO_DAY_TRADE_PCT = 1.0     # sobre o LUCRO do dia

# --- Reforma 2026 (LC 224/2025 e LC 15.270/2025) — regra NOVA, verificar ------
# Fontes: Demarest ("Receita Federal divulga perguntas e respostas sobre a
# nova tributação de dividendos e altas rendas") e rolmyjuncontabilidade
# ("JCP IRRF 17,5% — LC 224/2025"). Regra de transição: dividendo APROVADO até
# 31/12/2025 segue isento mesmo se pago depois dessa data.
JCP_IRRF_PCT = 17.5                       # subiu de 15% (LC 224/2025)
DIVIDENDO_RETENCAO_TETO_MES = 50_000.0    # acima disso (mesma empresa, no mês), retenção
DIVIDENDO_RETENCAO_PCT = 10.0
IRPF_MINIMO_TETO_ANUAL = 600_000.0        # acima disso, IRPF Mínimo (faixa progressiva até 10%)
DIVIDENDO_TRANSICAO_TXT = "dividendo aprovado até 31/12/2025 continua isento mesmo se pago depois"

# --- Liquidação ---------------------------------------------------------------
# Fonte: B3 oficial, "Liquidação D+1" (anúncio do projeto).
LIQUIDACAO_DIAS_HOJE = 2  # D+2
LIQUIDACAO_D1_STATUS_TXT = "projeto anunciado pela B3, sem vigência — previsão só para fevereiro/2028"

# --- Lote-padrão ---------------------------------------------------------------
LOTE_PADRAO_ACOES = 100

# --- Tipos de ordem (B3 — PUMA Trading System) --------------------------------
# Fonte: B3 oficial, página "Tipos de Ofertas" do PUMA Trading System. Lista
# completa; a KB (kb.py) cobre os tipos que um iniciante mais encontra, não
# necessariamente todos os 7.
TIPOS_ORDEM_OFICIAIS = (
    "Limitada", "A Mercado", "Stop", "A Mercado com Proteção",
    "Stop com Proteção", "Direta", "RLP",
)
