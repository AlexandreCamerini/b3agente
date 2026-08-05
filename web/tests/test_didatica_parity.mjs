// Camada de entendimento (Fase 1) — PARIDADE DOS DOIS STORES e o consentimento
// do push do gatilho.
//
// O achado que originou estes guardiões (revisão do supervisor, 2026-08-05):
// no aparelho, `deviceStore.putConfig` grava em localStorage e NUNCA chama a
// API. Ou seja, o servidor não enxerga `notif`, `appMode` nem `watchlist` de
// quem está no iPhone — que é exatamente a audiência do APNs. Um push decidido
// pela `config` avisaria sobre ativos removidos, no vocabulário errado, e
// ignoraria o interruptor desligado.
//
// A correção: o único caminho que SEMPRE chega ao servidor (o registro do
// token) passa a carregar consentimento + modo + universo. Estes testes travam
// isso — se alguém voltar a mandar só o token, o push volta a mentir.
//
// Roda sem build: `node web/tests/test_didatica_parity.mjs`.
import assert from "node:assert";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------ cliente HTTP
ok("api.conceitos chama GET /api/conceitos com o modo",
   /conceitos: \(modo, resumido\) => req\("GET", "\/api\/conceitos\?modo="/.test(apiSrc));
ok("api.conceito chama POST /api\/conceito\/{id} (corpo leva os números do card)",
   /conceito: \(cid, body\) => req\("POST", "\/api\/conceito\/"/.test(apiSrc));
ok("api.assistente usa o timeout de LLM (não os 15 s das rotas baratas)",
   /assistente: \(body\) => req\("POST", "\/api\/assistente", body \|\| \{\}, TIMEOUT_LLM\)/.test(apiSrc));
// O caminho do iPhone: modelo e chave são LOCAIS. Omitir `config` no corpo é
// exatamente o que produziu "Nenhum modelo de IA configurado" no qa/29.
ok("deviceStore manda `config` no corpo do assistente (caminho do iPhone)",
   /async assistente\(body\) \{[\s\S]*?config: \{ \.\.\.doc\.config \}/.test(persistence));
ok("pushRegisterToken aceita e propaga o extra (prefs/modo/universo)",
   /pushRegisterToken: \(token, extra\) => req\("POST", "\/api\/push\/register-token", \{ token, \.\.\.\(extra \|\| \{\}\) \}\)/.test(apiSrc));

// -------------------------------------------- paridade: método novo nos DOIS
for (const m of ["conceitos", "conceito", "assistente"]) {
  const noDevice = new RegExp("async " + m + "\\(").test(persistence);
  const noServer = new RegExp(m + ": \\(").test(persistence);
  ok(`${m} existe nos DOIS stores (deviceStore e serverStore)`, noDevice && noServer);
}
// `syncPushPrefs` precisa da MESMA ASSINATURA nos dois — não só do mesmo nome.
// App.jsx chama um nome só; um store que exigisse argumento receberia `{}`, o
// servidor não gravaria nada e a chamada devolveria ok. Guardião de nome não
// pega isso: por isso aqui a checagem é sobre o `()` vazio nos dois lados.
ok("syncPushPrefs existe nos DOIS stores COM a mesma assinatura (sem argumento)",
   /async syncPushPrefs\(\) \{ ensure\(\);/.test(persistence)
   && /syncPushPrefs: async \(\) => \{/.test(persistence));
ok("serverStore monta o corpo sozinho (não confia em quem chama)",
   /syncPushPrefs: async \(\) => \{[\s\S]*?const s = await sync\.readState\(\);[\s\S]*?api\.pushRegisterToken\(""/.test(persistence));

// ------------------------------------------------- consentimento do push
ok("deviceStore anexa prefs/modo/universo ao registrar o token",
   /async registerPushToken\(token, extra\) \{[\s\S]*?api\.pushRegisterToken\(token, \{ \.\.\._pushPrefsLocais\(\), \.\.\.\(extra \|\| \{\}\) \}\)/.test(persistence));
ok("consentimento é CONJUNÇÃO: mestre `enabled` E a classe `gatilho`",
   /gatilho: !!\(n\.enabled && n\.gatilho\)/.test(persistence));
ok("universo = watchlist + tickers com posição aberta",
   /for \(const t of \(doc\.watchlist \|\| \[\]\)\)/.test(persistence)
   && /for \(const p of \(doc\.positions \|\| \[\]\)\)/.test(persistence));
ok("syncPushPrefs reenvia as prefs sem token (interruptor/watchlist mudou)",
   /async syncPushPrefs\(\) \{ ensure\(\); return api\.pushRegisterToken\(""/.test(persistence));
// O universo muda em watchlist, compra, venda e no interruptor. Deixar a UI
// lembrar de sincronizar é garantir que um dia ela esqueça — e esquecer
// significa push sobre a lista de ontem, a falha que isto existe para matar.
ok("o STORE dispara o sync sozinho (a UI não precisa lembrar)",
   (persistence.match(/_agendarSyncPrefs\(\);/g) || []).length >= 5);
ok("o sync automático tem debounce (rajada de compras vira uma chamada só)",
   /let _prefsTimer = null;[\s\S]*?clearTimeout\(_prefsTimer\)/.test(persistence));

// --------------------------------------- allowlist: chave nova nos DOIS lados
// Chave ausente da allowlist é descartada em SILÊNCIO no putConfig — o mesmo
// modo de falha que já queimou o `agent.*`.
ok("notif.gatilho está na allowlist do deviceStore",
   /for \(const k of \["enabled", "stop", "alvo", "agente", "variacao", "gatilho"\]\)/.test(persistence));
ok("notif.gatilho nasce DESLIGADA (classe nova de alerta é opt-in)",
   /doc\.config\.notif\.gatilho = false/.test(persistence)
   && !/gatilho: true/.test(persistence));
ok("conceitosVistos é UNIÃO no deviceStore (dois aparelhos não se apagam)",
   /if \(Array\.isArray\(patch\.conceitosVistos\)\)/.test(persistence)
   && /if \(cid && !atual\.includes\(cid\)\) atual\.push\(cid\)/.test(persistence));
ok("conceitosVistos tem backfill em doc antigo", /doc\.config\.conceitosVistos = \[\]/.test(persistence));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
