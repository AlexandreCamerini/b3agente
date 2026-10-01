// Fase 46 (2026-10-01, revert 261001-0or + design v6): ponto ÚNICO das cores do
// card de Posição v6. O design v6 aprovado é DARK-ONLY e traz os valores
// literais abaixo; o tema CLARO não existe no design, então os equivalentes
// claros são derivados aqui (mesma matiz, luminosidade ajustada) para passar AA.
//
// ESCOPO: nada aqui altera o objeto de tema global `T`/`PALETTE` do App.jsx. O
// App aplica `varsCartaoV6(tema, modo)` como CSS custom properties NO WRAPPER do
// card (uma posição = um wrapper); como `T.x` é `var(--x)`, só a subárvore do
// card enxerga estas cores, e o resto do app segue na paleta global.
//
// Razões de contraste medidas em web/tests/test_estrutura_card_contraste.mjs
// (guardião lê ESTE módulo). Formato dos números: duas casas e ponto.

const ESCURO = {
  telaBg: "#0b111b", superficie: "#111b29", elevada: "#1b2a3d",
  borda: "#3a4d68", bordaForte: "#465d7b", bordaSuave: "#2a3850", controle: "#2c3d56",
  textoPrincipal: "#edf2fa", textoSecundario: "#c1cde0", textoAuxiliar: "#d6deeb",
  positivo: "#62dfb5", negativo: "#ff929c", textoAlerta: "#ffb3ba", textoOk: "#8cebcb", pontoIntermediario: "#9fd9c6",
  status: {
    warn: { bg: "#2a1e28", texto: "#ffb3ba" },
    info: { bg: "#16233a", texto: "#d6deeb" },
    ok: { bg: "#12302a", texto: "#8cebcb" },
    pendente: { bg: "#2d2618", texto: "#ffe3a0" },
  },
  zonas: {
    1: { texto: "#ffb3ba", ponto: "#ff929c" },
    2: { texto: "#8cebcb", ponto: "#9fd9c6" },
    3: { texto: "#62dfb5", ponto: "#62dfb5" },
  },
  modo: {
    estudo: { acc: "#55cfbe", accSurf: "#15312f", accBorder: "#3c8c83", accInk: "#06231f" },
    operador: { acc: "#e4be60", accSurf: "#302a1b", accBorder: "#947b3e", accInk: "#231a04" },
  },
};

// DERIVADO (o design não define claro). Neutros frios de mesma matiz do escuro.
const CLARO = {
  telaBg: "#f4f6fa", superficie: "#ffffff", elevada: "#eef2f7",
  borda: "#a9b6c8", bordaForte: "#8797ad", bordaSuave: "#dde4ee", controle: "#d3dbe7",
  textoPrincipal: "#0b111b", textoSecundario: "#27364d", textoAuxiliar: "#3c4c64",
  positivo: "#0d6a49", negativo: "#b3222d", textoAlerta: "#9a2230", textoOk: "#0d6a49", pontoIntermediario: "#054330",
  status: {
    warn: { bg: "#fdeef0", texto: "#9a2230" },
    info: { bg: "#e6edf8", texto: "#27364d" },
    ok: { bg: "#e1f3ec", texto: "#0d6a49" },
    pendente: { bg: "#f8efd5", texto: "#6b4d00" },
  },
  zonas: {
    1: { texto: "#9a2230", ponto: "#b3222d" },
    2: { texto: "#0d6a49", ponto: "#054330" },
    3: { texto: "#0d6a49", ponto: "#0d6a49" },
  },
  modo: {
    estudo: { acc: "#17695f", accSurf: "#e1f2ef", accBorder: "#17695f", accInk: "#ffffff" },
    operador: { acc: "#6f5410", accSurf: "#f6edd3", accBorder: "#6f5410", accInk: "#ffffff" },
  },
};

// Opacidade dos segmentos extremos (prejuízo / teto) da faixa e do simulador.
// Medida contra a trilha (knob) e o bgBase do card; o App.jsx usa este valor.
export const ALFA_ZONA_V6 = 0.75;
// Segmento do meio (lucro cresce): mais claro por desenho (gradação).
export const ALFA_ZONA_MEIO_V6 = 0.6;

// Cores do card para (tema, modo). Chaves iguais às de PALETTE quando
// substituem um `T.x` (assim `T.x` dentro do card passa a ler estas).
export function coresCartaoV6(tema, modo) {
  const P = tema === "light" ? CLARO : ESCURO;
  const m = P.modo[modo === "operador" ? "operador" : "estudo"];
  return {
    // superfícies
    bgCard: P.superficie, bgBase: P.elevada, bgPanel: P.elevada, knob: P.controle,
    borderSubtle: P.borda, borderDashed: P.bordaForte, borderFaint: P.bordaSuave,
    // textos
    textPrimary: P.textoPrincipal, textSecondary: P.textoSecundario,
    textMuted: P.textoAuxiliar, textDim: P.textoAuxiliar, textFaint: P.textoAuxiliar,
    // acento do modo
    accent: m.acc, accentTint: m.accSurf, accentTint10: m.accSurf, onAccent: m.accInk,
    accentBorder: m.accBorder,
    // semântica
    positive: P.positivo, negative: P.negativo,
    warn: P.status.warn.texto, warnTint10: P.status.warn.bg,
    negativeTint10: P.status.warn.bg,
    // extras só para medição / consumo pontual
    zonaMeio: P.pontoIntermediario,
    status: P.status, zonas: P.zonas, textoAlerta: P.textoAlerta, textoOk: P.textoOk,
    telaBg: P.telaBg,
  };
}

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const CHAVES_VAR = [
  "bgCard", "bgBase", "bgPanel", "knob", "borderSubtle", "borderDashed", "borderFaint",
  "textPrimary", "textSecondary", "textMuted", "textDim", "textFaint",
  "accent", "accentTint", "accentTint10", "onAccent",
  "positive", "negative", "warn", "warnTint10", "negativeTint10",
];

// Style para o wrapper do card: sobrescreve só as variáveis que o card lê.
export function varsCartaoV6(tema, modo) {
  const c = coresCartaoV6(tema, modo);
  const out = {};
  for (const k of CHAVES_VAR) out[VARKEY(k)] = c[k];
  out["--cv-zona-meio"] = c.zonaMeio;
  return out;
}
