---
phase: 25-planos-comerciais
plan: 02
subsystem: auth
tags: [rbac, owner, adr-013, permissoes, guardioes, fastapi, web-admin]

requires:
  - phase: 25-planos-comerciais
    provides: "25-01 (conserto do contador mensal) — nao ha acoplamento de codigo; este plano e a Fase 1 do mesmo 25-CONTEXT"
  - phase: adr-013
    provides: "RBAC por grupos de macro funcao, `permissoes_do_papel` derivando ROLE_ADMIN da uniao de GRUPOS, bootstrap aditivo e audit log"
provides:
  - "papel `owner`: permissoes pela uniao DINAMICA de GRUPOS, como ROLE_ADMIN — permissao futura entra sozinha"
  - "irrevogabilidade real em DUAS camadas (D1): `rbac.revoke_role` recusa com `PapelIrrevogavel`, e `ensure_bootstrap_role` reconcede"
  - "ancora por e-mail (`B3_OWNER_EMAIL`, default alexandre.camerini@gmail.com) SEM fallback de primeira conta — fecha parcialmente o A-12"
  - "`papeisIrrevogaveis` em GET /api/admin/users: o portal mostra o papel como ESTADO, sem oferecer acao impossivel"
  - "owner visivel para a varredura de destinatarios do push de kill-switch"
  - "server/tests/test_owner.py e web/tests/test_admin_owner_ui.mjs — os guardioes das duas camadas"
affects: [25-03-catalogo-de-planos, 25-04-gates-leem-o-plano, 25-05-modulo-no-portal]

tech-stack:
  added: []
  patterns:
    - "Papel TOTAL derivado da uniao dinamica de GRUPOS, nunca lista literal — `_PAPEIS_TOTAIS` e o unico ponto a tocar"
    - "Excecao de dominio propria (`PapelIrrevogavel(ValueError)`) para a rota distinguir 403 de 400 sem raspar string"
    - "Campo de backend que descreve o que a UI pode OFERECER (`papeisIrrevogaveis`), em vez de a UI deduzir por literal"

key-files:
  created:
    - server/tests/test_owner.py
    - web/tests/test_admin_owner_ui.mjs
  modified:
    - server/app/rbac.py
    - server/app/main.py
    - server/app/agent.py
    - web-admin/src/App.jsx

key-decisions:
  - "`B3_OWNER_EMAIL` definida VAZIA significa sem owner, e nao use o default — e como se desliga a ancora sem editar codigo"
  - "403 (nao 400) na recusa de revogacao: o pedido esta bem formado e o papel existe; o que falta e autorizacao para o efeito"
  - "`owner` fica FORA de `gruposDisponiveis` e entra em `papeisIrrevogaveis` — some-lo da tela faria o admin achar que a conta do dono nao tem o papel"
  - "Nenhum guardiao do ADR-013 foi tocado: o owner nao acrescenta permissao, deriva as mesmas 9"
  - "Guardiao estatico novo para o portal (deviation Rule 2) — o plano nao previa, mas a asercao de UI sem teste e promessa"

patterns-established:
  - "Defesa em profundidade com teste POR CAMADA: recusa (casos 3 e 4) e reconciliacao (caso 5) sao casos separados, porque cada um cobre o que o outro nao cobre"
  - "Teste de permissao futura por monkeypatch em GRUPOS: e o unico caso que reprova uma lista literal de permissoes"

requirements-completed: ["Fase 1 do 25-CONTEXT — papel owner (decisão D1)"]

duration: 35min
completed: 2026-09-12
---

# Phase 25 Plan 02: Papel `owner` — Summary

**O dono do produto deixou de depender de ordem de criação de conta e de
alguém lembrar de configurar uma lista de e-mails: `owner` tem toda permissão
que existe e toda que vier (união dinâmica de `GRUPOS`), não sai por rota
nenhuma, e volta sozinho se sumir por fora dela.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-12T18:11Z
- **Completed:** 2026-09-12T18:46Z
- **Tasks:** 3 de 3
- **Files modified:** 4 modificados + 2 criados

## Accomplishments

- **A irrevogabilidade virou regra declarada, não efeito colateral.** Até aqui
  `rbac.revoke_role` era um `DELETE` cru sem condição nenhuma, e o que salvava
  o `role_admin` de sumir era a reconcessão automática do bootstrap no request
  seguinte. Agora `PapelIrrevogavel` é a primeira regra do repositório que diz
  "este papel não sai", e ela mora na função de domínio — não só na rota, que é
  uma porta conhecida entre várias possíveis.
- **As permissões do owner são derivadas, não listadas.** Mesmo ramo de
  `ROLE_ADMIN` em `permissoes_do_papel`, via `_PAPEIS_TOTAIS`. O caso 2 do
  guardião injeta um grupo fictício em `GRUPOS` por monkeypatch e exige que a
  permissão nova apareça sozinha — é o único caso do arquivo que reprova uma
  lista literal, que envelheceria no primeiro grupo novo e faria
  "o dono nunca perde função" virar mentira silenciosa.
- **A âncora é e-mail explícito, sem fallback de primeira conta.** Fecha
  parcialmente o A-12: o papel máximo do produto não é mais eleito por
  `ORDER BY created_at ASC LIMIT 1`. `_is_admin_bootstrap` continua com o
  fallback para `role_admin` porque é contrato testado do ADR-013 (três testes
  dependem dele) — fechar o A-12 de vez segue sendo decisão separada.
- **O portal parou de ter as duas formas de mentir.** `owner` dentro de
  `gruposDisponiveis` viraria um botão de toggle que sempre toma 403; fora da
  tela inteira, o admin abriria a conta do dono e concluiria que ela não tem o
  papel. A saída é a terceira: papel permanente renderizado como estado
  (`owner · permanente`, `<span>` sem `onClick`), com a lista vindo do backend.

## Task Commits

1. **Task 1: o papel owner no rbac** — `6d7b31b` (feat)
2. **Task 2: a rota recusa, e o portal não oferece o botão** — `1d23dac` (feat)
3. **Task 3: guardiões do owner** — `dd6209d` (test)

## Files Created/Modified

- `server/app/rbac.py` — `OWNER`, `_PAPEIS_TOTAIS`, `OWNER_EMAIL_DEFAULT`,
  `PapelIrrevogavel`, `_is_owner`, e `ensure_bootstrap_role` reconciliando os
  dois papéis.
- `server/app/main.py` — ramo `revogar` capturando a recusa e respondendo 403;
  freio de concessão para `owner` ao lado do de `role_admin`;
  `papeisIrrevogaveis` em `GET /api/admin/users`.
- `server/app/agent.py` — `rbac.OWNER` na varredura de destinatários do push de
  kill-switch.
- `web-admin/src/App.jsx` — papel permanente como estado, antes dos toggles.
- `server/tests/test_owner.py` (novo) — 14 casos, os 8 pedidos pelo plano mais
  não-regressão, caixa/espaço no e-mail, push de kill-switch e sanidade.
- `web/tests/test_admin_owner_ui.mjs` (novo) — guardião estático do portal.

## RED medido antes de cada correção

**Backend (`test_owner.py`, contra o código anterior): `12 failed, 2 passed`.**

| Caso | RED | Vermelho por quê |
|------|-----|------------------|
| 1. owner tem todas as permissões | falhou | `AttributeError: module 'app.rbac' has no attribute 'OWNER'` |
| 2. permissão futura entra sozinha | falhou | `assert set() == {'futuro.mandar'}` — sem papel, nenhuma permissão cresce |
| 3. revogar pela rota → 403 | falhou | `AttributeError ... 'OWNER'` |
| 4. `revoke_role` direto levanta | falhou | `AttributeError ... 'PapelIrrevogavel'` |
| 5. reconciliação após `DELETE` no banco | falhou | `AttributeError ... 'OWNER'` |
| 6. idempotência do bootstrap | falhou | `AttributeError ... 'OWNER'` |
| 7. sem e-mail correspondente → nenhum owner | falhou | `AttributeError ... 'OWNER'` |
| 7b. primeira conta não vira owner (A-12) | falhou | `AttributeError ... 'OWNER'` |
| 7c. e-mail ignora caixa e espaço | falhou | `AttributeError ... 'OWNER'` |
| 8. não-owner não concede owner | falhou | `AttributeError ... 'OWNER'` |
| 8b. owner concede owner | falhou | `400 {"detail":"Papel desconhecido: 'owner'"}` |
| 9. owner recebe o push de kill-switch | falhou | `AttributeError ... 'OWNER'` |
| não-regressão: revogar outro papel pela rota | **passou** | passa nos DOIS estados, por desenho — é o que prova que a recusa é do `owner`, não da rota |
| sanidade: a união calculada não é vazia | **passou** | passa nos DOIS estados — existe para impedir que os casos 1, 2 e 8 aprovem por vacuidade |

**Ressalva honesta sobre os casos 7, 7b e 7c:** eles ficaram vermelhos por
`AttributeError` na constante, não por comportamento — antes do papel existir,
"nenhuma conta é owner" era verdadeiro por vacuidade. O valor deles é
prospectivo: travam a ausência do fallback de primeira conta para que o A-12
não se repita no papel novo.

**Depois da Task 1, só as 3 do escopo da Task 2 seguiam vermelhas:** a rota
respondendo 500 em vez de 403 na revogação, o freio de concessão inexistente
(`200` onde devia ser `403`) e o push do kill-switch (`assert 0 == 1`).

**Portal (`test_admin_owner_ui.mjs`, contra os fontes de `HEAD` em cópia
temporária): `7 falha(s)` de 19 asserções** — `papeisIrrevogaveis` ausente na
rota e no card, o trecho do papel permanente inexistente, e a checagem de
`<span>`/`permanente` sem nada para casar. As 12 que passaram são as de
não-regressão (toggle por `gruposDisponiveis`, `alternar()`, confirmação) e as
5 de sanidade.

**Achado no próprio RED, corrigido:** a asserção "o papel permanente NÃO tem
`onClick`" passava por VACUIDADE quando o recorte vinha vazio — checagem de
ausência sobre string vazia é sempre verdadeira. Passou a exigir o recorte
não-vazio (`permanente.length > 200 && !/onClick/`), e o RED subiu de 6 para 7
falhas. Foi o próprio ensaio do RED que expôs o furo.

## Verificação

- `bash scripts/executar.sh --testes` **fora do sandbox**:
  **`2590 passed, 5 skipped, 3 xfailed` + `132` arquivos `.mjs [OK]`, exit 0.**
  Baseline `2576/5/3xfail + 131` — os `+14` e o `+1` são exatamente os casos
  novos deste plano. Sem regressão.
- `cd web-admin && npx vite build` — verde (`55 modules transformed`,
  `built in 838ms`).
- `node web/tests/test_admin_plano_ui.mjs` (guardião do 24-17, o vizinho de
  card) — verde, rodado à parte antes do commit da Task 2.
- Índice conferido com `git diff --cached --stat` antes de cada um dos três
  commits; nenhum arquivo alheio entrou (os 4 diretórios não rastreados em
  `.claude/skills/` continuam intocados).

## Decisões Made

1. **`B3_OWNER_EMAIL` vazia = sem owner**, não "use o default". É como se
   desliga a âncora sem editar código; a env AUSENTE é que vale o default.
2. **403 e não 400 na recusa de revogação.** O pedido está bem formado e o
   papel existe — o que falta é autorização para o efeito. `PapelIrrevogavel`
   herda de `ValueError` para quem trata erro de domínio genericamente
   continuar funcionando, e a rota captura a classe específica para distinguir.
3. **`papeisIrrevogaveis` como campo separado**, em vez de marcar o item dentro
   de `gruposDisponiveis`. `gruposDisponiveis` significa "o que a UI renderiza
   como toggle"; misturar os dois obrigaria o portal a ramificar por conteúdo
   da lista.
4. **`_is_owner(conn, user)` recebe `conn` sem usar.** Simetria com
   `_is_admin_bootstrap` e antecipação do dia em que a âncora vier do kv.
   Documentado no docstring para não parecer descuido.
5. **Nenhum guardião do ADR-013 foi tocado.** As 9 permissões cravadas em
   `test_adr013_rbac.py:94-99` e `:119` continuam exatas, porque o `owner` não
   acrescenta permissão nenhuma — deriva as mesmas. O plano previa a
   possibilidade de mexer com nota datada; não foi preciso, e não se afrouxa
   guardião por precaução.

## Deviations from Plan

### Auto-fixed / acrescentado

**1. [Rule 2 — funcionalidade crítica ausente] Guardião estático do portal**

- **Found during:** Task 2 (a parte de `web-admin/src/App.jsx`)
- **Issue:** o plano lista `web-admin/src/App.jsx` em `files_modified` e cobra
  no critério de aceite que "o portal mostra que a conta é owner e NÃO oferece
  um botão que tente revogá-lo" — mas não previa teste para isso. `npx vite
  build` prova que compila, não que a tela diz a verdade. A asserção de UI sem
  guardião é promessa, e o repositório já tem o precedente exato
  (`web/tests/test_admin_plano_ui.mjs`, do card vizinho, criado no 24-17).
- **Fix:** `web/tests/test_admin_owner_ui.mjs`, 19 asserções, com RED provado
  contra os fontes de `HEAD` copiados para um diretório temporário (nenhum
  arquivo da árvore foi revertido, movido ou stashed para isso).
- **Files modified:** `web/tests/test_admin_owner_ui.mjs` (novo)
- **Verification:** verde na árvore atual, `7 falha(s)` contra os fontes de
  antes; entra na contagem canônica como o 132º `.mjs`.
- **Committed in:** `1d23dac` (junto da Task 2, que é o que ele guarda)

**2. [Rule 1 — bug] Asserção de ausência que passava por vacuidade**

- **Found during:** Task 2, no ensaio de RED do guardião acima
- **Issue:** `!/onClick/.test(permanente)` é sempre verdadeiro quando
  `permanente` é a string vazia — ou seja, a asserção aprovava justamente o
  fonte que não tem o trecho, que é o defeito que ela existe para pegar.
- **Fix:** passou a exigir `permanente.length > 200 &&`, com o motivo
  comentado no arquivo e apontando para a medição.
- **Files modified:** `web/tests/test_admin_owner_ui.mjs`
- **Verification:** RED de 6 → 7 falhas contra os fontes de antes.
- **Committed in:** `1d23dac`

**3. [Registro] `server/tests/test_adr013_rbac.py` NÃO foi modificado**

O plano o lista em `files_modified` prevendo que os números cravados
(9 permissões, lista de papéis) pudessem precisar mudar. Não precisaram: o
`owner` deriva as mesmas permissões e não entra em nenhuma das listas que
aqueles testes conferem. Fica registrado para ninguém procurar o diff que não
existe.

---

**Total deviations:** 2 auto-fixed (1× Rule 2, 1× Rule 1) + 1 registro.
**Impact on plan:** nenhum desvio de escopo — os dois acréscimos são teste do
que o próprio plano cobra no critério de aceite.

## Issues Encountered

Nenhum. O único susto foi o `500` da rota na primeira rodada pós-Task 1, que
era o esperado: a exceção nova subindo sem o `except` da Task 2.

## O que este plano deliberadamente NÃO fez

- **`owner` ainda não pula o cap comercial (D3).** Isso é a Fase 3 do
  `25-CONTEXT` (`_gate_analise`), e lá vale a metade que importa: pula o cap
  comercial, **nunca** o teto físico. Hoje `rbac.OWNER` só existe como papel de
  governança — nada em `plan.py` o consulta.
- **O A-12 não foi fechado de vez.** `_is_admin_bootstrap` e o fallback de
  primeira conta do `role_admin` seguem intactos, com os três testes que
  dependem deles verdes.
- **`opcoes.criar_setup` não migrou para o plano (D2).** É a Fase 3, e mexe em
  `ENTIDADES_POR_PERMISSAO` e em `test_opcoes_dsl.py`.

## Next Phase Readiness

Pronto para a Fase 2 (catálogo de planos, `plan.py`). O que a Fase 3 herda
daqui: `rbac.OWNER` para o D3, e o padrão de papel derivado — se algum dia
existir um segundo papel total, ele entra em `_PAPEIS_TOTAIS` e mais nada muda.

**Não está no ar, e são DUAS publicações em ordem** (mesma sequência do 24-17,
pelo mesmo motivo):

1. deploy do backend, com **bump manual de `SERVER_BUILD_ID`** — sem ele
   `papeisIrrevogaveis` não existe na resposta;
2. só depois `publicar-admin.sh` — o portal publicado antes do backend leria um
   campo inexistente e não mostraria o papel permanente (degrada para "não
   mostra", não quebra, porque o código usa `data.papeisIrrevogaveis || []`).

**Efeito no primeiro request depois do deploy:** a conta
`alexandre.camerini@gmail.com` recebe `owner` automaticamente (é o default da
âncora), e a partir daí não perde o papel por rota nenhuma. Se o e-mail da
conta do Alex em produção for outro, é só definir `B3_OWNER_EMAIL` no Railway —
sem isso, **não haverá owner nenhum**, por desenho.

Nada empurrado a `origin`, nenhum PR, nenhuma publicação.

## Self-Check: PASSED

- Arquivos declarados como criados/modificados: os 6 existem em disco
  (`server/app/rbac.py`, `main.py`, `agent.py`, `web-admin/src/App.jsx`,
  `server/tests/test_owner.py`, `web/tests/test_admin_owner_ui.mjs`).
- Commits declarados existem: `6d7b31b`, `1d23dac`, `dd6209d`.
- `git diff --diff-filter=D HEAD~3 HEAD` — **nenhuma** deleção de arquivo nos
  três commits.
- Frontmatter de `STATE.md` e deste SUMMARY validados por `yaml.safe_load`
  (o frontmatter do STATE já quebrou antes, commit `7227c67`).

---
*Phase: 25-planos-comerciais*
*Completed: 2026-09-12*
