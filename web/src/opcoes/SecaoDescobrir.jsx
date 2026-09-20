/**
 * SecaoDescobrir.jsx — Fase 33 (33-02), extração de OpcoesScreen.jsx.
 *
 * Job 1 do PROJECT.md ("descobrir oportunidades cross-carteira") — hoje
 * inline em OpcoesScreen.jsx (a frase-ponte e os dois blocos cross-
 * carteira). Comportamento idêntico, zero funcionalidade nova (D-03 do
 * 33-CONTEXT.md), com UMA exceção explícita e aprovada: o carimbo de
 * frescor dos dois blocos (D-04b, TODO nomeado
 * carimbo-frescor-blocos-cross-carteira.md). Recebe TUDO por prop; não
 * instancia nenhum hook de dado — só o orquestrador (OpcoesScreen) chama o
 * hook que já busca a curadoria e o hook que já busca as propostas por
 * ticker (padrão Emenda 3 do ADR-027, já replicado por
 * OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx na Fase 32, e por
 * SecaoVigias.jsx na Fase 33-01).
 *
 * Este componente é um WRAPPER FINO: compõe OportunidadesOpcoes (Bloco A,
 * motor COM gate de liquidez) e CuradoriaEstruturas (Bloco B, motor SEM
 * gate) com as MESMAS props que recebiam em OpcoesScreen.jsx, sem
 * reescrever o conteúdo de nenhum dos dois.
 *
 * ORDEM INTERNA OBRIGATÓRIA (D-05, mitigação regulatória — Pitfall 2 da
 * pesquisa desta fase): a frase-ponte (cp.duasLeiturasIntro) vem antes do
 * Bloco A, que vem antes do Bloco B, sempre nesta sequência, sempre
 * adjacentes. O texto abaixo e o
 * comentário de decisão são os MESMOS que viviam em OpcoesScreen.jsx antes
 * desta extração — só o arquivo mudou, o motivo regulatório é o mesmo:
 *
 *   "Frase-ponte entre os dois motores cross-carteira, SEMPRE no DOM, sem
 *   estado de colapso, sem toggle de expansão, sem condicional — tornar
 *   esta frase colapsável seria regressão regulatória, não ajuste visual
 *   (é a mitigação do risco de D-05: sem ela, quem escaneia a tela lê 'AS 4
 *   MELHORES' do Bloco B como veredito geral do app, em vez de 'melhores
 *   entre os 4 candidatos do próprio bloco')."
 *
 * Nota datada 2026-09-19/2026-09-20 (33-02): a frase migra para este
 * arquivo JUNTO com o Bloco B de propósito — separar as duas em arquivos
 * diferentes quebraria a adjacência física que é a própria mitigação
 * (Pitfall 2 da pesquisa da Fase 33).
 *
 * REORG-07: `curadoria.top`/`curadoria.meta` são consumidos por REFERÊNCIA
 * e por ÍNDICE — nenhuma reordenação nem recomposição desses dois campos
 * neste arquivo (nada de reordenar/recortar sobre eles). A seleção é do
 * motor determinístico; reordenar por conveniência de exibição faria a
 * interface decidir o que o motor já decidiu.
 *
 * Carimbo de frescor (D-04b, exceção explícita e aprovada a "zero feature
 * nova" — ver o TODO nomeado acima). Descoberta da Task 1 desta fase,
 * FRONT-ONLY (registrada com `arquivo:linha` no SUMMARY do plano): as duas
 * rotas que alimentam os blocos já devolvem `at`/`source` na resposta, e os
 * dois hooks do orquestrador já preservam os dois campos até aqui — nenhuma
 * rota de backend mudou, nenhuma chamada de rede nova. Um carimbo por
 * bloco (motores e respostas diferentes, um carimbo compartilhado
 * afirmaria a mesma hora pra duas medições distintas), derivado só do
 * campo que a própria resposta carrega — nunca do relógio de quem está com
 * a tela aberta. Campo ausente vira o vocabulário de "não medido" já
 * existente em copy.js, nunca uma hora inventada (princípios 3 e 4 do
 * CLAUDE.md).
 */
import OportunidadesOpcoes from "./OportunidadesOpcoes.jsx";
import CuradoriaEstruturas from "./CuradoriaEstruturas.jsx";

// Espelho declarado do núcleo do app (mesmo padrão de
// OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx) — só o token que este
// componente usa.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "textFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Fase 33 (33-02, D-04b): "DD/MM/AAAA HH:mm" (formato do carimbador de hora
// único do backend, que toda resposta desta aba usa) vira uma chave
// comparável "AAAA-MM-DD HH:mm" — comparação por STRING, sem nenhum objeto
// de data e sem tocar o relógio local. Serve só para achar, entre vários
// tickers, o carimbo mais antigo; não é usado para exibir nada (o texto
// exibido é sempre o `at` original, no formato que o servidor já mandou).
function chaveComparavel(at) {
  const m = typeof at === "string"
    ? /^(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2})$/.exec(at)
    : null;
  return m ? m[3] + "-" + m[2] + "-" + m[1] + " " + m[4] + ":" + m[5] : null;
}

// Bloco A é agregado sobre N tickers — cada resposta com o próprio
// `at`/`source`, independente das outras. O carimbo tem de dizer a idade
// REAL do conjunto: o `at` mais antigo entre os tickers com proposta
// concreta (mesmo critério que já decide se o ticker aparece no bloco),
// nunca o mais recente, que esconderia o dado mais velho do grupo. A fonte
// só aparece quando é a MESMA em todos os tickers do conjunto — eleger uma
// por maioria seria inventar consenso que a resposta não deu. Percorrido
// com laço comum, sem os métodos de array que reordenam ou recortam
// (`sort()`/`filter()`) de propósito: nada aqui reordena o que o motor
// decidiu, só resume duas leituras (hora e fonte) para exibição honesta.
function frescorAgregadoOportunidades(opcoesPorTicker) {
  const tickers = Object.keys(opcoesPorTicker || {});
  let atMaisAntigo = null;
  let chaveMaisAntiga = null;
  let fonteComum;
  let fonteDivergente = false;
  for (let i = 0; i < tickers.length; i++) {
    const entrada = opcoesPorTicker[tickers[i]];
    const proposta = entrada && entrada.proposta;
    const at = proposta && proposta.at;
    const chave = chaveComparavel(at);
    if (chave && (chaveMaisAntiga === null || chave < chaveMaisAntiga)) {
      chaveMaisAntiga = chave;
      atMaisAntigo = at;
    }
    if (proposta && at) {
      if (fonteComum === undefined) fonteComum = proposta.source;
      else if (fonteComum !== proposta.source) fonteDivergente = true;
    }
  }
  return { at: atMaisAntigo, source: fonteDivergente ? null : (fonteComum || null) };
}

// Carimbo de frescor — um por bloco (D-04b). Ausência de `at` vira o
// vocabulário de "não medido" já existente em copy.js — nunca uma hora
// composta no cliente.
function CarimboFrescor({ at, source, cp }) {
  return (
    <div style={{ fontSize: "10.5px", color: T.textFaint, margin: "0 0 6px", lineHeight: 1.4 }}>
      {at
        ? (cp.opcoesConsultadoEmRotulo || "Consultado") + ": " + at +
          (source ? " · " + (cp.opcoesFonteRotulo || "Fonte") + ": " + source : "")
        : (cp.opcoesFrescorNaoMedido || "frescor não medido")}
    </div>
  );
}

export default function SecaoDescobrir({
  opcoesPorTicker, opcoesPorTickerCarregando, carteira, curadoria,
  onAbrir, onExecutar, onNarrar, onRecarregar, operador, palette, cp,
}) {
  const frescorA = frescorAgregadoOportunidades(opcoesPorTicker);
  const metaCuradoria = curadoria && curadoria.meta;

  return (
    <>
      {/* D-05, incondicional — ver o comentário de proveniência no topo do
          arquivo. Sem onClick, sem estado de expansão, numa linha isolada. */}
      <p style={{ fontSize: "12px", color: T.textMuted, lineHeight: 1.5, margin: "10px 0 14px" }}>
        {cp.duasLeiturasIntro}
      </p>
      <CarimboFrescor at={frescorA.at} source={frescorA.source} cp={cp} />
      <OportunidadesOpcoes
        propostas={opcoesPorTicker}
        carregando={opcoesPorTickerCarregando}
        positions={carteira}
        cp={cp}
        onAbrir={onAbrir}
      />
      <CarimboFrescor at={metaCuradoria && metaCuradoria.at} source={metaCuradoria && metaCuradoria.source} cp={cp} />
      <CuradoriaEstruturas
        top={(curadoria && curadoria.top) || []}
        meta={metaCuradoria}
        carregando={!!(curadoria && curadoria.carregando)}
        erro={!!(curadoria && curadoria.erro)}
        concluido={!!(curadoria && curadoria.concluido)}
        narrativa={curadoria && curadoria.narrativa}
        narrando={!!(curadoria && curadoria.narrando)}
        erroNarrativa={curadoria && curadoria.erroNarrativa}
        onNarrar={onNarrar}
        onRecarregar={onRecarregar}
        cp={cp}
        onAbrir={onAbrir}
        onExecutar={onExecutar}
        operador={operador}
        palette={palette}
      />
    </>
  );
}
