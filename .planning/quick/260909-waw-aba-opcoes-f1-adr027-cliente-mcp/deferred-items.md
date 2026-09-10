# Itens fora do escopo — descobertos em 260909-waw (aba-opcoes F1)

## D-1 — `test_adr013_cobertura_rotas` está CEGO para rotas de router (fastapi 0.141.1)

**Severidade:** alta (guardião de segurança passando por vacuidade)
**Descoberto em:** Task 3, ao escrever o guardião (iv) de `test_mcp_guardioes.py`.

Com `fastapi==0.141.1` / `starlette==1.6.0`, `app.include_router()` **não**
achata as rotas em `app.routes`: ele insere um objeto `_IncludedRouter`, cujo
`.path` é `None` e cujo `APIRouter` original fica pendurado em
`.original_router`.

`test_adr013_cobertura_rotas.py` varre `app.routes` procurando `.path` e pula
o que não tem — ou seja, **nenhuma rota registrada por `include_router` é
verificada hoje**. Isso vale para `options_router` (`/api/options/expirations`,
`/chain`, `/gate`, `/analyze`) desde que a resolução do fastapi passou para a
1.4x, e passaria a valer para `/api/options/mcp/status`.

Verificado no worktree:

```
from app.main import app
[p for p in (str(getattr(r, "path", "") or "") for r in app.routes) if "expirations" in p]
# => []
```

**Por que NÃO foi corrigido aqui:** (a) `test_adr013_cobertura_rotas.py` não
está em `files_modified` desta quick; (b) fazer o guardião enxergar as rotas
de router pode revelar rotas hoje sem gate reconhecido, o que expandiria a
allowlist (que o plano manda deixar em 19) e o escopo desta fase por completo.
É mudança arquitetural de guardião de segurança — decisão do Alex (Rule 4).

**Como corrigir quando for a hora:** reusar o helper `_todas_as_rotas` que já
está escrito em `server/tests/test_mcp_guardioes.py` (descida recursiva por
`original_router.routes`), rodar o guardião com ele e decidir caso a caso as
rotas que aparecerem sem gate.

**Nota de risco imediato:** as rotas de `options_router` que a allowlist já
declara públicas (`expirations`, `chain`, `gate`, `analyze`) continuam sendo
públicas de fato — o que se perdeu foi a VERIFICAÇÃO, não o gate. A rota nova
`/api/options/mcp/status` tem gate próprio e guardião próprio (iv), então não
depende disso.
