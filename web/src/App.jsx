import { useState, useEffect, useRef, useCallback, useMemo, createContext, useContext } from "react";
import { store, isNative, auth } from "./persistence.js";
<<<<<<< HEAD
import { hasSession } from "./sync.js"; // BLOCO 2: welcome exibe estado da sessão salva
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
import { defaultLlmPrompts } from "./catalog.js";
import { testServer, describeRuntimeConfig } from "./api.js";
import { createChart, ColorType, CrosshairMode, LineStyle } from "lightweight-charts";
import { sampleTechnicals } from "./demo.js";
import { DISCLAIMERS } from "./disclaimers.js";
import { canAddTicker, canAnalyze } from "./plan.js";
<<<<<<< HEAD
import { portfolioMetrics, dayReturnPct, equityCurve, markPrice } from "./finance.js";
import * as notify from "./notify.js";

/* =============================================================================
   BolsIA — simulador EDUCACIONAL de paper trading da B3.
   Identidade "mesa de operações": fundo quase-preto, acento índigo (IA), números mono.
=======
import * as notify from "./notify.js";

/* =============================================================================
   B3 Agente — simulador EDUCACIONAL de paper trading da B3.
   Identidade "mesa de operações": fundo quase-preto, acento âmbar, números mono.
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
   Todo o estado é persistido no backend (sobrevive a reinício). A análise
   técnica é feita PELA LLM configurada, sob demanda, por ativo.
   Dinheiro simulado. Nada aqui é recomendação de investimento.
============================================================================= */

// Identidade "mesa de operações" em dois esquemas. DARK = mesa noturna;
// LIGHT = mesma identidade adaptada para leitura confortável (cores semânticas,
// contraste adequado — boas práticas iOS). DOM usa var(--x); gráficos (canvas/
// SVG) usam a paleta REAL via ThemeCtx, pois var() não resolve em canvas.
const PALETTE = {
  dark: {
    bgBase: "#0b0e14", bgPanel: "#0d111a", bgCard: "#11151c", bgToast: "#1b2230",
    borderSubtle: "#232a35", borderFaint: "#1b212b", borderDashed: "#2f3a48", borderToast: "#2b3340",
    textPrimary: "#e7ecf3", textSecondary: "#c3ccd8", textMuted: "#9aa6b6", textDim: "#8a96a6",
    textFaint: "#5b6675", textBright: "#dfe6ef",
<<<<<<< HEAD
    accent: "#3B82F6", accentSoft: "#9DBEFF", positive: "#34d399", negative: "#fb7185",
    knob: "#1b212b", navDotIdle: "#2b333f", confirmOkText: "#06231a",
    accentTint: "rgba(59,130,246,0.14)", accentTintHi: "rgba(59,130,246,0.26)", accentTint10: "rgba(59,130,246,0.10)",
    positiveTint: "rgba(52,211,153,0.12)", positiveTint10: "rgba(52,211,153,0.10)",
    negativeTint: "rgba(251,113,133,0.12)", negativeTint10: "rgba(251,113,133,0.10)",
    scrim: "rgba(5,7,11,0.68)",
    chartGrid: "rgba(255,255,255,0.04)", chartBorder: "rgba(255,255,255,0.08)", chartAxis: "#6b7384", lineSubtle: "rgba(255,255,255,0.18)", onAccent: "#ffffff",
=======
    accent: "#f0b429", accentSoft: "#f0e3c2", positive: "#34d399", negative: "#fb7185",
    knob: "#1b212b", navDotIdle: "#2b333f", confirmOkText: "#06231a",
    accentTint: "rgba(240,180,41,0.12)", accentTintHi: "rgba(240,180,41,0.22)", accentTint10: "rgba(240,180,41,0.10)",
    positiveTint: "rgba(52,211,153,0.12)", positiveTint10: "rgba(52,211,153,0.10)",
    negativeTint: "rgba(251,113,133,0.12)", negativeTint10: "rgba(251,113,133,0.10)",
    scrim: "rgba(5,7,11,0.68)",
    chartGrid: "rgba(255,255,255,0.04)", chartBorder: "rgba(255,255,255,0.08)", chartAxis: "#6b7384", lineSubtle: "rgba(255,255,255,0.18)", onAccent: "#0b0e14",
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  },
  light: {
    bgBase: "#f3f4f7", bgPanel: "#ffffff", bgCard: "#ffffff", bgToast: "#222936",
    borderSubtle: "#e3e6ec", borderFaint: "#edeff3", borderDashed: "#d2d8e0", borderToast: "#39414f",
    textPrimary: "#11161d", textSecondary: "#2d3742", textMuted: "#5d6775", textDim: "#6b7480",
    textFaint: "#98a1ad", textBright: "#0a0e13",
<<<<<<< HEAD
    accent: "#2563EB", accentSoft: "#1d4ed8", positive: "#10976a", negative: "#d6455f",
    knob: "#dfe3e9", navDotIdle: "#c4cad3", confirmOkText: "#ffffff",
    accentTint: "rgba(37,99,235,0.12)", accentTintHi: "rgba(37,99,235,0.20)", accentTint10: "rgba(37,99,235,0.10)",
    positiveTint: "rgba(16,151,106,0.12)", positiveTint10: "rgba(16,151,106,0.10)",
    negativeTint: "rgba(214,69,95,0.12)", negativeTint10: "rgba(214,69,95,0.10)",
    scrim: "rgba(15,20,28,0.45)",
    chartGrid: "rgba(0,0,0,0.05)", chartBorder: "rgba(0,0,0,0.10)", chartAxis: "#8a93a0", lineSubtle: "rgba(0,0,0,0.16)", onAccent: "#ffffff",
=======
    accent: "#b97e09", accentSoft: "#7a5c12", positive: "#10976a", negative: "#d6455f",
    knob: "#dfe3e9", navDotIdle: "#c4cad3", confirmOkText: "#ffffff",
    accentTint: "rgba(185,126,9,0.12)", accentTintHi: "rgba(185,126,9,0.20)", accentTint10: "rgba(185,126,9,0.10)",
    positiveTint: "rgba(16,151,106,0.12)", positiveTint10: "rgba(16,151,106,0.10)",
    negativeTint: "rgba(214,69,95,0.12)", negativeTint10: "rgba(214,69,95,0.10)",
    scrim: "rgba(15,20,28,0.45)",
    chartGrid: "rgba(0,0,0,0.05)", chartBorder: "rgba(0,0,0,0.10)", chartAxis: "#8a93a0", lineSubtle: "rgba(0,0,0,0.16)", onAccent: "#1a1205",
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  },
};
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
// T mantém as MESMAS chaves, mas aponta para var(--x) — nenhum uso T.x muda.
const T = Object.fromEntries(Object.keys(PALETTE.dark).map((k) => [k, `var(${VARKEY(k)})`]));
const themeVarBlock = (name) => Object.entries(PALETTE[name]).map(([k, v]) => `${VARKEY(k)}:${v}`).join(";");
const THEME_CSS = `.b3-theme-dark{${themeVarBlock("dark")}} .b3-theme-light{${themeVarBlock("light")}}`;
const ThemeCtx = createContext("dark");
const useThemeKey = () => useContext(ThemeCtx);
const usePalette = () => PALETTE[useContext(ThemeCtx)] || PALETTE.dark;

// Logo do app: "mesa de operações" — candles âmbar sobre fundo escuro, com uma
// fita (ticker tape). Mantém o fundo escuro nos dois temas (identidade de ícone).
function LogoMark({ size = 32, radius }) {
  const r = radius != null ? radius : Math.round(size * 0.26);
<<<<<<< HEAD
  const rx = (r / size) * 32;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden role="img" style={{ display: "block", flex: "none" }}>
      <defs>
        <linearGradient id="bolsiaLM" x1="6" y1="3" x2="26" y2="29" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#3B82F6" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="32" height="32" rx={rx} fill="#0b0e14" />
      <rect x="0.6" y="0.6" width="30.8" height="30.8" rx={rx - 0.6} fill="none" stroke="#3B82F6" strokeOpacity="0.30" strokeWidth="1.1" />
      {/* pavio do candle */}
      <rect x="15.1" y="10.5" width="1.8" height="15" rx="0.9" fill="url(#bolsiaLM)" />
      {/* corpo do candle */}
      <rect x="11.6" y="14.4" width="8.8" height="9.6" rx="2.5" fill="url(#bolsiaLM)" />
      {/* spark de IA na ponta */}
      <path d="M16 3.4 C16.5 7.2 17.6 8.3 21.4 8.8 C17.6 9.3 16.5 10.4 16 14.2 C15.5 10.4 14.4 9.3 10.6 8.8 C14.4 8.3 15.5 7.2 16 3.4 Z" fill="url(#bolsiaLM)" />
      <circle cx="16" cy="8.8" r="0.95" fill="#fff" fillOpacity="0.9" />
=======
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden role="img" style={{ display: "block", flex: "none" }}>
      <rect x="0" y="0" width="32" height="32" rx={(r / size) * 32} fill="#0b0e14" />
      <rect x="0.6" y="0.6" width="30.8" height="30.8" rx={(r / size) * 32 - 0.6} fill="none" stroke="#f0b429" strokeOpacity="0.25" strokeWidth="1.2" />
      <line x1="5" y1="23.5" x2="27" y2="23.5" stroke="#3a4250" strokeWidth="1.4" strokeLinecap="round" />
      {/* candle de alta */}
      <line x1="11" y1="6.5" x2="11" y2="21" stroke="#f0b429" strokeWidth="1.5" strokeLinecap="round" />
      <rect x="8.6" y="10" width="4.8" height="8.4" rx="1.2" fill="#f0b429" />
      {/* candle menor */}
      <line x1="21" y1="9.5" x2="21" y2="22" stroke="#f0b429" strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.85" />
      <rect x="18.6" y="13.4" width="4.8" height="6.2" rx="1.2" fill="#f0b429" fillOpacity="0.85" />
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    </svg>
  );
}
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const SANS = "-apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif";
<<<<<<< HEAD
// BolsIA: "IA" recebe o gradiente da marca (azul → ciano).
const IA_GRAD = { background: "linear-gradient(135deg,#3B82F6,#22D3EE)", WebkitBackgroundClip: "text", backgroundClip: "text", WebkitTextFillColor: "transparent" };
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026

const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const price = (n) => (n == null || isNaN(n) ? "—" : nf2.format(n));
const money = (n) => (n == null || isNaN(n) ? "—" : "R$ " + nf2.format(n));
const moneySigned = (n) => (n == null || isNaN(n) ? "—" : (n >= 0 ? "+R$ " : "−R$ ") + nf2.format(Math.abs(n)));
const pct = (n) => (n == null || isNaN(n) ? "—" : (n >= 0 ? "+" : "−") + Math.abs(n).toFixed(2).replace(".", ",") + "%");

// Estimativa educacional de stop/alvo a partir do PERFIL + preço atual.
// Usada como fallback quando a IA (servidor) não devolve `proposal` — assim a
// função é útil mesmo offline. É deterministica e claramente rotulada (não-IA).
function localProposal(price, profile) {
  if (!(price > 0)) return null;
  const pf = profile || {};
  const tol = Math.min(20, Math.max(0.5, Number(pf.toleranciaPerdaPct) || 2)); // % perda/operação
  const riskMult = pf.risco === "conservador" ? 0.8 : pf.risco === "agressivo" ? 1.4 : 1.0;
  const stopFrac = Math.min(0.25, (tol / 100) * riskMult);   // mais conservador → mais próximo
  const rr = pf.horizonte === "intraday" ? 1.5 : pf.horizonte === "posicao" ? 2.5 : 2.0;
  const stop = +(price * (1 - stopFrac)).toFixed(2);
  const alvo = +(price * (1 + stopFrac * rr)).toFixed(2);
  const rationale = `Perfil ${pf.risco || "moderado"} / horizonte ${pf.horizonte || "swing"}: stop ~${(stopFrac * 100).toFixed(1)}% abaixo do preço para limitar a perda, e alvo na proporção ${rr.toFixed(1)}:1 sobre o risco.`;
  return { stop, alvo, rr, stopFrac, rationale };
}

const card = { background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderRadius: "12px" };
const kicker = { fontSize: "10px", color: T.textFaint, letterSpacing: "0.06em" };
const field = { width: "100%", padding: "10px 11px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", color: T.textPrimary };

function GlobalStyle() {
  return (
    <style>{`
      ${THEME_CSS}
      .b3-theme-dark{ color-scheme:dark; }
      .b3-theme-light{ color-scheme:light; }
      html,body,#root{ height:100%; }
      body{ margin:0; background:${T.bgBase}; color:${T.textPrimary}; }
      .b3 *{ box-sizing:border-box; }
      .b3-shell{ height:100vh; height:100dvh; }
      .b3{ transition:background .25s ease, color .25s ease; }
      .b3 button{ font:inherit; color:inherit; cursor:pointer; transition:filter .12s ease, transform .05s ease; }
      .b3 button:active:not(:disabled){ transform:translateY(1px); filter:brightness(1.12); }
      .b3 button:disabled{ cursor:default; opacity:.6; }
      .b3 input,.b3 textarea,.b3 select{ font:inherit; }
      .b3 textarea{ resize:vertical; }
      .b3 :focus-visible{ outline:2px solid ${T.accent}; outline-offset:2px; border-radius:4px; }
      .b3 ::-webkit-scrollbar{ width:10px; height:10px; }
      .b3 ::-webkit-scrollbar-thumb{ background:${T.borderSubtle}; border-radius:6px; }
      @keyframes b3spin{ to{ transform:rotate(360deg); } }
      .b3 .spin{ animation:b3spin .8s linear infinite; }
      @keyframes b3shimmer{ 0%{ background-position:-200px 0; } 100%{ background-position:200px 0; } }
      .b3 .sk{ border-radius:6px; background:linear-gradient(90deg, ${T.bgPanel} 25%, ${T.borderSubtle} 37%, ${T.bgPanel} 63%); background-size:400px 100%; animation:b3shimmer 1.2s linear infinite; }
      @keyframes b3tt{ from{ transform:translateX(0); } to{ transform:translateX(-50%); } }
      .b3 .tt-track{ animation:b3tt 52s linear infinite; }
      @media (prefers-reduced-motion: reduce){ .b3 .tt-track,.b3 .spin{ animation:none !important; } }
    `}</style>
  );
}

function Toggle({ on, onClick, label }) {
  const s = { bg: on ? T.accentTintHi : T.knob, border: on ? T.accent : T.borderSubtle, knob: on ? "24px" : "2px", color: on ? T.accent : T.textFaint };
  return (
    <button onClick={onClick} role="switch" aria-checked={on} aria-label={label}
      style={{ position: "relative", width: "50px", height: "28px", borderRadius: "16px", border: `1px solid ${s.border}`, background: s.bg, flex: "none" }}>
      <span style={{ position: "absolute", top: "2px", left: s.knob, width: "22px", height: "22px", borderRadius: "50%", background: s.color, transition: "left .15s" }} />
    </button>
  );
}

function Spinner({ size = 16, color = T.accent }) {
  return <span className="spin" style={{ display: "inline-block", width: size, height: size, border: `2px solid ${color}`, borderTopColor: "transparent", borderRadius: "50%" }} />;
}

// Botão-ícone discreto para o cabeçalho (ações secundárias).
function IconBtn({ label, onClick, busy, disabled, children, primary }) {
  return (
    <button onClick={onClick} disabled={disabled || busy} aria-label={label} title={label}
      style={{ width: "42px", height: "42px", borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", lineHeight: 1, border: `1px solid ${primary ? T.accent : T.borderSubtle}`, background: primary ? T.accentTint : T.bgPanel, color: primary ? T.accent : T.textSecondary }}>
      <span className={busy ? "spin" : undefined} style={{ display: "inline-block" }}>{children}</span>
    </button>
  );
}

// Marcador MÍNIMO junto ao conteúdo de IA (o texto completo vive em "Sobre").
const AiNote = ({ at }) => (
  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "10px", color: T.textFaint, marginTop: "10px" }}>
    <span aria-hidden style={{ fontWeight: 700 }}>ⓘ</span>
    <span>Conteúdo educacional de IA · não é recomendação{at ? " · " + at : ""}</span>
  </div>
);

// Ponto ÚNICO do aviso completo (acessível pela Config e pelo onboarding).
function AboutModal({ onClose }) {
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 70, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "460px", ...card, padding: "22px", maxHeight: "86vh", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
          <LogoMark size={32} />
          <div style={{ fontSize: "17px", fontWeight: 700 }}>Sobre · Aviso legal</div>
        </div>
        <p style={{ color: T.textSecondary, fontSize: "13.5px", lineHeight: 1.6, margin: "0 0 12px" }}>{DISCLAIMERS.appBanner}</p>
        <p style={{ color: T.textMuted, fontSize: "13px", lineHeight: 1.6, margin: "0 0 12px" }}>{DISCLAIMERS.aiContent}</p>
        <p style={{ color: T.textMuted, fontSize: "13px", lineHeight: 1.6, margin: "0 0 18px" }}>
          As cotações vêm do Yahoo Finance e podem atrasar ou conter imprecisões. Stop, alvo e
          recomendações são exercícios didáticos calculados a partir do seu perfil e de dados
          passados — desempenho passado não garante resultado futuro.
        </p>
        <button onClick={onClose} style={{ width: "100%", padding: "12px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "14px" }}>Entendi</button>
      </div>
    </div>
  );
}

function OnboardingModal({ name, budget, risco, onComplete }) {
  const [v, setV] = useState(name || "");
  const [bud, setBud] = useState(Number.isFinite(budget) ? budget : 10000);
  const [risk, setRisk] = useState(risco || "moderado");
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 80, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div style={{ width: "100%", maxWidth: "460px", ...card, padding: "26px 24px", maxHeight: "92vh", overflowY: "auto" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", marginBottom: "16px" }}>
          <LogoMark size={60} />
<<<<<<< HEAD
          <div style={{ fontSize: "21px", fontWeight: 800, marginTop: "12px", letterSpacing: "-0.01em" }}>Bols<span style={IA_GRAD}>IA</span></div>
=======
          <div style={{ fontSize: "21px", fontWeight: 800, marginTop: "12px", letterSpacing: "-0.01em" }}>B3 Agente</div>
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          <div style={{ fontSize: "13px", color: T.accent, fontWeight: 600, marginTop: "2px" }}>sua mesa de operações para aprender</div>
        </div>
        <p style={{ color: T.textSecondary, fontSize: "13px", lineHeight: 1.6, margin: "0 0 16px", textAlign: "center" }}>
          Treine a operar a bolsa com <b>cotações reais</b> e <b>dinheiro simulado</b>, com uma
          <b> IA</b> que explica o raciocínio. É uma ferramenta <b>educacional</b> — nada aqui é
          recomendação de investimento.
        </p>
        <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Como prefere ser chamado? (opcional)</label>
        <input value={v} onChange={(e) => setV(e.target.value)} placeholder="Seu nome" maxLength={40} style={{ ...field, marginBottom: "14px" }} />
        <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Orçamento simulado para começar (R$)</label>
        <input type="number" min="100" step="100" inputMode="decimal" value={bud} onChange={(e) => setBud(parseFloat(e.target.value) || 0)} style={{ ...field, fontFamily: MONO, fontWeight: 700, marginBottom: "14px" }} />
        <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Seu perfil de risco</label>
        <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
          {["conservador", "moderado", "agressivo"].map((r) => (
            <button key={r} onClick={() => setRisk(r)} style={{ flex: 1, padding: "10px 6px", borderRadius: "10px", border: `1px solid ${risk === r ? T.accent : T.borderSubtle}`, background: risk === r ? T.accentTint : T.bgPanel, color: risk === r ? T.accent : T.textMuted, fontWeight: 700, fontSize: "12px", textTransform: "capitalize" }}>{r}</button>
          ))}
        </div>
        <button onClick={() => onComplete({ name: v.trim(), budget: bud, risco: risk })} style={{ width: "100%", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px" }}>Entrar na mesa</button>
        <p style={{ color: T.textFaint, fontSize: "11px", lineHeight: 1.5, margin: "12px 0 0", textAlign: "center" }}>Você pode rever isto e o aviso legal em Perfil → Sobre.</p>
      </div>
    </div>
  );
}

// FASE 2 — conta OPCIONAL (decisão A). Logado: mostra e-mail, sair e excluir
// conta. Anônimo: login/registro por e-mail+senha. Tudo guardado: se algo
// falhar, o modal mostra o erro e o app segue funcionando sem login.
<<<<<<< HEAD
function AppleGlyph() {
  return (
    <svg width="15" height="17" viewBox="0 0 14 16" fill="currentColor" aria-hidden style={{ flex: "none" }}>
      <path d="M11.3 8.5c0-1.7 1.4-2.5 1.4-2.6-.8-1.1-2-1.3-2.4-1.3-1-.1-2 .6-2.5.6s-1.3-.6-2.2-.6c-1.1 0-2.2.7-2.7 1.7-1.2 2-.3 5 .8 6.6.6.8 1.2 1.7 2.1 1.7.8 0 1.1-.5 2.1-.5s1.3.5 2.2.5 1.4-.8 2-1.6c.6-.9.9-1.8.9-1.8s-1.7-.7-1.7-2.4zM9.7 3.3c.5-.6.8-1.4.7-2.3-.7 0-1.6.5-2.1 1.1-.5.5-.9 1.4-.7 2.2.8.1 1.6-.4 2.1-1z" />
    </svg>
  );
}
function GoogleGlyph() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" aria-hidden style={{ flex: "none" }}>
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.71-1.57 2.68-3.89 2.68-6.62z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z" />
      <path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z" />
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.9 11.43 0 9 0A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z" />
    </svg>
  );
}
// Botões de login social (UI). Caminho nativo (Apple/Google) fica pronto: quando
// os plugins Capacitor expuserem `window.__bolsiaSocial.{apple,google}()` para
// devolver o idToken, o clique chama ctx.oauth e autentica. Sem isso (estado
// atual), mostra um aviso amigável e mantém o e-mail como caminho principal.
function SocialAuthButtons({ ctx }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const go = async (provider) => {
    setNote("");
    const bridge = (typeof window !== "undefined" && window.__bolsiaSocial) || null;
    if (bridge && typeof bridge[provider] === "function") {
      setBusy(provider);
      try {
        const idToken = await bridge[provider]();
        if (ctx && ctx.oauth) await ctx.oauth({ provider, idToken });
      } catch (e) { setNote((e && e.message) || "Falha no login social."); }
      finally { setBusy(""); }
      return;
    }
    setNote("Login com " + (provider === "apple" ? "a Apple" : "o Google") + " chega em breve — por enquanto, use o e-mail abaixo.");
  };
  const btn = { width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "9px", padding: "12px", borderRadius: "11px", fontWeight: 700, fontSize: "14px", marginBottom: "10px" };
  return (
    <div>
      <button onClick={() => go("apple")} disabled={!!busy} aria-label="Continuar com a Apple" style={{ ...btn, border: "none", background: "#000", color: "#fff", opacity: busy && busy !== "apple" ? 0.6 : 1 }}>
        <AppleGlyph /> Continuar com a Apple
      </button>
      <button onClick={() => go("google")} disabled={!!busy} aria-label="Continuar com o Google" style={{ ...btn, border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, opacity: busy && busy !== "google" ? 0.6 : 1 }}>
        <GoogleGlyph /> Continuar com o Google
      </button>
      {note && <p style={{ color: T.textMuted, fontSize: "11.5px", lineHeight: 1.5, margin: "2px 0 0", textAlign: "center" }}>{note}</p>}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", color: T.textFaint, fontSize: "11px", margin: "14px 0" }}>
        <span style={{ flex: 1, height: "1px", background: T.borderSubtle }} /> ou com e-mail <span style={{ flex: 1, height: "1px", background: T.borderSubtle }} />
      </div>
    </div>
  );
}
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
function AuthModal({ ctx, onClose }) {
  const user = (ctx && ctx.authUser) || null;
  const [mode, setMode] = useState("login");   // login | register
  const [email, setEmail] = useState((user && user.email) || "");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [confirmDel, setConfirmDel] = useState(false);

  const run = async (fn) => {
    setErr(""); setBusy(true);
    try { await fn(); onClose && onClose(); }
    catch (e) { setErr((e && e.message) || String(e)); }
    finally { setBusy(false); }
  };

  const wrap = (children) => (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 82, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "420px", ...card, padding: "24px", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
          <LogoMark size={30} />
          <div style={{ fontSize: "17px", fontWeight: 800 }}>{user ? "Sua conta" : (mode === "login" ? "Entrar" : "Criar conta")}</div>
        </div>
        {children}
        {err && <p style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5, margin: "12px 0 0", whiteSpace: "pre-wrap" }}>{err}</p>}
      </div>
    </div>
  );

  if (user) {
    return wrap(
      <div>
        <div style={{ fontSize: "13px", color: T.textMuted, marginBottom: "4px" }}>Conectado como</div>
        <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "18px", wordBreak: "break-all" }}>{user.email || user.name || user.id}</div>
        <p style={{ color: T.textMuted, fontSize: "12px", lineHeight: 1.6, margin: "0 0 16px" }}>
          Sua carteira simulada fica salva na sua conta e sobrevive a trocar de aparelho. Conteúdo educacional — nada aqui é recomendação de investimento.
        </p>
        <button disabled={busy} onClick={() => run(() => ctx.logout())} style={{ width: "100%", padding: "12px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontWeight: 700, fontSize: "14px", marginBottom: "10px" }}>Sair</button>
        {!confirmDel ? (
          <button disabled={busy} onClick={() => setConfirmDel(true)} style={{ width: "100%", padding: "12px", borderRadius: "10px", border: `1px solid ${T.negative}`, background: "transparent", color: T.negative, fontWeight: 700, fontSize: "13.5px" }}>Excluir conta</button>
        ) : (
          <div style={{ border: `1px solid ${T.negative}`, borderRadius: "10px", padding: "12px" }}>
            <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5, marginBottom: "10px" }}>Isso apaga <b>todos os dados</b> da sua conta no servidor, de forma permanente. Tem certeza?</div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button disabled={busy} onClick={() => setConfirmDel(false)} style={{ flex: 1, padding: "10px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textMuted, fontWeight: 700, fontSize: "13px" }}>Cancelar</button>
              <button disabled={busy} onClick={() => run(() => ctx.deleteAccount())} style={{ flex: 1, padding: "10px", borderRadius: "9px", border: "none", background: T.negative, color: "#fff", fontWeight: 800, fontSize: "13px" }}>{busy ? "Excluindo…" : "Excluir"}</button>
            </div>
          </div>
        )}
      </div>
    );
  }

  const submit = () => run(async () => {
    if (mode === "register") await ctx.register({ email, password, name });
    else await ctx.login({ email, password });
  });

  return wrap(
    <div>
      <p style={{ color: T.textMuted, fontSize: "12.5px", lineHeight: 1.6, margin: "0 0 16px" }}>
        Criar conta é <b>opcional</b> — o app funciona sem login. Com conta, sua carteira fica salva e acompanha você entre aparelhos.
      </p>
<<<<<<< HEAD
      <SocialAuthButtons ctx={ctx} />
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      {mode === "register" && (
        <>
          <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome (opcional)</label>
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={40} placeholder="Seu nome" style={{ ...field, marginBottom: "12px" }} />
        </>
      )}
      <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>E-mail</label>
      <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoCapitalize="none" autoCorrect="off" placeholder="voce@exemplo.com" style={{ ...field, marginBottom: "12px" }} />
      <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Senha</label>
      <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="ao menos 8 caracteres" style={{ ...field, marginBottom: "18px" }} />
      <button disabled={busy || !email || !password} onClick={submit} style={{ width: "100%", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px", opacity: (busy || !email || !password) ? 0.6 : 1 }}>
        {busy ? "…" : (mode === "login" ? "Entrar" : "Criar conta")}
      </button>
      <button onClick={() => { setErr(""); setMode(mode === "login" ? "register" : "login"); }} style={{ width: "100%", marginTop: "12px", padding: "6px", background: "transparent", border: "none", color: T.accent, fontWeight: 600, fontSize: "13px" }}>
        {mode === "login" ? "Não tem conta? Criar uma" : "Já tem conta? Entrar"}
      </button>
    </div>
  );
}

/* -------------------------------- Chrome --------------------------------- */
// Tela de ABERTURA (welcome = login). Mantém o local-first (decisão A): o link
// "usar sem conta" no rodapé leva ao onboarding anônimo (orçamento/risco).
// Self-contained e undefined-safe — não acessa campos de `data`.
function WelcomeAuthScreen({ ctx, onAuthed, onSkip }) {
  const [mode, setMode] = useState("register"); // criar conta em destaque
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
<<<<<<< HEAD
  // BLOCO 2: boot gate. Se a sessão salva já foi restaurada (auth.me), mostra
  // "Conectado como X" + Entrar. Se há token salvo mas o /auth/me ainda não
  // respondeu, mostra o formulário com um aviso de restauração — quando a
  // resposta chegar, esta tela troca sozinha para o estado conectado.
  const user = ctx.authUser;
  const restoring = !user && hasSession();
  const userLabel = user ? ((user.name || "").trim() || user.email || "sua conta") : "";
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      if (mode === "register") await ctx.register({ email, password, name });
      else await ctx.login({ email, password });
      onAuthed && onAuthed();
    } catch (e) { setErr((e && e.message) || String(e)); }
    finally { setBusy(false); }
  };
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 85, background: T.bgBase, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px", overflowY: "auto" }}>
      <div style={{ width: "100%", maxWidth: "420px", ...card, padding: "26px 24px" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", marginBottom: "18px" }}>
          <LogoMark size={56} />
<<<<<<< HEAD
          <div style={{ fontSize: "21px", fontWeight: 800, marginTop: "10px", letterSpacing: "-0.01em" }}>Bols<span style={IA_GRAD}>IA</span></div>
          <div style={{ fontSize: "13px", color: T.accent, fontWeight: 600, marginTop: "2px" }}>Dados reais da bolsa · capital simulado</div>
          <p style={{ color: T.textMuted, fontSize: "12.5px", lineHeight: 1.6, margin: "12px 0 0" }}>
            Treine operações com <b>cotações reais</b> e <b>dinheiro simulado</b>, com uma <b>IA</b> que explica cada decisão. Conteúdo <b>educacional</b> — não é recomendação de investimento.
          </p>
        </div>
        {user ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "13px 14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, marginBottom: "16px" }}>
              <div aria-hidden style={{ width: "38px", height: "38px", borderRadius: "50%", background: T.accentTint, color: T.accent, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "16px", flex: "none" }}>{userLabel.slice(0, 1).toUpperCase()}</div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: "11px", color: T.textFaint, letterSpacing: "0.05em" }}>CONECTADO COMO</div>
                <div style={{ fontSize: "14px", fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{userLabel}</div>
              </div>
            </div>
            <button onClick={() => onAuthed && onAuthed()} style={{ width: "100%", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px" }}>
              Entrar
            </button>
          </>
        ) : (
          <>
            {restoring && (
              <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "9px 12px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textMuted, fontSize: "12px", marginBottom: "14px" }}>
                <span className="spin" style={{ display: "inline-block" }}>↻</span> Restaurando sessão salva… Se preferir, entre abaixo.
              </div>
            )}
            <SocialAuthButtons ctx={ctx} />
            {mode === "register" && (
              <>
                <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome (opcional)</label>
                <input value={name} onChange={(e) => setName(e.target.value)} maxLength={40} placeholder="Seu nome" style={{ ...field, marginBottom: "12px" }} />
              </>
            )}
            <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>E-mail</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoCapitalize="none" autoCorrect="off" placeholder="voce@exemplo.com" style={{ ...field, marginBottom: "12px" }} />
            <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Senha</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="ao menos 8 caracteres" style={{ ...field, marginBottom: "18px" }} />
            <button disabled={busy || !email || !password} onClick={submit} style={{ width: "100%", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px", opacity: (busy || !email || !password) ? 0.6 : 1 }}>
              {busy ? "…" : (mode === "register" ? "Criar conta" : "Entrar")}
            </button>
            <button onClick={() => { setErr(""); setMode(mode === "register" ? "login" : "register"); }} style={{ width: "100%", marginTop: "10px", padding: "6px", background: "transparent", border: "none", color: T.accent, fontWeight: 600, fontSize: "13px" }}>
              {mode === "register" ? "Já tem conta? Entrar" : "Criar uma conta"}
            </button>
            {err && <p style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5, margin: "12px 0 0", whiteSpace: "pre-wrap" }}>{err}</p>}
            <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: `1px solid ${T.borderSubtle}`, textAlign: "center" }}>
              <button onClick={() => onSkip && onSkip()} style={{ background: "transparent", border: "none", color: T.textMuted, fontSize: "12.5px", fontWeight: 600, textDecoration: "underline", padding: "4px" }}>
                Usar sem conta
              </button>
            </div>
          </>
        )}
=======
          <div style={{ fontSize: "21px", fontWeight: 800, marginTop: "10px", letterSpacing: "-0.01em" }}>B3 Agente</div>
          <div style={{ fontSize: "13px", color: T.accent, fontWeight: 600, marginTop: "2px" }}>sua mesa de operações para aprender</div>
          <p style={{ color: T.textMuted, fontSize: "12.5px", lineHeight: 1.6, margin: "12px 0 0" }}>
            Crie sua conta para salvar a carteira e acompanhar entre aparelhos. Ferramenta <b>educacional</b> — nada aqui é recomendação de investimento.
          </p>
        </div>
        {mode === "register" && (
          <>
            <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome (opcional)</label>
            <input value={name} onChange={(e) => setName(e.target.value)} maxLength={40} placeholder="Seu nome" style={{ ...field, marginBottom: "12px" }} />
          </>
        )}
        <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>E-mail</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoCapitalize="none" autoCorrect="off" placeholder="voce@exemplo.com" style={{ ...field, marginBottom: "12px" }} />
        <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Senha</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="ao menos 8 caracteres" style={{ ...field, marginBottom: "18px" }} />
        <button disabled={busy || !email || !password} onClick={submit} style={{ width: "100%", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px", opacity: (busy || !email || !password) ? 0.6 : 1 }}>
          {busy ? "…" : (mode === "register" ? "Criar conta" : "Entrar")}
        </button>
        <button onClick={() => { setErr(""); setMode(mode === "register" ? "login" : "register"); }} style={{ width: "100%", marginTop: "10px", padding: "6px", background: "transparent", border: "none", color: T.accent, fontWeight: 600, fontSize: "13px" }}>
          {mode === "register" ? "Já tem conta? Entrar" : "Criar uma conta"}
        </button>
        {err && <p style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5, margin: "12px 0 0", whiteSpace: "pre-wrap" }}>{err}</p>}
        <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: `1px solid ${T.borderSubtle}`, textAlign: "center" }}>
          <button onClick={() => onSkip && onSkip()} style={{ background: "transparent", border: "none", color: T.textMuted, fontSize: "12.5px", fontWeight: 600, textDecoration: "underline", padding: "4px" }}>
            Usar sem conta
          </button>
        </div>
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      </div>
    </div>
  );
}

function Ticker({ items, live }) {
  const loop = items.concat(items.map((x) => ({ ...x, _: 1 })));
  return (
    <div style={{ position: "relative", overflow: "hidden", borderBottom: `1px solid ${T.borderSubtle}`, background: `linear-gradient(180deg,${T.bgPanel},${T.bgBase})`, height: "38px", display: "flex", alignItems: "center", flex: "none" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, zIndex: 2, display: "flex", alignItems: "center", padding: "0 13px", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "11px", letterSpacing: "0.08em", fontFamily: MONO }}>
        {live ? "B3 ▸ YAHOO" : "B3 ▸ —"}
      </div>
      <div className="tt-track" style={{ display: "inline-flex", flexWrap: "nowrap", whiteSpace: "nowrap", paddingLeft: "104px" }}>
        {loop.map((ti, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "baseline", gap: "6px", padding: "0 16px", borderRight: `1px solid ${T.borderFaint}`, fontFamily: MONO, fontSize: "12px" }}>
            <span style={{ color: T.textDim }}>{ti.t}</span>
            <span style={{ color: T.textPrimary }}>{ti.priceStr}</span>
            <span style={{ color: ti.color }}>{ti.arrow} {ti.chStr}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

<<<<<<< HEAD
function Topbar({ patr, dia, caixa, name }) {
  const up = dia >= 0;
  const base = patr - dia;
  const pct = base > 0 ? (dia / base) * 100 : 0;
  const pctStr = (pct >= 0 ? "+" : "") + pct.toFixed(1).replace(".", ",") + "%";
  const arrow = up ? "▲" : "▼";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 16px", borderBottom: `1px solid ${T.borderSubtle}`, background: T.bgPanel, flex: "none" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "11px", marginRight: "auto", minWidth: 0 }}>
        <LogoMark size={42} />
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: "18px", lineHeight: 1.05, letterSpacing: "-0.01em" }}>Bols<span style={IA_GRAD}>IA</span></div>
          {name ? <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "2px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Olá, {name}</div> : null}
        </div>
      </div>
      <div style={{ textAlign: "right", flex: "none", fontFamily: MONO }}>
        <div style={{ fontWeight: 700, fontSize: "18px", lineHeight: 1.05, color: T.textPrimary }}>{money(patr)}</div>
        <div style={{ fontSize: "11px", marginTop: "3px", fontWeight: 700, color: up ? T.positive : T.negative, whiteSpace: "nowrap" }}>{arrow} {moneySigned(dia)} ({pctStr})</div>
        <div style={{ fontSize: "10.5px", marginTop: "2px", color: T.textFaint, whiteSpace: "nowrap" }}>caixa {money(caixa)}</div>
=======
function Topbar({ patr, dia, caixa, name, live }) {
  const chip = (label, value, color) => (
    <div style={{ textAlign: "right" }}>
      <div style={{ fontSize: "9px", color: T.textFaint, letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: "13px", fontWeight: 600, color, lineHeight: 1.15 }}>{value}</div>
    </div>
  );
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 14px", borderBottom: `1px solid ${T.borderSubtle}`, background: T.bgPanel, flex: "none" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginRight: "auto", minWidth: 0 }}>
        <LogoMark size={26} />
        <span style={{ fontWeight: 700, fontSize: "14px", whiteSpace: "nowrap" }}>B3 Agente</span>
        <span title={live ? "cotações ao vivo" : "sem cotações"} style={{ width: "6px", height: "6px", borderRadius: "50%", background: live ? T.positive : T.textFaint, flex: "none" }} />
        {name ? <span style={{ fontSize: "11px", color: T.textMuted, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", minWidth: 0 }}>· {name}</span> : null}
      </div>
      <div style={{ display: "flex", gap: "14px", alignItems: "center", fontFamily: MONO, flex: "none" }}>
        {chip("PATR.", money(patr), T.textPrimary)}
        {chip("DIA", moneySigned(dia), dia >= 0 ? T.positive : T.negative)}
        {chip("CAIXA", money(caixa), T.textMuted)}
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      </div>
    </div>
  );
}

function NavIcon({ id, active }) {
  const c = active ? T.accent : T.textMuted;
  const p = { fill: "none", stroke: c, strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    evolucao: <><polyline points="3 17 9 11 13 15 21 7" {...p} /><polyline points="16 7 21 7 21 12" {...p} /></>,
    mercado: <><line x1="6" y1="20" x2="6" y2="13" {...p} /><line x1="12" y1="20" x2="12" y2="5" {...p} /><line x1="18" y1="20" x2="18" y2="10" {...p} /></>,
<<<<<<< HEAD
    radar: <><circle cx="12" cy="12" r="8.5" {...p} /><circle cx="12" cy="12" r="4.2" {...p} /><line x1="12" y1="12" x2="18" y2="6" {...p} /><circle cx="12" cy="12" r="1.2" fill={c} stroke="none" /></>,
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    carteira: <><rect x="3" y="6" width="18" height="13" rx="2.5" {...p} /><path d="M3 9h13a2 2 0 0 1 2 2v0" {...p} /><circle cx="17" cy="13" r="1.3" fill={c} stroke="none" /></>,
    opcoes: <><path d="M4 17c4-9 12-9 16 0" {...p} /><path d="M6 12h12" {...p} /><circle cx="8" cy="12" r="1.3" fill={c} stroke="none" /><circle cx="16" cy="12" r="1.3" fill={c} stroke="none" /></>,
    perfil: <><circle cx="12" cy="8.5" r="3.4" {...p} /><path d="M5.5 19a6.5 6.5 0 0 1 13 0" {...p} /></>,
  };
  return <svg width="23" height="23" viewBox="0 0 24 24" aria-hidden>{paths[id]}</svg>;
}

function BottomNav({ tab, setTab }) {
<<<<<<< HEAD
  const defs = [["evolucao", "Evolução"], ["mercado", "Mercado"], ["radar", "Radar"], ["opcoes", "Opções"], ["carteira", "Carteira"], ["perfil", "Perfil"]];
=======
  const defs = [["evolucao", "Evolução"], ["mercado", "Mercado"], ["opcoes", "Opções"], ["carteira", "Carteira"], ["perfil", "Perfil"]];
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  return (
    <nav style={{ flex: "none", background: T.bgPanel, borderTop: `1px solid ${T.borderSubtle}`, paddingBottom: "env(safe-area-inset-bottom)" }}>
      <div style={{ display: "flex", maxWidth: "720px", margin: "0 auto", padding: "5px 6px" }}>
        {defs.map(([id, label]) => {
          const active = tab === id;
          return (
            <button key={id} onClick={() => setTab(id)} aria-pressed={active} aria-label={label}
              style={{ flex: 1, minHeight: "54px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "3px", background: "transparent", border: "none", color: active ? T.accent : T.textMuted, fontSize: "10.5px", fontWeight: active ? 700 : 600 }}>
              <NavIcon id={id} active={active} />
              {label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

/* ------------------------------- Screens --------------------------------- */
/* ---- KPIs executivos vindos da análise da IA ---- */
const TEAL = "#2dd4bf";
const ORANGE = "#fb923c";
const DIR_STYLE = {
  Alta: [T.positive, "▲"],
  Baixa: [T.negative, "▼"],
  Lateral: [T.accent, "→"],
};
const SCALE_STYLE = {
  "Muito Alto": T.positive, Alto: T.positive, Médio: T.accent, Baixo: T.negative,
  Excelente: T.positive, Boa: T.positive, Regular: T.accent, Ruim: T.negative,
};
const REC_STYLE = {
  "Estudar alta": [T.positive, T.positiveTint10],
  "Estudar baixa": [T.negative, T.negativeTint10],
  Monitorar: [TEAL, "rgba(45,212,191,0.12)"],
  Aguardar: [T.accent, T.accentTint10],
  "Não operar": [T.textMuted, T.bgBase],
  "Reduzir risco": [ORANGE, "rgba(251,146,60,0.12)"],
  // compatibilidade com análises antigas
  Comprar: [T.positive, T.positiveTint10],
  "Comprar parcialmente": [T.positive, T.positiveTint10],
  "Realizar lucro": [ORANGE, "rgba(251,146,60,0.12)"],
  "Reduzir exposição": [ORANGE, "rgba(251,146,60,0.12)"],
  Vender: [T.negative, T.negativeTint10],
};
const TECH_MODELS = [
  ["completo", "Completo", "Visão geral para estudo"],
  ["tendencia", "Tendência", "Médias e estrutura"],
  ["price_action", "Price Action", "Candles e níveis"],
  ["momentum", "Momentum", "RSI, MACD e força"],
  ["volume", "Volume", "Confirmação do movimento"],
  ["volatilidade", "Volatilidade", "ATR e amplitude"],
  ["suporte_resistencia", "Suporte/Resist.", "Regiões de preço"],
  ["swing_trade", "Swing", "Risco/retorno didático"],
  ["opcoes", "Opções", "Ativo objeto + yfinance"],
];

function KpiCell({ label, value, color, prefix }) {
  return (
    <div style={{ ...card, borderRadius: "9px", padding: "8px 9px", background: T.bgBase }}>
      <div style={{ fontSize: "9px", color: T.textFaint, letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: "13px", fontWeight: 700, color: color || T.textSecondary, marginTop: "2px" }}>
        {value ? (prefix ? prefix + " " : "") + value : "—"}
      </div>
    </div>
  );
}

function KpiBlock({ kpis }) {
  const [recColor, recBg] = REC_STYLE[kpis.recomendacao] || [T.textMuted, T.bgBase];
  const [dirColor, dirArrow] = DIR_STYLE[kpis.direcao] || [T.textMuted, ""];
  return (
    <div style={{ marginTop: "12px", display: "grid", gap: "8px" }}>
      {kpis.recomendacao && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", padding: "10px 12px", borderRadius: "9px", background: recBg, border: `1px solid ${recColor}` }}>
            <span style={{ fontSize: "10px", letterSpacing: "0.06em", color: T.textFaint }}>PLANO EDUCACIONAL</span>
            <span style={{ fontWeight: 800, fontSize: "14px", color: recColor }}>{kpis.recomendacao}</span>
          </div>
          {/* FASE 3 (item 3): rodapé educacional fixo, sob cada sinal */}
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "6px", lineHeight: 1.5 }}>
            Sinal gerado para fins educacionais — não é recomendação de compra ou venda.
          </div>
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "8px" }}>
        <KpiCell label="DIREÇÃO" value={kpis.direcao} color={dirColor} prefix={dirArrow} />
        <KpiCell label="CONVICÇÃO" value={kpis.conviccao} color={SCALE_STYLE[kpis.conviccao]} />
        <KpiCell label="QUALIDADE" value={kpis.qualidade} color={SCALE_STYLE[kpis.qualidade]} />
      </div>
    </div>
  );
}

// Lista rotulada (confirmações/invalidações/cuidados) — render seguro em React,
// sem HTML injetado (XSS-safe por construção).
function LabeledList({ title, items, icon, color }) {
  if (!items || !items.length) return null;
  return (
    <div style={{ marginTop: "10px" }}>
      <div style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: "0.05em", color: T.textFaint, marginBottom: "5px" }}>{title.toUpperCase()}</div>
      <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: "5px" }}>
        {items.map((it, i) => (
          <li key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start", fontSize: "12.5px", lineHeight: 1.5, color: T.textSecondary }}>
            <span style={{ color, fontWeight: 800, flex: "none", marginTop: "1px" }}>{icon}</span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Renderizador de markdown SEGURO (subconjunto), em React puro — sem HTML cru,
// compatível com mobile. Suporta ## títulos, **negrito**, *itálico*, `código`,
// listas (- / *), listas numeradas e parágrafos.
function MdInline({ text }) {
  const out = [];
  let rest = String(text == null ? "" : text);
  let key = 0;
  const re = /(\*\*([^*]+)\*\*|\*([^*]+)\*|\u0060([^\u0060]+)\u0060)/;
  let guard = 0;
  while (guard++ < 500) {
    const m = re.exec(rest);
    if (!m) { if (rest) out.push(rest); break; }
    if (m.index > 0) out.push(rest.slice(0, m.index));
    if (m[2] != null) out.push(<strong key={key++}>{m[2]}</strong>);
    else if (m[3] != null) out.push(<em key={key++}>{m[3]}</em>);
    else if (m[4] != null) out.push(<code key={key++} style={{ fontFamily: MONO, fontSize: "0.92em", background: "rgba(255,255,255,0.06)", padding: "0 4px", borderRadius: "4px" }}>{m[4]}</code>);
    rest = rest.slice(m.index + m[0].length);
  }
  return <>{out}</>;
}
function Markdown({ text }) {
  let src = String(text == null ? "" : text).replace(/\r\n/g, "\n").trim();
  // remove cercas de markdown que às vezes embrulham o corpo inteiro
  src = src.replace(/^\u0060{3}[a-zA-Z]*\n?/, "").replace(/\n?\u0060{3}$/, "").trim();
  if (!src) return null;
  const lines = src.split("\n");
  const blocks = [];
  let para = [];
  let list = null; // { ordered, items: [] }
  const flushPara = () => { if (para.length) { blocks.push({ type: "p", lines: para }); para = []; } };
  const flushList = () => { if (list) { blocks.push({ type: "list", ordered: list.ordered, items: list.items }); list = null; } };
  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    const h = /^(#{1,4})\s*(.+)$/.exec(line);
    const bul = /^\s*[-*•]\s+(.*)$/.exec(line);
    const num = /^\s*\d+[.\u0029]\s+(.*)$/.exec(line);
    if (!line.trim()) { flushPara(); flushList(); continue; }
    if (h) { flushPara(); flushList(); blocks.push({ type: "h", level: h[1].length, text: h[2] }); continue; }
    if (bul) { flushPara(); if (!list || list.ordered) { flushList(); list = { ordered: false, items: [] }; } list.items.push(bul[1]); continue; }
    if (num) { flushPara(); if (!list || !list.ordered) { flushList(); list = { ordered: true, items: [] }; } list.items.push(num[1]); continue; }
    flushList(); para.push(line);
  }
  flushPara(); flushList();
  return (
    <div style={{ display: "grid", gap: "9px" }}>
      {blocks.map((b, i) => {
        if (b.type === "h") {
          const size = b.level <= 1 ? "15px" : b.level === 2 ? "14px" : "13px";
          return <div key={i} style={{ fontSize: size, fontWeight: 800, color: T.textPrimary }}><MdInline text={b.text} /></div>;
        }
        if (b.type === "list") {
          if (b.ordered) {
            return <ol key={i} style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "5px" }}>{b.items.map((it, j) => <li key={j} style={{ fontSize: "13px", lineHeight: 1.55, color: T.textSecondary }}><MdInline text={it} /></li>)}</ol>;
          }
          return (
            <ul key={i} style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: "5px" }}>
              {b.items.map((it, j) => (
                <li key={j} style={{ display: "flex", gap: "8px", alignItems: "flex-start", fontSize: "13px", lineHeight: 1.55, color: T.textSecondary }}>
                  <span style={{ color: T.accent, flex: "none", marginTop: "1px" }}>•</span><span><MdInline text={it} /></span>
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} style={{ margin: 0, fontSize: "13px", lineHeight: 1.6, color: T.textSecondary }}>
            {b.lines.map((l, j) => (<span key={j}>{j > 0 && <br />}<MdInline text={l} /></span>))}
          </p>
        );
      })}
    </div>
  );
}

// Análise formatada da IA, renderizada NO card (progressive disclosure).
function AnalysisView({ an }) {
  if (!an) return null;
  if (an.error) return <div style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5 }}>{an.error}</div>;
  const d = an.detail || {};
  const body = an.markdown || d.resumo || an.text || an.analysis || "";
  // FASE 1: a análise do ativo individual exibe SÓ texto. O stop/alvo
  // (an.proposal) foi desacoplado deste fluxo — a lógica permanece em
  // localProposal() e no estado an.proposal, e migra para a Carteira na Fase 3.
  return (
    <div style={{ display: "grid", gap: "2px" }}>
      {body ? <Markdown text={body} /> : <div style={{ color: T.textMuted, fontSize: "13px" }}>A análise foi gerada, mas não veio texto legível. Tente reanalisar.</div>}
      {Array.isArray(d.fatos) && d.fatos.length > 0 && (
        <div style={{ marginTop: "14px", padding: "13px 14px", borderRadius: "11px", background: T.bgBase, border: `1px solid ${T.borderSubtle}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "8px" }}>
            <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="9.5" fill="none" stroke={T.textSecondary} strokeWidth="1.8" /><path d="M12 11v5M12 7.5h.01" stroke={T.textSecondary} strokeWidth="2" strokeLinecap="round" /></svg>
            <span style={{ fontSize: "11px", fontWeight: 700, color: T.textSecondary, letterSpacing: "0.05em" }}>FATOS RELEVANTES / CONTEXTO</span>
          </div>
          <ul style={{ margin: 0, paddingLeft: "18px", display: "grid", gap: "5px" }}>
            {d.fatos.map((f, i) => <li key={i} style={{ fontSize: "13px", color: T.textPrimary, lineHeight: 1.5 }}>{f}</li>)}
          </ul>
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "9px", lineHeight: 1.5 }}>Contexto informativo com base nos dados disponíveis — sem garantia de completude ou atualidade. Não é recomendação de compra ou venda.</div>
        </div>
      )}
      <AiNote at={an.at} />
    </div>
  );
}

function hasAnalysis(an) {
  if (!an) return false;
  const d = an.detail || {};
  return !!(an.kpis || an.markdown || an.text || an.error || d.resumo || (d.confirmacoes && d.confirmacoes.length) || (d.invalidacoes && d.invalidacoes.length) || (d.cuidados && d.cuidados.length) || (d.fatos && d.fatos.length));
}

/* ---------- Análise técnica: gráfico interativo + indicadores ---------- */
function extentOf(arrays) {
  let mn = Infinity, mx = -Infinity;
  for (const a of arrays) { if (!a) continue; for (const v of a) { if (v == null) continue; if (v < mn) mn = v; if (v > mx) mx = v; } }
  if (mn === Infinity) return [0, 1];
  if (mn === mx) return [mn - 1, mx + 1];
  const pad = (mx - mn) * 0.05; return [mn - pad, mx + pad];
}
function linePath(arr, mn, mx, W, H, pad = 3) {
  if (!arr || !arr.length) return "";
  const n = arr.length;
  const xs = (i) => pad + (n > 1 ? i / (n - 1) : 0) * (W - 2 * pad);
  const ys = (v) => (mx === mn ? H / 2 : H - pad - ((v - mn) / (mx - mn)) * (H - 2 * pad));
  let d = "", started = false;
  for (let i = 0; i < n; i++) { const v = arr[i]; if (v == null) { started = false; continue; } const x = xs(i), y = ys(v); d += started ? ` L${x.toFixed(1)} ${y.toFixed(1)}` : ` M${x.toFixed(1)} ${y.toFixed(1)}`; started = true; }
  return d;
}
function lastVal(arr) { if (!arr) return null; for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i]; return null; }
const stateColor = (s) => (s === "alta" || s === "sobrevendido" || s === "acima" ? T.positive : s === "baixa" || s === "sobrecomprado" || s === "abaixo" ? T.negative : T.textSecondary);
const REDUCE_MOTION = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function RSIChart({ rsi }) {
  const P = usePalette();
  const W = 320, H = 64; const y = (v) => H - (v / 100) * H;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: "100%", height: "64px", display: "block" }}>
      <line x1="0" x2={W} y1={y(70)} y2={y(70)} stroke={P.borderSubtle} strokeDasharray="3 3" />
      <line x1="0" x2={W} y1={y(30)} y2={y(30)} stroke={P.borderSubtle} strokeDasharray="3 3" />
      <path d={linePath(rsi, 0, 100, W, H)} fill="none" stroke={P.accent} strokeWidth="1.5" />
    </svg>
  );
}
function MACDChart({ macd, signal, hist }) {
  const P = usePalette();
  const W = 320, H = 64;
  const mag = [...(macd || []), ...(signal || []), ...(hist || [])].filter((x) => x != null).map(Math.abs);
  const mx = Math.max(0.0001, ...mag); const mid = H / 2; const y = (v) => mid - (v / mx) * (mid - 4);
  const n = (hist || []).length || 1, bw = W / n;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: "100%", height: "64px", display: "block" }}>
      {(hist || []).map((v, i) => (v == null ? null : <rect key={i} x={(i * bw).toFixed(1)} y={(v >= 0 ? y(v) : mid).toFixed(1)} width={Math.max(0.5, bw - 0.5).toFixed(1)} height={Math.abs(mid - y(v)).toFixed(1)} fill={v >= 0 ? P.positive : P.negative} opacity="0.5" />))}
      <line x1="0" x2={W} y1={mid} y2={mid} stroke={P.borderSubtle} />
      <path d={linePath(macd, -mx, mx, W, H)} fill="none" stroke={P.accent} strokeWidth="1.3" />
      <path d={linePath(signal, -mx, mx, W, H)} fill="none" stroke={ORANGE} strokeWidth="1.1" />
    </svg>
  );
}
function IndCell({ label, value, sub, color }) {
  return (
    <div style={{ padding: "9px 10px", background: T.bgBase, borderRadius: "9px" }}>
      <div style={{ fontSize: "9.5px", color: T.textFaint, letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: "14px", fontWeight: 700, color: color || T.textSecondary, marginTop: "2px", fontFamily: MONO }}>{value == null ? "—" : value}</div>
      {sub && <div style={{ fontSize: "10px", color: color || T.textFaint, marginTop: "1px" }}>{sub}</div>}
    </div>
  );
}
function Toggle2({ on, label, color, onClick }) {
  return (
    <button onClick={onClick} style={{ padding: "6px 11px", borderRadius: "999px", fontSize: "12px", fontWeight: 700, minHeight: "32px", border: `1px solid ${on ? color : T.borderSubtle}`, background: on ? "color-mix(in srgb," + color + " 16%, transparent)" : "transparent", color: on ? color : T.textFaint }}>
      {label}
    </button>
  );
}

// Gráfico de preço interativo (lightweight-charts): pinça/zoom, pan, crosshair,
// linhas de preço (atual/stop/alvo). Volta para SVG simples se a lib falhar.
function PriceChart({ candles, ind, show, priceLines, viewBars, onRange }) {
  const P = usePalette();
  const themeKey = useThemeKey();
  const elRef = useRef(null);
  const chartRef = useRef(null);
  const sref = useRef({});
  const linesRef = useRef([]);
  const [tip, setTip] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let chart;
    try {
      chart = createChart(elRef.current, {
        width: elRef.current.clientWidth || 320, height: 240,
        layout: { background: { type: ColorType.Solid, color: "rgba(0,0,0,0)" }, textColor: P.chartAxis, fontFamily: MONO, fontSize: 10 },
        grid: { vertLines: { color: P.chartGrid }, horzLines: { color: P.chartGrid } },
        rightPriceScale: { borderColor: P.chartBorder },
        timeScale: { borderColor: P.chartBorder, timeVisible: false, secondsVisible: false },
        crosshair: { mode: CrosshairMode.Magnet, vertLine: { color: P.accent, width: 1, labelBackgroundColor: P.accent }, horzLine: { color: P.accent, labelBackgroundColor: P.accent } },
        handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
        handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
      });
    } catch (e) {
      setFailed(true); return;
    }
    chartRef.current = chart;
    const mk = (opts) => chart.addLineSeries(opts);
    const price = chart.addCandlestickSeries({
      upColor: "#22c55e", downColor: "#f43f5e",
      borderUpColor: "#22c55e", borderDownColor: "#f43f5e",
      wickUpColor: "#22c55e", wickDownColor: "#f43f5e",
      priceLineVisible: false, lastValueVisible: true,
    });
    const sma20 = mk({ color: TEAL, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
    const sma50 = mk({ color: ORANGE, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
    const bbU = mk({ color: P.lineSubtle, lineWidth: 1, lineStyle: LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
    const bbL = mk({ color: P.lineSubtle, lineWidth: 1, lineStyle: LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
    const vol = chart.addHistogramSeries({ priceScaleId: "vol", priceLineVisible: false, lastValueVisible: false });
    chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.86, bottom: 0 } });
    sref.current = { price, sma20, sma50, bbU, bbL, vol };

    const pair = (arr) => candles.map((c, i) => (arr[i] == null ? null : { time: c.date, value: arr[i] })).filter(Boolean);
    // Saneia OHLC por vela: trata 0/null como ausente, sintetiza doji do
    // fechamento (pregão do dia em aberto) e descarta outliers que esticariam
    // o eixo de preço. A escala da lib enquadra min/max dos dados válidos.
    const pos = (v) => (typeof v === "number" && isFinite(v) && v > 0 ? v : null);
    const validCloses = candles.map((c) => pos(c.close)).filter((x) => x != null).sort((a, b) => a - b);
    const med = validCloses.length ? validCloses[Math.floor(validCloses.length / 2)] : null;
    const bars = [];
    let prevC = null;
    for (const c of candles) {
      const close = pos(c.close);
      if (close == null) continue;
      if (med && (close > med * 6 || close < med / 6)) continue;        // outlier vs mediana
      if (prevC && (close > prevC * 5 || close < prevC / 5)) continue;  // outlier vs vizinho
      let o = pos(c.open) || close;
      let hi = pos(c.high) || Math.max(o, close);
      let lo = pos(c.low) || Math.min(o, close);
      hi = Math.max(hi, o, close, lo);
      lo = Math.min(lo, o, close, hi);
      bars.push({ time: c.date, open: o, high: hi, low: lo, close });
      prevC = close;
    }
    price.setData(bars);
    sma20.setData(pair(ind.sma20)); sma50.setData(pair(ind.sma50)); bbU.setData(pair(ind.bbUpper)); bbL.setData(pair(ind.bbLower));
    vol.setData(candles.map((c, i) => ({ time: c.date, value: c.volume || 0, color: i > 0 && c.close >= candles[i - 1].close ? "rgba(34,197,94,0.28)" : "rgba(244,63,94,0.28)" })));

    chart.subscribeCrosshairMove((p) => {
      if (!p || !p.time || !p.point || p.point.x < 0) { setTip(null); return; }
      const d = p.seriesData.get(price);
      if (!d) { setTip(null); return; }
      setTip({ x: p.point.x, date: p.time, value: d.close != null ? d.close : d.value });
    });
    if (onRange) chart.timeScale().subscribeVisibleLogicalRangeChange((r) => r && onRange(r));

    const ro = new ResizeObserver(() => { if (elRef.current) chart.applyOptions({ width: elRef.current.clientWidth }); });
    ro.observe(elRef.current);
    return () => { ro.disconnect(); chart.remove(); chartRef.current = null; sref.current = {}; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candles, themeKey]);

  useEffect(() => {
    const s = sref.current; if (!s.price) return;
    s.sma20.applyOptions({ visible: !!show.sma20 });
    s.sma50.applyOptions({ visible: !!show.sma50 });
    s.bbU.applyOptions({ visible: !!show.bb });
    s.bbL.applyOptions({ visible: !!show.bb });
    s.vol.applyOptions({ visible: !!show.vol });
  }, [show]);

  useEffect(() => {
    const s = sref.current; if (!s.price) return;
    linesRef.current.forEach((pl) => { try { s.price.removePriceLine(pl); } catch { /* */ } });
    linesRef.current = (priceLines || []).filter((L) => L.price != null).map((L) =>
      s.price.createPriceLine({ price: L.price, color: L.color, lineWidth: 1, lineStyle: L.dashed ? LineStyle.Dashed : LineStyle.Solid, axisLabelVisible: true, title: L.title })
    );
  }, [priceLines]);

  useEffect(() => {
    const ch = chartRef.current; if (!ch || !viewBars) return;
    const n = candles.length; const to = n - 0.5; const from = Math.max(0, n - viewBars) - 0.5;
    try { ch.timeScale().setVisibleLogicalRange({ from, to }); } catch { /* */ }
  }, [viewBars, candles]);

  if (failed) {
    const close = candles.map((c) => c.close);
    const [mn, mx] = extentOf([close, ind.sma20, ind.sma50]);
    return (
      <svg viewBox="0 0 320 240" preserveAspectRatio="none" style={{ width: "100%", height: "240px", display: "block" }}>
        <path d={linePath(ind.sma50, mn, mx, 320, 240)} fill="none" stroke={ORANGE} strokeWidth="1.2" />
        <path d={linePath(ind.sma20, mn, mx, 320, 240)} fill="none" stroke={TEAL} strokeWidth="1.2" />
        <path d={linePath(close, mn, mx, 320, 240)} fill="none" stroke={P.accent} strokeWidth="2" />
      </svg>
    );
  }
  return (
    <div style={{ position: "relative" }}>
      <div ref={elRef} style={{ width: "100%", height: "240px" }} />
      {tip && (
        <div style={{ position: "absolute", top: "6px", left: Math.max(6, Math.min(tip.x - 50, 220)), pointerEvents: "none", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, borderRadius: "7px", padding: "4px 8px", fontFamily: MONO, fontSize: "11px", color: T.textPrimary, whiteSpace: "nowrap" }}>
          <span style={{ color: T.textFaint }}>{tip.date}</span> · R$ {Number(tip.value).toFixed(2)}
        </div>
      )}
    </div>
  );
}

function ChartSkeleton() {
  return <div className="sk" style={{ width: "100%", height: "240px", borderRadius: "10px" }} />;
}

// Bottom sheet arrastável (fecha ao puxar para baixo).
function BottomSheet({ onClose, children }) {
  const [dy, setDy] = useState(0);
  const [dragging, setDragging] = useState(false);
  const startY = useRef(0);
  const onDown = (e) => { startY.current = e.clientY; setDragging(true); try { e.target.setPointerCapture(e.pointerId); } catch { /* */ } };
  const onMove = (e) => { if (!dragging) return; setDy(Math.max(0, e.clientY - startY.current)); };
  const onUp = () => { if (!dragging) return; setDragging(false); if (dy > 110) onClose(); else setDy(0); };
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.62)", display: "flex", flexDirection: "column" }}>
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ marginTop: "auto", background: T.bgBase, borderTopLeftRadius: "20px", borderTopRightRadius: "20px", borderTop: `1px solid ${T.borderSubtle}`, maxHeight: "94vh", display: "flex", flexDirection: "column", paddingBottom: "env(safe-area-inset-bottom)", transform: `translateY(${dy}px)`, transition: dragging || REDUCE_MOTION ? "none" : "transform .22s ease" }}
      >
        <div onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp} style={{ padding: "10px 0 4px", cursor: "grab", touchAction: "none", flex: "none" }}>
          <div style={{ width: "40px", height: "4px", borderRadius: "999px", background: T.borderSubtle, margin: "0 auto" }} />
        </div>
        {children}
      </div>
    </div>
  );
}

<<<<<<< HEAD
function TechnicalModal({ ticker, name, quote, position, onClose, period }) {
=======
function TechnicalModal({ ticker, name, quote, position, onClose }) {
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  const P = usePalette();
  const [data, setData] = useState(() => store.cachedTechnicals(ticker));
  const [loading, setLoading] = useState(false);
  const [demo, setDemo] = useState(false);
  const [show, setShow] = useState({ sma20: true, sma50: true, bb: false, vol: true });
  const [viewBars, setViewBars] = useState(66); // 3M inicial
  const [range, setRange] = useState(null);

  useEffect(() => {
    let alive = true;
<<<<<<< HEAD
    const per = period || "1y";
    const cached = store.cachedTechnicals(ticker, per);
    if (cached) { setData(cached); setDemo(!!cached.sample); }
    setLoading(true);
    store.technicals(ticker, per)
=======
    const cached = store.cachedTechnicals(ticker);
    if (cached) { setData(cached); setDemo(!!cached.sample); }
    setLoading(true);
    store.technicals(ticker)
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      .then((r) => { if (alive) { setData(r); setDemo(false); } })
      .catch(() => { if (alive && !cached) { setData(sampleTechnicals(ticker)); setDemo(true); } })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
<<<<<<< HEAD
  }, [ticker, period]);
=======
  }, [ticker]);
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026

  const ind = data && data.indicators;
  const sm = (data && data.summary) || {};
  const n = data ? data.candles.length : 0;
  const i0 = range ? Math.max(0, Math.floor(range.from)) : 0;
  const i1 = range ? Math.min(n - 1, Math.ceil(range.to)) : n - 1;
  const slice = (arr) => (arr ? arr.slice(i0, i1 + 1) : []);
  const lastClose = quote && quote.price != null ? quote.price : sm.close;

  const priceLines = [];
  if (lastClose != null) priceLines.push({ price: lastClose, color: P.accent, title: "atual", dashed: false });
  if (position && position.avg != null) priceLines.push({ price: position.avg, color: P.textMuted, title: "PM", dashed: true });
  if (position && position.stop != null) priceLines.push({ price: position.stop, color: P.negative, title: "stop", dashed: true });
  if (position && position.alvo != null) priceLines.push({ price: position.alvo, color: P.positive, title: "alvo", dashed: true });

  const periods = [["1S", 5], ["1M", 22], ["3M", 66], ["1A", 252]];

  return (
    <BottomSheet onClose={onClose}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "2px 18px 10px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "9px" }}>
            <span style={{ fontSize: "21px", fontWeight: 800, fontFamily: MONO }}>{ticker}</span>
            {lastClose != null && <span style={{ fontSize: "15px", fontWeight: 700, fontFamily: MONO }}>R$ {Number(lastClose).toFixed(2)}</span>}
            {quote && quote.change != null && <span style={{ fontSize: "12.5px", fontWeight: 700, color: quote.change >= 0 ? T.positive : T.negative }}>{quote.change >= 0 ? "+" : ""}{Number(quote.change).toFixed(2)}%</span>}
          </div>
          {name && <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "1px" }}>{name}</div>}
        </div>
        <button onClick={onClose} aria-label="Fechar" style={{ width: "44px", height: "44px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontSize: "17px" }}>✕</button>
      </div>

      <div style={{ overflowY: "auto", padding: "0 14px 22px" }}>
        {demo && <div style={{ fontSize: "11px", color: T.accent, background: T.accentTint10, border: `1px solid ${T.accentTint}`, borderRadius: "8px", padding: "7px 10px", marginBottom: "10px" }}>Dados de exemplo (servidor indisponível) — protótipo navegável.</div>}

        {/* atalhos de período */}
        <div style={{ display: "flex", gap: "7px", marginBottom: "10px" }}>
          {periods.map(([lab, bars]) => (
            <button key={lab} onClick={() => setViewBars(bars)} style={{ flex: 1, minHeight: "34px", padding: "7px", borderRadius: "8px", fontSize: "12.5px", fontWeight: 700, border: `1px solid ${viewBars === bars ? T.accent : T.borderSubtle}`, background: viewBars === bars ? T.accentTint : T.bgPanel, color: viewBars === bars ? T.accent : T.textMuted }}>{lab}</button>
          ))}
        </div>

        {!data && loading && <ChartSkeleton />}
        {data && ind && (
          <>
            <PriceChart candles={data.candles} ind={ind} show={show} priceLines={priceLines} viewBars={viewBars} onRange={setRange} />
            <div style={{ display: "flex", gap: "7px", flexWrap: "wrap", margin: "8px 0 4px" }}>
              <Toggle2 on={show.sma20} label="SMA 20" color={TEAL} onClick={() => setShow((s) => ({ ...s, sma20: !s.sma20 }))} />
              <Toggle2 on={show.sma50} label="SMA 50" color={ORANGE} onClick={() => setShow((s) => ({ ...s, sma50: !s.sma50 }))} />
              <Toggle2 on={show.bb} label="Bollinger" color={T.textSecondary} onClick={() => setShow((s) => ({ ...s, bb: !s.bb }))} />
              <Toggle2 on={show.vol} label="Volume" color={T.textSecondary} onClick={() => setShow((s) => ({ ...s, vol: !s.vol }))} />
            </div>
            <div style={{ fontSize: "10.5px", color: T.textFaint, marginBottom: "12px" }}>Pinça para zoom · arraste para navegar no tempo · toque e segure para ver preço/data.</div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", margin: "4px 2px 4px" }}><span style={{ fontSize: "11.5px", fontWeight: 700, color: T.textSecondary }}>IFR / RSI (14)</span><span style={{ fontSize: "10px", color: T.textFaint }}>30 / 70</span></div>
            <RSIChart rsi={slice(ind.rsi14)} />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", margin: "12px 2px 4px" }}><span style={{ fontSize: "11.5px", fontWeight: 700, color: T.textSecondary }}>MACD (12, 26, 9)</span></div>
            <MACDChart macd={slice(ind.macd)} signal={slice(ind.macdSignal)} hist={slice(ind.macdHist)} />

            {/* valores dos indicadores */}
            <div style={{ fontSize: "12px", fontWeight: 700, color: T.accent, letterSpacing: "0.04em", margin: "18px 2px 10px" }}>INDICADORES (valores atuais)</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: "8px" }}>
              <IndCell label="TENDÊNCIA (SMA20 x SMA50)" value={sm.trend} color={stateColor(sm.trend)} />
              <IndCell label="PREÇO x SMA20" value={sm.priceVsSma20} color={stateColor(sm.priceVsSma20)} />
              <IndCell label="IFR / RSI (14)" value={sm.rsi14} sub={sm.rsiState} color={stateColor(sm.rsiState)} />
              <IndCell label="ESTOCÁSTICO %K / %D" value={sm.stochK == null ? null : `${sm.stochK} / ${sm.stochD}`} sub={sm.stochState} color={stateColor(sm.stochState)} />
              <IndCell label="MACD (histograma)" value={sm.macdHist} sub={sm.macdState} color={stateColor(sm.macdState)} />
              <IndCell label="ATR (14) — volatilidade" value={sm.atr14} />
              <IndCell label="SMA 20" value={sm.sma20} />
              <IndCell label="SMA 50" value={sm.sma50} />
              <IndCell label="EMA 9" value={lastVal(ind.ema9)} />
              <IndCell label="EMA 21" value={lastVal(ind.ema21)} />
              <IndCell label="BOLLINGER SUP." value={sm.bbUpper} />
              <IndCell label="BOLLINGER INF." value={sm.bbLower} />
            </div>

            <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "14px", lineHeight: 1.5 }}>
              Fonte: Yahoo Finance{data.at && data.at !== "exemplo" ? " · " + data.at : ""}. Conteúdo educacional — não é recomendação de investimento.
            </div>
          </>
        )}
      </div>
    </BottomSheet>
  );
}

// ---- FASE A: Evolução (home centrada em progresso) ----

// Curva de capital (Fase B1): série real de patrimônio a partir de equitySnapshots,
// com retorno acumulado e drawdown (queda desde o pico). Determinístico, sem IA.
function CapitalCurve({ ctx }) {
  const { data, quotes } = ctx;
<<<<<<< HEAD
  const m = portfolioMetrics(data.positions, quotes, data.cash);
  const patr = m.patr;
  const budget = (data.config && data.config.initialBudget) || 0;
  const todayYmd = new Date().toISOString().slice(0, 10);
  const ec = equityCurve(data.equitySnapshots, budget, patr, todayYmd);
  const retVsInicio = budget > 0 ? ((patr - budget) / budget) * 100 : ec.retAcum;
  const hasSeries = ec.days >= 1;          // mostra a curva a partir do 1º dia (baseline = orçamento)
  const retAcum = ec.retAcum;               // base = orçamento inicial → bate com "vs início"
  const dd = ec.drawdown;                   // drawdown sobre a MESMA curva exibida
  const series = ec.curve;                  // curva exibida (orçamento → ... → ao vivo)
=======
  const posVal = (data.positions || []).reduce((s, p) => s + p.qty * ((quotes[p.t] || {}).price || 0), 0);
  const patr = (data.cash || 0) + posVal;
  const budget = (data.config && data.config.initialBudget) || 0;
  const snaps = (data.equitySnapshots || []).filter((s) => s && typeof s.patrimonio === "number");
  const series = snaps.map((s) => s.patrimonio);
  const hasSeries = series.length >= 2;
  const retVsInicio = budget > 0 ? ((patr - budget) / budget) * 100 : 0;
  // retorno acumulado e drawdown sobre a série persistida
  let peak = series.length ? series[0] : 0, dd = 0;
  for (const v of series) { peak = Math.max(peak, v); if (peak > 0) dd = Math.max(dd, ((peak - v) / peak) * 100); }
  const retAcum = hasSeries && series[0] > 0 ? ((series[series.length - 1] - series[0]) / series[0]) * 100 : retVsInicio;
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  const up = retAcum >= 0;
  // polyline normalizada ao viewBox 300x92
  let path = "";
  if (hasSeries) {
    const min = Math.min(...series), max = Math.max(...series), span = max - min || 1;
    path = series.map((v, i) => {
      const x = series.length === 1 ? 0 : (i / (series.length - 1)) * 300;
      const y = 84 - ((v - min) / span) * 72;
      return (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }
  const stat = (label, value, color) => (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: "9.5px", color: T.textFaint, letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "14px", color: color || T.textPrimary }}>{value}</div>
    </div>
  );
  return (
    <div style={{ ...card, padding: "18px 18px 14px" }}>
      <div style={{ fontSize: "12px", color: T.textMuted, letterSpacing: "0.04em" }}>PATRIMÔNIO SIMULADO</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginTop: "4px", flexWrap: "wrap" }}>
        <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 700 }}>{money(patr)}</div>
        <div style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: retVsInicio >= 0 ? T.positive : T.negative }}>{pct(retVsInicio)} vs. início</div>
      </div>
      <div style={{ marginTop: "12px", position: "relative", height: "92px", borderRadius: "10px", overflow: "hidden", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
        <svg viewBox="0 0 300 92" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
          <line x1="0" y1="84" x2="300" y2="84" stroke={T.chartGrid} strokeWidth="1" />
          {hasSeries
            ? <path d={path} fill="none" stroke={up ? T.positive : T.negative} strokeWidth="2" />
            : <path d="M0,72 C60,66 110,58 150,52 C200,45 250,40 300,30" fill="none" stroke={T.textFaint} strokeWidth="2" strokeOpacity="0.35" strokeDasharray="4 4" />}
        </svg>
      </div>
      {hasSeries ? (
        <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
          {stat("RETORNO ACUMULADO", pct(retAcum), retAcum >= 0 ? T.positive : T.negative)}
          {stat("DRAWDOWN (DESDE O PICO)", "-" + dd.toFixed(1) + "%", T.negative)}
<<<<<<< HEAD
          {stat("DIAS REGISTRADOS", String(ec.days))}
=======
          {stat("DIAS REGISTRADOS", String(series.length))}
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
        </div>
      ) : (
        <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "10px", lineHeight: 1.5 }}>
          Sua curva começa amanhã. Volte para vê-la crescer — cada dia que você abrir o app vira um ponto aqui.
        </div>
      )}
    </div>
  );
}

const COACH_TIPS = [
  "Defina stop e alvo ANTES de comprar. Decidir no susto costuma sair caro.",
  "Operar demais aumenta custo e erro. No aprendizado, menos é mais.",
  "Perder faz parte. O que importa é o tamanho da perda, não a frequência.",
  "Anote o motivo de cada operação. Rever depois ensina mais que acertar.",
  "Posição grande demais tira seu sono e sua clareza. Dimensione pelo perfil.",
  "Ter um plano e segui-lo vale mais que adivinhar o próximo movimento.",
  "Caixa parado também é decisão. Não é obrigatório operar todo dia.",
];
const WEEK_CHALLENGES = [
  "Esta semana: defina um stop antes de cada compra.",
  "Esta semana: registre o porquê de cada operação.",
  "Esta semana: revise a carteira 1x/dia, sem operar por impulso.",
  "Esta semana: mantenha nenhuma posição acima de 30% do patrimônio.",
  "Esta semana: antes de vender, releia o motivo da compra.",
];
const dayIndex = () => Math.floor(Date.now() / 86400000);
const coachTip = () => COACH_TIPS[dayIndex() % COACH_TIPS.length];
const weeklyChallenge = () => WEEK_CHALLENGES[Math.floor(dayIndex() / 7) % WEEK_CHALLENGES.length];

function EvolucaoScreen({ ctx }) {
  const { data, A } = ctx;
  const name = ((data.config && data.config.userName) || "").trim().split(/\s+/)[0] || "";
  const streak = (data.config && data.config.streak && data.config.streak.days) || 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div>
        <h1 style={{ margin: 0, fontSize: "23px", fontWeight: 700, letterSpacing: "-0.01em" }}>{name ? "Olá, " + name : "Sua evolução"}</h1>
        <p style={{ margin: "5px 0 0", color: T.textMuted, fontSize: "13px", lineHeight: 1.5 }}>Acompanhe seu progresso como operador — aprendizado, não só lucro.</p>
      </div>

      <CapitalCurve ctx={ctx} />

      {/* Streak de consistência (intrínseco, sem push) */}
      <div style={{ ...card, padding: "16px 18px", display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ width: 46, height: 46, borderRadius: "12px", background: T.accentTint, color: T.accent, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: MONO, fontWeight: 800, fontSize: "20px", flex: "none" }}>{streak}</div>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 700 }}>{streak <= 0 ? "Comece sua sequência hoje" : streak === 1 ? "1 dia de consistência" : streak + " dias de consistência"}</div>
          <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "2px", lineHeight: 1.5 }}>Abrir o app e revisar sua carteira cria o hábito. O hábito é o que faz você melhorar.</div>
        </div>
      </div>

      {/* Card do Coach (insight do dia — determinístico na Fase A) */}
      <div style={{ ...card, padding: "16px 18px", borderLeft: `3px solid ${T.accent}` }}>
        <div style={{ fontSize: "11px", fontWeight: 700, color: T.accent, letterSpacing: "0.05em" }}>COACH · INSIGHT DO DIA</div>
        <div style={{ fontSize: "14px", color: T.textPrimary, marginTop: "7px", lineHeight: 1.55 }}>{coachTip()}</div>
        <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "8px" }}>Orientação educacional sobre comportamento — não é recomendação de compra/venda.</div>
      </div>

      {/* Desafio da semana (meta de comportamento, não de mercado) */}
      <div style={{ ...card, padding: "16px 18px" }}>
        <div style={{ fontSize: "11px", fontWeight: 700, color: T.textSecondary, letterSpacing: "0.05em" }}>DESAFIO DA SEMANA</div>
        <div style={{ fontSize: "14px", color: T.textPrimary, marginTop: "7px", lineHeight: 1.55 }}>{weeklyChallenge()}</div>
      </div>

      {/* Atalhos */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button onClick={() => A.go("carteira")} style={{ flex: "1 1 150px", minHeight: "46px", padding: "12px", borderRadius: "12px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Registrar operação</button>
        <button onClick={() => A.go("mercado")} style={{ flex: "1 1 150px", minHeight: "46px", padding: "12px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>Ver Mercado</button>
      </div>
    </div>
  );
}

// Cabeçalho de sub-tela (drill-down): seta voltar + título. Alvo de toque ≥44px.
function BackHeader({ title, onBack }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "14px" }}>
      <button onClick={onBack} aria-label="Voltar" style={{ minWidth: "44px", minHeight: "44px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "10px", border: "none", background: "transparent", color: T.textSecondary }}>
        <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden><polyline points="15 5 8 12 15 19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
      <div style={{ fontSize: "18px", fontWeight: 700 }}>{title}</div>
    </div>
  );
}

// Linha de menu (divulgação progressiva): abre uma sub-tela focada.
function DrillRow({ icon, title, sub, onClick }) {
  return (
    <button onClick={onClick} style={{ width: "100%", minHeight: "60px", display: "flex", alignItems: "center", gap: "13px", padding: "12px 14px", borderRadius: "13px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, textAlign: "left" }}>
      <span style={{ width: 38, height: 38, flex: "none", borderRadius: "10px", background: T.accentTint, color: T.accent, display: "flex", alignItems: "center", justifyContent: "center" }} aria-hidden>{icon}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: "block", fontSize: "14.5px", fontWeight: 700, color: T.textPrimary }}>{title}</span>
        {sub ? <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginTop: "2px" }}>{sub}</span> : null}
      </span>
      <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden style={{ flex: "none", color: T.textFaint }}><polyline points="9 5 16 12 9 19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
    </button>
  );
}

// Hub do Perfil: menu raso e escaneável; cada item entra numa tela focada.
function PerfilHub({ ctx, onOpen }) {
  const { data } = ctx;
  const name = ((data.config && data.config.userName) || "").trim();
  const prof = data.profile || {};
  const notifOn = data.config && data.config.notif && data.config.notif.enabled;
  const ag = data.agent || {};
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "13px", marginBottom: "2px" }}>
        <div style={{ width: 48, height: 48, borderRadius: "14px", background: T.accent, color: T.onAccent, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "20px", flex: "none" }}>{(name || "·").slice(0, 1).toUpperCase()}</div>
        <div>
          <div style={{ fontSize: "18px", fontWeight: 700 }}>{name || "Seu perfil"}</div>
          <div style={{ fontSize: "12.5px", color: T.textMuted }}>Perfil {prof.risco || "—"} · {prof.horizonte || "horizonte —"}</div>
        </div>
      </div>

      <DrillRow onClick={() => ctx.openAuth && ctx.openAuth()} title={ctx.authUser ? "Conta" : "Entrar ou criar conta"} sub={ctx.authUser ? ((ctx.authUser.email || ctx.authUser.name || "conectado") + " · toque para gerenciar") : "Opcional — salva sua carteira e sincroniza entre aparelhos"} icon={
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="8.5" r="3.6" fill="none" stroke="currentColor" strokeWidth="1.9" /><path d="M5 19.5c0-3.6 3.1-5.5 7-5.5s7 1.9 7 5.5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" /></svg>
      } />
      <DrillRow onClick={() => onOpen("config")} title="Conta & preferências" sub="Perfil de risco, IA & skill, aparência, notificações, orçamento" icon={
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.9" /><path d="M12 3v2.5M12 18.5V21M21 12h-2.5M5.5 12H3M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8M18.4 18.4l-1.8-1.8M7.4 7.4 5.6 5.6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
      } />
      <DrillRow onClick={() => onOpen("agente")} title="Agente autônomo" sub={ag.autonomous ? "Ligado · opera sozinho em intervalos" : "Desligado"} icon={
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden><rect x="5" y="8" width="14" height="10" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.9" /><path d="M12 8V5M9 13h.01M15 13h.01" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" /></svg>
      } />
      <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "2px", lineHeight: 1.5 }}>
        Notificações {notifOn ? "ativas" : "desativadas"} · ferramenta educacional — nada aqui é recomendação de investimento.
      </div>
    </div>
  );
}

function MercadoScreen({ ctx }) {
  const { data, quotes, analysis, expanded, analysisModel, setAnalysisModel, A, quotesAt, quotesLoading } = ctx;
  const wl = data.watchlist;
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", marginBottom: "6px" }}>
        <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em" }}>Mercado</h1>
        <div style={{ display: "flex", gap: "8px" }}>
          <IconBtn label="Atualizar cotações" onClick={A.refreshQuotes} busy={quotesLoading}>↻</IconBtn>
          <IconBtn label="Editar watchlist" onClick={A.openCatalog}>✎</IconBtn>
        </div>
      </div>
      <p style={{ margin: "0 0 12px", color: T.textMuted, fontSize: "13px", maxWidth: "560px", lineHeight: 1.55 }}>
        Sua watchlist com cotação atual. Escolha o modelo técnico e envie candles + indicadores para a IA.{quotesAt ? "  ·  atualizado " + quotesAt : ""}
      </p>
      <div style={{ ...card, padding: "12px", marginBottom: "14px", background: T.bgPanel }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "9px" }}>
          <div>
            <div style={{ fontSize: "11px", color: T.textFaint, letterSpacing: "0.06em" }}>MODELO DE ANÁLISE</div>
            <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "2px" }}>O backend calcula; a LLM interpreta os dados históricos.</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", overflowX: "auto", WebkitOverflowScrolling: "touch", paddingBottom: "2px" }}>
          {TECH_MODELS.map(([id, label, sub]) => (
            <button key={id} onClick={() => setAnalysisModel(id)} style={{ minWidth: "118px", minHeight: "48px", padding: "8px 10px", borderRadius: "12px", border: `1px solid ${analysisModel === id ? T.accent : T.borderSubtle}`, background: analysisModel === id ? T.accentTint : T.bgBase, color: analysisModel === id ? T.accent : T.textSecondary, textAlign: "left", fontWeight: 800 }}>
              <span style={{ display: "block", fontSize: "12px" }}>{label}</span>
              <span style={{ display: "block", fontSize: "10px", color: T.textFaint, fontWeight: 600, marginTop: "2px" }}>{sub}</span>
            </button>
          ))}
        </div>
      </div>

      {wl.length === 0 && (
        <div style={{ background: T.bgCard, border: `1px dashed ${T.borderDashed}`, borderRadius: "12px", padding: "34px 20px", textAlign: "center" }}>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Sua watchlist está vazia</div>
          <p style={{ margin: "8px auto 16px", color: T.textMuted, fontSize: "13px", maxWidth: "380px", lineHeight: 1.5 }}>Escolha entre as 20 blue chips do catálogo quais ativos quer acompanhar. A seleção fica salva.</p>
          <button onClick={A.openCatalog} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Escolher ativos →</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: "14px" }}>
        {wl.map((t) => {
          const q = quotes[t] || {};
          const an = analysis[t] || {};
          const name = (data.catalog.find((c) => c.t === t) || {}).n || t;
          const chColor = (q.change || 0) >= 0 ? T.positive : T.negative;
          return (
            <div key={t} style={{ ...card, padding: "14px 15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                <div>
                  <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "16px", letterSpacing: "0.02em" }}>{t}</div>
                  <div style={{ color: T.textMuted, fontSize: "12px", marginTop: "3px" }}>{name}</div>
                </div>
                <div style={{ textAlign: "right", fontFamily: MONO, minWidth: "92px" }}>
                  {q.price == null && !q.error && quotesLoading ? (
                    <>
                      <div className="sk" style={{ height: "18px", width: "84px", marginLeft: "auto" }} />
                      <div className="sk" style={{ height: "11px", width: "52px", marginLeft: "auto", marginTop: "6px" }} />
                    </>
                  ) : (
                    <>
                      <div style={{ fontSize: "18px", fontWeight: 700 }}>{q.error ? "—" : "R$ " + price(q.price)}</div>
                      <div style={{ fontSize: "12.5px", fontWeight: 700, color: q.error ? T.textFaint : chColor }}>{q.error ? "sem cotação" : pct(q.change)}</div>
                    </>
                  )}
                </div>
              </div>

              {an.modelLabel && <div style={{ marginTop: "10px", display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 8px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textMuted, fontSize: "11px" }}>Modelo: <b style={{ color: T.textSecondary }}>{an.modelLabel}</b>{an.candlesSentToLLM ? <span>· {an.candlesSentToLLM} candles enviados</span> : null}</div>}

              {an.kpis && <KpiBlock kpis={an.kpis} />}

              <div style={{ display: "flex", gap: "8px", marginTop: "14px" }}>
                <button onClick={() => A.analyze(t)} disabled={an.loading} style={{ flex: 1.5, minHeight: "44px", padding: "10px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: an.kpis ? T.accentTint : T.accent, color: an.kpis ? T.accent : T.bgBase, fontWeight: 800, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "7px" }}>
                  {an.loading ? <><Spinner size={13} color={an.kpis ? T.accent : T.bgBase} /> Analisando…</> : hasAnalysis(an) ? "Reanalisar" : "Analisar com IA"}
                </button>
                <button onClick={() => A.openBuy(t)} disabled={q.error || q.price == null} style={{ flex: 1, minHeight: "44px", padding: "10px", borderRadius: "9px", border: `1px solid ${T.positive}`, background: T.positiveTint10, color: T.positive, fontWeight: 700, fontSize: "13px" }}>Comprar</button>
              </div>

              {hasAnalysis(an) && (
                <button onClick={() => A.toggleExpand(t)} aria-expanded={!!expanded[t]} style={{ marginTop: "9px", width: "100%", minHeight: "40px", padding: "9px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "12.5px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                  {expanded[t] ? "Ocultar análise ▴" : "Ver análise da IA ▾"}
                </button>
              )}
              {expanded[t] && hasAnalysis(an) && (
                <div style={{ marginTop: "11px", paddingTop: "12px", borderTop: `1px solid ${T.borderSubtle}` }}>
                  <AnalysisView an={an} />
                </div>
              )}

              <button onClick={() => A.openTech(t)} disabled={q.error} style={{ marginTop: "9px", width: "100%", minHeight: "40px", padding: "9px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textMuted, fontWeight: 600, fontSize: "12.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span>📈 Indicadores técnicos</span>
                <span style={{ fontSize: "15px" }}>›</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// FASE 3: popup de stop/alvo, exclusivo da Carteira, acionado por ícone. Base do
// cálculo = localProposal (desacoplada na Fase 1). A IA (prompts.carteiraStopAlvo
// + BYOK) refina quando disponível; sem IA/chave, a estimativa por perfil vale.
// FASE 3 (revisão): popup INDIVIDUAL de stop/alvo de UM ativo da carteira.
// Acionado pelo ícone do card; analisa só aquele ativo; o usuário decide aplicar
// ou não NAQUELE ativo e a popup fecha. Base do cálculo = localProposal (Fase 1);
// a IA (prompts.carteiraStopAlvo + BYOK) propõe os números e a explicação.
function StopAlvoModal({ ctx }) {
  const { data, quotes, stopAlvo, stopAlvoFor, A } = ctx;
  const t = stopAlvoFor;
  if (!t) return null;
  const pos = (data.positions || []).find((p) => p.t === t);
  const q = quotes[t] || {};
  const base = q.price != null ? q.price : (pos ? pos.avg : null);
  const r = (stopAlvo && stopAlvo[t]) || {};
  const est = base != null ? (localProposal(base, data.profile) || {}) : {};
  const loading = !!r.loading;
  const done = r.loading === false;
  const aguardar = r.operar === false;
  const fromAI = done && !aguardar && (r.stop != null || r.alvo != null);
  // enquanto carrega/erro, mostra a estimativa por perfil como prévia
  const stop = aguardar ? null : (r.stop != null ? r.stop : (fromAI ? null : est.stop));
  const alvo = aguardar ? null : (r.alvo != null ? r.alvo : (fromAI ? null : est.alvo));
  const why = r.explicacao || (loading ? "" : est.rationale) || "";
  const canApply = !loading && !aguardar && (stop != null || alvo != null);
  const apply = () => A.applyStopAlvoFor(t, stop != null ? stop : null, alvo != null ? alvo : null);
  return (
    <div onClick={A.closeStopAlvo} style={{ position: "fixed", inset: 0, zIndex: 55, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "480px", maxHeight: "86vh", display: "flex", flexDirection: "column", ...card, borderRadius: "14px" }}>
        <div style={{ padding: "16px 18px", borderBottom: `1px solid ${T.borderSubtle}` }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
            <div style={{ fontSize: "16px", fontWeight: 700, fontFamily: MONO }}>{t} · stop e alvo</div>
            {loading && <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "11.5px", color: T.textMuted }}><Spinner size={12} /> IA analisando…</span>}
          </div>
          <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "4px", lineHeight: 1.5 }}>Sugestão por perfil <b>{(data.profile || {}).risco || "—"}</b> — conteúdo educacional, dinheiro simulado. <b>Não é recomendação</b> de compra ou venda.</div>
        </div>
        <div style={{ padding: "16px 18px", overflowY: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "10px" }}>
            <span style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: "0.04em", color: loading ? T.textMuted : aguardar ? T.textSecondary : fromAI ? T.accent : T.textSecondary }}>
              {loading ? "ANALISANDO…" : aguardar ? "SUGESTÃO: AGUARDAR" : fromAI ? "SUGESTÃO DA IA" : "ESTIMATIVA PELO PERFIL"}
            </span>
            {q.price != null && <span style={{ fontFamily: MONO, fontSize: "12px", color: T.textMuted }}>atual R$ {price(q.price)}</span>}
          </div>
          {!aguardar && (
            <div style={{ display: "flex", gap: "14px" }}>
              <div style={{ flex: 1, padding: "11px 12px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.negative}` }}>
                <div style={{ fontSize: "9.5px", color: T.textFaint, letterSpacing: "0.04em" }}>STOP</div>
                <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "17px", color: T.negative }}>{stop != null ? "R$ " + price(stop) : "—"}</div>
              </div>
              <div style={{ flex: 1, padding: "11px 12px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.positive}` }}>
                <div style={{ fontSize: "9.5px", color: T.textFaint, letterSpacing: "0.04em" }}>ALVO</div>
                <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "17px", color: T.positive }}>{alvo != null ? "R$ " + price(alvo) : "—"}</div>
              </div>
            </div>
          )}
          {why && <div style={{ marginTop: "13px", fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6 }}><Markdown text={why} /></div>}
          {r.error && <div style={{ marginTop: "10px", fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>IA indisponível ({r.error}) — exibindo a estimativa automática pelo seu perfil.</div>}
          <div style={{ marginTop: "13px", fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>Os níveis são uma sugestão dimensionada pelo seu perfil de risco. A decisão é sua — isto não é recomendação de investimento.</div>
        </div>
        <div style={{ padding: "14px 18px", borderTop: `1px solid ${T.borderSubtle}`, display: "flex", gap: "9px", justifyContent: "flex-end" }}>
          <button onClick={A.closeStopAlvo} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Fechar</button>
          <button onClick={apply} disabled={!canApply} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${canApply ? T.accent : T.borderSubtle}`, background: canApply ? T.accent : T.bgPanel, color: canApply ? T.onAccent : T.textFaint, fontWeight: 800, fontSize: "13px" }}>Aplicar em {t}</button>
        </div>
      </div>
    </div>
  );
}

function CarteiraScreen({ ctx }) {
  const { data, quotes, analysis, A, goMercado } = ctx;
  const byQ = (t) => quotes[t] || {};
<<<<<<< HEAD
  const m = portfolioMetrics(data.positions, quotes, data.cash);
  const positionsValue = m.posVal;
  const total = m.patr;
  const cost = m.cost;
  const openPnL = m.openPnL;
  const openPct = m.openPct;
=======
  const positionsValue = data.positions.reduce((s, p) => s + p.qty * (byQ(p.t).price || 0), 0);
  const total = data.cash + positionsValue;
  const cost = data.positions.reduce((s, p) => s + p.avg * p.qty, 0);
  const openPnL = data.positions.reduce((s, p) => s + ((byQ(p.t).price || p.avg) - p.avg) * p.qty, 0);
  const openPct = cost ? (openPnL / cost) * 100 : 0;
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  const kpi = (label, value, color, sub, subColor) => (
    <div style={{ ...card, padding: "14px 15px" }}>
      <div style={kicker}>{label}</div>
      <div style={{ fontFamily: MONO, fontSize: "19px", fontWeight: 600, marginTop: "3px", color }}>{value}</div>
      {sub != null && <div style={{ fontFamily: MONO, fontSize: "12px", color: subColor }}>{sub}</div>}
    </div>
  );
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
        <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Carteira</h1>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px", margin: "16px 0 18px" }}>
        {kpi("PATRIMÔNIO TOTAL", money(total), T.textPrimary)}
        {kpi("RESULTADO ABERTO", moneySigned(openPnL), openPnL >= 0 ? T.positive : T.negative, pct(openPct), openPnL >= 0 ? T.positive : T.negative)}
        {kpi("CAIXA DISPONÍVEL", money(data.cash), T.textMuted)}
        {kpi("EM POSIÇÕES", money(positionsValue), T.textMuted)}
      </div>

      {data.positions.length === 0 && (
        <div style={{ background: T.bgCard, border: `1px dashed ${T.borderDashed}`, borderRadius: "12px", padding: "34px 20px", textAlign: "center" }}>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Carteira vazia</div>
          <p style={{ margin: "8px auto 16px", color: T.textMuted, fontSize: "13px", maxWidth: "380px", lineHeight: 1.5 }}>Você ainda não tem posições. Vá ao Mercado e simule sua primeira compra — é dinheiro simulado, sem risco.</p>
          <button onClick={goMercado} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Ir ao mercado →</button>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "11px" }}>
        {data.positions.map((p) => {
          const q = byQ(p.t);
<<<<<<< HEAD
          const cur = markPrice(q, p);
          const avg = Number(p.avg) || 0;
          const pnl = (cur - avg) * p.qty;
          const pnlPct = avg > 0 ? (cur / avg - 1) * 100 : 0;
=======
          const cur = q.price != null ? q.price : p.avg;
          const pnl = (cur - p.avg) * p.qty;
          const pnlPct = (cur / p.avg - 1) * 100;
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          const color = pnl >= 0 ? T.positive : T.negative;
          const cell = (label, value, c) => (<div><div style={kicker}>{label}</div><div style={{ fontFamily: MONO, fontSize: "13px", color: c }}>{value}</div></div>);
          return (
            <div key={p.t} style={{ ...card, padding: "14px 15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", flexWrap: "wrap" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
                    <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "16px" }}>{p.t}</span>
                    <span style={{ color: T.textFaint, fontFamily: MONO, fontSize: "12px" }}>{p.qty} cotas</span>
                  </div>
                </div>
                <div style={{ textAlign: "right", fontFamily: MONO }}>
                  <div style={{ fontSize: "16px", fontWeight: 600, color }}>{moneySigned(pnl)}</div>
                  <div style={{ fontSize: "12px", color }}>{pct(pnlPct)}</div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "8px", marginTop: "13px" }}>
                {cell("P. MÉDIO", "R$ " + price(p.avg), T.textPrimary)}
                {cell("P. ATUAL", q.price != null ? "R$ " + price(cur) : "—", T.textPrimary)}
                {cell("STOP", p.stop != null ? "R$ " + price(p.stop) : "—", T.negative)}
                {cell("ALVO", p.alvo != null ? "R$ " + price(p.alvo) : "—", T.positive)}
              </div>
              <button onClick={() => ctx.openStopAlvo(p.t)} aria-label={"Sugerir stop e alvo de " + p.t + " com IA"} title="Sugerir stop e alvo por IA (sugestão por perfil)" style={{ marginTop: "12px", width: "100%", minHeight: "40px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 700, fontSize: "12.5px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden><path d="M3 17l5-5 4 4 7-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><path d="M15 8h5v5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                Sugerir stop e alvo (IA)
              </button>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                <input type="number" step="0.01" placeholder="stop" aria-label={"Stop de " + p.t} defaultValue={p.stop ?? ""} onBlur={(e) => A.setStop(p.t, e.target.value)} style={{ ...field, width: "92px", fontFamily: MONO, padding: "7px 9px" }} />
                <input type="number" step="0.01" placeholder="alvo" aria-label={"Alvo de " + p.t} defaultValue={p.alvo ?? ""} onBlur={(e) => A.setAlvo(p.t, e.target.value)} style={{ ...field, width: "92px", fontFamily: MONO, padding: "7px 9px" }} />
                <div style={{ fontSize: "12px", color: T.textMuted, marginLeft: "auto" }}>MV <span style={{ fontFamily: MONO, color: T.textPrimary, fontWeight: 600 }}>{money(p.qty * cur)}</span></div>
                <button onClick={() => A.sell(p.t)} style={{ padding: "8px 16px", borderRadius: "8px", border: `1px solid ${T.negative}`, background: T.negativeTint10, color: T.negative, fontWeight: 700, fontSize: "13px" }}>Vender</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function HistoricoScreen({ ctx }) {
  const { data } = ctx;
  const head = (flex, text, right) => (<div style={{ flex, textAlign: right ? "right" : "left" }}>{text}</div>);
  return (
    <div>
      <h1 style={{ margin: "0 0 16px", fontSize: "22px", fontWeight: 700 }}>Histórico de operações</h1>
      {data.history.length === 0 ? (
        <div style={{ background: T.bgCard, border: `1px dashed ${T.borderDashed}`, borderRadius: "12px", padding: "34px 20px", textAlign: "center" }}>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Nenhuma operação ainda</div>
          <p style={{ margin: "8px auto 0", color: T.textMuted, fontSize: "13px", maxWidth: "380px", lineHeight: 1.5 }}>Suas compras e vendas simuladas aparecerão aqui.</p>
        </div>
      ) : (
        <div style={{ ...card, overflow: "hidden" }}>
          <div style={{ display: "flex", gap: "10px", padding: "11px 15px", background: T.bgPanel, borderBottom: `1px solid ${T.borderSubtle}`, fontSize: "10px", letterSpacing: "0.06em", color: T.textFaint, fontFamily: MONO }}>
            {head(1.6, "DATA")}{head(1, "TIPO")}{head(0.9, "ATIVO")}{head(0.6, "QTD", true)}{head(1, "PREÇO", true)}{head(1.1, "RESULTADO", true)}
          </div>
          {data.history.map((h, i) => (
            <div key={i} style={{ display: "flex", gap: "10px", alignItems: "center", padding: "12px 15px", borderBottom: `1px solid ${T.borderFaint}`, fontFamily: MONO, fontSize: "13px" }}>
              <div style={{ flex: 1.6, color: T.textMuted, fontSize: "12px" }}>{h.date}</div>
              <div style={{ flex: 1 }}><span style={{ fontSize: "11px", fontWeight: 700, padding: "3px 7px", borderRadius: "5px", color: h.type === "COMPRA" ? T.positive : T.negative, background: h.type === "COMPRA" ? T.positiveTint : T.negativeTint }}>{h.type}</span></div>
              <div style={{ flex: 0.9, fontWeight: 700 }}>{h.t}</div>
              <div style={{ flex: 0.6, textAlign: "right", color: T.textSecondary }}>{h.qty}</div>
              <div style={{ flex: 1, textAlign: "right", color: T.textSecondary }}>R$ {price(h.price)}</div>
              <div style={{ flex: 1.1, textAlign: "right", fontWeight: 600, color: h.pnl == null ? T.textFaint : h.pnl >= 0 ? T.positive : T.negative }}>{h.pnl == null ? "—" : moneySigned(h.pnl)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgenteScreen({ ctx }) {
  const { data, A, cycleBusy } = ctx;
  const ag = data.agent;
  return (
    <div>
      <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Agente</h1>
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "13px", maxWidth: "600px", lineHeight: 1.5 }}>
        O agente remarca a carteira a mercado e protege stop/alvo das suas posições. Com o modo autônomo ligado, ele pode encerrar uma posição simulada ao tocar o stop ou o alvo.
      </p>

      <div style={{ marginTop: "16px", ...card, padding: "16px 17px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px" }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "15px" }}>Modo autônomo</div>
            <p style={{ margin: "4px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "440px" }}>Ligado: ao rodar o ciclo, vende automaticamente posições que atingiram stop ou alvo.</p>
          </div>
          <Toggle on={ag.autonomous} onClick={() => A.toggleAuto(!ag.autonomous)} label="Modo autônomo" />
        </div>
        <div style={{ marginTop: "16px", paddingTop: "15px", borderTop: `1px solid ${T.borderFaint}` }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label htmlFor="alloc" style={{ fontWeight: 600, fontSize: "14px" }}>Alocação por operação</label>
            <span style={{ fontFamily: MONO, fontSize: "15px", fontWeight: 600, color: T.accent }}>{ag.allocPct}%</span>
          </div>
          <input id="alloc" type="range" min="1" max="20" step="1" value={ag.allocPct} onChange={(e) => A.setAlloc(+e.target.value)} style={{ width: "100%", marginTop: "10px", accentColor: T.accent }} />
          <div style={{ fontSize: "12px", color: T.textFaint, marginTop: "4px" }}>Percentual de referência do patrimônio por nova posição (paper trading).</div>
        </div>

        <div style={{ marginTop: "16px", paddingTop: "15px", borderTop: `1px solid ${T.borderFaint}` }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: "14px" }}>Intervalo entre execuções</div>
              <p style={{ margin: "3px 0 0", color: T.textFaint, fontSize: "12px", lineHeight: 1.5, maxWidth: "420px" }}>Com o modo autônomo ligado, o ciclo roda sozinho nesta frequência {ag.autonomous ? "" : "(ligue o modo autônomo para ativar)"}.</p>
            </div>
            <span style={{ fontFamily: MONO, fontSize: "15px", fontWeight: 700, color: ag.autonomous ? T.accent : T.textFaint }}>{ag.intervalMin || 15} min</span>
          </div>
          <div style={{ display: "flex", gap: "7px", marginTop: "11px", flexWrap: "wrap" }}>
            {[5, 10, 15, 30, 60].map((m) => {
              const on = (ag.intervalMin || 15) === m;
              return (
                <button key={m} onClick={() => A.setAgentInterval(m)} aria-pressed={on} style={{ flex: 1, minWidth: "56px", minHeight: "40px", padding: "8px", borderRadius: "8px", fontSize: "13px", fontWeight: 700, border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgPanel, color: on ? T.accent : T.textMuted }}>{m}m</button>
              );
            })}
          </div>
        </div>

        <button onClick={A.cycle} disabled={cycleBusy} style={{ marginTop: "16px", width: "100%", padding: "12px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "14px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
          {cycleBusy && <Spinner size={14} color={T.bgBase} />} Executar ciclo agora
        </button>
      </div>

      <div style={{ marginTop: "16px" }}>
        <div style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.04em", color: T.textMuted, marginBottom: "10px" }}>EVENTOS E AVISOS RECENTES</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
          {ag.events.map((e, i) => (
            <div key={i} style={{ display: "flex", gap: "11px", ...card, borderRadius: "10px", padding: "12px 14px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: e.kind === "warn" ? T.accent : e.kind === "buy" ? T.positive : T.textFaint, marginTop: "5px", flex: "none" }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "13px", lineHeight: 1.5, color: T.textSecondary }}>{e.text}</div>
                <div style={{ fontFamily: MONO, fontSize: "11px", color: T.textFaint, marginTop: "4px" }}>{e.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Seção de Notificações LOCAIS — reflete a permissão REAL do sistema, pede no
// momento certo, dispara um teste com confirmação na tela e explica o caso iOS.
function NotifSection({ ctx }) {
  const { data, A } = ctx;
  const c = data.config || {};
  const nf = c.notif || { enabled: false, stop: true, alvo: true, agente: true, variacao: true };
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };
  const [perm, setPerm] = useState("default"); // granted | denied | default | unsupported
  const [msg, setMsg] = useState("");
  const refreshPerm = () => { notify.getPermission().then(setPerm).catch(() => setPerm("unsupported")); };
  useEffect(() => {
    refreshPerm();
    const onVis = () => { if (typeof document !== "undefined" && document.visibilityState === "visible") refreshPerm(); };
    if (typeof document !== "undefined") document.addEventListener("visibilitychange", onVis);
    return () => { if (typeof document !== "undefined") document.removeEventListener("visibilitychange", onVis); };
  }, []);
  const statusText = {
    granted: "Permissão concedida.",
<<<<<<< HEAD
    denied: "Permissão negada — ative em Ajustes → Notificações → BolsIA.",
=======
    denied: "Permissão negada — ative em Ajustes → Notificações → B3 Agente.",
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    default: "Permissão ainda não solicitada — ligue abaixo para pedir.",
    unsupported: isNative ? "Indisponível neste app — recompile (npm install + cap sync) para registrar o plugin." : "Seu navegador não suporta notificações.",
  }[perm] || "";
  const statusColor = perm === "granted" ? T.positive : (perm === "denied" || perm === "unsupported") ? T.negative : T.textMuted;
  const onMaster = async () => { setMsg(""); await A.setNotif({ enabled: !nf.enabled }); refreshPerm(); };
  const onRequestPermission = async () => {
    setMsg("Solicitando permissão do sistema…");
    const p = await notify.requestPermission();
    setPerm(p);
<<<<<<< HEAD
    setMsg(p === "granted" ? "Permissão concedida. Agora use o teste agendado." : (p === "denied" ? "Permissão negada pelo iOS. Ative em Ajustes → Notificações → BolsIA." : "Plugin ou navegador não suportou a permissão."));
  };
  const onTest = async () => {
    const id = await notify.schedule("BolsIA · teste imediato", "Teste técnico de notificação local.", new Date(Date.now() + (isNative ? 5000 : 500)));
=======
    setMsg(p === "granted" ? "Permissão concedida. Agora use o teste agendado." : (p === "denied" ? "Permissão negada pelo iOS. Ative em Ajustes → Notificações → B3 Agente." : "Plugin ou navegador não suportou a permissão."));
  };
  const onTest = async () => {
    const id = await notify.schedule("B3 Agente · teste imediato", "Teste técnico de notificação local.", new Date(Date.now() + (isNative ? 5000 : 500)));
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    setMsg(id != null
      ? (isNative ? "Teste agendado para 5s. Coloque o app em segundo plano para ver o banner; com app aberto, o iOS pode apenas registrar a entrega." : "Notificação de teste enviada/agendada.")
      : "Não foi possível enviar agora — verifique permissão, plugin e recompilação do app.");
  };
  const onTestScheduled = async () => {
<<<<<<< HEAD
    // BLOCO 1: 30s à frente — tempo suficiente para mandar o app para segundo
    // plano OU fechá-lo de vez (a entrega é do SISTEMA; independe do WebView).
    const id = await notify.schedule("Teste agendado", "Esta notificação foi agendada há 30 segundos.", new Date(Date.now() + 30000));
    setMsg(id != null
      ? (isNative ? "Agendada para daqui a 30s (id " + id + "). Mande o app para segundo plano — ou feche-o — para validar a entrega pelo sistema." : "Agendada para daqui a 30s (mantenha esta aba aberta).")
=======
    // FASE 4: agenda 10s à frente para validar o disparo "no horário agendado".
    const id = await notify.schedule("Teste agendado", "Esta notificação foi agendada há 10 segundos.", new Date(Date.now() + 10000));
    setMsg(id != null
      ? (isNative ? "Agendada para daqui a 10s. Mande o app para segundo plano para ver o banner." : "Agendada para daqui a 10s (mantenha esta aba aberta).")
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      : "Não foi possível agendar agora — verifique a permissão acima.");
  };
  const row = (key, label, desc) => (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", padding: "10px 0", opacity: nf.enabled ? 1 : 0.45 }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: "13px", fontWeight: 600 }}>{label}</div>
        <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.4 }}>{desc}</div>
      </div>
      <Toggle on={nf.enabled && nf[key] !== false} onClick={() => nf.enabled && A.setNotif({ [key]: !(nf[key] !== false) })} label={label} />
    </div>
  );
  return (
    <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px" }}>
        <div>
          <div style={sectionTitle}>NOTIFICAÇÕES</div>
          <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "5px", maxWidth: "420px", lineHeight: 1.5 }}>Avisos <b>locais</b> sobre movimentos da carteira simulada. Pediremos a permissão do sistema ao ativar.</div>
        </div>
        <Toggle on={!!nf.enabled} onClick={onMaster} label="Ativar notificações" />
      </div>

      <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "7px", fontSize: "12px", color: statusColor }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor, flex: "none" }} />
        {statusText}
      </div>

      <div style={{ marginTop: "8px", borderTop: `1px solid ${T.borderFaint}` }}>
        {row("stop", "Stop acionado", "Quando o preço cai até o seu stop.")}
        {row("alvo", "Alvo atingido", "Quando o preço alcança o seu alvo.")}
        {row("agente", "Operações do agente", "Compra/venda automática do agente autônomo.")}
        {row("variacao", "Movimentos fortes", "Variação relevante de uma posição no dia (±5%).")}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "12px", flexWrap: "wrap" }}>
        {perm !== "granted" && <button onClick={onRequestPermission} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "13px" }}>Pedir permissão</button>}
        <button onClick={onTest} disabled={perm !== "granted"} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${perm === "granted" ? T.accent : T.borderSubtle}`, background: perm === "granted" ? T.accentTint : T.bgPanel, color: perm === "granted" ? T.accent : T.textFaint, fontWeight: 700, fontSize: "13px" }}>Testar notificação</button>
        <button onClick={onTestScheduled} disabled={perm !== "granted"} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${perm === "granted" ? T.borderSubtle : T.borderSubtle}`, background: T.bgPanel, color: perm === "granted" ? T.textSecondary : T.textFaint, fontWeight: 700, fontSize: "13px" }}>Testar agendada (10s)</button>
        {msg && <span style={{ fontSize: "11.5px", color: T.textMuted, flex: 1, minWidth: "180px", lineHeight: 1.4 }}>{msg}</span>}
      </div>

      <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "11px", lineHeight: 1.5 }}>
        Isto é notificação <b>local</b> (disparada pelo próprio app). No iOS, para validar banner de teste, coloque o app em segundo plano após tocar em testar. Avisos com o app <b>fechado</b> por push/APNs não fazem parte desta versão.
      </div>
    </div>
  );
}

// FASE 2: rótulos/ajuda dos prompts conhecidos. Chaves extras (adicionadas no
// futuro) aparecem com o próprio nome — a interface não precisa mudar.
const PROMPT_META = {
  carteiraStopAlvo: {
    label: "Prompt — Análise de carteira (stop/alvo)",
    hint: "Usado na Carteira (Fase 3) para a IA propor stop e alvo por perfil. Mantenha o enquadramento educacional: sugestão por perfil, nunca recomendação de compra ou venda.",
  },
};

function PromptsSection({ ctx }) {
  const { data, A } = ctx;
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };
  const prompts = (data && data.llmPrompts) || {};
  const known = Object.keys(PROMPT_META);
  const extra = Object.keys(prompts).filter((k) => !known.includes(k));
  const keys = [...known, ...extra];
  return (
    <div style={{ marginTop: "14px", ...card, padding: "17px 18px" }}>
      <div style={sectionTitle}>CONFIG DE LLMs E PROMPTS</div>
      <p style={{ margin: "6px 0 16px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "580px" }}>Prompts que guiam as funções de IA da solução. Edite com cuidado — mantenha sempre o enquadramento educacional (sugestão por perfil, nunca recomendação de compra ou venda).</p>
      {keys.map((key) => {
        const meta = PROMPT_META[key] || { label: key, hint: "" };
        const value = typeof prompts[key] === "string" ? prompts[key] : "";
        return (
          <div key={key} style={{ marginBottom: "18px" }}>
            <label style={{ display: "block" }}>
              <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px", fontWeight: 600 }}>{meta.label}</span>
              <textarea value={value} onChange={(e) => A.editPrompt(key, e.target.value)} rows={11} style={{ width: "100%", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", color: T.textBright, fontFamily: MONO, fontSize: "12.5px", lineHeight: 1.6 }} />
            </label>
            {meta.hint && <div style={{ fontSize: "11px", color: T.textFaint, marginTop: "6px", lineHeight: 1.5 }}>{meta.hint}</div>}
            <div style={{ display: "flex", gap: "8px", marginTop: "11px" }}>
              <button onClick={() => A.savePrompt(key)} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Salvar</button>
              <button onClick={() => A.restorePrompt(key)} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Restaurar default</button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

<<<<<<< HEAD
/* BLOCO 3 — Radar de mercado. Varre o universo no SERVIDOR (cache-first) e
   lista, por ativo, as condições técnicas detectadas pelo motor de sinais.
   Linguagem 100% descritiva/educacional (nada de "compre/venda/entre agora");
   o score é INTENSIDADE de sinais, não direção. Período = candlePeriod da
   Config (mesma config nos dois stores). */
const RADAR_PERIOD_LABEL = { "1mo": "1M", "3mo": "3M", "6mo": "6M", "1y": "1A", "2y": "2A" };
function RadarScreen({ ctx }) {
  const { data } = ctx;
  const period = (data.config && data.config.candlePeriod) || "1y";
  const [st, setSt] = useState({ busy: false, res: null, error: "" });
  const ranFor = useRef(null);
  const run = useCallback(async (p) => {
    setSt((s) => ({ ...s, busy: true, error: "" }));
    try {
      const r = await store.scan(p);
      setSt({ busy: false, res: r, error: "" });
    } catch (e) {
      setSt((s) => ({ ...s, busy: false, error: (e && e.message) || String(e) }));
    }
  }, []);
  useEffect(() => {
    // varre ao abrir a aba e sempre que o período da Config mudar; o servidor
    // segura repetições (resultado cacheado por 60s por período+universo).
    if (ranFor.current === period) return;
    ranFor.current = period;
    run(period);
  }, [period, run]);
  const res = st.res;
  const results = (res && res.results) || [];
  const maxScore = results.reduce((m, r) => Math.max(m, r.score_tecnico || 0), 0) || 1;
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", marginBottom: "6px" }}>
        <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em" }}>Radar de mercado</h1>
        <IconBtn label="Varrer novamente" onClick={() => run(period)} busy={st.busy}>↻</IconBtn>
      </div>
      <p style={{ margin: "0 0 12px", color: T.textMuted, fontSize: "13px", maxWidth: "560px", lineHeight: 1.55 }}>
        Varredura do universo de ativos com o motor de sinais: quais condições técnicas
        estão ativas em cada papel, para você estudar — sem qualquer recomendação.
      </p>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "14px" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 10px", borderRadius: "999px", background: T.accentTint, border: `1px solid ${T.accent}`, color: T.accent, fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em" }}>
          PERÍODO EM USO: {RADAR_PERIOD_LABEL[period] || period}{res ? " · " + res.periodBars + " pregões" : ""}
        </span>
        {res && (
          <span style={{ fontSize: "11.5px", color: T.textFaint }}>
            {res.scanned}/{res.universeSize} ativos varridos{res.errors && res.errors.length ? " · " + res.errors.length + " sem dados" : ""} · {res.timestamp}
          </span>
        )}
      </div>

      {st.busy && !res && (
        <div style={{ ...card, padding: "22px 20px", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13.5px", fontWeight: 700 }}>
            <span className="spin" style={{ display: "inline-block", color: T.accent }}>↻</span> Varrendo o universo…
          </div>
          <p style={{ margin: "8px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5 }}>
            A primeira varredura do dia carrega o histórico de todos os ativos e pode levar
            até um minuto. As próximas voltam em segundos (cache no servidor).
          </p>
        </div>
      )}
      {st.error && (
        <div style={{ ...card, padding: "16px 18px", marginBottom: "14px", border: `1px solid ${T.negative}` }}>
          <div style={{ fontSize: "13px", fontWeight: 700, color: T.negative }}>A varredura falhou</div>
          <p style={{ margin: "6px 0 10px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{st.error}</p>
          <button onClick={() => run(period)} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Tentar de novo</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: "14px" }}>
        {results.map((r) => {
          const chColor = (r.variacaoPeriodoPct || 0) >= 0 ? T.positive : T.negative;
          const barPct = Math.round(((r.score_tecnico || 0) / maxScore) * 100);
          return (
            <div key={r.ticker} style={{ ...card, padding: "14px 15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                <div>
                  <div style={{ fontFamily: MONO, fontWeight: 800, fontSize: "16px", letterSpacing: "0.02em" }}>{r.ticker}</div>
                  <div style={{ color: T.textMuted, fontSize: "11.5px", marginTop: "3px" }}>{r.candles} candles no período</div>
                </div>
                <div style={{ textAlign: "right", fontFamily: MONO, minWidth: "92px" }}>
                  <div style={{ fontSize: "16px", fontWeight: 700 }}>{r.close != null ? "R$ " + price(r.close) : "—"}</div>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: chColor }}>{pct(r.variacaoPeriodoPct)} no período</div>
                </div>
              </div>
              <div style={{ marginTop: "11px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", color: T.textFaint, letterSpacing: "0.05em", marginBottom: "4px" }}>
                  <span>INTENSIDADE DE SINAIS</span><span style={{ fontFamily: MONO, fontWeight: 800, color: T.textSecondary }}>{r.score_tecnico}</span>
                </div>
                <div style={{ height: "6px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderFaint}`, overflow: "hidden" }}>
                  <div style={{ width: barPct + "%", height: "100%", background: T.accent, borderRadius: "999px" }} />
                </div>
              </div>
              {r.condicoes_detectadas && r.condicoes_detectadas.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "11px" }}>
                  {r.condicoes_detectadas.map((cnd, i) => (
                    <span key={i} style={{ padding: "5px 9px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textSecondary, fontSize: "11px", fontWeight: 600, lineHeight: 1.35 }}>{cnd}</span>
                  ))}
                </div>
              ) : (
                <div style={{ marginTop: "11px", fontSize: "11.5px", color: T.textFaint }}>Nenhuma condição marcante no fechamento mais recente.</div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ ...card, padding: "13px 16px", marginTop: "16px", background: T.bgPanel }}>
        <div style={{ fontSize: "11.5px", color: T.accent, lineHeight: 1.55 }}>{DISCLAIMERS.radar}</div>
      </div>
    </div>
  );
}

=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
function ConfigScreen({ ctx }) {
  const { data, A, test, themePref } = ctx;
  const c = data.config;
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };
  const seg = (on) => ({ flex: 1, padding: "10px", borderRadius: "8px", fontWeight: 600, fontSize: "13px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgPanel, color: on ? T.accent : T.textMuted });
  const testColor = test.status === "ok" ? T.positive : test.status === "error" ? T.negative : T.accent;
  const testBg = test.status === "ok" ? T.positiveTint10 : test.status === "error" ? T.negativeTint10 : T.accentTint10;
  const suggest = { anthropic: "Ex.: claude-sonnet-4 · claude-haiku-4", openai: "Ex.: gpt-4.1 · gpt-4o-mini", google: "Ex.: gemini-2.5-pro · gemini-2.5-flash", local: "Ex.: llama-3.1-70b · qwen2.5-72b" }[c.provider];
  const [srvTest, setSrvTest] = useState({ status: null, msg: "" });
  const [diagState, setDiagState] = useState({ status: null, text: "" });
  const handleTestServer = async () => {
    setSrvTest({ status: "testing", msg: "Testando…" });
    const r = await testServer(c.serverUrl);
    setSrvTest({ status: r.ok ? "ok" : "error", msg: r.message });
  };
  const runFullDiagnostic = async () => {
    setDiagState({ status: "testing", text: "Executando diagnóstico…" });
    const lines = [];
    const stamp = new Date().toISOString();
<<<<<<< HEAD
    lines.push("BolsIA · Diagnóstico iOS/WebView");
=======
    lines.push("B3 Agente · Diagnóstico iOS/WebView");
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    lines.push("Gerado em: " + stamp);
    lines.push("");
    try {
      const rt = describeRuntimeConfig();
      lines.push("[Runtime]");
      lines.push("nativeMode=" + rt.nativeMode);
      lines.push("apiBase=" + rt.apiBase);
      lines.push("serverUrlConfig=" + (c.serverUrl || "(vazio)"));
      lines.push("");
    } catch (e) { lines.push("[Runtime] ERRO: " + (e.message || e)); }
    try {
      const srv = await testServer(c.serverUrl);
      lines.push("[Servidor /api/health]");
      lines.push((srv.ok ? "OK" : "FALHA") + " - " + srv.message);
      lines.push("");
    } catch (e) { lines.push("[Servidor] ERRO: " + (e.message || e)); lines.push(""); }
    try {
      const ia = await store.testConfig();
      lines.push("[IA /api/config/test]");
      lines.push((ia.ok ? "OK" : "FALHA") + " - " + (ia.message || "sem mensagem"));
      if (ia.provider || ia.model || ia.keySource) lines.push("config=" + [ia.provider ? "provider=" + ia.provider : "", ia.model ? "model=" + ia.model : "", ia.keySource ? "keySource=" + ia.keySource : ""].filter(Boolean).join(", "));
      if (ia.action) lines.push("ação=" + ia.action);
      if (ia.hint) lines.push("dica=" + ia.hint);
      lines.push("");
    } catch (e) { lines.push("[IA] ERRO: " + (e.message || e)); lines.push(""); }
    try {
      const nd = await notify.diag();
      lines.push("[Notificações]");
      lines.push("isNative=" + nd.isNative);
      lines.push("pluginLoaded=" + nd.pluginLoaded);
      lines.push("hasSchedule=" + !!nd.hasSchedule);
      lines.push("hasRequest=" + !!nd.hasRequest);
      lines.push("permission=" + nd.permission);
      if (nd.error) lines.push("erro=" + nd.error);
      if (nd.permission === "granted") {
<<<<<<< HEAD
        const id = await notify.schedule("BolsIA · teste QA", "Validação técnica de notificação local agendada.", new Date(Date.now() + 8000));
=======
        const id = await notify.schedule("B3 Agente · teste QA", "Validação técnica de notificação local agendada.", new Date(Date.now() + 8000));
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
        lines.push("scheduledTestId=" + (id == null ? "falhou" : id));
        lines.push("ação=se estiver no iPhone, mande o app para segundo plano por 8 segundos para ver o banner.");
      } else {
        lines.push("ação=ative a permissão em Configurações → Notificações e rode o teste novamente.");
      }
      lines.push("");
    } catch (e) { lines.push("[Notificações] ERRO: " + (e.message || e)); lines.push(""); }
    lines.push("Checklist de correção rápida:");
    lines.push("1. API base deve ser URL absoluta, ex.: https://b3-production-8fc0.up.railway.app");
    lines.push("2. Se keySource=manual no iPhone, a chave precisa estar salva no próprio app.");
<<<<<<< HEAD
    lines.push("3. Se permissão=denied, corrigir em Ajustes do iOS → Notificações → BolsIA.");
=======
    lines.push("3. Se permissão=denied, corrigir em Ajustes do iOS → Notificações → B3 Agente.");
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    lines.push("4. Reinstale/recompile após mudanças de plugin: npm install && npx cap sync ios.");
    setDiagState({ status: "done", text: lines.join("\n") });
  };
  const copyDiag = async () => {
    try {
      await navigator.clipboard.writeText(diagState.text || "");
      setDiagState((d) => ({ ...d, status: "done", text: (d.text || "") + "\n\n[UI] Relatório copiado para a área de transferência." }));
    } catch {
      setDiagState((d) => ({ ...d, status: "done", text: (d.text || "") + "\n\n[UI] Não foi possível copiar automaticamente. Selecione e copie o texto acima." }));
    }
  };
  const srvColor = srvTest.status === "ok" ? T.positive : srvTest.status === "error" ? T.negative : T.accent;
  return (
    <div>
      <h1 style={{ margin: "0 0 18px", fontSize: "22px", fontWeight: 700 }}>Configurações</h1>

      {/* Personalização — nome e aparência (tema) */}
      <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
        <div style={sectionTitle}>PERSONALIZAÇÃO</div>
        <div style={{ marginTop: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Seu nome</span>
          <input value={c.userName || ""} onChange={(e) => A.saveName(e.target.value)} placeholder="Como prefere ser chamado" maxLength={40} style={field} />
        </div>
        <div style={{ marginTop: "16px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "8px" }}>Aparência</span>
          <div style={{ display: "flex", gap: "8px" }}>
            {[["light", "Claro"], ["dark", "Escuro"], ["system", "Sistema"]].map(([val, lab]) => (
              <button key={val} onClick={() => A.setTheme(val)} style={seg(themePref === val)}>{lab}</button>
            ))}
          </div>
          <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "8px", lineHeight: 1.5 }}>
            "Sistema" segue o tema do iPhone. O tema escuro mantém a identidade da mesa; o claro é a versão legível dela.
          </div>
        </div>
      </div>

<<<<<<< HEAD
      {/* Objetivo 4: período de candles do gráfico e da análise */}
      <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
        <div style={sectionTitle}>PERÍODO DE DADOS (CANDLES)</div>
        <p style={{ margin: "6px 0 14px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
          Janela de candles exibida no gráfico e enviada à IA na análise. Os indicadores
          (médias, RSI, MACD…) seguem calculados sobre um histórico maior — só a janela
          exibida/analisada muda.
        </p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {[["1mo", "1M"], ["3mo", "3M"], ["6mo", "6M"], ["1y", "1A"], ["2y", "2A"]].map(([val, lab]) => (
            <button key={val} onClick={() => A.saveConfig({ candlePeriod: val })} style={seg((c.candlePeriod || "1y") === val)}>{lab}</button>
          ))}
        </div>
      </div>

=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      {/* Notificações locais de movimentos da carteira */}
      <NotifSection ctx={ctx} />

      {/* Orçamento inicial SIMULADO — vira o caixa e entra no contexto da IA */}
      <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
        <div style={sectionTitle}>ORÇAMENTO DE INVESTIMENTO</div>
        <p style={{ margin: "6px 0 14px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
          Quanto você quer simular como capital inicial. Vira o caixa da carteira e
          entra no contexto da IA, para que tamanho de posição, stop e alvo fiquem
          coerentes com este valor e com o seu perfil de risco.
        </p>
        <div style={{ display: "flex", gap: "10px", alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 200px" }}>
            <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Orçamento disponível (R$)</span>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontFamily: MONO, color: T.textDim, fontSize: "15px" }}>R$</span>
              <input
                type="number" min="100" step="100" inputMode="decimal"
                value={Number.isFinite(data.config.initialBudget) ? data.config.initialBudget : 10000}
                onChange={(e) => { const v = parseFloat(e.target.value); A.saveBudget(Number.isFinite(v) ? v : 0); }}
                style={{ ...field, fontFamily: MONO, fontWeight: 700, fontSize: "16px" }}
              />
            </div>
          </div>
          <button
            onClick={() => { if (window.confirm("Recomeçar do zero? A carteira volta ao orçamento (R$ " + money(data.config.initialBudget) + ") e zera posições e histórico.")) A.resetPortfolio(); }}
            style={{ padding: "11px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textMuted, fontWeight: 600, fontSize: "13px", whiteSpace: "nowrap" }}
          >
            ↺ Recomeçar do zero
          </button>
        </div>
        <div style={{ fontSize: "11px", color: T.accent, marginTop: "10px" }}>{DISCLAIMERS.budget}</div>
      </div>

      {/* Perfil do operador — entra no prompt da IA */}
      {(() => {
        const pf = data.profile || {};
        const selStyle = { ...field, fontWeight: 600 };
        const Lab = ({ children }) => <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>{children}</span>;
        return (
          <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
            <div style={sectionTitle}>PERFIL DO OPERADOR</div>
            <p style={{ margin: "6px 0 16px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
              Estes parâmetros compõem o prompt enviado à IA. As recomendações, o stop e o alvo passam a ser adaptados ao seu perfil — um conservador recebe leitura diferente de um agressivo para o mesmo ativo.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: "12px" }}>
              <label>
                <Lab>Perfil de risco</Lab>
                <select value={pf.risco || "moderado"} onChange={(e) => A.saveProfile({ risco: e.target.value })} style={selStyle}>
                  <option value="conservador">Conservador</option>
                  <option value="moderado">Moderado</option>
                  <option value="agressivo">Agressivo</option>
                </select>
              </label>
              <label>
                <Lab>Horizonte</Lab>
                <select value={pf.horizonte || "swing"} onChange={(e) => A.saveProfile({ horizonte: e.target.value })} style={selStyle}>
                  <option value="intraday">Intraday (day trade)</option>
                  <option value="swing">Swing (dias/semanas)</option>
                  <option value="posicao">Posição (semanas/meses)</option>
                </select>
              </label>
              <label>
                <Lab>Objetivo</Lab>
                <select value={pf.objetivo || "crescimento"} onChange={(e) => A.saveProfile({ objetivo: e.target.value })} style={selStyle}>
                  <option value="preservacao">Preservação de capital</option>
                  <option value="renda">Renda</option>
                  <option value="crescimento">Crescimento</option>
                </select>
              </label>
              <label>
                <Lab>Experiência</Lab>
                <select value={pf.experiencia || "intermediario"} onChange={(e) => A.saveProfile({ experiencia: e.target.value })} style={selStyle}>
                  <option value="iniciante">Iniciante</option>
                  <option value="intermediario">Intermediário</option>
                  <option value="avancado">Avançado</option>
                </select>
              </label>
              <label>
                <Lab>Tolerância a perda por operação (%)</Lab>
                <input type="number" min="0.5" max="20" step="0.5" value={pf.toleranciaPerdaPct ?? 2}
                  onChange={(e) => A.saveProfile({ toleranciaPerdaPct: Number(e.target.value) })}
                  style={{ ...field, fontFamily: MONO }} />
              </label>
            </div>
          </div>
        );
      })()}

      {/* Servidor do app (somente no iPhone) */}
      {isNative && (
        <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
          <div style={sectionTitle}>SERVIDOR DO APP (MAC)</div>
          <p style={{ margin: "6px 0 14px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
            Endereço do computador que roda o servidor (usado para cotações e análise da IA), na mesma rede Wi-Fi. Fica salvo neste aparelho — troque aqui se o IP mudar, sem recompilar.
          </p>
          <label style={{ display: "block", marginBottom: "12px" }}>
            <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Endereço do servidor</span>
            <input type="text" value={c.serverUrl || ""} onChange={(e) => A.editConfig({ serverUrl: e.target.value })} onBlur={(e) => A.saveConfig({ serverUrl: e.target.value })} placeholder="http://192.168.0.12:8787" style={{ ...field, fontFamily: MONO }} />
          </label>
          <button onClick={handleTestServer} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Testar conexão</button>
          {srvTest.status && srvTest.status !== "testing" && (
            <div style={{ marginTop: "10px", fontSize: "12.5px", color: srvColor }}>{srvTest.msg}</div>
          )}
          {srvTest.status === "testing" && <div style={{ marginTop: "10px", fontSize: "12.5px", color: T.textMuted }}><Spinner /> {srvTest.msg}</div>}
        </div>
      )}

      <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
        <div style={sectionTitle}>DIAGNÓSTICO QA · iOS / IA / NOTIFICAÇÕES</div>
        <p style={{ margin: "6px 0 14px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
          Executa um teste integrado da URL do servidor, configuração da IA e plugin de notificações. Use este relatório para entender exatamente onde está a falha.
        </p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button onClick={runFullDiagnostic} disabled={diagState.status === "testing"} style={{ padding: "10px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "13px", display: "inline-flex", alignItems: "center", gap: "8px" }}>
            {diagState.status === "testing" && <Spinner size={13} />} Rodar diagnóstico completo
          </button>
          {diagState.text && (
            <button onClick={copyDiag} style={{ padding: "10px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>Copiar relatório</button>
          )}
        </div>
        {diagState.text && (
          <pre style={{ marginTop: "12px", maxHeight: "260px", overflow: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "10px", padding: "12px", color: T.textSecondary, fontFamily: MONO, fontSize: "11px", lineHeight: 1.5 }}>{diagState.text}</pre>
        )}
      </div>

      {/* A) Modelo de IA */}
      <div style={{ ...card, padding: "17px 18px" }}>
        <div style={sectionTitle}>MODELO DE IA DO AGENTE</div>
        <p style={{ margin: "6px 0 16px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>Provedor e modelo usados para gerar as análises. A chave nunca é exibida depois de salva e fica apenas {isNative ? "neste aparelho" : "no servidor"}.</p>

        <label style={{ display: "block", marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Provedor</span>
          <select value={c.provider} onChange={(e) => A.saveConfig({ provider: e.target.value })} style={field}>
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="google">Google</option>
            <option value="local">Compatível / Local</option>
          </select>
        </label>

        <label style={{ display: "block", marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Modelo</span>
          <input type="text" value={c.model} onChange={(e) => A.editConfig({ model: e.target.value })} onBlur={(e) => A.saveConfig({ model: e.target.value })} placeholder="nome-do-modelo" style={{ ...field, fontFamily: MONO }} />
          <span style={{ display: "block", fontSize: "11px", color: T.textFaint, marginTop: "5px", fontFamily: MONO }}>{suggest}</span>
        </label>

        <div style={{ marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Origem da chave</span>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={() => A.saveConfig({ keySource: "env" })} aria-pressed={c.keySource === "env"} style={seg(c.keySource === "env")}>Variável de ambiente</button>
            <button onClick={() => A.saveConfig({ keySource: "manual" })} aria-pressed={c.keySource === "manual"} style={seg(c.keySource === "manual")}>Digitar aqui</button>
          </div>
        </div>

        {c.keySource === "env" && (
          <div style={{ background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", padding: "12px 13px", marginBottom: "14px", fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
            Lendo a chave da variável <span style={{ fontFamily: MONO, color: T.accent }}>{c.envVar}</span> (ou <span style={{ fontFamily: MONO, color: T.accent }}>B3_AGENTE_API_KEY</span>) no servidor. O valor nunca é exibido.
          </div>
        )}
        {c.keySource === "manual" && c.keyStored && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", padding: "11px 13px", marginBottom: "14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "9px" }}>
              <span style={{ fontFamily: MONO, letterSpacing: "2px", color: T.textMuted }}>••••••••••••</span>
              <span style={{ fontSize: "11px", color: T.positive, fontWeight: 700 }}>chave configurada ✅ <span style={{ color: T.textFaint, fontWeight: 500 }}>{isNative ? "(neste aparelho)" : "(no servidor)"}</span></span>
            </div>
            <button onClick={A.clearKey} style={{ padding: "7px 12px", borderRadius: "7px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontSize: "12px", fontWeight: 600 }}>Substituir</button>
          </div>
        )}
        {c.keySource === "manual" && !c.keyStored && (
          <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
            <input type="password" value={ctx.keyDraft} onChange={(e) => ctx.setKeyDraft(e.target.value)} placeholder="cole a chave de API" aria-label="Chave de API" style={{ ...field, flex: 1, fontFamily: MONO }} />
            <button onClick={A.saveKey} style={{ padding: "10px 15px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Salvar chave</button>
          </div>
        )}

        {c.provider === "local" && (
          <label style={{ display: "block", marginBottom: "14px" }}>
            <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Base URL</span>
            <input type="text" value={c.baseUrl} onChange={(e) => A.editConfig({ baseUrl: e.target.value })} onBlur={(e) => A.saveConfig({ baseUrl: e.target.value })} placeholder="http://localhost:11434/v1" style={{ ...field, fontFamily: MONO }} />
          </label>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <button onClick={A.test} disabled={test.status === "testing"} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}>
            {test.status === "testing" && <Spinner size={13} />} {test.status === "testing" ? "Testando…" : "Testar conexão"}
          </button>
          {(test.status === "ok" || test.status === "error") && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", borderRadius: "8px", background: testBg, border: `1px solid ${testColor}` }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: testColor }} />
              <span style={{ fontSize: "12.5px", color: testColor, whiteSpace: "pre-wrap", lineHeight: 1.45 }}>{test.msg}</span>
            </div>
          )}
        </div>
      </div>

      {/* B) Skill */}
      <div style={{ marginTop: "14px", ...card, padding: "17px 18px" }}>
        <div style={sectionTitle}>INSTRUÇÕES DO AGENTE (SKILL)</div>
        <p style={{ margin: "6px 0 16px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "580px" }}>Estas instruções guiam a análise da IA. Reforce sempre: análise educacional, nunca prometer lucro, sempre destacar gerenciamento de risco.</p>

        <label style={{ display: "block", marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome do skill</span>
          <input type="text" value={data.skill.name} onChange={(e) => A.editSkill({ name: e.target.value })} style={{ ...field, fontFamily: MONO }} />
        </label>
        <label style={{ display: "block" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Instruções</span>
          <textarea value={data.skill.text} onChange={(e) => A.editSkill({ text: e.target.value })} rows={12} style={{ width: "100%", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", color: T.textBright, fontFamily: MONO, fontSize: "12.5px", lineHeight: 1.6 }} />
        </label>
        <div style={{ display: "flex", gap: "8px", marginTop: "13px" }}>
          <button onClick={A.saveSkill} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Salvar</button>
          <button onClick={A.restoreSkill} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Restaurar padrão</button>
        </div>
      </div>

      {/* C) Config de LLMs e Prompts (FASE 2) */}
      <PromptsSection ctx={ctx} />

      {/* Ponto único do aviso completo + boas-vindas */}
      <div style={{ display: "flex", gap: "10px", marginTop: "16px", flexWrap: "wrap" }}>
<<<<<<< HEAD
        <button onClick={ctx.openWelcomeAuth} style={{ flex: "1 1 160px", padding: "14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
=======
        <button onClick={ctx.openWelcome} style={{ flex: "1 1 160px", padding: "14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          <LogoMark size={18} /> Tela de boas-vindas
        </button>
        <button onClick={A.openAbout} style={{ flex: "1 1 160px", padding: "14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
          <span aria-hidden style={{ fontWeight: 700, color: T.accent }}>ⓘ</span> Sobre · Aviso legal
        </button>
      </div>
<<<<<<< HEAD
      <div style={{ textAlign: "center", fontSize: "11px", color: T.textFaint, marginTop: "12px" }}>BolsIA · simulador educacional · {DISCLAIMERS.short}</div>
=======
      <div style={{ textAlign: "center", fontSize: "11px", color: T.textFaint, marginTop: "12px" }}>B3 Agente · simulador educacional · {DISCLAIMERS.short}</div>
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    </div>
  );
}

function CatalogModal({ ctx }) {
  const { data, catalogSel, setCatalogSel, addState, setAddState, A } = ctx;
  const [tk, setTk] = useState("");
  const toggle = (t) => setCatalogSel((sel) => (sel.includes(t) ? sel.filter((x) => x !== t) : [...sel, t]));
  const submit = async () => {
    const v = tk.trim().toUpperCase();
    if (v.length < 4 || addState.busy) return;
    const ok = await A.addTicker(v);
    if (ok) setTk("");
  };
  return (
    <div onClick={A.closeCatalog} style={{ position: "fixed", inset: 0, zIndex: 50, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "520px", maxHeight: "82vh", display: "flex", flexDirection: "column", ...card, borderRadius: "14px" }}>
        <div style={{ padding: "16px 18px", borderBottom: `1px solid ${T.borderSubtle}` }}>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Editar watchlist</div>
          <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "3px" }}>{catalogSel.length} de {data.catalog.length} selecionados</div>
        </div>

        <div style={{ padding: "12px 18px", borderBottom: `1px solid ${T.borderSubtle}` }}>
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginBottom: "7px" }}>Adicionar outro ativo da B3 — digite o código; a existência é confirmada no Yahoo Finance.</div>
          <div style={{ display: "flex", gap: "8px" }}>
            <input
              value={tk}
              onChange={(e) => { setTk(e.target.value.toUpperCase()); if (addState.msg) setAddState({ busy: false, msg: "" }); }}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
              placeholder="ex.: TAEE11"
              maxLength={8}
              aria-label="Adicionar ticker"
              style={{ ...field, fontFamily: MONO }}
            />
            <button onClick={submit} disabled={addState.busy || tk.trim().length < 4} style={{ padding: "0 16px", minHeight: "44px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "13px", display: "flex", alignItems: "center", gap: "7px", whiteSpace: "nowrap" }}>
              {addState.busy ? <Spinner size={13} /> : null}Validar e adicionar
            </button>
          </div>
          {addState.msg && <div style={{ marginTop: "8px", fontSize: "12px", color: addState.msg.startsWith("✓") ? T.positive : T.negative }}>{addState.msg}</div>}
        </div>

        <div style={{ overflowY: "auto", padding: "12px 14px", display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(150px,1fr))", gap: "8px" }}>
          {data.catalog.map((cat) => {
            const on = catalogSel.includes(cat.t);
            const custom = !(data.custom == null) && (data.custom || []).some((x) => x.t === cat.t);
            return (
              <button key={cat.t} onClick={() => toggle(cat.t)} aria-pressed={on} style={{ textAlign: "left", padding: "10px 11px", borderRadius: "9px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgPanel }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px" }}>
                  <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "14px", color: on ? T.accent : T.textPrimary }}>{cat.t}{custom ? " •" : ""}</span>
                  <span style={{ width: "16px", height: "16px", borderRadius: "5px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accent : "transparent", color: T.onAccent, fontSize: "12px", fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center" }}>{on ? "✓" : ""}</span>
                </div>
                <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "3px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{cat.n}</div>
              </button>
            );
          })}
        </div>
        <div style={{ padding: "14px 18px", borderTop: `1px solid ${T.borderSubtle}`, display: "flex", gap: "8px", justifyContent: "flex-end" }}>
          <button onClick={A.closeCatalog} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Cancelar</button>
          <button onClick={A.saveCatalog} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Salvar watchlist</button>
        </div>
      </div>
    </div>
  );
}

function BuyModal({ ctx }) {
  const { buyModal, quotes, data, A, setBuyModal } = ctx;
  const t = buyModal.t;
  const q = quotes[t] || {};
  const name = (data.catalog.find((c) => c.t === t) || {}).n || t;
  const cost = (q.price || 0) * buyModal.qty;
  const ok = cost <= data.cash && q.price != null;
  return (
    <div onClick={A.closeBuy} style={{ position: "fixed", inset: 0, zIndex: 50, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "420px", ...card, borderRadius: "14px", padding: "20px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "11px", color: T.textFaint, letterSpacing: "0.06em" }}>COMPRA SIMULADA</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "3px" }}>
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "19px" }}>{t}</span>
              <span style={{ color: T.textMuted, fontSize: "13px" }}>{name}</span>
            </div>
          </div>
          <div style={{ textAlign: "right", fontFamily: MONO }}>
            <div style={{ fontSize: "10px", color: T.textFaint }}>PREÇO</div>
            <div style={{ fontSize: "16px", fontWeight: 600 }}>R$ {price(q.price)}</div>
          </div>
        </div>
        <div style={{ marginTop: "18px" }}>
          <div style={{ fontSize: "12px", color: T.textMuted, marginBottom: "8px" }}>Quantidade (lotes de 100)</div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button onClick={() => setBuyModal((b) => ({ ...b, qty: Math.max(100, b.qty - 100) }))} aria-label="Diminuir" style={{ width: "42px", height: "42px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "20px", fontWeight: 600 }}>−</button>
            <div style={{ flex: 1, textAlign: "center", fontFamily: MONO, fontSize: "22px", fontWeight: 600 }}>{buyModal.qty}</div>
            <button onClick={() => setBuyModal((b) => ({ ...b, qty: b.qty + 100 }))} aria-label="Aumentar" style={{ width: "42px", height: "42px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "20px", fontWeight: 600 }}>+</button>
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "16px", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "9px", fontFamily: MONO }}>
          <span style={{ color: T.textMuted, fontSize: "13px" }}>Custo estimado</span>
          <span style={{ fontWeight: 700, fontSize: "15px" }}>{money(cost)}</span>
        </div>
        {!ok && q.price != null && <div style={{ fontSize: "12px", color: T.negative, marginTop: "8px" }}>Caixa insuficiente. Disponível: {money(data.cash)}</div>}
        <div style={{ fontSize: "11px", color: T.textFaint, marginTop: "8px" }}>O preço final é o da cotação no momento da confirmação (servidor).</div>
        <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
          <button onClick={A.closeBuy} style={{ flex: 1, padding: "11px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "14px" }}>Cancelar</button>
          <button onClick={A.confirmBuy} disabled={!ok} style={{ flex: 1.4, padding: "11px", borderRadius: "9px", border: `1px solid ${ok ? T.positive : T.borderSubtle}`, background: ok ? T.positive : T.knob, color: ok ? T.confirmOkText : T.textFaint, fontWeight: 800, fontSize: "14px" }}>Confirmar compra</button>
        </div>
      </div>
    </div>
  );
}

function OptionsScreen({ ctx }) {
  const { data, A } = ctx;
  const defaultTicker = (data && data.watchlist && data.watchlist[0]) || "PETR4";
  const [ticker, setTicker] = useState(defaultTicker);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [chain, setChain] = useState(null);
  const [expiration, setExpiration] = useState("");
  const [side, setSide] = useState("calls");
  const [selected, setSelected] = useState(null);
  const [analysis, setOptAnalysis] = useState(null);

  const contracts = (chain && chain[side]) || [];
  const topContracts = contracts
    .slice()
    .sort((a, b) => ((b.openInterest || 0) + (b.volume || 0)) - ((a.openInterest || 0) + (a.volume || 0)))
    .slice(0, 18);

  const loadChain = useCallback(async (nextExpiration) => {
    const t = String(ticker || "").trim().toUpperCase();
    if (!t) return;
    setLoading(true); setErr(""); setSelected(null); setOptAnalysis(null);
    try {
      const r = await store.optionsChain(t, nextExpiration || expiration || undefined);
      setChain(r);
      if (!expiration && r.expiration) setExpiration(r.expiration);
      if ((!r.calls || !r.calls.length) && (!r.puts || !r.puts.length)) {
        setErr(r.warning || "O provedor não retornou opções para este ativo/vencimento.");
      }
    } catch (e) {
      setErr(e.message || String(e));
      setChain(null);
    } finally {
      setLoading(false);
    }
  }, [ticker, expiration]);

  useEffect(() => { loadChain(undefined); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const chooseExpiration = async (v) => {
    setExpiration(v);
    await loadChain(v);
  };

  const analyze = async (c) => {
    setSelected(c); setOptAnalysis({ loading: true });
    try {
      const r = await store.analyzeOption({ ticker, expiration: chain && chain.expiration, contractSymbol: c.contractSymbol });
      setOptAnalysis({ loading: false, ...r });
    } catch (e) {
      setOptAnalysis({ loading: false, error: e.message || String(e) });
    }
  };

  const small = { fontSize: "11px", color: T.textFaint };
  const cell = { padding: "8px 7px", borderBottom: `1px solid ${T.borderFaint}`, fontSize: "12px", whiteSpace: "nowrap" };

  return (
    <div style={{ display: "grid", gap: "14px" }}>
      <div style={{ ...card, padding: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={kicker}>B3 AGENTE OPÇÕES · EDUCACIONAL</div>
            <h2 style={{ margin: "4px 0 6px", fontSize: "22px" }}>Cadeia de opções e score de risco</h2>
            <p style={{ margin: 0, color: T.textMuted, fontSize: "13px", lineHeight: 1.45 }}>
              Estudo de calls/puts com liquidez, volatilidade, Black-Scholes, gregos e risco. Não é recomendação de investimento.
            </p>
          </div>
          <button onClick={() => A.go("mercado")} style={{ padding: "9px 12px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700 }}>Ver ações</button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: "10px", marginTop: "14px" }}>
          <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} placeholder="PETR4" style={field} />
          <select value={expiration} onChange={(e) => chooseExpiration(e.target.value)} style={field}>
            {(chain && chain.expirations && chain.expirations.length ? chain.expirations : [expiration].filter(Boolean)).map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
          <button onClick={() => loadChain(undefined)} disabled={loading} style={{ padding: "10px 14px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800 }}>{loading ? "Buscando…" : "Buscar"}</button>
        </div>
      </div>

      {err && <div style={{ ...card, padding: "13px", borderColor: T.accent, color: T.accent, fontSize: "13px" }}>{err}</div>}

      {chain && <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0,1fr))", gap: "10px" }}>
        <Metric title="Ativo objeto" value={chain.ticker || ticker} sub={chain.symbol || "Yahoo"} />
        <Metric title="Preço base" value={money(chain.underlyingPrice)} sub={chain.currency || ""} />
        <Metric title="Vol hist. 21d" value={chain.technical && chain.technical.hv21 ? (chain.technical.hv21 * 100).toFixed(1) + "%" : "—"} sub="HV anualizada" />
        <Metric title="Tendência" value={(chain.technical && chain.technical.trend) || "—"} sub="Leitura simples" />
      </div>}

      {chain && <div style={{ ...card, overflow: "hidden" }}>
        <div style={{ display: "flex", borderBottom: `1px solid ${T.borderSubtle}` }}>
          {[['calls','Calls'], ['puts','Puts']].map(([id, label]) => (
            <button key={id} onClick={() => { setSide(id); setSelected(null); setOptAnalysis(null); }} style={{ flex: 1, padding: "12px", border: "none", borderBottom: side === id ? `2px solid ${T.accent}` : "2px solid transparent", background: side === id ? T.accentTint10 : T.bgCard, color: side === id ? T.accent : T.textMuted, fontWeight: 800 }}>{label}</button>
          ))}
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: MONO }}>
            <thead>
              <tr style={{ color: T.textFaint, textAlign: "right" }}>
                <th style={{ ...cell, textAlign: "left" }}>Contrato</th><th style={cell}>Strike</th><th style={cell}>Último</th><th style={cell}>Bid/Ask</th><th style={cell}>Vol</th><th style={cell}>OI</th><th style={cell}>IV</th><th style={cell}>Liq.</th><th style={cell}>Score</th>
              </tr>
            </thead>
            <tbody>
              {topContracts.map((c) => (
                <tr key={c.contractSymbol || c.strike} onClick={() => analyze(c)} style={{ cursor: "pointer", background: selected && selected.contractSymbol === c.contractSymbol ? T.accentTint10 : "transparent" }}>
                  <td style={{ ...cell, textAlign: "left", color: T.textPrimary, fontWeight: 700 }}>{c.contractSymbol || "—"}</td>
                  <td style={cell}>{price(c.strike)}</td><td style={cell}>{price(c.lastPrice)}</td><td style={cell}>{price(c.bid)} / {price(c.ask)}</td><td style={cell}>{c.volume || 0}</td><td style={cell}>{c.openInterest || 0}</td><td style={cell}>{c.impliedVolatility ? (c.impliedVolatility * 100).toFixed(1) + "%" : "—"}</td><td style={cell}>{c.liquidity ? c.liquidity.score : "—"}</td><td style={{ ...cell, color: c.educationalScore && c.educationalScore.score >= 60 ? T.positive : T.accent }}>{c.educationalScore ? c.educationalScore.score : "—"}</td>
                </tr>
              ))}
              {!topContracts.length && <tr><td colSpan="9" style={{ padding: "18px", color: T.textMuted, textAlign: "center" }}>Sem contratos retornados para este vencimento.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>}

      {selected && <div style={{ ...card, padding: "15px" }}>
        <div style={kicker}>CONTRATO SELECIONADO</div>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "baseline", flexWrap: "wrap" }}>
          <h3 style={{ margin: "4px 0", fontFamily: MONO }}>{selected.contractSymbol}</h3>
          <span style={{ color: T.textMuted, fontSize: "13px" }}>Breakeven: {price(selected.breakeven)} · Theta/dia: {selected.blackScholes ? selected.blackScholes.theta : "—"}</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0,1fr))", gap: "8px", marginTop: "8px" }}>
          <Metric title="Delta" value={selected.blackScholes ? selected.blackScholes.delta : "—"} sub="sensibilidade" />
          <Metric title="Gamma" value={selected.blackScholes ? selected.blackScholes.gamma : "—"} sub="aceleração" />
          <Metric title="Vega" value={selected.blackScholes ? selected.blackScholes.vega : "—"} sub="volatilidade" />
          <Metric title="Theo." value={selected.blackScholes ? price(selected.blackScholes.theoretical) : "—"} sub="Black-Scholes" />
          <Metric title="Prob. ITM" value={selected.blackScholes ? (selected.blackScholes.prob_itm * 100).toFixed(1) + "%" : "—"} sub="aprox." />
        </div>
        {analysis && <div style={{ marginTop: "12px", padding: "12px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: analysis.error ? T.negative : T.textSecondary, fontSize: "13px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
          {analysis.loading ? "Gerando leitura educacional…" : analysis.error ? analysis.error : ((analysis.riskFlags || []).join("\n") + "\n\n" + (analysis.markdown || ""))}
        </div>}
        <p style={{ ...small, marginTop: "10px" }}>Opções têm risco elevado e podem perder 100% do prêmio. O score é apenas educacional e não gera ordem de compra ou venda.</p>
      </div>}
    </div>
  );
}

function Metric({ title, value, sub }) {
  return (
    <div style={{ ...card, padding: "10px", background: T.bgPanel }}>
      <div style={{ fontSize: "10px", color: T.textFaint, letterSpacing: "0.05em" }}>{title}</div>
      <div style={{ marginTop: "3px", fontWeight: 800, fontFamily: MONO, fontSize: "15px", color: T.textPrimary }}>{value == null ? "—" : value}</div>
      {sub && <div style={{ marginTop: "2px", fontSize: "11px", color: T.textMuted }}>{sub}</div>}
    </div>
  );
}


/* --------------------------------- App ----------------------------------- */
export default function App() {
  const [data, setData] = useState(null);
  const [loadErr, setLoadErr] = useState(null);
  const [quotes, setQuotes] = useState({});
  const [quotesAt, setQuotesAt] = useState(null);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [tab, setTab] = useState("evolucao");
  const [carteiraView, setCarteiraView] = useState("main"); // main | historico
  const [perfilView, setPerfilView] = useState("hub");       // hub | config | agente
  const navigate = (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); };
  const [analysis, setAnalysis] = useState({});
  const [expanded, setExpanded] = useState({});
  const [analysisModel, setAnalysisModel] = useState("completo");
  const [toast, setToast] = useState(null);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [catalogSel, setCatalogSel] = useState([]);
  const [buyModal, setBuyModal] = useState(null);
  const [techFor, setTechFor] = useState(null);
  const [keyDraft, setKeyDraft] = useState("");
  const [test, setTest] = useState({ status: null, msg: "" });
  const [cycleBusy, setCycleBusy] = useState(false);
  const [addState, setAddState] = useState({ busy: false, msg: "" });
  // Tema: preferência (dark|light|system) vinda da config; resolvido p/ dark|light.
  const sysDark = () => (typeof window !== "undefined" && window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : true);
  const [sysIsDark, setSysIsDark] = useState(sysDark);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const [stopAlvoFor, setStopAlvoFor] = useState(null); // FASE 3: ticker do popup de stop/alvo (individual)
  const [stopAlvo, setStopAlvo] = useState({}); // FASE 3: resultados por ticker { loading, stop, alvo, explicacao, operar, error }
  // FASE 2: conta opcional. authUser=null => anônimo (app abre normalmente).
  const [authUser, setAuthUser] = useState(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [welcomeAuthOpen, setWelcomeAuthOpen] = useState(false); // tela de abertura (login)
  const welcomeShownRef = useRef(false);
  const themePref = (data && data.config && data.config.theme) || (typeof localStorage !== "undefined" && localStorage.getItem("b3-theme")) || "dark";
  const themeKey = themePref === "system" ? (sysIsDark ? "dark" : "light") : themePref;
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const on = (e) => setSysIsDark(e.matches);
    try { mq.addEventListener("change", on); } catch { mq.addListener(on); }
    return () => { try { mq.removeEventListener("change", on); } catch { mq.removeListener(on); } };
  }, []);
  useEffect(() => {
    if (typeof document === "undefined") return;
    const html = document.documentElement;
    html.classList.remove("b3-theme-dark", "b3-theme-light");
    html.classList.add("b3-theme-" + themeKey);
    try { localStorage.setItem("b3-theme", themePref); } catch { /* ignore */ }
  }, [themeKey, themePref]);
  const cfgTimer = useRef(null);
  const cycleRef = useRef(null);
  // Pull-to-refresh (mobile) sobre o scroller principal.
  const mainRef = useRef(null);
  const [pullY, setPullY] = useState(0);
  const pullYRef = useRef(0); pullYRef.current = pullY;
  const refreshRef = useRef(null);

  const flash = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast((cur) => (cur === msg ? null : cur)), 2600);
  }, []);

<<<<<<< HEAD
  // Objetivo 2: notificações locais aparecem MESMO com o app aberto. No iOS o
  // banner do sistema é suprimido em foreground; aqui mostramos um aviso in-app
  // (toast) quando uma notificação dispara com o app aberto. A notificação do
  // sistema segue valendo para quando o app está em segundo plano.
  useEffect(() => {
    notify.setForegroundHandler((title, body) => flash(body ? (title + " — " + body) : title));
    notify.setup();
    return () => notify.setForegroundHandler(null);
  }, [flash]);

=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  const loadState = useCallback(async () => {
    try {
      const s = await store.getState();
      setData(s);
      if (s.analyses && typeof s.analyses === "object") {
        const seed = {};
        for (const t of Object.keys(s.analyses)) {
          const a = s.analyses[t] || {};
          seed[t] = { loading: false, text: a.text || a.analysis || "", markdown: a.markdown || a.text || a.analysis || "", kpis: a.kpis || null, detail: a.detail || null, proposal: a.proposal || null, model: a.model || null, modelLabel: a.modelLabel || null, technicalContext: a.technicalContext || null, candlesSentToLLM: a.candlesSentToLLM || null, at: a.at || null };
        }
        if (Object.keys(seed).length) setAnalysis((cur) => ({ ...seed, ...cur }));
      }
      setLoadErr(null);
    } catch (e) {
      setLoadErr(e.message || String(e));
    }
  }, []);

  const refreshQuotes = useCallback(async () => {
    setQuotesLoading(true);
    try {
      const r = await store.getQuotes();
      setQuotes(r.quotes || {});
      setQuotesAt(r.at || null);
    } catch (e) {
      flash("Cotações: " + (e.message || e));
    } finally {
      setQuotesLoading(false);
    }
  }, [flash]);

  useEffect(() => {
    loadState();
  }, [loadState]);
  // FASE 2: ao abrir, se houver sessão salva, recupera o usuário (e o estado
  // já no escopo da conta). Totalmente guardado: qualquer falha => segue anônimo.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        if (!auth || typeof auth.me !== "function") return;
        const r = await auth.me();
        if (alive && r && r.user) {
          setAuthUser(r.user);
          if (r.state) setData(r.state);
        }
      } catch { /* sessão inválida/sem rede: app segue sem login */ }
    })();
    return () => { alive = false; };
  }, []);
  useEffect(() => {
    if (data) refreshQuotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data && Array.isArray(data.watchlist) ? data.watchlist.join(",") : ""]);

  const A = useMemo(() => ({
    refreshQuotes,
    go: (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); },
    openCatalog: () => { setCatalogSel(data ? [...data.watchlist] : []); setCatalogOpen(true); },
    closeCatalog: () => setCatalogOpen(false),
    saveCatalog: async () => {
      try { const s = await store.putWatchlist(catalogSel); setData(s); setCatalogOpen(false); flash("Watchlist salva."); }
      catch (e) { flash("Erro: " + (e.message || e)); }
    },
    analyze: async (t) => {
      // GANCHO FREEMIUM (hoje sempre permite): limite de análises/mês do gratuito.
      const gate = canAnalyze(0); // FUTURO: passar contagem do mês
      if (!gate.ok) { flash(gate.reason); setAnalysis((a) => ({ ...a, [t]: { loading: false, error: gate.reason } })); setExpanded((x) => ({ ...x, [t]: true })); return; }
      setExpanded((x) => ({ ...x, [t]: true }));
      setAnalysis((a) => ({ ...a, [t]: { ...(a[t] || {}), loading: true, error: null } }));
      try {
        const r = await store.analyze(t, { model: analysisModel });
        setAnalysis((a) => ({ ...a, [t]: { loading: false, text: r.text || r.analysis || "", markdown: r.markdown || r.text || r.analysis || "", kpis: r.kpis || null, detail: r.detail || null, proposal: r.proposal || null, model: r.model, modelLabel: r.modelLabel, technicalContext: r.technicalContext || null, candles: r.candles, candlesSentToLLM: r.candlesSentToLLM, at: r.at, quote: r.quote } }));
      } catch (e) {
        setAnalysis((a) => ({ ...a, [t]: { loading: false, error: e.message || String(e) } }));
      }
    },
    toggleExpand: (t) => setExpanded((x) => ({ ...x, [t]: !x[t] })),
    openBuy: (t) => setBuyModal({ t, qty: 100 }),
    closeBuy: () => setBuyModal(null),
    openTech: (t) => setTechFor(t),
    closeTech: () => setTechFor(null),
    confirmBuy: async () => {
      const bm = buyModal; if (!bm) return;
      try { const s = await store.buy(bm.t, bm.qty); setData(s); setBuyModal(null); flash("Compra simulada: " + bm.qty + " " + bm.t + "."); }
      catch (e) { flash("Compra: " + (e.message || e)); }
    },
    sell: async (t) => {
      try { const s = await store.sell(t); setData(s); flash("Venda simulada: " + t + "."); }
      catch (e) { flash("Venda: " + (e.message || e)); }
    },
    setStop: async (t, v) => { try { const s = await store.putPosition(t, { stop: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setAlvo: async (t, v) => { try { const s = await store.putPosition(t, { alvo: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    applyProposal: async (t, stop, alvo) => {
      try {
        const s = await store.putPosition(t, { stop, alvo });
        setData(s);
        setAnalysis((a) => ({ ...a, [t]: { ...(a[t] || {}), applied: true } })); // fecha o popup de sugestão
        flash("Stop/alvo aplicados em " + t + ".");
      } catch (e) { flash("Erro: " + (e.message || e)); }
    },
    toggleAuto: async (v) => { try { const s = await store.putAgent({ autonomous: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setAlloc: async (v) => { setData((d) => ({ ...d, agent: { ...d.agent, allocPct: v } })); try { await store.putAgent({ allocPct: v }); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setAgentInterval: async (v) => { setData((d) => ({ ...d, agent: { ...d.agent, intervalMin: v } })); try { await store.putAgent({ intervalMin: v }); } catch (e) { flash("Erro: " + (e.message || e)); } },
    saveBudget: (v) => {
      // orçamento simulado: controlado + persistido com debounce
      setData((d) => ({ ...d, config: { ...d.config, initialBudget: v } }));
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => {
        cfgTimer.current = null;
        store.putConfig({ initialBudget: v }).then((s) => setData(s)).catch((e) => flash("Orçamento: " + (e.message || e)));
      }, 600);
    },
    resetPortfolio: async () => {
      try { const s = await store.resetPortfolio(); setData(s); flash("Carteira reiniciada com o orçamento simulado."); }
      catch (e) { flash("Erro: " + (e.message || e)); }
    },
    setTheme: async (v) => {
      setData((d) => ({ ...d, config: { ...d.config, theme: v } }));
      try { localStorage.setItem("b3-theme", v); } catch { /* ignore */ }
      try { await store.putConfig({ theme: v }); } catch (e) { flash("Tema: " + (e.message || e)); }
    },
    saveName: (v) => {
      setData((d) => ({ ...d, config: { ...d.config, userName: v } }));
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => { cfgTimer.current = null; store.putConfig({ userName: v }).then((s) => setData(s)).catch((e) => flash("Nome: " + (e.message || e))); }, 600);
    },
    // FASE 2: edição/salvamento da coleção de prompts (mesmo padrão do skill).
    editPrompt: (key, text) => setData((d) => ({ ...d, llmPrompts: { ...(d.llmPrompts || {}), [key]: text } })),
    savePrompt: async (key) => {
      const text = ((data && data.llmPrompts) || {})[key] || "";
      try { const s = await store.putLlmPrompts({ [key]: text }); setData(s); flash("Prompt salvo."); }
      catch (e) { flash("Prompt: " + (e.message || e)); }
    },
    restorePrompt: async (key) => {
      const def = (defaultLlmPrompts() || {})[key] || "";
      setData((d) => ({ ...d, llmPrompts: { ...(d.llmPrompts || {}), [key]: def } }));
      try { const s = await store.putLlmPrompts({ [key]: def }); setData(s); flash("Prompt restaurado ao padrão."); }
      catch (e) { flash("Prompt: " + (e.message || e)); }
    },
    // FASE 3: análise INDIVIDUAL de stop/alvo de um ativo da carteira, via prompt
    // configurável + BYOK. Resultado fica em `stopAlvo[t]`, transitório (popup).
    closeStopAlvo: () => setStopAlvoFor(null),
    runStopAlvoFor: async (t) => {
      const prompt = ((data && data.llmPrompts) || {}).carteiraStopAlvo || "";
      setStopAlvo((s) => ({ ...s, [t]: { ...(s[t] || {}), loading: true, error: null } }));
      try {
        const r = await store.analyzeStopAlvo(t, { prompt });
        const prop = r.proposal || {};
        setStopAlvo((s) => ({ ...s, [t]: { loading: false, stop: prop.stop != null ? prop.stop : null, alvo: prop.alvo != null ? prop.alvo : null, explicacao: r.explicacao || "", operar: r.operar, at: r.at } }));
      } catch (e) {
        setStopAlvo((s) => ({ ...s, [t]: { ...(s[t] || {}), loading: false, error: e.message || String(e) } }));
      }
    },
    applyStopAlvoFor: async (t, stop, alvo) => {
      try {
        const s = await store.putPosition(t, { stop, alvo });
        setData(s);
        flash("Stop e alvo aplicados em " + t + ".");
      } catch (e) { flash("Erro ao aplicar: " + (e.message || e)); }
      setStopAlvoFor(null);
    },
    openAbout: () => setAboutOpen(true),
    closeAbout: () => setAboutOpen(false),
    setNotif: async (patch) => {
      const p = { ...patch };
      // momento certo: ao LIGAR o mestre, pede permissão do sistema
      if (patch.enabled === true) {
        const perm = await notify.requestPermission();
        if (perm !== "granted") {
          p.enabled = false;
<<<<<<< HEAD
          if (perm === "denied") flash("Permissão negada. Ative em Ajustes → Notificações → BolsIA.");
=======
          if (perm === "denied") flash("Permissão negada. Ative em Ajustes → Notificações → B3 Agente.");
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          else flash(isNative ? "Plugin de notificações não registrado. Rode 'npm install' e recompile (cap sync)." : "Notificações não são suportadas neste navegador.");
        } else {
          notify.send("Notificações ativadas", "Você será avisado sobre stop, alvo e movimentos da carteira.");
        }
      }
      setData((d) => ({ ...d, config: { ...d.config, notif: { ...(d.config.notif || {}), ...p } } }));
      try { await store.putConfig({ notif: p }); } catch (e) { flash("Notif: " + (e.message || e)); }
    },
    cycle: async () => {
      setCycleBusy(true);
      const beforeN = (data.agent && data.agent.events ? data.agent.events.length : 0);
      try {
        const s = await store.cycle();
        setData(s); if (s.quotes) setQuotes((q) => ({ ...q, ...s.quotes })); flash("Ciclo executado.");
        const n = s.config && s.config.notif;
        const evs = (s.agent && s.agent.events) || [];
        if (n && n.enabled && n.agente !== false && evs.length > beforeN) {
          const ev = evs[0];
          if (ev && /compr|vend/i.test((ev.kind || "") + " " + (ev.text || ""))) notify.notifyIfEnabled(n, "agente", "Agente operou na carteira", ev.text || "O agente executou uma operação.");
        }
      } catch (e) { flash("Ciclo: " + (e.message || e)); }
      finally { setCycleBusy(false); }
    },
    saveConfig: async (patch) => { if (cfgTimer.current) { clearTimeout(cfgTimer.current); cfgTimer.current = null; } try { const s = await store.putConfig(patch); setData(s); setTest({ status: null, msg: "" }); } catch (e) { flash("Config: " + (e.message || e)); } },
    editConfig: (patch) => {
      // atualiza o campo na hora (controlado) e persiste com debounce
      setData((d) => ({ ...d, config: { ...d.config, ...patch } }));
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => {
        cfgTimer.current = null;
        store.putConfig(patch).then((s) => setData(s)).catch((e) => flash("Config: " + (e.message || e)));
      }, 600);
    },
    saveKey: async () => {
      if (!keyDraft.trim()) return;
      try { const s = await store.putConfig({ apiKey: keyDraft.trim() }); setData(s); setKeyDraft(""); flash(isNative ? "Chave salva neste aparelho." : "Chave salva no servidor."); }
      catch (e) { flash("Chave: " + (e.message || e)); }
    },
    clearKey: async () => { try { const s = await store.putConfig({ clearKey: true }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    test: async () => {
      setTest({ status: "testing", msg: "" });
      try {
        const r = await store.testConfig();
        const detail = [
          r.message || "Sem mensagem",
          (r.provider || r.model || r.keySource) ? "Configuração: " + [r.provider ? "provedor=" + r.provider : "", r.model ? "modelo=" + r.model : "", r.keySource ? "chave=" + r.keySource : ""].filter(Boolean).join(", ") : "",
          r.action ? "Como corrigir: " + r.action : "",
          r.hint ? "Dica: " + r.hint : "",
        ].filter(Boolean).join("\n");
        setTest({ status: r.ok ? "ok" : "error", msg: detail });
      }
      catch (e) { setTest({ status: "error", msg: e.message || String(e) }); }
    },
    editSkill: (patch) => setData((d) => ({ ...d, skill: { ...d.skill, ...patch } })),
    saveSkill: async () => { try { const s = await store.putSkill({ name: data.skill.name, text: data.skill.text }); setData(s); flash("Skill salva."); } catch (e) { flash("Skill: " + (e.message || e)); } },
    restoreSkill: async () => { try { const s = await store.restoreSkill(); setData(s); flash("Instruções restauradas ao padrão."); } catch (e) { flash("Erro: " + (e.message || e)); } },
    saveProfile: async (patch) => {
      // otimista: reflete na hora e persiste (o perfil entra no prompt da IA)
      setData((d) => ({ ...d, profile: { ...d.profile, ...patch } }));
      try { const s = await store.putProfile(patch); setData(s); } catch (e) { flash("Perfil: " + (e.message || e)); }
    },
    addTicker: async (ticker) => {
      const dbg = (() => { try { return (typeof window !== "undefined" && window.B3_DEBUG) || (typeof localStorage !== "undefined" && localStorage.getItem("b3-debug")); } catch { return false; } })();
      // GANCHO FREEMIUM (hoje sempre permite): limite de ativos do tier gratuito.
      const gate = canAddTicker((data.watchlist || []).length);
      if (!gate.ok) { setAddState({ busy: false, msg: "✗ " + gate.reason }); return false; }
      setAddState({ busy: true, msg: "" });
      try {
        const s = await store.addWatchlistTicker(ticker);
        setData(s); // (g) UI relê o estado retornado pelo store
        if (dbg) console.log("[b3:add:g-setData]", { watchlist: s.watchlist, added: s.added });
        if (s.added) {
          setCatalogSel((sel) => Array.from(new Set([...(sel || []), s.added.t])));
          refreshQuotes(); // (h) recarrega cotações para o novo ativo já aparecer com preço
        }
        setAddState({ busy: false, msg: "✓ " + (s.added ? s.added.t + " adicionado à watchlist" : "adicionado") });
        return true;
      } catch (e) {
        if (dbg) console.log("[b3:add:erro]", e && e.message);
        setAddState({ busy: false, msg: "✗ " + (e.message || String(e)) });
        return false;
      }
    },
  }), [data, catalogSel, buyModal, keyDraft, refreshQuotes, flash, analysisModel]);

  // Mantém a referência do ciclo sempre atual (sem reiniciar o timer a cada render)
  cycleRef.current = A.cycle;
  // Modo autônomo: executa o ciclo automaticamente no intervalo configurado.
  const autoOn = !!(data && data.agent && data.agent.autonomous);
  const autoMin = data && data.agent ? data.agent.intervalMin || 15 : 15;
  useEffect(() => {
    if (!autoOn) return undefined;
    const mins = Math.max(1, autoMin);
    const id = setInterval(() => { if (cycleRef.current) cycleRef.current(); }, mins * 60000);
    return () => clearInterval(id);
  }, [autoOn, autoMin]);

  // Pull-to-refresh: ao puxar a partir do topo, atualiza as cotações.
  refreshRef.current = A.refreshQuotes;
  useEffect(() => {
    const el = mainRef.current;
    if (!el) return undefined;
    const THRESH = 70, MAX = 110, ENGAGE = 14; // só engata após arrasto real
    const INTERACTIVE = "button,input,textarea,select,a,[role=switch],[role=button]";
    const st = { active: false, startY: 0, pulling: false };
    const onStart = (e) => {
      st.active = false; st.pulling = false;
      // não capturar gestos que começam num controle (senão o clique é cancelado no iOS)
      const tgt = e.target;
      if (tgt && tgt.closest && tgt.closest(INTERACTIVE)) return;
      if (el.scrollTop <= 0 && e.touches.length === 1) { st.active = true; st.startY = e.touches[0].clientY; }
    };
    const onMove = (e) => {
      if (!st.active) return;
      const dy = e.touches[0].clientY - st.startY;
      if (dy <= 0 || el.scrollTop > 0) { if (st.pulling) { st.pulling = false; setPullY(0); } return; }
      if (!st.pulling && dy < ENGAGE) return;          // ainda é um toque, não um arrasto
      st.pulling = true;
      setPullY(Math.min(MAX, (dy - ENGAGE) * 0.5));
      if (e.cancelable) e.preventDefault();             // só após confirmar o arrasto
    };
    const onEnd = () => { if (st.pulling && pullYRef.current >= THRESH && refreshRef.current) refreshRef.current(); st.active = false; st.pulling = false; setPullY(0); };
    el.addEventListener("touchstart", onStart, { passive: true });
    el.addEventListener("touchmove", onMove, { passive: false });
    el.addEventListener("touchend", onEnd, { passive: true });
    el.addEventListener("touchcancel", onEnd, { passive: true });
    return () => { el.removeEventListener("touchstart", onStart); el.removeEventListener("touchmove", onMove); el.removeEventListener("touchend", onEnd); el.removeEventListener("touchcancel", onEnd); };
  }, []);

  // Notificações locais: detecta movimentos relevantes da carteira.
  const notifRef = useRef({});
  useEffect(() => {
    const n = data && data.config && data.config.notif;
    if (!n || !n.enabled) return;
    for (const p of (data.positions || [])) {
      const q = quotes[p.t];
      if (!q || q.price == null) continue;
      const st = notifRef.current[p.t] || (notifRef.current[p.t] = { stopArmed: true, alvoArmed: true, varKey: "" });
      if (n.stop !== false && p.stop != null) {
        if (q.price <= p.stop && st.stopArmed) { notify.notifyIfEnabled(n, "stop", "Stop acionado · " + p.t, p.t + " a R$ " + price(q.price) + " atingiu o stop de R$ " + price(p.stop) + "."); st.stopArmed = false; }
        else if (q.price > p.stop) st.stopArmed = true;
      }
      if (n.alvo !== false && p.alvo != null) {
        if (q.price >= p.alvo && st.alvoArmed) { notify.notifyIfEnabled(n, "alvo", "Alvo atingido · " + p.t, p.t + " a R$ " + price(q.price) + " alcançou o alvo de R$ " + price(p.alvo) + "."); st.alvoArmed = false; }
        else if (q.price < p.alvo) st.alvoArmed = true;
      }
      if (n.variacao !== false && q.change != null && Math.abs(q.change) >= 5) {
        const key = new Date().toDateString() + (q.change >= 0 ? "+" : "-");
        if (st.varKey !== key) { notify.notifyIfEnabled(n, "variacao", "Movimento forte · " + p.t, p.t + " " + pct(q.change) + " no dia (R$ " + price(q.price) + ")."); st.varKey = key; }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quotes, data]);

  // Tela de abertura: na 1a vez (flag do STORE) mostra login/criar conta; o
  // onboarding anônimo (orçamento/risco) só aparece se escolher "usar sem conta".
<<<<<<< HEAD
  // Debug opcional no device: no console do Safari, antes de recarregar, rode
  // `localStorage.setItem("b3-debug-welcome","1")` (ou `window.__B3_DEBUG_WELCOME=true`)
  // para logar a decisão (onboarded / já mostrado / vai mostrar).
  useEffect(() => {
    if (!data) return;
    // BLOCO 2: o welcome é o PORTÃO DE ENTRADA do app — aparece SEMPRE no boot
    // (uma vez por abertura), independente de config.onboarded e de sessão
    // ativa. Com sessão restaurada, a tela mostra "Conectado como X" + Entrar;
    // sem sessão, login/continuar sem conta. `onboarded` deixa de esconder o
    // welcome e passa a controlar APENAS se o onboarding anônimo (orçamento/
    // risco) roda ao escolher "usar sem conta".
    const onboarded = !!(data.config && data.config.onboarded);
    const willShow = !welcomeShownRef.current;
    let dbg = false;
    try { dbg = (typeof window !== "undefined") && (window.__B3_DEBUG_WELCOME || localStorage.getItem("b3-debug-welcome") === "1"); } catch { /* storage indisponível */ }
    if (dbg) { try { console.log("[welcome]", { bootGate: true, onboarded, hasSavedSession: hasSession(), alreadyShown: welcomeShownRef.current, willShow }); } catch { /* noop */ } }
    if (willShow) {
=======
  useEffect(() => {
    if (data && !(data.config && data.config.onboarded) && !welcomeShownRef.current) {
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      welcomeShownRef.current = true;
      setWelcomeAuthOpen(true);
    }
  }, [data]);

  // Snapshot diário de patrimônio (Fase B1): grava 1x por sessão, após as
  // cotações chegarem (para não subestimar). upsert por dia no store.
  const snapRanRef = useRef(false);
  useEffect(() => {
    if (!data || snapRanRef.current) return;
    const positions = data.positions || [];
    const temCotacoes = positions.length === 0 || positions.some((p) => quotes[p.t] && quotes[p.t].price != null);
    if (positions.length > 0 && !temCotacoes) return; // espera as cotações
    snapRanRef.current = true;
    const ymd = new Date().toISOString().slice(0, 10);
<<<<<<< HEAD
    const m = portfolioMetrics(positions, quotes, data.cash);
    store.putSnapshot({ data: ymd, patrimonio: m.patr, caixa: m.cash, posicoesValor: m.posVal })
=======
    const posVal = positions.reduce((s, p) => s + p.qty * ((quotes[p.t] || {}).price || 0), 0);
    const caixa = data.cash || 0;
    store.putSnapshot({ data: ymd, patrimonio: caixa + posVal, caixa, posicoesValor: posVal })
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
      .then((s) => s && setData(s))
      .catch(() => { /* offline-first: silencioso */ });
  }, [data, quotes]);
  const streakRanRef = useRef(false);
  useEffect(() => {
    if (!data || !data.config || streakRanRef.current) return;
    streakRanRef.current = true;
    const ymd = (d) => d.toISOString().slice(0, 10);
    const st = data.config.streak || { days: 0, last: "" };
    const today = ymd(new Date());
    if (st.last === today) return; // já contou hoje
    const y = new Date(); y.setDate(y.getDate() - 1);
    const next = st.last === ymd(y) ? (st.days || 0) + 1 : 1;
    const ns = { days: next, last: today };
    setData((d) => (d ? { ...d, config: { ...d.config, streak: ns } } : d));
    store.putConfig({ streak: ns }).catch(() => { /* silencioso */ });
  }, [data]);

  const ctx = {
    data, quotes, analysis, expanded, analysisModel, setAnalysisModel, A, quotesAt, quotesLoading, test, keyDraft, setKeyDraft,
    catalogSel, setCatalogSel, buyModal, setBuyModal, cycleBusy, addState, setAddState,
    themePref, themeKey, aboutOpen,
    stopAlvo, stopAlvoFor,
    goMercado: () => setTab("mercado"),
    openWelcome: () => setWelcomeOpen(true),
<<<<<<< HEAD
    openWelcomeAuth: () => { welcomeShownRef.current = true; setWelcomeAuthOpen(true); },
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    openStopAlvo: (t) => { setStopAlvoFor(t); A.runStopAlvoFor(t); }, // FASE 3: abre popup do ativo e analisa só ele
    markOnboarded: async () => {
      setData((d) => (d ? { ...d, config: { ...d.config, onboarded: true } } : d));
      try { await store.putConfig({ onboarded: true }); } catch { /* silencioso */ }
    },
    // FASE 2 — conta opcional. Handlers guardados; erros sobem para o AuthModal.
    authUser,
    openAuth: () => setAuthOpen(true),
    login: async ({ email, password }) => {
      const r = await auth.login({ email, password });
      if (r && r.user) setAuthUser(r.user);
      if (r && r.state) setData(r.state); else await loadState();
      flash("Conectado.");
      return r;
    },
    register: async ({ email, password, name }) => {
      const r = await auth.register({ email, password, name });
      if (r && r.user) setAuthUser(r.user);
      if (r && r.state) setData(r.state); else await loadState();
      flash("Conta criada.");
      return r;
    },
<<<<<<< HEAD
    // FASE 2 — login social (Apple/Google). A UI está pronta; o token nativo é
    // obtido pelos plugins Capacitor quando configurados. O servidor já valida.
    oauth: async ({ provider, idToken }) => {
      const r = await auth.oauth({ provider, idToken });
      if (r && r.user) setAuthUser(r.user);
      if (r && r.state) setData(r.state); else await loadState();
      flash("Conectado.");
      return r;
    },
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    logout: async () => {
      await auth.logout();
      setAuthUser(null);
      await loadState();
      flash("Você saiu da conta.");
    },
    deleteAccount: async () => {
      await auth.deleteAccount();
      setAuthUser(null);
      await loadState();
      flash("Conta excluída.");
    },
  };

  // chips do topo
  const { patr, dia } = useMemo(() => {
    if (!data) return { patr: null, dia: 0 };
<<<<<<< HEAD
    const m = portfolioMetrics(data.positions, quotes, data.cash);
    return { patr: m.patr, dia: m.dayVal };
=======
    const posVal = (data.positions || []).reduce((s, p) => s + p.qty * ((quotes[p.t] && quotes[p.t].price) || 0), 0);
    const dayVal = (data.positions || []).reduce((s, p) => { const q = quotes[p.t] || {}; return s + p.qty * (q.price || 0) * ((q.change || 0) / 100); }, 0);
    return { patr: (data.cash || 0) + posVal, dia: dayVal };
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
  }, [data, quotes]);

  const tickerItems = useMemo(() => {
    if (!data) return [];
    return (data.watchlist || []).map((t) => { const q = quotes[t] || {}; return { t, priceStr: price(q.price), chStr: pct(q.change), color: (q.change || 0) >= 0 ? T.positive : T.negative, arrow: (q.change || 0) >= 0 ? "▲" : "▼" }; });
  }, [data, quotes]);

  const shell = {
    className: "b3 b3-shell b3-theme-" + themeKey,
    style: { boxSizing: "border-box", background: T.bgBase, color: T.textPrimary, fontFamily: SANS, display: "flex", flexDirection: "column", WebkitFontSmoothing: "antialiased", paddingTop: "env(safe-area-inset-top)", overflow: "hidden" },
  };
  const firstName = ((data && data.config && data.config.userName) || "").trim().split(/\s+/)[0] || "";

  if (loadErr) {
    return (
      <div {...shell}>
        <GlobalStyle />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
          <div style={{ ...card, padding: "22px", maxWidth: "420px", textAlign: "center" }}>
            <div style={{ fontSize: "16px", fontWeight: 700 }}>Não consegui falar com o servidor</div>
            <p style={{ color: T.textMuted, fontSize: "13px", lineHeight: 1.5, margin: "8px 0 14px" }}>Verifique se o backend está rodando (porta 8787). Detalhe: {loadErr}</p>
            <button onClick={loadState} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Tentar de novo</button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div {...shell}>
        <GlobalStyle />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", color: T.textMuted }}>
          <Spinner /> Carregando…
        </div>
      </div>
    );
  }

  return (
    <ThemeCtx.Provider value={themeKey}>
    <div {...shell}>
      <GlobalStyle />
<<<<<<< HEAD
      <Ticker items={tickerItems} live={Object.keys(quotes).length > 0} />
      <Topbar patr={patr} dia={dia} caixa={data.cash} name={firstName} />
=======
      <Topbar patr={patr} dia={dia} caixa={data.cash} name={firstName} live={Object.keys(quotes).length > 0} />
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026

      <main ref={mainRef} style={{ position: "relative", flex: 1, minHeight: 0, overflowY: "auto", WebkitOverflowScrolling: "touch" }}>
        {pullY > 0 && (
          <div style={{ position: "absolute", top: "8px", left: "50%", transform: "translateX(-50%)", zIndex: 5, opacity: Math.min(1, pullY / 70), color: T.accent, fontSize: "12px", fontWeight: 700, display: "flex", alignItems: "center", gap: "7px", pointerEvents: "none" }}>
            <span className={pullY >= 70 ? "spin" : undefined} style={{ display: "inline-block" }}>↻</span>
            {pullY >= 70 ? "Solte para atualizar" : "Puxe para atualizar"}
          </div>
        )}
<<<<<<< HEAD
        <div style={{ maxWidth: "1060px", margin: "0 auto", padding: "24px 18px 34px", transform: pullY ? `translateY(${pullY}px)` : undefined, transition: pullY ? "none" : "transform .2s ease" }}>
          {tab === "evolucao" && <EvolucaoScreen ctx={ctx} />}
          {tab === "mercado" && <MercadoScreen ctx={ctx} />}
          {tab === "radar" && <RadarScreen ctx={ctx} />}
=======
        <div style={{ maxWidth: "1060px", margin: "0 auto", padding: "14px 14px 26px", transform: pullY ? `translateY(${pullY}px)` : undefined, transition: pullY ? "none" : "transform .2s ease" }}>
          {tab === "evolucao" && <EvolucaoScreen ctx={ctx} />}
          {tab === "mercado" && <MercadoScreen ctx={ctx} />}
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          {tab === "opcoes" && <OptionsScreen ctx={ctx} />}
          {tab === "carteira" && (carteiraView === "historico"
            ? (<><BackHeader title="Histórico de operações" onBack={() => setCarteiraView("main")} /><HistoricoScreen ctx={ctx} /></>)
            : (<><CapitalCurve ctx={ctx} /><CarteiraScreen ctx={ctx} /><div style={{ marginTop: "14px" }}><button onClick={() => setCarteiraView("historico")} style={{ width: "100%", minHeight: "48px", padding: "13px", borderRadius: "13px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}><span>Ver histórico de operações</span><span aria-hidden style={{ color: T.textFaint }}>›</span></button></div></>))}
          {tab === "perfil" && (perfilView === "config"
            ? (<><BackHeader title="Conta & preferências" onBack={() => setPerfilView("hub")} /><ConfigScreen ctx={ctx} /></>)
            : perfilView === "agente"
              ? (<><BackHeader title="Agente autônomo" onBack={() => setPerfilView("hub")} /><AgenteScreen ctx={ctx} /></>)
              : <PerfilHub ctx={ctx} onOpen={setPerfilView} />)}
        </div>
      </main>

      <BottomNav tab={tab} setTab={navigate} />

      {catalogOpen && <CatalogModal ctx={ctx} />}
      {buyModal && <BuyModal ctx={ctx} />}
      {techFor && (
        <TechnicalModal
          ticker={techFor}
          name={(data.catalog.find((c) => c.t === techFor) || {}).n}
          quote={quotes[techFor]}
          position={data.positions.find((p) => p.t === techFor)}
<<<<<<< HEAD
          period={(data.config && data.config.candlePeriod) || "1y"}
=======
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
          onClose={A.closeTech}
        />
      )}
      {aboutOpen && <AboutModal onClose={A.closeAbout} />}
      {authOpen && <AuthModal ctx={ctx} onClose={() => setAuthOpen(false)} />}
      {stopAlvoFor && <StopAlvoModal ctx={ctx} />}
      {welcomeAuthOpen && (
        <WelcomeAuthScreen
          ctx={ctx}
          onAuthed={() => { setWelcomeAuthOpen(false); ctx.markOnboarded(); }}
<<<<<<< HEAD
          onSkip={() => {
            // BLOCO 2 (boot gate): "usar sem conta" só roda o onboarding
            // (orçamento/risco) para quem NUNCA concluiu; veterano entra direto.
            setWelcomeAuthOpen(false);
            if (!(data.config && data.config.onboarded)) setWelcomeOpen(true);
          }}
=======
          onSkip={() => { setWelcomeAuthOpen(false); setWelcomeOpen(true); }}
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
        />
      )}
      {welcomeOpen && (
        <OnboardingModal
          name={firstName}
          budget={data.config && data.config.initialBudget}
          risco={data.profile && data.profile.risco}
          onComplete={({ name, budget, risco }) => {
            if (name) A.saveName(name);
            if (budget) A.saveBudget(budget);
            if (risco) A.saveProfile({ risco });
            setWelcomeOpen(false);
            ctx.markOnboarded();
          }}
        />
      )}

      {toast && (
        <div style={{ position: "fixed", left: "50%", bottom: "92px", transform: "translateX(-50%)", zIndex: 60, background: T.bgToast, border: `1px solid ${T.borderToast}`, color: "#fff", padding: "11px 17px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, boxShadow: "0 10px 34px rgba(0,0,0,0.55)", maxWidth: "90vw", textAlign: "center" }}>
          {toast}
        </div>
      )}
    </div>
    </ThemeCtx.Provider>
  );
}
