// Fase 38 (38-02) — guardião da extração de web/src/entendimento.jsx.
//
// Contratos travados:
//  (a) entendimento.jsx exporta ConceitoSheet, SetorAlvo, AssistenteBox,
//      AiNote, SUBLINHADO.
//  (b) entendimento.jsx não importa App.jsx nem OpcoesScreen.jsx — seria
//      ciclo e quebraria o isolamento do ADR-027 (T-38-06).
//  (c) todo `T.<chave>` usado em entendimento.jsx está declarado no próprio
//      array TOKENS — o defeito calado que a Fase 35 achou em
//      SecaoVigias.jsx (token fora do array vira `undefined` em silêncio).
//  (d) App.jsx não define mais nenhum dos 7 símbolos e importa de
//      "./entendimento.jsx".
//  (e) opcoes/OpcoesScreen.jsx continua sem importar App.jsx.
//  (f) prova negativa de (c): injetar `T.tokenInexistente` numa cópia em
//      memória do módulo faz a checagem acusar exatamente 1 faltante — sem
//      isso, um bug na função de checagem passaria os dois lados do
//      contrato em silêncio (padrão de
//      test_kb.py::test_negacao_detecta_a_forma_permitida_e_a_proibida).
//
// Roda sem build: `node web/tests/test_entendimento_modulo.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const ent = readFileSync(join(here, "..", "src", "entendimento.jsx"), "utf8");
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const opcoesScreen = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------- (a) exports
ok("entendimento.jsx exporta ConceitoSheet",
   /^export function ConceitoSheet\(/m.test(ent));
ok("entendimento.jsx exporta SetorAlvo",
   /^export function SetorAlvo\(/m.test(ent));
ok("entendimento.jsx exporta AssistenteBox",
   /^export function AssistenteBox\(/m.test(ent));
ok("entendimento.jsx exporta AiNote",
   /^export const AiNote = /m.test(ent));
ok("entendimento.jsx exporta SUBLINHADO",
   /^export const SUBLINHADO = /m.test(ent));

// ------------------------------------------------------- (b) sem ciclo
ok("entendimento.jsx não importa App.jsx",
   !/from ["'][^"']*App\.jsx["']/.test(ent));
ok("entendimento.jsx não importa OpcoesScreen.jsx",
   !/from ["'][^"']*OpcoesScreen\.jsx["']/.test(ent));

// ---------------------------------------------- (c)/(f) tokens declarados
// Extrai as chaves usadas como `T.chave` e as declaradas no array TOKENS;
// devolve a lista de faltantes (usadas mas não declaradas).
function tokensFaltantes(fonte) {
  const usadas = new Set([...fonte.matchAll(/\bT\.([a-zA-Z0-9]+)/g)].map((m) => m[1]));
  const mDecl = fonte.match(/const TOKENS = \[([^\]]*)\]/);
  const declaradas = new Set(
    mDecl ? [...mDecl[1].matchAll(/"([a-zA-Z0-9]+)"/g)].map((m) => m[1]) : []
  );
  return [...usadas].filter((k) => !declaradas.has(k));
}

const faltantesReal = tokensFaltantes(ent);
if (faltantesReal.length) console.error("tokens faltantes em entendimento.jsx:", faltantesReal);
ok("todo T.<chave> usado em entendimento.jsx está no array TOKENS do próprio arquivo",
   faltantesReal.length === 0);

// (f) prova negativa: injeta um uso de token inexistente numa cópia em
// memória e confirma que a checagem acusa exatamente 1 faltante.
const entComDefeito = ent.replace(
  "export const AiNote = ",
  "const _provaNegativa = T.tokenInexistente;\nexport const AiNote = "
);
const faltantesDefeito = tokensFaltantes(entComDefeito);
ok("prova negativa: token inexistente injetado é detectado (exatamente 1 faltante)",
   faltantesDefeito.length === 1 && faltantesDefeito[0] === "tokenInexistente");

// --------------------------------------------- (d) App.jsx não define mais
ok("App.jsx não define mais ConceitoSheet/SetorAlvo/AssistenteBox/AiNote/SUBLINHADO/SR_ONLY/CONCEITO_BLOCOS",
   !/^(export )?function (ConceitoSheet|SetorAlvo|AssistenteBox)\(/m.test(app)
   && !/^(export )?const (AiNote|SUBLINHADO|SR_ONLY|CONCEITO_BLOCOS) = /m.test(app));
ok("App.jsx importa de ./entendimento.jsx",
   /from ["']\.\/entendimento\.jsx["']/.test(app));

// ------------------------------------------ (e) isolamento preservado
ok("opcoes/OpcoesScreen.jsx continua sem importar App.jsx",
   !/from ["'][^"']*App\.jsx["']/.test(opcoesScreen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
