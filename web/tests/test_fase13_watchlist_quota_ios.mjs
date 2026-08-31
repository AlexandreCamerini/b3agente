// Fase 13, Plano 02 — guardião do gate fail-closed do CR-01 (12-REVIEW.md):
// deviceStore.putWatchlist/addWatchlistTicker gravavam direto no localStorage
// sem NENHUM gate — o limite de 10 ativos da Fase 12 só valia no web/PWA. No
// iOS não existe gate autoritativo no servidor para watchlist (o aparelho é a
// fonte da verdade, local-first); a checagem local é a ÚNICA linha de defesa.
//
// Por isso este guardião assere ORDEM (rede antes da escrita), não resultado:
// um `watchlistQuota()` que existisse DEPOIS de `write()` teria o mesmo
// "resultado" superficial (a função chama a API), mas já teria persistido o
// 11º ativo antes de saber se era permitido — reabrindo o CR-01 em silêncio.
// Mesmo raciocínio para o `catch` fail-closed: precisa terminar em `throw`,
// nunca em bloco vazio (fail-open), e a resposta inválida/não-numérica cai no
// MESMO caminho de bloqueio (CLAUDE.md princípio 4 — dado inválido bloqueia).
//
// Padrão "static source inspection" da casa (mesmo de
// test_device_budget_sync.mjs / test_fase5_gate_mensal_front.mjs):
// readFileSync + regex/índice sobre o fonte, sem Vitest/Jest e sem fetch real.
// Roda sem build: `node web/tests/test_fase13_watchlist_quota_ios.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const srcPersistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const srcPlan = readFileSync(join(here, "..", "src", "plan.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

const addBody = bodyOf(srcPersistence, "async addWatchlistTicker(ticker)");
const putBody = bodyOf(srcPersistence, "async putWatchlist(tickers)");

ok("deviceStore.addWatchlistTicker localizado", !!addBody);
ok("deviceStore.putWatchlist localizado", !!putBody);

// --- 1) addWatchlistTicker: rede ANTES da escrita ---------------------------
if (addBody) {
  const iQuota = addBody.indexOf("watchlistQuota");
  const iWrite = addBody.indexOf("write()");
  const iWatchlistPush = addBody.indexOf("doc.watchlist = [...doc.watchlist");
  ok("addWatchlistTicker chama watchlistQuota()", iQuota >= 0);
  ok("addWatchlistTicker: watchlistQuota() vem ANTES de write()", iQuota >= 0 && iWrite >= 0 && iQuota < iWrite);
  ok("addWatchlistTicker: watchlistQuota() vem ANTES de doc.watchlist = [...doc.watchlist", iQuota >= 0 && iWatchlistPush >= 0 && iQuota < iWatchlistPush);
}

// --- 1b) addWatchlistTicker: canAddTicker recebe o count LOCAL, não o do servidor
// Achado do code review da Fase 13 (CR-01): `quota.count` vem do servidor e o
// iOS nunca sincroniza a watchlist pra lá (local-first) — passar quota.count
// pro gate deixava o cap sempre desconectado do tamanho real do doc, reabrindo
// o CR-01 em silêncio mesmo com o teste de ORDEM (item 1 acima) passando.
ok(
  "addWatchlistTicker: canAddTicker(doc.watchlist.length, ...) — nunca canAddTicker(quota.count, ...)",
  !!addBody && /canAddTicker\(doc\.watchlist\.length,/.test(addBody) && !/canAddTicker\(quota\.count,/.test(addBody)
);

// --- 2) putWatchlist: rede ANTES da escrita ---------------------------------
if (putBody) {
  const iQuota = putBody.indexOf("watchlistQuota");
  const iWrite = putBody.indexOf("write()");
  ok("putWatchlist chama watchlistQuota()", iQuota >= 0);
  ok("putWatchlist: watchlistQuota() vem ANTES de write()", iQuota >= 0 && iWrite >= 0 && iQuota < iWrite);
}

// --- 3) fail-closed: o catch do GATE de watchlist não é vazio ---------------
// `catch { throw ... }` — nunca `catch { }` / `catch { /* ... */ }` (o padrão
// fail-open de analisesNoMes/aiQuota, que aqui reabriria o CR-01). Escopo
// restrito ao catch que envolve api.watchlistQuota() nos dois gates — outros
// catches pré-existentes no arquivo são fora do escopo deste plano.
function catchBodyAfter(src, marker) {
  const iMarker = src.indexOf(marker);
  if (iMarker < 0) return null;
  const iCatch = src.indexOf("catch", iMarker);
  if (iCatch < 0) return null;
  const open = src.indexOf("{", iCatch);
  if (open < 0) return null;
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

if (addBody) {
  const catchBody = catchBodyAfter(addBody, "await api.watchlistQuota()");
  ok(
    "addWatchlistTicker: catch em torno de api.watchlistQuota() contém throw new Error (fail-closed)",
    !!catchBody && /throw new Error\(/.test(catchBody)
  );
}
if (putBody) {
  const catchBody = catchBodyAfter(putBody, "await api.watchlistQuota()");
  ok(
    "putWatchlist: catch em torno de api.watchlistQuota() contém throw new Error (fail-closed)",
    !!catchBody && /throw new Error\(/.test(catchBody)
  );
}

// --- 4) putWatchlist: só crescimento dispara rede (remoção nunca falha) ----
ok(
  "putWatchlist compara final.length > tamanho atual antes de buscar quota",
  !!putBody && /final\.length\s*>\s*\(doc\.watchlist \|\| \[\]\)\.length/.test(putBody)
);

// --- 4b) putWatchlist: canGrowWatchlistTo recebe final.length (LOCAL), não quota.count
// Espelho da asserção 1b — mesma classe de bug (CR-01) é possível aqui: nada
// impede alguém de trocar `final.length` por `quota.count` neste call site
// irmão sem que nenhum teste existente perceba (achado do 13-VERIFICATION.md,
// não-bloqueante mas mesma causa raiz do CR-01 original).
ok(
  "putWatchlist: canGrowWatchlistTo(final.length, ...) — nunca canGrowWatchlistTo(quota.count, ...)",
  !!putBody && /canGrowWatchlistTo\(final\.length,/.test(putBody) && !/canGrowWatchlistTo\(quota\.count,/.test(putBody)
);

// --- 5) mensagem de indisponibilidade é exata e única -----------------------
const msgIndisponivel = "Não foi possível confirmar o limite do plano agora. Tente de novo.";
const ocorrenciasMsg = srcPersistence.split(msgIndisponivel).length - 1;
ok(
  `mensagem de indisponibilidade exata aparece >= 1x em persistence.js (achado ${ocorrenciasMsg})`,
  ocorrenciasMsg >= 1
);

// --- 6) plan.js sem CTA de upgrade ------------------------------------------
ok("plan.js não contém 'Faça upgrade'", !srcPlan.includes("Faça upgrade"));

// --- 7) nenhum limite hardcodado em persistence.js --------------------------
// Filtra linhas de comentário antes de checar — mesmo cuidado de
// test_fase5_gate_mensal_front.mjs: só remove linhas cujo trim COMEÇA com //.
const linhasSemComentario = srcPersistence.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
ok(
  "persistence.js (sem comentários) não contém maxWatchlist seguido de literal numérico",
  !/maxWatchlist\s*[:=]\s*\d/.test(linhasSemComentario)
);

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
