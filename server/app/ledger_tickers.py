"""server/app/ledger_tickers.py — mapa de resolução de tickers do BOOTSTRAP do
ledger de sinais resolvidos (LEDGER-01, Fase 0 do milestone v1.2,
`00-01-PLAN.md`, Task 2).

Por que este mapa existe: 9 dos 74 tickers de `scanner.DEFAULT_UNIVERSE`
falhavam com HTTP 404 estável no Yahoo dentro do bootstrap
(`signal_ledger_bootstrap.py`). O diagnóstico datado
(`docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md`) evidenciou, por ticker, se
o 404 é renomeação (mesma empresa, mesmo papel, código novo — vira alias
aqui) ou reorganização societária/deslistagem/classe extinta (vira exclusão
com razão). Cada entrada dos dois dicionários abaixo cita a linha de
evidência do diagnóstico — nenhuma entrada nasce sem prova anexada.

Por que este mapa NÃO é `scanner.DEFAULT_UNIVERSE` (decisão A-01 do plano):
`DEFAULT_UNIVERSE` é o universo que o Radar varre — trocar um símbolo ali
muda o que o usuário vê na tela, e o guardrail do milestone v1.2 proíbe
qualquer superfície visível nova/alterada. A resolução de símbolo fica
inteiramente confinada ao bootstrap: o ticker do UNIVERSO nunca muda (é a
chave do ledger, `UNIQUE(ticker, setup, lado, data_sinal)`), só o símbolo
BUSCADO no Yahoo muda quando há alias.

Regra A-02 (mesma decisão do plano): se o ticker foi RENOMEADO (mesma
empresa, mesmo papel/classe, código novo), a série do Yahoo sob o código
novo é a continuação da mesma série — vira `ALIASES`. Se houve
INCORPORAÇÃO/FUSÃO (empresa diferente, relação de troca de ações),
DESLISTAGEM, ou o candidato encontrado é de CLASSE diferente (ON vs PN,
DR vs ação comum), o ticker é EXCLUÍDO com razão escrita — emendar duas
séries de preço distintas corromperia exatamente a medição que LEDGER-01
existe para destravar.

Se um diagnóstico futuro concluir que os 9 originais eram só ruído
transitório do Yahoo (veredito `TRANSITORIO` no documento), os dois
dicionários abaixo ficam VAZIOS — isso é um resultado LEGÍTIMO, não uma
falha deste módulo: o retry de 404 adicionado em `carregar_candles`
(`signal_ledger_bootstrap.py`) é o que fecharia o requisito nesse cenário,
sem precisar de nenhuma entrada aqui.
"""
from __future__ import annotations

from typing import Optional

from .tickers import normalize_ticker

# ---------------------------------------------------------------------------
# ALIASES — renomeação: mesma empresa, mesmo papel/classe, código novo.
# Evidência: docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, seção 4.
# ---------------------------------------------------------------------------
ALIASES: dict[str, str] = {
    # MRFG3 -> MBRF3: Marfrig absorveu BRF e renomeou o código já listado
    # ("MBRF Global Foods Company S.A."); série de preço contínua de 2 anos
    # sob o código novo, mesma classe ON (dígito 3).
    "MRFG3": "MBRF3",
    # EMBR3 -> EMBJ3: mesma classe ON (dígito 3), série de preço contínua de
    # 2 anos sob o código novo, quote ativo "Embraer S.A.". A busca por raiz
    # do ticker (EMBR) não encontra o candidato porque a raiz mudou de
    # letras, não só o dígito — achado fechado por busca por NOME da
    # empresa (seção 3.2/5 do diagnóstico).
    "EMBR3": "EMBJ3",
}

# ---------------------------------------------------------------------------
# EXCLUIDOS — deslistagem, incorporação/fusão, classe extinta, ou lacuna
# aberta (`INDETERMINADO`, prefixo datado obrigatório).
# Evidência: docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, seção 4.
# ---------------------------------------------------------------------------
EXCLUIDOS: dict[str, str] = {
    "BRFS3": (
        "EXCLUIR: BRF S.A. sem série própria remanescente sob nenhum "
        "código Yahoo (quote vazio); evidência aponta fusão com Marfrig no "
        "combinado \"MBRF Global Foods Company S.A.\" (MBRF3.SA), mas a "
        "série de MBRF3 tem patamar de preço compatível com o histórico do "
        "Marfrig antigo, não com BRF — emendar corromperia a medição "
        "(A-02, incorporação/fusão com relação de troca de ações). Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito BRFS3."
    ),
    "JBSS3": (
        "EXCLUIR: JBS S.A. reorganizada em JBS N.V.; a única sucessora "
        "encontrada na B3 (JBSS32.SA) é um instrumento DR2 (recibo de "
        "depósito), classe diferente da ação ordinária original — falha o "
        "teste de \"mesmo papel\" de A-02. Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito JBSS3."
    ),
    "CRFB3": (
        "EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false "
        "(instrumento inativo, não ausência total) e nenhuma sucessora foi "
        "encontrada em nenhuma busca (raiz do ticker, nome \"Atacadão\"/"
        "\"Carrefour Brasil\"). Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito CRFB3."
    ),
    "NTCO3": (
        "EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false "
        "(mesmo padrão de CRFB3/JBSS3); nenhuma sucessora encontrada em "
        "nenhuma busca (raiz do ticker, nome \"Natura\"). Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito NTCO3."
    ),
    "CPLE6": (
        "EXCLUIR: classe PNB extinta — os únicos candidatos encontrados "
        "(CPLE3 e variantes) são todos classe ON, papel diferente do "
        "original por A-02; sem candidato de classe 6/PNB. Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito CPLE6."
    ),
    "ELET3": (
        "não resolvido em 2026-08-28: 404 em 3/3 tentativas, quote Yahoo "
        "vazio (sem stub), busca por raiz \"ELET\" e por nome "
        "\"Eletrobras\" sem candidato plausível na B3. Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito ELET3."
    ),
    "ELET6": (
        "não resolvido em 2026-08-28: mesma ausência total de ELET3 — 404 "
        "em 3/3 tentativas, quote Yahoo vazio, sem candidato de sucessora "
        "de classe 6/PNB encontrado. Ver "
        "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito ELET6."
    ),
}


def resolver(ticker: str) -> tuple[Optional[str], Optional[str]]:
    """Resolve um ticker do universo para o símbolo a buscar no Yahoo.

    Devolve `(simbolo_para_buscar, None)` quando o ticker é negociável hoje
    (direto ou via alias), ou `(None, razao_da_exclusao)` quando o ticker
    está em `EXCLUIDOS`. Ticker fora dos dois mapas resolve para si mesmo —
    é o caminho comum, sem custo, para os outros 65 tickers do universo.
    """
    tk = normalize_ticker(ticker)
    if tk in EXCLUIDOS:
        return None, EXCLUIDOS[tk]
    if tk in ALIASES:
        return ALIASES[tk], None
    return tk, None
