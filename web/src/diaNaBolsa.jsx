/**
 * diaNaBolsa.jsx — Fase 51 (51-08): card "Seu dia na bolsa" e faixa de dias de
 * decisão do Acompanhar. Contrato visual: 51-UI-SPEC.md.
 *
 * Regras que este arquivo NÃO quebra:
 *  - Todo texto vem de `diaNaBolsaTxt` (copy.js) ou do payload do servidor; o
 *    front nunca compõe frase e nunca calcula número financeiro (princípio 5).
 *  - Alvo e stop usam O MESMO `estiloChip` neutro (D-04/P-9): a distinção é por
 *    texto e glifo, nunca por cor. T.positive/T.negative só no valor de carteira
 *    da família 2.
 *  - Analytics só com modo/tipo/família/card — nunca ticker nem preço (D-18).
 *  - Sem hex literal: cor só via `ui.T` (tokens do app, passados por prop —
 *    App.jsx não exporta T; entendimento.jsx adota o mesmo espelho local).
 *
 * Este módulo NÃO importa App.jsx (ciclo). A integração é do plano 51-10.
 */
import { useEffect, useRef, useState } from "react";
import { diaNaBolsaTxt } from "./copy.js";
import { track } from "./analytics.js";
import { DISCLAIMERS } from "./disclaimers.js";
import {
  familiasNaOrdem, linhasVisiveis, chaveExploracao,
  contarDiasDecisao, textoDecisao4Sem, faixaDots,
} from "./diaNaBolsaLogica.js";

const SR_ONLY = { position: "absolute", width: "1px", height: "1px", padding: 0, margin: "-1px", overflow: "hidden", clipPath: "inset(50%)", whiteSpace: "nowrap", border: 0 };

// Dedupe por sessão (módulo): 1x por card.
const _shown = new Set();
const _opened = new Set();
const _explored = new Set();

const MARCA_C = "\u0001C\u0001";
const MARCA_I = "\u0001I\u0001";

export function DiaNaBolsaCard({
  estado, payload, mode, ui, podeConvidar,
  onRetry, onConvite, onAbrirPlano, onAbrirAtivo, onAbrirConceito, onDecisao,
}) {
  const { T, MONO, DISPLAY, SUBLINHADO } = ui;
  const txt = (chave, variante, vals) => diaNaBolsaTxt(mode, chave, variante, vals);
  const raiz = useRef(null);
  const [conviteResp, setConviteResp] = useState(null); // null | "aceite" | "recusa"
  const [conviteBusy, setConviteBusy] = useState(false);
  const card = estado === "ok" && payload ? payload.card : null;
  const dataCard = card ? card.data : null;
  const ordemTxt = card && Array.isArray(card.ordem) ? card.ordem.join("") : "";

  const abrir = () => {
    if (!dataCard || _opened.has(dataCard)) return;
    _opened.add(dataCard);
    track("daily_card_opened", { modo: mode, card: dataCard });
  };

  // shown/opened: visível >= 1s (IntersectionObserver + timer), 1x por card/sessão.
  useEffect(() => {
    if (!dataCard || !raiz.current) return undefined;
    if (typeof IntersectionObserver === "undefined") return undefined;
    let timer = null;
    const io = new IntersectionObserver((entradas) => {
      const visivel = entradas.some((e) => e.isIntersecting);
      if (visivel && !timer) {
        timer = setTimeout(() => {
          if (!_shown.has(dataCard)) {
            _shown.add(dataCard);
            track("daily_card_shown", { modo: mode, card: dataCard, familias: ordemTxt });
          }
          abrir();
        }, 1000);
      } else if (!visivel && timer) {
        clearTimeout(timer);
        timer = null;
      }
    }, { threshold: 0.5 });
    io.observe(raiz.current);
    return () => { io.disconnect(); if (timer) clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataCard, mode, ordemTxt]);

  // Confirmação do convite some em 3s.
  useEffect(() => {
    if (!conviteResp) return undefined;
    const t = setTimeout(() => setConviteResp("feito"), 3000);
    return () => clearTimeout(t);
  }, [conviteResp]);

  const explorar = (tipo, familia, alvoId) => {
    const k = chaveExploracao(dataCard, tipo, alvoId);
    if (_explored.has(k)) return;
    _explored.add(k);
    track("daily_card_explored", { modo: mode, card: dataCard, tipo, familia });
  };

  const estiloCaixa = { background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, borderRadius: "10px", padding: "12px", display: "flex", flexDirection: "column", gap: "8px" };
  const labelFam = { fontSize: "11px", fontWeight: 700, lineHeight: 1.4, color: T.textFaint, letterSpacing: "0.05em" };
  const corpo = { fontSize: "13px", fontWeight: 400, lineHeight: 1.5, color: T.textPrimary };
  const numDestaque = { fontFamily: MONO, fontSize: "18px", fontWeight: 700, lineHeight: 1.2 };
  const botaoLinha = { display: "flex", flexDirection: "column", gap: "4px", width: "100%", minHeight: 44, padding: "8px 0", background: "transparent", border: 0, borderTop: `1px solid ${T.borderFaint}`, color: T.textPrimary, textAlign: "left", cursor: "pointer", fontFamily: "inherit" };
  // ÚNICO estilo de chip de desfecho (alvo, stop, expirou, sem gatilho): neutro
  // por desenho — T.negative/T.positive aqui criariam "ganhou/perdeu" visual.
  const estiloChip = { background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, color: T.textPrimary, borderRadius: "999px", padding: "2px 10px", fontSize: "11px", fontWeight: 700, lineHeight: 1.4 };

  if (estado === "carregando") {
    const barra = (h) => ({ height: h, background: T.bgPanel, borderRadius: "8px" });
    return (
      <div aria-busy="true" role="region" aria-label={txt("titulo")}
        style={{ background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderLeft: `3px solid ${T.accent}`, borderRadius: "12px", padding: "16px", minHeight: 148, display: "flex", flexDirection: "column", gap: "12px" }}>
        <span style={SR_ONLY}>{txt("sr_carregando")}</span>
        <div aria-hidden style={barra(16)} />
        <div aria-hidden style={barra(48)} />
        <div aria-hidden style={barra(48)} />
      </div>
    );
  }

  if (estado === "erro") {
    return (
      <div role="status" style={{ background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px", display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
        <span style={{ ...corpo, flex: "1 1 200px" }}>{txt("erro_carregar")}</span>
        <button type="button" onClick={onRetry}
          style={{ minHeight: 44, padding: "0 12px", background: "transparent", border: 0, color: T.accent, fontWeight: 700, fontSize: "13px", cursor: "pointer", fontFamily: "inherit" }}>
          {txt("erro_tentar")}
        </button>
      </div>
    );
  }

  if (!card) return null;
  const familias = familiasNaOrdem(card);
  if (!familias.length) return null;

  const tituloId = "dia-na-bolsa-titulo";
  const fontes = [];
  for (const f of familias) {
    const fonte = card.familias[String(f)].fonte;
    if (fonte && !fontes.includes(fonte)) fontes.push(fonte);
  }
  const carimbo = txt("carimbo", 0, { data: card.dataLabel, hora: card.calculadoEm, fonte: fontes.join(" + ") });
  const chamada = card.chamada ? txt(card.chamada.chave, card.chamada.variante, card.chamada.vals) : "";

  const familia1 = () => {
    const f = card.familias["1"];
    const { visiveis, excedente } = linhasVisiveis(f.linhas, f.excedente);
    const pv = (f.placar && f.placar.vals) || {};
    return (
      <div key="f1" style={estiloCaixa}>
        <div style={labelFam}>{txt("label_f1")}</div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {visiveis.map((l) => {
            const chip = txt(l.chip);
            const r = l.vals && l.vals.R;
            return (
              <button type="button" key={l.ticker + "|" + (l.setup || "")}
                aria-label={[l.ticker, l.setup, chip, r].filter(Boolean).join(", ")}
                onClick={() => {
                  abrir(); explorar("plano", 1, l.ticker);
                  if (onDecisao) onDecisao("plano");
                  if (onAbrirPlano) onAbrirPlano(l.ticker);
                }}
                style={botaoLinha}>
                <span style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px", width: "100%" }}>
                  <span style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700 }}>{l.ticker}</span>
                  {l.setup ? <span style={corpo}>{l.setup}</span> : null}
                  <span style={estiloChip}>{chip}</span>
                  {r ? <span style={{ ...numDestaque, color: T.textPrimary, marginLeft: "auto" }}>{r}</span> : null}
                </span>
                <span style={corpo}>{txt(l.chave, l.variante, l.vals)}</span>
              </button>
            );
          })}
        </div>
        {excedente > 0 ? <div style={{ ...corpo, color: T.textSecondary }}>{txt("mais_n", 0, { n: excedente })}</div> : null}
        <div style={corpo}>
          {txt("placar_semana", 0, { X: MARCA_C + (pv.X ?? "—"), Y: MARCA_C + (pv.Y ?? "—"), Z: MARCA_C + (pv.Z ?? "—"), W: MARCA_C + (pv.W ?? "—") })
            .split(MARCA_C).map((parte, i) => {
              if (i === 0) return parte;
              const m = parte.match(/^(\S+)([\s\S]*)$/);
              return m ? <span key={i}><span style={{ fontFamily: MONO, fontWeight: 700 }}>{m[1]}</span>{m[2]}</span> : parte;
            })}
        </div>
      </div>
    );
  };

  const familia2 = () => {
    const f = card.familias["2"];
    const ci = f.carteiraIbov;
    const cor = (pct) => (pct == null ? T.textMuted : pct > 0 ? T.positive : pct < 0 ? T.negative : T.textMuted);
    let linhaCI = null;
    if (ci) {
      const ibovOk = ci.ibovPct != null;
      const vals = { carteira: MARCA_C, ibov: ibovOk ? MARCA_I : "—" };
      const partes = txt("f2_carteira_ibov", 0, vals).split(/(\u0001[CI]\u0001)/);
      linhaCI = (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px", paddingTop: "8px", borderTop: `1px solid ${T.borderFaint}` }}>
          <div style={{ ...corpo, display: "flex", flexWrap: "wrap", alignItems: "baseline", gap: "4px" }}>
            {partes.map((p, i) => {
              if (p === MARCA_C) return <span key={i} style={{ ...numDestaque, color: cor(ci.carteiraPct) }}>{(ci.vals && ci.vals.carteira) || "—"}</span>;
              if (p === MARCA_I) return <span key={i} style={{ ...numDestaque, color: cor(ci.ibovPct) }}>{(ci.vals && ci.vals.ibov) || "—"}</span>;
              return p ? <span key={i}>{p}</span> : null;
            })}
          </div>
          {!ibovOk ? <div style={{ ...corpo, color: T.textMuted }}>{txt("f2_ibov_indisponivel")}</div> : null}
        </div>
      );
    }
    return (
      <div key="f2" style={estiloCaixa}>
        <div style={labelFam}>{txt("label_f2")}</div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {(f.linhas || []).map((l, i) => (
            <button type="button" key={(l.ticker || "") + (l.hora || "") + i}
              onClick={() => {
                abrir(); explorar("ativo", 2, l.ticker);
                if (onDecisao) onDecisao("plano");
                if (onAbrirAtivo) onAbrirAtivo(l.ticker);
              }}
              style={botaoLinha}>
              <span style={corpo}>{txt(l.chave, l.variante, l.vals)}</span>
            </button>
          ))}
        </div>
        {linhaCI}
      </div>
    );
  };

  const familia3 = () => {
    const f = card.familias["3"];
    const fato = f.fato;
    const frase = txt(fato.chave, fato.variante, fato.vals);
    const rotulo = fato.conceito && fato.conceito.rotulo;
    const pergunta = mode === "estudo" && fato.perguntaChave ? txt(fato.perguntaChave) : "";
    const selo = fato.selo ? txt(fato.selo) : "";
    const abrirConceito = () => {
      abrir(); explorar("conceito", 3, fato.conceito && fato.conceito.id);
      if (onDecisao) onDecisao("card");
      if (onAbrirConceito) onAbrirConceito(fato.conceito);
    };
    // Termo sublinhado dentro da frase, quando o rótulo aparece nela (sem inventar texto).
    const idx = rotulo ? frase.toLowerCase().indexOf(String(rotulo).toLowerCase()) : -1;
    const conteudoFrase = idx >= 0
      ? [frase.slice(0, idx),
        <span key="t" style={SUBLINHADO}>{frase.slice(idx, idx + String(rotulo).length)}</span>,
        frase.slice(idx + String(rotulo).length)]
      : frase;
    return (
      <div key="f3" style={estiloCaixa}>
        <div style={labelFam}>{txt("label_f3")}</div>
        <div style={{ ...corpo, position: "relative" }}>
          <span onClick={rotulo ? abrirConceito : undefined} style={{ cursor: rotulo ? "pointer" : "default" }}>{conteudoFrase}</span>
          {rotulo ? <button type="button" onClick={abrirConceito} aria-label={"O que é " + rotulo + "?"} style={SR_ONLY}>?</button> : null}
        </div>
        {pergunta ? <div style={{ ...corpo, color: T.textSecondary }}>{pergunta}</div> : null}
        {selo ? <div style={labelFam}>{selo}</div> : null}
        {rotulo ? (
          <button type="button" onClick={abrirConceito}
            style={{ minHeight: 44, alignSelf: "flex-start", padding: 0, background: "transparent", border: 0, color: T.accent, fontWeight: 700, fontSize: "13px", cursor: "pointer", fontFamily: "inherit" }}>
            {txt("ver_conceito", 0, { conceito: rotulo })}
          </button>
        ) : null}
      </div>
    );
  };

  const renderFamilia = { 1: familia1, 2: familia2, 3: familia3 };

  const mostrarConvite = !!(payload.convite && podeConvidar) && conviteResp !== "feito";
  const responder = async (aceite) => {
    if (conviteBusy) return;
    setConviteBusy(true);
    try {
      if (onConvite) await onConvite(aceite);
      setConviteResp(aceite ? "aceite" : "recusa");
    } catch (e) {
      // falha: o convite permanece; nada é dado como gravado.
    } finally { setConviteBusy(false); }
  };
  const estiloBotaoConvite = { flex: 1, minHeight: 44, fontWeight: 700, fontSize: "13px", borderRadius: "10px", cursor: "pointer", fontFamily: "inherit" };

  return (
    <div ref={raiz} role="region" aria-labelledby={tituloId} onClickCapture={abrir}
      style={{ background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderLeft: `3px solid ${T.accent}`, borderRadius: "12px", padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
      {card.atrasado ? (
        <div role="status" style={{ background: T.warnTint10, color: T.warn, borderRadius: "8px", padding: "8px 12px", fontSize: "13px", lineHeight: 1.5 }}>
          {txt("atrasado", 0, { data: card.dataLabel })}
        </div>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <div style={labelFam}>{txt("kicker", 0, { data: card.dataLabel })}</div>
        <h2 id={tituloId} style={{ margin: 0, fontFamily: DISPLAY, fontSize: "16px", fontWeight: 700, lineHeight: 1.2, color: T.textPrimary }}>{chamada || txt("titulo")}</h2>
        <div style={labelFam}>{carimbo}</div>
      </div>
      {familias.map((f) => renderFamilia[f]())}
      {mostrarConvite ? (
        conviteResp ? (
          <div role="status" style={{ ...corpo, background: T.accentTint10, borderRadius: "10px", padding: "12px" }}>
            {txt(conviteResp === "aceite" ? "convite_ok_aceite" : "convite_ok_recusa")}
          </div>
        ) : (
          <div style={{ background: T.accentTint10, borderRadius: "10px", padding: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <div style={corpo}>{txt("convite_pergunta")}</div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button type="button" disabled={conviteBusy} onClick={() => responder(true)}
                style={{ ...estiloBotaoConvite, background: T.accent, color: T.onAccent, border: `1px solid ${T.accent}` }}>
                {txt("convite_aceitar")}
              </button>
              <button type="button" disabled={conviteBusy} onClick={() => responder(false)}
                style={{ ...estiloBotaoConvite, background: "transparent", color: T.textSecondary, border: `1px solid ${T.borderSubtle}` }}>
                {txt("convite_recusar")}
              </button>
            </div>
          </div>
        )
      ) : null}
      <div style={labelFam}>{DISCLAIMERS.short}</div>
    </div>
  );
}

export function FaixaDecisao({ diasDecisao, ultimas4Semanas, mode, ui }) {
  const { T, MONO } = ui;
  const x = contarDiasDecisao(diasDecisao, ultimas4Semanas);
  const texto = textoDecisao4Sem(mode, x, diaNaBolsaTxt);
  const dots = faixaDots(diasDecisao, ultimas4Semanas);
  // O número destacado em MONO 700 dentro do texto vindo do copy.
  const partes = x >= 2 ? texto.split(String(x)) : [texto];
  const corpo = { fontSize: "13px", fontWeight: 400, lineHeight: 1.5, color: T.textPrimary };
  const dot = (d) => {
    if (d.tipo === "decisao") return <span key={d.data} style={{ width: 8, height: 8, borderRadius: "50%", background: T.textSecondary }} />;
    if (d.tipo === "sem_pregao") {
      return <span key={d.data} style={{ width: 8, height: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ width: 4, height: 4, borderRadius: "50%", background: T.borderFaint }} />
      </span>;
    }
    return <span key={d.data} style={{ width: 8, height: 8, borderRadius: "50%", border: `1px solid ${T.borderSubtle}`, boxSizing: "border-box" }} />;
  };
  return (
    <div aria-label={texto} role="group" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={corpo}>
        {partes.length > 1
          ? <>{partes[0]}<span style={{ fontFamily: MONO, fontWeight: 700 }}>{x}</span>{partes.slice(1).join(String(x))}</>
          : texto}
      </div>
      {dots.length ? (
        <div aria-hidden style={{ display: "grid", gridTemplateColumns: "repeat(7, 8px)", gap: "4px" }}>
          {dots.map(dot)}
        </div>
      ) : null}
    </div>
  );
}
