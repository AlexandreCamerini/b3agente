// Fase 5, FIX-C38 — Guardião estático do alerta preventivo de gasto de IA no
// portal admin (web-admin/src/App.jsx, componentes Custos e MudancaDeLLM).
//
// Origem: o hard stop de gasto de IA já existe (metering.py, cap_global) mas
// só se manifesta CORTANDO — a aba Custos não avisava antes. Este guardião
// trava que:
//   • a nova linha "Alerta de gasto (IA gerenciada)" existe, lê
//     data.alertaGastoIA (contrato do Plano 05-02) e mostra os 4 estados
//     (não configurado / sem base de comparação / acima do limiar / dentro
//     do normal) com o tom certo;
//   • o alerta preventivo NUNCA usa tom "negative" — fundir com o hard stop
//     numa severidade só é a regressão que este teste existe para pegar
//     (05-UI-SPEC.md, FIX-C38, contrato de cor);
//   • `Kv` ganhou o tom "faint" (usado pelos 2 estados sem base suficiente,
//     que não podem cair no verde de "positive" — CLAUDE.md item 4);
//   • os 2 campos novos de config (llmAlertaGastoPct/llmAlertaJanelaDias)
//     existem no formulário auditado, usam teclado numérico (ADR-014) e
//     entram no laço numérico de `salvar` (senão campo vazio não limpa o
//     override);
//   • nenhuma permissão nova aparece em MudancaDeLLM — `llm.configurar`
//     continua sendo a única citada.
//
// web-admin/ não tem suíte de teste própria (package.json só tem
// dev/build/preview) — este guardião segue o precedente já estabelecido em
// web/tests/test_fase3_custos_falha_brapi.mjs: mora em web/tests/, lê o
// fonte de web-admin/ por readFileSync, roda sem build e sem depender de
// web-admin/node_modules.
//
// Roda sem build: `node web/tests/test_fase5_alerta_gasto_admin.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const contar = (str) => appAdmin.split(str).length - 1;

// ─── literais do Copywriting Contract (05-UI-SPEC.md) ──────────────────────
// "dentro do normal" já existia 1x no card de orçamento brapi (linha ~207,
// alerta de taxa de falha) — a contagem esperada aqui é 2, não 1, por causa
// dessa ocorrência PRÉ-EXISTENTE (não confundir com regressão).
ok('rótulo "Alerta de gasto (IA gerenciada)" aparece 1x', contar("Alerta de gasto (IA gerenciada)") === 1);
ok('estado "não configurado" aparece 1x', contar('"não configurado"') === 1);
ok('estado "sem base de comparação" aparece 1x', contar('"sem base de comparação"') === 1);
ok('estado "dentro do normal" aparece 2x (1 pré-existente no card brapi + 1 novo)', contar('"dentro do normal"') === 2);
ok('label do campo "Limiar de alerta de gasto (%)" aparece 1x', contar("Limiar de alerta de gasto (%)") === 1);
ok('label do campo "Janela de comparação (dias)" aparece 1x', contar("Janela de comparação (dias)") === 1);

// ─── leitura do payload ─────────────────────────────────────────────────────
ok("lê data.alertaGastoIA", /data\??\.alertaGastoIA/.test(appAdmin));

// ─── os 4 estados existem, tom warn no cruzamento — NUNCA negative ─────────
const idxInicio = appAdmin.indexOf("const alertaGasto");
const idxFim = appAdmin.indexOf('<Kv label="Alerta de gasto (IA gerenciada)"');
ok("bloco de cálculo do alerta encontrado (const alertaGasto ... Kv de render)", idxInicio !== -1 && idxFim > idxInicio);
if (idxInicio !== -1 && idxFim > idxInicio) {
  const bloco = appAdmin.slice(idxInicio, idxFim + 200);
  ok('estado "não configurado" usa tom "faint"', /"não configurado",\s*tone:\s*"faint"/.test(bloco));
  ok('estado "sem base de comparação" usa tom "faint"', /"sem base de comparação"[^,]*,\s*tone:\s*"faint"/.test(bloco));
  ok('estado "acima" usa tom "warn"', /tone:\s*"warn"/.test(bloco));
  ok('estado "dentro do normal" usa tom "positive"', /"dentro do normal",\s*tone:\s*"positive"/.test(bloco));
  ok('NUNCA usa tom "negative" no bloco do alerta preventivo (regressão-alvo: fundir com o hard stop)', !/tone:\s*"negative"/.test(bloco));
}

// ─── Kv ganhou o tom "faint" ────────────────────────────────────────────────
ok('Kv aceita tone "faint"', /tone === "faint" \? T\.faint/.test(appAdmin));

// ─── campos novos de config: numéricos + entram no laço de salvar ─────────
// [^"]*" casa cada argumento string inteiro sem parar em "(%)" (o label do
// primeiro campo contém parênteses literais, que quebrariam um [^)]* ingênuo).
ok('campo("llmAlertaGastoPct", ...) existe com numerico=true',
   /campo\("llmAlertaGastoPct",\s*"[^"]*",\s*"[^"]*",\s*true\)/.test(appAdmin));
ok('campo("llmAlertaJanelaDias", ...) existe com numerico=true',
   /campo\("llmAlertaJanelaDias",\s*"[^"]*",\s*"[^"]*",\s*true\)/.test(appAdmin));
ok('llmAlertaGastoPct entra no laço numérico de salvar',
   /for \(const k of \[[^\]]*"llmAlertaGastoPct"[^\]]*\]\)/.test(appAdmin));
ok('llmAlertaJanelaDias entra no laço numérico de salvar',
   /for \(const k of \[[^\]]*"llmAlertaJanelaDias"[^\]]*\]\)/.test(appAdmin));

// ─── nenhuma permissão nova em MudancaDeLLM — só llm.configurar ───────────
const idxComponente = appAdmin.indexOf("function MudancaDeLLM(");
const idxProximaFuncao = appAdmin.indexOf("\nfunction ", idxComponente + 1);
ok("componente MudancaDeLLM encontrado", idxComponente !== -1 && idxProximaFuncao > idxComponente);
if (idxComponente !== -1 && idxProximaFuncao > idxComponente) {
  const corpo = appAdmin.slice(idxComponente, idxProximaFuncao);
  const permissoes = corpo.match(/"[a-z_]+\.[a-z_]+"/g) || [];
  const distintas = [...new Set(permissoes)];
  ok('MudancaDeLLM cita só "llm.configurar" como permissão', distintas.length === 1 && distintas[0] === '"llm.configurar"');
}

console.log(fails === 0 ? "\nTODOS OS TESTES PASSARAM" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
