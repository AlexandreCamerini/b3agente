/**
 * CandidatoOpcao.jsx — Fase 32 (32-02), extração de App.jsx.
 *
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3 — isolamento do núcleo) e `App.jsx` não pode
 * importar `OpcoesScreen.jsx` (seria ciclo). A fiação correta é de UMA VIA
 * para os dois lados — um módulo terceiro que ambos importam, nunca um
 * importando o outro. Isto é a Emenda 3 ao ADR-027 (registrada na Fase 28,
 * `PropostaLastreada.jsx`), aplicada agora aos três componentes que faltavam.
 *
 * (b) O que é: o cartão de UM candidato dentro da linha de N candidatos do
 * detalhe de posição (Fase 19, MULTI-02) — reusa o padrão visual de
 * `OportunidadesOpcoes` e os internos de `PropostaLastreada` (`ChipDaProposta`,
 * importado abaixo). Manchete VERBATIM do motor determinístico (guardrail
 * CVM, CLAUDE.md princípio 5). Assinatura de props INALTERADA nesta task.
 *
 * (c) Por que `T`/`MONO`/`price`/`carouselItemStyle` são declarados AQUI em
 * vez de importados de `App.jsx`: importar de `App.jsx` reintroduziria
 * exatamente o import que a Emenda 3 proíbe. São espelho declarado — mesmo
 * padrão de `PropostaLastreada.jsx:22-49` (Fase 28).
 */
import { ChipDaProposta } from "./PropostaLastreada.jsx";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgCard", "borderFaint", "textPrimary", "textSecondary", "textMuted", "textFaint", "accent", "accentTint", "positive", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Espelho declarado de App.jsx:264/293-294 (Fase 32, 32-02).
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const price = (n) => (n == null || isNaN(n) ? "—" : nf2.format(n));

// Espelho declarado de App.jsx:342 (Fase 32, 32-02) — usado só pelo item
// dentro da linha (o trilho em si é do chamador, `PropostaDaPosicao`).
const carouselItemStyle = (align = "start") => ({ scrollSnapAlign: align });

// Fase 19 (Plano 03, MULTI-02): item de UM candidato dentro da linha de N
// candidatos do detalhe de posição — reusa verbatim o padrão visual do item
// de OportunidadesOpcoes (Fase 18, App.jsx:3938-3964) e os internos de
// PropostaLastreada (Fase 14/17, App.jsx:3056-3134). NÃO renderiza o
// componente PropostaLastreada de propósito: o guardião de contagem 2x da
// Fase 18 (test_carteira_opcoes_tira.mjs) trava esse componente aos dois
// pontos de uso já existentes (AtivoCard + PropostaDaPosicao de candidato
// único).
export default function CandidatoOpcao({ p, r, cp, operador, busy, onAceitar, onVerbeteLiquidez }) {
  const isCollar = p.tipo === "collar";
  const isCall = p.optionType === "call";
  // mesma regra de polaridade da manchete do card (App.jsx:3038): nunca
  // T.accent na linha da manchete.
  const cor = isCall ? T.positive : T.negative;
  const eyebrow = isCollar ? cp.eyebrowPropostaCollar : isCall ? cp.eyebrowPropostaCall : cp.eyebrowPropostaPut;
  const degradado = r.providerStatus !== "ok";
  const est = p.estrutura || null;
  // ATENÇÃO: `null * 100 === 0` em JS — só multiplica NÚMERO; null/undefined
  // continuam null e caem em price(null) → "—" (regra "null nunca 0.0"
  // aplicada à UI, mesmo helper de App.jsx:3051-3055).
  const porLote = (v) => (typeof v === "number" ? v * (p.qtyAcoes || 0) : null);
  return (
    // teto de largura (achado ao vivo 2026-09-07, staging/iPhone, dois
    // candidatos put_protecao + collar): sem `flex-basis` fixo o item
    // dimensiona por `max-content` — a manchete do collar, que é longa por
    // desenho, então esticava o card até virar linha única e empurrar os
    // valores do payoff pra fora da leitura confortável. A manchete NUNCA é
    // truncada (guardrail CVM — cortar reescreveria a afirmação do motor),
    // por isso a correção é de LARGURA, nunca de texto. `flex: "0 0 210px"`
    // CUMPRE a Decisão 1 do 22-UI-SPEC pela primeira vez (o `minWidth:"210px"`
    // documentado sempre foi piso, nunca teto — decisão do Alex, 2026-09-07,
    // ver 260907-w33-PLAN.md Task 1) em vez de revertê-la: os dois candidatos
    // seguem comparáveis lado a lado, sem a T-22-02 (esconder o 2º candidato).
    // Os dois cards têm a MESMA largura de propósito — duas propostas
    // disputam a MESMA decisão; largura diferente daria peso visual diferente
    // (CLAUDE.md princípio 9). Espelhado no item de OportunidadesOpcoes acima.
    <div style={{ ...carouselItemStyle("start"), flex: "0 0 210px", minWidth: "210px", minHeight: "44px", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
      <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent }}>{eyebrow}</div>
      <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "13px", color: T.textSecondary, marginTop: "3px" }}>
        {isCollar
          ? cp.collarPernasLinha(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut))
          : `${p.contratos}× ${isCall ? "CALL" : "PUT"} ${r.ticker} · strike ${price(p.strike)}`}
      </div>
      {/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md); nunca
          truncada com reticências: cortar reescreveria a afirmação do
          motor. */}
      <div style={{ fontSize: "12.5px", fontWeight: 700, color: cor, marginTop: "4px", whiteSpace: "normal" }}>{p.manchete}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "10px" }}>
        {(p.chips || []).map((c) => (
          <ChipDaProposta key={c.k} c={c} p={p} ticker={r.ticker} onVerbeteLiquidez={onVerbeteLiquidez} />
        ))}
      </div>
      {est && (
        <div style={{ marginTop: "10px", padding: "10px", borderRadius: "9px", background: T.bgBase }}>
          <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint }}>{cp.payoffTitulo}</div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "6px" }}>
            <span style={{ color: T.textSecondary }}>{cp.payoffGanhoMaximo}</span>
            <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>
              {est.ganho_ilimitado ? cp.payoffIlimitado : "R$ " + price(porLote(est.ganho_maximo))}
            </b>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "4px" }}>
            <span style={{ color: T.textSecondary }}>{cp.payoffPerdaMaxima}</span>
            <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>
              {est.perda_ilimitada ? cp.payoffIlimitado : "R$ " + price(porLote(est.perda_maxima))}
            </b>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "4px" }}>
            <span style={{ color: T.textSecondary }}>{cp.payoffBreakeven}</span>
            <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>
              {Array.isArray(est.breakevens) && est.breakevens.length ? est.breakevens.map((b) => price(b)).join(" / ") : cp.payoffSemDado}
            </b>
          </div>
          {p.caixa && (
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "4px" }}>
              <span style={{ color: T.textSecondary }}>
                {p.caixa.fluxo === "credito" ? cp.payoffCaixaCredito : p.caixa.fluxo === "debito" ? cp.payoffCaixaDebito : cp.payoffCaixaNeutro}
              </span>
              {p.caixa.fluxo !== "neutro" && (
                <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>R$ {price(Math.abs(p.caixa.custoLiquidoTotal))}</b>
              )}
            </div>
          )}
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "8px" }}>{cp.payoffNota(price(p.precoObjeto))}</div>
        </div>
      )}
      {/* Modo Estudo (vocab["educacional"]): a MESMA proposta, condicional —
          nunca um botão de executar (T-14-23). */}
      {!operador && (
        <div style={{ fontSize: "12px", color: T.textMuted, lineHeight: 1.5, marginTop: "10px" }}>{p.didatica}</div>
      )}
      {/* Modo Operador: CTA imperativo próprio deste candidato. O ramo multi
          só existe quando não há posição lastreada aberta (a rota devolve
          candidatos: [] nesse caso) — sem ramo posAberta/ctaFecharLastreada
          aqui, ao contrário de PropostaLastreada. */}
      {operador && (
        <button
          type="button"
          onClick={() => onAceitar(p)}
          disabled={busy || degradado}
          style={{ marginTop: "12px", width: "100%", minHeight: "40px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "12.5px" }}
        >
          {degradado
            ? cp.propostaIndisponivelDegradada
            : isCollar
            ? (p.caixa && p.caixa.fluxo === "credito"
                ? cp.ctaCollarCredito(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut), price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0)))
                : cp.ctaCollarDebito(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut), price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0))))
            : isCall
            ? cp.ctaVendaCoberta(p.contratos, r.ticker, price(p.strike), price(p.premioTotal))
            : cp.ctaPutProtecao(p.contratos, r.ticker, price(p.strike), price(p.premioTotal))}
        </button>
      )}
    </div>
  );
}
