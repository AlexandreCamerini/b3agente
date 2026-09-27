// Fase 42 (HIER-01/CHIP-02; D-01, D-09, D-10, D-15, D-16): apresentação
// determinística do sinal — lê campos do motor, nunca recalcula; null nunca
// vira 0. Módulo PURO (sem JSX, sem import de App.jsx/React) para ser
// testável por entrada/saída, no padrão de `finance.js`.
import { copyFor } from "./copy.js";

// Decisões com lado (compra/venda) — só elas admitem marca de alinhamento e
// cláusula "padrão de X" no rótulo do anel. Vocabulário: Operador (COMPRAR/
// VENDER) e Estudo (Estudar alta/Estudar baixa) — ver decisaoDoModo em
// App.jsx (o mapa estudo→mesa do antigo bloco de KPIs saiu na Fase 43).
export const DECISOES_DIRECIONAIS = ["COMPRAR", "VENDER", "Estudar alta", "Estudar baixa"];
export function decisaoDirecional(decisao) {
  return DECISOES_DIRECIONAIS.includes(decisao);
}

// Rótulos de regime exibidos no chip — hoje vivem em REGIME_STYLE
// (App.jsx:1389), mas SÓ o rótulo migra para aqui; a cor NÃO vem junto
// (D-06: chip de contexto é neutro).
export const REGIME_ROTULO = { tendencia_alta: "ALTA", tendencia_baixa: "BAIXA", lateral: "LATERAL" };
export function regimeRotulo(regime) {
  // D-16: sem objeto, sem regime.regime, ou "indefinido" -> null (nunca chip).
  if (!regime || !regime.regime || regime.regime === "indefinido") return null;
  return REGIME_ROTULO[regime.regime] || String(regime.regime).toUpperCase();
}

// Lado do setup operável (o padrão que o anel descreve) tem precedência;
// plano.lado é fallback — os dois são motor (setups.py:707). Nunca inferido
// do nome do setup (D-09) — só do campo `lado`.
export function ladoDoMotor(motor) {
  const { setup, plano } = motor || {};
  const bruto = (setup && setup.lado) != null ? setup.lado : (plano && plano.lado);
  if (bruto == null) return null;
  const norm = String(bruto).toLowerCase();
  return norm === "alta" || norm === "baixa" ? norm : null;
}

// Marca de alinhamento (D-01/D-07): só existe com decisão direcional E
// regime de tendência E `gatilhoAlinhado` booleano vindo do payload
// (regime._gatilho_alinhado, regime.py:193) — em lateral não há tendência
// para estar a favor ou contra (DP-2, 42-06); em indefinido também não.
// gatilhoAlinhado ausente/não-booleano -> null (nunca inventa).
export function alinhamentoDoMotor({ decisao, regime, gatilhoAlinhado } = {}) {
  if (!decisaoDirecional(decisao)) return null;
  if (!regime || (regime.regime !== "tendencia_alta" && regime.regime !== "tendencia_baixa")) return null;
  if (gatilhoAlinhado === true) return "a_favor";
  if (gatilhoAlinhado === false) return "contra";
  return null;
}

// Rótulo do anel de confluência (D-09/D-10): "{pct}% · {tierLabel} — padrão
// de {lado}: {setup}". Sem conf/setup válido -> null (o anel não tem o que
// dizer). Lado ausente -> cláusula omitida, nunca inferida.
export function rotuloAnel({ conf, tierLabel, lado, setup } = {}, modo) {
  if (conf == null || !(Number(conf) > 0) || !setup) return null;
  const pct = Math.max(0, Math.min(100, Number(conf)));
  const cabeca = pct + "% · " + tierLabel;
  const ladoTxt = lado ? copyFor(modo).sinal.anelLado[lado] || null : null;
  const texto = cabeca + " — " + (ladoTxt ? ladoTxt + ": " : "") + setup;
  return { pct, cabeca, ladoTxt, setup, texto };
}

// aria-label do chip de regime: "Regime: {valor}" + base degradada + marca
// de alinhamento — uma fonte só para texto visível e acessível (D-15).
export function ariaRegime(regime, alinhamento, modo) {
  const valor = regimeRotulo(regime);
  if (valor == null) return null;
  const alinhamentoTxt = alinhamento ? copyFor(modo).sinal.alinhamento[alinhamento] : null;
  const degradado = regime && regime.confiavel === false;
  return copyFor(modo).sinal.ariaRegime(valor, alinhamentoTxt, degradado);
}

// aria-label do chip de fundamento: "Fundamento: qualidade {score} (não
// indica direção)". Sem score -> null (D-16: fundamento sem score não vira chip).
export function ariaFundamento(score, modo) {
  if (!score) return null;
  return copyFor(modo).sinal.ariaFundamento(score);
}

// aria-label do bloco de manchete (SinalChip peso="primario"): kicker + decisão.
export function ariaManchete(kicker, decisao, modo) {
  return copyFor(modo).sinal.ariaManchete(kicker, decisao);
}
