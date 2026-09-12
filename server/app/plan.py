"""Ganchos do modelo FREEMIUM do Boris+ — plano comercial (ADR-010).

A partir da v1.3 (Fase 12), os dois limites do PLAN_FREE estao ATIVOS: 10
ativos na watchlist e 30 analises/mes. PLAN_PRO continua com ambos os
limites `None` (ilimitado) POR DECISAO comercial — nao existe loja/IAP neste
milestone, entao "pro" e um estado alcancavel so por atribuicao manual
(`users.plan`), nao por compra.

Estrategia de custo (pilar): BYOK — o usuario pluga a PROPRIA chave de LLM
(Config -> Modelo de IA). Assim o custo de inferencia nao recai sobre o app, o
que viabiliza um tier gratuito generoso.

O gate de assinatura (`requires_subscription`) deve consultar o recibo
validado da loja (server-side receipt validation) quando a loja/IAP existir —
NUNCA confiar so no cliente. Continua HOOK (sempre False) nesta fase.

Contrato de contagem (C-32, fixado na fase 3 — server/app/main.py::_gate_analise):
`server/app/metering.py` e o CONTADOR UNICO de uso de IA do app (cota DIARIA
por usuario + teto global, persistidos no kv). `can_analyze` aqui embaixo e o
gate de TIER comercial (MENSAL) e NUNCA mantem contagem propria — ele so LE o
limite do plano e decide permitido/negado. Com o ADR-010 tendo ligado
`max_analyses_per_month` (Fase 12), o valor de `used_this_month` passado a
`can_analyze` TEM de derivar do ledger de `metering` (C-33, fase 5) — nunca de
um segundo contador paralelo. Os dois gates (plano e metering) sao aplicados
num UNICO ponto de decisao por requisicao (`_gate_analise`), nunca em
paralelo.

-----------------------------------------------------------------------------
2026-09-12 (25-03, Fase 2 do `.planning/phases/25-planos-comerciais/25-CONTEXT.md`)

Até aqui este era o ÚNICO bloco de limites 100% literal do app: os outros
pontos de controle já tinham env, e três já tinham kv + painel + auditoria.
Agora os dois dicts de plano são a camada de DEFAULT de um catálogo, e o valor
vigente de cada limite resolve por **memória → kv → env → default** —
`LIMITES_DE_PLANO` mais abaixo é a declaração única, e `limites_do_plano()` é
a única porta que decide um valor.

**O que este plano deliberadamente NÃO fez:** ninguém LÊ o catálogo ainda. Os
três gates (`can_add_ticker`, `can_grow_watchlist_to`, `can_analyze`) seguem
lendo o dict estático que `current_plan()` devolve, byte a byte como antes —
ligá-los ao catálogo é o 25-04. Por isso o guardião de `test_catalogo_planos.py`
crava os números de hoje (30, 10, `None`, 20, 60, 1.0) EXPLICITAMENTE: sem
configuração, nada muda, e quem mudar um default tem de encarar o teste.

**Fronteira de import (deliberada):** este módulo NÃO importa `managed` nem
`options_mcp_api`, e nunca deve. O catálogo DECLARA limites; quem os aplica é
o gate. O import ao contrário criaria ciclo — `options_mcp_api` já é fiado por
injeção justamente por isso. Consequência honesta e conhecida: os overrides
GLOBAIS que já existem naqueles módulos (o `llmDailyQuota` do painel em
`managed`, o `mcpCotaUsuarioDia` em `options_mcp_api`) ficam FORA da cadeia
daqui; conciliar os dois é decisão do 25-04, não silêncio deste arquivo.

**O que NÃO entra no catálogo**, e a razão (ADR-010, decisão 2 — *"um usuário
pago consome da MESMA cota física"*): `managed.global_daily_cap()`,
`options_mcp_api.cota_global_dia()`, `TETO_SERVICO_DIA`, `brapi_budget.cota_mes()`
e `mydata_budget` protegem o app de cair, não o modelo de negócio; e **rate por
minuto** é freio contra flood — vender "mais requisições por minuto" seria
vender o direito de derrubar o serviço.

**`plan_at_least` foi REMOVIDA nesta data.** Era órfã desde que nasceu (zero
call sites; o achado do REPORT-01 já a registrava assim) e a docstring citava
um `require_plan()` que nunca existiu em `main.py` — um ponteiro para código
inexistente é pior que ausência, porque quem lê acredita. O esboço segue
registrado no ADR-013 (que é história e não se reescreve), mas a decisão D2 do
25-CONTEXT escolheu outro mecanismo para gate de função: **conjunto de funções
por plano** (`funcoes_do_plano`), não ordem de tier. Manter os dois convites
seria garantir que o dia da divergência chegasse. `_ORDEM_PLANO` FICA — tem
consumidor real (`main.py` ordena `planosDisponiveis` por ela).
"""
import math
import os
from typing import Optional

from . import db

# ---------------------------------------------------------------------------
# Injeção da conexão, mesmo padrão de `candle_cache.configure_db` /
# `brapi_budget.configure_db` / `managed.configure_db`: `main.py` importa este
# módulo e entrega a conexão. O inverso seria import circular.
#
# Sem `configure_db`, a camada de kv fica INERTE (nunca falsa): a resolução
# degrada para env → default. É o que acontece num teste unitário que não quer
# banco, e é degradação, não erro.
# ---------------------------------------------------------------------------
_conn = None


def configure_db(conn=None) -> None:
    global _conn
    _conn = conn
    # O cache é de PROCESSO, e este é o ponto em que o processo passa a falar
    # com OUTRO banco (é o que a suíte faz a cada cliente novo). Sem esta
    # linha, o limite configurado num teste valeria no seguinte, que roda
    # contra um banco vazio — o mesmo defeito que `options_mcp_api.configure`
    # já resolve com `reset_limites_cache()`.
    reset_cache_planos()


# ---------------------------------------------------------------------------
# CATÁLOGO — a declaração única dos pontos de controle que variam por plano.
#
# Cada linha: (chave, sufixo_kv, env, tipo, {plano: default}).
#
#  · chave      — o nome lido pelo resto do app. `max_analyses_per_month` e
#                 `max_watchlist` NÃO mudam de nome: têm chamador desde a Fase
#                 12 (`can_analyze`, `can_add_ticker`, `can_grow_watchlist_to`).
#  · sufixo_kv  — a chave de kv é `plano{Id}.{sufixo}` (ex.: `planoFree.watchlist`).
#                 O id do plano ENTRA na chave: sem isso dois planos disputariam
#                 o mesmo registro e configurar o free mudaria o pro.
#  · env        — se o nome contém `{PLANO}`, a env é POR PLANO
#                 (`B3_PLANO_FREE_WATCHLIST`); se não contém, é GLOBAL — e é
#                 global exatamente onde o valor de hoje JÁ é global (os três
#                 de baixo valem igual para todo mundo hoje, e reusar a env que
#                 já os controla é o que faz o catálogo espelhar a realidade em
#                 vez de inventar um segundo número).
#  · tipo       — `int` ou `float`. Existe porque um dos cinco é dinheiro
#                 (R$/dia) e o painel (25-05) precisa saber renderizar e
#                 validar. Inferir do default falharia: `pro` tem `None`.
#  · defaults   — o valor de HOJE, por plano. É a única cópia: `PLAN_FREE` e
#                 `PLAN_PRO` são construídos a partir daqui.
#
# `None` = SEM LIMITE. `0` = BLOQUEIA. As duas coisas são diferentes e
# sobrevivem distinguíveis ao ida e volta pelo kv (JSON `null` vs `0`).
# ---------------------------------------------------------------------------
LIMITES_DE_PLANO = (
    # ATIVOS desde a v1.3 (Fase 12, ADR-010) — têm chamador, o nome é contrato.
    ("max_watchlist", "watchlist", "B3_PLANO_{PLANO}_WATCHLIST",
     int, {"free": 10, "pro": None}),
    ("max_analyses_per_month", "analisesMes", "B3_PLANO_{PLANO}_ANALISES_MES",
     int, {"free": 30, "pro": None}),
    # Declarados aqui, ainda aplicados por quem sempre os aplicou (25-04 liga).
    # A env é a MESMA que `managed.daily_quota()` lê hoje.
    ("ia_gerenciada_dia", "iaGerenciadaDia", "B3_MANAGED_DAILY_QUOTA",
     int, {"free": 20, "pro": 20}),
    # A env é a MESMA que `options_mcp_api.cota_usuario_dia()` lê hoje.
    ("opcoes_chamadas_dia", "opcoesChamadasDia", "B3_MCP_COTA_USUARIO_DIA",
     int, {"free": 60, "pro": 60}),
    # Dinheiro: teto de custo do assistente em R$/dia. A env é a MESMA que
    # `assistente.teto_dia_brl()` lê hoje.
    ("assistente_brl_dia", "assistenteBrlDia", "B3_ASSISTENTE_TETO_BRL",
     float, {"free": 1.0, "pro": 1.0}),
)

# Como "sem limite" se escreve fora do Python. No kv o valor é o `null` do
# próprio JSON (e uma linha com `null` é distinguível de linha AUSENTE — é
# disto que depende "None ≠ não configurado"); na env, que só carrega texto,
# é esta palavra.
TXT_SEM_LIMITE = "ilimitado"

# 25-05 (2026-09-12) — o sentinela de "VOLTAR AO PADRÃO", gravado no kv.
#
# Até aqui não havia como LIMPAR um limite configurado: `db` expõe
# `kv_delete_user` (por usuário) e não um delete de chave GLOBAL, então uma
# vez gravado o valor vencia a env para sempre — limitação registrada no
# 25-03 e repetida no 25-04. E gravar `None` NÃO serve: `None` aqui é valor
# legítimo ("sem limite"), e usá-lo para as duas coisas transformaria "voltar
# ao padrão" em "plano ilimitado", que é o oposto do pedido.
#
# Por isso o sentinela: uma linha PRESENTE cujo conteúdo significa "não
# configurado". É o mesmo truque do `_AUSENTE` logo abaixo, agora atravessando
# o kv — e é mais barato que inventar um DELETE novo em `db.py` para uma
# chave global, que abriria a porta para apagar QUALQUER chave global.
#
# Não é valor aceitável de entrada: `_coerce_entrada` recusa a palavra como
# recusa qualquer outro texto. Quem restaura chama `restaurar_padrao_do_plano`.
TXT_PADRAO = "__padrao__"

# Funções de PRODUTO liberadas por plano (decisão D2 do 25-CONTEXT: RBAC é
# administração, plano é produto). Lista de chaves, não de permissões: a
# permissão `opcoes.criar_setup` sai de `GRUPOS["opcoes"]` no 25-04, e é lá que
# `require_criar_setup` passa a consultar o plano. Aqui a função só é
# DECLARADA — nada lê isto ainda.
FUNCOES_DE_PLANO = {
    "free": (),
    "pro": ("opcoes.criar_setup",),
}

# Candidatas registradas e NÃO implementadas — as duas que a docstring de
# `requires_subscription` já citava. Ficam nomeadas num lugar só para que a
# próxima função de produto não nasça como literal solta numa rota.
FUNCOES_CANDIDATAS = ("agente_autonomo", "analises_ilimitadas")


def _defaults_do_plano(plano_id: str) -> dict:
    """Os defaults declarados, na forma de dict de plano. Uma cópia só: os
    literais de `PLAN_FREE`/`PLAN_PRO` moram em `LIMITES_DE_PLANO`."""
    return {chave: padroes[plano_id] for chave, _kv, _env, _tipo, padroes in LIMITES_DE_PLANO}


# Limites por plano. None = ilimitado.
#
# ATENÇÃO: estes dicts carregam o DEFAULT de cada limite, não o valor vigente.
# O vigente (que respeita painel e env) vem de `limites_do_plano(id)`. Os dois
# primeiros continuam sendo lidos DAQUI pelos gates da Fase 12 — de propósito,
# porque este plano (25-03) não muda comportamento; o 25-04 é quem troca a
# fonte deles.
PLAN_FREE = {
    "id": "free",
    **_defaults_do_plano("free"),
    "byok_required": False,          # futuro: gratuito pode exigir BYOK
    "funcoes": FUNCOES_DE_PLANO["free"],
}
PLAN_PRO = {
    "id": "pro",
    **_defaults_do_plano("pro"),
    "byok_required": False,
    "funcoes": FUNCOES_DE_PLANO["pro"],
}

# ACTIVE_PLAN e o fallback de quem nao tem `user` (escopo anonimo, D-06) —
# aponta para PLAN_FREE, entao anonimo passa a valer os mesmos dois limites
# ativados acima (comportamento intencional, Fase 12).
ACTIVE_PLAN = PLAN_FREE

PLANOS_POR_ID = {"free": PLAN_FREE, "pro": PLAN_PRO}
_ORDEM_PLANO = ["free", "pro"]


# ---------------------------------------------------------------------------
# RESOLUÇÃO — memória → kv → env → default.
#
# Padrão copiado de `options_mcp_api._valor_e_origem` (a mais completa das
# quatro implementações do repo: valida POR CAMADA, recusa `bool`, expõe a
# `origem` e tem reset para os testes). Duas divergências, cada uma com razão:
#
#  1. lá, `<= 0` é lixo e cai para a camada de baixo, porque um `0` no teto do
#     serviço seria o freio DESLIGADO. Aqui `0` é valor LEGÍTIMO: é como um
#     plano bloqueia um ponto de controle. O que continua sendo lixo é o
#     negativo, o texto, o `bool` e o não-finito;
#  2. lá, `None` significa "não achei". Aqui `None` é o valor "sem limite", que
#     precisa passar pelas camadas. Por isso o sentinela é `_AUSENTE`, um
#     objeto próprio — usar `None` para as duas coisas transformaria "plano sem
#     limite" em "plano não configurado" no primeiro ida e volta pelo kv.
# ---------------------------------------------------------------------------
_AUSENTE = object()

# Cache em memória do valor vindo do KV — e só dele. Cachear a env mataria em
# silêncio a troca de limite sem redeploy; o default não precisa de cache.
# A chave pode guardar `None` (sem limite), então a consulta é por `in`, nunca
# por `.get() is None`.
_limites_mem: dict = {}


def reset_cache_planos() -> None:
    """Esquece o que veio do kv. Chamado por `configure_db` e pelos testes
    entre casos — é "processo novo" em miniatura: memória vazia, kv intacto."""
    _limites_mem.clear()


def _linha(chave: str) -> tuple:
    for linha in LIMITES_DE_PLANO:
        if linha[0] == chave:
            return linha
    raise ValueError(f"limite desconhecido: {chave!r}")


def kv_key(plano_id: str, chave: str) -> str:
    """`planoFree.watchlist`. O id do plano entra na chave para que dois
    planos não disputem o mesmo registro."""
    sufixo = _linha(chave)[1]
    return f"plano{plano_id.capitalize()}.{sufixo}"


def env_key(plano_id: str, chave: str) -> str:
    """O nome da env que vale para este plano. Com `{PLANO}` no molde, é por
    plano; sem, é a env global que já controla o ponto hoje."""
    return _linha(chave)[2].replace("{PLANO}", plano_id.upper())


def _numero_valido(v, tipo):
    """Valor aceitável, ou `_AUSENTE`. `bool` é recusado de propósito (`True`
    é `int` em Python, e um `True` no banco viraria limite 1)."""
    if isinstance(v, bool):
        return _AUSENTE
    if tipo is int:
        if not isinstance(v, int):
            return _AUSENTE
    else:
        if not isinstance(v, (int, float)):
            return _AUSENTE
        v = float(v)
        if not math.isfinite(v):
            return _AUSENTE
    if v < 0:
        return _AUSENTE
    return v


def _do_kv(chave_kv: str, tipo):
    """O que o painel gravou, ou `_AUSENTE`. Linha ausente e linha com `null`
    são coisas diferentes: a primeira é "não configurado", a segunda é "sem
    limite" — e é por isso que o default passado ao `kv_get` é um sentinela e
    não `None`."""
    if _conn is None:
        return _AUSENTE
    try:
        bruto = db.kv_get(_conn, chave_kv, _AUSENTE, user_id=None)
    except Exception:  # noqa: BLE001 — banco indisponível degrada, não derruba
        return _AUSENTE
    if bruto is _AUSENTE:
        return _AUSENTE
    if bruto is None:
        return None
    if isinstance(bruto, str):
        texto = bruto.strip().lower()
        if texto == TXT_SEM_LIMITE:
            return None
        # 25-05: "voltar ao padrão" — a linha existe, o valor diz que não há
        # configuração, e a decisão desce para env → default. EXPLÍCITO de
        # propósito: qualquer texto não-numérico já cairia em `_AUSENTE` pelo
        # `_numero_valido` abaixo, mas depender desse acidente faria o
        # mecanismo de restauração sumir no dia em que a validação mudasse.
        if texto == TXT_PADRAO:
            return _AUSENTE
    return _numero_valido(bruto, tipo)


def _do_env(nome: str, tipo):
    """O que a env declara, ou `_AUSENTE`. Lida A CADA leitura de propósito: é
    assim que o Railway troca um limite sem publicar código."""
    bruto = os.environ.get(nome)
    if bruto is None:
        return _AUSENTE
    texto = bruto.strip()
    if not texto:
        return _AUSENTE
    if texto.lower() == TXT_SEM_LIMITE:
        return None
    try:
        v = int(texto) if tipo is int else float(texto)
    except (TypeError, ValueError):
        return _AUSENTE
    return _numero_valido(v, tipo)


def _valor_e_origem(plano_id: str, linha: tuple) -> tuple:
    """O ÚNICO lugar que decide um limite vigente. A `origem` não é enfeite:
    sem ela o admin muda pelo painel, a env continua diferente, e ninguém sabe
    qual manda."""
    chave, _sufixo, _molde, tipo, padroes = linha
    chave_kv = kv_key(plano_id, chave)

    if chave_kv in _limites_mem:
        return _limites_mem[chave_kv], "kv"
    v = _do_kv(chave_kv, tipo)
    if v is not _AUSENTE:
        _limites_mem[chave_kv] = v
        return v, "kv"

    v = _do_env(env_key(plano_id, chave), tipo)
    if v is not _AUSENTE:
        return v, "env"

    return padroes[plano_id], "default"


def limites_do_plano(plano_id: str) -> dict:
    """Os limites VIGENTES do plano, cada um com a origem, a env que o declara,
    a chave de kv e o default. É o que a rota admin (25-05) publica e o que o
    gate (25-04) vai ler — nenhuma lista paralela na UI."""
    if plano_id not in PLANOS_POR_ID:
        raise ValueError(f"plano desconhecido: {plano_id!r}")
    fora = {}
    for linha in LIMITES_DE_PLANO:
        chave, _sufixo, _molde, tipo, padroes = linha
        valor, origem = _valor_e_origem(plano_id, linha)
        fora[chave] = {
            "valor": valor,
            "origem": origem,
            "env": env_key(plano_id, chave),
            "kv": kv_key(plano_id, chave),
            "default": padroes[plano_id],
            "tipo": "int" if tipo is int else "float",
        }
    return fora


def _coerce_entrada(valor, tipo):
    """Entrada do painel → valor persistível. Aceita `None`, a palavra
    `ilimitado` e número (inclusive como texto, que é o que um formulário
    manda). Levanta `ValueError` no resto.

    Divergência deliberada de `options_mcp_api._set_limite`, que faz
    `max(1, int(n))`: lá, clampar é proteger um teto físico compartilhado de
    quem digitou errado. Aqui um `0` é intenção de produto ("este plano não
    acessa isto") e um lixo é lixo — engolir em silêncio faria o painel
    confirmar uma configuração que não foi a pedida."""
    if valor is None:
        return None
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            raise ValueError("valor vazio: use `ilimitado` para sem limite")
        if texto.lower() == TXT_SEM_LIMITE:
            return None
        try:
            valor = int(texto) if tipo is int else float(texto)
        except (TypeError, ValueError):
            raise ValueError(f"valor invalido: {texto!r}")
    v = _numero_valido(valor, tipo)
    if v is _AUSENTE:
        raise ValueError(f"valor invalido: {valor!r}")
    return v


def set_limite_do_plano(plano_id: str, chave: str, valor):
    """Persiste no kv e invalida o cache. `None` (ou `ilimitado`) grava o
    `null` do JSON — linha PRESENTE com valor nulo, que é o que distingue
    "sem limite" de "não configurado" na leitura seguinte."""
    if plano_id not in PLANOS_POR_ID:
        raise ValueError(f"plano desconhecido: {plano_id!r}")
    _chave, _sufixo, _molde, tipo, _padroes = _linha(chave)
    v = _coerce_entrada(valor, tipo)
    chave_kv = kv_key(plano_id, chave)
    _limites_mem[chave_kv] = v
    if _conn is not None:
        try:
            db.kv_set(_conn, chave_kv, v, user_id=None)
        except Exception:  # noqa: BLE001 — vale neste processo; some no deploy
            pass
    return v


def coerce_limite(chave: str, valor):
    """A MESMA conversão que `set_limite_do_plano` aplica, exposta para quem
    precisa validar ANTES de gravar. A rota admin (25-05) valida tudo-ou-nada:
    metade da mudança de pé é pior que nenhuma, porque o admin não tem como
    saber qual metade. Levanta `ValueError` no lixo."""
    _chave, _sufixo, _molde, tipo, _padroes = _linha(chave)
    return _coerce_entrada(valor, tipo)


def valor_sem_painel(plano_id: str, chave: str) -> tuple:
    """`(valor, origem)` que passariam a valer se a configuração do painel
    sumisse — env → default, sem tocar no kv nem no cache.

    É o que a PRÉVIA do botão "voltar ao padrão" mostra: um "→ (padrão)" sem
    número faria o admin aplicar sem saber onde o valor vai cair, e "voltar ao
    padrão" não é zerar — é devolver a decisão às camadas de BAIXO, que podem
    ter uma env declarada."""
    if plano_id not in PLANOS_POR_ID:
        raise ValueError(f"plano desconhecido: {plano_id!r}")
    _chave, _sufixo, _molde, tipo, padroes = _linha(chave)
    v = _do_env(env_key(plano_id, chave), tipo)
    if v is not _AUSENTE:
        return v, "env"
    return padroes[plano_id], "default"


def restaurar_padrao_do_plano(plano_id: str, chave: str) -> tuple:
    """Desfaz a configuração do painel para este limite: grava o sentinela
    `TXT_PADRAO` e esquece o cache, devolvendo a decisão a env → default.

    Devolve `(valor, origem)` vigentes depois da restauração — e a origem
    NUNCA é `kv`, que é a prova observável de que o sentinela funcionou (ver
    `TXT_PADRAO` sobre por que não é um `DELETE` e por que não é `None`)."""
    if plano_id not in PLANOS_POR_ID:
        raise ValueError(f"plano desconhecido: {plano_id!r}")
    linha = _linha(chave)
    chave_kv = kv_key(plano_id, chave)
    # Sai do cache em vez de guardar o sentinela: `_valor_e_origem` consulta o
    # cache por `in` e devolveria a marca como se fosse valor.
    _limites_mem.pop(chave_kv, None)
    if _conn is not None:
        try:
            db.kv_set(_conn, chave_kv, TXT_PADRAO, user_id=None)
        except Exception:  # noqa: BLE001 — vale neste processo; some no deploy
            pass
    return _valor_e_origem(plano_id, linha)


def funcoes_do_plano(plano_id: str) -> set:
    """As funções de PRODUTO que o plano libera (D2). Plano desconhecido
    devolve conjunto vazio — fail-closed, igual ao que `current_plan` já faz
    ao cair para `free`."""
    return set(FUNCOES_DE_PLANO.get(plano_id, ()))


def current_plan(user: Optional[dict] = None) -> dict:
    """ADR-013: resolve pelo campo persistido `users.plan` (free|pro) em vez
    do ACTIVE_PLAN global fixo. A VALIDACAO do recibo de loja que decide esse
    campo continua pendente do ADR-010 — aqui so liga a leitura ao dado que
    ja existe em `db.users.plan` (default 'free'). O trecho "sem override
    manual nesta rodada" que estava aqui deixou de valer em 2026-09-12: o
    portal admin ganhou `POST /api/admin/users/{id}/plan` (permissao
    `usuarios.gerenciar`, auditado). O recibo de loja segue pendente — o
    override e manual e humano, nao e compra. `user=None` (anonimo) cai no
    fallback ACTIVE_PLAN, igual antes."""
    if not user:
        return ACTIVE_PLAN
    return PLANOS_POR_ID.get(user.get("plan") or "free", PLAN_FREE)


# ---- GATES DE PLANO (ATIVOS desde a v1.3 para o PLAN_FREE) ----
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de tamanho da watchlist no tier gratuito.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)


def can_grow_watchlist_to(final_size: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: variante EM MASSA de can_add_ticker, para PUT /api/watchlist
    (WR-02, 12-REVIEW.md). `can_add_ticker(current_count, ...)` documenta
    `current_count` como "quantos itens existem ANTES desta adição" — semantica
    de item-a-item que nao existe numa troca em massa (o PUT substitui a lista
    inteira de uma vez). O call site antigo reusava esse hook passando
    `len(final) - 1` só para fazer a comparacao `>=` coincidir com "bloqueia
    sse o tamanho FINAL ultrapassa o limite"; estava aritmeticamente certo,
    mas por coincidencia com o operador atual, nao pelo contrato da funcao.
    Aqui a checagem é honesta: recebe o tamanho FINAL e compara direto.
    Retorna (permitido: bool, motivo: str|None)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and final_size > limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)


def can_analyze(used_this_month: int, plan: Optional[dict] = None) -> tuple:
    """HOOK: limite de analises/mes no tier gratuito.
    Retorna (permitido: bool, motivo: str|None).

    Esta funcao NUNCA mantem contador proprio — `used_this_month` e sempre
    fornecido pelo chamador. O contador real de uso de IA e o de
    `metering.py` (cota diaria); quando o limite mensal for ativado, o valor
    aqui tem de vir do ledger de `metering` (C-33, fase 5)."""
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_analyses_per_month")
    if limit is not None and used_this_month >= limit:
        return (False, f"Voce atingiu o limite de {limit} analises/mes do plano {plan['id']}.")
    return (True, None)


def requires_subscription(feature: str, user: Optional[dict] = None) -> bool:
    """HOOK: gate de assinatura por recurso premium (ex.: 'agente_autonomo',
    'analises_ilimitadas'). HOJE: nunca exige. FUTURO: validar recibo da loja."""
    return False
