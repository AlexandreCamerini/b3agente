# Quick Task 260908-ldg: gate de liquidez em três faixas com consentimento do usuário — Context

**Gathered:** 2026-09-08
**Status:** Ready for planning
**Decisões:** confirmadas pelo Alex ("confirmo o quadro") — LOCKED, não re-litigar.

<domain>
## Task Boundary

Trocar o corte binário de liquidez (score ≥ 40 → existe; < 40 → não existe)
por três faixas com comportamento diferente em cada ponto onde a nota é usada,
para que o usuário VEJA o grau de liquidez e decida — sem o simulador jamais
inventar um preço de execução.

Pré-requisito já entregue: `liquidity_score` recalibrado (quick 260908-dnl,
commit 3c49f43). A fórmula NÃO muda aqui.

</domain>

<decisions>
## Implementation Decisions (LOCKED)

### O quadro

| faixa | descoberta (card/tira) | seleção (motor) | execução (Operador) |
|---|---|---|---|
| NEGOCIÁVEL ≥ 55 | aparece | preferido | normal |
| DIFÍCIL 30–54 | aparece, com a nota visível | só se não houver negociável | consentimento explícito |
| SEM MERCADO < 30 | aparece a nota, sem proposta | nunca | bloqueado, sem override |

As faixas JÁ existem em `opcoes_lastreadas._label_liquidez` (55/30). Reusar
— "não inventar uma segunda escala" (docstring da própria função). Centralizar
os dois limiares numa fonte única (hoje `opcoes_motor.LIQUIDEZ_MINIMA = 40` é
o número que morre).

### Seleção: duas passadas, nunca mistura
`opcoes_motor.rastrear()` seleciona primeiro entre NEGOCIÁVEL (≥55); só se a
lista vier vazia, segunda passada entre DIFÍCIL (≥30). Nunca escolhe um
DIFÍCIL de strike "melhor" por cima de um NEGOCIÁVEL. A proposta é a coisa
mais próxima de recomendação que o produto tem.

### Consentimento é passo PRÓPRIO, não enxerto
Hoje só call (`confirmAbrirCoberta`) e collar (`confirmAbrirCollar`) têm
`window.confirm`; a put abre sem confirmação. O consentimento de liquidez é um
confirm separado que dispara para QUALQUER estrutura quando a pior perna é
DIFÍCIL — antes do confirm específico da estrutura, se houver.

### O texto do consentimento vem do MOTOR
Os números (score, volume do dia, spread) e a frase são determinísticos e
saem do backend em `proposta.liquidez` (`faixa`, `volume`, `spreadPct`,
`aviso`), com a frase em `skill_ref` nos DOIS modos (guardião de paridade
`test_opcoes_collar_vocab.py:74` exige as mesmas chaves em operador e
educacional). O front exibe `liquidez.aviso` verbatim — "o front nunca compõe
vocabulário". Forma de referência (operador):
"Liquidez DIFÍCIL (38/100): 300 unidades negociadas hoje, spread 66%. O preço
simulado é o do último negócio; no mercado real sua ordem poderia não ser
atendida a esse preço. Continuar?" — spread ausente → dizer "sem livro
publicado", nunca 0%.

### Servidor exige o consentimento (anti-padrão "esconder só no front")
`POST /api/options/lastreada/abrir` e `/abrir-collar`: pior perna DIFÍCIL sem
`body.aceitaLiquidezDificil === true` → 400 com mensagem PT-BR acionável;
pior perna SEM MERCADO → 400 sempre, sem flag que destrave (princípio 4 do
CLAUDE.md: sem negócio no dia não há prêmio real para simular). NEGOCIÁVEL
ignora o flag.

### Paridade dos dois stores
`web/src/persistence.js`: o campo novo do corpo entra em `deviceStore` E
`serverStore` (guardião `test_api_parity.mjs`; regra do repo).

### Descoberta
`GET /api/options/gate/{t}`: `liquida` passa a significar "melhor contrato ≥
30" (DIFÍCIL ou melhor — compat com todo consumidor de `opGate.liquida`), e a
resposta ganha `faixa` e `melhorScore`. SEM MERCADO cai no estado vazio que já
existe (`tiraOpcoesSemCobertura`), com o texto ajustado para nomear a faixa.

### Agente autônomo
Não abre estruturas de opção (só fecha vencidas). Se o planner encontrar
qualquer caminho automático de abertura, ele só pode operar em NEGOCIÁVEL —
não há humano para consentir. Registrar como guardião se existir o caminho.

### Modo Estudo
Nunca executa. A graduação é ensino puro: verbete determinístico
"liquidez de opção" em `server/app/conceitos.py` (`CONCEITOS`), custo zero de
LLM, com `campos` lidos da proposta (score, faixa, volume, spread), no padrão
dos verbetes existentes. Ligado a partir do chip de liquidez do card.

### Claude's Discretion
- Nome exato da constante/estrutura que centraliza 55/30.
- Como o front descobre que precisa do confirm (ler `liquidez.faixa` da
  proposta é o esperado).
- Ordem dos dois confirms quando ambos existem (liquidez primeiro, depois o
  da estrutura).

</decisions>

<specifics>
## Specific Ideas

- Os 20 arquivos de cadeia real de 2026-09-08 estão em
  `/private/tmp/claude-501/-Users-acamerini-dev-borisv2/31307cb9-7fa3-4f76-9369-16d54ae23ca0/scratchpad/chains/*.json`
  (não versionados). Servem para medir quantos contratos caem em cada faixa
  com a fórmula atual antes de escrever os guardiões.
- Guardiões esperados (mínimo): duas passadas de `rastrear`; gate devolve
  faixa; `/abrir` recusa SEM MERCADO sempre; `/abrir` recusa DIFÍCIL sem flag e
  aceita com flag; NEGOCIÁVEL ignora flag; paridade das chaves novas em
  skill_ref (dois modos) e em copy.js (estudo/operador); paridade dos stores;
  verbete registrado em `conceitos.ids()`.

</specifics>

<canonical_refs>
## Canonical References

- `CLAUDE.md` §Princípios 4 (nunca inventar valor), 5 (cálculo determinístico),
  9 (estados completos); §Guardrails (manchete só do motor; paridade dos
  stores; guardião não se apaga).
- `docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md` — por que o gate estava
  impossível e o que a recalibração fez.
- `.planning/quick/260908-dnl-*/260908-dnl-SUMMARY.md` — a fórmula atual.
- ADR-017 (setup aposentado) como analogia de "o front não decide sozinho o
  que o motor já decidiu".

</canonical_refs>

<scope_fence>
- NÃO alterar `liquidity_score` (acabou de ser recalibrado com guardião).
- NÃO rodar `scripts/bump.sh` nem `scripts/publicar-web.sh` — a branch já tem
  publicação pendente de promoção (PR #31); publicação desta task é passo
  posterior, registrar como pendência.
- NÃO tocar `server/web_dist`.
</scope_fence>
