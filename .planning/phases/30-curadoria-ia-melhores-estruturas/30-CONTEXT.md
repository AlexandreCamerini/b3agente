# Fase 30 — Curadoria de IA das 4 melhores estruturas · CONTEXT

> Consolidado por Claude, sem `/gsd-discuss-phase` assistido por subagente.
> D1 (universo) e D2 (fórmula de ranking) foram decididos pelo Alex via
> `AskUserQuestion` em 2026-09-13, entre alternativas concretas ancoradas
> no que o motor já calcula — não presumidos. D3-D6 (detalhe de execução)
> foram delegados pelo Alex ("pode decidir") e fechados com a mesma
> disciplina de citar código real antes de decidir — D3 corrigiu a própria
> moldura da fase ao descobrir que a cadeia hoje só traz um vencimento.

## Guardrail não-negociável (repetido de propósito — é o motivo da fase)

O pedido original: "análise de IA cobrindo todas as possibilidades,
mostrando as 4 melhores para gerar receita com risco mínimo". A leitura
ingênua — um LLM pontuando estruturas por retorno ajustado a risco — é
**exatamente** o que o princípio 5 do CLAUDE.md proíbe (cálculo financeiro
é sempre determinístico, nunca da IA). A escolha de QUAIS 4 aparecem vem de
matemática já existente no motor; a IA **narra** as 4 já escolhidas pelo
número, nunca decide quais são as 4. Qualquer plano desta fase que não
deixar isso explícito no código (não só na intenção) está errado.

## Decisões (fechadas em 2026-09-13, via AskUserQuestion)

### D1 — Universo: só venda coberta, várias janelas, toda a carteira elegível

Entre três opções apresentadas (só venda coberta; as 3 lastreadas
misturadas; as 3 + estruturas via MCP), o Alex escolheu a mais estreita:
**apenas venda coberta**, testando várias combinações de strike/vencimento,
em todas as posições da carteira elegíveis (comprado, com lote ≥ 100
ações livres). Put de proteção e collar ficam fora desta fase — misturar
"proteção" com "gerar receita" no mesmo ranking de risco mínimo não fazia
sentido matemático (put por definição não gera receita), e o Alex
concordou com a leitura estreita.

### D2 — Fórmula: prêmio ÷ perda máxima, com piso de liquidez

Ranking por **razão prêmio recebido / perda máxima**, maior primeiro,
com um piso de liquidez como filtro de entrada (contrato ilíquido não
entra no ranking, não importa a razão). Verificado por leitura do motor
(`opcoes_payoff.perfil_da_estrutura`, 2026-09-13): para venda coberta
(ACAO +1, CALL vendida -1 → inclinação direita **zero**), `ganho_maximo` E
`perda_maxima` são **sempre números finitos** — nunca `None`/ilimitado,
diferente de put ou naked. `perda_maxima` de uma venda coberta é o valor
da ação a caminho de zero, líquido do prêmio — então a razão
`prêmio / perda_maxima` converge para algo muito próximo do "yield do
prêmio sobre o valor da ação", uma métrica padrão do mercado real de
covered call. A escolha de D1 (só venda coberta) é o que torna esta
fórmula limpa; ela não funcionaria tão bem misturada com put/naked (onde
perda_maxima ora é o prêmio inteiro, ora é ilimitada).

## O que já existe hoje (verificado por leitura direta, 2026-09-13)

1. **A enumeração de múltiplos candidatos já é suportada, só não usada.**
   `rastrear(cadeia, filtros)` (`server/app/opcoes_motor.py:42`) aceita
   `filtros["n"]` (default 1) — pedir mais de um contrato já é um parâmetro
   existente, não uma função nova. `opcoes_lastreadas.propor()`
   (`opcoes_lastreadas.py:185`) hoje chama a régua de liquidez+strike
   extremo para escolher UM contrato por estrutura; não usa `n > 1` em
   lugar nenhum.
2. **O payoff de cada candidato já é uma chamada, não um cálculo novo.**
   `avaliar(pernas)` (`opcoes_motor.py:193`) delega direto a
   `perfil_da_estrutura` (`opcoes_payoff.py:161`) — mesma função que já
   serve a proposta única de hoje. Nenhuma aritmética nova acontece nesta
   fase; o que muda é RODAR essa função várias vezes (uma por candidato) e
   ORDENAR o resultado, nunca reescrevê-la.
3. **Custo ZERO do serviço MCP externo, por arquitetura, não por
   promessa.** A cadeia de opções que alimenta `propor()` vem de
   `options_provider.get_options(...)` (`main.py:3037` e outros 5 call
   sites) — o provider mydata/Yahoo (ADR-004/008/009), **nunca**
   `mcp_client`/`mcp.semente.dev`. Enumerar N candidatos a partir da MESMA
   cadeia já buscada (uma vez por posição) não gera nenhuma chamada de
   rede adicional — `rastrear()`/`avaliar()` são funções puras sobre dado
   em memória. Esta fase não cruza a fronteira do ADR-027 (isso já foi
   feito nas Emendas 1/2/3, por outras fases); aqui nem precisa.
4. **O motor multi-candidato da Fase 19 já devolve lista, mas com teto de
   2.** `propor()` retorna `candidatos` com 1 ou 2 entradas (venda coberta
   OU put, mais collar se coexistir) — é a lista que a sub-aba "Operar"
   (Fase 28) consome hoje. Esta fase NÃO estende essa lista para a UI de
   "Operar" — é uma tela/bloco NOVO e separado (ver "Em aberto" abaixo),
   porque o que ele mostra é fundamentalmente diferente: não "a proposta
   desta posição", mas "as 4 melhores entre várias janelas, cruzando
   posições".

## Decisões de detalhe (fechadas em 2026-09-13, delegadas pelo Alex — "pode decidir")

### D3 — Janelas: só STRIKE, dentro do vencimento único que a cadeia já traz

**Achado que corrigiu a própria moldura desta fase, antes de fechar a
decisão**: `chain.get("expiration")` (`opcoes_lastreadas.py:16`, comentário
do próprio código: "cadeia carregada traz um vencimento só") — a cadeia
que `options_provider.get_options(underlying)` devolve hoje já vem presa a
UM vencimento. Testar "várias janelas de VENCIMENTO" exigiria chamar
`get_options(underlying, expiration=X)` uma vez por vencimento testado,
por posição — isso multiplica chamadas ao provider (mydata/Yahoo) e
**deixaria de ser verdade** a propriedade de custo zero/sem chamada extra
que este CONTEXT declarou no achado 3 acima.

**Decisão: "várias janelas" nesta fase significa vários STRIKES dentro do
MESMO vencimento único já buscado — nunca múltiplos vencimentos.** Isso
preserva uma chamada de rede por posição elegível, igual ao fluxo de
proposta única de hoje; `rastrear(cadeia, {"tipo": "call", "relacao":
"acima", "criterio": "min", "n": 5, ...})` (ajustando `n`) já devolve até 5
strikes candidatos da MESMA cadeia em memória, sem chamada nova. Expandir
para múltiplos vencimentos fica para uma fase futura, se o Alex pedir,
com o custo de rede declarado explicitamente nela.

### D4 — Onde a IA narra: bloco novo em Posições, ao lado de "Oportunidades de opções"

**Decisão: o bloco de "4 melhores" vive em Posições/Portfólio**, como
irmão da tira `OportunidadesOpcoes` (Fase 18) — é o precedente já
estabelecido de "resumo cross-posição de opções" nesta tela, e ranking de
venda coberta por toda a carteira é exatamente esse tipo de resumo. Não é
um bloco por ativo (não pertence ao card de uma posição específica), nem
uma tela nova.

### D5 — Piso de liquidez: `LIQUIDEZ_NEGOCIAVEL`

**Decisão: reusa `LIQUIDEZ_NEGOCIAVEL`** (`server/app/options_quant.py`) —
o mesmo piso que o resto do app já usa para "líquido o bastante para
confiar no preço". Não é um piso novo e mais permissivo/restritivo
inventado só para este ranking.

### D6 — Gatilho e custo: mesma cota mensal de `/api/analyze`

**Decisão: a narração da IA consome a MESMA cota de análises do plano
comercial (Fase 25)**, pelo MESMO gate que `/api/analyze` já usa
(`_gate_analise`, BYOK → plano mensal → metering diário) — não um
orçamento paralelo. O RANKING em si (a matemática de `rastrear()`/
`avaliar()`) é custo zero e pode rodar sem gate nenhum, já que não fala
com LLM nem com o serviço MCP; só a ETAPA de narração — a chamada ao LLM
que escreve o texto sobre as 4 já escolhidas — entra no gate de análise.

## Fora de escopo (explícito)

- **Put de proteção e collar no ranking** — D1 os exclui desta fase.
  Poderiam entrar numa fase futura com uma fórmula própria (proteção não
  se mede por "prêmio ÷ perda máxima" — o objetivo é o oposto de
  maximizar prêmio).
- **Estruturas via MCP/b-mcp** — D1 as exclui; o universo desta fase é
  100% o motor interno determinístico.
- **Migrar `OpcoesCamada` para "Operar"** e **opção a descoberto além do
  que a Fase 29 já fechou** — não tocados aqui.
- **Estender a lista `candidatos` da Fase 19/28** — a UI desta fase é
  nova, não uma extensão da proposta única por posição.

## Guardrails (herdados, não re-litigar)

- **Princípio 5 do CLAUDE.md**: a escolha das 4 é 100% determinística
  (razão prêmio/perda máxima, calculada por `avaliar()`); a IA só recebe
  as 4 já rankeadas e escreve texto sobre elas — nunca "reordena por
  bom senso" nem recebe candidatos não rankeados para "escolher".
- **Nenhuma chamada nova ao serviço MCP** — achado 3 acima; qualquer plano
  que introduza uma chamada a `mcp_client`/`options_mcp_api` nesta fase
  está fora do que foi pedido.
- **Cota de análise de IA (Fase 25)**: a narração consome a MESMA cota
  mensal de `/api/analyze`, não um orçamento paralelo.
- **Paridade obrigatória** `deviceStore` ↔ `serverStore` se algum estado
  novo precisar persistir (ex.: cache do ranking do dia).
- **Guardiões de teste não se apagam** — reversão deliberada atualiza com
  nota datada.
- **Suíte canônica**: `bash scripts/executar.sh --testes`, fora do
  sandbox. Front editado → `npx vite build` antes de declarar ok.
- **Verificação adversarial (`gsd-plan-checker`) recomendada**: esta fase
  produz um NÚMERO que o usuário vai ler como "a IA recomenda isto para
  ganhar dinheiro" — o mesmo nível de cuidado que a Fase 29 aplicou ao
  gate de lastro se aplica aqui à fórmula de ranking. Decisão de rodar ou
  não fica para quando o plano estiver pronto.
