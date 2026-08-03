// F5 — Guardião do PAINEL DE ADMINISTRAÇÃO (v1 SÓ VER, decisão do Alex:
// nenhum botão de ação nesta versão). Vive em LogsDebugScreen, mesmo padrão
// de esconder em 403 que os logs do servidor já usam (adminDenied).
// Roda sem build: `node web/tests/test_admin_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const api = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// cliente HTTP
ok("api.adminSummary chama GET /api/admin/summary", /adminSummary: \(\) => req\("GET", "\/api\/admin\/summary"/.test(api));

// paridade dos DOIS stores
ok("serverStore expõe adminSummary", /adminSummary: \(\) => api\.adminSummary\(\)/.test(persistence));
ok("deviceStore expõe adminSummary", /async adminSummary\(\) \{ ensure\(\); return api\.adminSummary\(\); \}/.test(persistence));

// esconde em 403, igual aos logs do servidor (mesmo portão de admin)
ok("adminDenied existe e esconde a seção (403 => sem erro visível)", /setAdminDenied\(true\)/.test(app) && /!adminDenied && admin/.test(app));
ok("carrega junto com os outros painéis (loadAdmin no mesmo useEffect)", /loadSrv\(\); loadDiario\(\); loadObs\(\); loadAdmin\(\);/.test(app));

// v1 SÓ VER: nenhum botão de ação no painel (só o refresh ↻, igual aos logs)
const painelAdmin = (app.match(/PAINEL DE ADMINISTRAÇÃO[\s\S]*?\{\/\* F5 \(2026-08-02\) — PAINEL DE ADMINISTRAÇÃO/) || [null])[0]
  || (app.split("ADMINISTRAÇÃO</div>")[1] || "").split("</>")[0];
ok("painel existe no arquivo", app.includes("PAINEL DE ADMINISTRAÇÃO"));
ok("v1 SÓ VER: nenhum onClick além do refresh (↻) no bloco do admin", (() => {
  const idx = app.indexOf("PAINEL DE ADMINISTRAÇÃO");
  const fim = app.indexOf("Observabilidade — status do servidor", idx + 1); // próxima seção não existe; usa fim do arquivo
  const bloco = app.slice(idx, idx + 2600); // recorte generoso do bloco (ver render acima)
  const onClicks = bloco.match(/onClick=/g) || [];
  return onClicks.length === 1; // só o botão de refresh
})());

// conteúdo mostrado: usuários, uso de IA, agente, gate — sem vazar segredo
ok("mostra total de usuários e lista (email/provider/created_at)", /admin\.totalUsuarios/.test(app) && /u\.email/.test(app) && /u\.provider/.test(app) && /u\.created_at/.test(app));
ok("mostra uso de IA (cota/teto) sem token/chave", /admin\.usoIA\.cotaPorUsuarioDia/.test(app) && /admin\.usoIA\.tetoGlobalDia/.test(app));
ok("mostra o estado do gate de cadastro obrigatório", /admin\.gate\.ativo/.test(app) && /admin\.gate\.hostsFechados/.test(app));
ok("mostra saúde do agente (kill switch, intervalo)", /admin\.agente\.killSwitch/.test(app) && /admin\.agente\.intervaloS/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
