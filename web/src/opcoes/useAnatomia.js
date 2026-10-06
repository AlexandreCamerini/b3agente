// Fase 49 (2026-10-06), ANAT-03 — leitura da anatomia da perna.
// Rota grátis GET /api/options/anatomia/{ticker}: custo MCP 0. Nenhum número é
// calculado aqui (o front nunca soma nem subtrai valores); o store chega por
// argumento, nunca por import. Erro guarda o objeto inteiro (mensagem verbatim).
import { useCallback, useEffect, useRef, useState } from "react";

export function chaveAnatomia(ticker, excluir, ids, modo) {
  const ex = [...(excluir || [])].sort().join(",");
  const id = [...(ids || [])].sort().join(",");
  return ticker + "|" + (modo || "") + "|" + ex + "|" + id;
}

export function buscarAnatomia(store, ticker, excluir) {
  if (!ticker || !store || typeof store.opcoesAnatomia !== "function") return Promise.resolve(null);
  return store.opcoesAnatomia(ticker, excluir && excluir.length ? { excluir: excluir.join(",") } : {});
}

export function useAnatomia(store, ticker, excluir, ids, modo) {
  const [estado, setEstado] = useState({ dados: null, carregando: false, erro: null });
  const [recarga, setRecarga] = useState(0);
  const meuRef = useRef(0);
  const tickerAnterior = useRef(ticker);
  const excluirRef = useRef(excluir);
  excluirRef.current = excluir;
  const chave = chaveAnatomia(ticker, excluir, ids, modo);

  useEffect(() => {
    const meu = ++meuRef.current;
    if (!store || !ticker) {
      setEstado({ dados: null, carregando: false, erro: null });
      tickerAnterior.current = ticker;
      return;
    }
    const mudouTicker = tickerAnterior.current !== ticker;
    tickerAnterior.current = ticker;
    setEstado((e) => ({ dados: mudouTicker ? null : e.dados, carregando: true, erro: null }));
    Promise.resolve()
      .then(() => buscarAnatomia(store, ticker, excluirRef.current))
      .then((d) => { if (meuRef.current === meu) setEstado({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (meuRef.current === meu) setEstado((a) => ({ dados: a.dados, carregando: false, erro: e })); });
  }, [store, chave, recarga]); // eslint-disable-line react-hooks/exhaustive-deps

  const recarregar = useCallback(() => setRecarga((n) => n + 1), []);
  if (!store || !ticker) return { dados: null, carregando: false, erro: null, recarregar };
  return { ...estado, recarregar };
}
