"""aba-opcoes F1 (ADR-027) — rotas do serviço MCP autenticado.

O que este módulo É: a camada HTTP da aba Opções. Ele decide QUEM pode
chamar (sessão obrigatória), QUANTO pode chamar (cap por usuário/dia,
ancorado em São Paulo) e COMO a falha vira resposta (nada cai no handler
500). Todo o diálogo com o serviço mora em `mcp_client.py`.

O que este módulo NÃO faz: nenhuma conta financeira, nenhum número
fabricado. `pregao` é `None` quando a resposta não traz pregão — princípio 4
do CLAUDE.md: dado que falta é dado que falta, nunca um valor inventado.

Cota e reserva: `_cap_check` RESERVA o custo declarado antes da rede e devolve
uma `_Reserva`; a rota a usa como context manager, e o que foi reservado e não
consumido volta na saída (quick 260911-lib, decisão (A) do achado A-07 — sem
isso, o caminho de cache produzia um "Cota do dia da aba Opções esgotada"
falso, com `usado: 0` no mesmo corpo da resposta).

Fase 1 entregou `GET /status`. A Fase 2 (quick 260910-biz) acrescenta
`GET /leitura/{ticker}` e `GET /setups/{name}/grafico`. Cadeia, proposta,
possibilidades, veredito e criação de setups são as Fases 3–5 do
`docs/PLANO-aba-opcoes.md`.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException

from . import ai_activity, audit, db, llm, mcp_client, metering, obslog, pregao

router = APIRouter(prefix="/api/options/mcp", tags=["options-mcp"])

# Fuso local ao módulo, mesmo padrão de `store.py`/`brapi.py`/`obslog.py`: o
# Brasil não tem horário de verão desde 2019, e não existe módulo
# compartilhado de fuso no repo. O container do Railway roda em UTC — sem
# isto, o dia do cap viraria 3 h antes do reset do serviço.
BRT = timezone(timedelta(hours=-3))

# Texto do contrato, literal. O que o usuário lê tem de ser o mesmo horário
# que o serviço de fato usa para zerar o contador dele.
RESET_TXT = "00:00 America/Sao_Paulo"

# Seções PRÓPRIAS de kv. `mcpUsageMonth` separado de `aiUsageMonth` não é
# arrumação: sem ele, uma sessão na aba Opções queimaria o balde mensal de
# análises do plano comercial do usuário (ADR-010) a cada chamada de tool.
SECTION = "mcpUsage"
GLOBAL_SECTION = "mcpUsageGlobal"
MONTH_SECTION = "mcpUsageMonth"

FONTE = "mcp.semente.dev"
CLASSE_CRITICA = "negociacao_b3"
EM_DIA = "em_dia"

# F5. A permissão é a do grupo `opcoes` do ADR-013; a entidade é o que
# `audit.record` grava e o que `rbac.ENTIDADES_POR_PERMISSAO` publica ao
# admin. Os dois nomes ficam aqui para que a rota, o teste e o mapa do RBAC
# citem a MESMA string — divergir faria a auditoria existir e ninguém a ver.
PERM_CRIAR_SETUP = "opcoes.criar_setup"
ENTIDADE_AUDITORIA = "opcoes_setup"

# Corpo do 503 de fiação ausente. Constante porque `require_user` e
# `require_criar_setup` respondem a MESMA coisa pelo mesmo motivo (o router
# não foi fiado no boot), e duas cópias divergiriam na primeira correção.
_NAO_CONFIGURADO = {
    "code": "mcp_nao_configurado",
    "message": "Serviço de opções não configurado no servidor.",
    "action": "O router não foi fiado no boot (options_mcp_api.configure).",
}

# Avisos de frescor, extraídos para constante na F2 (quick 260910-biz): eram
# literal inline dentro de `_frescor`, sem cobertura do guardião imperativo.
# Os dois dizem "não medido" com a razão do não-medido — e nenhum dos dois
# pode ser suprimido na UI, porque "não medido" que vira silêncio é lido
# como "em dia" (ADR-027, Decisão 8).
AVISO_FRESCOR_NAO_MEDIDO = (
    "frescor não medido: a classe negociacao_b3 não veio na resposta"
)
AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA = (
    "frescor não medido nesta leitura: nenhum setup deste ticker foi avaliado"
)
# F3: `find_tradable_options`, `propose_option_setups` e
# `evaluate_option_structure` NÃO anexam `data_freshness` à resposta. O texto
# diz onde a medição ESTÁ, em vez de calar: a tela combina este envelope com o
# do `/status` (que mede) e prefere o medido. Silenciar aqui faria "não
# medido" passar por "em dia", que é o erro que a Decisão 8 do ADR-027 existe
# para impedir.
AVISO_FRESCOR_SEM_ANEXO = (
    "frescor não medido nesta consulta: esta chamada não traz o carimbo de "
    "idade do dado; o estado medido está no cabeçalho da aba"
)
# Único motivo que esta camada escreve por conta própria, e só porque não há
# resposta do serviço para citar: quando nenhum vencimento foi escolhido, não
# houve segunda chamada e portanto não existe `reason` verbatim. Todo o resto
# do "por que não montou" vem do serviço ([R-15]).
MOTIVO_SEM_VENCIMENTO = (
    "nenhum vencimento para montar: a cadeia deste ativo não trouxe vencimento "
    "que atenda ao pedido"
)

# F5 — frescor BLOQUEANTE da escrita de setup (ADR-027, Decisão 8). Os dois
# textos separam o que a tela não pode confundir: dado medido e atrasado é
# diferente de dado que ninguém mediu. Gravar um vigia sobre qualquer um dos
# dois seria fabricar confiança.
AVISO_DADO_ATRASADO = (
    "o dado de negociação da B3 está atrasado: um setup criado agora vigiaria "
    "um pregão que já passou"
)
AVISO_DADO_NAO_MEDIDO = (
    "a idade do dado de negociação da B3 não foi medida nesta consulta: sem a "
    "medição não dá para afirmar que o setup vigiaria o pregão certo"
)
# F5 — os DOIS 402 do gate de análise, com texto PRÓPRIO da aba. O copy do
# `metering` fala de BYOK e mandaria a pessoa configurar uma chave que não
# resolve nada aqui (§3.2 do PLANO) — mesma razão pela qual `_cap_check`
# descarta o `_motivo` que recebe.
AVISO_PLANO_ANALISES = (
    "as análises com IA do seu plano acabaram neste mês; ler a cadeia, os "
    "operáveis e os setups já gravados continua liberado"
)
AVISO_IA_GERENCIADA = (
    "a IA do app atingiu o limite de análises de hoje; o contador zera na "
    "virada do dia"
)
# 24-06 (F-02) — falha de TRANSPORTE do provedor de LLM. "nada foi gravado" é
# a informação que o 500 de hoje não dava e a única que a pessoa precisa: a
# compilação é dry-run (`confirm=false`), então a falha é inócua. Sem essa
# frase ela fica sem saber se um setup foi parar no armazém compartilhado e
# tenta de novo por medo.
AVISO_IA_INDISPONIVEL = (
    "O modelo de IA não respondeu agora. Tente de novo em alguns minutos — "
    "nada foi gravado."
)

# 24-06 (F-01) — os quatro motivos de a razão ganho/perda NÃO existir. Cada um
# diz QUAL caso é, porque os quatro são diferentes para quem decide: "sem
# teto" é a melhor notícia possível, "sem piso" é a pior, "não veio o dado" é
# ignorância do app e "perda máxima zero" é estrutura sem risco declarado. Um
# `null` mudo no lugar de qualquer um deles devolveria a tela ao estado que o
# achado F-01 descreve — a pessoa faz a conta de cabeça e erra o caso.
RAZAO_GANHO_ILIMITADO = (
    "razão ganho/perda indefinida: o serviço declarou ganho sem teto, e não "
    "existe quanto vezes o ilimitado cabe na perda"
)
RAZAO_PERDA_ILIMITADA = (
    "razão ganho/perda indefinida: o serviço declarou perda sem piso, e "
    "dividir por uma perda sem limite não produz número que signifique algo"
)
RAZAO_SEM_DADO = (
    "razão ganho/perda indefinida: o serviço não trouxe ganho máximo e perda "
    "máxima como número nesta resposta"
)
RAZAO_PERDA_ZERO = (
    "razão ganho/perda indefinida: não há perda máxima para comparar, e "
    "dividir por zero é o número que mais engana numa tela de risco"
)

# 24-07 (F-04) — a recusa de tool passou a DEBITAR 1 do cap (decisão do Alex
# em 2026-09-11: cobrar a viagem). Cobrar sem dizer que cobrou é a metade do
# defeito que o usuário enxerga: a cota dele cai e a tela mostra só "o serviço
# recusou". Esta frase é o que falta para a conta dele fechar.
AVISO_RECUSA_COBRADA = (
    "Esta tentativa consumiu uma chamada da sua cota do dia: o serviço cobra "
    "a consulta mesmo quando recusa o pedido."
)

# 24-11 (achado ao vivo 2026-09-11) — os três motivos de um campo da LEITURA
# DO ATIVO vir vazio. Na tela do Alex, `Tendência`, `HV 21`, `HV 63`,
# `Distância da média 63` e `Faixa de 63 pregões` mostravam travessão e mais
# nada: quem olha não sabe se o app quebrou, se o ativo é estranho ou se falta
# dado — e travessão mudo não é estado vazio (princípio 9 do CLAUDE.md).
#
# A saída NÃO é preencher: o número não existe na origem, e inventá-lo seria
# fabricar (princípio 4). Nem recalcular: o Boris teria uma segunda
# implementação do mesmo indicador, que diverge da do serviço na primeira
# correção feita de um lado só (decisão do Alex, 2026-09-11: fonte única).
# Resta dizer o motivo, e é o que estes três fazem — cada um diz O QUE falta,
# POR QUE falta e que ninguém estimou nada no lugar. Nenhum culpa quem lê nem
# sugere ação que não existe: "tente de novo" não encurta uma série de pregões.
#
# O "63" e o "21" que aparecem no texto são as JANELAS que o próprio serviço
# nomeia nos campos (`sma63`, `range_63_sessions`, `change_21_sessions_pct`) —
# NÃO uma contagem da série. O `behavior` não traz quantos candles existem, e
# afirmar esse número seria inventá-lo; o guardião do 24-11 tranca essa
# diferença nos dois sentidos.
MOTIVO_JANELA_63 = (
    "exigem 63 pregões e a série disponível não fecha essa janela — a de 21 "
    "fecha, por isso os campos de 21 vieram"
)
MOTIVO_SERIE_CURTA = (
    "a série de pregões é curta demais para as médias; só o que não depende "
    "de janela veio"
)
MOTIVO_HV_AUSENTE = (
    "o provedor não publica volatilidade realizada para este ativo; ela não é "
    "calculada aqui, por isso não há número a mostrar"
)

# 24-14 (achado ao vivo 2026-09-11) — o ensaio que não testou nada. O 24-11
# tratou o campo VAZIO; este trata o caso pior, que é o número PLAUSÍVEL:
# `disparos: 0` com `pregoes_avaliaveis: 31` se lê como "testei e não
# disparou", quando a verdade é "nunca pôde disparar".
#
# Os três textos dizem só o que a aritmética de janela demonstra. Nenhum
# afirma que o setup dispararia com mais histórico (previsão), que o setup é
# ruim (juízo) nem manda mudar o período (ação que a tela não oferece) — quem
# extrapola aqui só troca a primeira leitura errada por uma segunda.
MOTIVO_JANELA_NUNCA_FECHOU = (
    "esta condição precisa de mais pregões do que o histórico do ensaio tem, "
    "então ela não teve valor em nenhum dia — não é que não tenha ocorrido, "
    "é que não deu para verificar"
)
MOTIVO_JANELA_CURTA_PARA_SEQUENCIA = (
    "esta condição só passou a ter valor nos últimos pregões do histórico, em "
    "quantidade menor que a sequência de dias seguidos que o setup exige — a "
    "sequência não teve como se formar"
)
AVISO_ENSAIO_INDISPARAVEL = (
    "Este ensaio não testou o setup: uma das condições nunca pôde ser "
    "verificada no histórico disponível, e por isso o número de disparos é "
    "zero por construção — não por raridade."
)

# `AVISOS` é a superfície de varredura do módulo no `test_guardrail_imperativo`
# (FONTES) — não só os avisos de frescor. Texto fixo novo que chega ao usuário
# entra aqui na fase que o cria.
AVISOS = "\n".join((AVISO_FRESCOR_NAO_MEDIDO,
                    AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA,
                    AVISO_FRESCOR_SEM_ANEXO,
                    MOTIVO_SEM_VENCIMENTO,
                    AVISO_DADO_ATRASADO,
                    AVISO_DADO_NAO_MEDIDO,
                    AVISO_PLANO_ANALISES,
                    AVISO_IA_GERENCIADA,
                    AVISO_IA_INDISPONIVEL,
                    RAZAO_GANHO_ILIMITADO,
                    RAZAO_PERDA_ILIMITADA,
                    RAZAO_SEM_DADO,
                    RAZAO_PERDA_ZERO,
                    AVISO_RECUSA_COBRADA,
                    MOTIVO_JANELA_63,
                    MOTIVO_SERIE_CURTA,
                    MOTIVO_HV_AUSENTE,
                    MOTIVO_JANELA_NUNCA_FECHOU,
                    MOTIVO_JANELA_CURTA_PARA_SEQUENCIA,
                    AVISO_ENSAIO_INDISPARAVEL))

# Critério de "operável" do BORIS, não do serviço (D-24.4). O serviço aceita
# qualquer peneira; estes três números são escolha nossa, e por isso viajam na
# resposta em `criterioAplicado` — número escondido vira "a peneira sumiu com
# o meu strike" sem ninguém conseguir explicar por quê.
OPERAVEIS_MIN_NEGOCIOS = 100
OPERAVEIS_DELTA_MIN = 0.25
OPERAVEIS_DELTA_MAX = 0.55

# `kind` e `direction` aceitos. Valor fora da lista é 422 ANTES da rede: o
# serviço recusaria de qualquer jeito, e a viagem já teria custado uma
# chamada do teto compartilhado.
TIPOS_DE_OPCAO = ("CALL", "PUT")
DIRECOES = ("bullish", "bearish", "neutral")

# `limit` da cadeia. Teto de 200 porque pedir mais multiplica o payload sem
# multiplicar a informação — a cadeia inteira de um vencimento raramente
# passa disso, e o `truncated` do serviço diz como pedir o resto.
LIMITE_MIN = 1
LIMITE_MAX = 200

# [R-13]: o custo de `/possibilidades` é 2×N+1 e cresce linear com o número de
# vencimentos. 6 é o teto que cabe no cap de 60/dia sem que UMA consulta
# consuma a sessão inteira da pessoa.
N_MAX_VENCIMENTOS = 6

# Campos da estrutura que viajam VERBATIM do serviço para a tela. Lista
# explícita, e não `**avaliacao`, porque o envelope da rota (`pregao`,
# `fonte`, `at`, `cap`) não pode ser sobrescrito por um campo homônimo que o
# serviço venha a acrescentar.
CHAVES_DA_ESTRUTURA = (
    "kind", "name", "legs", "net_cost", "flow", "max_gain", "max_loss",
    "unlimited_gain", "unlimited_loss", "breakevens", "net_delta",
    "payoff", "scenarios", "sessions_to_nearest_expiry", "note",
)

# --------------------------------------------------------------------------
# F5 — criação de setup por descrição em português.
# --------------------------------------------------------------------------
TOOL_CREATE_SETUP = "create_setup"
TOOL_DEACTIVATE_SETUP = "deactivate_setup"
# Texto para HUMANOS do `create_setup`, publicado pelo serviço. Junto com o
# `inputSchema` de `tools/list`, é a SEGUNDA fonte do `system` do compilador.
URI_CREATE_SETUP = "mydata://tools/create_setup"

# Rótulo do ledger de atividade da IA (`ai_activity`), na forma dos irmãos
# ("Radar", "Análise", "Carteira") — o usuário precisa reconhecer de ONDE veio
# o custo quando olhar a lista.
TIPO_ATIVIDADE = "Opções · setup"

MAX_TOKENS_COMPILADOR = 1500
# Teto da descrição. Não é capricho: o texto vai inteiro para dentro de um
# prompt pago (a chave do servidor, no caminho gerenciado), e sem limite uma
# colagem de 200 KB viraria uma conta que ninguém pediu. 2.000 caracteres é
# muito mais do que qualquer descrição de setup real.
DESCRICAO_MAX = 2000

# Forma MÍNIMA do objeto que a LLM devolve. É só FORMA: quem valida a
# semântica (indicador existe? operador é aceito? janela é possível?) é o
# próprio serviço, em `create_setup(confirm=false)`. Duplicar aqui a régua
# semântica seria portar a DSL para dentro do Boris — o que o ENG-06 proíbe.
CAMPOS_OBRIGATORIOS_DO_SETUP = ("name", "ticker", "description", "conditions")

# Instrução FIXA do Boris ao compilador. É deliberadamente curta e sem
# vocabulário de setup: os campos, indicadores, operadores e padrões chegam
# ao modelo pelo `inputSchema` vivo e pelo texto do resource, montados em
# runtime (`_system_compilador`). Uma lista aqui envelheceria em silêncio no
# dia em que o serviço acrescentasse um indicador — e é exatamente a cópia
# que o ENG-06 proíbe.
#
# Texto fixo que vira instrução de sistema numa LLM cujo resultado a pessoa
# GRAVA: entra em `FONTES` do `test_guardrail_imperativo` por isso (imperativo
# de pressão aqui contaminaria o que ela grava), e não em `AVISOS`, que é a
# superfície do que a tela EXIBE.
SYSTEM_COMPILADOR_CABECALHO = "\n".join((
    "Você traduz a descrição que uma pessoa escreveu em português para o "
    "objeto de setup técnico especificado abaixo.",
    "",
    "Regras, todas obrigatórias:",
    "- Use SOMENTE os campos e os valores que a especificação abaixo declara. "
    "O que não estiver nela não existe: nada de campo, nome ou valor inventado.",
    "- Não reescreva a descrição da pessoa: o campo de descrição recebe o "
    "texto dela.",
    "- O que a descrição não disser fica de fora. Não complete com um valor "
    "provável nem com um padrão seu.",
    "- Responda SÓ o objeto JSON, sem cerca de código, sem comentário e sem "
    "texto antes ou depois.",
    # Medido com LLM real em 2026-09-11: sem esta linha o modelo respondia
    # `{\"setup\": {...}}`, que é a forma que a especificação abaixo (o schema
    # da FERRAMENTA) de fato descreve. Ele seguia o schema; faltava dizer que
    # queremos só o miolo dele.
    "- Responda o objeto de setup em si, com os campos no nível de cima. Não "
    "o embrulhe em nenhum outro objeto, nem repita o nome da ferramenta em "
    "volta dele.",
    "",
    "Contexto: isto é um simulador educacional. O objeto vira um vigia que "
    "avisa quando a condição descrita ocorre no pregão; nada é enviado ao "
    "mercado, e quem decide o que fazer com o aviso é a pessoa.",
))


_conn = None
_require_user = None
_require_permission = None
_gate_analise = None
_config_do_usuario = None
# 25-04: a conciliação "limite do plano → override global → env → default".
# Nasce em `main.py` (depende de `plan` + `_plano_do_escopo`) e chega por
# injeção, como as três acima. Sem ela, os tetos desta aba resolvem
# EXATAMENTE como resolviam antes — é a degradação certa, não uma falha.
_limite_do_plano = None


def configure(conn, require_user_dep, *, require_permission_dep=None,
              gate_analise=None, config_do_usuario=None,
              limite_do_plano=None) -> None:
    """Injeção pelo mesmo padrão de `candle_cache.configure_db` /
    `setups.set_historico_provider`: `main.py` importa este módulo e entrega
    a conexão e a dependency de sessão. O inverso (este módulo importar
    `main`) seria import circular — `require_user` e `_conn` nascem lá.

    Os três extras nascem na F5 (D-24.5) e são a fiação de LLM que a Fase 4
    do PLANO traria; pela MESMA razão de `require_user`, todos moram em
    `main.py`:

    · `require_permission_dep` — a factory `require_permission(perm)`;
    · `gate_analise` — `_gate_analise(scope, config)`, o ponto ÚNICO de gate
      de análise (plano mensal + IA gerenciada), que devolve
      `(config_efetiva, consume)`;
    · `config_do_usuario` — `lambda uid: store.get(conn, "config", user_id=uid)`.

    O quarto nasce no 25-04, pela MESMA razão:

    · `limite_do_plano` — `_limite_do_plano(scope, chave, global_fn)`, a
      conciliação entre o limite do PLANO da conta e o override GLOBAL que
      esta aba já aplica. Ausente, `_cota_usuario` resolve como sempre
      resolveu (kv global → env → default): degradação, não falha.

    São KEYWORD e OPCIONAIS de propósito: `configure(conn, require_user)`
    continua válido, e nenhum chamador (teste inclusive) precisa mudar. Sem
    eles as rotas de ESCRITA falham FECHADO (503) — ver `require_criar_setup`.
    """
    global _conn, _require_user, _require_permission, _gate_analise, _config_do_usuario
    global _limite_do_plano
    _conn = conn
    # 24-15: os tetos vindos do kv são cache de PROCESSO, e este é o ponto em
    # que o processo passa a falar com outro banco (é o que a suíte faz a cada
    # cliente novo). Sem esta linha, o teto configurado num teste valeria como
    # teto do seguinte, que roda contra um banco vazio.
    reset_limites_cache()
    _require_user = require_user_dep
    _require_permission = require_permission_dep
    _gate_analise = gate_analise
    _config_do_usuario = config_do_usuario
    _limite_do_plano = limite_do_plano


def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """Delegação ao `require_user` de `main.py`, injetado por `configure()`.

    O nome é o mesmo de propósito, e por dois motivos que apontam para o
    mesmo lugar: (a) é literalmente a MESMA checagem de sessão, e (b) é o
    nome que `test_adr013_cobertura_rotas` reconhece como gate de identidade
    — chamar de outra coisa faria a rota parecer "sem gate" para o guardião
    e obrigaria a mexer na allowlist pública, que é exatamente o que não
    pode acontecer numa rota autenticada."""
    if _require_user is None:
        raise HTTPException(503, _NAO_CONFIGURADO)
    return _require_user(authorization)


def require_criar_setup(user: dict = Depends(require_user)) -> dict:
    """Sessão + a permissão `opcoes.criar_setup` (ADR-013, grupo `opcoes`).

    **Por que `Depends(require_user)` e não o header cru**: o guardião (iv)
    de `test_mcp_guardioes` exige `require_user` nas dependências de TODA
    rota `/api/options/mcp/*`, e o `test_adr013_cobertura_rotas` reconhece o
    mesmo nome como gate de identidade. Recebendo o `user` já resolvido, a
    árvore de dependências da rota carrega os DOIS nomes — sessão e permissão
    — em vez de esconder a primeira dentro desta função.

    **Por que 503 sem a fiação, e nunca um 200 permissivo:** esta é rota de
    ESCRITA num armazém de setups SEM DONO (ADR-027, Decisão 7) — quem grava,
    grava para todos os clientes do serviço. Falhar ABERTO aqui seria pior do
    que não ter a rota: a recusa tem de ser do backend, não de um botão
    escondido na tela.
    """
    if _require_permission is None:
        raise HTTPException(503, _NAO_CONFIGURADO)
    # A factory devolve a dependency de `main.py` (`_dep`), que faz
    # `ensure_bootstrap_role` e levanta 403 nomeando a permissão. Chamá-la com
    # o `user` já resolvido é o que evita resolver a sessão duas vezes.
    return _require_permission(PERM_CRIAR_SETUP)(user)


# --------------------------------------------------------------------------
# Os três tetos da aba: memória → kv → env → default.
#
# 24-15 (pedido do Alex, 2026-09-11). Antes eles eram SÓ env do Railway, e
# mexer neles exigia redeploy — lento demais para o que controlam, ainda mais
# depois de a Fase 24 multiplicar o consumo por sessão (`/possibilidades`
# custa até 13 `tools/call`). O kv entra NA FRENTE da env; a env **continua
# valendo** quando não há valor no kv, e é lida A CADA leitura de propósito:
# é assim que o Railway troca um teto sem publicar código, e é o que
# `monkeypatch.setenv` exercita na suíte.
#
# Padrão copiado de `brapi_budget.spot_intervalo_s`/`set_spot_intervalo` — o
# precedente da casa para "configuração que sobrevive a deploy", incluindo o
# `try/except` que engole falha de kv (um banco indisponível degrada para a
# camada de baixo; nunca derruba a rota).
#
# Valor torto em qualquer camada cai para a seguinte. Isso não é
# permissividade: um `0` vindo do banco não seria "limite baixo", seria o
# freio DESLIGADO em cima de um teto de 2.000 chamadas/dia compartilhado por
# toda a base do Boris.
# --------------------------------------------------------------------------
COTA_USUARIO_DIA_DEFAULT = 60
RATE_MIN_DEFAULT = 20
COTA_GLOBAL_DIA_DEFAULT = 1800

_KV_COTA_USUARIO = "mcpCotaUsuarioDia"
_KV_RATE_MIN = "mcpRateMin"
_KV_COTA_GLOBAL = "mcpCotaGlobalDia"

# Contrato do serviço (ADR-027, "Contra (aceito)"): 2.000 `tools/call` por dia
# para TODOS os usuários do Boris somados. Não é configuração daqui — é o
# número que dá sentido aos três de cima, e a razão de o painel avisar quando
# alguém configura acima dele.
TETO_SERVICO_DIA = 2000

# Entidade do audit log da escrita destes tetos. Fica aqui, junto do que ela
# descreve, pelo MESMO motivo de `ENTIDADE_AUDITORIA`: a rota, o teste e
# `rbac.ENTIDADES_POR_PERMISSAO` precisam citar a mesma string, e duas cópias
# fariam a auditoria existir sem ninguém a ver.
ENTIDADE_COTA = "mcp_cota"

# Cache em memória do valor vindo do KV — e só dele.
#
# Por que existe: estes três são lidos no caminho de `_cap_check`, ou seja, a
# cada chamada de tool. Por que é seguro aqui: o valor muda por ação
# administrativa explícita (nunca por evento de mercado nem por virada de
# dia), e quem o muda é `set_*`, que roda no MESMO processo e invalida a
# entrada na hora. Por que NÃO cacheia a env nem o default: cachear a env
# mataria em silêncio a troca de teto sem redeploy — o custo de não cachear é
# um SELECT por chave primária no SQLite, a mesma classe do que o `metering`
# já faz várias vezes por requisição.
_limites_mem: dict = {}


def reset_limites_cache() -> None:
    """Esquece o que veio do kv. Chamado por `configure()` (processo fiado a
    outro banco) e pelos testes entre casos — sem isto, um `set_*` de um teste
    valeria como teto do seguinte, que roda contra outro banco."""
    _limites_mem.clear()


def _env_int(nome: str) -> Optional[int]:
    """Inteiro > 0 declarado na env, ou `None`. Texto, vazio, 0 e negativo
    devolvem `None` — a decisão cai para a camada de baixo."""
    bruto = os.environ.get(nome)
    if bruto is None:
        return None
    try:
        v = int(bruto)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def _int_env(nome: str, padrao: int) -> int:
    """Compatível byte a byte com o que existia antes deste plano (env vazia,
    torta, 0 ou negativa → `padrao`); hoje é a TERCEIRA camada, não a
    primeira."""
    v = _env_int(nome)
    return v if v is not None else padrao


def _kv_int(chave: str) -> Optional[int]:
    """Inteiro > 0 gravado no kv, ou `None`. `bool` é recusado de propósito
    (`True` é `int` em Python, e um `True` no banco viraria cota 1)."""
    if _conn is None:
        return None
    try:
        v = db.kv_get(_conn, chave, None, user_id=None)
    except Exception:  # noqa: BLE001 — banco indisponível degrada, não derruba
        return None
    if isinstance(v, bool) or not isinstance(v, int):
        return None
    return v if v > 0 else None


def _valor_e_origem(chave_kv: str, env: str, padrao: int) -> tuple:
    """O ÚNICO lugar que decide um teto vigente. `origem` é `"kv"`, `"env"` ou
    `"default"` — sem ela o admin muda pelo painel, a env continua diferente e
    ninguém sabe qual manda."""
    v = _limites_mem.get(chave_kv)
    if v is None:
        v = _kv_int(chave_kv)
        if v is not None:
            _limites_mem[chave_kv] = v
    if v is not None:
        return v, "kv"
    v = _env_int(env)
    if v is not None:
        return v, "env"
    return padrao, "default"


def _set_limite(chave_kv: str, n) -> int:
    """Persiste e invalida o cache. O mínimo de 1 é imposto AQUI, no código,
    não na UI — mesma decisão do `max(30, ...)` de `set_spot_intervalo`: a
    camada que menos se pode obrigar a lembrar é justamente a de cima."""
    v = max(1, int(n))
    _limites_mem[chave_kv] = v
    if _conn is not None:
        try:
            db.kv_set(_conn, chave_kv, v, user_id=None)
        except Exception:  # noqa: BLE001 — vale neste processo; some no deploy
            pass
    return v


def cota_usuario_dia() -> int:
    """O teto por usuário GLOBAL — o mesmo número para toda a base.

    25-04: virou a camada de BAIXO da conciliação. Quem tem plano com
    `opcoes_chamadas_dia` configurado é barrado pelo número do plano
    (`_cota_usuario`); quem não tem cai aqui, e este valor continua sendo o que
    o card `CotaOpcoes` do portal escreve e mostra. A função NÃO muda: é
    exatamente por não mudar que "sem configuração, nada muda" vale."""
    return _valor_e_origem(_KV_COTA_USUARIO, "B3_MCP_COTA_USUARIO_DIA",
                           COTA_USUARIO_DIA_DEFAULT)[0]


def set_cota_usuario_dia(n) -> int:
    return _set_limite(_KV_COTA_USUARIO, n)


def rate_min() -> int:
    return _valor_e_origem(_KV_RATE_MIN, "B3_MCP_RATE_MIN", RATE_MIN_DEFAULT)[0]


def set_rate_min(n) -> int:
    return _set_limite(_KV_RATE_MIN, n)


def cota_global_dia() -> int:
    return _valor_e_origem(_KV_COTA_GLOBAL, "B3_MCP_COTA_GLOBAL_DIA",
                           COTA_GLOBAL_DIA_DEFAULT)[0]


def set_cota_global_dia(n) -> int:
    return _set_limite(_KV_COTA_GLOBAL, n)


# Nome de cada teto → (chave de kv, env, default). Uma tupla só: a rota admin
# itera por ela em vez de repetir a lista de três em cada ponto.
LIMITES = (
    ("cotaUsuarioDia", _KV_COTA_USUARIO, "B3_MCP_COTA_USUARIO_DIA", COTA_USUARIO_DIA_DEFAULT),
    ("rateMin", _KV_RATE_MIN, "B3_MCP_RATE_MIN", RATE_MIN_DEFAULT),
    ("cotaGlobalDia", _KV_COTA_GLOBAL, "B3_MCP_COTA_GLOBAL_DIA", COTA_GLOBAL_DIA_DEFAULT),
)

# Os que se medem POR DIA e por isso se comparam com `TETO_SERVICO_DIA`.
# `rateMin` fica fora: é por MINUTO, e compará-lo com um teto diário seria
# erro de unidade travestido de aviso.
LIMITES_POR_DIA = ("cotaUsuarioDia", "cotaGlobalDia")


def limites() -> dict:
    """Os três tetos vigentes, cada um com a ORIGEM e a env que o declara,
    mais o teto do próprio serviço."""
    fora = {"tetoServicoDia": TETO_SERVICO_DIA}
    for nome, chave_kv, env, padrao in LIMITES:
        valor, origem = _valor_e_origem(chave_kv, env, padrao)
        fora[nome] = {"valor": valor, "origem": origem, "env": env, "default": padrao}
    return fora


def consumo_global_hoje() -> dict:
    """Consumo de HOJE do balde global da aba (`mcpUsageGlobal`), no dia de
    São Paulo. Mora aqui, e não na rota, porque a seção e a noção de dia são
    deste módulo — lidas de fora, divergiriam do que o cap de fato conta."""
    return metering.global_snapshot(
        _conn, cap=cota_global_dia(), section=GLOBAL_SECTION, _dia=_dia_sp())


# As três privadas que o `_cap_check` usa delegam nas públicas: um lugar só
# decide o valor vigente. Os nomes seguem porque são o vocabulário do cap (e
# o que a suíte já exercita).
def _cota_usuario(uid: Optional[str] = None) -> Optional[int]:
    """O teto por usuário VIGENTE para `uid`. 25-04: o limite do PLANO da conta
    vem na frente do teto global; sem plano configurado (ou sem a injeção do
    `main.py`), é `cota_usuario_dia()` — o número de sempre.

    Valor torto vindo do plano (tipo errado, negativo) é ignorado em vez de
    virar cap: o teto do serviço MCP é COMPARTILHADO por toda a base, e um
    número inválido aqui viraria o freio desligado — mesma disciplina do
    `_kv_int` logo acima."""
    if uid and _limite_do_plano is not None:
        try:
            v = _limite_do_plano(uid, "opcoes_chamadas_dia", cota_usuario_dia)
        except Exception:  # noqa: BLE001 — eixo comercial não derruba a aba
            v = None
        if v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
            return v
    return cota_usuario_dia()


def _rate_min() -> int:
    return rate_min()


def _cota_global() -> int:
    return cota_global_dia()


# --------------------------------------------------------------------------
# Dia/mês em São Paulo. `agora` só existe para o teste fixar o relógio sem
# monkeypatch de `datetime`.
# --------------------------------------------------------------------------
def _dia_sp(agora: Optional[datetime] = None) -> str:
    return (agora or datetime.now(timezone.utc)).astimezone(BRT).strftime("%Y-%m-%d")


def _mes_sp(agora: Optional[datetime] = None) -> str:
    return (agora or datetime.now(timezone.utc)).astimezone(BRT).strftime("%Y-%m")


# --------------------------------------------------------------------------
# Cap.
# --------------------------------------------------------------------------
class _Reserva:
    """Contabilidade de UMA reserva de cota dentro de uma rota: quanto foi
    reservado pelo `_cap_check`, quanto virou consumo confirmado, e o que
    sobrou — devolvido na saída, inclusive quando a rota levanta.

    **Por que existe** (quick 260911-lib, decisão (A) do achado A-07): a
    reserva atômica do `metering` protege de verdade, mas o que é reservado e
    NÃO consumido só voltava por expiração (`RESERVA_TTL_S`, 120 s). Nas rotas
    desta aba isso não é teórico — `/leitura` reserva 3 e consome 0 quando as
    três tools vêm do cache. Medido no worktree da correção, com a cota em 6:

        n  http  codigo     usado  reservado
        1  200   -              0          3
        2  200   -              0          6
        3  402   mcp_cota       0          6   <- "Cota do dia ... esgotada."

    A terceira leitura recusava com `usado: 0, limite: 6` — a resposta se
    contradizendo no mesmo corpo. Afirmação falsa ao usuário é a MESMA classe
    do A-08, corrigido no lote anterior; daí a devolução imediata.

    **Por que um objeto em vez de `try/finally` em cada rota:** são três rotas
    hoje e a quarta vem na Fase 3 do PLANO. Contabilidade manual espalhada
    divergiria justamente na que for escrita depois — e divergir para o lado
    de devolver a MAIS seria dar cota de graça, pior que o defeito original.

    Invariantes, em ordem de perigo:
    · **devolvido nunca excede reservado** — `saldo` desconta consumo E
      devolução anterior, e `devolver()` NÃO chama `metering.liberar` com
      saldo zero (`liberar` normaliza `custo` para no mínimo 1: chamá-la com
      0 devolveria uma unidade que ninguém reservou);
    · **consumo real nunca é escondido** — `consome()` sempre passa ao
      `metering`, mesmo se a rota consumir mais do que reservou; nesse caso o
      saldo satura em 0 e nada é devolvido (consumir menos que o checado é
      permitido, o contrário nunca foi, e mascarar seria dar cota de graça);
    · **`liberar` nunca toca `count`** — devolver reserva não é gastar nem
      estornar gasto; quem conta é só o `consume`.
    """

    __slots__ = ("uid", "reservado", "consumido", "devolvido")

    def __init__(self, uid: str, reservado: int) -> None:
        self.uid = uid
        self.reservado = max(0, int(reservado or 0))
        self.consumido = 0
        self.devolvido = 0

    @property
    def saldo(self) -> int:
        """Unidades reservadas que ainda não viraram consumo nem voltaram."""
        return max(0, self.reservado - self.consumido - self.devolvido)

    def consome(self, custo: int = 1) -> None:
        custo = int(custo or 0)
        if custo <= 0:
            return
        _cap_consume(self.uid, custo)
        self.consumido += custo

    def devolver(self) -> int:
        """Devolve o saldo ao balde de reservas. Idempotente: chamar duas
        vezes (saída do `with` depois de uma devolução explícita) não devolve
        nada na segunda."""
        saldo = self.saldo
        if saldo <= 0:
            return 0
        metering.liberar(
            _conn, self.uid, custo=saldo,
            section=SECTION, global_section=GLOBAL_SECTION, _dia=_dia_sp(),
        )
        self.devolvido += saldo
        return saldo

    def __enter__(self) -> "_Reserva":
        return self

    def __exit__(self, *_exc) -> bool:
        self.devolver()
        return False    # nunca engole a exceção da rota


def _cap_check(uid: str, custo: int) -> _Reserva:
    """Recusa ANTES de chamar o serviço — o teto de 2.000/dia é compartilhado
    por toda a base do Boris, e uma chamada recusada pelo serviço já teria
    custado a viagem.

    Devolve a `_Reserva` do que foi reservado, para a rota usar como context
    manager: `with _cap_check(uid, 3) as cap:`. Quando a cota está cheia isto
    LEVANTA — nada foi reservado e, por construção do `with`, nada é devolvido.
    Usar sem o `with` volta ao comportamento antigo (devolução só por
    expiração); é o que o guardião de `test_mcp_cap.py` impede."""
    if custo <= 0:
        return _Reserva(uid, 0)
    dia = _dia_sp()
    # 25-04: só `quota` (o teto POR USUÁRIO) passa a conhecer o plano da conta.
    # `rate_per_min` é freio contra flood e `cap_global` é o teto do SERVIÇO,
    # compartilhado por toda a base do Boris (2.000 `tools/call`/dia, ADR-027):
    # deixá-los variar por plano não criaria capacidade nenhuma — transferiria
    # a recusa para outro usuário, com uma mensagem que não explica isso.
    ok, _motivo = metering.check(
        _conn, uid,
        quota=_cota_usuario(uid), rate_per_min=_rate_min(), custo=custo,
        cap_global=_cota_global(),
        section=SECTION, global_section=GLOBAL_SECTION, _dia=dia,
    )
    if ok:
        return _Reserva(uid, custo)
    # O `_motivo` do metering é DESCARTADO de propósito: o texto dele fala de
    # BYOK e de "análises com a IA do app", que não é o que aconteceu aqui.
    # Mandar esse copy na aba Opções mandaria o usuário configurar uma chave
    # de LLM que não resolveria nada (§3.2 do PLANO).
    raise HTTPException(402, {
        "code": "mcp_cota",
        "message": "Cota do dia da aba Opções esgotada.",
        "usado": metering.used(_conn, uid, section=SECTION, _dia=dia),
        "limite": _cota_usuario(uid),
        "reinicia": RESET_TXT,
    })


def _cap_consume(uid: str, custo: int) -> None:
    if custo <= 0:
        return
    metering.consume(
        _conn, uid, custo=custo,
        section=SECTION, global_section=GLOBAL_SECTION,
        month_section=MONTH_SECTION,
        _dia=_dia_sp(), _mes=_mes_sp(),
    )


# --------------------------------------------------------------------------
# Tradução de erro. NADA cai no handler 500.
# --------------------------------------------------------------------------
# 24-07 (F-04) — marca posta na exceção NO PONTO em que o débito acontece
# (`_chamada_com_cap`) e lida só aqui, na tradução. Não é enfeite: um
# `"cobrado": True` FIXO neste 422 mentiria, porque nem todo `McpErroDeTool`
# vem de uma `tools/call`. `_material_do_compilador` FABRICA um quando o
# serviço não publica o schema ou o texto de `create_setup`, e ali nenhuma
# viagem contável aconteceu (`tools/list` e `resources/read` são protocolo,
# grátis no teto do serviço e fora do cap). Afirmar um débito que não existe
# é o mesmo erro do F-04 invertido, e desta vez na tela da pessoa.
ATR_DEBITADO = "debitado_do_cap"


def _debitou_a_viagem(e: Exception) -> bool:
    """A recusa que chega à tradução já custou 1 do cap do usuário?"""
    return bool(getattr(e, ATR_DEBITADO, False))


def _bloco_cobrado(e: Exception) -> dict:
    """Os dois campos que contam ao usuário o que a recusa custou. Sai VAZIO
    quando não houve débito — a ausência do campo é a forma de não afirmar."""
    if not _debitou_a_viagem(e):
        return {}
    return {"cobrado": True, "nota": AVISO_RECUSA_COBRADA}


def _erro_http(e: Exception) -> HTTPException:
    if isinstance(e, mcp_client.McpNaoConfigurado) or isinstance(e, ValueError):
        # ValueError aqui só vem de `mcp_client.url()` com `MCP_URL` de
        # esquema inválido — é estado de configuração do servidor, mesma
        # classe de "falta credencial", e não pode virar 500 opaco.
        return HTTPException(503, {
            "code": "mcp_nao_configurado",
            "message": "Serviço de opções não configurado no servidor.",
            "action": "Defina MCP_CLIENT_ID e MCP_CLIENT_SECRET no Railway.",
        })
    if isinstance(e, mcp_client.McpTetoAtingido):
        return HTTPException(402, {
            "code": "mcp_teto_servico",
            "message": "O serviço de opções atingiu o teto de chamadas do dia.",
            "reinicia": e.data.get("reinicia"),
            "escopo": e.data.get("escopo"),
        })
    if isinstance(e, mcp_client.McpErroDeTool):
        return HTTPException(422, {
            "code": "mcp_erro_de_tool",
            "message": str(e),
            "available": e.available,
            "hint": e.hint,
            # `cobrado`/`nota` só quando a recusa de fato debitou (F-04).
            **_bloco_cobrado(e),
        })
    # McpNaoAutorizado e McpIndisponivel caem juntos, e o texto NÃO tem
    # número nem nome de credencial: para o usuário final os dois são "não
    # deu agora". O detalhe (que separa "credencial recusada" de "serviço
    # fora do ar") vai só para o obslog, onde o Alex enxerga.
    return HTTPException(503, {
        "code": "mcp_indisponivel",
        "message": "O serviço de opções não respondeu agora. Tente de novo em alguns minutos.",
    })


# --------------------------------------------------------------------------
# Frescor. Tolerante à FORMA: a resposta real de `check_data_freshness` só se
# confirma ao vivo (`test_mcp_vivo.py`), e adivinhar campo seria inventar
# dado. Por isso o `bruto` volta inteiro — a Fase 2 lê a forma real dali sem
# gastar outra chamada.
# --------------------------------------------------------------------------
_CHAVES_COLECAO = ("classes", "class_status", "dados", "status")
_CHAVES_NOME = ("classe", "class", "nome", "name")
_CHAVES_SITUACAO = ("situacao", "status", "estado", "situation")


def _situacao_de(info) -> Optional[str]:
    if isinstance(info, str):
        return info
    if isinstance(info, dict):
        for chave in _CHAVES_SITUACAO:
            v = info.get(chave)
            if isinstance(v, str):
                return v
    return None


def _colecao_de(sc: Optional[dict]):
    for chave in _CHAVES_COLECAO:
        v = (sc or {}).get(chave)
        if isinstance(v, (list, dict)) and v:
            return v
    return None


def _normaliza_classes(colecao) -> list:
    itens = []
    if isinstance(colecao, dict):
        for nome, info in colecao.items():
            itens.append({"classe": str(nome), "situacao": _situacao_de(info), "bruto": info})
    elif isinstance(colecao, list):
        for item in colecao:
            nome = None
            if isinstance(item, dict):
                for chave in _CHAVES_NOME:
                    if item.get(chave):
                        nome = item[chave]
                        break
            itens.append({
                "classe": str(nome) if nome else None,
                "situacao": _situacao_de(item),
                "bruto": item,
            })
    return itens


def _frescor(sc: Optional[dict], erro: Optional[str]) -> dict:
    sc = sc if isinstance(sc, dict) else None
    classes = _normaliza_classes(_colecao_de(sc))
    stale = [c for c in classes if c.get("situacao") != EM_DIA]
    critica = next((c for c in classes if c.get("classe") == CLASSE_CRITICA), None)

    warning = erro or (sc or {}).get("warning")
    if not warning and critica is None:
        # "não medido" NUNCA pode passar por "em dia" (ADR-027, Decisão 8).
        warning = AVISO_FRESCOR_NAO_MEDIDO
    bloqueia = bool(warning) or (critica is not None and critica.get("situacao") != EM_DIA)

    return {
        "classes": classes,
        "stale": stale,
        "warning": warning or None,
        "bloqueia": bool(bloqueia),
        # `medido` (F2, aditiva): a UI precisa separar TRÊS estados — em dia,
        # atrasado com idade real, e não medido. Sem esta chave a tela teria
        # de deduzir "não medido" raspando o texto do `warning`, e um dia o
        # texto muda e a tela passa a afirmar "em dia" por default. Verdadeira
        # só quando a classe crítica veio E nenhum erro de tool atrapalhou.
        "medido": bool(critica is not None and not erro),
        "bruto": sc,
    }


def _frescor_do_anexo(dados) -> Optional[dict]:
    """Frescor a partir do `data_freshness` que a tool ANEXOU à resposta.

    `None` quando a resposta não traz o anexo — e `None` aqui é "não veio",
    que o chamador converte em "não medido" (`_frescor_nao_medido`), nunca em
    "em dia".

    Extraída de `_frescor_da_avaliacao` na F3, que passou a delegar: duas
    tools anexam a MESMA estrutura (`evaluate_setups` e `get_option_chain`),
    e duas leituras independentes dela divergiriam na primeira mudança de
    contrato. Devolve as mesmas chaves de `_frescor` porque o front tem UM
    renderizador de frescor, não três.
    """
    dados = dados if isinstance(dados, dict) else {}
    df = dados.get("data_freshness")
    if not (isinstance(df, dict) and df):
        return None

    situacao = df.get("quotes")
    situacao = situacao if isinstance(situacao, str) else "desconhecido"
    idade = df.get("quotes_age_hours")
    # `bool` é subclasse de `int`: sem a recusa explícita, um `True` viraria
    # "1 hora" na tela — número inventado a partir de um dado que não é
    # número (mesma régua de `_numero` em `opcoes_payoff.py`).
    idade_ok = isinstance(idade, (int, float)) and not isinstance(idade, bool)
    aviso = df.get("warning")
    aviso = aviso if isinstance(aviso, str) and aviso else None

    classe = {
        "classe": CLASSE_CRITICA,
        "situacao": situacao,
        # idade real quando o serviço mandou; `None` quando não mandou —
        # nunca 0, que a tela leria como "acabou de atualizar".
        "idadeHoras": idade if idade_ok else None,
        "bruto": df,
    }
    classes = [classe]
    return {
        "classes": classes,
        "stale": [c for c in classes if c.get("situacao") != EM_DIA],
        # O `warning` do anexo é do PRÓPRIO serviço sobre o dado dele —
        # quando vem, bloqueia: quem mediu é quem sabe dizer que não dá.
        "warning": aviso,
        "bloqueia": bool(aviso) or situacao != EM_DIA,
        "medido": situacao != "desconhecido",
        "bruto": df,
    }


def _frescor_nao_medido(motivo: str) -> dict:
    """O outro lado de `_frescor_do_anexo`: a tool NÃO carimba idade de dado.

    `medido: False` e `bloqueia: True` porque ausência de medição não é
    medição favorável (ADR-027, Decisão 8). A tela combina este envelope com
    o do `/status` e mostra o medido quando existir.
    """
    return {"classes": [], "stale": [], "warning": motivo,
            "bloqueia": True, "medido": False, "bruto": None}


def _frescor_da_avaliacao(evaluate_dados: Optional[dict], chamou_evaluate: bool) -> dict:
    """Frescor do `/leitura` derivado do que `evaluate_setups` JÁ devolveu.

    **Por que não há `check_data_freshness` aqui:** o custo declarado da rota
    no ADR-027 §3.3 é **3**, e `_cap_check(uid, 3)` é a promessa que o
    usuário paga. Uma quarta chamada faria o cap prometer menos do que o
    consumo real — o teto de 2.000/dia é compartilhado por toda a base, e
    subestimar o consumo é exatamente como ele estoura em silêncio. O frescor
    MEDIDO de verdade continua vindo do `/status` (cache 600 s), que a tela
    chama junto. E "não medido" nunca passa por "em dia" (ADR-027, Decisão 8):
    quando não há medição, `medido` é falso e `bloqueia` é verdadeiro.

    Devolve as MESMAS chaves de `_frescor` de propósito: o front tem UM
    renderizador de frescor, não dois que divergem com o tempo.
    """
    dados = evaluate_dados if isinstance(evaluate_dados, dict) else {}

    anexo = _frescor_do_anexo(dados)
    if anexo is not None:
        return anexo

    if chamou_evaluate and dados.get("status") == "nao_avaliado":
        # Gate de frescor do próprio serviço: o `reason` vai VERBATIM, sem
        # reescrita ([R-15] do PLANO). Quem explica o motivo é quem mediu.
        motivo = dados.get("reason")
        return {
            "classes": [],
            "stale": [],
            "warning": motivo if isinstance(motivo, str) and motivo else AVISO_FRESCOR_NAO_MEDIDO,
            "bloqueia": True,
            "medido": False,
            "bruto": dados,
        }

    return {
        "classes": [],
        "stale": [],
        "warning": (AVISO_FRESCOR_NAO_MEDIDO if chamou_evaluate
                    else AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA),
        "bloqueia": True,
        "medido": False,
        "bruto": None,
    }


# --------------------------------------------------------------------------
# Distância em pregões — a medição que o Boris faz, ao lado do veredito que o
# fornecedor assina.
# --------------------------------------------------------------------------
FONTE_DO_ATRASO = "calendario_b3"


def _atraso_em_pregoes(data_do_dado, _hoje=None) -> dict:
    """Quantos pregões separam o dado exibido do último pregão fechado.

    Existe porque o SLA da fonte e a pergunta do usuário são coisas
    diferentes. Medido em 2026-09-11: `negociacao_b3` com 49,58 h de idade
    contra um SLA de 96 h é `em_dia` pelo contrato do fornecedor, e ainda
    assim faltavam DOIS pregões na base — a tela dizia "dado em dia" sobre
    uma cotação de terça, numa sexta. Repassar o veredito de quem publica,
    em vez de medir a distância, é o que produz esse tipo de afirmação.

    **O dia corrente não entra na conta**, e isso não é conservadorismo: o
    COTAHIST de um pregão só sai depois do fechamento, então contar hoje
    faria o app acusar atraso todas as manhãs, sobre um dado que ainda não
    poderia existir.

    `pregoes: None` para data ausente, malformada ou no futuro — nunca 0,
    que afirmaria "está no último pregão" sem ter como saber.

    Quem conhece o calendário é `pregao.py` (fixos, móveis derivados da
    Páscoa, exceções por ofício e a env `B3_FERIADOS_EXTRA`) — fonte ÚNICA.
    Uma segunda contagem aqui divergiria dele em silêncio no primeiro
    Carnaval. `fonte` viaja no envelope para a tela poder dizer de onde saiu
    o número sem raspar texto.

    `_hoje` existe só para o teste fixar o relógio — mesmo padrão de
    `_dia_sp`. Teste que muda de resultado em novembro é pior que teste
    nenhum.
    """
    hoje = _hoje or datetime.now(timezone.utc).astimezone(BRT).date()
    envelope = {"pregoes": None, "referencia": hoje.isoformat(),
                "fonte": FONTE_DO_ATRASO}

    try:
        d = date.fromisoformat(data_do_dado)
    except (ValueError, TypeError):
        return envelope
    if d > hoje:
        # Dado carimbado no futuro é dado que não se sabe ler: qualquer
        # número aqui seria invenção, e 0 seria a invenção mais cara —
        # afirmaria que a tela está no último pregão fechado.
        return envelope

    # ESTRITAMENTE entre o dado e hoje: o próprio pregão do dado já está na
    # tela, e o de hoje ainda não foi publicado.
    dias = (hoje - d).days
    envelope["pregoes"] = sum(
        1 for n in range(1, dias) if pregao.is_trading_day(d + timedelta(days=n)))
    return envelope


# --------------------------------------------------------------------------
# Envelope comum e chamada com cap.
# --------------------------------------------------------------------------
def _agora_brt() -> str:
    return datetime.now(BRT).strftime("%d/%m/%Y %H:%M") + " BRT"


def _cap_bloco(uid: str) -> dict:
    return {
        "usado": metering.used(_conn, uid, section=SECTION, _dia=_dia_sp()),
        "limite": _cota_usuario(),
        "reinicia": RESET_TXT,
    }


async def _chamada_com_cap(cap: _Reserva, nome: str, args: dict) -> tuple:
    """Uma chamada de tool + o consumo de 1 do cap. Devolve `(dados, cache)`.

    O critério é literal, e é UM só: **tocou a rede, debitou.**

    · **acerto de cache não consome** — o custo que o cap protege é a chamada
      ao serviço, e ela não aconteceu;
    · **recusa da TOOL consome** — a viagem aconteceu: o serviço conta toda
      `tools/call` no porteiro, ANTES de executar a tool, então o teto
      compartilhado de 2.000/dia já foi debitado quando a tool disse não;
    · **as outras quatro falhas NÃO consomem**, cada uma por um motivo
      próprio — ver o `except` abaixo.

    A F2 deixou a recusa de graça e registrou a escolha como "a avalizar". O
    achado F-04 do `24-VERIFICATION.md` mediu o preço dela depois que a Fase
    24 acrescentou o fan-out de até 6 vencimentos do `/possibilidades`: seis
    `evaluate` sobre uma cadeia que não precifica custavam 6 do teto da BASE
    e 0 do cap de quem os provocou, e ~330 toques no botão esgotavam os
    2.000/dia de todo mundo sem mover os 60/dia de ninguém. **Avalizado pelo
    Alex em 2026-09-11: cobrar a viagem** (as outras duas opções — cachear a
    recusa, limitar falhas por requisição — foram descartadas nesta rodada).

    O que NÃO foi consumido (cache ou exceção sem viagem) volta ao balde de
    reservas na saída do `with` da rota — ver `_Reserva`. Recebe a `_Reserva`
    em vez do `uid` justamente para que o consumo seja CONTADO: sem isso, a
    rota não saberia quanto sobrou da reserva para devolver.
    """
    try:
        r = await mcp_client.call_tool(nome, args)
    except mcp_client.McpErroDeTool as e:
        # A viagem ACONTECEU. `call_tool` serve o cache ANTES de abrir sessão
        # e só levanta isto depois da resposta do serviço (`mcp_client`:
        # a recusa nem chega ao `_cache_put`) — então um `McpErroDeTool` aqui
        # é prova de rede tocada, nunca de acerto de cache.
        #
        # As outras QUATRO seguem sem debitar, e cada uma por uma razão
        # diferente — está escrito porque a próxima pessoa vai querer
        # "uniformizar" e precisa saber por que não:
        #   · `McpNaoConfigurado` — não houve viagem: falta credencial e o
        #     cliente nem abre sessão;
        #   · `McpNaoAutorizado` — o porteiro do serviço recusa ANTES do
        #     contador de tools;
        #   · `McpTetoAtingido` — o próprio contrato do serviço diz que a
        #     chamada recusada por teto não conta;
        #   · `McpIndisponivel` — timeout/5xx: não há PROVA de que o serviço
        #     contou, e cobrar por indisponibilidade puniria o usuário pela
        #     queda do fornecedor.
        # Cobrar o que não se sabe se foi cobrado é o mesmo erro do F-04,
        # invertido.
        cap.consome(1)
        setattr(e, ATR_DEBITADO, True)
        raise
    if not r.cache:
        cap.consome(1)
    return (r.dados if isinstance(r.dados, dict) else {}), bool(r.cache)


# --------------------------------------------------------------------------
# Validação do pedido (recusa ANTES da rede) e a única conta desta camada.
# --------------------------------------------------------------------------
def _tipo_de_opcao(valor) -> Optional[str]:
    """`kind` normalizado, ou `None` quando o pedido não restringe o tipo."""
    if valor is None or valor == "":
        return None
    tipo = str(valor).strip().upper()
    if tipo not in TIPOS_DE_OPCAO:
        raise HTTPException(422, {
            "code": "kind_invalido",
            "message": "Escolha CALL ou PUT, ou deixe em branco para ver os dois.",
            "recebido": repr(valor),
        })
    return tipo


def _direcao(valor) -> Optional[str]:
    """Tese direcional, ou `None` quando o pedido não a informa.

    O serviço NÃO escolhe direção, e esta camada também não: alta, baixa ou
    neutra é juízo de quem opera. O que se faz aqui é recusar o que não é
    tese antes de gastar uma chamada.
    """
    if valor is None or valor == "":
        return None
    direcao = str(valor).strip().lower()
    if direcao not in DIRECOES:
        raise HTTPException(422, {
            "code": "direction_invalida",
            "message": "A tese é de alta (bullish), baixa (bearish) ou neutra (neutral).",
            "recebido": repr(valor),
        })
    return direcao


def _preco_de_cenario(valor, campo: str) -> Optional[float]:
    """Preço do objeto num cenário nomeado (alvo/stop), ou `None` quando não
    veio. Zero e negativo são recusados: não existe preço de ação assim, e
    aceitá-los produziria uma linha de payoff sobre um preço impossível."""
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        raise HTTPException(422, {
            "code": "cenario_invalido",
            "message": f"O preço de '{campo}' precisa ser um número maior que zero.",
            "recebido": repr(valor),
        })
    return float(valor)


def _limite(valor) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) \
            or not (LIMITE_MIN <= valor <= LIMITE_MAX):
        raise HTTPException(422, {
            "code": "limite_invalido",
            "message": f"Peça entre {LIMITE_MIN} e {LIMITE_MAX} contratos por vez.",
            "recebido": repr(valor),
        })
    return valor


def _lote(valor) -> int:
    """Lote em número de AÇÕES (D-24.3).

    NÃO exige múltiplo de 100: o tamanho do contrato é da SÉRIE, e recusar
    150 seria inventar uma regra que a B3 não aplica uniformemente. O que se
    recusa é o que não é lote: zero, negativo, fracionário, booleano e texto.
    """
    inteiro = None
    if not isinstance(valor, bool) and isinstance(valor, (int, float)):
        try:
            if float(valor).is_integer():
                inteiro = int(valor)
        except (OverflowError, ValueError):
            inteiro = None
    if inteiro is None or inteiro <= 0:
        raise HTTPException(422, {
            "code": "lote_invalido",
            "message": ("Informe o lote em número de ações (inteiro positivo). "
                        "1 contrato = 100 ações."),
            "recebido": repr(valor),
        })
    return inteiro


def _vezes_lote(valor, lote: int) -> Optional[float]:
    """Multiplica pelo lote SÓ o que é número. Qualquer outra coisa — `None`
    de ganho ilimitado, texto, booleano — sai `None`: um 0 aqui seria a tela
    afirmando "não ganha nada" onde o serviço disse "não tem teto"."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return valor * lote


# **Por que não há conversão de breakeven no bloco abaixo, e por que isso não
# é esquecimento:** breakeven é PREÇO DO OBJETO, não dinheiro da posição.
# Multiplicado pelo lote viraria um número sem significado que a tela
# exibiria como reais. O campo fica FORA de `emReais`, na resposta da rota,
# em preço — desenho que torna o defeito impossível em vez de proibido
# (D-24.2).
def _em_reais(dados: dict, lote: int) -> dict:
    """Cifras da estrutura multiplicadas pelo lote, em reais.

    `lote` é número de AÇÕES: o serviço devolve tudo por unidade do objeto
    (uma ação), e o contrato padrão da B3 são 100 ações. Multiplicar é a
    única conta que esta camada faz, e ela é fechada aqui para não haver uma
    segunda versão dela no front — duas implementações da mesma conta
    divergem na primeira correção feita só de um lado.

    `None` entra e `None` sai (ver `_vezes_lote`). `preco do objeto` de
    cenário viaja VERBATIM: é preço, não dinheiro da posição.
    """
    dados = dados if isinstance(dados, dict) else {}

    bloco = dados.get("scenarios")
    lista = bloco.get("scenarios") if isinstance(bloco, dict) else None
    cenarios = []
    for item in lista or []:
        if not isinstance(item, dict):
            continue
        cenarios.append({
            "name": item.get("name"),
            "underlying": item.get("underlying"),
            "resultado": _vezes_lote(item.get("result"), lote),
        })

    return {
        "lote": lote,
        "custoLiquido": _vezes_lote(dados.get("net_cost"), lote),
        "ganhoMaximo": _vezes_lote(dados.get("max_gain"), lote),
        "perdaMaxima": _vezes_lote(dados.get("max_loss"), lote),
        "cenarios": cenarios,
        "unidade": "reais para o lote informado (lote = número de ações)",
    }


def _razao_ganho_perda(dados: dict) -> dict:
    """Quantas vezes o ganho máximo cabe na perda máxima.

    Adimensional de propósito: NÃO recebe lote, porque multiplicar os dois
    lados pelo mesmo número não muda a razão — e um parâmetro que não muda o
    resultado é um convite a multiplicá-lo por engano, que é o defeito irmão
    do breakeven × lote (D-24.2). Por isso ela também fica FORA de `emReais`:
    razão não é dinheiro, e dentro do bloco de reais seria lida como tal.

    `valor` é `None` sempre que a razão não EXISTE, e nesse caso `motivo` diz
    qual dos casos é. Um número aqui onde não há razão seria a pior classe de
    fabricação desta aba: o leitor compara 2,3 com 1,5 e decide.

    A ORDEM dos testes é o desenho. Os dois `unlimited_*` vêm primeiro porque
    são a afirmação MAIS forte do serviço sobre a estrutura — e nesse caso o
    `max_gain`/`max_loss` costuma vir `null` junto, o que cairia em
    `RAZAO_SEM_DADO` e trocaria "sem teto" (informação) por "não veio o dado"
    (ignorância). A perda zero vem por último porque só se sabe que ela é zero
    depois de confirmar que ela é número.
    """
    dados = dados if isinstance(dados, dict) else {}

    if dados.get("unlimited_gain"):
        return {"valor": None, "motivo": RAZAO_GANHO_ILIMITADO}
    if dados.get("unlimited_loss"):
        return {"valor": None, "motivo": RAZAO_PERDA_ILIMITADA}

    ganho = dados.get("max_gain")
    perda = dados.get("max_loss")
    # Mesma régua de `_vezes_lote`: booleano NÃO é número. `True` passaria por
    # 1 num `isinstance(x, (int, float))` ingênuo e produziria uma razão.
    for v in (ganho, perda):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return {"valor": None, "motivo": RAZAO_SEM_DADO}

    if perda == 0:
        return {"valor": None, "motivo": RAZAO_PERDA_ZERO}

    # Magnitudes: o serviço pode mandar a perda máxima com sinal (−1,20) ou
    # sem (1,20) — as duas dizem a mesma coisa, e a razão é entre tamanhos.
    return {"valor": round(abs(ganho) / abs(perda), 2), "motivo": None}


# Campos da leitura agrupados pela JANELA de que dependem — a mesma janela que
# o nome de cada um já declara. `range_63_sessions` chega SEMPRE como dict
# (`{"highest": None, "lowest": None}` quando a janela não fechou), então a
# ausência dele é conteúdo nulo, não chave nula: ver `_campo_vazio`.
_CAMPOS_DE_63 = ("trend", "distance_from_sma63_pct", "range_63_sessions")
_CAMPOS_DE_JANELA = ("trend", "rsi14", "distance_from_sma21_pct",
                     "distance_from_sma63_pct", "range_63_sessions",
                     "change_21_sessions_pct")
# `hv21`/`hv63` NÃO são calculados pelo serviço: são colunas DIRETAS do candle.
# Nulos querem dizer que o provedor não publicou volatilidade realizada para
# aquele ativo — motivo diferente dos outros dois, e por isso texto separado.
_CAMPOS_DE_HV = ("hv21", "hv63")


def _campo_vazio(behavior: dict, campo: str) -> bool:
    """Se o campo da leitura veio sem número.

    `range_63_sessions` é o único que exige olhar DENTRO: o serviço manda o
    dicionário mesmo quando a janela não fechou, com os dois extremos nulos.
    Tratá-lo como os demais faria o app dar por presente uma faixa que não
    existe.
    """
    valor = behavior.get(campo)
    if campo == "range_63_sessions":
        if not isinstance(valor, dict):
            return valor is None
        return all(valor.get(k) is None for k in ("highest", "lowest"))
    return valor is None


def _lacunas_da_leitura(behavior) -> list:
    """Por que cada campo ausente da leitura está ausente.

    Deriva do que o PRÓPRIO `behavior` mostra — não consulta nada, não conta
    pregão, não afirma tamanho de série. A regra é de observação: se a janela
    de 21 fechou e a de 63 não, a série está entre as duas, e é isso que se
    pode dizer com honestidade.

    Existe porque travessão mudo não é estado vazio: a pessoa não sabe se o
    app quebrou, se o ativo é estranho ou se falta dado (princípio 9). E
    porque preencher o número seria fabricar (princípio 4) — os campos não
    existem na origem, e o Boris NÃO os recalcula (decisão do Alex,
    2026-09-11: fonte única).

    Devolve `[{"campos": [...], "motivo": "<texto>"}]`, no máximo três
    entradas, e NOMEIA só o que de fato veio vazio: citar um campo que chegou
    seria a mesma classe de erro, na direção contrária.

    Lista vazia quando não há o que explicar — `behavior` ausente, torto,
    `status: "sem_candles"` ou sem nem o fechamento. Nesses casos a tela tem
    estado próprio, e repetir o motivo aqui viraria duas mensagens para a
    mesma ausência. Sem `close` também não se pode afirmar nada sobre o
    provedor de volatilidade: não há leitura nenhuma para explicar.
    """
    if not isinstance(behavior, dict) or behavior.get("status") == "sem_candles":
        return []
    if behavior.get("close") is None:
        return []

    def _vazios(campos):
        return [c for c in campos if _campo_vazio(behavior, c)]

    lacunas = []
    tem_sma21 = behavior.get("sma21") is not None
    tem_sma63 = behavior.get("sma63") is not None

    # A ORDEM é de precedência, não de conveniência: a janela de 63 e a série
    # curta demais são o MESMO fato em graus diferentes, e emitir os dois
    # diria duas coisas sobre a mesma ausência.
    if tem_sma21 and not tem_sma63:
        campos = _vazios(_CAMPOS_DE_63)
        if campos:
            lacunas.append({"campos": campos, "motivo": MOTIVO_JANELA_63})
    elif not tem_sma21:
        campos = _vazios(_CAMPOS_DE_JANELA)
        if campos:
            lacunas.append({"campos": campos, "motivo": MOTIVO_SERIE_CURTA})

    # `hv` é independente das médias: pode faltar com a série inteira fechada,
    # porque não é conta do serviço — é coluna que o provedor publica ou não.
    hv = _vazios(_CAMPOS_DE_HV)
    if hv:
        lacunas.append({"campos": hv, "motivo": MOTIVO_HV_AUSENTE})
    return lacunas


def _pernas_para_avaliar(setup: Optional[dict]) -> list:
    """Pernas do setup no formato que `evaluate_option_structure` aceita.

    Perna sem `contract` é descartada: o serviço identifica o contrato pelo
    código, e avaliar uma estrutura com perna anônima devolveria número sobre
    outra coisa. Lista vazia é o sinal de "não dá para avaliar" — e a rota a
    usa para PULAR a segunda chamada daquele vencimento.
    """
    pernas = []
    for perna in (setup or {}).get("legs") or []:
        if not isinstance(perna, dict):
            continue
        contrato = perna.get("contract")
        if not contrato:
            continue
        item = {"contract": contrato, "side": perna.get("side")}
        # `quantity` omitida é 1 no serviço; mandar `None` seria dizer
        # "quantidade nenhuma", que é outra coisa.
        if perna.get("quantity") is not None:
            item["quantity"] = perna.get("quantity")
        pernas.append(item)
    return pernas


def _registros_do_ticker(lista: Optional[dict], alvo: str) -> list:
    """Pares `(setup, registro)` de `list_setups` cujo ticker bate com `alvo`.
    Registro torto (sem `setup`, sem ticker) é ignorado — não vira item vazio
    na tela."""
    fora = []
    for item in (lista or {}).get("setups") or []:
        if not isinstance(item, dict):
            continue
        setup = item.get("setup")
        setup = setup if isinstance(setup, dict) else {}
        t = str(setup.get("ticker") or "").strip().upper()
        if not t or t != alvo:
            continue
        fora.append((setup, item))
    return fora


# --------------------------------------------------------------------------
# Rotas.
# --------------------------------------------------------------------------
@router.get("/status")
async def status(user: dict = Depends(require_user)) -> dict:
    """Estado do dado do serviço de opções: pregão, frescor por classe e o
    saldo do cap do dia.

    Erro de TOOL aqui responde **200**, não 422 — decisão registrada no
    ADR-027 ("Decisão de implementação (Fase 1)"). A finalidade de `/status`
    é reportar o estado do dado; devolver 422 faria a tela não saber dizer
    nada, e "idade desconhecida" viraria silêncio, que é o mesmo que "em
    dia" para quem olha. O 422 segue valendo em `_erro_http`, usado pelas
    rotas de leitura das Fases 2+, onde o erro da tool é falha do pedido.
    """
    uid = user["id"]
    # `with` (quick 260911-lib): o que for reservado e não consumido volta na
    # saída — inclusive no `raise` abaixo. Ver `_Reserva`.
    with _cap_check(uid, 1) as cap:
        erro_tool = None
        r = None
        try:
            r = await mcp_client.call_tool("check_data_freshness", {})
        except mcp_client.McpErroDeTool as e:
            # A viagem aconteceu, mesma razão do `_chamada_com_cap` (F-04) —
            # e aqui ela é mais fácil de esquecer justamente porque a rota
            # responde 200: ninguém desconfia de que um 200 custou. O débito
            # é o mesmo; o que segue diferente é só o CÓDIGO da resposta,
            # pela finalidade da rota (reportar estado do dado).
            cap.consome(1)
            erro_tool = str(e)
        except (mcp_client.McpErro, ValueError) as e:
            # `detalhe=str(e)` (achado A-03): o nome da classe sozinho não
            # separa "emissor recusou" de "conexão fechada" de "erro de
            # protocolo", e o diagnóstico ficava dedutivo. É seguro logar: as
            # mensagens do `mcp_client` são livres de segredo por construção
            # (docstring de topo do módulo, e o guardião T-waw-01 em
            # `test_mcp_client.py` prova).
            obslog.log("mcp", "status falhou", level="warn",
                       rota="/api/options/mcp/status", uid=uid,
                       erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        sc = r.dados if (r is not None and isinstance(r.dados, dict)) else None
        if r is not None and not r.cache:
            # Acerto de cache não gasta cap: o custo que o cap protege é a
            # chamada ao serviço, e ela não aconteceu.
            cap.consome(1)

        frescor = _frescor(sc, erro_tool)
        # `None` quando a resposta não traz pregão — nunca uma data fabricada
        # (princípio 4 do CLAUDE.md).
        pregao_do_dado = (sc or {}).get("trading_date") or (sc or {}).get("pregao") or None
        obslog.log("mcp", "status", rota="/api/options/mcp/status", uid=uid,
                   cache=bool(r is not None and r.cache),
                   bloqueia=frescor["bloqueia"])

        return {
            "pregao": pregao_do_dado,
            # 24-12 — a distância MEDIDA até o último pregão fechado, ao lado
            # do frescor que o serviço assina. São grandezas diferentes (idade
            # da carga × pregões faltando) e nenhuma substitui a outra; esta
            # não bloqueia nada (quem bloqueia segue sendo `frescor`).
            # Derivada do mesmo valor que já vai em `pregao`, sem chamada nova.
            "atraso": _atraso_em_pregoes(pregao_do_dado),
            "fonte": FONTE,
            "at": _agora_brt(),
            "frescor": frescor,
            # `usado` é o CONFIRMADO (`metering.used`), não o reservado —
            # reserva não é gasto, e a devolução do saldo não mexe em `count`.
            "cap": _cap_bloco(uid),
        }


@router.get("/leitura/{ticker}")
async def leitura(ticker: str, user: dict = Depends(require_user)) -> dict:
    """Leitura de um ticker: comportamento recente, catálogo de estruturas,
    vencimentos e os setups GRAVADOS daquele ticker com a avaliação do dia.

    Custo declarado 3 (ADR-027 §3.3): `propose_option_setups`, `list_setups`
    e `evaluate_setups`. A terceira é PULADA quando o ticker não tem nenhum
    setup gravado — consumir menos que o checado é sempre permitido, o
    contrário não.

    Nada aqui é calculado: `behavior`, `catalog`, `expirations`, `conditions`
    e o `reason` do gate de frescor viajam VERBATIM. Campo que não veio é
    `None` — nunca 0, nunca lista inventada (princípio 4 do CLAUDE.md).
    """
    uid = user["id"]
    # Reserva 3, consome de 0 a 3 — e o que sobra volta na saída do `with`.
    # É a rota onde o defeito A-07 aparecia inteiro: três acertos de cache
    # reservavam 3 e consumiam 0 (quick 260911-lib, ver `_Reserva`).
    with _cap_check(uid, 3) as cap:
        alvo = (ticker or "").strip().upper()
        rota = "/api/options/mcp/leitura/{ticker}"

        passo = "propose_option_setups"
        chamou_evaluate = False
        cache_tudo = True
        try:
            proposta, c1 = await _chamada_com_cap(cap, "propose_option_setups",
                                                  {"ticker": alvo})
            cache_tudo = cache_tudo and c1

            passo = "list_setups"
            lista, c2 = await _chamada_com_cap(cap, "list_setups", {})
            cache_tudo = cache_tudo and c2
            registros = _registros_do_ticker(lista, alvo)

            avaliacao_dados: Optional[dict] = None
            if registros:
                passo = "evaluate_setups"
                avaliacao_dados, c3 = await _chamada_com_cap(cap, "evaluate_setups", {})
                cache_tudo = cache_tudo and c3
                chamou_evaluate = True
        except (mcp_client.McpErro, ValueError) as e:
            # `McpErroDeTool` INCLUSIVE: aqui o erro da tool é falha do PEDIDO
            # (ticker inexistente, sem cotações), não um estado a exibir — vira
            # 422 por `_erro_http`. O 200-com-`bloqueia` é exclusividade do
            # `/status`, cuja finalidade é justamente reportar estado do dado.
            obslog.log("mcp", "leitura falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, passo=passo, erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        avaliacoes = {}
        nao_avaliado = None
        if isinstance(avaliacao_dados, dict):
            if avaliacao_dados.get("status") == "nao_avaliado":
                # Gate de frescor do serviço: ninguém foi avaliado. O motivo vai
                # VERBATIM ([R-15]) e NENHUM cartão recebe veredito — "não
                # armado" por ausência de avaliação seria afirmação sem medição.
                nao_avaliado = {"reason": avaliacao_dados.get("reason")}
            else:
                # `sem_setups` NÃO é bloqueio: é a ausência de setup, que a tela
                # já mostra como estado vazio com motivo.
                for av in avaliacao_dados.get("evaluations") or []:
                    if isinstance(av, dict) and av.get("name"):
                        avaliacoes[av["name"]] = av

        setups = []
        for setup, registro in registros:
            nome = setup.get("name")
            av = avaliacoes.get(nome) if nome else None
            setups.append({
                "name": nome,
                "ticker": alvo,
                # `status` do REGISTRO (`ativo`/`inativo`). NÃO é o status da
                # AVALIAÇÃO (`avaliado`/`nao_avaliavel`/`expirado`/…), que vive
                # em `avaliacao.status` — confundir os dois faria a tela dizer
                # "ativo" onde o serviço disse "não consegui avaliar".
                "status": registro.get("status"),
                "avaliacao": av,
                "armed": av.get("armed") if av else None,
                "streak": av.get("streak") if av else None,
                # Sem avaliação, o `required_streak` cai no `consecutive_days`
                # DECLARADO no próprio setup — valor que o usuário escreveu, não
                # número calculado. Não é fabricação.
                "required_streak": (av.get("required_streak") if av
                                    else setup.get("consecutive_days")),
                "conditions": av.get("conditions") if av else None,
                "backtest_na_criacao": registro.get("backtest_na_criacao"),
            })

        frescor = _frescor_da_avaliacao(avaliacao_dados, chamou_evaluate)
        # `None` quando nenhuma das respostas trouxe pregão — nunca uma data
        # fabricada (princípio 4 do CLAUDE.md).
        pregao_do_dado = (proposta.get("trading_date")
                          or (avaliacao_dados or {}).get("trading_date")
                          or None)
        obslog.log("mcp", "leitura", rota=rota, uid=uid, ticker=alvo,
                   setups=len(setups), avaliou=chamou_evaluate,
                   cache=cache_tudo, bloqueia=frescor["bloqueia"])

        return {
            "ticker": alvo,
            "pregao": pregao_do_dado,
            # 24-12 — a MESMA medição do `/status`, sobre o pregão que esta
            # rota exibe. Derivada do valor que já está na mão: o custo
            # declarado da rota continua 3.
            "atraso": _atraso_em_pregoes(pregao_do_dado),
            "fonte": FONTE,
            "at": _agora_brt(),
            # Verbatim, sem interpretar: `behavior` pode ser
            # `{"status": "sem_candles"}` e a tela tem estado próprio para isso.
            "behavior": proposta.get("behavior"),
            # 24-11 — POR QUE cada campo vazio do `behavior` está vazio. Campo
            # NOVO ao lado, nunca reescrita do que o serviço mandou: `null`
            # continua `null`, e a explicação é derivada do que JÁ veio nesta
            # mesma resposta — nenhuma chamada de tool a mais, o custo
            # declarado da rota continua 3.
            "lacunas": _lacunas_da_leitura(proposta.get("behavior")),
            "catalog": proposta.get("catalog"),
            "expirations": proposta.get("expirations"),
            "setups": setups,
            "setupsNaoAvaliados": nao_avaliado,
            "frescor": frescor,
            "cap": _cap_bloco(uid),
        }


@router.get("/setups/{name}/grafico")
async def setup_grafico(name: str, user: dict = Depends(require_user)) -> dict:
    """Série de candles de um setup gravado, com os índices de disparo.

    **Sem `frescor` nesta rota** — diverge do "toda resposta traz frescor" do
    §3.3 do PLANO, de propósito (decisão travada da F2): o gráfico é o insumo
    do que a leitura JÁ carimbou, e medir frescor aqui exigiria uma segunda
    chamada, quebrando o custo 1 declarado no ADR-027. Quem carimba pregão e
    frescor é o `/leitura` e o `/status`, que a tela chama antes desta.

    Limitação conhecida: nome de setup contendo `/` não resolve aqui —
    `{name}` não é conversor `path`, e transformá-lo em um engoliria o
    `/grafico` do fim da URL. Nome com barra devolve 404 do roteador.
    """
    uid = user["id"]
    with _cap_check(uid, 1) as cap:   # saldo não consumido volta na saída
        rota = "/api/options/mcp/setups/{name}/grafico"
        try:
            dados, cache = await _chamada_com_cap(cap, "get_setup_chart",
                                                  {"name": name})
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "grafico de setup falhou", level="warn", rota=rota,
                       uid=uid, setup=name, erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        obslog.log("mcp", "grafico de setup", rota=rota, uid=uid, setup=name,
                   cache=cache)

        # Payload da tool PRIMEIRO, envelope DEPOIS: invertida, a ordem deixaria
        # o `trading_date` do payload sobrescrever o `pregao` do envelope.
        return {
            **dados,
            "pregao": dados.get("trading_date") or None,
            "fonte": FONTE,
            "at": _agora_brt(),
            "cap": _cap_bloco(uid),
        }


@router.get("/cadeia/{ticker}")
async def cadeia(ticker: str, expiration: Optional[str] = None,
                 kind: Optional[str] = None, limit: int = 50,
                 user: dict = Depends(require_user)) -> dict:
    """Cadeia de opções do ticker: os contratos que o serviço tem para aquele
    pregão, com prêmio, strike, delta e volume — custo 1.

    Nada aqui é calculado. `options` viaja VERBATIM, e `truncated` também: é
    o serviço dizendo quantos contratos ficaram de fora e como pedir o resto.
    Engolir esse aviso faria a tela afirmar sobre a cadeia inteira tendo
    visto metade.
    """
    uid = user["id"]
    alvo = (ticker or "").strip().upper()
    # Validação ANTES do cap, e o cap antes da rede: mesmo princípio em dois
    # degraus — pedido torto não pode custar uma chamada do teto compartilhado.
    tipo = _tipo_de_opcao(kind)
    limite = _limite(limit)

    args = {"ticker": alvo, "limit": limite}
    # Chave omitida ≠ chave com `None`: o serviço trata ausência como "todos
    # os vencimentos", e mandar `expiration: None` é um filtro nulo explícito.
    if expiration:
        args["expiration"] = expiration
    if tipo:
        args["kind"] = tipo

    with _cap_check(uid, 1) as cap:   # saldo não consumido volta na saída
        rota = "/api/options/mcp/cadeia/{ticker}"
        try:
            dados, cache = await _chamada_com_cap(cap, "get_option_chain", args)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "cadeia falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        frescor = _frescor_do_anexo(dados) or _frescor_nao_medido(AVISO_FRESCOR_SEM_ANEXO)
        obslog.log("mcp", "cadeia", rota=rota, uid=uid, ticker=alvo,
                   vencimento=args.get("expiration"), tipo=tipo,
                   retornados=dados.get("returned"), cache=cache)

        return {
            "ticker": alvo,
            "pregao": dados.get("trading_date") or None,
            "precoObjeto": dados.get("underlying_price"),
            "fonte": FONTE,
            "at": _agora_brt(),
            "opcoes": dados.get("options") or [],
            "encontrados": dados.get("matched"),
            "retornados": dados.get("returned"),
            "truncado": dados.get("truncated"),
            "frescor": frescor,
            "cap": _cap_bloco(uid),
        }


@router.get("/operaveis/{ticker}")
async def operaveis(ticker: str, expiration: Optional[str] = None,
                    kind: Optional[str] = None,
                    user: dict = Depends(require_user)) -> dict:
    """A cadeia depois da peneira de liquidez e delta — custo 1.

    O critério é do BORIS (D-24.4), e por isso sai declarado em
    `criterioAplicado` junto do `criteria` que o serviço escreve. Peneira que
    some com o strike da pessoa sem dizer o número que a reprovou é peneira
    que a tela não consegue explicar.
    """
    uid = user["id"]
    alvo = (ticker or "").strip().upper()
    tipo = _tipo_de_opcao(kind)

    args = {"ticker": alvo, "min_trades": OPERAVEIS_MIN_NEGOCIOS,
            "delta_min": OPERAVEIS_DELTA_MIN, "delta_max": OPERAVEIS_DELTA_MAX}
    if expiration:
        args["expiration"] = expiration
    if tipo:
        args["kind"] = tipo

    with _cap_check(uid, 1) as cap:
        rota = "/api/options/mcp/operaveis/{ticker}"
        try:
            dados, cache = await _chamada_com_cap(cap, "find_tradable_options", args)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "operaveis falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        obslog.log("mcp", "operaveis", rota=rota, uid=uid, ticker=alvo,
                   vencimento=args.get("expiration"), tipo=tipo,
                   opcoes=len(dados.get("options") or []), cache=cache)

        return {
            "ticker": alvo,
            "pregao": dados.get("trading_date") or None,
            "precoObjeto": dados.get("underlying_price"),
            "fonte": FONTE,
            "at": _agora_brt(),
            "opcoes": dados.get("options") or [],
            "criterio": dados.get("criteria"),
            "criterioAplicado": {
                "minNegocios": OPERAVEIS_MIN_NEGOCIOS,
                "deltaMin": OPERAVEIS_DELTA_MIN,
                "deltaMax": OPERAVEIS_DELTA_MAX,
            },
            "excluidos": dados.get("excluded"),
            "nota": dados.get("note"),
            # `find_tradable_options` não anexa `data_freshness`: aqui é
            # sempre "não medido", nunca uma tentativa de ler anexo que não
            # existe — e "não medido" declarado não pode virar silêncio.
            "frescor": _frescor_nao_medido(AVISO_FRESCOR_SEM_ANEXO),
            "cap": _cap_bloco(uid),
        }


def _ticker_do_corpo(corpo: dict) -> str:
    alvo = str((corpo or {}).get("ticker") or "").strip().upper()
    if not alvo:
        raise HTTPException(422, {
            "code": "ticker_ausente",
            "message": "Informe o ativo (por exemplo, PETR4).",
        })
    return alvo


def _tese(corpo: dict) -> tuple:
    """`(direction, kind)` validados, exigindo ao menos um dos dois.

    O serviço não escolhe direção — e esta camada, menos ainda. Sem tese não
    existe "a" estrutura a montar, e devolver uma qualquer seria o app
    decidindo por quem opera.
    """
    direcao = _direcao((corpo or {}).get("direction"))
    tipo = _tipo_de_opcao((corpo or {}).get("kind"))
    if not direcao and not tipo:
        raise HTTPException(422, {
            "code": "tese_ausente",
            "message": ("Escolha uma tese (alta, baixa ou neutra) ou nomeie a "
                        "estrutura. O serviço não escolhe direção — isso é "
                        "juízo de quem opera."),
        })
    return direcao, tipo


@router.post("/proposta")
async def proposta(body: dict = Body(default={}),
                   user: dict = Depends(require_user)) -> dict:
    """Estruturas que a cadeia permite montar para uma tese — custo 1.

    `estruturas: []` com `motivo` preenchido é resposta **200** legítima: o
    serviço diz em PT-BR por que a cadeia não preencheu a perna (strike sem
    negócio, vencimento sem prêmio), e isso é estado a exibir, não erro.

    `emReais` só existe quando o corpo trouxe `lote` E o serviço devolveu
    UMA estrutura. Sem lote, a tela mostra por ação — que é a unidade em que
    o serviço fala.
    """
    uid = user["id"]
    corpo = body if isinstance(body, dict) else {}
    alvo = _ticker_do_corpo(corpo)
    direcao, tipo = _tese(corpo)
    lote = _lote(corpo.get("lote")) if corpo.get("lote") is not None else None
    vencimento = corpo.get("expiration")

    args = {"ticker": alvo}
    if direcao:
        args["direction"] = direcao
    if tipo:
        args["kind"] = tipo
    if vencimento:
        args["expiration"] = vencimento

    with _cap_check(uid, 1) as cap:
        rota = "/api/options/mcp/proposta"
        try:
            dados, cache = await _chamada_com_cap(cap, "propose_option_setups", args)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "proposta falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        estruturas = [s for s in (dados.get("setups") or []) if isinstance(s, dict)]
        # Uma estrutura só: com duas na tela, um `emReais` no envelope não
        # diria de qual delas é o dinheiro.
        em_reais = _em_reais(estruturas[0], lote) if (lote and len(estruturas) == 1) else None
        # A razão segue a MESMA régua de ambiguidade do `emReais` (uma
        # estrutura só), e NÃO a de lote: ela é adimensional, então existe
        # mesmo sem lote informado — é o número de decisão de quem ainda nem
        # escolheu tamanho de posição.
        razao = _razao_ganho_perda(estruturas[0]) if len(estruturas) == 1 else None

        obslog.log("mcp", "proposta", rota=rota, uid=uid, ticker=alvo,
                   direcao=direcao, tipo=tipo, estruturas=len(estruturas),
                   cache=cache)

        return {
            "ticker": alvo,
            "pregao": dados.get("trading_date") or None,
            "precoObjeto": dados.get("underlying_price"),
            "fonte": FONTE,
            "at": _agora_brt(),
            # O que o serviço CONFIRMA ter usado; na falta do eco, o que foi
            # pedido — nunca um valor que ninguém escolheu.
            "direction": dados.get("direction") or direcao,
            "kind": dados.get("kind") or tipo,
            "behavior": dados.get("behavior"),
            "estruturas": estruturas,
            "motivo": dados.get("reason"),
            "nota": dados.get("note"),
            "emReais": em_reais,
            # FORA de `emReais`, no mesmo nível: razão não é dinheiro (F-01).
            "razaoGanhoPerda": razao,
            "frescor": _frescor_nao_medido(AVISO_FRESCOR_SEM_ANEXO),
            "cap": _cap_bloco(uid),
        }


@router.post("/possibilidades")
async def possibilidades(body: dict = Body(default={}),
                         user: dict = Depends(require_user)) -> dict:
    """O que dá para montar em CADA vencimento aberto, com payoff e reais.

    Custo 2×N+1, reservado em DUAS etapas (D-24.1): N só se conhece depois da
    primeira chamada, que é quem traz `expirations`. Reservar o teto (13)
    recusaria quem tem cota de sobra; reservar 1 e gastar 13 faria o cap
    mentir. Então reserva 1, descobre N, e aninha um `with` de 2×N — as duas
    devolvem o que não foi consumido na saída.

    Vencimento cuja estrutura não montou NÃO gasta a segunda chamada, e falha
    de tool em UM vencimento não apaga os outros: erro de tool é sobre aquele
    pedido, enquanto serviço fora do ar é condição de todos e encerra a rota
    (insistir nos cinco restantes contra um serviço mudo só queima a viagem).
    """
    uid = user["id"]
    corpo = body if isinstance(body, dict) else {}
    alvo = _ticker_do_corpo(corpo)
    direcao, tipo = _tese(corpo)
    lote = _lote(corpo.get("lote"))
    rota = "/api/options/mcp/possibilidades"

    # Cenários NOMEADOS do usuário. A banda de ±1σ o serviço devolve sozinho —
    # duplicá-la aqui seria inventar a volatilidade em vez de lê-la.
    cenarios = []
    preco_alvo = _preco_de_cenario(corpo.get("alvo"), "alvo")
    preco_stop = _preco_de_cenario(corpo.get("stop"), "stop")
    if preco_alvo is not None:
        cenarios.append({"name": "alvo", "underlying": preco_alvo})
    if preco_stop is not None:
        cenarios.append({"name": "stop", "underlying": preco_stop})

    pedidos = corpo.get("expirations")
    pedidos = ([v for v in pedidos if isinstance(v, str)]
               if isinstance(pedidos, list) else None)

    with _cap_check(uid, 1) as cap1:
        try:
            base, _cache = await _chamada_com_cap(cap1, "propose_option_setups",
                                                  {"ticker": alvo})
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "possibilidades falhou", level="warn", rota=rota,
                       uid=uid, ticker=alvo, passo="propose_option_setups",
                       erro=type(e).__name__,
                       detalhe=str(e))  # A-03 — ver nota em `/status`
            raise _erro_http(e)

        disponiveis = [v for v in (base.get("expirations") or []) if isinstance(v, str)]
        # Vencimento pedido que a cadeia não tem não vira chamada: gastaria
        # cap para o serviço responder que não existe.
        escolhidos = ([v for v in pedidos if v in disponiveis] if pedidos
                      else list(disponiveis))[:N_MAX_VENCIMENTOS]

        envelope = {
            "ticker": alvo,
            "pregao": base.get("trading_date") or None,
            "precoObjeto": base.get("underlying_price"),
            "fonte": FONTE,
            "at": _agora_brt(),
            "lote": lote,
            "direction": direcao,
            "kind": tipo,
            "vencimentosConsiderados": escolhidos,
            "vencimentosDisponiveis": disponiveis,
            # O MESMO número que a UI mostra antes de disparar — sai na
            # resposta para que os dois lados não possam divergir.
            "chamadasPrevistas": 2 * len(escolhidos) + 1,
            "behavior": base.get("behavior"),
            "frescor": _frescor_nao_medido(AVISO_FRESCOR_SEM_ANEXO),
        }

        if not escolhidos:
            obslog.log("mcp", "possibilidades", rota=rota, uid=uid, ticker=alvo,
                       vencimentos=0, montadas=0)
            return {**envelope, "possibilidades": [], "motivo": MOTIVO_SEM_VENCIMENTO,
                    "cap": _cap_bloco(uid)}

        # N real, agora conhecido. `_cap_check` recusa aqui ANTES da rede — e
        # o que este `with` reservar e não gastar volta na saída.
        with _cap_check(uid, 2 * len(escolhidos)) as cap2:
            lista = []
            passo = "propose_option_setups"
            try:
                for vencimento in escolhidos:
                    try:
                        passo = "propose_option_setups"
                        args = {"ticker": alvo, "expiration": vencimento}
                        if direcao:
                            args["direction"] = direcao
                        if tipo:
                            args["kind"] = tipo
                        proposta_do_venc, _c = await _chamada_com_cap(
                            cap2, "propose_option_setups", args)

                        montados = [s for s in (proposta_do_venc.get("setups") or [])
                                    if isinstance(s, dict)]
                        setup = montados[0] if montados else None
                        pernas = _pernas_para_avaliar(setup)
                        if not pernas:
                            # Avaliar o que não existe gastaria cap por nada.
                            # O motivo é do serviço, verbatim ([R-15]).
                            lista.append({
                                "vencimento": vencimento, "estrutura": None,
                                "emReais": None, "razaoGanhoPerda": None,
                                "erro": None,
                                "motivo": (proposta_do_venc.get("reason")
                                           or proposta_do_venc.get("note")),
                            })
                            continue

                        passo = "evaluate_option_structure"
                        args_avaliacao = {"ticker": alvo, "legs": pernas}
                        if cenarios:
                            args_avaliacao["scenarios"] = cenarios
                        avaliacao, _c = await _chamada_com_cap(
                            cap2, "evaluate_option_structure", args_avaliacao)
                    except mcp_client.McpErroDeTool as e:
                        # Erro de tool é sobre ESTE vencimento. Os outros
                        # seguem — e a mensagem do serviço vai inteira, porque
                        # ela é quem explica (livre de segredo por construção
                        # do `mcp_client`).
                        obslog.log("mcp", "possibilidades: vencimento recusado",
                                   level="warn", rota=rota, uid=uid, ticker=alvo,
                                   vencimento=vencimento, passo=passo,
                                   detalhe=str(e))
                        lista.append({"vencimento": vencimento, "estrutura": None,
                                      "emReais": None, "razaoGanhoPerda": None,
                                      "motivo": None, "erro": str(e)})
                        continue

                    estrutura = {c: avaliacao.get(c) for c in CHAVES_DA_ESTRUTURA}
                    # `kind`/`name` NOMEIAM a estrutura e vêm de quem a montou
                    # (`propose`), não de quem a avaliou.
                    for chave in ("kind", "name"):
                        if estrutura.get(chave) is None:
                            estrutura[chave] = (setup or {}).get(chave)

                    lista.append({
                        "vencimento": vencimento,
                        "estrutura": estrutura,
                        # Reais calculados UMA vez, aqui. `breakevens` fica na
                        # estrutura, em preço do objeto — ver `_em_reais`.
                        "emReais": _em_reais(avaliacao, lote),
                        # Irmã do bloco acima e deliberadamente FORA dele: a
                        # razão é adimensional e não conhece lote (F-01).
                        "razaoGanhoPerda": _razao_ganho_perda(avaliacao),
                        "motivo": None,
                        "erro": None,
                    })
            except (mcp_client.McpErro, ValueError) as e:
                # Condição do SERVIÇO (sem credencial, fora do ar, teto
                # atingido): não é sobre um vencimento, é sobre todos. A
                # captura fica FORA do `for` de propósito — o `continue` do
                # erro de tool não se aplica aqui, e uma resposta 200 parcial
                # esconderia que o serviço parou no meio.
                obslog.log("mcp", "possibilidades falhou", level="warn",
                           rota=rota, uid=uid, ticker=alvo,
                           vencimento=vencimento, passo=passo,
                           erro=type(e).__name__,
                           detalhe=str(e))  # A-03 — ver nota em `/status`
                raise _erro_http(e)

            obslog.log("mcp", "possibilidades", rota=rota, uid=uid, ticker=alvo,
                       vencimentos=len(escolhidos),
                       montadas=len([i for i in lista if i.get("estrutura")]))

            return {**envelope, "possibilidades": lista, "motivo": None,
                    "cap": _cap_bloco(uid)}


# --------------------------------------------------------------------------
# F5 — criar setup por descrição em português: compilar → dry-run → confirmar,
# e desativar. Tudo atrás de `require_criar_setup`.
# --------------------------------------------------------------------------
def _descricao_do_corpo(corpo: dict) -> str:
    """A descrição ORIGINAL, do jeito que a pessoa digitou — é ela que viaja
    para o campo `description` do setup, e é ela que prova depois o que foi
    pedido."""
    texto = str((corpo or {}).get("descricao") or "").strip()
    if not texto:
        raise HTTPException(422, {
            "code": "descricao_ausente",
            "message": "Descreva o setup com as suas palavras.",
        })
    if len(texto) > DESCRICAO_MAX:
        raise HTTPException(422, {
            "code": "descricao_longa",
            "message": (f"A descrição passou de {DESCRICAO_MAX} caracteres. "
                        "Resuma a condição que você quer vigiar."),
            "caracteres": len(texto),
            "maximo": DESCRICAO_MAX,
        })
    return texto


def _campos_faltando(setup) -> list:
    """Checagem de FORMA, e só. `conditions` precisa ser lista NÃO VAZIA: um
    setup sem condição nenhuma dispararia todo pregão, e o serviço o recusaria
    de qualquer jeito — depois de gastar a viagem."""
    setup = setup if isinstance(setup, dict) else {}
    faltando = []
    for campo in CAMPOS_OBRIGATORIOS_DO_SETUP:
        valor = setup.get(campo)
        if campo == "conditions":
            if not (isinstance(valor, list) and valor):
                faltando.append(campo)
        elif not (isinstance(valor, str) and valor.strip()):
            faltando.append(campo)
    return faltando


def _janela_declarada(spec) -> Optional[int]:
    """A janela que um lado da comparação DECLARA, ou `None`.

    A leitura é de FORMA, não de vocabulário: quem tem janela é a condição que
    traz `window`, e o serviço só aceita `window` em indicador que a use
    ("não usa janela — remova"). Guardar aqui a lista dos indicadores com
    janela criaria a segunda cópia do contrato — a que ninguém atualiza quando
    o serviço ganha o próximo indicador (ENG-06).

    `bool` é recusado de propósito (subclasse de `int`): um `True` viraria
    janela de 1 e produziria aviso sobre uma condição que não declarou nada.
    """
    if not isinstance(spec, dict):
        return None
    janela = spec.get("window")
    if isinstance(janela, bool) or not isinstance(janela, int) or janela < 1:
        return None
    return janela


def _ensaio_inconclusivo(setup, backtest) -> dict:
    """Condições cuja janela não cabe no histórico usado pelo ensaio.

    **Por que existe** (achado ao vivo, 2026-09-11): um setup com média de 200
    sobre 48 pregões volta `disparos: 0` e `pregoes_avaliaveis: 31`. Os dois
    números estão certos — `AND` com um `False` conhecido é `False`, e nos dias
    de RSI acima de 30 o dia é comprovadamente falso. O que está errado é o que
    a pessoa entende: "testei e não disparou", quando a verdade é que a
    condição da média NUNCA teve valor e o setup era indisparável.

    É pior que um campo vazio: vazio se vê, número plausível não. Alguém pode
    GRAVAR um setup acreditando que ele passou por um teste que não houve.

    A conta é de janela, não de análise técnica: uma janela de `w` sobre `n`
    pregões produz `n - w + 1` pontos. `<= 0` significa que a condição nunca
    teve valor; menos que `consecutive_days` significa que a sequência exigida
    é impossível mesmo com todos os pontos verdadeiros.

    `n - w + 1` é o TETO, e é assim de propósito: as médias produzem essa
    contagem, e os indicadores que olham o pregão anterior produzem um ponto a
    menos. Errar para o lado generoso só pode deixar de avisar — nunca dar
    como morta uma condição que teve valor.

    O veredito `indisparavel` é reservado ao caso DEMONSTRÁVEL: condição sem
    ponto nenhum dentro de um `AND`. Aí a impossibilidade é aritmética — se
    uma condição do `AND` nunca é verdadeira, o dia nunca é verdadeiro, e
    `disparos` é 0 por construção. Com `OR`, uma condição morta não impede as
    outras; com a janela curta para a sequência, a condição TEVE valor em
    alguns pregões e o ensaio de fato avaliou alguma coisa. Nos dois, a
    condição é listada como ressalva e o veredito é calado: afirmar
    indisparabilidade que não se pode provar seria trocar uma leitura errada
    por outra.

    Nada aqui é recalculado e nada é consultado: `setup` e `backtest` são o
    que o dry-run JÁ devolveu, na mesma resposta.
    """
    periodo = backtest.get("periodo") if isinstance(backtest, dict) else None
    pregoes = periodo.get("pregoes") if isinstance(periodo, dict) else None
    if isinstance(pregoes, bool) or not isinstance(pregoes, int) or pregoes < 1:
        # Sem o tamanho do período não existe a conta, e a tela não afirma
        # nada. Um aviso derivado de um número que ninguém informou seria a
        # fabricação que este helper existe para impedir (princípio 4).
        return {"indisparavel": False, "condicoes": [], "pregoes": None}

    setup = setup if isinstance(setup, dict) else {}
    # Os dois defaults são os do motor (`setup.get("logic", "AND")`,
    # `setup.get("consecutive_days", 1)`). Tratar a ausência como
    # "desconhecido" faria o caso mais comum — setup sem `logic` explícita —
    # perder justamente o aviso.
    and_logico = str(setup.get("logic") or "AND").strip().upper() == "AND"
    exigidos = setup.get("consecutive_days")
    if isinstance(exigidos, bool) or not isinstance(exigidos, int) or exigidos < 1:
        exigidos = 1

    condicoes = []
    morta = False
    for cond in (setup.get("conditions") or []):
        if not isinstance(cond, dict):
            continue
        # Os DOIS lados contam, e a maior janela manda: é ela que decide
        # quando a comparação passa a ter valor. No caso real a janela que
        # mata o ensaio mora na `reference` (`close > média de 200`), não no
        # lado esquerdo.
        lados = [(_janela_declarada(lado), lado)
                 for lado in (cond, cond.get("reference"))]
        lados = [(j, lado) for j, lado in lados if j is not None]
        if not lados:
            continue
        janela, lado = max(lados, key=lambda par: par[0])
        pontos = pregoes - janela + 1
        if pontos <= 0:
            motivo = MOTIVO_JANELA_NUNCA_FECHOU
            morta = True
        elif pontos < exigidos:
            motivo = MOTIVO_JANELA_CURTA_PARA_SEQUENCIA
        else:
            continue
        # O nome do indicador sai VERBATIM do lado que bloqueia: é vocabulário
        # do serviço, e traduzi-lo aqui criaria o segundo dicionário.
        indicador = lado.get("indicator")
        condicoes.append({
            "indicador": indicador if isinstance(indicador, str) else None,
            "janela": janela,
            "pontos": pontos,
            "motivo": motivo,
        })

    return {"indisparavel": bool(morta and and_logico),
            "condicoes": condicoes,
            "pregoes": pregoes}


# Chaves toleradas para idade e SLA dentro da classe de frescor. Mesma razão
# da tolerância de `_frescor`: a forma real de `check_data_freshness` só se
# confirma ao vivo (`test_mcp_vivo.py`), e cravar UMA chave faria o número
# sumir em silêncio se o serviço usar a irmã.
_CHAVES_IDADE = ("idadeHoras", "idade_horas", "age_hours", "quotes_age_hours", "horas")
_CHAVES_SLA = ("slaHoras", "sla_horas", "sla_hours", "sla_horas_max", "sla")


def _numero_de(info, chaves) -> Optional[float]:
    """Primeiro número achado na classe ou no `bruto` dela. `bool` é recusado
    (subclasse de `int`): um `True` viraria "1 hora" na tela. Ausente é
    `None` — nunca 0, que se lê como "acabou de atualizar"."""
    fontes = []
    if isinstance(info, dict):
        fontes.append(info)
        if isinstance(info.get("bruto"), dict):
            fontes.append(info["bruto"])
    for fonte in fontes:
        for chave in chaves:
            v = fonte.get(chave)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return v
    return None


def _pregao_medido(frescor: dict, dados: Optional[dict] = None):
    """O pregão de quem MEDIU o dado (`check_data_freshness`, cujo bruto viaja
    dentro do frescor), com o da resposta da tool como segunda porta.

    `create_setup` não devolve `trading_date` no contrato — sem esta leitura,
    o `pregao` da rota sairia `None` mesmo tendo a medição na mão, e a tela
    mostraria "pregão desconhecido" ao lado de um frescor "em dia". `None`
    continua sendo a resposta quando nenhum dos dois traz data: data
    fabricada, nunca (princípio 4 do CLAUDE.md).
    """
    bruto = (frescor or {}).get("bruto")
    bruto = bruto if isinstance(bruto, dict) else {}
    return bruto.get("trading_date") or (dados or {}).get("trading_date") or None


def _erro_de_frescor(frescor: dict) -> HTTPException:
    """409 `dado_atrasado`. Forma UNIFORME (as quatro chaves sempre presentes,
    `None` onde não se aplica): chave que aparece e some obriga a tela a
    testar existência em vez de valor."""
    critica = next((c for c in frescor.get("classes") or []
                    if c.get("classe") == CLASSE_CRITICA), None)
    medido = bool(frescor.get("medido"))
    return HTTPException(409, {
        "code": "dado_atrasado",
        "message": AVISO_DADO_ATRASADO if medido else AVISO_DADO_NAO_MEDIDO,
        # `motivo` distingue as DUAS causas do mesmo 409 — "medi e está
        # velho" não é a mesma coisa que "ninguém mediu", e a segunda é a que
        # a Decisão 8 do ADR-027 existe para não deixar passar por "em dia".
        "motivo": "atrasado" if medido else "nao_medido",
        "idadeHoras": _numero_de(critica, _CHAVES_IDADE),
        "slaHoras": _numero_de(critica, _CHAVES_SLA),
        "frescor": frescor,
    })


async def _frescor_bloqueante(cap: _Reserva) -> dict:
    """Mede o frescor e LEVANTA 409 quando ele bloqueia (ADR-027, Decisão 8).

    Custo 1 quando toca a rede (cache de 600 s no `mcp_client`), por isso as
    rotas que a usam reservam uma unidade a mais.

    Erro da TOOL vira "não medido" e bloqueia igual — é o mesmo tratamento do
    `/status`, e pela mesma razão: ausência de medição não é medição
    favorável. As demais exceções sobem para o `_erro_http` da rota: falta de
    credencial ou serviço fora do ar não é dado atrasado.
    """
    erro_tool = None
    dados = None
    try:
        dados, _cache = await _chamada_com_cap(cap, "check_data_freshness", {})
    except mcp_client.McpErroDeTool as e:
        erro_tool = str(e)

    frescor = _frescor(dados, erro_tool)
    if frescor["bloqueia"]:
        raise _erro_de_frescor(frescor)
    return frescor


# --------------------------------------------------------------------------
# 25-04 (Fase 3 do 25-CONTEXT) — O CÓDIGO DA RECUSA.
#
# Até aqui esta tradução descobria QUAL teto barrou procurando a substring
# `"analises/mes"` no TEXTO da mensagem (`_MARCA_DO_GATE_MENSAL`, 24-07). Era
# acoplamento frágil e silencioso: bastava `plan.py` reescrever a frase — ou
# traduzi-la, ou trocar "analises" por "análises" — para esta aba passar a
# chamar de `ia_gerenciada` um limite MENSAL de plano, sem teste nenhum
# reclamar na hora do erro. O guardião que travava a marca virou o guardião do
# código (`test_opcoes_dsl.py`, nota datada lá).
#
# Agora o gate CARIMBA a exceção no ponto em que a decisão acontece, e aqui só
# se lê o carimbo. É o mesmo padrão de `ATR_DEBITADO` logo abaixo, pelo mesmo
# motivo: quem sabe a resposta é quem decidiu, não quem traduz.
#
# As três constantes moram NESTE módulo, e não em `plan.py`, por duas razões:
# `main.py` já importa este módulo (o contrário seria circular), e os dois
# códigos são CONTRATO publicado desta aba — o front lê `detail.code`. O texto
# que chega ao usuário não muda em nada.
# --------------------------------------------------------------------------
ATR_CODIGO_DO_LIMITE = "codigo_do_limite"
COD_PLANO_ANALISES = "plano_analises"
COD_IA_GERENCIADA = "ia_gerenciada"


def marcar_o_limite(exc: HTTPException, codigo: str) -> HTTPException:
    """Carimba QUAL teto produziu esta recusa. Devolve a própria exceção para
    o chamador poder escrever `raise marcar_o_limite(HTTPException(...), ...)`
    numa linha — o carimbo esquecido é o defeito que isto existe para evitar."""
    setattr(exc, ATR_CODIGO_DO_LIMITE, codigo)
    return exc


def codigo_do_limite(exc: Exception) -> Optional[str]:
    """O carimbo, ou `None` quando a recusa veio de um caminho que ninguém
    carimbou (código futuro, biblioteca, teste antigo)."""
    codigo = getattr(exc, ATR_CODIGO_DO_LIMITE, None)
    return codigo if isinstance(codigo, str) else None


def _gate_de_analise(uid: str) -> tuple:
    """`(config_efetiva, consume)` do gate de análise de `main.py`, com o 402
    traduzido para o vocabulário desta aba.

    São DOIS tetos diferentes na mesma requisição e eles não significam a
    mesma coisa: `plano_analises` é o balde MENSAL do plano comercial
    (ADR-010), `ia_gerenciada` é a cota DIÁRIA da chave do servidor, e
    `mcp_cota` (o `_cap_check`) é o teto de chamadas da aba. Mandar o copy de
    BYOK do `metering` aqui mandaria a pessoa configurar uma chave que não
    resolve nenhum dos três.

    25-04: qual dos dois barrou vem do CARIMBO posto pelo gate, não mais da
    frase da mensagem — ver o bloco de `ATR_CODIGO_DO_LIMITE` acima.
    """
    if _gate_analise is None or _config_do_usuario is None:
        raise HTTPException(503, _NAO_CONFIGURADO)
    config = _config_do_usuario(uid)
    config = config if isinstance(config, dict) else {}
    try:
        return _gate_analise(uid, config)
    except HTTPException as e:
        if e.status_code != 402:
            raise
        # Sem carimbo, cai em `ia_gerenciada` — o MESMO lado em que a raspagem
        # antiga caía quando a marca não estava na frase. Um 402 de origem
        # desconhecida vira uma recusa legível, nunca um 500.
        mensal = codigo_do_limite(e) == COD_PLANO_ANALISES
        raise HTTPException(402, {
            "code": COD_PLANO_ANALISES if mensal else COD_IA_GERENCIADA,
            "message": AVISO_PLANO_ANALISES if mensal else AVISO_IA_GERENCIADA,
        }) from None


def _campo_de(item, *chaves):
    """Lê de objeto do SDK OU de dict. `tools/list` devolve o objeto tipado do
    SDK; o mesmo conteúdo, num teste ou num SDK futuro, pode chegar como
    dict — e o compilador não pode depender de qual dos dois é."""
    for chave in chaves:
        valor = item.get(chave) if isinstance(item, dict) else getattr(item, chave, None)
        if valor:
            return valor
    return None


def _schema_da_tool(catalogo, nome: str) -> Optional[dict]:
    """`inputSchema` da tool pedida, do catálogo VIVO do serviço."""
    tools = _campo_de(catalogo, "tools") or []
    for tool in tools:
        if _campo_de(tool, "name") == nome:
            schema = _campo_de(tool, "inputSchema", "input_schema", "schema")
            return schema if isinstance(schema, dict) else None
    return None


def _texto_do_resource(recurso) -> str:
    """Texto de um `resources/read`: o SDK devolve `contents[]`, cada item com
    `text`. Itens sem texto (binário) são ignorados — não viram string vazia
    no meio do prompt."""
    partes = []
    for item in _campo_de(recurso, "contents") or []:
        texto = _campo_de(item, "text")
        if isinstance(texto, str) and texto.strip():
            partes.append(texto)
    return "\n\n".join(partes).strip()


def _system_compilador(schema: dict, texto: str) -> str:
    """O `system` do compilador: instrução do Boris + o `inputSchema` VIVO +
    o texto para humanos do serviço, verbatim.

    Função PURA de propósito (nenhuma rede): é ela que o guardião do ENG-06
    exercita para provar que nenhum indicador, operador ou padrão está
    hardcodado aqui — o que aparece no prompt é o que veio no schema e no
    texto passados.
    """
    return "\n".join((
        SYSTEM_COMPILADOR_CABECALHO,
        "",
        "--- ESPECIFICAÇÃO DO OBJETO (schema publicado pelo serviço) ---",
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        "",
        "--- EXPLICAÇÃO DO SERVIÇO, PALAVRA POR PALAVRA ---",
        texto,
    ))


def _user_do_compilador(descricao: str, ticker: str) -> str:
    """A descrição vai DELIMITADA e rotulada como texto de terceiro. O que ela
    diz é dado, não instrução: sem a marca, uma frase como "ignore as regras
    acima" chegaria ao modelo indistinguível do `system`."""
    return "\n".join((
        f"Ativo: {ticker}",
        "Descrição escrita pela pessoa, entre as marcas, palavra por palavra:",
        "<<<DESCRICAO",
        descricao,
        "DESCRICAO>>>",
    ))


async def _material_do_compilador() -> tuple:
    """`(inputSchema, texto_humano)` de `create_setup` — as DUAS fontes do
    `system`.

    Montar em runtime é o que impede o vocabulário (indicadores, operadores,
    padrões) de virar constante dentro do Boris: cópia que envelhece em
    silêncio quando o serviço acrescenta um indicador, e é exatamente o que o
    ENG-06 proíbe.

    `tools/list` e `resources/read` são PROTOCOLO: de graça no teto do serviço
    e fora do cap por usuário, com cache de 1 h no `mcp_client`. Faltando
    qualquer um dos dois, `McpErroDeTool` → 422: compilar sem o contrato vivo
    seria compilar de memória.
    """
    catalogo = await mcp_client.list_tools()
    schema = _schema_da_tool(catalogo.dados, TOOL_CREATE_SETUP)
    if not schema:
        raise mcp_client.McpErroDeTool(
            f"o serviço não publicou o schema de `{TOOL_CREATE_SETUP}`",
            hint="sem o schema vivo não há como compilar a descrição")

    recurso = await mcp_client.read_resource(URI_CREATE_SETUP)
    texto = _texto_do_resource(recurso.dados)
    if not texto:
        raise mcp_client.McpErroDeTool(
            f"o serviço não publicou o texto de `{URI_CREATE_SETUP}`",
            hint="sem a explicação do serviço não há como compilar a descrição")

    return schema, texto


def _desembrulha_setup(objeto):
    """Aceita o setup tanto pelado quanto dentro do envelope `{"setup": …}`.

    **Medido com LLM real em 2026-09-11**, na primeira execução da etapa 5 do
    `fechar-fase-24.sh`: o modelo compilou a descrição perfeitamente e ainda
    assim tomou 422 `forma_invalida`, porque respondeu
    `{"setup": {...}, ...}` e a validação procurava os campos na raiz.

    E ele estava CERTO. O `system` do compilador é montado do `inputSchema` de
    `create_setup`, que é `{setup: Setup, confirm: bool}` — o modelo devolveu
    exatamente a forma que a especificação que nós demos a ele descreve. Quem
    estava fora do contrato era o validador.

    O `system` passou a pedir o objeto interno explicitamente (ver
    `SYSTEM_COMPILADOR_CABECALHO`), mas isto fica como rede: instrução em
    prosa disputando com um schema formal é disputa que o schema ganha, e
    perder uma compilação boa por causa de um invólucro seria jogar fora
    trabalho que o usuário já pagou.

    Desembrulha SÓ quando não há ambiguidade: chaves de topo contidas em
    `{"setup", "confirm"}` e `setup` sendo um dict não vazio. Um objeto que
    tenha `setup` junto de `name`/`ticker` NÃO é envelope — é setup com campo
    estranho, e aí quem decide é a validação de forma.
    """
    if not isinstance(objeto, dict):
        return objeto
    interno = objeto.get("setup")
    if isinstance(interno, dict) and interno and set(objeto) <= {"setup", "confirm"}:
        return interno
    return objeto


def _setup_do_corpo(corpo: dict) -> dict:
    """O setup que o usuário VIU no dry-run, de volta para gravar. Não é
    recompilado nem passa por LLM: se fosse, o que se grava poderia não ser o
    que ele aprovou."""
    setup = (corpo or {}).get("setup")
    if not isinstance(setup, dict) or not setup:
        raise HTTPException(422, {
            "code": "setup_ausente",
            "message": "Envie o setup que apareceu no ensaio.",
        })
    faltando = _campos_faltando(setup)
    if faltando:
        raise HTTPException(422, {
            "code": "forma_invalida",
            "message": "O setup chegou incompleto.",
            "faltando": faltando,
        })
    return setup


def _lista_verbatim(e: mcp_client.McpErroDeTool, chave: str) -> list:
    """A lista que o serviço mandou junto da recusa, na ORDEM dele e sem
    reescrita — é a única informação acionável que a pessoa tem. `available`
    é o campo genérico do contrato de tool e serve de segunda porta para a
    mesma lista."""
    valor = e.bruto.get(chave)
    if not isinstance(valor, list):
        valor = e.available if isinstance(e.available, list) else []
    return list(valor)


def _erro_de_setup_invalido(e: mcp_client.McpErroDeTool) -> HTTPException:
    """`create_setup` recusou por SEMÂNTICA. Quem valida indicador, operador e
    janela é o serviço — esta camada só carrega os `problems` item a item."""
    return HTTPException(422, {
        "code": "setup_invalido",
        "message": str(e),
        "problems": _lista_verbatim(e, "problems"),
        # Recusa semântica também é viagem cobrada (F-04). O campo vem da
        # MESMA marca dos outros 422 para não haver uma segunda regra: aqui
        # ele está sempre presente na prática, porque este erro só nasce do
        # `except` colado num `_chamada_com_cap`.
        **_bloco_cobrado(e),
    })


def _erro_de_setup_desconhecido(e: mcp_client.McpErroDeTool) -> HTTPException:
    return HTTPException(422, {
        "code": "setup_desconhecido",
        "message": str(e),
        "known_setups": _lista_verbatim(e, "known_setups"),
        **_bloco_cobrado(e),
    })


def _audita(uid: str, nome: str, antes, depois, *, rota: str) -> None:
    """Grava a auditoria da escrita de setup SEM poder derrubar a rota (F-03).

    **A assimetria com o resto do arquivo é deliberada, e a razão é a ordem
    dos fatos:** quando esta função roda, a escrita no armazém do serviço JÁ
    aconteceu. Derrubar a resposta por falha de CONTABILIDADE (`database is
    locked` sob concorrência, disco cheio no Railway) faria a pessoa acreditar
    que o setup não foi criado e tentar de novo — e o armazém é SEM DONO
    (ADR-027, Decisão 7), então a retentativa deixa dois setups iguais para
    toda a base. Perder uma linha de auditoria é ruim; duplicar registro no
    armazém compartilhado é pior.

    Silêncio REGISTRADO, não silêncio: a falha vai ao obslog com `level="warn"`
    — mesmo padrão do `ai_activity.registrar_uso` em `/setups/compilar`
    ("contabilidade nunca derruba a rota"). Sem o registro, ninguém saberia
    que a trilha ficou com buraco.
    """
    try:
        audit.record(_conn, uid, ENTIDADE_AUDITORIA, nome, "status", antes, depois)
    except Exception as e:  # noqa: BLE001 — contabilidade nunca derruba a rota
        obslog.log("mcp", "auditoria do setup falhou", level="warn", rota=rota,
                   uid=uid, setup=nome, estado=depois,
                   erro=type(e).__name__, detalhe=str(e))


def _erro_de_ia(e: Exception, *, rota: str, uid: str, ticker: str) -> HTTPException:
    """Falha de TRANSPORTE da LLM → 503 acionável (F-02 do 24-VERIFICATION).

    Mesma divisão de `_erro_http`: o detalhe que separa "o modelo demorou" de
    "o SDK mudou de forma" vai para o obslog, onde o Alex enxerga; para quem
    está na tela os dois são "não deu agora, e nada foi gravado".

    O texto NÃO nomeia provedor nem modelo de propósito: a chave pode ser a do
    servidor (caminho gerenciado), e nesse caso o nome do provedor não é
    informação do usuário — é detalhe de infraestrutura numa mensagem que ele
    não pode acionar.
    """
    obslog.log("mcp", "compilar falhou", level="warn", rota=rota, uid=uid,
               ticker=ticker, passo="llm", erro=type(e).__name__, detalhe=str(e))
    return HTTPException(503, {
        "code": "ia_indisponivel",
        "message": AVISO_IA_INDISPONIVEL,
        "action": ("Espere alguns minutos e peça de novo. Se insistir, a "
                   "cadeia, as operáveis e os setups já gravados continuam "
                   "funcionando — eles não dependem de IA."),
    })


@router.post("/setups/compilar")
async def setup_compilar(body: dict = Body(default={}),
                         user: dict = Depends(require_criar_setup)) -> dict:
    """Descrição em português → setup declarativo, com ENSAIO (`confirm=false`)
    antes de qualquer gravação — custo 2 (frescor + `create_setup`) e uma
    chamada de LLM.

    A ordem das etapas é o desenho, não acaso:
    1. frescor BLOQUEANTE, antes de tudo — nem LLM nem gravação sobre dado que
       ninguém mediu;
    2. gate de análise, antes de gastar a chave;
    3. schema + texto do serviço (de graça) e SÓ então a LLM;
    4. forma conferida aqui, semântica conferida pelo serviço;
    5. cota de análise consumida só no sucesso.
    """
    uid = user["id"]
    corpo = body if isinstance(body, dict) else {}
    # Validação ANTES do cap, como nas rotas de leitura: pedido torto não pode
    # custar uma chamada do teto compartilhado.
    descricao = _descricao_do_corpo(corpo)
    # `ticker` é do CORPO e não sai do texto: o serviço exige o ativo no setup,
    # e adivinhá-lo da frase seria inventar o que a pessoa não disse.
    alvo = _ticker_do_corpo(corpo)
    rota = "/api/options/mcp/setups/compilar"

    with _cap_check(uid, 2) as cap:
        try:
            frescor = await _frescor_bloqueante(cap)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "compilar falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, passo="check_data_freshness",
                       erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        config, consumir_analise = _gate_de_analise(uid)

        try:
            schema, texto = await _material_do_compilador()
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "compilar falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, passo="material", erro=type(e).__name__,
                       detalhe=str(e))
            raise _erro_http(e)

        system = _system_compilador(schema, texto)
        try:
            with llm.collect_usage() as usos:
                cru = await llm._call_llm(config, llm.resolve_key(config), system,
                                          _user_do_compilador(descricao, alvo),
                                          MAX_TOKENS_COMPILADOR)
        except llm.LLMUserError as e:
            # `public_error` já sanitiza (nenhuma chave em mensagem) e preserva
            # `code`/`action` — o front sabe renderizar "Como corrigir:".
            raise HTTPException(400, llm.public_error(e)) from None
        except (httpx.TimeoutException, httpx.HTTPError) as e:
            # F-02: o caso que DE FATO acontece. `llm._call_anthropic` usa
            # `httpx.AsyncClient(timeout=60)` sem capturar nada, e um modelo
            # que demore mais que isso para compilar (plausível com o
            # `inputSchema` inteiro no system) mandava `httpx.ReadTimeout`
            # para o handler global — 500 com `{"detail": "ReadTimeout: "}`.
            raise _erro_de_ia(e, rota=rota, uid=uid, ticker=alvo) from None
        except Exception as e:  # noqa: BLE001 — ver justificativa abaixo
            # **Por que um `except Exception` aqui não é preguiça:** o critério
            # 7 do ROADMAP desta fase é literal ("nada cai no handler 500"), e
            # o provedor de LLM é código de TERCEIRO cuja taxonomia de exceção
            # não é do Boris — ela muda de versão para versão sem aviso. As
            # duas classes de transporte ficam NOMEADAS acima para documentar
            # o caso conhecido; este é a rede de segurança do critério, e o
            # tipo real vai inteiro para o obslog.
            #
            # `HTTPException` levantada dentro dos `except` irmãos NÃO cai
            # aqui (exceção levantada em bloco `except` não é capturada por
            # cláusula irmã do mesmo `try`).
            raise _erro_de_ia(e, rota=rota, uid=uid, ticker=alvo) from None

        setup = _desembrulha_setup(llm._parse_json_loose(cru))
        if not isinstance(setup, dict):
            # O texto CRU vai junto, rotulado, para a pessoa ver o que a IA
            # respondeu. Fabricar um setup para "salvar" a resposta seria
            # gravar uma coisa que ninguém escreveu.
            raise HTTPException(422, {
                "code": "compilacao_invalida",
                "message": "A IA não respondeu um setup que dê para ler.",
                "cru": cru,
            })

        faltando = _campos_faltando(setup)
        if faltando:
            raise HTTPException(422, {
                "code": "forma_invalida",
                "message": "A IA respondeu um setup incompleto.",
                "faltando": faltando,
                "cru": cru,
            })

        # A descrição volta a ser a da PESSOA, sempre. É o campo que prova o
        # que ela pediu; a paráfrase da LLM apagaria isso, e o armazém de
        # setups é compartilhado (ADR-027, Decisão 7) — quem ler depois só tem
        # este texto para saber a intenção. Mesma razão para o `ticker`: o que
        # vale é o ativo que ela escolheu na tela.
        setup["description"] = descricao
        setup["ticker"] = alvo

        try:
            dados, cache = await _chamada_com_cap(
                cap, TOOL_CREATE_SETUP, {"setup": setup, "confirm": False})
        except mcp_client.McpErroDeTool as e:
            # Recusa SEMÂNTICA do serviço — é sobre este setup, não sobre o
            # serviço. Os `problems` voltam item a item.
            obslog.log("mcp", "compilar: setup recusado", level="warn", rota=rota,
                       uid=uid, ticker=alvo, detalhe=str(e))
            raise _erro_de_setup_invalido(e)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "compilar falhou", level="warn", rota=rota, uid=uid,
                       ticker=alvo, passo=TOOL_CREATE_SETUP,
                       erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        # Cota de análise e ledger de custo SÓ no sucesso.
        consumir_analise()
        try:
            ai_activity.registrar_uso(_conn, scope=uid, ticker=alvo,
                                      tipo=TIPO_ATIVIDADE, usos=usos)
        except Exception as e:  # noqa: BLE001 — contabilidade nunca derruba a rota
            print(f"[options-mcp] registro de custo falhou: {e}")

        obslog.log("mcp", "compilar", rota=rota, uid=uid, ticker=alvo,
                   condicoes=len(setup.get("conditions") or []), cache=cache)

        # O que o serviço ENTENDEU — e o que a tela mostra, e o que
        # `/setups/confirmar` recebe de volta. O `ensaio` é lido DESTE objeto,
        # não do que a IA respondeu: descrever um setup que ninguém vai gravar
        # seria explicar a coisa errada.
        interpretado = dados.get("setup_as_interpreted") or setup
        return {
            "status": dados.get("status") or "dry_run",
            "ticker": alvo,
            # A descrição ORIGINAL viaja de volta: é ela que a tela mostra ao
            # lado da interpretação, para a pessoa comparar antes de gravar.
            "descricao": descricao,
            # O que o serviço ENTENDEU. Na falta do eco, o que foi enviado —
            # é esse objeto que `/setups/confirmar` recebe de volta.
            "setup": interpretado,
            "backtest": dados.get("backtest"),
            # 24-14: a leitura que faltava AO LADO do backtest, nunca no lugar
            # dele — o `backtest` continua verbatim, byte a byte. Sai dos
            # mesmos números que já vieram: nenhuma chamada nova, nenhum
            # indicador recalculado.
            "ensaio": _ensaio_inconclusivo(interpretado, dados.get("backtest")),
            "proximoPasso": dados.get("next_step"),
            "pregao": _pregao_medido(frescor, dados),
            "fonte": FONTE,
            "at": _agora_brt(),
            "frescor": frescor,
            "cap": _cap_bloco(uid),
        }


@router.post("/setups/confirmar")
async def setup_confirmar(body: dict = Body(default={}),
                          user: dict = Depends(require_criar_setup)) -> dict:
    """Grava o setup que o usuário VIU no ensaio — custo 2 (frescor +
    `create_setup`), sem LLM nenhuma.

    Frescor bloqueante DE NOVO, e não é redundância: o dry-run pode ter sido
    visto há uma hora, e o que decide se o vigia nasce é o estado do dado
    AGORA.
    """
    uid = user["id"]
    corpo = body if isinstance(body, dict) else {}
    setup = _setup_do_corpo(corpo)
    nome = str(setup.get("name") or "").strip()
    rota = "/api/options/mcp/setups/confirmar"

    with _cap_check(uid, 2) as cap:
        try:
            frescor = await _frescor_bloqueante(cap)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "confirmar falhou", level="warn", rota=rota, uid=uid,
                       setup=nome, passo="check_data_freshness",
                       erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        try:
            dados, cache = await _chamada_com_cap(
                cap, TOOL_CREATE_SETUP, {"setup": setup, "confirm": True})
        except mcp_client.McpErroDeTool as e:
            obslog.log("mcp", "confirmar: setup recusado", level="warn", rota=rota,
                       uid=uid, setup=nome, detalhe=str(e))
            raise _erro_de_setup_invalido(e)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "confirmar falhou", level="warn", rota=rota, uid=uid,
                       setup=nome, passo=TOOL_CREATE_SETUP,
                       erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        gravado = str(dados.get("name") or nome)
        # O estado sai do SERVIÇO, e a MESMA variável vai para a auditoria e
        # para a resposta: assim as duas não podem divergir — um log dizendo
        # "ativo" enquanto a tela mostra outra coisa seria pior que não logar.
        estado = str(dados.get("status") or "ativo")
        # Auditoria DEPOIS do sucesso: o armazém é compartilhado e sem dono
        # (ADR-027, Decisão 7), então quem gravou é a única resposta possível
        # para "de onde veio este setup". Antes do sucesso registraria uma
        # gravação que não aconteceu.
        _audita(uid, gravado, None, estado, rota=rota)

        obslog.log("mcp", "confirmar", rota=rota, uid=uid, setup=gravado, cache=cache)

        return {
            "status": estado,
            "name": gravado,
            "ticker": setup.get("ticker"),
            "setup": dados.get("setup_as_interpreted") or setup,
            "backtest": dados.get("backtest"),
            "nota": dados.get("note"),
            "pregao": _pregao_medido(frescor, dados),
            "fonte": FONTE,
            "at": _agora_brt(),
            "frescor": frescor,
            "cap": _cap_bloco(uid),
        }


@router.post("/setups/{name}/desativar")
async def setup_desativar(name: str,
                          user: dict = Depends(require_criar_setup)) -> dict:
    """Desliga um setup gravado — custo 1.

    **Sem frescor bloqueante, e a assimetria é deliberada:** criar é começar a
    AFIRMAR, e afirmar sobre dado velho é fabricar confiança; desativar é
    PARAR de afirmar. Travar o desligamento por dado atrasado deixaria um
    setup errado vigiando justamente porque a carga do dia falhou — o oposto
    do que a Decisão 8 do ADR-027 protege.

    Limitação conhecida: nome com `/` não resolve aqui, pela mesma razão já
    documentada em `/setups/{name}/grafico` (`{name}` não é conversor `path`,
    e transformá-lo em um engoliria o `/desativar` do fim da URL).
    """
    uid = user["id"]
    rota = "/api/options/mcp/setups/{name}/desativar"

    with _cap_check(uid, 1) as cap:
        try:
            dados, cache = await _chamada_com_cap(
                cap, TOOL_DEACTIVATE_SETUP, {"name": name})
        except mcp_client.McpErroDeTool as e:
            obslog.log("mcp", "desativar: setup desconhecido", level="warn",
                       rota=rota, uid=uid, setup=name, detalhe=str(e))
            raise _erro_de_setup_desconhecido(e)
        except (mcp_client.McpErro, ValueError) as e:
            obslog.log("mcp", "desativar falhou", level="warn", rota=rota, uid=uid,
                       setup=name, erro=type(e).__name__, detalhe=str(e))
            raise _erro_http(e)

        alvo = str(dados.get("name") or name)
        # Mesma regra de `/setups/confirmar`: a auditoria e a resposta leem a
        # MESMA variável, vinda do serviço.
        estado = str(dados.get("status") or "inativo")
        _audita(uid, alvo, "ativo", estado, rota=rota)

        obslog.log("mcp", "desativar", rota=rota, uid=uid, setup=alvo, cache=cache)

        return {
            "status": estado,
            "name": alvo,
            "fonte": FONTE,
            "at": _agora_brt(),
            # Declarado "não medido" como nas outras rotas sem anexo — aqui
            # ele NÃO bloqueia nada (ver a nota acima), é só o carimbo honesto
            # de que esta chamada não mediu idade de dado.
            "frescor": _frescor_nao_medido(AVISO_FRESCOR_SEM_ANEXO),
            "cap": _cap_bloco(uid),
        }
