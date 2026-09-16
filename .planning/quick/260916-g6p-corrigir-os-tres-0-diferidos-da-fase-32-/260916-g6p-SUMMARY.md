---
quick_id: 260916-g6p
slug: corrigir-os-tres-ou-zero-diferidos-da-fase-32
date: 2026-09-16
status: complete
tasks_completed: [1, 2, 3]
task_deferred: null
subsystem: web/opcoes
tags: [null-safety, guardiao, principio-4, opcoes]
dependency-graph:
  requires: [Fase 32 (32-02), deferred-items.md]
  provides: []
  affects: [web/src/opcoes/CuradoriaEstruturas.jsx, web/src/opcoes/CandidatoOpcao.jsx, web/src/opcoes/PropostaLastreada.jsx, web/tests/test_opcoes_analisar_ui.mjs]
key-files:
  created: []
  modified:
    - web/src/opcoes/CuradoriaEstruturas.jsx
    - web/src/opcoes/CandidatoOpcao.jsx
    - web/src/opcoes/PropostaLastreada.jsx
    - web/tests/test_opcoes_analisar_ui.mjs
    - .planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/deferred-items.md
decisions:
  - "Guard passou a ENVOLVER a operação (multiplicação/Math.abs) em vez de `|| 0` DENTRO dela — evita a armadilha `Math.abs(null) === 0`"
  - "`p.caixa &&` na frente do CTA de collar preservado — o ramo `ctaCollarDebito` é alcançado também quando `p.caixa` é falsy"
  - "Suíte canônica rodada fora do sandbox (dangerouslyDisableSandbox) por PermissionError de SSL conhecido como falso-positivo do ambiente sandboxed, não relacionado às mudanças"
metrics:
  duration_minutes: null
  completed: 2026-09-16
---

# Quick 260916-g6p: Corrigir os três `|| 0` diferidos da Fase 32 — Summary

Guard null-safe explícito nas três cópias do helper `porLote`/CTA de collar
em `web/src/opcoes/`, e remoção da exceção `ARQUIVOS_EXCECAO_OU_ZERO` do
guardião `OU_ZERO` — a regra volta a cobrir os três arquivos sem exceção
nenhuma, medida (não só descrita) como não-vácua.

## Escopo executado nesta sessão

**Task 1 e Task 2 completas e commitadas.** Task 3 (bump, `publicar-web.sh`,
push nas duas branches, confirmação HTTP em produção) foi **deliberadamente
NÃO executada** — publicação em produção exige confirmação explícita do
Alex, a ser pedida separadamente após este relato.

## O que mudou (Task 1)

Nos três arquivos que carregavam cópias do mesmo helper — armadilha medida
antes de planejar (ver `260916-g6p-PLAN.md`): `Math.abs(null) === 0`, então
o guard precisa ENVOLVER `Math.abs`, nunca ficar dentro dele:

- `CuradoriaEstruturas.jsx:99` (`item ? porLote : null`):
  `v * (item.qtyAcoes || 0)` → `typeof item.qtyAcoes === "number" ? v * item.qtyAcoes : null`
- `CandidatoOpcao.jsx:57` e `PropostaLastreada.jsx:200` (mesma forma, com `p`):
  `v * (p.qtyAcoes || 0)` → `typeof p.qtyAcoes === "number" ? v * p.qtyAcoes : null`
- Os quatro call sites do CTA de collar (`CandidatoOpcao.jsx:143-144`,
  `PropostaLastreada.jsx:268-269`):
  `price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0))` →
  `price(p.caixa && typeof p.caixa.custoLiquidoTotal === "number" ? Math.abs(p.caixa.custoLiquidoTotal) : null)`
  — o `p.caixa &&` na frente foi preservado de propósito (segunda armadilha
  medida: o ramo `ctaCollarDebito` é alcançado também quando `p.caixa` é
  falsy, porque a condição do ternário é `p.caixa && p.caixa.fluxo ===
  "credito"`; removê-lo trocaria "R$ 0,00" por `TypeError` em render).

Comentários históricos (`CuradoriaEstruturas.jsx:97-98`,
`CandidatoOpcao.jsx:54-56`, `PropostaLastreada.jsx:196-199`) foram
**emendados**, não apagados: mantiveram o texto original sobre `null * 100
=== 0` e ganharam uma nota datada (`ATUALIZADO 2026-09-16, quick
260916-g6p`) explicando a mudança de forma.

`npx vite build` (em `web/`) — verde:
```
✓ 105 modules transformed.
✓ built in 989ms
```

`grep -n "|| 0"` nos três arquivos — só linhas de comentário (histórico da
correção), nenhuma linha de código:
```
CuradoriaEstruturas.jsx:100:  // multiplicação (`typeof item.qtyAcoes === "number"`) em vez do `|| 0`
CandidatoOpcao.jsx:57:  // ATUALIZADO 2026-09-16 (quick 260916-g6p): o `|| 0` dentro da
PropostaLastreada.jsx:200:  // ATUALIZADO 2026-09-16 (quick 260916-g6p): o `|| 0` que ficava DENTRO da
```

`git diff --name-only` após o commit `c584c96` listou exatamente os três
`.jsx` — nada além.

## O que mudou (Task 2)

- `web/tests/test_opcoes_analisar_ui.mjs`: `PropostaLastreada.jsx` entrou
  na allowlist `ARQUIVOS` (linha 55); a exceção nomeada de dois arquivos que
  excluía `CuradoriaEstruturas.jsx`/`CandidatoOpcao.jsx` da seção 10 (`null`
  nunca vira 0) foi removida do código E do comentário (o identificador
  literal não aparece mais em lugar nenhum do arquivo — `grep -c` devolve
  `0`). Sanidade da regex mantida intacta.
- `deferred-items.md`: seção `## RESOLVIDO (2026-09-16, quick 260916-g6p)`
  anexada ao final, texto original do achado preservado sem edição.

### Prova negativa real (não descrita — executada)

Reintroduzido à mão `|| 0` em `PropostaLastreada.jsx` (`porLote`):
```js
// antes de reverter
const porLote = (v) => (typeof v === "number" ? v * (p.qtyAcoes || 0) : null);
```

Rodado `node web/tests/test_opcoes_analisar_ui.mjs` — saída real (trecho):
```
ok CandidatoOpcao.jsx sem `|| 0` (ausência não é zero)
FALHOU PropostaLastreada.jsx sem `|| 0` (ausência não é zero)
ok PropostaLastreada.jsx não divide para obter a razão (ela vem pronta do backend)
...
1 FALHA(S)
```
Exit code do processo: `1`.

Revertido com `git checkout -- web/src/opcoes/PropostaLastreada.jsx`.
Confirmação de reversão:
```
$ git diff --stat -- web/src/opcoes/PropostaLastreada.jsx
(sem saída — diff vazio)
$ node web/tests/test_opcoes_analisar_ui.mjs
...
todos os testes passaram
```
Exit code: `0`.

### Suíte canônica completa

`bash scripts/executar.sh --testes` — rodada **fora do sandbox**
(`dangerouslyDisableSandbox`). A primeira tentativa dentro do sandbox
mostrou 27 falhas de pytest, todas com `PermissionError: [Errno 1]
Operation not permitted` originando em `ssl.py` na criação de
`httpx.AsyncClient` (mesmo quando o fetch já estava com `monkeypatch` —
a própria construção do client tenta tocar certificados do sistema, que o
sandbox nega). Isso bate com o achado documentado na memória do projeto
("sandbox mente", ~26 falsas) e não tem relação nenhuma com os arquivos
tocados por esta quick (`test_benchmark_ibov.py`, `test_yahoo_*`,
`test_texto_vazio.py` etc. — nenhum deles em `web/src/opcoes/` ou no
guardião editado). Re-rodada fora do sandbox:

```
2923 passed, 5 skipped, 3 xfailed, 991 warnings in 261.84s (0:04:21)
```
e 152 arquivos `.mjs` com `[OK]`, zero `FALHOU`, exit 0.

**Comparação com a baseline da Fase 32** (2923 pytest + 152 `.mjs`):
idêntico, sem nenhuma queda. O delta de "+1 `.mjs`" citado no plano refere-se
à asserção nova DENTRO de `test_opcoes_analisar_ui.mjs` (seção 10 passa a
checar `PropostaLastreada.jsx` também) — não a um arquivo `.mjs` novo; a
contagem de arquivos por si permanece 152, como esperado (nenhum arquivo
novo foi criado nesta quick).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - correção de vazamento de detalhe interno] Comentário do
guardião citava o identificador `ARQUIVOS_EXCECAO_OU_ZERO` por nome, o que
fazia `grep -c ARQUIVOS_EXCECAO_OU_ZERO` devolver `1` em vez de `0` (critério
de aceite literal do Task 2). Reescrito para descrever a exceção sem repetir
o identificador removido. Sem impacto de comportamento — só texto de
comentário. Commit: `47b8907` (emendado antes do commit final, não gerou
commit extra).

Nenhum outro desvio.

## Auth gates

Nenhum.

## Known Stubs

Nenhum.

## Threat Flags

Nenhum — mudança é puramente de guard null-safe em componentes de exibição
já existentes; nenhuma superfície nova (rede, auth, schema).

## Task 3 — executada após confirmação explícita do Alex

Alex confirmou a publicação ("Pública") na mesma sessão, em turno separado.
Sequência executada pelo orquestrador (fora do sandbox, mesmo motivo de TLS
das Tasks 1-2):

1. `git fetch origin main` — `origin/main` confirmado ancestral do HEAD antes
   de tocar em qualquer coisa.
2. `bash scripts/bump.sh` — `F10-20260916-02` → `F10-20260916-03`.
3. `bash scripts/publicar-web.sh` (`npm ci` + `vite build`, publica em
   `server/web_dist`, sincroniza `SERVER_BUILD_ID`) — verde, `dist` com o
   carimbo `F10-20260916-03` confirmado por `grep`.
4. Comentário do `SERVER_BUILD_ID` em `server/app/main.py` reescrito à mão
   (script só sincroniza o valor, não o texto): nova entrada descrevendo esta
   quick, texto anterior (entrega `F10-20260916-02`, quick `260916-cod`)
   preservado como `HISTORICO`, no padrão do repositório.
5. Suíte canônica completa pós-bump, fora do sandbox: **2923 pytest + 152
   `.mjs`, exit 0** — idêntico à Task 2, sem queda.
6. Commit `bc2e03a` (`web/src/version.js`, `server/web_dist`,
   `server/app/main.py`). `git status --porcelain` limpo depois.
7. Push em `v2/interacao-estrutural` e `git push origin HEAD:main`
   (Railway só observa `main`) — ambos fast-forward, sem merge.
8. Confirmação HTTP: `curl https://boris.semente.dev/api/health` respondeu
   `{"ok":true,"build":"F10-20260916-02"}` por ~6 min (Railway ainda
   redesplegando) e então `{"ok":true,"build":"F10-20260916-03"}` — carimbo
   novo em produção, confirmado.

**Estado final:** `git rev-parse HEAD == origin/main == bc2e03a`, produção
respondendo `F10-20260916-03`. Nada pendente desta quick.

## Self-Check

Arquivos citados neste SUMMARY:
```
FOUND: web/src/opcoes/CuradoriaEstruturas.jsx
FOUND: web/src/opcoes/CandidatoOpcao.jsx
FOUND: web/src/opcoes/PropostaLastreada.jsx
FOUND: web/tests/test_opcoes_analisar_ui.mjs
FOUND: .planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/deferred-items.md
```

Commits citados:
```
FOUND commit: c584c96 (Task 1)
FOUND commit: 47b8907 (Task 2)
FOUND commit: bc2e03a (Task 3)
```

## Self-Check: PASSED
