// qa/49 (pedido do Alex) — Guardião: o campo de modelo virou uma LISTBOX por
// provedor, alimentada pelo catálogo do servidor (/api/ai/models), com os
// parâmetros que cada modelo aceita (temperatura / teto de saída) já com default
// editável e armazenado. Assim evitamos erros de API (modelo que recusa
// temperature / precisa de teto alto). Roda sem build.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const api = readFileSync(join(here, "..", "src", "api.js"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// camada de API
ok("api.js expõe aiModels (GET /api/ai/models)", /aiModels:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/ai\/models"\)/.test(api));
// BUG qa/49 (reporte do Alex "aiModels is not a function"): o app nativo usa
// deviceStore, o web usa serverStore — AMBOS precisam expor aiModels.
ok("serverStore expõe aiModels", /aiModels:\s*\(\)\s*=>\s*api\.aiModels\(\)/.test(persistence));
ok("deviceStore (nativo) expõe aiModels", /async aiModels\(\)\s*\{\s*ensure\(\);\s*return api\.aiModels\(\);/.test(persistence));
ok("App.jsx chama aiModels com guarda (não derruba a tela)", /typeof store\.aiModels === "function"/.test(app));

// AiConfigScreen busca o catálogo e deriva a spec do modelo atual
ok("AiConfigScreen busca o catálogo via store.aiModels()", /store\.aiModels\(\)\.then/.test(app));
ok("deriva a lista de modelos do provedor", /catalogo\.catalog\[c\.provider\]/.test(app));
ok("deriva a spec do modelo atual", /modelos\.find\(\(m\)\s*=>\s*m\.id === c\.model\)/.test(app));

// listbox de modelos + opção personalizada (não trava modelos novos)
ok("renderiza <select> de modelos com map do catálogo", /modelos\.map\(\(m\)\s*=>\s*<option key=\{m\.id\}/.test(app));
ok("mantém opção Personalizado (digitar)", /__custom__/.test(app) && /Personalizado/.test(app));
ok("fallback p/ texto livre quando o catálogo não carrega", /modelos\.length > 0 \?/.test(app));

// parâmetros por-modelo: teto de saída e temperatura (condicional ao aceite)
ok("campo de teto de saída (maxTokens) salvo no config", /A\.saveConfig\(\{ maxTokens:/.test(app));
ok("temperatura só editável se o modelo aceita (aceitaTemp)", /aceitaTemp \?/.test(app));
ok("modelo que raciocina mostra aviso de temperatura não aceita", /não é aceito na API/.test(app));

// trocar de provedor reescolhe um modelo válido do novo provedor
ok("trocar provedor auto-seleciona 1º modelo do provedor", /A\.saveConfig\(\{ provider: p, model: lst\[0\]/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
