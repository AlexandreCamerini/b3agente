# QA 24 — FASE 8B (noite): mecânica de identidade redesenhada e refatorada
*09/07/2026 · build F8B-20260709-2 · baseline verde antes de mexer*

## Sintomas relatados → causas-raiz encontradas

### 1. "Só parte da aplicação é configurada para a nova identidade"
- **Causa A (gráficos):** os componentes de gráfico/canvas não resolvem
  `var(--x)` e liam `usePalette()` — que devolvia a paleta CRUA do tema, sem o
  override do modo. Resultado: UI verde, gráficos AZUIS. **Fix:** `ThemeCtx`
  agora carrega `{tema, modo}` e `usePalette()` mescla `MODE_OPERADOR` —
  identidade completa em TODAS as superfícies, inclusive canvas.
- **Causa B (superfícies esquecidas):** kicker "SETUPS NA SUA WATCHLIST",
  botões "Levar para a watchlist/Ver Watchlist", título do DeepModal
  ("leitura da IA" × "plano da mesa") e os CONFIRMAR dos modais de
  compra/venda estavam hardcoded. Migrados para o copy.js (31 chaves
  espelhadas agora).

### 2. "A identidade se perde; preciso sair e entrar de novo"
- **Causa-raiz (iOS local-first violado):** o boot (`auth.me`) e os handlers
  de login/registro/oauth faziam `setData(r.state)` com o estado do
  **SERVIDOR** — mas no iPhone a fonte da verdade é o APARELHO. Como o
  `deviceStore.putConfig` grava só localmente, o `appMode/termo/risco` do
  aparelho era SOBRESCRITO pelo estado do servidor a cada boot/login — a
  identidade "se perdia" exatamente como você descreveu.
- **Fix:** no nativo, o estado pós-auth vem SEMPRE do deviceStore
  (`loadState()`, com o namespace já trocado); o estado do servidor só vale no
  web. Guardião tranca os 4 pontos (boot + 3 handlers).

### 3. "Não apresenta a tela inicial"
- Trocar de modo deixava o usuário parado no Perfil — metade da identidade
  nova ficava invisível. **Fix:** ativar/trocar o modo agora navega para a
  HOME (`A.go("evolucao")`): tema + chip + saudação + abas aparecem juntos,
  no primeiro segundo.

### 4. Tela de login unificada (pedido)
- Existiam DOIS formulários (Welcome e AuthModal) com estados e textos
  divergentes. **Refatorado:** `AuthForm` único (social + e-mail/senha +
  alternância entrar/criar + erro + lastEmail), usado pelas duas superfícies;
  o Welcome mantém o hero/"usar sem conta", o modal mantém a gestão da conta.
  Contrato no guardião: `saveLastEmail` em exatamente 1 ponto; `<AuthForm>` em
  exatamente 2 superfícies.

### 5. Prompts/instruções LLM por modo (exemplo que você citou)
- A coleção editável `llmPrompts` tinha só a versão educacional do stop/alvo.
  **Agora:** `carteiraStopAlvoOperador` (voz de mesa: stop na invalidação
  técnica, R:R mínimo 1,5:1, "não operar também é posição") nos DEFAULTS dos
  dois lados (catalog.js + defaults.py, com backfill automático para contas e
  aparelhos existentes); a rota e o cliente escolhem a versão pelo modo (com
  fallback); a tela de prompts mostra e edita OS DOIS separadamente
  ("Modo Estudo (professor)" × "Modo Operador (mesa)"). Somado ao que já
  existia (personas/N1/N2/guardrails por modo da rodada anterior), TODAS as
  instruções de IA agora têm as duas vozes.

## Testes
- `test_copy_theme.mjs` estendido: **+16 asserções** (usePalette com modo,
  local-first no auth, navegação pós-troca, prompts por modo nas 4 pontas,
  superfícies N5).
- `test_radar.mjs` atualizado para o contrato da unificação do login.
- Regressão: **19 suítes backend offline + 21 web — 0 falhas** · py_compile +
  parse JSX ok.
- Build: **F8B-20260709-2** (rodapé do Perfil e /api/health).

## Hard stop (aparelho, após deploy + npm run ios + reinstalar)
1. Conferir `build F8B-20260709-2` no rodapé do Perfil.
2. Trocar para Operador → cai na HOME com TUDO trocado (tema, gráficos,
   chip, saudação, abas, botões). Fechar e reabrir o app: CONTINUA operador.
3. Entrar/sair da conta: o modo do aparelho não muda mais sozinho.
4. Stop/alvo (IA) numa posição: voz de mesa no operador, professor no estudo;
   Perfil → prompts mostra os dois textos.
5. Login: welcome e modal são o MESMO formulário (e-mail lembrado nos dois).
