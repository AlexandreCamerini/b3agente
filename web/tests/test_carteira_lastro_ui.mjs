// Fase 14 (opções lastreadas — venda coberta/put de proteção), Plano 07.
//
// Guardião da CARTEIRA lastreada: trava visível (badge nas duas superfícies),
// venda limitada à quantidade LIVRE (fonte única `qtyLivre`, sem reimplementar
// a subtração em App.jsx), guardrail "stop/alvo nunca são vetados" preservado,
// patrimônio com as pernas lastreadas, e aviso de liquidação como ESTADO (sem
// CTA). Irmão de web/tests/test_opcoes_lastreadas_stores.mjs (guarda a mesma
// fonte única do lado de persistence.js) — este arquivo não duplica as
// asserções de store, só as de App.jsx.
//
// Roda sem build: `node web/tests/test_carteira_lastro_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) TravaPill: definida uma vez, RENDERIZADA em duas superfícies ------
ok("function TravaPill definida uma única vez", (app.match(/function TravaPill\(/g) || []).length === 1);
const usosTravaPill = (app.match(/<TravaPill /g) || []).length;
ok("TravaPill renderizada em duas ou mais superfícies (badge x2)", usosTravaPill >= 2);

// ---- (2) FONTE ÚNICA de qtyLivre: App.jsx IMPORTA, nunca reimplementa -----
ok("App.jsx IMPORTA qtyLivre de ./finance.js (linha de import, não identificador solto)",
  /import\s*\{[^}]*\bqtyLivre\b[^}]*\}\s*from\s*["']\.\/finance\.js["']/.test(app));
ok("App.jsx NÃO reimplementa a subtração qty - qtyTravada (asserção negativa)",
  !/qty\s*-\s*\(?[A-Za-z.]*qtyTravada/.test(app));
ok("App.jsx NÃO calcula `livre` por subtração local — só via qtyLivre(",
  !/const\s+livre\s*=\s*(?!\s*qtyLivre\()/.test(app));

// ---- (3) SellModal: teto é `livre` (via qtyLivre), nunca mais pos.qty -----
ok("SellModal NÃO usa mais Math.min(pos.qty como teto (asserção negativa)",
  !/Math\.min\(pos\.qty/.test(app));
ok("SellModal deriva o teto de qtyLivre(pos) (const livre = qtyLivre(pos))",
  /const\s+livre\s*=\s*qtyLivre\(pos\)/.test(app));
ok("SellModal usa `livre` no cálculo de qty/step/botão (Math.min(livre)",
  (app.match(/Math\.min\(livre,/g) || []).length >= 2);
ok("botão 'Vender tudo' usa livre, não pos.qty (\"Vender tudo (\" + livre)",
  app.includes('"Vender tudo (" + livre + ")"'));
ok("botão de confirmar venda desabilita quando livre <= 0",
  /A\.confirmSell\}\s*disabled=\{livre\s*<=\s*0\}/.test(app));
ok("aviso de trava na venda vem de cp.avisoTravaNaVenda (não hardcodado)",
  app.includes("ctx.cp.avisoTravaNaVenda(pos.qtyTravada)"));

// ---- (4) A.openSell monta a quantidade a partir de qtyLivre(pos) ----------
ok("A.openSell NÃO usa mais pos.qty (asserção negativa)",
  !/setSellModal\(\{\s*t,\s*qty:\s*pos\.qty\s*\}\)/.test(app));
ok("A.openSell usa qtyLivre(pos)",
  /setSellModal\(\{\s*t,\s*qty:\s*qtyLivre\(pos\)\s*\}\)/.test(app));

// ---- (5) guardrail: stop/alvo NUNCA são vetados pela trava -----------------
ok("nenhum botão de stop/alvo é desabilitado por qtyTravada (asserção negativa)",
  !/disabled=\{[^}]*qtyTravada[^}]*\}/.test(app));
// Fase 22 (SYS-02, 2026-09-06): o emoji de gráfico do botão de Stop/alvo
// virou `<NavIcon id="evolucao">`; o rótulo textual não mudou. O glifo
// tipográfico do botão irmão (editar/lápis) segue como está — fora do
// escopo de SYS-02, ver 22-UI-SPEC.md Out-of-scope symbols. O que este
// guardião protege continua sendo o guardrail de produto: stop/alvo NUNCA é
// vetado, então os dois botões existem e não têm `disabled`.
ok("os botões de Stop/alvo (IA) e Editar stop/alvo continuam sem `disabled`",
  app.includes("Stop/alvo (IA)") && app.includes("✎ Editar stop/alvo"));

// ---- (6) Patrimônio: TODAS as chamadas de portfolioMetrics passam optionPositions
const chamadas = (app.match(/portfolioMetrics\([^)]*\)/g) || []);
ok("existem chamadas de portfolioMetrics em App.jsx", chamadas.length > 0);
ok("TODAS as chamadas de portfolioMetrics passam optionPositions (patrimônio inclui as pernas lastreadas)",
  chamadas.length > 0 && chamadas.every((c) => c.includes("optionPositions")));
ok("concentracaoMaxima continua recebendo só positions/quotes/total (não optionPositions)",
  /concentracaoMaxima\(data\.positions, quotes, total\)/.test(app));
ok("qtyLivre NÃO entra em nenhuma conta de valor de patrimônio (só é usada como teto de venda)",
  !/portfolioMetrics\([^)]*qtyLivre/.test(app));

// ---- (7) Aviso de liquidação: ESTADO, não ação — sem botão -----------------
const iAviso = app.indexOf("function AvisoLiquidacao(");
ok("function AvisoLiquidacao existe", iAviso >= 0);
const blocoAviso = iAviso >= 0 ? app.slice(iAviso, app.indexOf("\n}", iAviso) + 2) : "";
ok("bloco de AvisoLiquidacao NÃO contém <button", iAviso >= 0 && !blocoAviso.includes("<button"));
ok("texto do aviso vem de cp.avisoLiquidacaoForcada (não hardcodado no JSX)",
  blocoAviso.includes("cp.avisoLiquidacaoForcada("));
ok("AvisoLiquidacao é renderizado no card da posição (CarteiraScreen)",
  app.includes("<AvisoLiquidacao evento={eventoLiquidacaoRecente(data.history, p.t)} cp={cp} />"));
ok("evento de liquidação é derivado do histórico (motivo/origem/kind/acao do servidor)",
  /h\.motivo === "vencimento" && h\.origem === "sistema"/.test(app) || /motivo === "vencimento" && h\.origem === "sistema"/.test(app));

// ---- (8) copy.js: chaves novas existem nos dois modos, sem vocabulário de ordem no Estudo
const CHAVES_NOVAS = ["badgeTravada", "avisoTravaNaVenda", "avisoLiquidacaoForcada", "linhaPatrimonioOpcoes"];
ok("chaves novas existem nos dois modos (badgeTravada/avisoTravaNaVenda/avisoLiquidacaoForcada/linhaPatrimonioOpcoes)",
  CHAVES_NOVAS.every((k) => k in COPY.estudo) && CHAVES_NOVAS.every((k) => k in COPY.operador));
ok("COPY.estudo.badgeTravada não contém vocabulário de ordem",
  !/vender|comprar/i.test(COPY.estudo.badgeTravada(3)));
ok("COPY.estudo.avisoTravaNaVenda não contém vocabulário de ordem",
  !/vender|comprar/i.test(COPY.estudo.avisoTravaNaVenda(3)));
ok("COPY.estudo.avisoLiquidacaoForcada (ITM e OTM) não contém vocabulário de ordem",
  !/vender|comprar/i.test(COPY.estudo.avisoLiquidacaoForcada("PETR4", "1,85")) &&
  !/vender|comprar/i.test(COPY.estudo.avisoLiquidacaoForcada("PETR4", 0)));
ok("avisoLiquidacaoForcada branca ITM × OTM pelo valor (valor === 0 muda o texto)",
  COPY.operador.avisoLiquidacaoForcada("PETR4", "1,85") !== COPY.operador.avisoLiquidacaoForcada("PETR4", 0));

if (fails) { console.error(`\n${fails} asserção(ões) falharam.`); process.exit(1); }
console.log("\nTODOS OS TESTES DA CARTEIRA LASTREADA PASSARAM");
