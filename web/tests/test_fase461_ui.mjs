// Guardião não se apaga — fiação da Fase 46.1 no App.jsx (G-07, G-08, AL-02, MD-05).
// Origem: 46.1-04 (2026-10-02). Lê App.jsx como TEXTO. Roda: `node web/tests/test_fase461_ui.mjs`.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { cartaoPosicaoTxt, cartaoDidaticaTxt } from "../src/copy.js";

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

const tela = functionBody("CarteiraScreen");
const hook = functionBody("useLeiturasPlano");
const cartao = functionBody("CartaoPosicao");
const linhas = functionBody("LinhasResultadoV6");

ok("corpos recortados", tela && hook && cartao && linhas);
ok("CarteiraScreen usa nomeEmpresaCard( e situacaoLeituraPlano(", /nomeEmpresaCard\(/.test(tela) && /situacaoLeituraPlano\(/.test(tela));
ok("CarteiraScreen não repassa mais q.name cru", !/q\.name \? q\.name : null/.test(tela));
ok("hook: tentarDeNovo, _sigPos, _lidaEm e tentativa nas deps", /tentarDeNovo/.test(hook) && /_sigPos/.test(hook) && /_lidaEm/.test(hook) && /\[assinatura, escopoSeq, tentativa\]/.test(hook));
ok("hook sem retry automático (sem setInterval/setTimeout)", !/setInterval|setTimeout/.test(hook));
for (const k of ['res.chipCabecalho', '"leitura_falhou"', '"leitura_desatualizada"', '"tentar_de_novo"', 'onTentarPlano', 'estruturaPendente']) {
  ok("CartaoPosicao contém " + k, cartao.includes(k));
}
ok("CartaoPosicao sem disabled=", !/disabled=/.test(cartao));
ok("LinhasResultadoV6 renderiza notas", /notas/.test(linhas) && /n\.chave/.test(linhas));
ok("sem dangerouslyDisableSetInnerHTML nos trechos", !/dangerouslySetInnerHTML/.test(cartao + linhas));

const CHAVES = ["motivo_lendo", "motivo_leitura_indisponivel", "chip_desatualizado", "tentar_de_novo", "legenda_resultado_so_acoes",
  "leitura_falhou", "leitura_desatualizada", "causa_sem_cotacao", "causa_fora_da_cadeia", "causa_sem_negocio", "causa_fonte_indisponivel", "payoff_aria_teto_parcial"];
for (const modo of ["estudo", "operador"]) {
  for (const k of CHAVES) ok(`copy ${modo}.${k}`, typeof cartaoPosicaoTxt(modo, k) === "string");
}
for (const k of ["caso_equilibrio_collar", "caso_equilibrio_collar_sem_hoje"]) ok("didática " + k, typeof cartaoDidaticaTxt(k) === "string");

if (fails) { console.log(fails + " falha(s)"); process.exit(1); }
console.log("OK test_fase461_ui");
