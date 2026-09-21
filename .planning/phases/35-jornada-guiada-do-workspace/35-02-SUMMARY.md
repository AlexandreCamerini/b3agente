---
phase: 35-jornada-guiada-do-workspace
plan: 02
subsystem: ui
tags: [react, design-tokens, wcag-contrast, opcoes, accessibility]

# Dependency graph
requires:
  - phase: 35-01-r-tulos-de-est-gio-e-corre-o-do-gate-por-pill
    provides: "Rótulos de estágio (Passo 1 de 2 / Passo 2 de 2), abaWorkspace/temLeitura já expostos, chaves opcoesEstruturaMontada/opcoesPossibilidadesVistas já em copy.js"
provides:
  - "BOTAO_PRIMARIO/CUSTO_NO_BOTAO_PRIMARIO/desabilitadoPrimario/MARCA_RESULTADO — espelhos locais em OpcoesScreen.jsx/SecaoAnalisar.jsx/SecaoComparar.jsx"
  - "3 CTAs da jornada (Ler no serviço de opções, Montar estrutura, Ver possibilidades) preenchidos com T.accent + texto T.onAccent"
  - "Marca neutra de resultado (✓ + T.textMuted) em Montar estrutura/Ver possibilidades, gateada por resultado com conteúdo"
  - "Fold-in: SecaoVigias.jsx ganha bgPanel no array TOKENS (undefined calado desde a Fase 33)"
  - "Guardião test_opcoes_jornada_ui.mjs estendido com 9 blocos novos (varredura de token por diretório, fronteira D-04, identidade de cópias, D-05/D-06/D-07, prova negativa JORN-03) + 4 provas negativas reais"
affects: [35-03-checkpoint-publicacao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BOTAO_PRIMARIO: mesma geometria do BOTAO neutro, só border/background/color mudam para o preenchimento sólido de accent — T.onAccent nunca #fff literal (D-03/D-07)"
    - "Varredura de tokens por diretório: T.<nome> referenciado fora do array TOKENS do próprio arquivo vira undefined calado — guardião trava a classe inteira do defeito, não só o achado pontual"
    - "Contagem de identificador exata (lookbehind/lookahead de fronteira \\w) em vez de grep/substring ingênuo, necessária porque CUSTO_NO_BOTAO_PRIMARIO contém a string BOTAO_PRIMARIO como substring"

key-files:
  created: []
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/SecaoAnalisar.jsx
    - web/src/opcoes/SecaoComparar.jsx
    - web/src/opcoes/SecaoVigias.jsx
    - web/tests/test_opcoes_jornada_ui.mjs

key-decisions:
  - "Comentários que citam nomes de token/constante entre aspas (ex.: \"onAccent\") foram reescritos SEM aspas para não inflar contagens de grep/regex que a própria verificação do plano usa — achado da execução, não do planejamento"
  - "Bloco 14 do guardião (cópia morta proibida) usa a fonte SEM COMENTÁRIO — um comentário explicando por que uma constante NÃO é declarada num arquivo (ex. 'NÃO declarar CUSTO_NO_BOTAO_PRIMARIO aqui') cita o nome literal sem ser declaração real; contá-lo junto do código faria a asserção reprovar por texto explicativo, não por cópia morta de verdade"

requirements-completed: [JORN-02, JORN-01]

# Metrics
duration: ~35min
completed: 2026-09-21
---

# Phase 35 Plan 02: Hierarquia visual do CTA + marca de resultado Summary

**Os 3 CTAs que movem a jornada (Ler no serviço de opções, Montar estrutura, Ver possibilidades) passam do estilo neutro genérico a um preenchimento sólido de `T.accent` com texto `T.onAccent` (nunca `#fff` literal — reprova AA em 2 das 4 combinações tema×modo), e os dois re-clicáveis ganham uma marca `✓` discreta quando produzem resultado.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-21
- **Tasks:** 3/3
- **Files modified:** 5 (`OpcoesScreen.jsx`, `SecaoAnalisar.jsx`, `SecaoComparar.jsx`, `SecaoVigias.jsx`, `test_opcoes_jornada_ui.mjs`)

## Accomplishments

- `BOTAO_PRIMARIO` (mesma geometria de `BOTAO`, `border: none` + `background: T.accent` + `color: T.onAccent`) aplicado a exatamente 3 botões do app — nenhum outro controle ganhou accent.
- `CUSTO_NO_BOTAO_PRIMARIO` (subtexto de custo dentro do botão preenchido) usa `T.onAccent` — a correção de contraste do UI-SPEC contra a proposta original de `color-mix(#fff 72%)`, que reprovava em TODOS os temas medidos (2,20:1–3,38:1).
- `desabilitadoPrimario` usa `opacity: 0.55` (não o `0.45` do neutro) — o botão nunca some, só `opacity`/`cursor` mudam.
- `MARCA_RESULTADO` (✓ + `T.textMuted`) aparece em "Montar estrutura"/"Ver possibilidades" só quando o resultado tem conteúdo (`.length` no gate, nunca `.carregando`/`.erro`) — os dois botões continuam re-clicáveis, nunca desabilitam nem somem depois do clique.
- Fold-in corrigido: `SecaoVigias.jsx` referenciava `T.bgPanel` fora do array `TOKENS` desde a Fase 33 (33-01) — o chip de vigia não selecionado renderizava sem fundo, em silêncio. Achado pela própria varredura de tokens desta fase, não por relato.
- Guardião `test_opcoes_jornada_ui.mjs` (35-01) estendido com 9 blocos novos (varredura de token por diretório, fronteira D-04 dos 3 CTAs, identidade byte a byte das cópias locais, cópia morta proibida, D-05/D-06/D-07, prova negativa estrutural de JORN-03) e 4 provas negativas reais, todas executadas e revertidas.

## Task Commits

1. **Task 1: BOTAO_PRIMARIO no CTA da leitura paga + fold-in SecaoVigias.jsx** - `b76f5d4` (feat)
2. **Task 2: os dois CTAs das seções + marca de resultado re-clicável** - `e3934fa` (feat)
3. **Task 3: guardião — varredura de tokens, fronteira, identidade, provas negativas** - `7825845` (test)

## Files Created/Modified

- `web/src/opcoes/OpcoesScreen.jsx` — `onAccent` no array `TOKENS`; `BOTAO_PRIMARIO`/`CUSTO_NO_BOTAO_PRIMARIO` declarados grudados nos neutros que espelham; botão "Ler no serviço de opções" restilizado
- `web/src/opcoes/SecaoAnalisar.jsx` — `onAccent` no `TOKENS`; `BOTAO_PRIMARIO`/`desabilitadoPrimario`/`CUSTO_NO_BOTAO_PRIMARIO`/`MARCA_RESULTADO` declarados; botão "Montar estrutura" restilizado + marca de resultado
- `web/src/opcoes/SecaoComparar.jsx` — `accent` E `onAccent` acrescentados ao `TOKENS` (arquivo não tinha nenhum dos dois); `BOTAO_PRIMARIO`/`desabilitadoPrimario`/`MARCA_RESULTADO` declarados (sem `CUSTO_NO_BOTAO_PRIMARIO` — custo é linha própria antes do botão, fora de escopo); botão "Ver possibilidades" restilizado + marca de resultado
- `web/src/opcoes/SecaoVigias.jsx` — `bgPanel` acrescentado ao `TOKENS` (fold-in do achado do planejamento)
- `web/tests/test_opcoes_jornada_ui.mjs` — 9 blocos novos (10-18) + 4 provas negativas documentadas

## Decisions Made

- Comentários explicativos que citavam nomes de token entre aspas (`"onAccent"`, `"bgPanel"`) foram reescritos sem aspas — as próprias acceptance criteria do plano usam `grep -c '"onAccent"'` para contar SÓ a entrada no array, e um comentário com aspas inflava essa contagem para 2. Achado durante a Task 1, corrigido antes de rodar a verificação.
- Bloco 14 do guardião (cópia morta proibida) usa a fonte sem comentário — um comentário explicando por que `CUSTO_NO_BOTAO_PRIMARIO` NÃO é declarada em `SecaoComparar.jsx` cita o nome literal da constante sem ser uma declaração real; contar isso junto do código fazia a asserção reprovar por texto explicativo. Corrigido usando `semComentario()` (mesmo padrão já estabelecido no arquivo desde o 35-01).
- Contagem de identificador por fronteira exata (`(?<![A-Za-z0-9_])NOME(?![A-Za-z0-9_])`) em vez de `grep -c`/substring ingênuo no guardião — necessário porque `CUSTO_NO_BOTAO_PRIMARIO` contém a string `BOTAO_PRIMARIO` como substring; um `grep -c "BOTAO_PRIMARIO"` contaria as duas constantes juntas. As acceptance criteria do plano (que usam `grep -c` puro) foram verificadas com essa ressalva documentada abaixo em "Issues Encountered", não seguidas literalmente onde colidiam com esse artefato.

## Deviations from Plan

### Achados de leitura (não são bugs, são discrepâncias entre a redação da acceptance_criteria e o comportamento real do grep)

**1. `grep -c "BOTAO_PRIMARIO"` não retorna 2 como a acceptance criteria da Task 1/2 sugere**
- **Encontrado durante:** Task 1, ao rodar a verificação literal do plano
- **Causa:** `CUSTO_NO_BOTAO_PRIMARIO` contém a substring `BOTAO_PRIMARIO`; um `grep -c` de substring conta as duas constantes juntas (declaração + uso de cada uma = 4, não 2)
- **Verificação real usada:** contagem de identificador exato via regex com fronteira de palavra (`(?<![A-Za-z0-9_])BOTAO_PRIMARIO(?![A-Za-z0-9_])`), que confirma exatamente 2 ocorrências (1 declaração + 1 uso) em cada um dos 3 arquivos — a intenção da acceptance criteria está satisfeita, só o comando literal sugerido no texto do plano não isola o identificador
- **Nenhum código mudado por causa disso** — é puramente uma nota de verificação, refletida no guardião novo (bloco 11) que já usa a contagem exata

**2. O helper neutro `desabilitado` (0,45) ficou sem nenhum consumidor em `SecaoAnalisar.jsx`/`SecaoComparar.jsx`**
- **Encontrado durante:** Task 2, ao verificar a proibição "não renomear/reescrever `desabilitado`, ele continua servindo os botões neutros dos mesmos arquivos"
- **Achado:** em ambos os arquivos, o ÚNICO botão que usava `desabilitado(...)` era exatamente o botão que esta fase promoveu a `BOTAO_PRIMARIO`/`desabilitadoPrimario` (D-04). Os outros botões dos mesmos arquivos ("Ver a cadeia"/"Ver as operáveis") nunca tiveram estado desabilitado.
- **Ação:** `desabilitado` permanece declarado, intocado, conforme a proibição explícita do plano — agora é código morto (declarado, sem chamada) em ambos os arquivos. Não removido: a proibição do plano é literal ("não renomear nem reescrever") e remover a declaração seria além do escopo desta fase sem decisão explícita.
- **Impacto:** nenhum — `desabilitado` continua correto e disponível para o próximo botão do arquivo que precisar de estado desabilitado neutro; não é um defeito funcional, é uma nota para quem eventualmente notar o aviso de variável não usada (o projeto não roda ESLint em `web/`, então isso não bloqueia nada hoje).

---

**Total de achados:** 2 notas de verificação/leitura, nenhuma exigiu Rule 1-4 (nenhum bug, nenhuma funcionalidade crítica faltando, nenhuma mudança arquitetural). Nenhum código de produto precisou de correção além do que o plano já pedia.

## Issues Encountered

- Sandbox padrão relata falsos positivos em `pytest` (achado já documentado na memória do projeto — "sandbox mente"); a suíte canônica foi rodada com `dangerouslyDisableSandbox: true` para bater contra a baseline real.

## User Setup Required

None - no external service configuration required.

## Prova Negativa Real (Task 3, executada e revertida)

Todas as 4 injeções foram feitas em arquivo real, testadas com `node web/tests/test_opcoes_jornada_ui.mjs`, e revertidas com `git checkout -- <arquivo>` (confirmado `git diff --stat` vazio após cada uma).

**(a)** `color: T.onAccent` → `color: "#fff"` em `SecaoAnalisar.jsx`:
```
exit=1
FALHOU BOTAO_PRIMARIO: as 3 cópias locais são byte a byte idênticas (normalizado por espaço) — DIVERGEM em: OpcoesScreen.jsx, SecaoAnalisar.jsx, SecaoComparar.jsx
FALHOU SecaoAnalisar.jsx: nenhum #fff/#ffffff/"white"/color-mix( no CÓDIGO (D-07 ...)
```

**(b)** remover `"onAccent"` do `TOKENS` de `SecaoComparar.jsx`:
```
exit=1
FALHOU nenhum arquivo de web/src/opcoes/ referencia T.<token> fora do próprio array TOKENS (...) — violações: SecaoComparar.jsx: onAccent
```

**(c)** aplicar `BOTAO_PRIMARIO` a um botão de `SecaoSetups.jsx`:
```
exit=1
FALHOU BOTAO_PRIMARIO existe SOMENTE nos 3 arquivos da allowlist (D-04) — achados: ["OpcoesScreen.jsx","SecaoAnalisar.jsx","SecaoComparar.jsx","SecaoSetups.jsx"]
FALHOU SecaoSetups.jsx: BOTAO_PRIMARIO declarada e USADA (≥ 2 ocorrências, nunca cópia morta)
FALHOU SecaoSetups.jsx continua sem BOTAO_PRIMARIO/T.accent/T.onAccent (...)
```

**(d)** trocar `desabilitadoPrimario(` por `desabilitado(` no botão de `SecaoAnalisar.jsx`:
```
exit=1
FALHOU SecaoAnalisar.jsx: desabilitadoPrimario declarada e USADA (≥ 2 ocorrências, nunca cópia morta)
FALHOU SecaoAnalisar.jsx: o botão de Montar estrutura usa desabilitadoPrimario(, nunca desabilitado(
```

Todas as 4 reverteram limpo (`git diff --stat` vazio confirmado após cada uma).

## Verificação Final

- `node web/tests/test_opcoes_jornada_ui.mjs` — verde, 70 asserções (24 do 35-01 + 46 novas)
- `node web/tests/test_brand_book_v2_tokens.mjs` — verde (contraste `onAccent`×`accent` ≥ 4,5:1 nas 4 combinações tema×modo, já travado desde antes desta fase)
- `bash scripts/executar.sh --testes` — suíte canônica completa: **2923 passed, 5 skipped, 3 xfailed, 0 failed** (pytest) + **153/154 `.mjs`** (só a falha ambiental pré-existente `test_ios_assets.mjs`, `web/ios/` gitignored) — idêntica à baseline
- `cd web && npx vite build` — verde, 3 rodadas (Task 1, Task 2, verificação final)
- `git diff web/src/App.jsx` — vazio (App.jsx nunca tocado)

## Next Phase Readiness

- Os 3 CTAs da jornada estão visualmente proeminentes e a marca de resultado fecha o laço de progresso — pronto para o checkpoint humano ao vivo do plano 35-03.
- Nenhum blocker conhecido para o plano 35-03.
- O achado documentado sobre `desabilitado` (código morto em 2 arquivos) não bloqueia nada — é só uma nota para uma limpeza futura, se o Alex/equipe decidir.

---
*Phase: 35-jornada-guiada-do-workspace*
*Completed: 2026-09-21*

## Self-Check: PASSED

- FOUND: web/src/opcoes/OpcoesScreen.jsx (modificado, BOTAO_PRIMARIO/CUSTO_NO_BOTAO_PRIMARIO confirmados)
- FOUND: web/src/opcoes/SecaoAnalisar.jsx (modificado, BOTAO_PRIMARIO/desabilitadoPrimario/MARCA_RESULTADO confirmados)
- FOUND: web/src/opcoes/SecaoComparar.jsx (modificado, BOTAO_PRIMARIO/desabilitadoPrimario/MARCA_RESULTADO confirmados)
- FOUND: web/src/opcoes/SecaoVigias.jsx (modificado, bgPanel no TOKENS confirmado)
- FOUND: web/tests/test_opcoes_jornada_ui.mjs (estendido, blocos 10-18 + 4 provas negativas, 70 asserções passando)
- FOUND commit b76f5d4 (git log --oneline --all)
- FOUND commit e3934fa (git log --oneline --all)
- FOUND commit 7825845 (git log --oneline --all)
