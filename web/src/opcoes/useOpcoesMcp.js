/**
 * useOpcoesMcp.js — aba-opcoes F2 (ADR-027, quick 260910-biz, 2026-09-10).
 *
 * Estado das chamadas ao serviço MCP para a aba Opções. Um trio
 * `dados / carregando / erro` por chamada (3 na F2, +4 na F3, +1 na F5).
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
  // F5: contador PRÓPRIO da leitura. `recarregarLeitura()` (chamada depois de
  // gravar ou desativar um setup) não é troca de ativo — se ela bumpasse
  // `tickerRef`, invalidaria as chamadas sob demanda em voo, inclusive a que
  // acabou de pedir a recarga. Com um contador só da leitura, as duas
  // disciplinas convivem: `tickerRef` diz DE QUAL ATIVO é a resposta,
  // `leituraRef` diz QUAL das leituras daquele ativo é a mais recente.
  const leituraRef = useRef(0);

  // F3: os quatro trios sob demanda. Ordem fixa de chamada (regra dos hooks).
  const [cadeia, dispararCadeia, limparCadeia] = useChamadaSobDemanda(tickerRef);
  const [operaveis, dispararOperaveis, limparOperaveis] = useChamadaSobDemanda(tickerRef);
  const [proposta, dispararProposta, limparProposta] = useChamadaSobDemanda(tickerRef);
  const [possibilidades, dispararPossibilidades, limparPossibilidades] = useChamadaSobDemanda(tickerRef);
  // F5: o trio da criação de setup. Um só para as TRÊS ações (compilar,
  // confirmar, desativar) porque as três são a mesma conversa: a resposta de
  // uma substitui a da anterior na tela, e `status` (`dry_run`/`ativo`/
  // `inativo`) diz qual delas respondeu.
  const [setupNovo, dispararSetup, limparSetup] = useChamadaSobDemanda(tickerRef);

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
    limparSetup();

    if (!t || !store || typeof store.mcpLeitura !== "function") {
      setLeitura(VAZIO);
      return undefined;
    }
    const minha = ++leituraRef.current;
    setLeitura({ dados: null, carregando: true, erro: null });
    store.mcpLeitura(t)
      .then((d) => { if (tickerRef.current === meu && leituraRef.current === minha) setLeitura({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (tickerRef.current === meu && leituraRef.current === minha) setLeitura({ dados: null, carregando: false, erro: e }); });
    return undefined;
  }, [store, ticker, limparCadeia, limparOperaveis, limparProposta, limparPossibilidades, limparSetup]);

  // F5: recarga da leitura do MESMO ticker, sob demanda. Existe porque gravar
  // ou desativar um setup muda a lista que a seção "SETUPS GRAVADOS" mostra —
  // deixar a tela velha depois de um "gravado com sucesso" faria a pessoa
  // duvidar de ter gravado, e duvidar leva a gravar de novo (o mesmo vigia,
  // duas vezes, no armazém compartilhado do serviço).
  //
  // O corpo repete o do efeito acima de propósito: mover o `store.mcpLeitura`
  // para fora do efeito quebraria a leitura que o guardião faz do fonte (o
  // efeito PRECISA continuar sendo o lugar onde a leitura inicial dispara),
  // e chamar esta função de dentro dele criaria uma dependência que
  // reexecutaria o efeito a cada troca de `ticker` duas vezes.
  const recarregarLeitura = useCallback(() => {
    const t = (ticker || "").trim();
    if (!t || !store || typeof store.mcpLeitura !== "function") return;
    const meu = tickerRef.current;        // NÃO incrementa: não é troca de ativo
    const minha = ++leituraRef.current;
    setLeitura({ dados: null, carregando: true, erro: null });
    store.mcpLeitura(t)
      .then((d) => { if (tickerRef.current === meu && leituraRef.current === minha) setLeitura({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (tickerRef.current === meu && leituraRef.current === minha) setLeitura({ dados: null, carregando: false, erro: e }); });
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

  // ---------------------------------------------------------------- F5 --
  // As três ações de ESCRITA de setup. Também por clique, nunca por efeito:
  // `compilar` gasta uma chamada de LLM paga além de duas do cap, e uma
  // chamada de modelo disparada por render seria a conta que ninguém pediu.
  //
  // O ticker sai do argumento do hook, como nas quatro da F3: a pessoa nunca
  // pode gravar um vigia sobre um ativo diferente do que está no cabeçalho.
  const compilarSetup = useCallback((op) => {
    if (!alvoAtual || !store || typeof store.mcpSetupCompilar !== "function") return;
    const o = op || {};
    dispararSetup(() => store.mcpSetupCompilar({ descricao: o.descricao, ticker: alvoAtual }));
  }, [store, alvoAtual, dispararSetup]);

  // O setup que viaja de volta é o MESMO objeto que a tela exibiu no ensaio —
  // não é recompilado nem passa por LLM. Recarregar a leitura no sucesso é
  // parte da ação, não cosmético: é o que prova à pessoa que o vigia nasceu.
  const confirmarSetup = useCallback((setup) => {
    if (!setup || !store || typeof store.mcpSetupConfirmar !== "function") return;
    dispararSetup(() => store.mcpSetupConfirmar({ setup }).then((d) => {
      recarregarLeitura();
      return d;
    }));
  }, [store, dispararSetup, recarregarLeitura]);

  const desativarSetup = useCallback((nome) => {
    if (!nome || !store || typeof store.mcpSetupDesativar !== "function") return;
    dispararSetup(() => store.mcpSetupDesativar(nome).then((d) => {
      recarregarLeitura();
      return d;
    }));
  }, [store, dispararSetup, recarregarLeitura]);

  return {
    status, leitura, grafico, abrirGrafico, fecharGrafico, recarregarLeitura,
    cadeia, operaveis, proposta, possibilidades,
    abrirCadeia, abrirOperaveis, montarProposta, verPossibilidades,
    setupNovo, compilarSetup, confirmarSetup, desativarSetup,
  };
}

export default useOpcoesMcp;
