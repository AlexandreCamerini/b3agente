/**
 * diaNaBolsaLogica.js — Fase 51 (51-08). Lógica PURA do card "Seu dia na bolsa"
 * e da faixa de dias de decisão. Sem React, sem I/O, importável por node.
 * A janela de 28 dias vem de `ultimas4Semanas` do servidor (D-17): nenhuma data
 * é calculada aqui a partir do relógio do aparelho.
 */

export const MAX_LINHAS_F1 = 3;

// Famílias presentes (conteúdo não vazio), na ordem que o servidor mandou.
export function familiasNaOrdem(card) {
  if (!card || !Array.isArray(card.ordem) || !card.familias) return [];
  const out = [];
  for (const f of card.ordem) {
    const fam = card.familias[String(f)];
    if (!fam) continue;
    const temLinhas = Array.isArray(fam.linhas) && fam.linhas.length > 0;
    const temCarteira = !!fam.carteiraIbov;
    const temFato = !!(fam.fato && fam.fato.chave);
    if (temLinhas || temCarteira || temFato) out.push(Number(f));
  }
  return out;
}

// No máximo 3 linhas visíveis; o excedente vira "+N" não clicável.
export function linhasVisiveis(linhas, excedenteServidor = 0) {
  const l = Array.isArray(linhas) ? linhas : [];
  const visiveis = l.slice(0, MAX_LINHAS_F1);
  return { visiveis, excedente: Math.max(0, l.length - visiveis.length) + (excedenteServidor | 0) };
}

// Chave estável de dedupe do daily_card_explored (D-18): card + tipo + alvo.
export function chaveExploracao(dataCard, tipo, alvoId) {
  return [dataCard, tipo, alvoId == null ? "" : alvoId].join("|");
}

// Datas (ISO) de decisão que caem dentro da janela devolvida pelo servidor.
function janela(ultimas4Semanas) {
  return Array.isArray(ultimas4Semanas) ? ultimas4Semanas : [];
}

export function contarDiasDecisao(diasDecisao, ultimas4Semanas) {
  const datas = new Set((janela(ultimas4Semanas)).map((d) => d && d.data));
  const vistos = new Set();
  for (const d of Array.isArray(diasDecisao) ? diasDecisao : []) {
    if (datas.has(d)) vistos.add(d);
  }
  return vistos.size;
}

// Chave de copy + vals do texto "X dias de decisão" (o chamador passa por diaNaBolsaTxt).
export function chaveDecisao4Sem(x) {
  return x === 0 ? "decisao_4sem_zero" : x === 1 ? "decisao_4sem_um" : "decisao_4sem";
}

// Texto final; `txt` = diaNaBolsaTxt injetado (mantém este módulo livre de copy.js).
export function textoDecisao4Sem(mode, x, txt) {
  return txt(mode, chaveDecisao4Sem(x), 0, { X: x });
}

// 28 itens {data, tipo}; dia sem pregão nunca vira "vazio" (fim de semana não quebra nada).
export function faixaDots(diasDecisao, ultimas4Semanas) {
  const dec = new Set(Array.isArray(diasDecisao) ? diasDecisao : []);
  return janela(ultimas4Semanas).map((d) => ({
    data: d.data,
    tipo: dec.has(d.data) ? "decisao" : !d.pregao ? "sem_pregao" : "vazio",
  }));
}
