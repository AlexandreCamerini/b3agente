// qa/46 — reporte do Alex: a "análise completa" às vezes aparecia como JSON CRU
// (parse do servidor falhou, ou análise ANTIGA em cache). O cliente agora
// extrai o `corpo` do JSON no componente Markdown, cobrindo TODOS os casos.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const here = dirname(fileURLToPath(import.meta.url));
// 09/08/2026: `corpoDeJson`/`Markdown` saíram de `App.jsx` para `markdown.jsx`,
// para o chat do Boris poder usar o MESMO renderizador (ele não pode importar
// de `App.jsx` — import circular). A invariante guardada aqui é a blindagem
// contra JSON cru no render, não o arquivo onde ela mora.
const app = readFileSync(join(here, "..", "src", "markdown.jsx"), "utf8");
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

ok("corpoDeJson definido", /function corpoDeJson\(raw\)/.test(app));
ok("Markdown usa corpoDeJson (blindagem no render)", /const _t = corpoDeJson\(text\)/.test(app));
ok("extrai corpo/markdown/resumo do objeto", /obj\.corpo \|\| obj\.markdown \|\| obj\.resumo/.test(app));
ok("repara \\n/\\t crus dentro de string JSON", /out \+= "\\\\n"/.test(app) && /inStr/.test(app));
ok("só age quando parece JSON (não toca markdown limpo)", /startsWith\("\{"\) \|\| !\/"\(corpo\|markdown\|resumo/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
