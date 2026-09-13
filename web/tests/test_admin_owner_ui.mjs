// 25-02 (Fase 1 do 25-CONTEXT, decisão D1 do Alex, 2026-09-12) — Guardião
// estático do papel IRREVOGÁVEL no card "Usuários e papéis" do portal admin
// (web-admin/src/App.jsx) e da lista que o alimenta (server/app/main.py).
//
// O defeito que este arquivo existe para pegar tem duas caras opostas, e as
// duas fazem o portal mentir sobre o estado da conta:
//   • `owner` dentro de `gruposDisponiveis` vira um BOTÃO DE TOGGLE — o portal
//     renderiza um por item da lista —, e clicá-lo tenta revogar um papel que
//     a rota recusa: uma ação impossível oferecida na tela, que sempre termina
//     em 403;
//   • `owner` fora da tela INTEIRA faz o admin abrir a conta do dono e
//     concluir que ela não tem o papel.
// A saída é a terceira: papel irrevogável aparece como ESTADO, não como ação.
//
// E a lista vem do BACKEND (`papeisIrrevogaveis`), porque a regra é do
// backend: um literal "owner" no portal seria a segunda cópia dela, e ela não
// acompanharia o dia em que existir outro papel permanente — mesmo critério
// que 24-17 aplicou aos ids de plano.
//
// web-admin/ não tem suíte própria — mesmo precedente de
// web/tests/test_admin_plano_ui.mjs: lê o fonte por readFileSync.
//
// Roda sem build: `node web/tests/test_admin_owner_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const app = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");
const api = readFileSync(join(raiz, "web-admin", "src", "api.js"), "utf8");
const mainPy = readFileSync(join(raiz, "server", "app", "main.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------- backend ----
const users = (mainPy.match(/@app\.get\("\/api\/admin\/users"\)[\s\S]*?\n    \}\n/) || [""])[0];
ok("a rota GET /api/admin/users foi recortada (guarda contra vacuidade)", users.length > 300);
ok("a rota publica `papeisIrrevogaveis`", /"papeisIrrevogaveis":\s*\[rbac\.OWNER\]/.test(users));
ok("a lista de TOGGLE continua sendo grupos + role_admin, sem o owner",
   /"gruposDisponiveis":\s*sorted\(rbac\.GRUPOS\)\s*\+\s*\[rbac\.ROLE_ADMIN\]/.test(users)
   && !/"gruposDisponiveis":[^\n]*rbac\.OWNER/.test(users));

// ------------------------------------------------------------- App.jsx ----
// Recorte do componente inteiro, comentário de topo incluído.
const bloco = (app.match(/\/\/ ADR-013 — Usuários e papéis[\s\S]*?\nfunction Usuarios\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco do card Usuários foi recortado (guarda contra vacuidade)", bloco.length > 800);

ok("o card lê `papeisIrrevogaveis` do backend", /data\.papeisIrrevogaveis/.test(bloco));
ok("o papel permanente é filtrado dos papéis QUE A CONTA TEM (mostra estado real)",
   /\(u\.roles\s*\|\|\s*\[\]\)\.filter\(\s*\(role\)\s*=>\s*\(data\.papeisIrrevogaveis\s*\|\|\s*\[\]\)\.includes\(role\)\s*\)/.test(bloco));

// O trecho renderizado para o papel permanente: <span>, nunca <button>.
const permanente = (bloco.match(/\(u\.roles \|\| \[\]\)\.filter\([\s\S]*?\n {14}\)\)\}/) || [""])[0];
ok("o trecho do papel permanente foi recortado", permanente.length > 200);
ok("o papel permanente é renderizado como <span>, não <button>",
   /<span\b/.test(permanente) && !/<button\b/.test(permanente));
// a checagem de ausência exige o recorte NÃO vazio — senão passa por
// vacuidade num fonte que nem tem o trecho (medido no RED deste guardião).
ok("o papel permanente NÃO tem onClick (não existe ação a oferecer)",
   permanente.length > 200 && !/onClick/.test(permanente));
ok("o papel permanente diz na tela que é permanente", /permanente/.test(permanente));

// não-regressão: os papéis com toggle continuam como estavam
ok("não-regressão: o toggle continua vindo de gruposDisponiveis", /data\.gruposDisponiveis/.test(bloco));
ok("não-regressão: o toggle continua chamando alternar()", /onClick=\{\(\) => alternar\(u\.id, role, tem\)\}/.test(bloco));
ok("não-regressão: a confirmação dos papéis segue de pé", /window\.confirm/.test(bloco));

// ------------------------- fonte única: nenhum literal no portal -----------
// "owner" escrito na UI seria a segunda cópia da regra do backend.
const literaisOwner = [...app.matchAll(/["']owner["']/g), ...api.matchAll(/["']owner["']/g)];
ok("nenhum literal \"owner\" no fonte do portal", literaisOwner.length === 0);

// ------------------------------------------------------------- sanidade ---
// Regex que não pega nada aprovaria este arquivo inteiro por vacuidade.
ok("sanidade: a regex do backend reprova o owner dentro do toggle",
   /"gruposDisponiveis":[^\n]*rbac\.OWNER/.test('        "gruposDisponiveis": sorted(rbac.GRUPOS) + [rbac.ROLE_ADMIN, rbac.OWNER],'));
ok("sanidade: a checagem de <button> reprova o defeito que existe para pegar",
   /<button\b/.test('<button onClick={() => alternar(u.id, role, tem)}>{role}</button>'));
ok("sanidade: a busca por literal encontra um \"owner\" escrito na UI",
   [...'const PERMANENTES = ["owner"];'.matchAll(/["']owner["']/g)].length === 1);
ok("sanidade: o recorte do bloco recusa um fonte sem o componente",
   ("function Outra() {}\n").match(/\/\/ ADR-013 — Usuários e papéis[\s\S]*?\nfunction Usuarios\([\s\S]*?\n\}\n/) === null);
ok("sanidade: o recorte da rota recusa um main.py sem ela",
   ("def outra(): pass\n").match(/@app\.get\("\/api\/admin\/users"\)[\s\S]*?\n    \}\n/) === null);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
