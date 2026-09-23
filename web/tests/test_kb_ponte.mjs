// Fase 38 (38-03) — guardião da PONTE entre as duas fontes didáticas
// determinísticas: a explicação ANCORADA nos números do card (`conceitos.py`,
// via `POST /api/conceito/{cid}`) e o glossário GENÉRICO da KB (`kb.py`, via
// o catálogo de 38-01, `GET /api/kb/catalogo`).
//
// Parte 1 (Task 1): caminho de dados do catálogo — helpers puros em
// glossario.js, rota em api.js, paridade nos dois stores, estado/ctx/ação em
// App.jsx.
// Parte 2 (Task 2): ConceitoSheet com discriminador `fonte`, render do
// verbete kb, mount global.
//
// Roda sem build: `node web/tests/test_kb_ponte.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { catalogoKbValido, verbeteDoCatalogo } from "../src/glossario.js";

const here = dirname(fileURLToPath(import.meta.url));
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const glossario = readFileSync(join(here, "..", "src", "glossario.js"), "utf8");
const ent = readFileSync(join(here, "..", "src", "entendimento.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ============================================================ Parte 1 (comportamental)
ok("catalogoKbValido(null) => false", catalogoKbValido(null) === false);
ok("catalogoKbValido({}) => false", catalogoKbValido({}) === false);
ok("catalogoKbValido({ verbetes: [] }) => false (falta familias)", catalogoKbValido({ verbetes: [] }) === false);
ok("catalogoKbValido({ modo, familias: [], verbetes: [] }) => true",
   catalogoKbValido({ modo: "educacional", familias: [], verbetes: [] }) === true);

const CAT = {
  modo: "educacional",
  familias: [{ id: "indicadores", rotulo: "Indicadores" }],
  verbetes: [
    { id: "ind-rsi", familia: "indicadores", titulo: "IFR (RSI)", texto: "O IFR mede a velocidade e a magnitude das variações de preço.", veja: [], termos: ["ifr", "rsi"] },
    { id: "vazio", familia: "indicadores", titulo: "Sem texto", texto: "", veja: [], termos: [] },
  ],
};
ok("verbeteDoCatalogo(cat, 'ind-rsi') => o verbete", verbeteDoCatalogo(CAT, "ind-rsi") === CAT.verbetes[0]);
ok("verbeteDoCatalogo(cat, 'nao-existe') => null", verbeteDoCatalogo(CAT, "nao-existe") === null);
ok("verbeteDoCatalogo(null, 'ind-rsi') => null", verbeteDoCatalogo(null, "ind-rsi") === null);
ok("verbeteDoCatalogo(undefined, 'x') => null", verbeteDoCatalogo(undefined, "x") === null);
ok("verbeteDoCatalogo com texto vazio => null (nunca corpo vazio)", verbeteDoCatalogo(CAT, "vazio") === null);

// ============================================================ Parte 1 (estático)
ok("glossario.js é módulo PURO: zero import (importável sem ciclo)",
   (glossario.match(/^import /gm) || []).length === 0);

ok("api.kbCatalogo chama GET /api/kb/catalogo com timeout 15000",
   /kbCatalogo: \(modo\) => req\("GET", "\/api\/kb\/catalogo"[\s\S]{0,120}?undefined, 15000\)/.test(apiSrc));
ok("rota /api/kb/catalogo referenciada exatamente 1x em api.js",
   (apiSrc.match(/\/api\/kb\/catalogo/g) || []).length === 1);

ok("serverStore.kbCatalogo existe (paridade)",
   /kbCatalogo: \(modo\) => api\.kbCatalogo\(modo\)/.test(persistence));
ok("deviceStore.kbCatalogo existe, modo local-first (paridade)",
   /async kbCatalogo\(modo\) \{ ensure\(\); return api\.kbCatalogo\(modo \|\| doc\.config\.appMode \|\| "estudo"\); \}/.test(persistence));

ok("App.jsx busca o catálogo via store.kbCatalogo(modoApp)",
   /store\.kbCatalogo\(modoApp\)/.test(app));
ok("A.abrirVerbeteKb existe e carrega fonte: \"kb\"",
   /abrirVerbeteKb: \(vid\) => setConceitoAberto\(\{ cid: vid, dados: null, trilha: \[\], fonte: "kb" \}\)/.test(app));
ok("A.abrirVerbete NÃO mudou de assinatura (test_concentracao_carteira.mjs trava isso)",
   /abrirVerbete: \(cid, dados\) => setConceitoAberto\(\{ cid, dados: dados \|\| null, trilha: \[\] \}\)/.test(app));
ok("ctx expõe kbCatalogo", /\bkbCatalogo,/.test(app));
ok("ctx expõe recarregarKb: carregarKb", /recarregarKb: carregarKb,/.test(app));
ok("falha do fetch cai em setKbCatalogo(null) (nunca lista inventada, princípio 4)",
   /setKbCatalogo\(null\)/.test(app));
ok("resposta em forma inesperada também cai em null (catalogoKbValido(r) ? r : null)",
   /catalogoKbValido\(r\) \? r : null/.test(app));

// ============================================================ Parte 2 (Task 2, estático)
ok("ConceitoSheet: default fonte = \"conceito\" (call-sites existentes preservados)",
   /fonte = "conceito"/.test(ent));
ok("literal 'fonte = \"conceito\"' aparece exatamente 1x em entendimento.jsx",
   (ent.match(/fonte = "conceito"/g) || []).length === 1);
ok("ramo conceito continua chamando store.conceito(cid, { dados }) sem edição",
   /store\.conceito\(cid, \{ dados \}\)/.test(ent));
ok("ramo kb resolve por verbeteDoCatalogo(kbCatalogo, cid), sem fetch",
   /verbeteDoCatalogo\(kbCatalogo, cid\)/.test(ent));
ok("bloco conceito guardado por fonte !== \"kb\"",
   /\{c && fonte !== "kb" && \(/.test(ent));
ok("bloco kb guardado por fonte === \"kb\"",
   /\{c && fonte === "kb" && \(/.test(ent));
ok("subtítulo do verbete kb é o texto honesto sobre ser genérico",
   /Verbete do glossário — explicação geral, sem números de nenhum ativo\./.test(ent));
ok("literal do subtítulo kb aparece exatamente 1x", (ent.match(/Verbete do glossário — explicação geral, sem números de nenhum ativo\./g) || []).length === 1);

// bloco kb não tem AssistenteBox nem Markdown — fatia entre o início do bloco
// kb e o fechamento do componente (não há mais nada depois dele no arquivo).
const iniBlocoKb = ent.indexOf('{c && fonte === "kb" && (');
const blocoKb = iniBlocoKb === -1 ? "" : ent.slice(iniBlocoKb);
ok("bloco kb encontrado para fatiamento", iniBlocoKb !== -1);
ok("bloco kb NÃO renderiza AssistenteBox (verbete genérico não tem snapshot de ativo)",
   !/AssistenteBox/.test(blocoKb));
ok("bloco kb NÃO usa <Markdown> nem dangerouslySetInnerHTML (T-38-09, texto = nó React puro)",
   !/<Markdown/.test(blocoKb) && !/dangerouslySetInnerHTML/.test(blocoKb));

ok("mount global passa fonte={conceitoAberto.fonte || \"conceito\"}",
   /fonte=\{conceitoAberto\.fonte \|\| "conceito"\}/.test(app));
ok("mount global passa kbCatalogo={kbCatalogo}",
   /kbCatalogo=\{kbCatalogo\}/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
