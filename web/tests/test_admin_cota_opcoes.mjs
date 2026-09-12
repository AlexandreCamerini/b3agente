// 24-15 (pedido do Alex, 2026-09-11) — Guardião estático do card "Cota da aba
// Opções" no portal admin (web-admin/src/App.jsx + web-admin/src/api.js).
//
// O que este arquivo trava, e por quê:
//   • as três chamadas existem e apontam para /api/obs/opcoes/cota — sem elas
//     o card não fala com nada;
//   • PRÉVIA e APLICAR são chamadas DIFERENTES, e só a segunda manda
//     `aplicar: true`. Se a prévia mandasse, o botão "simular" gravaria;
//   • o card mostra a ORIGEM de cada limite. Sem ela o admin muda pelo
//     painel, a env do Railway continua diferente, e ninguém sabe qual manda;
//   • o card mostra o consumo global de HOJE — decidir um teto sem ver o
//     consumo é decidir no escuro, que é o estado que o plano encerra;
//   • a frase sobre o teto de 2.000/dia do SERVIÇO está lá. Sem ela um admin
//     sobe a cota por usuário achando que aumentou o total disponível;
//   • o card é gateado por `fontes_dados.configurar` no front TAMBÉM (o
//     backend recusa de qualquer jeito — ADR-013: nunca escondido só na UI);
//   • o array VIEWS continua com as 10 abas e as permissões originais: o card
//     novo mora DENTRO de "Fontes de dados", não numa aba nova.
//
// web-admin/ não tem suíte própria — mesmo precedente de
// web/tests/test_fase5_auditoria_perm.mjs: lê o fonte por readFileSync.
//
// Roda sem build: `node web/tests/test_admin_cota_opcoes.mjs`.
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
const reGet = /opcoesCotaGet:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/obs\/opcoes\/cota"/;
const rePrevia = /opcoesCotaPrevia:\s*\(campos\)\s*=>\s*req\("POST",\s*"\/api\/obs\/opcoes\/cota",\s*campos\)/;
const reAplicar = /opcoesCotaAplicar:\s*\(campos\)\s*=>\s*req\("POST",\s*"\/api\/obs\/opcoes\/cota",\s*\{\s*\.\.\.campos,\s*aplicar:\s*true\s*\}\)/;

ok("api.opcoesCotaGet chama GET /api/obs/opcoes/cota", reGet.test(api));
ok("api.opcoesCotaPrevia posta SEM aplicar", rePrevia.test(api));
ok("api.opcoesCotaAplicar posta COM aplicar: true", reAplicar.test(api));

// A prévia não pode mandar `aplicar` — o botão de simular gravaria.
ok("a linha da prévia não contém `aplicar`", (() => {
  const linha = (api.split("\n").find((l) => l.includes("opcoesCotaPrevia")) || "");
  return linha.length > 0 && !linha.includes("aplicar");
})());

// --------------------------------------------------------------- App.jsx ---
ok("existe o componente CotaOpcoes", /function CotaOpcoes\(/.test(app));
ok("o card se chama \"Cota da aba Opções\"", /Card title="Cota da aba Opções/.test(app));

// Recorte que vai do mapa de rótulos ao fim do componente: `ORIGEM_ROTULO`
// e `CAMPOS_COTA` são constantes de módulo, não moram dentro da função.
const bloco = (app.match(/const ORIGEM_ROTULO[\s\S]*?\nfunction CotaOpcoes\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco do card foi recortado (guarda contra vacuidade)", bloco.length > 400);

ok("o card busca os dados pela api.opcoesCotaGet", /api\.opcoesCotaGet\(\)/.test(bloco));
ok("o card tem botão de prévia (api.opcoesCotaPrevia)", /api\.opcoesCotaPrevia\(/.test(bloco));
ok("o card tem botão de aplicar (api.opcoesCotaAplicar)", /api\.opcoesCotaAplicar\(/.test(bloco));

// os TRÊS limites, cada um com campo editável
for (const campo of ["cotaUsuarioDia", "rateMin", "cotaGlobalDia"]) {
  ok(`o card trata ${campo}`, bloco.includes(campo));
}

// a ORIGEM, traduzida — "kv" não é palavra que um admin tenha de decifrar
ok("a origem é traduzida para o humano (painel / variável de ambiente / padrão)",
   /painel/.test(bloco) && /variável de ambiente/.test(bloco) && /padrão/.test(bloco));
ok("a origem de cada limite é lida do backend (campo `origem`)", /\.origem/.test(bloco) || /origem\]/.test(bloco));

// o consumo real de hoje
ok("o card mostra o consumo global de hoje", /consumoGlobalHoje/.test(bloco));

// a frase que dá sentido à decisão
ok("o card diz que o teto de 2.000/dia é do SERVIÇO e compartilhado",
   /2\.000/.test(bloco) && /compartilhad/i.test(bloco) && /serviço/i.test(bloco));

// ADR-013 — nunca escondido SÓ na UI, mas escondido também na UI
ok("o card só renderiza os campos para quem tem fontes_dados.configurar",
   /fontes_dados\.configurar/.test(bloco));

// --------------------------------------------------- não-regressão VIEWS ---
const views = (app.match(/const VIEWS = \[[\s\S]*?\n\];/) || [""])[0];
ok("VIEWS foi recortado", views.length > 200);
ok("VIEWS continua com 10 abas", (views.match(/\{ id: /g) || []).length === 10);
ok("nenhuma aba nova foi criada para a cota de opções", !/CotaOpcoes/.test(views));
ok("a aba de fontes de dados mantém a permissão original",
   /\{ id: "fontesDados", label: "Fontes de dados", C: FontesDeDados, perm: "fontes_dados\.configurar" \}/.test(views));

// o card mora DENTRO da aba de fontes de dados (é a mesma família: teto de
// consumo de fonte externa)
const blocoFontes = (app.match(/function FontesDeDados\([\s\S]*?\n\}\n/) || [""])[0];
ok("o bloco de FontesDeDados foi recortado", blocoFontes.length > 400);
ok("FontesDeDados renderiza o card de cota de opções", /<CotaOpcoes/.test(blocoFontes));

// ------------------------------------------------------------- sanidade ---
// Uma regex que não pega nada passaria este arquivo inteiro por vacuidade.
ok("sanidade: a regex do GET recusa um endereço diferente",
   !reGet.test('opcoesCotaGet: () => req("GET", "/api/obs/brapi/projecao")'));
ok("sanidade: a regex do aplicar recusa um POST sem aplicar",
   !reAplicar.test('opcoesCotaAplicar: (campos) => req("POST", "/api/obs/opcoes/cota", campos)'));
ok("sanidade: a contagem de VIEWS recusa um array com 11",
   ((views + '\n  { id: "novo", ').match(/\{ id: /g) || []).length === 11);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
