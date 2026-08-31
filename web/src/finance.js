// Cálculos financeiros determinísticos (sem IA, sem rede) — FONTE ÚNICA usada
// pela Home/Topbar, Carteira e Evolução, para que os números BATAM entre si.
//
// Definições adotadas (Objetivo 3 — auditoria de KPIs):
//  • Preço de marcação: cotação ao vivo quando disponível (> 0); senão, o preço
//    médio da posição (`avg`) como piso estável — evita "tela piscando" para 0
//    enquanto as cotações não chegaram. Em regime (cotações carregadas) o
//    resultado é idêntico ao anterior.
//  • Patrimônio = caixa + caixa reservado em ordens pendentes + Σ (qty ×
//    preço). Fase 2 (MERC-02..04, D-05): a reserva de uma ordem pendente
//    debita `cash` na hora do PEDIDO (reusa o caminho de débito existente),
//    e sem somar o reservado de volta o app mostraria o patrimônio
//    encolhendo sozinho ao criar uma ordem — dinheiro simulado sumindo da
//    tela, o oposto da transparência que o produto promete.
//  • Resultado aberto (P&L) = Σ (preço − avg) × qty ; % sobre o CUSTO.
//  • Retorno do dia (R$) = Σ qty × preço × (variação%_do_ativo / 100), contando
//    apenas posições com cotação real (com `change`).
//  • Retorno acumulado: base = ORÇAMENTO INICIAL (`initialBudget`). A curva começa
//    no orçamento e termina no patrimônio AO VIVO — assim o número exibido e a
//    curva são o MESMO valor. (Se não houver orçamento, cai para o 1º snapshot.)
//  • Drawdown = maior queda percentual desde o pico, sobre a MESMA curva exibida.
//  • Quantidade livre (Fase 14, opções lastreadas) = quantidade total de uma
//    posição menos a travada como lastro de uma CALL coberta aberta
//    (`qtyTravada`). Gêmeo exato de `store.qty_livre` (`server/app/store.py`,
//    Plano 14-01) — MESMO nome, MESMA semântica; nenhum outro módulo do
//    front recalcula a subtração — `persistence.js`/`App.jsx` importam
//    `qtyLivre` daqui. Mesmo padrão de fonte única do front já usado por
//    RR_MIN/RR_MIN_TXT abaixo (amarrado ao backend por teste dedicado).

// Relação risco-retorno mínima (piso 1,5:1) — espelho de
// server/app/skill_ref.py (RR_MIN/RR_MIN_TXT). ADR-015 (06-05): fonte única
// do front, amarrada ao backend por web/tests/test_rr_min_fonte_unica.mjs e
// por test_a8iii em server/tests/test_auditoria_prompts.py. finance.js é o
// módulo de números determinísticos do front — é onde a constante pertence.
export const RR_MIN = 1.5;
export const RR_MIN_TXT = "1,5"; // formato pt-BR para interpolação em texto

// Fase 14 (Plano 05, D-3 do 14-CONTEXT.md): quantidade de uma posição que
// pode ser vendida — total menos o que está travado como lastro de uma CALL
// coberta aberta (`qtyTravada`). ÚNICA fonte da aritmética de quantidade
// vendável no FRONT — proibido recalcular a subtração `qty - qtyTravada` em
// outro módulo (mesma disciplina do gêmeo backend, `store.qty_livre`,
// `server/app/store.py`, Plano 14-01 — MESMO nome, MESMA semântica).
// `persistence.js`/`App.jsx` IMPORTAM esta função, nenhum dos dois reimplementa
// a subtração. Defensiva a `pos` nulo, mesmo estilo de `markPrice` acima.
// `qtyTravada` ausente (posição do modelo antigo, sem CALL coberta) lê 0.
export function qtyLivre(pos) {
  return Math.max(0, (Number(pos && pos.qty) || 0) - (Number(pos && pos.qtyTravada) || 0));
}

export function markPrice(quote, position) {
  const px = quote && typeof quote.price === "number" && quote.price > 0 ? quote.price : null;
  if (px != null) return px;
  const avg = position && typeof position.avg === "number" ? position.avg : 0;
  return avg;
}

export function portfolioMetrics(positions, quotes, cash, reservado) {
  const ps = Array.isArray(positions) ? positions : [];
  const q = quotes || {};
  let posVal = 0, cost = 0, openPnL = 0, dayVal = 0;
  for (const p of ps) {
    const qty = Number(p && p.qty) || 0;
    const quote = q[p && p.t] || {};
    const price = markPrice(quote, p);
    const avg = Number(p && p.avg) || 0;
    posVal += qty * price;
    cost += qty * avg;
    openPnL += (price - avg) * qty;
    if (typeof quote.price === "number" && quote.price > 0 && typeof quote.change === "number") {
      dayVal += qty * quote.price * (quote.change / 100);
    }
  }
  const c = Number(cash) || 0;
  const r = Number(reservado) || 0; // 4º parâmetro opcional (D-05); mesma defensiva do cash acima
  const patr = c + r + posVal;
  const openPct = cost > 0 ? (openPnL / cost) * 100 : 0;
  return { posVal, cost, openPnL, openPct, dayVal, patr, cash: c, reservado: r };
}

// Maior posição da carteira em % do patrimônio (Plano 04-07, FIX-C05) — mesma
// família de cálculo de portfolioMetrics, usando o MESMO markPrice para que o
// `pct` bata com o patrimônio exibido na tela. Função PURA: não toca em cash,
// reservado nem optionPositions (posição de opção é coleção própria,
// ADR-003; o aviso de concentração fala de ativo). NÃO aplica o limiar de
// 50% aqui — quem decide o corte é a UI (finance.js só devolve o número).
export function concentracaoMaxima(positions, quotes, patr) {
  const p = Number(patr);
  if (!(p > 0)) return null;
  if (!Array.isArray(positions) || positions.length === 0) return null;
  const q = quotes || {};
  let melhor = null;
  for (const pos of positions) {
    const qty = Number(pos && pos.qty) || 0;
    const quote = q[pos && pos.t] || {};
    const price = markPrice(quote, pos);
    const valor = qty * price;
    if (!melhor || valor > melhor.valor) {
      melhor = { t: pos && pos.t, valor };
    }
  }
  if (!melhor) return null;
  return { t: melhor.t, valor: melhor.valor, pct: (melhor.valor / p) * 100 };
}

// Retorno do dia em %: variação do patrimônio no dia sobre a base de ontem
// (patr − ganho_do_dia). Seguro contra base <= 0.
export function dayReturnPct(patr, dayVal) {
  const base = patr - dayVal;
  return base > 0 ? (dayVal / base) * 100 : 0;
}

// Curva de capital + retorno acumulado + drawdown, todos consistentes entre si.
// snapshots: [{ data:"YYYY-MM-DD", patrimonio:number }, ...]
export function equityCurve(snapshots, budget, livePatr, todayYmd) {
  const snaps = (Array.isArray(snapshots) ? snapshots : []).filter(
    (s) => s && typeof s.patrimonio === "number" && isFinite(s.patrimonio)
  );
  const series = snaps.map((s) => s.patrimonio);
  // BASE = o capital com que ESTA série começou, carimbado no 1º snapshot
  // (`base`). O `initialBudget` corrente só entra quando ainda não há série.
  //
  // Antes a base era sempre o `initialBudget`, que a pessoa edita livremente na
  // Config sem que caixa ou posições mudem — e o "retorno acumulado" de meses
  // era reescrito por uma digitação. Era daí que saía o +9990% sem operação
  // nenhuma por trás. Retorno é (patrimônio de hoje ÷ capital que entrou); o
  // divisor não pode ser um campo de formulário.
  const carimbada = snaps.find((s) => typeof s.base === "number" && s.base > 0);
  const b = carimbada ? carimbada.base : (Number(budget) || 0);
  const base = b > 0 ? b : (series.length ? series[0] : (Number(livePatr) || 0));

  // série de exibição: baseline (orçamento) → snapshots, com o ÚLTIMO ponto
  // refletindo o patrimônio AO VIVO (substitui o snapshot de hoje; senão anexa).
  // `datas` é construída em PARALELO a `plot`, mesma decisão de
  // substituir/anexar — Plano 04-06 (FIX-C03): é o que permite ao
  // `benchmarkSerie` alinhar o Ibovespa por data real em vez de por índice.
  let plot = series.slice();
  let datasPlot = snaps.map((s) => s.data);
  if (livePatr != null && isFinite(livePatr)) {
    const last = snaps[snaps.length - 1];
    if (last && todayYmd && last.data === todayYmd && plot.length) {
      plot[plot.length - 1] = livePatr;
      // datasPlot: a data do último ponto não muda (já é a de hoje).
    } else {
      plot.push(livePatr);
      datasPlot.push(todayYmd != null ? todayYmd : null);
    }
  }
  const curve = b > 0 ? [base, ...plot] : plot;
  // ponto-base não carrega data própria (o baseline do orçamento não é um
  // pregão) — `null` na posição, tratado por `benchmarkSerie` como "sem data".
  const datas = b > 0 ? [null, ...datasPlot] : datasPlot;
  const end = curve.length ? curve[curve.length - 1] : base;
  const retAcum = base > 0 ? ((end - base) / base) * 100 : 0;

  let peak = curve.length ? curve[0] : 0, dd = 0;
  for (const v of curve) {
    if (v > peak) peak = v;
    if (peak > 0) { const d = ((peak - v) / peak) * 100; if (d > dd) dd = d; }
  }
  return { curve, series, days: series.length, retAcum, drawdown: dd, base, end, datas };
}

// Alinha a série do Ibovespa (candles do provedor) às DATAS REAIS da curva da
// carteira (`equityCurve(...).datas`) — Plano 04-06 (FIX-C03). Pura: sem
// rede, sem leitura de relógio do sistema, sem estado de módulo (I/O fica no
// chamador, mesma disciplina de portfolioMetrics/sizingPlano). Nunca
// extrapola: uma data anterior a QUALQUER vela vira `null` (não 0, não
// inventado); uma data sem pregão usa o último fechamento REAL anterior (não
// é valor inventado — é onde o índice de fato estava).
export function benchmarkSerie(candles, datas) {
  if (!Array.isArray(candles) || !Array.isArray(datas)) return null;

  const validos = [];
  for (const c of candles) {
    if (!c || typeof c.date !== "string" || !c.date) continue;
    const close = c.close;
    if (typeof close !== "number" || !isFinite(close) || close <= 0) continue;
    validos.push({ date: c.date, close });
  }
  if (validos.length < 2) return null;
  validos.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  // último fechamento REAL em ou antes de `date` — nunca um valor futuro.
  function closeAtOrBefore(date) {
    let found = null;
    for (const c of validos) {
      if (c.date <= date) found = c.close;
      else break;
    }
    return found;
  }

  const raw = datas.map((d) => (typeof d === "string" && d ? closeAtOrBefore(d) : null));

  let coberturaReal = 0, firstIdx = -1;
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] != null) {
      coberturaReal++;
      if (firstIdx === -1) firstIdx = i;
    }
  }
  if (coberturaReal < 2) return null;

  const firstClose = raw[firstIdx];
  // pct[i] = variação % desde o primeiro ponto COBERTO (não desde a 1ª vela
  // recebida). O ponto-base (datas[i] === null) recebe 0 quando existe
  // cobertura adiante — garantido aqui por coberturaReal >= 2.
  const pct = datas.map((d, i) => {
    if (d == null) return 0;
    if (raw[i] == null) return null;
    return ((raw[i] - firstClose) / firstClose) * 100;
  });

  let retAcum = null;
  for (let i = pct.length - 1; i >= 0; i--) {
    if (pct[i] != null) { retAcum = pct[i]; break; }
  }
  const cobertura = pct.filter((v) => v != null).length;
  return { pct, retAcum, cobertura };
}

// FASE 7 (F7.1) — Modo Operador: position sizing por % de risco do capital.
// Puro e espelhável em teste: o plano (entrada/stop/riscoPorAcao) vem PRONTO do
// servidor (setups.plano_operacional); aqui só entra a aritmética do usuário —
// capital e % de risco ficam no aparelho/conta, nunca no cache compartilhado.
// Lote padrão B3 = 100 ações; risco financeiro = capital × pct/100.
export function sizingPlano(plano, capital, pctPorTrade) {
  const p = plano || {};
  if (p.decisao !== "COMPRAR" && p.decisao !== "VENDER") return null;
  const risco = typeof p.riscoPorAcao === "number" ? p.riscoPorAcao : null;
  const entrada = typeof p.entrada === "number" ? p.entrada : null;
  const cap = typeof capital === "number" && capital > 0 ? capital : null;
  const pct = typeof pctPorTrade === "number" && pctPorTrade > 0 ? Math.min(5, pctPorTrade) : 1.0;
  if (!risco || risco <= 0 || !entrada || !cap) return null;
  const riscoFinanceiro = +(cap * (pct / 100)).toFixed(2);
  const qtd = Math.floor(riscoFinanceiro / risco / 100) * 100;
  if (qtd < 100) {
    return { qtd: 0, valorAprox: 0, riscoFinanceiro, pct, aviso: "Capital insuficiente para 1 lote de 100 com risco de " + pct + "% — aumente o capital operacional ou o % de risco." };
  }
  return { qtd, valorAprox: +(qtd * entrada).toFixed(2), riscoFinanceiro, pct, aviso: null };
}

// ---------------------------------------------------------------------------
// ADR-017 Bloco 3 (Fase 8, Plano 03) — estado do histórico medido por setup.
// Estas duas funções derivam ESTADO a partir do dicionário `historico` que o
// backend já calculou (`signal_ledger._fundir`, consumido por
// `server/app/regime.py`) — NENHUM número novo é computado aqui. A
// precedência do estado "insuficiente" sobre "inelegivel" codifica o
// princípio "Dois pisos de amostra" do ADR-017: ausência de evidência não é
// evidência negativa. Puras: sem `Date.now()` interno (a data de hoje é
// argumento), sem I/O, sem exceção para entrada malformada — entrada
// inesperada cai sempre no default mais conservador (nunca vira "elegivel"
// nem "inelegivel" por engano).
// ---------------------------------------------------------------------------

// Extrai {y,mo,d} do prefixo YYYY-MM-DD de uma string (aceita também um
// ISO-8601 completo, ex.: `calculadoEm`). NUNCA usa `new Date(string)` — no
// WKWebView isso interpreta a string em fuso local e desloca o dia.
function _ymdParts(s) {
  if (typeof s !== "string") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
  if (!m) return null;
  return { y: +m[1], mo: +m[2], d: +m[3] };
}
function _utcMs(parts) {
  return Date.UTC(parts.y, parts.mo - 1, parts.d);
}
function _ehFimDeSemana(utcMs) {
  const dow = new Date(utcMs).getUTCDay(); // 0=domingo, 6=sábado
  return dow === 0 || dow === 6;
}

export function historicoEstado(historico, aposentado) {
  if (aposentado === true) return "aposentado"; // precedência sobre tudo
  if (!historico || typeof historico !== "object") return "nunca_medido";
  if (historico.insuficiente === true || historico.elegivel == null) return "insuficiente";
  if (historico.elegivel === true) return "elegivel";
  if (historico.elegivel === false) return "inelegivel";
  // defensivo: valor inesperado em `elegivel` nunca vira "inelegivel" sem
  // veredito explícito — cai no mesmo estado neutro de "sem evidência".
  return "insuficiente";
}

export function historicoDesatualizado(historico, hojeYmd) {
  if (!historico || typeof historico !== "object") return false;
  const ref = _ymdParts(historico.medidoAte || historico.calculadoEm);
  const hoje = _ymdParts(hojeYmd);
  // ausência de carimbo (ou de hojeYmd) não vira "dado velho" — a UI só
  // degrada com evidência de data (regra: nunca inventar estado).
  if (!ref || !hoje) return false;
  const refMs = _utcMs(ref);
  const hojeMs = _utcMs(hoje);
  if (refMs >= hojeMs) return false; // hoje ou no futuro: nunca degrada
  // conta 2 dias ÚTEIS para trás a partir de hoje (sábado/domingo não
  // contam; feriados NÃO são considerados — limitação deliberada: erra
  // sempre para o lado de "não degradar").
  let limiteMs = hojeMs, uteis = 0;
  while (uteis < 2) {
    limiteMs -= 86400000;
    if (!_ehFimDeSemana(limiteMs)) uteis++;
  }
  return refMs < limiteMs; // estritamente anterior ao limite
}
