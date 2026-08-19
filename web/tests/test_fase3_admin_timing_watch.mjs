// Fase 3, C-35 — Guardião estático do portal admin: kill-switch do push de
// gatilho (timing_watch), par irmão do kill-switch do agente (ADR-013).
//
// Origem: `timing_watch.kill_switch_on()` lia SÓ a env `B3_TIMING_PUSH_KILL`,
// nenhuma das abas do portal mostrava o estado, e nenhuma rota o expunha —
// se ligado por engano, o aviso de gatilho parava para TODA a base e o único
// caminho de volta era redeploy. É o mesmo padrão de risco que já produziu o
// incidente do kill-switch do agente (ligado sem querer, execução automática
// parada por 2,5 dias).
//
// Este teste trava que:
//   • os dois métodos novos existem em api.js, com os caminhos exatos;
//   • o componente TimingWatchKillSwitchBox existe;
//   • as 6 strings literais de copy do Copywriting Contract aparecem 1x cada;
//   • o gate execucao_automatica.controlar é verificado dentro do componente
//     novo (nenhuma permissão nova é criada);
//   • há um window.confirm dentro do componente novo;
//   • o KPI "PUSH DO GATILHO" existe em VisaoGeral;
//   • o componente novo NÃO usa T.accent (não é ação primária/branding);
//   • KillSwitchBox (o box antigo) continua existindo e sendo renderizado em
//     Automacao — o novo é um PAR, não uma substituição.
//
// Roda sem build: `node web/tests/test_fase3_admin_timing_watch.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");
const apiAdmin = readFileSync(join(raiz, "web-admin", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ─── api.js: os dois métodos novos, com os caminhos exatos ─────────────────
ok('api.js tem timingWatchKillSwitchGet apontando pro caminho exato',
   /timingWatchKillSwitchGet:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/admin\/timing-watch\/kill-switch"\)/.test(apiAdmin));
ok('api.js tem timingWatchKillSwitchPut apontando pro caminho exato',
   /timingWatchKillSwitchPut:\s*\(on\)\s*=>\s*req\("PUT",\s*"\/api\/admin\/timing-watch\/kill-switch",\s*\{\s*on\s*\}\)/.test(apiAdmin));

// ─── App.jsx: o componente novo existe ──────────────────────────────────────
ok("componente TimingWatchKillSwitchBox existe",
   /function TimingWatchKillSwitchBox\(/.test(appAdmin));

// Região do componente novo (do function até o próximo `function `) — usada
// pra checar gate de permissão, window.confirm e ausência de T.accent SÓ
// dentro dele, sem falso positivo/negativo do resto do arquivo.
const idxInicio = appAdmin.indexOf("function TimingWatchKillSwitchBox");
ok("início do componente encontrado", idxInicio !== -1);
const idxProximaFuncao = appAdmin.indexOf("\nfunction ", idxInicio + 1);
ok("próxima função (fim do componente) encontrada", idxProximaFuncao !== -1 && idxProximaFuncao > idxInicio);
const regiaoBox = idxInicio !== -1 && idxProximaFuncao !== -1
  ? appAdmin.slice(idxInicio, idxProximaFuncao)
  : "";
ok("região do componente tem tamanho plausível (não vazia/truncada)", regiaoBox.length > 400);

ok('gate execucao_automatica.controlar verificado dentro do componente novo',
   /execucao_automatica\.controlar/.test(regiaoBox));
ok('window.confirm presente dentro do componente novo',
   /window\.confirm\(/.test(regiaoBox));
ok('componente novo NÃO usa T.accent (não é ação primária/branding)',
   !/T\.accent/.test(regiaoBox));

// ─── as 6 strings literais do Copywriting Contract, 1x cada ────────────────
const rotulos = [
  "Kill-switch do push de gatilho (timing_watch)",
  "LIGADO (push do gatilho parado)",
  "desligado (push do gatilho roda normalmente)",
  "Override em runtime sobre a env B3_TIMING_PUSH_KILL — some no próximo deploy só se ninguém mexer aqui de novo.",
  "Desligar o kill-switch do push de gatilho? O aviso de gatilho volta a ser enviado normalmente.",
  "Ligar o kill-switch do push de gatilho? Nenhum aviso de gatilho será enviado a ninguém enquanto estiver ligado.",
];
for (const rotulo of rotulos) {
  const ocorrencias = appAdmin.split(rotulo).length - 1;
  ok(`copy aparece 1x: "${rotulo.slice(0, 60)}${rotulo.length > 60 ? "…" : ""}"`, ocorrencias === 1);
}

// Botão e fallback de permissão reaproveitam o MESMO texto de KillSwitchBox
// (não são literais novos exclusivos deste componente) — checar presença
// dentro da região, não unicidade global.
ok('botão "Aplicando…" presente no componente novo', /Aplicando…/.test(regiaoBox));
ok('botão "Desligar kill-switch" presente no componente novo', /Desligar kill-switch/.test(regiaoBox));
ok('botão "Ligar kill-switch" presente no componente novo', /Ligar kill-switch/.test(regiaoBox));
ok('fallback de permissão presente no componente novo',
   /Sem permissão para alternar \(requer execucao_automatica\.controlar\)\./.test(regiaoBox));

// ─── VisãoGeral: o KPI novo ─────────────────────────────────────────────────
ok('KPI "PUSH DO GATILHO" existe em VisaoGeral', (appAdmin.split("PUSH DO GATILHO").length - 1) === 1);
ok('KPI novo lê data.timingWatchKillSwitch',
   /label="PUSH DO GATILHO"[^>]*value=\{data\.timingWatchKillSwitch/.test(appAdmin) ||
   /value=\{data\.timingWatchKillSwitch[^}]*\}[^>]*label="PUSH DO GATILHO"/.test(appAdmin) ||
   /Kpi label="PUSH DO GATILHO" value=\{data\.timingWatchKillSwitch/.test(appAdmin));

// ─── par casado: KillSwitchBox continua existindo, o novo entra logo depois
ok("KillSwitchBox (antigo) continua existindo (definição)",
   /function KillSwitchBox\(/.test(appAdmin));
ok('KillSwitchBox (antigo) continua com título "Kill-switch do Operador (execução automática)"',
   (appAdmin.split("Kill-switch do Operador (execução automática)").length - 1) === 1);
ok("KillSwitchBox continua renderizado em Automacao",
   /<KillSwitchBox user=\{user\} \/>/.test(appAdmin));
ok("TimingWatchKillSwitchBox é renderizado em Automacao",
   /<TimingWatchKillSwitchBox user=\{user\} \/>/.test(appAdmin));

const idxKillSwitchUso = appAdmin.indexOf("<KillSwitchBox user={user} />");
const idxTimingWatchUso = appAdmin.indexOf("<TimingWatchKillSwitchBox user={user} />");
ok("TimingWatchKillSwitchBox é renderizado IMEDIATAMENTE após KillSwitchBox (par casado)",
   idxKillSwitchUso !== -1 && idxTimingWatchUso !== -1 &&
   appAdmin.slice(idxKillSwitchUso + "<KillSwitchBox user={user} />".length, idxTimingWatchUso).trim() === "");

console.log(fails === 0 ? "\nTODOS OS TESTES PASSARAM" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
