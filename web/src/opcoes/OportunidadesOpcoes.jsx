/**
 * OportunidadesOpcoes.jsx — Fase 32 (32-02), extração de App.jsx.
 *
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3 — isolamento do núcleo) e `App.jsx` não pode
 * importar `OpcoesScreen.jsx` (seria ciclo). A fiação correta é de UMA VIA
 * para os dois lados — um módulo terceiro que ambos importam, nunca um
 * importando o outro. Isto é a Emenda 3 ao ADR-027 (registrada na Fase 28,
 * `PropostaLastreada.jsx`), aplicada agora aos três componentes que faltavam
 * (D-07 da Fase 32: este componente é MOVIDO, não deletado nem substituído
 * pela lista curada — os dois motores cross-posição continuam lado a lado).
 *
 * (b) O que é: a tira "Oportunidades de opções" (Fase 18, NAV-01/NAV-03) —
 * o motor COM gate de liquidez, movido sem redesenho. Manchete VERBATIM do
 * motor determinístico (guardrail CVM, CLAUDE.md princípio 5). Assinatura de
 * props INALTERADA nesta task; a tela que a renderiza é a Task 3 (32-03).
 *
 * (c) Por que `T`/`MONO`/`carouselTrackStyle`/`carouselItemStyle` são
 * declarados AQUI em vez de importados de `App.jsx`: importar de `App.jsx`
 * reintroduziria exatamente o import que a Emenda 3 proíbe. São espelho
 * declarado — mesmo padrão de `PropostaLastreada.jsx:22-49` (Fase 28).
 */
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgCard", "borderFaint", "textPrimary", "textSecondary", "textMuted", "textFaint", "accent", "positive", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Espelho declarado de App.jsx:264 (Fase 32, 32-02) — só a fonte MONO, único
// helper tipográfico que este componente usa (não formata dinheiro).
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";

// Espelho declarado de App.jsx:333-342 (Fase 32, 32-02) — padrão ÚNICO de
// rolagem horizontal do app (Fase 22, SYS-01). Ver o comentário completo em
// App.jsx; aqui só a forma, sem repetir a justificativa.
const carouselTrackStyle = (extra) => ({
  display: "flex",
  overflowX: "auto",
  scrollSnapType: "x proximity",
  WebkitOverflowScrolling: "touch",
  ...extra,
});
const carouselItemStyle = (align = "start") => ({ scrollSnapAlign: align });

// Fase 18 (Plano 03, NAV-01/NAV-03): tira agregada "Oportunidades de opções"
// no topo de Posições — a única superfície que reúne, numa olhada, todas as
// posições com estrutura possível hoje. Diferente do card individual
// (App.jsx:3484-3489, ADR-004: silêncio deliberado pra não virar "seis
// avisos idênticos por tela"), aqui o silêncio é o ERRO: a tira só aparece
// uma vez por tela, então sumir sem dizer o motivo faria o usuário concluir
// que o produto quebrou (NAV-03). Por isso o cabeçalho `cp.tiraOpcoesTitulo`
// é fixo nos três estados (itens / carregando / vazio com motivo) — a seção
// nunca desaparece silenciosamente quando há posições.
// Recebe `propostas`/`carregando` PRONTOS por prop (do hook `useOpcoesPropostas`,
// Plano 18-01) — nenhum fetch daqui, dobraria o tráfego que o hook existe pra
// evitar. A manchete de cada item é `pr.manchete` renderizada VERBATIM
// (guardrail CVM, CLAUDE.md): proibido compor frase nova a partir de
// strike/contratos/optionType/premioTotal neste componente.
export default function OportunidadesOpcoes({ propostas, carregando, positions, cp, onAbrir, abertoTicker, infoBotao }) {
  // item só existe quando o gate aprovou liquidez E veio proposta CONCRETA —
  // o ramo "sem proposta" de PropostaLastreada (r.proposta null) não vira
  // item de tira.
  const itens = (positions || []).filter((p) => {
    const e = propostas[p.t];
    return !!(e && e.gate && e.gate.liquida && e.proposta && e.proposta.proposta);
  });
  // decide QUAL dos dois motivos de NAV-03 exibir quando não há item: gate
  // líquido em pelo menos uma posição (falta setup técnico) × nenhuma
  // cobertura líquida (falta contrato líquido pra sequer estudar estrutura).
  const algumLiquido = (positions || []).some((p) => {
    const e = propostas[p.t];
    return !!(e && e.gate && e.gate.liquida);
  });
  // Quick 260908-ldg (D-07): terceiro caso do estado vazio — nenhuma posição
  // com gate líquido E ao menos uma com faixa nomeada SEM MERCADO. NOMEIA a
  // faixa em vez de dizer genericamente "sem liquidez suficiente"
  // (`tiraOpcoesSemCobertura`, que segue valendo quando o gate simplesmente
  // não devolveu faixa — backend antigo/degradado).
  const algumSemMercado = !algumLiquido && (positions || []).some((p) => {
    const e = propostas[p.t];
    return !!(e && e.gate && e.gate.faixa === "SEM MERCADO");
  });
  return (
    <div style={{ marginBottom: "14px" }}>
      {/* Fase 39 (NAV-01, D-13): slot do ⓘ contextual da aba — opcional,
          `infoBotao || null` não muda nada para quem não passa a prop. */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "4px" }}>
        <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint }}>{cp.tiraOpcoesTitulo}</div>
        {infoBotao || null}
      </div>
      {/* Fase 32 (32-03, D-05): subtítulo NOMEIA o motor deste bloco (COM
          gate) — os dois blocos cross-carteira passam a conviver na mesma
          tela, então o eyebrow sozinho não basta mais para dizer qual é
          qual. Mesma métrica de CuradoriaEstruturas.jsx:142. */}
      <div style={{ fontSize: "11.5px", color: T.textMuted, marginBottom: "8px", lineHeight: 1.4 }}>{cp.tiraOpcoesSubtitulo}</div>
      {itens.length > 0 && (
        <div style={carouselTrackStyle({ gap: "10px", scrollbarWidth: "none", paddingBottom: "2px" })}>
          {itens.map((p) => {
            const pr = propostas[p.t].proposta.proposta;
            const isCollar = pr.tipo === "collar";
            const isCall = pr.optionType === "call";
            const eyebrow = isCollar ? cp.eyebrowPropostaCollar : isCall ? cp.eyebrowPropostaCall : cp.eyebrowPropostaPut;
            // mesma regra de polaridade da manchete do card (App.jsx:3038):
            // nunca T.accent na linha da manchete.
            const cor = isCall ? T.positive : T.negative;
            return (
              <button
                key={p.t}
                type="button"
                aria-label={p.t + " — " + cp.tiraOpcoesVerDetalhe}
                aria-expanded={abertoTicker === p.t}
                onClick={() => onAbrir(p.t)}
                // teto de largura: mesma decisão do item de CandidatoOpcao (App.jsx,
                // achado ao vivo 2026-09-07) — ver comentário completo lá.
                style={{ ...carouselItemStyle("start"), flex: "0 0 210px", minWidth: "210px", minHeight: "44px", textAlign: "left", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, cursor: "pointer" }}
              >
                <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent }}>{eyebrow}</div>
                <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "13px", color: T.textPrimary, marginTop: "3px" }}>{p.t}</div>
                {/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md);
                    nunca truncada com reticências: cortar reescreveria a
                    afirmação do motor. */}
                <div style={{ fontSize: "12.5px", fontWeight: 700, color: cor, marginTop: "4px", whiteSpace: "normal" }}>{pr.manchete}</div>
                <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.tiraOpcoesVerDetalhe}</div>
              </button>
            );
          })}
        </div>
      )}
      {/* carregando vem ANTES dos vazios: sem esse ramo a tira pisca "não há
          oportunidade" durante a busca e mente sobre o estado real. */}
      {itens.length === 0 && carregando && (
        <div style={{ fontSize: "12px", color: T.textFaint, lineHeight: 1.5 }}>{cp.tiraOpcoesCarregando}</div>
      )}
      {/* estado vazio EXPLÍCITO (NAV-03) — é ESTADO, não ação: sem botão e
          sem CTA, mesmo precedente de AvisoLiquidacao (App.jsx:1053-1063). */}
      {itens.length === 0 && !carregando && (
        <div style={{ padding: "10px 11px", borderRadius: "9px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
          {algumLiquido ? cp.tiraOpcoesSemSetup : algumSemMercado ? cp.tiraOpcoesSemMercado : cp.tiraOpcoesSemCobertura}
        </div>
      )}
    </div>
  );
}
