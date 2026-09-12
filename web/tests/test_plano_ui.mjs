// Fase 25, Plano 06 (Fase 5 do 25-CONTEXT) — guardião do PLANO VISÍVEL no app.
//
// O que esta fase mudou: até 2026-09-12 NADA no app lia `authUser.plan`, e a
// recusa por limite de watchlist chegava como frase crua do backend. Agora há
// um tile no grupo Conta do hub de Perfil, uma sub-tela (`PlanoScreen`) e um
// banner compartilhado (`LimiteAtingido`) alimentado pelo 402 estruturado.
//
// As REGRESSÕES que este guardião existe para pegar — todas do relatório do
// UX Researcher desta fase, e todas fáceis de reintroduzir "melhorando" a tela:
//  1) linguagem de upgrade (não existe loja/IAP: um CTA promete o que não se
//     cumpre — ADR-010, decisão 4);
//  2) `T.negative` no aviso de limite (vermelho é reservado a P&L; usá-lo aqui
//     faria "bati o teto" parecer prejuízo);
//  3) o texto divergir entre Estudo e Operador (é estado de CONTA, não voz de
//     professor vs mesa) — aqui a paridade é de CONTEÚDO, não só de chave;
//  4) badge global de plano em toda tela;
//  5) tabela comparativa Free × Pro dentro da tela de plano;
//  6) o código do 402 divergir entre `main.py` e `plan.js` — são duas pontas do
//     mesmo contrato e nada mais as amarra;
//  7) o aviso de limite virar toast/modal, ou engolir erro técnico junto.
//
// Padrão "static source inspection" da casa (mesmo de
// test_fase13_contadores_ui.mjs), com import de verdade onde o módulo é JS
// puro (copy.js, plan.js). Roda sem build: `node web/tests/test_plano_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";
import { COD_LIMITE_WATCHLIST, canAddTicker, canGrowWatchlistTo, erroDeLimiteWatchlist, limiteDeWatchlist } from "../src/plan.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const srcPlan = readFileSync(join(here, "..", "src", "plan.js"), "utf8");
const mainPy = readFileSync(join(here, "..", "..", "server", "app", "main.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Bracket-matching igual ao de test_fase13_contadores_ui.mjs.
function bodyOf(source, anchor) {
  const at = source.indexOf(anchor);
  if (at < 0) return null;
  const open = source.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") { depth--; if (depth === 0) return source.slice(open, i + 1); }
  }
  return null;
}
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const CHAVES = [
  "planoRotulo", "planoNome", "planoResumoTile", "planoTituloTela", "planoDescricao",
  "planoEntitlementAnalises", "planoEntitlementWatchlist", "planoLimiteIndisponivel",
  "planoAvisoLimiteWatchlist",
];

// ===========================================================================
// 1) copy.js — as chaves existem nos dois modos com o MESMO CONTEÚDO
// ===========================================================================
// Paridade mais forte que a de `test_copy_theme.mjs` (que compara CONJUNTOS de
// chave): aqui as duas vozes têm de dizer a MESMA frase. Chave espelhada com
// texto diferente passaria lá e quebraria a decisão desta fase em silêncio.
const AMOSTRAS = [[], [10, 7], [null, null], [0, 0], ["free"], [30]];
const renderiza = (v) => (typeof v === "function" ? AMOSTRAS.map((a) => String(v(...a))).join(" ") : String(v));

for (const k of CHAVES) {
  ok(`copy.estudo.${k} existe`, Object.prototype.hasOwnProperty.call(COPY.estudo, k));
  ok(`copy.operador.${k} existe`, Object.prototype.hasOwnProperty.call(COPY.operador, k));
  ok(
    `copy.${k}: CONTEÚDO idêntico nos dois modos (não só a chave)`,
    renderiza(COPY.estudo[k]) === renderiza(COPY.operador[k])
  );
}

// Sanidade da comparação acima: se ela estivesse quebrada (comparando sempre
// "undefined" === "undefined", por exemplo), o assert passaria com textos
// diferentes. Este caso prova que ela REPROVA divergência.
ok(
  "sanidade: a comparação de conteúdo reprova textos diferentes",
  renderiza("Plano") !== renderiza("Plano ")
);

// ===========================================================================
// 2) ZERO linguagem de upgrade — nas chaves e no fonte da tela
// ===========================================================================
// Não existe loja/IAP no produto. Um CTA de assinatura (ou um "em breve")
// prometeria o que não se cumpre — ADR-010, decisão 4.
const PADROES_DE_UPGRADE = [
  /\bassin(e|ar|atura|aturas)\b/i,
  /\bupgrade\b/i,
  /\bvire\s+pro\b/i,
  /\bcontrat(e|ar)\b/i,
  /\bfa[çc]a\s+o\s+upgrade\b/i,
  /\bem\s+breve\b/i,
  /\bdesbloquei(e|ar)\b/i,
  /\bplano\s+pago\b/i,
];
const textoDasChaves = CHAVES.map((k) => renderiza(COPY.estudo[k]) + renderiza(COPY.operador[k])).join(" ");
for (const re of PADROES_DE_UPGRADE) {
  ok(`nenhuma chave de plano contém ${re} (ADR-010, decisão 4)`, !re.test(textoDasChaves));
}
ok(
  "sanidade: os padrões de upgrade casam quando o texto existe",
  PADROES_DE_UPGRADE.some((re) => re.test("Assine o plano pago e faça o upgrade"))
);
ok(
  "nenhuma CHAVE de copy com nome de CTA de upgrade (planoUpgrade*, planoAssinar*, planoCta*)",
  !Object.keys(COPY.estudo).some((k) => /^plano(Upgrade|Assinar|Assinatura|Cta|Comprar)/.test(k))
);

// ===========================================================================
// 3) LimiteAtingido — cor, gatilho e lugar
// ===========================================================================
const limiteBody = bodyOf(src, "function LimiteAtingido({ erro, cp }) ");
ok("corpo de LimiteAtingido localizado", !!limiteBody);
ok(
  "LimiteAtingido NÃO usa T.negative (vermelho é reservado a P&L)",
  !!limiteBody && !limiteBody.includes("T.negative")
);
ok(
  "LimiteAtingido NÃO usa T.positive (idem)",
  !!limiteBody && !limiteBody.includes("T.positive")
);
ok("LimiteAtingido usa T.warn", !!limiteBody && limiteBody.includes("T.warn"));
ok(
  "sanidade: a busca por T.negative acha o padrão quando ele existe",
  /T\.negative/.test("color: T.negative")
);
ok(
  "LimiteAtingido só renderiza com código reconhecido (passa por limiteDeWatchlist e sai cedo)",
  !!limiteBody && /limiteDeWatchlist\(erro\)/.test(limiteBody) && /if \(!lim\) return null;/.test(limiteBody)
);
ok(
  "LimiteAtingido mostra texto de copy.js, nunca `erro.message` cru do backend",
  !!limiteBody && limiteBody.includes("cp.planoAvisoLimiteWatchlist(") && !/erro\.message|\.detail\.message/.test(limiteBody)
);

// INLINE, não toast/modal: os dois usos moram dentro do CatalogModal, e o
// modal é uma tela que já estava aberta — o banner não abre nada.
const usos = (src.match(/<LimiteAtingido/g) || []).length;
ok(`<LimiteAtingido é usado exatamente 2 vezes (achado ${usos})`, usos === 2);
const catalogBody = bodyOf(src, "function CatalogModal({ ctx }) ");
ok("corpo de CatalogModal localizado", !!catalogBody);
ok(
  "os DOIS usos do banner estão dentro do CatalogModal (inline, no ponto da tentativa)",
  !!catalogBody && (catalogBody.match(/<LimiteAtingido/g) || []).length === 2
);

// ===========================================================================
// 4) a recusa de plano NÃO vira toast, e o erro técnico continua virando
// ===========================================================================
// Misturar as duas categorias no mesmo componente é o que o princípio 4 do
// CLAUDE.md proíbe: "fonte fora do ar" e "bateu o teto do plano" não são a
// mesma coisa e não podem ter a mesma saída na tela.
const saveCatalogBody = bodyOf(src, "saveCatalog: async () => ");
ok("corpo de A.saveCatalog localizado", !!saveCatalogBody);
const saveSemComentario = saveCatalogBody ? semComentario(saveCatalogBody) : "";
ok(
  "saveCatalog desvia a recusa de limite para o banner ANTES de qualquer flash",
  !!saveCatalogBody
    && /if \(limiteDeWatchlist\(e\)\) \{ setCatalogLimite\(e\); return; \}/.test(saveSemComentario)
    && saveSemComentario.indexOf("limiteDeWatchlist(e)") < saveSemComentario.indexOf('flash("Erro:')
);
ok(
  "saveCatalog MANTÉM o toast para erro técnico (as duas categorias não foram fundidas)",
  !!saveSemComentario && saveSemComentario.includes('flash("Erro:')
);
const addTickerBody = bodyOf(src, "addTicker: async (ticker) => ");
ok("corpo de A.addTicker localizado", !!addTickerBody);
const addSemComentario = addTickerBody ? semComentario(addTickerBody) : "";
ok(
  "addTicker manda a recusa de limite para o banner (msg vazia, sem linha vermelha duplicada)",
  !!addSemComentario && /if \(limiteDeWatchlist\(e\)\) \{ setAddState\(\{ busy: false, msg: "", limite: e \}\); return false; \}/.test(addSemComentario)
);
ok(
  "addTicker MANTÉM a linha de erro para o que NÃO é limite (ticker inexistente, provedor fora do ar)",
  !!addSemComentario && /msg: "✗ " \+ \(e\.message \|\| String\(e\)\)/.test(addSemComentario)
);
ok(
  "o gate LOCAL de watchlist também vai para o banner (iPhone: lá não há 402)",
  !!addSemComentario && /erroDeLimiteWatchlist\(gate\)/.test(addSemComentario)
);
// A regressão específica: o banner NUNCA pode ser disparado por `flash`.
ok(
  "nenhum `flash(` recebe o aviso de limite do plano",
  !/flash\([^)]*planoAvisoLimiteWatchlist/.test(semComentario(src))
);

// ===========================================================================
// 5) o tile mora no grupo CONTA — e não há badge global
// ===========================================================================
const iConta = src.indexOf('<div style={hubGroup}>Conta</div>');
const iPersonalizacao = src.indexOf('<div style={hubGroup}>Personalização e simulação</div>');
const iTilePlano = src.indexOf('onOpen("plano")');
ok("grupo Conta localizado no PerfilHub", iConta >= 0);
ok("grupo seguinte (Personalização e simulação) localizado", iPersonalizacao > iConta);
ok(
  "o tile de Plano está DENTRO do grupo Conta (entre os dois cabeçalhos)",
  iTilePlano > iConta && iTilePlano < iPersonalizacao
);
ok(
  "o tile usa os textos de copy.js (planoRotulo/planoResumoTile), não literal na tela",
  /title=\{ctx\.cp\.planoRotulo\}/.test(src) && /sub=\{ctx\.cp\.planoResumoTile\(/.test(src)
);
// Badge global: se o plano aparecesse em toda tela, `authUser.plan` seria lido
// em mais lugares que estes dois (o tile e a sub-tela).
const leiturasDoPlano = (semComentario(src).match(/authUser\.plan\b/g) || []).length;
ok(
  `authUser.plan é lido em exatamente 2 lugares — o tile e a PlanoScreen (achado ${leiturasDoPlano})`,
  leiturasDoPlano === 2
);
ok(
  "roteamento: perfilView === \"plano\" abre a PlanoScreen",
  /perfilView === "plano"/.test(src) && /<PlanoScreen ctx=\{ctx\} \/>/.test(src)
);

// ===========================================================================
// 6) PlanoScreen — sem comparação entre planos, sem cor de P&L
// ===========================================================================
const planoBody = bodyOf(src, "function PlanoScreen({ ctx }) ");
ok("corpo de PlanoScreen localizado", !!planoBody);
const planoSemComentario = planoBody ? semComentario(planoBody) : "";
ok(
  "PlanoScreen não monta tabela comparativa (<table)",
  !!planoSemComentario && !/<table/i.test(planoSemComentario)
);
ok(
  "PlanoScreen não itera uma lista de planos (.map( sobre planos)",
  !!planoSemComentario && !/\.map\(/.test(planoSemComentario)
);
ok(
  "PlanoScreen não escreve nenhum id de plano (a lista de planos não vive no front)",
  !!planoSemComentario && !/["'`](free|pro)["'`]/.test(planoSemComentario)
);
ok(
  "PlanoScreen não usa cor de P&L (T.negative/T.positive)",
  !!planoSemComentario && !/T\.negative|T\.positive/.test(planoSemComentario)
);
ok(
  "PlanoScreen compõe as DUAS cotas (aiQuota + watchlistQuota), não uma só",
  !!planoSemComentario && planoSemComentario.includes("store.aiQuota()") && planoSemComentario.includes("store.watchlistQuota()")
);
ok(
  "PlanoScreen lê o plano de authUser (já vem de /api/auth/me), sem chamada nova",
  !!planoSemComentario && /ctx\.authUser\.plan/.test(planoSemComentario)
);
ok(
  "PlanoScreen não hardcoda limite: nenhum número solto de análises/ativos",
  !!planoSemComentario && !/\b(10|30|60)\b/.test(planoSemComentario.replace(/fontSize|padding|borderRadius|marginTop|letterSpacing|width|height|maxWidth|"[0-9.]+px"/g, ""))
);

// ===========================================================================
// 7) o CÓDIGO do 402 é o mesmo dos dois lados da fronteira
// ===========================================================================
// `main.COD_WATCHLIST` e `plan.COD_LIMITE_WATCHLIST` são as duas pontas do
// mesmo contrato e nada mais as amarra: divergir aqui faz o banner sumir sem
// erro nenhum, calado, em produção.
const mCod = mainPy.match(/COD_WATCHLIST = "([^"]+)"/);
ok("main.py declara COD_WATCHLIST", !!mCod);
ok(
  `o código é o MESMO no backend e no front ("${mCod ? mCod[1] : "?"}" × "${COD_LIMITE_WATCHLIST}")`,
  !!mCod && mCod[1] === COD_LIMITE_WATCHLIST
);
// O 402 estruturado publica os quatro campos que o front lê.
const recusaPy = mainPy.slice(mainPy.indexOf("def _recusa_de_watchlist"), mainPy.indexOf("@app.post(\"/api/snapshot\")"));
for (const campo of ["code", "message", "limite", "usado"]) {
  ok(`_recusa_de_watchlist publica "${campo}"`, recusaPy.includes(`"${campo}"`));
}

// ===========================================================================
// 8) comportamento de plan.js — a leitura do erro, de verdade (não por regex)
// ===========================================================================
const erroServidor = { code: COD_LIMITE_WATCHLIST, detail: { code: COD_LIMITE_WATCHLIST, message: "...", limite: 10, usado: 10 } };
ok("limiteDeWatchlist lê o 402 do servidor", JSON.stringify(limiteDeWatchlist(erroServidor)) === JSON.stringify({ limite: 10, usado: 10 }));
ok("limiteDeWatchlist devolve null para erro genérico (erro técnico não vira aviso de plano)", limiteDeWatchlist(new Error("Sem conexão com o servidor.")) === null);
ok("limiteDeWatchlist devolve null para 402 de OUTRO teto (código diferente)", limiteDeWatchlist({ code: "plano_analises", detail: { limite: 30 } }) === null);
ok("limiteDeWatchlist tolera null/undefined", limiteDeWatchlist(null) === null && limiteDeWatchlist(undefined) === null);
ok(
  "limiteDeWatchlist nunca inventa 0: número torto vira null",
  JSON.stringify(limiteDeWatchlist({ code: COD_LIMITE_WATCHLIST, detail: { limite: "dez", usado: null } })) === JSON.stringify({ limite: null, usado: null })
);

// O gate LOCAL produz a MESMA forma do 402 — é o que faz o banner funcionar
// no iPhone, onde não existe 402 de watchlist.
const gateLocal = canAddTicker(10, { id: "free", maxWatchlist: 10 });
ok("canAddTicker recusa carimbando o código", gateLocal.ok === false && gateLocal.code === COD_LIMITE_WATCHLIST);
ok("canAddTicker mantém a `reason` de sempre (texto de fallback intacto)", /10 ativos/.test(gateLocal.reason));
const eLocal = erroDeLimiteWatchlist(gateLocal);
ok("erroDeLimiteWatchlist produz Error com code e detail (mesma forma do api.js)", eLocal instanceof Error && eLocal.code === COD_LIMITE_WATCHLIST);
ok("o erro do gate local é lido pelo MESMO leitor do 402", JSON.stringify(limiteDeWatchlist(eLocal)) === JSON.stringify({ limite: 10, usado: 10 }));
const gateBulk = canGrowWatchlistTo(11, { id: "free", maxWatchlist: 10 });
ok("canGrowWatchlistTo recusa carimbando o código", gateBulk.ok === false && gateBulk.code === COD_LIMITE_WATCHLIST);
ok(
  "canGrowWatchlistTo NÃO inventa `usado` (só recebe o tamanho PEDIDO; quem tem o de hoje é o chamador)",
  gateBulk.usado === undefined
);
ok(
  "o chamador informa `usado` de hoje na recusa em massa",
  JSON.stringify(limiteDeWatchlist(erroDeLimiteWatchlist(gateBulk, 10))) === JSON.stringify({ limite: 10, usado: 10 })
);
ok("gate que PASSA não carrega código nenhum", canAddTicker(0, { id: "free", maxWatchlist: 10 }).ok === true);

// O guardrail de topo do plan.js continua valendo: nenhum limite hardcodado.
ok(
  "plan.js (sem comentários) continua sem número de limite hardcodado",
  !/maxWatchlist:\s*\d|maxAnalysesPerMonth:\s*\d/.test(semComentario(srcPlan))
);

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
