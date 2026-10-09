/**
 * PayoffPrimitivas.jsx — Onda H (2026-10-08, quick 261008-oos).
 *
 * Linguagem visual comum dos gráficos de payoff: eixo Y (até 3 ticks em coluna
 * dimensionada), eixo X (3 ticks), marcadores verticais numerados no topo (nenhum
 * texto de marcador sobre a área plotada) e legenda numerada abaixo do gráfico.
 * Só desenha geometria vinda de payoffEixos.js; nenhum número financeiro nasce
 * aqui. Cor sempre via `style` (tema), sem transição (Reduce Motion), fonte
 * inteira em px reais (o SVG usa viewBox = largura medida).
 * Onda H2 (2026-10-08, quick 261008-w9i): `traco` opcional por marcador; default 3 3.
 */
import { useEffect, useState } from "react";
import { T, TIPO, MONO } from "./fluxoEstilo.js";
import { FONTE_EIXO, MARC_R, MARC_LINHA_H } from "./payoffEixos.js";

const fonteEixo = { fontSize: FONTE_EIXO + "px", fontFamily: MONO.fontFamily, fill: T.textSecondary };

// Mede a largura real do container (px). Sem ResizeObserver (SSR/testes): `inicial`.
export function useLarguraMedida(ref, inicial = 340) {
  const [largura, setLargura] = useState(inicial);
  useEffect(() => {
    const el = ref && ref.current;
    if (!el) return undefined;
    const ler = () => {
      const w = Math.round(el.clientWidth);
      if (w > 0) setLargura(w);
    };
    ler();
    if (typeof ResizeObserver === "undefined") return undefined;
    const ro = new ResizeObserver(ler);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return largura;
}

export function EixoY({ geo, semTeto, semPiso }) {
  const xFim = geo.W - geo.MR;
  const basePlot = geo.topo + geo.plotH;
  return (
    <g aria-hidden="true">
      {geo.ticksY.map((t) => (
        <g key={t.chave}>
          {t.chave === "zero" ? (
            <line x1={geo.ML} x2={xFim} y1={t.y} y2={t.y} style={{ stroke: T.textMuted }} strokeWidth="1" />
          ) : (
            <line x1={geo.ML - 4} x2={geo.ML} y1={t.y} y2={t.y} style={{ stroke: T.textMuted }} strokeWidth="1" />
          )}
          <text x={geo.ML - 6} y={t.y} textAnchor="end" dominantBaseline="central" style={fonteEixo}>{t.rotulo}</text>
        </g>
      ))}
      {semTeto ? (
        <text x={geo.ML - 6} y={geo.topo + 14} textAnchor="end" style={{ fontSize: "14px", fill: T.textSecondary }}>{"↑"}</text>
      ) : null}
      {semPiso ? (
        <text x={geo.ML - 6} y={basePlot - 2} textAnchor="end" style={{ fontSize: "14px", fill: T.textSecondary }}>{"↓"}</text>
      ) : null}
    </g>
  );
}

export function EixoX({ geo, formatar }) {
  return (
    <g aria-hidden="true">
      {geo.ticksX.map((t, i) => (
        <text key={i} x={t.x} y={geo.H - 6} textAnchor={t.ancora} style={fonteEixo}>{formatar(t.valor)}</text>
      ))}
    </g>
  );
}

export function MarcadoresVerticais({ geo }) {
  const base = geo.topo + geo.plotH;
  return (
    <g aria-hidden="true">
      {geo.marcadores.map((m, i) => {
        const cy = 4 + MARC_R + m.linha * MARC_LINHA_H;
        return (
          <g key={i}>
            <line x1={m.x} x2={m.x} y1={cy + MARC_R} y2={base} style={{ stroke: T.textSecondary }} strokeWidth="1" strokeDasharray={m.traco || "3 3"} />
            {m.cx !== m.x ? (
              <line x1={m.cx} x2={m.x} y1={cy + MARC_R} y2={cy + MARC_R + 4} style={{ stroke: T.textSecondary }} strokeWidth="1" />
            ) : null}
            <circle cx={m.cx} cy={cy} r={MARC_R} style={{ fill: T.accent }} />
            <text x={m.cx} y={cy} textAnchor="middle" dominantBaseline="central"
              style={{ fontSize: "12px", fontWeight: 700, fill: T.onAccent }}>{m.n}</text>
          </g>
        );
      })}
    </g>
  );
}

export function BadgeNumero({ n }) {
  return (
    <span aria-hidden="true"
      style={{
        minWidth: "20px", height: "20px", borderRadius: "999px", background: T.accent, color: T.onAccent, ...TIPO.label,
        display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
      }}>{n}</span>
  );
}

export function LegendaMarcadores({ itens, formatarPreco }) {
  const lista = Array.isArray(itens) ? itens : [];
  if (!lista.length) return null;
  return (
    <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "4px" }}>
      {lista.map((it, i) => (
        <li key={i} style={{ display: "flex", gap: "8px", alignItems: "center", ...TIPO.corpo, color: T.textSecondary }}>
          <BadgeNumero n={it.n} />
          <span>
            <span style={{ color: T.textPrimary }}>{it.rotulo}</span>
            {it.comPreco && formatarPreco ? <span style={{ ...MONO }}>{" " + formatarPreco(it.preco)}</span> : null}
          </span>
        </li>
      ))}
    </ol>
  );
}
