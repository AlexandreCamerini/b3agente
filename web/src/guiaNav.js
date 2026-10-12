// Navegação, progresso e layout da folha do guia das telas (quick 261011-l5x).
// Puro: sem React, sem DOM, sem Vite — testável no Node (web/tests/test_guia_nav.mjs).
//
// Estado: { tela, ponto }. `ponto === telas[tela].pontos.length` é o cartão "Na prática"
// (missão + teste), depois do último ponto da tela. `ponto === -1` é o cartão "Visão
// geral" (campo `visao` da tela): só existe quando o guia é aberto pelo Bóris
// (quick 261012-09v); `proximo` leva -1 -> 0 e `anterior` de -1 vai ao "Na prática" da
// tela anterior (ou fica, na tela 0).
import { BORDA_PX, DX_MIN, DY_MAX } from "./navStack.js";
import { telaDoAssistente } from "./telas.js";

export const TOPO_PX = 44;
export const RODAPE_PX = 32;
export const LARGURA_LADO_A_LADO = 900;
// Mesma chave do guia web (site/js/guia.js): payload {v:2, mis:{id:true}, q:{id:true}}.
// No iOS (capacitor://) o localStorage é outra origem — o progresso do app é próprio.
export const CHAVE_PROGRESSO = "boris-guia-v1";

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const nPontos = (telas, i) => ((telas[i] && telas[i].pontos) || []).length;

export function proximo(e, telas) {
  const n = nPontos(telas, e.tela);
  if (e.ponto < n) return { tela: e.tela, ponto: e.ponto + 1 }; // inclui ir do último ponto ao "Na prática"
  if (e.tela < telas.length - 1) return { tela: e.tela + 1, ponto: 0 };
  return e;
}

export function anterior(e, telas) {
  if (e.ponto > 0) return { tela: e.tela, ponto: e.ponto - 1 };
  if (e.tela > 0) return { tela: e.tela - 1, ponto: nPontos(telas, e.tela - 1) }; // "Na prática" da tela anterior
  return e;
}

// ---- ponte tela do app -> tela do guia (quick 261012-09v) ----
// Toda tela do registro (web/src/telas.js) tem decisão explícita aqui: o id do guia que a
// explica, ou null ("ainda não tem tour": o guia abre com o aviso). Tela nova em telas.js
// reprova web/tests/test_guia_mapa.mjs até ganhar linha. Sem dado do guia embutido: o
// índice é resolvido contra os dados em estadoInicialGuia.
export const GUIA_DA_TELA_APP = Object.freeze({
  evolucao: "acomp", radar: "radar", mercado: "watch", carteira: "port", opcoes: "opc",
  agente: "opia", historico: null, perfil: null,
});
// Opções por nível (navOpcoes.NIVEIS). `confirmar` depende do modo: no Estudo é `confest`;
// no Operador o resultado de confirmar é a estrutura aberta (`opcaberta`) — `confest` tem o
// ponto "Estudo não executa", errado para quem está no Operador.
export const GUIA_DO_NIVEL_OPCOES = Object.freeze({
  hub: "opc", objetivo: "opcobj", escada: "opcpiso",
  confirmar: Object.freeze({ estudo: "confest", operador: "opcaberta" }),
  montar: "opc",
});
const tem = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

export function guiaIdDaTelaApp({ tab, carteiraView, opcoesNivel, operador } = {}) {
  const id = telaDoAssistente(tab, carteiraView);
  if (id === "opcoes") {
    // Nível desconhecido cai em `opc`, mesmo fallback do navOpcoes (inválido -> hub).
    const alvo = tem(GUIA_DO_NIVEL_OPCOES, opcoesNivel) ? GUIA_DO_NIVEL_OPCOES[opcoesNivel] : GUIA_DO_NIVEL_OPCOES.hub;
    return typeof alvo === "object" ? (operador ? alvo.operador : alvo.estudo) : alvo;
  }
  return typeof id === "string" && tem(GUIA_DA_TELA_APP, id) ? GUIA_DA_TELA_APP[id] : null;
}

// 1º uso (camada "tour"): abre em Boas-vindas, sem o cartão Visão geral.
export const ABERTURA_PRIMEIRO_USO = Object.freeze({ id: "boas", visao: false, n: 0 });

// Cada toque em "Me mostra esta tela" gera identidade nova (`n` cresce, mesmo com o mesmo
// id): o App usa `n` como `key` do GuiaTelas para remontar e reler o estado inicial com o
// guia já aberto em Perfil.
export function novaAberturaBoris(anterior, id) {
  return { id: id ?? null, visao: true, n: ((anterior && anterior.n) || 0) + 1 };
}

// Estado inicial do guia: primeira tela não concluída (0 se todas concluídas) quando não há
// abertura; com abertura, a tela `abertura.id` (no ponto -1 se `visao` e a tela tem `visao`,
// senão no 0). Id nulo/inexistente = sem tour: 1ª não concluída + semTour (aviso na folha).
export function estadoInicialGuia(telas, progresso, abertura) {
  const lista = Array.isArray(telas) ? telas : [];
  const prim = lista.findIndex((t) => !telaConcluida(progresso, t && t.id));
  const base = Math.max(0, prim);
  if (!abertura) return { tela: base, ponto: 0, semTour: false };
  const i = abertura.id ? lista.findIndex((t) => t && t.id === abertura.id) : -1;
  if (i < 0) return { tela: base, ponto: 0, semTour: true };
  const t = lista[i];
  const comVisao = abertura.visao === true && typeof t.visao === "string" && t.visao.trim() !== "";
  return { tela: i, ponto: comVisao ? -1 : 0, semTour: false };
}

export function irParaTela(e, i, telas) {
  const max = telas ? telas.length - 1 : Infinity;
  return { tela: clamp(Math.trunc(Number(i)) || 0, 0, max), ponto: 0 };
}

export function rotuloSeletor(e, telas) {
  return (e.tela + 1) + "/" + telas.length;
}

// ---- progresso ----
export function carregarProgresso(raw) {
  const vazio = { v: 2, mis: {}, q: {} };
  try {
    const o = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!o || typeof o !== "object") return vazio;
    return { v: 2, mis: o.v === 2 && o.mis && typeof o.mis === "object" ? { ...o.mis } : {}, q: o.q && typeof o.q === "object" ? { ...o.q } : {} };
  } catch {
    return vazio;
  }
}
export function serializarProgresso(p) {
  return JSON.stringify({ v: 2, mis: (p && p.mis) || {}, q: (p && p.q) || {} });
}
export function telaConcluida(p, id) {
  return !!(p && p.mis && p.mis[id] && p.q && p.q[id]);
}

// ---- layout ----
// < 900px: captura em cima (55% da altura útil), folha embaixo. >= 900px: lado a lado.
export function layoutGuia(vw, vh) {
  const util = Math.max(0, vh - TOPO_PX - RODAPE_PX);
  const rodape = { top: vh - RODAPE_PX, left: 0, width: vw, height: RODAPE_PX };
  if (vw >= LARGURA_LADO_A_LADO) {
    const cw = Math.round(0.58 * vw);
    return {
      lado: true, topo: TOPO_PX, rodape,
      captura: { top: TOPO_PX, left: 0, width: cw, height: util },
      folha: { top: TOPO_PX, left: cw, width: vw - cw, height: util },
    };
  }
  const ch = Math.round(0.55 * util);
  return {
    lado: false, topo: TOPO_PX, rodape,
    captura: { top: TOPO_PX, left: 0, width: vw, height: ch },
    folha: { top: TOPO_PX + ch, left: 0, width: vw, height: util - ch },
  };
}

// Câmera: escala = largura da moldura / largura natural da captura; o ponto vai ao centro
// horizontal e a ~40% da altura. `ponto` null = tela inteira (cartão "Na prática").
const MARGEM_SPOT = 14;
export function enquadrar(ponto, natW, natH, vw, vh) {
  if (!ponto) {
    const s = Math.min(vw / natW, vh / natH);
    const w = natW * s, h = natH * s;
    return { s, w, h, tx: (vw - w) / 2, ty: (vh - h) / 2, spot: null };
  }
  const s = vw / natW;
  const w = natW * s, h = natH * s;
  const X = (ponto.x / 100) * w, Y = (ponto.y / 100) * h;
  let tx = vw / 2 - X, ty = vh * 0.4 - Y;
  tx = Math.min(0, Math.max(vw - w, tx));
  ty = Math.min(0, Math.max(vh - h, ty));
  if (w <= vw) tx = (vw - w) / 2;
  if (h <= vh) ty = (vh - h) / 2;
  const sw = ((ponto.w || 0) / 100) * w + MARGEM_SPOT, sh = ((ponto.h || 0) / 100) * h + MARGEM_SPOT;
  const cx = tx + X, cy = ty + Y;
  const l = Math.max(0, cx - sw / 2), t = Math.max(0, cy - sh / 2);
  const r = Math.min(vw, cx + sw / 2), b = Math.min(vh, cy + sh / 2);
  return { s, w, h, tx, ty, spot: { left: l, top: t, width: Math.max(0, r - l), height: Math.max(0, b - t) } };
}

// Swipe horizontal entre pontos. Toque iniciado na borda (x0 < BORDA_PX) é do gesto de
// fechar a folha (Onda J) e nunca vira troca de ponto.
export function ehSwipeHorizontal({ x0, y0, x1, y1 } = {}) {
  if (![x0, y0, x1, y1].every((v) => typeof v === "number" && Number.isFinite(v))) return null;
  if (x0 < BORDA_PX) return null;
  const dx = x1 - x0, dy = y1 - y0;
  if (Math.abs(dx) < DX_MIN || Math.abs(dy) > DY_MAX) return null;
  return dx < 0 ? "proximo" : "anterior";
}
