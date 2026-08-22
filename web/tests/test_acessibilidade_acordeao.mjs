// FIX-C15 (REPORT-01) — guardião de teclado do padrão de acordeão.
//
// Contrato: todo elemento com role="button" (padrão de toggle acessível já
// estabelecido no app: div + role + tabIndex, hoje em OpcaoContrato e
// OpcoesCamada) precisa responder a Enter e Espaço — sem rolar a página no
// Espaço — e anunciar o estado via aria-expanded. Se alguém adicionar um
// role="button" novo sem teclado, este guardião tem que falhar: ele conta
// TODAS as ocorrências de role="button" e exige o mesmo número de
// onKeyDown/aria-expanded adjacentes, em vez de travar só nos dois pontos
// conhecidos hoje.
// Roda sem build: `node web/tests/test_acessibilidade_acordeao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const roleButtonCount = (app.match(/role="button"/g) || []).length;
ok(`existe pelo menos um role="button" no arquivo (guardião não fica vácuo)`, roleButtonCount > 0);

// Cada elemento com role="button" hoje é um único `<div ...>` numa linha só
// (padrão já estabelecido pelos dois toggles do acordeão de opções) — extrai
// a linha inteira de cada ocorrência e valida os 4 atributos juntos nela.
const linhas = app.split("\n").filter((l) => l.includes('role="button"'));
ok(`todas as ${roleButtonCount} ocorrência(s) de role="button" estão em linhas isoláveis (o guardião consegue auditar cada uma)`,
   linhas.length === roleButtonCount);

let comTeclado = 0;
for (const linha of linhas) {
  const temEnter = linha.includes('e.key === "Enter"');
  const temEspaco = linha.includes('e.key === " "');
  const temPreventDefault = linha.includes("e.preventDefault()");
  const temAriaExpanded = /aria-expanded=\{/.test(linha);
  if (temEnter && temEspaco && temPreventDefault && temAriaExpanded) comTeclado++;
}
ok(`todo role="button" (${roleButtonCount}) tem onKeyDown (Enter + Espaço + preventDefault) e aria-expanded — falha se um role="button" novo nascer sem teclado`,
   comTeclado === roleButtonCount);

// Confere os dois pontos de uso conhecidos hoje, nominalmente — não só a
// contagem agregada, para o erro apontar pro lugar certo se regredir.
ok('OpcaoContrato: aria-expanded={isOpen}', /role="button" tabIndex=\{0\} aria-expanded=\{isOpen\}/.test(app));
ok('OpcoesCamada: aria-expanded={open}', /role="button" tabIndex=\{0\} aria-expanded=\{open\}/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
