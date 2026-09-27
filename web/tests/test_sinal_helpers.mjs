// Fase 42 (HIER-01/CHIP-02; D-01, D-09, D-10, D-15, D-16) — guardião das
// funções puras de apresentação do sinal (`web/src/sinal.js`).
//
// Padrão de runner: `ok(name, cond)` + contador de falhas + process.exit,
// igual test_historico_ui.mjs/test_radar_regime_chip.mjs. Sem DOM, sem build
// — importa os módulos ES direto.
import {
  ladoDoMotor,
  decisaoDirecional,
  alinhamentoDoMotor,
  regimeRotulo,
  rotuloAnel,
  ariaRegime,
  ariaFundamento,
  ariaManchete,
} from "../src/sinal.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- ladoDoMotor ------------------------------------------------------------
ok("ladoDoMotor: setup.lado baixa", ladoDoMotor({ setup: { lado: "baixa" } }) === "baixa");
ok("ladoDoMotor: fallback plano.lado", ladoDoMotor({ setup: null, plano: { lado: "ALTA" } }) === "alta");
ok("ladoDoMotor: setup.lado fora do domínio -> null", ladoDoMotor({ setup: { lado: "neutro" } }) === null);
ok("ladoDoMotor: objeto vazio -> null", ladoDoMotor({}) === null);
ok("ladoDoMotor: null -> null", ladoDoMotor(null) === null);
ok(
  "ladoDoMotor: setup.lado tem precedência sobre plano.lado",
  ladoDoMotor({ setup: { lado: "alta" }, plano: { lado: "baixa" } }) === "alta"
);

// ---- decisaoDirecional -------------------------------------------------------
ok("decisaoDirecional: VENDER true", decisaoDirecional("VENDER") === true);
ok("decisaoDirecional: Estudar baixa true", decisaoDirecional("Estudar baixa") === true);
ok("decisaoDirecional: AGUARDAR CONFIRMAÇÃO false", decisaoDirecional("AGUARDAR CONFIRMAÇÃO") === false);
ok("decisaoDirecional: NÃO OPERAR false", decisaoDirecional("NÃO OPERAR") === false);
ok("decisaoDirecional: Monitorar false", decisaoDirecional("Monitorar") === false);
ok("decisaoDirecional: null false", decisaoDirecional(null) === false);

// ---- alinhamentoDoMotor ------------------------------------------------------
ok(
  "alinhamentoDoMotor: VENDER + tendencia_alta + gatilhoAlinhado false -> contra",
  alinhamentoDoMotor({ decisao: "VENDER", regime: { regime: "tendencia_alta" }, gatilhoAlinhado: false }) === "contra"
);
ok(
  "alinhamentoDoMotor: COMPRAR + tendencia_alta + gatilhoAlinhado true -> a_favor",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "tendencia_alta" }, gatilhoAlinhado: true }) === "a_favor"
);
ok(
  "alinhamentoDoMotor: decisão não direcional -> null",
  alinhamentoDoMotor({ decisao: "AGUARDAR CONFIRMAÇÃO", regime: { regime: "tendencia_alta" }, gatilhoAlinhado: true }) === null
);
ok(
  "alinhamentoDoMotor: regime lateral (true) -> null",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "lateral" }, gatilhoAlinhado: true }) === null
);
ok(
  "alinhamentoDoMotor: regime lateral (false) -> null",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "lateral" }, gatilhoAlinhado: false }) === null
);
ok(
  "alinhamentoDoMotor: regime indefinido -> null",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "indefinido" }, gatilhoAlinhado: true }) === null
);
ok(
  "alinhamentoDoMotor: gatilhoAlinhado undefined -> null (nunca inventa)",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: { regime: "tendencia_alta" } }) === null
);
ok(
  "alinhamentoDoMotor: regime null -> null",
  alinhamentoDoMotor({ decisao: "COMPRAR", regime: null, gatilhoAlinhado: true }) === null
);

// ---- regimeRotulo -------------------------------------------------------------
ok("regimeRotulo: tendencia_alta -> ALTA", regimeRotulo({ regime: "tendencia_alta" }) === "ALTA");
ok("regimeRotulo: tendencia_baixa -> BAIXA", regimeRotulo({ regime: "tendencia_baixa" }) === "BAIXA");
ok("regimeRotulo: lateral -> LATERAL", regimeRotulo({ regime: "lateral" }) === "LATERAL");
ok("regimeRotulo: indefinido -> null", regimeRotulo({ regime: "indefinido" }) === null);
ok("regimeRotulo: null -> null", regimeRotulo(null) === null);
ok("regimeRotulo: regime desconhecido -> XYZ", regimeRotulo({ regime: "xyz" }) === "XYZ");

// ---- rotuloAnel -----------------------------------------------------------------
const anelBaixa = rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "baixa", setup: "Reversão de sobrecompra" }, "estudo");
ok(
  "rotuloAnel: texto com lado baixa",
  anelBaixa && anelBaixa.texto === "100% · Forte — padrão de venda: Reversão de sobrecompra"
);
const anelSemLado = rotuloAnel({ conf: 100, tierLabel: "Forte", lado: null, setup: "Reversão de sobrecompra" }, "estudo");
ok(
  "rotuloAnel: sem lado, cláusula omitida (nunca inferida)",
  anelSemLado && anelSemLado.texto === "100% · Forte — Reversão de sobrecompra"
);
ok("rotuloAnel: conf 0 -> null (D-10)", rotuloAnel({ conf: 0, tierLabel: "Fraca", lado: "alta", setup: "X" }, "estudo") === null);
ok("rotuloAnel: conf null -> null", rotuloAnel({ conf: null, tierLabel: "Forte", lado: "alta", setup: "X" }, "estudo") === null);
ok("rotuloAnel: setup vazio -> null", rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "alta", setup: "" }, "estudo") === null);
ok("rotuloAnel: setup null -> null", rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "alta", setup: null }, "estudo") === null);
const anelClamp = rotuloAnel({ conf: 130, tierLabel: "Forte", lado: "alta", setup: "X" }, "estudo");
ok("rotuloAnel: conf 130 -> pct 100 (mesmo clamp do ConfluenceRing)", anelClamp && anelClamp.pct === 100);
const anelPartes = rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "baixa", setup: "Reversão de sobrecompra" }, "estudo");
ok(
  "rotuloAnel: devolve pct/cabeca/ladoTxt/setup para o componente estilizar",
  anelPartes &&
    anelPartes.pct === 100 &&
    anelPartes.cabeca === "100% · Forte" &&
    anelPartes.ladoTxt === "padrão de venda" &&
    anelPartes.setup === "Reversão de sobrecompra"
);

// ---- ariaRegime -----------------------------------------------------------------
const ariaReg = ariaRegime({ regime: "tendencia_alta", confiavel: false }, "contra", "estudo");
ok(
  "ariaRegime: contém Regime/base degradada/contra a tendência",
  ariaReg &&
    ariaReg.includes("Regime: alta") &&
    ariaReg.includes("base degradada SMA50") &&
    ariaReg.includes("contra a tendência")
);

// ---- ariaFundamento -----------------------------------------------------------------
ok(
  "ariaFundamento: score A modo operador",
  ariaFundamento("A", "operador") === "Fundamento: qualidade A (não indica direção)"
);

// ---- cenário composto UGPA3 -------------------------------------------------------
const decisaoUgpa = "VENDER";
const regimeUgpa = { regime: "tendencia_alta", confiavel: true };
const alinhamentoUgpa = alinhamentoDoMotor({ decisao: decisaoUgpa, regime: regimeUgpa, gatilhoAlinhado: false });
const rotuloUgpa = rotuloAnel({ conf: 100, tierLabel: "Forte", lado: ladoDoMotor({ setup: { lado: "baixa" } }), setup: "Reversão de sobrecompra" }, "estudo");
ok("UGPA3: alinhamento === contra", alinhamentoUgpa === "contra");
ok("UGPA3: rótulo contém 'padrão de venda'", rotuloUgpa && rotuloUgpa.texto.includes("padrão de venda"));
console.log("UGPA3: ok");

// ---- paridade estudo/operador ------------------------------------------------------
ok(
  "rotuloAnel: resultado idêntico entre modos",
  rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "baixa", setup: "X" }, "estudo").texto ===
    rotuloAnel({ conf: 100, tierLabel: "Forte", lado: "baixa", setup: "X" }, "operador").texto
);
ok(
  "ariaRegime: resultado idêntico entre modos",
  ariaRegime({ regime: "tendencia_alta", confiavel: false }, "contra", "estudo") ===
    ariaRegime({ regime: "tendencia_alta", confiavel: false }, "contra", "operador")
);
ok(
  "ariaFundamento: resultado idêntico entre modos",
  ariaFundamento("A", "estudo") === ariaFundamento("A", "operador")
);
ok(
  "ariaManchete: resultado idêntico entre modos",
  ariaManchete("DECISÃO DA MESA", "VENDER", "estudo") === ariaManchete("DECISÃO DA MESA", "VENDER", "operador")
);

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
