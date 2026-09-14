# Fase 30 — Curadoria de IA das 4 melhores estruturas · CONTEXT

> Consolidado por Claude, sem `/gsd-discuss-phase` assistido por subagente.
> D1 (universo) e D2 (fórmula de ranking) foram decididos pelo Alex via
> `AskUserQuestion` em 2026-09-13, entre alternativas concretas ancoradas
> no que o motor já calcula — não presumidos. O resto do desenho segue
> abaixo, com o que ainda precisa de detalhe marcado como tal, não como
> bloqueio.

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

## Em aberto — detalhe de execução, não bloqueia o desenho, mas precisa de resposta antes do plano

Estes itens são menores que D1/D2 e não exigem nova rodada de
`AskUserQuestion` — mas o plano de execução não pode inventá-los sozinho
sem risco de retrabalho; ficam nomeados para quem planejar decidir com
critério, e o Alex pode responder em uma linha se tiver preferência antes
de eu rodar `/gsd:plan-phase`:

1. **Quantas janelas por posição?** Ex.: 2 vencimentos × 3 strikes = até 6
   candidatos por posição elegível, antes do corte de liquidez. Um número
   grande demais estressa `rastrear()` sem ganho (mais candidatos ilíquidos
   descartados); pequeno demais pode deixar a "melhor" de fora. Sugestão a
   validar no plano: mirar o que `rastrear()` já usa como faixa padrão de
   vencimento/strike no motor de proposta única, multiplicado por um fator
   pequeno (2-3x), não um número arbitrário novo.
2. **Onde a IA narra as 4?** Um bloco novo em algum lugar da aba
   Opções/Portfólio, ou um card no Radar/Acompanhar? Não decidido — este
   CONTEXT não presume tela.
3. **Piso de liquidez exato do filtro D2** — reusar o `LIQUIDEZ_NEGOCIAVEL`
   que já existe em `options_quant.py` (mesmo piso do resto do app) é o
   default óbvio, a confirmar no plano.
4. **Gatilho**: clique explícito (como toda leitura paga desta app) ou
   parte do fluxo de "análise de IA" já existente (`/api/analyze`, cota
   mensal do plano)? Dado que o custo de MCP é zero (achado 3 acima), o
   único custo real aqui é a análise de IA que NARRA o resultado — essa
   sim consome a cota de análises do plano comercial (Fase 25), então o
   comportamento deve seguir o MESMO gate que `/api/analyze` já usa, não
   inventar um novo.

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
