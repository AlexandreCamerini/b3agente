/**
 * useOpcoesMcp.js — aba-opcoes F2 (ADR-027, quick 260910-biz, 2026-09-10).
 *
 * Estado das chamadas ao serviço MCP para a aba Opções. Três trios
 * `dados / carregando / erro`, um por chamada.
 *
 * O `store` chega por ARGUMENTO, nunca por import de `persistence.js`: é o
 * que mantém o hook testável e o que evita acoplar a tela ao módulo de
 * estado (que decide sozinho, em runtime, entre `deviceStore` e
 * `serverStore`).
 *
 * `erro` guarda o OBJETO de erro inteiro, não a string: a tela precisa do
 * `erro.code` (`mcp_nao_configurado`/`mcp_cota`/…) para escolher o estado, e
 * raspar a mensagem seria o jeito que quebra na primeira mudança de copy.
 */
import { useCallback, useEffect, useRef, useState } from "react";

const VAZIO = { dados: null, carregando: false, erro: null };

export function useOpcoesMcp(store, ticker) {
  // `carregando` nasce VERDADEIRO: o estado "carregando" tem de vir ANTES do
  // estado "vazio", nunca depois — vazio pintado durante a consulta é uma
  // afirmação ("não há nada") que ninguém mediu ainda.
  const [status, setStatus] = useState({ dados: null, carregando: true, erro: null });
  const [leitura, setLeitura] = useState({ dados: null, carregando: true, erro: null });
  const [grafico, setGrafico] = useState({ dados: null, carregando: false, erro: null, setup: null });

  // Dois contadores de requisição, não um: `tickerRef` invalida TUDO que
  // estiver em voo quando o ticker muda (sem ele, trocar de ativo rápido
  // pinta a tela com o dado do ativo anterior — e o cabeçalho diria o ticker
  // novo sobre números do antigo). `graficoRef` invalida só o gráfico, para
  // abrir um segundo setup não descartar a leitura ainda em voo.
  const tickerRef = useRef(0);
  const graficoRef = useRef(0);

  useEffect(() => {
    if (!store || typeof store.mcpStatus !== "function") { setStatus(VAZIO); return undefined; }
    let vivo = true;
    setStatus((s) => ({ ...s, carregando: true }));
    store.mcpStatus()
      .then((d) => { if (vivo) setStatus({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (vivo) setStatus({ dados: null, carregando: false, erro: e }); });
    return () => { vivo = false; };
  }, [store]);

  useEffect(() => {
    const t = (ticker || "").trim();
    const meu = ++tickerRef.current;
    graficoRef.current += 1;               // gráfico do ticker anterior morre junto
    setGrafico({ dados: null, carregando: false, erro: null, setup: null });

    if (!t || !store || typeof store.mcpLeitura !== "function") {
      setLeitura(VAZIO);
      return undefined;
    }
    setLeitura({ dados: null, carregando: true, erro: null });
    store.mcpLeitura(t)
      .then((d) => { if (tickerRef.current === meu) setLeitura({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (tickerRef.current === meu) setLeitura({ dados: null, carregando: false, erro: e }); });
    return undefined;
  }, [store, ticker]);

  // Sob demanda: o usuário abre o gráfico de UM setup. Não dispara por
  // efeito — cada abertura custa uma chamada do cap.
  const abrirGrafico = useCallback((nome) => {
    if (!nome || !store || typeof store.mcpSetupGrafico !== "function") return;
    const meuTicker = tickerRef.current;
    const meu = ++graficoRef.current;
    setGrafico({ dados: null, carregando: true, erro: null, setup: nome });
    store.mcpSetupGrafico(nome)
      .then((d) => {
        if (graficoRef.current === meu && tickerRef.current === meuTicker) {
          setGrafico({ dados: d, carregando: false, erro: null, setup: nome });
        }
      })
      .catch((e) => {
        if (graficoRef.current === meu && tickerRef.current === meuTicker) {
          setGrafico({ dados: null, carregando: false, erro: e, setup: nome });
        }
      });
  }, [store]);

  const fecharGrafico = useCallback(() => {
    graficoRef.current += 1;
    setGrafico({ dados: null, carregando: false, erro: null, setup: null });
  }, []);

  return { status, leitura, grafico, abrirGrafico, fecharGrafico };
}

export default useOpcoesMcp;
