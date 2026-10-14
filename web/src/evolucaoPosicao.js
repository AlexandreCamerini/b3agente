// 2026-10-13 (quick 261013-svo) — evolução do resultado em aberto de UMA posição de ações (puro).
//
// Reconstrói, pregão a pregão desde a 1ª compra do episódio atual, qty e PM vigentes a partir de
// `data.history` (mesma regra de server/app/store.py: compra = média ponderada com PM arredondado a
// 2 casas; venda parcial preserva o PM; venda total encerra o episódio) e mede
// (fechamento do dia − PM vigente) × qty vigente.
//
// Princípio 4 (não inventar valor): se a reconstrução não fecha com a posição atual, se não há compra,
// se há menos de 2 pregões fechados ou se o período não pode ser definido, NADA é desenhado — o helper
// devolve { ok: false, motivo } e a UI mostra o motivo. Princípio 5: cálculo determinístico, nunca IA.
//
// Sem import de React/App. Único lugar do front desta task que lê relógio/fuso é `hojeBRT`.
// `PERIODOS_CANDLES` espelha PERIOD_BARS de server/app/candles.py (travado por teste que lê o .py).
// O período só recorta a cauda do payload de candles; não afirma nada sobre orçamento de requisições.

const arred2 = (x) => Math.round(x * 100) / 100;
const YMD = /^(\d{4})-(\d{2})-(\d{2})$/;

function ymdValido(s) {
  if (typeof s !== "string") return false;
  const m = YMD.exec(s);
  if (!m) return false;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  return d.getUTCFullYear() === Number(m[1]) && d.getUTCMonth() === Number(m[2]) - 1 && d.getUTCDate() === Number(m[3]);
}

// "dd/mm/aaaa[ HH:MM]" (now_str() do backend, BRT) -> "AAAA-MM-DD" | null.
export function parseDataOperacao(s) {
  if (typeof s !== "string") return null;
  const m = /^(\d{2})\/(\d{2})\/(\d{4})(?:\s+\d{2}:\d{2})?$/.exec(s);
  if (!m) return null;
  const dia = Number(m[1]), mes = Number(m[2]);
  if (mes < 1 || mes > 12 || dia < 1 || dia > 31) return null;
  return m[3] + "-" + m[2] + "-" + m[1];
}

// Dia corrente na B3 (America/Sao_Paulo) em "AAAA-MM-DD"; relógio inválido -> null.
export function hojeBRT(agora = new Date()) {
  if (!(agora instanceof Date) || Number.isNaN(agora.getTime())) return null;
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(agora);
}

// Hora do dia na B3 (America/Sao_Paulo) em "HH:MM" (00:00–23:59); relógio inválido -> null.
// Quick 261013-vai (2026-10-14): mesma técnica de fuso de `hojeBRT`; serve ao deviceStore.cycle
// para não liquidar vencimento antes da abertura do próprio dia (espelho de pregao.ABERTURA).
export function horaMinutoBRT(agora = new Date()) {
  if (!(agora instanceof Date) || Number.isNaN(agora.getTime())) return null;
  const partes = new Intl.DateTimeFormat("en-GB", {
    timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(agora);
  const h = partes.find((p) => p.type === "hour").value;
  const m = partes.find((p) => p.type === "minute").value;
  return h + ":" + m;
}

// "AAAA-MM-DD" -> "dd/mm/aaaa" | null.
export function ymdParaBr(ymd) {
  if (typeof ymd !== "string") return null;
  const m = YMD.exec(ymd);
  return m ? m[3] + "/" + m[2] + "/" + m[1] : null;
}

export const PERIODOS_CANDLES = Object.freeze([["1mo", 22], ["3mo", 66], ["6mo", 126], ["1y", 252], ["2y", 504]]);

// Menor período cujo recorte cobre os pregões estimados desde `inicioYmd` (+5 de folga); acima de
// 504 barras -> "2y" (a série começa no 1º candle disponível e é marcada `parcial`).
export function periodoCandles(inicioYmd, hojeYmd) {
  if (!ymdValido(inicioYmd) || !ymdValido(hojeYmd) || inicioYmd > hojeYmd) return null;
  const a = YMD.exec(inicioYmd), b = YMD.exec(hojeYmd);
  const dias = Math.round((Date.UTC(+b[1], +b[2] - 1, +b[3]) - Date.UTC(+a[1], +a[2] - 1, +a[3])) / 86400000);
  const estimado = Math.ceil(dias * 5 / 7) + 5;
  for (const [per, barras] of PERIODOS_CANDLES) if (barras >= estimado) return per;
  return "2y";
}

function opsDoTicker(ticker, history) {
  const lista = Array.isArray(history) ? history : [];
  // histórico é newest-first: ordem cronológica = array invertido (sem ordenar por data).
  return [...lista].reverse().filter((h) => {
    if (!h || typeof h !== "object") return false;
    if (h.t !== ticker) return false;
    if (h.status !== undefined && h.status !== null && h.status !== "executada") return false;
    if (h.kind === "opcao") return false;
    if (h.underlying) return false;
    return h.type === "COMPRA" || h.type === "VENDA";
  });
}

export function reconstruirPosicao({ ticker, history, posicao } = {}) {
  if (!posicao || !(Number(posicao.qty) > 0)) return { ok: false, motivo: "sem_posicao" };
  let qty = 0, pm = null, ops = [], nCompras = 0, inicioYmd = null, totalCompras = 0;
  for (const h of opsDoTicker(ticker, history)) {
    const q = h.qty, preco = h.price, ymd = parseDataOperacao(h.date);
    if (typeof q !== "number" || !(q > 0) || !ymd) return { ok: false, motivo: "nao_fecha" };
    if (h.type === "COMPRA") {
      if (typeof preco !== "number" || !(preco > 0)) return { ok: false, motivo: "nao_fecha" };
      totalCompras++;
      if (qty === 0) { ops = []; nCompras = 0; inicioYmd = ymd; pm = arred2(preco); }
      else pm = arred2((pm * qty + preco * q) / (qty + q));
      qty += q; nCompras++;
      ops.push({ ymd, tipo: "compra", qtyDepois: qty, pmDepois: pm });
    } else {
      if (qty === 0) return { ok: false, motivo: "nao_fecha" };
      if (q >= qty) { qty = 0; pm = null; ops.push({ ymd, tipo: "venda", qtyDepois: 0, pmDepois: null }); }
      else { qty -= q; ops.push({ ymd, tipo: "venda", qtyDepois: qty, pmDepois: pm }); }
    }
  }
  if (totalCompras === 0) return { ok: false, motivo: "sem_compra" };
  if (qty !== Number(posicao.qty) || pm === null) return { ok: false, motivo: "nao_fecha" };
  if (Math.abs(pm - Number(posicao.avg)) > 0.01 * nCompras + 1e-9) return { ok: false, motivo: "nao_fecha" };
  return { ok: true, inicioYmd, ops, nCompras };
}

export function serieResultadoPosicao({ ticker, history, candles, posicao, hojeYmd } = {}) {
  const rec = reconstruirPosicao({ ticker, history, posicao });
  if (!rec.ok) return rec;
  const insuf = { ok: false, motivo: "candles_insuficientes" };
  if (!ymdValido(hojeYmd)) return insuf;
  // Candles válidos (formato, close finito > 0), deduplicados por data, ordenados.
  const porData = new Map();
  for (const c of Array.isArray(candles) ? candles : []) {
    if (!c || typeof c.date !== "string") continue;
    const data = c.date.slice(0, 10);
    if (!ymdValido(data)) continue;
    if (typeof c.close !== "number" || !Number.isFinite(c.close) || !(c.close > 0)) continue;
    porData.set(data, c.close);
  }
  const todos = [...porData.keys()].sort();
  if (todos.length === 0) return insuf;
  const parcial = todos[0] > rec.inicioYmd;
  // O candle de HOJE nunca entra: não é fechamento enquanto o pregão roda.
  const datas = todos.filter((d) => d >= rec.inicioYmd && d < hojeYmd);
  const pontos = [];
  let i = 0, qty = 0, pm = null;
  for (const data of datas) {
    while (i < rec.ops.length && rec.ops[i].ymd <= data) { qty = rec.ops[i].qtyDepois; pm = rec.ops[i].pmDepois; i++; }
    if (qty > 0) pontos.push({ data, resultado: arred2((porData.get(data) - pm) * qty) });
  }
  if (pontos.length < 2) return insuf;
  const desde = pontos[0].data, ate = pontos[pontos.length - 1].data;
  const marcas = [];
  for (const o of rec.ops) {
    if (parcial && o.ymd < desde) continue;
    const alvo = pontos.find((p) => p.data >= o.ymd);
    if (alvo) marcas.push({ data: alvo.data, tipo: o.tipo });
  }
  const rs = pontos.map((p) => p.resultado);
  return {
    ok: true, pontos, marcas,
    inicio: rec.inicioYmd, ate, parcial, desde,
    inicioBr: ymdParaBr(rec.inicioYmd), ateBr: ymdParaBr(ate), desdeBr: ymdParaBr(desde),
    min: Math.min(...rs), max: Math.max(...rs), ultimo: rs[rs.length - 1],
  };
}

// Geometria SVG pronta (o componente não faz conta). Domínio Y sempre inclui o zero.
export function geometriaSerie({ pontos, marcas, largura = 280, altura = 72, margem = 4 } = {}) {
  const ps = Array.isArray(pontos) ? pontos : [];
  const n = ps.length;
  const rs = ps.map((p) => p.resultado);
  let yMin = Math.min(0, ...rs), yMax = Math.max(0, ...rs);
  if (!(yMax > yMin)) { yMin = -1; yMax = 1; }
  const x = (idx) => (n > 1 ? margem + (idx / (n - 1)) * (largura - 2 * margem) : margem);
  const y = (v) => margem + ((yMax - v) / (yMax - yMin)) * (altura - 2 * margem);
  const d = ps.map((p, idx) => (idx === 0 ? "M" : "L") + x(idx).toFixed(1) + " " + y(p.resultado).toFixed(1)).join(" ");
  const ms = [];
  for (const m of Array.isArray(marcas) ? marcas : []) {
    const idx = ps.findIndex((p) => p.data === m.data);
    if (idx >= 0) ms.push({ x: x(idx), y: y(ps[idx].resultado), tipo: m.tipo });
  }
  return { d, yZero: y(0), marcas: ms, W: largura, H: altura };
}
