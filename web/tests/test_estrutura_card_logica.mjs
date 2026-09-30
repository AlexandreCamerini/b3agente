// Guardião — lógica pura do card de Posição estruturada (Fase 45).
// Roda isolado: `node web/tests/test_estrutura_card_logica.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import * as E from "../src/estruturaCard.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// tickersComPernas
ok("tickersComPernas interseção", eq(E.tickersComPernas([{ t: "UGPA3" }, { t: "PETR4" }], [{ underlying: "UGPA3" }, { underlying: "UGPA3" }, { underlying: "VALE3" }]), ["UGPA3"]));
ok("tickersComPernas não-array positions", eq(E.tickersComPernas(null, []), []));
ok("tickersComPernas não-array opções", eq(E.tickersComPernas([{ t: "A" }], undefined), []));

// assinaturaEstrutura
const pos = [{ t: "UGPA3", qty: 1000, avg: 20 }];
const ops = [{ id: "a", underlying: "UGPA3", qty: 10, side: "vendida" }, { id: "b", underlying: "UGPA3", qty: 10, side: "comprada" }];
const base = E.assinaturaEstrutura("UGPA3", pos, ops, true);
ok("assinatura estável", base === E.assinaturaEstrutura("UGPA3", pos, ops, true));
ok("assinatura muda com qty da ação", base !== E.assinaturaEstrutura("UGPA3", [{ t: "UGPA3", qty: 900, avg: 20 }], ops, true));
ok("assinatura muda com avg da ação", base !== E.assinaturaEstrutura("UGPA3", [{ t: "UGPA3", qty: 1000, avg: 21 }], ops, true));
ok("assinatura muda com qty da perna", base !== E.assinaturaEstrutura("UGPA3", pos, [{ ...ops[0], qty: 5 }, ops[1]], true));
ok("assinatura muda com side da perna", base !== E.assinaturaEstrutura("UGPA3", pos, [{ ...ops[0], side: "comprada" }, ops[1]], true));
ok("assinatura muda com id da perna", base !== E.assinaturaEstrutura("UGPA3", pos, [{ ...ops[0], id: "z" }, ops[1]], true));
ok("assinatura muda com operador", base !== E.assinaturaEstrutura("UGPA3", pos, ops, false));
ok("assinatura ignora ordem das pernas", base === E.assinaturaEstrutura("UGPA3", pos, [ops[1], ops[0]], true));
ok("assinatura ignora perna de outro ticker", base === E.assinaturaEstrutura("UGPA3", pos, [...ops, { id: "x", underlying: "VALE3", qty: 1, side: "vendida" }], true));

// estadoLeitura
ok("estadoLeitura sem pernas -> atual", E.estadoLeitura(false, { status: "ok", estrutura: {} }) === "atual");
ok("estadoLeitura undefined -> carregando", E.estadoLeitura(true, undefined) === "carregando");
ok("estadoLeitura carregando", E.estadoLeitura(true, { status: "carregando" }) === "carregando");
ok("estadoLeitura falha", E.estadoLeitura(true, { status: "falha" }) === "falha");
ok("estadoLeitura ok + null -> falha", E.estadoLeitura(true, { status: "ok", estrutura: null }) === "falha");
ok("estadoLeitura ok + estrutura -> estruturada", E.estadoLeitura(true, { status: "ok", estrutura: { nome: "collar" } }) === "estruturada");

// mostraAvisoSemStop
ok("aviso: atual sem stop", E.mostraAvisoSemStop({ stop: null }, "atual") === true);
ok("aviso: carregando suprimido", E.mostraAvisoSemStop({ stop: null }, "carregando") === false);
ok("aviso: falha suprimido", E.mostraAvisoSemStop({ stop: null }, "falha") === false);
ok("aviso: estruturada com stopTexto suprimido", E.mostraAvisoSemStop({ stop: null }, "estruturada", { stopTexto: "x" }) === false);
ok("aviso: estruturada sem stopTexto aparece", E.mostraAvisoSemStop({ stop: null }, "estruturada", { stopTexto: null }) === true);
ok("aviso: com stop nunca", ["atual", "carregando", "falha", "estruturada"].every((m) => E.mostraAvisoSemStop({ stop: 10 }, m, { stopTexto: null }) === false));

// mostraRR
ok("RR com stop e alvo", E.mostraRR({ stop: 1, alvo: 2 }) === true);
ok("RR sem stop", E.mostraRR({ stop: null, alvo: 2 }) === false);
ok("RR sem alvo", E.mostraRR({ stop: 1, alvo: null }) === false);

// tipoPillTravada
ok("pill collar", E.tipoPillTravada({ nome: "collar" }, 1000) === "collar");
ok("pill call coberta padrão", E.tipoPillTravada({ nome: "call_coberta" }, 100) === "padrao");
ok("pill nome null padrão", E.tipoPillTravada({ nome: null }, 100) === "padrao");
ok("pill sem trava", E.tipoPillTravada({ nome: "collar" }, 0) === null && E.tipoPillTravada({ nome: "collar" }, null) === null && E.tipoPillTravada({ nome: "collar" }, undefined) === null);

// ddmmDeIso
ok("ddmm ok", E.ddmmDeIso("2026-10-16") === "16/10");
ok("ddmm null", E.ddmmDeIso(null) === null && E.ddmmDeIso("") === null);
ok("ddmm inválido", E.ddmmDeIso("16/10/2026") === null && E.ddmmDeIso(20261016) === null);

// chipVencimento
const cv = (estado, dias, ref = "2026-09-18") => E.chipVencimento({ estado, vencimentoReferencia: ref, diasParaVencimento: dias });
ok("chip vencida", eq(cv("vencida", -3), { tipo: "vencida", ddmm: "18/09", dias: -3, ambar: false }));
ok("chip hoje", cv("vigente", 0).tipo === "hoje" && cv("vigente", 0).ambar === true);
ok("chip vence 3 âmbar", cv("vigente", 3).tipo === "vence" && cv("vigente", 3).ambar === true);
ok("chip vence 5 âmbar", cv("vigente", 5).ambar === true);
ok("chip vence 6 neutro", cv("vigente", 6).ambar === false);
ok("chip vence 12 neutro", cv("vigente", 12).tipo === "vence" && cv("vigente", 12).ambar === false);
ok("chip negativo sem estado vencida", cv("vigente", -1).tipo === "vencida");
ok("chip premio_indisponivel com 3 dias segue âmbar por dias", cv("premio_indisponivel", 3).ambar === true);
ok("chip sem referência -> null", cv("vigente", 3, null) === null && E.chipVencimento(null) === null);

// régua
ok("domínio ignora não-finitos", eq(E.dominioRegua([10, null, 20, undefined, NaN]), { min: 10, max: 20 }));
ok("domínio <2 valores", E.dominioRegua([10, null]) === null && E.dominioRegua([]) === null);
ok("domínio valores iguais", E.dominioRegua([10, 10]) === null);
const dom = { min: 10, max: 20 };
ok("posRegua mín 8", E.posRegua(10, dom) === 8);
ok("posRegua máx 92", E.posRegua(20, dom) === 92);
ok("posRegua meio 50", E.posRegua(15, dom) === 50);
ok("posRegua clamp", E.posRegua(0, dom) === 8 && E.posRegua(99, dom) === 92);

// tomDoEstado
ok("tom vigente", E.tomDoEstado("vigente") === "linha");
ok("tom atenção", E.tomDoEstado("ate_5_dias") === "atencao" && E.tomDoEstado("exercicio_provavel") === "atencao");
ok("tom info", E.tomDoEstado("premio_indisponivel") === "info");
ok("tom encerrada", E.tomDoEstado("vencida") === "encerrada");
ok("tom desconhecido", E.tomDoEstado("xyz") === "linha");

// executarComTeto
{
  let emVoo = 0, pico = 0;
  const mk = (i, falha) => () => new Promise((res, rej) => {
    emVoo++; pico = Math.max(pico, emVoo);
    setImmediate(() => { emVoo--; falha ? rej(new Error("x" + i)) : res(i); });
  });
  const r = await E.executarComTeto([mk(0), mk(1), mk(2, true), mk(3), mk(4)], 3);
  ok("teto: nunca >3 em voo", pico <= 3 && pico >= 1, "pico=" + pico);
  ok("teto: ordem de entrada", r.length === 5 && r[0].valor === 0 && r[4].valor === 4);
  ok("teto: rejeição não interrompe", r[2].ok === false && r[2].erro.message === "x2" && r[3].ok === true && r[4].ok === true);
  ok("teto: lista vazia", eq(await E.executarComTeto([], 3), []));
}

// Fase 45 (code review WR-01/WR-02): fila única com abandono — comportamento real.
{
  const espera = () => new Promise((r) => setImmediate(r));
  // WR-01: vale() é conferido quando chega a vez, não ao enfileirar.
  {
    const fila = E.criarFilaLeituras(1);
    let vigente = true, chamadas = [];
    let solta;
    const p1 = fila.enfileirar(() => new Promise((res) => { chamadas.push("a"); solta = res; }), () => true);
    const p2 = fila.enfileirar(() => { chamadas.push("b"); return 1; }, () => vigente);
    vigente = false; // a assinatura mudou com "b" ainda na fila
    solta(0);
    const [r1, r2] = await Promise.all([p1, p2]);
    ok("fila WR-01: item superado na fila não chama a API", eq(chamadas, ["a"]) && r2.abandonada === true && r1.ok === true);
    ok("fila WR-01: vaga liberada após abandono", eq(fila.estado(), { ativos: 0, pendentes: 0 }));
  }
  // WR-01: item vigente na vez roda normalmente.
  {
    const fila = E.criarFilaLeituras(2);
    const r = await fila.enfileirar(() => "x", () => true);
    ok("fila: item vigente roda e devolve valor", r.ok === true && r.valor === "x");
  }
  // WR-02: teto global entre enfileiramentos separados (pico <= 3).
  {
    const fila = E.criarFilaLeituras(3);
    let emVoo = 0, pico = 0;
    const mk = () => () => new Promise((res) => { emVoo++; pico = Math.max(pico, emVoo); setImmediate(() => { emVoo--; res(); }); });
    const todos = [];
    for (let i = 0; i < 5; i++) todos.push(fila.enfileirar(mk(), () => true));
    await espera();
    for (let i = 0; i < 4; i++) todos.push(fila.enfileirar(mk(), () => true));
    await Promise.all(todos);
    ok("fila WR-02: teto de 3 vale entre lotes na mesma fila", pico === 3, "pico=" + pico);
  }
  // WR-02: cancelar abandona os pendentes sem chamar a API; o em voo termina.
  {
    const fila = E.criarFilaLeituras(1);
    let chamadas = 0, solta;
    const p1 = fila.enfileirar(() => new Promise((res) => { chamadas++; solta = res; }), () => true);
    const p2 = fila.enfileirar(() => { chamadas++; }, () => true);
    const p3 = fila.enfileirar(() => { chamadas++; }, () => true);
    fila.cancelar();
    solta("fim");
    const [r1, r2, r3] = await Promise.all([p1, p2, p3]);
    ok("fila WR-02: cancelar não dispara pendentes", chamadas === 1 && r2.abandonada && r3.abandonada && r1.valor === "fim");
    const r4 = await fila.enfileirar(() => "depois", () => true);
    ok("fila WR-02: continua utilizável após cancelar", r4.ok === true && r4.valor === "depois");
  }
  // Rejeição e throw síncrono não travam a fila.
  {
    const fila = E.criarFilaLeituras(1);
    const a = await fila.enfileirar(() => Promise.reject(new Error("boom")), () => true);
    const b = await fila.enfileirar(() => { throw new Error("sync"); }, () => true);
    const c = await fila.enfileirar(() => 7, () => true);
    await espera();
    ok("fila: rejeição/throw não travam", a.ok === false && b.ok === false && c.valor === 7 && fila.estado().ativos === 0);
  }
}

// Pós-teste local 45: kicker "só as ações" só com o número das ações presente;
// zero exato é neutro.
ok("kicker so-acoes: acoes numérico", E.kickerResultadoSoAcoes({ total: null, acoes: -9500 }) === true);
ok("kicker so-acoes: acoes null -> neutro", E.kickerResultadoSoAcoes({ total: null, acoes: null }) === false);
ok("kicker so-acoes: sem resultado -> neutro", E.kickerResultadoSoAcoes(null) === false);
ok("sinalResultado: zero/pos/neg/null", E.sinalResultado(0) === "zero" && E.sinalResultado(1) === "pos" && E.sinalResultado(-1) === "neg" && E.sinalResultado(null) === null);

// Fase 45 (code review WR-03): chaves neutras existem nos dois modos e nunca geram "null"/"undefined".
{
  const { copyFor } = await import("../src/copy.js");
  for (const modo of ["educacional", "operador"]) {
    const cp = copyFor(modo);
    const textos = [cp.semPremioPerna, cp.estruturaPremioSoAtual("1,20"), cp.estruturaPernaLinha("", "vendida", "20,00", "20/10").trim()];
    ok("copy WR-03 (" + modo + "): chaves neutras presentes", textos.every((t) => typeof t === "string" && t.length > 0));
    ok("copy WR-03 (" + modo + "): sem null/undefined/NaN, sem espaço inicial", textos.every((t) => !/null|undefined|NaN/.test(t)) && !/^\s/.test(textos[2]));
    ok("copy WR-03 (" + modo + "): prêmio só-atual sem seta", !/→/.test(textos[1]) && !/→/.test(textos[0]));
  }
}

// Fase 45 (code review WR-04): motivo neutro do Encerrar nos dois modos.
{
  const { copyFor } = await import("../src/copy.js");
  for (const modo of ["educacional", "operador"]) {
    const t = copyFor(modo).encerrarSemMotivo;
    ok("copy WR-04 (" + modo + "): encerrarSemMotivo presente e sem null/undefined/NaN", typeof t === "string" && t.length > 0 && !/null|undefined|NaN/.test(t));
  }
}

// pureza estática
const src = readFileSync(fileURLToPath(new URL("../src/estruturaCard.js", import.meta.url)), "utf8");
const codigo = src.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");
ok("sem import de react", !/from\s+["']react["']/.test(codigo));
ok("sem import de persistence/api/App", !/import[^;]*(persistence|\/api|App\.jsx)/.test(codigo));
ok("sem timers", !/setInterval|setTimeout/.test(codigo));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntudo ok");
