// Fase 48 (2026-10-05) — hook de dados do caminho B (escada por objetivo).
// UI-SPEC "Mapa de telas e fluxo" + ADR-027 (custo só em clique, declarado
// pelo backend). Três blocos { dados, carregando, erro }:
//   escada        — GET /api/options/escada/{ticker}: custo MCP 0, sai de efeito;
//   leituraCelula — POST /api/options/escada/leitura: custo 0, sai de clique;
//   matriz        — POST /api/options/mcp/escada-matriz: ÚNICA chamada paga
//                   (2N+1, rótulo vem de escada.dados.comparar), SÓ por clique.
// Nenhum número é calculado ou inventado aqui; erro guarda `e` inteiro
// (mensagem verbatim, princípio 4 do produto).
import { useCallback, useEffect, useRef, useState } from "react";

const VAZIO = { dados: null, carregando: false, erro: null };

// Padrão do useOpcoesMcp: contador próprio + conferência do ticker descartam
// resposta velha (disparo repetido; resposta de PETR4 sob a tela de VALE3).
function useBloco(tickerRef) {
  const [estado, setEstado] = useState(VAZIO);
  const meuRef = useRef(0);
  const disparar = useCallback((executar) => {
    const meuTicker = tickerRef.current;
    const meu = ++meuRef.current;
    setEstado({ dados: null, carregando: true, erro: null });
    Promise.resolve().then(executar)
      .then((d) => {
        if (meuRef.current === meu && tickerRef.current === meuTicker) {
          setEstado({ dados: d, carregando: false, erro: null });
        }
      })
      .catch((e) => {
        if (meuRef.current === meu && tickerRef.current === meuTicker) {
          setEstado({ dados: null, carregando: false, erro: e });
        }
      });
  }, [tickerRef]);
  const limpar = useCallback(() => { meuRef.current += 1; setEstado(VAZIO); }, []);
  return [estado, disparar, limpar];
}

export function useEscada(store, { ticker, objetivo, vencimento, ativo } = {}) {
  const tickerRef = useRef(ticker);
  tickerRef.current = ticker;
  const [escada, dispararEscada, limparEscada] = useBloco(tickerRef);
  const [matriz, dispararMatriz, limparMatriz] = useBloco(tickerRef);
  const [leituraCelula, dispararLeitura, limparLeitura] = useBloco(tickerRef);
  const [recarga, setRecarga] = useState(0);

  // Custo MCP 0 (rota /api/options/escada/{ticker}). Dependências PRIMITIVAS.
  useEffect(() => {
    if (!ativo || !ticker) { limparEscada(); return; }
    const q = {};
    if (objetivo) q.objetivo = objetivo;
    if (vencimento) q.vencimento = vencimento;
    dispararEscada(() => store.opcoesEscada(ticker, q));
  }, [store, ativo, ticker, objetivo, vencimento, recarga, dispararEscada, limparEscada]);

  // Matriz e leitura de célula descrevem o ativo anterior: limpa ao trocar.
  useEffect(() => { limparMatriz(); limparLeitura(); }, [ticker, limparMatriz, limparLeitura]);

  const recarregarEscada = useCallback(() => setRecarga((n) => n + 1), []);

  // ÚNICA chamada paga: só por clique, nunca por efeito.
  const verMatriz = useCallback(({ expirations } = {}) => {
    dispararMatriz(() => store.mcpEscadaMatriz({ ticker, expirations }));
  }, [store, ticker, dispararMatriz]);

  // Fase 48 (48-10): repassa `indice` (posição da célula na linha, escolhe o
  // degrau certo no backend), `precoObjeto` da matriz e `vencimentosExecutaveis`
  // — a rota os aceita e, sem eles, caía em indice 0 (rótulo de degrau errado).
  const lerCelula = useCallback((celula, { objetivo: obj, vencimento: venc, indice, precoObjeto, vencimentosExecutaveis } = {}) => {
    dispararLeitura(() => store.opcoesEscadaLeitura({
      ticker, objetivo: obj, vencimento: venc, pernas: celula && celula.pernas,
      indice, precoObjeto, vencimentosExecutaveis,
    }));
  }, [store, ticker, dispararLeitura]);

  return { escada, recarregarEscada, matriz, verMatriz, limparMatriz, leituraCelula, lerCelula };
}
