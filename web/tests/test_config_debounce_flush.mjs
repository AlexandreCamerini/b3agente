// Guardião do bug confirmado em 2026-08-09: orçamento (e qualquer campo salvo
// pelo mesmo debounce — nome, model, baseUrl, serverUrl, candlePeriod...)
// definido e PERDIDO no restart. Repro relatado: "reinicio o aplicativo do
// zero e coloco 1000000 de valor, ele sempre volta para 10000".
//
// Causa raiz (não era o round-trip com o servidor — persistence.js já
// confirma cash/posições corretamente; o defeito está inteiro na orquestração
// de UI do App.jsx): o debounce de 600ms (`cfgTimer`) só guardava o TIMER,
// nunca o PATCH pendente. Três caminhos descartavam a escrita em silêncio:
//   1. saveConfig() cancelava o timer de OUTRO campo sem nunca enviar o
//      patch dele — editar orçamento e, antes de 600ms, tocar em
//      candlePeriod/provider/model perdia o orçamento sem erro nenhum.
//   2. Sem flush em background/appStateChange: fechar o app dentro da janela
//      de 600ms mata o setTimeout ANTES de ele rodar — nada é escrito. É
//      exatamente o que "reiniciar do zero logo depois de mudar o valor"
//      testa, e por isso o sintoma é "sempre", não intermitente.
//   3. O campo de orçamento não tinha onBlur — ao contrário de
//      model/baseUrl/serverUrl (mesmo padrão editConfig+onBlur=saveConfig),
//      sair do campo não flusheava nada.
//   4. (achado depois do fix acima, mesma entrega) resetPortfolio() não
//      flusheava NADA antes de "Recomeçar do zero" — e é a ação que MAIS
//      depende do orçamento estar em dia: o reset lê `initialBudget` de
//      onde ele estiver persistido NA HORA (DB do servidor, ou doc.config
//      local offline), então digitar um valor novo e tocar em reset antes
//      dos 600ms corria contra o mesmo debounce e reiniciava com o valor
//      VELHO — sem erro, sem aviso.
// Fix: cfgPending (patch acumulado) + flushCfg() como único ponto que decide
// "hora de mandar" — chamado pelo timer, por saveConfig ANTES do próprio
// patch, pelo onBlur do campo, pelo listener de ida a segundo plano, e por
// resetPortfolio ANTES de ler o orçamento salvo.
//
// Roda sem build: `node web/tests/test_config_debounce_flush.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// --- 1) existe um ponto único de flush, e ele NÃO descarta o pendente ------
ok("flushCfg existe como useCallback", /const flushCfg = useCallback\(async \(\) => \{/.test(src));
const flushBody = (() => {
  const i = src.indexOf("const flushCfg = useCallback(async () => {");
  const j = src.indexOf("}, [flash]);", i);
  return i >= 0 && j > i ? src.slice(i, j) : "";
})();
ok("flushCfg body localizado", flushBody.length > 0);
ok("flushCfg lê cfgPending.current (não descarta)", /const pending = cfgPending\.current/.test(flushBody));
ok("flushCfg envia o pendente via store.putConfig", /store\.putConfig\(pending\)/.test(flushBody));

// --- 2) saveConfig flusheia ANTES de aplicar o próprio patch ---------------
// Bug original: `if (cfgTimer.current) { clearTimeout(...); cfgTimer.current = null; }`
// cancelava sem NUNCA chamar store.putConfig do que estava pendente.
const saveConfigMatch = src.match(/saveConfig: async \(patch\) => \{([\s\S]*?)\n\s{4}\},/);
ok("saveConfig localizado", !!saveConfigMatch);
const saveConfigBody = saveConfigMatch ? saveConfigMatch[1] : "";
ok("saveConfig chama flushCfg() antes do próprio patch (não descarta mais)", /await flushCfg\(\)/.test(saveConfigBody));
ok("saveConfig NÃO volta a cancelar o timer sem enviar (regressão do bug original)",
   !/clearTimeout\(cfgTimer\.current\); cfgTimer\.current = null; \} try \{ const s = await store\.putConfig\(patch\)/.test(src));

// --- 3) saveBudget e editConfig acumulam em cfgPending, não só no timer ----
const saveBudgetMatch = src.match(/saveBudget: \(v\) => \{([\s\S]*?)\n\s{4}\},/);
ok("saveBudget localizado", !!saveBudgetMatch);
ok("saveBudget grava o patch em cfgPending.current",
   saveBudgetMatch && /cfgPending\.current = \{ \.\.\.\(cfgPending\.current \|\| \{\}\), initialBudget: v \}/.test(saveBudgetMatch[1]));

const editConfigMatch = src.match(/editConfig: \(patch\) => \{([\s\S]*?)\n\s{4}\},/);
ok("editConfig localizado", !!editConfigMatch);
ok("editConfig grava o patch em cfgPending.current",
   editConfigMatch && /cfgPending\.current = \{ \.\.\.\(cfgPending\.current \|\| \{\}\), \.\.\.patch \}/.test(editConfigMatch[1]));

// --- 4) o campo de orçamento flusheia no blur (paridade com model/baseUrl) -
const budgetFieldMatch = src.match(/Orçamento disponível \(R\$\)[\s\S]{0,900}/);
ok("campo de orçamento localizado", !!budgetFieldMatch);
ok("campo de orçamento tem onBlur={A.flushCfg} (não tinha nenhum onBlur antes)",
   budgetFieldMatch && /onBlur=\{A\.flushCfg\}/.test(budgetFieldMatch[0]));

// --- 5) ida a segundo plano flusheia — cobre "restart perde o valor" -------
const visEffectMatch = src.match(/const onVisible = \(\) => \{([\s\S]*?)\};\s*\n\s*document\.addEventListener\("visibilitychange", onVisible\)/);
ok("listener de visibilitychange localizado", !!visEffectMatch);
ok("visibilitychange flusheia ao ficar oculto (não só recarrega ao voltar)",
   visEffectMatch && /flushCfgRef\.current/.test(visEffectMatch[1]));
ok("appStateChange (nativo) também flusheia ao inativar",
   /CapApp\.addListener\("appStateChange", \(\{ isActive \}\) => \{\s*if \(isActive\) loadState\(\);\s*else if \(flushCfgRef\.current\) flushCfgRef\.current\(\);/.test(src));

// --- 6) flushCfg está nas deps do useMemo(A) — senão a closure fica velha --
const depsMatch = src.match(/\}\), \[data, catalogSel, buyModal, sellModal, keyDraft, refreshQuotes, flash, analysisModel, wlScanLoading, destaque, quotes(.*?)\]\);/);
ok("array de deps do A localizado", !!depsMatch);
ok("flushCfg está nas deps do A", depsMatch && depsMatch[1].includes("flushCfg"));

// --- 7) resetPortfolio flusheia o orçamento pendente ANTES de ler o salvo --
const resetMatch = src.match(/resetPortfolio: async \(\) => \{([\s\S]*?)\n\s{4}\},/);
ok("resetPortfolio localizado", !!resetMatch);
ok("resetPortfolio chama flushCfg() antes de store.resetPortfolio() — reset não pode correr contra o debounce",
   resetMatch && (() => {
     const body = resetMatch[1];
     const iFlush = body.indexOf("flushCfg()");
     const iReset = body.indexOf("store.resetPortfolio()");
     return iFlush >= 0 && iReset >= 0 && iFlush < iReset;
   })());

console.log(fails ? `\n${fails} FALHA(S) NO FLUSH DE CONFIG` : "\nFLUSH DE CONFIG (ORÇAMENTO) OK");
process.exit(fails ? 1 : 0);
