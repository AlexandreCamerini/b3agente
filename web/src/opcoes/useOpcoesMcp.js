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

// Fase 27 (27-04) — período da LEITURA TÉCNICA INTERNA, FIXO e nomeado.
//
// Duas coisas o número resolve, e nenhuma delas é estética:
//
//  1. **A régua precisa de sete velas FECHADAS na cauda.** Com um período
//     curto a série viria truncada e o `motivo` da régua ("a série tem menos
//     de 7 pregões") apareceria em TODA leitura, sem defeito nenhum por trás
//     — um aviso que aparece sempre deixa de ser lido.
//  2. **O período escolhe a CAUDA, não o histórico.** O warmup das médias
//     longas é fixo em 2 anos no backend (`server/app/candles.py`,
//     `FETCH_RANGE`), então a confiabilidade da SMA200 — e portanto o
//     `confiavel` de cada segmento — NÃO depende deste valor.
//
// O que ele não pode é VARIAR por chamada: dois períodos diferentes na mesma
// tela produziriam duas leituras do mesmo dia, e a régua discordaria da linha
// de tendência logo acima dela (correção C7 do plano). Não passar `period` é
// a alternativa pior: o default fica implícito no backend e some do fonte que
// a tela lê.
const PERIODO_DA_LEITURA = "1y";

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
  // Fase 27 (27-02) — "Seus vigias": o ÍNDICE local da conta, que existe fora
  // de qualquer ticker. Trio próprio, e não um campo da `leitura`, porque é
  // justamente essa independência que corrige o defeito da fase (sair da aba e
  // voltar deixava de mostrar setup nenhum). `carregando` nasce VERDADEIRO
  // pela mesma razão do `status` e da `leitura`: uma lista vazia pintada
  // durante a consulta é a afirmação "você não tem vigia", que ninguém mediu.
  const [vigias, setVigias] = useState({ dados: null, carregando: true, erro: null });
  // Fase 27 (27-04) — a LEITURA TÉCNICA INTERNA do ativo (tendência,
  // volatilidade, níveis e a régua de 7 pregões), do motor determinístico do
  // próprio Boris+.
  //
  // Nasce VAZIO, e não `carregando: true` como os três acima: eles saem no
  // mount e a tela tem de dizer "consultando" desde o primeiro frame; este só
  // existe DEPOIS de haver ativo escolhido, e o bloco não é renderizado sem
  // ticker. Nascer "carregando" afirmaria uma consulta que não foi pedida.
  const [tecnico, setTecnico] = useState(VAZIO);

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
  // Fase 27: contador TRANSVERSAL ao ticker, e é essa a razão de ele existir.
  // `useChamadaSobDemanda(tickerRef)` descarta a resposta quando o ticker
  // mudou entre o pedido e a volta — disciplina certa para cadeia, proposta e
  // leitura, que são afirmações SOBRE um ativo. A lista de vigias não é: ela
  // atravessa todos os ativos. Passar `tickerRef` aqui faria clicar num
  // cartão de vigia (que troca o ticker) apagar a lista que a pessoa acabou
  // de pagar 2 chamadas para ver. Um ref que nunca muda mantém a disciplina
  // do contador próprio (`meuRef`, contra disparo repetido) e desliga só a
  // conferência de ticker.
  const vigiasRef = useRef(0);

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
  // Fase 27: o ESTADO DO DIA dos vigias (`armed`/`streak`), sob demanda.
  // Acrescentado no FIM do bloco, porque a ordem de chamada dos hooks é fixa.
  // Sem `limpar`: a troca de ticker não invalida esta lista (ver `vigiasRef`).
  const [vigiasVivos, dispararVigias] = useChamadaSobDemanda(vigiasRef);

  useEffect(() => {
    if (!store || typeof store.mcpStatus !== "function") { setStatus(VAZIO); return undefined; }
    let vivo = true;
    setStatus((s) => ({ ...s, carregando: true }));
    store.mcpStatus()
      .then((d) => { if (vivo) setStatus({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (vivo) setStatus({ dados: null, carregando: false, erro: e }); });
    return () => { vivo = false; };
  }, [store]);

  // Fase 27 (27-02) — o ÚNICO efeito NOVO que dispara chamada sozinho, e ele é
  // legítimo por CONTRATO DA ROTA, não por conveniência: `GET
  // /api/options/vigias` custa **ZERO** no cap (27-01). Ela lê o índice local
  // do Boris+ e não toca `mcp.semente.dev` — é por isso que a rota mora fora
  // do prefixo `/mcp/`. O ADR-027 §3.3 proíbe gastar COTA ao abrir tela; ler
  // o que é de graça é justamente o que permite a aba abrir com conteúdo em
  // vez de abrir vazia.
  //
  // NÃO depende de `ticker`: o bloco "Seus vigias" existe fora de qualquer
  // ativo, e essa independência É a correção do defeito 2 do 27-CONTEXT.
  useEffect(() => {
    if (!store || typeof store.mcpVigias !== "function") { setVigias(VAZIO); return undefined; }
    let vivo = true;
    setVigias((s) => ({ ...s, carregando: true }));
    store.mcpVigias()
      .then((d) => { if (vivo) setVigias({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (vivo) setVigias({ dados: null, carregando: false, erro: e }); });
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

  // Fase 27 (27-04) — a leitura técnica INTERNA, disparada pela troca de
  // ticker.
  //
  // **Por que ESTE efeito pode disparar sozinho quando quase nenhum outro
  // pode.** O §3.3 do ADR-027 proíbe gastar COTA do serviço de opções sem
  // clique explícito. Aqui não há cota nenhuma a gastar: `GET
  // /api/options/tecnico/{ticker}` é rota INTERNA, declara `custoMcp: 0` como
  // campo de contrato e não toca `mcp.semente.dev` (27-03, provado no backend
  // por bomba no `mcp_client.call_tool`). É a mesma justificativa do efeito de
  // `mcpVigias` logo acima, e é ela que permite a aba responder "tendência,
  // volatilidade e níveis" assim que a pessoa escolhe um ativo, de graça.
  //
  // **Invalidação: `vivo`, e não `tickerRef`.** É a MESMA disciplina dos dois
  // efeitos de cima, de propósito. Ler `tickerRef.current` aqui faria a
  // correção depender da ORDEM DE DECLARAÇÃO dos efeitos — quem incrementa
  // `tickerRef` é o efeito de `leitura`, logo acima —, e mover este bloco
  // para cima dele deixaria a comparação falsa para sempre: nenhuma resposta
  // pintaria a tela, em silêncio e sem teste vermelho. O `vivo` do cleanup dá
  // a MESMA garantia ("resposta de PETR4 nunca pinta a tela de VALE3", porque
  // a troca de ticker roda o cleanup antes de reexecutar o efeito) sem
  // depender de ordem nenhuma.
  //
  // UMA referência ao método `opcoesTecnico` do store, com o guard sobre ELA
  // (e não sobre o nome escrito de novo) — mesmo
  // padrão de "porta única" de `atualizarVigias`. `.call(store)` preserva o
  // `this` do `deviceStore`, que declara o método no estilo atalho.
  useEffect(() => {
    const t = (ticker || "").trim();
    const ler = store && store.opcoesTecnico;
    if (!t || typeof ler !== "function") { setTecnico(VAZIO); return undefined; }
    let vivo = true;
    setTecnico({ dados: null, carregando: true, erro: null });
    ler.call(store, t, { period: PERIODO_DA_LEITURA })
      .then((d) => { if (vivo) setTecnico({ dados: d, carregando: false, erro: null }); })
      .catch((e) => { if (vivo) setTecnico({ dados: null, carregando: false, erro: e }); });
    return () => { vivo = false; };
  }, [store, ticker]);

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

  // Fase 27: recarga do ÍNDICE, sob demanda e de custo ZERO. Existe porque
  // gravar ou desativar um vigia muda a lista do topo da aba — e um vigia
  // recém-criado que só aparece depois de um reload é exatamente o defeito que
  // esta fase existe para fechar ("os setups não estão sendo gravados").
  //
  // O corpo repete o do efeito acima de propósito, pela MESMA razão já
  // documentada em `recarregarLeitura`: o efeito PRECISA continuar sendo o
  // lugar onde a leitura do índice dispara (é o que o guardião lê no fonte), e
  // chamar esta função de dentro dele criaria uma dependência que
  // reexecutaria o efeito. As duas chamadas custam zero.
  const recarregarVigias = useCallback(() => {
    if (!store || typeof store.mcpVigias !== "function") return;
    setVigias((s) => ({ ...s, carregando: true }));
    store.mcpVigias()
      .then((d) => setVigias({ dados: d, carregando: false, erro: null }))
      .catch((e) => setVigias({ dados: null, carregando: false, erro: e }));
  }, [store]);

  // Fase 27: o estado do dia dos vigias. NUNCA por efeito —
  // `GET /api/options/mcp/setups` custa **2** chamadas do cap, sempre 2,
  // qualquer que seja o número de vigias (27-01). Esta função é a única porta
  // para a rota, e o botão que a abre declara o custo no próprio controle.
  //
  // UMA referência ao método, e o guard sobre ELA: "porta única" é o que o
  // guardião lê no fonte, então o nome não é escrito em dois lugares.
  // `.call(store)` preserva o `this` do `deviceStore`, que usa método-atalho.
  const atualizarVigias = useCallback(() => {
    const listar = store && store.mcpSetupsListar;
    if (typeof listar !== "function") return;
    dispararVigias(() => listar.call(store));
  }, [store, dispararVigias]);

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
  //
  // Fase 27: além da leitura do ticker, recarrega o ÍNDICE (custo zero). Sem
  // isso o vigia recém-criado não aparece no bloco do topo até um reload — e
  // "não aparece" é literalmente o defeito que originou a fase.
  const confirmarSetup = useCallback((setup) => {
    if (!setup || !store || typeof store.mcpSetupConfirmar !== "function") return;
    dispararSetup(() => store.mcpSetupConfirmar({ setup }).then((d) => {
      recarregarLeitura();
      recarregarVigias();
      return d;
    }));
  }, [store, dispararSetup, recarregarLeitura, recarregarVigias]);

  const desativarSetup = useCallback((nome) => {
    if (!nome || !store || typeof store.mcpSetupDesativar !== "function") return;
    dispararSetup(() => store.mcpSetupDesativar(nome).then((d) => {
      recarregarLeitura();
      recarregarVigias();
      return d;
    }));
  }, [store, dispararSetup, recarregarLeitura, recarregarVigias]);

  return {
    status, leitura, grafico, abrirGrafico, fecharGrafico, recarregarLeitura,
    cadeia, operaveis, proposta, possibilidades,
    abrirCadeia, abrirOperaveis, montarProposta, verPossibilidades,
    setupNovo, compilarSetup, confirmarSetup, desativarSetup,
    // Fase 27: os dois trios de "Seus vigias" e as duas recargas. `vigias` é o
    // índice (custo zero, sai no mount); `vigiasVivos` é o estado do dia
    // (custo 2, só de clique).
    vigias, vigiasVivos, atualizarVigias, recarregarVigias,
    // Fase 27 (27-04): a leitura técnica interna do ativo — custo ZERO de
    // cota, motor determinístico do próprio app.
    tecnico,
  };
}

export default useOpcoesMcp;
