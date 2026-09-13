---
phase: quick-260912-vle
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/MANUAL-BORIS-PLUS.md
  - .planning/STATE.md
autonomous: true
requirements: [QUICK-260912-VLE]
must_haves:
  truths:
    - "O manual de utilização do Boris+ existe no repositório, em docs/MANUAL-BORIS-PLUS.md"
    - "O conteúdo de docs/MANUAL-BORIS-PLUS.md é byte a byte igual ao do scratchpad (nenhuma palavra reescrita, resumida ou 'melhorada')"
    - "A suíte canônica continua verde (nada quebrou por engano)"
    - "A tabela Quick Tasks Completed do STATE.md registra esta task"
    - "Um commit atômico em PT-BR referencia 'manual de utilização' e 12/09/2026"
  artifacts:
    - path: "docs/MANUAL-BORIS-PLUS.md"
      provides: "Manual de utilização do Boris+ (análise de UX de 12/09/2026) versionado no repo"
      min_lines: 255
      contains: "# Manual de utilização — Boris+"
  key_links:
    - from: "/private/tmp/claude-501/-Users-acamerini-dev-borisv2/d3eda106-4c74-4678-91f7-d2ecb2bf5c10/scratchpad/MANUAL-BORIS-PLUS.md"
      to: "docs/MANUAL-BORIS-PLUS.md"
      via: "cópia verbatim verificada por diff"
      pattern: "diff -u .* docs/MANUAL-BORIS-PLUS.md"
---

<objective>
Trazer para o histórico do repositório o manual de utilização do Boris+ produzido
na análise de UX de 12/09/2026, hoje existente só como arquivo de scratchpad
(e como artefato HTML "Anatomia do Boris+", não versionado).

Purpose: documentação de produto já escrita e revisada — o conteúdo está aprovado;
o que falta é o canal correto de entrada no repo (arquivo em `docs/`, commit,
registro no STATE.md). Fora do scratchpad, esse texto se perde na próxima sessão.

Output: `docs/MANUAL-BORIS-PLUS.md` (arquivo novo, nada modificado no código),
linha nova na tabela Quick Tasks Completed do STATE.md, um commit atômico.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

Fonte (externa ao repo, não versionada):
`/private/tmp/claude-501/-Users-acamerini-dev-borisv2/d3eda106-4c74-4678-91f7-d2ecb2bf5c10/scratchpad/MANUAL-BORIS-PLUS.md`
— 261 linhas, começa em `# Manual de utilização — Boris+`, termina na nota de
rodapé sobre o artefato de análise de 12/09/2026.

<escopo_negativo>
Limites duros desta task. Violar qualquer um destes pontos é falha, não zelo:

- **NÃO reescrever, resumir, reformatar ou "melhorar" a prosa.** O conteúdo é
  documentação de produto já aprovada. A entrega é o texto VERBATIM.
- **NÃO reconferir cada `arquivo:linha`** citado no rodapé do documento: a
  própria nota de rodapé declara que as referências completas ficam no artefato
  de análise e no prompt de execução, que são externos ao repo.
- **NÃO corrigir o texto por conta própria** se alguma afirmação de comportamento
  contradisser o código atual — sinalizar no SUMMARY e parar aí (ver Task 2).
- **NÃO rodar `npx vite build`**: nenhum arquivo de `web/src/` é tocado; o CLAUDE.md
  exige build só quando o front é editado.
- **NÃO publicar, NÃO deployar, NÃO bumpar `SERVER_BUILD_ID`, NÃO rodar
  `bump.sh`/`publicar-web.sh`/`publicar-admin.sh`, NÃO tocar no Railway.** É
  documentação entrando no histórico do repo, nada mais.
- **NÃO empurrar para `origin`, NÃO abrir PR.** Commit local na branch
  `v2/interacao-estrutural`.
- **NÃO usar os mutadores de estado do `gsd-sdk`** (`state.advance-plan`,
  `state.record-session`, `state.record-metric`, `state.add-decision`) — eles
  corrompem o `.planning/STATE.md` deste repo (decisão registrada no CLAUDE.md).
  STATE.md é editado à mão, com Edit.
</escopo_negativo>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Copiar o manual verbatim para docs/MANUAL-BORIS-PLUS.md</name>
  <files>docs/MANUAL-BORIS-PLUS.md</files>
  <action>
Copiar o arquivo do scratchpad para `docs/MANUAL-BORIS-PLUS.md` com `cp` via Bash,
não com a ferramenta Write: o mandato é verbatim, e reescrever 261 linhas à mão
admite deriva silenciosa (uma travessão virando hífen, um acento perdido) que
nenhuma revisão por leitura pega com confiabilidade. `cp` é a única forma que
garante igualdade byte a byte.

Comando exato:
`cp "/private/tmp/claude-501/-Users-acamerini-dev-borisv2/d3eda106-4c74-4678-91f7-d2ecb2bf5c10/scratchpad/MANUAL-BORIS-PLUS.md" docs/MANUAL-BORIS-PLUS.md`

O arquivo de destino NÃO existe hoje — é criação, não sobrescrita. Confirmar isso
antes (`ls docs/MANUAL-BORIS-PLUS.md` deve falhar); se existir, parar e relatar
em vez de sobrescrever.

Não alterar nada depois da cópia: nem encoding, nem final de linha, nem a nota de
rodapé. O arquivo entra no repo exatamente como foi escrito e revisado.
  </action>
  <verify>
    <automated>diff -u "/private/tmp/claude-501/-Users-acamerini-dev-borisv2/d3eda106-4c74-4678-91f7-d2ecb2bf5c10/scratchpad/MANUAL-BORIS-PLUS.md" docs/MANUAL-BORIS-PLUS.md &amp;&amp; head -1 docs/MANUAL-BORIS-PLUS.md | grep -q "^# Manual de utilização — Boris+" &amp;&amp; test "$(wc -l &lt; docs/MANUAL-BORIS-PLUS.md)" -ge 255 &amp;&amp; echo OK</automated>
  </verify>
  <done>`docs/MANUAL-BORIS-PLUS.md` existe, `diff` contra a fonte sai vazio com exit 0, primeira linha é o título do manual, 261 linhas.</done>
</task>

<task type="auto">
  <name>Task 2: Checar contradição manifesta com o código e rodar a suíte canônica</name>
  <files>(nenhum — leitura e verificação)</files>
  <action>
Duas verificações independentes, nenhuma delas autorizada a editar o texto do manual.

**(a) Contradição manifesta de comportamento.** O manual faz algumas afirmações
com a forma "nesta versão" — são as únicas que podem ter envelhecido nesta branch.
Conferir SÓ essas, por grep, sem abrir uma auditoria de UX:

- linha 191, "Coruja … Não funciona na aba Opções nesta versão" → a lista de telas
  do assistente é `PET_TELAS` em `server/app/conceitos.py:555`. Confirmar se
  `opcoes` está ou não na tupla.
- linha 186, "Ler opções da B3 … Esta versão não executa ordem de opção por aqui"
  e linha 188, "Rever o tour … Não cobre Acompanhar nem Opções nesta versão" →
  conferir por grep direcionado se ainda se sustentam.

Se alguma contradisser o código atual: **não editar o manual.** Registrar no
SUMMARY, com arquivo:linha dos dois lados (a frase do manual e o código que a
contradiz), para o Alex decidir. Corrigir prosa aprovada por conta própria é
justamente o que o escopo proíbe.

Se todas se sustentarem, dizer isso no SUMMARY em uma linha — "nenhuma
contradição encontrada" é resultado, não silêncio.

**(b) Suíte canônica.** `bash scripts/executar.sh --testes` (as DUAS suítes —
pytest do backend + `web/tests/*.mjs`; `scripts/test.sh` sozinho é meia baseline
e não conta). Aqui ela é checagem de que nada quebrou por engano, não validação
de funcionalidade: o diff é um arquivo markdown novo em `docs/`, que nenhuma
suíte lê. O baseline a bater é o do 25-06: 2682 passed, 5 skipped, 3 xfailed +
134 `.mjs`. Qualquer divergência disso é achado e vai ao SUMMARY.

Se a suíte der falha de sandbox (o histórico deste repo registra 26 falhas falsas
em ambiente restrito), repetir fora do sandbox antes de declarar regressão.
  </action>
  <verify>
    <automated>grep -n "PET_TELAS" server/app/conceitos.py | grep -v "^.*#" | head -2; bash scripts/executar.sh --testes</automated>
  </verify>
  <done>Saída da suíte registrada e comparada ao baseline 2682/5/3xfail + 134 .mjs; as três afirmações "nesta versão" conferidas contra o código, com o veredito (sustenta-se / contradiz, com arquivo:linha) anotado para o SUMMARY. Nenhuma linha do manual editada.</done>
</task>

<task type="auto">
  <name>Task 3: Registrar no STATE.md e commitar</name>
  <files>.planning/STATE.md</files>
  <action>
**STATE.md à mão, com Edit** — nunca pelos mutadores do `gsd-sdk` (decisão do
Alex registrada no CLAUDE.md: eles sobrescrevem `stopped_at`/`status` com texto
de sessão antiga, erram o contador de planos e colam métrica fora da tabela).

Adicionar UMA linha ao fim da tabela `### Quick Tasks Completed` (linha ~755),
respeitando as colunas existentes: `# | Description | Date | Commit | Status |
Directory`. Conteúdo:

- `#`: `260912-vle`
- `Description`: que o manual de utilização do Boris+, produzido na análise de UX
  de 12/09/2026, entrou no repo como `docs/MANUAL-BORIS-PLUS.md`, cópia verbatim
  do artefato de scratchpad; documentação apenas, nenhum código tocado; e o
  veredito da checagem de contradição da Task 2 (se alguma afirmação "nesta
  versão" envelheceu, nomeá-la aqui).
- `Date`: `2026-09-12`
- `Commit`: o hash curto do commit desta task (preencher depois de commitar, ou
  commitar o STATE.md junto e usar `—` como as linhas `Documented` já fazem).
- `Status`: `Documented` (o precedente das linhas 260908-bzf e 260909-dao, que
  também são documentação sem código).
- `Directory`: `[260912-vle](./quick/260912-vle-salvar-manual-de-utiliza-o-do-boris-em-d/)`

NÃO mexer no frontmatter (`progress`, `stopped_at`, `last_activity`, `percent`):
quick task não é plano do ROADMAP e mexer ali faria o contador mentir — mesma
razão já escrita no próprio STATE.md sobre a fase 25.

Depois, commit atômico, por caminho explícito (`git add docs/MANUAL-BORIS-PLUS.md
.planning/STATE.md .planning/quick/260912-vle-*` — nunca `git add -A`: a árvore
tem untracked de outras sessões, as skills em `.claude/skills/`). Mensagem em
PT-BR referenciando "manual de utilização" e a data da análise, por exemplo:

`docs(quick-260912-vle): manual de utilização do Boris+ (análise de 12/09/2026)`

com corpo curto dizendo que é cópia verbatim do artefato da análise de UX,
documentação apenas, nada publicado.

Sem `git push`, sem PR.
  </action>
  <verify>
    <automated>grep -q "260912-vle" .planning/STATE.md &amp;&amp; git log -1 --pretty=%s | grep -qi "manual de utiliza" &amp;&amp; git log -1 --name-only --pretty=format: | grep -q "docs/MANUAL-BORIS-PLUS.md" &amp;&amp; git status --porcelain docs/ .planning/STATE.md | grep -q . &amp;&amp; echo "SUJO - revisar" || echo OK</automated>
  </verify>
  <done>Linha `260912-vle` presente na tabela Quick Tasks Completed; frontmatter do STATE.md inalterado (`git diff` do commit não mostra mudança em `progress`/`percent`/`stopped_at`); um commit local na branch `v2/interacao-estrutural` contendo `docs/MANUAL-BORIS-PLUS.md` + `.planning/`; nada empurrado a origin.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| scratchpad `/private/tmp` → repo `docs/` | Conteúdo externo ao repo entrando no histórico versionado |
| working tree → commit | Árvore com trabalho não rastreado de outras sessões (skills em `.claude/skills/`) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-vle-01 | Tampering | `docs/MANUAL-BORIS-PLUS.md` | mitigate | cópia por `cp` + `diff` contra a fonte no `<verify>` da Task 1; retipar o texto (Write) é proibido justamente porque admite deriva silenciosa |
| T-vle-02 | Information Disclosure | conteúdo do manual | accept | o texto é documentação de produto de uso final; não contém segredo, token nem chave — a nota de rodapé deixa as referências internas `arquivo:linha` FORA do documento, no artefato externo |
| T-vle-03 | Tampering | commit | mitigate | `git add` por caminho explícito, nunca `-A`; a árvore tem untracked de outras sessões (lição registrada em memória: `entregar.sh git add -A`) |
| T-vle-04 | Repudiation | `.planning/STATE.md` | mitigate | Edit à mão + `git diff .planning/STATE.md` antes do commit; mutadores do `gsd-sdk` proibidos por decisão registrada (corrompem `stopped_at`/`progress`) |
| T-vle-SC | Tampering | npm/pip/cargo installs | n/a | nenhuma dependência instalada nesta task — zero pacotes, zero `requirements.txt`/`package.json` tocados |
</threat_model>

<verification>
1. `diff` entre scratchpad e `docs/MANUAL-BORIS-PLUS.md` sai vazio (verbatim provado, não afirmado).
2. `bash scripts/executar.sh --testes` verde, no baseline do 25-06 (2682/5/3xfail + 134 `.mjs`).
3. `git diff HEAD~1 --stat` mostra SÓ `docs/MANUAL-BORIS-PLUS.md`, `.planning/STATE.md` e os artefatos de `.planning/quick/260912-vle-*` — nenhum arquivo de `web/`, `server/`, `web_dist/` ou `version.js`.
4. `web/src/version.js` e `SERVER_BUILD_ID` intocados (`git diff HEAD~1 -- web/src/version.js server/app/` vazio): nada foi publicado nem bumpado.
5. `git log origin/v2/interacao-estrutural..HEAD` mostra o commit local e NADA foi empurrado.
</verification>

<success_criteria>
- [ ] `docs/MANUAL-BORIS-PLUS.md` existe e é byte a byte igual à fonte do scratchpad
- [ ] Nenhuma palavra do manual reescrita, resumida ou reformatada
- [ ] As três afirmações "nesta versão" conferidas contra o código; contradição (se houver) SINALIZADA no SUMMARY, não corrigida no texto
- [ ] Suíte canônica (as duas) verde, no baseline
- [ ] Linha `260912-vle` na tabela Quick Tasks Completed, editada à mão, frontmatter intacto
- [ ] Commit atômico em PT-BR citando "manual de utilização" e 12/09/2026
- [ ] Nenhum deploy, bump, publicação, push ou PR
</success_criteria>

<output>
Create `.planning/quick/260912-vle-salvar-manual-de-utiliza-o-do-boris-em-d/260912-vle-SUMMARY.md` when done.

O SUMMARY deve conter, explicitamente:
- resultado do `diff` (verbatim provado);
- o veredito da checagem de contradição das três afirmações "nesta versão" —
  inclusive quando nada contradiz;
- números da suíte contra o baseline;
- a declaração de que nada foi publicado.
</output>
