/**
 * OpcoesScreen.jsx — aba-opcoes F2 (ADR-027, quick 260910-biz, 2026-09-10).
 *
 * Primeira superfície real da aba Opções: o que o serviço `mcp.semente.dev`
 * já sabe sobre um ticker — comportamento recente, catálogo de estruturas,
 * vencimentos e os setups gravados com a avaliação do dia. Sem cadeia, sem
 * payoff, sem veredito (Fases 3–4 do `docs/PLANO-aba-opcoes.md`).
 *
 * Regras que esta tela NÃO negocia:
 * · nenhum número é recalculado aqui — tudo vem do serviço, e campo ausente
 *   vira travessão, nunca 0 (princípio 4/5 do CLAUDE.md);
 * · "em dia" só aparece com frescor MEDIDO — "não medido" que vira silêncio
 *   é lido como "em dia" (ADR-027, Decisão 8); e "nada foi consultado" não
 *   vira "não medido" — achado ao vivo 2026-09-10 (quick 260910-d57);
 * · erro escolhido por `code` conhecido (ADR-027), nunca pela chamada que
 *   respondeu primeiro — mesmo achado ao vivo;
 * · o motivo de uma recusa do serviço vai VERBATIM, sem reescrita;
 * · vazio nunca é silêncio: todo estado vazio diz o porquê.
 */
import { useState } from "react";
// Fase 27 (27-02): `finance.js` é módulo PURO — zero import de `App.jsx` —,
// então o isolamento do ADR-027 continua intacto (o guardião proíbe importar
// `App.jsx`, não `finance.js`). `qtyLivre` é a FONTE ÚNICA da subtração
// `qty - qtyTravada` no front, gêmea de `store.qty_livre` no backend:
// recalculá-la aqui criaria uma segunda implementação que divergiria da
// primeira na correção seguinte, em silêncio e com o mesmo nome na tela.
import { qtyLivre } from "../finance.js";
// Fase 27 (27-04): o formatador de volatilidade é ESCOLHIDO pela unidade que
// o contrato declara. Ver o comentário do bloco de HV em `LeituraInterna` —
// nesta mesma tela convivem um percentual (motor interno) e uma fração
// (serviço MCP), e trocá-los erra por 10× em silêncio.
import { formatarVolatilidade } from "./unidades.js";
import { useOpcoesMcp } from "./useOpcoesMcp.js";
import ReguaRegime from "./ReguaRegime.jsx";
import PayoffChart from "./PayoffChart.jsx";
// Fase 28 (28-02): módulo terceiro do 28-01 — nenhum import de `App.jsx`
// aqui (isolamento ADR-027 Decisão 3 intacto).
// Fase 32 (32-04): `FonteDoDadoProposta` entra no import — o ramo
// multi-candidato de `SubAbaOperar` passa a exibir o frescor do dado abaixo
// do carrossel, mesmo padrão que `PropostaDaPosicao` tinha em App.jsx.
import PropostaLastreada, { FonteDoDadoProposta, useAceiteLastreado } from "./PropostaLastreada.jsx";
import { useOpcoesPropostas } from "./useOpcoesPropostas.js";
// Fase 32 (32-04): `CandidatoOpcao` (o cartão de UM candidato) é reusado
// verbatim — o ramo multi-candidato de `PropostaDaPosicao` (App.jsx) é
// portado para dentro de `SubAbaOperar`, e `PropostaDaPosicao` morre em
// App.jsx (ver 32-04-PLAN.md, decisão arquitetural B). Módulo terceiro,
// nenhum import de App.jsx.
import CandidatoOpcao from "./CandidatoOpcao.jsx";
// Fase 33 (33-01): `Kicker`/`Aviso`/`ErroDoMcp`/`RecusaCobrada` migraram para
// o módulo de primitivos compartilhados — uma implementação só de `ErroDoMcp`
// (ramifica nos 4 códigos do ADR-027) reusada por esta tela e pelas seções
// job-to-be-done (`Secao*.jsx`, D-01 do 33-CONTEXT.md). `SecaoVigias` é o job
// 2 ("gerenciar vigias"), extraído na Fase 33-01.
// Fase 33 (33-04): `Linha` migrou para `uiOpcoes.jsx` — LeituraInterna
// (abaixo, custo zero) e as seções job-to-be-done usam a MESMA implementação.
// `RazaoGanhoPerda` migrou junto no 33-04, mas o único consumidor que restava
// em OpcoesScreen.jsx (o job 3, "O QUE DÁ PARA MONTAR") saiu na Fase 33-05
// para SecaoAnalisar.jsx — o import daqui foi removido (SecaoAnalisar.jsx/
// SecaoComparar.jsx importam `RazaoGanhoPerda` de `uiOpcoes.jsx` direto).
import { Kicker, Aviso, ErroDoMcp, RecusaCobrada, Linha } from "./uiOpcoes.jsx";
import SecaoVigias from "./SecaoVigias.jsx";
// Fase 33 (33-05): `SecaoAnalisar` é o job 3 ("analisar um ticker
// manualmente") — LEITURA DO ATIVO + O QUE DÁ PARA MONTAR, com o painel local
// de cadeia/operáveis. Último dos 5 jobs extraídos; fecha D-03.
import SecaoAnalisar from "./SecaoAnalisar.jsx";
// Fase 33 (33-02): `SecaoDescobrir` é o job 1 ("descobrir oportunidades
// cross-carteira") — frase-ponte + Bloco A (OportunidadesOpcoes) + Bloco B
// (CuradoriaEstruturas) juntos, adjacentes (D-05). `OportunidadesOpcoes.jsx`/
// `CuradoriaEstruturas.jsx` deixam de ser importados AQUI: quem os compõe
// agora é o componente novo, não mais esta tela.
import SecaoDescobrir from "./SecaoDescobrir.jsx";
// Fase 33 (33-03): `SecaoSetups` é o job 5 ("gerenciar/criar setups
// salvos") — a listagem "SETUPS GRAVADOS" + a porta "CRIAR UM SETUP", que só
// envolve o `CriarSetup.jsx` já existente (D-01, não renomeado). `CriarSetup`/
// `BotaoDesativar`/`SetupChart` deixam de ser importados AQUI: quem os
// envolve agora é o componente novo.
import SecaoSetups from "./SecaoSetups.jsx";
// Fase 33 (33-04): `SecaoComparar` é o job 4 ("comparar os vencimentos") — a
// caixa com custo declarado, alvo/stop e a cascata de possibilidades por
// vencimento. Posição EXATA de hoje: entre o job 3 (Analisar, ainda aqui) e a
// seção de setups gravados (job 5), abaixo.
import SecaoComparar from "./SecaoComparar.jsx";
// Fase 34 (34-01/34-02): `WorkspaceHeader` é o header fixo do modo workspace
// (D-05/NAV-03) — nome do ticker + botão "Voltar" ligado a `escolherTicker`
// já existente (D-03: reset de tese/vencimento/alvo/stop sem segundo
// caminho). Componente props-only, criado no 34-01.
import WorkspaceHeader from "./WorkspaceHeader.jsx";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root` — padrão de
// `pet/BorisChat.jsx`. Zero import de `App.jsx` (seria ciclo).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Fase 32 (32-04): espelho declarado de App.jsx (padrão ÚNICO de rolagem
// horizontal, Fase 22 SYS-01) — mesmo padrão já usado em
// OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx (Fase 32, 32-02): nunca
// importar de App.jsx (ADR-027, isolamento de duas vias). Usado só pelo
// container do ramo multi-candidato de `SubAbaOperar` — `CandidatoOpcao.jsx`
// já declara seu próprio `carouselItemStyle` local, então este arquivo não
// precisa dele.
const carouselTrackStyle = (extra) => ({
  display: "flex",
  overflowX: "auto",
  scrollSnapType: "x proximity",
  WebkitOverflowScrolling: "touch",
  ...extra,
});

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const pct = (v, casas = 2) => (ehNum(v) ? fmt(v, casas) + "%" : "—");

// Fase 33 (33-04): `Linha` migrou para `uiOpcoes.jsx` — LeituraInterna
// (custo zero, abaixo) e as seções job-to-be-done usam a MESMA implementação.
// Ver o import de `uiOpcoes.jsx` no topo do arquivo.
//
// Fase 33 (33-05): `fracPct`/`txt`/`faixa`, `ROTULO_LEITURA`/
// `LacunasDaLeitura` e o botão de "Montar estrutura" desabilitado saíram
// daqui — único consumidor de cada um era o job 3 ("LEITURA DO ATIVO"/"O QUE
// DÁ PARA MONTAR"), extraído para `SecaoAnalisar.jsx` (que declara os mesmos
// nomes localmente, espelho declarado de formatador de uma linha).

// aba-opcoes F3 (plano 24-02). Alvo de toque de 44 px em TODO botão novo —
// os dois estilos abaixo existem para que nenhum deles possa esquecer disso.
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};

// Fase 27 (27-05) — a SEGUNDA LINHA do botão, onde o custo é declarado. Estilo
// nomeado e não repetido botão a botão: são sete controles com a mesma linha, e
// sete cópias de um objeto de estilo divergem na primeira manutenção feita só
// numa delas. Tokens existentes, nenhuma cor nova (Brand Book v2).
//
// DENTRO do botão, não ao lado: o custo tem de viajar junto do alvo de toque,
// senão a pessoa lê o rótulo e clica no controle errado. Peso e tamanho menores
// que o rótulo porque a ação é o que se lê primeiro; o preço é a ressalva que
// vem grudada nela.
const CUSTO_NO_BOTAO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.textMuted, marginTop: "3px",
};

const CAIXA = {
  border: `1px solid ${T.borderSubtle}`, borderRadius: "12px",
  padding: "12px 14px", background: T.bgPanel,
};
const AJUDA = { fontSize: "11px", color: T.textMuted, marginTop: "4px", lineHeight: 1.45 };

// Fase 33 (33-05): `CAMPO`/`ROTULO` (campos de formulário do job 3) e
// `ROLAGEM`/`TABELA`/`TH`/`TD`/`LADO` (tabela de pernas/cadeia/operáveis, só
// usada por `Pernas`/`TabelaDeOpcoes`, que migraram junto) saíram daqui —
// único consumidor de cada um era o job 3, extraído para
// `SecaoAnalisar.jsx` (espelho declarado local, mesmo padrão de
// `SecaoComparar.jsx`).

const num = (v) => {
  const n = Number(v);
  return isFinite(n) ? n : null;
};

// Espelho de `options_mcp_api.N_MAX_VENCIMENTOS`. O backend também corta em 6
// — o número vive nos dois lados porque a tela precisa dizer o custo ANTES de
// perguntar ao servidor quanto vai custar. Divergir aqui só produziria um
// aviso errado; quem corta de verdade é o backend.
const N_MAX_VENCIMENTOS = 6;

// Fase 27 (27-05) — **O CUSTO DE CADA AÇÃO DA ABA, EM CHAMADAS DO CAP.**
//
// Três coisas que esta tabela é, e que o próximo leitor precisa saber antes de
// mexer num número:
//
//  1. **Ela é ESPELHO do backend.** Cada valor aqui é o `N` de um
//     `_cap_check(uid, N)` de `server/app/options_mcp_api.py` — a mesma
//     disciplina de `N_MAX_VENCIMENTOS` logo acima, e a mesma de
//     `ACOES_POR_CONTRATO` logo abaixo. Quem cobra de verdade é o backend;
//     esta tabela existe só para a tela poder dizer o preço ANTES do clique.
//  2. **O número vive nos dois lados de propósito.** Perguntar ao servidor
//     quanto vai custar seria uma chamada para saber o preço de uma chamada.
//     O preço do espelho é o risco de divergir — e é por isso que ele não é
//     livre: `web/tests/test_opcoes_custo_declarado.mjs` lê ESTE objeto e os
//     `_cap_check` do backend e reprova a suíte quando os dois discordam.
//     Mudar um `_cap_check` sem mudar aqui não produz um rótulo errado em
//     produção: produz um teste vermelho.
//  3. **Custo zero não entra.** `mcpVigias` e `opcoesTecnico` custam 0 por
//     contrato da rota; declarar custo onde não há custo mentiria para o outro
//     lado, e o guardião proíbe. `mcpPossibilidades` também fica fora: o custo
//     dela é CALCULADO (`2 * N + 1`) e já é declarado no próprio controle.
//     `mcpStatus` fica fora pela terceira razão: ela não tem controle — é o
//     frescor do cabeçalho, e o custo dela é declarado em texto
//     (`cp.opcoesCustoFrescor`).
//
// `listarVigias` era a constante solta `CUSTO_LISTAR_VIGIAS` (27-02); entrou na
// tabela sem mudar de valor — duas formas de declarar a mesma grandeza na
// mesma tela divergiriam na primeira manutenção feita só numa delas.
const CUSTO_DA_ACAO = {
  leitura: 3,        // GET /mcp/leitura/{ticker}      — _cap_check(uid, 3)
  cadeia: 1,         // GET /mcp/cadeia/{ticker}       — _cap_check(uid, 1)
  operaveis: 1,      // GET /mcp/operaveis/{ticker}    — _cap_check(uid, 1)
  proposta: 1,       // POST /mcp/proposta             — _cap_check(uid, 1)
  grafico: 1,        // GET /mcp/setups/{name}/grafico — _cap_check(uid, 1)
  compilar: 2,       // POST /mcp/setups/compilar      — _cap_check(uid, 2) + 1 análise de IA
  confirmar: 2,      // POST /mcp/setups/confirmar     — _cap_check(uid, 2)
  desativar: 1,      // POST /mcp/setups/{name}/desativar — _cap_check(uid, 1)
  listarVigias: 2,   // GET /mcp/setups                — _cap_check(uid, 2)
};

// Fase 27 (27-02) — o tamanho do contrato padrão na B3. Espelho declarado de
// `store.py` (`qty = contratos * 100`) e do conceito que o próprio arquivo já
// enuncia em `opcoesLoteAjuda` ("1 contrato = 100 ações"). Constante nomeada
// em vez de um `100` solto no meio do JSX: o número solto é indistinguível de
// um palpite de layout, e este é um espelho de regra do backend.
const ACOES_POR_CONTRATO = 100;

export default function OpcoesScreen({ ctx }) {
  const cp = (ctx && ctx.cp) || {};
  const store = ctx && ctx.store;
  const palette = (ctx && ctx.palette) || {};
  // Fase 27 (D3 do 27-CONTEXT, 2026-09-13) — o universo desta aba é a
  // CARTEIRA, não a watchlist. O pedido do Alex é literal ("que a aba de
  // opções só apresentasse os ativos que estão no portfolio e que os setups
  // fossem armados sob os mesmos"), e a razão é de produto: toda estrutura
  // que esta aba monta é lastreada no papel em carteira. Watchlist é
  // INTENÇÃO; posição é LASTRO — e é o lastro que decide o que dá para
  // montar. Sem chamada nova: `positions` já chega no `ctx` (a MESMA fonte
  // que o `App.jsx` usa para marcar "em carteira").
  //
  // Ordem: a que `positions` chega. Nada é reordenado aqui — "Em aberto 2" do
  // 27-CONTEXT (carteira grande, acima de ~8 posições, vira rolagem longa)
  // segue sem decisão do Alex, e o desenho abaixo não impede uma busca depois
  // nem a inventa agora.
  const carteira = ((ctx && ctx.data && ctx.data.positions) || []).filter((p) => p && p.t);
  // O ticker NASCE VAZIO — e isto é a decisão, não a omissão. Escolher um
  // ativo dispara `mcpLeitura` pelo efeito de troca de ticker
  // (`useOpcoesMcp.js`), e essa chamada custa **3** no cap do ADR-027.
  // Auto-selecionar o primeiro da carteira cobraria 3 consultas de quem só
  // abriu a aba — exatamente o que o §3.3 proíbe ("custo de MCP só em clique
  // explícito, nunca ao abrir tela") e o que o guardião
  // `test_opcoes_analisar_ui.mjs` reprova.
  //
  // A aba não abre VAZIA; ela abre sem ATIVO ESCOLHIDO, que é outra coisa: a
  // lista das posições e o bloco "Seus vigias" já estão na tela quando ela
  // abre, os dois de custo zero. É o desenho aprovado (D4: a aba abre na
  // lista, e entrar num ativo é um toque).
  const [ticker, setTicker] = useState("");
  // Fase 28 (28-02) — a aba ganha duas sub-abas: "Setups" (esta tela, tal
  // como a Fase 27 entregou) e "Operar" (proposta lastreada da posição
  // escolhida). Nasce em "setups" porque é a tela que abre de graça hoje. O
  // `ticker` acima é COMPARTILHADO entre as duas: quem escolheu um ativo
  // para ler não deve reescolher para operar.
  const [subaba, setSubaba] = useState("setups");
  const {
    status, leitura, grafico, abrirGrafico, fecharGrafico, abrirLeitura,
    cadeia, operaveis, proposta, possibilidades,
    abrirCadeia, abrirOperaveis, montarProposta, verPossibilidades,
    setupNovo, compilarSetup, confirmarSetup, desativarSetup,
    vigias, vigiasVivos, atualizarVigias,
    tecnico,
  } = useOpcoesMcp(store, ticker);

  // F5 (plano 24-04) — a seção de ESCRITA de setup só aparece para quem tem
  // `opcoes.criar_setup`. Isto é conveniência, não segurança: as três rotas
  // respondem 403 sozinhas (ADR-013; provado por injeção de defeito no plano
  // 24-03), e nada aqui muda esse fato. Sem a lista de permissões
  // disponível (anônimo, ou estado ainda não carregado), FALSO — falhar
  // fechado na UI é o lado certo de errar, já que o servidor recusaria de
  // qualquer jeito e um botão que sempre dá 403 é pior que botão nenhum.
  //
  // A leitura vem de `ctx.authUser.permissions`, a MESMA fonte que o grupo
  // "Administração" do Perfil já usa (ADR-014). Um segundo caminho de
  // leitura de permissão divergiria do primeiro na próxima mudança do
  // `_public_user`.
  const permissoes = (ctx && ctx.authUser && Array.isArray(ctx.authUser.permissions))
    ? ctx.authUser.permissions : [];
  const podeCriarSetup = permissoes.includes("opcoes.criar_setup");

  // F3 — o que a pessoa escolhe antes de gastar chamada. Nada disto dispara
  // nada sozinho: são os argumentos dos cliques.
  const [tese, setTese] = useState("");      // "" = nenhuma; ver comentário no seletor
  const [vencimento, setVencimento] = useState("");
  const [lote, setLote] = useState("100");
  const [alvo, setAlvo] = useState("");
  const [stop, setStop] = useState("");

  // Trocar de ativo apaga a TESE e os preços: tese é juízo sobre AQUELE
  // ativo, e um alvo de 41,00 herdado de outro papel seria um cenário falso.
  // O lote fica — ele é da pessoa, não do ativo. `painel` (cadeia/operáveis)
  // virou estado LOCAL de SecaoAnalisar.jsx na Fase 33 (33-05) — o
  // componente não desmonta ao trocar de ticker (fica na mesma posição da
  // árvore), então o reset agora é um `useEffect([ticker])` DENTRO dele
  // (mesma garantia de antes: painel fecha ao trocar de ativo), em vez de
  // `setPainel("")` aqui.
  const escolherTicker = (t) => {
    setTicker(t === ticker ? "" : t);
    setTese(""); setVencimento(""); setAlvo(""); setStop("");
  };

  // Fase 27: o cartão do vigia NAVEGA; ele não alterna. `escolherTicker` é
  // toggle — é o que o chip precisa, para poder desselecionar —, e reusá-lo
  // cru aqui faria clicar no vigia do ativo JÁ ABERTO fechar o ativo, o
  // oposto de "me leve até ele" (SC-1: não precisar lembrar em qual ativo
  // criei o vigia).
  const irParaVigia = (t) => { if (t && t !== ticker) escolherTicker(t); };

  // Fase 32 (32-03): destino do "ver posição" de dentro do painel curado
  // (Bloco B) e do "ver detalhe" da tira (Bloco A) — substitui o
  // `abrirOpcoesDe`/`scrollIntoView` de CarteiraScreen, que dependia de um
  // elemento `#posicao-<t>` que só existe naquela tela (Pitfall 4 do
  // 32-RESEARCH.md). MESMA guarda de `irParaVigia` acima: `escolherTicker`
  // é TOGGLE, e chamá-lo cru com o ticker já aberto DESSELECIONARIA o
  // ativo — o oposto de "me leve até ele".
  const irParaOperar = (t) => { if (t && t !== ticker) escolherTicker(t); setSubaba("operar"); };

  // Fase 32 (32-03), Decisão A: fan-out gate+proposta por ticker sobre o
  // universo desta aba (a carteira) — mesma fonte que alimentava a tira em
  // CarteiraScreen (ADR-027 Emenda 3, módulo compartilhado).
  const { propostas: opcoesPorTicker, carregando: opcoesPorTickerCarregando } =
    useOpcoesPropostas(store, carteira.map((p) => p.t));

  const l = leitura.dados;
  const behavior = l && l.behavior;
  const setups = (l && Array.isArray(l.setups) && l.setups) || [];
  const naoAvaliado = l && l.setupsNaoAvaliados;

  // Frescor escolhido por QUALIDADE da medição, não por quem respondeu
  // primeiro — mesma classe do defeito 2 (escolherErroOpcoes), corrigido
  // hoje. `pregao`/`fonte` continuam pela leitura: são carimbo do dado
  // exibido, não medição de qualidade — o pregão da leitura é o correto
  // para o que está na tela.
  const frescor = escolherFrescor(l && l.frescor, status.dados && status.dados.frescor);
  const pregao = (l && l.pregao) || (status.dados && status.dados.pregao) || null;
  const fonte = (l && l.fonte) || (status.dados && status.dados.fonte) || null;

  // Chip de frescor em TRÊS variantes, pela ORIGEM da informação — nunca um
  // default genérico que sobra quando ninguém respondeu:
  //   (a) `!frescor` — nada foi consultado ainda (achado ao vivo, produção
  //       sem a Fase 2: `/leitura` 404 e `frescor` fica nulo). O chip não
  //       afirma nada: fica de fora. Mesma simetria que este arquivo já
  //       aplica aos setups ("sem avaliação NÃO vira não armado: ausência de
  //       leitura não é leitura negativa") — aqui, ausência de resposta não
  //       vira "não medido". Omitir em vez de travessão porque o cabeçalho
  //       já tem `Pregão: —`; um segundo traço solto ao lado seria ruído sem
  //       ganho de informação.
  //   (b) `frescor.medido === false` — o serviço respondeu e não mediu:
  //       "não medido" continua, e agora é verdade (houve resposta).
  //   (c) `frescor.medido === true` — em dia / atrasado com idade.
  //   (d) 24-12 — a DISTÂNCIA em pregões até o último fechado, medida pelo
  //       backend com o calendário da B3. É a única variante com precedência
  //       sobre "dado em dia": no achado de 2026-09-11 o serviço estava
  //       coerente com o próprio SLA (49,58 h contra 96 h) e ainda assim
  //       faltavam DOIS pregões na base — "dado em dia" era falso mesmo com
  //       o fornecedor assinando embaixo. O que o chip diz passa a ser o que
  //       se pode medir.
  //
  // A distância acompanha o `pregao` (leitura primeiro, status depois): são
  // carimbo e medição do MESMO dado exibido. `0` e `null` seguem o caminho de
  // hoje — 0 é "está no último pregão fechado", e null é "não deu para medir".
  const atraso = (l && l.atraso) || (status.dados && status.dados.atraso) || null;
  const pregoesAtras = (atraso && ehNum(atraso.pregoes) && atraso.pregoes >= 1)
    ? atraso.pregoes : 0;
  const distancia = pregoesAtras
    ? (cp.opcoesAtrasoPregoes ? cp.opcoesAtrasoPregoes(pregoesAtras)
      : pregoesAtras + " pregões atrás")
    : "";

  let chip = null;
  if (frescor && frescor.medido === false) {
    chip = cp.opcoesFrescorNaoMedido || "frescor não medido";
  } else if (frescor && frescor.medido) {
    const critica = (frescor.classes || [])[0];
    const idade = critica && ehNum(critica.idadeHoras) ? " (" + fmt(critica.idadeHoras, 0) + " h)" : "";
    if (frescor.bloqueia) {
      // O alerta do serviço CONTINUA: idade da carga e pregões faltando são
      // grandezas diferentes, e a distância entra somando, logo abaixo.
      chip = (cp.opcoesFrescorAtrasado || "dado atrasado") + idade;
    } else if (!distancia) {
      // "dado em dia" só sobra quando NÃO há pregão faltando.
      chip = cp.opcoesFrescorEmDia || "dado em dia";
    }
  }
  // A distância nunca é engolida por um veredito herdado: soma ao alerta de
  // quem mediu a carga e ocupa sozinha o lugar do "em dia" que o ramo acima
  // deixou de escolher.
  if (distancia) chip = chip ? chip + " · " + distancia : distancia;

  // Vencimentos que a LEITURA já trouxe — é deles que sai o custo em
  // chamadas mostrado ANTES do clique. Nenhuma consulta extra para saber
  // quanto a próxima consulta vai custar.
  const vencimentos = (Array.isArray(l && l.expirations) ? l.expirations : [])
    .filter((v) => typeof v === "string" && v);
  const N = Math.min(vencimentos.length, N_MAX_VENCIMENTOS);
  const consultados = vencimentos.slice(0, N);
  const chamadasPrevistas = 2 * N + 1;

  // Lote em AÇÕES, inteiro ≥ 1 (D-24.3): a UI oferece múltiplos de 100 e diz
  // "1 contrato = 100 ações", mas não recusa 150 — recusar seria inventar uma
  // regra que a B3 aplica por série, e o backend também não recusa.
  const loteNum = ehNum(num(lote)) ? Math.trunc(num(lote)) : null;
  const loteOk = ehNum(loteNum) && loteNum >= 1;
  // Fase 33 (33-04): `alvoNum`/`stopNum` (a forma numérica de `alvo`/`stop`,
  // preço ausente vira AUSÊNCIA — `undefined`, nunca zero) migraram para
  // dentro de SecaoComparar.jsx, único consumidor do par desde que o disparo
  // de `verPossibilidades` saiu daqui.
  const temTese = !!tese;

  const erro = escolherErroOpcoes(leitura.erro, status.erro);
  const carregando = status.carregando || leitura.carregando;
  const semTicker = !ticker;
  const semCandles = !!(behavior && behavior.status === "sem_candles");
  const temLeitura = !!(behavior && !semCandles);
  const nadaParaMostrar = semTicker || (!temLeitura && setups.length === 0);

  const cabecalho = (
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "14px", padding: "12px 14px", background: T.bgPanel }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "baseline", justifyContent: "space-between" }}>
        <div style={{ fontSize: "12.5px", color: T.textSecondary }}>
          {(cp.opcoesPregaoRotulo || "Pregão") + ": "}
          <strong style={{ color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{pregao || "—"}</strong>
        </div>
        <div style={{ fontSize: "12px", color: T.textMuted }}>
          {/* Mesma regra do chip: sem resposta do serviço, não se afirma
              origem — o default literal "mcp.semente.dev" mentia a fonte
              mesmo com `/status`/`/leitura` fora do ar. Travessão aqui (não
              omissão) porque este rótulo já convive ao lado do "Pregão: —"
              no mesmo padrão visual. */}
          {(cp.opcoesFonteRotulo || "Fonte") + ": " + (fonte || "—")}
        </div>
        {chip ? (
          <span style={{ fontSize: "11.5px", fontWeight: 700, color: T.textSecondary, border: `1px solid ${T.borderSubtle}`, borderRadius: "999px", padding: "3px 9px" }}>
            {chip}
          </span>
        ) : null}
      </div>
      {frescor && frescor.bloqueia && frescor.warning ? (
        <div style={{ marginTop: "8px", fontSize: "12px", color: T.textSecondary, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
          {frescor.warning}
        </div>
      ) : null}
      {/* 24-12 — a regra da contagem, só quando há contagem na tela:
          explicar um número que ninguém está vendo é ruído. Mesmo tom
          discreto do rodapé das lacunas (24-11) — é informação, não erro. */}
      {distancia && cp.opcoesAtrasoAjuda ? (
        <div style={{ marginTop: "6px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
          {cp.opcoesAtrasoAjuda}
        </div>
      ) : null}
      {/* Fase 27 (27-05) — **A ÚNICA EXCEÇÃO AO CRITÉRIO 4, DITA NA TELA.**

          `mcpStatus` sai no mount e reserva 1 chamada do cap; ela só vira
          consumo quando a consulta precisa mesmo ir ao serviço (acerto de
          cache não gasta — `options_mcp_api.py`, `status`). É a única chamada
          desta aba que não nasce de um clique, e a exceção é PRÉ-EXISTENTE:
          ela vem da F2, não desta fase.

          Por que ela não vira botão: o cabeçalho precisa dizer a idade do dado
          desde o primeiro frame (ADR-027, Decisão 8), e um gate de frescor que
          só aparece depois de um clique não protege ninguém — a pessoa já
          teria lido a tela inteira acreditando no dado. A correção honesta não
          é esconder o custo, é declará-lo; e é isto aqui.

          Sem condição de render: o custo existe mesmo quando o serviço não
          respondeu (a reserva sai antes da resposta), então escondê-lo no
          estado de erro seria calar justamente onde a pessoa vai reclamar do
          contador. */}
      <div style={{ marginTop: "8px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
        {cp.opcoesCustoFrescor || ""}
      </div>
    </div>
  );

  // ------------------------------------------- Fase 27: SEUS VIGIAS (27-02) --
  // O bloco que corrige o defeito da fase. Ele existe FORA de qualquer ticker:
  // é isso que faz o vigia gravado aparecer ao abrir a aba, em vez de só
  // aparecer com o ativo dele selecionado (27-CONTEXT, defeito 2).
  //
  // Duas fontes, dois custos, e a diferença é deliberada:
  //  · `vigias` — o ÍNDICE local da conta. Custo ZERO, sai no mount. Traz o
  //    cadastro (nome que a pessoa escreveu, ticker, data) e NENHUM estado;
  //  · `vigiasVivos` — o estado do dia (`armed`/`streak`). Custo 2, só de
  //    clique.
  //
  // ORDENAÇÃO (decisão do executor, 27-CONTEXT "Em aberto" item 1, herdada do
  // protótipo aprovado pelo Alex): quem disparou primeiro — `armed` na frente,
  // depois sequência, depois antiguidade, depois nome. A tela NÃO reimplementa
  // essa régua: o backend do 27-01 já ordena a listagem por ela
  // (`_ordem_dos_vigias`) e o índice já chega mais-recente-primeiro
  // (`opcoes_vigias.listar`). Uma segunda implementação em JavaScript
  // divergiria da primeira na correção seguinte, em silêncio, com as duas
  // listas parecendo a mesma coisa na tela. Por isso aqui só se ESCOLHE a
  // fonte: com estado medido, a lista do dia (superset, já ordenada); sem
  // estado, o índice (já em antiguidade decrescente).
  const listaDeVigias = (vigiasVivos.dados && Array.isArray(vigiasVivos.dados.vigias))
    ? vigiasVivos.dados.vigias
    : ((vigias.dados && Array.isArray(vigias.dados.vigias)) ? vigias.dados.vigias : []);
  const temEstadoDosVigias = !!(vigiasVivos.dados && Array.isArray(vigiasVivos.dados.vigias));
  const tickersEmCarteira = carteira.map((p) => p.t);
  // Fase 27 (27-02): a posição do ativo escolhido, de onde sai o lastro. Pode
  // não existir — clicar num vigia de ativo que saiu da carteira seleciona um
  // ticker sem posição, e esse é um estado real a exibir, não um erro.
  const posicaoSelecionada = ticker ? carteira.find((p) => p.t === ticker) : null;

  // Fase 33 (33-01, 2026-09-19): o bloco virou componente próprio
  // (`SecaoVigias.jsx`) — comportamento idêntico, zero funcionalidade nova
  // (D-03 do 33-CONTEXT.md). `listaDeVigias`/`temEstadoDosVigias`/
  // `tickersEmCarteira` continuam DERIVADOS aqui (a régua de ordenação é do
  // backend) e descem por prop.

  // ------------------------ Fase 27 (27-05): A LEITURA DO SERVIÇO, SOB CLIQUE --
  //
  // O convite que substitui o disparo automático. Até este plano, escolher um
  // ativo — inclusive tocando num cartão de "Seus vigias", que na tela parece
  // navegação — gastava 3 chamadas do cap sem nenhum controle dizer isso.
  //
  // **Por que ele não mora dentro do bloco "LEITURA DO ATIVO" da cascata**, que
  // é onde o plano o pedia: aquele bloco só é renderizado no ramo 4 (DADOS),
  // que depende de `temLeitura` — ou seja, de a leitura JÁ ter voltado. Um
  // convite para pedir a leitura que só aparece depois de a leitura existir
  // seria inalcançável. Ele é irmão de `blocoVigias`: montado fora da cascata,
  // renderizado logo abaixo do bloco técnico interno (grátis, 27-04), que é a
  // ordem que a Emenda 2 do ADR-027 fixou — o que não custa vem primeiro.
  //
  // Some quando o serviço declarou um estado que o clique não resolve (os
  // quatro códigos acionáveis: não configurado, cota, teto, indisponível). A
  // cascata abaixo já diz o que fazer, e um botão que só pode falhar é pior que
  // botão nenhum — mesma disciplina de `podeCriarSetup`. Erro SEM código
  // (falha pontual da própria leitura) mantém o convite: ali repetir é
  // legítimo, e sem ele a pessoa ficaria sem porta nenhuma.
  const servicoIndisponivel = !!(erro && CODIGOS_ACIONAVEIS.includes(erro.code));
  const podePedirLeitura = !!ticker && !leitura.dados && !leitura.carregando
    && !servicoIndisponivel;
  const blocoLeituraDoServico = (
    <div style={{ marginTop: "14px" }}>
      <Kicker>{cp.opcoesLeituraTitulo || "LEITURA DO ATIVO"}</Kicker>
      <div style={CAIXA}>
        <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
          {cp.opcoesLeituraConvite || ""}
        </div>
        {/* O custo vai DENTRO do controle, na segunda linha do próprio botão —
            mesmo padrão do "Atualizar" dos vigias (27-02). O número sai de
            `CUSTO_DA_ACAO.leitura`, espelho do `_cap_check(uid, 3)` da rota:
            um `3` solto aqui envelheceria em silêncio no dia em que o backend
            mudasse, e é exatamente essa divergência que o guardião reprova. */}
        <button
          onClick={abrirLeitura}
          style={{ ...BOTAO, width: "100%", marginTop: "12px" }}
        >
          <span style={{ display: "block" }}>{cp.opcoesLerNoServico || "Ler no serviço de opções"}</span>
          <span style={CUSTO_NO_BOTAO}>
            {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.leitura)}
          </span>
        </button>
      </div>
    </div>
  );

  const seletor = (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "14px 0 4px" }}>
      {carteira.map((p) => (
        <button
          key={p.t}
          onClick={() => escolherTicker(p.t)}
          aria-pressed={p.t === ticker}
          style={{ minHeight: "44px", padding: "8px 14px", borderRadius: "11px", border: `1px solid ${p.t === ticker ? T.accent : T.borderSubtle}`, background: p.t === ticker ? T.accentTint10 : T.bgPanel, color: p.t === ticker ? T.accent : T.textSecondary, fontWeight: 700, fontSize: "13px" }}
        >
          {p.t}
        </button>
      ))}
    </div>
  );

  // Fase 33 (33-02): o job 1 ("descobrir oportunidades cross-carteira") —
  // frase-ponte + Bloco A + Bloco B — virou componente próprio
  // (`SecaoDescobrir.jsx`). Comportamento idêntico ao que estava inline
  // aqui até a Fase 32 (D-04/D-05/D-07), zero funcionalidade nova além do
  // carimbo de frescor (D-04b, exceção explícita e aprovada). `curadoria`
  // desce como o objeto `ctx.curadoria` INTEIRO — MESMA fonte que a linha
  // de chamada em Posições (D-03: uma fonte, duas leituras), nunca uma
  // segunda instância do hook que a busca.
  const secaoDescobrir = (
    <SecaoDescobrir
      opcoesPorTicker={opcoesPorTicker}
      opcoesPorTickerCarregando={opcoesPorTickerCarregando}
      carteira={carteira}
      curadoria={ctx && ctx.curadoria}
      onAbrir={irParaOperar}
      onExecutar={(cand, o) => ctx.A.executarCandidatoCurado(cand, o)}
      onNarrar={() => ctx.curadoria.narrar(ctx.data && ctx.data.config)}
      onRecarregar={ctx && ctx.curadoria && ctx.curadoria.recarregar}
      operador={!!(ctx && ctx.operador)}
      palette={palette}
      cp={cp}
    />
  );

  // Fase 28 (28-02) — o alternador de sub-aba. Mesma régua visual do
  // `seletor` acima (D2/D3 do 28-CONTEXT: reusar, não inventar): mesmos
  // tokens (`T.accent`/`T.accentTint10`/`T.bgPanel`/`T.borderSubtle`/
  // `T.textSecondary`, já em TOKENS — nenhuma chave nova), mesma métrica
  // (44px de alvo tátil, raio 11px, padding 8/14, peso 700, 13px), mesma
  // afordância (`aria-pressed`, sem `role="tab"` — este app não usa ARIA de
  // tab em lugar nenhum, ver BottomNav em App.jsx).
  const subabas = (
    <div style={{ display: "flex", gap: "8px", margin: "10px 0 4px" }}>
      {[
        { id: "setups", rotulo: cp.opcoesSubabaSetups || "Setups" },
        { id: "operar", rotulo: cp.opcoesSubabaOperar || "Operar" },
      ].map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => setSubaba(s.id)}
          aria-pressed={subaba === s.id}
          style={{ minHeight: "44px", padding: "8px 14px", borderRadius: "11px", border: `1px solid ${subaba === s.id ? T.accent : T.borderSubtle}`, background: subaba === s.id ? T.accentTint10 : T.bgPanel, color: subaba === s.id ? T.accent : T.textSecondary, fontWeight: 700, fontSize: "13px" }}
        >
          {s.rotulo}
        </button>
      ))}
    </div>
  );

  // Fase 34 (34-02): particiona por `ticker` o que fica ACIMA da cascata de
  // estados do serviço — hub (sem ticker) × workspace (com ticker). Nenhum
  // estado novo, nenhuma chamada nova: o ternário sobre `ticker`, logo
  // abaixo no `return`, é a única leitura de estado acrescentada
  // (34-CONTEXT.md, <objective>).
  // Cabecalho e os ramos 1-2 da cascata (carregando/erro) NÃO entram aqui —
  // continuam únicos, acima desta partição, porque nascem verdadeiros mesmo
  // sem ticker (NAV-06, ver comentário no `return`).
  //
  // D-04 (ordem fixa do hub): frase-ponte+Bloco A+Bloco B (já um componente
  // só, SecaoDescobrir) → Meus vigias → seletor. Mesmas props de sempre,
  // nenhuma acrescentada/removida.
  const hubTopo = (
    <>
      {secaoDescobrir}
      <SecaoVigias
        vigias={vigias}
        vigiasVivos={vigiasVivos}
        atualizarVigias={atualizarVigias}
        listaDeVigias={listaDeVigias}
        temEstado={temEstadoDosVigias}
        tickersEmCarteira={tickersEmCarteira}
        ticker={ticker}
        onIr={irParaVigia}
        custos={CUSTO_DA_ACAO}
        cp={cp}
      />
      {carteira.length > 0 ? seletor : null}
    </>
  );

  // D-05/D-03: header fixo do workspace, ligado à MESMA `escolherTicker` que
  // já reseta tese/vencimento/alvo/stop ao fechar o ticker — nenhum segundo
  // caminho de reset (duas implementações do mesmo reset divergiriam na
  // primeira manutenção feita só numa delas). Os dois `ticker ? ... : null`
  // que existiam soltos no `return` (LastroDoAtivo/LeituraInterna) somem
  // AQUI DENTRO porque a guarda subiu de nível: `workspaceTopo` só é
  // escolhido quando `ticker` já é truthy.
  const workspaceTopo = (
    <>
      <WorkspaceHeader ticker={ticker} onVoltar={() => escolherTicker(ticker)} cp={cp} />
      <LastroDoAtivo pos={posicaoSelecionada} cp={cp} />
      <LeituraInterna tecnico={tecnico} cp={cp} />
      {podePedirLeitura ? blocoLeituraDoServico : null}
    </>
  );

  return (
    <section>
      <h1 style={{ fontSize: "22px", fontWeight: 800, margin: "0 0 4px" }}>{cp.tituloOpcoes || "Opções"}</h1>
      <p style={{ fontSize: "13px", color: T.textSecondary, margin: "0 0 14px", lineHeight: 1.5 }}>
        {cp.subtituloOpcoes || ""}
      </p>
      {subabas}

      {subaba !== "setups" ? (
        <SubAbaOperar
          carteira={carteira}
          ticker={ticker}
          posicaoSelecionada={posicaoSelecionada}
          tecnico={tecnico}
          cp={cp}
          ctx={ctx}
          seletor={seletor}
          opcoesPorTicker={opcoesPorTicker}
          opcoesPorTickerCarregando={opcoesPorTickerCarregando}
        />
      ) : (
      <>
      {cabecalho}
      {/* Fase 34 (34-02): o que ficava aqui como sequência plana (frase-
          ponte/Bloco A/Bloco B, vigias, seletor, lastro, leitura interna,
          convite pago) passa a ser escolhido por MODO — `hubTopo` (sem
          ticker) ou `workspaceTopo` (com ticker), ambos definidos acima do
          `return`. Nenhum bloco some, nenhum é duplicado: cada um migrou
          para dentro do fragmento do seu modo, na MESMA ordem relativa de
          antes (D-04 no hub; grátis-antes-do-pago no workspace). */}
      {ticker ? workspaceTopo : hubTopo}

      {/* ------------------------------------------------ 1. CARREGANDO --
          Antes do vazio, sempre: vazio pintado durante a consulta afirma
          "não há nada" sem ninguém ter medido. */}
      {carregando ? (
        <div style={{ marginTop: "14px" }}>
          <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
        </div>
      ) : erro ? (
        /* ------------------------------------------ 2. ERRO / DEGRADAÇÃO --
           Escolhido pelo `code` do backend (ADR-027), nunca por raspagem da
           mensagem. Cada código tem seu estado próprio — nenhum vira tela
           em branco. */
        <div style={{ marginTop: "14px" }}>
          {erro.code === "mcp_nao_configurado" ? (
            <Aviso>{cp.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>
          ) : erro.code === "mcp_cota" || erro.code === "mcp_teto_servico" ? (
            <Aviso>
              {(cp.opcoesCota || ((r) => "Cota esgotada." + (r ? " Reinicia às " + r + "." : "")))(
                erro.detail && erro.detail.reinicia)}
            </Aviso>
          ) : erro.code === "mcp_indisponivel" ? (
            <Aviso>{cp.opcoesIndisponivel || "Serviço de opções sem resposta agora."}</Aviso>
          ) : (
            /* Inclui `mcp_erro_de_tool`: a mensagem já vem multi-linha com
               "Como corrigir:" / "Dica:" do enrichErrorMessage — vai CRUA,
               em nó de texto (React escapa), com pre-wrap. A linha da cota
               vem DEPOIS dela e só quando o backend disse que cobrou. */
            <>
              <Aviso tom="forte">{erro.message}</Aviso>
              <RecusaCobrada erro={erro} cp={cp} />
            </>
          )}
        </div>
      ) : nadaParaMostrar ? (
        /* ------------------------------------------ 3. VAZIO COM MOTIVO --
           Vazio nunca é silêncio. */
        <div style={{ marginTop: "14px", display: "grid", gap: "10px" }}>
          {/* Fase 27 (D2) — carteira vazia tem MOTIVO e CAMINHO. O destino é a
              CARTEIRA e não o Mercado por decisão explícita do Alex
              (27-CONTEXT, D2: "estado vazio com caminho para a carteira"), e a
              aba NÃO cai para a watchlist: lista de interesse não serve de
              lastro. O ramo vem ANTES do `semTicker` porque sem posição nenhuma
              não há ativo a escolher — "escolha um ativo" seria pedir o
              impossível. */}
          {carteira.length === 0 ? (
            <Aviso>
              {cp.opcoesCarteiraVazia || "Esta aba trabalha sobre os ativos que você tem em carteira."}
              <button
                onClick={() => { if (ctx && ctx.goCarteira) ctx.goCarteira(); }}
                style={{ ...BOTAO, width: "100%", marginTop: "12px" }}
              >
                {cp.opcoesIrParaCarteira || "Ir para a Carteira"}
              </button>
            </Aviso>
          ) : semTicker ? (
            <Aviso>{cp.opcoesEscolherAtivo || "Escolha um ativo para ver a leitura."}</Aviso>
          ) : null}
          {semCandles ? (
            <Aviso>
              O serviço não tem candles para este ativo, então não há leitura de
              comportamento para mostrar. Nada foi estimado no lugar.
            </Aviso>
          ) : null}
          {/* Fase 27 (27-05) — o `l &&` é a correção que a saída da leitura do
              efeito tornou obrigatória. "Nenhum setup gravado para este ativo"
              é uma AFIRMAÇÃO sobre o armazém do serviço, e quem a mede é a
              própria leitura. Com a leitura virando clique, ela passa a não
              existir enquanto ninguém pedir — e sem esta guarda a tela diria
              "nenhum setup" sobre um ativo que ela nunca consultou, que é
              exatamente o princípio 4 do CLAUDE.md ao contrário (não inventar
              estado quando a fonte não respondeu). Sem leitura pedida, quem
              fala é o convite acima.

              2026-09-20 (Fase 33, 33-03) — este aviso NÃO é duplicata do
              aviso interno de SecaoSetups.jsx (mesma chave `cp.opcoesSemSetups`,
              de propósito): este aqui fala quando NENHUMA leitura foi pedida
              (ramo "3. VAZIO" da cascata); o de dentro da seção fala quando a
              leitura ACONTECEU e voltou sem setups (ramo "4. DADOS"). São
              medições diferentes, com a MESMA frase porque o resultado que a
              pessoa vê ("nenhum setup") é o mesmo nos dois casos — só o motivo
              muda. Não "limpar" um dos dois como redundante. */}
          {!semTicker && l && setups.length === 0 ? (
            <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
          ) : null}
        </div>
      ) : (
        /* ------------------------------------------------------ 4. DADOS -- */
        <div>
          {/* Fase 33 (33-05, 2026-09-20): job 3 ("analisar um ticker
              manualmente") extraído para SecaoAnalisar.jsx — último dos 5
              jobs a sair. Posição EXATA de hoje: primeiro elemento do ramo
              DADOS, renderizado antes do job 4 logo abaixo. `temLeitura`/
              `semCandles` continuam decididos aqui (o orquestrador é dono do
              estado compartilhado); a seção só recebe o resultado pronto. */}
          <SecaoAnalisar
            ticker={ticker}
            temLeitura={temLeitura}
            semCandles={semCandles}
            behavior={behavior}
            lacunas={l && l.lacunas}
            pregao={pregao}
            expirations={l && l.expirations}
            tese={tese}
            setTese={setTese}
            temTese={temTese}
            vencimento={vencimento}
            setVencimento={setVencimento}
            vencimentos={vencimentos}
            lote={lote}
            setLote={setLote}
            loteOk={loteOk}
            proposta={proposta}
            montarProposta={montarProposta}
            cadeia={cadeia}
            operaveis={operaveis}
            abrirCadeia={abrirCadeia}
            abrirOperaveis={abrirOperaveis}
            custos={CUSTO_DA_ACAO}
            cp={cp}
            palette={palette}
          />

          {temLeitura ? (
            /* Fase 33 (33-04): job 4 ("comparar os vencimentos"), extraído
                para SecaoComparar.jsx. Posição EXATA de hoje — logo depois
                do job 3 acima, dentro do MESMO ramo `temLeitura`
                (comportamento idêntico: sem leitura não há de onde a tese
                sair). `tese`/`lote` continuam o MESMO formulário do job 3
                (Pitfall 6); `alvo`/`stop` ficam aqui no orquestrador para
                não resetarem entre re-renders. */
            <SecaoComparar
              ticker={ticker}
              tese={tese}
              temTese={temTese}
              lote={lote}
              loteOk={loteOk}
              alvo={alvo}
              setAlvo={setAlvo}
              stop={stop}
              setStop={setStop}
              vencimentos={vencimentos}
              consultados={consultados}
              chamadasPrevistas={chamadasPrevistas}
              possibilidades={possibilidades}
              verPossibilidades={verPossibilidades}
              custos={CUSTO_DA_ACAO}
              cp={cp}
              palette={palette}
            />
          ) : null}

          {/* Fase 33 (33-03): job 5 ("gerenciar/criar setups salvos"),
              extraído para SecaoSetups.jsx. Posição EXATA de hoje — logo
              depois do bloco "COMPARAR OS VENCIMENTOS" acima, dentro do ramo
              "4. DADOS" da cascata. `naoAvaliado`/`setups`/`grafico` e os 4
              callbacks continuam vindo do hook aqui no orquestrador; a
              seção só recebe o que já foi derivado. */}
          <SecaoSetups
            ticker={ticker}
            setups={setups}
            naoAvaliado={naoAvaliado}
            grafico={grafico}
            abrirGrafico={abrirGrafico}
            fecharGrafico={fecharGrafico}
            setupNovo={setupNovo}
            compilarSetup={compilarSetup}
            confirmarSetup={confirmarSetup}
            desativarSetup={desativarSetup}
            podeCriarSetup={podeCriarSetup}
            custos={CUSTO_DA_ACAO}
            cp={cp}
            ctx={ctx}
            palette={palette}
          />
        </div>
      )}

      <p style={{ marginTop: "20px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.55 }}>
        {cp.opcoesDisclaimer || ""}
      </p>
      </>
      )}
    </section>
  );
}

// -------------------------------------------------------- SUB-ABA OPERAR --
// Fase 28 (28-02). Universo = CARTEIRA (Fase 27 D3), nunca watchlist; o
// `seletor` é recebido POR PROP (o mesmo chip que "Setups" usa, não uma
// segunda implementação) para que trocar de sub-aba nunca perca o ativo
// escolhido — os dois ramos leem o MESMO `ticker` do componente pai.
//
// Decisão de Fase 30 SUPERADA (Fase 32, 32-04, 2026-09-16): o parágrafo
// abaixo dizia que o ramo multi-candidato NÃO seria replicado aqui — essa
// lacuna foi fechada nesta fase. `PropostaDaPosicao` (App.jsx) morreu; o
// ramo de N candidatos que só existia nela foi PORTADO para
// este componente (ver 32-04-PLAN.md, decisão arquitetural B): quando a
// proposta traz mais de um candidato, os N aparecem lado a lado via
// `CandidatoOpcao` (reusado verbatim, não recriado), com o MESMO
// `aceitarCandidato` de `useAceiteLastreado` para todos — sem regressão de
// MULTI-02. Candidato único continua caindo em `PropostaLastreada`, como
// sempre. O texto histórico abaixo (AtivoCard nunca teve seletor de N
// candidatos) segue válido — só o "aqui" mudou de resposta.
function SubAbaOperar({
  carteira, ticker, posicaoSelecionada, tecnico, cp, ctx, seletor,
  opcoesPorTicker, opcoesPorTickerCarregando,
}) {
  const store = ctx && ctx.store;
  const A = ctx && ctx.A;
  // Fonte única de appMode (FIX-C21) — nunca redevirar de ctx.data.config.
  const operador = !!(ctx && ctx.operador);

  // Hook chamado incondicionalmente, antes de qualquer return (regra dos
  // hooks) — mesmo com ticker vazio, ele só fica ocioso.
  const { busy, aceitarCandidato, fecharLastreada } = useAceiteLastreado({ A, cp, ticker });

  // 2026-09-20, Fase 33 (33-05), fold-in D-04a
  // (`.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`):
  // o par gate→proposta NÃO sumiu, mudou de dono. Antes, esta função tinha
  // dois `useEffect` chamando `store.optionsGate(ticker)`/
  // `store.optionsProposta(ticker, true)` toda vez que o ticker mudava — a
  // MESMA busca que `useOpcoesPropostas(store, carteira.map((p) => p.t))`
  // (topo de OpcoesScreen.jsx) já faz para TODA a carteira, com a MESMA
  // guarda (`gate && gate.liquida`) e o MESMO `multiperna: true`. O universo
  // do fan-out é exatamente a carteira de onde este `ticker` é escolhido —
  // ele está sempre coberto. A rota é interna e de custo ZERO (ADR-027
  // §3.3); o que se ganha não é cota de MCP, é uma busca a menos e uma fonte
  // só para os dois destinos da aba (Setups já lia o fan-out; Operar refazia
  // a mesma pergunta).
  const entrada = opcoesPorTicker[ticker] || null;
  const gate = entrada && entrada.gate;
  const prop = entrada && entrada.proposta;
  // "Ainda não varrido" é o estado correto quando o fan-out do topo ainda não
  // respondeu para este ticker — NUNCA um fallback de fetch local (seria a
  // segunda fonte que a regra 3 do guardião existe para impedir).
  const carregandoGate = opcoesPorTickerCarregando && !entrada;

  // Fórmula de App.jsx (PropostaDaPosicao, aposentada — Fase 32/32-04): a
  // posição de opções já ABERTA que casa com o candidato principal da
  // proposta, para o CTA virar "fechar" em vez de "abrir". Esta é agora a
  // ÚNICA implementação (App.jsx tinha uma irmã idêntica dentro de
  // PropostaDaPosicao; morreu junto com o componente para as duas nunca
  // mais divergirem — ver 32-04-PLAN.md, "Duplicações resolvidas").
  const myOptionPositions = ((ctx && ctx.data && ctx.data.optionPositions) || []).filter((p) => p.underlying === ticker);
  const posAberta = (prop && prop.proposta)
    ? myOptionPositions.find((p) => p.id === prop.proposta.contractSymbol) || null
    : null;

  // Fase 32 (32-04, MULTI-02 portado de PropostaDaPosicao/App.jsx): quando a
  // proposta traz mais de um candidato (ex.: venda coberta E put de proteção
  // sobre a MESMA posição), os dois aparecem lado a lado em vez de o motor
  // escolher um só por trás das cenas. `candidatos` é SEMPRE array (default
  // [] no servidor) — a mesma guarda `Array.isArray` de PropostaDaPosicao.
  const candidatos = Array.isArray(prop && prop.candidatos) ? prop.candidatos : [];
  const multi = candidatos.length > 1;

  return (
    <>
      <p style={{ fontSize: "13px", color: T.textSecondary, margin: "0 0 14px", lineHeight: 1.5 }}>
        {cp.opcoesOperarIntro || ""}
      </p>
      {carteira.length === 0 ? (
        // Fase 27 D2 — carteira vazia tem MOTIVO e CAMINHO, e o destino é a
        // Carteira, nunca a watchlist. Reuso verbatim do mesmo bloco da
        // sub-aba Setups (chaves já existentes, nenhuma nova).
        <Aviso>
          {cp.opcoesCarteiraVazia || "Esta aba trabalha sobre os ativos que você tem em carteira."}
          <button
            onClick={() => { if (ctx && ctx.goCarteira) ctx.goCarteira(); }}
            style={{ ...BOTAO, width: "100%", marginTop: "12px" }}
          >
            {cp.opcoesIrParaCarteira || "Ir para a Carteira"}
          </button>
        </Aviso>
      ) : (
        <>
          {seletor}
          {!ticker ? (
            <Aviso>{cp.opcoesOperarEscolherPosicao || "Escolha uma posição para ver a proposta."}</Aviso>
          ) : (
            <>
              <LastroDoAtivo pos={posicaoSelecionada} cp={cp} />
              <LeituraInterna tecnico={tecnico} cp={cp} />
              {carregandoGate ? (
                <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
              ) : !gate || !gate.liquida ? (
                <Aviso>{(cp.opcoesOperarSemLiquidez || ((t) => "Sem liquidez confirmada para " + t + " agora."))(ticker)}</Aviso>
              ) : multi ? (
                <>
                  {/* Fase 32 (32-04, MULTI-02 portado): dois (ou mais)
                      candidatos disputam a MESMA decisão sobre a MESMA
                      posição — largura fixa e igual entre eles (vem de
                      dentro de CandidatoOpcao) porque um cartão maior que o
                      outro passaria peso visual diferente para a mesma
                      escolha (princípio 9 do CLAUDE.md, mesma razão já
                      registrada em App.jsx quando este ramo vivia em
                      PropostaDaPosicao). O aceite continua exclusivo por
                      rodada: todos os candidatos usam o MESMO
                      `aceitarCandidato` de `useAceiteLastreado` — não existe
                      (nem é criado aqui) nenhuma trava nova na UI; a
                      exclusividade é garantida pelo motor no backend. */}
                  <div style={carouselTrackStyle({ marginTop: "11px", gap: "10px", scrollbarWidth: "none", paddingBottom: "2px" })}>
                    {candidatos.map((c) => (
                      <CandidatoOpcao
                        key={c.tipo + "-" + (c.contractSymbol || "collar")}
                        p={c}
                        r={prop}
                        cp={cp}
                        operador={operador}
                        busy={busy}
                        onAceitar={aceitarCandidato}
                        onVerbeteLiquidez={(dados) => { if (A && A.abrirVerbete) A.abrirVerbete("liquidez-opcao", dados); }}
                      />
                    ))}
                  </div>
                  <FonteDoDadoProposta r={prop} cp={cp} />
                </>
              ) : (
                <PropostaLastreada
                  r={prop}
                  operador={operador}
                  cp={cp}
                  busy={busy}
                  onAbrir={() => aceitarCandidato(prop && prop.proposta)}
                  onFechar={() => fecharLastreada(prop)}
                  posAberta={posAberta}
                  onVerbeteLiquidez={(dados) => { if (A && A.abrirVerbete) A.abrirVerbete("liquidez-opcao", dados); }}
                />
              )}
            </>
          )}
        </>
      )}
    </>
  );
}

// Fase 33 (33-01, 2026-09-19): `ErroDoMcp`/`RecusaCobrada` migraram para
// `uiOpcoes.jsx` (import no topo do arquivo) — uma implementação só,
// reusada por esta tela e pelas seções job-to-be-done novas.

// Fase 27 (27-02) — o LASTRO LIVRE do ativo escolhido.
//
// Três informações, todas derivadas da posição que já está no `ctx`: quantas
// ações estão livres para lastro, quantas já estão travadas (e por quê) e
// quantos contratos isso permite. Nenhuma chamada nova.
//
// A subtração NÃO acontece aqui: `qtyLivre` vem de `finance.js`, fonte única
// do front e gêmea de `store.qty_livre`. Uma segunda implementação divergiria
// da primeira na correção seguinte — com o mesmo nome na tela, e em silêncio.
//
// Ausência tem MOTIVO (princípio 4 do CLAUDE.md): posição sem `qty` legível
// mostra travessão e o porquê, nunca `0`. Zero aqui seria lido como "você não
// tem lastro", que é afirmação diferente de "não sei quanto você tem".
function LastroDoAtivo({ pos, cp }) {
  const c = cp || {};
  const qtd = ehNum(pos && pos.qty) ? pos.qty : null;
  const livres = ehNum(qtd) ? qtyLivre(pos) : null;
  const contratos = ehNum(livres) ? Math.floor(livres / ACOES_POR_CONTRATO) : null;
  // Travadas só aparecem quando existem: uma linha dizendo "0 travadas" seria
  // ruído sobre o caso normal.
  const travadas = (ehNum(pos && pos.qtyTravada) && pos.qtyTravada > 0) ? pos.qtyTravada : null;
  return (
    <div style={{ ...CAIXA, marginTop: "10px" }}>
      <div style={{ fontSize: "12.5px", color: T.textPrimary, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
        {ehNum(livres)
          ? (c.opcoesLastroLivre || ((l, k) => l + " livre(s) · " + k + " contrato(s)"))(livres, contratos)
          : "— " + (c.opcoesLastroSemDado || "")}
      </div>
      {ehNum(travadas) ? (
        <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "5px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
          {(c.opcoesLastroTravado || ((t) => t + " travada(s)"))(travadas)}
        </div>
      ) : null}
      <div style={AJUDA}>{c.opcoesLastroAjuda || ""}</div>
    </div>
  );
}

// Fase 27 (27-04) — A LEITURA TÉCNICA INTERNA DO ATIVO (D1 do 27-CONTEXT).
//
// Primeiro bloco que a pessoa vê depois de escolher um ativo, e o único que
// responde de GRAÇA: tendência, volatilidade, suporte/resistência e a régua
// de sete pregões saem do motor determinístico do próprio Boris+
// (`/api/options/tecnico/{ticker}`, 27-03) — o MESMO que alimenta Radar e
// Watchlist. Sem ele, escolher um ativo continuaria só tendo resposta paga.
//
// **Independente do bloco do serviço, nos DOIS sentidos.** Ele é renderizado
// fora da cascata de estados do MCP de propósito: se o serviço de opções
// estiver fora do ar ou não configurado, esta leitura continua aparecendo (é
// justamente quando ela mais vale); e se ela degradar, a leitura do serviço e
// os vigias continuam na tela. Duas fontes, dois carimbos, nenhuma
// escondendo a outra — é o que a Emenda 2 do ADR-027 aceitou por escrito.
//
// Nenhum número é calculado aqui. A régua de regime também não é derivada na
// tela: ela vem pronta do backend, que a monta chamando `regime.classificar`
// um pregão por vez. Uma segunda régua em JavaScript divergiria da primeira
// na correção seguinte — é a classe de defeito que o Snapshot Técnico Único
// existe para matar.
//
// Em que média o filtro de direção se apoiou. Tabela de campo↔rótulo local,
// como `ROTULO_LEITURA`: é vocabulário técnico idêntico nos dois modos (o
// número da janela não muda de nome na mesa), e o que tem voz por modo — a
// ressalva de confiabilidade — mora no `copy.js`.
const ROTULO_BASE = {
  sma200: "média de 200 pregões",
  sma50: "média de 50 pregões",
};

// Preço do nível MAIS a distância até ele, quando as duas coisas existem.
// Sem preço, travessão: um nível sem valor não vira "0" nem some da lista, e
// a distância sozinha não é nível nenhum.
const nivelComDistancia = (preco, distanciaPct) => (ehNum(preco)
  ? fmt(preco) + (ehNum(distanciaPct) ? " · " + pct(distanciaPct, 1) : "")
  : "—");

function LeituraInterna({ tecnico, cp }) {
  const c = cp || {};
  const t = tecnico || {};
  const dados = t.dados;
  // Sem pedido em curso, sem erro e sem dado não há bloco: um quadro vazio
  // com título seria lido como "este ativo não tem leitura técnica", que é
  // afirmação diferente de "ainda não perguntei".
  if (!t.carregando && !t.erro && !dados) return null;

  const tend = (dados && dados.tendencia) || {};
  const vol = (dados && dados.volatilidade) || {};
  const niveis = (dados && dados.niveis) || {};
  const carimbo = (dados && dados.carimbo) || {};
  const rotuloRegime = ((c.opcoesRegimeRotulo || {})[tend.regime]) || "—";
  const rotuloForca = ((c.opcoesForcaRotulo || {})[tend.forca]) || null;
  // O selo de gratuidade é DERIVADO da resposta, nunca escrito fixo: o dia em
  // que esta rota passar a custar, ele some sozinho (T-27-19).
  const semCusto = !!dados && dados.custoMcp === 0;
  // A régua só é desenhada com segmento MEDIDO. Sem nenhum, quem fala é o
  // motivo do backend — faixa vazia seria lida como "a semana inteira
  // indefinida", que é outra afirmação.
  const regua = (dados && dados.regua) || null;
  const temRegua = !!(regua && Array.isArray(regua.itens) && regua.itens.length);
  const motivoDaRegua = (regua && typeof regua.motivo === "string" && regua.motivo) || "";
  // Motivos de ausência, do backend e VERBATIM. Cada bloco traz o seu quando
  // o insumo não existe; juntá-los no rodapé é o mesmo desenho de
  // `LacunasDaLeitura` — explicar a ausência sem preencher o número.
  const motivos = [tend.motivo, vol.motivo, niveis.motivo, carimbo.motivo]
    .filter((m) => typeof m === "string" && m);

  return (
    <>
      <Kicker>{c.opcoesInternaTitulo || "LEITURA TÉCNICA DO ATIVO"}</Kicker>
      {t.carregando ? (
        <Aviso>{c.opcoesInternaCarregando || "Calculando a leitura técnica no próprio app…"}</Aviso>
      ) : t.erro ? (
        <>
          <Aviso tom="forte">{(t.erro && t.erro.message) || "—"}</Aviso>
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
            {c.opcoesInternaErro || ""}
          </div>
        </>
      ) : (
        <>
          <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "4px 14px 10px", background: T.bgPanel }}>
            <Linha rotulo="Tendência" valor={rotuloRegime} />
            <Linha rotulo="Força (ADX 14)" valor={rotuloForca ? rotuloForca + " · " + fmt(tend.adx14, 1) : "—"} />
            <Linha rotulo="Base do filtro" valor={ROTULO_BASE[tend.base] || "—"} />
            {/* ATENÇÃO À UNIDADE — o erro de 10× mora aqui.
                `hv21Pct`/`hv63Pct` deste bloco vêm em PERCENTUAL (31,4 = 31,4%)
                e o contrato declara `unidade: "pct"`; o `behavior.hv21` do
                serviço MCP, exibido no bloco "LEITURA DO ATIVO" logo abaixo,
                vem em FRAÇÃO (0,314) e continua passando por `fracPct`. Os
                dois ficam no MESMO ecrã. Por isso o formatador não é fixo: ele
                é ESCOLHIDO pela unidade que a própria resposta declara, e
                unidade que o app não conhece vira travessão com motivo, nunca
                palpite (`unidades.js`). */}
            <Linha rotulo="HV 21" valor={formatarVolatilidade(vol.hv21Pct, vol.unidade)} />
            <Linha rotulo="HV 63" valor={formatarVolatilidade(vol.hv63Pct, vol.unidade)} />
            <Linha rotulo="Suporte mais próximo" valor={nivelComDistancia(niveis.nearestSupport, niveis.distanceToSupportPct)} />
            <Linha rotulo="Resistência mais próxima" valor={nivelComDistancia(niveis.nearestResistance, niveis.distanceToResistancePct)} />

            {/* A régua vem LOGO ABAIXO da linha de tendência e das demais: é
                ali que a pergunta "mudou esta semana?" nasce. Ela lê
                `dados.regua`, o MESMO objeto de que sai a linha de tendência
                (`dados.tendencia`) — o último segmento e a linha dizem o mesmo
                regime porque vêm da mesma resposta, classificada uma única vez
                no backend. A tela não deriva regime em lugar nenhum. */}
            {temRegua ? (
              <ReguaRegime regua={dados.regua} cp={cp} />
            ) : (
              <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "8px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                {c.opcoesReguaSemDados || ""}
                {motivoDaRegua ? "\n" + motivoDaRegua : ""}
              </div>
            )}
          </div>

          {/* Ressalva, NÃO erro: o valor acima continua valendo. O que ela diz
              é em que janela ele se apoiou — esconder o número seria pior. */}
          {tend.confiavel === false ? (
            <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
              {c.opcoesRegimeNaoConfiavel || ""}
            </div>
          ) : null}

          {motivos.map((m, i) => (
            <div key={i} style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "4px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
              {m}
            </div>
          ))}

          {/* Carimbo (princípio 3): de qual pregão é a leitura e de onde veio a
              série. Fonte ausente vira travessão dentro da própria frase — um
              nome de fonte por default é a mentira que o cabeçalho da aba já
              corrigiu uma vez ("Fonte: —"). */}
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px", lineHeight: 1.5 }}>
            {(c.opcoesInternaCarimbo || ((a, f) => "Pregão: " + (a || "—") + " · fonte: " + (f || "—")))(
              carimbo.asOf, carimbo.source)}
          </div>
          {semCusto ? (
            <div style={{ display: "inline-block", marginTop: "6px", fontSize: "11px", fontWeight: 700, color: T.textSecondary, border: `1px solid ${T.borderSubtle}`, borderRadius: "999px", padding: "3px 9px" }}>
              {c.opcoesSemCusto || ""}
            </div>
          ) : null}
        </>
      )}
    </>
  );
}

// Fase 33 (33-01, 2026-09-19): `CartaoDeVigia` migrou para dentro de
// `SecaoVigias.jsx` — uso exclusivo dele, nenhum outro consumidor no app.

// Fase 33 (33-05, 2026-09-20): `Pernas`/`TabelaDeOpcoes` migraram para dentro
// de `SecaoAnalisar.jsx` — único consumidor de cada uma (a tabela de pernas
// da proposta e as tabelas de cadeia/operáveis, todas dentro do job 3),
// nenhum outro lugar de `web/src/opcoes/` as chama.

// Fase 33 (33-04): `Cenarios` migrou para dentro de SecaoComparar.jsx — era o
// único consumidor (o mapa de "COMPARAR OS VENCIMENTOS"), então não virou
// primitivo compartilhado em uiOpcoes.jsx.

// Códigos de degradação do ADR-027 que dizem à pessoa O QUE FAZER ("não
// configurado", "sem cota", "fora do ar"). Um erro SEM código conhecido (ex.:
// 404 genérico de rota) não carrega essa informação. Declarado no fim do
// arquivo (não antes do componente) para não empurrar a string literal
// "mcp_nao_configurado" para antes do primeiro uso real dela na cadeia de
// estados (carregando → erro → vazio → dados) — `function`/`const` de módulo
// já estão avaliados quando o componente roda, independente da ordem física.
const CODIGOS_ACIONAVEIS = ["mcp_nao_configurado", "mcp_cota", "mcp_teto_servico", "mcp_indisponivel"];

// Achado ao vivo (2026-09-10): `leitura.erro || status.erro` deixava o 404 da
// leitura (que, até a Fase 27 (27-05), disparava sempre que a pessoa escolhia
// um ticker — hoje ela só sai do botão "Ler no serviço", e o `leitura.erro` só
// existe depois desse clique) mascarar o `mcp_nao_configurado` do `/status` — que é
// o único dos dois que diz o que fazer. Escolha por ACIONABILIDADE: erro COM
// `code` conhecido vence erro SEM código, venha de onde vier; com os dois
// codificados (ou os dois sem código), a leitura vence — é a chamada que a
// pessoa disparou ao escolher o ticker.
function escolherErroOpcoes(erroLeitura, erroStatus) {
  const acionavel = (e) => !!(e && CODIGOS_ACIONAVEIS.includes(e.code));
  if (!erroLeitura) return erroStatus;
  if (!erroStatus) return erroLeitura;
  if (acionavel(erroStatus) && !acionavel(erroLeitura)) return erroStatus;
  return erroLeitura;
}

// Achado ao vivo (2026-09-10, primeira leitura real de PETR4/VALE3 em
// produção): `(l && l.frescor) || (status.dados && status.dados.frescor)`
// deixava o frescor da LEITURA vencer sempre — mas sem setups gravados
// (`evaluate_setups` nem é chamada) `_frescor_da_avaliacao` corretamente
// devolve `{ medido: false, bloqueia: true }` (ela não tem de onde medir; e
// "não medido" nunca pode passar por "em dia", ADR-027 Decisão 8). Esse
// objeto NÃO É falsy — o `||` nunca cai para o `/status`, que MEDIU de
// verdade via `check_data_freshness`. A informação que não sabe mascarava a
// que sabe. Mesma classe do defeito 2 corrigido hoje em 260910-d57
// (`escolherErroOpcoes`): escolha por QUALIDADE da informação, não por
// ORIGEM/ordem de chamada. `medido === true` vence `medido !== true`, venha
// de onde vier; empate (os dois medidos, ou nenhum medido) mantém a
// leitura — é a chamada que a pessoa disparou ao escolher o ticker; `null`
// de um lado nunca vence objeto do outro.
function escolherFrescor(frescorLeitura, frescorStatus) {
  const medido = (f) => !!(f && f.medido === true);
  if (!frescorLeitura) return frescorStatus || null;
  if (!frescorStatus) return frescorLeitura;
  if (medido(frescorStatus) && !medido(frescorLeitura)) return frescorStatus;
  return frescorLeitura;
}
