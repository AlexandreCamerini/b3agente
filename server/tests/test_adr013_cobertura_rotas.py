"""ADR-013 (Decisão 5b) — mitigação do risco "permissão vazando por rota
esquecida": enumera TODAS as rotas do app e falha se alguma não tiver
uma dependency reconhecida (current_scope, require_user, ou um wrapper de
require_permission/require_plan/require_any_admin_permission — todos
retornam uma closure interna chamada `_dep`) e não estiver na allowlist
explícita de "pública, dado de mercado/estático/entrada de auth".

A allowlist abaixo É o baseline da Etapa 2 do ADR-013 (tabela de 76 rotas,
categoria PÚBLICO) — rota nova sem dependency E sem entrada aqui quebra o
teste, força uma decisão consciente em vez de omissão silenciosa.

2026-09-10 (auditoria A-17) — ESTE GUARDIÃO FOI PROVADO CEGO. Varria
`app.routes` procurando `.path`, e o `_IncludedRouter` do fastapi 0.141 tem
`.path is None`: 7 rotas registradas por `include_router()` eram invisíveis (4
em `/api/options/*`, 3 em `/api/options/mcp/*`). O auditor removeu o
`require_user` da rota de status do MCP e este teste PASSOU; o guardião irmão
(`test_mcp_guardioes.py`) falhou corretamente, nomeando a rota. Ou seja: era
possível publicar rota de opções sem exigir sessão sem nenhum teste do ADR-013
reclamar.

Correção: a varredura virou a recursiva de `tests/rotas_fastapi.py` (fonte
única, antes duplicada aqui e no guardião do MCP — a divergência ENTRE as duas
cópias era o defeito). Junto entrou trava de VACUIDADE: contagem mínima de
rotas e presença explícita de rotas de router conhecidas. Sem ela, um guardião
de cobertura "passa" quando não olha nada, que é o modo mais silencioso de
falhar. Nada foi apagado deste arquivo — a allowlist não mudou (ver nota em
`test_allowlist_publica_nao_cresce_sem_atualizar_este_teste`).
"""
from app.main import app

from .rotas_fastapi import ANCORAS_DE_ROUTER, nomes_dependencias, todas_as_rotas

_PUBLICAS_CONHECIDAS = {
    ("POST", "/api/auth/register"), ("POST", "/api/auth/login"), ("POST", "/api/auth/oauth"),
    ("POST", "/api/auth/logout"), ("GET", "/api/ai/models"),
    ("GET", "/.well-known/apple-app-site-association"), ("GET", "/api/fundamentals/{ticker}"),
    ("GET", "/api/scan/progress"), ("GET", "/privacidade"), ("GET", "/privacy"),
    ("GET", "/ios/manifest.plist"),
    ("GET", "/api/options/expirations/{ticker}"), ("GET", "/api/options/chain/{ticker}"),
    ("GET", "/api/options/gate/{ticker}"), ("POST", "/api/options/analyze"),
    # ADR-014: troca o código de handoff (curto, uso único, minted só por quem
    # já passou por require_any_admin_permission em /mobile-handoff) por uma
    # sessão plena — a segurança está no código em si, não numa dependency
    # de rota; sem sessão prévia não há como chegar aqui com um código válido.
    ("POST", "/api/admin/mobile-handoff/exchange"),
    # Fase 2 (02-02, MERC-01/T-02-08): status de pregão é dado PÚBLICO de
    # calendário (aberto/fechado, horários) — nenhum user_id, nenhuma
    # carteira. Consumida pela tela de LOGIN, antes de autenticar (D-08).
    ("GET", "/api/market/status"),
    # ADR-23 (Fase 4): relying party do portal semente.id — mesma classe dos
    # /api/auth/* acima (pré-sessão, por natureza). /inicio é um redirect
    # público (503 sem config); /callback recebe code/state/error direto do
    # portal, também antes de haver sessão — a segurança está no state PKCE
    # de uso único + validação do id_token, não numa dependency de rota.
    ("GET", "/api/auth/semente-id/inicio"), ("GET", "/api/auth/semente-id/callback"),
}


# A-17: `_nomes_dependencias` morava aqui e era COPIADA no guardião do MCP.
# Agora as duas lêem de `tests/rotas_fastapi.py`. O alias mantém o nome antigo
# para quem leu este arquivo antes (e para a prova de cegueira invertida, que
# referencia o helper por nome).
_nomes_dependencias = nomes_dependencias

# Piso da varredura. Número de 2026-09-10: 110 rotas na recursiva (102 na rasa
# que este guardião usava). O piso é folgado de propósito — não é um contador
# de rotas (rota removida não deve quebrar o teste), é um detector de varredura
# que parou de encontrar coisa.
_MINIMO_DE_ROTAS = 90


def _rotas_da_api():
    """(método, path, nomes das dependências) de toda rota de API do app —
    incluindo as registradas por `include_router()` (A-17)."""
    fora = []
    for route in todas_as_rotas(app.routes):
        path = getattr(route, "path", None)
        if not path or not path.startswith(("/api", "/.well-known", "/privac", "/ios")):
            continue
        nomes = nomes_dependencias(getattr(route, "dependant", None))
        for metodo in getattr(route, "methods", None) or set():
            if metodo == "HEAD":
                continue
            fora.append((metodo, path, nomes))
    return fora


def test_a17_a_varredura_enxerga_rota_registrada_por_router():
    """Trava de VACUIDADE — é este teste que impede o A-17 de voltar. Um
    guardião de cobertura que varre a coisa errada passa sem olhar nada; aqui
    a ausência das rotas de router FALHA, e a mensagem diz por quê."""
    todas = _rotas_da_api()
    assert len(todas) >= _MINIMO_DE_ROTAS, (
        "a varredura encontrou só %d rotas de API — ela parou de achar o que "
        "deveria (com fastapi 0.141, varrer `app.routes` por `.path` perde "
        "toda rota de `include_router()`). Use `todas_as_rotas` de "
        "tests/rotas_fastapi.py." % len(todas)
    )
    vistas = {(m, p) for m, p, _ in todas}
    faltando = ANCORAS_DE_ROUTER - vistas
    assert not faltando, (
        "rota(s) registrada(s) por `include_router()` invisível(eis) para este "
        "guardião — é exatamente o A-17 (o `_IncludedRouter` do fastapi tem "
        "`.path is None`): " + repr(sorted(faltando))
    )


def test_toda_rota_de_api_tem_gate_reconhecido_ou_esta_na_allowlist():
    RECONHECIDAS = {"current_scope", "require_user", "_dep"}
    sem_gate = []
    for metodo, path, nomes in _rotas_da_api():
        chave = (metodo, path)
        tem_gate = bool(nomes & RECONHECIDAS)
        if not tem_gate and chave not in _PUBLICAS_CONHECIDAS:
            sem_gate.append((chave, sorted(nomes)))
    assert not sem_gate, (
        "rota(s) sem nenhuma dependency de identidade reconhecida e fora da "
        "allowlist pública — decida explicitamente (gate ou allowlist), não "
        "deixe cair no limbo: " + repr(sem_gate)
    )


def test_allowlist_publica_nao_cresce_sem_atualizar_este_teste():
    """Se uma rota que HOJE está na allowlist ganhar uma dependency de
    verdade, ótimo — mas se o INVERSO acontecer (uma rota gated perder a
    dependency sem ninguém notar), o teste acima já pega. Este segundo teste
    cobre o caminho raro de uma rota nova nascer SEM dependency E já
    entrar direto na allowlist por engano: o tamanho serve de sinal humano
    de "isso cresceu, foi você que decidiu?" — não é uma trava rígida."""
    # 17 + 2 (ADR-23, Fase 4: GET /api/auth/semente-id/inicio e /callback,
    # 2026-08-30) — crescimento deliberado, revisado nesta mesma quick task.
    #
    # 2026-09-10 (auditoria A-17): a varredura passou a enxergar 7 rotas que
    # eram invisíveis, e a allowlist NÃO precisou crescer — conferido rota por
    # rota. As 4 de `/api/options/*` que são públicas por desenho (dado de
    # mercado, sem user_id: `GET expirations/{ticker}`, `GET chain/{ticker}`,
    # `GET gate/{ticker}`, `POST analyze`) JÁ estavam listadas acima, escritas
    # quando a aba Opções entrou; só nunca haviam sido de fato exercitadas por
    # este guardião. As outras 3 (`/api/options/mcp/status`,
    # `/mcp/leitura/{ticker}`, `/mcp/setups/{name}/grafico`) têm
    # `require_user` e passam pelo gate, sem entrar na allowlist. Por isso o
    # número continua 19: nenhuma rota foi promovida a pública nesta correção.
    assert len(_PUBLICAS_CONHECIDAS) == 19
