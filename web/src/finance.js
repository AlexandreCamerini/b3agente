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
//  • Retorno acumulado: base resolvida pela própria SÉRIE de snapshots
//    (`resolverBaseSerie`): base carimbada provada, ou o 1º dia registrado, ou
//    nenhuma (retAcum null). A curva termina no patrimônio AO VIVO — assim o
//    número exibido e a curva são o MESMO valor. Histórico: já foi o ORÇAMENTO
//    INICIAL (`initialBudget`); 2026-10-06 (quick 261006-dvf) saiu de vez — era
//    um campo de formulário e gerou +10.193 % para um retorno real de ~+2,9 %.
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

// Quick 260908-ldg (2026-09-08): régua de três faixas de liquidez de opção —
// espelho DECLARADO de `server/app/options_quant.faixa_de_liquidez`
// (LIQUIDEZ_NEGOCIAVEL=55, LIQUIDEZ_DIFICIL=30). O front precisa da escala
// porque `/api/options/chain` entrega `liquidity.score` cru (sem rótulo) e o
// ramo OFFLINE do `deviceStore` (persistence.js) decide sem servidor — não é
// uma segunda régua, é a MESMA régua replicada e testada, mesma disciplina de
// `deviceStore` × `store.py` já vigente no resto do arquivo. Guardião de
// paridade byte-a-byte em `web/tests/test_faixa_liquidez_ui.mjs` (lê os dois
// arquivos-fonte). Score não-numérico/negativo cai em "SEM MERCADO" — nunca
// lança exceção (mesmo padrão do lado Python).
export const FAIXA_NEGOCIAVEL_MIN = 55;
export const FAIXA_DIFICIL_MIN = 30;

export function faixaDeLiquidez(score) {
  if (typeof score !== "number" || Number.isNaN(score) || score < 0) return "SEM MERCADO";
  if (score >= FAIXA_NEGOCIAVEL_MIN) return "NEGOCIÁVEL";
  if (score >= FAIXA_DIFICIL_MIN) return "DIFÍCIL";
  return "SEM MERCADO";
}

export function markPrice(quote, position) {
  const px = quote && typeof quote.price === "number" && quote.price > 0 ? quote.price : null;
  if (px != null) return px;
  const avg = position && typeof position.avg === "number" ? position.avg : 0;
  return avg;
}

// Fase 14 (Plano 05, D-6 do 14-CONTEXT.md): patrimônio total passa a somar
// as pernas de opção LASTREADAS (call coberta vendida / put de proteção
// comprada, `abrir_call_coberta`/`comprar_put_protecao`, Plano 14-02). 5º e
// 6º argumentos são ADITIVOS e OPCIONAIS — chamada antiga com 4 argumentos
// produz EXATAMENTE o resultado de hoje, nenhum call site quebra (os 7 sites
// em App.jsx continuam passando só 4).
//
// Regras:
//  • [REVERTIDO em 2026-10-06, quick 261006-bwv — ver nota no fim deste
//    bloco] Na Fase 14 só entravam posições com `lastro`; a posição do modelo
//    antigo (`buy_option`, sem `lastro`) ficava FORA do agregado.
//  • Marcação: prêmio ao vivo de `optionQuotes[contractSymbol]` quando for
//    número > 0; senão `avg` — MESMO piso estável de `markPrice` (nunca 0,
//    CLAUDE.md item 4).
//  • `side === "comprada"` (put de proteção): `+qty*preço` em `posVal`,
//    `+qty*avg` em `cost`, `+(preço-avg)*qty` em `openPnL` — é um ativo, o
//    prêmio foi desembolsado.
//  • `side === "vendida"` (call coberta): `-qty*preço` em `posVal` (passivo
//    de recompra — o prêmio recebido já está dentro de `cash`) e
//    `+(avg-preço)*qty` em `openPnL`. NÃO soma nada em `cost` — não houve
//    desembolso.
//  • `posVal` de AÇÃO continua contando a posição INTEIRA (`pos.qty`),
//    travada ou não: a trava restringe a VENDA, não retira o ativo do
//    patrimônio — não confundir `qtyLivre` (o que pode ser vendido) com o
//    que é marcado a mercado.
//  • `dayVal` não muda: continua contando só a variação diária de AÇÃO (sem
//    `change` diário confiável de contrato de opção nesta fase).
//  • Marcação ao vivo de contrato NÃO é buscada nesta fase pela tela de
//    Carteira (`optionQuotes` chega vazio por padrão, perna marcada pelo
//    prêmio de abertura) — cada cadeia é uma requisição contra o orçamento
//    medido do mydata (ADR-020), que é justamente o que está travando a
//    virada de produção; gastar requisição por posição na Carteira compraria
//    um número mais fresco ao preço de agravar esse bloqueio.
//
// quick 261006-bwv (2026-10-06): perna sem lastro (`buy_option`) passa a
// entrar no agregado — antes ficava fora e o caixa debitado sumia do
// patrimônio (caso VALEV731W2: PUT 100 x R$ 0,92, R$ 92 a menos na tela).
// Perna sem `side` é COMPRADA. Regra sem cotação viva = custo de entrada
// (`avg`, o prêmio de fato pago — nunca 0, nunca inventado), sempre contada em
// `opcoesSemMarcacao` para a UI sinalizar "prêmio de abertura — sem cotação ao
// vivo". Gêmeo backend: `store.valor_opcoes`; paridade travada pela fixture
// server/tests/fixtures/patrimonio_opcoes_paridade.json.
export function portfolioMetrics(positions, quotes, cash, reservado, optionPositions, optionQuotes) {
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
  const ops = Array.isArray(optionPositions) ? optionPositions : [];
  const oq = optionQuotes || {};
  let opcoesVal = 0, opcoesPnL = 0, opcoesSemMarcacao = 0;
  for (const op of ops) {
    if (!op || typeof op !== "object") continue;
    const qty = Number(op.qty) || 0;
    const avg = Number(op.avg) || 0;
    const vivo = oq[op.id];
    const temVivo = typeof vivo === "number" && Number.isFinite(vivo) && vivo > 0;
    const preco = temVivo ? vivo : avg; // mesmo piso estável de markPrice
    if (!temVivo) opcoesSemMarcacao += 1;
    if (op.side === "vendida") {
      opcoesVal += -(qty * preco); // passivo de recompra — prêmio recebido já está em `cash`
      opcoesPnL += (avg - preco) * qty;
    } else { // "comprada" ou ausente (perna de buy_option)
      opcoesVal += qty * preco;
      opcoesPnL += (preco - avg) * qty;
    }
  }
  const patr = c + r + posVal + opcoesVal;
  const openPct = cost > 0 ? (openPnL / cost) * 100 : 0;
  return { posVal, cost, openPnL, openPct, dayVal, patr, cash: c, reservado: r, opcoesVal, opcoesPnL, opcoesSemMarcacao };
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

// Quick 260906-vf9 (C-06, REPORT-01), escopo REDUZIDO: uma frase em
// português simples por operação EXECUTADA já existente no Histórico — não
// cria tela/aba/endpoint novo. Função PURA: não inventa dado que não esteja
// em `h` (CLAUDE.md princípios 4/5) — campo essencial ausente/inválido
// devolve `null`, nunca fabrica um "—" dentro de uma frase em prosa.
//
// `finance.js` não tem formatador de moeda (nf2/price em App.jsx são
// módulo-locais, não exportados de propósito — importar de App.jsx criaria
// ciclo de import). Duplicação deliberada: função pura não pode depender da
// camada de UI.
const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function resumoOperacao(h) {
  if (!h || typeof h !== "object") return null;
  // Entrada REJEITADA já tem sua própria linha ("Rejeitada: ...") no
  // Histórico — nunca duplicar. Condição SEMPRE === "rejeitada" (nunca
  // !== "executada"), mesma regra de App.jsx (FIX-C02): entrada LEGADA sem
  // `status` conta como executada, histórico não se reescreve.
  if (h.status === "rejeitada") return null;
  if (h.type !== "COMPRA" && h.type !== "VENDA") return null;
  if (h.qty == null) return null;
  const precoNum = Number(h.price);
  if (h.price == null || !isFinite(precoNum)) return null;
  const precoTxt = nf2.format(precoNum);

  if (h.type === "COMPRA") {
    return `Comprou ${h.qty} ${h.t} a R$ ${precoTxt}.`;
  }

  // VENDA — sufixo de motivo (nada para "manual"/undefined/valor desconhecido).
  let sufixoMotivo = "";
  if (h.motivo === "stop") sufixoMotivo = " no stop";
  else if (h.motivo === "alvo") sufixoMotivo = " no alvo";
  else if (h.motivo === "vencimento") sufixoMotivo = " no vencimento";
  const base = `Vendeu ${h.qty} ${h.t} a R$ ${precoTxt}${sufixoMotivo}`;

  const pnlNum = Number(h.pnl);
  // pnl nulo/inválido é defensivo (o motor não deveria produzir) — sem
  // resultado, sem inventar sinal de lucro/prejuízo.
  if (h.pnl == null || !isFinite(pnlNum)) return `${base}.`;

  const pnlTxt = nf2.format(Math.abs(pnlNum));
  return pnlNum >= 0
    ? `${base}, com lucro de R$ ${pnlTxt}.`
    : `${base}, com prejuízo de R$ ${pnlTxt}.`;
}

// Retorno do dia em %: variação do patrimônio no dia sobre a base de ontem
// (patr − ganho_do_dia). Seguro contra base <= 0.
export function dayReturnPct(patr, dayVal) {
  const base = patr - dayVal;
  return base > 0 ? (dayVal / base) * 100 : 0;
}

// Base do retorno acumulado, resolvida na LEITURA pela própria série.
// Gêmeo de store.resolver_base_serie (server/app/store.py) — paridade travada por
// test_retorno_acumulado_base.mjs/.py sobre server/tests/fixtures/retorno_acumulado_casos.json.
// Pura: não muta a entrada. `initialBudget` nunca entra (quick 261006-dvf, 2026-10-06).
// Retorna { origem, base, inicio, desde, serie } — `inicio` indexa `serie`
// (já filtrada e ordenada). origem: carimbada | primeiro_registro | sem_serie | inconsistente.
const TOL_BASE = 0.01;
export function resolverBaseSerie(snapshots) {
  const num = (v) => typeof v === "number" && isFinite(v);
  const conhecida = (s) => num(s.base) && s.base > 0;
  const serie = (Array.isArray(snapshots) ? snapshots : [])
    .filter((s) => s && num(s.patrimonio) && typeof s.data === "string")
    .sort((a, b) => (a.data < b.data ? -1 : a.data > b.data ? 1 : 0));
  const vazio = { origem: "sem_serie", base: null, inicio: null, desde: null, serie };
  if (!serie.length) return vazio;
  let vigente = null, inicio = null;
  if (conhecida(serie[0])) { vigente = serie[0].base; inicio = 0; }
  for (let i = 1; i < serie.length; i++) {
    const si = serie[i];
    if (!conhecida(si)) continue; // cliente antigo: herda a vigente
    const ancora = Math.abs(si.base - si.patrimonio) <= TOL_BASE;
    if (vigente === null) {
      // carimbo isolado sobre série sem base = o caso do bug (initialBudget legado);
      // só vale como âncora o ponto sem operação (base == patrimônio).
      if (ancora) { vigente = si.base; inicio = i; }
    } else if (si.base !== vigente) {
      if (ancora) { vigente = si.base; inicio = i; } // aporte/retirada reinicia a janela
      else return { ...vazio, origem: "inconsistente" };
    }
  }
  if (vigente !== null) return { origem: "carimbada", base: vigente, inicio, desde: serie[inicio].data, serie };
  if (serie[0].patrimonio > 0) return { origem: "primeiro_registro", base: serie[0].patrimonio, inicio: 0, desde: serie[0].data, serie };
  return vazio;
}

// Curva de capital + retorno acumulado + drawdown, todos consistentes entre si.
// snapshots: [{ data:"YYYY-MM-DD", patrimonio:number, base?:number }, ...]
// `budget` permanece na assinatura por compatibilidade de chamada e NÃO é usado
// como divisor (2026-10-06, quick 261006-dvf: era campo de formulário; ver
// resolverBaseSerie). Sem base determinável, retAcum é null — nunca 0.
export function equityCurve(snapshots, budget, livePatr, todayYmd) { // eslint-disable-line no-unused-vars
  const r = resolverBaseSerie(snapshots);
  const base = r.base;
  // Janela: só de `inicio` em diante — vale para retorno/drawdown/benchmark (a base
  // só existe a partir dali). O patrimônio ANTERIOR é dado real e entra apenas na
  // exibição (`curvaCompleta`). Nota 2026-10-06 (quick 261006-qre, regressão da
  // 261006-dvf): descartar o prefixo da LINHA desenhada fazia o começo da curva sumir.
  const k = r.inicio || 0;
  const snaps = r.serie.slice(k);
  const antes = r.serie.slice(0, k);
  const series = snaps.map((s) => s.patrimonio);

  // série de exibição: snapshots, com o ÚLTIMO ponto refletindo o patrimônio AO
  // VIVO (substitui o snapshot de hoje; senão anexa). `datas` é construída em
  // PARALELO a `plot` — Plano 04-06 (FIX-C03): permite ao `benchmarkSerie`
  // alinhar o Ibovespa por data real em vez de por índice.
  let plot = series.slice();
  let datasPlot = snaps.map((s) => s.data);
  if (livePatr != null && isFinite(livePatr)) {
    const last = snaps[snaps.length - 1];
    if (last && todayYmd && last.data === todayYmd && plot.length) {
      plot[plot.length - 1] = livePatr;
    } else {
      plot.push(livePatr);
      datasPlot.push(todayYmd != null ? todayYmd : null);
    }
  }
  // ponto-base só em `carimbada` (capital aportado, não é um pregão: sem data,
  // tratado por `benchmarkSerie` como "sem data"). `primeiro_registro` já tem a
  // base como 1º ponto.
  const comPontoBase = r.origem === "carimbada";
  const curve = comPontoBase ? [base, ...plot] : plot;
  const datas = comPontoBase ? [null, ...datasPlot] : datasPlot;
  const end = curve.length ? curve[curve.length - 1] : (Number(livePatr) || 0);
  const retAcum = base > 0 ? ((end - base) / base) * 100 : null;

  let peak = curve.length ? curve[0] : 0, dd = 0;
  for (const v of curve) {
    if (v > peak) peak = v;
    if (peak > 0) { const d = ((peak - v) / peak) * 100; if (d > dd) dd = d; }
  }
  // exibição: série inteira (mesma referência de curve/datas quando não há prefixo)
  const curvaCompleta = k > 0 ? [...antes.map((s) => s.patrimonio), ...curve] : curve;
  const datasCompleta = k > 0 ? [...antes.map((s) => s.data), ...datas] : datas;
  return {
    curve, series, days: r.serie.length, diasJanela: series.length, retAcum, drawdown: dd, base, end, datas,
    baseOrigem: r.origem, baseDesde: r.desde, baseInicio: r.inicio,
    curvaCompleta, datasCompleta, inicioNaCurvaCompleta: k,
  };
}

// Curva da carteira em % desde a base da série (escala compartilhada com o
// Ibovespa na Evolução). Quick 261007-w5t (2026-10-07): sem base > 0 devolve
// null — nunca uma série de 0 % (antes: `: 0` desenhava linha plana como se a
// carteira não tivesse variado). Só exibição: sem gêmeo em store.py.
export function pctDesdeBase(curva, base) {
  if (!Array.isArray(curva) || typeof base !== "number" || !isFinite(base) || base <= 0) return null;
  return curva.map((v) => (typeof v === "number" && isFinite(v) ? ((v - base) / base) * 100 : null));
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

// ---------------------------------------------------------------------------
// Achado ao vivo (ABEV3, 2026-09-07): App.jsx consumia `setups[0]` cru em
// dois pontos, sem filtrar setup aposentado — enquanto o backend já filtra
// (`server/app/setups.py:725`, `plano_do_resultado`: `operaveis = [s for s in
// setups_list if not s.get("aposentado")]`). Resultado: `setupEntrada`
// gravado com `setup`/`veredito` de UM setup (via `sc.melhorSetup`, fonte já
// filtrada pelo backend) e `lado`/`gatilho`/`invalidacao` de OUTRO
// (`setups[0]` cru, podendo ser aposentado) — meta internamente contraditório
// que inverte a leitura de invalidação em App.jsx (`se.lado === "baixa" ? cur
// > se.invalidacao : cur < se.invalidacao`). As duas funções abaixo são o
// espelho no front da regra do backend, casa única de consumo dos dois
// pontos afetados (grade da watchlist e card do Radar).
// ---------------------------------------------------------------------------

// setupOperavel(setups, melhorSetupNome): devolve o elemento de `setups` que
// é a base do plano operacional — NUNCA um `aposentado: true`. Casamento por
// NOME vem primeiro (não por índice) porque `melhorSetupNome` já é a fonte
// filtrada pelo backend (`melhorSetup` no payload do scan); casar por nome
// garante POR CONSTRUÇÃO que `setup`/`veredito` (de `melhorSetupNome`) e
// `lado`/`gatilho`/`invalidacao` (do elemento devolvido aqui) descrevem o
// MESMO setup — não uma coincidência de índice como era `setups[0]`. Sem
// nome (ausente/não encontrado), cai no fallback por ordem, mesma regra de
// `setups.py:725` (`operaveis[0]`). Defensiva a lista ausente/não-array e a
// elemento nulo dentro da lista.
export function setupOperavel(setups, melhorSetupNome) {
  const lista = Array.isArray(setups) ? setups : [];
  const operaveis = lista.filter((s) => s && !s.aposentado);
  if (!operaveis.length) return null;
  if (typeof melhorSetupNome === "string" && melhorSetupNome) {
    const porNome = operaveis.find((s) => s.nome === melhorSetupNome);
    if (porNome) return porNome;
  }
  return operaveis[0];
}

// metaDeEntrada(sc): monta o meta de compra a partir do scan (`sc`), para
// gravação em `setupEntrada` (`store.buy(meta)`). `setup`/`veredito`/
// `confluencia`/`snapshotId` continuam vindo direto de `sc` (fonte já
// filtrada pelo backend); `lado`/`gatilho`/`invalidacao` entram por SPREAD
// CONDICIONAL a partir do MESMO elemento operável — ficam literalmente
// AUSENTES do objeto quando não há setup operável (princípio 4 do CLAUDE.md:
// nunca inventar dado). `_sanitize_trade_meta` (server/app/store.py:621-637)
// já omite chave ausente sem quebrar o payload salvo — nada de `0` nem o
// aposentado como stand-in.
export function metaDeEntrada(sc) {
  const s = sc || {};
  const op = setupOperavel(s.setups, s.melhorSetup);
  return {
    setup: (op && op.nome) || s.melhorSetup || undefined,
    veredito: s.veredito,
    confluencia: s.confluencia,
    snapshotId: s.snapshotId,
    ...(op ? { lado: op.lado, gatilho: op.gatilho, invalidacao: op.invalidacao } : {}),
  };
}
