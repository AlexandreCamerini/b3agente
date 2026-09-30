/**
 * classificarOportunidades.js — quick 260928-u0h (2026-09-28).
 *
 * Classificação PURA (sem React, sem I/O) das posições da aba Oportunidades em
 * três grupos: estruturas abertas (proposta de ENCERRAMENTO), oportunidades
 * novas e posições sem proposta (com a chave do motivo). Nenhum texto nasce
 * aqui — só chaves; as frases moram em `copy.js` (`tiraOpcoesMotivo`).
 *
 * Por que separar: o backend monta o encerramento em `proposta_fechar` sem
 * consultar a leitura técnica, então ele não pode aparecer sob "confirmadas
 * pela leitura técnica".
 */

// Os 6 motivos que o motor devolve quando `proposta` é null
// (server/app/opcoes_lastreadas.py + main.py, rota de proposta).
const MOTIVOS_MOTOR = ["degradado", "sem_lastro", "sem_setup", "sem_vencimento_elegivel", "sem_contrato_liquido", "caixa_insuficiente"];

export const MOTIVOS_SEM_PROPOSTA = Object.freeze([
  "sem_setup", "sem_lastro", "sem_vencimento_elegivel", "sem_contrato_liquido",
  "caixa_insuficiente", "degradado", "sem_mercado", "sem_liquidez",
  "indisponivel", "aberta_sem_proposta", "desconhecido",
]);

// Espelho declarado de `pos_op_aberta` em server/app/main.py (rota
// /api/options/proposta): estrutura aberta = mesma posição de opção com
// `underlying === t` E `lastro` truthy. Quando existe, o servidor chama
// `proposta_fechar` e nunca `propor()`.
export function temEstruturaAberta(optionPositions, t) {
  const l = Array.isArray(optionPositions) ? optionPositions : [];
  for (let i = 0; i < l.length; i++) {
    const p = l[i];
    if (p && p.underlying === t && p.lastro) return true;
  }
  return false;
}

export function classificarOportunidades({ propostas, positions, optionPositions, carregando } = {}) {
  const abertas = [];
  const novas = [];
  const semProposta = [];
  const props = propostas || {};
  const lista = Array.isArray(positions) ? positions : [];
  for (let i = 0; i < lista.length; i++) {
    const p = lista[i];
    const e = props[p.t];
    const aberta = temEstruturaAberta(optionPositions, p.t);
    const pr = !!(e && e.gate && e.gate.liquida && e.proposta && e.proposta.proposta);
    if (pr) {
      (aberta ? abertas : novas).push({ p, pr: e.proposta.proposta });
      continue;
    }
    if (!e && carregando) continue;
    let motivo;
    if (aberta) motivo = "aberta_sem_proposta";
    else if (!e || !e.gate) motivo = "indisponivel";
    else if (!e.gate.liquida) motivo = e.gate.faixa === "SEM MERCADO" ? "sem_mercado" : "sem_liquidez";
    else if (!e.proposta) motivo = "indisponivel";
    else motivo = MOTIVOS_MOTOR.indexOf(e.proposta.motivo) > -1 ? e.proposta.motivo : "desconhecido";
    semProposta.push({ p, motivo });
  }
  return { abertas, novas, semProposta };
}

export function fraseDoMotivo(mapa, motivo) {
  return (mapa && (mapa[motivo] || mapa.desconhecido)) || "";
}
