# QA 32 — Página intermediária de login, cópia do e-mail oculto, e propostas de UX
*09/07/2026 · build alvo: F9-20260709-8*

Pedido do Alex, usando como referência de rigor a persona "Apple Product
Engineer Sênior" (Modo A — Descoberta/MVP, Modo C — Experiência/HIG)
rascunhada em outra sessão: dois bugs concretos + validação de uma proposta
de reorganização de UX.

## 1. Bug: página intermediária entre login e o app

### Causa-raiz
`WelcomeAuthScreen` (`App.jsx`) é o "portão de entrada" do app — por decisão
de produto anterior (comentário original: "BLOCO 2: o welcome é o PORTÃO DE
ENTRADA do app — aparece SEMPRE no boot... independente de sessão ativa"),
ele aparecia em TODO boot, mesmo para quem já tinha sessão salva e
restaurada com sucesso (`auth.me()` confirmando o usuário). Nesse caso a
tela mostrava "Conectado como X" + um botão "Entrar" que o usuário tinha que
tocar manualmente antes de ver qualquer coisa do app — um toque extra sem
propósito, já que a sessão JÁ confirma quem é o usuário.

### Fix
`web/src/App.jsx`, `useEffect` que resolve `auth.me()` no boot: quando a
sessão restaura com sucesso (`r.user` presente), fecha o portão sozinho
(`setWelcomeAuthOpen(false)`) e marca `welcomeShownRef.current = true` ANTES
do outro efeito (boot gate, que depende de `data`) rodar — sem isso ele
reabriria a tela ao ver a ref ainda falsa. Cobre as duas ordens de corrida
possíveis entre o carregamento de `data` e a resolução de `auth.me()`.

Escopo do fix: só usuários AUTENTICADOS com sessão restaurada. Usuários
anônimos que já escolheram "Usar sem conta" anteriormente CONTINUAM vendo o
portão em todo boot (mesmo comportamento de antes) — não mudei esse
caminho porque o pedido do Alex foi especificamente sobre login; ver seção
5 (proposta) para estender o mesmo raciocínio lá também, se fizer sentido.

### Guardião
`web/tests/test_login_intermediary_page.mjs` — tranca que o bloco de
sucesso do `auth.me()` sempre marca `welcomeShownRef.current = true` e
chama `setWelcomeAuthOpen(false)`.

## 2. Cópia: "e-mail oculto" como título soa como erro

### Achado
A lógica de detectar e-mail de relay da Apple (`@privaterelay.appleid.com`)
já existia e está CORRETA (mostra o nome quando disponível; para conta Apple
com "Ocultar e-mail" sem nome salvo, mostra um rótulo + explicação). O
problema é que o rótulo usado como TÍTULO era "Conta Apple (e-mail oculto)"
— a palavra "oculto" como primeira coisa que a pessoa lê soa como algo
quebrado, não como uma escolha de privacidade normal.

### Fix
Título trocado para o neutro **"Sua conta Apple"** nos 3 lugares que usavam
o rótulo antigo (modal "Sua conta", `WelcomeAuthScreen`, `DrillRow` de
Conta no Perfil). A explicação detalhada do relay (que já existia, no modal
de conta: "Você entrou com a Apple usando Ocultar e-mail... para
compartilhar o e-mail verdadeiro: Ajustes →...") **não mudou** — ela
continua disponível pra quem quiser entender/reverter, só não é mais o
título em destaque.

### Guardião
`web/tests/test_login_intermediary_page.mjs` (mesmo arquivo) — tranca que
`"(e-mail oculto)"` não aparece mais em lugar nenhum do fonte e que o novo
rótulo aparece nos 3 pontos esperados.

## 3. Paletas Estudo × Operador "ainda iguais" — causa-raiz encontrada

### Achado (comparação hex a hex contra o mock aprovado)
Comparando `PALETTE`/`MODE_OPERADOR` no código com os valores do mock
`dois-apps-em-um.html`, dois problemas reais:

1. **Tema CLARO (light) não tinha diferenciação nenhuma além de
   acento/positivo/negativo.** `MODE_OPERADOR.light` só sobrescrevia 3
   chaves (`accent`, `positive`, `negative` + tints) — `bgBase`, `bgPanel`,
   `bgCard`, bordas e todos os tons de texto (`textMuted`/`textDim`/
   `textFaint`) ficavam EXATAMENTE iguais ao Modo Estudo em tema claro. Se
   o Alex testou em tema claro, Estudo e Operador realmente pareciam quase
   idênticos — não era impressão, era um gap real de implementação (o
   override em dark existia desde uma fase anterior; o de light nunca foi
   completado).
2. **Mesmo em tema escuro, a diferenciação além do acento é sutil por
   design do próprio mock** — `bgBase`/`bgPanel`/`textMuted`/`textFaint` no
   mock aprovado já eram muito próximos entre os dois modos (ex.:
   `--muted` do mock: `#9aa6b6` no Estudo vs `#93a5ad` no Operador — quase
   a mesma cor). A diferenciação "impossível de confundir" do mock vem
   quase inteiramente do ACENTO (âmbar vs verde no mock original) + do chip
   permanente no header — não do fundo/texto.

### Fix aplicado agora (não é decisão de design, é completar o que faltava)
`MODE_OPERADOR.light` ganhou as mesmas chaves de chrome que o dark já tinha
(`bgBase #eef1f0`, `bgPanel #f6f8f7`, `bgCard #ffffff`, bordas e textos mais
frios/esverdeados que o Estudo), seguindo a MESMA lógica relativa que o dark
já usava. Isso é objetivamente conserto de um buraco, não uma escolha de
gosto — por isso apliquei direto.

### Guardião
`web/tests/test_mode_operador_light_palette.mjs` — tranca que
`MODE_OPERADOR.light` define `bgBase`/`bgPanel`/`bgCard`/`borderSubtle`/
`textMuted`/`textDim`/`textFaint`, e que o `bgBase` do Operador é diferente
do Estudo em tema claro.

### Decisões do Alex (AskUserQuestion) sobre as propostas
- **Paleta**: só o que já foi corrigido acima (chrome completo em claro e
  escuro). Não mexer mais por enquanto — nem contraste mais forte no escuro,
  nem recuperar o acento âmbar original do mock.
- **Badge "MODO OPERADOR"**: trocar de pill SÓLIDO pra CONTORNADO (borda +
  `accentTint` translúcido, mesmo padrão já usado em botões/filtros
  selecionados no resto do app) — IMPLEMENTADO nesta rodada.
  `web/src/App.jsx` (`Topbar`): `background: T.accent` → `border: 1px
  solid T.accent` + `background: T.accentTint` + `color: T.accent`.
  Guardião novo: `test_mode_badge_outlined.mjs`. Isso também obrigou
  atualizar uma asserção antiga em `test_copy_theme.mjs` (R3) que travava
  o padrão sólido anterior — trocada para o padrão contornado.
- **Reorganização do Perfil**: Alex pediu pra ver um mockup antes de
  decidir — mockup gerado no chat (hub proposto com 6 áreas: Conta, Conta &
  preferências slim, Configurações de IA, Notificações, Eficiência da IA,
  Logs & debug). Aguardando aprovação antes do refactor de navegação
  (task #27).

## 4. Validação da proposta de reorganizar o Perfil em áreas dedicadas

Mapeamento do estado ATUAL do hub de Perfil (`PerfilHub`/`ConfigScreen`/
`ObservabilidadeScreen`) contra a proposta do Alex (Notificações /
Configurações de IA / Eficiência da IA / Logs e Debug) — feito na resposta
de chat, com a estrutura completa das 7 seções hoje empilhadas dentro de
"Conta & preferências" (Personalização, Período de candles, Orçamento,
Perfil do operador, Servidor do app, Diagnóstico QA/notificações, Modelo de
IA do agente) como evidência de que a tela realmente virou um monólito.
Proposta de 5 áreas trazida para validação — não implementada ainda
(mudança grande de navegação, precisa de aval antes do refactor).

## 5. Testes

```
Backend (offline, sandbox sem rede): 20/20 — 0 falhas, 1 pulada.
Web: 29/29 arquivos — 0 falhas (26 anteriores + test_login_intermediary_page.mjs
+ test_mode_operador_light_palette.mjs + test_mode_badge_outlined.mjs;
test_copy_theme.mjs R3 atualizado pro padrão contornado do badge).
```
Sintaxe verificada via `@babel/parser` (modo JSX) — sem erro.

## 6. Build

`web/src/version.js`: `BUILD_ID` `F9-20260709-7` → **`F9-20260709-8`**.

## 7. Roteiro de hard stop

1. `bash entregar.sh "qa/32: login sem página intermediária, cópia do e-mail, paleta light do Operador"` (no Mac).
2. Xcode: ⇧⌘K + Run no iPhone físico.
3. Perfil → rodapé → confirmar **F9-20260709-8**.
4. Fechar o app e reabrir com uma conta já logada → deve cair DIRETO na tela
   principal, sem tela de "Conectado como X + Entrar".
5. Perfil → Conta (com conta Apple/e-mail oculto, se tiver uma de teste) →
   conferir que o título não diz mais "(e-mail oculto)".
6. Ativar tema claro + Modo Operador → conferir que agora o fundo/cartões/
   texto ficam visivelmente diferentes do Modo Estudo (antes ficavam quase
   idênticos em tema claro).

## 8. Pendente

Fase B da eficiência (trades reais). Propostas de badge/paleta-avançada/
reorganização do Perfil em 5 áreas — aguardando decisão do Alex (ver chat)
antes de implementar. Itens B(resto)/C/D/E da matriz qa/26. Fraseologia
(copy.js) contra os mocks. Radar sem "análise inicial rápida". "Desenhar o
prompt como especialista no Claude" (escopo ainda não confirmado).
