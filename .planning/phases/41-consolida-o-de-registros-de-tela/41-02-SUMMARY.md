---
phase: 41-consolida-o-de-registros-de-tela
plan: 02
subsystem: front (registro de telas) + guardioes de teste
tags: [telas-01, registro, paridade, guardiao, refactor-puro, tdd]

requires:
  - phase: 41-01
    provides: "web/src/telas.js (registro), telas_baseline_41.json (fixture), test_telas_registro.mjs (PARTES A/B/C), server/tests/test_telas_paridade.py"
provides:
  - "web/src/App.jsx: BottomNav/petTela/tourPassos/ajudaSecoes religados a web/src/telas.js — nenhuma lista paralela de tela sobrou (SC#1)"
  - "test_telas_registro.mjs PARTES C (cont.)/D/E: equivalência tour/ajuda executando App.jsx, fiação (nenhuma lista antiga), switch de petSnapshot amarrado ao registro por sha256"
  - "6 guardiões antigos reconciliados com nota datada (5 previstos no plano + 1 achado durante a suíte canônica: test_fase22_componentes_compartilhados.mjs)"
  - "web/src/telas.js: cabeçalho 'Como adicionar uma tela' com o procedimento real pós-religação"
  - "SC#4 demonstrado por walkthrough: tela hipotética 'estudos', 16 asserções JS + 1 pytest reprovando nomeando a causa, revertido"
affects:
  - 41-03 (checkpoint humano + publicação)

tech-stack:
  added: []
  patterns:
    - "objeto local porTela indexado por id, iterado via telasDoTour()/telasDaAjuda() (D-02) — texto fica na função, estrutura vem do registro"
    - "sha256 de bloco de código como guardrail de 'switch intocado' (D-03), mesma técnica do gerador do fixture (41-01)"
    - "reconciliação de guardião fora da lista do plano segue a mesma regra (nota datada, cobertura mantida) — não é exceção"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/src/telas.js
    - web/tests/test_telas_registro.mjs
    - web/tests/test_pet_opcoes.mjs
    - web/tests/test_operador_ia_subtela.mjs
    - web/tests/test_copy_theme.mjs
    - web/tests/test_radar.mjs
    - web/tests/test_pet_ui.mjs
    - web/tests/test_tour_opcoes.mjs
    - web/tests/test_fase22_componentes_compartilhados.mjs

key-decisions:
  - "petSnapshot (switch) não foi editado — só ganhou um comentário ACIMA do useMemo (fora do bloco hasheado), preservando o sha256 do fixture (D-03)"
  - "porTela é objeto LOCAL dentro de cada função (tourPassos/ajudaSecoes), não módulo compartilhado — textos continuam vivendo exatamente onde D-02 mandou"
  - "guardião fora da lista do plano (test_fase22_componentes_compartilhados.mjs) reconciliado com a MESMA regra dos 6 previstos, não tratado como exceção"

requirements-completed: []

duration: "~35min"
completed: 2026-09-25
---

# Phase 41 Plan 02: Religação dos 4 consumidores ao registro único de telas Summary

BottomNav, petTela, tourPassos e ajudaSecoes do `App.jsx` passam a ler a
LISTA de telas de `web/src/telas.js` (41-01) — zero mudança visível provada
por equivalência byte a byte contra o fixture pré-refactor, 6 guardiões
reconciliados com nota datada, e o switch de `petSnapshot` amarrado ao
registro por sha256 em vez de inspeção manual.

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-25
- **Tasks:** 3 (Task 2 com ciclo TDD RED→GREEN)
- **Files modified:** 10

## Accomplishments

- `BottomNav.defs` → `defsDaBarra(cp)`; `petTela` → `telaDoAssistente(tab, carteiraView)` — zero lista literal restante (SC#1, PARTE D)
- `tourPassos`/`ajudaSecoes` iteram `telasDoTour()`/`telasDaAjuda()`; os textos continuam nas próprias funções via objeto local `porTela` (D-02) — equivalência byte a byte com o fixture pré-refactor confirmada nas 2 e 4 combinações de modo (PARTE C)
- `petSnapshot` (switch) intocado — case↔registro amarrado por teste (sha256 do bloco == fixture, PARTE E, D-03)
- 6 guardiões reconciliados (5 previstos + 1 achado ao vivo na suíte canônica), cada um com nota datada "REVERSÃO DELIBERADA (2026-09-25, Fase 41, TELAS-01)", nenhuma cobertura perdida
- Cabeçalho "Como adicionar uma tela" em `telas.js`, honesto sobre o que cada campo opcional exige e qual teste reprova sem ele
- SC#4 demonstrado por walkthrough real (tela hipotética `"estudos"`), não só descrito

## Task Commits

1. **Task 1: BottomNav e petTela religados + 5 guardiões reconciliados** — `73f50a2` (feat)
2. **Task 2 RED: PARTES C/D/E do guardião do registro** — `8495470` (test)
2. **Task 2 GREEN: tourPassos/ajudaSecoes iteram os ids do registro** — `3f5785c` (feat)
3. **Task 3: cabeçalho "Como adicionar uma tela"** — `3e9ea9f` (docs)
4. **Deviation: guardião da Fase 22 reconciliado** — `b633238` (fix)

_TDD: Task 2 seguiu RED (`8495470`, 2 falhas esperadas confirmadas) → GREEN (`3f5785c`, verde)._

## Files Created/Modified

- `web/src/App.jsx` — BottomNav/petTela/tourPassos/ajudaSecoes religados ao registro; comentário amarrando o switch de petSnapshot ao registro (sem editar o switch)
- `web/src/telas.js` — cabeçalho "Como adicionar uma tela" acrescentado (nenhuma função/dado mudou)
- `web/tests/test_telas_registro.mjs` — PARTES C (cont.)/D/E acrescentadas (equivalência tour/ajuda, fiação, switch↔registro)
- `web/tests/test_pet_opcoes.mjs`, `test_operador_ia_subtela.mjs`, `test_copy_theme.mjs`, `test_radar.mjs`, `test_pet_ui.mjs` — reconciliados: asserção textual (regex sobre `const defs = [[...]]`/ternária) trocada por asserção comportamental (chamando `defsDaBarra`/`telaDoAssistente`/`TELAS` do registro)
- `web/tests/test_tour_opcoes.mjs` — import de `telasDoTour`/`telasDaAjuda` para o `eval` resolver (nenhuma asserção mudou)
- `web/tests/test_fase22_componentes_compartilhados.mjs` — asserção de contagem de `radar:` restrita ao bloco isolado do NavIcon (achado fora da lista do plano, ver Deviations)

## Decisions Made

- `porTela` é um objeto **local** dentro de cada função consumidora (não um módulo novo) — os textos do tour/ajuda continuam exatamente onde D-02 mandou, só o LUGAR de cada par `[título, corpo]` mudou.
- O switch de `petSnapshot` não foi tocado; o comentário novo fica ACIMA do `useMemo(`, fora da janela `switch (petTela) { … }, [petTela, data, quotes, wlScan]);` que o sha256 mede — confirmado pela PARTE E permanecer verde com o mesmo hash do fixture.
- O guardião fora da lista do plano (`test_fase22_componentes_compartilhados.mjs`) foi reconciliado com a MESMA regra dos 6 previstos (nota datada, cobertura mantida) — não é tratado como "bug do plano", é o comportamento esperado do repo_guardrail ("qualquer outro guardião que ficar vermelho... entra no SUMMARY").

## SC#4 — Passo-a-passo real de adicionar uma tela nova (demonstrado, não só descrito)

**Cenário simulado (aplicado e revertido, não commitado):** uma tela hipotética
`"estudos"`, **na barra** (6º item), **sem tour**, **com ajuda**, **snapshot
`"switch"`**. Uma única entrada foi acrescentada a `TELAS` em `web/src/telas.js`:

```js
Object.freeze({
  id: "estudos", barra: 6, rotuloCp: null, rotuloPadrao: "Estudos",
  tour: null, ajuda: true, snapshot: "switch",
  subtelaDe: null, carteiraView: null,
}),
```

Rodando **só essa mudança** (nenhum outro arquivo tocado):

- `node tests/test_telas_registro.mjs` → **16 falhas**, cada uma nomeando a causa:
  - `o registro tem exatamente 8 ids` — achou 9
  - `o conjunto de ids do registro é IGUAL ao de conceitos.PET_TELAS` — "registro-só=estudos" (aponta direto para o espelho que falta no backend)
  - `as ordens de barra são contíguas 1..5` — achou `1,2,3,4,5,6` (aponta que a barra cresceu sem o NavIcon/rótulo terem sido pensados)
  - `defsDaBarra(estudo/operador/nulo/vazio) reproduz o baseline` — 4 falhas, cada uma mostrando o item extra `["estudos","Estudos"]` no array obtido (mudança visível não intencional)
  - `ajudaSecoes(estudo,false/estudo,true/operador,false/operador,true) extraída do App.jsx reproduz o baseline` — 4 falhas: `telasDaAjuda()` já inclui `"estudos"` (porque `ajuda: true`), mas não existe `porTela.estudos` em `ajudaSecoes` → a seção vira `null` no array em vez de um `[título, corpo]` — a PARTE C pega isso como divergência do fixture (e não como um crash, o que é pior sem o teste: o guia da Ajuda mostraria um buraco silencioso)
  - `o conjunto de case do switch é IGUAL a idsComSnapshotNoSwitch()` — "registro-só=estudos" (a PARTE E, D-03)
  - `a entrada "estudos" (snapshot:"switch") tem case no switch` — nomeia a consequência: "cai no default: return {} e o Boris fala sem dado (achado A1 da Fase 26)"
- `server/tests/test_telas_paridade.py -k telas_paridade` → **1 falha**: `esperado 8 ids no registro, achou 9: [..., 'estudos']` — o espelho Python reprova de forma independente (paridade em dois pontos testados, sem import cross-language).

Revertido com `cp` do backup e conferido `diff` idêntico ao original; `git status --porcelain` limpo.

**Contagem de arquivos tocados, antes × depois da 41-02:**

| | Antes (pré-41-01) | Depois (pós-41-02) |
|---|---|---|
| Ponto único da LISTA de telas (front) | não existia — 4 listas paralelas em `App.jsx` (`defs`, `tourPassos`, `ajudaSecoes`, `switch`) | 1: `web/src/telas.js` (`TELAS`) |
| Espelho backend | `conceitos.PET_TELAS` | `conceitos.PET_TELAS` (inalterado, D-01 sempre exigiu os dois) |
| Conteúdo condicional em `App.jsx` (dependendo dos campos da tela) | mesmo trabalho, mas SEM teste ligando um ponto ao outro — exatamente o defeito do achado A1 (tela na barra, ausente do switch/allowlist, ninguém percebia) | mesmo trabalho (`case` no switch, entrada em `porTela` do tour/da ajuda, path no `NavIcon`, chave em `copy.js`) — **agora cada um tem um teste que reprova sem ele** (exceto NavIcon, achado registrado abaixo) |
| Falha ao esquecer um passo | **silenciosa** (Boris muda de assunto ou some do menu sem erro) | ** 16 asserções JS + 1 Python** nomeando exatamente o arquivo/campo que falta |

**Leitura honesta:** o número de arquivos tocados para uma tela completa (com
snapshot, tour ou ajuda) não caiu para "1" — isso nunca foi realista, porque
D-03 mantém o snapshot em runtime (hooks) e D-02 mantém os textos fora do
registro. O que SC#4 realmente entrega é: (a) a LISTA de quais telas existem
e onde aparecem mora num ponto só, testado 8-com-8 contra o backend; (b) todo
conteúdo condicional que antes podia ser esquecido em silêncio agora reprova
em teste, nomeando a consequência para o usuário (não apenas "assertion
failed"). Essa é a leitura que o checkpoint da 41-03 vai pedir para o Alex
aprovar por nome.

## Achados registrados (D-04 — não corrigidos nesta fase)

1. **`ajudaSecoes` tem 11 seções, só 6 mapeiam 1:1 com uma tela.** As 5 seções
   institucionais ("O que é o Boris+", "Os dois modos", "Fundamento (A/B/C)",
   "Eficiência da IA", "Avisos importantes") não são tela nenhuma.
   `historico` e `perfil` não têm seção própria — quem usa essas duas telas
   não tem "Como funciona" dedicado na Ajuda. (`web/src/App.jsx`, função
   `ajudaSecoes`.)
2. **`tourPassos` cobre só 4 das 8 telas** (`radar`, `mercado`, `carteira`,
   `opcoes`) + 2 passos de introdução que não são tela. `evolucao` só aparece
   no passo-zero de boas-vindas (não tem passo de funil dedicado);
   `agente`/`historico`/`perfil` não têm passo nenhum.
3. **Rótulo da aba do Radar diverge entre barra e tour/ajuda.** Na barra,
   `cp.tabRadar` = `"Radar"` (Estudo) / `"Mesa"` (Operador) — curto, para
   caber no ícone. No tour e na Ajuda, `cp.tituloRadar` = `"Radar de
   mercado"` (Estudo) / `"Mesa de oportunidades"` (Operador) — mais longo.
   Consistente internamente (é o padrão de todas as 4 telas com título longo
   × rótulo curto), mas é uma tela com DOIS nomes diferentes dependendo de
   onde a pessoa olha. (`web/src/copy.js:82-84,962-964`.)
4. **"Operador IA" na Ajuda é texto literal; o `BackHeader` da tela usa
   `cp.tituloOperadorIA`.** Hoje os dois batem (`"Operador IA"` nos dois
   modos, `web/src/copy.js:101,978`) — mas se algum dia `tituloOperadorIA`
   divergir por modo, a Ajuda ficaria com o nome antigo, porque não lê do
   `cp`. Chave já existe e é idêntica nos dois modos hoje; não é um bug
   ativo, é um risco de deriva futura.
5. **"Acompanhar" é literal nos três lugares** (barra: `web/src/telas.js`
   `rotuloPadrao: "Acompanhar"`; tour: `"Bem-vindo · você está em
   Acompanhar"`; ajuda: `["Acompanhar (início)", ...]`) — sem chave de
   `copy.js`, ao contrário das outras 4 telas da barra. Não muda por modo
   hoje (rótulo idêntico Estudo/Operador desde sempre), então não é um bug
   visível — é uma inconsistência estrutural (a única tela da barra sem
   `rotuloCp`).
6. **`NavIcon.paths` (ícone da barra) não tem teste estrutural genérico.**
   Uma tela nova com `barra` não-nulo mas sem entrada em `NavIcon.paths`
   renderiza um `<svg>` vazio (nenhum crash, nenhum teste acusa) — ao
   contrário de `snapshot`/`tour`/`ajuda`, que agora reprovam em teste sem a
   entrada correspondente. Documentado no cabeçalho de `telas.js` como
   lacuna conhecida, não corrigido (fora do escopo desta fase — criar esse
   teste seria uma funcionalidade nova, não uma religação).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / guardião fora de escopo] `test_fase22_componentes_compartilhados.mjs` quebrou na suíte canônica**
- **Found during:** verificação final da Task 3 (`bash scripts/executar.sh --testes`, fora do sandbox)
- **Issue:** a asserção `(app.match(/^\s*radar:/gm) || []).length === 1` (Seção C5, Fase 22) contava ocorrências de `radar:` no `App.jsx` INTEIRO, assumindo que só `NavIcon.paths` usava essa chave. A Task 2 introduziu `porTela.radar` dentro de `tourPassos` e `ajudaSecoes` (D-02) — duas ocorrências novas e legítimas da mesma chave, em outro contexto.
- **Fix:** restringida a busca ao `navIconBloco` (já isolado por `isolarFuncao("NavIcon")` mais acima no próprio arquivo) — mesma cobertura (nenhuma entrada `radar:` duplicada DENTRO do mapa de ícones), nota datada "REVERSÃO DELIBERADA (2026-09-25, Fase 41, TELAS-01)" acrescentada.
- **Files modified:** `web/tests/test_fase22_componentes_compartilhados.mjs`
- **Verification:** `node tests/test_fase22_componentes_compartilhados.mjs` volta a passar (118 asserções, exit 0); suíte canônica completa reexecutada, exit 0.
- **Committed in:** `b633238`

---

**Total deviations:** 1 auto-fixed (guardião fora da lista do plano, mesma regra dos 6 previstos)
**Impact on plan:** Nenhum scope creep — reconciliação segue exatamente o `repo_guardrail` do plano ("qualquer outro guardião que ficar vermelho... entra no SUMMARY"). Nenhuma cobertura perdida.

## Issues Encountered

Nenhum bloqueio. A única surpresa foi o guardião da Fase 22 (documentado acima) — encontrado só na suíte canônica completa, porque nenhum dos 6 arquivos listados no plano o citava.

## Validação

- Task 1: 6 guardiões (`test_pet_opcoes`, `test_operador_ia_subtela`,
  `test_copy_theme`, `test_radar`, `test_pet_ui`, `test_telas_registro`)
  verdes + `npx vite build` ok + `git diff --quiet web/src/copy.js
  docs/AJUDA.md server/app/` vazio.
- Task 2: RED confirmado (2 falhas nomeadas, PARTE D) → GREEN (todas as
  PARTES A-E verdes, incluindo `test_tour_opcoes.mjs`/`test_ajuda_help.mjs`
  sem edição de asserção) + `npx vite build` ok.
- Prova negativa executada de verdade (não só descrita): (a)
  `case "fantasma": { return {}; }` acrescentado ao switch → PARTE E reprova
  3 asserções nomeando a causa (`switch-só=fantasma`, sha256 diverge);
  revertido, `diff` confirma arquivo idêntico ao original. (b) um caractere
  trocado no primeiro título do tour (`"Descubra"` → `"DescubraX"`) → PARTE C
  reprova nas 2 combinações de modo, mostrando o `esperado`/`obtido` lado a
  lado; revertido, `diff` idêntico.
- Task 3: cabeçalho `"Como adicionar uma tela"` (1 ocorrência); walkthrough
  da tela hipotética `"estudos"` executado e revertido (`git status
  --porcelain` limpo); `git diff 1d4f54a -- web/src/copy.js docs/AJUDA.md
  server/app/` — 0 linhas (zero mudança de produto/regra desde a captura de
  contexto da fase).
- Suíte canônica completa, fora do sandbox (`bash scripts/executar.sh
  --testes`): **3050 passed, 5 skipped, 3 xfailed, 0 failed** (backend,
  idêntico ao baseline do 41-01 — zero regressão) + **165 `.mjs` OK, 0
  falha** (igual ao baseline do 41-01, incluindo o guardião da Fase 22 já
  reconciliado). `npx vite build` limpo (mesmo aviso pré-existente de chunk
  >500kB, não introduzido por este plano).

## Known Stubs

Nenhum. Todos os consumidores religados renderizam dado real; nenhum campo
novo foi introduzido sem fonte.

## Threat Flags

Nenhum. As superfícies tocadas (religação de 4 consumidores já existentes a
um registro já testado na 41-01, mais reconciliação de guardiões) estão
inteiramente dentro do `threat_model` do plano — T-41-05/T-41-06 mitigados
pela equivalência PARTE C + tabela-verdade; T-41-07 mitigado pelas notas
datadas nos 6 guardiões (5 previstos + 1 achado); T-41-08 confirmado pelo
diff vazio de `copy.js`/`docs/AJUDA.md`/`server/app/` desde `1d4f54a`.

## Next Phase Readiness

SC#1-#4 demonstrados por teste e por walkthrough real. Falta apenas o
checkpoint humano da 41-03 (roteiro de verificação visual: navegar pelas 5
abas nos dois modos, rodar o tour inteiro, abrir a Ajuda, perguntar ao
assistente em 2-3 telas incluindo uma subtela) + publicação (bump +
`publicar-web.sh`) + fechamento de docs. Nenhum bloqueio técnico conhecido —
o app iOS com bundle antigo segue funcionando sem nenhuma mudança de
comportamento (D-04 confirmado); a religação só chega ao binário num build
novo de TestFlight, sem efeito para o usuário atual.

## Self-Check: PASSED

- `web/src/App.jsx` — FOUND
- `web/src/telas.js` — FOUND
- `web/tests/test_telas_registro.mjs` — FOUND
- `web/tests/test_pet_opcoes.mjs` — FOUND
- `web/tests/test_operador_ia_subtela.mjs` — FOUND
- `web/tests/test_copy_theme.mjs` — FOUND
- `web/tests/test_radar.mjs` — FOUND
- `web/tests/test_pet_ui.mjs` — FOUND
- `web/tests/test_tour_opcoes.mjs` — FOUND
- `web/tests/test_fase22_componentes_compartilhados.mjs` — FOUND
- commit `73f50a2` (Task 1) — FOUND em `git log --oneline`
- commit `8495470` (Task 2 RED) — FOUND
- commit `3f5785c` (Task 2 GREEN) — FOUND
- commit `3e9ea9f` (Task 3) — FOUND
- commit `b633238` (deviation) — FOUND

---
*Phase: 41-consolida-o-de-registros-de-tela*
*Completed: 2026-09-25*
