// FASE 4 — wiring do Radar diário (1.3) e do DeepModal enxuto (1.4).
// Padrão "grep de wiring" do projeto: prova que as pontas estão conectadas.
// Roda sem build: `node web/tests/test_fase4_radar_deepmodal.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", p), "utf8");
const app = read("src/App.jsx");
const api = read("src/api.js");
const pers = read("src/persistence.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1.3: force ponta a ponta (UI → stores → API → query) ------------------
ok("botão manual passa force=true", /run\(period,\s*true\)/.test(app));
ok("run() repassa force ao store", /store\.scan\(p,\s*undefined,\s*force\)/.test(app));
ok("serverStore.scan aceita force", /scan:\s*\(period,\s*tickers,\s*force\)/.test(pers));
ok("deviceStore.scan aceita force (mesma interface)", /async scan\(period,\s*tickers,\s*force\)/.test(pers));
ok("api.scan envia force=1 na query", /force=1/.test(api));

// ---- 1.3: etiqueta da varredura do dia -------------------------------------
ok("UI mostra 'Varredura automática de hoje'", app.includes("Varredura automática de hoje"));
ok("UI mostra a origem manual", app.includes("Última varredura (manual)"));
ok("UI usa scanAtLabel do servidor", /res\.scanAtLabel/.test(app));

// ---- 1.4: DeepModal — fechar sempre possível + seções colapsáveis ----------
ok("componente Fold existe", /function Fold\(\{ title/.test(app));
ok("Leitura por setup em Fold", app.includes('Fold title="Leitura por setup"'));
ok("Cenários em Fold", app.includes('Fold title="Cenários de estudo"'));
ok("Riscos em Fold", app.includes('Fold title="Riscos"'));
ok("✕ visível no cabeçalho do modal", /aria-label="Fechar"/.test(app));
ok("área de conteúdo rolável de verdade (flex:1 + minHeight:0)",
  /overflowY:\s*"auto",\s*flex:\s*1,\s*minHeight:\s*0/.test(app));
ok("scroll contido no iOS (não trava a página atrás)", /overscrollBehavior:\s*"contain"/.test(app));
ok("rodapé respeita a safe area", app.includes("env(safe-area-inset-bottom"));

// ---- FASE 6 (fix 2): formatação da leitura no DeepModal --------------------
// BUG: o resumo era renderizado só com MdInline (colapsava quebras de linha) e,
// quando o JSON do N1 vinha truncado, o servidor devolvia o blob cru — texto
// "todo mal formatado" no modal. Contratos: resumo em BLOCO (<Markdown/>) e
// aviso explícito quando o servidor sinaliza parseFalhou.
ok("resumo renderizado em bloco (Markdown, não MdInline)", /r\.resumo && <div[^>]*><Markdown text=\{r\.resumo\} \/>/.test(app));
ok("aviso de leitura parcial quando parseFalhou", /r\.parseFalhou &&/.test(app) && app.includes("leitura veio incompleta"));

console.log(fails ? `\n${fails} FALHA(S)` : "\nWIRING FASE 4 (RADAR + DEEPMODAL) OK");
process.exit(fails ? 1 : 0);
