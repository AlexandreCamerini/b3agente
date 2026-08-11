// ADR-008 — princípio #3 do CLAUDE.md: "dados de mercado exibem fonte,
// horário da última atualização e se são em tempo real, atrasados ou
// históricos." O backend já mandava `source` em todo payload de cotação
// desde a Fase 5, mas nada na UI mostrava. Guardião: trava a legenda de
// fonte no card do preço e a seção "FONTE DE COTAÇÕES" no painel de
// Administração (que já buscava admin.usoIA.candles e nunca renderizava).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 1) FONTE_LABEL existe e mapeia os dois provedores conhecidos
ok("FONTE_LABEL existe", appSrc.includes("const FONTE_LABEL"));
ok("FONTE_LABEL mapeia brapi", /source === "brapi" \? "brapi"/.test(appSrc));
ok("FONTE_LABEL mapeia yahoo pra 'Yahoo'", /source === "yahoo" \? "Yahoo"/.test(appSrc));

// 2) badge de fonte no card do preço (AtivoCard) — cobre os dois ramos:
//    cotação viva (q.change != null) e fallback de fechamento
ok("legenda de fonte no ramo de cotação viva",
  /!q\.error && q\.change != null && q\.source[\s\S]{0,220}FONTE_LABEL\(q\.source\)/.test(appSrc));
ok("legenda de fonte junto do fallback 'fechamento'",
  /no período · fechamento\{q\.source \? " · " \+ FONTE_LABEL\(q\.source\) : ""\}/.test(appSrc));

// 3) seção nova no painel de Administração, lendo o que já era buscado
//    (admin.usoIA.candles) — v1 SÓ VER, mesmo portão de admin de sempre
const adminBlock = appSrc.slice(appSrc.indexOf("PAINEL DE ADMINISTRAÇÃO"), appSrc.indexOf("PAINEL DE ADMINISTRAÇÃO") + 6000);
ok("seção FONTE DE COTAÇÕES existe no painel admin", adminBlock.includes("FONTE DE COTAÇÕES"));
ok("lê admin.usoIA.candles (dado que já era buscado, nunca renderizado)",
  adminBlock.includes("admin.usoIA.candles"));
ok("mostra provedor + fallback", /provedor: \{FONTE_LABEL\(c\.provedor\)\}/.test(adminBlock));
ok("mostra orçamento (teto/dia, cota/mês)", /orçamento brapi: \{orc\.total\}\/\{orc\.tetoDia\}/.test(adminBlock));
ok("mostra intervalo do spot vigente", /intervalo do spot: \{orc\.spotIntervaloS\}s/.test(adminBlock));
ok("mostra projeção do mês e marca quando NÃO CABE",
  /projeção do mês:.*NÃO CABE/.test(adminBlock));
ok("degrada sem orçamento (Yahoo primário) — orc é opcional, nunca quebra",
  /\{orc && \(/.test(adminBlock));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
