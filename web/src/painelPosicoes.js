// 2026-10-13 (quick 261013-svo) — contadores de atenção, filtro e bloco "Hoje" do painel de Posições (puro).
//
// Os contadores derivam SÓ de prioridadeAtencao (listaPosicoes.js), já aplicada às linhas montadas.
// O "dia" usa os mesmos números do Acompanhar (m.dayVal + dayReturnPct) e o ranking usa EXATAMENTE
// o predicado de portfolioMetrics (cotacaoDoDiaValida): dia e ranking nunca divergem. Ativo sem
// cotação válida fica fora do ranking e é listado à parte (princípio 4: não inventar valor).
// Sem aritmética financeira além do que vem de finance.js; comparadores só `<`/`>`.
import { dayReturnPct, cotacaoDoDiaValida } from "./finance.js";

// RISCO..LEITURA_INDISPONIVEL; DEMAIS (6) nunca é contado.
export const NIVEIS_PAINEL = Object.freeze([0, 1, 2, 3, 4, 5]);

export const CHAVE_NIVEL = Object.freeze({
  0: "atn_risco", 1: "atn_perto_stop", 2: "atn_vence", 3: "atn_sem_plano", 4: "atn_perto_alvo", 5: "atn_sem_leitura",
});

// linhas: [{ t, nivel, lendo }] -> { estado: "lendo" | "nenhum" | "ok", grupos? }
export function resumoAtencao(linhas) {
  if (!Array.isArray(linhas)) return { estado: "nenhum" };
  if (linhas.some((l) => l && l.lendo)) return { estado: "lendo" };
  const grupos = [];
  for (const nivel of NIVEIS_PAINEL) {
    let n = 0;
    for (const l of linhas) if (l && l.nivel === nivel) n++;
    if (n > 0) grupos.push({ nivel, n });
  }
  return grupos.length ? { estado: "ok", grupos } : { estado: "nenhum" };
}

// O filtro some sozinho quando o nível zera ou a leitura volta a carregar (derivado, sem efeito).
export function filtroVigente(filtro, resumo) {
  if (filtro === null || filtro === undefined) return null;
  if (!resumo || resumo.estado !== "ok") return null;
  return resumo.grupos.some((g) => g.nivel === filtro) ? filtro : null;
}

export function filtrarPorNivel(linhas, nivel) {
  const ls = Array.isArray(linhas) ? linhas : [];
  if (nivel === null || nivel === undefined) return [...ls];
  return ls.filter((l) => l && l.nivel === nivel);
}

export function painelHoje({ positions, quotes, patr, dayVal, rotuloFonte, n = 2 } = {}) {
  const ps = Array.isArray(positions) ? positions : [];
  const q = quotes || {};
  const rotulo = typeof rotuloFonte === "function" ? rotuloFonte : (s) => String(s);
  const validos = [], semCotacao = [], fontes = [];
  for (const p of ps) {
    const quote = q[p && p.t];
    if (cotacaoDoDiaValida(quote)) {
      validos.push({ t: p.t, change: quote.change });
      if (typeof quote.source === "string" && quote.source && !fontes.includes(quote.source)) fontes.push(quote.source);
    } else if (p) semCotacao.push(p.t);
  }
  const porTicker = (a, b) => (a.t < b.t ? -1 : a.t > b.t ? 1 : 0);
  const altas = validos.filter((v) => v.change > 0).sort((a, b) => (b.change > a.change ? 1 : b.change < a.change ? -1 : porTicker(a, b))).slice(0, n);
  const baixas = validos.filter((v) => v.change < 0).sort((a, b) => (a.change > b.change ? 1 : a.change < b.change ? -1 : porTicker(a, b))).slice(0, n);
  return {
    dia: validos.length > 0 ? { valor: dayVal, pct: dayReturnPct(patr, dayVal) } : null,
    altas, baixas,
    semCotacao, semCotacaoTxt: semCotacao.join(", "),
    fontes,
    tipoFonte: fontes.length === 0 ? "nenhuma" : fontes.length === 1 ? "uma" : "varias",
    fontesTxt: fontes.map((s) => rotulo(s)).join(", "),
  };
}
