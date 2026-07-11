// qa/38 (Help) — Guardião: tela de Ajuda ("Como funciona") + tour de 1º uso.
// Contratos: a Ajuda é acessível pelo Perfil; o conteúdo é mode-aware (usa os
// rótulos de tela de cp); o tour aparece 1x (tourSeen persiste nas allowlists
// do device E do servidor); nada removido do hub. Roda sem build.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const store = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 1) componentes + fonte de conteúdo única.
ok("AjudaScreen definida", /function AjudaScreen\(/.test(app));
ok("TourModal definido", /function TourModal\(/.test(app));
ok("conteúdo numa fonte só (ajudaSecoes) reusada", /function ajudaSecoes\(/.test(app) && /ajudaSecoes\(cp, operador\)/.test(app));
ok("passos do tour (tourPassos)", /function tourPassos\(/.test(app));

// 2) mode-aware: usa os rótulos de tela do cp (que mudam Estudo/Operador).
ok("Ajuda usa rótulos mode-aware (cp.tituloRadar/Watchlist/Portfolio)",
  /cp\.tituloRadar/.test(app) && /cp\.tituloWatchlist/.test(app) && /cp\.tituloPortfolio/.test(app));

// 3) acessível pelo Perfil (tile + rota) — nada removido do hub.
ok("tile 'Como funciona' abre 'ajuda'", /onClick=\{\(\) => onOpen\("ajuda"\)\}/.test(app) && /Como funciona/.test(app));
ok("rota perfilView 'ajuda' → AjudaScreen", /perfilView === "ajuda"[\s\S]{0,120}<AjudaScreen/.test(app));

// 4) tour: abre 1x no 1º uso, guardado por ref + flag tourSeen; reabre pela Ajuda.
ok("tour abre 1x no 1º uso (ref + !tourSeen)",
  /tourShownRef\.current/.test(app) && /data\.config\.tourSeen/.test(app) && /setTourOpen\(true\)/.test(app));
ok("closeTour marca tourSeen (não reaparece)", /tourSeen: true/.test(app) && /A\.closeTour/.test(app));
ok("Ajuda tem 'Ver o tour de novo' (A.openTour)", /A\.openTour/.test(app));
ok("TourModal renderizado no app", /tourOpen && <TourModal/.test(app));

// 5) PERSISTÊNCIA de tourSeen nas DUAS allowlists (senão o tour volta sempre).
ok("device (persistence.js) persiste tourSeen", /"tourSeen" in patch\) c\.tourSeen = !!patch\.tourSeen/.test(persist));
ok("servidor (store.py) persiste tourSeen", /"tourSeen" in patch/.test(store) && /cfg\["tourSeen"\] = bool\(patch\["tourSeen"\]\)/.test(store));

// 6) honestidade: o guia deixa claro que é simulado/educacional.
ok("conteúdo diz 'educacional e simulado'", /educacional e \*\*simulado\*\*|educacional.*simulado/i.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
