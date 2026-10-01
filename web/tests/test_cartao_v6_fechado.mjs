// Fase 46 (plano 46-05, CART6-01) — guardião estático do card FECHADO v6.
// Lê App.jsx como TEXTO. Guardião não se apaga; reversão deliberada atualiza com nota.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const m = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`).exec(src);
  if (!m) return "";
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
const semCom = (b) => b.replace(/\{\/\*[\s\S]*?\*\/\}/g, "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");

const regua = semCom(functionBody("ReguaPlano"));
const faixa = semCom(functionBody("FaixaVencimento"));
const estado = semCom(functionBody("LinhaEstadoV6"));
const cartao = semCom(functionBody("CartaoPosicao"));
const hook = semCom(functionBody("useLeiturasPlano"));
const tela = semCom(functionBody("CarteiraScreen"));
const novos = [regua, faixa, estado, cartao, hook].join("\n");

// --- existência e ordem (D-14: antes de LinhaChamadaOpcoes) -----------------
const idx = (n) => src.indexOf(`function ${n}(`);
for (const n of ["useLeiturasPlano", "ReguaPlano", "FaixaVencimento", "LinhaEstadoV6", "CartaoPosicao"]) {
  ok(`${n} existe`, idx(n) > 0);
}
for (const n of ["ReguaPlano", "FaixaVencimento", "LinhaEstadoV6", "CartaoPosicao"]) {
  ok(`${n} fica antes de LinhaChamadaOpcoes`, idx(n) > 0 && idx(n) < idx("LinhaChamadaOpcoes"));
}

// --- rodapé (D-17, S8) ------------------------------------------------------
ok("rodapé com aria-expanded", /aria-expanded=\{aberto\}/.test(cartao));
ok("rodapé com aria-controls", /aria-controls=\{idCorpo\}/.test(cartao) && /id=\{idCorpo\}/.test(cartao));
ok("rodapé com alvo >= 44", /minHeight:\s*44\b/.test(cartao));
ok("rodapé troca rodape_abrir/rodape_fechar", /rodape_fechar/.test(cartao) && /rodape_abrir/.test(cartao));

// --- régua / faixa ---------------------------------------------------------
ok("ReguaPlano com role=img e aria-label", /role="img"/.test(regua) && /aria-label=/.test(regua));
ok("FaixaVencimento com role=img e aria-label do backend", /role="img"/.test(faixa) && /aria-label=\{c\.faixaAria\}/.test(faixa));
ok("ReguaPlano usa reguaAria do backend", /leitura\.reguaAria/.test(regua));
ok("disco 'agora' só com preco != null", /xAgora != null && \(\s*<div/.test(regua) && /const xAgora = preco != null \?/.test(regua));
ok("ReguaPlano só desenha com stop e alvo", /p\.stop == null \|\| p\.alvo == null\) return null/.test(regua));
ok("FaixaVencimento sem cenarios -> aguardando_calculo", /!c\)/.test(faixa) && /"aguardando_calculo"/.test(faixa));
ok("FaixaVencimento usa sem_piso e sem_teto", /"sem_piso"/.test(faixa) && /"sem_teto"/.test(faixa));
ok("régua OU faixa, nunca as duas", /\{e \? <FaixaVencimento[^>]*\/> : <ReguaPlano/.test(cartao));

// --- estado e Bóris explica ------------------------------------------------
ok("LinhaEstadoV6 usa estadoPrincipalV6 (não decide estado no JSX)", /estadoPrincipalV6\(/.test(estado));
ok("'Bóris explica' só no Estudo (!operador)", /!operador && explica/.test(cartao) && /cartaoDidaticaTxt\("boris_explica"\)/.test(cartao));
ok("Bóris explica vem do backend (didatica.borisExplica)", /didatica\.borisExplica/.test(cartao));

// --- pureza: sem hex, sem disabled, sem preço de marcação, sem innerHTML -----
ok("sem hex literal nos componentes novos", !/#[0-9a-fA-F]{3,6}\b/.test(novos));
ok("sem disabled= nos componentes novos", !/\bdisabled=/.test(novos));
ok("useLeiturasPlano não usa o preço de marcação", !/markPrice/.test(hook));
ok("useLeiturasPlano usa quotes[t].price > 0", /q\.price > 0/.test(hook) && /typeof q\.price === "number"/.test(hook));
ok("sem dangerouslySetInnerHTML na fatia nova", !/dangerouslySetInnerHTML/.test(novos));
ok("sem toFixed/Math.round em campo financeiro nos componentes", !/\.toFixed\(|Math\.round\(/.test([regua, faixa, estado, cartao].join("\n")));
const aritmetica = /\b(preco|resultado|be|stop|alvo|avg|distStopPct|distAlvoPct)\s*[-+*/]\s*[\w(]/;
ok("sem aritmética (+ - * /) sobre campo financeiro", !aritmetica.test([regua, faixa, estado, cartao, hook].join("\n").replace(/"[^"\n]*"/g, '""')));

// --- fiação ----------------------------------------------------------------
ok("hook chama store.carteiraLeitura uma vez", (src.match(/store\.carteiraLeitura/g) || []).length === 1);
ok("hook usa token monotônico e corte por escopo", /\+\+seqRef\.current/.test(hook) && /corteRef\.current = \+\+seqRef\.current/.test(hook));
ok("CarteiraScreen chama useLeiturasPlano", /useLeiturasPlano\(/.test(tela));
ok("CarteiraScreen renderiza <CartaoPosicao", /<CartaoPosicao/.test(tela));
ok("CarteiraScreen mantém âncora posicao-<t>", /id=\{"posicao-" \+ p\.t\}/.test(tela));
ok("CarteiraScreen sem disabled= novo", !/\bdisabled=/.test(tela));

console.log(fails ? `\n${fails} falha(s)` : "\nOK");
process.exit(fails ? 1 : 0);
