// 24-17 (pedido do Alex, 2026-09-12) — Guardião estático do controle de PLANO
// no card "Usuários e papéis" do portal admin (web-admin/src/App.jsx +
// web-admin/src/api.js).
//
// O que este arquivo trava, e por quê:
//   • `api.userPlan` existe e aponta para POST /api/admin/users/{id}/plan —
//     sem ela o controle não fala com nada;
//   • as opções vêm de `data.planosDisponiveis`, servido pelo backend a
//     partir de `plan.PLANOS_POR_ID`. NENHUM id de plano escrito na UI: uma
//     lista `["free","pro"]` aqui seria a segunda cópia, e ela não
//     acompanharia o dia em que existir um terceiro plano;
//   • a confirmação vem ANTES da chamada, nomeando o plano de destino e a
//     conta — mesmo motivo dos papéis (ADR-014): o efeito é imediato, o
//     portal abre no celular e um dedo torto promoveria uma conta;
//   • o plano ATUAL de cada usuário aparece no card (decidir sem ver o estado
//     é decidir no escuro);
//   • erro do backend vira mensagem na tela, reusando o `msg` do card;
//   • alvo de toque de 44px, como o resto do portal (HIG);
//   • a nota de topo do componente REGISTRA a reversão com data, em vez de
//     apagar o "SEM override de plano nesta rodada" que estava lá — o
//     repositório registra reversão deliberada (guardrail do CLAUDE.md);
//   • não-regressão: os papéis continuam vindo de `gruposDisponiveis` pela
//     `api.userRole`, com a confirmação deles intacta.
//
// web-admin/ não tem suíte própria — mesmo precedente de
// web/tests/test_admin_cota_opcoes.mjs: lê o fonte por readFileSync.
//
// Roda sem build: `node web/tests/test_admin_plano_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const app = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");
const api = readFileSync(join(raiz, "web-admin", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---------------------------------------------------------------- api.js ---
const rePlan = /userPlan:\s*\(userId,\s*plano\)\s*=>\s*req\("POST",\s*"\/api\/admin\/users\/"\s*\+\s*encodeURIComponent\(userId\)\s*\+\s*"\/plan",\s*\{\s*plano\s*\}\)/;
ok("api.userPlan posta em /api/admin/users/{id}/plan com { plano }", rePlan.test(api));

const reRole = /userRole:\s*\(userId,\s*role,\s*acao\)\s*=>\s*req\("POST",\s*"\/api\/admin\/users\/"\s*\+\s*encodeURIComponent\(userId\)\s*\+\s*"\/roles"/;
ok("não-regressão: api.userRole continua intacta", reRole.test(api));

// --------------------------------------------------------------- App.jsx ---
// Recorte do componente inteiro, comentário de topo incluído.
const bloco = (app.match(/\/\/ ADR-013 — Usuários e papéis[\s\S]*?\nfunction Usuarios\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco do card Usuários foi recortado (guarda contra vacuidade)", bloco.length > 800);

ok("o card chama api.userPlan", /api\.userPlan\(/.test(bloco));
ok("as opções de plano vêm de data.planosDisponiveis", /data\.planosDisponiveis/.test(bloco));
ok("o plano atual de cada usuário aparece no card", /u\.plan\b/.test(bloco));
ok("erro do backend vira mensagem (reusa o msg do card)", /setMsg\(/.test(bloco));
ok("alvo de toque de 44px no controle de plano", /minHeight:\s*"44px"/.test(bloco));

// --------------------------------- fonte única dos ids de plano ------------
// O id do plano NUNCA é escrito na UI — nem como lista, nem como literal
// solto. Ele nasce em server/app/plan.py e chega pelo backend.
const literaisDePlano = [
  ...app.matchAll(/["'](free|pro)["']/g),
  ...api.matchAll(/["'](free|pro)["']/g),
].map((m) => m[0]);
ok("nenhum id de plano escrito no fonte do portal", literaisDePlano.length === 0);

const reListaLiteral = /\[\s*["'](?:free|pro)["']\s*,\s*["'](?:free|pro)["']\s*\]/;
ok("nenhuma lista literal de planos no portal", !reListaLiteral.test(app) && !reListaLiteral.test(api));

// ------------------------- confirmação antes da escrita --------------------
const mudar = (bloco.match(/const mudarPlano = async[\s\S]*?\n  \};/) || [""])[0];
ok("a função mudarPlano foi recortada", mudar.length > 200);

const iConfirm = mudar.indexOf("window.confirm");
const iChamada = mudar.indexOf("api.userPlan");
ok("existe window.confirm em mudarPlano", iConfirm >= 0);
ok("a confirmação vem ANTES da chamada que grava", iConfirm >= 0 && iChamada > iConfirm);
ok("a confirmação nomeia o plano de destino", /confirm\([^)]*\$\{plano\}/.test(mudar));
ok("a confirmação nomeia a conta", /const quem = u\.email/.test(mudar) && /confirm\([^)]*\$\{quem\}/.test(mudar));
ok("recusar a confirmação aborta antes de chamar", /if \(!window\.confirm\([\s\S]*?\)\) return;/.test(mudar));

// não-regressão: a confirmação dos PAPÉIS continua lá
const alternar = (bloco.match(/const alternar = async[\s\S]*?\n  \};/) || [""])[0];
ok("a função alternar (papéis) foi recortada", alternar.length > 200);
ok("não-regressão: papéis continuam com confirmação", alternar.includes("window.confirm"));
ok("não-regressão: papéis continuam vindo de gruposDisponiveis", /data\.gruposDisponiveis/.test(bloco));

// ------------------------ a reversão fica registrada, não apagada ----------
const notaTopo = (bloco.match(/^\/\/[\s\S]*?\nfunction Usuarios\(/) || [""])[0];
ok("a nota de topo foi recortada", notaTopo.length > 100);
ok("a nota de topo data a reversão (2026-09-12)", /2026-09-12/.test(notaTopo));
ok("a nota de topo preserva o registro antigo (\"sem override de plano\")",
   /override de plano/i.test(notaTopo));

// ------------------------------------------------------------- sanidade ---
// Uma regex que não pega nada aprovaria este arquivo inteiro por vacuidade.
ok("sanidade: a regex do userPlan recusa um endereço diferente",
   !rePlan.test('userPlan: (userId, plano) => req("POST", "/api/admin/users/" + encodeURIComponent(userId) + "/roles", { plano })'));
ok("sanidade: a busca por literal de plano encontra o defeito que existe para pegar",
   [...'const PLANOS = ["free", "pro"];'.matchAll(/["'](free|pro)["']/g)].length === 2);
ok("sanidade: a regex da lista literal reprova o defeito",
   reListaLiteral.test('const PLANOS = ["free", "pro"];'));
ok("sanidade: a ordem confirm→chamada reprova a ordem invertida", (() => {
  const invertido = 'await api.userPlan(u.id, plano); if (!window.confirm("x")) return;';
  return invertido.indexOf("window.confirm") > invertido.indexOf("api.userPlan");
})());
ok("sanidade: o recorte do bloco recusa um fonte sem o componente",
   ("function Outra() {}\n").match(/\/\/ ADR-013 — Usuários e papéis[\s\S]*?\nfunction Usuarios\([\s\S]*?\n\}\n/) === null);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
