/**
 * PropostaLastreada.jsx — Fase 28 (28-01), extração de App.jsx.
 *
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3 — isolamento do núcleo) e `App.jsx` não pode
 * importar `OpcoesScreen.jsx` (seria ciclo). A fiação correta é de UMA VIA
 * para os dois lados — um módulo terceiro que ambos importam, nunca um
 * importando o outro. Isto é a Emenda 3 ao ADR-027, registrada nesta fase, e
 * é a mesma técnica das Emendas 1 e 2 (aplicadas a dado), agora aplicada a
 * componente de UI.
 *
 * (b) O que é: o componente é o de sempre, movido sem redesenho — manchete
 * VERBATIM do motor determinístico (guardrail CVM, CLAUDE.md princípio 5),
 * payoff numérico (ganho máximo/perda máxima/breakevens), CTA de
 * abrir/fechar só em Modo Operador. Nenhuma cor, texto ou rota mudou.
 *
 * (c) Por que `T`/`MONO`/`price`/`FONTE_LABEL` são declarados AQUI em vez de
 * importados de `App.jsx`: importar de `App.jsx` reintroduziria exatamente o
 * import que a Emenda 3 proíbe. Os quatro são espelho declarado — ver nota
 * datada acima de cada um.
 */
import { useState } from "react";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root` — padrão já
// estabelecido em `OpcoesScreen.jsx`/`SetupChart.jsx`. Zero import de
// `App.jsx` (seria ciclo).
//
// ATENÇÃO: a lista de `OpcoesScreen.jsx`/`SetupChart.jsx` NÃO cobre este
// componente — falta `bgCard` (fundo do card), `accentTint` (fundo do CTA) e
// `positive` (cor da manchete de CALL). As três chaves são reais em
// `PALETTE` (App.jsx) nos dois temas; sem elas `T.bgCard` etc. sairiam
// `undefined` e o card perderia fundo/CTA/cor em silêncio, sem erro de build.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "bgCard", "borderSubtle", "borderFaint",
  "textPrimary", "textSecondary", "textMuted", "textFaint", "accent",
  "accentTint", "accentTint10", "positive", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Espelho declarado de App.jsx:256/285/286/1342 (Fase 28, 28-01). Os
// guardiões de `FONTE_LABEL` em `test_fonte_cotacoes_visivel.mjs` e
// `test_fase3_fonte_technicals.mjs` obrigam a definição a continuar
// existindo TAMBÉM em App.jsx; a Task 3 deste plano instala um guardião de
// igualdade caractere a caractere entre as duas cópias — divergir o
// formatador de dinheiro entre dois lugares é exatamente o tipo de erro que
// ninguém vê até virar número errado na tela.
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const price = (n) => (n == null || isNaN(n) ? "—" : nf2.format(n));
const FONTE_LABEL = (source) => (source === "mydata" ? "MyData" : source === "brapi" ? "brapi" : source === "yahoo" ? "Yahoo" : source);

// Fase 17 (Plano 04, FLOW-04): declara fonte e horário do dado da proposta
// (CLAUDE.md princípio 3) — reusa FONTE_LABEL. "Não há proposta" também é
// uma afirmação sobre dado de mercado — renderizado nos DOIS ramos de
// PropostaLastreada, inclusive o vazio (T-17-19).
// Movido de App.jsx:3272-3278 (Fase 28, 28-01) — corpo verbatim.
export function FonteDoDadoProposta({ r, cp }) {
  return (
    <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "10px" }}>
      {r.source ? cp.fontePropostaLinha(FONTE_LABEL(r.source), r.at || "—") : cp.fontePropostaSemDado}
    </div>
  );
}

// Quick 260908-ldg (D-09): chip de liquidez → verbete determinístico. Único
// chip com afordância de toque entre os de `p.chips` — os outros seguem
// `<span>`. `minHeight: 44px` = alvo tátil mínimo, mesmo padrão do resto do
// app; os outros chips continuam pill de 20px porque não são interativos.
// Movido de App.jsx:3286-3305 (Fase 28, 28-01) — corpo verbatim.
export function ChipDaProposta({ c, p, ticker, onVerbeteLiquidez }) {
  if (c.k === "liquidez" && onVerbeteLiquidez) {
    const liq = p.liquidez || {};
    return (
      <button
        type="button"
        onClick={() => onVerbeteLiquidez({ ticker, faixa: liq.faixa, score: liq.score, volume: liq.volume, spreadPct: liq.spreadPct })}
        aria-label="O que é liquidez de opção?"
        style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textSecondary, fontWeight: 700, border: "none", cursor: "pointer", minHeight: "44px", display: "inline-flex", alignItems: "center" }}
      >
        {c.k} <b style={{ fontWeight: 800, color: T.textPrimary, marginLeft: "4px" }}>{c.v}</b>
      </button>
    );
  }
  return (
    <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>
      {c.k} <b style={{ fontWeight: 800, color: T.textPrimary }}>{c.v}</b>
    </span>
  );
}

// Fase 28 (28-01): implementação ÚNICA do caminho de aceite/fechamento
// lastreado — fusão verbatim de `PropostaDaPosicao` em App.jsx (o
// `useState(false)` de App.jsx:4323 + `aceitarCandidato`/`onFecharLastreada`
// de App.jsx:4352-4394). A única substituição de lógica permitida é o
// identificador do closure (`t` em App.jsx, ticker desta posição) pelo
// parâmetro `ticker` do hook, e `r` do closure pelo parâmetro `r` de
// `fecharLastreada`.
//
// A cópia mais antiga e NÃO parametrizada, em `AtivoCard`
// (`onAbrirLastreada`/`onFecharLastreada` lendo `opProposta` do closure),
// NÃO foi tocada por este plano — ela é removida no plano 28-03 junto com o
// card de Watchlist/Radar.
export function useAceiteLastreado({ A, cp, ticker }) {
  // Estado local — cada posição/ativo tem o próprio "em voo", senão aceitar
  // numa posição travaria o botão de outra.
  const [busy, setBusy] = useState(false);

  // Réplica de App.jsx:3292-3321 (App.jsx:4352-4384 antes desta extração) —
  // mesmo corpo, parametrizado pelo candidato clicado (Fase 19, MULTI-02: uma
  // posição pode ter N candidatos, cada um com seu próprio CTA; `busy`
  // continua único, lido por TODOS os candidatos — 19-UI-SPEC.md, Decisão de
  // Interação 1). Corpo enviado ao collar carrega SÓ contractSymbol + lado
  // por perna — prêmio e strike o servidor re-deriva (T-17-24).
  const aceitarCandidato = async (p) => {
    if (!p) return;
    // Quick 260908-ldg (D-03): mesmo confirm de liquidez de App.jsx:3446
    // (onAbrirLastreada) — a put, que hoje não tinha confirm nenhum, passa a
    // ter este quando é DIFÍCIL. Vem ANTES de qualquer confirm de estrutura.
    const liq = p.liquidez || {};
    let aceitaLiquidezDificil = false;
    if (liq.faixa === "DIFÍCIL") {
      if (!liq.aviso) { A.flash("Não foi possível confirmar a liquidez desta operação — tente novamente."); return; }
      if (!window.confirm(liq.aviso)) return;
      aceitaLiquidezDificil = true;
    }
    if (p.tipo === "collar") {
      if (!window.confirm(cp.confirmAbrirCollar(p.contratos, ticker, p.qtyAcoes))) return;
      setBusy(true);
      try {
        await A.abrirCollar({
          underlying: ticker,
          pernasContratos: (p.pernasContratos || []).map((perna) => ({ contractSymbol: perna.contractSymbol, lado: perna.lado })),
          contratos: p.contratos,
          expiration: p.expiration,
          aceitaLiquidezDificil,
        });
      } finally { setBusy(false); }
      return;
    }
    // A confirmação existe pela TRAVA do lastro, não pelo gasto — só a CALL
    // coberta trava ações; a PUT de proteção não trava nada (T-14-24).
    if (p.optionType === "call" && !window.confirm(cp.confirmAbrirCoberta(p.contratos, ticker, p.qtyAcoes))) return;
    setBusy(true);
    try { await A.abrirLastreada({ underlying: ticker, contractSymbol: p.contractSymbol, expiration: p.expiration, contratos: p.contratos, aceitaLiquidezDificil }); }
    finally { setBusy(false); }
  };

  // Réplica de App.jsx:3322-3329 (App.jsx:4387-4394 antes desta extração).
  const fecharLastreada = async (r) => {
    if (!r || !r.proposta) return;
    const p = r.proposta;
    if (!window.confirm(cp.confirmFecharCoberta(price(p.premioTotal), p.qtyAcoes, ticker, p.optionType === "call"))) return;
    setBusy(true);
    try { await A.fecharLastreada({ contractSymbol: p.contractSymbol, contratos: p.contratos }); }
    finally { setBusy(false); }
  };

  return { busy, aceitarCandidato, fecharLastreada };
}

// Fase 14 (Plano 06, 14-UI-SPEC.md) — o CARD DE PROPOSTA: venda coberta ou
// put de proteção prontas, no mesmo formato visual da manchete única do hero
// (Display 17/800, eyebrow 10/800). A MANCHETE e a frase didática são SEMPRE
// `proposta.manchete`/`proposta.didatica` — o motor determinístico decide o
// texto (guardrail CVM, T-14-22); este componente só arruma layout e decide
// CTA × explicação pelo modo (T-14-23, defesa em UI — o servidor recusa com
// 403 mesmo que este código tivesse um bug).
// Movido de App.jsx:3314-3424 (Fase 28, 28-01) — corpo verbatim.
export function PropostaLastreada({ r, operador, cp, busy, onAbrir, onFechar, posAberta, onVerbeteLiquidez }) {
  if (!r) return null; // ainda carregando — silêncio, a proposta é secundária ao card (sem esqueleto)
  if (!r.proposta) {
    return (
      <div style={{ marginTop: "11px", padding: "16px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
        <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint }}>{cp.propostaVaziaTitulo}</div>
        <div style={{ fontSize: "12px", color: T.textMuted, lineHeight: 1.5, marginTop: "4px" }}>
          {r.motivo === "degradado" ? cp.propostaIndisponivelDegradada : r.motivoTexto}
        </div>
        <FonteDoDadoProposta r={r} cp={cp} />
      </div>
    );
  }
  const p = r.proposta;
  const isCall = p.optionType === "call";
  const cor = isCall ? T.positive : T.negative; // NUNCA T.accent — mesma regra da manchete do ativo
  // Fase 17 (Plano 05, FLOW-02/FLOW-03): collar (2 pernas, call + put) —
  // `optionType`/`strike` vêm `null` na proposta de collar (isCall fica
  // false, cor sai T.negative: coerente, é operação defensiva), por isso
  // eyebrow/identificação de contrato/CTA ganham um ramo próprio abaixo.
  const isCollar = p.tipo === "collar";
  const eyebrow = isCollar ? cp.eyebrowPropostaCollar : isCall ? cp.eyebrowPropostaCall : cp.eyebrowPropostaPut;
  const degradado = r.providerStatus !== "ok";
  // Fase 17 (Plano 04, FLOW-01): payoff completo que a Fase 16 já calcula
  // (proposta.estrutura/proposta.caixa) — ausente em proposta de FECHAMENTO
  // (proposta_fechar não devolve estrutura/caixa/precoObjeto), por isso o
  // bloco inteiro é guardado por `est &&` mais abaixo (T-17-21).
  const est = p.estrutura || null;
  // ATENÇÃO: `null * 100 === 0` em JS — só multiplica NÚMERO; null/undefined
  // continuam null e caem em price(null) → "—" (regra "null nunca 0.0"
  // aplicada à UI, T-17-17). Nunca multiplicar campo anulável da estrutura
  // direto por qtyAcoes — sempre passar pelo helper abaixo.
  const porLote = (v) => (typeof v === "number" ? v * (p.qtyAcoes || 0) : null);
  return (
    <div style={{ marginTop: "11px", padding: "16px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
      <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent }}>{eyebrow}</div>
      <div style={{ fontSize: "17px", fontWeight: 800, color: cor, marginTop: "2px" }}>{p.manchete}</div>
      <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "13px", color: T.textSecondary, marginTop: "6px" }}>
        {isCollar
          ? cp.collarPernasLinha(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut))
          : `${p.contratos}× ${isCall ? "CALL" : "PUT"} ${r.ticker} · strike ${price(p.strike)}`}
      </div>
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
      {/* Modo Operador: CTA imperativo. Com posAberta (a proposta atual casa
          com uma posição já lastreada neste contrato), o botão vira fechar. */}
      {operador && (
        <button
          onClick={posAberta ? onFechar : onAbrir}
          disabled={busy || degradado}
          style={{ marginTop: "12px", width: "100%", minHeight: "40px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "12.5px" }}
        >
          {degradado
            ? cp.propostaIndisponivelDegradada
            : posAberta
            ? cp.ctaFecharLastreada(price(p.premioTotal), isCall)
            : isCollar
            ? (p.caixa && p.caixa.fluxo === "credito"
                ? cp.ctaCollarCredito(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut), price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0)))
                : cp.ctaCollarDebito(p.contratos, r.ticker, price(p.strikeCall), price(p.strikePut), price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0))))
            : isCall
            ? cp.ctaVendaCoberta(p.contratos, r.ticker, price(p.strike), price(p.premioTotal))
            : cp.ctaPutProtecao(p.contratos, r.ticker, price(p.strike), price(p.premioTotal))}
        </button>
      )}
      <FonteDoDadoProposta r={r} cp={cp} />
    </div>
  );
}

export default PropostaLastreada;
