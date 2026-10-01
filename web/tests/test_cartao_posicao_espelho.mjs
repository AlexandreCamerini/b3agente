// GUARDIÃO DE PARIDADE — vocabulário do card de posição v6 (Fase 46, CART6-06/07).
// Guardião não se apaga: reversão deliberada atualiza este arquivo com nota.
//
// `skill_ref.CARTAO_POSICAO` / `CARTAO_DIDATICA` são a fonte única; o espelho é
// `COPY[modo].cartaoPosicao` e `COPY.estudo.cartaoDidatica` (web/src/copy.js),
// byte a byte. Lê o .py como TEXTO (nunca importa Python). Trava também: mesmo
// conjunto de chaves nos dois modos, igualdade Estudo=Operador das neutras,
// vocabulário proibido no Estudo (T-46-02) e semântica dos helpers.
// Roda isolado: `node web/tests/test_cartao_posicao_espelho.mjs`.
// Override do fonte Python por B3_SKILL_REF_PATH (só para sabotagem controlada).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { COPY, cartaoPosicaoTxt, cartaoDidaticaTxt } from "../src/copy.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

const caminhoSkillRef = process.env.B3_SKILL_REF_PATH
  ? process.env.B3_SKILL_REF_PATH
  : fileURLToPath(new URL("../../server/app/skill_ref.py", import.meta.url));
let src = "";
try {
  src = readFileSync(caminhoSkillRef, "utf8");
} catch (e) {
  ok(`skill_ref.py legível em ${caminhoSkillRef}`, false, e.message);
}
ok("skill_ref.py não vazio", src.length > 0);

function blocoDoDict(s, nome) {
  const m = s.match(new RegExp("^" + nome + " = \\{([\\s\\S]*?)^\\}", "m"));
  return m ? m[1] : null;
}
function blocoDoModo(bloco, modo) {
  const m = bloco.match(new RegExp('"' + modo + '":\\s*\\{([\\s\\S]*?)\\n\\s*\\},'));
  return m ? m[1] : null;
}
function paresDoModo(modoSrc) {
  const pares = {};
  const re = /"([a-zA-Z_]+)":\s*"([^"]*)"/g;
  let m;
  while ((m = re.exec(modoSrc))) pares[m[1]] = m[2];
  return pares;
}

const MODO_JS = { educacional: "estudo", operador: "operador" };
const PROIBIDO = /\bcomprar\b|\bvender\b|trava protetora|abate o custo|\bgarante|\bcerto\b|\bsempre\b/i;
const ANCORAS = /trava(\(s\))?\s+protetora|abate\s+o\s+custo/i;

// Chaves neutras (UI-SPEC "Neutras"): texto idêntico nos dois modos.
const NEUTRAS = [
  "face_acao", "face_opcoes", "face_grupo_aria", "plano_titulo",
  "compras_titulo", "ver", "ocultar", "compras_indisponivel",
  "compras_sem_detalhe", "falta_definir", "estado_sem_plano", "estado_falta_alvo",
  "estado_falta_stop", "estado_abaixo_stop", "estado_acima_alvo", "estado_dentro",
  "estado_travadas_todas", "estado_travadas_parcial", "extra_resultado_parcial", "extra_cotacao_indisponivel",
  "plano_ia_definir", "plano_ia_completar", "plano_ia_ajustar", "reanalisar",
  "historico", "kicker_ia", "encerrar", "atualizar",
  "origem_nao_informada", "sem_cenario", "conta_sem_formula", "aguardando_calculo",
  "piso", "equilibrio_rotulo", "teto", "sem_piso",
  "sem_teto", "agora", "hoje", "faixa_titulo",
  "chip_hoje", "chip_equilibrio", "chip_teto", "chip_alta_forte",
  "rr_atual", "em_operacao", "do_capital", "cotacao_atual",
  "setup_entrada", "gatilho_valido", "gatilho_invalidado", "nota_pm",
  "nota_pm_vendas", "editar_plano", "regua_aria", "faixa_aria",
  "leg_hoje", "leg_be", "leg_k", "leg_eixo",
  "cel_be", "cel_ate_be", "cel_ate_k", "cel_ganho_max",
  "cel_perda_max", "cel_lastro", "conta_be_call", "conta_ate_be",
  "conta_ate_k", "conta_ganho_call", "conta_perda_call", "conta_lastro",
  "sim_aria", "sim_valuetext", "payoff_sem_custos", "zona_rotulo_perda_travada",
  "zona_rotulo_prejuizo", "zona_rotulo_ganho", "zona_rotulo_ganho_travado", "saida_motivo_lastro",
  "rodape_fechar",
  // 46-UAT (2026-10-01, G-01..G-06): chaves do card fechado rótulo/valor
  "legenda_resultado", "legenda_resultado_variacao", "legenda_resultado_estrutura", "chip_total_suspenso",
  "linha_acoes", "linha_opcoes", "linha_estrutura", "motivo_premio_indisponivel",
  "motivo_dados_incompletos", "motivo_aguardando_premio", "motivo_aguardando_cotacao", "motivo_cotacao_indisponivel",
  "chip_acoes_pm", "chip_vence", "chip_plano", "chip_estrategia_generica",
  "faixa_rot_teto", "faixa_leg_hoje",
];

// --- (1) CARTAO_POSICAO <-> COPY[modo].cartaoPosicao
const blocoPos = src ? blocoDoDict(src, "CARTAO_POSICAO") : null;
ok('skill_ref.py: bloco "CARTAO_POSICAO = {...}" encontrado', !!blocoPos);
const paresPorModo = {};
for (const modoPy of ["operador", "educacional"]) {
  const modoJs = MODO_JS[modoPy];
  const pares = paresDoModo((blocoPos && blocoDoModo(blocoPos, modoPy)) || "");
  paresPorModo[modoPy] = pares;
  const objJs = (COPY[modoJs] && COPY[modoJs].cartaoPosicao) || {};
  const kPy = Object.keys(pares).sort().join(",");
  const kJs = Object.keys(objJs).sort().join(",");
  ok(`CARTAO_POSICAO["${modoPy}"] não vazio`, Object.keys(pares).length > 0);
  ok(`COPY.${modoJs}.cartaoPosicao: mesmo conjunto de chaves do .py`, kJs === kPy, `python={${kPy}} js={${kJs}}`);
  for (const [chave, valor] of Object.entries(pares)) {
    ok(`CARTAO_POSICAO["${modoPy}"].${chave} idêntico byte a byte`, objJs[chave] === valor,
       `python="${valor}" js="${objJs[chave]}"`);
  }
  ok(`COPY.${modoJs}.cartaoPosicao sem âncoras proibidas`, !ANCORAS.test(Object.values(objJs).join("\n")));
}
ok("CARTAO_POSICAO: mesmo conjunto de chaves nos dois modos",
   Object.keys(paresPorModo.operador).sort().join(",") === Object.keys(paresPorModo.educacional).sort().join(","));
ok("estudo.cartaoPosicao sem vocabulário proibido (T-46-02)",
   !PROIBIDO.test(Object.values(COPY.estudo.cartaoPosicao).join("\n")));

// --- (2) neutras idênticas
const E = COPY.estudo.cartaoPosicao, O = COPY.operador.cartaoPosicao;
for (const k of NEUTRAS) {
  ok(`neutra ${k} existe e é idêntica nos dois modos`,
     typeof E[k] === "string" && E[k].length > 0 && E[k] === O[k], `estudo=${E[k]} operador=${O[k]}`);
}
const ESPECIFICAS = ["rodape_abrir", "saida", "saida_sem_livres", "apoio_saida"];
for (const k of ESPECIFICAS) {
  ok(`${k} difere entre Estudo e Operador (muda só o registro)`, E[k] !== O[k] && E[k].length > 0 && O[k].length > 0);
}

// --- (3) CARTAO_DIDATICA <-> COPY.estudo.cartaoDidatica (só Estudo)
const blocoDid = src ? blocoDoDict(src, "CARTAO_DIDATICA") : null;
ok('skill_ref.py: bloco "CARTAO_DIDATICA = {...}" encontrado', !!blocoDid);
const paresDid = paresDoModo((blocoDid && blocoDoModo(blocoDid, "educacional")) || "");
const didJs = COPY.estudo.cartaoDidatica || {};
ok("CARTAO_DIDATICA só tem o modo educacional", !!blocoDid && !/"operador":/.test(blocoDid));
ok("COPY.operador não tem cartaoDidatica", COPY.operador.cartaoDidatica === undefined);
ok("COPY.estudo.cartaoDidatica: mesmo conjunto de chaves do .py",
   Object.keys(didJs).sort().join(",") === Object.keys(paresDid).sort().join(",") && Object.keys(paresDid).length > 0);
for (const [chave, valor] of Object.entries(paresDid)) {
  ok(`CARTAO_DIDATICA.${chave} idêntico byte a byte`, didJs[chave] === valor, `python="${valor}" js="${didJs[chave]}"`);
}
ok("estudo.cartaoDidatica sem vocabulário proibido (T-46-02)", !PROIBIDO.test(Object.values(didJs).join("\n")));
// Todo marcador [[id]] de parágrafo tem rótulo de termo correspondente.
for (const [k, v] of Object.entries(didJs)) {
  if (!k.startsWith("paragrafo_")) continue;
  for (const m of v.matchAll(/\[\[([a-z_]+)\]\]/g)) {
    ok(`${k}: marcador [[${m[1]}]] tem termo_${m[1]}`, typeof didJs["termo_" + m[1]] === "string");
  }
}

// --- (4) helpers
ok('cartaoPosicaoTxt("operador","rodape_abrir")', cartaoPosicaoTxt("operador", "rodape_abrir") === "Detalhes e ações ▾");
ok('cartaoPosicaoTxt("estudo","rodape_abrir")', cartaoPosicaoTxt("estudo", "rodape_abrir") === "Ver detalhes e aprender ▾");
ok("cartaoPosicaoTxt modo desconhecido cai no estudo", cartaoPosicaoTxt("xyz", "saida") === "Simular venda");
ok("cartaoPosicaoTxt operador saida", cartaoPosicaoTxt("operador", "saida") === "Registrar saída");
ok("cartaoPosicaoTxt interpola",
   cartaoPosicaoTxt("estudo", "estado_travadas_parcial", { n: "600", m: "1.000", k: "400" }) === "600 de 1.000 ações travadas · 400 livres");
ok("cartaoPosicaoTxt chave desconhecida -> null", cartaoPosicaoTxt("operador", "nao_existe") === null);
ok("cartaoDidaticaTxt chave desconhecida -> null", cartaoDidaticaTxt("nao_existe") === null);
ok("cartaoDidaticaTxt interpola", cartaoDidaticaTxt("caso_sem_piso", { perdaMaxima: "38.010,00" }) ===
   "Sem piso: se a ação fosse a zero, a perda seria de R$ 38.010,00.");

// --- (4b) 46-UAT (2026-10-01): card fechado rótulo/valor
ok("linha_opcoes interpola contrato", cartaoPosicaoTxt("estudo", "linha_opcoes", { contrato: "UGPAK422" }) === "Opções · UGPAK422");
ok("chip_acoes_pm interpola", cartaoPosicaoTxt("operador", "chip_acoes_pm", { qty: "1000", pm: "39,50" }) === "1000 ações · PM 39,50");
ok("faixa_rot_be estudo começa com '◆ equilíbrio'", cartaoPosicaoTxt("estudo", "faixa_rot_be", { v: "R$ 38,01" }).startsWith("◆ equilíbrio"));
ok("faixa_rot_be operador começa com '◆ BE'", cartaoPosicaoTxt("operador", "faixa_rot_be", { v: "R$ 38,01" }).startsWith("◆ BE"));
ok('linha_estrutura = "Estrutura" nos dois modos', E.linha_estrutura === "Estrutura" && O.linha_estrutura === "Estrutura");
ok("estado_travadas_todas (G-03) nos dois modos",
   E.estado_travadas_todas === "Ações travadas pela call · saída após encerrar" && O.estado_travadas_todas === E.estado_travadas_todas);

// --- (5) rótulo de encerrar (S13): v6 evolui o da Fase 45
ok("encerrar = 'Encerrar opção em Opções' nos dois modos", E.encerrar === "Encerrar opção em Opções" && O.encerrar === E.encerrar);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
