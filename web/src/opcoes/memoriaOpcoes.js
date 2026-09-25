// Fase 40 (ESTADO-01) — módulo puro de memória em sessão do ticker + aba
// ativa da tela Opções. Sem React, sem I/O, sem store: só as três regras de
// precedência/validação que a fiação (App.jsx/OpcoesScreen.jsx) consome.
// A ausência de import de React/store aqui é o próprio contrato de D-01
// (a memória nunca passa por deviceStore/serverStore/localStorage).

// D-03: o deep-link `abaInicial` (one-shot, `ctx.opcoesAbaInicial`) SEMPRE
// vence a memória, incondicionalmente — mesmo com memória válida de uma
// visita anterior na mesma sessão. T-39-14: valor fora de `abas` nunca é
// aceito, nem do deep-link nem da memória; cai para "oportunidades".
export function abaInicialOpcoes(abas, abaInicial, memoria) {
  if (!Array.isArray(abas)) return "oportunidades";
  if (abas.includes(abaInicial)) return abaInicial;
  if (memoria && abas.includes(memoria.aba)) return memoria.aba;
  return "oportunidades";
}

// P-2: o ticker lembrado só é aceito se ainda estiver na carteira atual —
// nunca lê carteira[0] (não é auto-seleção, é restauração de escolha
// explícita do próprio usuário). Cenário E/E2: vendeu tudo ou carteira
// zerada → cai para "" (mesmo default de sempre, `OpcoesScreen.jsx:311`).
export function tickerInicialOpcoes(memoria, carteira) {
  if (!memoria || typeof memoria.ticker !== "string" || memoria.ticker === "") return "";
  if (!Array.isArray(carteira)) return "";
  return carteira.some((p) => p && p.t === memoria.ticker) ? memoria.ticker : "";
}

// Escrita da memória (write-back, chamada a cada mudança de ticker/aba pelo
// OpcoesScreen). Normaliza o estado default (ticker vazio + "oportunidades")
// para `null` — é o valor que faz o cenário C2 (troca de escopo com a tela
// montada) "terminar null" literalmente, como o UI-SPEC exige.
export function memoriaOpcoes(ticker, aba) {
  if (ticker === "" && aba === "oportunidades") return null;
  return { ticker, aba };
}
