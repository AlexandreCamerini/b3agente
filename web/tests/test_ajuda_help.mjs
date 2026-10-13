// qa/38 (Help) — Guardião: tela de Ajuda ("Como funciona") + tour de 1º uso.
// Contratos: a Ajuda é acessível pelo Perfil; o conteúdo é mode-aware (usa os
// rótulos de tela de cp); o tour aparece 1x (tourSeen persiste nas allowlists
// do device E do servidor); nada removido do hub. Roda sem build.
//
// Nota 2026-10-12 (quick 261012-09v): GUIA ÚNICO. A tela "Como funciona" e o tour
// saíram do app; o Guia de treinamento (GuiaTelas.jsx, dados em site/js/telas-data.js)
// é o único material. As asserções de PRESENÇA de AjudaScreen/TourModal/ajudaSecoes/
// tourPassos/A.openTour viraram asserções de AUSÊNCIA + presença do que as substituiu;
// o 1º uso (ref + !tourSeen + tourSeen:true) e as allowlists de tourSeen seguem iguais.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { guiaIdDaTelaApp, ABERTURA_PRIMEIRO_USO } from "../src/guiaNav.js";
import { DISCLAIMERS } from "../src/disclaimers.js";

const here = dirname(fileURLToPath(import.meta.url));
const appBruto = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
// Regex de ausência rodam sobre o código sem comentários (as notas datadas citam os nomes antigos).
const semComentarios = (t) => t.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
const app = semComentarios(appBruto);
const guiaJsx = readFileSync(join(here, "..", "src", "GuiaTelas.jsx"), "utf8");
const guiaLoader = readFileSync(join(here, "..", "src", "guiaTelas.js"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const store = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 1) componentes + fonte de conteúdo única.
// Nota 2026-10-12 (quick 261012-09v): AjudaScreen/TourModal/ajudaSecoes/tourPassos deixaram de existir.
ok("AjudaScreen não existe mais (nem é renderizada)", !/function AjudaScreen\(/.test(app) && !/<AjudaScreen/.test(app));
ok("TourModal não existe mais (nem é renderizado)", !/function TourModal\(/.test(app) && !/<TourModal/.test(app));
ok("ajudaSecoes e tourPassos não são mais definidas", !/function ajudaSecoes\(/.test(app) && !/function tourPassos\(/.test(app) && !/ajudaSecoes\(cp, operador\)/.test(app));
ok("conteúdo numa fonte só: GuiaTelas lê GUIA_TELAS, que importa site/js/telas-data.js",
  /import \{[^}]*GUIA_TELAS[^}]*\} from "\.\/guiaTelas\.js"/.test(guiaJsx) && /site\/js\/telas-data\.js\?raw/.test(guiaLoader));

// 2) mode-aware: o mapeamento tela do app -> tela do guia depende do modo (Opções · confirmar).
ok("mapeamento mode-aware: opcoes/confirmar = confest (Estudo) e opcaberta (Operador)",
  guiaIdDaTelaApp({ tab: "opcoes", opcoesNivel: "confirmar", operador: false }) === "confest"
  && guiaIdDaTelaApp({ tab: "opcoes", opcoesNivel: "confirmar", operador: true }) === "opcaberta");

// 3) acessível pelo Perfil: o grupo Ajuda abre o guia; o tile/rota "Como funciona" saíram.
ok("tile 'Guia de treinamento' abre o guia", /onClick=\{\(\) => onOpen\("guia"\)\}[^>]*title="Guia de treinamento"/.test(app));
ok("sem tile 'Como funciona', sem onOpen('ajuda') e sem rota perfilView 'ajuda'",
  !/onOpen\("ajuda"\)/.test(app) && !/title="Como funciona"/.test(app) && !/perfilView === "ajuda"/.test(app));

// 4) 1º uso: abre 1x, guardado por ref + flag tourSeen (MANTIDO). Reabrir = Perfil → Ajuda → Guia.
ok("1º uso abre 1x (ref + !tourSeen)",
  /tourShownRef\.current/.test(app) && /data\.config\.tourSeen/.test(app) && /setTourOpen\(true\)/.test(app));
ok("closeTour marca tourSeen (não reaparece)", /tourSeen: true/.test(app) && /A\.closeTour/.test(app));
ok("openTour não existe mais (rever = tile Guia de treinamento)", !/openTour/.test(app));
ok("1º uso monta o Guia em Boas-vindas, fechando por A.closeTour",
  /tourOpen && <GuiaTelas abertura=\{ABERTURA_PRIMEIRO_USO\} onClose=\{A\.closeTour\}/.test(app) && ABERTURA_PRIMEIRO_USO.id === "boas");

// 5) PERSISTÊNCIA de tourSeen nas DUAS allowlists (senão o tour volta sempre).
ok("device (persistence.js) persiste tourSeen", /"tourSeen" in patch\) c\.tourSeen = !!patch\.tourSeen/.test(persist));
ok("servidor (store.py) persiste tourSeen", /"tourSeen" in patch/.test(store) && /cfg\["tourSeen"\] = bool\(patch\["tourSeen"\]\)/.test(store));

// 6) honestidade: o guia deixa claro que é simulado/educacional (rodapé único da folha).
// Nota 2026-10-12 (quick 261012-09v): antes casava "educacional e simulado" no texto da Ajuda.
ok("GuiaTelas renderiza DISCLAIMERS.short e ele diz 'Simulador educacional' e 'dinheiro simulado'",
  /\{DISCLAIMERS\.short\}/.test(guiaJsx) && /Simulador educacional/.test(DISCLAIMERS.short) && /dinheiro simulado/.test(DISCLAIMERS.short));

// 2026-10-13 (quick 261013-cqk, orquestrador): regressão achada no app local — o guia do
// 1º uso (z 1100) abria por cima da tela de login porque o efeito do 1º uso rodava antes
// do efeito do portão no mesmo ciclo. Trava: o efeito só abre depois que o portão foi
// decidido (welcomeShownRef), além de esperar welcomeAuthOpen/welcomeOpen fecharem.
{
  const i = app.indexOf("if (tourShownRef.current || !data || !data.config) return;");
  const trecho = i >= 0 ? app.slice(i, i + 500) : "";
  ok("1º uso: o guia espera o portão de login fechar E ter sido decidido (welcomeShownRef)",
    /if \(welcomeAuthOpen \|\| welcomeOpen\) return;/.test(trecho)
    && /if \(!welcomeShownRef\.current\) return;/.test(trecho)
    && trecho.indexOf("!welcomeShownRef.current") < trecho.indexOf("setTourOpen(true)"));
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
