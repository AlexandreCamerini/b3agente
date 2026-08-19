// Fase 3, C-36 — Guardião estático do painel "Orçamento brapi (ADR-008)"
// (web-admin/src/App.jsx).
//
// Origem: o incidente de 31/07/2026 foi HTTP 200 com ZERO velas por 2 horas
// de pregão — o painel só lia `erros` (não-200), então mostrava "Erros: 0" e
// o problema real ficava invisível. `candle_provider.snapshot()` já devolvia
// `vazios`/`taxaFalha`/`alerta`/`limiarAlerta` no payload; ninguém no front
// lia. Este teste trava que:
//   • as 3 linhas novas existem, com o texto LITERAL do Copywriting Contract;
//   • `vazios` é lido do payload e NUNCA somado/fundido com `erros` — fundir
//     os dois reintroduz a mesma cegueira do incidente;
//   • a linha antiga "Erros (janela 3 dias)" continua existindo (as duas
//     métricas coexistem, a nova não substitui a antiga);
//   • o tom do alerta usa "negative" quando `alerta` é true e "positive"
//     caso contrário.
//
// Roda sem build: `node web/tests/test_fase3_custos_falha_brapi.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ─── os 3 rótulos literais do Copywriting Contract ─────────────────────────
const rotulos = [
  "Respostas vazias (200 sem vela, janela 3 dias)",
  "Taxa de falha (erros + vazios / requisições, 3 dias)",
  "Alerta do provedor primário",
];
for (const rotulo of rotulos) {
  const ocorrencias = appAdmin.split(rotulo).length - 1;
  ok(`rótulo aparece 1x: "${rotulo}"`, ocorrencias === 1);
}

// ─── os 4 campos do payload são lidos ──────────────────────────────────────
ok("lê data.candles.vazios", /data\.candles\.vazios/.test(appAdmin));
ok("lê data.candles.taxaFalha", /data\.candles\.taxaFalha/.test(appAdmin));
ok("lê data.candles.alerta", /data\.candles\.alerta/.test(appAdmin));
ok("lê data.candles.limiarAlerta", /data\.candles\.limiarAlerta/.test(appAdmin));

// ─── vazios nunca é somado/fundido com erros no CÓDIGO ─────────────────────
// É a razão de ser do achado: se alguém "simplificar" isto num contador só,
// o incidente de 31/07 volta a ler "0 erros" na próxima vez que acontecer.
// A checagem mira a EXPRESSÃO (leitura dos campos somados), não o rótulo em
// texto — o Copywriting Contract exige que o rótulo da taxa de falha CITE
// "erros + vazios" em prosa (é a fórmula explicada ao admin), o que é
// diferente de fundir os dois números num único contador no código.
ok("vazios NÃO é somado a erros no código (nenhum `candles.erros + ... candles.vazios`)",
   !/candles\.erros\s*\+\s*[^;\n]*candles\.vazios/.test(appAdmin));
ok("vazios NÃO é somado a erros no código (nenhum `candles.vazios + ... candles.erros`)",
   !/candles\.vazios\s*\+\s*[^;\n]*candles\.erros/.test(appAdmin));

// ─── a linha antiga de erros continua existindo, intacta ──────────────────
ok('EventoComSerie "Erros (janela 3 dias)" continua existindo',
   (appAdmin.split("Erros (janela 3 dias)").length - 1) === 1);
ok('linha antiga de erros ainda usa data.candles.erros (não foi fundida)',
   /label="Erros \(janela 3 dias\)" value=\{data\.candles\.erros/.test(appAdmin));

// ─── tom do alerta: negative quando alerta, positive caso contrário ───────
const idxAlertaRow = appAdmin.indexOf('label="Alerta do provedor primário"');
ok('linha "Alerta do provedor primário" encontrada no fonte', idxAlertaRow !== -1);
if (idxAlertaRow !== -1) {
  const fimLinha = appAdmin.indexOf("\n", idxAlertaRow);
  const trecho = appAdmin.slice(idxAlertaRow, fimLinha === -1 ? undefined : fimLinha);
  ok('tom "negative" quando data.candles.alerta', /tone=\{data\.candles\.alerta[^}]*"negative"/.test(trecho));
  ok('tom "positive" quando NÃO alerta', /"positive"/.test(trecho));
}

// ─── as três linhas novas vivem dentro do Card "Orçamento brapi (ADR-008)",
// logo após o EventoComSerie de erros — não um Card novo, não fora do bloco.
const idxCard = appAdmin.indexOf('Card title="Orçamento brapi (ADR-008)"');
const idxErros = appAdmin.indexOf("Erros (janela 3 dias)", idxCard);
const idxVazios = appAdmin.indexOf("Respostas vazias (200 sem vela, janela 3 dias)", idxCard);
const idxProximoCard = appAdmin.indexOf('Card title="Cache de candles (L2)"', idxCard);
ok("Card correto encontrado", idxCard !== -1 && idxProximoCard !== -1);
ok("linha de vazios vem DEPOIS da linha de erros existente", idxErros !== -1 && idxVazios > idxErros);
ok("todas as linhas novas ficam dentro do mesmo Card (antes do próximo Card)",
   idxVazios !== -1 && idxVazios < idxProximoCard);

console.log(fails === 0 ? "\nTODOS OS TESTES PASSARAM" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
