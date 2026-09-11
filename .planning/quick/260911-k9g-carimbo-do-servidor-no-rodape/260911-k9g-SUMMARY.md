---
quick_id: 260911-k9g
status: done
commit: a003612
files_modified: [web/src/App.jsx, web/src/api.js, web/src/persistence.js, web/tests/test_carimbo_servidor_rodape.mjs]
---

# 260911-k9g — Rodapé do Perfil mostra o carimbo do app E do servidor

## O que mudou

O rodapé do Perfil (`PerfilHub`, `web/src/App.jsx`) mostrava só o `BUILD_ID`
do FRONT. Num deploy só-backend (aconteceu 5x em 10-11/09/26) o app parecia
desatualizado e não havia forma de ver, do aparelho, qual servidor estava
respondendo de fato — isso confundiu o Alex três vezes nesta mesma sessão. O
comentário do próprio código dizia "se não bater, aparelho com código
antigo", o que é falso especificamente nesse caso.

Decisão do Alex (do PLAN): mostrar OS DOIS carimbos, sempre.

## Forma final escolhida para a linha do rodapé

```
app F10-20260910-02 · servidor F10-20260911-02
```

Três estados, testados e provados abaixo:
- **Carregando** (`serverBuildId === undefined`): só `app {BUILD_ID}` — o
  segmento do servidor nem aparece, sem piscar travessão.
- **Sucesso** (`serverBuildId` é string): `app {BUILD_ID} · servidor {build}`.
- **Falha** (`serverBuildId === null`): `app {BUILD_ID} · servidor —` — NUNCA
  repete o build do front.

Optei por rótulos "app"/"servidor" (em vez de "front"/"back" ou variantes
mais técnicas) porque é a nomenclatura que o próprio comentário FASE 8B e o
Alex usaram ao descrever o problema — e cabe folgado nos 10px do rodapé.

## Arquivos e decisões

- **`web/src/api.js`**: `serverBuild()` virou propriedade do objeto `api`
  (não export standalone, ao contrário do rascunho inicial) — precisa ser
  chamável como `api.serverBuild()` a partir de `persistence.js`, no mesmo
  padrão de `mcpStatus`/`mcpLeitura`. Bate em `/api/health` do servidor JÁ
  CONFIGURADO (`runtimeBase`), timeout de 8s (não os 15s/90s padrão — um
  carimbo não justifica isso), e **nunca lança**: qualquer falha (rede,
  timeout, HTTP não-ok, corpo não-JSON, campo `build` ausente/não-string)
  vira `null`. Distinto de `testServer(url)`, que valida um ENDEREÇO
  digitado antes de aplicá-lo — este lê o servidor já em uso.
- **`web/src/persistence.js`**: método espelhado nos DOIS stores (paridade
  obrigatória do CLAUDE.md — confirmada pelo guardião genérico, ver abaixo).
  `serverStore` delega puro (`() => api.serverBuild()`); `deviceStore` chama
  `ensure()` antes (mesmo padrão de `mcpStatus`), porque é `ensure()` quem
  aplica `setApiBase(doc.config.serverUrl)` — sem isso o carimbo buscaria o
  endereço errado no modo nativo (iPhone com servidor customizado).
- **`web/src/App.jsx`**: `PerfilHub` ganhou `useState(undefined)` +
  `useEffect(() => { store.serverBuild().then(...) }, [])` — busca ao MONTAR
  a tela do Perfil (diagnóstico, não caminho crítico do boot), com guarda
  `ativo` contra setState após desmontagem. Semântica dos 3 estados
  deliberadamente espelha o padrão já existente do `QuotaSeg`
  (`undefined`/`null`/valor real). Comentário FASE 8B acima do rodapé foi
  reescrito: a versão antiga afirmava categoricamente que carimbo diferente
  = "aparelho com código antigo"; a nova explica que os dois carimbos
  **divergem por desenho** num deploy só-backend, e que só o carimbo do APP
  (comparado com a entrega) indica desatualização real.
- **`copy.js`**: NÃO tocado. Avaliei e decidi que os rótulos "app"/"servidor"
  são texto diagnóstico neutro (mesma classe do "build {BUILD_ID}" antigo,
  que já era hardcoded sem passar por `cp.*`), não vocabulário de voz por
  modo (Estudo/Operador) — não há tom de "professor" vs "mesa" a aplicar
  aqui. O plano dizia "se precisar" — julguei que não precisa.

## Guardião novo — prova da regressão perigosa

`web/tests/test_carimbo_servidor_rodape.mjs`, 19 asserções, padrão
readFileSync + regex com filtro de comentário (como os guardiões desta
sessão). A asserção central é a que a constraint pedia: **quando a consulta
ao servidor falhar, o rodapé NÃO pode cair no `BUILD_ID` do front**.

Provei empiricamente que o guardião pega essa regressão específica — apliquei
a mudança perigosa (`servidor {serverBuildId || "—"}` → `servidor
{serverBuildId || BUILD_ID}`) num arquivo temporário e rodei o teste antes de
reverter:

```
FALHOU estado de sucesso/falha mostra `servidor` com travessão como único fallback
FALHOU defeito NÃO existe: o segmento do servidor nunca cai em `serverBuildId || BUILD_ID`
FALHOU defeito NÃO existe: nenhuma variante do carimbo do servidor usa `BUILD_ID` como fallback de falha
3 FALHA(S)
```

Arquivo restaurado ao original logo em seguida (`git status` confirmou árvore
limpa antes do commit). Com o código real (sem a regressão), as 19 asserções
passam:

```
todos os testes passaram
```

O guardião também trava: `api.serverBuild` existe dentro do objeto `api`
(não standalone) com timeout de 8000ms e catch→null; paridade nos dois
stores (`serverStore`/`deviceStore`); `PerfilHub` nasce com `undefined` e
busca em `useEffect` ao montar; o comentário FASE 8B foi atualizado com a
frase "POR DESENHO" e não repete a afirmação antiga sem qualificação.

## Suíte e build

- `bash scripts/executar.sh --testes` (sandbox negou escrita de log em `/`
  na primeira tentativa — `Operation not permitted`; repetido com
  `dangerouslyDisableSandbox: true` por instrução do ambiente):
  - Backend (pytest): **2342 passed, 4 skipped**, 484 warnings (deprecations
    pré-existentes de `asyncio.get_event_loop_policy`, fora de escopo).
  - Web (`web/tests/*.mjs`): **127/127 OK**, incluindo o guardião novo e
    `test_fase3_paridade_stores_generica.mjs` (confirmou 71/71 métodos
    espelhados nos dois stores, sem assimetria nova).
- `cd web && npx vite build`: **build OK** (917ms, 94 módulos, PWA
  precache 23 entradas). Aviso pré-existente de chunk >500kB
  (`index-Dsaj0eU9.js`, 827kB) — não relacionado a esta mudança, fora de
  escopo.
- `web/node_modules` nasceu ausente no worktree (`npm ci`, 439 pacotes) —
  esperado, documentado no ambiente da tarefa.

## Deviations from Plan

Nenhuma. O único ajuste foi de implementação, não de escopo: o rascunho
inicial exportou `serverBuild()` como função standalone em `api.js` (espelhando
`testServer`), mas o plano exige que o método passe pelos DOIS stores via
`api.serverBuild()` — corrigido para propriedade do objeto `api`, mesmo
padrão de `mcpStatus`/`mcpLeitura`/`mcpSetupGrafico`. Descoberto e corrigido
antes do commit, sem impacto no resultado final.

## Limitações conhecidas / próximos passos obrigatórios

Esta é uma mudança de FRONT. **Não chega ao usuário** até:
1. `scripts/bump.sh` (bump do `BUILD_ID` de `web/src/version.js`);
2. `scripts/publicar-web.sh` (publica `web_dist` para o backend servir);
3. Deploy do Railway.

No iPhone, só chega com nova instalação (`npm run ios` + reinstalar) ou uma
nova build TestFlight — o bundle nativo carrega o JS embutido, sem
`server.url` (`web/capacitor.config.ts`).

Nenhum desses três passos foi executado nesta sessão, por instrução explícita
do ambiente da tarefa (NÃO deploy, NÃO bump.sh, NÃO publicar-web.sh, NÃO
railway).

## Como validar localmente

1. `cd web && npm run dev` (ou o proxy padrão do projeto).
2. Abrir o app, ir em Perfil.
3. Observar o rodapé: nasce só com `app F10-...`, e em ~1s (resposta do
   `/api/health` local) completa para `app F10-... · servidor F10-...`.
4. Para forçar o estado de falha: derrubar o backend local e reabrir a tela
   do Perfil — o rodapé deve mostrar `app F10-... · servidor —` (nunca
   repetir o build do front no lugar do servidor).

## Self-Check

- `web/src/App.jsx`: FOUND (modificado, diff conferido)
- `web/src/api.js`: FOUND (modificado, diff conferido)
- `web/src/persistence.js`: FOUND (modificado, diff conferido)
- `web/tests/test_carimbo_servidor_rodape.mjs`: FOUND (criado, 19/19 OK)
- Commit `a003612`: FOUND (`git log --oneline -3` confirma no topo do branch)

## Self-Check: PASSED
