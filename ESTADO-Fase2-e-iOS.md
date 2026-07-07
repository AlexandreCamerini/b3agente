# Estado salvo — Fase 2 (multiusuário) + UIScene (iOS) + Fase 3 (COMPLETA)

## Construído e validado aqui (gate verde)
**Fase 2 — multiusuário**: schema `users`/`sessions`, KV escopado por usuário
(anônimo/legado preservado), `auth.py` (e-mail/senha PBKDF2 + sessões + OIDC
opcional), `/api/auth/*` + `DELETE /api/account`, semeadura de 1º login com BYOK
preservado. Cliente: `api.js` (Bearer), `sync.js` (cache + fila offline),
`persistence.js` (superfície `auth`), `App.jsx` (`AuthModal` + item Conta).

**iOS / UIScene**: `scripts/ios-adopt-uiscene.sh` embute o `SceneDelegate` no
`AppDelegate.swift` (evita o problema de target → tela preta) + manifest limpo.

**Fase 3 — item 2 (IA gerenciada)**: `managed.py` (config via env, chave
server-side), `metering.py` (cota diária + rate limit por usuário no KV escopado),
gate nas 3 rotas de análise (BYOK tem prioridade e não consome cota; logado sem
BYOK cai na gerenciada; 402 ao estourar), `GET /api/ai/quota`, `aiQuota` no
`api.js` e nos dois stores.

**Fase 3 — item 1 (escopo por usuário no aparelho)**: backend já escopado na
Fase 2; no device, login passa a um **namespace por usuário** no localStorage
(anônimo **inalterado** — sem migração, sem risco de tela branca; 1º login adota o
doc anônimo como semente; logout volta ao anônimo).

**Fase 3 — item 3 (disclaimers nos sinais)**: rodapé fixo discreto sob cada sinal
(no `KpiBlock`, sob COMPRA/VENDA/ESPERAR). Texto: "Sinal gerado para fins
educacionais — não é recomendação de compra ou venda." String estática (sem risco
de tela branca); troca o texto numa linha do `App.jsx`.

Suítes verdes: backend `test_metering/test_auth/test_multiuser/test_persistence/
test_kpi/test_indicators/test_tickers` + `py_compile`; web `test_auth_sync/
test_api_parity/test_migrate` + `node --check`; balance do `App.jsx`; `bash -n`.

## Pendente (seu lado — gates de device antes de prosseguir)
1. **Hard-stop Fase 2**: criar/login/logout/excluir, 2 usuários isolados,
   pré-existente sem tela branca, dados sobrevivem a redeploy (volume Railway).
2. **Hard-stop Fase 3**: cota gerenciada bloqueia/BYOK destrava; 2 logins no mesmo
   aparelho com dados locais isolados; logout volta ao anônimo; rodapé do sinal OK.
3. **Railway**: `B3_MANAGED_LLM_*` (se quiser IA gerenciada) + volume em `/data`
   com `B3_DB_PATH=/data/b3_agente.db`. Detalhes no runbook.
