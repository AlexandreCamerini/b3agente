// qa/47 (Fase 2) — ancoragem da instrumentação dos 12 eventos da taxonomia
// (server/app/analytics.py aceita qualquer nome; a disciplina de QUAIS
// eventos o app manda vive só aqui, no client). Mesmo padrão de
// test_config_debounce_flush.mjs: lê o texto-fonte, não executa a UI.
// Roda sem build: `node web/tests/test_analytics_instrumentacao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const count = (re) => (src.match(re) || []).length;

ok("importa track/setAnalyticsUser/flush de analytics.js",
   /import \{ track, setAnalyticsUser, flush as flushAnalytics \} from "\.\/analytics\.js";/.test(src));

// --- os 12 eventos da taxonomia (qa/47) — cada um precisa de PELO MENOS 1
// call site de track() no código real, não só em comentário -----------------
const EVENTOS = [
  "onboarding_step_completed", "portfolio_view", "radar_scan_run", "radar_result_opened",
  "setup_alert_shown", "setup_alert_opened", "options_chain_view", "trade_simulated",
  "coach_tip_shown", "coach_tip_dismissed", "notification_tapped", "session_start", "session_end",
];
for (const ev of EVENTOS) {
  ok(`evento "${ev}" tem track() no código`, new RegExp(`track\\("${ev}"`).test(src));
}

// --- trade_simulated cobre compra E venda, ação E opção ---------------------
// Fase 2 (02-06, MERC-02/03): confirmBuy/confirmSell passaram a acrescentar
// `pendente: !!s.pendente`/`pendente: !!st.pendente` ao evento — sem isto a
// analítica confundiria uma ordem PENDENTE (mercado fechado, nada executou
// ainda) com uma compra/venda concluída. Guardião atualizado de propósito
// (nota exigida por CLAUDE.md: "guardiões não se apagam, reversão
// deliberada atualiza com nota") — o shape de ação/opção continua exato
// porque buyOption/sellOption não passam por ordem pendente.
ok("trade_simulated: compra de ação (confirmBuy)", /track\("trade_simulated", \{ side: "buy", ticker: bm\.t, instrument: "equity", pendente: !!s\.pendente \}\)/.test(src));
ok("trade_simulated: venda de ação (confirmSell)", /track\("trade_simulated", \{ side: "sell", ticker: sm\.t, instrument: "equity", pendente: !!st\.pendente \}\)/.test(src));
ok("trade_simulated: compra de opção (buyOption)", /track\("trade_simulated", \{ side: "buy", ticker: underlying, instrument: "option" \}\)/.test(src));
ok("trade_simulated: venda de opção (sellOption)", /track\("trade_simulated", \{ side: "sell", contract: contractId, instrument: "option" \}\)/.test(src));

// --- coach_tip: shown/dismissed só contam a via PROATIVA (openConceito),
// nunca abertura manual (abrirSetor) — regressão aqui confundiria as duas.
ok("coach_tip_shown dispara dentro de openConceito", /openConceito: \(cid, dados\) => \{\s*track\("coach_tip_shown", \{ cid \}\);/.test(src));
ok("openConceito marca viaProativa no estado", /setConceitoAberto\(\{ cid, dados: dados \|\| null, trilha: \[\], viaProativa: true \}\)/.test(src));
ok("closeConceito só dispara dismissed quando viaProativa é true (não em abertura manual)",
   /closeConceito: \(\) => setConceitoAberto\(\(c\) => \{\s*if \(c && c\.viaProativa\) track\("coach_tip_dismissed", \{ cid: c\.cid \}\);/.test(src));
ok("abrirSetor (abertura MANUAL) não seta viaProativa — não pode virar coach_tip",
   !/setConceitoAberto\(\{ cid, dados: dados \|\| null, trilha: \[\], setor: setorId, viaProativa/.test(src));

// --- session_end sempre flusheia a fila (iOS pode matar o processo logo
// depois de ir a background — sem isso o lote fica preso no aparelho) -------
ok("session_end chama flushAnalytics() no mesmo branch", count(/track\("session_end"\); flushAnalytics\(\);/g) === 2);

// --- identidade do usuário de analytics segue login/logout ------------------
ok("setAnalyticsUser no login/register/oauth (3 pontos)", count(/setAuthUser\(r\.user\); setAnalyticsUser\(r\.user\.id\); \}/g) === 3);
ok("setAnalyticsUser na restauração de sessão do boot", /setAuthUser\(r\.user\);\s*\n\s*setAnalyticsUser\(r\.user\.id\);/.test(src));
ok("setAnalyticsUser\\(null\\) no logout/deleteAccount (2 pontos)", count(/setAnalyticsUser\(null\); \/\/ qa\/47 \(Fase 2\)/g) === 2);

console.log(fails ? `\n${fails} FALHA(S) NA INSTRUMENTAÇÃO DE ANALYTICS` : "\nINSTRUMENTAÇÃO DE ANALYTICS OK");
process.exit(fails ? 1 : 0);
