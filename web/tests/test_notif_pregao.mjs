// Quick task 260824-i45 (item 5) — Guardião: notificação LOCAL só com o pregão
// CONFIRMADO aberto.
//
// O DEFEITO: o laço de stop/alvo/variação dispara a cada mudança de `quotes`,
// sem nenhuma noção de horário — inclusive com cotação stale de madrugada. Não
// existe (e não é para existir) equivalente de `pregao.in_market_hours` em
// `web/src/`: o único juiz é o backend, via `/api/market/status`, cujo estado o
// root já mantém em `mercado`. O segundo alvo era o recap de boot, que emitia
// banner de SISTEMA a qualquer hora, sobre eventos de horas antes.
//
// Padrão source-grep (mesmo de test_notif_central.mjs): lê `App.jsx` como
// texto, recorta chunks por âncoras e roda regex. Sem render, sem build.
// FALHA RUIDOSAMENTE se uma âncora não for encontrada — chunk vazio é teste
// mudo, exatamente a falha silenciosa que este guardião não pode ter.
//
// Roda sem build: `node web/tests/test_notif_pregao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Toda asserção de ORDEM ou de AUSÊNCIA roda sobre o CÓDIGO, nunca sobre a
// prosa: os comentários que justificam a guarda citam `notifRef.current[p.t]` e
// `notify.send` de propósito (é neles que a decisão fica registrada), e sem
// isto o guardião acusaria a própria explicação. A negativa de `[^:]` preserva
// `https://` — só o comentário de linha cai.
const semComentarios = (s) => s.split("\n")
  .map((l) => l.replace(/(^|[^:])\/\/.*$/, "$1"))
  .join("\n");
const appCode = semComentarios(app);

function chunk(de, ate, rotulo) {
  const i = app.indexOf(de);
  const j = i >= 0 ? app.indexOf(ate, i) : -1;
  ok(`âncora inicial do chunk ${rotulo} existe (${JSON.stringify(de)})`, i >= 0);
  ok(`âncora final do chunk ${rotulo} existe (${JSON.stringify(ate)})`, j > i);
  return i >= 0 && j > i ? app.slice(i, j) : "";
}

// ---- 1) o laço de notificação local -----------------------------------------
const laco = chunk("const notifRef = useRef({});", "// Tela de abertura", "do laço");
ok("chunk do laço é não-vazio", laco.length > 0);

// A asserção é sobre a LINHA LITERAL do early return, não sobre dois tokens
// soltos: `indexOf("mercado.aberto") < indexOf("notifRef.current")` passaria
// num refactor que move a guarda para um `continue` dentro do `for` — e um
// `continue` depois de `const st = notifRef.current[p.t] || (... = {...})` já
// teria criado a entrada e CONSUMIDO o `armado`, destruindo o invariante que
// esta guarda existe para preservar.
const lacoCode = semComentarios(laco);
const iGuarda = lacoCode.indexOf("if (!pregaoAberto) return;");
const iRef = lacoCode.indexOf("notifRef.current[p.t]");
ok("guarda de pregão é um early return literal", iGuarda >= 0);
ok("o return vem ANTES de tocar notifRef.current[p.t] (preserva o armado)",
  iGuarda >= 0 && iRef > iGuarda);

ok("pregaoAberto deriva de mercado.aberto (fonte canônica do backend)",
  lacoCode.includes("mercado.aberto") && /const pregaoAberto\s*=/.test(lacoCode));
ok("estado indeterminado (null / { erro: true }) não é tratado como aberto",
  /!!\(mercado && !mercado\.erro && mercado\.aberto\)/.test(lacoCode));
ok("`mercado` está na dep array do efeito (o aviso represado sai quando o estado resolve)",
  lacoCode.includes("}, [quotes, data, mercado]);"));

// O front NÃO reimplementa o calendário da B3 (feriado fixo e móvel moram em
// server/app/pregao.py). Qualquer horário hardcodado aqui é regressão.
ok("nenhum cálculo de horário local no laço (getHours/getDay)",
  !/getHours\(|getDay\(/.test(lacoCode));
ok("nenhum literal de horário de pregão no laço (10:00 / 16:55)",
  !lacoCode.includes("10:00") && !lacoCode.includes("16:55"));

// As três chamadas de copy continuam DENTRO do chunk — ou seja, atrás da
// guarda. Mover qualquer uma para fora quebraria também
// web/tests/test_copy_theme.mjs:120.
for (const fn of ["cp.notifStopTitulo(", "cp.notifAlvoTitulo(", "cp.notifVarTitulo("]) {
  ok(`${fn} continua dentro do laço (atrás da guarda)`, lacoCode.includes(fn));
}

// ---- 2) o recap de boot não emite banner de sistema --------------------------
const recap = chunk("const agentSummaryDone", "// FASE 2: ao abrir, se houver sessão salva", "do recap de boot");
ok("chunk do recap de boot é não-vazio", recap.length > 0);
const recapCode = semComentarios(recap);
ok("recap de boot NÃO chama notify.send (roda no boot, a qualquer hora)",
  !recapCode.includes("notify.send"));
// A informação NÃO se perde: `flash` continua mostrando in-app (e no nativo o
// próprio notify.send já caía no mesmo _emitForeground → handler do App).
ok("os DOIS flash( do recap continuam existindo (a informação fica)",
  (recapCode.match(/flash\(/g) || []).length === 2);

// ---- 3) não regredir guardiões vizinhos --------------------------------------
ok("notifRef.current = {} continua existindo (reset de escopo no logout)",
  appCode.includes("notifRef.current = {}"));
ok("store.marketStatus( continua aparecendo 1x (a guarda CONSOME o estado, não consulta)",
  (appCode.match(/store\.marketStatus\(/g) || []).length === 1);
ok("sobra exatamente 1 notify.send em App.jsx (a confirmação do próprio toggle)",
  (appCode.match(/notify\.send\(/g) || []).length === 1);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);