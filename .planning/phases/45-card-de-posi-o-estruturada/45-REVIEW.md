---
phase: 45-card-de-posi-o-estruturada
reviewed: 2026-09-30T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - web/src/App.jsx
  - web/src/estruturaCard.js
  - web/src/copy.js
  - server/app/skill_ref.py
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/memoriaOpcoes.js
  - server/app/main.py
findings:
  critical: 0
  warning: 6
  info: 7
  total: 13
status: issues_found
---

# Fase 45: Code Review Report

**Reviewed:** 2026-09-30
**Depth:** standard (somente leitura; regiões novas de App.jsx via Grep + Read com offset/limit)
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Escopo: `git diff 8242c016..HEAD -- web/src server/app` (sem web_dist), mais a rota `/api/options/proposta` e `estrutura_posicao.py` como contrato de dados.

Invariantes verificadas e OK:
- Texto do motor entra só como filho JSX; nenhum `dangerouslySetInnerHTML`/`innerHTML` na região nova.
- Não há cálculo financeiro novo além de %capital e R:R (`App.jsx:4632-4633`); resultado, piso/teto, PM e total vêm de `estrutura`.
- "Encerrar" só chama `ctx.goOpcoes(...)` (`App.jsx:4695`); não há chamada de ordem no card. Stop/alvo e "Stop/alvo (IA)" nunca recebem `disabled`.
- Paridade `skill_ref.ESTRUTURA_CARD` <-> `copy.js estruturaCard` conferida chave a chave nos dois modos (`educacional`<->`estudo`, `operador`): idênticas byte a byte. Tokens de tema usados (`warnTint10`, `borderDashed`, `knob`, `borderFaint`, `borderSubtle`) existem. `abrirTickerOpcoes` valida tipo e carteira; o one-shot é limpo no mount (`OpcoesScreen.jsx:341-343`) e no reset de escopo (`App.jsx:9459`).
- Troca Estudo<->Operador: `escolher()` (`App.jsx:2464-2482`) faz `await saveConfig` e depois `window.location.reload()`. O modo do servidor (`cfg.appMode`, `main.py:3176`) já está gravado antes de o refetch da assinatura disparar, então não há vazamento de vocabulário do modo errado.

Problemas encontrados concentram-se no pool de leituras do hook, em campos parciais do motor renderizados sem guarda, e no estado desabilitado do "Encerrar".

## Warnings

### WR-01: Thunk enfileirado no pool reemite token e derruba a leitura vigente, deixando o ticker em "carregando" para sempre

**File:** `web/src/App.jsx:4407-4412` (thunk), `4387-4390` (`lerEstrutura`/`aceita`), `4422` (pool)
**Issue:** O thunk `() => lerEstrutura(t, sig)` captura `sig` na criação e não reconfere `pedidasRef.current[t] === sig` ao iniciar. `executarComTeto(thunks, 3)` só inicia o 4º thunk em diante quando um dos 3 trabalhadores libera.

Cenário com 5 ativos com pernas:
1. O pool 1 roda os tickers A, B, C. D e E ficam na fila.
2. O usuário fecha uma perna de D. A `chave` muda, o efeito roda de novo, `pedidasRef[D]` passa a `sigNova` e o pool 2 inicia `lerEstrutura(D, sigNova)` (token k, `ultimoRef[D] = k`).
3. O pool 1 chega ao thunk antigo de D e chama `lerEstrutura(D, sigVelha)`. Isso gera o token k+1 e sobrescreve `ultimoRef[D] = k+1`.
4. A resposta k falha em `meu === ultimoRef[D]`. A resposta k+1 falha em `pedidasRef[D] === sigVelha`. As duas são descartadas.
5. `leituras[D]` fica `{status:"carregando", emVoo:true}` sem promessa que a resolva. O `BotaoAtualizarEstrutura` fica `disabled` (`emVoo`), e `atualizar` sai cedo por `atual.emVoo` (`4428`). Só desmontar a tela ou trocar de escopo destrava.

O mesmo vale se a assinatura muda com o thunk ainda na fila e a nova leitura já em voo. Exige mais de 3 ativos com opções, o que é raro hoje, mas o estado é irrecuperável pela UI.
**Fix:**
```js
thunks.push(() => {
  if (!vivoRef.current || pedidasRef.current[t] !== sig) return Promise.resolve();
  return lerEstrutura(t, sig);
});
```
Se o thunk for pulado, a leitura da assinatura vigente já está coberta pelo pool que a criou. Faça o mesmo em `atualizar` (`4433`).

### WR-02: Pool continua disparando requisições após desmontar/trocar escopo, e o teto de 3 concorrentes não é global

**File:** `web/src/App.jsx:4422`, `4433`, `4385`
**Issue:**
- Após desmontar (`vivoRef=false`) ou após `escopoSeq` mudar, os thunks pendentes do pool antigo continuam chamando `store.optionsProposta` (o guard só descarta a resposta, não a chamada). Cada chamada consome cota da brapi (orçamento de 15k/mês do app inteiro, CLAUDE.md > Constraints) e, na troca de conta, roda com o token da conta nova.
- `executarComTeto` é instanciado a cada efeito e a cada `atualizar`. Uma mudança de `chave` durante um carregamento, ou Atualizar em outro ticker, soma um pool novo ao antigo: até 6 ou mais concorrentes. Isso contradiz a premissa "teto de 3" (comentário `4366`, guardião `test_estrutura_card_ui.mjs:38`).
**Fix:** guarda `vivoRef` e `pedidasRef` dentro do thunk (ver WR-01) e uma fila única por instância do hook. Por exemplo, um `Promise` encadeado em `useRef`, ou um `emVooRef` contador que o `trabalhador` consulte antes de iniciar.

### WR-03: Perna com campo parcial do motor renderiza "×null" e prefixo vazio

**File:** `web/src/App.jsx:4672` (linha da perna), `copy.js` `estruturaQtdPerna`, `estruturaPernaLinha`
**Issue:** `estrutura_posicao._perna` devolve `quantidade = _num(op.qty)` (`estrutura_posicao.py:86`), e `_num` devolve `None` para 0, negativo e não numérico. O cliente faz `cp.estruturaQtdPerna(perna.quantidade)` sem guarda, o que produz o literal `×null` na tela. `perna.tipo` vem `""` quando `optionType` falta (`estrutura_posicao.py:82`), e a linha começa com espaço: ` vendida · strike ...`. Com `premioEntrada` null, a linha vira `prêmio R$ — → R$ —` (o `price()` protege contra NaN, mas o "R$" fica solto). Esses são exatamente os caminhos `dados_invalidos`/`premio_indisponivel` que o motor já sinaliza. O critério "nenhum NaN/undefined/null na tela" falha nesses casos.
**Fix:**
```jsx
{perna.quantidade != null ? " " + cp.estruturaQtdPerna(perna.quantidade) : ""}
// premio: só renderiza "R$" quando o número existe
{perna.premioEntrada == null ? cp.semPremioPerna : cp.estruturaPremioLinha(price(perna.premioEntrada), ...)}
```
Trate `tipo` vazio com fallback textual (ex.: `perna.tipo || "OPÇÃO"`).

### WR-04: "Encerrar" desabilitado pode ficar sem motivo e com `aria-describedby` apontando para id inexistente; `disabled` nativo impede o foco que leria o motivo

**File:** `web/src/App.jsx:4524`, `4693-4704`
**Issue:**
1. `bloqueado = !(e.encerrar && e.encerrar.permitido)`. Se `e.encerrar` estiver ausente (servidor antigo ou resposta parcial) ou `texto` for null, o botão fica desabilitado sem nenhuma explicação (princípio 9) e `aria-describedby="encerrar-motivo-<t>"` referencia um id que não é renderizado (`4704` exige `e.encerrar.texto`).
2. Botão com `disabled` nativo não recebe foco por teclado. Leitor de tela e teclado nunca chegam ao botão para ouvir o `aria-describedby`; `aria-disabled` junto de `disabled` é redundante. A spec (§248) pede o motivo como texto visível, que é atendido para quem enxerga, mas o vínculo programático é inócuo.
**Fix:**
```jsx
const motivo = bloqueado && e.encerrar && e.encerrar.texto ? e.encerrar.texto : null;
<button ... aria-disabled={bloqueado}
  aria-describedby={motivo ? "encerrar-motivo-" + p.t : undefined}
  onClick={bloqueado ? undefined : () => ctx.goOpcoes(...)}   // sem `disabled` nativo: continua focável
/>
```
Se `bloqueado` sem `texto`, exiba uma frase fallback (chave nova em `ESTRUTURA_CARD`, com espelho) em vez de silêncio.

### WR-05: Card legado ainda renderiza "R:R atual —" quando o preço está abaixo do stop

**File:** `web/src/App.jsx:4965`
**Issue:** `mostraRR(p)` só verifica `stop != null && alvo != null`. Com stop e alvo definidos e `cur <= p.stop` (o caso mais relevante: preço já furou o stop), `rr` é `null` e a linha mostra `R:R atual —`, o que viola "R:R nunca renderiza —" (45-UI-SPEC.md:165). O card estruturado trata corretamente (`4644`: `rr != null &&`). O guardião W-001 (`test_estrutura_card_ui.mjs`) fixa apenas o `mostraRR(p) && (<span>R:R atual` e não pega isso.
**Fix:** no legado, `{mostraRR(p) && rr != null && (<span>R:R atual <b ...>{rr.toFixed(2)}</b></span>)}` (a exceção deliberada continua limitada ao gate de stop/alvo; o "—" some). Atualize o guardião com nota de reversão.

### WR-06: `nomeTexto` nulo vira "undefined"/"null" no aria-label da régua e chip sem nome

**File:** `web/src/App.jsx:4474`, `4538`
**Issue:** `estrutura_posicao_txt` devolve `None` quando a chave `nome_<x>` não existe (fail-closed, `skill_ref.py:820`), então `nomeTexto` pode ser null. `cp.estruturaFaixaAria(e.nomeTexto, ...)` interpola o template `${nome}` e a frase lida por leitor de tela começa com "null. ...". Em `4538`, com `e.nome` definido mas `nomeTexto` vazio, o chip vira `ESTRUTURA · ` (sem nome).
**Fix:** `cp.estruturaFaixaAria(e.nomeTexto || "Estrutura de opções", ...)` e no chip `e.nome && e.nomeTexto ? ... : chip_estrutura_generica`.

## Info

### IN-01: Nenhum teste comportamental do hook de corrida; guardiões são regex sobre o texto de App.jsx

**File:** `web/tests/test_estrutura_card_ui.mjs:32-40`
**Issue:** Os testes fixam a presença de `corteRef`, `meu === ultimoRef`, `executarComTeto(..., 3)`, mas nada exercita o hook com respostas fora de ordem, troca de escopo em voo ou fila com mais de 3 ativos. É por isso que WR-01/WR-02 passam na suíte. Extraia a máquina de leituras para módulo puro (como `estruturaCard.js`) e teste em Node com promessas controladas.

### IN-02: Chip "vence dd/mm · — dia(s)" quando `diasParaVencimento` é null

**File:** `web/src/App.jsx:4525`, `estruturaCard.js:72`
**Issue:** `chipVencimento` devolve `dias: null` e o texto sai `vence 20/10 · — dia(s)`. Não é NaN, mas é ruído. Omita o trecho de dias quando null (ex.: chave `chipVenceSemDias: (ddmm) => \`vence ${ddmm}\``).

### IN-03: Callout de estado pode aparecer vazio

**File:** `web/src/App.jsx:4553-4563`
**Issue:** Para `tom` diferente de `linha` (atenção/info/encerrada), o bloco é renderizado mesmo com `e.estadoTexto` null: sobra um "⚠" ou "ⓘ" com borda e sem frase. Guarde com `e.estadoTexto ?`, como o ramo `linha` já faz.

### IN-04: Quatro controles equivalentes para editar stop/alvo no mesmo card

**File:** `web/src/App.jsx:4610`, `4616`, `4623`, `5019`
**Issue:** "definir ▸" (stop), "definir ▸" (alvo), "✎ definir stop e alvo" e o rodapé compartilhado "✎ Editar stop/alvo" (este com `padding: 5px 0`, abaixo dos 44px) chamam o mesmo `setEditFor`. É redundante e o rodapé herdado não cumpre o alvo de 44px da spec. Recomendo manter um só na área STOP/ALVO e subir o rodapé para 44px ou ocultá-lo no modo estruturado.

### IN-05: Anel de foco (`:focus-visible`) da spec não foi definido

**File:** `web/src/App.jsx:4358-4361`, `4560`, `4610`, `4693-4703`; `45-UI-SPEC.md:246`
**Issue:** A spec pede anel `T.accent` 2px offset 2px em todo botão/link novo, "se inexistente, definir no componente". `grep focus-visible` em `web/src` e `index.html` não encontra nada; os botões novos dependem do outline padrão do navegador (que some com `border:none` em alguns WKWebView). Defina uma regra global ou estilo do componente.

### IN-06: Falha em "Atualizar" descarta a última leitura boa

**File:** `web/src/App.jsx:4393`, `4429-4432`
**Issue:** `atualizar` mantém `status:"ok"` com `emVoo:true`, mas se a nova chamada falhar, o `catch` grava `{status:"falha"}` sem `estrutura`. O card estruturado some e cai no legado com "indisponível" por causa de uma falha transitória. Guardar `estrutura`/`at` anterior e marcar `erroAtualizar:true` preservaria a leitura carimbada (`Opções lidas de X em <at>`) com aviso de que a atualização falhou. É decisão de produto (princípio 4: não inventar), mas o carimbo já protege.

### IN-07: `goOpcoes` com `abrirTicker` sobrescreve o ticker lembrado e não move o foco; `operador` na assinatura é código morto

**File:** `web/src/App.jsx:9537`, `estruturaCard.js:24`
**Issue:** (a) `setOpcoesMemoria({ticker, aba:"oportunidades"})` substitui a escolha anterior de ticker do usuário em Montar sem aviso; efeito colateral aceitável, mas não documentado no UI-SPEC. Nenhum foco é levado ao painel aberto ao chegar em Opções (a11y). (b) `operador` na `assinaturaEstrutura` só dispara refetch redundante nos ~700 ms antes do `window.location.reload()` (`App.jsx:2482`), consumindo uma chamada de brapi por ativo sem uso. Se o reload for removido no futuro, ela passa a ser necessária, então mantenha, mas registre o motivo. Além disso, `useEstruturasPosicao` refaz a leitura a cada remontagem da Carteira (sem cache entre montagens): custo de brapi aceito no comentário `4366`, listado aqui apenas como lembrete do orçamento de 15k/mês.


## Correções aplicadas

Aplicadas em 2026-09-30 (iteração 1), um commit por WR, na branch v2/interacao-estrutural.

- WR-01 (`7419dff3`): o item da fila confere vivo + assinatura vigente quando chega a vez e, se superado, abandona sem chamar a API (a leitura que o superou é dona do estado, então `emVoo` não fica órfão). A lógica saiu do hook para `criarFilaLeituras` em `estruturaCard.js`, com teste comportamental (IN-01 parcialmente endereçado; o hook em si segue com guardião estático).
- WR-02 (`01b63258`): UMA fila por instância do hook (`filaRef`), usada pelo efeito e por `atualizar` (teto de 3 global). `cancelar()` no cleanup de desmontagem e na troca de `escopoSeq`; `vale()` também confere a época (`corteRef`) capturada ao enfileirar. Cleanup zera `pedidasRef` para o efeito repedir tudo se o hook remontar (StrictMode).
- WR-03 (`70d58f5f`): `×qtd` omitido com quantidade null; tipo vazio sem espaço inicial (`.trim()`); prêmio de entrada null vira `prêmio —` ou `prêmio atual R$ x`, sem seta. Chaves neutras `semPremioPerna` e `estruturaPremioSoAtual` só em copy.js.
- WR-04 (`9dfaf2e2`): `disabled` nativo trocado por `aria-disabled` + `onClick` que não navega (botão segue focável); motivo do motor com fallback neutro `encerrarSemMotivo` (só em copy.js, sem par em skill_ref.py); `aria-describedby` só quando o id existe.
- WR-05 (`9da8a7cf`): `valorRR`/`mostraRR(p, cur)` em `estruturaCard.js`; R:R só com fórmula finita e positiva, nos DOIS cards. Card legado não mostra mais `R:R atual —`. Continua exceção deliberada ao D-02. Guardião W-001 atualizado com nota de reversão (sem `cur`, `mostraRR(p)` mantém o gate antigo).
- WR-06 (`a4a4d52a`): `nomeTexto` nulo cai no chip `ESTRUTURA · OPÇÕES` (mesmo tratamento de fora_da_biblioteca) e o aria-label da régua usa `estruturaGrupoAria` como fallback.

Guardiões alterados por reversão deliberada (com nota "Fase 45 (code review)"): `hook usa executarComTeto(..., 3)` virou `criarFilaLeituras(3)` via `filaRef` (WR-01/02); `R:R atual sob mostraRR(p) &&` e `const rr = mostraRR(p)` passaram a `mostraRR(p, cur)`/`valorRR(p, cur)` (WR-05).

### Dívida deixada (INFO não corrigidos)

IN-02 (chip "vence dd/mm · — dia(s)"), IN-03 (callout de estado vazio), IN-04 (controles redundantes de stop/alvo e rodapé < 44px), IN-05 (anel `:focus-visible`), IN-06 (falha em Atualizar descarta a última leitura boa), IN-07 (`goOpcoes` sobrescreve ticker lembrado; `operador` na assinatura). IN-01 fica parcial: a fila tem teste comportamental, mas o hook (`useEstruturasPosicao`) ainda só tem guardião por regex, sem teste com respostas fora de ordem.

---

_Reviewed: 2026-09-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
