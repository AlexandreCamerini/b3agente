// 25-05 (Fase 4 do `.planning/phases/25-planos-comerciais/25-CONTEXT.md`) —
// Guardião estático do card "Limites e funções por plano" no portal admin
// (web-admin/src/App.jsx + web-admin/src/api.js).
//
// O que este arquivo trava, e por quê:
//   • as três chamadas existem e apontam para /api/admin/planos — sem elas o
//     card não fala com nada;
//   • PRÉVIA e APLICAR são chamadas DIFERENTES, e só a segunda manda
//     `aplicar: true`. Se a prévia mandasse, "simular" gravaria;
//   • NENHUMA lista de plano, limite ou função no fonte do portal. A segunda
//     cópia de `plan.LIMITES_DE_PLANO` não acompanharia a próxima mudança, e
//     o dia em que existir um terceiro plano ele sumiria da tela;
//   • a linha que explica `origem: "default"` existe E é condicionada a esse
//     valor — é o achado do 25-04: num limite de PLANO, "padrão" não quer
//     dizer "ninguém configurou nada", quer dizer "quem manda é o resolvedor
//     GLOBAL". Uma frase incondicional mentiria no caso em que o plano de fato
//     decide;
//   • o botão "voltar ao padrão" só aparece com `origem === "kv"` — só existe
//     configuração de painel para desfazer quando ela existe;
//   • as funções do plano são SOMENTE LEITURA (D2 pendente por decisão do Alex
//     no 25-04): nenhum botão, input ou onClick entre os marcadores;
//   • `window.confirm` NÃO aparece neste componente — o padrão da casa para
//     esta classe de decisão é prévia/aplicar, e os dois juntos seriam ruído;
//   • o card é gateado por `usuarios.gerenciar` no front TAMBÉM (o backend
//     recusa de qualquer jeito — ADR-013: nunca escondido só na UI);
//   • o array VIEWS continua com as 10 abas: o card mora DENTRO de "Usuários e
//     papéis", não numa aba nova.
//
// web-admin/ não tem suíte própria — mesmo precedente de
// web/tests/test_admin_cota_opcoes.mjs: lê o fonte por readFileSync.
//
// Roda sem build: `node web/tests/test_admin_planos_config_ui.mjs`.
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
const reGet = /planosGet:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/admin\/planos"\)/;
const rePrevia = /planosPrevia:\s*\(corpo\)\s*=>\s*req\("POST",\s*"\/api\/admin\/planos",\s*corpo\)/;
const reAplicar = /planosAplicar:\s*\(corpo\)\s*=>\s*req\("POST",\s*"\/api\/admin\/planos",\s*\{\s*\.\.\.corpo,\s*aplicar:\s*true\s*\}\)/;

ok("api.planosGet chama GET /api/admin/planos", reGet.test(api));
ok("api.planosPrevia posta SEM aplicar", rePrevia.test(api));
ok("api.planosAplicar posta COM aplicar: true", reAplicar.test(api));

ok("a linha da prévia não contém `aplicar`", (() => {
  const linha = (api.split("\n").find((l) => l.includes("planosPrevia")) || "");
  return linha.length > 0 && !linha.includes("aplicar");
})());

// --------------------------------------------------------------- App.jsx ---
ok("existe o componente PlanosConfig", /function PlanosConfig\(/.test(app));
ok("o card se chama \"Limites e funções por plano\"",
   /Card title="Limites e funções por plano/.test(app));

// Recorte que vai da nota de origem ao fim do componente.
const bloco = (app.match(/function NotaDeOrigem\([\s\S]*?\nfunction PlanosConfig\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco do card foi recortado (guarda contra vacuidade)", bloco.length > 1200);

ok("o card busca os dados pela api.planosGet", /api\.planosGet\(\)/.test(bloco));
ok("o card tem prévia (api.planosPrevia)", /api\.planosPrevia\(/.test(bloco));
ok("o card tem aplicar (api.planosAplicar)", /api\.planosAplicar\(/.test(bloco));

// ------------------------------------ nenhuma lista literal no portal ------
// A segunda cópia do catálogo é o defeito que este guardrail existe para
// impedir: ela não acompanha a mudança seguinte e some do painel em silêncio.
for (const literal of ["free", "pro", "max_watchlist", "max_analyses_per_month",
                       "ia_gerenciada_dia", "opcoes_chamadas_dia",
                       "assistente_brl_dia", "opcoes.criar_setup", "ilimitado"]) {
  ok(`o card não escreve o literal "${literal}"`, !bloco.includes(`"${literal}"`));
}
ok("os planos vêm do backend (data.planos)", /data\.planos\.map\(/.test(bloco));
ok("os limites vêm do backend (data.limites)", /data\.limites\.map\(/.test(bloco));
ok("as funções vêm do backend (data.funcoes)", /data\.funcoes\[/.test(bloco));
ok("a palavra de \"sem limite\" vem do backend (textoSemLimite)",
   /textoSemLimite/.test(bloco));

// a ORIGEM, traduzida pelo mapa que o card de cota já estabeleceu
ok("a origem é lida do backend e traduzida pelo ORIGEM_ROTULO",
   /ORIGEM_ROTULO\[lim\.origem\]/.test(bloco));

// ---------------------------- a leitura de `origem: default` (25-04) -------
const reNotaDefault = /if \(lim\.origem === "default"\)/;
ok("a linha explicativa é CONDICIONADA a origem === \"default\"", reNotaDefault.test(bloco));
ok("a linha explicativa diz que o valor não é próprio do plano",
   /Sem valor próprio neste plano/.test(bloco));
ok("ela nomeia quem decide quando o backend informa (meta.global)",
   /meta\.global/.test(bloco));
// e NÃO é incondicional: a frase mora dentro do ramo, nunca no corpo solto
ok("a frase não é renderizada fora de um ramo condicional", (() => {
  const i = bloco.indexOf("Sem valor próprio neste plano");
  if (i < 0) return false;
  const antes = bloco.slice(0, i);
  const ultimoIf = antes.lastIndexOf("if (");
  return ultimoIf >= 0 && antes.slice(ultimoIf).includes('=== "default"');
})());

// --------------------------------------------- voltar ao padrão (só kv) ----
const reRestaurar = /lim\.origem === "kv" && \(/;
ok("o botão de voltar ao padrão só é renderizado sob origem === \"kv\"", reRestaurar.test(bloco));
ok("o botão chama o mesmo fluxo de aplicar, com null no campo",
   /restaurar\(pid, L\.chave\)/.test(bloco) && /\[chave\]: null/.test(bloco));

// ------------------------------- funções: leitura, nenhum controle ---------
const blocoFuncoes = (bloco.match(/funções do plano — SOMENTE LEITURA[\s\S]*?fim das funções do plano/) || [""])[0];
ok("o bloco das funções foi recortado", blocoFuncoes.length > 120);
for (const proibido of ["<button", "<input", "onClick", "onChange"]) {
  ok(`nenhum controle de escrita nas funções do plano (${proibido})`,
     !blocoFuncoes.includes(proibido));
}
ok("a nota que diz que o RBAC ainda manda é renderizada", /notasDeFuncao/.test(bloco));

// ------------------------------------------- o padrão da casa: sem modal ---
ok("o card não usa window.confirm (prévia/aplicar é a confirmação)",
   !/window\.confirm/.test(bloco));

// ADR-013 — nunca escondido SÓ na UI, mas escondido também na UI
ok("o card só renderiza os campos para quem tem usuarios.gerenciar",
   /usuarios\.gerenciar/.test(bloco));

// --------------------------------------------------- não-regressão VIEWS ---
const views = (app.match(/const VIEWS = \[[\s\S]*?\n\];/) || [""])[0];
ok("VIEWS foi recortado", views.length > 200);
ok("VIEWS continua com 10 abas", (views.match(/\{ id: /g) || []).length === 10);
ok("nenhuma aba nova foi criada para os planos", !/PlanosConfig/.test(views));
ok("a aba de usuários mantém a permissão original",
   /\{ id: "usuarios", label: "Usuários e papéis", C: Usuarios, perm: "usuarios\.gerenciar" \}/.test(views));

// o card mora DENTRO da aba "Usuários e papéis" — é a mesma decisão comercial
const blocoUsuarios = (app.match(/function Usuarios\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco de Usuarios foi recortado", blocoUsuarios.length > 400);
ok("Usuarios renderiza o card de planos", /<PlanosConfig/.test(blocoUsuarios));

// ------------------------------------------------------------- sanidade ---
// Uma regex que não pega nada passaria este arquivo inteiro por vacuidade.
ok("sanidade: a regex do GET recusa um endereço diferente",
   !reGet.test('planosGet: () => req("GET", "/api/admin/users")'));
ok("sanidade: a regex do aplicar recusa um POST sem aplicar",
   !reAplicar.test('planosAplicar: (corpo) => req("POST", "/api/admin/planos", corpo)'));
ok("sanidade: a regex da nota de origem PEGA o padrão quando ele existe",
   reNotaDefault.test('  if (lim.origem === "default") {\n    return null;\n  }'));
ok("sanidade: a regex da nota recusa uma condição sobre outra origem",
   !reNotaDefault.test('if (lim.origem === "env") {'));
ok("sanidade: a regex do botão de restaurar PEGA o padrão quando ele existe",
   reRestaurar.test('{lim.origem === "kv" && ('));
ok("sanidade: a regex do botão recusa um render incondicional",
   !reRestaurar.test('{podeEditar && (\n  <button>voltar ao padrão</button>'));
ok("sanidade: a busca por literal PEGA uma lista escrita à mão",
   'const PLANOS = ["free", "pro"];'.includes('"free"'));
ok("sanidade: a contagem de VIEWS recusa um array com 11",
   ((views + '\n  { id: "novo", ').match(/\{ id: /g) || []).length === 11);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
