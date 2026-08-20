# Prompt 2 — Camada de evidência medida: do sinal opinativo ao histórico verificável

**Alvo:** Claude Code no repo `b3-agente` · **Modo:** Plan Mode primeiro
**Natureza:** desenho + implementação faseada. Planejar antes de escrever código.

---

<contexto_travado>
Leia antes de qualquer coisa, e não re-derive nada daqui:
`.planning/prompts/insumo-consolidado-qualidade-do-sinal.md`
(consolida ADR-015, ADR-016 e os dois adendos, com todos os números e as
hipóteses já eliminadas).

O essencial, para você não propor o que já caiu:

- O motor de setups tem expectância **−0,104R** (n=32.095, t=−19,7) e **perde
  para entrada em dia sorteado** por −0,088R (t=−12,4).
- A confluência não discrimina: 93,1% dos sinais valem 100%, porque em 2 dos 13
  setups esse é o único valor possível.
- Já eliminados por medição: horizonte maior, barra semanal, só comprado,
  filtro de média móvel, refazer só a confluência, regime como salvador.
- O lado comprado perde de **simplesmente segurar a ação** por 1,49 p.p. por
  operação (t=−32,6).
- A instrumentação forward (`analysis_outcomes`) está quebrada e otimista;
  a Phase 6 que a conserta está planejada e **não executada** em
  `.planning/phases/06-instrumentacao-assertividade-adr015/`.

O harness que produziu isso está em `scripts/backtest_*.py`, é determinístico,
não usa LLM e não consome orçamento de brapi.
</contexto_travado>

<decisao_de_produto_a_confrontar>
O ADR-016 recomendou parar de apresentar o sinal como operável (Alternativa A).
Este trabalho é a forma construtiva de fazer isso: em vez de simplesmente
remover a recomendação, **substituí-la por evidência medida**.

A tese: o Boris+ para de ser um provedor de sinal e passa a ser uma escola de
avaliação de sinal. O usuário não aprende "compre quando o 9.2 aparecer";
aprende "o 9.2 apareceu — e é assim que se descobre se ele vale alguma coisa".

Você precisa **confrontar essa tese explicitamente no plano**, não assumi-la.
Duas perguntas que o plano tem de responder antes de propor tela:

1. Um produto que mostra que seus próprios setups perdem dinheiro ainda tem
   proposta de valor? Se sim, qual exatamente, e o que no fluxo atual sustenta
   ou contradiz isso?
2. O que acontece com o Modo Operador (execução automática) se o sinal que ele
   executa é medido como negativo? Manter, restringir ou desligar é decisão de
   produto — apresente o trade-off, com recomendação, e marque como decisão do
   Alex.

Se você concluir que a tese não se sustenta, diga isso em uma frase e proponha
a alternativa que sustenta — não entregue tela bonita sobre premissa furada.
</decisao_de_produto_a_confrontar>

<objetivo>
Entregar, ponta a ponta:

1. **Medição retrospectiva** — o histórico medido de cada setup vira dado de
   produto: computado por regra determinística, versionado, servido pela API.
2. **Medição prospectiva** — a instrumentação forward consertada, para
   acompanhar se o que o produto mostra hoje continua valendo amanhã.
3. **Camada de entendimento** — a interface expõe a evidência com honestidade, e
   a IA explica o que ela significa, sem nunca produzi-la.
</objetivo>

<restricoes_invariantes>
Não re-litigar. Violação aqui invalida a entrega:

- **Princípio 5 / guardrail CVM.** Todo número de performance vem de código
  determinístico. A IA lê o número pronto e explica; nunca calcula, nunca estima,
  nunca arredonda "para ficar melhor". A manchete do card continua vindo do motor.
- **Nunca misturar metodologias no mesmo número.** Expectância retrospectiva
  (backtest) e prospectiva (`analysis_outcomes`) medem coisas diferentes e não se
  somam. Misturá-las é exatamente o erro que o ADR-015 documenta, um nível acima.
  Cada número exibido declara a origem e a janela.
- **Sem promessa.** Nada de "este setup tem 65% de chance". Amostra insuficiente
  se declara como insuficiente; a frase canônica do CLAUDE.md
  ("Não há dados suficientes para concluir") existe para isso.
- Paridade obrigatória: `server/app/defaults.py` ↔ `web/src/catalog.js` (byte a
  byte) e `deviceStore` ↔ `serverStore` em `web/src/persistence.js`.
- Fonte de dados: brapi master com orçamento, Yahoo backup (ADR-001, ADR-008).
  O backtest usa cache e **não** consome cota do app.
- Validação: `bash scripts/executar.sh --testes` (as DUAS suítes). Front editado
  → `npx vite build`.
- Guardião de teste não se apaga; reversão deliberada atualiza o guardião com nota.
</restricoes_invariantes>

<escopo>

## Bloco 1 — O backtest vira dado de produto

Hoje o harness é script de análise. Precisa virar artefato servível, sem virar
carga de runtime.

Decisões que o plano precisa tomar (com justificativa, não por default):
- **Onde o cálculo roda.** Rodar 32k sinais por request está fora de questão.
  Job periódico, artefato versionado em disco, ou tabela — escolha e explique.
  O padrão de cache diário do ADR-012 (`admin_cache`, hook no `scheduler_loop`)
  é precedente do repo e provavelmente o caminho certo.
- **Qual recorte é exibido.** Por setup, por setup × regime, por faixa de
  confluência — e o que fazer com célula abaixo do piso de amostra.
- **Como o dado envelhece.** O backtest tem data de corte; a UI precisa dizer
  qual é. Dado de 2023–2026 apresentado em 2027 sem carimbo é o mesmo pecado de
  proveniência que o ADR-011/FIX-C11 corrigiu.
- **Reprodutibilidade.** Quem lê o número no app tem de conseguir chegar nele —
  o comando que reproduz fica documentado.

Reuse o que existe: `scripts/backtest_sinal.py` já é determinístico e puro. Não
reescreva o motor de replay; extraia o que for compartilhado.

## Bloco 2 — Instrumentação prospectiva

A Phase 6 já está planejada, revisada por plan-checker (0 blockers) e não
executada. Decida no plano: executar como está, ajustar, ou sequenciar depois do
Bloco 1 — com o motivo. Ela conserta a âncora, a duplicação, os campos que
faltam (`entrada`, `confluencia`, `alvo2`, `rr2`) e o `motivo` em `store.sell()`.

Ponto de atenção: com o Bloco 1 entregue, o dado retrospectivo passa a existir e
o prospectivo continua raso por meses. A UI precisa conviver com isso sem
sugerir que são a mesma coisa.

## Bloco 3 — Interface

O que o usuário vê. Restrições de desenho:
- A evidência aparece **junto do setup**, no momento em que ele é apresentado —
  não escondida numa aba de estatísticas que ninguém abre.
- Resultado negativo se mostra com o mesmo destaque que positivo. O CLAUDE.md
  já proíbe manipulação visual de resultado; aqui isso é o ponto central.
- Vocabulário por modo: Estudo (professor) × Operador (mesa) vêm de
  `skill_ref.py` no backend e `copy.js` no front. O front não compõe vocabulário.
- Estados completos: sem amostra, amostra insuficiente, dado desatualizado.

Consulte a skill `didatica-boris` (`.claude/skills/didatica-boris/SKILL.md`)
antes de escrever qualquer texto didático — ela tem as regras de vocabulário,
os princípios de dado e o caminho de deploy dessa camada.

## Bloco 4 — Camada de IA

A IA explica a evidência. Regras:
- Recebe o número pronto no snapshot; nunca recalcula nem infere.
- Explica o conceito por trás (expectância × taxa de acerto, R múltiplo, tamanho
  de amostra, por que "perdeu de segurar a ação" importa) — a camada educacional
  do CLAUDE.md lista esses conceitos como obrigatórios.
- Quando a amostra não sustenta conclusão, diz isso, textualmente.
- Prompts editáveis pelo portal admin são espelhados byte a byte
  (`defaults.py` ↔ `catalog.js`) — qualquer texto novo entra nos dois.

</escopo>

<entregavel>
1. **Plano de fase GSD** em `.planning/phases/`, seguindo o padrão do repo
   (frontmatter, waves, `must_haves`, tasks com `read_first`/`action`/
   `acceptance_criteria` verificáveis). Rode o plan-checker antes de executar.
2. **ADR** para as decisões estruturais do Bloco 1 e para a decisão de produto
   sobre o Modo Operador — as duas são arquiteturais e precisam ficar
   registradas com trade-off.
3. **Implementação** dos blocos aprovados, com suíte canônica verde e
   `npx vite build` quando o front for tocado.
4. **Verificação ao vivo** do que a suíte não pega: o número que aparece na tela
   é o mesmo que o harness produz, e o carimbo de data está correto.
</entregavel>

<como_trabalhar>
- Plan Mode primeiro. Não escreva código de produção antes do plano aprovado.
- Faça o inventário do que já existe antes de propor peça nova — o repo tem
  precedente para quase tudo aqui (cache diário do ADR-012, snapshot técnico
  único, vocabulário por modo, editor de prompt byte-exato).
- Decida sozinho o rotineiro. Traga ao Alex só o que é decisão de produto:
  o destino do Modo Operador, e o quanto de resultado negativo o produto exibe.
- Se discordar da tese do documento, diga em uma frase e siga com a sua
  recomendação registrada — não pare para debater.
- Teto de 4 subagentes simultâneos.
</como_trabalhar>
