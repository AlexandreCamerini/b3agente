// Onda B (2026-10-08) — quick 261008-1ar: voltar do sistema sobe UM nível.
// Decisão: a navegação segue sendo ESTADO LOCAL do App (tab/carteiraView/perfilView,
// nav das Opções, folha de conceito). A history do navegador é só um ESPELHO da
// profundidade: o App empilha/desempilha entradas para casar com `profundidade(e)`
// e, no `popstate`, aplica `subirNivel(e)`. Módulo PURO: sem DOM, sem React, sem I/O.
// Níveis das Opções espelham navOpcoes.NIVEIS (o teste cruza os dois).
// Navegação pura: nenhum dado financeiro passa por aqui.

export const BORDA_PX = 20;
export const DX_MIN = 60;
export const DY_MAX = 40;

const n0 = (v) => (Number.isFinite(Number(v)) && Number(v) > 0 ? Math.floor(Number(v)) : 0);

export function profundidadeOpcoes(nivel, temTicker) {
  switch (nivel) {
    case "objetivo": return 1;
    case "escada": return 2;
    case "confirmar": return 3;
    case "montar": return temTicker ? 2 : 1;
    default: return 0;
  }
}

function baseDe(e) {
  if (!e) return 0;
  if (e.tab === "carteira") return e.carteiraView && e.carteiraView !== "main" ? 1 : 0;
  if (e.tab === "perfil") return e.perfilView && e.perfilView !== "hub" ? 1 : 0;
  if (e.tab === "opcoes") return e.opcoes ? profundidadeOpcoes(e.opcoes.nivel, e.opcoes.temTicker) : 0;
  return 0;
}

export function profundidade(e) {
  if (!e) return 0;
  return baseDe(e) + (e.conceito ? 1 + n0(e.conceito.trilha) : 0);
}

export function subirNivel(e) {
  if (!e) return null;
  if (e.conceito) return n0(e.conceito.trilha) > 0 ? "conceitoVoltar" : "conceitoFechar";
  if (e.tab === "carteira" && e.carteiraView && e.carteiraView !== "main") return "carteiraMain";
  if (e.tab === "perfil" && e.perfilView && e.perfilView !== "hub") return "perfilHub";
  if (e.tab === "opcoes" && e.opcoes && profundidadeOpcoes(e.opcoes.nivel, e.opcoes.temTicker) > 0) return "opcoesVoltar";
  return null;
}

export function reconciliarPilha(empurradas, prof) {
  const a = n0(empurradas);
  const p = n0(prof);
  if (p > a) return { tipo: "push", n: p - a };
  if (p < a) return { tipo: "voltar", n: a - p };
  return { tipo: "nada", n: 0 };
}

// Reload: a history do navegador sobrevive, o estado React não. Dado o `history.state`
// atual, devolve quantas entradas `b3nav` órfãs desfazer para voltar à entrada raiz.
// Lê SOMENTE o contador b3nav (navegação pura).
export function entradasOrfas(state) {
  return state && typeof state === "object" ? n0(state.b3nav) : 0;
}

export function chaveDeTela(e) {
  if (!e) return "";
  if (e.tab === "carteira" && e.carteiraView && e.carteiraView !== "main") return `carteira:${e.carteiraView}`;
  if (e.tab === "perfil" && e.perfilView && e.perfilView !== "hub") return `perfil:${e.perfilView}`;
  return e.tab;
}

export function chaveDeScroll(e) {
  const base = chaveDeTela(e);
  return e && e.tab === "opcoes" ? `${base}:${e.opcoes ? e.opcoes.nivel : "hub"}` : base;
}

export function transicaoDe(antes, depois) {
  if (!antes || !depois) return null;
  if (antes.tab !== depois.tab) return "tab";
  if (depois.prof > antes.prof) return "entrar";
  if (depois.prof < antes.prof) return "voltar";
  return null;
}

export function classeDaTransicao(t) {
  if (t === "tab") return "tela-tab";
  if (t === "entrar") return "tela-entrar";
  if (t === "voltar") return "tela-voltar";
  return undefined;
}

export function ehGestoVoltarBorda({ x0, y0, x1, y1 } = {}) {
  if (![x0, y0, x1, y1].every((v) => typeof v === "number" && Number.isFinite(v))) return false;
  return x0 <= BORDA_PX && (x1 - x0) > DX_MIN && Math.abs(y1 - y0) < DY_MAX;
}
