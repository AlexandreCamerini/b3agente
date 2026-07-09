# QA 28 — Causa-raiz encontrada: "LocalNotifications.then() is not implemented on ios"
*09/07/2026 · build alvo: F9-20260709-5*

## 1. Como chegamos até aqui

qa/27 descartou cache do Xcode/DerivedData como causa (o Alex rodou o reparo
profundo completo — Reset Package Caches, Resolve, Clean Build Folder, apagar
o app do iPhone, reinstalar — e o Diagnóstico continuou travando). Chunk
parity entre `dist/` e o bundle iOS foi reconferida byte a byte: idêntica.
Ou seja, tanto o binário nativo quanto o bundle JS estavam corretos — a causa
tinha que ser comportamento em RUNTIME, não arquivo faltando.

Com o Web Inspector do Safari conectado no aparelho físico, o console
mostrou o erro real:

```
Unhandled Promise Rejection: Error: "LocalNotifications.then()" is not
implemented on ios
```

## 2. Causa-raiz

Bug clássico e documentado da comunidade Capacitor: **o objeto do plugin
nativo é um proxy que responde a QUALQUER nome de propriedade/método**
(inclusive um hipotético `"then"`). O `web/src/notify.js` cacheava e
devolvia esse proxy DIRETO como valor de retorno de uma `async function`:

```js
// ANTES (bug)
async function plugin() {
  if (_plugin) return _plugin;      // <- proxy CRU sendo retornado
  ...
  return _plugin;
}
// call sites:
const p = await plugin();           // <- await aqui dispara o bug
```

Quando um valor "thenable" (que tem uma propriedade `.then` chamável) é o
resultado de um `return` dentro de uma `async function`, o motor JavaScript
**não devolve o valor direto** — ele assume que é uma Promise aninhada e
chama `.then(resolve, reject)` nele para "desembrulhar". Como o proxy do
Capacitor responde a QUALQUER acesso de propriedade (inclusive `.then`)
criando uma chamada de bridge nativa, isso vira uma chamada real para o
método **"then"** no plugin nativo — que não existe. Resultado: a Promise
nunca resolve nem rejeita de forma tratável em alguns call sites, e nos que
tinham `try/catch` ao redor, o erro aparecia sem contexto útil.

Isso explica TODOS os sintomas relatados com uma causa só:
- Diagnóstico "não fazia nada" (a chamada nativa por trás travava/rejeitava
  de forma não tratada).
- "Pedir permissão" não funcionava (mesmo caminho: `plugin()` → `then()`).
- "Ativar push" ficava preso desabilitado (depende de `perm === "granted"`,
  que nunca chegava lá porque `getPermission()` nunca completava direito).
- O app sumir de Ajustes → Notificações (o `requestPermissions()` nativo de
  verdade nunca era de fato invocado, porque a chamada morria antes).

**E por que nenhum guardião pegou isso antes:** todos os guardiões existentes
(`test_push_wiring.mjs`, `test_ios_assets.mjs`) conferem CONTEÚDO ESTÁTICO de
arquivo (o AppDelegate tem tal string, o config sincronizado tem tal opção).
Este bug é de SEMÂNTICA DE RUNTIME do JavaScript — invisível a esse tipo de
checagem. Só apareceu com o console real do aparelho.

## 3. Correção aplicada

`web/src/notify.js`:
- `plugin()` agora SEMPRE devolve um objeto comum "boxed": `{ p: ... }` —
  nunca o proxy solto. Um objeto literal `{ p: proxy }` não tem propriedade
  `.then`, então nunca é tratado como thenable.
- Todo call site (9 ocorrências: `diag`, `getPending`, `getPermission`,
  `requestPermission`, `setup`, `send`, `schedule`, `cancel`, `cancelAll`)
  passou a desestruturar: `const { p } = await plugin();` em vez de
  `const p = await plugin();`.
- Conferido: `registerPush` (push remoto, `@capacitor/push-notifications`)
  **não tinha esse padrão** — nunca retorna o proxy `P` de uma async
  function, só chama métodos nele. Não precisou de correção.

**Guardião novo:** `web/tests/test_notify_plugin_boxing.mjs` tranca por
regex que `plugin()` nunca faça `return _plugin;` cru e que nenhum call site
capture o retorno sem desestruturar `{ p }`. Isso pega qualquer reintrodução
futura do bug (ex.: alguém copiar o padrão antigo ao adicionar uma nova
chamada nativa).

Suítes completas depois do patch: **19/20 backend offline (1 pulada,
dependência ausente) + 23/23 web, 0 falhas** (as 2 anteriores de qa/27 mais
esta nova).

**Carimbo bumped:** `F9-20260709-4` → `F9-20260709-5` (mudança de
comportamento real, precisa reinstalar para valer).

## 4. Hard stop (o que o Alex precisa fazer)

Este é um fix de CÓDIGO — não precisa do reparo de cache do qa/27 de novo
(esse já foi feito e não era a causa). Basta a entrega normal:

```bash
cd ~/dev/bolsia/b3-agente
bash entregar.sh "qa/28: corrige thenable do plugin de notificações"
```

No Xcode: Product → Clean Build Folder (⇧⌘K) → Run no iPhone.

No aparelho:
1. Confirme o carimbo no rodapé do Perfil = `F9-20260709-5`.
2. Perfil → Notificações → **Diagnóstico** — deve responder na hora agora.
   Se ainda travar ou aparecer erro, cola o texto exato (agora sabemos ler o
   console — Web Inspector do Safari continua sendo a ferramenta certa se
   precisar).
3. Toque em **Pedir permissão** — deve aparecer o diálogo do iOS.
4. Depois de conceder: **Ativar push neste aparelho** deve deixar de estar
   desabilitado.
5. Retome a matriz A (A1–A6) e reporte só as FALHAS remanescentes.

## 5. Pendências

- Item B (Identidade/Modo Operador, B1–B7) segue sem detalhamento do Alex —
  aguardando quais itens falharam e o que a tela mostrou.
- Pytest completo (219 casos) segue não confirmável neste sandbox (sem
  acesso à rede para montar venv próprio); rodar `bash operar.sh testes` no
  Mac antes do próximo `entregar.sh` para ter a cobertura completa.
