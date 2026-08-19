// Fase 3, C-37 — Guardião estático do portal admin: duração "Ligado há" no
// kill-switch do Operador (agent kill-switch), par visível do alerta ativo
// implementado no backend (agent._alertar_kill_switch).
//
// Origem: o kill-switch ligado em pregão era um sinal 100% PASSIVO — só o
// KPI vermelho denunciava, e alguém precisava abrir a aba e notar. É o
// mesmo padrão de risco que já produziu o incidente real (execução
// automática parada por 2,5 dias sem ninguém notar).
//
// Este teste trava que:
//   • a linha "Ligado há" existe 1x, condicionada a data.on === true;
//   • o texto literal de ressalva (não calculável / ativado por variável de
//     ambiente) aparece 1x — a MESMA ressalva que o push usa;
//   • o limiar de 4h aparece na lógica de tom (negative/warn);
//   • nenhuma linha de histórico ("Desligado há" / "última vez") foi
//     introduzida — só o estado atual, nunca um passado;
//   • TimingWatchKillSwitchBox (plano 03-05) NÃO ganhou a mesma linha —
//     este plano é só do kill-switch do agente, não do timing_watch.
//
// Roda sem build: `node web/tests/test_fase3_admin_duracao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ─── região do KillSwitchBox (agente) — do function até o próximo `function ` ─
const idxInicio = appAdmin.indexOf("function KillSwitchBox(");
ok("início do KillSwitchBox encontrado", idxInicio !== -1);
const idxProximaFuncao = appAdmin.indexOf("\nfunction ", idxInicio + 1);
ok("próxima função (fim do componente) encontrada", idxProximaFuncao !== -1 && idxProximaFuncao > idxInicio);
const regiaoKillSwitchBox = idxInicio !== -1 && idxProximaFuncao !== -1
  ? appAdmin.slice(idxInicio, idxProximaFuncao)
  : "";
ok("região do KillSwitchBox tem tamanho plausível (não vazia/truncada)", regiaoKillSwitchBox.length > 400);

// ─── linha "Ligado há": existe 1x, condicionada a data.on ──────────────────
ok('linha "Ligado há" aparece exatamente 1x em App.jsx',
   (appAdmin.split("Ligado há").length - 1) === 1);
ok('"Ligado há" está dentro da região do KillSwitchBox (agente)',
   regiaoKillSwitchBox.includes("Ligado há"));
ok('a linha "Ligado há" está condicionada a data.on (renderização condicional)',
   /\{data\.on\s*&&\s*<Kv label="Ligado há"/.test(regiaoKillSwitchBox));

// ─── ressalva de não-rastreabilidade: MESMO texto do push, aparece 1x ──────
const ressalva = "não calculável (ativado por variável de ambiente — sem registro de auditoria)";
ok(`ressalva literal aparece exatamente 1x: "${ressalva}"`,
   (appAdmin.split(ressalva).length - 1) === 1);
ok("ressalva está dentro da região do KillSwitchBox (agente)",
   regiaoKillSwitchBox.includes(ressalva));

// ─── limiar de 4h na lógica de tom ──────────────────────────────────────────
ok('limiar de 4h presente na lógica de tom (regex ">= 4")',
   />=\s*4/.test(regiaoKillSwitchBox));
ok('tom "negative" e "warn" ambos referenciados na lógica de duração',
   /"negative"/.test(regiaoKillSwitchBox) && /"warn"/.test(regiaoKillSwitchBox));

// ─── nenhuma linha de histórico foi introduzida (só estado atual) ──────────
ok('nenhuma linha "Desligado há" foi introduzida',
   !/Desligado há/.test(appAdmin));
ok('nenhuma referência a "última vez" foi introduzida',
   !/última vez/.test(appAdmin));

// ─── fronteira: TimingWatchKillSwitchBox NÃO ganhou a mesma linha ──────────
const idxTimingWatchInicio = appAdmin.indexOf("function TimingWatchKillSwitchBox(");
ok("início do TimingWatchKillSwitchBox encontrado", idxTimingWatchInicio !== -1);
const idxTimingWatchFim = appAdmin.indexOf("\nfunction ", idxTimingWatchInicio + 1);
ok("fim do TimingWatchKillSwitchBox encontrado", idxTimingWatchFim !== -1 && idxTimingWatchFim > idxTimingWatchInicio);
const regiaoTimingWatch = idxTimingWatchInicio !== -1 && idxTimingWatchFim !== -1
  ? appAdmin.slice(idxTimingWatchInicio, idxTimingWatchFim)
  : "";
ok("região do TimingWatchKillSwitchBox tem tamanho plausível", regiaoTimingWatch.length > 400);
ok('"Ligado há" NÃO aparece dentro do TimingWatchKillSwitchBox (fronteira do escopo)',
   !regiaoTimingWatch.includes("Ligado há"));

console.log(fails === 0 ? "\nTODOS OS TESTES PASSARAM" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
