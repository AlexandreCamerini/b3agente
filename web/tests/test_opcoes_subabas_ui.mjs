// Fase 28, plano 28-02 (2026-09-13) — guardião das DUAS SUB-ABAS da aba
// Opções ("Setups" / "Operar") introduzidas neste plano.
//
// Cada item abaixo nomeia o defeito que ele reprova. Nenhum é decorativo:
//
//  1. **`OpcoesScreen.jsx` importando `App.jsx`, ou `PropostaLastreada.jsx`
//     importando `OpcoesScreen.jsx`** — o invariante de DUAS VIAS da Emenda 3
//     ao ADR-027 (28-01): o módulo compartilhado nunca pode fechar o ciclo
//     por nenhum dos dois lados.
//  2. **`store.mcp*` dentro de `SubAbaOperar`** — cota do MCP gasta ao abrir
//     a sub-aba ou trocar de ativo, o que o ADR-027 §3.3 proíbe
//     explicitamente ("custo de MCP só em clique explícito").
//  3. **`store.optionsGate(`/`store.optionsProposta(` duplicados** em
//     `OpcoesScreen.jsx` — uma segunda busca da mesma coisa diverge da
//     primeira na próxima correção.
//  4. **`store.optionsProposta` chamado sem a guarda de `gate`/`liquida`** —
//     pediria proposta sobre ativo sem cadeia líquida, o que o servidor
//     recusaria, mas gastando o disparo do efeito à toa.
//  5. **Manchete recomposta dentro de `SubAbaOperar`** — o guardrail CVM
//     (CLAUDE.md princípio 5) exige que só o motor determinístico decida a
//     manchete; `SubAbaOperar` tem que delegar a `PropostaLastreada`, nunca
//     renderizar `manchete` com as próprias mãos.
//  6. **Segunda implementação do caminho de aceite** — `window.confirm`
//     próprio ou chamada direta a `A.abrirLastreada`/`A.abrirCollar`/
//     `A.fecharLastreada` dentro de `SubAbaOperar` divergiria do hook único
//     `useAceiteLastreado` (28-01) na próxima mudança de regra de negócio.
//  7. **Modo derivado de outro lugar que não `ctx.operador`** — fonte única
//     de appMode (FIX-C21); o mesmo precedente de
//     `test_fase5_appmode_fonte_unica.mjs`.
//  8. **`SubAbaOperar` iterando `watchlist`** — o universo desta aba é a
//     CARTEIRA (Fase 27, D3): lista de interesse não é lastro.
//  9. **`cp.X` referenciada em `SubAbaOperar` sem existir nos DOIS ramos de
//     `COPY`** — quebraria em produção só no modo que não foi testado à mão.
//  10. **Alternador de sub-aba sem `aria-pressed` ou sem `minHeight: "44px"`
//      nos dois botões** — perde a afordância de estado e o alvo tátil
//      mínimo que o resto do app usa.
//  11. **Qualquer bloco da Fase 27 sumindo da tela** (`cabecalho`,
//      `blocoVigias`, `seletor`, `LastroDoAtivo`, `LeituraInterna`,
//      `blocoLeituraDoServico`) — regressão silenciosa no rewrap do JSX que
//      criou a sub-aba nova.
//
// Roda sem build: `node web/tests/test_opcoes_subabas_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const dirSrc = join(here, "..", "src");

const brutos = {
  "OpcoesScreen.jsx": readFileSync(join(dirOpcoes, "OpcoesScreen.jsx"), "utf8"),
  "PropostaLastreada.jsx": readFileSync(join(dirOpcoes, "PropostaLastreada.jsx"), "utf8"),
  "App.jsx": readFileSync(join(dirSrc, "App.jsx"), "utf8"),
};

// Sem comentários: eles citam os mesmos termos ao explicar as decisões, e
// contá-los faria o guardião se auto-invalidar (mesmo padrão de
// test_opcoes_mcp_aba_ui.mjs).
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const fontes = Object.fromEntries(
  Object.entries(brutos).map(([k, v]) => [k, semComentario(v)]));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const tela = fontes["OpcoesScreen.jsx"];
const propostaModulo = fontes["PropostaLastreada.jsx"];

// ---- fatia de SubAbaOperar, por marcador de linha (mais estável que casar
// chaves — mesmo padrão de test_fase22_componentes_compartilhados.mjs) ------
const idxInicio = tela.indexOf("function SubAbaOperar");
let subAba = "";
if (idxInicio >= 0) {
  const idxFim = tela.indexOf("\nfunction ", idxInicio + 1);
  subAba = idxFim > idxInicio ? tela.slice(idxInicio, idxFim) : tela.slice(idxInicio);
}
// Asserção de "parse mudo": um recorte vazio faria toda negativa abaixo
// passar de graça, sem medir nada de verdade.
ok("a fatia de `SubAbaOperar` foi localizada e tem corpo (>300 caracteres)",
   idxInicio >= 0 && subAba.length > 300);

// ---- 1) invariante de duas vias (Emenda 3 ao ADR-027) -----------------------
ok("OpcoesScreen.jsx não importa App.jsx",
   !/from\s+["'][^"']*App\.jsx["']/.test(fontes["OpcoesScreen.jsx"]));
ok("PropostaLastreada.jsx não importa OpcoesScreen.jsx",
   !/from\s+["'][^"']*OpcoesScreen\.jsx["']/.test(propostaModulo));

// ---- 2) custo zero de MCP em SubAbaOperar -----------------------------------
ok("`SubAbaOperar` não chama nenhum método `store.mcp*` (ADR-027 §3.3)",
   !/store\.mcp/.test(subAba));

// ---- 3) sem busca duplicada de gate/proposta --------------------------------
const nGate = (tela.match(/store\.optionsGate\(/g) || []).length;
const nProposta = (tela.match(/store\.optionsProposta\(/g) || []).length;
ok("`store.optionsGate(` aparece exatamente 1× em OpcoesScreen.jsx", nGate === 1);
ok("`store.optionsProposta(` aparece exatamente 1× em OpcoesScreen.jsx", nProposta === 1);

// ---- 4) optionsProposta guardado por gate/liquida ---------------------------
// Precisão deliberada: olhar só o TEXTO ENTRE `setProp(null)` e a chamada —
// não o componente inteiro, senão a dependência do useEffect
// (`[store, ticker, gate && gate.liquida]`, que sempre existe) faria esta
// asserção passar mesmo com o `if` de guarda removido (achado por injeção de
// defeito real durante a escrita deste guardião — ver SUMMARY).
const idxSetProp = subAba.indexOf("setProp(null);");
const idxCallProposta = subAba.indexOf("store.optionsProposta(", idxSetProp >= 0 ? idxSetProp : 0);
const guardaProposta = (idxSetProp >= 0 && idxCallProposta > idxSetProp)
  ? subAba.slice(idxSetProp, idxCallProposta) : "";
ok("a chamada de `store.optionsProposta` está guardada por um `if`/`return` que testa `gate`/`liquida` ANTES da chamada",
   /if\s*\([^)]*!\(gate && gate\.liquida\)[^)]*\)\s*return/.test(guardaProposta));

// ---- 5) manchete só via PropostaLastreada (guardrail CVM) -------------------
ok("`SubAbaOperar` não renderiza `manchete` própria (delega a PropostaLastreada)",
   !/\{[^}]*\bmanchete\b[^}]*\}/.test(subAba) && !/\.manchete/.test(subAba));
ok("`SubAbaOperar` usa `<PropostaLastreada` (não reimplementa o card)",
   /<PropostaLastreada/.test(subAba));

// ---- 6) caminho de aceite único (useAceiteLastreado) ------------------------
ok("`SubAbaOperar` não declara `window.confirm` próprio",
   !/window\.confirm/.test(subAba));
ok("`SubAbaOperar` não chama `A.abrirLastreada(`/`A.abrirCollar(`/`A.fecharLastreada(` direto",
   !/A\.(abrirLastreada|abrirCollar|fecharLastreada)\(/.test(subAba));
ok("`SubAbaOperar` usa o hook único `useAceiteLastreado(`",
   /useAceiteLastreado\(/.test(subAba));

// ---- 7) fonte única de appMode -----------------------------------------------
ok("`SubAbaOperar` deriva o modo só de `ctx.operador`",
   /ctx && ctx\.operador/.test(subAba) && !/appMode/.test(subAba) && !/data\.config/.test(subAba));

// ---- 8) universo = carteira, nunca watchlist --------------------------------
ok("`SubAbaOperar` não referencia `watchlist`",
   !/watchlist/i.test(subAba));

// ---- 9) toda cp.X referenciada em SubAbaOperar existe nos DOIS ramos --------
const chavesCp = Array.from(new Set(
  Array.from(subAba.matchAll(/cp\.([A-Za-z0-9_]+)/g)).map((m) => m[1])
));
ok("achou pelo menos uma chave `cp.X` em SubAbaOperar (sanidade da asserção seguinte)",
   chavesCp.length > 0);
const chavesFaltando = chavesCp.filter((k) => !(k in COPY.estudo) || !(k in COPY.operador));
ok("toda `cp.X` referenciada em SubAbaOperar existe em COPY.estudo e COPY.operador"
   + (chavesFaltando.length ? " (faltando: " + chavesFaltando.join(", ") + ")" : ""),
   chavesFaltando.length === 0);

// ---- 10) alternador com aria-pressed e alvo tátil mínimo --------------------
const idxSubabas = tela.indexOf("const subabas = (");
const blocoSubabas = idxSubabas >= 0 ? tela.slice(idxSubabas, idxSubabas + 1200) : "";
ok("o alternador de sub-aba existe (`const subabas = (`)", idxSubabas >= 0);
ok("o alternador usa `aria-pressed`", /aria-pressed=/.test(blocoSubabas));
ok("o alternador usa `minHeight: \"44px\"` (alvo tátil mínimo)", /minHeight:\s*"44px"/.test(blocoSubabas));

// ---- 11) nada da Fase 27 desapareceu -----------------------------------------
for (const nome of ["cabecalho", "blocoVigias", "seletor", "LastroDoAtivo", "LeituraInterna", "blocoLeituraDoServico"]) {
  ok(`\`${nome}\` continua referenciado em OpcoesScreen.jsx`, tela.includes(nome));
}

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
