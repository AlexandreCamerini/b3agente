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
import { useState, useEffect } from "react";
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
import SetupChart from "./SetupChart.jsx";
import PayoffChart from "./PayoffChart.jsx";
import CriarSetup, { BotaoDesativar } from "./CriarSetup.jsx";
// Fase 28 (28-02): módulo terceiro do 28-01 — nenhum import de `App.jsx`
// aqui (isolamento ADR-027 Decisão 3 intacto).
import PropostaLastreada, { useAceiteLastreado } from "./PropostaLastreada.jsx";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root` — padrão de
// `pet/BorisChat.jsx`. Zero import de `App.jsx` (seria ciclo).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const pct = (v, casas = 2) => (ehNum(v) ? fmt(v, casas) + "%" : "—");
// `hv21`/`hv63` chegam como FRAÇÃO (0,31 = 31%). A conversão para % é
// formatação da mesma grandeza, não conta nova — é exatamente como o portal
// do próprio serviço a exibe. Sem valor, travessão.
const fracPct = (v) => (ehNum(v) ? fmt(v * 100, 1) + "%" : "—");
const txt = (v) => (typeof v === "string" && v ? v : "—");
// `range_63_sessions` chega SEMPRE como dicionário — com os dois extremos
// nulos quando a janela de 63 pregões não fechou. Exibi-lo sem esta checagem
// produzia "— – —", que é travessão travestido de faixa: parece um intervalo
// que o app não soube formatar, quando é ausência do dado (24-11). Ausência é
// UM travessão, e o porquê dela aparece no rodapé do bloco.
const faixa = (v) => ((v && (ehNum(v.lowest) || ehNum(v.highest)))
  ? fmt(v.lowest) + " – " + fmt(v.highest) : "—");

function Linha({ rotulo, valor }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
      <span style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</span>
      <span style={{ fontSize: "12.5px", color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{valor}</span>
    </div>
  );
}

// aba-opcoes 24-06 (achado F-01): a razão ganho/perda que o critério 1 do
// ROADMAP enumera e a Fase 24 tinha perdido no planejamento.
//
// Ela chega PRONTA do backend (`_razao_ganho_perda`), adimensional: aqui não
// há divisão, não há lote e não há fallback numérico. Sem `valor`, o que
// aparece é o MOTIVO — e ele ocupa a linha inteira, com quebra, porque é ele
// que impede a leitura errada e não pode ser cortado em 375 px. Travessão
// mudo seria "o app não calculou"; um número seria pior, porque a pessoa
// compara 2,3 com 1,5 e decide.
function RazaoGanhoPerda({ razao, cp }) {
  if (!razao) return null;
  const rotulo = cp.opcoesRazaoRotulo || "Razão ganho/perda";
  return (
    <div>
      {ehNum(razao.valor) ? (
        <Linha rotulo={rotulo} valor={"1 : " + fmt(razao.valor)} />
      ) : (
        <div style={{ padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</div>
          <div style={{ fontSize: "12.5px", color: T.textPrimary, marginTop: "3px", whiteSpace: "pre-wrap", lineHeight: 1.45 }}>
            {razao.motivo || "—"}
          </div>
        </div>
      )}
      <div style={AJUDA}>{cp.opcoesRazaoAjuda || ""}</div>
    </div>
  );
}

// aba-opcoes 24-11 (achado ao vivo 2026-09-11): a LEITURA DO ATIVO de PETR4
// mostrava travessão em cinco campos sem dizer por quê — a pessoa não sabe se
// o app quebrou, se o ativo é estranho ou se falta dado (princípio 9).
//
// UM mapa só de rótulo↔campo, aqui, para que a explicação e a tabela falem o
// MESMO vocabulário: dois mapas divergiriam no primeiro rótulo renomeado, e a
// frase passaria a nomear um campo que a tabela não mostra com esse nome.
const ROTULO_LEITURA = {
  trend: "Tendência",
  rsi14: "RSI 14",
  hv21: "HV 21",
  hv63: "HV 63",
  sma63: "Média de 63",
  distance_from_sma21_pct: "Distância da média 21",
  distance_from_sma63_pct: "Distância da média 63",
  range_63_sessions: "Faixa de 63 pregões",
  change_21_sessions_pct: "Variação em 21 pregões",
};

// Os motivos vão AGRUPADOS no rodapé do bloco, ao lado do carimbo do pregão —
// um por motivo, com os campos afetados nomeados. Repetir a explicação nas
// cinco linhas da tabela empurraria para fora da tela os números que VIERAM,
// que é o oposto do que o achado pede.
//
// O motivo é do backend e vai VERBATIM: aqui só se juntam os rótulos, e a
// gramática (a vírgula, o "e", o singular/plural) mora no `copy.js`, com voz
// por modo. Sem `lacunas`, nada é renderizado — estado normal é silêncio.
function LacunasDaLeitura({ lacunas, cp }) {
  const itens = (Array.isArray(lacunas) ? lacunas : []).filter(
    (x) => x && x.motivo && Array.isArray(x.campos) && x.campos.length);
  if (!itens.length) return null;
  return (
    <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "4px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
      {itens.map((x, i) => (
        <div key={i} style={{ marginTop: i ? "3px" : 0 }}>
          {cp.opcoesLacuna
            ? cp.opcoesLacuna(x.campos.map((c) => ROTULO_LEITURA[c] || c), x.motivo)
            : x.motivo}
        </div>
      ))}
    </div>
  );
}

function Kicker({ children }) {
  return (
    <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", color: T.textMuted, margin: "18px 0 8px" }}>
      {children}
    </div>
  );
}

function Aviso({ children, tom }) {
  return (
    <div style={{ border: `1px solid ${tom === "forte" ? T.negative : T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel, color: T.textSecondary, fontSize: "12.5px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

// aba-opcoes F3 (plano 24-02). Alvo de toque de 44 px em TODO botão novo —
// os dois estilos abaixo existem para que nenhum deles possa esquecer disso.
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
// Botão desabilitado FICA VISÍVEL, em vez de sumir: a pessoa precisa ver que
// a ação existe e o que falta para liberá-la (tese, lote) — botão que some
// vira "o app não faz isso".
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);

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
const CAMPO = {
  minHeight: "44px", width: "100%", boxSizing: "border-box", padding: "8px 10px",
  borderRadius: "10px", border: `1px solid ${T.borderSubtle}`,
  background: T.bgBase, color: T.textPrimary, fontSize: "14px",
};
const ROTULO = { display: "block", fontSize: "12.5px", color: T.textSecondary, margin: "12px 0 4px" };
const AJUDA = { fontSize: "11px", color: T.textMuted, marginTop: "4px", lineHeight: 1.45 };

// Rolagem horizontal no CONTAINER da tabela, nunca no `body`: a cadeia tem
// mais colunas do que cabem em 375 px, e empurrar a página inteira para o
// lado quebra a leitura de tudo o mais.
const ROLAGEM = { overflowX: "auto", WebkitOverflowScrolling: "touch", margin: "8px 0" };
const TABELA = { borderCollapse: "collapse", fontSize: "12px", minWidth: "460px", width: "100%" };
const TH = { textAlign: "left", padding: "6px 8px", color: T.textMuted, fontWeight: 700, borderBottom: `1px solid ${T.borderSubtle}`, whiteSpace: "nowrap" };
const TD = { padding: "6px 8px", color: T.textSecondary, borderBottom: `1px solid ${T.borderFaint}`, whiteSpace: "nowrap", fontVariantNumeric: "tabular-nums" };

// `side` do serviço descreve a PERNA da estrutura ("esta trava compra o
// strike 38 e vende o 40"), não uma instrução a quem lê — por isso vale nos
// dois modos, inclusive no Estudo. O que o Estudo não tem é veredito em voz
// de ordem, e isso continua valendo.
const LADO = { buy: "compra", sell: "venda" };

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
  const [painel, setPainel] = useState("");  // "" | "cadeia" | "operaveis"

  // Trocar de ativo apaga a TESE e os preços: tese é juízo sobre AQUELE
  // ativo, e um alvo de 41,00 herdado de outro papel seria um cenário falso.
  // O lote fica — ele é da pessoa, não do ativo.
  const escolherTicker = (t) => {
    setTicker(t === ticker ? "" : t);
    setTese(""); setVencimento(""); setAlvo(""); setStop(""); setPainel("");
  };

  // Fase 27: o cartão do vigia NAVEGA; ele não alterna. `escolherTicker` é
  // toggle — é o que o chip precisa, para poder desselecionar —, e reusá-lo
  // cru aqui faria clicar no vigia do ativo JÁ ABERTO fechar o ativo, o
  // oposto de "me leve até ele" (SC-1: não precisar lembrar em qual ativo
  // criei o vigia).
  const irParaVigia = (t) => { if (t && t !== ticker) escolherTicker(t); };

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
  // Preço não existente é AUSÊNCIA: `undefined` some do JSON e o cenário
  // simplesmente não é pedido. Zero seria um preço — e um cenário de ativo
  // valendo zero.
  const alvoNum = ehNum(num(alvo)) && num(alvo) > 0 ? num(alvo) : undefined;
  const stopNum = ehNum(num(stop)) && num(stop) > 0 ? num(stop) : undefined;
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

  const blocoVigias = (
    <div>
      <Kicker>{cp.opcoesVigiasTitulo || "SEUS VIGIAS"}</Kicker>
      {/* carregando → erro → vazio com motivo → dados, a mesma cascata do
          resto da tela: lista vazia pintada durante a consulta afirmaria
          "você não tem vigia" sem ninguém ter medido. */}
      {vigias.carregando ? (
        <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
      ) : vigias.erro ? (
        <ErroDoMcp erro={vigias.erro} cp={cp} />
      ) : listaDeVigias.length === 0 ? (
        <Aviso>{cp.opcoesVigiasVazio || "Nenhum vigia gravado nesta conta ainda."}</Aviso>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {listaDeVigias.map((v, i) => (
            <CartaoDeVigia
              key={(v && v.nomeNoServico ? v.nomeNoServico : "vigia") + "-" + i}
              vigia={v}
              temEstado={temEstadoDosVigias}
              selecionado={!!(v && v.ticker) && v.ticker === ticker}
              naCarteira={!!(v && v.ticker) && tickersEmCarteira.includes(v.ticker)}
              onIr={irParaVigia}
              cp={cp}
            />
          ))}
        </div>
      )}

      {/* O custo vai DENTRO do controle, não ao lado: descobrir que o clique
          custou 2 depois de gastá-las não é aviso, é recibo. Reusa
          `opcoesCustoChamadas` — uma segunda forma de dizer custo criaria dois
          vocabulários para a mesma grandeza. */}
      <button
        onClick={atualizarVigias}
        disabled={vigiasVivos.carregando}
        style={{ ...BOTAO, width: "100%", marginTop: "10px", ...desabilitado(vigiasVivos.carregando) }}
      >
        <span style={{ display: "block" }}>{cp.opcoesVigiasAtualizar || "Atualizar o estado dos vigias"}</span>
        <span style={CUSTO_NO_BOTAO}>
          {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.listarVigias)}
        </span>
      </button>

      {vigiasVivos.carregando ? (
        <div style={{ marginTop: "10px" }}>
          <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
        </div>
      ) : vigiasVivos.erro ? (
        <div style={{ marginTop: "10px" }}>
          <ErroDoMcp erro={vigiasVivos.erro} cp={cp} />
        </div>
      ) : null}
    </div>
  );

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
        />
      ) : (
      <>
      {cabecalho}
      {/* Fase 27 (D4: "vigias antes da carteira"). SEMPRE renderizado, com ou
          sem ativo escolhido — é o que faz a aba abrir com conteúdo em vez de
          abrir vazia, e de graça. */}
      {blocoVigias}
      {carteira.length > 0 ? seletor : null}
      {/* Fase 27 (D4): o lastro livre no cartão, ANTES da tentativa. Hoje este
          número só aparece na mensagem de recusa do backend ("Lastro
          insuficiente: N ação(ões) livres de PETR4"), depois de a pessoa
          tentar — e recusa não é aviso, é recibo. */}
      {ticker ? <LastroDoAtivo pos={posicaoSelecionada} cp={cp} /> : null}
      {/* Fase 27 (27-04, D1): a leitura de GRAÇA vem primeiro; a paga só
          quando a pessoa clica. Fica FORA da cascata de estados do serviço de
          opções de propósito — são fontes independentes, e é exatamente
          quando o MCP está fora do ar que esta leitura mais vale. */}
      {ticker ? <LeituraInterna tecnico={tecnico} cp={cp} /> : null}
      {/* Fase 27 (27-05): e a paga, logo depois, atrás de um clique que diz o
          preço. A ordem é a decisão: grátis primeiro, pago depois. */}
      {podePedirLeitura ? blocoLeituraDoServico : null}

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
              fala é o convite acima. */}
          {!semTicker && l && setups.length === 0 ? (
            <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
          ) : null}
        </div>
      ) : (
        /* ------------------------------------------------------ 4. DADOS -- */
        <div>
          {temLeitura ? (
            <>
              <Kicker>{cp.opcoesLeituraTitulo || "LEITURA DO ATIVO"}</Kicker>
              <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "4px 14px 10px", background: T.bgPanel }}>
                <Linha rotulo="Tendência" valor={txt(behavior.trend)} />
                <Linha rotulo="Fechamento" valor={fmt(behavior.close)} />
                <Linha rotulo="RSI 14" valor={fmt(behavior.rsi14, 1)} />
                <Linha rotulo="HV 21" valor={fracPct(behavior.hv21)} />
                <Linha rotulo="HV 63" valor={fracPct(behavior.hv63)} />
                <Linha rotulo="Distância da média 21" valor={pct(behavior.distance_from_sma21_pct, 1)} />
                <Linha rotulo="Distância da média 63" valor={pct(behavior.distance_from_sma63_pct, 1)} />
                <Linha rotulo="Faixa de 63 pregões" valor={faixa(behavior.range_63_sessions)} />
                <Linha rotulo="Variação em 21 pregões" valor={pct(behavior.change_21_sessions_pct, 1)} />
              </div>
              <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px" }}>
                {"Leitura referente ao pregão de " + (behavior.trading_date || pregao || "—") + "."}
              </div>
              {/* 24-11 — o rodapé continua, e agora diz POR QUE os campos
                  vazios estão vazios. A tabela acima segue com travessão:
                  o objetivo é explicar a ausência, não preenchê-la. */}
              <LacunasDaLeitura lacunas={l && l.lacunas} cp={cp} />
            </>
          ) : semCandles ? (
            <div style={{ marginTop: "14px" }}>
              <Aviso>
                O serviço não tem candles para este ativo — sem leitura de
                comportamento. Os setups abaixo continuam valendo.
              </Aviso>
            </div>
          ) : null}

          {Array.isArray(l && l.expirations) && l.expirations.length > 0 ? (
            <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "10px" }}>
              {"Vencimentos disponíveis: " + l.expirations.join(" · ")}
            </div>
          ) : null}

          {/* ============================================ ANALISAR (F3) --
              Depois da leitura e ANTES dos setups: a ordem da tela é a ordem
              do raciocínio — leio o ativo, vejo o que dá para montar, e só
              então olho os setups que vigiam. Sem leitura não há de onde a
              tese sair, então a seção inteira depende de `temLeitura`. */}
          {temLeitura ? (
            <>
              <Kicker>{cp.opcoesAnalisarTitulo || "O QUE DÁ PARA MONTAR"}</Kicker>
              <div style={CAIXA}>
                {/* Nenhuma tese vem pré-selecionada: o serviço não escolhe
                    direção (é 422 `tese_ausente` sem ela) e a tela não pode
                    escolher no lugar de quem opera. */}
                <div id="opcoes-tese-rotulo" style={{ ...ROTULO, margin: "0 0 6px" }}>
                  {cp.opcoesTeseRotulo || "Qual é a sua tese para este ativo?"}
                </div>
                <div role="group" aria-labelledby="opcoes-tese-rotulo" style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {[["bullish", cp.opcoesTeseAlta || "Alta"],
                    ["bearish", cp.opcoesTeseBaixa || "Baixa"],
                    ["neutral", cp.opcoesTeseNeutra || "Neutra"]].map(([valor, rotulo]) => (
                      <button
                        key={valor}
                        onClick={() => setTese(valor === tese ? "" : valor)}
                        aria-pressed={valor === tese}
                        style={{ ...BOTAO, flex: "1 1 90px", ...(valor === tese ? { borderColor: T.accent, background: T.accentTint10, color: T.accent } : null) }}
                      >
                        {rotulo}
                      </button>
                    ))}
                </div>

                {/* "o serviço escolhe" é o default HONESTO: `propose_option_setups`
                    sem `expiration` decide pelo critério dele, e fingir que
                    fomos nós que escolhemos o primeiro da lista seria a tela
                    assumindo uma decisão que não tomou. */}
                <label htmlFor="opcoes-venc" style={ROTULO}>Vencimento</label>
                <select id="opcoes-venc" value={vencimento} onChange={(ev) => setVencimento(ev.target.value)} style={CAMPO}>
                  <option value="">o serviço escolhe</option>
                  {vencimentos.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>

                <label htmlFor="opcoes-lote" style={ROTULO}>{cp.opcoesLoteRotulo || "Lote (ações)"}</label>
                <input
                  id="opcoes-lote" type="number" step="100" min="100" inputMode="numeric"
                  value={lote} onChange={(ev) => setLote(ev.target.value)}
                  aria-describedby="opcoes-lote-ajuda" style={CAMPO}
                />
                <div id="opcoes-lote-ajuda" style={AJUDA}>{cp.opcoesLoteAjuda || ""}</div>

                {/* Fase 27 (27-05): o custo DENTRO do controle, na segunda
                    linha do próprio botão — mesmo padrão do "Atualizar" dos
                    vigias e do "Ler no serviço". Uma forma só de dizer custo
                    (`opcoesCustoChamadas`) em toda a aba: duas divergiriam na
                    primeira manutenção feita só numa delas. */}
                <button
                  onClick={() => montarProposta({ direction: tese, expiration: vencimento || undefined, lote: loteNum })}
                  disabled={!temTese || !loteOk}
                  style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!temTese || !loteOk) }}
                >
                  <span style={{ display: "block" }}>{cp.opcoesMontarEstrutura || "Montar estrutura"}</span>
                  <span style={CUSTO_NO_BOTAO}>
                    {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.proposta)}
                  </span>
                </button>

                {/* carregando → erro → vazio com motivo → dados */}
                <div style={{ marginTop: "10px" }}>
                  {proposta.carregando ? (
                    <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                  ) : proposta.erro ? (
                    <ErroDoMcp erro={proposta.erro} cp={cp} />
                  ) : proposta.dados && !(proposta.dados.estruturas || []).length ? (
                    <Aviso>
                      {/* Motivo do serviço, VERBATIM. Sem motivo nenhum, a
                          tela diz que não houve motivo — não preenche com um
                          palpite sobre o porquê. */}
                      {proposta.dados.motivo || proposta.dados.nota
                        || "O serviço não montou estrutura para esta tese e não informou o motivo. Nada foi estimado no lugar."}
                    </Aviso>
                  ) : proposta.dados ? (
                    <>
                      <PayoffChart
                        estrutura={proposta.dados.estruturas[0]}
                        emReais={proposta.dados.emReais}
                        cp={cp}
                        palette={palette}
                      />
                      <RazaoGanhoPerda razao={proposta.dados.razaoGanhoPerda} cp={cp} />
                      <Pernas pernas={proposta.dados.estruturas[0].legs} cp={cp} />
                    </>
                  ) : null}
                </div>

                {/* Duas consultas secundárias, cada uma custando 1 chamada.
                    Reabrir o painel refaz o pedido — e o cache L1 do serviço
                    (15 min) devolve sem tocar a rede, sem consumir cap. */}
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "14px" }}>
                  <button
                    onClick={() => { const abrir = painel !== "cadeia"; setPainel(abrir ? "cadeia" : ""); if (abrir) abrirCadeia({ expiration: vencimento || undefined }); }}
                    aria-pressed={painel === "cadeia"}
                    style={{ ...BOTAO, flex: "1 1 150px" }}
                  >
                    <span style={{ display: "block" }}>{cp.opcoesVerCadeia || "Ver a cadeia"}</span>
                    <span style={CUSTO_NO_BOTAO}>
                      {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.cadeia)}
                    </span>
                  </button>
                  <button
                    onClick={() => { const abrir = painel !== "operaveis"; setPainel(abrir ? "operaveis" : ""); if (abrir) abrirOperaveis({ expiration: vencimento || undefined }); }}
                    aria-pressed={painel === "operaveis"}
                    style={{ ...BOTAO, flex: "1 1 150px" }}
                  >
                    <span style={{ display: "block" }}>{cp.opcoesVerOperaveis || "Ver as operáveis"}</span>
                    <span style={CUSTO_NO_BOTAO}>
                      {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.operaveis)}
                    </span>
                  </button>
                </div>

                {painel === "cadeia" ? (
                  <div style={{ marginTop: "10px" }}>
                    {cadeia.carregando ? (
                      <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                    ) : cadeia.erro ? (
                      <ErroDoMcp erro={cadeia.erro} cp={cp} />
                    ) : cadeia.dados && !(cadeia.dados.opcoes || []).length ? (
                      <Aviso>A cadeia deste ativo voltou sem contrato para os filtros pedidos. Nada foi estimado no lugar.</Aviso>
                    ) : cadeia.dados ? (
                      <>
                        <div style={{ fontSize: "11.5px", color: T.textMuted }}>
                          {"Contratos: " + (ehNum(cadeia.dados.retornados) ? cadeia.dados.retornados : "—")
                            + " de " + (ehNum(cadeia.dados.encontrados) ? cadeia.dados.encontrados : "—")}
                        </div>
                        {cadeia.dados.truncado ? (
                          <div style={{ marginTop: "8px" }}>
                            <Aviso>{(cp.opcoesCadeiaTruncada || ((t) => t))(cadeia.dados.truncado)}</Aviso>
                          </div>
                        ) : null}
                        <TabelaDeOpcoes linhas={cadeia.dados.opcoes} />
                        <div style={AJUDA}>{cp.opcoesDeltaAjuda || ""}</div>
                      </>
                    ) : null}
                  </div>
                ) : null}

                {painel === "operaveis" ? (
                  <div style={{ marginTop: "10px" }}>
                    {operaveis.carregando ? (
                      <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                    ) : operaveis.erro ? (
                      <ErroDoMcp erro={operaveis.erro} cp={cp} />
                    ) : operaveis.dados && !(operaveis.dados.opcoes || []).length ? (
                      <Aviso>
                        {/* Peneira vazia NÃO é "não há opções": é "nenhuma
                            passou no critério". Por isso o critério aparece
                            junto — a pessoa precisa saber o que sumiu com os
                            strikes dela. */}
                        {(cp.opcoesCriterioOperaveis || (() => ""))(operaveis.dados.criterioAplicado)}
                        {"\n\nNenhum contrato passou nessa peneira neste ativo."}
                      </Aviso>
                    ) : operaveis.dados ? (
                      <>
                        <div style={{ fontSize: "11.5px", color: T.textSecondary, lineHeight: 1.5 }}>
                          {(cp.opcoesCriterioOperaveis || (() => ""))(operaveis.dados.criterioAplicado)}
                        </div>
                        {operaveis.dados.criterio ? (
                          <div style={{ ...AJUDA, whiteSpace: "pre-wrap" }}>
                            {/* Texto do serviço, verbatim (vem em inglês) —
                                reescrever seria a tela falando pelo serviço. */}
                            {"Como o serviço descreveu a peneira: " + operaveis.dados.criterio}
                          </div>
                        ) : null}
                        <TabelaDeOpcoes linhas={operaveis.dados.opcoes} />
                        <div style={AJUDA}>
                          {ehNum(operaveis.dados.excluidos) ? "Descartados pela peneira: " + operaveis.dados.excluidos + ". " : ""}
                          {cp.opcoesDeltaAjuda || ""}
                        </div>
                        {operaveis.dados.nota ? (
                          <div style={{ ...AJUDA, whiteSpace: "pre-wrap" }}>{operaveis.dados.nota}</div>
                        ) : null}
                      </>
                    ) : null}
                  </div>
                ) : null}
              </div>

              {/* ==================================== POSSIBILIDADES (F3) -- */}
              <Kicker>{cp.opcoesPossibilidadesTitulo || "COMPARAR OS VENCIMENTOS"}</Kicker>
              <div style={CAIXA}>
                {N === 0 ? (
                  <Aviso>{cp.opcoesSemVencimento || "Nenhum vencimento aberto na leitura deste ativo."}</Aviso>
                ) : (
                  <>
                    {/* O custo ANTES do clique. `2 * N + 1` sai dos
                        vencimentos que a leitura já trouxe, sem consultar
                        nada: descobrir o preço depois de pagar não é aviso,
                        é recibo. */}
                    <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
                      {(cp.opcoesCustoChamadas || ((n) => String(n)))(chamadasPrevistas)}
                    </div>
                    {/* Fase 27 (27-02): a COMPOSIÇÃO do custo saiu de
                        `opcoesCustoChamadas` (que agora também serve ao botão
                        dos vigias, cuja conta é outra) e passou a ter chave
                        própria. O número continua vindo da mesma frase de
                        sempre, logo acima. */}
                    <div style={{ ...AJUDA, marginTop: "6px" }}>
                      {cp.opcoesCustoVencimentos || ""}
                    </div>
                    <div style={{ ...AJUDA, marginTop: "6px" }}>
                      {"Vencimentos consultados: " + consultados.join(" · ")}
                      {vencimentos.length > N
                        ? " (os " + N + " primeiros de " + vencimentos.length + ")"
                        : ""}
                    </div>

                    <label htmlFor="opcoes-alvo" style={ROTULO}>{cp.opcoesAlvoRotulo || "Alvo (opcional)"}</label>
                    <input id="opcoes-alvo" type="number" step="0.01" min="0" inputMode="decimal"
                      value={alvo} onChange={(ev) => setAlvo(ev.target.value)} style={CAMPO} />
                    <label htmlFor="opcoes-stop" style={ROTULO}>{cp.opcoesStopRotulo || "Stop (opcional)"}</label>
                    <input id="opcoes-stop" type="number" step="0.01" min="0" inputMode="decimal"
                      value={stop} onChange={(ev) => setStop(ev.target.value)} style={CAMPO} />

                    <button
                      onClick={() => verPossibilidades({
                        direction: tese, lote: loteNum, alvo: alvoNum, stop: stopNum,
                        expirations: consultados,
                      })}
                      disabled={!temTese || !loteOk}
                      style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!temTese || !loteOk) }}
                    >
                      {cp.opcoesVerPossibilidades || "Ver possibilidades"}
                    </button>
                  </>
                )}

                <div style={{ marginTop: "10px" }}>
                  {possibilidades.carregando ? (
                    <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                  ) : possibilidades.erro ? (
                    <ErroDoMcp erro={possibilidades.erro} cp={cp} />
                  ) : possibilidades.dados && !(possibilidades.dados.possibilidades || []).length ? (
                    <Aviso>{possibilidades.dados.motivo || cp.opcoesSemVencimento || ""}</Aviso>
                  ) : possibilidades.dados ? (
                    <div style={{ display: "grid", gap: "10px" }}>
                      {/* Um vencimento que falhou NÃO apaga os outros — é a
                          razão de o backend não abortar o laço, e a lista
                          aqui é uniforme justamente para não precisar testar
                          existência de chave. */}
                      {possibilidades.dados.possibilidades.map((item) => (
                        <div key={item.vencimento}>
                          {item.erro ? (
                            <Aviso tom="forte">{item.vencimento + ": " + item.erro}</Aviso>
                          ) : !item.estrutura ? (
                            <Aviso>
                              {item.vencimento + ": "
                                + (item.motivo || "o serviço não montou estrutura e não informou o motivo.")}
                            </Aviso>
                          ) : (
                            <>
                              <PayoffChart estrutura={item.estrutura} emReais={item.emReais} cp={cp} palette={palette} />
                              <RazaoGanhoPerda razao={item.razaoGanhoPerda} cp={cp} />
                              <Cenarios emReais={item.emReais} cp={cp} />
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>

                {/* Ressalva FIXA, não tooltip opcional: ela acompanha todo
                    número de cenário que a seção mostra. */}
                <div style={{ ...AJUDA, marginTop: "12px" }}>{cp.opcoesSigmaAjuda || ""}</div>
              </div>
            </>
          ) : null}

          <Kicker>{cp.opcoesSetupsTitulo || "SETUPS GRAVADOS"}</Kicker>

          {naoAvaliado ? (
            <div style={{ marginBottom: "10px" }}>
              <Aviso>
                {(cp.opcoesNaoAvaliado || ((m) => "Setups não avaliados hoje." + (m ? " " + m : "")))(
                  naoAvaliado.reason)}
              </Aviso>
            </div>
          ) : null}

          {setups.length === 0 ? (
            <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
          ) : (
            <div style={{ display: "grid", gap: "10px" }}>
              {setups.map((s) => {
                const av = s.avaliacao;
                // Fase 27 (27-02) — DOIS nomes, e confundi-los quebra a tela.
                // A partir do 27-01 a `/leitura` devolve `name` = o nome que a
                // PESSOA escreveu e `nomeNoServico` = a chave real no armazém
                // compartilhado (com o prefixo de 8 hexadecimais da conta).
                // Tudo que VIAJA ao serviço — `/grafico`, `/desativar` — usa
                // `nomeNoServico`; tudo que a pessoa LÊ usa `name`. Mandar o
                // nome sem prefixo ao serviço leva 422 `setup_desconhecido`.
                const chave = s.nomeNoServico || s.name;
                const aberto = grafico.setup === chave;
                return (
                  <div key={chave} style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px 14px", background: T.bgPanel }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "baseline" }}>
                      <div style={{ fontSize: "14px", fontWeight: 700, color: T.textPrimary }}>{s.name}</div>
                      <div style={{ fontSize: "11.5px", color: T.textMuted }}>{"registro: " + txt(s.status)}</div>
                    </div>

                    {av ? (
                      <div style={{ fontSize: "12.5px", color: T.textSecondary, marginTop: "6px" }}>
                        {"avaliação: " + txt(av.status)}
                        {" · armado: " + (s.armed === true ? "sim" : s.armed === false ? "não" : "—")}
                        {" · sequência: " + (ehNum(s.streak) ? s.streak : "—")
                          + "/" + (ehNum(s.required_streak) ? s.required_streak : "—")}
                      </div>
                    ) : (
                      /* Sem avaliação NÃO vira "não armado": ausência de
                         leitura não é leitura negativa. */
                      <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "6px" }}>
                        {"sem avaliação hoje · exige "
                          + (ehNum(s.required_streak) ? s.required_streak : "—")
                          + " pregão(s) seguidos"}
                      </div>
                    )}

                    {Array.isArray(s.conditions) && s.conditions.length > 0 ? (
                      <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none" }}>
                        {s.conditions.map((c, i) => (
                          <li key={i} style={{ fontSize: "12.5px", color: T.textSecondary, padding: "3px 0" }}>
                            <span aria-hidden style={{ marginRight: "6px", color: T.textFaint }}>
                              {c && c.met ? "✓" : "·"}
                            </span>
                            {(c && (c.summary || c.label)) || "—"}
                            <span style={{ color: T.textFaint }}>{c && c.met ? " (atendida)" : " (não atendida)"}</span>
                          </li>
                        ))}
                      </ul>
                    ) : null}

                    {s.backtest_na_criacao && ehNum(s.backtest_na_criacao.disparos) ? (
                      <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "8px" }}>
                        {"Na criação, este setup disparou " + s.backtest_na_criacao.disparos
                          + " vez(es) no histórico. Contagem passada, não expectativa."}
                      </div>
                    ) : null}

                    {/* Fase 27 (27-05): só ABRIR custa (1 chamada); fechar é
                        local. O rótulo de custo acompanha a ação que cobra e
                        some quando o botão vira "Fechar gráfico" — declarar
                        custo numa ação de graça mentiria na outra direção.

                        O custo entra TAMBÉM no `aria-label`: ele SUBSTITUI o
                        texto do botão para quem usa leitor de tela, então um
                        custo que vivesse só no <span> seria invisível
                        justamente para quem não pode conferir na tela. */}
                    <button
                      onClick={() => (aberto ? fecharGrafico() : abrirGrafico(chave))}
                      aria-pressed={aberto}
                      aria-label={(aberto ? "Fechar" : "Ver") + " disparos do setup " + s.name
                        + (aberto ? "" : ". " + (cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.grafico))}
                      style={{ marginTop: "10px", width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}
                    >
                      <span style={{ display: "block" }}>
                        {aberto ? "Fechar gráfico" : (cp.opcoesGraficoTitulo || "Disparos do setup")}
                      </span>
                      {aberto ? null : (
                        <span style={CUSTO_NO_BOTAO}>
                          {(cp.opcoesCustoChamadas || ((n) => String(n)))(CUSTO_DA_ACAO.grafico)}
                        </span>
                      )}
                    </button>

                    {aberto ? (
                      <div style={{ marginTop: "10px" }}>
                        {grafico.carregando ? (
                          <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                        ) : grafico.erro ? (
                          <Aviso tom="forte">{grafico.erro.message}</Aviso>
                        ) : grafico.dados ? (
                          <SetupChart ctx={ctx} grafico={grafico.dados} palette={palette} cp={cp} />
                        ) : null}
                      </div>
                    ) : null}

                    {/* Desativar é ESCRITA: mesma permissão da seção de
                        criação, e em dois toques (ver `BotaoDesativar`). O
                        resultado aparece logo abaixo, na seção de criação —
                        as duas ações compartilham o mesmo trio de estado
                        porque são a mesma conversa com o serviço. */}
                    {podeCriarSetup ? (
                      <BotaoDesativar
                        nome={chave}
                        nomeVisivel={s.name}
                        onDesativar={desativarSetup}
                        ocupado={setupNovo.carregando}
                        custos={CUSTO_DA_ACAO}
                        cp={cp}
                      />
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}

          {/* ======================================== CRIAR SETUP (F5) --
              Depois da lista: criar vem depois de ver o que já existe —
              com a lista acima, a pessoa não grava um segundo vigia para a
              condição que já vigia. A permissão só ESCONDE; quem recusa é o
              backend (ADR-013). */}
          {podeCriarSetup ? (
            <>
              <Kicker>{cp.opcoesCriarTitulo || "CRIAR UM SETUP"}</Kicker>
              {/* Fase 27 (27-05): a tabela de custo chega por PROP, como tudo
                  o mais que este componente recebe. Importá-la de
                  `OpcoesScreen.jsx` criaria uma segunda porta de acoplamento
                  de graça — e `CriarSetup` é deliberadamente um componente sem
                  fonte de dado própria. */}
              <CriarSetup
                ticker={ticker}
                estado={setupNovo}
                onCompilar={compilarSetup}
                onConfirmar={confirmarSetup}
                custos={CUSTO_DA_ACAO}
                cp={cp}
              />
            </>
          ) : null}
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
// Decisão registrada (Fase 30 não redescobrir): o ramo multi-candidato
// (`r.candidatos.length > 1` / `CandidatoOpcao`, hoje só em `App.jsx` dentro
// de `PropostaDaPosicao`) NÃO é replicado aqui. Com multi-candidato,
// `PropostaLastreada` mostra `r.proposta` (o candidato principal que o motor
// devolve) — o mesmo comportamento que `AtivoCard` já tem hoje. Trazer o
// seletor de N candidatos para esta sub-aba exigiria uma quarta cópia do
// padrão visual (App.jsx tem duas: AtivoCard e PropostaDaPosicao), fora de
// escopo deste plano.
function SubAbaOperar({ carteira, ticker, posicaoSelecionada, tecnico, cp, ctx, seletor }) {
  const store = ctx && ctx.store;
  const A = ctx && ctx.A;
  // Fonte única de appMode (FIX-C21) — nunca redevirar de ctx.data.config.
  const operador = !!(ctx && ctx.operador);

  // Hook chamado incondicionalmente, antes de qualquer return (regra dos
  // hooks) — mesmo com ticker vazio, ele só fica ocioso.
  const { busy, aceitarCandidato, fecharLastreada } = useAceiteLastreado({ A, cp, ticker });

  const [gate, setGate] = useState(null);
  const [prop, setProp] = useState(null);

  // Réplica do par gate→proposta de AtivoCard (App.jsx, useEffect de
  // opGate/opProposta) — mesma disciplina: dois efeitos em cascata, cada um
  // best-effort (`.catch` silencioso), flag `vivo` no cleanup para que a
  // resposta de PETR4 nunca pinte a tela de VALE3, e a segunda chamada
  // guardada por um PRIMITIVO (`gate && gate.liquida`), não pelo objeto —
  // um objeto novo a cada resposta recriaria o efeito em loop.
  //
  // As duas rotas são INTERNAS, custo ZERO de cota do MCP
  // (`/api/options/gate`, `/api/options/proposta`) — é só por isso que podem
  // sair de efeito em vez de clique explícito (ADR-027 §3.3), a mesma
  // justificativa já aceita por escrito para `/api/options/tecnico` (Emenda
  // 2) e `/api/options/vigias` (Emenda 1). NENHUMA chamada aos métodos de
  // leitura paga do serviço externo (o prefixo `mcp` do store) vive aqui.
  useEffect(() => {
    let vivo = true;
    setGate(null);
    if (!store || !ticker) return () => { vivo = false; };
    store.optionsGate(ticker).then((r) => { if (vivo) setGate(r); }).catch(() => { /* best-effort */ });
    return () => { vivo = false; };
  }, [store, ticker]);

  useEffect(() => {
    let vivo = true;
    setProp(null);
    if (!store || !ticker || !(gate && gate.liquida)) return () => { vivo = false; };
    store.optionsProposta(ticker, true).then((r) => { if (vivo) setProp(r); }).catch(() => { /* best-effort */ });
    return () => { vivo = false; };
  }, [store, ticker, gate && gate.liquida]);

  // Fórmula de App.jsx (PropostaDaPosicao): a posição de opções já ABERTA
  // que casa com o candidato principal da proposta, para o CTA virar
  // "fechar" em vez de "abrir".
  const myOptionPositions = ((ctx && ctx.data && ctx.data.optionPositions) || []).filter((p) => p.underlying === ticker);
  const posAberta = (prop && prop.proposta)
    ? myOptionPositions.find((p) => p.id === prop.proposta.contractSymbol) || null
    : null;

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
              {gate === null ? (
                <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
              ) : !gate.liquida ? (
                <Aviso>{(cp.opcoesOperarSemLiquidez || ((t) => "Sem liquidez confirmada para " + t + " agora."))(ticker)}</Aviso>
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

// ---------------------------------------------------------------- F3 --
// As quatro peças que as seções novas repetem. Todas declaradas DEPOIS do
// componente, pela mesma razão do `CODIGOS_ACIONAVEIS` abaixo: o guardião lê
// a ORDEM das primeiras ocorrências no fonte (carregando → erro → vazio →
// dados), e um literal `mcp_nao_configurado` acima do componente inverteria
// essa ordem sem que nada tivesse mudado na tela. Declaração de função é
// içada, então a ordem física não muda a execução.

// A mesma cascata de códigos da cadeia de estados principal, para os quatro
// trios sob demanda. Não substitui a de cima: aquela é o texto que o guardião
// lê na posição em que ele exige lê-la.
function ErroDoMcp({ erro, cp }) {
  if (!erro) return null;
  const c = cp || {};
  if (erro.code === "mcp_nao_configurado") {
    return <Aviso>{c.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>;
  }
  if (erro.code === "mcp_cota" || erro.code === "mcp_teto_servico") {
    return (
      <Aviso>
        {(c.opcoesCota || ((r) => "Cota esgotada." + (r ? " Reinicia às " + r + "." : "")))(
          erro.detail && erro.detail.reinicia)}
      </Aviso>
    );
  }
  if (erro.code === "mcp_indisponivel") {
    return <Aviso>{c.opcoesIndisponivel || "Serviço de opções sem resposta agora."}</Aviso>;
  }
  // Inclui `mcp_erro_de_tool` e os 422 de pedido torto: a mensagem já vem
  // pronta e multi-linha do `enrichErrorMessage`, e vai crua (React escapa).
  return (
    <>
      <Aviso tom="forte">{erro.message}</Aviso>
      <RecusaCobrada erro={erro} cp={cp} />
    </>
  );
}

// 24-07 (achado F-04). A recusa da tool passou a DEBITAR uma chamada do cap:
// a viagem aconteceu e o serviço já a cobrou do teto compartilhado. Cobrar
// sem dizer que cobrou é a metade do defeito que a pessoa enxerga — a cota
// dela cai e a tela mostra só "o serviço recusou".
//
// As DUAS condições são necessárias, e nenhuma delas é zelo: os 422 de pedido
// torto (`kind_invalido`, `lote_invalido`, `ticker_ausente`) são recusa ANTES
// da rede e não custam chamada nenhuma. Afirmar cobrança neles seria inventar
// um débito — o mesmo erro do F-04, invertido e agora na tela.
function RecusaCobrada({ erro, cp }) {
  if (!erro || erro.code !== "mcp_erro_de_tool") return null;
  const d = (erro.detail && typeof erro.detail === "object") ? erro.detail : {};
  if (d.cobrado !== true) return null;
  // Discreta de propósito: é informação de contabilidade, não alarme. Quem
  // precisa agir sobre a recusa lê a mensagem do serviço, acima.
  return (
    <div style={{ marginTop: "6px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
      {(cp || {}).opcoesRecusaCobrada
        || "Esta tentativa consumiu uma chamada da sua cota do dia."}
    </div>
  );
}

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

// Fase 27 (27-02) — um cartão do bloco "Seus vigias".
//
// O nome exibido é SEMPRE o nome que a pessoa escreveu (`nome` no índice de
// custo zero, `name` na listagem do dia). O `nomeNoServico` — que carrega os 8
// hexadecimais do hash da conta — NUNCA chega à tela: ele é endereço no
// armazém compartilhado do serviço, não rótulo. Exibi-lo é exatamente o dano
// que a injeção nº 4 do 27-01 mediu ("o hash vira o nome que a pessoa lê").
//
// O cartão é um `<button>` de verdade, e não uma `div` com `onClick`: ele
// navega, e navegação precisa de foco, de Enter e de alvo de toque.
function CartaoDeVigia({ vigia, temEstado, selecionado, naCarteira, onIr, cp }) {
  const v = vigia || {};
  const c = cp || {};
  const nome = txt(v.nome || v.name);
  const alvo = txt(v.ticker);

  // Três estados, e a diferença entre eles é O QUE FOI MEDIDO:
  //  (a) o serviço não conhece mais este vigia → motivo do backend, VERBATIM.
  //      Sumir do armazém é FATO a mostrar, não item a esconder;
  //  (b) o estado do dia foi pedido → `armed`/`streak` como o serviço mediu;
  //  (c) só o índice respondeu → travessão COM motivo. Nunca leitura negativa:
  //      ausência de medição não é medição de ausência — a mesma simetria que
  //      este arquivo já aplica aos setups do ticker.
  const estado = v.motivo ? (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textSecondary, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {v.motivo}
    </span>
  ) : temEstado ? (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textSecondary, marginTop: "6px" }}>
      {"armado: " + (v.armed === true ? "sim" : v.armed === false ? "não" : "—")}
      {" · sequência: " + (ehNum(v.streak) ? v.streak : "—")
        + "/" + (ehNum(v.required_streak) ? v.required_streak : "—")}
    </span>
  ) : (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textMuted, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {c.opcoesVigiasSemEstado || "—"}
    </span>
  );

  return (
    <button
      onClick={() => { if (onIr) onIr(v.ticker); }}
      aria-pressed={!!selecionado}
      aria-label={"Abrir " + alvo + " — vigia " + nome}
      style={{
        display: "block", width: "100%", textAlign: "left", minHeight: "44px",
        border: `1px solid ${selecionado ? T.accent : T.borderSubtle}`,
        borderRadius: "12px", padding: "12px 14px",
        background: selecionado ? T.accentTint10 : T.bgPanel,
      }}
    >
      <span style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "baseline" }}>
        <span style={{ fontSize: "14px", fontWeight: 700, color: selecionado ? T.accent : T.textPrimary }}>{nome}</span>
        <span style={{ fontSize: "12px", fontWeight: 700, color: T.textMuted }}>{alvo}</span>
      </span>
      {estado}
      {/* Vigia de ativo que saiu da carteira NÃO some: ele existe e continua
          sendo avaliado pelo serviço. Escondê-lo repetiria o defeito desta
          fase — o vigia invisível que parece nunca ter sido gravado. */}
      {naCarteira ? null : (
        <span style={{ display: "block", fontSize: "11.5px", color: T.textMuted, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
          {c.opcoesVigiaForaDaCarteira || ""}
        </span>
      )}
      {/* Data do índice. Sem data, o motivo do backend — nunca a data de hoje
          no lugar (princípio 4 do CLAUDE.md). */}
      {v.criadoEm || v.motivoCriadoEm ? (
        <span style={{ display: "block", fontSize: "11px", color: T.textFaint, marginTop: "6px" }}>
          {v.criadoEm ? "criado em " + v.criadoEm : v.motivoCriadoEm}
        </span>
      ) : null}
    </button>
  );
}

// Pernas da estrutura. `side` e os números vêm do serviço; nada é recalculado
// — inclusive a quantidade, que é do contrato e não do lote.
function Pernas({ pernas, cp }) {
  const lista = Array.isArray(pernas) ? pernas.filter((p) => p && typeof p === "object") : [];
  if (!lista.length) return null;
  return (
    <>
      <div style={ROLAGEM}>
        <table style={TABELA}>
          <thead>
            <tr>
              <th style={TH}>Contrato</th><th style={TH}>Lado</th><th style={TH}>Qtd.</th>
              <th style={TH}>Strike</th><th style={TH}>Prêmio</th><th style={TH}>Delta</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((p, i) => (
              <tr key={(p.contract || "perna") + "-" + i}>
                <td style={{ ...TD, color: T.textPrimary, fontWeight: 700 }}>{txt(p.contract)}</td>
                <td style={TD}>{LADO[p.side] || txt(p.side)}</td>
                <td style={TD}>{ehNum(p.quantity) ? p.quantity : "—"}</td>
                <td style={TD}>{fmt(p.strike)}</td>
                <td style={TD}>{fmt(p.premium)}</td>
                <td style={TD}>{fmt(p.delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={AJUDA}>{(cp && cp.opcoesDeltaAjuda) || ""}</div>
    </>
  );
}

// Cadeia e operáveis: MESMA tabela, porque as duas rotas devolvem a mesma
// linha do serviço (chaves em PT-BR, ao contrário das pernas). `situacao_sigma`
// é coluna de primeira classe: é ela que explica por que delta e volatilidade
// vêm vazios em ~10% dos contratos — sem ela, o travessão vira "o app não
// sabe" quando o serviço declarou o motivo.
function TabelaDeOpcoes({ linhas }) {
  const lista = Array.isArray(linhas) ? linhas.filter((o) => o && typeof o === "object") : [];
  if (!lista.length) return null;
  return (
    <div style={ROLAGEM}>
      <table style={TABELA}>
        <thead>
          <tr>
            <th style={TH}>Contrato</th><th style={TH}>Tipo</th><th style={TH}>Strike</th>
            <th style={TH}>Prêmio</th><th style={TH}>Delta</th><th style={TH}>Vol. impl.</th>
            <th style={TH}>Negócios</th><th style={TH}>Vencimento</th><th style={TH}>Obs.</th>
          </tr>
        </thead>
        <tbody>
          {lista.map((o, i) => (
            <tr key={(o.contrato || "opcao") + "-" + i}>
              <td style={{ ...TD, color: T.textPrimary, fontWeight: 700 }}>{txt(o.contrato)}</td>
              <td style={TD}>{txt(o.tipo)}</td>
              <td style={TD}>{fmt(o.strike)}</td>
              <td style={TD}>{fmt(o.premio)}</td>
              <td style={TD}>{fmt(o.delta)}</td>
              <td style={TD}>{fracPct(o.volatilidade_implicita)}</td>
              <td style={TD}>{ehNum(o.total_negocios) ? o.total_negocios : "—"}</td>
              <td style={TD}>{txt(o.dt_vencimento)}</td>
              <td style={TD}>{txt(o.situacao_sigma)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Cenários em REAIS, já multiplicados pelo backend. O preço do objeto viaja
// verbatim (é preço, não dinheiro da posição) e o resultado ausente é
// travessão — 0 aqui seria "empata neste cenário", que é outra afirmação.
function Cenarios({ emReais, cp }) {
  const lista = (emReais && Array.isArray(emReais.cenarios) ? emReais.cenarios : [])
    .filter((s) => s && typeof s === "object");
  if (!lista.length) return null;
  return (
    <div style={{ marginTop: "8px" }}>
      <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".06em", color: T.textMuted, marginBottom: "4px" }}>
        {((cp && cp.opcoesCenariosTitulo) || "Cenários").toUpperCase()}
      </div>
      {lista.map((s, i) => (
        <Linha
          key={(s.name || "cenario") + "-" + i}
          rotulo={txt(s.name) + " · ativo a " + fmt(s.underlying)}
          valor={ehNum(s.resultado) ? "R$ " + fmt(s.resultado) : "—"}
        />
      ))}
    </div>
  );
}

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
