---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
reviewed: 2026-09-16T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - server/app/main.py
  - web/src/App.jsx
  - web/src/copy.js
  - web/src/opcoes/CandidatoOpcao.jsx
  - web/src/opcoes/CuradoriaEstruturas.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/OportunidadesOpcoes.jsx
  - web/src/opcoes/useOpcoesPropostas.js
  - web/src/version.js
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Fase 32: Relatório de Code Review

**Revisado:** 2026-09-16
**Profundidade:** standard
**Arquivos revisados:** 9
**Status:** issues_found

## Escopo e método

Range usado: `bd459f1..HEAD` (branch local `main` estava atrasada, conforme
indicado). Arquivos de código-fonte tocados pela fase, dentro de `web/src/**`
+ `server/app/main.py`: os 9 listados acima. `server/app/main.py` só teve o
comentário/valor de `SERVER_BUILD_ID` bumpado — nenhuma rota, lógica ou
import mudou; não há achado ali. `server/web_dist/**` (build artifact) e
`.planning/**` foram excluídos por instrução explícita de escopo. Os 10
arquivos `web/tests/*.mjs` tocados/criados pela fase também ficaram fora do
escopo pedido (revisão restrita a `web/src/**`) e não foram auditados linha a
linha — apenas espiados para confirmar o mecanismo de exceção documentado em
`deferred-items.md`.

Item de `<ja_conhecido>` conferido e **confirmado, não expandido**: as três
cópias do padrão `v * (X || 0)` / `(Y || 0)` (`CuradoriaEstruturas.jsx:91`,
`CandidatoOpcao.jsx:57` e `:143-144`, mais a já registrada
`PropostaLastreada.jsx:200,268-269`, arquivo não tocado por esta fase) — não
existe uma quarta cópia introduzida por este diff.

## Resumo

O diff é majoritariamente extração/movimentação de componentes (ADR-027
Emenda 3) com correção pontual de um estado de erro que se disfarçava de
"vazio" (princípio 4 do CLAUDE.md). Manchete do motor determinístico segue
renderizada verbatim em todos os três componentes extraídos (guardrail CVM
intacto); nenhum cálculo de carteira/opção foi tocado; paridade de copy entre
`COPY.estudo`/`COPY.operador` está correta para as 9 chaves novas. Não há
achado de severidade Critical (sem injeção, sem segredo hardcoded, sem
cálculo financeiro migrado para a IA, sem veto de stop/alvo).

Dois achados de qualidade (Info) e um achado de comportamento (Warning) — este
último é uma regressão real, ainda que de baixo impacto prático, introduzida
pela mudança de desenho do `useCuradoria` (fetch condicional por flag).

## Warnings

### WR-01: `useCuradoria`/`LinhaChamadaOpcoes` podem pintar "nenhuma oportunidade" antes de a busca começar (regressão de honestidade de estado)

**Arquivos:**
`web/src/App.jsx:4140-4176` (`useCuradoria`), `web/src/App.jsx:7708-7719`
(`curadoriaAtiva`/`curadoria` em `App()`), `web/src/App.jsx:4216-4235`
(`LinhaChamadaOpcoes`), consumido também por
`web/src/opcoes/CuradoriaEstruturas.jsx:282-313` (ramos carregando/erro/vazio).

**Issue:** Antes da Fase 32, `useCuradoria()` era chamado diretamente dentro
de `CarteiraScreen` e nascia com `carregando: useState(true)` — a primeira
pintura da tela já mostrava "Varrendo sua carteira…", nunca "nenhuma
oportunidade". A partir desta fase, o hook subiu para `App()` atrás de uma
flag monotônica (`curadoriaAtiva`, linha 7711) que é ligada por um
`useEffect` separado (linha 7712-7715) quando o usuário visita Posições ou
Opções, e o próprio `useCuradoria` agora nasce com
`carregando: useState(false)` (linha 4145) e só passa a `true` dentro do seu
PRÓPRIO efeito (guardado por `if (!ativo) return;`, linha 4163), que só roda
depois que `ativo` virar `true`.

Isso cria uma cadeia de pelo menos dois saltos de efeito
(`App()` seta `curadoriaAtiva` → re-render → `useCuradoria`'s efeito nota
`ativo` mudou → seta `carregando=true`) em vez do valor já nascer certo. Na
PRIMEIRA visita da sessão a Posições ou Opções, há uma ou mais renderizações
— e, como `useEffect` roda depois do paint do browser, potencialmente uma ou
mais pinturas reais de tela — em que `curadoria` já existe mas ainda tem
`top: [], carregando: false, erro: false`. Nesse estado,
`LinhaChamadaOpcoes` (ramo `top.length === 0` → `linhaChamadaOpcoesVazia`,
"Nenhuma oportunidade de opções agora") e `CuradoriaEstruturas` (ramo
`top.length === 0 && !carregando && !erro` → `cp.curadoriaVazio`, "Nenhuma
estrutura elegível…") afirmam um resultado negativo antes de a varredura
sequer ter começado — exatamente o tipo de "estado que ninguém mediu ainda
apresentado como fato" que o princípio 4 do CLAUDE.md proíbe para dados de
mercado, aplicado aqui ao dado derivado da varredura de opções.

Diferente do hook irmão `useOpcoesPropostas` (que também nasce com
`carregando: false`, mas seta `true` dentro do MESMO efeito de montagem,
sem depender de uma flag de outro componente subir primeiro), aqui o atraso
é de dois níveis porque a flag mora em `App()` e o fetch mora no hook — a
prova de "sem flash" que valia antes da Fase 32 (carregando nasce `true`)
foi trocada por uma prova de "eventualmente consistente", sem garantia de
que a primeira pintura já reflita o estado real.

**Impacto real:** BAIXO — a janela é de poucos ciclos de render (tipicamente
sub-frame a poucos frames), acontece no máximo UMA vez por sessão (a flag é
monotônica: depois de ligada, nunca mais desliga), e autocorrige sozinha sem
interação do usuário. Não é visível em todo re-render, só na primeira vez
que `curadoriaAtiva` liga. Mas é uma regressão de um invariante que existia
antes desta fase (zero chance de mentira de estado) para um invariante mais
fraco, sem teste que cubra o caso (guardiões estáticos de string não pegam
timing de render).

**Fix sugerido (o que resolve de fato):** `useCuradoria` é instanciado UMA
vez, dentro de `App()` — `App()` monta uma vez só na vida da sessão. Por
isso, inicializar `carregando` com `useState(!!ativo)` seria um NO-OP na
prática: esse inicializador só roda no mount de `App()`, quando
`curadoriaAtiva` ainda é sempre `false` (linha 7711) — a regressão descrita
acima persistiria idêntica. O que precisa mudar é a própria cadeia de dois
saltos de efeito. Duas mudanças, aplicadas JUNTAS, fecham a janela:

1. Eliminar o `App()`-level effect (linhas 7712-7715) e computar a flag de
   ativação de forma SÍNCRONA durante o render, via ref mutado no corpo do
   componente (padrão de "latch" fora de efeito):
   ```js
   // web/src/App.jsx, em App()
   const curadoriaAtivaRef = useRef(false);
   if (!curadoriaAtivaRef.current && (tab === "opcoes" || (tab === "carteira" && carteiraView === "main"))) {
     curadoriaAtivaRef.current = true;
   }
   const curadoria = useCuradoria(curadoriaAtivaRef.current);
   ```
   Isso faz `ativo` chegar `true` em `useCuradoria` no MESMO render em que
   `CarteiraScreen`/`OpcoesScreen` montam pela primeira vez — mas sozinho
   ainda não basta, porque o `useEffect` interno de `useCuradoria` (linha
   4157 em diante) só roda DEPOIS do commit desse render.
2. Trocar o `useEffect` que seta `carregando(true)`/dispara a busca dentro
   de `useCuradoria` (linhas 4157-4176) por `useLayoutEffect` — que roda de
   forma síncrona, ANTES do browser pintar a tela, ao contrário de
   `useEffect` (que roda depois do paint, por desenho). Combinado com o
   item 1, isso impede qualquer pixel do estado "vazio" de chegar a ser
   pintado: `carregando` já é `true` antes do primeiro paint em que o bloco
   aparece.

Os dois pontos são necessários JUNTOS; qualquer um isolado (inclusive o
`useState(!!ativo)` cogitado acima como primeira ideia) deixa a janela
aberta.

## Info

### IN-01: Imports mortos deixados em `App.jsx` após a extração de `CuradoriaEstruturas`

**Arquivo:** `web/src/App.jsx:24-25`

**Issue:**
```js
import PayoffChart from "./opcoes/PayoffChart.jsx";
import { estruturaParaPayoff } from "./opcoes/estruturaParaPayoff.js";
```
Confirmado por busca no arquivo inteiro: cada identificador aparece
exatamente 1 vez — a própria linha de import, sem nenhum uso (`<PayoffChart`
ou `estruturaParaPayoff(`) em nenhum outro ponto de `App.jsx`. Esses dois
imports serviam exclusivamente `CuradoriaEstruturas`, que a Fase 32 (32-02)
moveu para `web/src/opcoes/CuradoriaEstruturas.jsx` — módulo que já importa
os dois diretamente. O comentário no topo do diff de `App.jsx` (linhas
17-19) documenta a extração de outros três imports (`PropostaLastreada`,
`FonteDoDadoProposta`, `ChipDaProposta`, `useAceiteLastreado`) mas não
menciona estes dois, que ficaram órfãos. `npx vite build`/o guardião de
paridade não pegam isso porque não há lint de import não usado no pipeline
de validação do repositório.

**Fix:** remover as duas linhas de `web/src/App.jsx:24-25`.

### IN-02: Variável `item` sombreada dentro de `CuradoriaEstruturas.jsx`

**Arquivo:** `web/src/opcoes/CuradoriaEstruturas.jsx:86,156`

**Issue:**
```js
const item = top.find((c) => (c.idCandidato || c.contractSymbol) === abertoId) || null;  // linha 86
...
{top.map((item) => (                                                                      // linha 156
```
O parâmetro do `.map` reusa o nome `item` já declarado no escopo do
componente para o candidato ABERTO (usado no painel de confirmação inline
mais abaixo). Não é um bug funcional hoje — o `item` de dentro do `.map` é
léxico e local ao callback — mas é um padrão de sombreamento que convida erro
em edição futura (ex.: alguém tentando ler o `item` "aberto" de dentro do
`.map` por engano, ou um linter configurado com `no-shadow` reprovando o
arquivo inteiro). Herdado verbatim do `App.jsx` anterior à extração (não é
uma regressão desta fase), mas o próprio ato de extrair para um módulo
dedicado — menor, mais fácil de ler isoladamente — é o momento natural para
corrigir, e não foi feito (a task era extração verbatim por desenho, então
isso é esperado, não uma falha do plano).

**Fix:** renomear o parâmetro do `.map` para algo como `cand` ou `c`:
```js
{top.map((cand) => (
  <button key={cand.idCandidato || cand.contractSymbol} ... onClick={() => setAbertoId((atual) => (atual === (cand.idCandidato || cand.contractSymbol) ? null : (cand.idCandidato || cand.contractSymbol)))}>
    ...{cand.manchete}...
  </button>
))}
```

---

_Reviewed: 2026-09-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
