// Guardião do card de posição enxuto (quick 261013-29f, opção A).
// Guardião não se apaga; reversão deliberada atualiza com nota.
// Lê App.jsx como TEXTO e trava a estrutura do corpo aberto: Evolução antes do
// Plano, sem linhas Stop/Alvo, Ajustar na régua, Compras/Análises recolhidas,
// Fechar no fim, cabeçalho sticky, folga do FAB e copy nova nos dois modos.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { COPY, cartaoPosicaoTxt } from "../src/copy.js";

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

const face = semCom(functionBody("FaceAcao"));
const cartao = semCom(functionBody("CartaoPosicao"));
const bloco = semCom(functionBody("BlocoBorisIA"));
const compras = semCom(functionBody("DetalheCompras"));
const chipEstado = semCom(functionBody("ChipEstadoV6"));
const pet = semCom(functionBody("PetFab"));

// 1. recortes não vazios
for (const [n, b] of [["FaceAcao", face], ["CartaoPosicao", cartao], ["BlocoBorisIA", bloco], ["DetalheCompras", compras], ["ChipEstadoV6", chipEstado]]) {
  ok(`recorte ${n} não vazio (> 200 caracteres)`, b.length > 200);
}

const ix = (s, t) => (t instanceof RegExp ? s.search(t) : s.indexOf(t));
const antes = (s, a, b) => { const ia = ix(s, a), ib = ix(s, b); return ia >= 0 && ib >= 0 && ia < ib; };

// 2. Evolução antes do Plano; régua só sem estrutura
const iEvo = ix(face, '"evolucao_titulo"');
const iPlano = ix(face, '"plano_titulo"');
const iRegua = ix(face, "<ReguaPlano p={p}");
ok("FaceAcao: evolucao_titulo antes de plano_titulo", iEvo >= 0 && iPlano > iEvo);
ok("FaceAcao: <ReguaPlano entre Evolução e Plano", iRegua > iEvo && iRegua < iPlano);
ok("FaceAcao: ReguaPlano guardada por !comEstrutura", /!comEstrutura && [^]*?<ReguaPlano/.test(face) || /comEstrutura \?[^]*?<ReguaPlano/.test(face));
ok("FaceAcao: com estrutura mostra stop/alvo em texto (rsNbsp(p.stop)/rsNbsp(p.alvo))", /rsNbsp\(p\.stop\)/.test(face) && /rsNbsp\(p\.alvo\)/.test(face));

// 3. par PM -> atual
ok("FaceAcao: preco_medio e cotacao_atual antes da régua", antes(face, '"preco_medio"', "<ReguaPlano") && antes(face, '"cotacao_atual"', "<ReguaPlano"));
ok("FaceAcao: valores via rsNbsp(p.avg) e rsNbsp(L.preco) com fallback —", /rsNbsp\(p\.avg\)/.test(face) && /rsNbsp\(L\.preco\)/.test(face) && /"—"/.test(face));
ok("FaceAcao: par PM -> atual e chip_qtd sob !comEstrutura", /!comEstrutura && [^]*?"preco_medio"/.test(face) && /!comEstrutura && [^]*?"chip_qtd"/.test(face));

// 4. sem linhas Stop/Alvo; sem botão largo
ok("FaceAcao: sem linha(\"stop\" e sem linha(\"alvo\"", !/linha\("stop"/.test(face) && !/linha\("alvo"/.test(face));
ok("App.jsx sem \"editar_plano\"", !/"editar_plano"/.test(src));

// 5. Ajustar / Falta definir (stop/alvo nunca vetados)
ok("FaceAcao: ajustar_plano com onClick={onEditarPlano} e aria-label ajustar_plano_aria",
  /"ajustar_plano"/.test(face) && /onClick=\{onEditarPlano\}/.test(face) && /aria-label=\{cartaoPosicaoTxt\(modo, "ajustar_plano_aria"/.test(face));
ok("FaceAcao: falta_definir presente e nenhum disabled", /"falta_definir"/.test(face) && !/disabled/.test(face));

// 6. editor colado na régua
ok("FaceAcao: {editorPlano} depois de <ReguaPlano e antes de plano_titulo", iRegua > 0 && ix(face, "{editorPlano}") > iRegua && ix(face, "{editorPlano}") < iPlano);

// 7. chips da Evolução
const trechoEvo = iEvo >= 0 && iPlano > iEvo ? face.slice(iEvo, iPlano) : "";
ok("FaceAcao: chips (<ChipEstadoV6, chip_qtd, em_operacao, do_capital) entre Evolução e Plano",
  ["<ChipEstadoV6", '"chip_qtd"', '"em_operacao"', '"do_capital"'].every((t) => trechoEvo.includes(t)));
ok("FaceAcao: <ChipEstadoV6 sob !comEstrutura", /!comEstrutura && <ChipEstadoV6/.test(face));
ok("FaceAcao: sem linha(\"dias\" nem linha(\"cap\"; não recebe mais simples", !/linha\("dias"/.test(face) && !/linha\("cap"/.test(face) && !/\bsimples\b/.test(face));

// 7b. uma fonte só
ok("CartaoPosicao: pctCapital: e || aberto ? null : pctCap", /pctCapital: e \|\| aberto \? null : pctCap/.test(cartao));
ok("CartaoPosicao: const mostraResumo = !aberto || !!e e <ChipsMetaV6 dentro de mostraResumo &&", /const mostraResumo = !aberto \|\| !!e/.test(cartao) && /mostraResumo && [^]*?<ChipsMetaV6/.test(cartao));
ok("CartaoPosicao: passa comEstrutura={!!e} à FaceAcao", /comEstrutura=\{!!e\}/.test(cartao));

// 7c. troca de face fecha o editor
ok("CartaoPosicao: troca de face fecha o editor", /if \(f !== "acao" && editAberto\) onEditar\(\)/.test(cartao));

// 8. Plano enxuto
const trechoPlano = iPlano >= 0 ? face.slice(iPlano) : "";
ok("FaceAcao: Plano só com linha(\"rr\" e linha(\"setup\"",
  /linha\("rr"/.test(trechoPlano) && /linha\("setup"/.test(trechoPlano) && !/linha\("cot"/.test(face) && !/linha\("stop"/.test(face));

// 9. setup sem MONO
const iSetup = face.indexOf('linha("setup"');
const trechoSetup = iSetup >= 0 ? face.slice(iSetup, face.indexOf("))}", iSetup) + 3) : "";
const iNome = trechoSetup.indexOf('{se.setup || "—"}');
const abreB = trechoSetup.lastIndexOf("<b", iNome);
const elNome = iNome >= 0 && abreB >= 0 ? trechoSetup.slice(abreB, iNome) : "";
// 2026-10-13 (quick 261013-29f, orquestrador): 600 -> 400. O card v6 só aceita pesos 400/700
// (test_cartao_v6_transversal); o destaque do setup vem da cor/tamanho, não de um peso fora do sistema.
ok("FaceAcao: nome do setup em fonte de texto, fontWeight 400, sem MONO", /fontWeight:\s*400/.test(elNome) && !/MONO/.test(elNome) && !/\.\.\.valor/.test(trechoSetup));
ok("FaceAcao: span externo do setup sem MONO/...valor", trechoSetup.length > 0 && !/\.\.\.valor/.test(trechoSetup) && !/fontFamily:\s*MONO[^]*?\{se\.setup/.test(trechoSetup));

// 10. Compras foi para DetalheCompras
ok("FaceAcao: sem comprasAberto/totalDaCompra/L.notaPm", !/comprasAberto/.test(face) && !/totalDaCompra/.test(face) && !/L\.notaPm/.test(face));
ok("DetalheCompras: disclosure completo", /aria-expanded=\{aberto\}/.test(compras) && /aria-controls=/.test(compras) && /totalDaCompra\(/.test(compras) && /L\.notaPm/.test(compras) && /"compras_titulo"/.test(compras));

// 11. BlocoBorisIA sem histórico
ok("BlocoBorisIA: sem historico/histAberto/onHist", !/"historico"/.test(bloco) && !/histAberto/.test(bloco) && !/onHist/.test(bloco));

// 12. ordem no corpo e rodapé único
const iCorpo = ix(cartao, "id={idCorpo}");
const iRodape = ix(cartao, "aria-controls={idCorpo}");
ok("CartaoPosicao: BlocoBorisIA < DetalheCompras < análises < rodapé",
  ix(cartao, "<BlocoBorisIA") >= 0 && antes(cartao, "<BlocoBorisIA", "<DetalheCompras") && antes(cartao, "<DetalheCompras", "aria-expanded={histAberto}") && antes(cartao, "aria-expanded={histAberto}", '"historico"') && antes(cartao, '"historico"', "aria-controls={idCorpo}"));
ok("CartaoPosicao: corpo (id={idCorpo}) antes do botão (aria-controls)", iCorpo >= 0 && iRodape > iCorpo);
ok("CartaoPosicao: um só aria-controls={idCorpo}", (cartao.match(/aria-controls=\{idCorpo\}/g) || []).length === 1);

// 13. resumo condicional
ok("CartaoPosicao: {e ? <FaixaVencimento dentro de mostraResumo &&", /mostraResumo && [^]*?\{e \? <FaixaVencimento/.test(cartao));

// 14. sticky
ok("CartaoPosicao: cabeçalho sticky quando aberto, top 0, overflowAnchor none", /position: aberto \? "sticky"/.test(cartao) && /top: 0/.test(cartao) && /overflowAnchor: "none"/.test(cartao));

// 15. folga do FAB
ok("App.jsx: constantes do FAB e FOLGA_FAB_PET", /const FAB_PET_BOTTOM = 92\b/.test(src) && /const FAB_PET_ALTURA = 54\b/.test(src) && /const FOLGA_FAB_PET = FAB_PET_BOTTOM \+ FAB_PET_ALTURA \+ SP\[3\]/.test(src));
ok("CartaoPosicao usa FOLGA_FAB_PET", /FOLGA_FAB_PET/.test(cartao));
ok("PetFab ainda tem bottom 92px e height 54px (espelho das constantes)", /bottom: "92px"/.test(pet) && /height: "54px"/.test(pet));

// 16. copy
const NOVAS = ["evolucao_titulo", "preco_medio", "regua_titulo", "ajustar_plano", "ajustar_plano_aria", "chip_qtd"];
for (const k of NOVAS) {
  const a = cartaoPosicaoTxt("estudo", k, { ticker: "X", qty: "1" });
  const b = cartaoPosicaoTxt("operador", k, { ticker: "X", qty: "1" });
  ok(`copy: ${k} não vazia e igual nos dois modos`, typeof a === "string" && a.length > 0 && a === b);
}
for (const m of ["estudo", "operador"]) {
  ok(`copy ${m}: editar_plano removida`, COPY[m].cartaoPosicao.editar_plano === undefined);
  ok(`copy ${m}: historico = "Análises do Bóris (2)"`, cartaoPosicaoTxt(m, "historico", { n: 2 }) === "Análises do Bóris (2)");
}

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
