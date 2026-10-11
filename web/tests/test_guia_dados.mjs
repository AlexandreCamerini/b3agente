// Guardião do guia das telas (quick 261011-l5x): paridade site<->web da fonte única de dados,
// regras de conteúdo (sem repetição, sem navegação pura, sem aviso por ponto, sem promessa) e
// orçamento de pontos por tela. Roda sem build: `node web/tests/test_guia_dados.mjs`.
import { readFileSync, existsSync, readdirSync, statSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import vm from "node:vm";
import { parseTelasData, validarGuia, sobreposicao, LIMIAR_SOBREPOSICAO } from "../src/guiaDados.js";

const here = dirname(fileURLToPath(import.meta.url));
const site = join(here, "..", "..", "site");
const arq = join(site, "js", "telas-data.js");
const texto = readFileSync(arq, "utf8");
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra)); if (!cond) fails++; };

// Orçamento por tela (PLAN 261011-l5x, soma 57). O guardião trava 50..60 no total e cada tela <= orçamento.
const ORCAMENTO = { boas: 2, acomp: 4, radar: 5, watch: 3, plano: 5, ordem: 3, pend: 2, port: 3, opc: 3, opcobj: 3,
  opcpiso: 3, pior: 3, payoff: 3, confest: 4, termo: 2, opcaberta: 2, boris: 3, web1: 1, web2: 2, web3: 1 };

// 1) paridade: o site executa o arquivo como script (window.TELAS); o app faz parse do mesmo texto.
const ctx = { window: {} };
vm.runInNewContext(texto, ctx);
const viaSite = JSON.parse(JSON.stringify(ctx.window.TELAS));
const viaApp = parseTelasData(texto);
ok("paridade site<->web: parseTelasData == avaliação do script", JSON.stringify(viaSite) === JSON.stringify(viaApp));
ok("20 telas", viaApp.length === 20);
ok("orçamento cobre exatamente as telas do guia", JSON.stringify(Object.keys(ORCAMENTO).sort()) === JSON.stringify(viaApp.map((t) => t.id).sort()));

// 2) regras de conteúdo
const viol = validarGuia(viaApp, ORCAMENTO, (img) => existsSync(join(site, img)));
ok("validarGuia devolve []", viol.length === 0, viol.join(" | "));
const total = viaApp.reduce((s, t) => s + t.pontos.length, 0);
ok("total de pontos entre 50 e 60 (" + total + ")", total >= 50 && total <= 60);

// 3) sanidade da métrica, com os textos antigos fixados como fixture
const antigoAcomp = "Cartão no Acompanhar com o estado do Operador IA: ligado ou desligado no servidor e se ele só avisa ou também executa. Descreve a configuração, não que ele esteja rodando agora. No Modo Estudo ele só sinaliza. Toque para abrir.";
const antigoPort = "O cartão no topo diz se o Operador IA está ligado ou desligado no servidor e se ele só avisa ou também executa. Descreve a configuração, não que ele esteja rodando agora. No Modo Estudo ele só sinaliza; no Modo Operador a execução segue simulada. Toque para abrir.";
const antigoConf = "Quantos contratos e ações entram. “Sem lastro: ações livres” indica que as ações ainda não estão comprometidas.";
const antigoAberta = "As 100 ações passam a ser lastro: ficam comprometidas com a estrutura e deixam de estar livres para outras operações.";
ok("métrica pega o duplicado antigo acomp x port (>= limiar)", sobreposicao(antigoAcomp, antigoPort) >= LIMIAR_SOBREPOSICAO);
ok("métrica solta o par legítimo confest x opcaberta (< limiar)", sobreposicao(antigoConf, antigoAberta) < LIMIAR_SOBREPOSICAO);
ok("sobreposição de união vazia = 0", sobreposicao("", "a b") === 0);
ok("LIMIAR_SOBREPOSICAO = 0,35", LIMIAR_SOBREPOSICAO === 0.35);

// validarGuia pega violações sintéticas
const base = JSON.parse(JSON.stringify(viaApp));
const ruim = JSON.parse(JSON.stringify(base)); ruim[0].guard = "x"; ruim[0].pontos[0].titulo = "Voltar";
ok("validarGuia acusa guard e navegação pura", validarGuia(ruim, ORCAMENTO).length >= 2);

// 4) fonte única: o loader do app importa o MESMO arquivo e não duplica dado
const loader = join(here, "..", "src", "guiaTelas.js");
if (existsSync(loader)) {
  const l = readFileSync(loader, "utf8");
  ok("guiaTelas.js importa site/js/telas-data.js?raw", /site\/js\/telas-data\.js\?raw/.test(l));
  ok("guiaTelas.js não duplica dado (sem \"titulo\":)", !/"titulo":/.test(l));
}
const alt0 = viaApp[0].alt;
const achados = [];
(function varre(dir) {
  for (const n of readdirSync(dir)) {
    const p = join(dir, n);
    if (statSync(p).isDirectory()) varre(p);
    else if (/\.(js|jsx)$/.test(n) && readFileSync(p, "utf8").includes(alt0)) achados.push(p);
  }
})(join(here, "..", "src"));
ok("nenhum arquivo de web/src duplica os dados do guia", achados.length === 0, achados.join(", "));

if (fails) { console.log(`\n${fails} falha(s).`); process.exit(1); }
console.log("\ntodos os testes passaram.");
