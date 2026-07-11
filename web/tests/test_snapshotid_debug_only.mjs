// qa/35 (P1) — Guardião: o snapshotId (hash do STU) NÃO aparece em nenhuma
// tela de consumo — só em Perfil → Logs & debug (LogsDebugScreen).
//
// BUG (F10 P1): o hash técnico vazava cru em 4+ superfícies de usuário —
// card do Radar ("· snapshot #hex"), chip da análise N2, popup de stop/alvo
// ("Análise baseada no snapshot #hex") e cards de posição (setupEntrada).
// Correção de produto: hash removido das telas; a rastreabilidade continua
// nos payloads/estado (persistência intacta) e é exibida SOMENTE na seção
// "SNAPSHOTS DAS ANÁLISES" do LogsDebugScreen.
// Roda sem build: `node web/tests/test_snapshotid_debug_only.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return { body: src.slice(m.index, i), start: m.index, end: i };
}

const logs = functionBody("LogsDebugScreen");
ok("LogsDebugScreen localizada", !!logs);

// 1) RENDER do hash: padrões de exibição ("#{...snapshotId}" / "snapshot #")
//    devem existir SOMENTE dentro do LogsDebugScreen.
const renderRe = /snapshot #|#\{[a-z0-9.]*snapshotId\}|·\s*#\{[a-z0-9.]*snapshotId\}/gi;
const hits = [];
let m2;
while ((m2 = renderRe.exec(src)) !== null) hits.push(m2.index);
const fora = logs ? hits.filter((i) => i < logs.start || i >= logs.end) : hits;
// linhas dos vazamentos (para a mensagem de falha apontar o lugar)
const lineOf = (idx) => src.slice(0, idx).split("\n").length;
ok(`render do hash SÓ no LogsDebugScreen (vazamentos fora: ${fora.length ? fora.map(lineOf).join(", ") : "nenhum"})`,
  fora.length === 0 && hits.length > 0);

// 2) A tela de debug tem a seção de rastreabilidade.
ok("LogsDebugScreen tem a seção SNAPSHOTS DAS ANÁLISES",
  !!logs && logs.body.includes("SNAPSHOTS DAS ANÁLISES") && /snapshot #\{r2\.id\}/.test(logs.body));

// 3) O fluxo de DADOS continua intacto (persistência/estado — não é UI):
//    o seed das análises e o retorno das rotas seguem carregando snapshotId.
ok("estado/persistência seguem carregando snapshotId (rastreabilidade viva)",
  (src.match(/snapshotId:\s*(a|r)\.snapshotId/g) || []).length >= 2);

// 4) O popup de stop/alvo mantém a DATA dos dados (informação útil ao usuário),
//    sem o hash.
ok("stop/alvo mostra a data dos dados (sem hash)",
  src.includes("Análise baseada nos dados de ") && !src.includes("Análise baseada no snapshot #"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
