/**
 * SetupChart.jsx — aba-opcoes F2 (ADR-027, quick 260910-biz, 2026-09-10).
 *
 * Adaptador entre `get_setup_chart` (arrays PARALELOS: `dates`, `open`,
 * `high`, `low`, `close`, `volume`, `series`, `triggers`) e o formato que
 * `PriceChart` exige. O `PriceChart` chega por `ctx.PriceChart` — importar
 * `App.jsx` daqui seria ciclo (App.jsx importa a tela de Opções).
 */
import { useMemo } from "react";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root` — padrão de
// `pet/BorisChat.jsx`. `var(--x)` resolve para o MESMO valor, no MESMO tema,
// sem importar `T` de `App.jsx` (que criaria import circular).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const MAX_LINHAS = 8;     // eixo de preço fica ilegível com dezenas de linhas
const BARRAS_VISIVEIS = 120;

const ehNum = (v) => typeof v === "number" && isFinite(v);

// Ajusta uma série do serviço ao comprimento dos candles: `PriceChart` faz
// `arr[i]` sem guard, então array curto viraria `undefined` no meio do
// desenho. Buraco vira `null` (lacuna), nunca 0 — 0 seria um preço.
function alinha(serie, n) {
  const fora = new Array(n);
  for (let i = 0; i < n; i++) {
    const v = serie ? serie[i] : null;
    fora[i] = ehNum(v) ? v : null;
  }
  return fora;
}

export default function SetupChart({ ctx, grafico, palette, cp }) {
  const g = grafico || {};
  const c = cp || {};
  const P = palette || {};

  const { candles, ind, show, legenda, priceLines, disparosTotal, disparos } = useMemo(() => {
    const dates = Array.isArray(g.dates) ? g.dates : [];
    const open = Array.isArray(g.open) ? g.open : [];
    const high = Array.isArray(g.high) ? g.high : [];
    const low = Array.isArray(g.low) ? g.low : [];
    const close = Array.isArray(g.close) ? g.close : [];
    const volume = Array.isArray(g.volume) ? g.volume : [];

    const velas = [];
    for (let i = 0; i < dates.length; i++) {
      velas.push({
        date: dates[i], open: open[i], high: high[i], low: low[i],
        close: close[i], volume: volume[i],
      });
    }
    const n = velas.length;
    // Comprimento DERIVADO dos candles, nunca fixo: série mais curta que a
    // janela deixaria o fim do gráfico lendo `undefined`.
    const nulos = new Array(n).fill(null);

    // `series` traz nomes ARBITRÁRIOS (os indicadores que as condições do
    // setup citam: `sma21`, `rsi14`, `highest20`…), nunca os `sma20`/`sma50`
    // que o PriceChart nomeia. Mapeamento DETERMINÍSTICO (ordem alfabética)
    // para os dois slots de linha, e a legenda diz o NOME REAL — ninguém
    // pode ler "SMA 20" onde o dado é `rsi14`.
    const nomes = Object.keys(g.series || {}).sort();
    const s0 = nomes[0] ? (g.series || {})[nomes[0]] : null;
    const s1 = nomes[1] ? (g.series || {})[nomes[1]] : null;
    const indicadores = {
      sma20: s0 ? alinha(s0, n) : nulos,
      sma50: s1 ? alinha(s1, n) : nulos,
      // Os QUATRO campos são obrigatórios: `pair()` do PriceChart faz
      // `arr[i]` sem guard e chave ausente vira TypeError.
      bbUpper: nulos,
      bbLower: nulos,
    };

    const linhas = [];
    const idx = Array.isArray(g.triggers) ? g.triggers : [];
    const datasDisparo = Array.isArray(g.trigger_dates) ? g.trigger_dates : [];
    idx.forEach((i, k) => {
      const preco = close[i];
      // Disparo sem fechamento numérico é DESCARTADO. Vira 0 = vira uma
      // linha rente ao eixo, que o usuário lê como "disparou no zero".
      if (!ehNum(preco)) return;
      linhas.push({
        price: preco,
        // Hex RESOLVIDO da paleta do tema/modo. `T.accent` (que é
        // `var(--accent)`) NÃO resolve em canvas — foi o bug real do Modo
        // Operador, e `test_chart_colors_theme_aware.mjs` guarda a classe.
        color: P.accent || "#6366f1",
        title: datasDisparo[k] || String(i),
        dashed: true,
      });
    });

    return {
      candles: velas,
      ind: indicadores,
      show: { sma20: !!s0, sma50: !!s1, bb: false, vol: true },
      legenda: nomes.slice(0, 2),
      priceLines: linhas.slice(-MAX_LINHAS),
      disparosTotal: linhas.length,
      disparos: linhas,
    };
  }, [g, P.accent]);

  const Chart = ctx && ctx.PriceChart;
  const viewBars = candles.length && candles.length < BARRAS_VISIVEIS ? candles.length : BARRAS_VISIVEIS;

  const cabecalho = (
    <div style={{ marginBottom: "8px" }}>
      <div style={{ fontSize: "13px", fontWeight: 700, color: T.textPrimary }}>
        {c.opcoesGraficoTitulo || "Disparos do setup"} · {g.name || "—"}
      </div>
      <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "2px" }}>
        {(c.opcoesPregaoRotulo || "Pregão") + ": " + (g.pregao || g.trading_date || "—")}
        {" · " + (c.opcoesDisparosRotulo || "Disparos") + ": " + disparosTotal}
        {disparosTotal > MAX_LINHAS
          ? " (marcados os " + MAX_LINHAS + " mais recentes no gráfico)"
          : ""}
      </div>
      {legenda.length > 0 && (
        <div style={{ fontSize: "11.5px", color: T.textSecondary, marginTop: "4px" }}>
          {/* NOME REAL da série, nunca o rótulo do slot do PriceChart. */}
          {"Linhas: " + legenda.join(" · ")}
        </div>
      )}
    </div>
  );

  // Fallback: sem `ctx.PriceChart` (ou sem candles) a lista textual dos
  // disparos continua informando. Tela em branco nunca é opção.
  if (!Chart || !candles.length) {
    return (
      <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel }}>
        {cabecalho}
        {disparos.length === 0 ? (
          <div style={{ fontSize: "12.5px", color: T.textMuted }}>
            Nenhum disparo com preço de fechamento neste período.
          </div>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
            {disparos.map((l, i) => (
              <li key={l.title + "-" + i} style={{ display: "flex", justifyContent: "space-between", gap: "10px", minHeight: "32px", alignItems: "center", fontSize: "12.5px", color: T.textSecondary, borderBottom: `1px solid ${T.borderFaint}` }}>
                <span>{l.title}</span>
                <span style={{ fontVariantNumeric: "tabular-nums", color: T.textPrimary }}>{l.price.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  return (
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel }}>
      {cabecalho}
      <Chart candles={candles} ind={ind} show={show} priceLines={priceLines} viewBars={viewBars} />
    </div>
  );
}
