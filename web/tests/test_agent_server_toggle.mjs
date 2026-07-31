// FASE 6 (fix 3) — Guardião: "Ativar no servidor" (Operador IA) ponta a ponta.
//
// BUG que motivou este teste: no iPhone (deviceStore), putAgent tratava só
// autonomous/allocPct/intervalMin — `serverEnabled` e demais parâmetros do
// Operador NO SERVIDOR eram DESCARTADOS em silêncio; o toggle nunca chegava
// ao backend. E no App.jsx, A.putAgent aplicava o patch OTIMISTA e engolia o
// erro — a UI mostrava "ligado" sem o servidor ter ligado (estado fantasma).
// Roda sem build: `node web/tests/test_agent_server_toggle.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

// ---- deviceStore.putAgent encaminha os parâmetros do SERVIDOR --------------
const dev = bodyOf(pers, "async putAgent(b)");
ok("deviceStore.putAgent localizado", !!dev);
// A asserção checa CHAVE A CHAVE, não a string literal da lista: antes, só
// reformatar a linha (ou acrescentar uma chave no meio) quebrava o teste sem
// que nada do contrato tivesse mudado. F2 acrescentou trailingMode/AtrMult/
// Lookback — sem elas na lista, o usuário não consegue escolher o critério.
ok("deviceStore encaminha os parâmetros do servidor via api.putAgent",
  !!dev && ["serverEnabled", "mode", "rules", "trailingPct", "trailingMode",
            "trailingAtrMult", "trailingLookback", "maxOpsDia", "maxValorOp",
            "intervalMin", "lastSeenAt"].every((k) => dev.includes(`"${k}"`))
        && dev.includes("api.putAgent(sb)"));
ok("deviceStore exige sessão para ligar o servidor",
  !!dev && dev.includes("sync.hasSession()") && dev.includes("Entre na sua conta"));
ok("deviceStore espelha a resposta confirmada no doc local",
  !!dev && /for \(const k of SERVER_KEYS\) if \(k in ag\) doc\.agent\[k\] = ag\[k\];/.test(dev));

// ---- serverStore: flag de servidor segue no caminho LIVE (sem outbox) ------
ok("serverStore mantém serverEnabled no caminho live",
  /putAgent:\s*\(b\)\s*=>\s*\("serverEnabled" in \(b \|\| \{\}\)\)\s*\?\s*sync\.live/.test(pers));

// ---- A.putAgent: serverEnabled sem otimismo e com erro propagado -----------
const aPut = bodyOf(app, "putAgent: async (patch) =>");
ok("A.putAgent localizado", !!aPut);
ok("A.putAgent NÃO aplica otimista quando serverEnabled",
  !!aPut && aPut.includes('("serverEnabled" in patch)') && /if \(!liveFlag\) setData/.test(aPut));
ok("A.putAgent propaga o erro do caminho live (sem engolir)",
  !!aPut && /if \(liveFlag\) throw e;/.test(aPut));

// ---- a tela confirma com o status real do servidor -------------------------
ok("setServer reconfirma via loadSrv após o toggle", /await A\.putAgent\(\{ serverEnabled: on \}\);\s*\n?\s*await loadSrv\(\);/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
