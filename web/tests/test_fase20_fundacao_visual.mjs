// Guardião da Fase 20 (fundação estrutural, plano 20-01) — FIX-01/FIX-02/SYS-04.
//
// Por que existe: a Fase 20 é a fundação do redesenho v1.5 e as Fases
// 21/22/23 EDITAM O MESMO App.jsx (9k+ linhas). Sem trava, uma dessas fases
// reintroduz o vazamento horizontal sem ninguém perceber, porque o sintoma
// só aparece em viewport estreito (375px) — em desktop tudo parece normal.
//
// Os três defeitos originais foram medidos AO VIVO (não deduzidos por leitura
// de código), duas vezes: uma na auditoria que abriu esta fase (scrollWidth
// 504px vs clientWidth 375px do .b3-shell) e outra na execução deste plano
// (2026-09-05), que revisitou o palpite do UI-SPEC para FIX-02 e mediu a
// causa raiz real: o span raiz do MarketStatusBadge é inline-flex — caixa
// inline-level, que só encolhe quando um pai flex/grid impõe flex-basis; um
// <div> de bloco comum não faz isso, então o badge sempre renderizava na
// largura intrínseca do texto, ignorando minWidth:0 dos ancestrais. A
// correção real ficou dentro do próprio componente (maxWidth:"100%"), não só
// nos ancestrais — por isso este guardião trava as DUAS metades da correção.
//
// Roda sem build: `node web/tests/test_fase20_fundacao_visual.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raw = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Remove comentários de linha (//...) antes de contar ocorrências — o próprio
// código-fonte comenta as decisões desta fase em português e menciona os
// mesmos termos ("720px", "1060px", "CONTENT_MAX_WIDTH"); contagem crua se
// autoinvalida (comentário conta como "código" e infla o resultado).
function stripLineComments(src) {
  return src
    .split("\n")
    .map((line) => {
      const i = line.indexOf("//");
      return i >= 0 ? line.slice(0, i) : line;
    })
    .join("\n");
}
const code = stripLineComments(raw);

function count(re) {
  const m = code.match(re);
  return m ? m.length : 0;
}

// --- FIX-01: raiz não vaza horizontalmente -------------------------------
// A regra .b3-shell dentro de GlobalStyle() precisa declarar overflow-x:hidden
// NA MESMA regra (não é suficiente ter o overflow:"hidden" inline do elemento
// — a auditoria original mediu vazamento com ele já no lugar).
ok("FIX-01: .b3-shell tem overflow-x:hidden na própria regra CSS", /\.b3-shell\{[^}]*overflow-x:hidden[^}]*\}/.test(code));

// A medição ao vivo deste plano (2026-09-05) confirmou que <main> TAMBÉM
// vazava (scrollWidth > clientWidth), não só o shell — a contenção extra
// precisa sobreviver a qualquer edição futura de App.jsx.
ok("FIX-01: <main> tem overflowX:\"hidden\" no style inline", /<main[^>]*overflowX: "hidden"/.test(code) || /<main[^>]*overflowY: "auto", overflowX: "hidden"/.test(code));

// --- FIX-02: badge de status de mercado trunca em vez de empurrar --------
// Metade 1 (ancestrais): pelo menos DOIS containers "marginTop: "4px", minWidth: 0"
// envolvendo o MarketStatusBadge (Topbar já tinha; home foi corrigido nesta fase).
const marginTopMinWidth = count(/marginTop: "4px", minWidth: 0/g);
ok("FIX-02: pelo menos 2 call sites de MarketStatusBadge com minWidth:0 no pai (Topbar + home)", marginTopMinWidth >= 2);

// Metade 2 (o próprio componente): o span raiz do MarketStatusBadge precisa de
// maxWidth:"100%" — sem isso, minWidth:0 no ancestral NÃO fecha o defeito
// (inline-flex não encolhe sozinho; medição ao vivo confirmou isto).
ok("FIX-02: span raiz do MarketStatusBadge trava a própria largura (maxWidth:\"100%\")", /display: "inline-flex", alignItems: "center", gap: "6px", minWidth: 0, maxWidth: "100%"/.test(code));

// O rótulo em si continua truncando com reticência (não removido/alterado).
ok("FIX-02: span de rótulo do badge continua com textOverflow ellipsis", /textOverflow: "ellipsis"/.test(code));

// --- SYS-04: teto único de largura ----------------------------------------
const declCount = count(/const CONTENT_MAX_WIDTH\s*=\s*"720px";/g);
ok("SYS-04: exatamente UMA declaração de CONTENT_MAX_WIDTH = \"720px\"", declCount === 1);

const usageCount = count(/maxWidth: CONTENT_MAX_WIDTH/g);
ok("SYS-04: exatamente DUAS referências a maxWidth: CONTENT_MAX_WIDTH (BottomNav + wrapper de conteúdo)", usageCount === 2);

ok("SYS-04: não sobrou nenhum literal \"1060px\" no arquivo", count(/"1060px"/g) === 0);
ok("SYS-04: não sobrou nenhum literal maxWidth: \"720px\" solto (tudo passou pela constante)", count(/maxWidth: "720px"/g) === 0);

// --- Anti-regressão de escopo ----------------------------------------------
// A Fase 20 é proibida de introduzir Tailwind/shadcn/styled-components/
// CSS-in-JS (20-UI-SPEC.md) — o padrão do arquivo é 100% style inline + CSS
// puro em GlobalStyle(). Se alguém importar um desses, é fora de escopo.
ok("anti-regressão: nenhum import de Tailwind/shadcn/styled-components", !/from ["']tailwind|from ["']shadcn|from ["']styled-components/.test(code));

console.log(fails === 0 ? "\nOK — todas as asserções da Fase 20 (plano 20-01) passaram" : `\n${fails} asserção(ões) falharam`);
process.exit(fails);
