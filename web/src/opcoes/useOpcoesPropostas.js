/**
 * useOpcoesPropostas.js — Fase 32 (32-03), extração de App.jsx.
 *
 * Fase 18 (Plano 01, NAV-01/NAV-02): uma busca de gate+proposta por ticker
 * serve as DUAS superfícies desta fase — a tira agregada ("Oportunidades de
 * opções", NAV-01) e o detalhe dentro do card de posição em CarteiraScreen
 * (NAV-02). Não existe rota bulk por decisão explícita do 18-CONTEXT.md: o
 * fan-out por ticker é o MESMO precedente de custo já aceito no ADR-004
 * ("1 chamada leve por card, best-effort"), estendido de 1 card pra N —
 * carteiras deste produto são de poucas posições (simulador educacional).
 *
 * ADR-027 Emenda 3: `OpcoesScreen.jsx` não pode importar `App.jsx` e
 * `App.jsx` não pode importar `OpcoesScreen.jsx` (seria ciclo) — este módulo
 * terceiro é a fiação correta, mesmo padrão de `OportunidadesOpcoes.jsx`/
 * `CuradoriaEstruturas.jsx` (32-02). `store` chega por ARGUMENTO, nunca por
 * import de `persistence.js` — mesmo padrão de `useOpcoesMcp(store, ticker)`.
 *
 * Fase 32 (32-03): o consumidor deste hook deixou de ser só `CarteiraScreen`
 * e passou a ser também a aba Opções — o fan-out agora dispara quando a aba
 * Opções abre, além de quando Posições abre, e não mais SÓ a cada entrada em
 * Posições (redução líquida de tráfego por sessão, não aumento: cada tela
 * chama o hook uma vez, sobre o mesmo universo de tickers).
 */
import { useState, useEffect } from "react";

export function useOpcoesPropostas(store, tickers) {
  const [propostas, setPropostas] = useState({});
  const [carregando, setCarregando] = useState(false);
  // Chave PRIMITIVA (string) como dependência do efeito — um array de
  // tickers recriaria o efeito a cada render do chamador, disparando N
  // requisições por render (mesma disciplina do `opGate && opGate.liquida`
  // primitivo em AtivoCard).
  const chave = (tickers || []).join(",");

  useEffect(() => {
    let alive = true;
    // Guarda nova (32-03): sem `store` (ex.: chamador ainda não recebeu o
    // ctx), o efeito não busca nada — nunca lança contra um store ausente.
    if (!store) {
      setCarregando(false);
      return () => { alive = false; };
    }
    const lista = chave ? chave.split(",") : [];
    setPropostas({});
    if (lista.length === 0) {
      setCarregando(false);
      return () => { alive = false; };
    }
    setCarregando(true);
    let pendentes = lista.length;
    // Decrementado em TODOS os caminhos (sucesso, gate reprovado e erro) —
    // nunca só no caminho feliz, senão a tira fica presa no texto de
    // carregamento quando o backend falha.
    const marcarPendenteResolvido = () => {
      pendentes -= 1;
      if (alive && pendentes <= 0) setCarregando(false);
    };
    lista.forEach((t) => {
      store.optionsGate(t)
        .then((gate) => {
          if (!alive) return;
          if (gate && gate.liquida) {
            store.optionsProposta(t, true)
              .then((proposta) => { if (alive) setPropostas((m) => ({ ...m, [t]: { gate, proposta } })); })
              .catch(() => { if (alive) setPropostas((m) => ({ ...m, [t]: { gate, proposta: null } })); })
              .finally(marcarPendenteResolvido);
          } else {
            setPropostas((m) => ({ ...m, [t]: { gate, proposta: null } }));
            marcarPendenteResolvido();
          }
        })
        .catch(() => { marcarPendenteResolvido(); /* best-effort: sem gate/proposta o ticker só não aparece na tira */ });
    });
    return () => { alive = false; };
  }, [store, chave]);

  return { propostas, carregando };
}
