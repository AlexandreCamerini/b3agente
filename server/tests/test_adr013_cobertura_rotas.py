"""ADR-013 (Decisão 5b) — mitigação do risco "permissão vazando por rota
esquecida": enumera TODAS as rotas de app.routes e falha se alguma não tiver
uma dependency reconhecida (current_scope, require_user, ou um wrapper de
require_permission/require_plan/require_any_admin_permission — todos
retornam uma closure interna chamada `_dep`) e não estiver na allowlist
explícita de "pública, dado de mercado/estático/entrada de auth".

A allowlist abaixo É o baseline da Etapa 2 do ADR-013 (tabela de 76 rotas,
categoria PÚBLICO) — rota nova sem dependency E sem entrada aqui quebra o
teste, força uma decisão consciente em vez de omissão silenciosa.
"""
from app.main import app

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
}


def _nomes_dependencias(dependant, vistos=None):
    """Nomes de TODAS as dependências, recursivo (Depends() aninhado — é o
    caso de require_permission(): o _dep interno depende de require_user)."""
    vistos = vistos if vistos is not None else set()
    out = set()
    if dependant is None or id(dependant) in vistos:
        return out
    vistos.add(id(dependant))
    for d in getattr(dependant, "dependencies", None) or []:
        call = getattr(d, "call", None)
        if call is not None:
            out.add(getattr(call, "__name__", str(call)))
        out |= _nomes_dependencias(d, vistos)
    return out


def test_toda_rota_de_api_tem_gate_reconhecido_ou_esta_na_allowlist():
    RECONHECIDAS = {"current_scope", "require_user", "_dep"}
    sem_gate = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if not path or not path.startswith(("/api", "/.well-known", "/privac", "/ios")):
            continue
        nomes = _nomes_dependencias(getattr(route, "dependant", None))
        for metodo in methods:
            if metodo == "HEAD":
                continue
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
    assert len(_PUBLICAS_CONHECIDAS) == 16
