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

// --- TYPO-01 (plano 20-02): dígitos de largura fixa em todo valor MONO ----
// A regra depende da string literal "ui-monospace" aparecer no atributo style
// que o React serializa — se alguém trocar o stack MONO por outro sem essa
// substring, o seletor de atributo deixa de casar em silêncio. O guardião
// trava as DUAS pontas do acoplamento: a regra CSS E a string da constante.
ok(
  "TYPO-01: GlobalStyle() tem a regra .b3 [style*=\"ui-monospace\"]{ font-variant-numeric: tabular-nums; }",
  /\.b3\s*\[style\*="ui-monospace"\]\s*\{\s*font-variant-numeric:\s*tabular-nums;\s*\}/.test(code)
);
ok(
  "TYPO-01: a constante MONO continua declarando o stack ui-monospace (acoplamento com o seletor de atributo acima)",
  /const MONO\s*=\s*"ui-monospace/.test(code)
);

// --- TYPO-02 (plano 20-02): escala numérica nomeada -----------------------
// Valores exatos aprovados na sessão de design da Fase 20 (20-CONTEXT.md):
// numHero 34/700, numBody 18/700, numMicro 13/600. As três nascem como
// objetos JS de só tamanho/peso (sem lineHeight/color/fontFamily), para
// spread livre em qualquer call site.
ok(
  "TYPO-02: numHero declarado com fontSize 34px e fontWeight 700",
  /const numHero\s*=\s*\{\s*fontSize:\s*"34px",\s*fontWeight:\s*700\s*\}/.test(code)
);
ok(
  "TYPO-02: numBody declarado com fontSize 18px e fontWeight 700",
  /const numBody\s*=\s*\{\s*fontSize:\s*"18px",\s*fontWeight:\s*700\s*\}/.test(code)
);
ok(
  "TYPO-02: numMicro declarado com fontSize 13px e fontWeight 600",
  /const numMicro\s*=\s*\{\s*fontSize:\s*"13px",\s*fontWeight:\s*600\s*\}/.test(code)
);
// numBody precisa de um consumidor real (patrimônio do Topbar) — sem isso as
// constantes nasceriam como código morto, contra o must_have do plano 20-02.
ok("TYPO-02: numBody tem pelo menos um consumidor real via spread (...numBody)", count(/\.\.\.numBody/g) >= 1);

// --- TYPO-03 (plano 20-03): Fredoka em todo H1 de tela --------------------
// Trava por IGUALDADE de contagem (não por número fixo), justamente para
// pegar um H1 NOVO introduzido por uma fase futura sem a fonte da marca
// (T-20-09 do threat model do plano 20-03) — se alguém adicionar uma tela
// nova sem fontFamily: DISPLAY no H1, a igualdade quebra e o teste falha.
const h1Count = count(/<h1[^>]*>/g);
const h1WithDisplay = count(/<h1[^>]*fontFamily: DISPLAY[^>]*>/g);
ok(
  `TYPO-03: todo <h1> do arquivo tem fontFamily: DISPLAY (${h1WithDisplay}/${h1Count} encontrados, esperado ≥15 e iguais)`,
  h1Count === h1WithDisplay && h1Count >= 15
);

// --- MOTION-03 (plano 20-03): gate abrangente de movimento reduzido ------
// Dois blocos @media (prefers-reduced-motion: reduce) precisam existir: o
// amplo (raiz + descendentes + troca de modo) e o estreito (as duas
// animações infinitas zeradas para "none", não para "0.01ms" — que
// produziria strobe, o oposto do que a preferência existe para evitar).
const reducedMotionCssBlocks = count(/@media \(prefers-reduced-motion: reduce\)\{/g);
ok(
  "MOTION-03: existem dois blocos @media (prefers-reduced-motion: reduce) em GlobalStyle()",
  reducedMotionCssBlocks === 2
);

ok(
  "MOTION-03: o bloco amplo lista .b3 (elemento raiz), não só .b3 *",
  /@media \(prefers-reduced-motion: reduce\)\{ \.b3, \.b3 \*/.test(code)
);
ok(
  "MOTION-03: o bloco amplo lista .b3-mode-switch e .b3-mode-switch \\*",
  /@media \(prefers-reduced-motion: reduce\)\{[^}]*\.b3-mode-switch, \.b3-mode-switch \*\{/.test(code)
);
ok(
  "MOTION-03: o bloco estreito com animation:none (ticker + spinner) continua existindo, não foi substituído por 0.01ms",
  /@media \(prefers-reduced-motion: reduce\)\{ \.b3 \.tt-track,\.b3 \.spin\{ animation:none !important; \} \}/.test(code)
);

// Ordem de fonte prescrita pelo plano 20-03: a regra .b3-mode-switch{transition:...}
// (empate de especificidade com o gate amplo) vem ANTES do bloco amplo, que por
// sua vez vem ANTES do bloco estreito — comparação por indexOf no texto já sem
// comentários de linha (o comentário de bloco explicativo foi escrito para NÃO
// repetir os literais buscados aqui, ver commit de correção desta mesma task).
const idxModeSwitchTransition = code.indexOf(".b3-mode-switch, .b3-mode-switch *{ transition:");
const idxWideBlock = code.indexOf("transition-duration: 0.01ms");
const idxNarrowBlock = code.indexOf(".b3 .tt-track,.b3 .spin{ animation:none");
ok(
  "MOTION-03: ordem de fonte correta (.b3-mode-switch transition < bloco amplo < bloco estreito)",
  idxModeSwitchTransition >= 0 &&
  idxWideBlock >= 0 &&
  idxNarrowBlock >= 0 &&
  idxModeSwitchTransition < idxWideBlock &&
  idxWideBlock < idxNarrowBlock
);

console.log(fails === 0 ? "\nOK — todas as asserções da Fase 20 (planos 20-01/20-02/20-03) passaram" : `\n${fails} asserção(ões) falharam`);
process.exit(fails);
