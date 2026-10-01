# Phase 46: Carteira v6 — card de posição com modos Estudo e Operador - Context

**Gathered:** 2026-09-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesenho de UI/UX do card de posição da Carteira conforme o protótipo aprovado
`~/Downloads/Carteira Boris+ v6 (standalone).html` (bundle do Claude Design; fonte legível
extraída: template + `class Component`, 66 KB). Entrega:

- Card fechado com **um visual e um estado**, igual nos dois modos (régua stop←agora→alvo
  para ação com plano; faixa no vencimento piso·◆BE·teto para composta com BE calculado).
- Card aberto com seletor `Ação | Opções (n)` e flip 3D só nessa área
  (170 ms + 170 ms; `prefers-reduced-motion` troca sem animação).
- Estudo: simulador "e se?" + termos tocáveis ("TOQUE NOS TERMOS" → painel com definição +
  "No seu caso:"). Operador: payoff no vencimento + grade 3×2 (BE · Até BE · Até K ·
  Ganho máx. · Perda máx. · Lastro) com a conta ao tocar. Remove a folha/chips "Entenda os termos".
- O modo muda só: cor de destaque, rótulos de botão/saída e a camada didática.
  Números, estados e ações são idênticos.

**Fora do escopo (fixo):** qualquer mudança em **método de cálculo**. A decisão do Alex
(2026-09-30): "a ideia é alterar somente o UI/UX sem alterar os métodos de cálculo,
continuando a calcular tudo de forma centralizada no backend".

Critérios de aceite da spec original (card fechado 1 visual/1 estado; flip só em Ação/Opções;
Estudo com simulador + termos; Operador com payoff + conta; sem cenário → nada desenhado;
valores todos do backend) valem integralmente, **exceto** o item "testes `optionsCalc`" — ver D-02.

</domain>

<decisions>
## Implementation Decisions

### Cálculo (travado)
- **D-01:** Nenhuma regra de cálculo muda. O backend (`server/app/opcoes_payoff.py`,
  `estrutura_posicao.py`) segue como única fonte de payoff, BE, ganho/perda máx., piso/teto.
  O `calc()` embutido no protótipo é só da prévia e **não é portado** para o front.
- **D-02:** **Não existe `optionsCalc` no cliente.** Os testes UGPA3 (PM 39,50, CALL K 42,25
  prêmio 1,49, 1.000 → BE 38,01, ganho +4.240, perda −38.010) e CXSE3 (PM 20,06, K 21,02,
  prêmio 0,25 → BE 19,81, +1.210, −19.810) viram **testes pytest do backend** sobre o
  mesmo caminho que o card já consome. O guardião `test_estrutura_para_payoff.mjs`
  (proíbe aritmética nos campos financeiros do adaptador) permanece intacto.
- **D-03:** Números que o protótipo derivava no front — "Até BE", "Até K" (distância % do preço
  de hoje), "Alta forte" (K × 1,09), preço de cada chip — **passam a ser campos do backend**,
  calculados em `estrutura_posicao`/módulo de opções (mesma convenção de arredondamento do
  motor). `1,09` vira constante nomeada no backend (decisão de produto), não literal no componente.

### Simulador "e se?" sem cálculo no front (recomendação aceita por delegação)
- **D-04:** O backend devolve, junto da faixa da estrutura, um bloco `simulador`:
  grade de preços (`min`, `max`, `passo`) com o resultado da estrutura em cada ponto,
  mais **pontos nomeados** (`hoje`, `equilibrio`, `teto`, `alta_forte`) com o resultado exato.
  Todos os valores vêm de `resultado_no_vencimento` / `perfil_da_estrutura` já existentes
  (a `curva` já é produzida por `perfil_da_estrutura`; hoje a `faixa` não a expõe).
  O slider (`input range`, alvo ≥ 44 px) tem `step` = `passo` da grade e **lê** o resultado
  por índice — zero aritmética no cliente; funciona sem nova chamada de rede ao arrastar.
- **D-05:** Alternativa descartada: endpoint por preço com debounce (a cada arrasto uma chamada,
  latência e falha no meio do gesto). Só entra como fallback se o planner provar que a grade
  fica grande demais (limite sugerido ~ 1,2 mil pontos; passo ≥ tick de R$ 0,05).
- **D-06:** Caixa de zona (abaixo do BE / entre BE e K / acima de K) e os textos de resultado
  são determinísticos: a **zona** é um rótulo do backend associado a cada ponto/intervalo
  (o front não compara preço com BE/K). Texto em `skill_ref.py` ↔ `copy.js`, paridade
  byte a byte (guardião existente).

### Operador: payoff + grade com a conta
- **D-07:** Cada célula da grade 3×2 chega do backend como `{rotulo, valor, conta}`;
  `conta` é a linha pronta com os números da posição (`BE = PM − prêmio` / `39,50 − 1,49 = 38,01`).
  Para estratégia sem fórmula fechada o backend devolve `conta: null` e o front mostra
  "Calculado pela camada de opções do app". Sem ⓘ e sem card de termos no Operador.
- **D-08:** Gráfico = curva do backend. Reutilizar `web/src/opcoes/PayoffChart.jsx`
  (adaptado ao estilo v6) vs. SVG novo e enxuto: **decisão do planner** (ver Claude's Discretion).
  Regras fixas: linha branca, zero, K tracejado verde, hoje tracejado na cor do modo,
  ◆ BE na linha zero, fundo vermelho antes do BE / verde depois, **sem texto dentro do desenho**
  (legenda abaixo), `role="img"` + `aria-label` descritivo. Sem curva → nada desenhado.

### Estudo: termos tocáveis e glossário (decisão do Alex: glossário vem da KB)
- **D-09:** Definição do termo vem de `GET /api/kb/catalogo` (`kb.py`), via o ponte puro
  `web/src/glossario.js` (`verbeteDoCatalogo`). O protótipo traz definições fixas no
  componente — **não copiar**. Termo sem verbete válido na KB **não é sublinhado/tocável**
  (princípio 4: nunca inventar).
- **D-10:** Verbetes que faltarem na KB (candidatos: lastro, call coberta, teto, equilíbrio,
  piso, R:R, stop, alvo, preço médio — o researcher confere o que já existe) entram nesta
  fase como **conteúdo determinístico em `kb.py`/`conceitos.py`**, sem promessa de
  rentabilidade. Distinto do DIDA-01 (expectativa matemática × taxa de acerto), que é a Fase 47.
- **D-11:** "No seu caso:" é frase determinística do backend com os números da posição
  (padrão `conceitos.montar` / `skill_ref`); a mesma frase serve ao termo tocado e ao
  "Bóris explica". Mapa de termos por tipo de posição (call coberta; ação com plano; sem plano;
  composta não classificada) mora no backend. Um termo aberto por vez; tocar de novo fecha;
  painel com `role="status"` e botão "Entendi".
- **D-12:** "Bóris explica" (1 linha, só Estudo) é **texto determinístico do caso**, nunca LLM
  (princípios 5–7 do CLAUDE.md). Operador não mostra.

### Relação com o card da Fase 45
- **D-13:** O v6 **evolui** `CardPosicaoEstruturada` (`web/src/App.jsx:4535`) e a lógica pura
  `web/src/estruturaCard.js`; não reescreve. Estados do motor (ESTR-04) mapeiam para o "um
  estado/próximo passo" pela prioridade da spec: ações travadas pela CALL → sem plano/plano
  incompleto → fora do plano → dentro do plano; pendências (ex.: nota de corretagem) e
  resultado parcial como linhas extras.
- **D-14:** O padrão vale para **toda posição** (inclui ação só com plano stop/alvo → régua),
  não só estruturadas. Componentes novos ficam **antes de `LinhaChamadaOpcoes`** (guardiões fatiam
  `App.jsx` por `function X`→`function Y`; sem `disabled=` dentro de `CarteiraScreen`).
- **D-15:** Guardiões da 45 que a v6 contradiz deliberadamente são **atualizados com nota**
  (nunca apagados). `test_opcoes_collar_vocab.py` varre todo `web/src/*.js(x)`: texto novo
  nasce em `skill_ref.py`/`copy.js`, sem âncoras proibidas.

### Cobertura de estruturas
- **D-16:** Mesmo conjunto de blocos para qualquer estrutura em que o backend devolve `faixa`
  (call coberta, collar, put de proteção — Fase 44). Sem `faixa`/curva → caixa tracejada
  "Cenários não calculados para esta combinação" e, nos termos, "aguardando o cálculo do app".
  Nunca desenhar gráfico sem dado. Encerrar: manter "Encerrar opção em Opções"
  (limite da 45: só recompra a call; dívida registrada, **não** resolver aqui).

### Acessibilidade e layout (da spec, travado)
- **D-17:** Alvos ≥ 44 px (exceto termos inline), `aria-expanded`/`aria-pressed` nos toggles,
  contraste ≥ 4,5:1 nos 4 temas×modo (guardião `test_estrutura_card_contraste.mjs`),
  `tabular-nums`, layout a partir de 320 px e texto a 130 %. Flip respeita
  `prefers-reduced-motion`.

### Claude's Discretion
- Reutilizar `PayoffChart.jsx` vs. SVG novo (D-08), formato exato do bloco `simulador`
  (D-04), nomes de campo novos, e o fatiamento em ondas (App.jsx serializa as ondas de UI).
- Passo/limites da grade por ativo (respeitar tick e o teto de pontos).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Protótipo e spec
- `~/Downloads/Carteira Boris+ v6 (standalone).html` — protótipo aprovado (fixtures UGPA3, CXSE3, ITSA4 sintético, B3SA3, PETR4, BBAS3; textos de termos; `flip()`, `calc()`, `learnVals()`).
  Fonte legível já extraída em `/tmp/claude-501/tpl.html` (efêmero: re-extrair do bundle se sumir).
- Spec original colada pelo Alex na sessão de 2026-09-30 (critérios de aceite) — reproduzida em "Phase Boundary" acima.
- Link de design (exige login): `https://claude.ai/design/p/93ba0b64-6af7-43f8-b0b6-3177a43abcaf`.

### Fase 45 (base a evoluir)
- `.planning/phases/45-card-de-posi-o-estruturada/45-CONTEXT.md`, `45-UI-SPEC.md`, `45-PATTERNS.md`, `45-04-SUMMARY.md`, `45-05-SUMMARY.md` — decisões D-01..D-11, dívida.
- `.planning/phases/44-motor-estrutura-por-ativo/` — contrato do motor de estrutura (`faixa`, estados, motivos).

### Backend de cálculo (fonte única)
- `server/app/opcoes_payoff.py` — `perfil_da_estrutura`, `resultado_no_vencimento`, `dominio_da_curva`, `segmentos_da_curva`.
- `server/app/estrutura_posicao.py` — `ler_estrutura`, `_faixa` (piso/teto/perda/ganho/breakevens).
- `server/app/skill_ref.py` — vocabulário por modo (paridade com `web/src/copy.js`).
- `server/app/kb.py`, `server/app/conceitos.py`, rotas `GET /api/kb/catalogo`, `GET /api/kb/buscar`, `POST /api/conceito/{cid}` (`server/app/main.py`).

### Front
- `web/src/App.jsx` (`CardPosicaoEstruturada` 4535, `LinhaChamadaOpcoes` 4757, `CarteiraScreen` 4801) — nunca ler inteiro.
- `web/src/estruturaCard.js`, `web/src/opcoes/PayoffChart.jsx`, `web/src/opcoes/estruturaParaPayoff.js`, `web/src/glossario.js`, `web/src/entendimento.jsx`, `web/src/copy.js`.

### Guardiões
- `web/tests/test_estrutura_card_{logica,ui,contraste,espelho}.mjs`, `test_estrutura_para_payoff.mjs`, `test_payoff_responsivo.mjs`, `server/tests/test_opcoes_collar_vocab.py`, `test_skill_ref.py`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `perfil_da_estrutura().curva` (`preco_objeto`, `resultado`) — já produzida no backend; falta só expô-la/amostrá-la na `faixa`/`simulador`.
- `glossario.js` (`catalogoKbValido`, `verbeteDoCatalogo`) — ponte pura para definições da KB.
- `PayoffChart.jsx` + `estruturaParaPayoff.js` — gráfico e adaptador (só renomeia chaves).
- `estruturaCard.js` — régua (`dominioRegua`, `posRegua`), `tomDoEstado`, `chipVencimento`, `criarFilaLeituras`.
- `useEstruturasPosicao` (App.jsx:4372) — busca/estados carregando/falha da estrutura.

### Established Patterns
- Frases só em `skill_ref.py`, espelhadas em `copy.js` byte a byte (teste trava).
- Campo `null` = "indisponível", nunca `0`; fonte/horário sempre visíveis.
- Pares `deviceStore` ↔ `serverStore` em `persistence.js`: método/campo novo entra nos DOIS (só se a fase tocar persistência — hoje a estrutura é lida do servidor).
- Suíte canônica `bash scripts/executar.sh --testes` (fora do sandbox, 1× por onda pelo orquestrador); `npx vite build` e `npx cap copy ios` antes.

### Integration Points
- Rota que devolve `estrutura` por ativo (`main.py`) ganha campos aditivos (`simulador`, células da grade, textos de termos) — contrato **aditivo**, sem quebrar o card da 45 em produção.
- Gap a mapear no research: campos que o protótipo mostra e a `estrutura` talvez não entregue hoje (qualidade do prêmio por perna, origem+horário da cotação, dias até o vencimento, livres × lastro, setup/gatilho/origem da posição, compras com explicação do PM).

</code_context>

<specifics>
## Specific Ideas

- Fixtures de aceite: UGPA3 e CXSE3 (call coberta, sem piso) e ITSA4 sintético (put + call sem BE → "aguardando o cálculo do app", sem cenário).
- "Alta forte" = K × 1,09 (constante do protótipo, a virar constante nomeada no backend).
- Rodapé: Estudo "Ver detalhes e aprender ▾" / Operador "Detalhes e ações ▾"; saída: Estudo "Simular venda" / Operador "Registrar saída"; desativada com "0 ações livres" quando tudo é lastro.

</specifics>

<deferred>
## Deferred Ideas

- Caminho de encerramento da put do collar / put de proteção (dívida da 45) — fase futura.
- IN-02..07 do `45-REVIEW.md` e `TravaPill` legado (AA 4,18 no claro) — só se o redesenho tocar.
- Fase 47 (Didática, DIDA-01..02): verbete expectativa matemática × taxa de acerto — renumerada de 46.
- Registrar o `passed` da `45-VERIFICATION.md` (validação do Alex em 2026-09-30) via `/gsd-verify-work` — pendente.

</deferred>

---

*Phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador*
*Context gathered: 2026-09-30*
