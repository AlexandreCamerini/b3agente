// Fase 46 (plano 46-06, CART6-02) — guardião estático do card ABERTO v6.
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

const seletor = semCom(functionBody("SeletorFace"));
const flip = semCom(functionBody("AreaFlip"));
const faceAcao = semCom(functionBody("FaceAcao"));
const bloco = semCom(functionBody("BlocoBorisIA"));
const opcoes = semCom(functionBody("CardPosicaoEstruturada"));
const cartao = semCom(functionBody("CartaoPosicao"));
const tela = semCom(functionBody("CarteiraScreen"));

// --- existência e ordem (D-14) ----------------------------------------------
const idx = (n) => src.indexOf(`function ${n}(`);
for (const n of ["SeletorFace", "AreaFlip", "FaceAcao", "BlocoBorisIA"]) {
  ok(`${n} existe e fica antes de LinhaChamadaOpcoes`, idx(n) > 0 && idx(n) < idx("LinhaChamadaOpcoes"));
}
ok("CardPosicaoEstruturada mantém o nome (1 definição)", (src.match(/^function CardPosicaoEstruturada\(/gm) || []).length === 1);

// --- seletor ----------------------------------------------------------------
ok("SeletorFace: role=group com aria-label face_grupo_aria", /role="group"/.test(seletor) && /"face_grupo_aria"/.test(seletor));
ok("SeletorFace: aria-pressed e minHeight 44", /aria-pressed=\{sel\}/.test(seletor) && /minHeight:\s*44\b/.test(seletor));

// --- flip -------------------------------------------------------------------
ok("AreaFlip lê flipDuracaoMs(prefereMovimentoReduzido(window)) na troca", /flipDuracaoMs\(prefereMovimentoReduzido\(window\)\)/.test(flip));
ok("AreaFlip não usa a constante REDUCE_MOTION (lida só no carregamento)", !/REDUCE_MOTION/.test(flip));
ok("AreaFlip: movimento reduzido (total 0) troca sem timer", /d\.total === 0/.test(flip));
ok("AreaFlip: trava busy, limpa timers no unmount", /busyRef/.test(flip) && /clearTimeout/.test(flip));
ok("AreaFlip: só monta a face exibida (render(est.exibida), sem display none)", /render\(est\.exibida\)/.test(flip) && !/display:\s*"none"/.test(flip));
ok("AreaFlip: 170+170 vêm de flipDuracaoMs (sem ms literais)", !/setTimeout\([^)]*,\s*\d+\)/.test(flip));
ok("CartaoPosicao: face inicial via faceInicial(", /faceInicial\(/.test(cartao));
ok("CartaoPosicao: seletor só com pernas (nPernas > 0)", /nPernas > 0/.test(cartao) && /<SeletorFace/.test(cartao) && /<AreaFlip/.test(cartao));

// --- FaceAcao ---------------------------------------------------------------
ok("FaceAcao: R:R do backend (L.rr), sem recalcular", /L\.rr != null/.test(faceAcao) && !/valorRR\(|mostraRR\(/.test(faceAcao));
ok("FaceAcao: gatilho vem de gatilhoStatus (sem comparar invalidacao no front)", /gatilhoStatus/.test(faceAcao) && !/invalidacao\s*[<>]|[<>]\s*se\.invalidacao/.test(faceAcao));
ok("FaceAcao: nota de PM do backend (notaPm)", /L\.notaPm/.test(faceAcao));
ok("FaceAcao: compras com aria-expanded e totalDaCompra", /aria-expanded=\{comprasAberto\}/.test(faceAcao) && /totalDaCompra\(/.test(faceAcao));
ok("FaceAcao: sem hex literal", !/#[0-9a-fA-F]{3,6}\b/.test(faceAcao));

// --- BlocoBorisIA -----------------------------------------------------------
const botaoPlano = /<button[^>]*onClick=\{\(\) => ctx\.openStopAlvo\(p\.t\)\}[^>]*>/.exec(bloco);
ok("BlocoBorisIA: botão de plano chama ctx.openStopAlvo(", !!botaoPlano);
ok("BlocoBorisIA: botão de plano SEM aria-disabled/disabled (stop/alvo nunca vetados)", !!botaoPlano && !/disabled/.test(botaoPlano[0]) && !/disabled/.test(bloco.slice(bloco.indexOf("openStopAlvo") - 80, bloco.indexOf("openStopAlvo") + 400).split("</button>")[0]));
ok("BlocoBorisIA: reanalisar chama ctx.openAvaliar(", /ctx\.openAvaliar\(p\.t\)/.test(bloco));
ok("BlocoBorisIA: saída usa qtyLivre(p) === 0, aria-disabled, aria-describedby e saida_motivo_lastro", /qtyLivre\(p\) === 0/.test(bloco) && /aria-disabled=/.test(bloco) && /aria-describedby=\{semLivres/.test(bloco) && /"saida_motivo_lastro"/.test(bloco));
ok("BlocoBorisIA: saída sem livres não abre o modal (onClick undefined)", /semLivres \? undefined : \(\) => ctx\.A\.openSell\(p\.t\)/.test(bloco));
ok("BlocoBorisIA: sem disabled= na fatia", !/(?<![-\w])disabled=/.test(bloco));
ok("BlocoBorisIA: rótulos plano_ia_definir/completar/ajustar", /plano_ia_definir/.test(bloco) && /plano_ia_completar/.test(bloco) && /plano_ia_ajustar/.test(bloco));
ok("SellModal mostra apoio_saida", /"apoio_saida"/.test(semCom(functionBody("SellModal"))));

// --- face Opções (evolução da 45) ------------------------------------------
ok("Opções: Encerrar com aria-describedby e goOpcoes('oportunidades'", /aria-describedby=\{motivoEncerrar/.test(opcoes) && /ctx\.goOpcoes\("oportunidades"/.test(opcoes));
ok("Opções: caixa sem_cenario e ponto de montagem data-area-cenario", /"sem_cenario"/.test(opcoes) && /data-area-cenario/.test(opcoes));
ok("Opções: linha de fonte + origem_nao_informada + atualizar", /"origem_nao_informada"/.test(opcoes) && /"atualizar"/.test(opcoes) && /<BotaoAtualizarEstrutura/.test(opcoes));

// --- CarteiraScreen sem corpo antigo ---------------------------------------
ok("CarteiraScreen sem corpo legado (POSIÇÃO NO RISCO, btnVender, disabled=)", !/POSIÇÃO NO RISCO/.test(tela) && !/btnVender/.test(tela) && !/(?<![-\w])disabled=/.test(tela));

// --- sem hex literal em todo o bloco v6 ------------------------------------
const a = src.indexOf("function ReguaPlano("), b = src.indexOf("function LinhaChamadaOpcoes(");
ok("sem hex literal de ReguaPlano a LinhaChamadaOpcoes", a > 0 && b > a && !/#[0-9a-fA-F]{3,6}\b/.test(semCom(src.slice(a, b))));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
