"""Varredura de rotas e de dependências do app FastAPI — insumo COMPARTILHADO
dos guardiões de cobertura de permissão. NÃO é um arquivo de teste: nenhuma
asserção mora aqui (`pytest` ignora, o nome não casa `test_*`).

2026-09-10 (auditoria A-17) — por que este módulo existe. As duas funções
abaixo estavam duplicadas em `test_adr013_cobertura_rotas.py` e
`test_mcp_guardioes.py`, com a cópia justificada por "guardião não importa
guardião". A justificativa é boa e continua valendo — o que este módulo faz é
atendê-la SEM a terceira cópia: ninguém aqui afirma nada, então nenhum
guardião depende do veredito de outro; os dois dependem do mesmo insumo.

A divergência entre as cópias foi exatamente o defeito A-17: a cópia do
`test_mcp_guardioes` já resolvia o router aninhado, a do ADR-013 não, e a do
ADR-013 — o guardião de SEGURANÇA — era a que passava cega. Fonte única
impede que a correção viva só num dos lados outra vez.

Quem mexer aqui quebra os DOIS guardiões de uma vez, e de forma ruidosa: ambos
travam a vacuidade (contagem mínima e presença de rotas de router conhecidas),
então uma varredura sabotada para devolver lista vazia FALHA, não passa.
"""


def nomes_dependencias(dependant, vistos=None) -> set:
    """Nomes de TODAS as dependências da rota, recursivo.

    Recursivo porque `Depends()` aninha: `require_permission()` devolve uma
    closure `_dep` que por sua vez depende de `require_user`. `vistos` corta
    ciclo (dependency que reaparece) em vez de estourar a pilha."""
    vistos = vistos if vistos is not None else set()
    out: set = set()
    if dependant is None or id(dependant) in vistos:
        return out
    vistos.add(id(dependant))
    for d in getattr(dependant, "dependencies", None) or []:
        call = getattr(d, "call", None)
        if call is not None:
            out.add(getattr(call, "__name__", str(call)))
        out |= nomes_dependencias(d, vistos)
    return out


def todas_as_rotas(rotas, vistos=None) -> list:
    """Achata `app.routes` RECURSIVAMENTE.

    ACHADO 2026-09-09 (aba-opcoes F1), confirmado como A-17 na auditoria de
    2026-09-10: com fastapi 0.141.1 / starlette 1.6.0, `include_router()` NÃO
    copia as rotas para `app.routes` — ele insere um objeto `_IncludedRouter`,
    com o `APIRouter` original pendurado em `.original_router`. Um guardião que
    varre só `app.routes` procurando `.path` fica CEGO para toda rota
    registrada por router e passa por vacuidade, que é o modo mais silencioso
    de um guardião falhar. Medido no worktree desta correção: 105 objetos em
    `app.routes`, 102 com `.path` (varredura rasa) e 110 na recursiva — 7
    rotas invisíveis, 4 em `/api/options/*` e 3 em `/api/options/mcp/*`.
    """
    vistos = vistos if vistos is not None else set()
    fora = []
    for r in rotas or []:
        if id(r) in vistos:
            continue
        vistos.add(id(r))
        if getattr(r, "path", None) is not None:
            fora.append(r)
        interno = getattr(r, "original_router", None)
        if interno is not None:
            fora.extend(todas_as_rotas(getattr(interno, "routes", None), vistos))
        elif getattr(r, "routes", None):
            fora.extend(todas_as_rotas(r.routes, vistos))
    return fora


# Rotas registradas por `include_router()` — as que a varredura rasa NÃO vê.
# Servem de âncora anti-vacuidade nos guardiões: se a varredura voltar a ser
# rasa (ou a devolver lista vazia), a ausência destas falha o teste em vez de
# deixá-lo passar sem ter olhado nada. Uma delas é pública por desenho
# (`/api/options/chain`), a outra é gated (`/api/options/mcp/status`) — de
# propósito, uma de cada lado da decisão que o guardião existe para cobrar.
ANCORAS_DE_ROUTER = {
    ("GET", "/api/options/chain/{ticker}"),
    ("GET", "/api/options/mcp/status"),
}
