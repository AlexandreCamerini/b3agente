/**
 * payoffEixos.js — Onda H (2026-10-08, quick 261008-oos).
 *
 * Geometria e formatação de EIXO dos gráficos de payoff. Nunca resultado
 * financeiro (princípio 5 do CLAUDE.md): os ticks são os extremos do domínio
 * que o motor já entregou, só posicionados e arredondados para leitura. Valor
 * ausente vira travessão; "sem teto"/"sem piso" declarado suprime o tick de
 * extremo em vez de inventar um número. Módulo puro: sem React, sem tema.
 */

export const FONTE_EIXO = 12;
export const PLOT_H = 244;
export const PLOT_H_COMPACTO = 132;
export const MARC_R = 9;
export const MARC_DIST = 22;
export const MARC_LINHA_H = 22;
export const MB_EIXO = 22;
export const MR_EIXO = 12;
export const PAD_INT = 8;

const LARGURA_FALLBACK = 340;
const ehNum = (v) => typeof v === "number" && isFinite(v);
const ptBR = (v, casas) => v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

// Formato do tick (decisão H-D3): < 100 com 2 casas; até 99.999 inteiro com
// milhar; >= 100 mil em "mil"; >= 1 mi em "mi". O valor exato fica na tabela.
export function rotuloEixoBRL(v) {
  if (!ehNum(v)) return "—";
  if (v === 0) return "R$ 0";
  const a = Math.abs(v);
  const sinal = v < 0 ? "−" : "";
  let corpo;
  if (a < 100) corpo = ptBR(a, 2);
  else if (a < 100000 && Math.round(a) < 100000) corpo = ptBR(Math.round(a), 0);
  else if (a < 1e6 && Math.round(a / 1000) < 1000) corpo = ptBR(Math.round(a / 1000), 0) + " mil";
  else corpo = ptBR(a / 1e6, 2) + " mi";
  return sinal + "R$ " + corpo;
}

export function margemEsquerda(rotulos, fonte = FONTE_EIXO) {
  const lista = Array.isArray(rotulos) ? rotulos : [];
  let maior = 0;
  for (const r of lista) maior = Math.max(maior, String(r).length);
  return Math.ceil(maior * fonte * 0.62) + 8;
}

export function ticksY({ yMin, yMax, sy, semTeto, semPiso }) {
  const folga = FONTE_EIXO + 2;
  const yZero = sy(0);
  const out = [];
  if (ehNum(yMax) && yMax > 0 && !semTeto && Math.abs(sy(yMax) - yZero) >= folga) {
    out.push({ chave: "max", valor: yMax, rotulo: rotuloEixoBRL(yMax), y: sy(yMax) });
  }
  out.push({ chave: "zero", valor: 0, rotulo: "R$ 0", y: yZero });
  if (ehNum(yMin) && yMin < 0 && !semPiso && Math.abs(sy(yMin) - yZero) >= folga) {
    out.push({ chave: "min", valor: yMin, rotulo: rotuloEixoBRL(yMin), y: sy(yMin) });
  }
  return out;
}

export function ticksX(x0, x1) {
  if (!ehNum(x0) || !ehNum(x1)) return [];
  return [
    { valor: x0, ancora: "start" },
    { valor: (x0 + x1) / 2, ancora: "middle" },
    { valor: x1, ancora: "end" },
  ];
}

// Marcadores verticais numerados. Ordena por preço; dois círculos a < `dist` px
// em X vão para linhas diferentes (nunca se sobrepõem; sem teto de linhas).
export function empilharMarcadores(itens, sx, { xMin, xMax, dist = MARC_DIST }) {
  const validos = (Array.isArray(itens) ? itens : [])
    .map((it, ordem) => ({ it, ordem }))
    .filter(({ it }) => it && ehNum(it.preco))
    .sort((a, b) => (a.it.preco - b.it.preco) || (a.ordem - b.ordem));
  const ultimo = [];
  const saida = [];
  validos.forEach(({ it }, k) => {
    const x = sx(it.preco);
    const cx = Math.min(xMax - MARC_R, Math.max(xMin + MARC_R, x));
    let linha = 0;
    while (linha < ultimo.length && Math.abs(cx - ultimo[linha]) < dist) linha++;
    ultimo[linha] = cx;
    saida.push({ ...it, n: Number.isInteger(it.n) ? it.n : k + 1, x, cx, linha });
  });
  return { itens: saida, linhas: ultimo.length };
}

export function alturaTopo(linhas) {
  return 6 + Math.max(1, linhas) * MARC_LINHA_H;
}

// Afasta verticalmente pontos que colidiriam (marcadores sobre a curva).
export function afastarPontos(pts, dist = 20) {
  const lista = Array.isArray(pts) ? pts : [];
  const out = [];
  for (const p of lista) {
    let dy = 0;
    for (const cand of [0, -dist, dist, -2 * dist, 2 * dist]) {
      // círculos de raio ~9: colidem se os centros ficam a menos de 0,9*dist
      const bate = out.some((q) => Math.hypot(q.x - p.x, (q.y + q.dy) - (p.y + cand)) < dist * 0.9);
      if (!bate) { dy = cand; break; }
    }
    out.push({ x: p.x, y: p.y, dy });
  }
  return out;
}

export function montarGeometria({ largura, x0, x1, yMin, yMax, marcadores, compacto, semTeto, semPiso }) {
  const W = ehNum(largura) && largura > 0 ? largura : LARGURA_FALLBACK;
  const lo = ehNum(yMin) ? yMin : 0;
  const hi = ehNum(yMax) ? yMax : 0;
  const yLo = Math.min(lo, 0);
  let yHi = Math.max(hi, 0);
  let yLoE = yLo;
  if (yHi === yLoE) { yHi = 1; yLoE = -1; }
  const ML = margemEsquerda([rotuloEixoBRL(hi), rotuloEixoBRL(0), rotuloEixoBRL(lo)]);
  const MR = MR_EIXO;
  const dx = ehNum(x0) && ehNum(x1) ? x1 - x0 : 0;
  const sx = (v) => ML + ((v - x0) / (dx || 1)) * (W - ML - MR);
  const emp = empilharMarcadores(marcadores, sx, { xMin: ML, xMax: W - MR });
  const topo = alturaTopo(emp.linhas);
  const plotH = compacto ? PLOT_H_COMPACTO : PLOT_H;
  const sy = (v) => topo + PAD_INT + ((yHi - v) / (yHi - yLoE)) * (plotH - 2 * PAD_INT);
  const ty = ticksY({ yMin: lo, yMax: hi, sy, semTeto, semPiso });
  const tX = ticksX(x0, x1).map((t) => ({ ...t, x: sx(t.valor) }));
  return {
    W, H: topo + plotH + MB_EIXO, ML, MR, topo, plotH, sx, sy, yZero: sy(0),
    ticksY: ty, ticksX: tX, marcadores: emp.itens, linhas: emp.linhas,
  };
}
