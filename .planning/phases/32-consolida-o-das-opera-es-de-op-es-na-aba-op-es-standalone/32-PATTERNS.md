# Phase 32: Consolidação das operações de opções na aba Opções - Pattern Map

**Mapped:** 2026-09-15
**Files analyzed:** 7 (4 componentes + 1 hook a mover, `copy.js`, mais os call sites/guardiões que precisam de reescrita)
**Analogs found:** 7 / 7 — todos os analogs são internos ao próprio par `App.jsx` ↔ `web/src/opcoes/*`, porque esta é uma fase de extração de código já existente (ADR-027 Emenda 3 é o precedente literal), não de construção de UI nova.

> Nota de escopo: esta fase não cria componente/role novo (nenhum controller,
> service, model). Todo "role" abaixo é `component` (React, puro por prop) ou
> `hook`, e todo "data flow" é `transform` (render de prop) ou
> `request-response` (fetch client-side best-effort). O padrão a copiar não é
> "como fazer CRUD", é "como mover JSX de `App.jsx` para um módulo de
> `web/src/opcoes/` sem quebrar o isolamento de import e sem quebrar os
> guardiões estáticos que travam a localização por `indexOf`".

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/opcoes/OportunidadesOpcoes.jsx` (novo módulo, ou inline em `OpcoesScreen.jsx`) | component | transform (puro por prop) | `web/src/opcoes/PropostaLastreada.jsx` (extração Fase 28, ADR-027 Emenda 3) | exact — mesmo padrão de extração de `App.jsx` p/ módulo de duas vias |
| `web/src/opcoes/CuradoriaEstruturas.jsx` (novo módulo) | component | transform (puro por prop) + ação (`onExecutar`) | `web/src/opcoes/PropostaLastreada.jsx` | exact |
| `web/src/opcoes/PropostaDaPosicao.jsx` + `CandidatoOpcao.jsx` (novos módulos, ou dobrados dentro de `SubAbaOperar`) | component | transform (puro por prop) | `web/src/opcoes/PropostaLastreada.jsx` | exact |
| `useCuradoria()` (hook — sobe de tier, de `CarteiraScreen` para `App()`/`ctx`) | hook | request-response (fetch client, best-effort, gatilho condicional) | `useOpcoesPropostas()` (`App.jsx:4632-4678`, mesmo arquivo, já resolve o problema irmão — fetch por posição, dependência primitiva, best-effort) | exact — é o padrão-irmão mais próximo dentro do mesmo arquivo |
| `SubAbaOperar` (modificado: ganha `multi`/`CandidatoOpcao`) | component | transform + request-response (fetch próprio) | `PropostaDaPosicao` (`App.jsx:4449-4503`, a lógica `multi = candidatos.length > 1` que precisa ser portada) | exact — é literalmente a mesma fórmula, mesmo arquivo de origem |
| Linha de chamada em `CarteiraScreen` (novo trecho JSX) | component | transform | Toggle de `PropostaDaPosicao` (`App.jsx:4480-4483`) — mesmo padrão visual (linha discreta, `borderBottom`, sem card) | exact — UI-SPEC já cita este exato analog |
| `web/src/copy.js` (chaves novas: `linhaChamadaOpcoes*`, `duasLeiturasIntro`, `curadoriaErroBusca`, `tiraOpcoesSubtitulo`, reescrita de `curadoriaSubtitulo`) | config (vocabulário) | transform (par estático Estudo/Operador) | `web/src/copy.js:585-594` / `1140-1148` (par `tiraOpcoesTitulo`/`linhaPropostaNaPosicao` já simétrico nos dois blocos) | exact |
| Guardiões `web/tests/test_curadoria_ui.mjs`, `test_carteira_opcoes_tira.mjs`, `test_opcoes_multi_candidato_ui.mjs` (reescrita) | test | transform (leitura estática de source) | `web/tests/test_opcoes_subabas_ui.mjs` (já testa multi-arquivo com `readFileSync` de dois diretórios) | role-match — é o guardião mais recente que já lida com "componente vive em `OpcoesScreen.jsx`, não em `App.jsx`" |

## Pattern Assignments

### Extração de componente de `App.jsx` para módulo de `web/src/opcoes/*`

**Analog:** `web/src/opcoes/PropostaLastreada.jsx` (linhas 1-40) — este é o
precedente EXATO desta fase: um componente que morava dentro de `App.jsx` e
foi extraído para um módulo terceiro porque nem `App.jsx` pode importar
`OpcoesScreen.jsx` nem o inverso (ciclo). Os quatro componentes desta fase
(`OportunidadesOpcoes`, `CuradoriaEstruturas`, `PropostaDaPosicao`,
`CandidatoOpcao`) e o mapa `ROTULO_TIPO_CURADORIA` devem seguir o MESMO
molde.

**Cabeçalho do módulo (comentário obrigatório, copiar a estrutura, adaptar o conteúdo):**
```javascript
/**
 * PropostaLastreada.jsx — Fase 28 (28-01), extração de App.jsx.
 *
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3 — isolamento do núcleo) e `App.jsx` não pode
 * importar `OpcoesScreen.jsx` (seria ciclo). A fiação correta é de UMA VIA
 * para os dois lados — um módulo terceiro que ambos importam, nunca um
 * importando o outro. Isto é a Emenda 3 ao ADR-027 ...
 */
import { useState } from "react";
```
(`web/src/opcoes/PropostaLastreada.jsx:1-22`)

**Tokens de tema replicados sem import de `App.jsx` (copiar literalmente, ajustar a lista de chaves usadas):**
```javascript
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "bgCard", "borderSubtle", "borderFaint",
  "textPrimary", "textSecondary", "textMuted", "textFaint", "accent",
  "accentTint", "accentTint10", "positive", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```
(`web/src/opcoes/PropostaLastreada.jsx:33-37`)

**Aplicação a esta fase:** `OportunidadesOpcoes`/`CuradoriaEstruturas`/
`PropostaDaPosicao`/`CandidatoOpcao` usam `T`, `MONO`, `money`/`price`,
`carouselTrackStyle`/`carouselItemStyle`, `PayoffChart` — a pesquisa já
confirmou (32-RESEARCH.md, "Mapa exato do que se move") que nenhum deles
importa nada privado de `App.jsx` além desses helpers genéricos, que já têm
espelho em `OpcoesScreen.jsx`/`PropostaLastreada.jsx`. Extrair `TOKENS`
adicionais (`positive`, `negative` já estão na lista acima) é o único ajuste
provável de import.

**Regra de guarda que o teste de isolamento trava (não violar):**
```javascript
ok("OpcoesScreen.jsx não importa App.jsx",
   !/from\s+["'][^"']*App\.jsx["']/.test(fontes["OpcoesScreen.jsx"]));
ok("PropostaLastreada.jsx não importa OpcoesScreen.jsx",
   ...);
```
(`web/tests/test_opcoes_subabas_ui.mjs:87-89`)

---

### Como um bloco cross-carteira é montado no topo da aba, fora da cascata por ticker (precedente Fase 27 "vigias" — o molde para Bloco A/B)

**Analog:** `blocoVigias` (`web/src/opcoes/OpcoesScreen.jsx:542-595`) — é o
precedente literal que D-04/D-07 mandam seguir para posicionar
`OportunidadesOpcoes`/`CuradoriaEstruturas` no topo da sub-aba Setups. Padrão
a copiar: o bloco é montado como uma `const` de JSX **dentro do corpo de
`OpcoesScreen`**, antes do `return`, e depois só referenciado por nome no
JSX final — não é um componente separado importado, é uma variável local com
sua própria cascata carregando→erro→vazio→dados:

```jsx
const blocoVigias = (
  <div>
    <Kicker>{cp.opcoesVigiasTitulo || "SEUS VIGIAS"}</Kicker>
    {/* carregando → erro → vazio com motivo → dados, a mesma cascata do
        resto da tela: lista vazia pintada durante a consulta afirmaria
        "você não tem vigia" sem ninguém ter medido. */}
    {vigias.carregando ? (
      <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
    ) : vigias.erro ? (
      <ErroDoMcp erro={vigias.erro} cp={cp} />
    ) : listaDeVigias.length === 0 ? (
      <Aviso>{cp.opcoesVigiasVazio || "Nenhum vigia gravado nesta conta ainda."}</Aviso>
    ) : (
      <div style={{ display: "grid", gap: "10px" }}>
        {listaDeVigias.map((v, i) => (
          <CartaoDeVigia key={...} vigia={v} ... onIr={irParaVigia} cp={cp} />
        ))}
      </div>
    )}
    ...
  </div>
);
```
(`web/src/opcoes/OpcoesScreen.jsx:542-595`)

**Onde é efetivamente colocado na árvore — fora da cascata por ticker, sempre renderizado, com ou sem ativo escolhido:**
```jsx
{subaba !== "setups" ? (
  <SubAbaOperar ... />
) : (
<>
{cabecalho}
{/* Fase 27 (D4: "vigias antes da carteira"). SEMPRE renderizado, com ou
    sem ativo escolhido — é o que faz a aba abrir com conteúdo em vez de
    abrir vazia, e de graça. */}
{blocoVigias}
{carteira.length > 0 ? seletor : null}
...
```
(`web/src/opcoes/OpcoesScreen.jsx:694-711`)

**Aplicação a esta fase:** Bloco A (`OportunidadesOpcoes`) e Bloco B
(`CuradoriaEstruturas`) seguem o MESMO molde — `const blocoOportunidades = (...)`
e `const blocoCuradoria = (...)` montados no corpo de `OpcoesScreen` (ou
importados como componente do módulo novo e invocados aqui), referenciados
antes de `{blocoVigias}` no ramo `subaba === "setups"`, dentro do mesmo `<>`
— nunca acima do `{subabas}` (isso seria a Leitura B, rejeitada pelo UI-SPEC,
Open Question #1 resolvida). A frase-ponte (D-05) entra como uma terceira
`const` do mesmo tipo, sempre no DOM, sem toggle — reforça o mesmo padrão
"variável JSX local, sem estado de colapso".

---

### `useCuradoria()` — hook que sobe de tier (D-03, Open Question #2)

**Analog primário:** `useOpcoesPropostas()` (`App.jsx:4632-4678`) — já resolve,
no mesmo arquivo, o problema-irmão de "buscar dado por posição, best-effort,
com dependência PRIMITIVA (não array/objeto) para não recriar o efeito a
cada render":

```javascript
function useOpcoesPropostas(tickers) {
  const [propostas, setPropostas] = useState({});
  const [carregando, setCarregando] = useState(false);
  // Chave PRIMITIVA (string) como dependência do efeito — um array de
  // tickers recriaria o efeito a cada render de CarteiraScreen, disparando
  // N requisições por render (mesma disciplina do `opGate && opGate.liquida`
  // primitivo em AtivoCard).
  const chave = (tickers || []).join(",");

  useEffect(() => {
    let alive = true;
    ...
    return () => { alive = false; };
  }, [chave]);

  return { propostas, carregando };
}
```
(`App.jsx:4632-4678`)

**Analog do próprio `useCuradoria` hoje** (`App.jsx:4687-4736`) — mantém a
mesma forma (`aliveRef`, `.then/.catch/.finally`, `best-effort`), mas dispara
com `useEffect(..., [])`, ou seja, dispara 1x por MOUNT do componente que o
chama. **O ajuste que esta fase exige (D-03 + Common Pitfall #2 do RESEARCH.md)
é o gatilho, não a forma do fetch**: em vez de `[]` puro no componente `App()`
(o que dispararia em todo boot), condicionar o efeito a uma flag do tipo
"visitou Posições ou Opções nesta sessão" — o hook em si (estados
`top`/`meta`/`carregando`/`erro`/`narrativa`, chamada
`store.opcoesCuradoria()`, `.finally`) não muda de forma, só de LOCAL (sobe
para onde `ctx` nasce, `App.jsx:9434+`) e de TRIGGER.

```javascript
useEffect(() => {
  aliveRef.current = true;
  setCarregando(true);
  // best-effort, igual useOpcoesPropostas acima: falha de rede só deixa
  // o bloco sem item, nunca quebra a tela.
  store.opcoesCuradoria()
    .then((r) => { ... })
    .catch(() => { if (aliveRef.current) setErro(true); })
    .finally(() => { if (aliveRef.current) setCarregando(false); });
  return () => { aliveRef.current = false; };
}, []); // <- ESTA dependência é o que o plano precisa decidir substituir
```
(`App.jsx:4699-4713`)

**Onde `ctx` já nasce compartilhado (o destino recomendado para o hook subir):**
`App.jsx:9434` em diante — `ctx` é construído 1x e passado idêntico a
`<CarteiraScreen ctx={ctx}/>` e `<OpcoesScreen ctx={ctx}/>` (`App.jsx:9775-9780`).
Isto é o "Don't Hand-Roll" do RESEARCH.md: não criar um segundo fetch
independente em `OpcoesScreen` — usar o mesmo padrão de estado único subido a
`App()` que `ctx` já demonstra para dado compartilhado entre as duas telas.

---

### `SubAbaOperar` ganhando suporte multi-candidato (D-04, Open Question #3)

**Analog exato — a lógica a portar, verbatim, de `PropostaDaPosicao`:**
```javascript
// Fase 19 (Plano 03, MULTI-02): candidatos é SEMPRE array (default [] no
// servidor); quando há mais de um, o ramo abaixo mostra os N lado a lado —
// um candidato só continua caindo no card de hoje (nenhuma regressão
// visual/funcional para posições com um candidato só).
const candidatos = Array.isArray(r.candidatos) ? r.candidatos : [];
const multi = candidatos.length > 1;
```
(`App.jsx:4464-4469`)

```jsx
{aberto && (
  multi ? (
    <>
      <div style={carouselTrackStyle({ marginTop: "11px", gap: "10px", scrollbarWidth: "none", paddingBottom: "2px" })}>
        {candidatos.map((c) => (
          <CandidatoOpcao key={c.tipo + "-" + (c.contractSymbol || "collar")} p={c} r={r} cp={cp} operador={operador} busy={busy} onAceitar={aceitarCandidato} onVerbeteLiquidez={(dados) => A.abrirVerbete("liquidez-opcao", dados)} />
        ))}
      </div>
      <FonteDoDadoProposta r={r} cp={cp} />
    </>
  ) : (
    <PropostaLastreada r={r} operador={operador} cp={cp} busy={busy} onAbrir={() => aceitarCandidato(r.proposta)} onFechar={() => fecharLastreada(r)} posAberta={posAberta} onVerbeteLiquidez={(dados) => A.abrirVerbete("liquidez-opcao", dados)} />
  )
)}
```
(`App.jsx:4484-4500`)

**Ponto de inserção em `SubAbaOperar`** — o ramo único hoje (a substituir por
condicional `multi`):
```javascript
) : (
  <PropostaLastreada
    r={prop}
    operador={operador}
    cp={cp}
    busy={busy}
    onAbrir={() => aceitarCandidato(prop && prop.proposta)}
    onFechar={() => fecharLastreada(prop)}
    posAberta={posAberta}
    onVerbeteLiquidez={(dados) => { if (A && A.abrirVerbete) A.abrirVerbete("liquidez-opcao", dados); }}
  />
)}
```
(`web/src/opcoes/OpcoesScreen.jsx:1379-1388`) — `prop.candidatos` já chega da
rota (`server/app/main.py:3253`, confirmado pela pesquisa), só falta o
`multi = candidatos.length > 1` + o `.map` acima.

**Duas implementações de `posAberta`/`myOptionPositions` a reconciliar — manter a de `SubAbaOperar` (já adaptada a "uma posição por vez"):**
```javascript
// SubAbaOperar (manter esta):
const myOptionPositions = ((ctx && ctx.data && ctx.data.optionPositions) || []).filter((p) => p.underlying === ticker);
const posAberta = (prop && prop.proposta)
  ? myOptionPositions.find((p) => p.id === prop.proposta.contractSymbol) || null
  : null;
```
(`web/src/opcoes/OpcoesScreen.jsx:1342-1345`, comparar com o duplicado em `App.jsx:4473-4476` — apagar este último com nota ao mover `PropostaDaPosicao`)

---

### Linha de chamada em `CarteiraScreen` (D-01/D-02/D-03)

**Analog de estilo — toggle discreto (sem card, sem borda ao redor, só `borderBottom`):**
```jsx
<button type="button" onClick={onToggle} aria-expanded={aberto} style={{ display: "flex", width: "100%", alignItems: "center", justifyContent: "space-between", padding: "5px 0", background: "transparent", border: "none", color: T.textMuted, fontSize: "11.5px", fontWeight: 700, cursor: "pointer" }}>
  <span style={{ display: "flex", alignItems: "center", gap: "7px" }}><span style={{ color: T.accent }}>⚡</span> {cp.linhaPropostaNaPosicao}</span>
  <span style={{ color: T.textFaint }}>{aberto ? "▴" : "▾"}</span>
</button>
```
(`App.jsx:4480-4483`) — o UI-SPEC (`32-UI-SPEC.md:315-335`) já deriva a linha
de chamada literalmente deste padrão, trocando `onToggle`/`▾` por
`onClick={() => navigate("opcoes")}`/`→` e adicionando `borderBottom`.

**Analog de navegação — `navigate(t)` já existe, zero mecanismo novo:**
```javascript
const [tab, setTab] = useState("evolucao");
...
const navigate = (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); };
```
(`App.jsx:8228, 8231`) — usar `navigate("opcoes")`.

**Analog de call site a substituir (os 4 blocos saem daqui):**
```jsx
{data.positions.length > 0 && (
  <>
    <OportunidadesOpcoes propostas={opcoesPorTicker} carregando={opcoesCarregando} positions={data.positions} cp={cp} onAbrir={abrirOpcoesDe} />
    <CuradoriaEstruturas
      top={curadoriaTop} meta={curadoriaMeta} carregando={curadoriaCarregando} erro={curadoriaErro}
      narrativa={curadoriaNarrativa} narrando={curadoriaNarrando} erroNarrativa={curadoriaErroNarrativa}
      onNarrar={() => narrarCuradoria(data.config)} cp={cp} onAbrir={abrirOpcoesDe}
      onExecutar={(cand, o) => A.executarCandidatoCurado(cand, o)} operador={operador} palette={ctx.palette}
    />
  </>
)}
```
(`App.jsx:4850-4872`) e
```jsx
<PropostaDaPosicao
  t={p.t} r={(opcoesPorTicker[p.t] || {}).proposta} cp={cp} operador={operador} A={A} data={data}
  aberto={opcoesFor === p.t} onToggle={() => setOpcoesFor(opcoesFor === p.t ? null : p.t)}
/>
```
(`App.jsx:5008-5011`, dentro do `.map` de posições) — este segundo call site
some inteiro (por-posição), não vira linha de chamada.

**Fonte de contagem (D-03) — usar exatamente `useCuradoria().top.length`, nunca recalcular:**
```javascript
} = useCuradoria();
```
(`App.jsx:4762`) — a instância movida/lifted expõe `top`; `n = top.length`.

---

### Cadeia de execução do collar curado (regressão mais provável — NÃO tocar)

**Analog — wiring de `ctx.A`, idêntico nas duas telas, não precisa mudar:**
```javascript
onExecutar={(cand, o) => A.executarCandidatoCurado(cand, o)}
```
(`App.jsx:4867`, chamado de `CarteiraScreen`; `ctx.A` é o mesmo objeto que
`OpcoesScreen` recebe via `ctx={ctx}` — trocar para
`onExecutar={(cand,o)=>ctx.A.executarCandidatoCurado(cand,o)}` é a única
mudança de wiring necessária. `executarCandidato.js`, `store.js`/
`persistence.js`, a rota `POST /api/options/curadoria/abrir-collar` — tudo
isso continua intocado.)

---

### Navegação "ver posição" dentro do painel curado (Pitfall 4 — trocar o destino)

**Analog do padrão atual (scroll-to-id, só existe em `CarteiraScreen`):**
```javascript
const abrirOpcoesDe = (t) => {
  setOpcoesFor(t);
  setTimeout(() => {
    const el = document.getElementById("posicao-" + t);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 60);
};
```
(`App.jsx:4769-4776`)

**Substituto dentro de `OpcoesScreen` (já prescrito pelo UI-SPEC, usar literalmente):**
```javascript
onAbrir={(t) => { escolherTicker(t); setSubaba("operar"); }}
```
(`32-UI-SPEC.md:461`, casando com `escolherTicker`/`setSubaba` já definidos em
`web/src/opcoes/OpcoesScreen.jsx:309, 347-350`)

---

### Vocabulário por modo (`copy.js`) — par Estudo/Operador

**Analog de par simétrico existente (copiar a estrutura para as chaves novas: `linhaChamadaOpcoes*`, `duasLeiturasIntro`, `curadoriaErroBusca`, `tiraOpcoesSubtitulo`):**
```javascript
// bloco COPY.estudo
tiraOpcoesTitulo: "OPORTUNIDADES DE OPÇÕES",
...
linhaPropostaNaPosicao: "Estrutura de opções possível nesta posição",
```
(`web/src/copy.js:585-594`)
```javascript
// bloco COPY.operador — mesma chave, texto de mesa
tiraOpcoesTitulo: "OPORTUNIDADES DE OPÇÕES",
...
linhaPropostaNaPosicao: "Estrutura de opções disponível nesta posição",
```
(`web/src/copy.js:1140-1148`)

**Regra de checklist de palavras proibidas a reaplicar às strings novas** (frase-ponte D-05, títulos do Bloco A, linha de chamada) — mesma lista já usada pelo guardião:
```
PROIBIDAS: "garantido", "lucro garantido", "sem risco", "certeza"
```
(referenciada em `web/tests/test_curadoria_ui.mjs`, ver comentário item 8, e citada em `32-UI-SPEC.md:297-302`)

## Shared Patterns

### Isolamento de import de duas vias (ADR-027 Emenda 3)
**Fonte:** `web/src/opcoes/PropostaLastreada.jsx:1-21` (comentário de cabeçalho)
**Aplicar a:** todos os 4 componentes/1 hook extraídos nesta fase.
```
"OpcoesScreen.jsx não pode importar App.jsx (ADR-027, Decisão 3) e App.jsx
não pode importar OpcoesScreen.jsx (seria ciclo). A fiação correta é de UMA
VIA para os dois lados — um módulo terceiro que ambos importam."
```
Guardião que trava isso: `web/tests/test_opcoes_subabas_ui.mjs:87-89`.

### Manchete do motor verbatim (guardrail CVM)
**Fonte:** comentário repetido em `App.jsx:4150-4153`, `4548-4551`, `4180-4185`
**Aplicar a:** `OportunidadesOpcoes`, `CuradoriaEstruturas`, `CandidatoOpcao` — em qualquer novo local.
```jsx
{/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md);
    nunca truncada com reticências: cortar reescreveria a
    afirmação do motor. */}
<div style={{ ..., color: cor, ... }}>{pr.manchete}</div>
```
Nenhuma composição de frase a partir de strike/prêmio/optionType é permitida — nem no módulo novo.

### `null` nunca vira `0.0` em cálculo de payoff por lote
**Fonte:** `App.jsx:4522-4525`
```javascript
const porLote = (v) => (typeof v === "number" ? v * (p.qtyAcoes || 0) : null);
```
**Aplicar a:** qualquer novo local que renderize `CandidatoOpcao`/payoff.
**Atenção ao mover:** `web/tests/test_opcoes_analisar_ui.mjs` (guardião irmão,
não listado nas 6 tabelas de risco do RESEARCH.md porque hoje só varre
`ARQUIVOS = ["OpcoesScreen.jsx", "useOpcoesMcp.js", "SetupChart.jsx",
"PayoffChart.jsx"]`, uma allowlist hardcoded, linha 44) trava, para esses 4
arquivos, que **nenhum arquivo de `web/src/opcoes/` multiplica indicador por
`lote`** (regex `MULT_LOTE = /\*\s*lote\b|\blote\s*\*/`, linha 93) — a
conversão para reais é fechada no backend (`_em_reais`), e uma segunda
multiplicação no front dobraria o número. `porLote` acima usa `qtyAcoes`, não
o literal `lote`, então não dispara a regex hoje — mas se `CandidatoOpcao`/
`PropostaDaPosicao` migrarem para um arquivo novo dentro de
`web/src/opcoes/`, **o `ARQUIVOS` desta allowlist não é atualizado
automaticamente**: o plano deve decidir explicitamente se o arquivo novo
entra nessa lista (recomendado, para o guardião continuar cobrindo todo o
diretório) ou se registra por que não precisa.

### Best-effort silencioso em fetch client-side de opções
**Fonte:** `useOpcoesPropostas` (`App.jsx:4658-4673`) e `useCuradoria` (`App.jsx:4704-4711`)
**Aplicar a:** qualquer novo hook ou hook movido — `.catch()` nunca propaga erro que quebre a tela; estado `erro` (quando existe) é setado, nunca lançado.

### Guardião estático por âncora de `indexOf("function X")`
**Fonte:** `web/tests/test_curadoria_ui.mjs:101-138`
```javascript
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const iOO = app.indexOf("function OportunidadesOpcoes");
const iCuradoria = app.indexOf("function CuradoriaEstruturas");
...
const fatiaCuradoria = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function CuradoriaEstruturas"),
  fonteSemComentario.indexOf("function PropostaDaPosicao"),
);
```
**Aplicar a:** toda task que move um dos 4 blocos precisa, no MESMO plano, reescrever este padrão apontando para o novo arquivo (`OpcoesScreen.jsx` ou o módulo novo em `web/src/opcoes/`), preservando as ~26 regras semanticamente — nunca deletar o arquivo de teste. Padrão de leitura multi-arquivo já pronto para copiar em `web/tests/test_opcoes_subabas_ui.mjs:43-55` (`readFileSync` de `OpcoesScreen.jsx` + `PropostaLastreada.jsx` + `App.jsx` no mesmo arquivo de teste).

### Paridade de conjunto de chaves de copy (não lista fixa)
**Fonte:** `web/tests/test_vocabulario_opcoes.mjs:1-40` (varre `OpcoesScreen.jsx` e confere que toda `cp.X` referenciada existe em `COPY.estudo`/`COPY.operador`)
**Aplicar a:** a chave nova `linhaChamadaOpcoes*` fica em `App.jsx` (CarteiraScreen), fora do escopo atual deste teste (que só varre `OpcoesScreen.jsx`) — precisa de um teste irmão ou extensão de escopo, conforme já registrado no RESEARCH.md (linha ~349).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Rastreio de `erro` em `useOpcoesPropostas` (Bloco A) | hook | request-response | Não existe hoje (best-effort silencioso desde a Fase 18) e o UI-SPEC marcou explicitamente como fora de escopo desta fase (Open Question #3 do UI-SPEC) — não inventar captura de erro nova aqui; só a exibição do `erro` de `useCuradoria` (Bloco B) está em escopo, porque já é capturado e só falta ser lido pelo componente. |
| Carimbo de frescor/pregão nos blocos cross-carteira (A e B) | component | transform | Lacuna pré-existente, promovida a TODO nomeado (`carimbo-frescor-blocos-cross-carteira.md`) pelo próprio Alex — fora de escopo por decisão registrada no UI-SPEC (Open Question #4), não por falta de analog. |

## Metadata

**Analog search scope:** `web/src/App.jsx` (linhas 4101-5064, 8228-8231,
9434-9780), `web/src/opcoes/OpcoesScreen.jsx` (linhas 273-719, 1297-1396),
`web/src/opcoes/PropostaLastreada.jsx` (linhas 1-40), `web/src/copy.js`
(linhas 580-625, 1135-1165), `web/tests/test_curadoria_ui.mjs`,
`web/tests/test_opcoes_subabas_ui.mjs`, `web/tests/test_vocabulario_opcoes.mjs`,
`web/tests/test_opcoes_analisar_ui.mjs`.
**Files scanned:** 9 arquivos de source + 4 arquivos de teste lidos
diretamente; mais 3 guardiões (`test_carteira_opcoes_tira.mjs`,
`test_opcoes_multi_candidato_ui.mjs`, `test_opcoes_collar_ui.mjs`,
`test_opcoes_proposta_ui.mjs`) já mapeados linha a linha pelo
`32-RESEARCH.md` e reaproveitados aqui sem releitura.
**Pattern extraction date:** 2026-09-15
