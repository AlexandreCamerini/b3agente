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

// aba-opcoes F3 (plano 24-02): cadeia, operáveis, proposta e possibilidades
// são QUATRO chamadas com a mesma disciplina — e quatro cópias do mesmo bloco
// divergem na primeira manutenção feita só numa delas.
//
// O contador próprio (`meuRef`) resolve o disparo repetido: apertar "montar"
// duas vezes e a PRIMEIRA resposta chegar por último pintaria a tela com o
// pedido velho. A conferência de `tickerRef` resolve o outro eixo: resposta de
// PETR4 não pinta a tela de VALE3. São os dois refs que o hook já usava para
// leitura e gráfico, agora aplicados por chamada.
function useChamadaSobDemanda(tickerRef) {
  const [estado, setEstado] = useState(VAZIO);
  const meuRef = useRef(0);

  // `executar` é uma função, não uma Promise já iniciada: quem chama decide o
  // corpo do pedido no clique, e `Promise.resolve().then(...)` transforma um
  // erro SÍNCRONO (store ausente, corpo inválido) na mesma rejeição tratada —
  // sem isso, uma exceção síncrona escaparia do trio e deixaria a seção
  // travada em "carregando" para sempre.
  const disparar = useCallback((executar) => {
    if (typeof executar !== "function") return;
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

  // Invalida o que estiver em voo E zera o trio: é o que a troca de ticker
  // precisa — cadeia de PETR4 sob o cabeçalho de VALE3 é afirmação falsa.
  const limpar = useCallback(() => { meuRef.current += 1; setEstado(VAZIO); }, []);

  return [estado, disparar, limpar];
}

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

  // F3: os quatro trios sob demanda. Ordem fixa de chamada (regra dos hooks).
  const [cadeia, dispararCadeia, limparCadeia] = useChamadaSobDemanda(tickerRef);
  const [operaveis, dispararOperaveis, limparOperaveis] = useChamadaSobDemanda(tickerRef);
  const [proposta, dispararProposta, limparProposta] = useChamadaSobDemanda(tickerRef);
  const [possibilidades, dispararPossibilidades, limparPossibilidades] = useChamadaSobDemanda(tickerRef);

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
    // Os quatro trios da F3 morrem junto pela MESMA razão: são afirmações
    // sobre o ativo anterior. Este efeito continua não disparando chamada
    // nenhuma — ele só apaga.
    limparCadeia();
    limparOperaveis();
    limparProposta();
    limparPossibilidades();

    if (!t || !store || typeof store.mcpLeitura !== "function") {
      setLeitura(VAZIO);
      return undefined;
    }
    setLeitura({ dados: null, carregando: true, erro: null });
    store.mcpLeitura(t)
      .then((d) => { if (tickerRef.current === meu) setLeitura({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (tickerRef.current === meu) setLeitura({ dados: null, carregando: false, erro: e }); });
    return undefined;
  }, [store, ticker, limparCadeia, limparOperaveis, limparProposta, limparPossibilidades]);

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

  // ---------------------------------------------------------------- F3 --
  // As quatro ações. TODAS por clique, NENHUMA por efeito: cada uma consome
  // o cap compartilhado, e `/possibilidades` consome até 13 chamadas de uma
  // vez. Chamada que dispara sozinha ao abrir a tela gastaria a cota da
  // pessoa sem ela ter pedido nada.
  //
  // O ticker vem do argumento do hook, não do corpo: a tela nunca escolhe um
  // ativo diferente do que está no cabeçalho.
  const alvoAtual = (ticker || "").trim();

  const abrirCadeia = useCallback((op) => {
    if (!alvoAtual || !store || typeof store.mcpCadeia !== "function") return;
    const o = op || {};
    dispararCadeia(() => store.mcpCadeia(alvoAtual, { expiration: o.expiration, kind: o.kind }));
  }, [store, alvoAtual, dispararCadeia]);

  const abrirOperaveis = useCallback((op) => {
    if (!alvoAtual || !store || typeof store.mcpOperaveis !== "function") return;
    const o = op || {};
    dispararOperaveis(() => store.mcpOperaveis(alvoAtual, { expiration: o.expiration, kind: o.kind }));
  }, [store, alvoAtual, dispararOperaveis]);

  // `undefined` em `direction`/`kind`/`expiration` SOME do JSON (é o que
  // `JSON.stringify` faz), e é isso que se quer: o backend distingue "não
  // pedi" de "pedi vazio" — sem tese ele devolve 422 `tese_ausente`, e a
  // tela só habilita o botão com tese escolhida.
  const montarProposta = useCallback((op) => {
    if (!alvoAtual || !store || typeof store.mcpProposta !== "function") return;
    const o = op || {};
    dispararProposta(() => store.mcpProposta({
      ticker: alvoAtual,
      direction: o.direction,
      kind: o.kind,
      expiration: o.expiration,
      lote: o.lote,
    }));
  }, [store, alvoAtual, dispararProposta]);

  const verPossibilidades = useCallback((op) => {
    if (!alvoAtual || !store || typeof store.mcpPossibilidades !== "function") return;
    const o = op || {};
    dispararPossibilidades(() => store.mcpPossibilidades({
      ticker: alvoAtual,
      direction: o.direction,
      kind: o.kind,
      lote: o.lote,
      // Preços NOMEADOS: viajam como `alvo`/`stop`, e é o backend que os
      // converte em cenários com esses mesmos nomes. Número solto no corpo
      // viraria um cenário anônimo que ninguém consegue ler no gráfico.
      alvo: o.alvo,
      stop: o.stop,
      expirations: o.expirations,
    }));
  }, [store, alvoAtual, dispararPossibilidades]);

  return {
    status, leitura, grafico, abrirGrafico, fecharGrafico,
    cadeia, operaveis, proposta, possibilidades,
    abrirCadeia, abrirOperaveis, montarProposta, verPossibilidades,
  };
}

export default useOpcoesMcp;
