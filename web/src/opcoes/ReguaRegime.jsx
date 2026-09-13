/**
 * ReguaRegime.jsx — aba Opções, Fase 27 (plano 27-04, D4 do 27-CONTEXT).
 *
 * A régua de regime do protótipo aprovado pelo Alex em 2026-09-13: até sete
 * segmentos, um por pregão FECHADO, do mais antigo à esquerda; cor do estado
 * MEDIDO naquele dia; hoje destacado.
 *
 * **Por que ela existe.** O número de hoje sozinho não diz se a tendência
 * virou ou se a volatilidade desabou na semana — e essa é a pergunta que
 * nasce assim que a pessoa olha o técnico do ativo. A régua responde "mudou
 * esta semana?" sem custar uma chamada.
 *
 * **O que ela NÃO faz.** Não classifica nada. Cada item já chega classificado
 * do backend (`opcoes_tecnico.regua`, que alimenta `regime.classificar` um
 * pregão por vez, com a profundidade de histórico correta de cada dia). Uma
 * segunda régua de regime em JavaScript divergiria da primeira na correção
 * seguinte, em silêncio e com as duas parecendo a mesma coisa na tela — é a
 * classe de defeito que o Snapshot Técnico Único existe para matar. Por isso
 * aqui não há comparação de preço com média, nem limiar de ADX: só desenho.
 *
 * **Cor não é informação acessível.** Todo segmento carrega o dia, o regime e
 * a força em TEXTO, no `aria-label` e no `title` — quem não distingue verde de
 * vermelho lê a mesma coisa que quem distingue (princípio 10 do CLAUDE.md).
 *
 * Zero import de `App.jsx` (seria ciclo) e bloco de tokens local, padrão de
 * `SetupChart.jsx`/`PayoffChart.jsx`. Nenhuma cor literal: só tokens que já
 * existem na paleta do Brand Book v2.
 */

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root`.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "positive", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Os QUATRO regimes de `server/app/regime.py::REGIMES`, mapeados em tokens
// que JÁ existem na paleta — nenhuma cor nova, nenhum hex
// (`test_brand_book_v2_tokens.mjs` e o guardião desta régua).
//
// `lateral` cai em `textMuted` e `indefinido` em `borderFaint` de propósito:
// "sem tendência definida" e "não deu para classificar" são estados neutros, e
// pintá-los de verde ou vermelho seria afirmar direção onde não há nenhuma.
// A diferença entre os dois é deliberadamente discreta na cor e explícita no
// texto — é o texto que carrega a distinção.
export const CORES_DO_REGIME = {
  tendencia_alta: "positive",
  tendencia_baixa: "negative",
  lateral: "textMuted",
  indefinido: "borderFaint",
};

// "2026-09-11" vira "11/09". Fora desse formato, o valor sai como veio — o
// carimbo do backend nunca é substituído por um palpite, e data ilegível é
// travessão, jamais a data de hoje no lugar.
const diaCurto = (iso) => {
  const s = typeof iso === "string" ? iso : "";
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return m[3] + "/" + m[2];
  return s || "—";
};

export default function ReguaRegime({ regua, cp }) {
  const c = cp || {};
  const itens = (regua && Array.isArray(regua.itens)) ? regua.itens : [];
  // Régua vazia NÃO é desenhada. Sete segmentos "indefinido" seriam lidos
  // como "a semana inteira sem direção", que é afirmação diferente de "não há
  // dado" — quem diz o porquê é o bloco pai, com o motivo do backend.
  if (!itens.length) return null;

  const rotuloRegime = (r) => ((c.opcoesRegimeRotulo || {})[r]) || "—";
  const rotuloForca = (f) => ((c.opcoesForcaRotulo || {})[f]) || null;

  // A informação INTEIRA em texto: dia, regime, força, se é hoje e a ressalva
  // de janela curta. É o que o leitor de tela anuncia e o que aparece ao
  // repousar o dedo/cursor sobre o segmento.
  const descricao = (item) => {
    const forca = rotuloForca(item && item.forca);
    return diaCurto(item && item.data)
      + ": " + rotuloRegime(item && item.regime)
      + (forca ? ", força " + forca : "")
      + (item && item.hoje ? " (hoje)" : "")
      + (item && item.confiavel === false && c.opcoesRegimeNaoConfiavel
        ? " — " + c.opcoesRegimeNaoConfiavel : "");
  };

  return (
    <div style={{ marginTop: "10px" }}>
      <div style={{ fontSize: "12px", fontWeight: 700, color: T.textSecondary }}>
        {c.opcoesReguaTitulo || "Como a semana evoluiu"}
      </div>

      {/* Largura igual por segmento e um por coluna: a faixa cabe em 375 px
          sem rolagem horizontal, e nenhum pregão fica maior que outro (o
          tamanho na tela seria lido como peso na decisão). */}
      <div
        role="list"
        aria-label={c.opcoesReguaTitulo || "Como a semana evoluiu"}
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${itens.length}, 1fr)`,
          gap: "4px",
          marginTop: "6px",
        }}
      >
        {itens.map((item, i) => {
          const rotulo = descricao(item);
          const cor = T[CORES_DO_REGIME[item && item.regime]] || T.borderFaint;
          const incerto = !!item && item.confiavel === false;
          return (
            <div key={(item && item.data) || i} role="listitem" title={rotulo} aria-label={rotulo}>
              <span
                style={{
                  display: "block",
                  height: "22px",
                  borderRadius: "5px",
                  background: cor,
                  // Opacidade reduzida marca "medido com a janela curta" — e
                  // NUNCA sozinha: o motivo vai junto no rótulo acessível.
                  opacity: incerto ? 0.45 : 1,
                  border: item && item.hoje
                    ? `2px solid ${T.accent}` : `1px solid ${T.borderSubtle}`,
                  boxSizing: "border-box",
                }}
              />
              <span
                style={{
                  display: "block",
                  textAlign: "center",
                  marginTop: "4px",
                  fontSize: "9.5px",
                  fontWeight: item && item.hoje ? 800 : 600,
                  color: item && item.hoje ? T.textSecondary : T.textFaint,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {diaCurto(item && item.data)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Motivo do backend, VERBATIM: série curta mostra MENOS segmentos e diz
          por quê — nunca preenche os que faltam. */}
      {regua && regua.motivo ? (
        <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
          {regua.motivo}
        </div>
      ) : null}

      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "4px", lineHeight: 1.45 }}>
        {c.opcoesReguaAjuda || ""}
      </div>
    </div>
  );
}
