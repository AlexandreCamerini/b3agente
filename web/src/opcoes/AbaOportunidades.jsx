/**
 * AbaOportunidades.jsx — Fase 39 (NAV-01, D-02), partição de SecaoDescobrir.jsx.
 *
 * Aba 1 das 3 abas fixas: o motor COM gate de liquidez (Bloco A da extração
 * da Fase 33). Nasce da partição de `SecaoDescobrir.jsx` (Fase 33, 33-02):
 * cada bloco cross-carteira que ali convivia numa mesma tela vira aba
 * própria e leva o SEU carimbo de frescor (todo carimbo-frescor-blocos-
 * cross-carteira.md, D-04b da Fase 33, preservado aqui sem mudança).
 *
 * A frase-ponte (`cp.duasLeiturasIntro`) NÃO vem junto: os dois motores
 * cross-carteira deixam de dividir a mesma tela (D-01 proíbe segunda camada
 * de abas, e Oportunidades/Recomendadas agora são abas irmãs, não blocos
 * adjacentes) — a negação de hierarquia entre os dois passou a morar em
 * `curadoriaSubtitulo` (Plano 39-02), dentro da própria aba Recomendadas.
 *
 * `chaveComparavel`/`frescorAgregadoOportunidades` migram VERBATIM de
 * `SecaoDescobrir.jsx:75-113` (comentários de proveniência preservados
 * abaixo, histórico não se reescreve — só o arquivo muda). Sem hook de
 * dado, sem `.manchete` próprio (guardrail CVM — a manchete renderizada é a
 * de `OportunidadesOpcoes.jsx`, verbatim do motor), sem sort/filter sobre as
 * propostas (a ordem é do motor).
 */
import OportunidadesOpcoes from "./OportunidadesOpcoes.jsx";
import { CarimboFrescor } from "./uiOpcoes.jsx";

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

export default function AbaOportunidades({
  opcoesPorTicker, carregando, carteira, cp, onAbrir, abertoTicker, infoBotao,
}) {
  const frescor = frescorAgregadoOportunidades(opcoesPorTicker);
  return (
    <>
      <CarimboFrescor at={frescor.at} source={frescor.source} cp={cp} />
      <OportunidadesOpcoes
        propostas={opcoesPorTicker}
        carregando={carregando}
        positions={carteira}
        cp={cp}
        onAbrir={onAbrir}
        abertoTicker={abertoTicker}
        infoBotao={infoBotao}
      />
    </>
  );
}
