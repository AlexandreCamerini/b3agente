// Fase 48 (2026-10-05) — UI-SPEC "Mapa de telas e fluxo": máquina de navegação
// em profundidade da aba Opções (hub -> objetivo -> escada -> confirmar, + montar).
// Estado ÚNICO que absorve `ticker` e `oportunidadeAberta`; as sub-abas deixam
// de ser superfícies. Módulo PURO: sem React, sem I/O, sem store, sem conta
// financeira. Toda função devolve objeto NOVO.
// A allowlist de abas segue validando deep-link (T-39-14 / T-48-10): valor fora
// dela cai no hub, nunca é aceito.
import { tickerInicialOpcoes, abrirTickerOpcoes, abaInicialOpcoes } from "./memoriaOpcoes.js";

export const NIVEIS = ["hub", "objetivo", "escada", "confirmar", "montar"];
// Ordem fixa do UI-SPEC: Proteger de queda, Gerar renda, Proteger com custo baixo.
export const OBJETIVOS = ["proteger", "renda", "collar"];
const UNIDADES = ["total", "acao"];

const BASE = { nivel: "hub", ticker: "", objetivo: null, vencimento: null, degrauId: null, unidade: "total" };

export function estadoInicialOpcoes({ abas, abaInicial, abrirTicker, memoria, carteira } = {}) {
  // Deep-link "Encerrar estrutura…" (Fase 45 D-05): ativo da carteira abre no objetivo.
  const alvo = abrirTickerOpcoes(abrirTicker, carteira);
  if (alvo) return { ...BASE, nivel: "objetivo", ticker: alvo };
  // abaInicialOpcoes valida contra a allowlist; só "montar" tem tela própria no fluxo novo.
  const aba = Array.isArray(abas) && abas.includes(abaInicial)
    ? abaInicial
    : abaInicialOpcoes(abas, null, memoria);
  if (aba === "montar" && Array.isArray(abas) && abas.includes("montar")) {
    return { ...BASE, nivel: "montar", ticker: tickerInicialOpcoes(memoria, carteira) };
  }
  return { ...BASE };
}

export function abrirAtivo(e, t) {
  if (typeof t !== "string" || t === "") return { ...e };
  if (e.ticker === t) return { ...e, nivel: "objetivo" };
  return { ...e, ticker: t, nivel: "objetivo", objetivo: null, vencimento: null, degrauId: null };
}

export function escolherObjetivo(e, obj) {
  if (!OBJETIVOS.includes(obj)) return { ...e };
  if (obj === e.objetivo) return { ...e, nivel: "escada" };
  return { ...e, objetivo: obj, vencimento: null, degrauId: null, nivel: "escada" };
}

export function escolherVencimento(e, iso) {
  if (typeof iso !== "string" || iso === "") return { ...e };
  if (iso === e.vencimento) return { ...e };
  return { ...e, vencimento: iso, degrauId: null };
}

export function escolherDegrau(e, id) {
  if (typeof id !== "string" || id === "") return { ...e };
  return { ...e, degrauId: id };
}

export function irConfirmar(e) {
  if (!e.degrauId) return { ...e };
  return { ...e, nivel: "confirmar" };
}

export function irMontar(e) {
  return { ...e, nivel: "montar" };
}

// Desce um nível sem apagar escolhas (preservadas até o ativo mudar).
export function voltar(e) {
  switch (e.nivel) {
    case "confirmar": return { ...e, nivel: "escada" };
    case "escada": return { ...e, nivel: "objetivo" };
    case "objetivo": return { ...e, nivel: "hub" };
    case "montar": return { ...e, nivel: e.ticker ? "objetivo" : "hub" };
    default: return { ...e, nivel: "hub" };
  }
}

export function trocarUnidade(e, u) {
  if (!UNIDADES.includes(u)) return { ...e };
  return { ...e, unidade: u };
}

// Célula da matriz -> vencimento + degrau juntos. Id sem par entre os degraus do
// vencimento = só leitura (não selecionável; nada é inventado).
export function selecaoDaCelula(celula, degrausPorVencimento) {
  const id = celula && typeof celula.id === "string" ? celula.id : null;
  const venc = celula && typeof celula.vencimento === "string" ? celula.vencimento : null;
  const lista = venc && degrausPorVencimento ? degrausPorVencimento[venc] : null;
  if (id && Array.isArray(lista) && lista.some((d) => d && d.id === id)) {
    return { vencimento: venc, degrauId: id, somenteLeitura: false };
  }
  return { vencimento: venc, degrauId: null, somenteLeitura: true };
}
