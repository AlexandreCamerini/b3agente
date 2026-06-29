// Dados de EXEMPLO para o protótipo navegável (offline). Geram uma série
// determinística (~1 ano) e calculam os mesmos indicadores do backend, no
// mesmo formato do /api/technicals, para iterar o layout sem servidor.

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const seedFrom = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };

function sma(v, p) { const o = Array(v.length).fill(null); let s = 0; for (let i = 0; i < v.length; i++) { s += v[i]; if (i >= p) s -= v[i - p]; if (i >= p - 1) o[i] = s / p; } return o; }
function ema(v, p) { const o = Array(v.length).fill(null); if (v.length < p) return o; const k = 2 / (p + 1); let prev = v.slice(0, p).reduce((a, b) => a + b, 0) / p; o[p - 1] = prev; for (let i = p; i < v.length; i++) { prev = v[i] * k + prev * (1 - k); o[i] = prev; } return o; }
function rsi(c, p = 14) { const o = Array(c.length).fill(null); if (c.length <= p) return o; let g = 0, l = 0; for (let i = 1; i <= p; i++) { const ch = c[i] - c[i - 1]; g += Math.max(ch, 0); l += Math.max(-ch, 0); } let ag = g / p, al = l / p; o[p] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); for (let i = p + 1; i < c.length; i++) { const ch = c[i] - c[i - 1]; ag = (ag * (p - 1) + Math.max(ch, 0)) / p; al = (al * (p - 1) + Math.max(-ch, 0)) / p; o[i] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); } return o; }
function macd(c) { const ef = ema(c, 12), es = ema(c, 26); const line = c.map((_, i) => ef[i] != null && es[i] != null ? ef[i] - es[i] : null); const idx = []; const sigIn = []; line.forEach((x, i) => { if (x != null) { idx.push(i); sigIn.push(x); } }); const so = ema(sigIn, 9); const signal = Array(line.length).fill(null); idx.forEach((i, j) => (signal[i] = so[j])); const hist = line.map((x, i) => x != null && signal[i] != null ? x - signal[i] : null); return [line, signal, hist]; }
function bollinger(c, p = 20, k = 2) { const mid = sma(c, p); const up = Array(c.length).fill(null), lo = Array(c.length).fill(null); for (let i = 0; i < c.length; i++) { if (i >= p - 1) { const w = c.slice(i - p + 1, i + 1); const m = mid[i]; const sd = Math.sqrt(w.reduce((a, x) => a + (x - m) ** 2, 0) / p); up[i] = m + k * sd; lo[i] = m - k * sd; } } return [up, mid, lo]; }
function stoch(h, l, c, kp = 14, dp = 3) { const k = Array(c.length).fill(null); for (let i = 0; i < c.length; i++) { if (i >= kp - 1) { const hh = Math.max(...h.slice(i - kp + 1, i + 1)); const ll = Math.min(...l.slice(i - kp + 1, i + 1)); k[i] = hh > ll ? (100 * (c[i] - ll)) / (hh - ll) : 50; } } const d = Array(c.length).fill(null); for (let i = 0; i < c.length; i++) { const w = []; for (let j = Math.max(0, i - dp + 1); j <= i; j++) if (k[j] != null) w.push(k[j]); if (w.length === dp) d[i] = w.reduce((a, b) => a + b, 0) / dp; } return [k, d]; }
function atr(h, l, c, p = 14) { const n = c.length, tr = Array(n).fill(null), o = Array(n).fill(null); for (let i = 0; i < n; i++) tr[i] = i === 0 ? h[i] - l[i] : Math.max(h[i] - l[i], Math.abs(h[i] - c[i - 1]), Math.abs(l[i] - c[i - 1])); if (n > p) { let prev = tr.slice(1, p + 1).reduce((a, b) => a + b, 0) / p; o[p] = prev; for (let i = p + 1; i < n; i++) { prev = (prev * (p - 1) + tr[i]) / p; o[i] = prev; } } return o; }
function obv(c, v) { const n = c.length, o = Array(n).fill(null); if (!n) return o; let acc = 0; o[0] = 0; for (let i = 1; i < n; i++) { if (c[i] > c[i - 1]) acc += v[i]; else if (c[i] < c[i - 1]) acc -= v[i]; o[i] = acc; } return o; }
const r2 = (a, n = 2) => a.map((x) => (x == null ? null : +x.toFixed(n)));
const last = (a) => { for (let i = a.length - 1; i >= 0; i--) if (a[i] != null) return a[i]; return null; };

export function sampleTechnicals(ticker, days = 252) {
  const rnd = mulberry32(seedFrom(ticker || "DEMO"));
  const base = 20 + rnd() * 60;
  let price = base;
  // datas: os ultimos `days` pregoes (seg-sex) terminando hoje
  const dates = [];
  const d = new Date();
  while (dates.length < days) {
    if (d.getDay() !== 0 && d.getDay() !== 6) dates.push(d.toISOString().slice(0, 10));
    d.setDate(d.getDate() - 1);
  }
  dates.reverse();
  const candles = [];
  let drift = (rnd() - 0.5) * 0.02;
  for (let i = 0; i < days; i++) {
    if (i % 45 === 0) drift = (rnd() - 0.5) * 0.02;
    const vol = 0.008 + rnd() * 0.012;
    const ch = drift * 0.3 + (rnd() - 0.5) * vol * 2;
    const open = price;
    price = Math.max(1, price * (1 + ch));
    const high = Math.max(open, price) * (1 + rnd() * 0.008);
    const low = Math.min(open, price) * (1 - rnd() * 0.008);
    candles.push({
      date: dates[i],
      open: +open.toFixed(2), high: +high.toFixed(2), low: +low.toFixed(2), close: +price.toFixed(2),
      volume: Math.round(800000 + rnd() * 4000000),
    });
  }
  const c = candles.map((x) => x.close), h = candles.map((x) => x.high), l = candles.map((x) => x.low), v = candles.map((x) => x.volume);
  const [bbU, bbM, bbL] = bollinger(c), [mL, mS, mH] = macd(c), [sK, sD] = stoch(h, l, c);
  const sma20 = sma(c, 20), sma50 = sma(c, 50), ema9 = ema(c, 9), ema21 = ema(c, 21), rsi14 = rsi(c, 14), atr14 = atr(h, l, c), obvv = obv(c, v);
  const indicators = {
    sma20: r2(sma20), sma50: r2(sma50), ema9: r2(ema9), ema21: r2(ema21),
    bbUpper: r2(bbU), bbMiddle: r2(bbM), bbLower: r2(bbL),
    rsi14: r2(rsi14, 1), macd: r2(mL, 3), macdSignal: r2(mS, 3), macdHist: r2(mH, 3),
    stochK: r2(sK, 1), stochD: r2(sD, 1), atr14: r2(atr14), obv: obvv.map((x) => (x == null ? null : Math.round(x))),
  };
  const lc = last(c), s20 = last(sma20), s50 = last(sma50), rr = last(rsi14), mh = last(mH), sk = last(sK), sd = last(sD);
  const summary = {
    close: +lc.toFixed(2), rsi14: rr == null ? null : +rr.toFixed(1),
    rsiState: rr >= 70 ? "sobrecomprado" : rr <= 30 ? "sobrevendido" : "neutro",
    macdHist: mh == null ? null : +mh.toFixed(3), macdState: mh > 0 ? "alta" : mh < 0 ? "baixa" : "neutro",
    stochK: sk == null ? null : +sk.toFixed(1), stochD: sd == null ? null : +sd.toFixed(1),
    stochState: sk >= 80 ? "sobrecomprado" : sk <= 20 ? "sobrevendido" : "neutro",
    sma20: s20 == null ? null : +s20.toFixed(2), sma50: s50 == null ? null : +s50.toFixed(2),
    trend: s20 > s50 ? "alta" : s20 < s50 ? "baixa" : "lateral",
    priceVsSma20: lc > s20 ? "acima" : "abaixo",
    bbUpper: r2([last(bbU)])[0], bbLower: r2([last(bbL)])[0], atr14: r2([last(atr14)])[0],
  };
  const changePct = +(((c[c.length - 1] - c[0]) / c[0]) * 100).toFixed(2);
  return { t: ticker, currency: "BRL", candles, indicators, summary, periodChangePct: changePct, at: "exemplo", sample: true };
}
