/**
 * useTecnicoCarteira.js — Fase 48 (48-08): fan-out de `store.opcoesTecnico`
 * (leitura técnica interna, custoMcp 0) por ticker da carteira, para a régua
 * e os chips dos cards do hub. Nenhum número é calculado aqui.
 *
 * Um pedido por ticker por montagem; chave primitiva (`tickers.join(",")`)
 * para o efeito não reexecutar por identidade de array. Erro por ticker não
 * derruba os outros.
 */
import { useEffect, useState } from "react";

export default function useTecnicoCarteira(store, tickers) {
  const [porTicker, setPorTicker] = useState({});
  const chave = Array.isArray(tickers) ? tickers.join(",") : "";

  useEffect(() => {
    const ler = store && store.opcoesTecnico;
    const lista = chave ? chave.split(",") : [];
    setPorTicker({});
    if (typeof ler !== "function" || lista.length === 0) return undefined;
    let vivo = true;
    lista.forEach((t) => {
      Promise.resolve()
        .then(() => ler.call(store, t))
        .then((d) => { if (vivo) setPorTicker((m) => ({ ...m, [t]: { dados: d, erro: null } })); })
        .catch((e) => { if (vivo) setPorTicker((m) => ({ ...m, [t]: { dados: null, erro: e } })); });
    });
    return () => { vivo = false; };
  }, [store, chave]);

  return porTicker;
}
