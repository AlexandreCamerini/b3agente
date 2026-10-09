// Guardião do link Perfil → Ajuda → Guia de treinamento (quick 261009-ukl).
// O guia é conteúdo estático (server/site_dist, URL /site/app/) — não uma tela do
// bundle. Este teste trava: (1) o tile no grupo Ajuda; (2) o destino /site/app/;
// (3) o handoff nativo pelo browser in-app (o bundle iOS é local, sem server.url),
// com origem do servidor/PROD_BASE; (4) na web, window.open SEM await antes
// (popup bloqueado em silêncio, mesma lição do abrirAdminMobile); (5) o service
// worker não sequestra /site (denylist). Roda sem build.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const vite = readFileSync(join(here, "..", "vite.config.js"), "utf8");
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const fnIni = src.indexOf("async function abrirGuiaTreinamento");
const fn = fnIni >= 0 ? src.slice(fnIni, src.indexOf("\n}\n", fnIni) + 3) : "";
ok("função abrirGuiaTreinamento existe", fnIni >= 0);
ok("destino é /site/app/ na origem do servidor", /"\/site\/app\/"/.test(fn));
ok("nativo usa Browser.open (browser in-app) com PROD_BASE de fallback", /Browser\.open\(\{ url \}\)/.test(fn) && /PROD_BASE/.test(fn));
const corpoWeb = fn.slice(fn.indexOf("} else {"));
ok("web: window.open noopener, sem await antes do clique", /window\.open\(url, "_blank", "noopener"\)/.test(fn) && !/await/.test(corpoWeb));
ok("falha mostra flash em PT-BR em vez de silenciar", /ctx\.flash\("Não foi possível abrir o guia de treinamento/.test(fn));

const ajuda = src.indexOf('<div style={hubGroup}>Ajuda</div>');
const fimAjuda = src.indexOf("Notificações {notifOn", ajuda);
const fatia = ajuda >= 0 ? src.slice(ajuda, fimAjuda) : "";
ok("tile 'Guia de treinamento' está no grupo Ajuda", /title="Guia de treinamento"/.test(fatia));
ok("tile chama abrirGuiaTreinamento(ctx)", /onClick=\{\(\) => abrirGuiaTreinamento\(ctx\)\}/.test(fatia));
ok("grupo Ajuda mantém Como funciona e Glossário", /title="Como funciona"/.test(fatia) && /title="Glossário"/.test(fatia));
ok("PWA não sequestra /site (navigateFallbackDenylist)", /navigateFallbackDenylist:[^\]]*\/\^\\\/site\//.test(vite));

if (fails) { console.log(`\n${fails} falha(s).`); process.exit(1); }
console.log("\ntodos os testes passaram.");
