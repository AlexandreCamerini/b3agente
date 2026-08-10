// Reporte do Alex (09/08/2026), dois defeitos no chat do FAB:
//   1. a resposta do Boris aparecia sem formatação (markdown cru na bolha);
//   2. usar o chat "desconfigurava o tamanho da tela do app".
//
// (2) não era do chat: o iOS dá zoom ao focar campo com fonte < 16px e NÃO
// desfaz ao sair. Existia regra global `.b3 input… { font-size:16px }`, mas
// `style={{fontSize:"12px"}}` inline vence a folha de estilo — a regra estava
// escrita e derrotada em quase todo campo do app.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const chat = readFileSync(join(here, "..", "src", "pet", "BorisChat.jsx"), "utf8");
const md = readFileSync(join(here, "..", "src", "markdown.jsx"), "utf8");
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

// --- 1. markdown na conversa -------------------------------------------------
ok("markdown mora em módulo próprio (chat não pode importar de App.jsx)",
  /export function Markdown\(\{ text \}\)/.test(md) && /export function MdInline/.test(md));
ok("App.jsx passa a importar o renderizador em vez de defini-lo",
  /import \{ Markdown, MdInline \} from "\.\/markdown\.jsx"/.test(app)
  && !/^function Markdown\(\{ text \}\)/m.test(app));
ok("chat importa o MESMO renderizador da análise",
  /import \{ Markdown \} from "\.\.\/markdown\.jsx"/.test(chat));
ok("resposta do Boris é renderizada, fala do usuário fica literal",
  /m\.papel === "boris" \? <Markdown text=\{m\.texto\} \/> : m\.texto/.test(chat));
ok("pre-wrap só na fala do usuário (senão o markdown não quebra em blocos)",
  /whiteSpace: m\.papel === "usuario" \? "pre-wrap" : "normal"/.test(chat));

// --- 2. quem responde --------------------------------------------------------
ok("a bolha do Boris se identifica", /BORIS/.test(chat));
ok("resposta da base do app é distinguida da resposta de IA",
  /da base do app/.test(chat) && /Conteúdo educacional de IA/.test(chat));

// --- 3. a tela não pode ser reescalada pelo teclado ---------------------------
ok("campo do chat com 16px (não dispara o zoom do iOS)",
  /fontSize: "16px", resize: "vertical"/.test(chat));
ok("regra global vence o fontSize inline em tela de toque",
  /@media \(pointer: coarse\)\{[\s\S]{0,160}font-size:16px !important/.test(app));
ok("viewport segue permitindo pinch-zoom (nada de maximum-scale)", (() => {
  const html = readFileSync(join(here, "..", "index.html"), "utf8");
  return !/maximum-scale|user-scalable\s*=\s*no/.test(html);
})());

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
