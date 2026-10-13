// quick 261013-cqk (2026-10-13) — prioridade de atenção e ordenação da lista de
// posições (opção B). Módulo PURO: só decide ordem e chip a partir de enums que
// o backend já calculou (estado principal, estrutura.estado). Nenhum número
// financeiro é calculado aqui; comparadores usam só < e >.
import { estadoPrincipalV6 } from "./estruturaCard.js";

// Menor nível = mais atenção.
export const NIVEIS_ATENCAO = Object.freeze({
  RISCO: 0, // vencida / exercício provável / abaixo do stop / acima do alvo
  PERTO_STOP: 1,
  VENCE_5_DIAS: 2,
  SEM_PLANO: 3, // sem plano / falta stop / falta alvo
  PERTO_ALVO: 4,
  LEITURA_INDISPONIVEL: 5,
  DEMAIS: 6,
});

export const CRITERIOS_ORDEM = Object.freeze(["atencao", "resultado", "vencimento"]);

const N = NIVEIS_ATENCAO;
const CHAVES_RISCO = ["motor", "estado_abaixo_stop", "estado_acima_alvo"];
const CHAVES_SEM_PLANO = ["estado_sem_plano", "estado_falta_stop", "estado_falta_alvo"];
const SITUACOES_INDISPONIVEIS = ["carregando", "falha", "desatualizada"];

// -> { nivel, chip }; chip: { tipo: "estado", chave, vals, tom, glifo } | { tipo: "vencimento" } | null.
// `p` pode ser nulo (perna avulsa): então só estrutura/leitura decidem.
export function prioridadeAtencao({ p, estrutura, leituraPlano, situacaoPlano } = {}) {
  const principal = estadoPrincipalV6({ p, estrutura, leituraPlano }).principal;
  const chave = principal ? principal.chave : null;
  const estado = principal ? { tipo: "estado", ...principal } : null;
  if (chave && CHAVES_RISCO.includes(chave)) return { nivel: N.RISCO, chip: estado };
  if (chave === "estado_perto_stop") return { nivel: N.PERTO_STOP, chip: estado };
  if (estrutura && estrutura.estado === "ate_5_dias") return { nivel: N.VENCE_5_DIAS, chip: { tipo: "vencimento" } };
  if (chave && CHAVES_SEM_PLANO.includes(chave)) return { nivel: N.SEM_PLANO, chip: estado };
  if (chave === "estado_perto_alvo") return { nivel: N.PERTO_ALVO, chip: estado };
  if (SITUACOES_INDISPONIVEIS.includes(situacaoPlano) || chave === "extra_cotacao_indisponivel") {
    return { nivel: N.LEITURA_INDISPONIVEL, chip: estado };
  }
  return { nivel: N.DEMAIS, chip: estado };
}

const porTicker = (a, b) => (a.t < b.t ? -1 : a.t > b.t ? 1 : 0);
const temNum = (v) => typeof v === "number" && Number.isFinite(v);

// Compara dois valores com null no fim; empate por ticker. Só < e >.
function cmpNullFim(va, vb, a, b) {
  const na = temNum(va), nb = temNum(vb);
  if (na && nb) return va < vb ? -1 : va > vb ? 1 : porTicker(a, b);
  if (na) return -1;
  if (nb) return 1;
  return porTicker(a, b);
}

// linhas: [{ t, nivel, resultado, dias }] -> NOVO array (não muta a entrada).
// "resultado": PIOR no topo (menor valor primeiro), suspenso (null) no fim.
// "vencimento": dias corridos crescentes (vencida, negativa, primeiro), sem opção no fim.
export function ordenarLinhas(linhas, criterio) {
  const lista = Array.isArray(linhas) ? linhas.slice() : [];
  if (criterio === "resultado") return lista.sort((a, b) => cmpNullFim(a.resultado, b.resultado, a, b));
  if (criterio === "vencimento") return lista.sort((a, b) => cmpNullFim(a.dias, b.dias, a, b));
  return lista.sort((a, b) => (a.nivel < b.nivel ? -1 : a.nivel > b.nivel ? 1 : porTicker(a, b)));
}
