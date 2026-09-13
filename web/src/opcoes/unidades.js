/**
 * unidades.js — aba Opções, Fase 27 (plano 27-04, 2026-09-13).
 *
 * **Por que este módulo existe.** Na MESMA tela da aba Opções convivem duas
 * volatilidades de fontes diferentes e em UNIDADES diferentes:
 *
 *  · `volatilidade.hv21Pct` — motor interno do Boris+ (27-03), em
 *    **PERCENTUAL** (31.4 significa 31,4%), com `unidade: "pct"` declarado no
 *    próprio contrato da rota;
 *  · `behavior.hv21` — serviço MCP de opções, em **FRAÇÃO** (0.314 significa
 *    31,4%), sem campo de unidade nenhum. `OpcoesScreen.jsx` já o converte
 *    com `fracPct`, e continua convertendo.
 *
 * Passar um pelo formatador do outro erra por 10× — em silêncio, com o mesmo
 * rótulo na tela ("HV 21") e sem nenhum teste vermelho. O 27-03 já declarava
 * `unidade` no contrato, mas ninguém a consumia, e **campo que ninguém
 * consome não impede erro nenhum**. Aqui ela deixa de ser anotação e vira
 * DESPACHANTE: é a unidade recebida que ESCOLHE o formatador.
 *
 * Três regras, e a terceira é o ponto:
 *  1. `"pct"` formata o número como está;
 *  2. `"frac"` multiplica por 100 antes de formatar;
 *  3. **qualquer outra coisa** (`undefined`, `null`, `"percent"`, string
 *     vazia) devolve travessão COM motivo — nunca um palpite. Adivinhar a
 *     unidade é exatamente o erro de 10× que este módulo existe para tornar
 *     impossível, e "não sei em que unidade isto está" é informação legítima
 *     (princípio 4 do CLAUDE.md: não invente valores; mostre o estado
 *     correto).
 *
 * **É `.js` e não `.jsx`, e isso é deliberado**: assim o guardião
 * (`web/tests/test_opcoes_leitura_interna_ui.mjs`) consegue IMPORTAR e
 * exercitar a função de verdade, em vez de fazer um `grep` no fonte. A
 * diferença é entre um teste permanente e uma conferência de uma vez só.
 *
 * Módulo PURO: zero JSX, zero import (nem de `App.jsx`, nem de `copy.js`),
 * zero conta de indicador — a regex `RECALCULO` de
 * `test_opcoes_analisar_ui.mjs` varre TODO arquivo de `web/src/opcoes/`, e o
 * que existe aqui é conversão de ESCALA da mesma grandeza, não cálculo novo.
 */

// As duas unidades que o app sabe formatar. Nome de constante em vez de
// string solta para que um `"percent"` digitado no backend caia no ramo 3
// (travessão com motivo) em vez de passar por engano.
export const UNIDADES = { pct: "pct", frac: "frac" };

// Ausência de VALOR: travessão seco. O porquê da ausência já vem do backend
// no `motivo` do próprio bloco (`volatilidade.motivo`), e repeti-lo aqui
// criaria duas explicações para o mesmo fato.
export const SEM_VALOR = "—";

// Ausência de UNIDADE com valor presente: o número chegou, mas não dá para
// exibi-lo sem saber a escala. Sem dígito nenhum de propósito — meio número
// é pior que número nenhum, porque a pessoa decide sobre ele.
export const SEM_UNIDADE = "— unidade não declarada";

const ehNum = (v) => typeof v === "number" && isFinite(v);

/**
 * Formata uma volatilidade como percentual, ESCOLHENDO o formatador pela
 * unidade declarada no contrato de quem mandou o número.
 *
 * @param {number|null|undefined} valor
 * @param {string|null|undefined} unidade  `"pct"` ou `"frac"` — qualquer
 *   outra coisa devolve travessão com motivo, nunca um palpite.
 * @param {number} casas  casas decimais (1 por padrão, como o `fracPct` da
 *   tela, para que os dois blocos da mesma tela não difiram na precisão).
 * @returns {string}
 */
export function formatarVolatilidade(valor, unidade, casas = 1) {
  // Valor primeiro: sem número, a unidade não muda nada e o travessão seco é
  // a resposta certa (o motivo do bloco explica a ausência logo abaixo).
  if (!ehNum(valor)) return SEM_VALOR;
  if (unidade === UNIDADES.pct) return emTexto(valor, casas);
  if (unidade === UNIDADES.frac) return emTexto(valor * 100, casas);
  return SEM_UNIDADE;
}

// Vírgula decimal, como o resto da tela (`fmt` em `OpcoesScreen.jsx`).
function emTexto(v, casas) {
  return v.toFixed(casas).replace(".", ",") + "%";
}

export default formatarVolatilidade;
