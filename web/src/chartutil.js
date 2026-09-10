/* Helpers puros de desenho de série. Extraídos de App.jsx na aba-opcoes F2
   (quick 260910-biz, 2026-09-10) porque `web/src/opcoes/SetupChart.jsx`
   precisa deles e NÃO pode importar App.jsx — o import seria circular
   (App.jsx importa a tela de Opções). Precedente da casa: `markdown.jsx`.

   O módulo é puro de propósito: zero import de React, zero import de
   App.jsx, zero leitura de tema. É isso que o mantém importável dos dois
   lados sem ciclo. Os corpos são os mesmos de App.jsx, byte a byte — a
   extração não é refatoração de comportamento. */

/* ---------- Análise técnica: gráfico interativo + indicadores ---------- */
export function extentOf(arrays) {
  let mn = Infinity, mx = -Infinity;
  for (const a of arrays) { if (!a) continue; for (const v of a) { if (v == null) continue; if (v < mn) mn = v; if (v > mx) mx = v; } }
  if (mn === Infinity) return [0, 1];
  if (mn === mx) return [mn - 1, mx + 1];
  const pad = (mx - mn) * 0.05; return [mn - pad, mx + pad];
}
export function linePath(arr, mn, mx, W, H, pad = 3) {
  if (!arr || !arr.length) return "";
  const n = arr.length;
  const xs = (i) => pad + (n > 1 ? i / (n - 1) : 0) * (W - 2 * pad);
  const ys = (v) => (mx === mn ? H / 2 : H - pad - ((v - mn) / (mx - mn)) * (H - 2 * pad));
  let d = "", started = false;
  for (let i = 0; i < n; i++) { const v = arr[i]; if (v == null) { started = false; continue; } const x = xs(i), y = ys(v); d += started ? ` L${x.toFixed(1)} ${y.toFixed(1)}` : ` M${x.toFixed(1)} ${y.toFixed(1)}`; started = true; }
  return d;
}
export function lastVal(arr) { if (!arr) return null; for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i]; return null; }
