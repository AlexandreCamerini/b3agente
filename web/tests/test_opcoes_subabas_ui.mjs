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
//     manchete; `SubAbaOperar` tem que delegar a `PropostaLastreada` (ramo
//     único) OU `CandidatoOpcao` (ramo multi-candidato, portado na Fase 32,
//     32-04 — ver nota datada abaixo), nunca renderizar `manchete` com as
//     próprias mãos.
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
// 2026-09-15, Fase 32 (32-04): `PropostaDaPosicao` deixou de existir; o ramo
// multi-candidato que só vivia nela foi portado para `SubAbaOperar`
// (`OpcoesScreen.jsx`), e o acordeão de opções saiu de Posições (D-01/D-04).
// A regra 5 (manchete só via componente delegado) passa a aceitar
// `CandidatoOpcao` como delegação legítima, ao lado de `PropostaLastreada`.
//
// Roda sem build: `node web/tests/test_opcoes_subabas_ui.mjs`.
import { readFileSync, readdirSync } from "fs";
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

// Fase 32 (32-03, 2026-09-15): estende o invariante acima a TODOS os arquivos de
// web/src/opcoes/, inclusive os criados pelos Planos 32-02/32-03
// (OportunidadesOpcoes.jsx, CuradoriaEstruturas.jsx, CandidatoOpcao.jsx,
// useOpcoesPropostas.js) — nenhum módulo desta pasta pode importar
// App.jsx (fecharia o ciclo que a Emenda 3 do ADR-027 proíbe). Varredura
// por DIRETÓRIO, não lista fixa: um arquivo novo entra automaticamente na
// checagem, sem precisar lembrar de atualizar este guardião.
const arquivosOpcoesDir = readdirSync(dirOpcoes).filter((f) => f.endsWith(".jsx") || f.endsWith(".js"));
ok("achou pelo menos 10 arquivos em web/src/opcoes/ (sanidade da varredura por diretório)",
   arquivosOpcoesDir.length >= 10);
const comImportDeApp = arquivosOpcoesDir.filter((f) => {
  const src = readFileSync(join(dirOpcoes, f), "utf8");
  return /from\s+["'][^"']*App\.jsx["']/.test(src);
});
ok("nenhum arquivo de web/src/opcoes/ importa App.jsx"
   + (comImportDeApp.length ? " (violam: " + comImportDeApp.join(", ") + ")" : ""),
   comImportDeApp.length === 0);

// ---- 2) custo zero de MCP em SubAbaOperar -----------------------------------
ok("`SubAbaOperar` não chama nenhum método `store.mcp*` (ADR-027 §3.3)",
   !/store\.mcp/.test(subAba));

// ---- 3) sem busca duplicada de gate/proposta (varredura de diretório) ------
// 2026-09-20, Fase 33 (33-05), fold-in D-04a
// (`.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`):
// a contagem em `OpcoesScreen.jsx` cai de 1 para 0 porque a busca MIGROU DE
// DONO, não porque desapareceu — `SubAbaOperar` passou a ler o fan-out que
// `useOpcoesPropostas(store, carteira.map((p) => p.t))` (topo do mesmo
// arquivo) já paga para toda a carteira, em vez de refazer a mesma pergunta
// por conta própria. A garantia "uma fonte só" fica MAIS FORTE, não mais
// fraca, e passa a ser medida por VARREDURA DE DIRETÓRIO (mesmo padrão da
// seção 1 acima, `arquivosOpcoesDir`): `store.optionsGate(`/
// `store.optionsProposta(` aparecem exatamente 1× cada somando TODOS os
// arquivos de `web/src/opcoes/` — a ocorrência legítima é a de
// `useOpcoesPropostas.js` — e 0× em `OpcoesScreen.jsx` especificamente.
const semComentarioArquivo = (f) => semComentario(readFileSync(join(dirOpcoes, f), "utf8"));
const contarNaPasta = (regex) => arquivosOpcoesDir.reduce(
  (soma, f) => soma + (semComentarioArquivo(f).match(regex) || []).length, 0);
const nGateDir = contarNaPasta(/store\.optionsGate\(/g);
const nPropostaDir = contarNaPasta(/store\.optionsProposta\(/g);
ok("`store.optionsGate(` aparece exatamente 1× em toda web/src/opcoes/ (fonte única, fold-in D-04a)",
   nGateDir === 1, `achou ${nGateDir}`);
ok("`store.optionsProposta(` aparece exatamente 1× em toda web/src/opcoes/ (fonte única, fold-in D-04a)",
   nPropostaDir === 1, `achou ${nPropostaDir}`);
const nGateTela = (tela.match(/store\.optionsGate\(/g) || []).length;
const nPropostaTela = (tela.match(/store\.optionsProposta\(/g) || []).length;
ok("`store.optionsGate(` aparece 0× em OpcoesScreen.jsx (queda de 1→0: a busca mudou de arquivo, não desapareceu)",
   nGateTela === 0);
ok("`store.optionsProposta(` aparece 0× em OpcoesScreen.jsx (queda de 1→0: a busca mudou de arquivo, não desapareceu)",
   nPropostaTela === 0);

// ---- 4) optionsProposta guardado por gate/liquida (agora no hook) ----------
// 2026-09-20, Fase 33 (33-05), fold-in D-04a: a guarda "proposta só é pedida
// quando gate.liquida" não desaparece — ela passa a ser medida em
// `useOpcoesPropostas.js`, que JÁ a implementa (mesma rota, mesmo
// `multiperna: true`), em vez de na fatia de `SubAbaOperar` (que não tem mais
// chamada nenhuma para guardar). Forma diferente da guarda antiga (era um
// `if (!(gate && gate.liquida)) return` dentro de um `useEffect`; o hook usa
// `if (gate && gate.liquida) { store.optionsProposta(...) }` dentro do
// `.then` do gate) — MESMA garantia, forma que o hook já tinha desde a
// Fase 32 (32-03).
const hookPropostasFonte = semComentarioArquivo("useOpcoesPropostas.js");
const idxGuardaHook = hookPropostasFonte.indexOf("if (gate && gate.liquida)");
const idxChamadaHook = hookPropostasFonte.indexOf("store.optionsProposta(", idxGuardaHook >= 0 ? idxGuardaHook : 0);
ok("useOpcoesPropostas.js guarda `store.optionsProposta` com `if (gate && gate.liquida)` ANTES da chamada",
   idxGuardaHook >= 0 && idxChamadaHook > idxGuardaHook);
// Contrapartida NOVA (trava o retorno do fetch redundante): `SubAbaOperar`
// não pode ter voltado a buscar gate/proposta por conta própria — nenhuma
// forma de `store.options`, nem gate nem proposta.
ok("`SubAbaOperar` não contém `store.options` nenhum (gate/proposta vêm do fan-out por prop, não de fetch local)",
   !/store\.options/.test(subAba));

// ---- 5) manchete só via PropostaLastreada OU CandidatoOpcao (guardrail CVM) -
// ATUALIZADO 2026-09-16 (Fase 32, 32-04): `SubAbaOperar` ganhou o ramo
// multi-candidato (MULTI-02, portado de `PropostaDaPosicao`/App.jsx,
// aposentada nesta fase). A guarda NEGATIVA (nenhuma manchete própria) segue
// intacta e independente — só a checagem POSITIVA de delegação passa a
// aceitar os dois componentes legítimos: `PropostaLastreada` (candidato
// único) e `CandidatoOpcao` (N candidatos). O card continua sendo um
// componente IMPORTADO em ambos os ramos, nunca reimplementado inline.
ok("`SubAbaOperar` não renderiza `manchete` própria (delega a PropostaLastreada/CandidatoOpcao)",
   !/\{[^}]*\bmanchete\b[^}]*\}/.test(subAba) && !/\.manchete/.test(subAba));
ok("`SubAbaOperar` usa `<PropostaLastreada` (ramo de candidato único, não reimplementa o card)",
   /<PropostaLastreada/.test(subAba));
ok("`SubAbaOperar` usa `<CandidatoOpcao` (ramo multi-candidato, não reimplementa o card)",
   /<CandidatoOpcao/.test(subAba));

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
// 2026-09-19, Fase 33 (33-01): `blocoVigias` virou `<SecaoVigias` (o bloco
// migrou para componente próprio, nomenclatura de tag em vez de const) — os
// outros cinco NÃO se movem nesta fase, continuam const/nome idêntico.
for (const nome of ["cabecalho", "<SecaoVigias", "seletor", "LastroDoAtivo", "LeituraInterna", "blocoLeituraDoServico"]) {
  ok(`\`${nome}\` continua referenciado em OpcoesScreen.jsx`, tela.includes(nome));
}

// ---- 12) REORG-06 (Fase 33, 33-02, 2026-09-20): guardrail CVM de manchete,
// generalizado por varredura de DIRETÓRIO -------------------------------------
// A regra 5 acima cobre só o texto de `SubAbaOperar` — escopo de VARIÁVEL
// ÚNICA que bastava até a Fase 32, porque `SubAbaOperar` era o único lugar
// novo que renderizava candidato de opções. A Fase 33 cria seções job-to-be-
// done (`Secao*.jsx`) fora de `SubAbaOperar` capazes de compor os mesmos
// componentes que exibem `manchete` — a primeira é `SecaoDescobrir.jsx`
// (33-02), que embute `OportunidadesOpcoes`/`CuradoriaEstruturas`. Um
// arquivo novo que passasse a renderizar `candidato.manchete` diretamente
// (sem delegar a um dos 4 renderizadores já cobertos) passaria calado pela
// regra 5, que só lê `SubAbaOperar`. A allowlist abaixo é dos 4 arquivos que
// HOJE renderizam manchete verbatim (medido por grep em 2026-09-19/20):
// `PropostaLastreada.jsx`, `CandidatoOpcao.jsx`, `CuradoriaEstruturas.jsx`,
// `OportunidadesOpcoes.jsx`. Nenhuma outra `Secao*.jsx`/arquivo desta pasta
// pode conter manchete.
const RENDERIZADORES_DE_MANCHETE = [
  "PropostaLastreada.jsx", "CandidatoOpcao.jsx",
  "CuradoriaEstruturas.jsx", "OportunidadesOpcoes.jsx",
];
// Sanidade 1: a varredura por diretório não prova nada se o diretório for
// pequeno demais para uma reorganização em 5 seções ter deixado marca —
// número real de hoje (Fase 33-02): 17 arquivos.
ok("achou pelo menos 15 arquivos em web/src/opcoes/ (sanidade da varredura, REORG-06)",
   arquivosOpcoesDir.length >= 15);
// Sanidade 2: a allowlist não pode envelhecer — se um dos 4 renderizadores
// parar de conter manchete (refactor futuro que a esvazie), a allowlist
// estaria autorizando algo que já não existe mais, escondendo o dia em que
// isso mudou.
const semMancheteNaAllowlist = RENDERIZADORES_DE_MANCHETE.filter((f) => {
  const src = readFileSync(join(dirOpcoes, f), "utf8");
  return !/\.manchete\b/.test(src);
});
ok("cada arquivo da allowlist de manchete CONTÉM .manchete de fato (allowlist não envelheceu)"
   + (semMancheteNaAllowlist.length ? " (sem manchete: " + semMancheteNaAllowlist.join(", ") + ")" : ""),
   semMancheteNaAllowlist.length === 0);
// A regra em si: todo .jsx/.js de web/src/opcoes/ FORA da allowlist não pode
// renderizar manchete — nem `{...manchete...}` (JSX) nem `.manchete` avulso.
const comMancheteForaDaAllowlist = arquivosOpcoesDir.filter((f) => {
  if (RENDERIZADORES_DE_MANCHETE.includes(f)) return false;
  const src = readFileSync(join(dirOpcoes, f), "utf8");
  return /\{[^}]*\bmanchete\b[^}]*\}/.test(src) || /\.manchete\b/.test(src);
});
ok("nenhum arquivo de web/src/opcoes/ FORA da allowlist renderiza manchete (REORG-06)"
   + (comMancheteForaDaAllowlist.length ? " (violam: " + comMancheteForaDaAllowlist.join(", ") + ")" : ""),
   comMancheteForaDaAllowlist.length === 0);

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
