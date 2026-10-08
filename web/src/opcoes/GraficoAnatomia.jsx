/**
 * GraficoAnatomia.jsx — Fase 49 (2026-10-06), ANAT-03/07.
 * Só posiciona números do motor: a escala (min/max) é geometria, não resultado.
 * Perda por hachura + cor; ganho liso. Sem transição.
 *
 * Componente genérico (perna e total): o texto entra por props (titulo,
 * descricao, rótulos dos marcadores); aqui não se compõe frase nem se calcula
 * resultado. Valor null quebra o traço, nunca vira zero.
 *
 * Onda H (2026-10-08, quick 261008-oos): o viewBox fixo de 720 (encolhido para
 * ~5px de fonte no iPhone) deu lugar à largura medida (viewBox = px reais).
 * Eixos, marcadores numerados e legenda vêm de payoffEixos.js/PayoffPrimitivas.jsx;
 * nenhum rótulo de marcador é escrito sobre a área plotada. O motor não informa
 * "sem teto" aqui, então os 3 ticks são os da janela (decisão H-D6).
 */
import { useId, useRef } from "react";
import { T } from "./fluxoEstilo.js";
import { montarGeometria } from "./payoffEixos.js";
import { useLarguraMedida, EixoY, EixoX, MarcadoresVerticais, LegendaMarcadores } from "./PayoffPrimitivas.jsx";

export const TRACOS = ["6 4", "2 3", "10 3 2 3", "1 3"];
const OPACIDADE_AREA = 0.16;

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
  const ref = useRef(null);
  const largura = useLarguraMedida(ref, 340);

  const lista = Array.isArray(precos) ? precos : [];
  const sers = Array.isArray(series) ? series : [];
  const marcs = Array.isArray(marcadores) ? marcadores : [];
  if (lista.length < 2) return null;

  const x0 = lista[0];
  const x1 = lista[lista.length - 1];

  const plot = [0];
  for (const s of sers) {
    if (s && Array.isArray(s.valores)) for (const v of s.valores) if (ehNum(v)) plot.push(v);
  }
  if (Array.isArray(area)) for (const v of area) if (ehNum(v)) plot.push(v);
  const geo = montarGeometria({
    largura, x0, x1, yMin: Math.min(...plot), yMax: Math.max(...plot), marcadores: marcs, compacto: !!compacto,
  });
  const { W, H, sx: X, sy: Y, yZero: y0 } = geo;

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

  const cursorOk = Number.isInteger(cursorIdx) && cursorIdx >= 0 && cursorIdx < lista.length
    && Array.isArray(area) && ehNum(area[cursorIdx]);

  return (
    <div ref={ref} style={{ display: "flex", flexDirection: "column", gap: "8px", minWidth: 0 }}>
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

        <EixoY geo={geo} />
        <MarcadoresVerticais geo={geo} />

        {sers.map((s, i) => {
          const d = caminho(s && s.valores);
          if (!d) return null;
          // WR-05 (49-REVIEW, 2026-10-06): o total é marcado por `tipo`, não inferido
          // de destaque/traço (com perna selecionada ele colidia com a perna 0).
          // Identidade por 3 sinais além da cor: cor de texto, peso 3 e halo de fundo.
          // Onda H: pernas finas e tracejadas (nenhuma em traço cheio), total cheio e grosso.
          const total = s.tipo === "total";
          const tr = ehNum(s.traco) ? TRACOS[s.traco % TRACOS.length] : "";
          return (
            <g key={s.id || i}>
              {total ? (
                <path d={d} fill="none" style={{ stroke: T.bgPanel }} strokeWidth={6}
                  strokeOpacity={s.apagada ? 0.45 : 1} />
              ) : null}
              <path d={d} fill="none"
                style={{ stroke: total ? T.textPrimary : T.accent }}
                strokeWidth={total ? 3 : (s.destaque ? 2.5 : 1.5)}
                strokeDasharray={tr || undefined}
                strokeOpacity={s.apagada ? (total ? 0.45 : 0.25) : 1} />
            </g>
          );
        })}

        {cursorOk ? (
          <g aria-hidden="true">
            <line x1={X(lista[cursorIdx])} x2={X(lista[cursorIdx])} y1={geo.topo} y2={geo.topo + geo.plotH} style={{ stroke: T.accent }} strokeWidth="1.5" />
            <circle cx={X(lista[cursorIdx])} cy={Y(area[cursorIdx])} r="5" style={{ fill: T.accent }} />
          </g>
        ) : null}
        <EixoX geo={geo} formatar={fmt} />
      </svg>
      <LegendaMarcadores itens={geo.marcadores} formatarPreco={fmt} />
    </div>
  );
}
