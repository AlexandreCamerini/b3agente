# CHECKOUT — v2: opções como classe de primeira ordem no BolsIA

Documento de entrada para um **chat novo** (Claude Code, na raiz de `b3-agente`).
Objetivo desta rodada: **decidir a arquitetura de produto**, não escrever a
feature. Termina em decisões registradas + mocks aprovados, e o código começa
depois.

---

## 1. O que se quer resolver

O app cobre **ações** bem. Opções existem como um estudo isolado
(`OptionsScreen`, alcançável por um botão em Mercado) e não participam do
funil, da carteira, do Operador nem do Radar.

A tese do Alex — que esta rodada deve validar ou refutar com fundamento — é que
**ação e opção pedem linhas de análise diferentes o bastante para justificar
separação na navegação**, e que hoje o app trata as duas como se fossem a mesma
coisa em escala menor.

O resultado desejado: uma pessoa consegue acompanhar um ativo **e** as opções
dele, e operar os dois na carteira simulada, sem precisar entender a diferença
entre as duas análises antes de começar.

**O Alex não tem conhecimento de mercado suficiente para arbitrar sozinho as
escolhas de análise.** Ele decide produto e risco; a competência técnica sobre
opções vem da skill e dos especialistas convocados. Traga recomendação com o
porquê, não um menu de opções para ele escolher às cegas.

---

## 2. Fase 0 — fundação de dados (bloqueia todo o resto)

**Não projete em cima de dado que não existe.** Confirme o estado real antes de
qualquer decisão de arquitetura:

| Fato a confirmar | Onde |
|---|---|
| Provider de opções hoje é Yahoo não-oficial, degrada com frequência para B3 | `server/app/options_provider_yahoo.py` |
| Decisão de 2026-08-04: brapi entra como fonte de opções **marcada como terceiro** | memória `opcoes-b3-fonte-de-dados` |
| A implementação vive no **MyData**, não aqui | `~/dev/cvm-financas/docs/contrato-consumidor.md` |
| B3 proíbe redistribuição do COTAHIST | `qa/35-f10-polimento-eficiencia-fundamentos.md` |
| BolsIA consome o MyData por chave de API + REST; nada implementado dos dois lados | idem |

Se a cadeia de opções ainda não chega de forma confiável, **isso é o primeiro
achado do relatório**, e o desenho assume dado ausente como estado normal (o
app já tem essa postura: nunca inventa cadeia — `OPTIONS-GUARDRAILS.md`).

Regra de fundação (CLAUDE.md global): dado que o mercado publicou é do MyData.
Uma proposta que crie provider de opções próprio aqui precisa virar ADR no
MyData antes de virar código.

---

## 3. Decisões que só o Alex fecha

Levante via `AskUserQuestion`, em **uma rodada**, com recomendação em cada
opção. Não comece a Fase 1 sem elas:

1. **Separação na navegação** — abas irmãs (Ações | Opções) × opção como camada
   dentro do ativo × outra forma que os especialistas proponham.
2. **Escopo de "operar"** — só compra de call/put a seco (1 perna, risco =
   prêmio) × travas e estruturas (multi-perna) × acompanhar sem operar.
3. **Enquadramento regulatório** — opção aparece nos dois modos (Estudo e
   Operador) ou só em Estudo? Opção é instrumento alavancado; timing e
   vocabulário aqui pesam mais que em ação. Decisão de produto/jurídica.

Item 3 conversa com uma pendência que já estava aberta no checkout anterior
(seção 5, item 1) e nunca foi respondida.

---

## 4. Painel de especialistas — **no máximo 4 agentes, uma rodada**

Delegue com teto explícito. Cada um entrega ≤ 400 palavras com uma
recomendação e o principal trade-off. Rode em paralelo, uma vez só.

| Lente | Pergunta que ele responde |
|---|---|
| `anthropic-skills:analise-tecnica-b3` | O que a análise de opção precisa que a de ação não precisa (IV, gregas, prazo, liquidez, IV rank) e o que dela é ruído para quem está aprendendo |
| `engineering:system-design` | Modelo de dados: posição de opção na carteira simulada (prêmio, vencimento, exercício, expiração sem valor) e o que isso quebra em `store.py` / `agent.py` / `analysis_outcomes.py` |
| `design:user-research` + `design:design-critique` | Como a pessoa transita entre ativo e opção sem se perder; onde a separação ajuda e onde ela vira trabalho a mais |
| `engineering:architecture` | Se a separação de temas merece ADR e qual escolha aqui é irreversível |

Você sintetiza. Onde discordarem, decida e diga por quê — não devolva o
conflito para o Alex resolver.

---

## 5. O que já existe e não pode quebrar

- **`skill_ref.py` é a fonte canônica da metodologia.** Persona, princípios e
  vocabulário vivem lá; nada de reescrever metodologia em módulo novo.
- **`OPTIONS-GUARDRAILS.md`** vale integralmente — inclusive "não inventar
  cadeia quando o provedor não retorna" e "score educacional não é
  recomendação".
- **Vocabulário descritivo**, sem verbo de ordem de operação
  (`test_guardrail_imperativo`, `test_textos_do_agente_sem_verbo_de_ordem`).
- **467 testes verdes** e `scripts/masstest-agentes.py` com as 32 violações
  `fund_score_incoerente` pré-existentes como piso — 0 novas.
- **Carteira simulada só de ação hoje**: `positions` guarda `{t, qty, avg,
  stop, alvo, alvoExtensoes}`. Opção não cabe nesse formato — dizer como cabe é
  metade do trabalho desta rodada.
- **Custo é restrição transversal.** Toda proposta declara impacto de fetch,
  armazenamento e IA antes de ser adotada.
- Já feito e reusável: F1 timing intraday, F2 trailing dinâmico, F3 alvo
  dinâmico, F4 web em `acamerini.app`, F5 admin. Ver `RELEASES.md`.

---

## 6. Entrega desta rodada

Um documento (`docs/v2-opcoes-proposta.md`) + mocks navegáveis em
`qa/mocks/`, contendo:

1. **Veredito sobre a separação de temas** — com o argumento de mercado que o
   sustenta, não só preferência de UI.
2. **Modelo de dados da posição de opção** e o que muda em cada módulo tocado.
3. **Mocks** das telas propostas, no padrão dos que já existem em `qa/mocks/`.
4. **Estado da fonte de dados** e o que precisa acontecer no MyData primeiro.
5. **Custo estimado** por decisão.
6. **O que fica de fora da v2** — declarado, não omitido.

**Aceite:** cada decisão tem o porquê registrado; nenhuma proposta depende de
dado que não existe sem dizer isso; guardrails preservados; suíte e masstest
intocados (esta rodada não escreve código de produção).

---

## 7. Como trabalhar

- **Termine em aprovação, não em commit.** Use `ExitPlanMode` com a proposta;
  o código da v2 começa depois do "pode ir".
- Entregue no escopo pedido. Decida o rotineiro sozinho; se discordar de algo
  aqui, diga em uma frase e siga.
- Exercite o que afirmar: rode o endpoint de opções de verdade antes de
  descrever como ele se comporta.
- Mocks HTML estáticos bastam — nada de mexer no `App.jsx` nesta rodada.

## 8. Modelo e effort

- **Esta rodada (arquitetura, ADR, síntese de painel):** `claude-opus-5`,
  effort `xhigh` — decisões irreversíveis, multi-arquivo, alto custo de erro.
- **Implementação da v2, depois de aprovada:** `claude-sonnet-5`, effort
  `high`, varrendo para `medium` onde a qualidade se mantiver.
- Sem carga de Batches (trabalho interativo); streaming não é fator abaixo de
  ~16K `max_tokens`.

## 9. Primeiro comando no chat novo

> Leia `CHECKOUT-V2-Opcoes-otimizado.md`. Comece pela Fase 0: confirme no
> código e na memória o estado real da fonte de dados de opções antes de
> qualquer decisão de arquitetura. Depois levante as três decisões da seção 3
> numa rodada de `AskUserQuestion`, com sua recomendação em cada uma.
