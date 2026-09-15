/**
 * executarCandidato.js — despacho puro por tipo (call_coberta/put_protecao/
 * collar/opcao_a_descoberto) para o método de store correto, com o corpo
 * EXATO que cada rota real exige (server/app/main.py:3566/3649/3017).
 *
 * Quick 260915-j5l: o clique num card do bloco "AS 4 MELHORES OPORTUNIDADES
 * DE OPÇÕES" (Fase 31) não tinha caminho de execução — jogava fora
 * idCandidato/contractSymbol/pernasContratos/contratos/qtyAcoes/expiration/
 * tipo e abria o acordeão genérico de UMA posição. Este módulo é o
 * tradutor candidato → chamada de store, nada mais.
 *
 * Regras não negociáveis deste módulo:
 * - ZERO aritmética financeira: `contratos`/`qtyAcoes` viajam como o backend
 *   os mandou. Nada de `* 100`, nada de recalcular prêmio (princípio 5 do
 *   CLAUDE.md — cálculo determinístico é do backend, nunca do front/IA).
 * - ZERO composição de mensagem de erro do servidor: este módulo não
 *   captura exceção nenhuma — a rejeição de `store[metodo](body)` sobe
 *   intacta para quem chamou.
 * - ZERO método novo de store: despacha só para os três que já existem nos
 *   DOIS stores (serverStore e deviceStore) — preserva a paridade
 *   `deviceStore`↔`serverStore` sem tocar em persistence.js.
 * - `aceitaLiquidezDificil` só entra no corpo por IDENTIDADE (`=== true`),
 *   nunca por truthiness — um valor truthy acidental (string, objeto) não
 *   pode virar consentimento de liquidez DIFÍCIL.
 */

const TIPOS_LASTREADA = new Set(["call_coberta", "put_protecao"]);

function exigirCampos(cand, campos, rotulo) {
  for (const campo of campos) {
    if (cand[campo] === undefined || cand[campo] === null || cand[campo] === "") {
      throw new Error(`Candidato de ${rotulo} sem campo obrigatório: ${campo}`);
    }
  }
}

/**
 * corpoDoCandidato(cand, { aceitaLiquidezDificil }) — PURA, zero I/O.
 * Devolve { metodo, body }: `metodo` é o NOME do método de store
 * ("optionsAbrirLastreada" | "optionsAbrirCollar" | "optionsBuy") e `body`
 * é o corpo exato da rota correspondente. Tipo desconhecido ou candidato
 * sem os campos obrigatórios do seu tipo lança Error nomeado — nunca
 * devolve corpo meia-boca (um corpo inválido viraria 400 do servidor com
 * mensagem que o usuário não entende).
 */
export function corpoDoCandidato(cand, opts = {}) {
  if (!cand || typeof cand !== "object") {
    throw new Error("Candidato ausente — nada para executar.");
  }
  const aceitaLiquidezDificil = opts.aceitaLiquidezDificil === true;
  const tipo = cand.tipo;

  if (TIPOS_LASTREADA.has(tipo)) {
    // call_coberta e put_protecao usam a MESMA rota — o servidor resolve
    // call→abrir_call_coberta, put→comprar_put_protecao pelo optionType do
    // contrato que ELE buscou (não é decisão do front).
    exigirCampos(cand, ["ticker", "contractSymbol", "expiration", "contratos"], tipo);
    const body = {
      underlying: cand.ticker,
      contractSymbol: cand.contractSymbol,
      expiration: cand.expiration,
      contratos: cand.contratos,
    };
    if (aceitaLiquidezDificil) body.aceitaLiquidezDificil = true;
    return { metodo: "optionsAbrirLastreada", body };
  }

  if (tipo === "collar") {
    exigirCampos(cand, ["ticker", "contratos", "expiration"], "collar");
    const pernas = Array.isArray(cand.pernasContratos) ? cand.pernasContratos : [];
    if (pernas.length !== 2) {
      throw new Error("Candidato de collar precisa de exatamente 2 pernas.");
    }
    // SÓ contractSymbol e lado por perna — a rota re-deriva prêmio/strike
    // no servidor (ADR-026 Decisão 2); mandar strike/prêmio a mais seria o
    // cliente tentando ditar a estrutura.
    const pernasContratos = pernas.map((p) => {
      if (!p || !p.contractSymbol || !p.lado) {
        throw new Error("Perna do collar sem contractSymbol/lado.");
      }
      return { contractSymbol: p.contractSymbol, lado: p.lado };
    });
    const body = {
      underlying: cand.ticker,
      pernasContratos,
      contratos: cand.contratos,
      expiration: cand.expiration,
    };
    if (aceitaLiquidezDificil) body.aceitaLiquidezDificil = true;
    return { metodo: "optionsAbrirCollar", body };
  }

  if (tipo === "opcao_a_descoberto") {
    exigirCampos(cand, ["ticker", "contractSymbol", "expiration", "qtyAcoes"], tipo);
    // SEM aceitaLiquidezDificil: /api/options/buy não tem gate de liquidez
    // (verificado no plano) — mandar a chave seria corpo que a rota nem lê.
    const body = {
      underlying: cand.ticker,
      contractSymbol: cand.contractSymbol,
      expiration: cand.expiration,
      qty: cand.qtyAcoes,
    };
    return { metodo: "optionsBuy", body };
  }

  throw new Error(`Tipo de candidato desconhecido: ${String(tipo)}`);
}

/**
 * executarCandidato(cand, { store, aceitaLiquidezDificil }) — resolve o par
 * por corpoDoCandidato e faz `store[metodo](body)`. `store` é INJETADO
 * (torna os casos testáveis sem DOM e sem rede); o valor devolvido é o
 * estado público da carteira que a rota retorna.
 */
export function executarCandidato(cand, { store, aceitaLiquidezDificil } = {}) {
  const { metodo, body } = corpoDoCandidato(cand, { aceitaLiquidezDificil });
  return store[metodo](body);
}
