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
import { useOpcoesMcp } from "./useOpcoesMcp.js";
import SetupChart from "./SetupChart.jsx";
import PayoffChart from "./PayoffChart.jsx";
import CriarSetup, { BotaoDesativar } from "./CriarSetup.jsx";

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

export default function OpcoesScreen({ ctx }) {
  const cp = (ctx && ctx.cp) || {};
  const store = ctx && ctx.store;
  const palette = (ctx && ctx.palette) || {};
  // Universo = a watchlist do usuário. Não se inventa um universo aqui, e
  // não há chamada extra para descobrir tickers.
  const watchlist = (ctx && ctx.data && ctx.data.watchlist) || [];
  const [ticker, setTicker] = useState("");
  const {
    status, leitura, grafico, abrirGrafico, fecharGrafico,
    cadeia, operaveis, proposta, possibilidades,
    abrirCadeia, abrirOperaveis, montarProposta, verPossibilidades,
    setupNovo, compilarSetup, confirmarSetup, desativarSetup,
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
  let chip = null;
  if (frescor && frescor.medido === false) {
    chip = cp.opcoesFrescorNaoMedido || "frescor não medido";
  } else if (frescor && frescor.medido) {
    const critica = (frescor.classes || [])[0];
    const idade = critica && ehNum(critica.idadeHoras) ? " (" + fmt(critica.idadeHoras, 0) + " h)" : "";
    chip = frescor.bloqueia
      ? (cp.opcoesFrescorAtrasado || "dado atrasado") + idade
      : (cp.opcoesFrescorEmDia || "dado em dia");
  }

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
    </div>
  );

  const seletor = (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "14px 0 4px" }}>
      {watchlist.map((t) => (
        <button
          key={t}
          onClick={() => escolherTicker(t)}
          aria-pressed={t === ticker}
          style={{ minHeight: "44px", padding: "8px 14px", borderRadius: "11px", border: `1px solid ${t === ticker ? T.accent : T.borderSubtle}`, background: t === ticker ? T.accentTint10 : T.bgPanel, color: t === ticker ? T.accent : T.textSecondary, fontWeight: 700, fontSize: "13px" }}
        >
          {t}
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

      {cabecalho}
      {watchlist.length > 0 ? seletor : null}

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
          {semTicker ? (
            <Aviso>{cp.opcoesEscolherAtivo || "Escolha um ativo para ver a leitura."}</Aviso>
          ) : null}
          {semCandles ? (
            <Aviso>
              O serviço não tem candles para este ativo, então não há leitura de
              comportamento para mostrar. Nada foi estimado no lugar.
            </Aviso>
          ) : null}
          {!semTicker && setups.length === 0 ? (
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

                <button
                  onClick={() => montarProposta({ direction: tese, expiration: vencimento || undefined, lote: loteNum })}
                  disabled={!temTese || !loteOk}
                  style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!temTese || !loteOk) }}
                >
                  {cp.opcoesMontarEstrutura || "Montar estrutura"}
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
                    {cp.opcoesVerCadeia || "Ver a cadeia"}
                  </button>
                  <button
                    onClick={() => { const abrir = painel !== "operaveis"; setPainel(abrir ? "operaveis" : ""); if (abrir) abrirOperaveis({ expiration: vencimento || undefined }); }}
                    aria-pressed={painel === "operaveis"}
                    style={{ ...BOTAO, flex: "1 1 150px" }}
                  >
                    {cp.opcoesVerOperaveis || "Ver as operáveis"}
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
                const aberto = grafico.setup === s.name;
                return (
                  <div key={s.name} style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px 14px", background: T.bgPanel }}>
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

                    <button
                      onClick={() => (aberto ? fecharGrafico() : abrirGrafico(s.name))}
                      aria-pressed={aberto}
                      aria-label={(aberto ? "Fechar" : "Ver") + " disparos do setup " + s.name}
                      style={{ marginTop: "10px", width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}
                    >
                      {aberto ? "Fechar gráfico" : (cp.opcoesGraficoTitulo || "Disparos do setup")}
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
                        nome={s.name}
                        onDesativar={desativarSetup}
                        ocupado={setupNovo.carregando}
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
              <CriarSetup
                ticker={ticker}
                estado={setupNovo}
                onCompilar={compilarSetup}
                onConfirmar={confirmarSetup}
                cp={cp}
              />
            </>
          ) : null}
        </div>
      )}

      <p style={{ marginTop: "20px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.55 }}>
        {cp.opcoesDisclaimer || ""}
      </p>
    </section>
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
// leitura (dispara sempre que a pessoa escolhe um ticker, mesmo com o
// serviço fora do ar) mascarar o `mcp_nao_configurado` do `/status` — que é
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
