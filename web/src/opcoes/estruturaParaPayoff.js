/**
 * estruturaParaPayoff.js — adaptador puro do envelope PT do motor interno
 * (`opcoes_motor.avaliar()` / `opcoes_payoff.perfil_da_estrutura()`) para o
 * envelope INGLÊS que `PayoffChart.jsx` já consome (herdado do caminho
 * MCP/`evaluate_option_structure`).
 *
 * Fase 31 (Plano 04, D-08): o bloco de curadoria em Posições passa a
 * mostrar a curva de payoff da estrutura nº 1, mas o motor interno fala PT
 * (`curva`/`resultado`/`ganho_maximo`/`perda_maxima`/...) e `PayoffChart`
 * só lê INGLÊS (`payoff`/`result`/`max_gain`/`max_loss`/...), porque
 * nasceu para o caminho MCP (Fase 24). Este arquivo faz SÓ renomeação de
 * chave — zero aritmética.
 *
 * Fazer qualquer conta aqui (multiplicar, somar, arredondar) criaria uma
 * segunda versão de um número que o backend já calculou (princípio 5 do
 * CLAUDE.md, "cálculos determinísticos, nunca pela IA/pelo front"). O
 * guardião de `web/tests/test_estrutura_para_payoff.mjs` proíbe, por regex
 * sobre o próprio fonte deste arquivo, qualquer operador aritmético
 * aplicado aos campos financeiros — manutenção futura que precise de uma
 * conta nova pertence ao backend, não a este adaptador.
 */
export function estruturaParaPayoff(estrutura, nome) {
  if (!estrutura || typeof estrutura !== "object") return null;
  const curva = estrutura.curva;
  if (!Array.isArray(curva) || curva.length < 2) return null;

  return {
    name: nome,
    legs: Array.isArray(estrutura.pernas) ? estrutura.pernas : [],
    payoff: curva.map((ponto) => ({
      underlying: ponto.preco_objeto,
      result: ponto.resultado,
    })),
    breakevens: Array.isArray(estrutura.breakevens) ? estrutura.breakevens : [],
    net_cost: estrutura.custo_liquido,
    max_gain: estrutura.ganho_maximo,
    max_loss: estrutura.perda_maxima,
    unlimited_gain: estrutura.ganho_ilimitado,
    unlimited_loss: estrutura.perda_ilimitada,
  };
}
