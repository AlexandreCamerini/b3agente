/**
 * GraficoAnatomia.jsx — Fase 49 (2026-10-06), ANAT-03/07.
 * Só posiciona números do motor: a escala (min/max) é geometria, não resultado.
 * Perda por hachura + cor; ganho liso. Sem transição.
 *
 * Componente genérico (perna e total): o texto entra por props (titulo,
 * descricao, rótulos dos marcadores); aqui não se compõe frase nem se calcula
 * resultado. Valor null quebra o traço, nunca vira zero.
 */
import { useId } from "react";
import { T, MONO } from "./fluxoEstilo.js";

export const TRACOS = ["", "6 4", "2 3", "10 3 2 3"];
const OPACIDADE_AREA = 0.16;
const ML = 44;
const MR = 12;
const MT = 14;
const MB = 26;

const ehNum = (v) => typeof v === "number" && isFinite(v);

const fmt = (v, casas = 2) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }).replace("-", "−")
    : "—";

const saneia = (s) => String(s).replace(/[^A-Za-z0-9_-]/g, "");

export default function GraficoAnatomia({ precos, series, area, marcadores, cursorIdx, titulo, descricao, compacto }) {
  const uid = saneia(useId());
  const idTitulo = "ga-t-" + uid;
  const idDesc = "ga-d-" + uid;
  const idHach = "ga-h-" + uid;
  const idPos = "ga-p-" + uid;
  const idNeg = "ga-n-" + uid;

  const W = compacto ? 340 : 720;
  const H = compacto ? 150 : 300;
  const lista = Array.isArray(precos) ? precos : [];
  const sers = Array.isArray(series) ? series : [];
  const marcs = Array.isArray(marcadores) ? marcadores : [];
  if (lista.length < 2) return null;

  const x0 = lista[0];
  const x1 = lista[lista.length - 1];
  const X = (p) => ML + ((p - x0) / (x1 - x0 || 1)) * (W - ML - MR);

  const plot = [0];
  for (const s of sers) {
    if (s && Array.isArray(s.valores)) for (const v of s.valores) if (ehNum(v)) plot.push(v);
  }
  if (Array.isArray(area)) for (const v of area) if (ehNum(v)) plot.push(v);
  let lo = Math.min(...plot);
  let hi = Math.max(...plot);
  const amp = hi - lo;
  const folga = amp === 0 ? 10 : amp * 0.08;
  lo -= folga;
  hi += folga;
  const Y = (v) => MT + ((hi - v) / (hi - lo || 1)) * (H - MT - MB);
  const y0 = Y(0);

  const caminho = (valores) => {
    let d = "";
    let aberto = false;
    for (let i = 0; i < lista.length; i++) {
      const v = Array.isArray(valores) ? valores[i] : null;
      if (!ehNum(v) || !ehNum(lista[i])) { aberto = false; continue; }
      d += (aberto ? "L" : "M") + X(lista[i]).toFixed(1) + " " + Y(v).toFixed(1) + " ";
      aberto = true;
    }
    return d.trim();
  };

  let dArea = "";
  if (Array.isArray(area)) {
    const ix = [];
    for (let i = 0; i < lista.length; i++) if (ehNum(area[i]) && ehNum(lista[i])) ix.push(i);
    if (ix.length > 1) {
      dArea = "M" + X(lista[ix[0]]).toFixed(1) + " " + y0.toFixed(1) + " "
        + ix.map((i) => "L" + X(lista[i]).toFixed(1) + " " + Y(area[i]).toFixed(1)).join(" ")
        + " L" + X(lista[ix[ix.length - 1]]).toFixed(1) + " " + y0.toFixed(1) + " Z";
    }
  }

  const eixo = { fontSize: "11.5px", fontFamily: MONO.fontFamily, fill: T.textSecondary };
  const meio = lista[Math.floor(lista.length / 2)];
  const cursorOk = Number.isInteger(cursorIdx) && cursorIdx >= 0 && cursorIdx < lista.length
    && Array.isArray(area) && ehNum(area[cursorIdx]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="auto" role="img" aria-labelledby={idTitulo + " " + idDesc}
      style={{ display: "block", width: "100%", height: "auto", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }}>
      <title id={idTitulo}>{titulo}</title>
      <desc id={idDesc}>{descricao}</desc>
      <defs>
        <clipPath id={idPos}><rect x="0" y="0" width={W} height={Math.max(0, y0)} /></clipPath>
        <clipPath id={idNeg}><rect x="0" y={y0} width={W} height={Math.max(0, H - y0)} /></clipPath>
        <pattern id={idHach} width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="7" style={{ stroke: T.negative }} strokeWidth="2" />
        </pattern>
      </defs>

      {dArea ? (
        <>
          <path d={dArea} clipPath={`url(#${idPos})`} style={{ fill: T.positive }} fillOpacity={OPACIDADE_AREA} />
          <path d={dArea} clipPath={`url(#${idNeg})`} fill={`url(#${idHach})`} />
        </>
      ) : null}

      <line x1={ML} x2={W - MR} y1={y0} y2={y0} style={{ stroke: T.textPrimary }} strokeOpacity="0.7" strokeWidth="1" />

      {sers.map((s, i) => {
        const d = caminho(s && s.valores);
        if (!d) return null;
        const total = s.destaque && s.traco === undefined;
        const tr = ehNum(s.traco) ? TRACOS[s.traco % TRACOS.length] : "";
        return (
          <path key={s.id || i} d={d} fill="none"
            style={{ stroke: total ? T.textPrimary : T.accent }}
            strokeWidth={total ? 3 : (s.destaque ? 3.5 : 2)}
            strokeDasharray={tr || undefined}
            strokeOpacity={s.apagada ? 0.25 : 1} />
        );
      })}

      <g aria-hidden="true">
        {marcs.map((m, i) => {
          if (!m || !ehNum(m.preco)) return null;
          return (
            <g key={i}>
              <line x1={X(m.preco)} x2={X(m.preco)} y1={MT} y2={H - MB}
                style={{ stroke: T.textSecondary }} strokeWidth="1" strokeDasharray="3 3" />
              <text x={X(m.preco) + 3} y={MT + 10 + (i % 2) * 12} style={eixo}>{m.rotulo}</text>
            </g>
          );
        })}
        {cursorOk ? (
          <g>
            <line x1={X(lista[cursorIdx])} x2={X(lista[cursorIdx])} y1={MT} y2={H - MB} style={{ stroke: T.accent }} strokeWidth="1.5" />
            <circle cx={X(lista[cursorIdx])} cy={Y(area[cursorIdx])} r="5" style={{ fill: T.accent }} />
          </g>
        ) : null}
        <text x={ML} y={H - 8} style={eixo}>{fmt(x0)}</text>
        <text x={X(meio)} y={H - 8} textAnchor="middle" style={eixo}>{fmt(meio)}</text>
        <text x={W - MR} y={H - 8} textAnchor="end" style={eixo}>{fmt(x1)}</text>
        <text x={ML - 4} y={Y(hi - folga) + 4} textAnchor="end" style={eixo}>{fmt(hi - folga, 0)}</text>
        <text x={ML - 4} y={y0 + 4} textAnchor="end" style={eixo}>0</text>
        <text x={ML - 4} y={Y(lo + folga) + 4} textAnchor="end" style={eixo}>{fmt(lo + folga, 0)}</text>
      </g>
    </svg>
  );
}
