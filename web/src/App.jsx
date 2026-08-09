import { useState, useEffect, useRef, useCallback, useMemo, createContext, useContext } from "react";
import { store, isNative, auth } from "./persistence.js";
import { hasSession } from "./sync.js"; // BLOCO 2: welcome exibe estado da sessão salva
import { defaultLlmPrompts } from "./catalog.js";
import { testServer, describeRuntimeConfig, getApiBase } from "./api.js";
import { createChart, ColorType, CrosshairMode, LineStyle } from "lightweight-charts";
import { sampleTechnicals } from "./demo.js";
import { DISCLAIMERS, TERMO_OPERADOR_VERSAO } from "./disclaimers.js";
import { copyFor } from "./copy.js";
import { BUILD_ID } from "./version.js";
// carimbo no console: prova de qual build está rodando (device/web)
try { console.log("[b3] build", BUILD_ID); } catch { /* noop */ }
import { canAddTicker, canAnalyze } from "./plan.js";
import { portfolioMetrics, dayReturnPct, equityCurve, markPrice, sizingPlano } from "./finance.js";
import * as notify from "./notify.js";
import Boris from "./pet/Boris.jsx";
import BorisChat from "./pet/BorisChat.jsx";
import BorisIntro from "./pet/BorisIntro.jsx";
import { falarTexto, calarVoz } from "./pet/vozBoris.js";

/* =============================================================================
   Boris+ — simulador EDUCACIONAL de paper trading da B3.
   Identidade "mesa de operações": fundo quase-preto, acento índigo (IA), números mono.
   Todo o estado é persistido no backend (sobrevive a reinício). A análise
   técnica é feita PELA LLM configurada, sob demanda, por ativo.
   Dinheiro simulado. Nada aqui é recomendação de investimento.
============================================================================= */

// Identidade "mesa de operações" em dois esquemas. DARK = mesa noturna;
// LIGHT = mesma identidade adaptada para leitura confortável (cores semânticas,
// contraste adequado — boas práticas iOS). DOM usa var(--x); gráficos (canvas/
// SVG) usam a paleta REAL via ThemeCtx, pois var() não resolve em canvas.
// Brand Book v2 (2026-08-08) — cores de MARCA. Não são tokens de tema nem de
// modo: o âmbar é do Bóris (logo, ícone, mascote) e o verde/rosa são o SINAL
// universal de compra/venda. "Não muda com tema ou modo", diz o Brand Book —
// por isso ficam fora de PALETTE/MODE_OPERADOR, que são justamente os dois
// eixos que mudam.
const BRAND = {
  amber: "#f2a93b", amberDark: "#c9791b",
  green: "#34d399", // compra
  red: "#f26d6d",   // venda
};
// Brand Book v2 formaliza DOIS EIXOS INDEPENDENTES:
//   1. TEMA (claro/escuro, segue o sistema operacional) — muda a base neutra.
//   2. MODO DE USO (Estudo/Operador) — muda a cor de ACENTO (MODE_* abaixo).
// A Fase 3 tinha colapsado parte disso: o Estudo usava o âmbar da marca como
// acento, então "cor de marca" e "cor de estado da UI" eram a mesma coisa. v2
// separa: o acento de modo substitui o âmbar em CTAs e destaques; o âmbar fica
// reservado à marca em qualquer tela.
//
// QUAIS acentos, porém, é decisão do Alex, e ela mudou em 08/08/2026 (paleta
// entregue hex a hex): Estudo = AZUL-ESVERDEADO (#2fa8a0 escuro / #1f7d76
// claro), Operador = DOURADO (#d4af37 / #8a6c1c). Antes eram o azul frio e o
// verde que o v2 sugeria. Ganho colateral: o verde deixou de acumular dois
// papéis — era acento do Operador E sinal de compra ao mesmo tempo, então um
// botão primário verde e um "+R$" verde diziam coisas diferentes com a mesma
// cor. Agora BRAND.green/BRAND.red só significam compra/venda, em modo nenhum
// eles são acento.
const PALETTE = {
  // Base = modo ESTUDO. O Operador entra como override em MODE_OPERADOR.
  // Neutros do dark e do light vêm literais do bloco "Design tokens" de v2:
  // --bg/--bg-2/--panel/--line/--ink/--muted/--muted-2. O light era a
  // pendência aberta da Fase 3 ("Brand Book só especifica dark") — v2 fecha.
  dark: {
    bgBase: "#10121a", bgPanel: "#161927", bgCard: "#1b1f2e", bgToast: "#1b1f2e",
    borderSubtle: "#2c3245", borderFaint: "#20242f", borderDashed: "#3a4258", borderToast: "#3a4258",
    textPrimary: "#eef1f8", textSecondary: "#c9d1e6", textMuted: "#9aa3bd", textDim: "#8890a8",
    textFaint: "#6f7797", textBright: "#f6f8fc",
    accent: "#2fa8a0", accentSoft: "#5cc4bd", positive: BRAND.green, negative: BRAND.red,
    knob: "#20242f", navDotIdle: "#2c3245", confirmOkText: "#04251a",
    accentTint: "rgba(47,168,160,0.14)", accentTintHi: "rgba(47,168,160,0.26)", accentTint10: "rgba(47,168,160,0.10)",
    positiveTint: "rgba(52,211,153,0.12)", positiveTint10: "rgba(52,211,153,0.10)",
    negativeTint: "rgba(242,109,109,0.12)", negativeTint10: "rgba(242,109,109,0.10)",
    scrim: "rgba(5,6,10,0.68)",
    chartGrid: "rgba(255,255,255,0.04)", chartBorder: "rgba(255,255,255,0.08)", chartAxis: "#6f7797", lineSubtle: "rgba(255,255,255,0.18)", onAccent: "#04231f",
    warn: "#fbbf24", // qa/34: âmbar de aviso (diário/logs) — antes hex solto fora do token system
  },
  light: {
    // Neutros literais de v2. Antes o painel e o card eram os dois #ffffff —
    // v2 separa --bg-2 (#eef0f7) de --panel (#ffffff), então o painel volta a
    // ter um degrau de profundidade sobre o card, como no dark.
    bgBase: "#f7f8fc", bgPanel: "#eef0f7", bgCard: "#ffffff", bgToast: "#222936",
    borderSubtle: "#e2e5f0", borderFaint: "#edeff5", borderDashed: "#d3d8e6", borderToast: "#39414f",
    textPrimary: "#10121a", textSecondary: "#2d3444", textMuted: "#5b6178", textDim: "#6b7288",
    textFaint: "#7a8099", textBright: "#080a12",
    // Acento do Estudo no claro: #2f6fe0 é o hex literal de v2 (AA 4,70 sobre
    // #ffffff). positive/negative NÃO são o verde/rosa crus da marca aqui: em
    // fundo claro eles medem 1,92:1 e 2,92:1, e neste app essas duas cores são
    // TEXTO em 72 lugares (valores de P&L), não só badge. Estes são os tons
    // mais próximos da marca que passam AA — mesma matiz, luminosidade menor.
    // Ver o bloco "sinal universal" no relatório da entrega.
    accent: "#1f7d76", accentSoft: "#166861", positive: "#1c825d", negative: "#c6464c",
    knob: "#dfe3ee", navDotIdle: "#c4cad8", confirmOkText: "#ffffff",
    accentTint: "rgba(31,125,118,0.12)", accentTintHi: "rgba(31,125,118,0.20)", accentTint10: "rgba(31,125,118,0.10)",
    positiveTint: "rgba(28,130,93,0.12)", positiveTint10: "rgba(28,130,93,0.10)",
    negativeTint: "rgba(198,70,76,0.12)", negativeTint10: "rgba(198,70,76,0.10)",
    scrim: "rgba(15,20,28,0.45)",
    chartGrid: "rgba(0,0,0,0.05)", chartBorder: "rgba(0,0,0,0.10)", chartAxis: "#8a90a0", lineSubtle: "rgba(0,0,0,0.16)", onAccent: "#ffffff",
    warn: "#a16207", // qa/34: âmbar de aviso legível sobre fundo claro
  },
};
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
// T mantém as MESMAS chaves, mas aponta para var(--x) — nenhum uso T.x muda.
const T = Object.fromEntries(Object.keys(PALETTE.dark).map((k) => [k, `var(${VARKEY(k)})`]));
const themeVarBlock = (name) => Object.entries(PALETTE[name]).map(([k, v]) => `${VARKEY(k)}:${v}`).join(";");
// FASE 8B (B2) — identidade do MODO OPERADOR: verde-mercado sobre grafite mais
// frio. Como TODA a UI lê var(--x), o modo é um OVERRIDE de variáveis por cima
// do tema (dark/light) — nenhum uso de T.x muda; a troca anima via transition.
// Valores IGUAIS ao mock aprovado (qa/mocks/dois-apps-em-um.html): fundo
// grafite frio, cards #10161a, textos frios, verde #22c55e como acento E
// como positivo, vermelho #ef4444 — identidade impossível de confundir.
const MODE_OPERADOR = {
  // O Operador é o eixo "modo de uso": acento DOURADO (#d4af37 escuro /
  // #8a6c1c claro), independente do tema — paleta entregue pelo Alex em
  // 08/08/2026, no lugar do verde que o Brand Book v2 sugeria. A leitura é
  // direta: dourado = mesa/dinheiro no Operador, azul-esverdeado = estudo.
  // Além de separar melhor os dois modos (matizes opostas, não dois tons da
  // mesma família), tira do verde o papel duplo de acento E sinal de compra.
  // A diferenciação de leiaute continua: fundo/cartão/borda seguem mais frios
  // que os do Estudo.
  dark: {
    bgBase: "#0a0c12", bgPanel: "#10131c", bgCard: "#141926", bgToast: "#141926",
    borderSubtle: "#242c40", borderFaint: "#1a2030", borderDashed: "#323c54", borderToast: "#323c54",
    textMuted: "#93a3c0", textDim: "#8492ac", textFaint: "#5b6890",
    accent: "#d4af37", accentSoft: "#e6c766",
    positive: BRAND.green, negative: BRAND.red,
    accentTint: "rgba(212,175,55,0.14)", accentTintHi: "rgba(212,175,55,0.26)", accentTint10: "rgba(212,175,55,0.10)",
    positiveTint: "rgba(52,211,153,0.13)", positiveTint10: "rgba(52,211,153,0.10)",
    negativeTint: "rgba(242,109,109,0.13)", negativeTint10: "rgba(242,109,109,0.10)",
    onAccent: "#241b06", knob: "#1a2030", navDotIdle: "#242c40", chartAxis: "#5b6890",
  },
  light: {
    // qa/32: faltavam bgBase/bgPanel/borders/text — o override em LIGHT só
    // trocava acento/positivo/negativo, então Estudo × Operador ficavam com
    // o MESMO chrome (fundo/cartão/bordas/texto) em tema claro. Mesma lógica
    // relativa do dark (base levemente mais fria/grafite que o Estudo).
    // Base neutra do Operador no claro: mesma lógica relativa do dark (um
    // degrau mais frio/grafite que o Estudo), agora derivada dos neutros de v2.
    bgBase: "#f2f6f4", bgPanel: "#e9efec", bgCard: "#ffffff", bgToast: "#16211c",
    borderSubtle: "#dce5e1", borderFaint: "#e8efec", borderDashed: "#c8d6d0", borderToast: "#24483a",
    textMuted: "#4f5f5a", textDim: "#5c6d67", textFaint: "#7a8a85",
    // O Alex passou #9c7a1f para o dourado no claro; ele mede 4,03:1 sobre
    // #ffffff — reprova AA (4,5) tanto como texto quanto como fundo de CTA com
    // rótulo branco, e o rótulo do botão primário tem 15px em negrito, longe do
    // limiar de "texto grande" que aceitaria 3:1. #8a6c1c é o MESMO dourado
    // (matiz 44° preservada), só um degrau mais escuro, e passa (4,93:1). Foi o
    // único dos quatro acentos que precisou de ajuste — os outros três entraram
    // exatamente como vieram. Mesmo critério aplicado ao positive/negative do
    // tema claro, e medido por test_brand_book_v2_tokens.mjs.
    accent: "#8a6c1c", accentSoft: "#7d621a",
    positive: "#1c825d", negative: "#c6464c",
    accentTint: "rgba(138,108,28,0.12)", accentTintHi: "rgba(138,108,28,0.20)", accentTint10: "rgba(138,108,28,0.10)",
    positiveTint: "rgba(28,130,93,0.12)", positiveTint10: "rgba(28,130,93,0.10)",
    negativeTint: "rgba(198,70,76,0.12)", negativeTint10: "rgba(198,70,76,0.10)",
    onAccent: "#ffffff", knob: "#dce5e1", navDotIdle: "#c8d6d0", chartAxis: "#7a8b85",
  },
};
const modeVarBlock = (name) => Object.entries(MODE_OPERADOR[name]).map(([k, v]) => `${VARKEY(k)}:${v}`).join(";");
const THEME_CSS = `.b3-theme-dark{${themeVarBlock("dark")}} .b3-theme-light{${themeVarBlock("light")}}`
  + ` .b3-mode-operador.b3-theme-dark{${modeVarBlock("dark")}} .b3-mode-operador.b3-theme-light{${modeVarBlock("light")}}`;
// FASE 8B (N1 — fix da identidade parcial): o contexto carrega TEMA + MODO.
// Gráficos/canvas não resolvem var(--x) — liam PALETTE crua e ficavam AZUIS
// no Modo Operador enquanto o resto da UI ficava verde. usePalette agora
// mescla o override do modo: identidade completa em TODAS as superfícies.
const ThemeCtx = createContext({ key: "dark", mode: "estudo" });
const useThemeKey = () => {
  const v = useContext(ThemeCtx);
  return typeof v === "string" ? v : (v && v.key) || "dark";
};
const usePalette = () => {
  const v = useContext(ThemeCtx);
  const key = typeof v === "string" ? v : (v && v.key) || "dark";
  const mode = typeof v === "string" ? "estudo" : (v && v.mode) || "estudo";
  const base = PALETTE[key] || PALETTE.dark;
  return mode === "operador" ? { ...base, ...(MODE_OPERADOR[key] || {}) } : base;
};

// Logo do app: símbolo estático do Brand Book (Fase 3, 2026-08-08) — o rosto
// do Bóris (óculos redondos + tufos de orelha) com o "+" como selo colado à
// armação. Substitui o ícone antigo (candle+ticker-tape da era "BolsIA").
// Usado nos contextos "estáticos" que o Brand Book reserva pro símbolo (não
// a animação): cabeçalho, telas de auth/onboarding — tudo abaixo de ~64px
// onde a coruja animada (Boris.jsx) perderia legibilidade.
function LogoMark({ size = 32, radius }) {
  // Brand Book v2, regra explícita: "nunca recolorir os óculos fora do âmbar
  // da marca". Até a Fase 3 os óculos/bico/selo seguiam o acento do MODO
  // (viravam verde no Operador) — v2 fecha essa porta: o âmbar é identidade de
  // marca, não estado de UI, então o símbolo é idêntico em Estudo e Operador,
  // claro e escuro. Rosto/orelhas seguem no azul-marinho fixo ("pele" do Bóris).
  const r = radius != null ? radius : Math.round(size * 0.26);
  const rx = (r / size) * 64;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden role="img" style={{ display: "block", flex: "none" }}>
      <rect x="0" y="0" width="64" height="64" rx={rx} fill="#161927" />
      {/* tufos de orelha */}
      <path d="M14 16 L22 27 L10 27 Z" fill="#2a3a6b" />
      <path d="M50 16 L42 27 L54 27 Z" fill="#2a3a6b" />
      {/* rosto */}
      <circle cx="32" cy="34" r="26" fill="#2a3a6b" />
      {/* óculos redondos */}
      <circle cx="22" cy="32" r="10" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <circle cx="42" cy="32" r="10" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <path d="M30 32 Q32 29 34 32" fill="none" stroke={BRAND.amber} strokeWidth="3.2" />
      <circle cx="22" cy="32" r="4" fill="#eef1f8" />
      <circle cx="42" cy="32" r="4" fill="#eef1f8" />
      {/* bico */}
      <path d="M32 42 L27.5 49 L36.5 49 Z" fill={BRAND.amber} />
      {/* selo "+" */}
      <circle cx="51" cy="50" r="10" fill="#161927" />
      <circle cx="51" cy="50" r="9" fill={BRAND.amber} />
      <path d="M51 45.5V54.5M46.5 50H55.5" stroke="#161927" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
// BLOCO D — login persistido: lembra APENAS o último e-mail (nunca a senha;
// a senha fica no Chaveiro do iOS via AutoFill + na sessão persistida).
const LAST_EMAIL_KEY = "b3-last-email";
function loadLastEmail() { try { return localStorage.getItem(LAST_EMAIL_KEY) || ""; } catch { return ""; } }
function saveLastEmail(e) { try { const v = String(e || "").trim(); if (v) localStorage.setItem(LAST_EMAIL_KEY, v); } catch { /* ignore */ } }

const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
// Fase 3 (rebranding Boris+, 2026-08-08): corpo do app em Nunito (marca) —
// stack de sistema como fallback se a fonte não carregar (offline no
// WKWebView, por exemplo); mesmo princípio de qualquer outro dado remoto
// deste app, nunca trava por falta de rede.
const SANS = "'Nunito', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif";
// Display: Fredoka 600 — títulos, wordmark, números de destaque (Brand Book).
const DISPLAY = "'Fredoka', " + SANS;
// Boris+: o "+" do wordmark é o acento fixo da marca — âmbar chapado
// (--brand-amber), NUNCA gradiente e NUNCA a cor do modo. Antes (marca
// "BolsIA") o "IA" seguia o acento do modo (`IA_GRAD`, azul→ciano/degradê); o "+" é
// identidade de marca, não estado de UI — fica igual em Estudo e Operador.
const PLUS_STYLE = { color: BRAND.amber };

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
      .b3 button{ font:inherit; color:inherit; cursor:pointer; transition:filter .12s ease, transform .05s ease; user-select:none; -webkit-user-select:none; }
      .b3 button:active:not(:disabled){ transform:translateY(1px); filter:brightness(1.12); }
      .b3 button:disabled{ cursor:default; opacity:.6; }
      /* FASE 8B (UX): sem o flash cinza de toque do iOS; inputs com 16px para
         o Safari NÃO dar zoom automático ao focar (pulo de tela clássico). */
      .b3, .b3 *{ -webkit-tap-highlight-color: transparent; }
      .b3 input,.b3 textarea,.b3 select{ font:inherit; font-size:16px; }
      /* FASE 8B (B2): troca de modo com transição suave — a classe entra por
         ~450ms só durante a troca (não pesa nas interações normais). */
      .b3-mode-switch, .b3-mode-switch *{ transition: background-color .35s ease, color .35s ease, border-color .35s ease, fill .35s ease !important; }
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

// qa/34 (mock v2 §10): affordance ÚNICA de disclaimer POR TELA — o ⓘ ao lado
// do título abre o "Sobre · Aviso legal" (AboutModal, ponto único do texto).
// Substitui a ideia de parágrafo fixo por seção; não remove os avisos de
// contexto que são exigência de conteúdo (ex.: termo do Operador).
const InfoDot = ({ onClick }) => (
  <button onClick={onClick} aria-label="Sobre e aviso legal"
    style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "15px", lineHeight: 1, padding: "4px 5px", flex: "none" }}>ⓘ</button>
);

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
          <div style={{ fontFamily: DISPLAY, fontSize: "21px", fontWeight: 600, marginTop: "12px", letterSpacing: "-0.01em" }}>Boris<span style={PLUS_STYLE}>+</span></div>
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
        // A ponte pode devolver a string do token (contrato antigo) ou o objeto
        // { idToken, name, authorizationCode } — name/code só vêm da Apple no
        // PRIMEIRO consentimento e precisam ser persistidos nessa hora.
        const r = await bridge[provider]();
        const payload = typeof r === "string" ? { idToken: r } : (r || {});
        if (!payload.idToken) throw new Error("Login não devolveu o token de identidade.");
        if (ctx && ctx.oauth) await ctx.oauth({ provider, ...payload });
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
// FASE 8B (N3) — FORMULÁRIO ÚNICO de login/registro. Antes existiam DOIS
// (Welcome e AuthModal) com estados, textos e comportamentos que divergiam.
// Fonte única: social + e-mail/senha + alternância entrar/criar + erro;
// pré-preenche o último e-mail e persiste no sucesso. Quem embala (tela cheia
// ou modal) só fornece o entorno e o onDone.
function AuthForm({ ctx, onDone }) {
  const lastEmail = loadLastEmail();
  const [mode, setMode] = useState(lastEmail ? "login" : "register");
  const [email, setEmail] = useState(lastEmail);
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      if (mode === "register") await ctx.register({ email, password, name });
      else await ctx.login({ email, password });
      saveLastEmail(email); // BLOCO D
      onDone && onDone();
    } catch (e) { setErr((e && e.message) || String(e)); }
    finally { setBusy(false); }
  };
  return (
    <div>
      <SocialAuthButtons ctx={ctx} />
      {mode === "register" && (
        <>
          <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome (opcional)</label>
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={40} placeholder="Seu nome" style={{ ...field, marginBottom: "12px" }} />
        </>
      )}
      <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>E-mail</label>
      <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" name="email" autoComplete="username" autoCapitalize="none" autoCorrect="off" placeholder="voce@exemplo.com" style={{ ...field, marginBottom: "12px" }} />
      <label style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Senha</label>
      <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" name="password" autoComplete={mode === "register" ? "new-password" : "current-password"} placeholder="ao menos 8 caracteres" style={{ ...field, marginBottom: "18px" }} />
      <button disabled={busy || !email || !password} onClick={submit} style={{ width: "100%", minHeight: "48px", padding: "13px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "15px", opacity: (busy || !email || !password) ? 0.6 : 1 }}>
        {busy ? "…" : (mode === "login" ? "Entrar" : "Criar conta")}
      </button>
      <button onClick={() => { setErr(""); setMode(mode === "login" ? "register" : "login"); }} style={{ width: "100%", marginTop: "12px", padding: "6px", background: "transparent", border: "none", color: T.accent, fontWeight: 600, fontSize: "13px" }}>
        {mode === "login" ? "Não tem conta? Criar uma" : "Já tem conta? Entrar"}
      </button>
      {err && <p style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5, margin: "12px 0 0", whiteSpace: "pre-wrap" }}>{err}</p>}
    </div>
  );
}

function AuthModal({ ctx, onClose }) {
  const user = (ctx && ctx.authUser) || null;
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
          <div style={{ fontSize: "17px", fontWeight: 800 }}>{user ? "Sua conta" : "Entrar ou criar conta"}</div>
        </div>
        {children}
        {err && <p style={{ color: T.negative, fontSize: "12.5px", lineHeight: 1.5, margin: "12px 0 0", whiteSpace: "pre-wrap" }}>{err}</p>}
      </div>
    </div>
  );

  if (user) {
    // FASE 8B (P1): quem entra com a Apple usando "Ocultar e-mail" recebe um
    // endereço @privaterelay.appleid.com — é o e-mail REAL da conta (os nossos
    // avisos chegam nele via relay da Apple), mas confunde na tela. Preferimos
    // o NOME e explicamos o relay + como compartilhar o e-mail verdadeiro.
    const isRelay = /@privaterelay\.appleid\.com$/i.test(user.email || "");
    // qa/32: "e-mail oculto" como TÍTULO soa como erro/problema — a explicação
    // do relay já vem detalhada logo abaixo (isRelay). Título neutro aqui.
    const displayId = (user.name || "").trim() || (isRelay ? "Sua conta Apple" : (user.email || user.id));
    return wrap(
      <div>
        <div style={{ fontSize: "13px", color: T.textMuted, marginBottom: "4px" }}>Conectado como</div>
        <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: (isRelay || ((user.name || "").trim() && user.email)) ? "4px" : "18px", wordBreak: "break-all" }}>{displayId}</div>
        {(user.name || "").trim() && user.email && !isRelay && (
          <div style={{ fontSize: "11.5px", color: T.textFaint, marginBottom: "14px", wordBreak: "break-all" }}>{user.email}</div>
        )}
        {isRelay && (
          <div style={{ fontSize: "11px", color: T.textFaint, lineHeight: 1.55, marginBottom: "14px" }}>
            Você entrou com a Apple usando <b>Ocultar e-mail</b> — o endereço {user.email} é um retransmissor privado da Apple (nossas mensagens chegam no seu e-mail real por ele). Para compartilhar o e-mail verdadeiro: Ajustes → seu nome → Início de Sessão e Segurança → Iniciar sessão com a Apple → Boris+ → parar de usar → e entre de novo escolhendo "Compartilhar meu e-mail".
          </div>
        )}
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

  // FASE 8B (N3): sem conta, o modal usa o MESMO formulário do Welcome.
  return wrap(
    <div>
      <p style={{ color: T.textMuted, fontSize: "12.5px", lineHeight: 1.6, margin: "0 0 16px" }}>
        Criar conta é <b>opcional</b> — o app funciona sem login. Com conta, sua carteira fica salva e acompanha você entre aparelhos.
      </p>
      <AuthForm ctx={ctx} onDone={onClose} />
    </div>
  );
}

/* -------------------------------- Chrome --------------------------------- */
// Tela de ABERTURA (welcome = login). Mantém o local-first (decisão A): o link
// "usar sem conta" no rodapé leva ao onboarding anônimo (orçamento/risco).
// Self-contained e undefined-safe — não acessa campos de `data`.
function WelcomeAuthScreen({ ctx, onAuthed, onSkip }) {
  // BLOCO D: quem já usou entra pré-preenchido — e-mail lembrado + modo login.
  // BLOCO 2: boot gate. Se a sessão salva já foi restaurada (auth.me), mostra
  // "Conectado como X" + Entrar. Se há token salvo mas o /auth/me ainda não
  // respondeu, mostra o formulário com um aviso de restauração — quando a
  // resposta chegar, esta tela troca sozinha para o estado conectado.
  // FASE 8B (N3): o formulário em si agora é o AuthForm ÚNICO (mesmo do modal).
  const user = ctx.authUser;
  const restoring = !user && hasSession();
  // FASE 8B (P1): e-mail de relay da Apple não é rótulo de gente — usa o nome
  const userLabel = user ? ((user.name || "").trim() || (/@privaterelay\.appleid\.com$/i.test(user.email || "") ? "Sua conta Apple" : user.email) || "sua conta") : "";
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 85, background: T.bgBase, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px", overflowY: "auto" }}>
      <div style={{ width: "100%", maxWidth: "420px", ...card, padding: "26px 24px" }}>
        {/* Decisão do Alex (2026-08-08): esta é a primeira tela que alguém vê,
            então a marca ocupa o espaço que merece. O empilhamento antigo
            (símbolo 56px em cima, nome em 21px embaixo, tudo centralizado)
            gastava altura e entregava um nome menor que o texto do formulário.
            Agora é uma LINHA: o Bóris inteiro e ANIMADO à esquerda, o nome em
            40px à direita, com a tagline ancorada sob ele. A coruja em 88px de
            largura (117 de altura, proporção do Brand Book) equilibra o peso do
            nome sem empurrar o formulário para fora da dobra. */}
        <div style={{ marginBottom: "18px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "14px" }}>
            <div aria-hidden style={{ flex: "none", lineHeight: 0 }}><Boris size={88} /></div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: DISPLAY, fontSize: "40px", fontWeight: 600, lineHeight: 1.0, letterSpacing: "-0.02em" }}>Boris<span style={PLUS_STYLE}>+</span></div>
              {/* Quebra na fronteira das duas frases: em qualquer largura o
                  corte cai onde a tagline já é escrita, nunca no meio de
                  "Sem pôr dinheiro". */}
              <div style={{ fontSize: "13px", color: T.accent, fontWeight: 600, marginTop: "7px", lineHeight: 1.35 }}>Aprenda a operar.<br />Sem pôr dinheiro em risco.</div>
            </div>
          </div>
          <p style={{ color: T.textMuted, fontSize: "12.5px", lineHeight: 1.6, margin: "16px 0 0", textAlign: "center" }}>
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
            <AuthForm ctx={ctx} onDone={onAuthed} />
            <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: `1px solid ${T.borderSubtle}`, textAlign: "center" }}>
              <button onClick={() => onSkip && onSkip()} style={{ background: "transparent", border: "none", color: T.textMuted, fontSize: "12.5px", fontWeight: 600, textDecoration: "underline", padding: "4px" }}>
                Usar sem conta
              </button>
            </div>
          </>
        )}
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

function Topbar({ patr, dia, caixa, name, onProfile, modeChip }) {
  const up = dia >= 0;
  const base = patr - dia;
  const pct = base > 0 ? (dia / base) * 100 : 0;
  const pctStr = (pct >= 0 ? "+" : "") + pct.toFixed(1).replace(".", ",") + "%";
  const arrow = up ? "▲" : "▼";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 16px", borderBottom: `1px solid ${T.borderSubtle}`, background: T.bgPanel, flex: "none" }}>
      {/* Decisão do Alex (2026-08-08): o cabeçalho fica SEM ícone — nem o Bóris
          nem o símbolo estático. Quem carrega a marca aqui é o nome, e é ele
          que cresce: 18px → 27px. A troca é direta, os ~42px que o ícone e o
          gap ocupavam viram espaço do wordmark, e a barra não fica mais alta.
          O Bóris segue presente onde tem função: animado no FAB (o assistente)
          e grande na tela de login. */}
      <div style={{ display: "flex", alignItems: "center", gap: "11px", marginRight: "auto", minWidth: 0 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "7px", minWidth: 0 }}>
            <div style={{ fontFamily: DISPLAY, fontWeight: 600, fontSize: "27px", lineHeight: 1.0, letterSpacing: "-0.015em" }}>Boris<span style={PLUS_STYLE}>+</span></div>
          </div>
          {/* qa/mock v2 (racionalização): o badge de modo SAIU de ao lado do
              wordmark (apertado contra o patrimônio) e virou uma LINHA de modo
              própria sob a marca — ponto (na cor do modo) + rótulo + nome.
              Simétrico nos dois modos (Estudo e Operador têm chipModo). */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px", minWidth: 0 }}>
            {modeChip && (<>
              <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: T.accent, flex: "none", boxShadow: `0 0 0 3px ${T.accentTint}` }} />
              <span style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.07em", color: T.accent, whiteSpace: "nowrap", flex: "none" }}>{modeChip}</span>
            </>)}
            {name ? (<>
              {modeChip && <span style={{ color: T.textFaint, fontSize: "11px", flex: "none" }}>·</span>}
              <span style={{ fontSize: "11px", color: T.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</span>
            </>) : null}
          </div>
        </div>
      </div>
      <div style={{ textAlign: "right", flex: "none", fontFamily: MONO }}>
        <div style={{ fontWeight: 700, fontSize: "18px", lineHeight: 1.05, color: T.textPrimary }}>{money(patr)}</div>
        <div style={{ fontSize: "11px", marginTop: "3px", fontWeight: 700, color: up ? T.positive : T.negative, whiteSpace: "nowrap" }}>{arrow} {moneySigned(dia)} ({pctStr})</div>
        <div style={{ fontSize: "10.5px", marginTop: "2px", color: T.textFaint, whiteSpace: "nowrap" }}>caixa {money(caixa)}</div>
      </div>
      {/* M1: Perfil mora no avatar (Conta, Config, IA & chaves, avisos) */}
      <button onClick={onProfile} aria-label="Abrir perfil e configurações" style={{ flex: "none", width: "40px", height: "40px", borderRadius: "50%", border: `1px solid ${T.borderSubtle}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "15px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        {(name || "").trim() ? (name.trim()[0] || "").toUpperCase() : <NavIcon id="perfil" active />}
      </button>
    </div>
  );
}

function NavIcon({ id, active }) {
  const c = active ? T.accent : T.textMuted;
  const p = { fill: "none", stroke: c, strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    evolucao: <><polyline points="3 17 9 11 13 15 21 7" {...p} /><polyline points="16 7 21 7 21 12" {...p} /></>,
    mercado: <><line x1="6" y1="20" x2="6" y2="13" {...p} /><line x1="12" y1="20" x2="12" y2="5" {...p} /><line x1="18" y1="20" x2="18" y2="10" {...p} /></>,
    radar: <><circle cx="12" cy="12" r="8.5" {...p} /><circle cx="12" cy="12" r="4.2" {...p} /><line x1="12" y1="12" x2="18" y2="6" {...p} /><circle cx="12" cy="12" r="1.2" fill={c} stroke="none" /></>,
    carteira: <><rect x="3" y="6" width="18" height="13" rx="2.5" {...p} /><path d="M3 9h13a2 2 0 0 1 2 2v0" {...p} /><circle cx="17" cy="13" r="1.3" fill={c} stroke="none" /></>,
    opcoes: <><path d="M4 17c4-9 12-9 16 0" {...p} /><path d="M6 12h12" {...p} /><circle cx="8" cy="12" r="1.3" fill={c} stroke="none" /><circle cx="16" cy="12" r="1.3" fill={c} stroke="none" /></>,
    perfil: <><circle cx="12" cy="8.5" r="3.4" {...p} /><path d="M5.5 19a6.5 6.5 0 0 1 13 0" {...p} /></>,
    // M1 (UX aprovada): Automatizar — chip/robô do agente autônomo
    agente: <><rect x="5" y="7" width="14" height="11" rx="2.5" {...p} /><line x1="12" y1="4" x2="12" y2="7" {...p} /><circle cx="12" cy="3.4" r="1" fill={c} stroke="none" /><circle cx="9.2" cy="11.5" r="1.1" fill={c} stroke="none" /><circle cx="14.8" cy="11.5" r="1.1" fill={c} stroke="none" /><path d="M9.5 15h5" {...p} /></>,
  };
  return <svg width="23" height="23" viewBox="0 0 24 24" aria-hidden>{paths[id]}</svg>;
}

function BottomNav({ tab, setTab, cp }) {
  // FASE 2 (2.1 — Revisão Total): funil canônico Acompanhar → Radar →
  // Watchlist → Portfólio → Operador IA. Ids internos preservados.
  // FASE 8B (B1): rótulos das abas de mercado/carteira vêm da fraseologia do
  // modo (Watchlist/Portfólio × Monitoramento/Posições) — a navegação também
  // fala a língua do modo.
  // qa/34: a aba do Radar também fala a língua do modo ("Radar" × "Mesa") —
  // antes ficava fixa em "Radar" enquanto a tela se chamava "Mesa de oportunidades".
  const defs = [["evolucao", "Acompanhar"], ["radar", (cp && cp.tabRadar) || "Radar"],
    ["mercado", (cp && cp.tituloWatchlist) || "Watchlist"],
    ["carteira", (cp && cp.tituloPortfolio) || "Portfólio"],
    ["agente", "Operador IA"]];
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
// ============================================================================
// FASE 2 — helpers do funil (puros; fonte: history dos stores + scan do STU)
// ============================================================================

// 2.3: tier de oportunidade pela confluência do STU (tokens próprios — verde/
// vermelho seguem reservados a sinal de mercado; aqui o tier é o emoji).
function tierOf(conf) {
  const c = Number(conf) || 0;
  if (c >= 75) return ["🟢", "Forte"];
  if (c >= 50) return ["🟡", "Moderada"];
  if (c > 0) return ["⚪", "Neutra"];
  return ["🔴", "Fraca"];
}

// 2.3 (a): resumo das operações simuladas de UM ativo — "N ops · ±X% acum."
// (% = PnL realizado sobre o custo total comprado; fonte única: history).
function opsSummary(history, t) {
  const ops = (history || []).filter((h) => h && h.t === t);
  const custo = ops.filter((h) => h.type === "COMPRA").reduce((sum, h) => sum + (h.qty || 0) * (h.price || 0), 0);
  const pnl = ops.filter((h) => h.type === "VENDA").reduce((sum, h) => sum + (h.pnl || 0), 0);
  const pct = custo > 0 ? (pnl / custo) * 100 : 0;
  return { ops, n: ops.length, pnl, pct };
}

// 2.4: dias desde a abertura — aceita "dd/mm/aaaa hh:mm" (formato dos stores).
function daysSince(str) {
  if (!str) return null;
  let d = null;
  const m = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(str);
  if (m) d = new Date(+m[3], +m[2] - 1, +m[1]);
  else { const p = new Date(str); if (!isNaN(p)) d = p; }
  if (!d || isNaN(d)) return null;
  return Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
}

// 2.4: fallback de data de abertura para posições antigas (sem abertaEm):
// a COMPRA mais antiga registrada no histórico do ativo.
function openedAt(history, t, pos) {
  if (pos && pos.abertaEm) return pos.abertaEm;
  const compras = (history || []).filter((h) => h && h.t === t && h.type === "COMPRA");
  return compras.length ? compras[compras.length - 1].date : null;
}

// 2.3 (b): mini-sparkline do preço com marcadores ▲compra/▼venda nas datas das
// operações (candles vêm de /api/technicals — o mesmo STU de tudo).
function OpsSparkline({ candles, ops }) {
  // qa/29 (B2): atributos de apresentação SVG (fill=/stroke=) não resolvem
  // var(--x) de forma confiável neste WebKit — mesma causa-raiz já
  // documentada para PriceChart (linha ~92). Usa usePalette() (hex
  // resolvido, já mesclado com o override do Modo Operador) em vez de T.x.
  const P = usePalette();
  const cs = candles || [];
  const closes = cs.map((c) => c.close);
  if (closes.length < 2) return null;
  const [mn, mx] = extentOf([closes]);
  const W = 280, H = 44;
  const idx = {};
  cs.forEach((c, i) => { if (c && c.date) idx[String(c.date).slice(0, 10)] = i; });
  const marks = [];
  for (const h of ops || []) {
    const m = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(h.date || "");
    if (!m) continue;
    const i = idx[`${m[3]}-${m[2]}-${m[1]}`];
    if (i == null) continue;
    const x = 3 + (i / (closes.length - 1)) * (W - 6);
    const y = (H - 3) - ((closes[i] - mn) / ((mx - mn) || 1)) * (H - 6);
    marks.push({ x, y, buy: h.type === "COMPRA" });
  }
  return (
    <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-label="Preço com marcações de operações">
      <path d={linePath(closes, mn, mx, W, H)} fill="none" stroke={P.textFaint} strokeWidth="1.4" />
      {marks.map((mk, i) => mk.buy
        ? <path key={i} d={`M ${mk.x} ${mk.y - 5} L ${mk.x - 4} ${mk.y + 3} L ${mk.x + 4} ${mk.y + 3} Z`} fill={P.positive} />
        : <path key={i} d={`M ${mk.x} ${mk.y + 5} L ${mk.x - 4} ${mk.y - 3} L ${mk.x + 4} ${mk.y - 3} Z`} fill={P.negative} />)}
    </svg>
  );
}

// FASE 3 (mock v2 aprovado): RÉGUA universal do plano/risco — um só modelo
// mental no funil: marcas (invalidação/gatilho/alvo ou stop/alvo) + ponto
// "agora". Reaproveitada pelo card do Radar e do Portfólio.
function PlanRuler({ caption, marks, cur, curLabel, legend, captionExtra }) {
  const nums = [...(marks || []).map((m) => m && m.v), cur].filter((v) => typeof v === "number" && isFinite(v));
  if (nums.length < 2) return null;
  const mn = Math.min(...nums), mx = Math.max(...nums);
  const posOf = (v) => 8 + ((v - mn) / ((mx - mn) || 1)) * 84;
  return (
    <div style={{ marginTop: "13px" }}>
      {caption && <div style={{ fontSize: "10.5px", color: T.textFaint, letterSpacing: "0.05em", fontWeight: 700, marginBottom: "15px", display: "flex", alignItems: "center", gap: "6px" }}>{caption}{captionExtra}</div>}
      <div style={{ position: "relative", height: "8px", borderRadius: "999px", background: `linear-gradient(90deg, ${T.negativeTint} 0%, ${T.knob} 40%, ${T.knob} 60%, ${T.positiveTint} 100%)` }}>
        {(marks || []).filter((m) => m && typeof m.v === "number").map((m, i) => (
          <div key={i} style={{ position: "absolute", top: "-3px", bottom: "-3px", width: "2.5px", borderRadius: "2px", transform: "translateX(-50%)", left: posOf(m.v) + "%", background: m.color }} />
        ))}
        {typeof cur === "number" && isFinite(cur) && (
          <>
            {curLabel && <div style={{ position: "absolute", top: "-16px", transform: "translateX(-50%)", left: posOf(cur) + "%", fontSize: "9.5px", color: T.textFaint, fontWeight: 800, whiteSpace: "nowrap" }}>{curLabel}</div>}
            <div style={{ position: "absolute", top: "50%", width: "14px", height: "14px", borderRadius: "50%", transform: "translate(-50%,-50%)", left: posOf(cur) + "%", background: T.textPrimary, border: `3px solid ${T.bgCard}`, boxShadow: `0 0 0 1.5px ${T.borderSubtle}` }} />
          </>
        )}
      </div>
      {legend && legend.length > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "7px", fontFamily: MONO, fontSize: "10.5px" }}>
          {legend.map((l, i) => (
            <div key={i} style={{ textAlign: i === 0 ? "left" : i === legend.length - 1 ? "right" : "center", lineHeight: 1.35 }}>
              <div style={{ color: l.kColor || T.textFaint, fontWeight: 800, letterSpacing: ".05em", fontSize: "9.5px" }}>{l.k}</div>
              <div style={{ fontWeight: 700, color: l.color || T.textPrimary }}>
                {l.v != null ? price(l.v) : (l.cta || "—")}
                {l.sub != null && <span style={{ color: T.textFaint, fontWeight: 600 }}> {l.sub}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// FASE 3: pill global "no portfólio · qtd" — regra aprovada: qualquer card
// mostra a quantidade quando o ativo tem posição.
function PosPill({ qty }) {
  if (!qty) return null;
  return <span style={{ padding: "3px 9px", borderRadius: "999px", background: T.accentTint10, color: T.accent, fontSize: "10.5px", fontWeight: 800, whiteSpace: "nowrap" }}>no portfólio · {qty}</span>;
}

// FASE 3 (Portfólio): compras que formaram a POSIÇÃO ATUAL — reinicia a lista
// quando a quantidade zera (posição encerrada) e ignora vendas parciais.
function comprasDaPosicao(history, t) {
  const ops = (history || []).filter((h) => h && h.t === t).slice().reverse(); // antiga → recente
  let qty = 0, compras = [];
  for (const h of ops) {
    if (h.type === "COMPRA") {
      if (qty <= 0) compras = [];
      compras.push(h);
      qty += (h.qty || 0);
    } else {
      qty -= (h.qty || 0);
      if (qty < 0) qty = 0;
    }
  }
  return qty > 0 ? compras : [];
}

// qa/40: rótulo de decisão por MODO — o `veredito` do scanner é vocabulário
// de ESTUDO por construção ("Estudar alta/baixa"); na MESA a decisão exibida
// vem do PLANO determinístico (COMPRAR/VENDER/AGUARDAR CONFIRMAÇÃO/NÃO
// OPERAR), que o scan sempre anexa. Fallback: o próprio veredito.
const decisaoDoModo = (item, operador) =>
  (operador && item && item.plano && item.plano.decisao) ? item.plano.decisao : (item || {}).veredito;

// qa/40: mapa de decisão educacional → mesa, aplicado NO RENDER. O servidor já
// devolve o vocabulário certo para análises NOVAS (analyze_structured/analyze),
// mas análises ANTIGAS em cache guardam "Estudar alta/baixa" — mapear aqui
// garante que a mesa nunca exiba a voz de estudo, seja qual for a idade do dado.
const REC_PRO_MAP = {
  "Estudar alta": "COMPRAR", "Estudar baixa": "VENDER",
  "Aguardar": "AGUARDAR CONFIRMAÇÃO", "Monitorar": "AGUARDAR CONFIRMAÇÃO",
  "Não operar": "NÃO OPERAR",
};
const recDoModo = (rec, operador) => (operador && REC_PRO_MAP[rec]) ? REC_PRO_MAP[rec] : rec;

const REC_STYLE = {
  "Estudar alta": [T.positive, T.positiveTint10],
  "Estudar baixa": [T.negative, T.negativeTint10],
  // FASE 8B (R4): decisões da MESA — sem isto o chip do N2 caía no cinza
  "COMPRAR": [T.positive, T.positiveTint10],
  "VENDER": [T.negative, T.negativeTint10],
  "AGUARDAR CONFIRMAÇÃO": [T.accent, T.accentTint10],
  "NÃO OPERAR": [T.textMuted, T.bgBase],
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
  // v2: o modelo "opcoes" sai do seletor ENQUANTO a fonte não devolver cadeia.
  // Ele continua inteiro no backend (technical_models.py + _options_status_for_llm);
  // com a cadeia vazia, escolhê-lo só gastava uma chamada de LLM para dizer
  // "não há opções para este ativo". Devolver = reinserir esta linha:
  //   ["opcoes", "Opções", "Ativo objeto + yfinance"],
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

function KpiBlock({ kpis, operador }) {
  // qa/40: a decisão exibida segue o MODO (mapeia cache antigo de estudo→mesa).
  const rec = recDoModo(kpis.recomendacao, operador);
  const [recColor, recBg] = REC_STYLE[rec] || [T.textMuted, T.bgBase];
  const [dirColor, dirArrow] = DIR_STYLE[kpis.direcao] || [T.textMuted, ""];
  return (
    <div style={{ marginTop: "12px", display: "grid", gap: "8px" }}>
      {kpis.recomendacao && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", padding: "10px 12px", borderRadius: "9px", background: recBg, border: `1px solid ${recColor}` }}>
            {/* qa/40: rótulo e rodapé por MODO — na mesa "PLANO EDUCACIONAL" não
                cabe; a decisão é da mesa, a execução é do usuário. */}
            <span style={{ fontSize: "10px", letterSpacing: "0.06em", color: T.textFaint }}>{operador ? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"}</span>
            <span style={{ fontWeight: 800, fontSize: "14px", color: recColor }}>{rec}</span>
          </div>
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "6px", lineHeight: 1.5 }}>
            {operador
              ? "Decisão da mesa sobre dados passados — a execução e o risco são seus, na sua corretora. Não é ordem nem recomendação personalizada."
              : "Sinal gerado para fins educacionais — não é recomendação de compra ou venda."}
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

// qa/36 (F10.2): FUNDAMENTO — chip de score A/B/C (filtro de qualidade, nunca
// gatilho) e tabela de métricas. Cor por score; "sem dado" explícito, nunca
// inferência. score ausente → nada renderiza (ticker sem cobertura).
const SCORE_COLOR = { A: "positive", B: "accent", C: "negative" };
function FundamentoChip({ f }) {
  if (!f || !f.score) return null;
  const c = T[SCORE_COLOR[f.score] || "textFaint"];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 9px", borderRadius: "7px", fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", border: `1px solid ${c}`, color: c }}>
      FUNDAMENTO <b style={{ fontFamily: MONO, fontSize: "11px" }}>{f.score}</b>
    </span>
  );
}
// fração → percentual pt-BR (0.244 → "24,4%"); null/NaN → null (vira "sem dado")
const fracPct = (v) => (v == null || isNaN(v) ? null : (v * 100).toFixed(1).replace(".", ",") + "%");
const num1 = (v) => (v == null || isNaN(v) ? null : Number(v).toFixed(1).replace(".", ","));
function FundamentoTabela({ f }) {
  if (!f) return null;
  const linhas = [
    ["P/L", num1(f.pl)],
    ["ROE", fracPct(f.roe)],
    ["Dividend yield", fracPct(f.dy)],
    ["Margem líquida", fracPct(f.margemLiquida)],
    ["Dívida/EBITDA", f.dividaEbitda == null ? null : num1(f.dividaEbitda) + "×"],
    ["Crescimento receita (5a)", fracPct(f.crescReceita)],
  ];
  return (
    <div style={{ marginTop: "12px", ...card, padding: "13px 15px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "6px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", color: T.textSecondary }}>FUNDAMENTO</span>
          <FundamentoChip f={f} />
        </div>
        <span style={{ fontSize: "10px", color: T.textFaint }}>{f.referencia ? "ref. " + f.referencia : ""}{f.fonte ? " · " + f.fonte : ""}</span>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
        <tbody>
          {linhas.map(([k, v], i) => (
            <tr key={i}>
              <td style={{ padding: "5px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", color: T.textMuted }}>{k}</td>
              <td style={{ padding: "5px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", textAlign: "right", fontFamily: MONO, fontWeight: 700, color: v == null ? T.textFaint : T.textSecondary, fontStyle: v == null ? "italic" : "normal" }}>{v == null ? "sem dado" : v}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: "10px", color: T.textFaint, lineHeight: 1.5, marginTop: "8px" }}>Filtro de qualidade (valuation · rentabilidade · solidez), não é gatilho de compra. Célula "sem dado" não pontua nem penaliza. Fonte indisponível = sem inferência.</div>
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
  // qa/44: alguns modelos escapam as quebras (\n / \t LITERAIS) — vira sujeira
  // no meio do texto inline. Normaliza para espaço (campo inline não tem linha).
  let rest = String(text == null ? "" : text).replace(/\\r\\n|\\n|\\r/g, " ").replace(/\\t/g, " ");
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
// qa/46: se o corpo chegar como JSON CRU (parse do servidor falhou, ou é uma
// análise ANTIGA em cache), extrai o campo de texto em vez de despejar o objeto.
// Repara quebras/tab reais dentro das strings (JSON "bonito" da LLM é inválido).
function corpoDeJson(raw) {
  let s = String(raw == null ? "" : raw).trim();
  if (!s.startsWith("{") || !/"(corpo|markdown|resumo|analise|analysis)"\s*:/.test(s)) return raw;
  const tryParse = (str) => { try { return JSON.parse(str); } catch { return null; } };
  let obj = tryParse(s);
  if (!obj) {
    let out = "", inStr = false, esc = false;
    for (const ch of s) {
      if (inStr) {
        if (esc) { out += ch; esc = false; continue; }
        if (ch === "\\") { out += ch; esc = true; continue; }
        if (ch === '"') { out += ch; inStr = false; continue; }
        if (ch === "\n") { out += "\\n"; continue; }
        if (ch === "\r") { out += "\\r"; continue; }
        if (ch === "\t") { out += "\\t"; continue; }
        out += ch; continue;
      }
      if (ch === '"') inStr = true;
      out += ch;
    }
    obj = tryParse(out);
  }
  if (obj && typeof obj === "object") return obj.corpo || obj.markdown || obj.resumo || obj.analise || obj.analysis || raw;
  return raw;
}
function Markdown({ text }) {
  const _t = corpoDeJson(text);
  let src = String(_t == null ? "" : _t).replace(/\r\n/g, "\n");
  // qa/44: modelos que escapam a quebra (\n / \t LITERAIS) faziam o corpo virar
  // UM bloco só ("completamente desformatado"). Desescapa antes de quebrar em
  // linhas — rede de segurança p/ qualquer LLM, além do normalize_markdown do server.
  src = src.replace(/\\r\\n|\\n|\\r/g, "\n").replace(/\\t/g, "  ").trim();
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
            {d.fatos.map((f, i) => <li key={i} style={{ fontSize: "13px", color: T.textPrimary, lineHeight: 1.5 }}><MdInline text={f} /></li>)}
          </ul>
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "9px", lineHeight: 1.5 }}>Contexto informativo com base nos dados disponíveis — sem garantia de completude ou atualidade. Não é recomendação de compra ou venda.</div>
        </div>
      )}
      {/* qa/36 (F10.2): seção Fundamento + nota do rebaixamento de confiança. */}
      {an.fundamento && <FundamentoTabela f={an.fundamento} />}
      {an.rebaixadoPorFundamento && (
        <div style={{ marginTop: "9px", padding: "9px 11px", borderRadius: "9px", background: T.accentTint10, borderLeft: `3px solid ${T.accent}`, fontSize: "11px", color: T.textSecondary, lineHeight: 1.5 }}>
          Confiança rebaixada para <b>{an.confiancaFinal}</b>: a decisão técnica é operável, mas o fundamento é fraco (score C). O plano técnico não muda — só a confiança desce um degrau.
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
    // qa/34: candles pela paleta do MODO (usePalette) — eram verde/rosa FIXOS,
    // a única parte do PriceChart que ignorava tema/modo (qa/29 B2 corrigiu
    // grid/linhas mas os candles ficaram de fora).
    const price = chart.addCandlestickSeries({
      upColor: P.positive, downColor: P.negative,
      borderUpColor: P.positive, borderDownColor: P.negative,
      wickUpColor: P.positive, wickDownColor: P.negative,
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

function TechnicalModal({ ticker, name, quote, position, onClose, period }) {
  const P = usePalette();
  const [data, setData] = useState(() => store.cachedTechnicals(ticker));
  const [loading, setLoading] = useState(false);
  const [demo, setDemo] = useState(false);
  const [show, setShow] = useState({ sma20: true, sma50: true, bb: false, vol: true });
  const [viewBars, setViewBars] = useState(66); // 3M inicial
  const [range, setRange] = useState(null);

  useEffect(() => {
    let alive = true;
    const per = period || "1y";
    const cached = store.cachedTechnicals(ticker, per);
    if (cached) { setData(cached); setDemo(!!cached.sample); }
    setLoading(true);
    store.technicals(ticker, per)
      .then((r) => { if (alive) { setData(r); setDemo(false); } })
      .catch(() => { if (alive && !cached) { setData(sampleTechnicals(ticker)); setDemo(true); } })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [ticker, period]);

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
  // qa/29 (B2): mesma causa-raiz do OpsSparkline — fill=/stroke= em SVG não
  // resolve var(--x) de forma confiável neste WebKit. usePalette() dá o hex
  // já mesclado com o override do Modo Operador.
  const P = usePalette();
  const gid = useMemo(() => "capArea" + Math.random().toString(36).slice(2, 8), []);
  const { data, quotes } = ctx;
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
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={up ? P.positive : P.negative} stopOpacity="0.28" />
              <stop offset="1" stopColor={up ? P.positive : P.negative} stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1="0" y1="84" x2="300" y2="84" stroke={P.chartGrid} strokeWidth="1" />
          {hasSeries
            ? (<>
                {/* qa/mock v2: ÁREA preenchida (gradiente na cor do modo) sob a linha */}
                <path d={`${path} L300,92 L0,92 Z`} fill={`url(#${gid})`} stroke="none" />
                <path d={path} fill="none" stroke={up ? P.positive : P.negative} strokeWidth="2" />
              </>)
            : <path d="M0,72 C60,66 110,58 150,52 C200,45 250,40 300,30" fill="none" stroke={P.textFaint} strokeWidth="2" strokeOpacity="0.35" strokeDasharray="4 4" />}
        </svg>
      </div>
      {hasSeries ? (
        <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
          {stat("RETORNO ACUMULADO", pct(retAcum), retAcum >= 0 ? T.positive : T.negative)}
          {stat("DRAWDOWN (DESDE O PICO)", "-" + dd.toFixed(1) + "%", T.negative)}
          {stat("DIAS REGISTRADOS", String(ec.days))}
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
  // FASE 2 (2.2): Acompanhar vira a HOME — resumo do dia (determinístico, do
  // STU + finance.js), operações de hoje, alertas de setups na watchlist e o
  // destaque de oportunidade (1 leitura N1/dia autorizada, cache por snapshot).
  const { data, quotes, A, wlScan, destaque, cp } = ctx;   // FASE 8B (B1)
  const operador = (data.config && data.config.appMode) === "operador"; // qa/40: pill de decisão por modo
  const name = ((data.config && data.config.userName) || "").trim().split(/\s+/)[0] || "";
  const streak = (data.config && data.config.streak && data.config.streak.days) || 0;
  const [deepOpen, setDeepOpen] = useState(false);
  useEffect(() => {
    A.refreshWlScan();
    if (destaque.stage === "idle") A.loadDestaque(); // 1× por sessão — evita re-varrer o universo a cada visita
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const m = portfolioMetrics(data.positions, quotes, data.cash);
  const diaPct = dayReturnPct(m.patr, m.dayVal);
  const ec = equityCurve(data.equitySnapshots, (data.config || {}).initialBudget, m.patr, new Date().toISOString().slice(0, 10));
  const hoje = (() => { const d = new Date(); const p2 = (n) => String(n).padStart(2, "0"); return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()}`; })();
  const opsHoje = (data.history || []).filter((h) => String(h.date || "").startsWith(hoje));
  // qa/mock v2: o hero-carrossel mostra as MELHORES oportunidades da watchlist
  // (qualquer setup com confluência > 0, ordenado do maior p/ o menor) — antes
  // só entravam vereditos "Estudar", então em pregão sem gatilho o carrossel
  // sumia. O veredito específico continua no pill de cada card.
  const alertas = ((wlScan && wlScan.results) || [])
    .filter((r) => (r.confluencia || 0) > 0)
    .sort((a, b) => (b.confluencia || 0) - (a.confluencia || 0));
  const novato = (data.positions || []).length === 0 && (data.watchlist || []).length === 0;
  const it = destaque.item;
  const dColor = (m.dayVal || 0) >= 0 ? T.positive : T.negative;
  const aColor = (ec.retAcum || 0) >= 0 ? T.positive : T.negative;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div>
        {/* FASE 8B (B1/B4): saudação e resumo do dia na VOZ do modo (professor × mesa) */}
        <h1 style={{ margin: 0, fontSize: "23px", fontWeight: 700, letterSpacing: "-0.01em" }}>{cp.saudacao(name || null)}</h1>
        <p style={{ margin: "5px 0 0", color: T.textMuted, fontSize: "13px", lineHeight: 1.5 }}>
          {cp.resumoDia(((wlScan && wlScan.results) || []).filter((r) => (r.confluencia || 0) > 0).length,
            ((wlScan && wlScan.results) || []).filter((r) => r.plano && (r.plano.decisao === "COMPRAR" || r.plano.decisao === "VENDER")).length)}
        </p>
      </div>

      {/* qa/mock v2: HERO-CARROSSEL das oportunidades — os setups da watchlist
          viram cards swipeable com anel de confluência (antes eram uma lista de
          texto dentro do Resumo). Mesma navegação (abre a Watchlist). */}
      {!novato && alertas.length > 0 && (
        <div>
          <div style={{ fontSize: "10.5px", fontWeight: 700, color: T.textFaint, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: "9px" }}>{cp.kickerSetups}</div>
          <div style={{ display: "flex", gap: "12px", overflowX: "auto", scrollSnapType: "x mandatory", margin: "0 -18px", padding: "2px 18px 6px", WebkitOverflowScrolling: "touch" }}>
            {alertas.slice(0, 8).map((r) => (
              <button key={r.ticker} onClick={() => A.go("mercado")} style={{ ...card, scrollSnapAlign: "center", flex: "0 0 84%", maxWidth: "330px", borderLeft: `3px solid ${T.accent}`, padding: "15px 16px", textAlign: "left", cursor: "pointer" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                      <span style={{ fontFamily: MONO, fontWeight: 800, fontSize: "16px", color: T.textPrimary }}>{r.ticker}</span>
                      <span style={{ padding: "3px 9px", borderRadius: "999px", background: T.accentTint10, color: (REC_STYLE[decisaoDoModo(r, operador)] || [T.textMuted])[0], fontSize: "11px", fontWeight: 800 }}>{decisaoDoModo(r, operador)}</span>
                    </div>
                    <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "6px", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.melhorSetup || "Setup técnico"}</div>
                  </div>
                  <ConfluenceRing conf={r.confluencia} size={52} />
                </div>
                <div style={{ marginTop: "12px", fontSize: "12px", fontWeight: 700, color: T.accent }}>{cp.btnVerWatchlist} →</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* FASE 2 (2.2): estado vazio elegante — onboarding do funil */}
      {novato && (
        <div style={{ ...card, padding: "20px 18px", textAlign: "center", border: `1px dashed ${T.borderDashed}` }}>
          {/* qa/34: onboarding na voz do modo — antes hardcodado ("seu simulador…
              dinheiro simulado") e exibido igual na mesa do Operador. */}
          <div style={{ fontSize: "16px", fontWeight: 700 }}>{cp.welcomeTitulo}</div>
          <p style={{ margin: "8px auto 14px", color: T.textMuted, fontSize: "13px", maxWidth: "420px", lineHeight: 1.6 }}>
            {cp.welcomeCorpo}
          </p>
          <button onClick={() => A.go("radar")} style={{ padding: "11px 20px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>{cp.welcomeCta}</button>
        </div>
      )}

      {/* FASE 2 (2.2): resumo do dia — determinístico (finance.js é a fonte única) */}
      {!novato && (
        <div style={{ ...card, padding: "16px 18px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: T.textSecondary, letterSpacing: "0.05em" }}>RESUMO DO DIA</div>
          <div style={{ display: "flex", gap: "18px", flexWrap: "wrap", marginTop: "10px" }}>
            <div><div style={kicker}>CARTEIRA NO DIA</div><div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "17px", color: dColor }}>{moneySigned(m.dayVal)} <span style={{ fontSize: "12px" }}>({pct(diaPct)})</span></div></div>
            <div><div style={kicker}>ACUMULADO</div><div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "17px", color: aColor }}>{pct(ec.retAcum)}</div></div>
            <div><div style={kicker}>OPERAÇÕES HOJE</div><div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "17px", color: T.textPrimary }}>{opsHoje.length}</div></div>
          </div>
          {opsHoje.length > 0 && (
            <div style={{ marginTop: "10px" }}>
              {opsHoje.slice(0, 4).map((h, i) => (
                <div key={i} style={{ display: "flex", gap: "8px", fontFamily: MONO, fontSize: "11.5px", padding: "5px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none" }}>
                  <span style={{ fontWeight: 800, color: h.type === "COMPRA" ? T.positive : T.negative }}>{h.type === "COMPRA" ? "▲" : "▼"}</span>
                  <span style={{ fontWeight: 700 }}>{h.t}</span>
                  <span style={{ color: T.textMuted }}>{h.qty} × R$ {price(h.price)}</span>
                  {h.pnl != null && <span style={{ marginLeft: "auto", fontWeight: 700, color: h.pnl >= 0 ? T.positive : T.negative }}>{moneySigned(h.pnl)}</span>}
                </div>
              ))}
            </div>
          )}
          {/* qa/mock v2: os setups da watchlist saíram desta lista de texto e
              agora são o hero-carrossel acima (mesma navegação p/ a Watchlist). */}
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "10px" }}>{cp.rodape}</div>
        </div>
      )}

      {/* FASE 2 (2.2): destaque de oportunidade — melhor score FORA da watchlist */}
      {!novato && destaque.stage !== "idle" && destaque.stage !== "empty" && (
        <div style={{ ...card, padding: "16px 18px", borderLeft: `3px solid ${T.accent}` }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: T.accent, letterSpacing: "0.05em" }}>OPORTUNIDADE ADICIONAL PARA ESTUDO</div>
          {destaque.stage === "loading" && <div style={{ marginTop: "10px" }}><SweepGauge compact label="Varrendo o mercado" steps={["scan diário do Radar", "melhor score fora da watchlist"]} /></div>}
          {destaque.stage === "error" && <div style={{ marginTop: "8px", fontSize: "12px", color: T.textMuted }}>Não deu para varrer agora ({destaque.error}). Tento de novo quando você voltar.</div>}
          {destaque.stage === "ready" && it && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: "9px", flexWrap: "wrap", marginTop: "9px" }}>
                <span style={{ fontFamily: MONO, fontWeight: 800, fontSize: "17px" }}>{it.ticker}</span>
                <span style={{ padding: "4px 10px", borderRadius: "999px", background: (REC_STYLE[decisaoDoModo(it, operador)] || [T.textMuted, T.bgBase])[1], color: (REC_STYLE[decisaoDoModo(it, operador)] || [T.textMuted])[0], fontSize: "11px", fontWeight: 800 }}>{decisaoDoModo(it, operador)}</span>
                <span style={{ fontSize: "11.5px", color: T.textMuted }}>{it.melhorSetup || ""} · <b style={{ fontFamily: MONO }}>{it.confluencia}%</b></span>
                {/* qa/35 (P1): snapshotId REMOVIDO das telas de consumo — o hash
                    técnico vazava cru pro usuário; rastreabilidade agora só em
                    Perfil → Logs & debug. */}
              </div>
              {destaque.deep && destaque.deep.deep && destaque.deep.deep.resumo && (
                <div style={{ marginTop: "9px", fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6 }}>{destaque.deep.deep.resumo}</div>
              )}
              <div style={{ display: "flex", gap: "8px", marginTop: "11px" }}>
                {destaque.deep && <button onClick={() => setDeepOpen(true)} style={{ flex: 1, minHeight: "40px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 800, fontSize: "12.5px" }}>Ver leitura completa</button>}
                <button onClick={() => ctx.openAvaliar(it.ticker)} style={{ flex: 1, minHeight: "40px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700, fontSize: "12.5px" }}>{cp.btnLevarWatchlist}</button>
              </div>
              <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "9px", lineHeight: 1.5 }}>{cp.rodape}</div>
            </>
          )}
        </div>
      )}
      {deepOpen && destaque.deep && <DeepModal t={destaque.deep.ticker} d={{ res: destaque.deep.deep, cache: destaque.deep.cache }} cp={cp} onClose={() => setDeepOpen(false)} onAvaliar={(tk) => { setDeepOpen(false); ctx.openAvaliar(tk); }} />}

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
        <button onClick={() => A.go("carteira")} style={{ flex: "1 1 150px", minHeight: "46px", padding: "12px", borderRadius: "12px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Abrir Portfólio</button>
        <button onClick={() => A.go("mercado")} style={{ flex: "1 1 150px", minHeight: "46px", padding: "12px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>{cp.btnVerWatchlist}</button>
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
// FASE 7 (F7.1) — Modo de trabalho (Estudo × Operador). A troca para Operador
// SÓ acontece com o termo aceito (regra espelhada nos DOIS stores); a 1ª
// ativação abre o termo com rolagem obrigatória + checkbox. Voltar ao Estudo
// é livre. Mock aprovado: qa/mocks/modo-operador.html (tela 1).
function ModoTrabalhoCard({ ctx }) {
  const { data, A } = ctx;
  const c = data.config || {};
  const mode = c.appMode === "operador" ? "operador" : "estudo";
  const [termoOpen, setTermoOpen] = useState(false);
  const escolher = async (m) => {
    if (m === mode) return;
    if (m === "operador" && !c.operadorTermo) { setTermoOpen(true); return; }
    try {
      await A.saveConfig({ appMode: m });
    } catch (e) {
      // qa/audit-2026-08-08: putConfig agora pode chamar o servidor (sync do
      // appMode) — antes era 100% local e nunca falhava. Sem este catch, uma
      // falha de rede aqui vira promise rejeitada sem aviso nenhum: o
      // aparelho muda de modo local mas o servidor nunca sabe, e nenhum
      // reload acontece — pior que um erro visível.
      A.flash("Não consegui confirmar a troca de modo com o servidor: " + (e.message || e));
      return;
    }
    // qa/audit-2026-08-07: a troca de modo reinicia o app INTEIRO — não só
    // navega pra home. `appMode` é lido de forma independente em mais de
    // 10 lugares do código (telas, disclaimers, gates de Executar/entrada
    // automática); um reload garante que TODOS reflitam o modo novo, em
    // vez de confiar que cada tela vai perceber a mudança de estado sozinha.
    A.flash(m === "operador" ? "Modo Operador ativado — reiniciando…" : "Modo Estudo ativado — reiniciando…");
    setTimeout(() => window.location.reload(), 700);
  };
  const segBtn = (on) => ({ flex: 1, border: "none", borderRadius: "9px", padding: "10px", fontWeight: 800, fontSize: "13px", background: on ? T.accent : "transparent", color: on ? T.onAccent : T.textMuted });
  return (
    <div style={{ ...card, padding: "15px 16px" }}>
      <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", color: T.textSecondary }}>MODO DE TRABALHO</div>
      <div style={{ display: "flex", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "11px", padding: "4px", gap: "4px", marginTop: "10px" }}>
        <button onClick={() => escolher("estudo")} style={segBtn(mode === "estudo")}>🎓 Estudo</button>
        <button onClick={() => escolher("operador")} style={segBtn(mode === "operador")}>📈 Operador</button>
      </div>
      <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "9px", lineHeight: 1.5 }}>
        {mode === "operador"
          ? <>Decisões diretas (comprar/vender/aguardar/não operar) com plano de entrada, stop, alvo e risco. Termo aceito em {(c.operadorTermo || {}).aceitoEm ? String(c.operadorTermo.aceitoEm).slice(0, 10) : "—"} (v{(c.operadorTermo || {}).versao || "?"}).</>
          : <>Carteira simulada e leitura didática — o padrão para aprender. O Modo Operador libera decisões diretas com plano e gestão de risco.</>}
      </div>
      {termoOpen && <TermoOperadorModal ctx={ctx} onClose={() => setTermoOpen(false)} />}
    </div>
  );
}

function TermoOperadorModal({ ctx, onClose }) {
  const { A } = ctx;
  const [liTudo, setLiTudo] = useState(false);   // exige rolar até o fim
  const [aceito, setAceito] = useState(false);
  const [busy, setBusy] = useState(false);
  // FASE 8B (P2): se o texto CABE sem rolagem (telas grandes/fonte pequena),
  // o onScroll nunca dispara e o aceite ficava travado para sempre. Ao montar
  // (e ao redimensionar), se não há overflow, o termo já conta como lido.
  const termoRef = useRef(null);
  useEffect(() => {
    const check = () => {
      const el = termoRef.current;
      if (el && el.scrollHeight - el.clientHeight < 12) setLiTudo(true);
    };
    check();
    const id = setTimeout(check, 250); // reflow tardio do WebView (fontes)
    window.addEventListener("resize", check);
    return () => { clearTimeout(id); window.removeEventListener("resize", check); };
  }, []);
  const onScroll = (e) => {
    const el = e.target;
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 12) setLiTudo(true);
  };
  const ativar = async () => {
    setBusy(true);
    try {
      // termo PRIMEIRO (mesmo patch): os stores só aceitam "operador" com ele
      await A.saveConfig({ operadorTermo: { aceitoEm: new Date().toISOString(), versao: TERMO_OPERADOR_VERSAO }, appMode: "operador" });
      onClose();
      // qa/audit-2026-08-07: mesmo reinício completo de escolher() — ver o
      // comentário lá. Esta é a OUTRA porta de entrada pro Modo Operador (1ª
      // ativação, com termo), e as duas precisam da mesma garantia.
      A.flash("Modo Operador ativado — reiniciando…");
      setTimeout(() => window.location.reload(), 700);
    } catch (e) { A.flash("Erro ao ativar: " + (e.message || e)); }
    finally { setBusy(false); }
  };
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 84, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "440px", ...card, padding: "20px", maxHeight: "88vh", display: "flex", flexDirection: "column" }}>
        <div style={{ fontSize: "16px", fontWeight: 800, marginBottom: "4px" }}>Termo de Responsabilidade</div>
        <div style={{ fontSize: "11.5px", color: T.textMuted, marginBottom: "10px" }}>Modo Operador · versão {TERMO_OPERADOR_VERSAO} — leia até o fim para habilitar o aceite.</div>
        <div ref={termoRef} onScroll={onScroll} style={{ overflowY: "auto", border: `1px solid ${T.borderSubtle}`, borderRadius: "10px", padding: "12px", fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6, maxHeight: "34vh", WebkitOverflowScrolling: "touch" }}>
          {DISCLAIMERS.operadorTermo}
        </div>
        {!liTudo && <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px", textAlign: "center" }}>↓ role o texto até o fim para liberar o aceite</div>}
        <label style={{ display: "flex", gap: "9px", alignItems: "flex-start", marginTop: "12px", fontSize: "12.5px", color: liTudo ? T.textPrimary : T.textFaint, lineHeight: 1.5 }}>
          <input type="checkbox" disabled={!liTudo} checked={aceito} onChange={(e) => setAceito(e.target.checked)} style={{ marginTop: "2px" }} />
          <span>Li até o fim e entendo que posso perder dinheiro operando por minha conta e risco.</span>
        </label>
        <div style={{ display: "flex", gap: "9px", marginTop: "14px" }}>
          <button onClick={onClose} style={{ flex: 1, padding: "11px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>Continuar no Estudo</button>
          <button onClick={ativar} disabled={!liTudo || !aceito || busy} style={{ flex: 1, padding: "11px", borderRadius: "10px", border: "none", background: (liTudo && aceito) ? T.accent : T.bgBase, color: (liTudo && aceito) ? T.onAccent : T.textFaint, fontWeight: 800, fontSize: "13px" }}>{busy ? "Ativando…" : "Ativar Modo Operador"}</button>
        </div>
      </div>
    </div>
  );
}

// qa/mock v2: tile de acesso do Perfil — entrada visual (ícone em chip + título
// + subtítulo). `wide` = card de largura total com chevron; senão, célula de grid.
function ProfileTile({ icon, title, sub, onClick, wide }) {
  return (
    <button onClick={onClick} style={{ display: "flex", flexDirection: wide ? "row" : "column", alignItems: wide ? "center" : "flex-start", gap: wide ? "13px" : "9px", minHeight: wide ? "auto" : "98px", padding: "14px", borderRadius: "14px", border: `1px solid ${T.borderSubtle}`, background: T.bgCard, textAlign: "left", cursor: "pointer", boxShadow: "0 8px 24px -14px rgba(0,0,0,0.5)" }}>
      <span style={{ width: 34, height: 34, flex: "none", borderRadius: "10px", background: T.accentTint, color: T.accent, display: "flex", alignItems: "center", justifyContent: "center" }} aria-hidden>{icon}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: "block", fontSize: "13.5px", fontWeight: 700, color: T.textPrimary }}>{title}</span>
        {sub ? <span style={{ display: "block", fontSize: "11.5px", color: T.textMuted, marginTop: "2px", lineHeight: 1.4 }}>{sub}</span> : null}
      </span>
      {wide ? <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden style={{ flex: "none", color: T.textFaint }}><polyline points="9 5 16 12 9 19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg> : null}
    </button>
  );
}

const hubGroup = { fontSize: "10px", fontWeight: 800, letterSpacing: "0.08em", color: T.textFaint, textTransform: "uppercase", margin: "8px 2px 0" };
const hubGrid = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" };

// qa/38 (Help): conteúdo do guia — mode-aware (usa os rótulos de tela de cp,
// que já mudam entre Estudo/Operador) e honesto sobre "tudo simulado". Uma
// fonte só, reusada pela tela de Ajuda, pelo tour e pelo doc externo (AJUDA.md).
function ajudaSecoes(cp, operador) {
  const tRadar = cp.tituloRadar, tWl = cp.tituloWatchlist, tPort = cp.tituloPortfolio;
  const aprofundar = cp.btnAprofundar; // "Aprofundar com IA" / "Plano da mesa (IA)"
  return [
    ["O que é o Boris+", [
      "Um app educacional de análise técnica da B3. Ele varre o mercado, mostra oportunidades de estudo e deixa você simular uma carteira — tudo com dinheiro fictício.",
      "Nada aqui é ordem real nem recomendação personalizada: nenhuma ordem é enviada à corretora. O objetivo é aprender a ler o mercado com disciplina.",
    ]],
    ["Os dois modos", [
      "O app tem dois modos, com a mesma base técnica e vozes diferentes. **Estudo** é um professor: explica o porquê de cada setup. **Operador** é uma mesa de operações: dá o plano objetivo (entrada, stop, alvo, risco).",
      "Você troca em Perfil → Modo de trabalho. O modo muda a cor, os rótulos e o tom — mas a execução e o risco são sempre seus.",
      operador ? "Você está no Modo Operador agora." : "Você está no Modo Estudo agora.",
    ]],
    ["Acompanhar (início)", [
      "A tela inicial resume seu dia: melhores oportunidades da sua watchlist, a curva do patrimônio simulado, sua sequência de estudo e um lembrete do que fazer a seguir.",
      "É o ponto de partida — dali você vai para o " + tRadar + ".",
    ]],
    [tRadar, [
      "Varre o universo de ações e lista, por ativo: o veredito, a **confluência** (anel de 0–100% = quanto o ativo bate com um setup clássico), uma leitura rápida e o mini-gráfico de preço.",
      "Em cada card você pode " + (operador ? "abrir o **" + aprofundar + "** (leitura da IA) ou **monitorar** o ativo." : "abrir o **" + aprofundar + "** (leitura da IA) ou levar para a **" + tWl + "**."),
      "A confluência mede aderência ao padrão em dados passados — não é probabilidade de resultado.",
    ]],
    [tWl, [
      "Seus ativos " + (operador ? "monitorados" : "em estudo") + ", ordenados por oportunidade. Cada linha tem um mini-gráfico e abre a análise completa.",
      "Use para acompanhar de perto os ativos que te interessam antes de simular uma operação.",
    ]],
    [tPort, [
      "Sua carteira **simulada**: patrimônio, resultado do dia e cada posição com a régua do plano (invalidação → gatilho → alvo).",
      "Você simula compras e vendas, define stop e alvo, e acompanha o resultado em R — sem risco de dinheiro real.",
    ]],
    ["Operador IA", [
      "Um agente que acompanha as posições da carteira simulada e age pelas regras que você define (proteger stop, realizar no alvo). Com conta, roda no servidor 24×5, mesmo com o app fechado.",
      "Você escolhe **Executar** (ele simula a saída no stop/alvo) ou **Apenas sinalizar** (só avisa), define regras e tetos, e o intervalo de reavaliação. Sempre sobre a carteira simulada.",
    ]],
    ["Fundamento (A/B/C)", [
      "Ao lado do sinal técnico, alguns ativos mostram um selo de **fundamento**: A (sólido), B (regular) ou C (fraco), por valuation, rentabilidade e solidez.",
      "É um **filtro de qualidade**, nunca um gatilho de compra: a técnica manda no plano. Quando a decisão técnica é operável mas o fundamento é fraco (C), a confiança desce um degrau. Sem dado de fundamento, o app mostra “sem dado” — nunca inventa.",
    ]],
    ["Eficiência da IA", [
      "O app guarda cada análise com stop/alvo e, 10 pregões depois, confere se bateu o alvo, o stop ou expirou. Isso vira estatística: taxa de acerto, expectância (vantagem média em R), calibração da confiança e a curva de R acumulado.",
      "Enquanto não há amostra suficiente, aparece “n insuficiente” ou “aguardando o prazo” — em vez de um número enganoso. É autoavaliação sobre o passado, não garantia de futuro.",
    ]],
    ["Avisos importantes", [
      "Tudo no Boris+ é **educacional e simulado**. Não é recomendação de investimento nem promessa de resultado. Operar no mercado real envolve risco de perda.",
      "Use sempre stop, dimensione a posição e respeite seu plano de risco. As decisões e a execução são suas.",
    ]],
  ];
}

// Passos do tour de primeiro uso (funil). Curto, aponta o caminho.
function tourPassos(cp) {
  return [
    ["Bem-vindo ao Boris+", "Um app para **estudar** o mercado da B3 com uma carteira simulada. Tudo aqui é educacional — nenhuma ordem real é enviada."],
    ["1 · Descubra no " + cp.tituloRadar, "O " + cp.tituloRadar + " varre o mercado e mostra os ativos com setup, com confluência e leitura rápida."],
    ["2 · Acompanhe na " + cp.tituloWatchlist, "Leve os melhores para a " + cp.tituloWatchlist + " e acompanhe de perto antes de agir."],
    ["3 · Simule no " + cp.tituloPortfolio, "Simule compras e vendas no " + cp.tituloPortfolio + " — com stop, alvo e risco em R, sem dinheiro real."],
  ];
}

// Render inline de **negrito** simples (sem HTML injetado).
function AjudaTexto({ children }) {
  const parts = String(children).split(/(\*\*[^*]+\*\*)/g);
  return <p style={{ margin: "0 0 9px", fontSize: "13px", color: T.textSecondary, lineHeight: 1.6 }}>{parts.map((p, i) => p.startsWith("**") && p.endsWith("**") ? <b key={i} style={{ color: T.textPrimary }}>{p.slice(2, -2)}</b> : <span key={i}>{p}</span>)}</p>;
}

// qa/38 (Help): TELA DE AJUDA — accordion "Como funciona", uma seção por área.
function AjudaScreen({ ctx }) {
  const cp = ctx.cp;
  const operador = (ctx.data.config && ctx.data.config.appMode) === "operador";
  const secoes = ajudaSecoes(cp, operador);
  const [aberta, setAberta] = useState(0);
  return (
    <div>
      <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Como funciona</h1>
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "13px", lineHeight: 1.5, maxWidth: "600px" }}>
        Um guia rápido de cada parte do app. Toque numa seção para abrir.
      </p>
      <button onClick={() => ctx.A.openTour && ctx.A.openTour()} style={{ marginTop: "12px", padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 700, fontSize: "12px" }}>▶ Ver o tour de novo</button>
      <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "8px" }}>
        {secoes.map(([titulo, paras], i) => {
          const on = aberta === i;
          return (
            <div key={i} style={{ ...card, padding: "0", overflow: "hidden" }}>
              <button onClick={() => setAberta(on ? -1 : i)} aria-expanded={on} style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", padding: "14px 16px", background: "transparent", border: "none", color: T.textPrimary, fontWeight: 700, fontSize: "14px", textAlign: "left" }}>
                <span>{titulo}</span>
                <span aria-hidden style={{ color: T.accent, fontWeight: 800, flex: "none" }}>{on ? "−" : "+"}</span>
              </button>
              {on && (
                <div style={{ padding: "0 16px 14px" }}>
                  {paras.map((p, j) => <AjudaTexto key={j}>{p}</AjudaTexto>)}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: "16px", padding: "12px 14px", borderRadius: "11px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, fontSize: "11px", color: T.textFaint, lineHeight: 1.55 }}>
        {DISCLAIMERS.appBanner}
      </div>
    </div>
  );
}

// qa/38 (Help): TOUR de primeiro uso — passo a passo curto do funil.
function TourModal({ ctx }) {
  const [i, setI] = useState(0);
  const passos = tourPassos(ctx.cp);
  const ultimo = i >= passos.length - 1;
  const fechar = () => ctx.A.closeTour && ctx.A.closeTour();
  const [titulo, corpo] = passos[i];
  return (
    <div onClick={fechar} style={{ position: "fixed", inset: 0, zIndex: 75, background: T.scrim, display: "flex", alignItems: "flex-end", justifyContent: "center", padding: "0" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "460px", ...card, borderBottomLeftRadius: 0, borderBottomRightRadius: 0, padding: "22px 20px calc(22px + env(safe-area-inset-bottom))" }}>
        <div style={{ display: "flex", gap: "5px", marginBottom: "14px" }}>
          {passos.map((_, k) => <span key={k} style={{ flex: 1, height: "3px", borderRadius: "999px", background: k <= i ? T.accent : T.borderSubtle }} />)}
        </div>
        <div style={{ fontSize: "18px", fontWeight: 800, marginBottom: "8px" }}>{titulo}</div>
        <AjudaTexto>{corpo}</AjudaTexto>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginTop: "16px" }}>
          <button onClick={fechar} style={{ background: "transparent", border: "none", color: T.textMuted, fontWeight: 700, fontSize: "13px", padding: "8px 4px" }}>Pular</button>
          <button onClick={() => (ultimo ? fechar() : setI(i + 1))} style={{ padding: "11px 22px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "14px" }}>{ultimo ? "Começar" : "Próximo"}</button>
        </div>
      </div>
    </div>
  );
}

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

      <ModoTrabalhoCard ctx={ctx} />

      {/* qa/mock v2: hub reorganizado em BLOCOS com tiles (entradas visuais), no
          lugar da pilha de linhas de mesmo peso. NENHUM destino removido — cada
          tile abre a MESMA sub-tela de antes (config/ia/notificacoes/eficiencia/
          logs) e a Conta segue no openAuth. */}
      <div style={hubGroup}>Conta</div>
      <ProfileTile wide onClick={() => ctx.openAuth && ctx.openAuth()} title={ctx.authUser ? "Conta" : "Entrar ou criar conta"} sub={ctx.authUser ? ((((ctx.authUser.name || "").trim()) || (/@privaterelay\.appleid\.com$/i.test(ctx.authUser.email || "") ? "Sua conta Apple" : ctx.authUser.email) || "conectado") + " · toque para gerenciar") : "Opcional — salva sua carteira e sincroniza entre aparelhos"} icon={
        <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="8.5" r="3.6" fill="none" stroke="currentColor" strokeWidth="1.9" /><path d="M5 19.5c0-3.6 3.1-5.5 7-5.5s7 1.9 7 5.5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" /></svg>
      } />

      <div style={hubGroup}>Personalização e simulação</div>
      <ProfileTile wide onClick={() => onOpen("config")} title="Conta & preferências" sub="Perfil de risco, aparência, período de candles, orçamento" icon={
        <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.9" /><path d="M12 3v2.5M12 18.5V21M21 12h-2.5M5.5 12H3M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8M18.4 18.4l-1.8-1.8M7.4 7.4 5.6 5.6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
      } />

      <div style={hubGroup}>IA e desempenho</div>
      <div style={hubGrid}>
        <ProfileTile onClick={() => onOpen("ia")} title="Configurações de IA" sub="Modelo, skills por modo e prompts" icon={
          <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><path d="M12 3a5 5 0 0 1 5 5c0 2-1.2 3.1-2 4-.6.7-1 1.3-1 2.3h-4c0-1-.4-1.6-1-2.3-.8-.9-2-2-2-4a5 5 0 0 1 5-5Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M10 17.5h4M10.5 20h3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
        } />
        <ProfileTile onClick={() => onOpen("eficiencia")} title="Eficiência da IA" sub="Quanto bateu alvo/stop" icon={
          <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="7.5" fill="none" stroke="currentColor" strokeWidth="1.7" /><circle cx="12" cy="12" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.7" /><circle cx="12" cy="12" r="0.9" fill="currentColor" stroke="none" /></svg>
        } />
        <ProfileTile onClick={() => onOpen("atividade")} title="Atividade da IA" sub="Custo estimado e histórico" icon={
          <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><path d="M4 19V5M4 19h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /><path d="M8 15l3-4 3 2 4-6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
        } />
      </div>

      <div style={hubGroup}>Notificações e avançado</div>
      <div style={hubGrid}>
        <ProfileTile onClick={() => onOpen("notificacoes")} title="Notificações" sub={notifOn ? "Ativas — stop, alvo, agente" : "Desativadas — toque p/ ativar"} icon={
          <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><path d="M6 10.5a6 6 0 0 1 12 0c0 4 1.3 5.3 1.8 6H4.2c.5-.7 1.8-2 1.8-6Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M10 19.5a2 2 0 0 0 4 0" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
        } />
        <ProfileTile onClick={() => onOpen("logs")} title="Logs & debug" sub={ag.serverEnabled ? "Status e Diário do Operador" : "Servidor e logs técnicos"} icon={
          <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><path d="M4 18v-5M9.5 18v-9M15 18V7M20 18v-3" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" /></svg>
        } />
      </div>
      <div style={hubGroup}>Ajuda</div>
      <ProfileTile wide onClick={() => onOpen("ajuda")} title="Como funciona" sub="Guia rápido de cada tela + tour do app" icon={
        <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M9.5 9.2a2.6 2.6 0 0 1 5 .9c0 1.7-2.5 2-2.5 3.6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="currentColor" strokeWidth="0.8" /></svg>
      } />

      <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "8px", lineHeight: 1.5 }}>
        Notificações {notifOn ? "ativas" : "desativadas"} · {ctx.cp.rodape}
      </div>
      {/* FASE 8B: carimbo do build instalado — se não bater com a entrega,
          o aparelho está rodando código antigo (rode npm run ios + reinstale). */}
      <div style={{ fontSize: "10px", color: T.textFaint, fontFamily: MONO }}>build {BUILD_ID}</div>
    </div>
  );
}

// F1 (timing de entrada): estilo por estado — [cor, fundo, rótulo operador,
// rótulo estudo]. Os rótulos do estudo descrevem a CONDIÇÃO, sem verbo de
// ordem (a frase do backend já respeita o vocabulário por modo).
const TIMING_STYLE = {
  gatilho: [T.positive, "rgba(52,211,153,.12)", "● GATILHO ATINGIDO", "● CONDIÇÃO ATINGIDA"],
  armado: [T.accent, T.accentTint10, "◔ PLANO ARMADO", "◔ CONDIÇÃO ARMADA"],
  esticado: [T.negative, "rgba(248,113,113,.12)", "⚠ ESTICADO", "⚠ MOVIMENTO ESTICADO"],
  sem_dado: [T.textFaint, T.bgBase, "◌ SEM DADO 15M", "◌ SEM DADO 15M"],
  // Variante de rótulo do mesmo estado `sem_dado`: com o mercado fechado (das
  // 18h às 10h, todo dia) "SEM DADO 15M" acusava avaria onde só havia pregão
  // encerrado. O servidor marca isso em `foraDoPregao`.
  fora_pregao: [T.textFaint, T.bgBase, "◌ FORA DO PREGÃO", "◌ FORA DO PREGÃO"],
  // Pregão aberto, mas a última barra FECHADA ainda é de ontem (primeiros
  // minutos do dia + atraso do feed). Sem isto, o card afirmava estado de hoje
  // — inclusive "gatilho atingido" — com evidência do pregão anterior.
  aguardando_barra: [T.textFaint, T.bgBase, "◌ AGUARDANDO 1ª BARRA", "◌ AGUARDANDO 1ª BARRA"],
};

// ---- Camada de entendimento: a FOLHA de explicação ------------------------
// Por que folha (bottom sheet) e não um bloco dentro do card: o AtivoCard já
// afirma 18 coisas (docs/didatica-inventario.md) e o TimingBadge sozinho ocupa
// 3 linhas, entre a manchete de decisão e os chips. Não cabe mais bloco no
// fluxo vertical — e conteúdo que cresce debaixo do polegar de um iniciante,
// numa lista de 6 cards, faz ele tocar no botão errado. A folha abre SOBRE o
// card: não reflui a lista, comporta as três perguntas com folga, e é o mesmo
// gesto para todos os conceitos (uma afordância, não dezoito).
const CONCEITO_BLOCOS = [
  // Ordem deliberada: quem acabou de ver "condição atingida" pergunta antes de
  // tudo se o app comprou alguma coisa. Essa resposta não pode ser a terceira.
  ["naoAcontece", "O QUE O APP NÃO FAZ"],
  ["oQueE", "O QUE É"],
  ["oQueAcontece", "O QUE ACONTECE"],
];

// A AFORDÂNCIA ÚNICA é o padrão do Duolingo: termo explicável carrega um
// SUBLINHADO PONTILHADO e abre a explicação com um TOQUE simples. A versão
// anterior (toque longo) caiu no teste ao vivo por três defeitos que se
// compõem: sem indicação ninguém sabia onde segurar; segurando em qualquer
// lugar, fora dos setores quem respondia era a SELEÇÃO DE TEXTO do sistema;
// e toque longo só funciona com alvo óbvio — num card de texto, nunca é.
// O tap resolve os três: a indicação mora no próprio termo, o gesto é o mais
// universal que existe, e tap não seleciona texto nem compete com rolagem.
//
// SETOR É REGIÃO DECLARADA, não inferência: cada bloco do card se envolve num
// SetorAlvo com um `setorId`; o QUE cada id explica vem do REGISTRO servido
// pelo backend (didatica.setores) — repontear um setor é deploy do Railway,
// não build de iOS. O setor mais interno sob o dedo vence (stopPropagation
// no click: o de fora nem vê o toque).
//
// A convenção visual, aplicada UMA vez por setor (só no termo-âncora):
const SUBLINHADO = { textDecorationLine: "underline", textDecorationStyle: "dotted", textDecorationColor: T.textFaint, textUnderlineOffset: "3px", textDecorationThickness: "1px" };

// Caminho ACESSÍVEL nomeado: cada setor carrega um botão só-para-leitor
// ("O que é X?") — o VoiceOver lê a pergunta, não o número sublinhado.
const SR_ONLY = { position: "absolute", width: "1px", height: "1px", padding: 0, margin: "-1px", overflow: "hidden", clipPath: "inset(50%)", whiteSpace: "nowrap", border: 0 };

function SetorAlvo({ setorId, dados, rotulo, A, didatica, ativo = true, style, children }) {
  const cid = (didatica && didatica.ligada && didatica.setores) ? didatica.setores[setorId] : null;
  // Sem registro (camada desligada, backend antigo) ou sem condição a
  // explicar (`ativo`), o setor vira um contêiner comum — toque desarmado.
  if (!cid || !A || !ativo) return <div style={style}>{children}</div>;
  const abrir = (origem) => A.abrirSetor(setorId, cid, dados, origem);
  const onClick = (e) => {
    // setor mais interno vence; o toque não vaza para o card por baixo
    e.stopPropagation();
    abrir("toque");
  };
  return (
    // `userSelect: none` fica: impede o toque duplo apressado de virar
    // seleção. `touchAction` NÃO é tocado — a rolagem segue do sistema.
    <div onClick={onClick}
      style={{ position: "relative", cursor: "pointer", ...style, WebkitTouchCallout: "none", WebkitUserSelect: "none", userSelect: "none" }}>
      {children}
      <button onClick={(e) => { e.stopPropagation(); abrir("botao"); }}
        aria-label={"O que é " + rotulo + "?"} style={SR_ONLY}>?</button>
    </div>
  );
}

// Fase 4 — o ASSISTENTE, dentro da folha do conceito.
// Duas camadas com custos diferentes: a explicação acima é determinística e
// grátis; isto aqui chama LLM. Por isso é opt-in por toque, mostra o que sobra
// do teto do dia, e qualquer falha degrada para "a explicação acima continua
// valendo" — nunca deixa a pessoa sem resposta.
function AssistenteBox({ cid, dados, setor, tela }) {
  const [aberto, setAberto] = useState(false);
  const [q, setQ] = useState("");
  const [r, setR] = useState(null);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const perguntar = async () => {
    const pergunta = q.trim();
    if (!pergunta || busy) return;
    setBusy(true); setErro(""); setR(null);
    try {
      // O snapshot é o MESMO view-model que ancorou a explicação — nada de
      // raspar a tela: o que vai é dado estruturado, auditável.
      // `tela` diz de ONDE a pessoa pergunta: o pet passa a dele pronta;
      // aberta pelo toque no setor é o setor (allowlist no backend); depois
      // de navegar a cadeia, o conceito.
      const res = await store.assistente({ tela: tela || (setor ? "setor:" + setor : "conceito:" + cid), snapshot: dados || {}, pergunta });
      setR(res);
    } catch (e) {
      setErro((e && e.message) || String(e));
    } finally { setBusy(false); }
  };
  if (!aberto) {
    return (
      <button onClick={() => setAberto(true)}
        style={{ width: "100%", minHeight: "44px", marginBottom: "10px", borderRadius: "11px", border: `1px dashed ${T.borderSubtle}`, background: "transparent", color: T.textMuted, fontWeight: 700, fontSize: "12.5px" }}>
        Ainda com dúvida? Pergunte à IA sobre estes números
      </button>
    );
  }
  return (
    <div style={{ marginBottom: "12px", padding: "12px", borderRadius: "11px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
      <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.08em", color: T.textFaint, marginBottom: "8px" }}>PERGUNTE SOBRE ESTA TELA</div>
      <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={2} maxLength={400}
        placeholder="Ex.: por que o gatilho está nesse preço e não em outro?"
        style={{ width: "100%", boxSizing: "border-box", padding: "10px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "13px", resize: "vertical" }} />
      <button onClick={perguntar} disabled={busy || !q.trim()}
        style={{ width: "100%", minHeight: "40px", marginTop: "8px", borderRadius: "9px", border: "none", background: busy || !q.trim() ? T.bgPanel : T.accentTint10, color: busy || !q.trim() ? T.textFaint : T.accent, fontWeight: 800, fontSize: "12.5px" }}>
        {busy ? "pensando…" : "Perguntar"}
      </button>
      {erro && (
        <div style={{ marginTop: "9px", fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
          {erro}
          <div style={{ color: T.textFaint, fontSize: "11px", marginTop: "4px" }}>A explicação acima continua valendo — ela não depende da IA.</div>
        </div>
      )}
      {r && r.texto && (
        <div style={{ marginTop: "10px" }}>
          <div style={{ fontSize: "13px", color: T.textSecondary, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{r.texto}</div>
          <AiNote />
          {r.restanteHojeBRL != null && (
            <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "2px" }}>
              Resta hoje ≈ R$ {Number(r.restanteHojeBRL).toFixed(2).replace(".", ",")} de uso da IA.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConceitoSheet({ cid, dados, setor, onClose, onTrocar, didatica, voltar }) {
  const [c, setC] = useState(null);
  const [erro, setErro] = useState(false);
  useEffect(() => {
    let alive = true;
    setC(null); setErro(false);
    store.conceito(cid, { dados })
      .then((r) => { if (alive) setC(r); })
      .catch(() => { if (alive) setErro(true); });
    return () => { alive = false; };
  }, [cid, dados]);
  return (
    // zIndex 86: acima de TODOS os outros overlays (tour 75, sobre 80, auth 82,
    // ajuda 84, portão de abertura 85). Esta é a única folha que abre SOZINHA,
    // e a via proativa é one-shot por conceito, para sempre — ficar por baixo
    // significaria queimar a estreia sem ninguém ler nada.
    <div onClick={onClose} role="dialog" aria-label="Explicação"
      style={{ position: "fixed", inset: 0, zIndex: 86, background: T.scrim, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
      <div onClick={(e) => e.stopPropagation()}
        style={{ width: "100%", maxWidth: "520px", background: T.bgPanel, borderTop: `1px solid ${T.borderSubtle}`, borderRadius: "18px 18px 0 0", padding: "16px 18px calc(18px + env(safe-area-inset-bottom))", maxHeight: "82vh", overflowY: "auto" }}>
        <div style={{ width: "38px", height: "4px", borderRadius: "999px", background: T.borderSubtle, margin: "0 auto 12px" }} aria-hidden />
        {/* A cadeia precisa de volta: quem segue stop → R → gatilho não pode
            ter como única saída fechar tudo e recomeçar. */}
        {voltar && (
          <button onClick={voltar} aria-label="Voltar ao conceito anterior"
            style={{ minHeight: "36px", padding: "0 12px 0 6px", marginBottom: "6px", borderRadius: "999px", border: "none", background: "transparent", color: T.textMuted, fontSize: "12px", fontWeight: 700 }}>‹ voltar</button>
        )}
        {erro && <p style={{ margin: 0, fontSize: "13px", color: T.textMuted }}>Não consegui carregar a explicação agora. O card continua válido.</p>}
        {!c && !erro && <div className="sk" style={{ height: "120px", width: "100%" }} />}
        {c && (
          <>
            <h2 style={{ margin: "0 0 4px", fontSize: "18px", fontWeight: 800, color: T.textPrimary }}>{c.titulo}</h2>
            <div style={{ fontSize: "10.5px", color: T.textFaint, marginBottom: "12px" }}>Explicação com os números deste ativo, agora.</div>
            {CONCEITO_BLOCOS.map(([chave, rotulo]) => (
              (c[chave] || []).length > 0 && (
                <div key={chave} style={{ marginBottom: "14px" }}>
                  <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.08em", color: chave === "naoAcontece" ? T.negative : T.accent, marginBottom: "6px" }}>{rotulo}</div>
                  {c[chave].map((p, i) => (
                    <p key={i} style={{ margin: "0 0 8px", fontSize: "13.5px", lineHeight: 1.6, color: T.textSecondary }}>{p}</p>
                  ))}
                </div>
              )
            ))}
            {/* VEJA TAMBÉM. Os conceitos deste app se explicam em cadeia —
                gatilho precisa de R, R precisa de stop. Encadear aqui dentro
                evita encher o card de "?" (o inventário conta 18 afirmações) e
                mantém a pessoa no fio do raciocínio em vez de mandá-la caçar. */}
            {(c.veja || []).length > 0 && didatica && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "7px", margin: "2px 0 14px" }}>
                {c.veja.map((vid) => {
                  const alvo = ((didatica.conceitos || []).find((x) => x && x.id === vid));
                  if (!alvo) return null;
                  return (
                    <button key={vid} onClick={() => onTrocar(vid)}
                      style={{ fontSize: "11.5px", padding: "8px 12px", minHeight: "36px", borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>
                      {alvo.titulo} →
                    </button>
                  );
                })}
              </div>
            )}
            {/* ASSISTENTE (Fase 4) — a camada PAGA, dentro da folha: é aqui
                que a pessoa já está com a dúvida, e o snapshot é o mesmo que
                ancorou a explicação. Fica atrás de um toque para o custo ser
                sempre uma escolha, nunca um efeito de abrir a tela. */}
            {didatica && didatica.assistente && <AssistenteBox cid={cid} dados={dados} setor={setor} />}
            <button onClick={onClose} style={{ width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 800, fontSize: "13px" }}>Entendi</button>
          </>
        )}
      </div>
    </div>
  );
}

// ---- O PET: mascote do assistente (referência: pet do Codex / Duo) --------
// A voz mora em `./pet/vozBoris.js` — web/PWA usa `speechSynthesis`; o app
// nativo Capacitor usa o plugin de TTS nativo (WKWebView não confia no
// `speechSynthesis`, ver cabeçalho de `Boris.jsx`). Regras herdadas da casa:
// o que o pet FALA é frase pronta do servidor (/api/pet/resumo — lei do
// vocabulário); a LLM continua opt-in atrás do resumo grátis; Operador não
// tem pet (mesmo isolamento da via proativa).

// A coruja: Boris (CSS puro, ver web/src/pet/Boris.jsx) — piscar, respiração,
// boca sincronizada com a fala e olhar que segue, tudo dirigido por ref.

// O FAB do pet: presença permanente e discreta na Watchlist do Estudo. Ele
// NUNCA abre folha sozinho — o único one-shot proativo do app continua sendo
// o do gatilho (decisão da spec: dois espontâneos viram ruído).
function PetFab({ onOpen }) {
  // Decisão do Alex (2026-08-08): o Bóris aparece INTEIRO e SEM BOLHA. Antes
  // era um avatar circular — botão de 54px com fundo, borda e sombra, e a cena
  // do Boris (490×655) ampliada e deslocada pra cima para mostrar só a cabeça.
  // Agora o corpo inteiro cabe no MESMO espaço reservado: a proporção manda na
  // altura (54px de altura ⇒ 40px de largura), e o botão continua 54×54 para
  // não encolher a área de toque abaixo do mínimo de 44px do iOS.
  // A sombra saiu do círculo e foi para a SILHUETA (drop-shadow segue o
  // recorte do PNG): não é bolha, é o que separa a coruja do conteúdo quando
  // ela passa por cima de um card claro.
  return (
    <button onClick={onOpen} aria-label="Abrir o assistente Boris+"
      style={{ position: "fixed", right: "14px", bottom: "92px", zIndex: 60, width: "54px", height: "54px", borderRadius: 0, border: "none", background: "transparent", padding: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
      {/* Decisão do Alex (2026-08-08): o FAB ANIMA. Sem `reduced` ele pisca,
          respira e faz as quebras de ociosidade — é o assistente sinalizando
          que está vivo e à mão. O do título continua `reduced`: lá a coruja é
          marca, e movimento permanente no cabeçalho competiria com o conteúdo.
          Um laço de animação, não dois. */}
      <div aria-hidden style={{ lineHeight: 0, filter: "drop-shadow(0 3px 6px rgba(0,0,0,0.45))" }}>
        <Boris size={40} />
      </div>
    </button>
  );
}

// A folha do pet, em DOIS estágios com custos diferentes: o resumo
// determinístico (grátis, para todo mundo — inclusive anônimo) e a pergunta
// livre (LLM, exige conta, teto do assistente). O botão "ouvir" lê o resumo
// com a voz do sistema; sem voz no aparelho, o texto continua inteiro — a
// voz é conforto, nunca dependência.
// qa/audit-2026-08-08 (Fase 1): o resumo automático (parágrafo determinístico
// lido antes de qualquer interação) saiu como superfície principal — o Alex
// achou que "não fazia muito sentido" abrir a folha e primeiro ter que ler
// (ou mandar ler em voz alta) um texto antes de poder perguntar algo. No
// lugar: a folha abre DIRETO no chat, com 2-3 perguntas sugeridas (vindas do
// MESMO `/api/pet/resumo`, que segue existindo — só o campo `perguntas` é
// novo) como chips clicáveis no estado vazio da conversa. `fala`/`itens`
// continuam chegando (mercado ainda usa `itens` como snapshot da LLM) — só
// pararam de ser TEXTO renderizado. Voz: como não há mais um parágrafo fixo
// para "ouvir", a leitura em voz alta passa a ser por RESPOSTA do chat (já
// existia em BorisChat via falarTexto) — nenhum mecanismo de voz novo.
function PetSheet({ onClose, didatica, tela, snapshot }) {
  // F4: qual aba o pet está explicando — "mercado" se ninguém disser (mesmo
  // comportamento de antes, quando só existia essa tela).
  const telaAtual = tela || "mercado";
  const [r, setR] = useState(null);
  const [erro, setErro] = useState(false);
  const borisRef = useRef(null);
  useEffect(() => {
    let alive = true;
    setR(null); setErro(false);
    store.petResumo(telaAtual)
      .then((res) => { if (alive) setR(res); })
      .catch(() => { if (alive) setErro(true); });
    // fechar/desmontar CALA a voz — coruja falando sozinha atrás de outra
    // tela é exatamente o tipo de fantasma que não pode existir.
    return () => { alive = false; calarVoz(); };
  }, [telaAtual]);
  return (
    <div onClick={() => { calarVoz(); onClose(); }} role="dialog" aria-label="Assistente Boris+"
      style={{ position: "fixed", inset: 0, zIndex: 86, background: T.scrim, display: "flex", alignItems: "flex-end" }}>
      <div onClick={(e) => e.stopPropagation()}
        style={{ width: "100%", maxHeight: "82vh", overflowY: "auto", background: T.bgPanel, borderRadius: "18px 18px 0 0", padding: "16px 16px 22px", boxSizing: "border-box" }}>
        <div aria-hidden style={{ width: "44px", height: "4px", borderRadius: "999px", background: T.borderSubtle, margin: "0 auto 12px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "12px" }}>
          {/* `flex: none` não é enfeite: o Boris desenha a cena em posição
              ABSOLUTA dentro da própria raiz, então quando o flex encolhe essa
              raiz (aqui ia de 72px para 42px, espremida pelo texto ao lado) a
              coruja NÃO acompanha — ela transborda e cai por cima do título.
              Mesmo cuidado do FAB e da tela de login. */}
          <div style={{ flex: "none", lineHeight: 0 }}><Boris ref={borisRef} size={72} /></div>
          <div>
            <div style={{ fontSize: "16px", fontWeight: 800, color: T.textPrimary }}>Converse com o Boris</div>
            <div style={{ fontSize: "11.5px", color: T.textFaint, marginTop: "2px" }}>Ele já sabe o que esta tela mostra — sem custo pra perguntar o óbvio, e sem ordem de compra.</div>
          </div>
        </div>
        {!r && !erro && <div className="sk" style={{ height: "56px", width: "100%", borderRadius: "10px" }} />}
        {erro && (
          <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
            Não consegui preparar o contexto desta tela agora. Os cards continuam valendo.
          </div>
        )}
        {r && r.ligada === false && (
          <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
            A camada de explicações está desligada no momento.
          </div>
        )}
        {r && r.ligada && (
          didatica && didatica.assistente ? (
            // F4: o formato de `pet:mercado` NÃO muda (itens vêm da própria
            // resposta do resumo, como sempre); as outras 6 telas usam o
            // snapshot que o App já montou a partir do MESMO view-model que
            // a tela renderiza (ctx/data — nunca raspagem de tela).
            <BorisChat key={telaAtual}
              tela={"pet:" + telaAtual}
              snapshot={telaAtual === "mercado" ? { itens: (r.itens || []) } : (snapshot || {})}
              sugestoes={r.perguntas || []}
              borisRef={borisRef} falarTexto={falarTexto} calarVoz={calarVoz} />
          ) : (
            <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
              O chat com o Boris está desativado no momento.
            </div>
          )
        )}
      </div>
    </div>
  );
}

// F1: badge do TIMING no card do ativo. Consulta /api/timing (determinístico,
// O(1) no servidor — plano diário × barra 15m FECHADA; zero fetch/LLM) e só
// ocupa espaço quando há plano a vigiar: sem_plano é silêncio, não ruído.
// Honestidade do dado: mostra a hora da barra fechada (asOf) e as ressalvas
// do backend (atraso ~15 min do feed; lacuna na série).
// ELEIÇÃO DE INSTÂNCIA para a via proativa. O AtivoCard renderiza por ticker e
// a watchlist padrão tem 6: os seis montam juntos, todos leem "ainda não viu",
// e sem isto ou a folha abre seis vezes ou uma corrida decide qual abre.
// O primeiro badge que chega ao efeito vira o DONO e é o único que pode abrir;
// os demais ficam só com a afordância permanente. JS é single-threaded, então
// a eleição é determinística — não é heurística de tempo.
//
// Por que não amarrar no card EXPANDIDO (que seria a instância óbvia): `expanded`
// só liga depois de uma análise de IA (`A.analyze`), que exige modelo configurado
// e custa dinheiro. A via proativa ficaria inalcançável justamente para o
// iniciante absoluto que ela existe para atender.
const _proativoDono = { t: null };

// O push do gatilho abre o app com um ativo específico em mente. Sem esta
// reserva, a eleição cairia no primeiro badge cuja rede responder (quase sempre
// o primeiro da watchlist) e a pessoa — que acabou de ler "BBAS3" na tela de
// bloqueio — receberia a explicação com os números de OUTRO ativo, gastando a
// única chance proativa que existe.
function reservarDonoProativo(t) { if (t) _proativoDono.t = t; }

// Camada de entendimento (`didatica`, `vistos`, `proativo`, `A`): a afordância
// permanente é o "?" no rótulo — o mesmo gesto de todos os conceitos.
function TimingBadge({ t, operador, didatica, vistos, proativo, A, dadosDoCard, onDadosTiming }) {
  const [r, setR] = useState(null);
  const proativoFeitoRef = useRef(false);
  useEffect(() => {
    let alive = true;
    setR(null);
    store.timing(t)
      .then((res) => {
        if (!alive) return;
        setR(res);
        // Devolve os números do PLANO ao card. Sem isto, o bundle do card não
        // teria `entrada` e seguir o "veja também" da confluência até o
        // gatilho entregaria o conceito sem o preço combinado — texto de
        // manual no lugar da explicação ancorada. Dispara uma vez por busca.
        if (onDadosTiming && res && res.entrada != null) {
          onDadosTiming({ entrada: res.entrada, stop: res.stop, estado: res.estado,
                          // Risco do PLANO (entrada − stop). É o número certo
                          // para explicar stop e R: o da posição (`avg − stop`)
                          // mede outra coisa e fica negativo com stop no lucro.
                          riscoPorAcao: res.riscoPorAcao,
                          distancia: res.distancia, distanciaEmR: res.distanciaEmR,
                          excedenteEmR: res.excedenteEmR, asOf: res.asOf });
        }
      })
      .catch(() => { /* badge é best-effort: sem timing, o card segue inteiro */ });
    return () => { alive = false; };
  }, [t, operador]);

  // DOIS gates, não um. `timing.avaliar` monta entrada/stop/lado ANTES de
  // decidir o estado, então fora do pregão o `sem_dado` volta COM os números do
  // plano do dia. Amarrar a afordância permanente ao estado vivo apagava a
  // explicação das 18h às 10h — justamente quando a pessoa navega com calma.
  // O conceito "gatilho" não deixa de ser explicável porque o mercado fechou.
  const temPlano = !!r && r.entrada != null;
  const estadoVivo = !!r && ["armado", "gatilho", "esticado"].includes(r.estado)
    && !r.foraDoPregao && !r.barraDeOutroDia;
  const didaticaOk = !!(didatica && didatica.ligada) && temPlano;
  // `estado` viaja junto porque `excedenteEmR` volta em DOIS estados
  // (gatilho e esticado) que pedem leituras OPOSTAS — sem ele, o texto diria
  // "movimento esticado, não persiga" no instante em que a condição valeu.
  // Sem estado vivo, os parágrafos por estado somem no backend e sobra a
  // definição + os números + a idade do dado: a leitura certa com o mercado
  // fechado, sem nenhuma linha de código a mais.
  // UM bundle: o do card por baixo, o do timing por cima. Sem a fusão, seguir
  // o "veja também" da confluência até o gatilho entregaria o conceito sem
  // `entrada`, e o caminho inverso entregaria o stop sem `precoAtual` — a
  // ancoragem quebrando justamente no encadeamento. `entrada`/`stop` do PLANO
  // (timing) prevalecem sobre os da posição: são o que o card está afirmando.
  // `hora`/`asOf` entram no bundle porque o setor "timing" abre o gatilho e a
  // cadeia "veja também" leva à barra15m — sem eles o elo entregaria o
  // conceito da barra sem o carimbo que o ancora.
  const horaDados = typeof r?.asOf === "string" && r.asOf.includes(" ")
    ? { hora: r.asOf.split(" ")[1].slice(0, 5), asOf: r.asOf } : {};
  const dados = temPlano ? {
    ...(dadosDoCard || {}),
    ticker: t, entrada: r.entrada, stop: r.stop, ...horaDados,
    ...(estadoVivo ? {
      estado: r.estado, distancia: r.distancia,
      distanciaEmR: r.distanciaEmR, excedenteEmR: r.excedenteEmR,
    } : {}),
  } : null;

  useEffect(() => {
    // Via proativa: UMA vez, numa instância só, e só no Estudo (o Operador não
    // recebe camada didática proativa — decisão fechada da spec).
    // `proativo` já carrega "nenhum outro overlay aberto": a folha é one-shot
    // POR CONCEITO, para sempre. Abrir sob o tour ou sob o portão de abertura
    // queimaria o tiro único sem ninguém ler nada. Aqui a regra é ADIAR — o
    // efeito reroda quando a tela ficar livre, e a estreia se preserva.
    if (!proativo || operador || proativoFeitoRef.current) return;
    if (!didaticaOk || !estadoVivo || !A || (vistos || []).includes("gatilho")) return;
    if (_proativoDono.t && _proativoDono.t !== t) return;   // outro card já é o dono
    _proativoDono.t = t;
    proativoFeitoRef.current = true;
    A.openConceito("gatilho", dados);
    A.marcarConceitoVisto("gatilho");
  }, [proativo, operador, didaticaOk, estadoVivo, vistos, A, dados, t]);

  if (!r || !TIMING_STYLE[r.estado]) return null;
  const variante = r.foraDoPregao ? "fora_pregao" : r.barraDeOutroDia ? "aguardando_barra" : r.estado;
  const [cor, bg, rotOp, rotEdu] = TIMING_STYLE[variante];
  const hora = typeof r.asOf === "string" && r.asOf.includes(" ") ? r.asOf.split(" ")[1].slice(0, 5) : "";
  const emR = (x) => x.toFixed(1).replace(".", ",") + "R";
  const nivel = operador ? "gatilho" : "nível";
  return (
    // Afordância PERMANENTE: segurar o badge abre o conceito do gatilho — o
    // alvo é o próprio bloco que afirma o estado, não um "?" ao lado dele.
    // Exige só o PLANO (`didaticaOk`): fora do pregão a explicação continua
    // alcançável, com a leitura de mercado fechado que o backend já serve.
    <SetorAlvo setorId="timing" dados={dados} rotulo={"o " + nivel} A={A} didatica={didatica}
      ativo={didaticaOk}
      style={{ marginTop: "9px", padding: "8px 11px", borderRadius: "9px", background: bg, border: `1px solid ${T.borderFaint}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
        {/* termo-âncora do setor: o sublinhado pontilhado É a indicação */}
        <span style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.05em", color: cor, ...(didaticaOk ? SUBLINHADO : {}) }}>{operador ? rotOp : rotEdu}</span>
        {hora && (
          // "barra de 15 minutos" e o atraso do feed são o conceito que mais
          // produz erro de leitura em iniciante — o carimbo é o setor MAIS
          // INTERNO do badge: o dedo nele explica a barra, fora dele o gatilho.
          <SetorAlvo setorId="barra" rotulo="a barra de 15 minutos" A={A} didatica={didatica}
            dados={{ ...(dados || dadosDoCard || {}), ticker: t, hora, asOf: r.asOf }}
            style={{ display: "inline-flex", alignItems: "center" }}>
            <span style={{ fontSize: "10px", color: T.textFaint, fontFamily: MONO, ...SUBLINHADO }}>
              {/* barra de outro dia: a hora sozinha ("16:45") esconde que o dado é
                  do pregão anterior — aqui a data vem junto. */}
              {r.barraDeOutroDia ? `última barra ${r.asOf}` : `barra 15m de ${hora}`}
            </span>
          </SetorAlvo>
        )}
        {r.estado === "armado" && r.distanciaEmR != null && (
          <span style={{ fontSize: "10px", color: T.textMuted, fontFamily: MONO }}>a {emR(r.distanciaEmR)} do {nivel}</span>
        )}
        {(r.estado === "gatilho" || r.estado === "esticado") && r.excedenteEmR != null && (
          <span style={{ fontSize: "10px", color: T.textMuted, fontFamily: MONO }}>+{emR(r.excedenteEmR)} além do {nivel}</span>
        )}
      </div>
      <div style={{ fontSize: "11.5px", color: T.textSecondary, marginTop: "4px", lineHeight: 1.45 }}>{r.frase}</div>
      {Array.isArray(r.ressalvas) && r.ressalvas.length > 0 && (
        <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "4px", lineHeight: 1.4 }}>{r.ressalvas.join(" ")}</div>
      )}
    </SetorAlvo>
  );
}

// v2 (ADR-003/004/005) — UM contrato de opção, dentro do accordion (só 1
// aberto por vez — decisão do painel: corta mais altura que esconder o
// ativo). Os 5 campos são os que a lente técnica marcou como carregando
// informação (não ruído) para quem está aprendendo; gregas completas e IV
// vs HV ficam de fora desta camada por decisão de escopo (proposta §2).
function OpcaoContrato({ c, cur, chain, isOpen, onToggle, sustains, pos, onBuy, onSell, busy }) {
  const premio = c.lastPrice;
  const custoTotal = typeof premio === "number" ? premio * 100 : null;
  const breakeven = c.breakeven;
  const distPct = typeof breakeven === "number" && cur ? ((breakeven - cur) / cur) * 100 : null;
  const liq = c.liquidity || {};
  const liqLabel = (liq.score || 0) >= 55 ? ["NEGOCIÁVEL", T.positive, T.positiveTint10]
    : (liq.score || 0) >= 30 ? ["DIFÍCIL", T.accent, T.accentTint10] : ["SEM MERCADO", T.negative, T.negativeTint10];
  const thetaSemanaPct = c.blackScholes && typeof c.blackScholes.theta === "number" && custoTotal
    ? Math.abs((c.blackScholes.theta * 7 * 100 / custoTotal) * 100) : null;
  const bloqueado = !chain || chain.providerStatus !== "ok"; // ADR-004
  return (
    <div style={{ borderTop: `1px solid ${T.borderFaint}` }}>
      <div onClick={onToggle} role="button" tabIndex={0} style={{ padding: "9px 0", display: "flex", justifyContent: "space-between", alignItems: "baseline", cursor: "pointer" }}>
        <span style={{ fontFamily: MONO, fontWeight: 800, fontSize: "12.5px" }}>
          <span style={{ color: c.optionType === "call" ? T.positive : T.negative }}>{c.optionType === "call" ? "CALL" : "PUT"}</span> {c.contractSymbol} · strike {price(c.strike)}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700 }}>{typeof premio === "number" ? "R$ " + price(premio) : "—"}</span>
          <span aria-hidden style={{ color: T.textFaint, fontSize: "10px", display: "inline-block", transform: isOpen ? "rotate(180deg)" : "none" }}>▾</span>
        </span>
      </div>
      {isOpen && (
        <div style={{ paddingBottom: "11px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 14px", fontSize: "11px" }}>
            <div style={{ color: T.textFaint }}>Custo (100 cotas)</div>
            <div style={{ textAlign: "right", fontWeight: 700, color: T.textSecondary, fontFamily: MONO }}>{custoTotal != null ? "R$ " + price(custoTotal) + " — risco máximo" : "—"}</div>
            <div style={{ color: T.textFaint }}>Até onde (breakeven)</div>
            <div style={{ textAlign: "right", fontWeight: 700, color: T.textSecondary, fontFamily: MONO }}>{breakeven != null ? "R$ " + price(breakeven) + (distPct != null ? " (" + (distPct >= 0 ? "+" : "") + distPct.toFixed(1) + "%)" : "") : "—"}</div>
            <div style={{ color: T.textFaint }}>Até quando</div>
            <div style={{ textAlign: "right", fontWeight: 700, color: T.textSecondary, fontFamily: MONO }}>{c.daysToExpiration != null ? c.daysToExpiration + " dias" : "—"}{chain && chain.expiration ? " · vence " + chain.expiration.split("-").reverse().join("/") : ""}</div>
            <div style={{ color: T.textFaint }}>Tendência sustenta?</div>
            <div style={{ textAlign: "right", fontWeight: 700, fontFamily: MONO, color: sustains == null ? T.textFaint : sustains ? T.positive : T.negative }}>{sustains == null ? "indefinido" : sustains ? "Sim" : "Não"}</div>
          </div>
          <PlanRuler
            marks={[typeof c.strike === "number" && { v: c.strike, color: T.textFaint }, typeof breakeven === "number" && { v: breakeven, color: T.accent }].filter(Boolean)}
            cur={cur} curLabel={cur != null ? "agora " + price(cur) : null}
            legend={[{ k: "STRIKE", v: c.strike }, { k: "AGORA", v: cur }, { k: "BREAKEVEN", v: breakeven, color: T.accent }]}
          />
          <div style={{ marginTop: "9px", fontSize: "10.5px", color: T.textMuted, display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
            <span style={{ padding: "2px 7px", borderRadius: "6px", fontSize: "9.5px", fontWeight: 800, background: liqLabel[2], color: liqLabel[1] }}>{liqLabel[0]}</span>
            {liq.spreadPct != null && <span>spread {liq.spreadPct.toFixed(0)}%</span>}
            {thetaSemanaPct != null && <span>· custo de esperar: ~{thetaSemanaPct.toFixed(1)}% do prêmio/semana</span>}
          </div>
          <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "8px", lineHeight: 1.5 }}>
            Perder 100% do prêmio é o resultado comum desta simulação, não uma exceção. Conteúdo educacional, dinheiro simulado — não é recomendação de investimento.
          </div>
          {pos ? (
            <div style={{ marginTop: "9px" }}>
              <div style={{ fontSize: "11px", color: T.textSecondary, marginBottom: "6px" }}>Em carteira · {pos.qty} cotas · prêmio médio R$ {price(pos.avg)}</div>
              <button onClick={onSell} disabled={busy || bloqueado} style={{ width: "100%", minHeight: "38px", borderRadius: "9px", border: `1px solid ${T.negative}`, background: "transparent", color: T.negative, fontWeight: 800, fontSize: "12px" }}>
                {busy ? "Vendendo…" : "Vender posição"}
              </button>
            </div>
          ) : (
            <button onClick={onBuy} disabled={busy || bloqueado || custoTotal == null} style={{ marginTop: "9px", width: "100%", minHeight: "40px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "12.5px" }}>
              {busy ? "Comprando…" : bloqueado ? "Indisponível — cotação de opções degradada" : "Comprar — " + (custoTotal != null ? "R$ " + price(custoTotal) : "…") + " (100 cotas)"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// v2 (ADR-003/004/005) — linha colapsada + painel expandido ("A acoplado").
// Gate de descobribilidade: só existe se `/api/options/gate` confirmar
// liquidez (chamado 1x por card em AtivoCard, best-effort). A cadeia completa
// só é buscada quando o usuário abre — zero fetch novo por padrão (proposta §5).
function OpcoesCamada({ t, cur, open, onToggle, chain, chainLoading, opContract, setOpContract, opShowAll, setOpShowAll, myPositions, decColor, onBuy, onSell, busy }) {
  const contratos = chain && chain.providerStatus === "ok"
    ? [...(chain.calls || []), ...(chain.puts || [])].sort((a, b) => Math.abs((a.strike || 0) - (cur || 0)) - Math.abs((b.strike || 0) - (cur || 0)))
    : [];
  const visiveis = opShowAll ? contratos : contratos.slice(0, 2);
  // Princípio 5/9: opção nunca contradiz a leitura do ativo — sem leitura
  // clara (decColor neutro), "indefinido" em vez de forçar Sim/Não.
  const sustains = (optionType) => decColor === T.positive ? optionType === "call" : decColor === T.negative ? optionType === "put" : null;
  const posFor = (id) => myPositions.find((p) => p.id === id);
  return (
    <div>
      <div onClick={onToggle} role="button" tabIndex={0} style={{ marginTop: "11px", paddingTop: "10px", borderTop: `1px solid ${T.borderFaint}`, display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}>
        <span style={{ fontSize: "12px", color: T.textSecondary, display: "flex", alignItems: "center", gap: "7px" }}>
          <span style={{ color: T.accent }}>⚡</span> {open ? "opções de " + t : "opções líquidas disponíveis"}
        </span>
        <span aria-hidden style={{ color: T.textFaint, fontSize: "11px", display: "inline-block", transform: open ? "rotate(180deg)" : "none" }}>▾</span>
      </div>
      {!open && <div style={{ marginTop: "6px", fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>Toque para ver — só compra a seco (1 perna), risco = prêmio pago.</div>}
      {open && (
        <div style={{ marginTop: "10px", padding: "2px 12px", borderRadius: "11px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
          {chainLoading && <div style={{ padding: "12px 0", fontSize: "11.5px", color: T.textFaint }}>Carregando cadeia de opções…</div>}
          {!chainLoading && chain && chain.providerStatus !== "ok" && (
            <div style={{ padding: "12px 0", fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>{chain.warning || "Cotação de opções indisponível no momento. Tente novamente em alguns minutos."}</div>
          )}
          {!chainLoading && chain && chain.providerStatus === "ok" && contratos.length === 0 && (
            <div style={{ padding: "12px 0", fontSize: "11.5px", color: T.textFaint }}>Nenhum contrato retornado para este vencimento.</div>
          )}
          {visiveis.map((c) => (
            <OpcaoContrato key={c.contractSymbol} c={c} cur={cur} chain={chain}
              isOpen={opContract === c.contractSymbol} onToggle={() => setOpContract(opContract === c.contractSymbol ? null : c.contractSymbol)}
              sustains={sustains(c.optionType)} pos={posFor(c.contractSymbol)}
              onBuy={() => onBuy(c)} onSell={() => onSell(c.contractSymbol)} busy={busy === c.contractSymbol} />
          ))}
          {!opShowAll && contratos.length > 2 && (
            <button onClick={() => setOpShowAll(true)} style={{ width: "100%", padding: "9px 0", background: "transparent", border: "none", borderTop: `1px dashed ${T.borderFaint}`, color: T.textFaint, fontSize: "10.5px", fontWeight: 700 }}>
              Ver mais {contratos.length - 2} contrato{contratos.length - 2 > 1 ? "s" : ""} ▾
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// qa/49 (v11): CARD ÚNICO DO ATIVO — fonte única de renderização em todas as
// abas (watchlist, radar, posições, home). Recebe um view-model normalizado
// (vm) + contexto; o núcleo (identidade, manchete única, chips de análise) é
// idêntico em todo o sistema. Extraído do card da watchlist.
function AtivoCard({ vm, contexto = "watchlist", children }) {
  const { t, q, an, name, chColor, sc, pos, cur, pnl, pnlPct, rrPos, diasPos, pctCapPos, kp, fscore, decM, decColor, decBg, os, buyMeta, operador, quotesLoading, expanded, opsOpen, opsSpark, onToggleOps, A, cp, data, didatica, overlayLivre } = vm;
  const chip = (label, value, col, explicavel) => (
    // `explicavel` põe o pontilhado no RÓTULO do chip — a indicação da camada
    // de entendimento (toque abre o conceito; o setor envolve o chip).
    <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}><span style={explicavel ? SUBLINHADO : undefined}>{label}</span> <b style={{ fontWeight: 800, color: col || T.textPrimary }}>{value}</b></span>
  );

  // v2 (ADR-003/004/005) — camada de opções: self-contained no AtivoCard (o
  // mesmo card serve Watchlist e Radar; nenhuma das duas telas precisa de
  // código novo). "A acoplado": 1 controle só — abrir opções encolhe a
  // identidade do ativo para uma espinha persistente (números, não selo) e
  // fecha a cauda (posição/histórico/CTA), que voltaria a competir por altura.
  const [opOpen, setOpOpen] = useState(false);
  const [opGate, setOpGate] = useState(null);
  const [opChain, setOpChain] = useState(null);
  const [opChainLoading, setOpChainLoading] = useState(false);
  const [opContract, setOpContract] = useState(null);
  const [opShowAll, setOpShowAll] = useState(false);
  const [opBusy, setOpBusy] = useState(null);

  useEffect(() => {
    let alive = true;
    setOpGate(null);
    store.optionsGate(t).then((r) => { if (alive) setOpGate(r); }).catch(() => { /* gate é best-effort: sem ele, a linha só não aparece */ });
    return () => { alive = false; };
  }, [t]);

  const toggleOp = () => {
    const next = !opOpen;
    setOpOpen(next);
    if (next && !opChain && !opChainLoading) {
      setOpChainLoading(true);
      store.optionsChain(t).then((r) => setOpChain(r)).catch(() => setOpChain({ providerStatus: "degraded", calls: [], puts: [] })).finally(() => setOpChainLoading(false));
    }
  };

  // UM bundle de dados para TODOS os conceitos deste card. Bundles parciais
  // por dot pareciam mais enxutos e quebravam o encadeamento: seguir "veja
  // também" da confluência para o stop entregava o conceito sem `stop` nem
  // `precoAtual`, e a pessoa recebia texto de manual — a Decisão 3 da spec
  // falhando justamente no caminho construído para ela. O superset é seguro
  // porque o `campos` de cada conceito é allowlist no backend: o que não
  // serve àquele conceito é descartado lá, não aqui.
  const riscoDaPosicao = (pos && pos.stop != null && pos.avg != null)
    ? +(pos.avg - pos.stop).toFixed(2) : null;   // negativo (stop no lucro) o backend recusa
  // Os números do PLANO chegam do TimingBadge (que já os busca) — assim o
  // bundle é um só de verdade e o encadeamento não perde a ancoragem.
  const [dadosTiming, setDadosTiming] = useState(null);
  const dadosDoCard = {
    ticker: t, precoAtual: cur,
    stop: pos ? pos.stop : null, alvo: pos ? pos.alvo : null,
    riscoPorAcao: riscoDaPosicao, rr: rrPos,
    confluencia: sc ? sc.confluencia : null, melhorSetup: sc ? sc.melhorSetup : null,
    fundamento: fscore || null,
    ...(dadosTiming || {}),   // entrada/stop/estado do plano prevalecem
  };
  const myOptionPositions = ((data && data.optionPositions) || []).filter((p) => p.underlying === t);
  const doBuyOption = async (contrato) => {
    setOpBusy(contrato.contractSymbol);
    try { await A.buyOption(t, contrato, opChain.expiration, buyMeta); }
    finally { setOpBusy(null); }
  };
  const doSellOption = async (contractId) => {
    setOpBusy(contractId);
    try { await A.sellOption(contractId); }
    finally { setOpBusy(null); }
  };

  return (
            // id: alvo do scroll quando o usuário chega por um toque no push.
            <div key={t} id={"ativo-" + t} style={{ ...card, padding: "14px 15px" }}>
              {opOpen ? (
                // ESPINHA: o que sustenta a checagem "opção respeita a leitura do
                // ativo" (Princípio 5/9) continua CONFERÍVEL — números, não um selo.
                <div style={{ padding: "9px 10px", borderRadius: "9px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", fontSize: "12px", flexWrap: "wrap", gap: "6px" }}>
                    <span><b style={{ fontFamily: MONO, fontSize: "13px" }}>{t}</b> {q.error ? "—" : "R$ " + price(q.price)} {!q.error && <span style={{ color: T.textFaint }}>({pct(q.change)})</span>}</span>
                    {(kp.direcao || kp.conviccao) && <span style={{ color: T.textSecondary, fontWeight: 700, fontSize: "11px" }}>{[kp.direcao, kp.conviccao].filter(Boolean).join(" · ")}</span>}
                  </div>
                  <div style={{ marginTop: "6px", fontSize: "10.5px", color: T.textMuted, display: "flex", gap: "10px", flexWrap: "wrap", fontFamily: MONO }}>
                    {pos && pos.stop != null && <span>stop <b style={{ color: T.textSecondary }}>{price(pos.stop)}</b></span>}
                    {pos && pos.alvo != null && <span>alvo <b style={{ color: T.textSecondary }}>{price(pos.alvo)}</b></span>}
                    {decM && <span>veredito <b style={{ color: decColor, fontFamily: "inherit" }}>{decM}</b></span>}
                  </div>
                </div>
              ) : (<>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "7px", flexWrap: "wrap" }}>
                    <span style={{ fontFamily: MONO, fontWeight: 800, fontSize: "16px", letterSpacing: "0.02em" }}>{t}</span>
                    {pos ? <PosPill qty={pos.qty} /> : null}
                  </div>
                  <div style={{ color: T.textMuted, fontSize: "12px", marginTop: "3px" }}>{name}</div>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "9px" }}>
                  <div style={{ textAlign: "right", fontFamily: MONO, minWidth: "72px" }}>
                    {q.price == null && !q.error && quotesLoading ? (
                      <>
                        <div className="sk" style={{ height: "18px", width: "70px", marginLeft: "auto" }} />
                        <div className="sk" style={{ height: "11px", width: "46px", marginLeft: "auto", marginTop: "6px" }} />
                      </>
                    ) : (
                      <>
                        <div style={{ fontSize: "16px", fontWeight: 700 }}>{q.error ? "—" : "R$ " + price(q.price)}</div>
                        <div style={{ fontSize: "12px", fontWeight: 700, color: q.error ? T.textFaint : chColor }}>{q.error ? "sem cotação" : pct(q.change)}</div>
                      </>
                    )}
                  </div>
                  {/* qa/49 (v11): o mini-gráfico vira o ACESSO ao candlestick, à direita do preço */}
                  <button onClick={() => A.openTech && A.openTech(t)} disabled={q.error} aria-label="Abrir gráfico de velas" style={{ background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "9px", padding: "6px 7px 4px", display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
                    {sc && Array.isArray(sc.spark) && sc.spark.length > 1 ? <Sparkline data={sc.spark} width={44} height={18} /> : <span aria-hidden style={{ fontSize: "14px" }}>📈</span>}
                    <span style={{ fontSize: "9px", color: T.accent, fontWeight: 800 }}>velas ⤢</span>
                  </button>
                </div>
              </div>

              {/* qa/49 (v11): POSIÇÃO — resumo (em carteira · cotas · PM · resultado) */}
              {pos && (
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11.5px", padding: "6px 9px", background: T.bgBase, borderRadius: "8px", marginTop: "10px" }}>
                  <span style={{ color: T.textSecondary }}>em carteira · {pos.qty} cotas · PM {price(pos.avg)}</span>
                  {pnl != null && <span style={{ fontFamily: MONO, fontWeight: 800, color: pnl >= 0 ? T.positive : T.negative }}>{moneySigned(pnl)} · {pct(pnlPct)}</span>}
                </div>
              )}

              {/* qa/49 (v11): MANCHETE ÚNICA — decisão da mesa (o veredito do plano,
                  já conciliado por decisaoDoModo). Antes competia com o tier/COMPRAR. */}
              {decM && (
                <div style={{ marginTop: "11px", background: decBg, borderRadius: "9px", padding: "9px 11px" }}>
                  <div style={{ fontSize: "10px", letterSpacing: "0.04em", color: decColor }}>{operador ? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"}{pos ? " · você está comprado" : ""}</div>
                  <div style={{ fontSize: "17px", fontWeight: 800, color: decColor }}>{decM}</div>
                </div>
              )}

              {/* F1: TIMING DE ENTRADA logo abaixo da manchete — o estado
                  determinístico (plano diário × barra 15m fechada) em todas as
                  superfícies do card; o próprio badge se cala sem plano. */}
              {/* A via proativa vive numa superfície só (a Watchlist, onde a
                  pessoa acompanha de perto) e numa instância só — a eleição
                  está em `_proativoDono`. O Radar fica de fora: lá o card é
                  vitrine de descoberta, não lugar de parar para aprender. */}
              <TimingBadge t={t} operador={operador} didatica={didatica} A={A}
                dadosDoCard={dadosDoCard} onDadosTiming={setDadosTiming}
                proativo={contexto !== "radar" && overlayLivre}
                vistos={(data && data.config && data.config.conceitosVistos) || []} />

              {/* qa/49 (v11): ANÁLISE — indicadores unificados em chips (mesmo peso);
                  confluência e fundamento deixam de ser vereditos concorrentes. */}
              {contexto !== "radar" && (kp.direcao || (sc && sc.confluencia != null) || fscore || (sc && sc.melhorSetup)) && (
                // Setor ANALISE: segurar a linha de chips abre a confluência
                // (e a cadeia "veja também" leva ao fundamento). O chip do
                // fundamento é o setor mais interno: o dedo NELE explica o
                // fundamento direto, sem passar pela cadeia.
                <SetorAlvo setorId="analise" rotulo="a confluência" A={A} didatica={didatica}
                  dados={dadosDoCard} ativo={!!(sc && sc.confluencia != null)}
                  style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "11px" }}>
                  {kp.direcao && chip("direção", kp.direcao, (DIR_STYLE[kp.direcao] || [T.textPrimary])[0])}
                  {kp.conviccao && chip("convicção", kp.conviccao)}
                  {kp.qualidade && chip("qualidade", kp.qualidade)}
                  {sc && sc.confluencia != null && chip("confluência", (sc.confluencia || 0) + "%", T.accent, true)}
                  {fscore && (
                    <SetorAlvo setorId="fundamento" rotulo="o fundamento" A={A} didatica={didatica}
                      dados={dadosDoCard} style={{ display: "inline-flex" }}>
                      {chip("fundamento", fscore, T[SCORE_COLOR[fscore]] || T.textPrimary, true)}
                    </SetorAlvo>
                  )}
                  {sc && sc.melhorSetup && <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textMuted }}>{sc.melhorSetup}</span>}
                </SetorAlvo>
              )}
              </>)}

              {/* v2 (ADR-003/004/005): linha de opções — só existe com liquidez
                  confirmada pelo gate (1 chamada leve por card, best-effort).
                  Enquanto a fonte não devolver cadeia da B3, ela não aparece em
                  card nenhum: o estado de indisponibilidade chegou a ser exibido
                  e virou seis avisos idênticos por tela, pior que o silêncio. O
                  porquê da ausência mora no ADR-004, não no card. */}
              {opGate && opGate.liquida && (
                <OpcoesCamada
                  t={t} cur={q.price} open={opOpen} onToggle={toggleOp}
                  chain={opChain} chainLoading={opChainLoading}
                  opContract={opContract} setOpContract={setOpContract}
                  opShowAll={opShowAll} setOpShowAll={setOpShowAll}
                  myPositions={myOptionPositions} decColor={decColor}
                  onBuy={doBuyOption} onSell={doSellOption} busy={opBusy}
                />
              )}

              {/* qa/49 (v11): CAUDA por contexto — sem children, a cauda da watchlist
                  (posição no risco + histórico + CTAs); com children, a aba pluga a sua.
                  v2: fechada enquanto a camada de opções está aberta — ela reclama o
                  espaço que a identidade do ativo cedeu para a espinha. */}
              {!opOpen && (children || (<>
              {/* POSIÇÃO NO RISCO — a régua reusada do card de posições. */}
              {pos && (pos.stop != null || pos.alvo != null) && (
                <>
                  {/* A régua aparece com stop OU alvo. O setor segue o número
                      EXIBIDO: régua só com alvo É o setor "alvo" — quem armou
                      só o alvo não recebe a explicação de um stop que não está
                      no card (regra herdada do guardião da afordância antiga). */}
                  <SetorAlvo setorId={pos.stop != null ? "risco" : "alvo"}
                    rotulo={pos.stop != null ? "o stop" : "o alvo"}
                    A={A} didatica={didatica} dados={dadosDoCard}>
                    <PlanRuler
                      caption={<span style={SUBLINHADO}>POSIÇÃO NO RISCO</span>}
                      marks={[pos.stop != null && { v: pos.stop, color: T.negative }, pos.alvo != null && { v: pos.alvo, color: T.positive }].filter(Boolean)}
                      cur={cur}
                      curLabel={cur != null ? "agora " + price(cur) : null}
                      legend={[
                        { k: "STOP", v: pos.stop, color: T.negative, sub: pos.stop != null && cur > 0 ? "−" + Math.abs(((cur - pos.stop) / cur) * 100).toFixed(1) + "%" : null },
                        { k: "P. MÉDIO", v: pos.avg },
                        { k: "ALVO", v: pos.alvo, color: T.positive, sub: pos.alvo != null && cur > 0 ? "+" + Math.abs(((pos.alvo - cur) / cur) * 100).toFixed(1) + "%" : null },
                      ]}
                    />
                  </SetorAlvo>
                  {(rrPos != null || diasPos != null || pctCapPos != null) && (
                    <div style={{ display: "flex", gap: "10px", fontSize: "10.5px", color: T.textSecondary, marginTop: "9px", flexWrap: "wrap" }}>
                      {rrPos != null && (
                        <SetorAlvo setorId="r" rotulo="o R" A={A} didatica={didatica}
                          dados={dadosDoCard} style={{ display: "inline-flex" }}>
                          <span><span style={SUBLINHADO}>R:R</span> <b style={{ color: T.textPrimary, fontWeight: 700 }}>{rrPos.toFixed(1)}</b></span>
                        </SetorAlvo>
                      )}
                      {diasPos != null && <span>· {diasPos} dias</span>}
                      {pctCapPos != null && <span>· {pctCapPos.toFixed(0)}% do patrimônio</span>}
                    </div>
                  )}
                </>
              )}
              {/* FASE 2 (2.3a): linha-resumo do histórico de operações do ativo */}
              {os.n > 0 && (
                <button onClick={() => onToggleOps()} aria-expanded={!!opsOpen} style={{ marginTop: "8px", width: "100%", minHeight: "34px", padding: "7px 10px", borderRadius: "9px", border: `1px solid ${T.borderFaint}`, background: T.bgBase, color: T.textMuted, fontWeight: 700, fontSize: "11.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span>{os.n} op{os.n > 1 ? "s" : ""} · <span style={{ fontFamily: MONO, color: os.pnl >= 0 ? T.positive : T.negative }}>{pct(os.pct)} acum.</span></span>
                  <span aria-hidden>{opsOpen ? "▴" : "▾"}</span>
                </button>
              )}
              {/* FASE 2 (2.3b+c): detalhe — sparkline com ▲/▼ + tabela de operações */}
              {opsOpen && os.n > 0 && (
                <div style={{ marginTop: "8px", padding: "10px 11px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  {opsSpark ? <OpsSparkline candles={opsSpark} ops={os.ops} /> : <div className="sk" style={{ height: "44px", width: "100%" }} />}
                  <div style={{ marginTop: "8px" }}>
                    {os.ops.map((h, i) => (
                      <div key={i} style={{ display: "flex", gap: "8px", alignItems: "center", padding: "6px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", fontFamily: MONO, fontSize: "11.5px" }}>
                        <span style={{ flex: 1.5, color: T.textFaint }}>{String(h.date || "").slice(0, 10)}</span>
                        <span style={{ flex: 1, fontWeight: 800, color: h.type === "COMPRA" ? T.positive : T.negative }}>{h.type === "COMPRA" ? "▲ compra" : "▼ venda"}</span>
                        <span style={{ flex: 0.7, textAlign: "right", color: T.textSecondary }}>{h.qty}</span>
                        <span style={{ flex: 1, textAlign: "right", color: T.textSecondary }}>R$ {price(h.price)}</span>
                        <span style={{ flex: 1, textAlign: "right", fontWeight: 700, color: h.pnl == null ? T.textFaint : h.pnl >= 0 ? T.positive : T.negative }}>{h.pnl == null ? "—" : moneySigned(h.pnl)}</span>
                      </div>
                    ))}
                  </div>
                  {os.n > 0 && <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "7px" }}>Resultado realizado sobre o custo comprado — estudo, não recomendação.</div>}
                </div>
              )}

              {an.modelLabel && expanded && <div style={{ marginTop: "10px", display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 8px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textMuted, fontSize: "11px" }}>Modelo: <b style={{ color: T.textSecondary }}>{an.modelLabel}</b>{an.candlesSentToLLM ? <span>· {an.candlesSentToLLM} candles enviados</span> : null}</div>}
              {/* BLOCO C1 — CTA ÚNICO pós-análise, condicionado à LEITURA:
                  favorável → sugestão de quantidade; neutra → sem sugestão;
                  desfavorável → discreto + aviso (nunca sugerir qtd contra a leitura). */}
              {!an.loading && hasAnalysis(an) && q.price != null && (() => {
                const rec = ((an.kpis && an.kpis.recomendacao) || "").toLowerCase();
                const boa = rec.includes("alta");
                const ruim = rec.includes("baixa") || rec.includes("não operar") || rec.includes("nao operar");
                if (boa) {
                  const qs = suggestedQty(data.cash, q.price, (data.profile || {}).risco);
                  return (
                    <button onClick={() => A.openBuy(t, qs, buyMeta)} style={{ marginTop: "10px", width: "100%", minHeight: "42px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.positive}`, background: T.positiveTint10, color: T.positive, fontWeight: 800, fontSize: "12.5px" }}>
                      {cp.btnComprar} · sugestão {qs} ações
                    </button>
                  );
                }
                if (ruim) {
                  return (
                    <div style={{ marginTop: "10px" }}>
                      <div style={{ fontSize: "11px", color: T.textFaint, lineHeight: 1.5, marginBottom: "6px" }}>A leitura atual não favorece entrada — se quiser praticar mesmo assim, é modo estudo, sem sugestão de quantidade.</div>
                      <button onClick={() => A.openBuy(t, undefined, buyMeta)} style={{ width: "100%", minHeight: "38px", padding: "8px", borderRadius: "10px", border: `1px dashed ${T.borderSubtle}`, background: "transparent", color: T.textFaint, fontWeight: 700, fontSize: "12px" }}>
                        Simular mesmo assim
                      </button>
                    </div>
                  );
                }
                return (
                  <button onClick={() => A.openBuy(t, undefined, buyMeta)} style={{ marginTop: "10px", width: "100%", minHeight: "42px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700, fontSize: "12.5px" }}>
                    {cp.btnComprar}… <span style={{ color: T.textFaint, fontWeight: 600 }}>(leitura: {recDoModo((an.kpis && an.kpis.recomendacao), operador) || "neutra"})</span>
                  </button>
                );
              })()}

              {/* qa/49 (v11): KpiBlock removido — decisão virou manchete única e
                  direção/convicção/qualidade viraram chips no setor Análise. */}
              {an.loading && (
                <div style={{ marginTop: "12px" }}>
                  <SweepGauge compact label={"Analisando " + t} steps={["consultando histórico", "calculando indicadores", "IA lendo as 5 famílias"]} />
                </div>
              )}

              {/* FASE 3 (mock v2): sem análise ainda → CTA neutro de compra (o
                  contextual pós-análise já existe acima, no bloco C1) */}
              {!hasAnalysis(an) && !an.loading && (
                <button onClick={() => A.openBuy(t, undefined, buyMeta)} disabled={q.error || q.price == null} style={{ marginTop: "12px", width: "100%", minHeight: "44px", padding: "10px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>{cp.btnComprar}…</button>
              )}
              {expanded && hasAnalysis(an) && (
                <div style={{ marginTop: "11px", paddingTop: "12px", borderTop: `1px solid ${T.borderSubtle}` }}>
                  <AnalysisView an={an} />
                </div>
              )}
              {/* FASE 3 (mock v2): ações secundárias viram LINHA DE LINKS —
                  fim da pilha de botões; a compra é a única ação-bloco. */}
              <div style={{ display: "flex", gap: "14px", alignItems: "center", marginTop: "12px", paddingTop: "9px", borderTop: `1px solid ${T.borderFaint}` }}>
                <button onClick={() => A.analyze(t)} disabled={an.loading} style={{ background: "transparent", border: "none", padding: "6px 0", color: T.accent, fontSize: "11.5px", fontWeight: 800, display: "flex", alignItems: "center", gap: "5px" }}>
                  {/* qa/34: chave órfã btnAnalise finalmente ligada — "Estudar este
                      ativo" × "Plano completo" (antes: "Analisar com IA" fixo). */}
                  {an.loading ? <><Spinner size={11} color={T.accent} /> analisando…</> : (hasAnalysis(an) ? "✨ Reanalisar" : "✨ " + cp.btnAnalise)}
                </button>
                <button onClick={() => A.openTech(t)} disabled={q.error} style={{ background: "transparent", border: "none", padding: "6px 0", color: T.textMuted, fontSize: "11.5px", fontWeight: 700 }}>📈 Indicadores</button>
                {hasAnalysis(an) && (
                  <button onClick={() => A.toggleExpand(t)} aria-expanded={!!expanded} style={{ background: "transparent", border: "none", padding: "6px 0", color: T.textMuted, fontSize: "11.5px", fontWeight: 700, marginLeft: "auto" }}>
                    {expanded ? "Ocultar análise ▴" : "Ver análise ▾"}
                  </button>
                )}
              </div>
              </>))}
            </div>
  );
}

function MercadoScreen({ ctx }) {
  // FASE 2 (2.3): a aba vira WATCHLIST — ordenada PERMANENTEMENTE por
  // oportunidade (confluência do STU, melhor → pior); filtro secundário por
  // direção; histórico de operações por ativo (formatos a+b no card, c no
  // detalhe expandido). A análise N2 segue abrindo como detalhe do card.
  const { data, quotes, analysis, expanded, analysisModel, setAnalysisModel, A, quotesAt, quotesLoading, wlScan, wlScanLoading, cp } = ctx;
  const operador = (data.config && data.config.appMode) === "operador"; // qa/40: pill de decisão por modo
  const [dirFilter, setDirFilter] = useState("todos");   // todos | alta | baixa | neutro
  const [opsOpen, setOpsOpen] = useState({});            // ticker -> histórico aberto
  const [sparks, setSparks] = useState({});              // ticker -> candles (lazy)
  useEffect(() => { A.refreshWlScan(); }, []);           // eslint-disable-line react-hooks/exhaustive-deps
  const scanBy = {};
  ((wlScan && wlScan.results) || []).forEach((r) => { scanBy[r.ticker] = r; });
  const dirOf = (t) => {
    const v = ((scanBy[t] || {}).veredito || "");
    if (v === "Estudar alta") return "alta";
    if (v === "Estudar baixa") return "baixa";
    return "neutro";
  };
  const wl = [...data.watchlist]
    .sort((a, b) => ((scanBy[b] || {}).confluencia || 0) - ((scanBy[a] || {}).confluencia || 0)
      || ((scanBy[b] || {}).score_tecnico || 0) - ((scanBy[a] || {}).score_tecnico || 0)
      || a.localeCompare(b))
    .filter((t) => dirFilter === "todos" || dirOf(t) === dirFilter);
  const emCarteira = new Set((data.positions || []).map((p) => p.t));
  const toggleOps = async (t) => {
    const next = !opsOpen[t];
    setOpsOpen((x) => ({ ...x, [t]: next }));
    if (next && !sparks[t]) {
      try {
        const r = await store.technicals(t, (data.config && data.config.candlePeriod) || undefined);
        setSparks((x) => ({ ...x, [t]: (r && r.candles) || [] }));
      } catch { /* sparkline é bônus */ }
    }
  };
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", marginBottom: "6px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "2px", minWidth: 0 }}>
          <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em" }}>{cp.tituloWatchlist}</h1>
          <InfoDot onClick={A.openAbout} />
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {/* v2 (ADR-003/004/005): botão isolado removido — a camada de opções
              agora vive dentro de cada AtivoCard (linha ⚡ opções, com gate de
              liquidez), substituindo este acesso genérico (proposta §2). */}
          <IconBtn label="Atualizar cotações" onClick={A.refreshQuotes} busy={quotesLoading}>↻</IconBtn>
          <IconBtn label="Editar watchlist" onClick={A.openCatalog}>✎</IconBtn>
        </div>
      </div>
      {/* qa/34: subtítulo na voz do modo ("em estudo" × "monitorados"). */}
      <p style={{ margin: "0 0 12px", color: T.textMuted, fontSize: "13px", maxWidth: "560px", lineHeight: 1.55 }}>
        {cp.subtituloWatchlist}{quotesAt ? "  ·  cotações " + quotesAt : ""}
      </p>
      {/* FASE 2 (2.3): filtro secundário por direção — a ordenação por
          oportunidade é permanente e não compete com ordenação manual. */}
      {data.watchlist.length > 1 && (
        <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "12px", flexWrap: "wrap" }}>
          {[["todos", "Todos"], ["alta", cp.filtroAlta], ["baixa", cp.filtroBaixa], ["neutro", "Neutros"]].map(([id, label]) => (
            <button key={id} onClick={() => setDirFilter(id)} style={{ minHeight: "34px", padding: "7px 12px", borderRadius: "999px", border: `1px solid ${dirFilter === id ? T.accent : T.borderSubtle}`, background: dirFilter === id ? T.accentTint : T.bgBase, color: dirFilter === id ? T.accent : T.textMuted, fontWeight: 700, fontSize: "11.5px" }}>{label}</button>
          ))}
          {wlScanLoading && <span style={{ fontSize: "11px", color: T.textFaint }}>atualizando oportunidade…</span>}
          {!wlScanLoading && <button onClick={A.refreshWlScan} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 700, padding: "6px" }}>↻ reordenar</button>}
        </div>
      )}
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
          <div style={{ fontSize: "16px", fontWeight: 700 }}>{ctx.cp.vazioWatchlist}</div>
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
          // FASE 2 (2.3): dados de oportunidade do STU + histórico do ativo
          const sc = scanBy[t];
          const [tierDot, tierLabel] = tierOf(sc && sc.confluencia);
          const rotuloDec = decisaoDoModo(sc, operador); // qa/40: mesa mostra a decisão do plano
          const [vColor, vBg] = REC_STYLE[rotuloDec] || [T.textMuted, T.bgBase];
          const melhorSet = sc && (sc.setups || [])[0];
          const buyMeta = sc ? {
            setup: sc.melhorSetup || undefined, veredito: sc.veredito, confluencia: sc.confluencia,
            snapshotId: sc.snapshotId,
            lado: melhorSet && melhorSet.lado, gatilho: melhorSet && melhorSet.gatilho,
            invalidacao: melhorSet && melhorSet.invalidacao,
          } : undefined;
          const os = opsSummary(data.history, t);
          // qa/49 (v11): dados da posição p/ o hero (régua reusada do card de posições)
          const pos = (data.positions || []).find((p) => p.t === t);
          const cur = q.price != null ? q.price : (pos ? pos.avg : null);
          const pnl = pos && cur != null ? (cur - pos.avg) * pos.qty : null;
          const pnlPct = pos && cur != null && pos.avg > 0 ? (cur / pos.avg - 1) * 100 : null;
          const rrPos = pos && pos.stop != null && pos.alvo != null && cur != null && cur > pos.stop ? (pos.alvo - cur) / (cur - pos.stop) : null;
          const diasPos = pos ? daysSince(openedAt(data.history, t, pos)) : null;
          const patrimonio = (data.cash || 0) + (data.positions || []).reduce((s, pp) => s + pp.qty * (((quotes[pp.t] || {}).price) || pp.avg || 0), 0);
          const pctCapPos = pos && patrimonio > 0 && cur != null ? (pos.qty * cur / patrimonio) * 100 : null;
          const kp = an.kpis || {};
          const fscore = an.fundamento && an.fundamento.score;
          // manchete única: decisão do plano (scan) e, sem scan, a recomendação da IA
          const decM = rotuloDec || (kp.recomendacao ? recDoModo(kp.recomendacao, operador) : null);
          const [decColor, decBg] = REC_STYLE[decM] || [vColor, vBg];
          const chip = (label, value, col) => (
            <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "999px", background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>{label} <b style={{ fontWeight: 800, color: col || T.textPrimary }}>{value}</b></span>
          );
          return <AtivoCard key={t} vm={{ t, q, an, name, chColor, sc, pos, cur, pnl, pnlPct, rrPos, diasPos, pctCapPos, kp, fscore, decM, decColor, decBg, os, buyMeta, operador, quotesLoading, expanded: !!expanded[t], opsOpen: !!opsOpen[t], opsSpark: sparks[t], onToggleOps: () => toggleOps(t), A, cp, data, didatica: ctx.didatica, overlayLivre: ctx.overlayLivre }} contexto="watchlist" />;
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
  // FASE 2 (1.3/2.3): CENÁRIOS estruturados (conservador/moderado/agressivo)
  // com memória de cálculo — 1 toque escolhe; o Aplicar continua manual.
  const cen = r.cenarios || [];
  const [selPerfil, setSelPerfil] = useState(null);
  const chosen = cen.length ? (cen.find((c) => c.perfil === selPerfil) || cen.find((c) => c.perfil === ((data.profile || {}).risco || "moderado")) || cen[0]) : null;
  // enquanto carrega/erro, mostra a estimativa por perfil como prévia
  const stop = aguardar ? null : (chosen && chosen.stop != null ? chosen.stop : (r.stop != null ? r.stop : (fromAI ? null : est.stop)));
  const alvo = aguardar ? null : (chosen && chosen.alvo != null ? chosen.alvo : (r.alvo != null ? r.alvo : (fromAI ? null : est.alvo)));
  const why = r.explicacao || (loading ? "" : est.rationale) || "";
  const canApply = !loading && !aguardar && (stop != null || alvo != null);
  const apply = () => A.applyStopAlvoFor(t, stop != null ? stop : null, alvo != null ? alvo : null);
  return (
    <div onClick={A.closeStopAlvo} style={{ position: "fixed", inset: 0, zIndex: 55, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "480px", maxHeight: "86vh", display: "flex", flexDirection: "column", ...card, borderRadius: "14px" }}>
        <div style={{ padding: "16px 18px", borderBottom: `1px solid ${T.borderSubtle}` }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
            <div style={{ fontSize: "16px", fontWeight: 700, fontFamily: MONO }}>{t} · stop e alvo</div>
            {loading && <SweepGauge compact label="Alvo & stop com IA" steps={["ATR, suportes e resistências", "cenários por perfil", "memória de cálculo"]} />}
          </div>
          <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "4px", lineHeight: 1.5 }}>Perfil <b>{(data.profile || {}).risco || "—"}</b> · {ctx.cp.notaStopAlvo}</div>
          {/* qa/35 (P1): o hash saiu; a data dos dados é o que importa pro usuário. */}
          {r.snapshotAt && <div style={{ fontFamily: MONO, fontSize: "10.5px", color: T.textFaint, marginTop: "5px" }}>Análise baseada nos dados de {r.snapshotAt}</div>}
        </div>
        <div style={{ padding: "16px 18px", overflowY: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "10px" }}>
            <span style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: "0.04em", color: loading ? T.textMuted : aguardar ? T.textSecondary : fromAI ? T.accent : T.textSecondary }}>
              {loading ? "ANALISANDO…" : aguardar ? "SUGESTÃO: AGUARDAR" : fromAI ? "SUGESTÃO DA IA" : "ESTIMATIVA PELO PERFIL"}
            </span>
            {q.price != null && <span style={{ fontFamily: MONO, fontSize: "12px", color: T.textMuted }}>atual R$ {price(q.price)}</span>}
          </div>
          {!aguardar && cen.length > 0 && (
            <div style={{ display: "flex", gap: "7px", marginBottom: "11px" }}>
              {cen.map((c) => {
                const on = chosen && chosen.perfil === c.perfil;
                return (
                  <button key={c.perfil} onClick={() => setSelPerfil(c.perfil)} style={{ flex: 1, padding: "8px 6px", borderRadius: "10px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgBase, color: on ? T.accent : T.textSecondary, fontWeight: 800, fontSize: "11px", textTransform: "capitalize" }}>
                    {c.perfil}{c.rrDesfavoravel ? " ⚠" : ""}
                  </button>
                );
              })}
            </div>
          )}
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
          {chosen && (
            <div style={{ marginTop: "10px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.55 }}>
              {chosen.riscoRetorno != null && <span style={{ fontFamily: MONO, fontWeight: 700, color: chosen.rrDesfavoravel ? T.negative : T.textSecondary }}>R:R {chosen.riscoRetorno}{chosen.rrDesfavoravel ? " · desfavorável (fins de estudo)" : ""}</span>}
              {chosen.memoriaCalculo && <div style={{ marginTop: "4px" }}>Memória de cálculo: {chosen.memoriaCalculo}</div>}
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
  // FASE 2 (2.5): qual posição está com o histórico de análises aberto
  const [histFor, setHistFor] = useState(null);
  // FASE 3 (mock v2): edição de stop/alvo sob demanda + compras da posição
  const [editFor, setEditFor] = useState(null);
  const [comprasOpen, setComprasOpen] = useState({});
  const { data, quotes, analysis, A, goMercado, cp } = ctx;   // FASE 8B (B1)
  const byQ = (t) => quotes[t] || {};
  const m = portfolioMetrics(data.positions, quotes, data.cash);
  const positionsValue = m.posVal;
  const total = m.patr;
  const cost = m.cost;
  const openPnL = m.openPnL;
  const openPct = m.openPct;
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
        <div style={{ display: "flex", alignItems: "center", gap: "2px", minWidth: 0 }}>
          <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>{cp.tituloPortfolio}</h1>
          <InfoDot onClick={ctx.A.openAbout} />
        </div>
      </div>
      {/* qa/34: chave órfã subtituloPortfolio finalmente ligada — "carteira
          SIMULADA" × "posições com plano e risco em R". */}
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>{cp.subtituloPortfolio}</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px", margin: "16px 0 18px" }}>
        {kpi("PATRIMÔNIO TOTAL", money(total), T.textPrimary)}
        {kpi("RESULTADO ABERTO", moneySigned(openPnL), openPnL >= 0 ? T.positive : T.negative, pct(openPct), openPnL >= 0 ? T.positive : T.negative)}
        {kpi("CAIXA DISPONÍVEL", money(data.cash), T.textMuted)}
        {kpi("EM POSIÇÕES", money(positionsValue), T.textMuted)}
      </div>

      {data.positions.length === 0 && (
        <div style={{ background: T.bgCard, border: `1px dashed ${T.borderDashed}`, borderRadius: "12px", padding: "34px 20px", textAlign: "center" }}>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Portfólio vazio</div>
          <p style={{ margin: "8px auto 16px", color: T.textMuted, fontSize: "13px", maxWidth: "380px", lineHeight: 1.5 }}>{cp.vazioPortfolio}</p>
          <button onClick={goMercado} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 700, fontSize: "13px" }}>Ir à watchlist →</button>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "11px" }}>
        {data.positions.map((p) => {
          const q = byQ(p.t);
          const cur = markPrice(q, p);
          const avg = Number(p.avg) || 0;
          const pnl = (cur - avg) * p.qty;
          const pnlPct = avg > 0 ? (cur / avg - 1) * 100 : 0;
          const color = pnl >= 0 ? T.positive : T.negative;
          const cell = (label, value, c) => (<div><div style={kicker}>{label}</div><div style={{ fontFamily: MONO, fontSize: "13px", color: c }}>{value}</div></div>);
          return (
            <div key={p.t} style={{ ...card, padding: "14px 15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", flexWrap: "wrap" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "8px", flexWrap: "wrap" }}>
                    <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "16px" }}>{p.t}</span>
                    <span style={{ color: T.textFaint, fontFamily: MONO, fontSize: "12px" }}>{p.qty} cotas · PM R$ {price(p.avg)}</span>
                  </div>
                </div>
                <div style={{ textAlign: "right", fontFamily: MONO }}>
                  <div style={{ fontSize: "16px", fontWeight: 600, color }}>{moneySigned(pnl)}</div>
                  <div style={{ fontSize: "12px", color }}>{pct(pnlPct)}</div>
                </div>
              </div>
              {/* FASE 3 (mock v2): a régua POSIÇÃO NO RISCO substitui as 4 células —
                  onde o preço está entre stop e alvo, à primeira vista. */}
              <PlanRuler
                caption="POSIÇÃO NO RISCO"
                marks={[p.stop != null && { v: p.stop, color: T.negative }, p.alvo != null && { v: p.alvo, color: T.positive }].filter(Boolean)}
                cur={cur}
                curLabel={"agora " + price(cur)}
                legend={[
                  { k: "STOP", v: p.stop, color: T.negative, cta: "definir ▸", sub: p.stop != null && cur > 0 ? "−" + Math.abs(((cur - p.stop) / cur) * 100).toFixed(1) + "%" : null },
                  { k: "P. MÉDIO", v: p.avg },
                  { k: "ALVO", v: p.alvo, color: T.positive, cta: "definir ▸", sub: p.alvo != null && cur > 0 ? "+" + Math.abs(((p.alvo - cur) / cur) * 100).toFixed(1) + "%" : null },
                ]}
              />
              {(p.stop == null || p.alvo == null) && (
                <button onClick={() => setEditFor(editFor === p.t ? null : p.t)} style={{ marginTop: "7px", background: "transparent", border: "none", padding: 0, color: T.accent, fontSize: "11px", fontWeight: 800 }}>
                  ✎ {p.stop == null && p.alvo == null ? "definir stop e alvo" : p.stop == null ? "definir stop" : "definir alvo"}
                </button>
              )}
              {/* FASE 2 (2.4): tudo que a decisão de stop/alvo/venda exige, num só lugar */}
              {(() => {
                const dias = daysSince(openedAt(data.history, p.t, p));
                const rr = (p.stop != null && p.alvo != null && cur > p.stop) ? (p.alvo - cur) / (cur - p.stop) : null;
                const pctCap = total > 0 ? (p.qty * cur / total) * 100 : 0;
                const se = p.setupEntrada;
                let gatStatus = null;
                if (se && se.invalidacao != null) {
                  const inval = se.lado === "baixa" ? cur > se.invalidacao : cur < se.invalidacao;
                  gatStatus = inval ? ["invalidado", T.negative] : ["válido", T.positive];
                }
                return (
                  <div style={{ marginTop: "10px", padding: "9px 11px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", fontSize: "11px", color: T.textMuted }}>
                      <span>{dias == null ? "—" : dias === 0 ? "aberta hoje" : dias + " dia" + (dias > 1 ? "s" : "") + " em operação"}</span>
                      <span>R:R atual <b style={{ fontFamily: MONO, color: rr == null ? T.textFaint : rr >= 1.5 ? T.textSecondary : T.negative }}>{rr == null ? "—" : rr.toFixed(2)}</b></span>
                      <span><b style={{ fontFamily: MONO, color: T.textSecondary }}>{pctCap.toFixed(1)}%</b> do capital</span>
                    </div>
                    {se && (
                      <div style={{ marginTop: "6px", fontSize: "11px", color: T.textMuted }}>
                        Entrada pelo setup <b style={{ color: T.textSecondary }}>{se.setup || "—"}</b>
                        {se.gatilho != null && <span> · gatilho R$ {price(se.gatilho)}</span>}
                        {gatStatus && <span> · <b style={{ color: gatStatus[1] }}>{gatStatus[0]}</b></span>}
                      </div>
                    )}
                    {p.stop == null && <div style={{ marginTop: "6px", fontSize: "11px", fontWeight: 700, color: T.negative }}>⚠ Posição sem stop definido — defina pela régua acima ou peça a sugestão da IA.</div>}
                  </div>
                );
              })()}
              {/* FASE 3 (aprovado): compras que formaram a posição + memória do PM */}
              {(() => {
                const cps = comprasDaPosicao(data.history, p.t);
                if (!cps.length) return null;
                const aberto = !!comprasOpen[p.t];
                const totV = cps.reduce((sum, h) => sum + (h.qty || 0) * (h.price || 0), 0);
                const totQ = cps.reduce((sum, h) => sum + (h.qty || 0), 0);
                return (
                  <div style={{ marginTop: "9px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}`, overflow: "hidden" }}>
                    <button onClick={() => setComprasOpen((x) => ({ ...x, [p.t]: !aberto }))} aria-expanded={aberto} style={{ display: "flex", width: "100%", alignItems: "center", justifyContent: "space-between", padding: "8px 10px", background: "transparent", border: "none", color: T.textMuted, fontSize: "11.5px", fontWeight: 700 }}>
                      <span>Compras desta posição ({cps.length})</span><span style={{ color: T.textFaint }}>{aberto ? "▴" : "▾"}</span>
                    </button>
                    {aberto && (
                      <>
                        {cps.map((h, i) => (
                          <div key={i} style={{ display: "flex", gap: "8px", padding: "6px 10px", borderTop: `1px solid ${T.borderFaint}`, fontFamily: MONO, fontSize: "11px", color: T.textSecondary }}>
                            <span style={{ flex: 1.3, color: T.textFaint }}>{String(h.date || "").slice(0, 10)}</span>
                            <span style={{ flex: 1.6 }}>▲ {h.qty} × R$ {price(h.price)}</span>
                            <span style={{ flex: 1, textAlign: "right" }}>{money((h.qty || 0) * (h.price || 0))}</span>
                          </div>
                        ))}
                        <div style={{ padding: "7px 10px", borderTop: `1px solid ${T.borderFaint}`, fontSize: "10.5px", color: T.textFaint }}>
                          Preço médio <b style={{ fontFamily: MONO, color: T.textSecondary }}>R$ {price(p.avg)}</b> = {money(totV)} ÷ {totQ} cotas (média ponderada das compras{p.qty !== totQ ? "; vendas parciais reduzem a quantidade, não o PM" : ""})
                        </div>
                      </>
                    )}
                  </div>
                );
              })()}
              {/* FASE 3 (mock v2): duas ações-bloco — o resto vira linha de links */}
              <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                <button onClick={() => ctx.openStopAlvo(p.t)} aria-label={"Sugerir stop e alvo de " + p.t + " com IA"} style={{ flex: 1, minHeight: "42px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 800, fontSize: "12.5px" }}>
                  📈 Stop/alvo (IA)
                </button>
                <button onClick={() => ctx.A.openSell(p.t)} style={{ flex: 1, minHeight: "42px", padding: "9px", borderRadius: "10px", border: `1px solid ${T.negative}`, background: T.negativeTint10, color: T.negative, fontWeight: 800, fontSize: "12.5px" }}>
                  {cp.btnVender}…
                </button>
              </div>
              <div style={{ display: "flex", gap: "14px", alignItems: "center", marginTop: "10px", paddingTop: "9px", borderTop: `1px solid ${T.borderFaint}` }}>
                <button onClick={() => setEditFor(editFor === p.t ? null : p.t)} style={{ background: "transparent", border: "none", padding: "5px 0", color: editFor === p.t ? T.accent : T.textMuted, fontSize: "11.5px", fontWeight: 800 }}>✎ Editar stop/alvo</button>
                <button onClick={() => ctx.openAvaliar(p.t)} style={{ background: "transparent", border: "none", padding: "5px 0", color: T.textMuted, fontSize: "11.5px", fontWeight: 700 }}>Reanalisar</button>
                <button onClick={() => setHistFor(histFor === p.t ? null : p.t)} style={{ background: "transparent", border: "none", padding: "5px 0", color: histFor === p.t ? T.accent : T.textMuted, fontSize: "11.5px", fontWeight: 700, marginLeft: "auto" }}>
                  Histórico de análises ({((data.analysisLog || {})[p.t] || []).length})
                </button>
              </div>
              {histFor === p.t && (
                <div style={{ marginTop: "9px", padding: "10px 11px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  {(((data.analysisLog || {})[p.t]) || []).length === 0 && (
                    <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>Sem registros ainda — cada análise e cada stop/alvo aplicados ficam guardados aqui, para você comparar o que a IA leu com o que aconteceu.</div>
                  )}
                  {(((data.analysisLog || {})[p.t]) || []).slice().reverse().map((e, i) => (
                    <div key={i} style={{ padding: "7px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", fontSize: "11.5px", lineHeight: 1.5 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                        <b style={{ color: T.textSecondary }}>{e.tipo || "análise"}{e.modelo ? " · " + e.modelo : ""}</b>
                        <span style={{ color: T.textFaint, fontFamily: MONO }}>{e.at || ""}</span>
                      </div>
                      <div style={{ color: T.textMuted, marginTop: "2px" }}>
                        {e.resumo ? e.resumo + " · " : ""}{e.preco != null ? "preço R$ " + price(e.preco) : ""}{e.stop != null ? " · stop R$ " + price(e.stop) : ""}{e.alvo != null ? " · alvo R$ " + price(e.alvo) : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {editFor === p.t && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "10px", flexWrap: "wrap", padding: "10px 11px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  {/* Sair do campo VAZIO não apaga mais — um blur sem querer (troca de
                      app, notificação, interrupção) não pode zerar a proteção da posição.
                      Limpar de propósito agora é uma ação explícita: o botão ✕. */}
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <input key={"stop-" + p.t + "-" + (p.stop ?? "vazio")} type="number" step="0.01" placeholder="stop" aria-label={"Stop de " + p.t} defaultValue={p.stop ?? ""}
                      onBlur={(e) => { const v = e.target.value; if (v.trim() !== "") A.setStop(p.t, v); }}
                      style={{ ...field, width: "92px", fontFamily: MONO, padding: "7px 9px" }} />
                    {p.stop != null && (
                      <button type="button" onClick={() => A.setStop(p.t, "")} aria-label={"Limpar stop de " + p.t}
                        style={{ minWidth: "26px", minHeight: "26px", borderRadius: "7px", border: `1px solid ${T.borderFaint}`, background: "transparent", color: T.textFaint, fontSize: "12px" }}>✕</button>
                    )}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <input key={"alvo-" + p.t + "-" + (p.alvo ?? "vazio")} type="number" step="0.01" placeholder="alvo" aria-label={"Alvo de " + p.t} defaultValue={p.alvo ?? ""}
                      onBlur={(e) => { const v = e.target.value; if (v.trim() !== "") A.setAlvo(p.t, v); }}
                      style={{ ...field, width: "92px", fontFamily: MONO, padding: "7px 9px" }} />
                    {p.alvo != null && (
                      <button type="button" onClick={() => A.setAlvo(p.t, "")} aria-label={"Limpar alvo de " + p.t}
                        style={{ minWidth: "26px", minHeight: "26px", borderRadius: "7px", border: `1px solid ${T.borderFaint}`, background: "transparent", color: T.textFaint, fontSize: "12px" }}>✕</button>
                    )}
                  </div>
                  <div style={{ fontSize: "11px", color: T.textFaint, flex: 1, minWidth: "140px", lineHeight: 1.4 }}>Sai do campo para salvar — deixar vazio não apaga; use ✕ para limpar. A régua acima reflete na hora. MV <span style={{ fontFamily: MONO, color: T.textPrimary, fontWeight: 600 }}>{money(p.qty * cur)}</span></div>
                </div>
              )}
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
          <p style={{ margin: "8px auto 0", color: T.textMuted, fontSize: "13px", maxWidth: "380px", lineHeight: 1.5 }}>{cp.vazioHistorico}</p>
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

// F2 — o app ENSINA o mecanismo: cada critério de trailing diz o que observa e
// o que isso implica. Vocabulário descritivo, sem verbo de ordem de operação
// (guardrail regulatório), e sem prometer resultado.
const TRAILING_CRITERIOS = [
  ["percentual", "Percentual", "O stop acompanha o preço a uma distância fixa em %. Simples e previsível, mas ignora se o papel está calmo ou agitado — a mesma distância vale para os dois casos."],
  ["atr", "Volatilidade (ATR)", "A distância vem do ATR(14), que mede a oscilação típica do papel. Em pregões agitados o stop fica mais longe; em pregões calmos, mais perto."],
  ["estrutura", "Estrutura", "O stop vai para a menor mínima das últimas velas — o nível cuja perda invalidaria a tese de alta. Segue o desenho do gráfico, não uma conta sobre o preço."],
];

function AgenteScreen({ ctx }) {
  const { data, A, cycleBusy } = ctx;
  const ag = data.agent;
  // FASE 3.2 — parâmetros do agente server-side (age com o app FECHADO; exige conta)
  const logged = !!ctx.authUser;
  const rules = (ag.rules && typeof ag.rules === "object") ? ag.rules : {};
  const putAg = (patch) => A.putAgent(patch);
  // Fase A (trava Modo Estudo): "Executar" só existe em Modo Operador — o
  // backend (agent.agent_params/store.set_agent) já trava a leitura e a
  // escrita; aqui é só a UI não OFERECER o que o servidor vai recusar.
  const { operador } = ctx;
  // Defensivo: se o dado local ainda tem "executar" salvo de antes desta
  // migração (ou não sincronizou), a UI mostra "sinalizar" mesmo assim —
  // nunca exibe um estado que o backend já rejeitou.
  const modoEfetivo = operador ? (ag.mode || (ag.autonomous ? "executar" : "sinalizar")) : "sinalizar";
  // FASE 6 (fix 4): a ativação/teste do push moraram aqui e na Observabilidade —
  // agora vivem na CENTRAL de notificações (Perfil → Conta & preferências).
  // Este atalho só leva o usuário para lá.
  // BLOCO D3 — só o necessário para CONFIRMAR o toggle (o resto da
  // observabilidade — status detalhado, Diário, passadas do scheduler —
  // mudou para Perfil → Observabilidade, a pedido do Alex).
  const [srv, setSrv] = useState(null);
  const [srvBusy, setSrvBusy] = useState(false);      // FASE 3: ativação confirmada (sem estado fantasma)
  const loadSrv = useCallback(async () => {
    try { setSrv(await store.agentStatus()); } catch { /* a confirmação do toggle é best-effort aqui */ }
  }, []);
  useEffect(() => { loadSrv(); const id = setInterval(loadSrv, 20000); return () => clearInterval(id); }, [loadSrv]);
  // FASE 3 — fim do timeout fantasma: a flag do SERVIDOR só muda com resposta
  // do servidor (caminho LIVE no persistence.js) e é reconfirmada pelo status.
  const setServer = async (on) => {
    if (srvBusy) return;
    setSrvBusy(true);
    try {
      await A.putAgent({ serverEnabled: on });
      await loadSrv();
      A.flash && A.flash("Operador no servidor " + (on ? "ATIVADO ✓ (confirmado)" : "desativado."));
    } catch (e) {
      const msg = (e && e.message) || String(e);
      A.flash && A.flash("Não deu para " + (on ? "ativar" : "desativar") + ": " + msg + (/(timeout|abort)/i.test(msg) ? " — o servidor pode estar ocupado numa varredura; veja Perfil → Logs & debug (os requests lentos aparecem como [slow] nos logs do Railway). Tente de novo em instantes." : ""));
      loadSrv();
    } finally { setSrvBusy(false); }
  };
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "2px" }}>
        <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Operador IA</h1>
        <InfoDot onClick={A.openAbout} />
      </div>
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "13px", maxWidth: "600px", lineHeight: 1.5 }}>
        Seu operador autônomo da carteira SIMULADA: monitora as posições, protege stop/alvo pelas regras que você define e registra cada decisão — no servidor, mesmo com o app fechado. Status detalhado, Diário e testes ficam em <b>Perfil → Logs & debug</b>.
      </p>

      {/* qa/audit-2026-08-07 (itens 3+4): resumo do modo do app, ANTES de
          qualquer controle desta tela. Esta tela ("Operador IA") configura os
          PARÂMETROS do agente; quem liga o Modo Operador de verdade é OUTRO
          interruptor (Perfil → Modo de trabalho) — a auditoria achou que
          nada aqui deixava essa distinção clara, e foi a causa raiz de
          "não me deixa selecionar Executar". Agora o modo aparece primeiro,
          sempre visível, com o link direto pra trocar. */}
      <div style={{ marginTop: "14px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", padding: "10px 14px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
        <div style={{ fontSize: "12px", color: T.textSecondary }}>
          Modo do app: <b style={{ color: operador ? T.accent : T.textPrimary }}>{operador ? "📈 Operador" : "🎓 Estudo"}</b>
          <span style={{ color: T.textFaint }}> — {operador ? "decisões diretas liberadas" : "só orienta, nunca decide sozinho"}</span>
        </div>
        <button onClick={() => A.go("perfil")} style={{ background: "transparent", border: "none", padding: 0, color: T.accent, fontWeight: 800, fontSize: "11.5px", textDecoration: "underline", flex: "none" }}>
          Trocar →
        </button>
      </div>

      {/* qa/34 (§7 da auditoria, aprovado): CARD-HERÓI — um ESTADO dominante no
          topo (ATIVO/INATIVO · modo), o toggle como único CTA de peso. As regras
          e tetos desceram para o card "Regras & limites"; o link de notificações
          foi para o rodapé. NADA foi removido — só reorganizado. */}
      <div style={{ marginTop: "16px", ...card, padding: "18px 17px", border: `1px solid ${(ag.serverEnabled && logged) ? T.accent : T.borderSubtle}` }}>
        <div style={{ fontSize: "10.5px", fontWeight: 800, letterSpacing: "0.06em", color: T.textFaint }}>OPERADOR NO SERVIDOR <span style={{ color: T.accent }}>· 24×5</span></div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px", marginTop: "8px" }}>
          <div>
            <div style={{ fontSize: "21px", fontWeight: 800, letterSpacing: "-0.01em", color: (ag.serverEnabled && logged) ? T.accent : T.textFaint }}>
              {(ag.serverEnabled && logged) ? "ATIVO" : "INATIVO"}
              <span style={{ fontSize: "13px", fontWeight: 700, color: T.textMuted }}> · {modoEfetivo === "executar" ? "Executar" : "Apenas sinalizar"}</span>
            </div>
            <p style={{ margin: "5px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "440px" }}>
              {logged ? "Roda no servidor a cada ciclo do pregão, mesmo com o app fechado. As regras do card abaixo valem para ele." : "Requer conta: sem login, o agente segue funcionando apenas com o app aberto (modo atual)."}
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
            <Toggle on={!!ag.serverEnabled && logged} onClick={() => logged && setServer(!ag.serverEnabled)} label="Agente no servidor" />
            {srvBusy && <span style={{ fontSize: "10px", color: T.accent, fontWeight: 800 }}>confirmando…</span>}
            {!srvBusy && logged && srv && <span style={{ fontSize: "10px", fontWeight: 800, color: srv.meuServerEnabled ? T.positive : T.textFaint }}>{srv.meuServerEnabled ? "✓ confirmado no servidor" : "inativo no servidor"}</span>}
          </div>
        </div>
        <div style={{ marginTop: "14px", paddingTop: "13px", borderTop: `1px solid ${T.borderFaint}`, display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {["executar", "sinalizar"].map((m) => {
            const on = modoEfetivo === m;
            const desabilitado = m === "executar" && !operador;
            return (
              // qa/audit-2026-08-07: `title` sozinho é invisível em toque (WKWebView
              // não tem hover) — o botão desabilitado não podia depender só dele.
              // O aviso visível abaixo agora tem um link direto pra onde a troca de
              // verdade acontece; antes explicava o motivo mas não dizia onde ir.
              <button key={m} onClick={() => !desabilitado && putAg({ mode: m })} disabled={desabilitado}
                style={{ flex: 1, minWidth: "140px", padding: "10px", borderRadius: "10px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgBase, color: desabilitado ? T.textFaint : (on ? T.accent : T.textSecondary), fontWeight: 800, fontSize: "12px", opacity: desabilitado ? 0.6 : 1, cursor: desabilitado ? "not-allowed" : "pointer" }}>
                {m === "executar" ? "Executar (vende no stop/alvo)" : "Apenas sinalizar"}
              </button>
            );
          })}
        </div>
        {!operador && (
          <p style={{ margin: "9px 0 0", fontSize: "11.5px", lineHeight: 1.5, color: T.textFaint }}>
            Disponível no Modo Operador — em Modo Estudo o agente só orienta, nunca vende sozinho.{" "}
            <button onClick={() => A.go("perfil")} style={{ background: "transparent", border: "none", padding: 0, color: T.accent, fontWeight: 800, fontSize: "11.5px", textDecoration: "underline" }}>
              Trocar para Modo Operador →
            </button>
          </p>
        )}
      </div>

      {/* qa/34: REGRAS & LIMITES — agrupamento das regras (stop/alvo/trailing),
          tetos e intervalo do ciclo do servidor, antes soltos no card do toggle. */}
      <div style={{ marginTop: "16px", ...card, padding: "16px 17px" }}>
        <div style={{ fontSize: "10.5px", fontWeight: 800, letterSpacing: "0.06em", color: T.textFaint }}>REGRAS & LIMITES</div>
        <div style={{ marginTop: "11px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {[["stop", "Regra: stop"], ["alvo", "Regra: alvo"], ["trailing", "Trailing (sobe o stop)"]].map(([k, lb]) => {
            const on = k === "trailing" ? !!rules[k] : rules[k] !== false;
            return (
              <button key={k} onClick={() => putAg({ rules: { [k]: !on } })} style={{ padding: "8px 12px", borderRadius: "999px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgBase, color: on ? T.accent : T.textMuted, fontWeight: 700, fontSize: "11.5px" }}>
                {on ? "✓ " : ""}{lb}
              </button>
            );
          })}
        </div>
        {/* F2 — critério do trailing. Só aparece com o trailing LIGADO: sem ele
            o seletor seria decoração. E só o campo do critério escolhido é
            exibido — três campos simultâneos, dois deles inertes, ensinariam
            errado sobre o que está governando o stop. */}
        {!!rules.trailing && (
          <div style={{ marginTop: "14px", paddingTop: "13px", borderTop: `1px solid ${T.borderFaint}` }}>
            <div style={{ fontSize: "12px", color: T.textMuted }}>Critério do trailing <span style={{ color: T.textFaint }}>· o que define até onde o stop sobe</span></div>
            <div style={{ display: "flex", gap: "8px", marginTop: "8px", flexWrap: "wrap" }}>
              {TRAILING_CRITERIOS.map(([m, lb]) => {
                const on = (ag.trailingMode || "percentual") === m;
                return (
                  <button key={m} onClick={() => putAg({ trailingMode: m })} style={{ flex: 1, minWidth: "104px", padding: "10px", borderRadius: "10px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgBase, color: on ? T.accent : T.textSecondary, fontWeight: 800, fontSize: "12px" }}>
                    {lb}
                  </button>
                );
              })}
            </div>
            <p style={{ margin: "9px 0 0", fontSize: "11.5px", lineHeight: 1.5, color: T.textFaint }}>
              {(TRAILING_CRITERIOS.find(([m]) => m === (ag.trailingMode || "percentual")) || TRAILING_CRITERIOS[0])[2]}
            </p>
            <div style={{ marginTop: "10px", maxWidth: "260px" }}>
              {(ag.trailingMode || "percentual") === "percentual" && (
                <label style={{ fontSize: "12px", color: T.textMuted }}>
                  Distância do preço (%)
                  <input type="number" min="1" max="20" step="0.5" value={ag.trailingPct ?? 5} onChange={(e) => putAg({ trailingPct: +e.target.value })} style={{ ...field, marginTop: "5px" }} />
                </label>
              )}
              {(ag.trailingMode || "percentual") === "atr" && (
                <label style={{ fontSize: "12px", color: T.textMuted }}>
                  Múltiplo do ATR(14)
                  <input type="number" min="1" max="4" step="0.5" value={ag.trailingAtrMult ?? 2} onChange={(e) => putAg({ trailingAtrMult: +e.target.value })} style={{ ...field, marginTop: "5px" }} />
                </label>
              )}
              {(ag.trailingMode || "percentual") === "estrutura" && (
                <label style={{ fontSize: "12px", color: T.textMuted }}>
                  Velas consideradas na mínima
                  <input type="number" min="2" max="20" step="1" value={ag.trailingLookback ?? 5} onChange={(e) => putAg({ trailingLookback: +e.target.value })} style={{ ...field, marginTop: "5px" }} />
                </label>
              )}
            </div>
            <p style={{ margin: "9px 0 0", fontSize: "11px", lineHeight: 1.5, color: T.textFaint }}>
              Em qualquer critério o stop só sobe — nunca desce. Se o dado técnico faltar num ciclo, a mesa usa o percentual e registra isso no Diário.
            </p>
          </div>
        )}
        {/* F3 — alvo dinâmico: só aparece com a regra de alvo LIGADA. Sem
            parâmetro extra (critério fixo: ATR, no máx. 2 extensões por
            posição) — decisão do Alex (2026-08-03) foi manter o v1 simples. */}
        {rules.alvo !== false && (
          <div style={{ marginTop: "14px", paddingTop: "13px", borderTop: `1px solid ${T.borderFaint}` }}>
            <div style={{ fontSize: "12px", color: T.textMuted }}>Alvo dinâmico <span style={{ color: T.textFaint }}>· estende o alvo em vez de fechar, quando o preço já bate com força</span></div>
            <div style={{ marginTop: "8px" }}>
              <button onClick={() => putAg({ alvoDinamico: !ag.alvoDinamico })} style={{ padding: "8px 12px", borderRadius: "999px", border: `1px solid ${ag.alvoDinamico ? T.accent : T.borderSubtle}`, background: ag.alvoDinamico ? T.accentTint : T.bgBase, color: ag.alvoDinamico ? T.accent : T.textMuted, fontWeight: 700, fontSize: "11.5px" }}>
                {ag.alvoDinamico ? "✓ " : ""}Alvo dinâmico ligado
              </button>
            </div>
            <p style={{ margin: "9px 0 0", fontSize: "11.5px", lineHeight: 1.5, color: T.textFaint }}>
              Quando o preço bate o alvo, se ainda sobrar 1,5× o ATR(14) de fôlego e o R:R recalculado continuar ≥ 1,5:1 (Princípio 5), o alvo é estendido — no máximo 2 vezes por posição. Depois disso, ou sem esse fôlego, o fechamento simulado da posição acontece normalmente.
            </p>
          </div>
        )}
        <div style={{ marginTop: "13px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <label style={{ flex: 1, minWidth: "150px", fontSize: "12px", color: T.textMuted }}>
            Teto de operações/dia
            <input type="number" min="1" max="20" value={ag.maxOpsDia || 3} onChange={(e) => putAg({ maxOpsDia: +e.target.value })} style={{ ...field, marginTop: "5px" }} />
          </label>
          <label style={{ flex: 1, minWidth: "150px", fontSize: "12px", color: T.textMuted }}>
            Valor máx. por operação (R$, 0 = sem teto)
            <input type="number" min="0" step="100" value={ag.maxValorOp || 0} onChange={(e) => putAg({ maxValorOp: +e.target.value })} style={{ ...field, marginTop: "5px" }} />
          </label>
        </div>
        {/* Intervalo do ciclo POR USUÁRIO (agent.intervalMin): com que frequência
            o Operador no servidor reavalia as posições durante o pregão. O laço do
            servidor acorda na cadência base e só roda o ciclo deste usuário quando
            passou o intervalo escolhido (granularidade mínima = cadência base). */}
        <div style={{ marginTop: "14px", paddingTop: "13px", borderTop: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "12px", color: T.textMuted }}>Intervalo do ciclo <span style={{ color: T.textFaint }}>· com que frequência a mesa reavalia durante o pregão</span></div>
          <div style={{ display: "flex", gap: "8px", marginTop: "8px", flexWrap: "wrap" }}>
            {[5, 15, 30, 60].map((mn) => {
              const on = (ag.intervalMin || 15) === mn;
              return (
                <button key={mn} onClick={() => putAg({ intervalMin: mn })} style={{ flex: 1, minWidth: "64px", padding: "10px", borderRadius: "10px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgBase, color: on ? T.accent : T.textSecondary, fontWeight: 800, fontSize: "12px" }}>
                  {mn} min
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Fase C (docs/plano-operador-entrada-e-modos.md) — entrada automática:
          mesma trava condicional de exibição/uso que a Fase A já estabeleceu
          para o botão "Executar" (seção inteira desabilitada fora do
          Operador, com o mesmo tipo de texto explicativo). O slider allocPct
          que morava solto no card "Modo local" (decorativo até a Fase B)
          agora mora aqui — é aqui que ele passou a ter efeito real. */}
      <div style={{ marginTop: "16px", ...card, padding: "16px 17px" }}>
        <div style={{ fontSize: "10.5px", fontWeight: 800, letterSpacing: "0.06em", color: T.textFaint }}>ENTRADA AUTOMÁTICA</div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px", marginTop: "8px" }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "15px" }}>{ag.entradaAuto && operador ? "Entrar automaticamente" : "Apenas avisar"}</div>
            <p style={{ margin: "4px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "440px" }}>
              Quando o gatilho de entrada dispara para um plano de COMPRA da watchlist, decide se a mesa compra sozinha (lote redondo, dentro do teto abaixo) ou só avisa, como hoje.
            </p>
          </div>
          <Toggle on={!!ag.entradaAuto && operador} onClick={() => operador && putAg({ entradaAuto: !ag.entradaAuto })} label="Entrar automaticamente" />
        </div>
        <div style={{ marginTop: "16px", paddingTop: "15px", borderTop: `1px solid ${T.borderFaint}`, opacity: operador ? 1 : 0.6 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label htmlFor="alloc" style={{ fontWeight: 600, fontSize: "14px" }}>Alocação por operação</label>
            <span style={{ fontFamily: MONO, fontSize: "15px", fontWeight: 600, color: T.accent }}>{ag.allocPct}%</span>
          </div>
          <input id="alloc" type="range" min="1" max="20" step="1" value={ag.allocPct} disabled={!operador} onChange={(e) => A.setAlloc(+e.target.value)} style={{ width: "100%", marginTop: "10px", accentColor: T.accent }} />
          <div style={{ fontSize: "12px", color: T.textFaint, marginTop: "4px" }}>Quando ligado, cada entrada automática usa até {ag.allocPct}% do caixa disponível — nunca mais, mesmo que o valor não feche num lote redondo (aí a entrada não acontece naquele ciclo).</div>
        </div>
        <p style={{ margin: "12px 0 0", fontSize: "11.5px", lineHeight: 1.5, color: T.textFaint }}>
          Só entra sozinha em plano de COMPRA — um setup de baixa (VENDER) nunca vira ordem automática, continua só aviso, em qualquer modo.
        </p>
        {!operador && (
          <p style={{ margin: "9px 0 0", fontSize: "11.5px", lineHeight: 1.5, color: T.textFaint }}>
            Disponível no Modo Operador — em Modo Estudo a entrada continua só por aviso.{" "}
            <button onClick={() => A.go("perfil")} style={{ background: "transparent", border: "none", padding: 0, color: T.accent, fontWeight: 800, fontSize: "11.5px", textDecoration: "underline" }}>
              Trocar para Modo Operador →
            </button>
          </p>
        )}
      </div>

      <div style={{ marginTop: "16px", ...card, padding: "16px 17px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px" }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "15px" }}>Modo local (com o app aberto)</div>
            <p style={{ margin: "4px 0 0", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "440px" }}>Complemento do operador no servidor: com o app aberto, o ciclo local também protege stop/alvo. Sem conta, é o único modo disponível.</p>
          </div>
          <Toggle on={ag.autonomous} onClick={() => A.toggleAuto(!ag.autonomous)} label="Modo autônomo" />
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

      {/* qa/34: rodapé da aba — link de notificações (antes no meio do card do
          toggle) + disclaimer. Mesmos destinos, hierarquia mais calma. */}
      <div style={{ marginTop: "18px", paddingTop: "13px", borderTop: `1px solid ${T.borderFaint}` }}>
        {logged && (
          <button onClick={() => A.openNotifCentral()} style={{ background: "transparent", border: "none", color: T.accent, fontWeight: 700, fontSize: "12px", padding: 0 }}>
            Notificações e push → central única em Perfil → Conta & preferências
          </button>
        )}
        <div style={{ marginTop: "8px", fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>Opera somente a carteira simulada. Conteúdo educacional — nenhuma ação é recomendação de investimento.</div>
      </div>
    </div>
  );
}

// FASE 6 (fix 4) — CENTRAL ÚNICA de notificações. Antes os controles viviam em
// três lugares (Config = locais; Operador IA = ativar push; Observabilidade =
// testar push) e o "Pedir permissão" parecia morto: depois de UMA negativa o
// iOS nunca pergunta de novo (requestPermissions volta "denied" na hora) — o
// único caminho é Ajustes, e agora há botão direto para lá. Tudo num painel:
// permissão do sistema → preferências locais → push do servidor → testes.
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
    denied: "Permissão negada — o iOS só pergunta UMA vez; reative em Ajustes → Notificações → Boris+ (botão abaixo).",
    default: "Permissão ainda não solicitada — toque em Pedir permissão.",
    unsupported: isNative ? "Indisponível neste app — recompile (npm install + cap sync) para registrar o plugin." : "Seu navegador não suporta notificações.",
  }[perm] || "";
  const statusColor = perm === "granted" ? T.positive : (perm === "denied" || perm === "unsupported") ? T.negative : T.textMuted;
  const onMaster = async () => { setMsg(""); await A.setNotif({ enabled: !nf.enabled }); refreshPerm(); };
  const onRequestPermission = async () => {
    setMsg("Solicitando permissão do sistema…");
    const p = await notify.requestPermission();
    setPerm(p);
    setMsg(p === "granted" ? "Permissão concedida. Agora use o teste agendado." : (p === "denied" ? "O iOS não vai perguntar de novo — use o botão Abrir Ajustes e ative Notificações → Boris+." : "Plugin ou navegador não suportou a permissão."));
  };
  // FASE 6 (fix 4): caminho REAL quando a permissão já foi negada — o pedido
  // via app nunca mais dispara; só os Ajustes resolvem. Com o plugin ausente
  // no build, degrada para o passo a passo manual.
  const onOpenSettings = async () => {
    const okOpen = await notify.openSettings();
    if (!okOpen) setMsg("Não deu para abrir os Ajustes automaticamente (recompile o app com npm install + cap sync). Caminho manual: Ajustes → Notificações → Boris+ → Permitir.");
    else setMsg("Nos Ajustes: Notificações → Permitir notificações. Ao voltar, o status atualiza sozinho.");
  };
  // FASE 6 (fix 4): PUSH DO SERVIDOR unificado aqui (antes vivia no Operador
  // IA e o teste na Observabilidade). Exige conta; cada etapa reporta o
  // resultado exato.
  const logged = !!ctx.authUser;
  const [pushMsg, setPushMsg] = useState("");
  const [pushBusy, setPushBusy] = useState(false);
  const onAtivarPush = async () => {
    setPushBusy(true); setPushMsg("registrando este aparelho no push…");
    try {
      const r = await notify.registerPush((tk) => store.registerPushToken(tk));
      setPushMsg(r.ok ? (r.apnsConfigured ? "push ativo neste aparelho ✓" : "token salvo — falta configurar as chaves APNs no Railway (APNS-PUSH.md)") : (r.reason || "falhou"));
    } finally { setPushBusy(false); }
  };
  const onTestarPush = async () => {
    setPushBusy(true); setPushMsg("enviando push de teste…");
    try { const r = await store.pushTest(); setPushMsg("push de teste enviado (" + r.enviados + "/" + r.total + " aparelho(s)) ✓ — coloque o app em segundo plano para ver o banner"); }
    catch (e) { setPushMsg((e && e.message) || String(e)); }
    finally { setPushBusy(false); }
  };
  const onTest = async () => {
    const id = await notify.schedule("Boris+ · teste imediato", "Teste técnico de notificação local.", new Date(Date.now() + (isNative ? 5000 : 500)));
    setMsg(id != null
      ? (isNative ? "Teste agendado para 5s. Coloque o app em segundo plano para ver o banner; com app aberto, o iOS pode apenas registrar a entrega." : "Notificação de teste enviada/agendada.")
      : "Não foi possível enviar agora — verifique permissão, plugin e recompilação do app.");
  };
  const onTestScheduled = async () => {
    // BLOCO 1: 30s à frente — tempo suficiente para mandar o app para segundo
    // plano OU fechá-lo de vez (a entrega é do SISTEMA; independe do WebView).
    const id = await notify.schedule("Teste agendado", "Esta notificação foi agendada há 30 segundos.", new Date(Date.now() + 30000));
    setMsg(id != null
      ? (isNative ? "Agendada para daqui a 30s (id " + id + "). Mande o app para segundo plano — ou feche-o — para validar a entrega pelo sistema." : "Agendada para daqui a 30s (mantenha esta aba aberta).")
      : "Não foi possível agendar agora — verifique a permissão acima.");
  };
  // BLOCO A: diagnóstico NO APARELHO, sem Safari/Mac. Interpreta o diag() e dá
  // o veredito em linguagem simples — inclusive o caso "plugin fora do build"
  // (app nem aparece em Ajustes → Notificações porque o pedido de permissão
  // nativo nunca chegou a existir no binário instalado).
  const [diag, setDiag] = useState(null);
  const onDiag = async () => {
    setMsg("");
    const raw = await notify.diag();
    let veredito;
    if (isNative && raw.pendingCount == null && !raw.error) {
      veredito = { ok: false, texto: "Este build é ANTIGO (não tem o campo pendingCount). As correções de notificação não estão instaladas — rode scripts/instalar-iphone.sh e reinstale pelo Xcode." };
    } else if (isNative && !raw.pluginLoaded) {
      veredito = { ok: false, texto: "O plugin de notificações NÃO está dentro do app instalado — por isso o Boris+ nem aparece em Ajustes → Notificações. Rode scripts/instalar-iphone.sh (ele faz build + cap sync + abre o Xcode) e reinstale no aparelho." };
    } else if (raw.permission !== "granted") {
      veredito = { ok: false, texto: "Plugin ok, mas sem permissão do sistema. Toque em Pedir permissão (SEMPRE toque nele primeiro — depois de reinstalar o app, é este pedido que faz o Boris+ voltar a aparecer em Ajustes → Notificações). Se o iOS não perguntar, aí sim use Abrir Ajustes." };
    } else {
      veredito = { ok: true, texto: "Tudo pronto: plugin no build e permissão concedida. Use o teste agendado (30s) e feche o app — a entrega passa a ser responsabilidade do iOS (confira Foco/Resumo Programado se não chegar)." };
    }
    setDiag({ raw, veredito });
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
  // Variante OPT-IN: `row` acima trata ausente como LIGADO (opt-out), o que é
  // adequado para avisos sobre a SUA carteira. O aviso de condição atingida é
  // outra coisa — é a única classe disparada por evento de MERCADO, e a única
  // que chega sem você ter feito nada. Classe assim nasce desligada.
  const rowOptIn = (key, label, desc) => (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", padding: "10px 0", opacity: nf.enabled ? 1 : 0.45 }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: "13px", fontWeight: 600 }}>{label}</div>
        <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.4 }}>{desc}</div>
      </div>
      <Toggle on={nf.enabled && nf[key] === true} onClick={() => nf.enabled && A.setNotif({ [key]: !(nf[key] === true) })} label={label} />
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
        {rowOptIn("gatilho", "Condição de estudo atingida",
          "Quando uma vela de 15 min FECHA no gatilho de um ativo que você acompanha. "
          + "Vem com ~15 min de atraso do feed e nunca é ordem — no máximo 6 avisos por dia, "
          + "1 por ativo. Exige conta e push ativo neste aparelho.")}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "12px", flexWrap: "wrap" }}>
        {/* FASE 8B (R1 — fix da regressão): "Pedir permissão" fica disponível
            SEMPRE que não está concedida (default E denied). Motivo: após
            REINSTALAR o app, o iOS pode reportar "denied" herdado e o Boris+
            some de Ajustes → Notificações até um novo requestPermissions —
            só mostrar "Abrir Ajustes" criava um beco sem saída. Pedir com
            denied é inofensivo e re-registra o app na lista de Ajustes. */}
        {perm !== "granted" && perm !== "unsupported" && <button onClick={onRequestPermission} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint, color: T.accent, fontWeight: 800, fontSize: "13px" }}>Pedir permissão</button>}
        {perm === "denied" && isNative && <button onClick={onOpenSettings} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Abrir Ajustes →</button>}
        <button onClick={onTest} disabled={perm !== "granted"} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${perm === "granted" ? T.accent : T.borderSubtle}`, background: perm === "granted" ? T.accentTint : T.bgPanel, color: perm === "granted" ? T.accent : T.textFaint, fontWeight: 700, fontSize: "13px" }}>Testar notificação</button>
        <button onClick={onTestScheduled} disabled={perm !== "granted"} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: perm === "granted" ? T.textSecondary : T.textFaint, fontWeight: 700, fontSize: "13px" }}>Testar agendada (30s)</button>
        <button onClick={onDiag} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}>Diagnóstico</button>
        {msg && <span style={{ fontSize: "11.5px", color: T.textMuted, flex: 1, minWidth: "180px", lineHeight: 1.4 }}>{msg}</span>}
      </div>

      {/* FASE 6 (fix 4): PUSH DO SERVIDOR (APNs) — unificado nesta central */}
      {isNative && (
        <div style={{ marginTop: "14px", paddingTop: "12px", borderTop: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", color: T.textSecondary }}>PUSH DO SERVIDOR (app fechado)</div>
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "5px", lineHeight: 1.5, maxWidth: "480px" }}>
            Avisos das ações do Operador no servidor chegam por push (APNs) mesmo com o app fechado. Exige conta e a permissão acima concedida.
          </div>
          {!logged && <div style={{ marginTop: "9px", fontSize: "12px", color: T.textFaint }}>Entre na sua conta para ativar o push deste aparelho.</div>}
          {logged && (
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "10px", flexWrap: "wrap" }}>
              <button onClick={onAtivarPush} disabled={pushBusy || perm !== "granted"} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${perm === "granted" ? T.accent : T.borderSubtle}`, background: perm === "granted" ? T.accentTint : T.bgPanel, color: perm === "granted" ? T.accent : T.textFaint, fontWeight: 800, fontSize: "13px", opacity: pushBusy ? 0.6 : 1 }}>Ativar push neste aparelho</button>
              <button onClick={onTestarPush} disabled={pushBusy} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13px", opacity: pushBusy ? 0.6 : 1 }}>Testar push</button>
              {pushMsg && <span style={{ fontSize: "11.5px", color: T.textMuted, flex: 1, minWidth: "180px", lineHeight: 1.4 }}>{pushMsg}</span>}
            </div>
          )}
        </div>
      )}

      {diag && (
        <div style={{ marginTop: "12px", padding: "12px 13px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${diag.veredito.ok ? T.borderSubtle : T.negative}` }}>
          <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", color: diag.veredito.ok ? T.positive : T.negative }}>DIAGNÓSTICO DO SISTEMA</div>
          <div style={{ fontFamily: MONO, fontSize: "11.5px", color: T.textSecondary, marginTop: "8px", lineHeight: 1.7 }}>
            <div>plugin nativo carregado: <b style={{ color: diag.raw.pluginLoaded ? T.positive : T.negative }}>{String(diag.raw.pluginLoaded)}</b></div>
            <div>permissão do sistema: <b style={{ color: diag.raw.permission === "granted" ? T.positive : T.negative }}>{String(diag.raw.permission)}</b></div>
            <div>agendamentos pendentes no iOS: <b>{diag.raw.pendingCount != null ? diag.raw.pendingCount : "n/d (build antigo)"}</b></div>
            {diag.raw.error && <div>erro: {diag.raw.error}</div>}
          </div>
          <div style={{ fontSize: "12px", color: diag.veredito.ok ? T.textMuted : T.negative, marginTop: "9px", lineHeight: 1.55 }}>{diag.veredito.texto}</div>
        </div>
      )}

      <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "11px", lineHeight: 1.5 }}>
        Notificações <b>locais</b> são disparadas pelo próprio app (stop/alvo/variação com o app aberto ou em segundo plano); o <b>push do servidor</b> cobre as ações do Operador com o app fechado. Para validar um banner de teste no iOS, coloque o app em segundo plano após tocar em testar.
      </div>
    </div>
  );
}

// FASE 2: rótulos/ajuda dos prompts conhecidos. Chaves extras (adicionadas no
// futuro) aparecem com o próprio nome — a interface não precisa mudar.
const PROMPT_META = {
  carteiraStopAlvo: {
    label: "Prompt — Stop/alvo · Modo Estudo (professor)",
    hint: "Usado no popup de stop/alvo quando o app está no Modo Estudo. Mantenha o enquadramento educacional: sugestão por perfil, nunca recomendação de compra ou venda.",
  },
  // FASE 8B (N4): cada modo tem o seu prompt — edite os dois separadamente.
  carteiraStopAlvoOperador: {
    label: "Prompt — Stop/alvo · Modo Operador (mesa)",
    hint: "Usado no popup de stop/alvo quando o app está no Modo Operador. Voz de mesa: stop na invalidação técnica, R:R mínimo de 1,5:1, execução sempre do usuário. O guardrail de mesa é aplicado por cima automaticamente.",
  },
};

// FASE 8B (R2) — INSTRUÇÕES DO AGENTE por skill/modo, selecionáveis pelo NOME.
// "skill" = professor (Modo Estudo, seção original); "skillOperador" = mesa.
// A skill do modo ATIVO é usada automaticamente nas análises; aqui o usuário
// escolhe pelo nome qual editar (abre na do modo em uso).
function SkillSection({ ctx, sectionTitle }) {
  const { data, A } = ctx;
  const modoAtivo = (data.config && data.config.appMode) === "operador" ? "operador" : "estudo";
  const [alvo, setAlvo] = useState(modoAtivo);   // estudo | operador
  const sk = alvo === "operador" ? (data.skillOperador || { name: "Mesa B3 - Operador v1", text: "" }) : (data.skill || { name: "", text: "" });
  const emUso = alvo === modoAtivo;
  return (
    <div style={{ marginTop: "14px", ...card, padding: "17px 18px" }}>
      <div style={sectionTitle}>INSTRUÇÕES DO AGENTE (SKILLS)</div>
      <p style={{ margin: "6px 0 12px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "580px" }}>
        Cada modo de trabalho tem a SUA instrução, selecionada pelo nome abaixo. A análise usa automaticamente a skill do modo ativo.
      </p>
      <label style={{ display: "block", marginBottom: "12px" }}>
        <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Skill (pelo nome)</span>
        <select value={alvo} onChange={(e) => setAlvo(e.target.value)} style={{ ...field, fontFamily: MONO }}>
          <option value="estudo">{(data.skill && data.skill.name) || "Mesa B3 - Educacional v1"} · 🎓 Estudo</option>
          <option value="operador">{(data.skillOperador && data.skillOperador.name) || "Mesa B3 - Operador v1"} · 📈 Operador</option>
        </select>
      </label>
      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px", borderRadius: "999px", background: emUso ? T.accentTint : T.bgBase, border: `1px solid ${emUso ? T.accent : T.borderSubtle}`, color: emUso ? T.accent : T.textFaint, fontSize: "10.5px", fontWeight: 800, marginBottom: "12px" }}>
        {emUso ? "EM USO no modo atual" : "usada só no modo " + (alvo === "operador" ? "Operador" : "Estudo")}
      </div>
      <label style={{ display: "block", marginBottom: "14px" }}>
        <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Nome do skill</span>
        <input type="text" value={sk.name || ""} onChange={(e) => A.editSkill({ name: e.target.value }, alvo)} style={{ ...field, fontFamily: MONO }} />
      </label>
      <label style={{ display: "block" }}>
        <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Instruções</span>
        <textarea value={sk.text || ""} onChange={(e) => A.editSkill({ text: e.target.value }, alvo)} rows={12} style={{ width: "100%", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "8px", color: T.textBright, fontFamily: MONO, fontSize: "12.5px", lineHeight: 1.6 }} />
      </label>
      <div style={{ display: "flex", gap: "8px", marginTop: "13px" }}>
        <button onClick={() => A.saveSkill(alvo)} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Salvar</button>
        <button onClick={() => A.restoreSkill(alvo)} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Restaurar padrão</button>
      </div>
    </div>
  );
}

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

// qa/32 — CONFIGURAÇÕES DE IA: modelo/provedor do agente + skills por modo +
// prompts, que antes viviam espalhados dentro de "Conta & preferências"
// (monólito de 7 seções). Reorganizado a pedido do Alex.
function AiConfigScreen({ ctx }) {
  const { data, A, test } = ctx;
  const c = data.config;
  // qa/49 (pedido do Alex): catálogo de modelos (fonte única no servidor) → a UI
  // vira uma listbox por provedor + os parâmetros que CADA modelo aceita (temp,
  // teto de saída), com defaults editáveis e armazenados. Fallback p/ texto livre
  // se o catálogo não carregar (offline / servidor não configurado).
  const [catalogo, setCatalogo] = useState(null);
  useEffect(() => {
    let vivo = true;
    // guarda: se o store não expõe aiModels (build antigo), cai no fallback de
    // texto livre em vez de derrubar a tela ("aiModels is not a function").
    if (typeof store.aiModels === "function") {
      store.aiModels().then((r) => { if (vivo) setCatalogo(r); }).catch(() => {});
    }
    return () => { vivo = false; };
  }, []);
  const modelos = (catalogo && catalogo.catalog && catalogo.catalog[c.provider]) || [];
  const specAtual = modelos.find((m) => m.id === c.model) || null;
  const modeloCustom = !!c.model && !specAtual && modelos.length > 0;
  const aceitaTemp = specAtual ? specAtual.temperature : true; // custom/desconhecido: permissivo
  const tempDefault = (catalogo && catalogo.temperatureDefault != null) ? catalogo.temperatureDefault : 0.2;
  const tetoDefault = specAtual ? specAtual.maxTokens : "";
  const tetoCap = specAtual ? specAtual.maxTokensCap : undefined;   // #3: teto máximo por modelo
  const tempMaxUI = specAtual ? specAtual.tempMax : 2;              // #2: Anthropic só até 1.0
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };
  const seg = (on) => ({ flex: 1, padding: "10px", borderRadius: "8px", fontWeight: 600, fontSize: "13px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgPanel, color: on ? T.accent : T.textMuted });
  const testColor = test.status === "ok" ? T.positive : test.status === "error" ? T.negative : T.accent;
  const testBg = test.status === "ok" ? T.positiveTint10 : test.status === "error" ? T.negativeTint10 : T.accentTint10;
  // qa/48: recomenda o modelo rápido/barato primeiro. Modelos que "raciocinam"
  // (sonnet-5/opus…) são mais lentos e caros por análise — bom p/ profundidade,
  // não p/ uso corriqueiro. Nomes atualizados p/ a linha atual.
  const suggest = { anthropic: "Recomendado: claude-haiku-4-5 (rápido/barato) · claude-sonnet-5 (raciocina, +caro)", openai: "Recomendado: gpt-4o-mini (barato) · gpt-4o", google: "Recomendado: gemini-2.5-flash (barato) · gemini-2.5-pro", local: "Ex.: llama-3.1-70b · qwen2.5-72b" }[c.provider];
  return (
    <div>
      <h1 style={{ margin: "0 0 6px", fontSize: "22px", fontWeight: 700 }}>Configurações de IA</h1>
      <p style={{ margin: "0 0 18px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
        Modelo/provedor do agente, instruções (skills) por modo e prompts — tudo que molda como a IA analisa e responde.
      </p>

      {/* A) Modelo de IA */}
      <div style={{ ...card, padding: "17px 18px" }}>
        <div style={sectionTitle}>MODELO DE IA DO AGENTE</div>
        <p style={{ margin: "6px 0 16px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>Provedor e modelo usados para gerar as análises. A chave nunca é exibida depois de salva e fica apenas {isNative ? "neste aparelho" : "no servidor"}.</p>

        <label style={{ display: "block", marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Provedor</span>
          <select value={c.provider} onChange={(e) => { const p = e.target.value; const lst = (catalogo && catalogo.catalog && catalogo.catalog[p]) || []; A.saveConfig({ provider: p, model: lst[0] ? lst[0].id : "" }); }} style={field}>
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="google">Google</option>
            <option value="local">Compatível / Local</option>
          </select>
        </label>

        <label style={{ display: "block", marginBottom: "14px" }}>
          <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Modelo</span>
          {modelos.length > 0 ? (
            <>
              <select
                value={modeloCustom ? "__custom__" : (c.model || "")}
                onChange={(e) => { const v = e.target.value; if (v === "__custom__") { A.saveConfig({ model: "" }); return; } A.saveConfig({ model: v, maxTokens: null, temperature: null }); }}
                style={field}
              >
                {(!c.model || modeloCustom) && <option value="">Escolha um modelo…</option>}
                {modelos.map((m) => <option key={m.id} value={m.id}>{m.label} — {m.tier}</option>)}
                <option value="__custom__">Personalizado (digitar)…</option>
              </select>
              {(modeloCustom || !c.model) && (
                <input type="text" value={c.model} onChange={(e) => A.editConfig({ model: e.target.value })} onBlur={(e) => A.saveConfig({ model: e.target.value })} placeholder="nome-do-modelo" style={{ ...field, fontFamily: MONO, marginTop: "8px" }} />
              )}
              <span style={{ display: "block", fontSize: "11px", color: T.textFaint, marginTop: "5px", lineHeight: 1.4 }}>{modeloCustom ? suggest : "A lista traz os modelos testados. Ao escolher, os parâmetros abaixo já vêm com o default seguro do modelo."}</span>
            </>
          ) : (
            <>
              <input type="text" value={c.model} onChange={(e) => A.editConfig({ model: e.target.value })} onBlur={(e) => A.saveConfig({ model: e.target.value })} placeholder="nome-do-modelo" style={{ ...field, fontFamily: MONO }} />
              <span style={{ display: "block", fontSize: "11px", color: T.textFaint, marginTop: "5px", fontFamily: MONO }}>{suggest}</span>
            </>
          )}
        </label>

        {/* qa/49: parâmetros que ESTE modelo aceita — defaults do catálogo, editáveis e armazenados. */}
        {!!c.model && (
          <div style={{ display: "flex", gap: "10px", marginBottom: "14px", flexWrap: "wrap" }}>
            <label style={{ flex: 1, minWidth: "140px" }}>
              <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Teto de saída (max tokens)</span>
              <input type="number" min="256" step="256" max={tetoCap || undefined}
                value={c.maxTokens != null ? c.maxTokens : (tetoDefault || "")}
                onChange={(e) => A.editConfig({ maxTokens: e.target.value === "" ? null : Number(e.target.value) })}
                onBlur={(e) => A.saveConfig({ maxTokens: e.target.value === "" ? null : Number(e.target.value) })}
                placeholder={String(tetoDefault || "")} style={{ ...field, fontFamily: MONO }} />
              {specAtual && specAtual.thinking && <span style={{ display: "block", fontSize: "10.5px", color: T.textFaint, marginTop: "4px", lineHeight: 1.35 }}>Modelo raciocina — precisa de folga; o servidor não deixa abaixo do mínimo seguro.</span>}
              {tetoCap ? <span style={{ display: "block", fontSize: "10.5px", color: T.textFaint, marginTop: "4px" }}>máx. {tetoCap}</span> : null}
            </label>
            <label style={{ flex: 1, minWidth: "140px" }}>
              <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Temperatura</span>
              {aceitaTemp ? (
                <input type="number" min="0" max={tempMaxUI} step="0.1"
                  value={c.temperature != null ? c.temperature : tempDefault}
                  onChange={(e) => A.editConfig({ temperature: e.target.value === "" ? null : Number(e.target.value) })}
                  onBlur={(e) => A.saveConfig({ temperature: e.target.value === "" ? null : Number(e.target.value) })}
                  style={{ ...field, fontFamily: MONO }} />
              ) : (
                <div style={{ ...field, color: T.textFaint, fontSize: "11.5px", lineHeight: 1.35, background: T.bgBase, height: "auto" }}>
                  Este modelo raciocina — usa a temperatura padrão (o parâmetro não é aceito na API).
                </div>
              )}
            </label>
          </div>
        )}

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

      {/* B) Skill — FASE 8B (R2): UMA instrução do agente POR SKILL/MODO,
          selecionada PELO NOME. O seletor abre por padrão na skill do modo
          ativo; a análise usa automaticamente a skill do modo em uso. */}
      <SkillSection ctx={ctx} sectionTitle={sectionTitle} />

      {/* C) Config de LLMs e Prompts (FASE 2) */}
      <PromptsSection ctx={ctx} />
    </div>
  );
}

// qa/32 — NOTIFICAÇÕES: área dedicada (antes era só mais uma seção dentro de
// "Conta & preferências"). NotifSection já era autossuficiente — só ganhou
// uma tela própria.
function NotificacoesScreen({ ctx }) {
  return (
    <div>
      <h1 style={{ margin: "0 0 18px", fontSize: "22px", fontWeight: 700 }}>Notificações</h1>
      <NotifSection ctx={ctx} />
    </div>
  );
}

// qa/45 — ATIVIDADE DA IA: custo estimado (R$) acumulado + histórico de cada
// chamada (Radar/Análise/Carteira). Tokens vêm capturados por chamada (qa/42);
// o servidor converte em R$ (estimativa). Esta tela só lê.
function AtividadeIAScreen({ ctx }) {
  const logged = !!ctx.authUser;
  const [ati, setAti] = useState(null);
  const [err, setErr] = useState("");
  const carregar = useCallback(async () => {
    try { setAti(await store.aiActivity()); setErr(""); }
    catch (e) { setErr((e && e.message) || String(e)); }
  }, []);
  useEffect(() => { carregar(); }, [carregar]);
  const brl = (v) => "R$ " + (Number(v || 0)).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const kfmt = (n) => (n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + "k" : String(n || 0));
  const t = (ati && ati.total) || {};
  const hoje = (ati && ati.hoje) || {};
  const recentes = (ati && ati.recentes) || [];
  const dataStr = (iso) => { try { const d = new Date(iso); const p = (x) => String(x).padStart(2, "0"); return `${p(d.getDate())}/${p(d.getMonth() + 1)} ${p(d.getHours())}:${p(d.getMinutes())}`; } catch { return ""; } };
  const cellStat = (label, valor, cor) => (
    <div style={{ flex: "1 1 90px", minWidth: "84px" }}>
      <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: cor || T.textPrimary }}>{valor}</div>
      <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>{label}</div>
    </div>
  );
  return (
    <div>
      <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Atividade da IA</h1>
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "13px", maxWidth: "600px", lineHeight: 1.5 }}>
        Quanto a IA gastou (estimativa em R$) e o histórico de cada leitura — Radar, Análise e Carteira. O custo real depende do provedor/modelo; aqui é uma estimativa por tokens.
      </p>
      <div style={{ marginTop: "16px", ...card, padding: "14px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "10px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em" }}>CUSTO ESTIMADO</div>
          <button onClick={carregar} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 800, padding: "4px" }}>↻ atualizar</button>
        </div>
        {err && <div style={{ color: T.negative, fontSize: "11.5px" }}>indisponível: {err}</div>}
        {!err && !ati && <div style={{ color: T.textFaint, fontSize: "11.5px" }}>carregando…</div>}
        {ati && (
          <>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {cellStat("ACUMULADO", brl(t.custo), T.accent)}
              {cellStat("HOJE", brl(hoje.custo), (hoje.custo || 0) > 0 ? T.textPrimary : T.textFaint)}
              {cellStat("CHAMADAS", kfmt(t.calls), T.textSecondary)}
              {cellStat("TOKENS", kfmt((t.inTok || 0) + (t.outTok || 0)), T.textSecondary)}
            </div>
            <div style={{ fontSize: "10px", color: T.textFaint, lineHeight: 1.5, marginTop: "9px" }}>
              Estimativa por preço de tabela dos modelos × câmbio (US$ 1 ≈ R$ {(ati.usdBrl || 5.4).toFixed(2).replace(".", ",")}). BYOK ou gerenciado. Não é fatura — é referência.
            </div>
          </>
        )}
      </div>

      {ati && recentes.length > 0 && (
        <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "8px" }}>HISTÓRICO</div>
          {recentes.map((r, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", padding: "8px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none" }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: "12.5px", color: T.textPrimary, fontWeight: 700 }}>
                  <span style={{ fontFamily: MONO }}>{r.ticker || "—"}</span>
                  <span style={{ color: T.textFaint, fontWeight: 600 }}> · {r.tipo}</span>
                </div>
                <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "2px" }}>{dataStr(r.at)} · {kfmt((r.inTok || 0) + (r.outTok || 0))} tok · {(r.model || "").replace(/^claude-/, "")}</div>
              </div>
              <div style={{ fontFamily: MONO, fontSize: "12.5px", fontWeight: 700, color: T.textSecondary, whiteSpace: "nowrap" }}>{brl(r.custo)}</div>
            </div>
          ))}
        </div>
      )}
      {ati && recentes.length === 0 && !err && (
        <div style={{ marginTop: "14px", fontSize: "12px", color: T.textFaint, lineHeight: 1.5 }}>Nenhuma leitura de IA registrada ainda. Use "Aprofundar com IA" no Radar, "Análise" na Watchlist ou "Stop/alvo" na Carteira — cada uma aparece aqui com o custo estimado.</div>
      )}
      <div style={{ marginTop: "14px", fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>
        Só chamadas de IA gerenciada e BYOK que retornam uso de tokens entram na conta. A estimativa reinicia o "hoje" à meia-noite; o acumulado é desde o primeiro uso.
      </div>
    </div>
  );
}

// qa/32 (Fase A) — EFICIÊNCIA DA IA: área dedicada, extraída da antiga
// Observabilidade. Quanto das análises (Plano da mesa/N1 + Aprofundar/N2 com
// stop/alvo definidos) bateram o alvo, o stop, ou expiraram a favor/contra em
// 10 pregões — autoavaliação da IA contra o que o ativo realmente fez depois.
// Job do servidor roda 1x/dia; esta tela só lê o resultado (nada calcula aqui).
function EficienciaIAScreen({ ctx }) {
  const logged = !!ctx.authUser;
  const [efic, setEfic] = useState(null);
  const [eficErr, setEficErr] = useState("");
  const [csvSt, setCsvSt] = useState("");
  const loadEficiencia = useCallback(async () => {
    try { setEfic(await store.analysisOutcomesStats()); setEficErr(""); }
    catch (e) { setEficErr((e && e.message) || String(e)); }
  }, []);
  useEffect(() => { if (logged) loadEficiencia(); }, [logged, loadEficiencia]);
  // qa/35 (P2): export CSV — compartilha (iOS share sheet) com fallback de
  // copiar pra área de transferência.
  const exportCsv = async () => {
    setCsvSt("gerando…");
    try {
      const csv = await store.analysisOutcomesCsv();
      if (navigator.share) {
        try { await navigator.share({ title: "Boris+ — eficiência da IA (CSV)", text: csv }); setCsvSt("compartilhado ✓"); return; } catch { /* usuário cancelou — cai pro clipboard */ }
      }
      await navigator.clipboard.writeText(csv);
      setCsvSt("CSV copiado ✓ — cole numa planilha");
    } catch (e) { setCsvSt("falhou: " + ((e && e.message) || String(e))); }
  };
  // qa/35 (P2c): linha de UMA célula de calibração — respeita o n mínimo do
  // servidor ("n insuficiente" em vez de % enganosa; regra do produto).
  const celula = (rotulo, c) => (
    <div key={rotulo} style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "11.5px", padding: "4px 0", color: T.textMuted }}>
      <span>{rotulo} <span style={{ color: T.textFaint, fontFamily: MONO }}>n={c.n}</span></span>
      {c.insuficiente
        ? <span style={{ color: T.textFaint }}>n insuficiente (mín. {(efic && efic.minN) || 10})</span>
        : <b style={{ fontFamily: MONO, color: c.taxaAcerto >= 50 ? T.positive : T.negative }}>{c.taxaAcerto}%{c.rMedio != null ? ` · ${c.rMedio >= 0 ? "+" : ""}${c.rMedio}R` : ""}</b>}
    </div>
  );
  if (!logged) {
    return (
      <div>
        <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Eficiência da IA</h1>
        <p style={{ margin: "10px 0 0", color: T.textMuted, fontSize: "13px", lineHeight: 1.5, maxWidth: "480px" }}>
          Entre na conta para ver a autoavaliação da IA — quanto das análises com stop/alvo definidos bateram o alvo, o stop, ou expiraram, calculado no servidor.
        </p>
      </div>
    );
  }
  return (
    <div>
      <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700 }}>Eficiência da IA</h1>
      <p style={{ margin: "6px 0 0", color: T.textMuted, fontSize: "13px", maxWidth: "600px", lineHeight: 1.5 }}>
        Autoavaliação da IA contra o que o ativo realmente fez depois — nada aqui é garantia de resultado futuro.
      </p>
      <div style={{ marginTop: "16px", ...card, padding: "14px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "9px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em" }}>EFICIÊNCIA DA IA</div>
          <button onClick={loadEficiencia} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 800, padding: "4px" }}>↻ atualizar</button>
        </div>
        {eficErr && <div style={{ color: T.negative, fontSize: "11.5px" }}>indisponível: {eficErr}</div>}
        {!eficErr && !efic && <div style={{ color: T.textFaint, fontSize: "11.5px" }}>carregando…</div>}
        {efic && efic.totalAnalises === 0 && (
          <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>Nenhuma análise com plano de stop/alvo definido ainda. Use "Plano da mesa (IA)" no Radar ou "Aprofundar com IA" num ativo — cada uma entra aqui e é conferida 10 pregões depois.</div>
        )}
        {efic && efic.totalAnalises > 0 && (
          <>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.taxaAcerto == null ? T.textFaint : (efic.taxaAcerto >= 50 ? T.positive : T.negative) }}>{efic.taxaAcerto == null ? "—" : efic.taxaAcerto + "%"}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>TAXA DE ACERTO</div>
              </div>
              <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.rMedio == null ? T.textFaint : (efic.rMedio >= 0 ? T.positive : T.negative) }}>{efic.rMedio == null ? "—" : (efic.rMedio >= 0 ? "+" : "") + efic.rMedio + "R"}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>R MÉDIO / ANÁLISE</div>
              </div>
              <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: T.textSecondary }}>{efic.avaliadas}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>AVALIADAS</div>
              </div>
              <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: T.textSecondary }}>{efic.pendentes}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>AGUARDANDO PRAZO</div>
              </div>
            </div>
            {efic.porSetup && Object.keys(efic.porSetup).length > 0 && (
              <p style={{ marginTop: "9px", marginBottom: 0, fontSize: "11px", color: T.textMuted, lineHeight: 1.6 }}>
                Por setup:{" "}
                {Object.entries(efic.porSetup).map(([s, v], i, arr) => (
                  <span key={s} style={{ fontFamily: MONO }}>{s} <b>{v.acerto}/{v.total}</b>{i < arr.length - 1 ? " · " : ""}</span>
                ))}
              </p>
            )}
            <p style={{ marginTop: "8px", marginBottom: 0, fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>
              Prazo fixo de 10 pregões por análise; conta só quem tinha stop e alvo definidos. Isto é autoavaliação estatística da IA sobre dados passados — não é garantia de resultado futuro.
            </p>
          </>
        )}
      </div>

      {/* qa/35 (P2a): EXPECTÂNCIA — a vantagem esperada por análise, em R.
          Cálculo 100% no servidor (analysis_outcomes.compute_stats).
          qa/35-fix: gate por totalAnalises (não avaliadas) — o card precisa
          aparecer JÁ com "n insuficiente" enquanto as análises não resolvem
          (10 pregões); antes sumia inteiro e parecia feature faltando. */}
      {efic && efic.totalAnalises > 0 && (
        <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "9px" }}>EXPECTÂNCIA</div>
          {efic.expectanciaInsuficiente ? (
            <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>{efic.avaliadas === 0 ? `Aguardando o prazo — expectância e profit factor aparecem quando ${efic.minN || 10} análises completarem os 10 pregões (avaliadas até agora: 0).` : `n insuficiente — expectância e profit factor aparecem a partir de ${efic.minN || 10} análises avaliadas (hoje: ${efic.avaliadas}).`}</div>
          ) : (
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <div style={{ flex: "1 1 110px", minWidth: "100px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.expectancia == null ? T.textFaint : (efic.expectancia >= 0 ? T.positive : T.negative) }}>{efic.expectancia == null ? "—" : (efic.expectancia >= 0 ? "+" : "") + efic.expectancia + "R"}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>EXPECTÂNCIA / ANÁLISE</div>
              </div>
              <div style={{ flex: "1 1 110px", minWidth: "100px" }}>
                <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.profitFactor == null ? T.textFaint : ((efic.profitFactor === "inf" || efic.profitFactor >= 1) ? T.positive : T.negative) }}>{efic.profitFactor == null ? "—" : efic.profitFactor === "inf" ? "∞" : efic.profitFactor}</div>
                <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>PROFIT FACTOR</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* qa/35 (P2c): CALIBRAÇÃO — a confiança que a IA declarou bate com o
          acerto real? Cada célula respeita o n mínimo do servidor.
          qa/35-fix: idem — gate por totalAnalises, com aviso de prazo quando
          nada resolveu ainda. */}
      {efic && efic.totalAnalises > 0 && (
        <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "6px" }}>CALIBRAÇÃO DA CONFIANÇA</div>
          <p style={{ margin: "0 0 8px", fontSize: "11px", color: T.textFaint, lineHeight: 1.5 }}>Acerto real por confiança declarada — se "alta" não acerta mais que "baixa", a confiança da IA está descalibrada.</p>
          {efic.avaliadas === 0 ? (
            <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>Aguardando o prazo — a calibração aparece conforme as análises completam os 10 pregões.</div>
          ) : (
            <>
              {["alta", "moderada", "baixa", "—"].filter((k) => efic.porConfianca && efic.porConfianca[k]).map((k) => celula(k === "—" ? "sem declaração" : "confiança " + k, efic.porConfianca[k]))}
              {efic.porDecisao && Object.keys(efic.porDecisao).length > 0 && (
                <div style={{ marginTop: "10px", paddingTop: "9px", borderTop: `1px solid ${T.borderFaint}` }}>
                  <div style={{ fontSize: "10px", fontWeight: 800, color: T.textFaint, letterSpacing: "0.05em", marginBottom: "4px" }}>POR DECISÃO</div>
                  {Object.entries(efic.porDecisao).map(([k, c]) => celula(k, c))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* qa/37 (P2e): CURVA DE R ACUMULADO + DRAWDOWN — a "equity curve" em R
          das análises resolvidas (soma dos R-múltiplos na ordem de resolução).
          Cálculo 100% no servidor. Sem comparação com IBOV (R de análise não
          compara com retorno de índice). */}
      {efic && efic.totalAnalises > 0 && (
        <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "6px" }}>CURVA DE R ACUMULADO</div>
          {(!efic.curvaR || efic.curvaR.length === 0) ? (
            <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>Aguardando o prazo — a curva aparece conforme as análises completam os 10 pregões.</div>
          ) : (
            <>
              <RCurve pts={efic.curvaR} />
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "10px" }}>
                <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                  <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.rAcumulado == null ? T.textFaint : (efic.rAcumulado >= 0 ? T.positive : T.negative) }}>{efic.rAcumulado == null ? "—" : (efic.rAcumulado >= 0 ? "+" : "") + efic.rAcumulado + "R"}</div>
                  <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>R ACUMULADO</div>
                </div>
                <div style={{ flex: "1 1 90px", minWidth: "80px" }}>
                  <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: efic.drawdownMax == null ? T.textFaint : T.negative }}>{efic.drawdownMax == null ? "n insuf." : "−" + efic.drawdownMax + "R"}</div>
                  <div style={{ fontSize: "10px", color: T.textFaint, fontWeight: 700, letterSpacing: "0.04em" }}>DRAWDOWN MÁX.</div>
                </div>
              </div>
              <div style={{ fontSize: "10px", color: T.textFaint, lineHeight: 1.5, marginTop: "8px" }}>Soma dos R-múltiplos na ordem de resolução. Drawdown = maior queda do pico, em R. Autoavaliação sobre dados passados, não é garantia de resultado.</div>
            </>
          )}
        </div>
      )}

      {/* qa/35 (P2): export CSV do registro bruto */}
      {efic && efic.totalAnalises > 0 && (
        <div style={{ marginTop: "14px", display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <button onClick={exportCsv} style={{ padding: "9px 14px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 700, fontSize: "12px" }}>Exportar CSV</button>
          {csvSt && <span style={{ fontSize: "11px", color: T.textMuted }}>{csvSt}</span>}
        </div>
      )}
    </div>
  );
}

// qa/37 (P2e): mini-gráfico da curva de R acumulado. Linha de base 0 tracejada;
// cor pela ponta (verde >=0, vermelho <0). usePalette() (hex resolvido — var()
// não resolve em atributo SVG neste WebKit, mesmo padrão do Sparkline).
function RCurve({ pts, width = 300, height = 64 }) {
  const P = usePalette();
  const vals = (pts || []).filter((v) => typeof v === "number" && isFinite(v));
  if (!vals.length) return null;
  const serie = vals.length === 1 ? [0, vals[0]] : [0, ...vals]; // ancora em 0
  const mn = Math.min(0, ...serie), mx = Math.max(0, ...serie), sp = (mx - mn) || 1;
  const x = (i) => (i / (serie.length - 1)) * (width - 2) + 1;
  const y = (v) => (height - 3) - ((v - mn) / sp) * (height - 6);
  const d = serie.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
  const up = vals[vals.length - 1] >= 0;
  const y0 = y(0);
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ display: "block", height: height }} aria-hidden>
      <line x1="1" y1={y0.toFixed(1)} x2={width - 1} y2={y0.toFixed(1)} stroke={P.textFaint} strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
      <path d={d} fill="none" stroke={up ? P.positive : P.negative} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// qa/32 — LOGS & DEBUG: fusão de duas telas técnicas que viviam separadas —
// "Servidor do app" + "Diagnóstico QA" (antes dentro de Conta & preferências,
// disponíveis mesmo sem login) e "Observabilidade" (status do servidor,
// Diário do operador, logs detalhados — exige login). Mesmo comportamento de
// antes, só que reunido num único lugar de "coisas técnicas".
function LogsDebugScreen({ ctx }) {
  const { data, A } = ctx;
  const c = data.config;
  const logged = !!ctx.authUser;
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };

  // --- Servidor do app + Diagnóstico QA (ex-ConfigScreen) ---
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
    lines.push("Boris+ · Diagnóstico iOS/WebView");
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
        const id = await notify.schedule("Boris+ · teste QA", "Validação técnica de notificação local agendada.", new Date(Date.now() + 8000));
        lines.push("scheduledTestId=" + (id == null ? "falhou" : id));
        lines.push("ação=se estiver no iPhone, mande o app para segundo plano por 8 segundos para ver o banner.");
      } else {
        lines.push("ação=ative a permissão em Configurações → Notificações e rode o teste novamente.");
      }
      lines.push("");
    } catch (e) { lines.push("[Notificações] ERRO: " + (e.message || e)); lines.push(""); }
    lines.push("Checklist de correção rápida:");
    lines.push("1. API base deve ser URL absoluta, ex.: https://boris.semente.dev");
    lines.push("2. Se keySource=manual no iPhone, a chave precisa estar salva no próprio app.");
    lines.push("3. Se permissão=denied, corrigir em Ajustes do iOS → Notificações → Boris+.");
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

  // --- Observabilidade: status do servidor, Diário, logs (ex-ObservabilidadeScreen) ---
  const [srv, setSrv] = useState(null);
  const [srvErr, setSrvErr] = useState("");
  const [diario, setDiario] = useState(null);
  const [runSt, setRunSt] = useState("");
  const [pushSt, setPushSt] = useState("");
  // FASE 5: logs detalhados do servidor (restritos ao admin — 403 esconde a seção)
  const [obs, setObs] = useState(null);          // { logs, stats } | null
  const [obsDenied, setObsDenied] = useState(false);
  const [obsLevel, setObsLevel] = useState("");  // "" (tudo) | warn | error
  const loadSrv = useCallback(async () => {
    try { setSrv(await store.agentStatus()); setSrvErr(""); }
    catch (e) { setSrvErr((e && e.message) || String(e)); }
  }, []);
  const loadDiario = useCallback(async () => {
    try { setDiario(await store.agentLog(60)); } catch { /* diário é observabilidade; não quebra a tela */ }
  }, []);
  const loadObs = useCallback(async () => {
    try { setObs(await store.obsLogs(120, obsLevel || undefined)); setObsDenied(false); }
    catch (e) {
      const msg = (e && e.message) || "";
      if (/403|restrito|administrador/i.test(msg)) setObsDenied(true); // conta não-admin: seção some
      /* erro de rede: mantém o que tem — logs são observabilidade, não quebram a tela */
    }
  }, [obsLevel]);
  // F5 (2026-08-02, v1 SÓ VER): mesmo padrão do obsDenied acima — 403 esconde
  // a seção inteira em vez de mostrar erro (é o mesmo portão de admin que os
  // logs já usam; quem não é admin nem sabe que a seção existiria).
  const [admin, setAdmin] = useState(null);
  const [adminDenied, setAdminDenied] = useState(false);
  const loadAdmin = useCallback(async () => {
    try { setAdmin(await store.adminSummary()); setAdminDenied(false); }
    catch (e) {
      const msg = (e && e.message) || "";
      if (/403|restrito|administrador/i.test(msg)) setAdminDenied(true);
    }
  }, []);
  useEffect(() => {
    loadSrv(); loadDiario(); loadObs(); loadAdmin();
    const id = setInterval(() => { loadSrv(); loadDiario(); loadObs(); loadAdmin(); }, 15000);
    return () => clearInterval(id);
  }, [loadSrv, loadDiario, loadObs, loadAdmin]);
  const rodarAgora = async () => {
    setRunSt("disparando…");
    try {
      const s = await store.agentRunNow();
      setRunSt(s.mensagem || "ciclo iniciado — acompanhe o Diário abaixo");
      setTimeout(() => { loadDiario(); loadSrv(); }, 3000);
      setTimeout(() => { loadDiario(); A.putAgent({}); }, 10000);
    } catch (e) { setRunSt((e && e.message) || String(e)); }
  };
  const testarPush = async () => {
    setPushSt("testando…");
    try { const r = await store.pushTest(); setPushSt("push de teste enviado (" + r.enviados + "/" + r.total + " aparelho(s)) ✓"); loadDiario(); }
    catch (e) { setPushSt((e && e.message) || String(e)); loadDiario(); }
  };

  return (
    <div>
      <h1 style={{ margin: "0 0 6px", fontSize: "22px", fontWeight: 700 }}>Logs & debug</h1>
      <p style={{ margin: "0 0 18px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "580px" }}>
        Servidor do app, diagnóstico técnico e — para quem tem conta — status do Operador no servidor, Diário e logs detalhados.
      </p>

      {/* qa/35 (P1): RASTREABILIDADE — o snapshotId saiu das telas de consumo
          (Radar/N2/stop-alvo/posições) e vive SÓ aqui: uma linha por análise
          recente com o hash do STU, para auditar qual snapshot embasou o quê. */}
      {(() => {
        const rows = [];
        for (const [t, a] of Object.entries(ctx.analysis || {})) {
          if (a && a.snapshotId) rows.push({ t, kind: "análise", id: a.snapshotId, at: a.snapshotAt || a.at || "" });
        }
        for (const [t, s] of Object.entries(ctx.stopAlvo || {})) {
          if (s && s.snapshotId) rows.push({ t, kind: "stop/alvo", id: s.snapshotId, at: s.snapshotAt || s.at || "" });
        }
        if (!rows.length) return null;
        rows.sort((x, y) => String(y.at).localeCompare(String(x.at)));
        return (
          <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
            <div style={sectionTitle}>SNAPSHOTS DAS ANÁLISES</div>
            <p style={{ margin: "6px 0 10px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
              Hash do snapshot técnico (STU) que embasou cada análise recente — rastreabilidade de QA; não aparece nas telas de uso.
            </p>
            {rows.slice(0, 20).map((r2, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontFamily: MONO, fontSize: "11px", color: T.textFaint, padding: "4px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none" }}>
                <span style={{ color: T.textMuted }}>{r2.t} · {r2.kind}</span>
                <span>snapshot #{r2.id}{r2.at ? " · " + r2.at : ""}</span>
              </div>
            ))}
          </div>
        );
      })()}

      {/* Servidor do app (somente no iPhone) */}
      {isNative && (
        <div style={{ ...card, padding: "17px 18px", marginBottom: "16px" }}>
          <div style={sectionTitle}>SERVIDOR DO APP</div>
          <p style={{ margin: "6px 0 14px", color: T.textMuted, fontSize: "12.5px", lineHeight: 1.5, maxWidth: "560px" }}>
            O app já vem apontado para o servidor de <b>produção</b> — não precisa configurar nada para usar (login, cotações e IA funcionam de fábrica). Este campo é um <b>override de desenvolvimento</b>: preencha só para testar contra um Mac na rede local; deixe vazio para voltar à produção. Vale para o aparelho inteiro (qualquer conta).
          </p>
          <label style={{ display: "block", marginBottom: "12px" }}>
            <span style={{ display: "block", fontSize: "12px", color: T.textMuted, marginBottom: "6px" }}>Override do servidor (opcional — vazio = produção)</span>
            <input type="text" value={c.serverUrl || ""} onChange={(e) => A.editConfig({ serverUrl: e.target.value })} onBlur={(e) => A.saveConfig({ serverUrl: e.target.value })} placeholder="vazio = produção · dev: http://192.168.0.12:8787" style={{ ...field, fontFamily: MONO }} />
          </label>
          <div style={{ margin: "0 0 12px", fontFamily: MONO, fontSize: "11px", color: T.textFaint }}>em uso agora: {getApiBase()}</div>
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

      {!logged && (
        <div style={{ ...card, padding: "14px 16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "6px" }}>STATUS DO SERVIDOR</div>
          <p style={{ margin: 0, color: T.textMuted, fontSize: "13px", lineHeight: 1.5 }}>
            Entre na conta para ver o status do Operador no servidor, o Diário de ações/push e os logs detalhados — sem conta, o agente roda só em foreground e não há nada do servidor para observar.
          </p>
        </div>
      )}

      {logged && (
        <>
          <div style={{ ...card, padding: "14px 16px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em", marginBottom: "9px" }}>STATUS DO SERVIDOR</div>
            {srvErr && <div style={{ color: T.negative, fontSize: "11.5px" }}>status indisponível: {srvErr}</div>}
            {!srvErr && !srv && <div style={{ color: T.textFaint, fontSize: "11.5px" }}>consultando o servidor…</div>}
            {srv && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", color: T.textMuted, fontSize: "11.5px" }}>
                <span>pregão: <b style={{ color: srv.pregaoAberto ? T.positive : T.textFaint }}>{srv.pregaoAberto ? "aberto" : "fechado"}</b></span>
                <span>ciclo: <b style={{ color: T.textSecondary, fontFamily: MONO }}>{Math.round((srv.intervaloS || 300) / 60)} min</b></span>
                <span>kill-switch: <b style={{ color: srv.killSwitch ? T.negative : T.positive }}>{srv.killSwitch ? "LIGADO" : "desligado"}</b></span>
                <span>usuários com o operador ligado: <b style={{ color: T.textSecondary, fontFamily: MONO }}>{srv.usuariosHabilitados ?? "—"}</b></span>
                <span>último ciclo: <b style={{ color: T.textSecondary, fontFamily: MONO }}>{(srv.ultimoCiclo || {}).at || "ainda não rodou"}{(srv.passadas && srv.passadas[0]) ? ` (${srv.passadas[0].duracaoS}s)` : ""}</b></span>
                {srv.proximaPassadaEmS != null && <span>próxima passada: <b style={{ color: T.textSecondary, fontFamily: MONO }}>~{srv.proximaPassadaEmS >= 60 ? Math.round(srv.proximaPassadaEmS / 60) + " min" : srv.proximaPassadaEmS + "s"}</b></span>}
                {(srv.ultimoCiclo || {}).erro && <span style={{ color: T.negative }}>erro: <b>{srv.ultimoCiclo.erro}</b></span>}
                <span>push: <b style={{ color: (srv.push || {}).configurado ? T.positive : T.textFaint }}>{(srv.push || {}).configurado ? "configurado" : "não configurado"}</b>{(srv.push || {}).meusAparelhos ? ` · ${srv.push.meusAparelhos} aparelho(s) meu(s)` : ""}</span>
              </div>
            )}
            <div style={{ display: "flex", gap: "8px", marginTop: "11px", flexWrap: "wrap", alignItems: "center" }}>
              <button onClick={rodarAgora} style={{ padding: "8px 13px", borderRadius: "9px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "11.5px" }}>▶ Rodar ciclo agora (servidor)</button>
              <button onClick={testarPush} style={{ padding: "8px 13px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "11.5px" }}>Testar push agora</button>
              {runSt && <span style={{ color: T.textMuted, fontSize: "11.5px" }}>{runSt}</span>}
              {pushSt && <span style={{ color: T.textMuted, fontSize: "11.5px" }}>{pushSt}</span>}
            </div>
          </div>

          {/* DIÁRIO DO OPERADOR: o log vivo do servidor — o que rodou, quanto
              demorou, o que falhou e por quê (inclui as tentativas de push). */}
          <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "8px" }}>
              <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em" }}>DIÁRIO DO OPERADOR (servidor)</div>
              <button onClick={loadDiario} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 800, padding: "4px" }}>↻ atualizar</button>
            </div>
            {!diario && <div style={{ fontSize: "11.5px", color: T.textFaint }}>carregando o diário…</div>}
            {diario && (!diario.log || diario.log.length === 0) && (
              <div style={{ fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>Nenhum registro ainda — ligue o operador no servidor (aba Operador IA), toque em "Rodar ciclo agora" ou "Testar push agora"; cada tentativa entra aqui com o resultado exato.</div>
            )}
            {diario && (diario.log || []).slice(0, 30).map((e, i) => {
              const kc = e.kind === "buy" ? T.positive : e.kind === "warn" ? T.warn : e.kind === "error" ? T.negative : T.textFaint;
              return (
                <div key={i} style={{ display: "flex", gap: "9px", alignItems: "flex-start", padding: "7px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none" }}>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: kc, flex: "none", marginTop: "5px" }} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: "11.5px", color: e.kind === "error" ? T.negative : T.textSecondary, lineHeight: 1.5 }}>{e.text}</div>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: T.textFaint, marginTop: "1px" }}>{e.time || ""}</div>
                  </div>
                </div>
              );
            })}
            {srv && srv.passadas && srv.passadas.length > 0 && (
              <div style={{ marginTop: "11px", paddingTop: "9px", borderTop: `1px solid ${T.borderFaint}` }}>
                <div style={{ fontSize: "10px", fontWeight: 800, color: T.textFaint, letterSpacing: "0.05em", marginBottom: "5px" }}>PASSADAS DO SCHEDULER (todas as contas)</div>
                {srv.passadas.slice(0, 5).map((p, i) => (
                  <div key={i} style={{ display: "flex", gap: "10px", fontFamily: MONO, fontSize: "10.5px", color: T.textMuted, padding: "3px 0" }}>
                    <span>{p.at}</span><span>{p.duracaoS}s</span><span>{p.usuarios} usuário(s)</span><span>{p.executadas} exec.</span>
                    {p.erros && p.erros.length > 0 && <span style={{ color: T.negative }}>{p.erros.length} erro(s)</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* FASE 5 — LOGS DETALHADOS DO SERVIDOR: toda request (rota, status,
              duração), lentidões, erros e eventos de auth/agente, direto do ring
              buffer do backend — sem precisar abrir o painel do Railway. Restrito
              ao admin (B3_ADMIN_EMAILS ou a primeira conta criada). */}
          {!obsDenied && (
            <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "8px", flexWrap: "wrap" }}>
                <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em" }}>LOGS DO SERVIDOR (detalhado)</div>
                <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                  {["", "warn", "error"].map((lv) => (
                    <button key={lv || "all"} onClick={() => setObsLevel(lv)} style={{ padding: "4px 9px", borderRadius: "999px", border: `1px solid ${obsLevel === lv ? T.accent : T.borderSubtle}`, background: obsLevel === lv ? T.accentTint : "transparent", color: obsLevel === lv ? T.accent : T.textFaint, fontSize: "10.5px", fontWeight: 800 }}>
                      {lv === "" ? "tudo" : lv === "warn" ? "lentos+erros" : "só erros"}
                    </button>
                  ))}
                  <button onClick={loadObs} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 800, padding: "4px" }}>↻</button>
                </div>
              </div>
              {obs && obs.stats && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 12px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO, marginBottom: "8px" }}>
                  <span>uptime {Math.floor((obs.stats.uptimeS || 0) / 3600)}h{Math.floor(((obs.stats.uptimeS || 0) % 3600) / 60)}m</span>
                  {Object.entries(obs.stats.porCategoria || {}).map(([c2, lv]) => (
                    <span key={c2}>{c2}: {Object.entries(lv).map(([k, v]) => k + "=" + v).join(" ")}</span>
                  ))}
                </div>
              )}
              {!obs && <div style={{ fontSize: "11.5px", color: T.textFaint }}>carregando logs do servidor…</div>}
              {obs && (obs.logs || []).length === 0 && <div style={{ fontSize: "11.5px", color: T.textFaint }}>nenhum evento registrado {obsLevel ? "neste filtro" : "desde o boot"}.</div>}
              <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                {obs && (obs.logs || []).map((e, i) => {
                  const lc = e.level === "error" ? T.negative : e.level === "warn" ? T.warn : T.textFaint;
                  return (
                    <div key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start", padding: "4px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", fontFamily: MONO, fontSize: "10.5px", lineHeight: 1.5 }}>
                      <span style={{ color: T.textFaint, flex: "none" }}>{e.ts}</span>
                      <span style={{ color: lc, fontWeight: 800, flex: "none", minWidth: "36px" }}>{e.cat}</span>
                      <span style={{ color: e.level === "error" ? T.negative : T.textMuted, wordBreak: "break-word" }}>{e.msg}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* F5 (2026-08-02) — PAINEL DE ADMINISTRAÇÃO, v1 SÓ VER (decisão do
              Alex: sem ação nenhuma nesta versão — nenhum botão aqui muda
              estado de ninguém). Mesmo portão de admin dos logs acima. */}
          {!adminDenied && admin && (
            <div style={{ marginTop: "14px", ...card, padding: "14px 16px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "10px" }}>
                <div style={{ fontSize: "11px", fontWeight: 800, color: T.textSecondary, letterSpacing: "0.05em" }}>ADMINISTRAÇÃO</div>
                <button onClick={loadAdmin} style={{ background: "transparent", border: "none", color: T.textFaint, fontSize: "11px", fontWeight: 800, padding: "4px" }}>↻</button>
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 14px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO, marginBottom: "12px" }}>
                <span>{admin.totalUsuarios} usuário(s) cadastrado(s)</span>
                <span>IA gerenciada: {admin.usoIA.iaGerenciadaAtiva ? "ativa" : "desligada"}</span>
                <span>cadastro obrigatório: {admin.gate.ativo ? admin.gate.hostsFechados.join(", ") : "nenhum domínio (todos abertos)"}</span>
              </div>

              <div style={{ fontSize: "10.5px", fontWeight: 800, color: T.textMuted, marginBottom: "6px" }}>USUÁRIOS</div>
              <div style={{ maxHeight: "220px", overflowY: "auto", marginBottom: "12px" }}>
                {admin.usuarios.length === 0 && <div style={{ fontSize: "11.5px", color: T.textFaint }}>nenhum usuário cadastrado ainda.</div>}
                {admin.usuarios.map((u, i) => (
                  <div key={u.id} style={{ display: "flex", justifyContent: "space-between", gap: "8px", padding: "4px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", fontFamily: MONO, fontSize: "10.5px" }}>
                    <span style={{ color: T.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{u.email || "(sem e-mail)"} · {u.provider}</span>
                    <span style={{ color: T.textFaint, flex: "none" }}>{u.created_at}</span>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: "10.5px", fontWeight: 800, color: T.textMuted, marginBottom: "6px" }}>USO DE IA (hoje)</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 14px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO, marginBottom: "12px" }}>
                <span>cota/usuário/dia: {admin.usoIA.cotaPorUsuarioDia ?? "—"}</span>
                <span>teto global/dia: {admin.usoIA.tetoGlobalDia ?? "ilimitado"}</span>
                {admin.usoIA.legacyAnalyze && admin.usoIA.legacyAnalyze.count > 0 && (
                  <span style={{ color: T.warn }}>rota legada: {admin.usoIA.legacyAnalyze.count} chamada(s) desde o deploy</span>
                )}
              </div>

              <div style={{ fontSize: "10.5px", fontWeight: 800, color: T.textMuted, marginBottom: "6px" }}>AGENTE (servidor)</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 14px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO }}>
                <span>kill switch: {admin.agente.killSwitch ? "ligado (parado)" : "desligado (rodando)"}</span>
                <span>intervalo: {admin.agente.intervaloS}s</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* BLOCO 3 — Radar de mercado. Varre o universo no SERVIDOR (cache-first) e
   lista, por ativo, as condições técnicas detectadas pelo motor de sinais.
   Linguagem 100% descritiva/educacional (nada de "compre/venda/entre agora");
   o score é INTENSIDADE de sinais, não direção. Período = candlePeriod da
   Config (mesma config nos dois stores). */
const RADAR_PERIOD_LABEL = { "1mo": "1M", "3mo": "3M", "6mo": "6M", "1y": "1A", "2y": "2A" };
// qa/mock v2: SPARKLINE inline (série de fechamentos vinda do scan — campo
// `spark`) para os cards da Watchlist. Cor pela direção do período. usePalette()
// dá o hex resolvido (var(--x) não resolve em atributo SVG neste WebKit).
function Sparkline({ data, width = 84, height = 22 }) {
  const P = usePalette();
  const vals = (data || []).filter((v) => typeof v === "number" && isFinite(v));
  if (vals.length < 2) return null;
  const mn = Math.min(...vals), mx = Math.max(...vals), sp = (mx - mn) || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const pts = vals.map((v, i) => [(i / (vals.length - 1)) * width, (height - 2) - ((v - mn) / sp) * (height - 4)]);
  const d = pts.map((pt, i) => (i ? "L" : "M") + pt[0].toFixed(1) + "," + pt[1].toFixed(1)).join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ flex: "none", display: "block" }} aria-hidden>
      <path d={d} fill="none" stroke={up ? P.positive : P.negative} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// qa/mock v2: ANEL de confluência — substitui a barra plana. Cor por tier
// (forte/moderada/fraca), % no centro. Usa usePalette() (hex resolvido, já com
// override do Modo Operador) — var(--x) não resolve em atributo SVG neste WebKit.
function ConfluenceRing({ conf, size = 54, label = true }) {
  const P = usePalette();
  const c = Math.max(0, Math.min(100, Number(conf) || 0));
  const cx = size / 2;
  const r = cx - 4;
  const C = 2 * Math.PI * r;
  const off = C * (1 - c / 100);
  const col = c >= 75 ? P.positive : c >= 50 ? P.accent : P.textFaint;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flex: "none" }} role="img" aria-label={`Confluência ${c}%`}>
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={P.borderFaint} strokeWidth="4" />
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={col} strokeWidth="4" strokeLinecap="round"
        strokeDasharray={C.toFixed(1)} strokeDashoffset={off.toFixed(1)} transform={`rotate(-90 ${cx} ${cx})`} />
      {label && <text x={cx} y={cx} textAnchor="middle" dominantBaseline="central" fontFamily={MONO} fontSize={Math.round(size * 0.26)} fontWeight="800" fill={P.textPrimary}>{c}%</text>}
    </svg>
  );
}

function RadarScreen({ ctx }) {
  const { data, cp } = ctx;   // FASE 8B (B1): fraseologia por modo
  const period = (data.config && data.config.candlePeriod) || "1y";
  const [st, setSt] = useState({ busy: false, res: null, error: "" });
  const [showModel, setShowModel] = useState(false);
  const [openTicker, setOpenTicker] = useState(null);
  // FASE 2 (2.1): aprofundamento IA (N1) — leituras por ativo + lote top-N
  const [deep, setDeep] = useState({});         // ticker -> {loading,res,error,cache,disclaimer}
  const [deepFor, setDeepFor] = useState(null); // ticker do modal aberto
  const [batch, setBatch] = useState({ stage: "idle", busy: false, est: null, error: "" });
  const runDeep = useCallback(async (t) => {
    setDeepFor(t);
    setDeep((d) => (d[t] && (d[t].res || d[t].loading)) ? d : ({ ...d, [t]: { loading: true } }));
    try {
      const cur = deep[t];
      if (cur && cur.res) return;                       // já aprofundado nesta sessão
      const r = await store.scanDeep({ period, tickers: t, topN: 1 });
      const item = (r.results || [])[0];
      if (!item || !item.deep) throw new Error((r.errors && r.errors[0] && r.errors[0].erro) || ("sem leitura para " + t));
      setDeep((d) => ({ ...d, [t]: { loading: false, res: item.deep, cache: !!item.cache, disclaimer: r.disclaimer } }));
    } catch (e) {
      setDeep((d) => ({ ...d, [t]: { loading: false, error: (e && e.message) || String(e) } }));
    }
  }, [period, deep]);
  // BLOCO B1/B2: enquanto o scan roda, sonda /api/scan/progress p/ o gauge
  const [prog, setProg] = useState(null);
  useEffect(() => {
    if (!st.busy) { setProg(null); return; }
    let alive = true;
    const tick = async () => {
      try { const p = await store.scanProgress(); if (alive && p && p.ativo) setProg(p); } catch { /* gauge é best-effort */ }
    };
    tick();
    const id = setInterval(tick, 900);
    return () => { alive = false; clearInterval(id); };
  }, [st.busy]);
  const runBatch = useCallback(async () => {
    if (batch.stage !== "confirm") {
      // 1º toque: mostra o CUSTO (chamadas novas de IA) antes de rodar
      setBatch({ stage: "confirm", busy: true, est: null, error: "" });
      try { const est = await store.scanDeepEstimate(period); setBatch({ stage: "confirm", busy: false, est, error: "" }); }
      catch (e) { setBatch({ stage: "idle", busy: false, est: null, error: (e && e.message) || String(e) }); }
      return;
    }
    setBatch((b) => ({ ...b, busy: true }));
    try {
      const r = await store.scanDeep({ period });
      const next = {};
      for (const it of (r.results || [])) if (it.deep) next[it.ticker] = { loading: false, res: it.deep, cache: !!it.cache, disclaimer: r.disclaimer };
      setDeep((d) => ({ ...d, ...next }));
      setBatch({ stage: "idle", busy: false, est: null, error: "" });
    } catch (e) { setBatch({ stage: "idle", busy: false, est: null, error: (e && e.message) || String(e) }); }
  }, [batch.stage, period]);
  const ranFor = useRef(null);
  const run = useCallback(async (p, force) => {
    // FASE 4 (1.3): sem force = serve o RESULTADO DO DIA armazenado no servidor
    // (instantâneo); force = varredura manual, que recomputa e vira a "do dia".
    setSt((s) => ({ ...s, busy: true, error: "" }));
    try {
      const r = await store.scan(p, undefined, force);
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
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", marginBottom: "6px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "2px", minWidth: 0 }}>
          <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700, letterSpacing: "-0.01em" }}>{cp.tituloRadar}</h1>
          <InfoDot onClick={ctx.A.openAbout} />
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button onClick={runBatch} disabled={batch.busy || st.busy || !res} style={{ minHeight: "36px", padding: "7px 12px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: batch.stage === "confirm" ? T.accent : T.accentTint, color: batch.stage === "confirm" ? T.onAccent : T.accent, fontWeight: 800, fontSize: "12px", opacity: (batch.busy || st.busy || !res) ? 0.6 : 1 }}>
            {batch.busy ? "…" : batch.stage === "confirm" && batch.est ? `Confirmar: ${batch.est.chamadas} chamada${batch.est.chamadas === 1 ? "" : "s"} de IA` : "IA no top-N"}
          </button>
          <IconBtn label="Varrer novamente" onClick={() => run(period, true)} busy={st.busy}>↻</IconBtn>
        </div>
      </div>
      {batch.stage === "confirm" && batch.est && (
        <div style={{ margin: "0 0 10px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
          Top {batch.est.topN}: {(batch.est.selecionados || []).join(", ")} · {(batch.est.emCache || []).length} já no cache de hoje (grátis) · toque de novo para confirmar.
        </div>
      )}
      {batch.error && <div style={{ margin: "0 0 10px", fontSize: "11.5px", color: T.negative }}>{batch.error}</div>}
      <p style={{ margin: "0 0 12px", color: T.textMuted, fontSize: "13px", maxWidth: "560px", lineHeight: 1.55 }}>{cp.subtituloRadar}</p>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "14px" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 10px", borderRadius: "999px", background: T.accentTint, border: `1px solid ${T.accent}`, color: T.accent, fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em" }}>
          PERÍODO EM USO: {RADAR_PERIOD_LABEL[period] || period}{res ? " · " + res.periodBars + " pregões" : ""}
        </span>
        {res && res.scanAtLabel && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 10px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textMuted, fontSize: "11px", fontWeight: 700 }}>
            {res.scanAuto ? "📡 Varredura automática de hoje" : "↻ Última varredura (manual)"} · {res.scanAtLabel}
          </span>
        )}
        {res && (
          <span style={{ fontSize: "11.5px", color: T.textFaint }}>
            {res.scanned}/{res.universeSize} ativos varridos{res.errors && res.errors.length ? " · " + res.errors.length + " sem dados" : ""} · {res.timestamp}
          </span>
        )}
      </div>

      {res && res.modelo && (
        <div style={{ ...card, padding: "13px 16px", marginBottom: "14px" }}>
          <button onClick={() => setShowModel(!showModel)} style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "center", background: "transparent", border: "none", color: T.textSecondary, fontSize: "12px", fontWeight: 800, letterSpacing: "0.05em", padding: 0 }}>
            {/* qa/34: título e corpo na voz do modo — "O veredito é sempre de
                estudo, nunca uma ordem" aparecia ATÉ na mesa do Operador. */}
            <span>{cp.comoAnalisaTitulo}</span><span style={{ color: T.accent }}>{showModel ? "−" : "+"}</span>
          </button>
          {showModel && (
            <div style={{ marginTop: "10px" }}>
              <p style={{ margin: "0 0 10px", color: T.textMuted, fontSize: "12px", lineHeight: 1.55 }}>
                {cp.comoAnalisaCorpo}
              </p>
              {res.modelo.map((m, i) => (
                <div key={i} style={{ padding: "8px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700 }}>{m.nome}</div>
                  <div style={{ fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5, marginTop: "2px" }}>{m.descricao}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {st.busy && !res && (
        <div style={{ ...card, padding: "18px 20px", marginBottom: "14px" }}>
          <SweepGauge progress={prog} label="Varrendo o universo…" steps={["carregando históricos para o cache", "calculando indicadores e setups", "rankeando por confluência"]} />
          <p style={{ margin: "10px 0 0", color: T.textMuted, fontSize: "12px", lineHeight: 1.5 }}>
            A primeira varredura do dia aquece o cache de todos os ativos; as próximas só atualizam a análise e voltam em segundos.
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
          const [vColor, vBg] = REC_STYLE[r.veredito] || [T.textMuted, T.bgBase];
          const isOpen = openTicker === r.ticker;
          // FASE 3 (mock v2): posição no portfólio + presença na watchlist + plano do setup
          const posR = (data.positions || []).find((p) => p.t === r.ticker);
          const naWl = (data.watchlist || []).includes(r.ticker);
          const s0 = (r.setups || [])[0];
          // FASE 7 (F7.1) — Modo Operador: decisão direta + plano do servidor.
          // O plano vem SEMPRE no payload (determinístico, do setups.py); a UI
          // só o exibe neste modo — o Estudo permanece intocado.
          const operador = (data.config && data.config.appMode) === "operador";
          const plano = operador ? r.plano : null;
          const opStyle = plano ? ({
            "COMPRAR": [T.positive, "rgba(52,211,153,.15)", "▲ "],
            "VENDER": [T.negative, "rgba(248,113,113,.15)", "▼ "],
            "AGUARDAR CONFIRMAÇÃO": [T.accent, T.accentTint, "◔ "],
          }[plano.decisao] || [T.textFaint, T.bgBase, "✕ "]) : null;
          const cRisco = (data.config && data.config.risco) || {};
          const capitalOp = typeof cRisco.capital === "number" ? cRisco.capital : (data.config && data.config.initialBudget) || null;
          const siz = plano ? sizingPlano(plano, capitalOp, cRisco.pctPorTrade || 1) : null;
          // qa/34 (P3): leitura inicial rápida — tier de confiança + critérios
          // atendidos do melhor setup, ambos derivados do payload já existente.
          const tierLabel = tierOf(r.confluencia)[1];
          const critTot = s0 ? (s0.criterios || []).length : 0;
          const critOk = s0 ? (s0.criterios || []).filter((c) => c.ok).length : 0;
          // qa/49 (v11, incremento 2): o Radar usa o CARD ÚNICO no cabeçalho
          // (identidade + preço + manchete). O corpo rico do Radar (plano,
          // confluence ring, aprofundar, critérios) segue como children.
          const decMr = decisaoDoModo(r, operador);
          const [decColorR, decBgR] = REC_STYLE[decMr] || [vColor, vBg];
          const nameR = (data.catalog.find((c) => c.t === r.ticker) || {}).n || r.ticker;
          const pnlR = posR && r.close != null ? (r.close - posR.avg) * posR.qty : null;
          const pnlPctR = posR && r.close != null && posR.avg > 0 ? (r.close / posR.avg - 1) * 100 : null;
          const radarVm = { t: r.ticker, name: nameR, q: { price: r.close, change: r.variacaoPeriodoPct, error: false }, chColor, sc: { spark: r.spark, confluencia: r.confluencia, melhorSetup: r.melhorSetup }, pos: posR, cur: r.close, pnl: pnlR, pnlPct: pnlPctR, kp: {}, fscore: r.fundamento && r.fundamento.score, decM: decMr, decColor: decColorR, decBg: decBgR, quotesLoading: false, operador, A: ctx.A, data: ctx.data, didatica: ctx.didatica, overlayLivre: ctx.overlayLivre };
          return (
            <AtivoCard key={r.ticker} vm={radarVm} contexto="radar">
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginTop: "11px" }}>
                {/* qa/49: a decisão vem da MANCHETE do AtivoCard; aqui fica a confiança/fundamento/setup */}
                {/* qa/34 (P3): pill de confiança (tierOf) ao lado da decisão, como no
                    mock modo-operador.html ("confiança MODERADA"). */}
                <span style={{ padding: "4px 9px", borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, color: T.textMuted, fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em" }}>confiança {tierLabel.toUpperCase()}</span>
                {/* qa/36 (F10.2): chip de score de fundamento (filtro de qualidade)
                    — do cache do servidor; ausente = ticker sem cobertura. */}
                <FundamentoChip f={r.fundamento} />
                {r.melhorSetup && <span style={{ fontSize: "11.5px", color: T.textMuted }}>{r.melhorSetup}{critTot > 0 ? ` · ${critOk}/${critTot} critérios` : ""}</span>}
              </div>
              {/* qa/34 (P1): leitura inicial rápida no Modo Estudo — o `motivo`
                  determinístico do plano (setups.py) sempre veio no payload, mas
                  só era exibido no Operador. Zero custo de LLM. */}
              {!operador && r.plano && r.plano.motivo && (
                <div style={{ marginTop: "9px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>{r.plano.motivo}</div>
              )}
              {/* FASE 7 (F7.1): plano operacional — só no Modo Operador */}
              {plano && (plano.decisao === "COMPRAR" || plano.decisao === "VENDER") && (
                <div style={{ marginTop: "10px", padding: "11px 12px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  {[
                    ["Entrada (" + (plano.tipo || "") + ")", "R$ " + price(plano.entrada), T.textSecondary],
                    ["Stop (invalidação do setup)", "R$ " + price(plano.stop), T.negative],
                    ["Alvo 1 (parcial, 1R) / Alvo final", price(plano.alvo1) + " / " + price(plano.alvo2), T.positive],
                    ["Risco:retorno (alvo final)", (plano.rr2 != null ? plano.rr2.toFixed(1).replace(".", ",") : "—") + " : 1", T.textSecondary],
                  ].map(([k, v, cor], i2) => (
                    <div key={i2} style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "11.5px", padding: "3px 0", color: T.textMuted }}>
                      <span>{k}</span><b style={{ fontFamily: MONO, color: cor }}>{v}</b>
                    </div>
                  ))}
                  {siz && (
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "11.5px", padding: "3px 0", color: T.textMuted, borderTop: `1px dashed ${T.borderFaint}`, marginTop: "4px", paddingTop: "7px" }}>
                      <span>Posição p/ risco de {siz.pct}%{typeof cRisco.capital === "number" ? "" : " (capital simulado — defina o real na Config)"}</span>
                      <b style={{ fontFamily: MONO, color: T.textSecondary }}>{siz.qtd > 0 ? siz.qtd + " ações ≈ R$ " + price(siz.valorAprox) : "—"}</b>
                    </div>
                  )}
                  {siz && siz.aviso && <div style={{ fontSize: "10.5px", color: T.negative, marginTop: "5px", lineHeight: 1.4 }}>{siz.aviso}</div>}
                </div>
              )}
              {plano && plano.decisao !== "COMPRAR" && plano.decisao !== "VENDER" && plano.motivo && (
                <div style={{ marginTop: "9px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>{plano.motivo}</div>
              )}
              {/* qa/mock v2: anel de confluência no lugar da barra plana. */}
              <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "13px" }}>
                <ConfluenceRing conf={r.confluencia} size={54} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: "10.5px", color: T.textFaint, letterSpacing: "0.05em", fontWeight: 700 }}>CONFLUÊNCIA DO SETUP</div>
                  <div style={{ fontSize: "12px", color: T.textMuted, marginTop: "3px", lineHeight: 1.4 }}>{tierOf(r.confluencia)[0]} {tierOf(r.confluencia)[1]} · aderência ao padrão de estudo</div>
                </div>
              </div>
              {/* FASE 3 (mock v2): régua do PLANO — invalidação → gatilho → alvo, com o preço "agora" */}
              {s0 && s0.gatilho != null && s0.invalidacao != null && s0.alvoSugerido != null && (
                <PlanRuler
                  caption="PLANO DO SETUP (didático)"
                  marks={[{ v: s0.invalidacao, color: T.negative }, { v: s0.gatilho, color: T.accent }, { v: s0.alvoSugerido, color: T.positive }]}
                  cur={r.close}
                  curLabel={r.close != null ? "agora " + price(r.close) : null}
                  legend={[
                    { k: "INVALIDAÇÃO", v: s0.invalidacao, color: T.negative },
                    { k: "GATILHO", kColor: T.accent, v: s0.gatilho },
                    { k: "ALVO 2:1", v: s0.alvoSugerido, color: T.positive },
                  ]}
                />
              )}
              {/* FASE 2 (2.1): jornada — aprofundar (N1) ou avaliar por completo (N2) */}
              <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                <button onClick={() => runDeep(r.ticker)} style={{ flex: 1, minHeight: "38px", padding: "8px", borderRadius: "10px", border: `1px solid ${T.accent}`, background: (deep[r.ticker] && deep[r.ticker].res) ? T.accent : T.accentTint10, color: (deep[r.ticker] && deep[r.ticker].res) ? T.onAccent : T.accent, fontWeight: 700, fontSize: "12px" }}>
                  {deep[r.ticker] && deep[r.ticker].loading ? "IA lendo…" : deep[r.ticker] && deep[r.ticker].res ? "Leitura da IA ✓" : cp.btnAprofundar}
                </button>
                {/* qa/34: CTA de monitoramento na voz do modo ("+ Watchlist" ×
                    "+ Monitorar") — antes hardcodado. */}
                {naWl ? (
                  <button disabled style={{ flex: 1, minHeight: "38px", padding: "8px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textFaint, fontWeight: 700, fontSize: "12px" }}>
                    {cp.jaMonitorado}
                  </button>
                ) : (
                  <button onClick={() => ctx.A.addToWatchlist(r.ticker)} style={{ flex: 1, minHeight: "38px", padding: "8px", borderRadius: "10px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "12px" }}>
                    {cp.btnAddMonitor}
                  </button>
                )}
              </div>
              {r.setups && r.setups.length > 0 && (
                <button onClick={() => setOpenTicker(isOpen ? null : r.ticker)} style={{ marginTop: "10px", background: "transparent", border: "none", color: T.accent, fontSize: "12px", fontWeight: 700, padding: 0 }}>
                  {isOpen ? "− Ocultar critérios" : "+ Ver critérios do setup"}
                </button>
              )}
              {isOpen && (r.setups || []).map((s, si) => (
                <div key={si} style={{ marginTop: "9px", padding: "10px 11px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "12px", fontWeight: 700 }}>
                    <span>{s.nome}</span><span style={{ fontFamily: MONO, color: T.textSecondary }}>{s.confluencia}%</span>
                  </div>
                  {(s.criterios || []).map((cr, ci) => (
                    <div key={ci} style={{ display: "flex", gap: "7px", alignItems: "flex-start", marginTop: "6px", fontSize: "11.5px", lineHeight: 1.45 }}>
                      <span style={{ color: cr.ok ? T.positive : T.textFaint, fontWeight: 800, flex: "none" }}>{cr.ok ? "✓" : "○"}</span>
                      <span style={{ color: cr.ok ? T.textSecondary : T.textFaint }}>{cr.criterio}</span>
                    </div>
                  ))}
                </div>
              ))}
              {r.condicoes_detectadas && r.condicoes_detectadas.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "11px" }}>
                  {r.condicoes_detectadas.slice(0, isOpen ? 99 : 3).map((cnd, i) => (
                    <span key={i} style={{ padding: "5px 9px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textSecondary, fontSize: "11px", fontWeight: 600, lineHeight: 1.35 }}>{cnd}</span>
                  ))}
                  {!isOpen && r.condicoes_detectadas.length > 3 && (
                    <button onClick={() => setOpenTicker(r.ticker)} style={{ padding: "5px 9px", borderRadius: "999px", background: "transparent", border: `1px dashed ${T.borderSubtle}`, color: T.textFaint, fontSize: "11px", fontWeight: 700 }}>+{r.condicoes_detectadas.length - 3} condições</button>
                  )}
                </div>
              )}
            </AtivoCard>
          );
        })}
      </div>

      <div style={{ ...card, padding: "13px 16px", marginTop: "16px", background: T.bgPanel }}>
        {/* FASE 7 (F7.1): no Modo Operador vale o aviso da persona (risco real) */}
        <div style={{ fontSize: "11.5px", color: T.accent, lineHeight: 1.55 }}>{(data.config && data.config.appMode) === "operador" ? DISCLAIMERS.operador : DISCLAIMERS.radar}</div>
      </div>
      {deepFor && <DeepModal t={deepFor} d={deep[deepFor] || {}} cp={cp} onClose={() => setDeepFor(null)} onAvaliar={() => { const t = deepFor; setDeepFor(null); ctx.openAvaliar(t); }} />}
    </div>
  );
}

// BLOCO B2 — SweepGauge: o "radar girando" do Boris+. Um componente para TODA
// operação longa. Dois modos: determinado (progress {feitos,total,atual,fase,
// ultimos} do /api/scan/progress) e indeterminado (steps: etapas nomeadas que
// rotacionam). Anel cônico com varredura, ticker pulsando no centro, contador
// e micro-log — a espera vira informação, não congelamento.
function SweepGauge({ progress, steps, label, compact }) {
  const [stepIx, setStepIx] = useState(0);
  useEffect(() => {
    if (!steps || !steps.length) return;
    const id = setInterval(() => setStepIx((i) => (i + 1) % steps.length), 1800);
    return () => clearInterval(id);
  }, [steps]);
  const det = progress && progress.total > 0;
  const pct = det ? Math.min(100, Math.round((progress.feitos / progress.total) * 100)) : null;
  const size = compact ? 44 : 92;
  const ring = det
    ? `conic-gradient(${T.accent} ${pct * 3.6}deg, ${T.borderFaint} 0deg)`
    : `conic-gradient(from 0deg, transparent 0deg, ${T.accent} 40deg, transparent 80deg)`;
  const center = det ? (progress.atual || "…") : (label || "…");
  return (
    <div role="status" aria-live="polite" style={{ display: "flex", alignItems: "center", gap: compact ? "10px" : "14px", padding: compact ? "2px 0" : "6px 0" }}>
      <div style={{ position: "relative", width: size, height: size, flex: "none" }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: ring, animation: det ? "none" : "sweepspin 1.3s linear infinite" }} />
        <div style={{ position: "absolute", inset: compact ? "5px" : "8px", borderRadius: "50%", background: T.bgPanel, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontFamily: MONO, fontWeight: 800, fontSize: compact ? "8.5px" : "12px", color: T.accent, animation: "sweeppulse 1.2s ease-in-out infinite", maxWidth: "90%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {det ? center : (pct != null ? pct + "%" : "IA")}
          </span>
        </div>
      </div>
      <div style={{ minWidth: 0 }}>
        {det ? (
          <>
            <div style={{ fontSize: compact ? "12px" : "13.5px", fontWeight: 800 }}>
              {progress.fase || "varrendo"} <span style={{ fontFamily: MONO, color: T.accent }}>{progress.feitos}/{progress.total}</span>
            </div>
            {!compact && (progress.ultimos || []).length > 0 && (
              <div style={{ fontSize: "11px", color: T.textFaint, marginTop: "3px", fontFamily: MONO }}>
                {(progress.ultimos || []).join(" · ")}
              </div>
            )}
          </>
        ) : (
          <>
            <div style={{ fontSize: compact ? "12px" : "13.5px", fontWeight: 800 }}>{label || "Trabalhando…"}</div>
            {steps && steps.length > 0 && (
              <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "3px" }}>{steps[stepIx]}</div>
            )}
          </>
        )}
      </div>
      <style>{`@keyframes sweepspin{to{transform:rotate(360deg)}}@keyframes sweeppulse{0%,100%{opacity:1}50%{opacity:0.45}}`}</style>
    </div>
  );
}

// FASE 2 (2.1) — leitura aprofundada da IA (N1) de UM ativo do Radar.
// Renderiza o JSON estruturado do analyze_deep: leitura por setup (critérios
// presentes/ausentes), cenários de ESTUDO, riscos, invalidação e o bloco
// educacional "Modelos utilizados". Vocabulário fixo — nunca ordem de operação.
// FASE 4 (1.4): seção colapsável do DeepModal — o resumo fica aberto; o resto
// abre sob demanda (mesmo padrão do "+ Modelos utilizados" que já existia).
function Fold({ title, count, children, open0 }) {
  const [open, setOpen] = useState(!!open0);
  return (
    <div style={{ marginBottom: "9px" }}>
      <button onClick={() => setOpen(!open)} style={{ background: "transparent", border: "none", color: T.accent, fontSize: "12px", fontWeight: 800, padding: 0, letterSpacing: "0.03em" }}>
        {(open ? "− " : "+ ") + title + (count != null ? " (" + count + ")" : "")}
      </button>
      {open && <div style={{ marginTop: "7px" }}>{children}</div>}
    </div>
  );
}

function DeepModal({ t, d, onClose, onAvaliar, cp }) {
  const [showModels, setShowModels] = useState(false);
  const r = d.res || {};
  const cen = r.cenarios || {};
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 55, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "520px", maxHeight: "86vh", display: "flex", flexDirection: "column", overflow: "hidden", ...card, borderRadius: "14px" }}>
        <div style={{ padding: "15px 18px", borderBottom: `1px solid ${T.borderSubtle}`, flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
            <div style={{ fontSize: "16px", fontWeight: 800, fontFamily: MONO }}>{cp ? cp.tituloLeituraIA(t) : t + " · leitura da IA"}</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {r.planoEstudo && <span style={{ padding: "4px 10px", borderRadius: "999px", background: T.accentTint, color: T.accent, fontSize: "11px", fontWeight: 800 }}>{r.planoEstudo}</span>}
              {/* FASE 4 (1.4): fechar SEMPRE visível — o rodapé pode sair da tela em leituras longas */}
              <button onClick={onClose} aria-label="Fechar" style={{ width: "30px", height: "30px", borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontSize: "15px", fontWeight: 700, lineHeight: 1, flexShrink: 0 }}>✕</button>
            </div>
          </div>
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "4px" }}>
            {d.cache ? "Resultado do cache de hoje (sem custo de IA)" : "Aprofundamento educacional"}{r.confianca ? " · confiança " + r.confianca : ""}
          </div>
        </div>
        <div style={{ padding: "15px 18px", overflowY: "auto", flex: 1, minHeight: 0, WebkitOverflowScrolling: "touch", overscrollBehavior: "contain" }}>
          {d.loading && <SweepGauge label={t + " · leitura profunda"} steps={["consultando o histórico", "montando o pacote técnico", "IA lendo os setups detectados"]} />}
          {d.error && <div style={{ fontSize: "12.5px", color: T.negative, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{d.error}</div>}
          {/* FASE 6 (fix 2): resumo renderizado em BLOCO (parágrafos, títulos e
              listas) — o MdInline colapsava quebras de linha e a leitura chegava
              "amassada". Se o servidor sinalizou parse parcial, avisa e oferece
              rodar de novo em vez de exibir texto quebrado como se fosse normal. */}
          {r.parseFalhou && (
            <div style={{ margin: "0 0 10px", padding: "9px 11px", borderRadius: "9px", background: T.accentTint10, border: `1px solid ${T.accent}`, fontSize: "11.5px", color: T.accent, lineHeight: 1.5 }}>
              A leitura veio incompleta do modelo (abaixo, o resumo recuperado). Toque em "Aprofundar com IA" de novo para a versão completa.
            </div>
          )}
          {r.resumo && <div style={{ margin: "0 0 12px", fontSize: "13px", color: T.textPrimary, lineHeight: 1.6 }}><Markdown text={r.resumo} /></div>}
          {(r.leituraSetups || []).length > 0 && (
          <Fold title="Leitura por setup" count={(r.leituraSetups || []).length}>
          {(r.leituraSetups || []).map((s, i) => (
            <div key={i} style={{ padding: "11px 12px", borderRadius: "10px", background: T.bgBase, border: `1px solid ${T.borderFaint}`, marginBottom: "9px" }}>
              <div style={{ fontSize: "12.5px", fontWeight: 800 }}>{s.setup}</div>
              {s.leitura && <div style={{ fontSize: "12px", color: T.textSecondary, lineHeight: 1.55, marginTop: "4px" }}><MdInline text={s.leitura} /></div>}
              {(s.criteriosPresentes || []).map((c, ci) => (
                <div key={"p" + ci} style={{ display: "flex", gap: "7px", marginTop: "5px", fontSize: "11.5px", lineHeight: 1.45 }}><span style={{ color: T.positive, fontWeight: 800 }}>✓</span><span style={{ color: T.textSecondary }}><MdInline text={c} /></span></div>
              ))}
              {(s.criteriosAusentes || []).map((c, ci) => (
                <div key={"a" + ci} style={{ display: "flex", gap: "7px", marginTop: "5px", fontSize: "11.5px", lineHeight: 1.45 }}><span style={{ color: T.textFaint, fontWeight: 800 }}>○</span><span style={{ color: T.textFaint }}><MdInline text={c} /></span></div>
              ))}
            </div>
          ))}
          </Fold>
          )}
          {(cen.alta || cen.baixa || cen.neutro) && (
            <Fold title="Cenários de estudo">
            <div style={{ marginBottom: "9px" }}>
              {cen.alta && <div style={{ fontSize: "12px", lineHeight: 1.55, marginBottom: "5px" }}><b style={{ color: T.positive }}>Alta:</b> <span style={{ color: T.textSecondary }}><MdInline text={cen.alta} /></span></div>}
              {cen.baixa && <div style={{ fontSize: "12px", lineHeight: 1.55, marginBottom: "5px" }}><b style={{ color: T.negative }}>Baixa:</b> <span style={{ color: T.textSecondary }}><MdInline text={cen.baixa} /></span></div>}
              {cen.neutro && <div style={{ fontSize: "12px", lineHeight: 1.55 }}><b style={{ color: T.textMuted }}>Neutro:</b> <span style={{ color: T.textSecondary }}><MdInline text={cen.neutro} /></span></div>}
            </div>
            </Fold>
          )}
          {(r.riscos || []).length > 0 && (
            <Fold title="Riscos" count={(r.riscos || []).length}>
            <div style={{ marginBottom: "9px" }}>
              {(r.riscos || []).map((x, i) => <div key={i} style={{ fontSize: "12px", color: T.textSecondary, lineHeight: 1.55, marginBottom: "4px" }}>• <MdInline text={x} /></div>)}
            </div>
            </Fold>
          )}
          {r.invalidacao && <div style={{ fontSize: "12px", lineHeight: 1.55, marginBottom: "9px" }}><b style={{ color: T.textSecondary }}>Invalidação da tese:</b> <span style={{ color: T.textMuted }}><MdInline text={r.invalidacao} /></span></div>}
          {(r.modelosUtilizados || []).length > 0 && (
            <div style={{ marginTop: "4px" }}>
              <button onClick={() => setShowModels(!showModels)} style={{ background: "transparent", border: "none", color: T.accent, fontSize: "12px", fontWeight: 700, padding: 0 }}>
                {showModels ? "− Modelos utilizados" : "+ Modelos utilizados (o que a IA usou e por quê)"}
              </button>
              {showModels && (r.modelosUtilizados || []).map((m, i) => (
                <div key={i} style={{ padding: "9px 0", borderTop: i ? `1px solid ${T.borderFaint}` : "none", marginTop: i ? "4px" : "8px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700 }}>{m.nome}</div>
                  <div style={{ fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5, marginTop: "2px" }}><MdInline text={[m.oQueE, m.oQueMede && ("· Mede: " + m.oQueMede), m.limitacoes && ("· Limitações: " + m.limitacoes)].filter(Boolean).join(" ")} /></div>
                </div>
              ))}
            </div>
          )}
          {d.disclaimer && !d.loading && <div style={{ marginTop: "12px", fontSize: "10.5px", color: T.textFaint, lineHeight: 1.5 }}>{d.disclaimer}</div>}
        </div>
        <div style={{ padding: "13px 18px", paddingBottom: "calc(13px + env(safe-area-inset-bottom, 0px))", borderTop: `1px solid ${T.borderSubtle}`, display: "flex", gap: "9px", justifyContent: "flex-end", flexShrink: 0 }}>
          <button onClick={onClose} style={{ padding: "10px 16px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px" }}>Fechar</button>
          <button onClick={onAvaliar} style={{ padding: "10px 18px", borderRadius: "8px", border: `1px solid ${T.accent}`, background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "13px" }}>Análise completa →</button>
        </div>
      </div>
    </div>
  );
}

function ConfigScreen({ ctx }) {
  const { data, A, themePref } = ctx;
  const c = data.config;
  const sectionTitle = { fontSize: "13px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent };
  const seg = (on) => ({ flex: 1, padding: "10px", borderRadius: "8px", fontWeight: 600, fontSize: "13px", border: `1px solid ${on ? T.accent : T.borderSubtle}`, background: on ? T.accentTint : T.bgPanel, color: on ? T.accent : T.textMuted });
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
                // Sair do campo não pode depender só do relógio de 600ms — os
                // outros campos deste mesmo padrão (model/baseUrl/serverUrl)
                // já flusheiam no blur; este era o único que não tinha.
                onBlur={A.flushCfg}
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

      {/* Ponto único do aviso completo + boas-vindas */}
      <div style={{ display: "flex", gap: "10px", marginTop: "16px", flexWrap: "wrap" }}>
        <button onClick={ctx.openWelcomeAuth} style={{ flex: "1 1 160px", padding: "14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
          <LogoMark size={18} /> Tela de boas-vindas
        </button>
        <button onClick={A.openAbout} style={{ flex: "1 1 160px", padding: "14px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
          <span aria-hidden style={{ fontWeight: 700, color: T.accent }}>ⓘ</span> Sobre · Aviso legal
        </button>
      </div>
      <div style={{ textAlign: "center", fontSize: "11px", color: T.textFaint, marginTop: "12px" }}>Boris+ · simulador educacional · {DISCLAIMERS.short}</div>
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

// FASE 2 (2.2): quantidade sugerida (lotes de 100) pelo caixa e apetite de
// risco do onboarding — conservador 15%, moderado 25%, agressivo 40% do caixa.
function suggestedQty(cash, priceV, risco) {
  if (!priceV || priceV <= 0 || !cash || cash <= 0) return 100;
  const frac = risco === "conservador" ? 0.15 : risco === "agressivo" ? 0.4 : 0.25;
  const q = Math.floor((cash * frac) / priceV / 100) * 100;
  return Math.max(100, q);
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
          <button onClick={A.confirmBuy} disabled={!ok} style={{ flex: 1.4, padding: "11px", borderRadius: "9px", border: `1px solid ${ok ? T.positive : T.borderSubtle}`, background: ok ? T.positive : T.knob, color: ok ? T.confirmOkText : T.textFaint, fontWeight: 800, fontSize: "14px" }}>{ctx.cp.confirmarCompra}</button>
        </div>
      </div>
    </div>
  );
}

// FASE 2 (2.4): venda simulada TOTAL ou PARCIAL (lotes de 100) com confirmação
// e prévia do resultado — espelha o BuyModal; o preço final é o do servidor.
function SellModal({ ctx }) {
  const { sellModal, setSellModal, quotes, data, A } = ctx;
  const t = sellModal.t;
  const pos = (data.positions || []).find((p) => p.t === t);
  if (!pos) return null;
  const q = quotes[t] || {};
  const cur = markPrice(q, pos);
  const qty = Math.min(pos.qty, Math.max(100, sellModal.qty));
  const total = qty >= pos.qty;
  const valor = qty * cur;
  const pnl = (cur - pos.avg) * qty;
  const pnlColor = pnl >= 0 ? T.positive : T.negative;
  const step = (dir) => setSellModal((m) => ({ ...m, qty: Math.min(pos.qty, Math.max(100, (m.qty || pos.qty) + dir * 100)) }));
  return (
    <div onClick={A.closeSell} style={{ position: "fixed", inset: 0, zIndex: 50, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: "420px", ...card, borderRadius: "14px", padding: "20px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "11px", color: T.textFaint, letterSpacing: "0.06em" }}>VENDA SIMULADA</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "3px" }}>
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: "19px" }}>{t}</span>
              <span style={{ color: T.textMuted, fontSize: "13px" }}>{pos.qty} cotas · PM R$ {price(pos.avg)}</span>
            </div>
          </div>
          <div style={{ textAlign: "right", fontFamily: MONO }}>
            <div style={{ fontSize: "10px", color: T.textFaint }}>PREÇO ATUAL</div>
            <div style={{ fontSize: "16px", fontWeight: 600 }}>R$ {price(cur)}</div>
          </div>
        </div>
        <div style={{ marginTop: "18px" }}>
          <div style={{ fontSize: "12px", color: T.textMuted, marginBottom: "8px" }}>Quantidade a vender (lotes de 100)</div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button onClick={() => step(-1)} aria-label="Diminuir" style={{ width: "42px", height: "42px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "20px", fontWeight: 600 }}>−</button>
            <div style={{ flex: 1, textAlign: "center", fontFamily: MONO, fontSize: "22px", fontWeight: 600 }}>{qty}</div>
            <button onClick={() => step(1)} aria-label="Aumentar" style={{ width: "42px", height: "42px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "20px", fontWeight: 600 }}>+</button>
          </div>
          <button onClick={() => setSellModal((m) => ({ ...m, qty: pos.qty }))} style={{ marginTop: "8px", width: "100%", minHeight: "34px", padding: "7px", borderRadius: "9px", border: `1px dashed ${total ? T.accent : T.borderSubtle}`, background: total ? T.accentTint10 : "transparent", color: total ? T.accent : T.textMuted, fontWeight: 700, fontSize: "12px" }}>
            {total ? "Venda TOTAL (encerra a posição)" : "Vender tudo (" + pos.qty + ")"}
          </button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "16px", padding: "12px 13px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, borderRadius: "9px", fontFamily: MONO }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: T.textMuted, fontSize: "13px" }}>Valor estimado</span><span style={{ fontWeight: 700, fontSize: "15px" }}>{money(valor)}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: T.textMuted, fontSize: "13px" }}>Resultado estimado</span><span style={{ fontWeight: 700, fontSize: "15px", color: pnlColor }}>{moneySigned(pnl)}</span></div>
        </div>
        {!total && <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "8px", lineHeight: 1.5 }}>Venda parcial: ficam {pos.qty - qty} cotas com o mesmo preço médio.</div>}
        <div style={{ fontSize: "11px", color: T.textFaint, marginTop: "6px" }}>O preço final é o da cotação no momento da confirmação (servidor). Registro vai para o histórico do ativo.</div>
        <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
          <button onClick={A.closeSell} style={{ flex: 1, padding: "11px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 600, fontSize: "14px" }}>Cancelar</button>
          <button onClick={A.confirmSell} style={{ flex: 1.4, padding: "11px", borderRadius: "9px", border: `1px solid ${T.negative}`, background: T.negativeTint10, color: T.negative, fontWeight: 800, fontSize: "14px" }}>{ctx.cp.confirmarVenda}{total ? " total" : " de " + qty}</button>
        </div>
      </div>
    </div>
  );
}

// v2: a tela solta de opções (OptionsScreen) e seu ajudante Metric foram
// removidos aqui — a camada de opções passou a viver DENTRO do AtivoCard
// (OpcoesCamada) e nada mais navegava até a tela: o botão de entrada saiu com
// a v2 e a rota `tab === "opcoes"` ficou órfã. O backend que ela consumia
// (/api/options/chain e /api/options/analyze) continua no ar.

/* --------------------------------- App ----------------------------------- */
export default function App() {
  const [data, setData] = useState(null);
  const [loadErr, setLoadErr] = useState(null);
  const [quotes, setQuotes] = useState({});
  const [quotesAt, setQuotesAt] = useState(null);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [tab, setTab] = useState("evolucao");
  const [carteiraView, setCarteiraView] = useState("main"); // main | historico
  const [perfilView, setPerfilView] = useState("hub");       // hub | config | ia | notificacoes | eficiencia | logs
  const navigate = (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); };
  const [analysis, setAnalysis] = useState({});
  const [expanded, setExpanded] = useState({});
  const [analysisModel, setAnalysisModel] = useState("completo");
  const [toast, setToast] = useState(null);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [catalogSel, setCatalogSel] = useState([]);
  const [buyModal, setBuyModal] = useState(null);
  const [sellModal, setSellModal] = useState(null);   // FASE 2 (2.4): venda total/parcial com confirmação
  const [wlScan, setWlScan] = useState(null);          // FASE 2 (2.3): scan do STU restrito à watchlist
  const [wlScanLoading, setWlScanLoading] = useState(false);
  const [destaque, setDestaque] = useState({ stage: "idle" }); // FASE 2 (2.2): oportunidade do dia
  const [techFor, setTechFor] = useState(null);
  const [keyDraft, setKeyDraft] = useState("");
  const [test, setTest] = useState({ status: null, msg: "" });
  const [cycleBusy, setCycleBusy] = useState(false);
  const [addState, setAddState] = useState({ busy: false, msg: "" });
  // Tema: preferência (dark|light|system) vinda da config; resolvido p/ dark|light.
  const sysDark = () => (typeof window !== "undefined" && window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : true);
  const [sysIsDark, setSysIsDark] = useState(sysDark);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);  // qa/38 (Help): tour de primeiro uso
  // Camada de entendimento: catálogo (buscado 1x) e a folha aberta no momento.
  // `didatica.ligada` vem do backend — desligar em produção é variável de
  // ambiente, não build de iOS.
  const [didatica, setDidatica] = useState(null);
  const [conceitoAberto, setConceitoAberto] = useState(null);  // {cid, dados}
  const [petOpen, setPetOpen] = useState(false);               // folha do pet (mascote)
  // F6: fonte ÚNICA que liga o pet — o FAB e o "Conversar agora" da
  // apresentação chamam a MESMA função (nunca duplicam a chamada que abre),
  // preservando o invariante "o pet só abre por ação explícita" que
  // `test_pet_ui.mjs` já trava contando ocorrências literais.
  const abrirPet = () => setPetOpen(true);
  const [borisIntroOpen, setBorisIntroOpen] = useState(false); // F6: apresentação do Boris (1x)
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const [stopAlvoFor, setStopAlvoFor] = useState(null); // FASE 3: ticker do popup de stop/alvo (individual)
  const [stopAlvo, setStopAlvo] = useState({}); // FASE 3: resultados por ticker { loading, stop, alvo, explicacao, operar, error }
  // FASE 2: conta opcional. authUser=null => anônimo (app abre normalmente).
  const [authUser, setAuthUser] = useState(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [welcomeAuthOpen, setWelcomeAuthOpen] = useState(false); // tela de abertura (login)
  const tourShownRef = useRef(false); // qa/38 (Help): tour aparece 1x no 1º uso
  const welcomeShownRef = useRef(false);
  const borisIntroShownRef = useRef(false); // F6: apresentação do Boris aparece 1x por boot
  const themePref = (data && data.config && data.config.theme) || (typeof localStorage !== "undefined" && localStorage.getItem("b3-theme")) || "dark";
  const themeKey = themePref === "system" ? (sysIsDark ? "dark" : "light") : themePref;
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const on = (e) => setSysIsDark(e.matches);
    try { mq.addEventListener("change", on); } catch { mq.addListener(on); }
    return () => { try { mq.removeEventListener("change", on); } catch { mq.removeListener(on); } };
  }, []);
  // FASE 8B (B2): o modo é uma CLASSE por cima do tema — os overrides de
  // var(--x) trocam a identidade inteira (verde-mercado × âmbar/azul) e o
  // theme-color/status bar acompanham.
  const appMode = (data && data.config && data.config.appMode) === "operador" ? "operador" : "estudo";
  // FASE 8B (B1): fraseologia por modo — definida ANTES do useMemo(A), que a
  // usa em toasts (recriado junto, pois deriva de `data`, que está nas deps).
  const cp = copyFor(appMode);
  useEffect(() => {
    if (typeof document === "undefined") return;
    const html = document.documentElement;
    html.classList.remove("b3-theme-dark", "b3-theme-light");
    html.classList.add("b3-theme-" + themeKey);
    // transição suave APENAS durante a troca de identidade
    if (html.classList.contains("b3-mode-operador") !== (appMode === "operador")) {
      html.classList.add("b3-mode-switch");
      setTimeout(() => html.classList.remove("b3-mode-switch"), 450);
    }
    html.classList.toggle("b3-mode-operador", appMode === "operador");
    try { localStorage.setItem("b3-theme", themePref); } catch { /* ignore */ }
    try {
      const meta = document.querySelector('meta[name="theme-color"]');
      // Lê o bgBase que a UI está de fato usando (tema × modo) em vez de
      // repetir hex à mão — era assim que o #f3f4f7 do light antigo sobrevivia
      // aqui depois da paleta mudar, e que o Operador no tema CLARO pintava a
      // barra do navegador de escuro (usava o bgBase do Operador dark sempre).
      const esquema = appMode === "operador"
        ? { ...PALETTE[themeKey], ...MODE_OPERADOR[themeKey] }
        : PALETTE[themeKey];
      if (meta) meta.setAttribute("content", esquema.bgBase);
    } catch { /* ignore */ }
  }, [themeKey, themePref, appMode]);
  const cfgTimer = useRef(null);
  // Bug confirmado (2026-08-09): orçamento (e nome, e qualquer campo editado
  // via editConfig) definido e perdido no restart. O debounce de 600ms só
  // guardava o TIMER, não o PATCH pendente — três caminhos descartavam a
  // escrita sem nunca mandá-la pro store: (1) saveConfig cancelava o timer
  // pendente de outro campo sem enviá-lo, então editar orçamento e em
  // seguida tocar em candlePeriod/provider/model perdia o orçamento em
  // silêncio; (2) fechar/backgroundear o app dentro da janela de 600ms mata
  // o setTimeout sem nunca escrever — exatamente o que "reiniciar do zero
  // logo depois de mudar o valor" testa; (3) o campo de orçamento não tinha
  // onBlur, então sair do campo não flusheava nada. cfgPending guarda o
  // patch acumulado; flushCfg() (definido em A, abaixo) é o único lugar que
  // decide "hora de mandar" — chamado pelo timer, por saveConfig antes de
  // aplicar o próprio patch, pelo onBlur do campo, e pelo listener de
  // background/app-state. Sem isso, closures diferentes.
  const cfgPending = useRef(null);
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

  // Objetivo 2: notificações locais aparecem MESMO com o app aberto. No iOS o
  // banner do sistema é suprimido em foreground; aqui mostramos um aviso in-app
  // (toast) quando uma notificação dispara com o app aberto. A notificação do
  // sistema segue valendo para quando o app está em segundo plano.
  useEffect(() => {
    notify.setForegroundHandler((title, body) => flash(body ? (title + " — " + body) : title));
    notify.setup();
    return () => notify.setForegroundHandler(null);
  }, [flash]);

  const loadState = useCallback(async () => {
    try {
      const s = await store.getState();
      setData(s);
      if (s.analyses && typeof s.analyses === "object") {
        const seed = {};
        for (const t of Object.keys(s.analyses)) {
          const a = s.analyses[t] || {};
          seed[t] = { loading: false, text: a.text || a.analysis || "", markdown: a.markdown || a.text || a.analysis || "", kpis: a.kpis || null, detail: a.detail || null, proposal: a.proposal || null, model: a.model || null, modelLabel: a.modelLabel || null, technicalContext: a.technicalContext || null, candlesSentToLLM: a.candlesSentToLLM || null, snapshotId: a.snapshotId || null, snapshotAt: a.snapshotAt || null, fundamento: a.fundamento || null, confiancaFinal: a.confiancaFinal || null, rebaixadoPorFundamento: !!a.rebaixadoPorFundamento, at: a.at || null };
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
  // qa/audit-2026-08-08: getState() só rodava no boot — qualquer mudança feita
  // só do lado do servidor (Operador autônomo com o app fechado, opção
  // negociada, reset por outro aparelho da mesma conta) nunca voltava pra
  // tela até a próxima compra/venda LOCAL. Reconfirma o estado sempre que o
  // app volta pro primeiro plano: `visibilitychange` cobre o navegador; no
  // iOS nativo o WKWebView nem sempre dispara esse evento de forma confiável
  // ao voltar de segundo plano, então soma-se o listener do plugin
  // `@capacitor/app` (import dinâmico — só existe runtime no nativo).
  useEffect(() => {
    // Bug confirmado (2026-08-09): orçamento (e outros campos deste debounce)
    // editado e perdido no restart — "reiniciar do zero logo depois de mudar
    // o valor" mata o setTimeout pendente de flushCfg ANTES dos 600ms, e a
    // escrita nunca chega no store. Indo pra SEGUNDO PLANO — o instante em
    // que o app pode ser encerrado a qualquer momento — flusheia o que
    // estiver pendente. Mesmo par de fontes que já cobre "voltar pro
    // primeiro plano" logo abaixo: visibilitychange no navegador,
    // appStateChange no WKWebView (nem sempre dispara visibilitychange).
    const onVisible = () => {
      if (document.visibilityState === "visible") loadState();
      else if (flushCfgRef.current) flushCfgRef.current();
    };
    document.addEventListener("visibilitychange", onVisible);
    let removeAppListener = null;
    if (isNative) {
      import("@capacitor/app").then(({ App: CapApp }) => {
        CapApp.addListener("appStateChange", ({ isActive }) => {
          if (isActive) loadState();
          else if (flushCfgRef.current) flushCfgRef.current();
        })
          .then((h) => { removeAppListener = () => h.remove(); });
      }).catch(() => { /* plugin ausente: visibilitychange segue cobrindo */ });
    }
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      if (removeAppListener) removeAppListener();
    };
  }, [loadState]);
  // Toque no aviso de condição atingida → a tela do ativo, não a aba inicial.
  // Registrado UMA vez, no boot. `reservarDonoProativo` garante que, se for a
  // estreia da pessoa no conceito, a explicação venha com os números do ativo
  // que a interrompeu — e não do primeiro card que a rede devolver.
  useEffect(() => {
    notify.onPushTap(async (t) => {
      // O universo do push é watchlist ∪ POSIÇÕES, mas a tela lista só a
      // watchlist — e "tem posição, não está na watchlist" é estado normal
      // (o modal do catálogo SUBSTITUI a lista inteira). Sem garantir o ativo
      // aqui, o toque levaria a uma tela sem ele em lugar nenhum.
      try {
        const s = await store.getState();
        const wl = (s && s.watchlist) || [];
        if (!wl.includes(t)) await store.putWatchlist([...wl, t]);
      } catch { /* sem rede o scroll falha; a navegação ainda vale */ }
      setTab("mercado");
      // A reserva da eleição só vale se o card EXISTE. Reservar antes de
      // confirmar prenderia `_proativoDono` num ticker que nunca monta, e
      // nenhum outro card conseguiria abrir a folha proativa até a pessoa
      // deslogar — o push mataria a estreia da camada que ele alimenta.
      for (const ms of [300, 1200]) {
        setTimeout(() => {
          const el = document.getElementById("ativo-" + t);
          if (!el) return;
          reservarDonoProativo(t);
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }, ms);
      }
    });
  }, []);
  // Camada de entendimento: catálogo buscado UMA vez por modo. Custo zero (é
  // texto determinístico do backend, sem LLM). Falha aqui é silêncio proposital
  // — sem catálogo o app segue inteiro, apenas sem as afordâncias de explicação.
  const modoApp = (data && data.config && data.config.appMode) || "estudo";
  useEffect(() => {
    let alive = true;
    store.conceitos(modoApp)
      .then((r) => { if (alive) setDidatica(r); })
      .catch(() => { if (alive) setDidatica({ ligada: false, conceitos: [] }); });
    return () => { alive = false; };
  }, [modoApp]);
  // qa/38 (Help): abre o tour UMA vez no primeiro uso — depois que o portão de
  // abertura (login) fecha e só se `tourSeen` ainda não foi marcado. Guardado
  // por ref para não reabrir; o Ver tour de novo (Ajuda) usa A.openTour.
  useEffect(() => {
    if (tourShownRef.current || !data || !data.config) return;
    if (welcomeAuthOpen || welcomeOpen) return;      // espera o portão fechar
    tourShownRef.current = true;
    if (!data.config.tourSeen) setTourOpen(true);
  }, [data, welcomeAuthOpen, welcomeOpen]);
  // F6: apresenta o Boris UMA vez, na primeira vez que a pessoa chega na aba
  // inicial (Mercado/Watchlist) depois que o portão de abertura fecha — e só
  // se a camada de entendimento estiver ligada nesta conta (sem `didatica`
  // não há FAB para explicar). Mesmo portão de overlays que `ctx.overlayLivre`
  // usa (tour incluído: a intro espera o tour terminar, nunca some por cima
  // dele) para não abrir em cima de outra folha. Guardado por ref — decide
  // uma vez por boot e nunca reavalia (não reabre ao voltar pra Mercado).
  useEffect(() => {
    if (borisIntroShownRef.current || !data || !data.config) return;
    if (tourOpen || aboutOpen || welcomeOpen || welcomeAuthOpen || conceitoAberto || petOpen) return; // espera o portão fechar
    if (tab !== "mercado") return;             // só na aba inicial (Watchlist)
    if (!(didatica && didatica.ligada)) return; // só com a camada de entendimento ligada
    borisIntroShownRef.current = true;
    if (!data.config.borisIntroVisto) setBorisIntroOpen(true);
  }, [data, tourOpen, aboutOpen, welcomeOpen, welcomeAuthOpen, conceitoAberto, petOpen, tab, didatica]);
  // FASE 3.3a — ao abrir o app, resume as ações do agente server-side desde a
  // última visita (agentLog vs. agent.lastSeenAt) com notificação local.
  const agentSummaryDone = useRef(false);
  useEffect(() => {
    if (!data || agentSummaryDone.current) return;
    agentSummaryDone.current = true;
    try {
      const log = data.agentLog || [];
      const seen = (data.agent || {}).lastSeenAt || "";
      const news = seen ? log.filter((e) => (e.at || e.time || "") > seen) : log;
      const acts = news.filter((e) => e.kind === "buy");
      if (acts.length > 0) {
        const msg = "O agente fez " + acts.length + " ação(ões) simulada(s) desde sua última visita — veja em Automatizar.";
        flash(msg);
        notify.send("Agente Boris+", msg);
      }
      if (log.length) store.putAgent({ lastSeenAt: new Date().toISOString() }).catch(() => {});
    } catch { /* resumo é best-effort */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);
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
          // qa/32: sessão restaurada com sucesso = identidade já confirmada
          // pelo servidor — exigir um toque extra em "Entrar" no portão de
          // abertura (WelcomeAuthScreen) é uma página intermediária sem
          // propósito. Fecha o portão sozinho (mesmo efeito de tocar
          // "Entrar" manualmente) e marca `welcomeShownRef` ANTES do outro
          // efeito (boot gate, abaixo) rodar — senão ele reabriria a tela ao
          // ver `welcomeShownRef.current` ainda falso.
          welcomeShownRef.current = true;
          setWelcomeAuthOpen(false);
          setData((d) => (d ? { ...d, config: { ...d.config, onboarded: true } } : d));
          try { await store.putConfig({ onboarded: true }); } catch { /* silencioso, mesma política de markOnboarded */ }
          // FASE 8B (N2 — fix "identidade se perde"): no iOS o APARELHO é a
          // fonte da verdade (local-first). O estado do SERVIDOR sobrescrevia
          // o doc local — appMode/termo/risco voltavam ao padrão a cada boot
          // ou login. Nativo: SEMPRE recarrega do deviceStore (o namespace já
          // foi trocado pelo _setDeviceScope); web: estado do servidor vale.
          if (isNative) await loadState();
          else if (r.state) setData(r.state);
        }
      } catch { /* sessão inválida/sem rede: app segue sem login */ }
    })();
    return () => { alive = false; };
  }, []);
  useEffect(() => {
    if (data) refreshQuotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data && Array.isArray(data.watchlist) ? data.watchlist.join(",") : ""]);

  // Envia AGORA o patch acumulado em cfgPending — o único lugar que decide
  // "hora de mandar pro store". Chamado pelo próprio debounce (após 600ms),
  // por saveConfig (que ANTES cancelava o timer alheio sem nunca enviar o
  // patch dele — via este flush, o patch pendente sai primeiro), pelo onBlur
  // do campo de orçamento, e pelo listener de app indo pra segundo plano
  // (cobre "reiniciar do zero logo depois de editar", que matava o setTimeout
  // pendente sem nunca escrever nada). Idempotente: nada pendente = no-op.
  const flushCfg = useCallback(async () => {
    if (cfgTimer.current) { clearTimeout(cfgTimer.current); cfgTimer.current = null; }
    const pending = cfgPending.current;
    cfgPending.current = null;
    if (!pending) return;
    try { const s = await store.putConfig(pending); setData(s); }
    catch (e) { flash("Config: " + (e.message || e)); }
  }, [flash]);
  // cycleRef já é o padrão deste componente pra "closure sempre atual sem
  // reiniciar o effect" — mesmo motivo aqui: o listener de background é
  // registrado uma vez (deps de loadState) e precisa do flushCfg mais recente.
  const flushCfgRef = useRef(null);
  flushCfgRef.current = flushCfg;

  const A = useMemo(() => ({
    flash,  // FASE 3: telas dão feedback padronizado (Operador IA usa)
    refreshQuotes,
    go: (t) => { setCarteiraView("main"); setPerfilView("hub"); setTab(t); },
    // FASE 6 (fix 4): atalho direto para a CENTRAL de notificações (Config)
    openNotifCentral: () => { setCarteiraView("main"); setPerfilView("notificacoes"); setTab("perfil"); },
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
        // FASE 2 (2.4): se o usuário TEM a posição, a IA recebe o contexto dela
        // (preço médio, quantidade, resultado atual) — reanálise situada.
        const posCtx = (() => {
          const p = (data.positions || []).find((x) => x.t === t);
          if (!p) return undefined;
          const q = quotes[t] || {};
          const res = q.price != null ? (q.price - p.avg) * p.qty : null;
          return { qty: p.qty, avg: p.avg, stop: p.stop, alvo: p.alvo, resultadoAtual: res != null ? Math.round(res * 100) / 100 : null };
        })();
        const r = await store.analyze(t, { model: analysisModel, position: posCtx });
        setAnalysis((a) => ({ ...a, [t]: { loading: false, text: r.text || r.analysis || "", markdown: r.markdown || r.text || r.analysis || "", kpis: r.kpis || null, detail: r.detail || null, proposal: r.proposal || null, model: r.model, modelLabel: r.modelLabel, technicalContext: r.technicalContext || null, candles: r.candles, candlesSentToLLM: r.candlesSentToLLM, snapshotId: r.snapshotId || null, snapshotAt: r.snapshotAt || null, fundamento: r.fundamento || null, confiancaFinal: r.confiancaFinal || null, rebaixadoPorFundamento: !!r.rebaixadoPorFundamento, at: r.at, quote: r.quote } }));
        // FASE 2 (2.5): telemetria didática — registra o que a IA disse (para
        // comparar depois com o que aconteceu). Best-effort, nunca bloqueia.
        try {
          const s2 = await store.pushAnalysisLog(t, { tipo: "análise", modelo: r.modelLabel || r.model || "", resumo: (r.kpis && r.kpis.recomendacao) || "", stop: r.proposal ? r.proposal.stop : null, alvo: r.proposal ? r.proposal.alvo : null, preco: (r.quote && r.quote.price) != null ? r.quote.price : ((quotes[t] || {}).price || null) });
          if (s2 && s2.analysisLog) setData(s2);
        } catch { /* log é best-effort */ }
      } catch (e) {
        setAnalysis((a) => ({ ...a, [t]: { loading: false, error: e.message || String(e) } }));
      }
    },
    toggleExpand: (t) => setExpanded((x) => ({ ...x, [t]: !x[t] })),
    // FASE 2 (2.4): meta = setup de entrada (do STU) registrado na compra
    openBuy: (t, qty, meta) => setBuyModal({ t, qty: qty || 100, meta: meta || null }),
    closeBuy: () => setBuyModal(null),
    // FASE 3 (Radar): "+ Watchlist" — move o achado para o funil sem sair da tela.
    // FASE 5 (fix): usa addWatchlistTicker (valida e REGISTRA em `custom` nos dois
    // stores). O caminho antigo (putWatchlist) filtrava contra o catálogo de 20
    // tickers e DESCARTAVA em silêncio qualquer ativo do Radar fora dele — a UI
    // dizia "adicionado ✓" mas o ativo nunca entrava. Guardado por
    // web/tests/test_radar_watchlist.mjs.
    addToWatchlist: async (t) => {
      try {
        if (!(data.watchlist || []).includes(t)) {
          const st = await store.addWatchlistTicker(t);
          setData(st);
          if (!((st.watchlist || []).includes(t))) throw new Error(t + " não entrou na watchlist. Tente pelo ✎ da Watchlist.");
        }
        flash(t + " adicionado à watchlist ✓");
      } catch (e) { flash("Watchlist: " + (e.message || e)); }
    },
    openSell: (t) => {
      const pos = (data.positions || []).find((p) => p.t === t);
      if (pos) setSellModal({ t, qty: pos.qty });
    },
    closeSell: () => setSellModal(null),
    confirmSell: async () => {
      const sm = sellModal; if (!sm) return;
      const pos = (data.positions || []).find((p) => p.t === sm.t);
      try {
        const total = !pos || sm.qty >= pos.qty;
        const st = await store.sell(sm.t, total ? undefined : sm.qty);
        setData(st); setSellModal(null);
        flash(cp.toastVenda(total ? "total" : sm.qty + " cotas", sm.t)); // FASE 8B (B1)
      } catch (e) { flash("Venda: " + (e.message || e)); }
    },
    // FASE 2 (2.3): scan do STU restrito aos ativos da watchlist — ordena os
    // cards por oportunidade e alimenta os alertas do Acompanhar. Silencioso:
    // a watchlist funciona sem ele (rate-limit do Yahoo não quebra a tela).
    refreshWlScan: async () => {
      const wl = (data && data.watchlist) || [];
      if (!wl.length) { setWlScan(null); return; }
      if (wlScanLoading) return;
      setWlScanLoading(true);
      try {
        const p = (data.config && data.config.candlePeriod) || undefined;
        const r = await store.scan(p, wl.join(","));
        setWlScan(r);
      } catch { /* silencioso — stale/erro não derruba a watchlist */ }
      finally { setWlScanLoading(false); }
    },
    // FASE 2 (2.2): destaque do dia — melhor score do scan do Radar que NÃO
    // está na watchlist; 1 chamada N1/dia autorizada (o cache do deep por
    // snapshotId garante que o mesmo candle não repaga a cota).
    loadDestaque: async () => {
      if (destaque.stage === "loading") return;
      setDestaque({ stage: "loading" });
      try {
        const p = (data.config && data.config.candlePeriod) || undefined;
        const scan = await store.scan(p);
        const inWl = new Set(data.watchlist || []);
        const best = (scan.results || []).find((r) => !inWl.has(r.ticker) && (r.confluencia || 0) > 0);
        if (!best) { setDestaque({ stage: "empty" }); return; }
        setDestaque({ stage: "ready", item: best });
        try {
          const deep = await store.scanDeep({ period: scan.period, tickers: best.ticker, topN: 1 });
          const d = (deep.results || [])[0];
          if (d) setDestaque({ stage: "ready", item: best, deep: d });
        } catch { /* leitura da IA é bônus; o card determinístico permanece */ }
      } catch (e) { setDestaque({ stage: "error", error: e.message || String(e) }); }
    },
    openTech: (t) => setTechFor(t),
    closeTech: () => setTechFor(null),
    confirmBuy: async () => {
      const bm = buyModal; if (!bm) return;
      try {
        const s = await store.buy(bm.t, bm.qty, bm.meta || undefined); // FASE 2 (2.4): setup de entrada
        setData(s); setBuyModal(null);
        flash(cp.toastCompra(bm.qty, bm.t)); // FASE 8B (B1): voz do modo
        // FASE 2 (2.3): oferta IMEDIATA do N3 — modal com cenários; nada é
        // aplicado sem o toque do usuário (Fechar cancela sem efeito).
        setStopAlvoFor(bm.t);
        A.runStopAlvoFor(bm.t);
      }
      catch (e) { flash("Compra: " + (e.message || e)); }
    },
    sell: async (t) => {
      try { const s = await store.sell(t); setData(s); flash(cp.toastVenda("total", t)); }
      catch (e) { flash("Venda: " + (e.message || e)); }
    },
    setStop: async (t, v) => { try { const s = await store.putPosition(t, { stop: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setAlvo: async (t, v) => { try { const s = await store.putPosition(t, { alvo: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    // v2 (ADR-003/004): compra a seco de 1 contrato (100 cotas). O servidor
    // recusa (502) se a cotação estiver degradada — nunca preenche `avg` com
    // um preço que o próprio sistema não confia.
    buyOption: async (underlying, contract, expiration, meta) => {
      try {
        const s = await store.optionsBuy({ underlying, contractSymbol: contract.contractSymbol, expiration, qty: 100, meta: meta || undefined });
        setData(s);
        flash("Opção " + contract.contractSymbol + " comprada — 100 cotas a R$ " + price(s.priceUsed) + ".");
      } catch (e) { flash("Compra de opção: " + (e.message || e)); }
    },
    sellOption: async (contractId) => {
      try {
        const s = await store.optionsSell({ contractSymbol: contractId });
        setData(s);
        flash("Opção " + contractId + " vendida.");
      } catch (e) { flash("Venda de opção: " + (e.message || e)); }
    },
    setOptionStop: async (contractId, v) => { try { const s = await store.putOptionPosition(contractId, { stop: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setOptionAlvo: async (contractId, v) => { try { const s = await store.putOptionPosition(contractId, { alvo: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    applyProposal: async (t, stop, alvo) => {
      try {
        const s = await store.putPosition(t, { stop, alvo });
        setData(s);
        setAnalysis((a) => ({ ...a, [t]: { ...(a[t] || {}), applied: true } })); // fecha o popup de sugestão
        flash("Stop/alvo aplicados em " + t + ".");
      } catch (e) { flash("Erro: " + (e.message || e)); }
    },
    toggleAuto: async (v) => { try { const s = await store.putAgent({ autonomous: v }); setData(s); } catch (e) { flash("Erro: " + (e.message || e)); } },
    // FASE 3.2: patch genérico dos parâmetros do agente (otimista + persiste).
    // FASE 6 (fix 3): `serverEnabled` NUNCA é otimista — antes o setData
    // adiantava o toggle e o catch engolia o erro: a UI mostrava "ligado" sem
    // o servidor ter ligado (fantasma) e o setServer não via a falha. Flag de
    // servidor = só com resposta confirmada; erro SOBE para quem chamou.
    putAgent: async (patch) => {
      const liveFlag = !!(patch && ("serverEnabled" in patch));
      if (!liveFlag) setData((d) => ({ ...d, agent: { ...d.agent, ...patch, rules: { ...((d.agent || {}).rules || {}), ...(patch.rules || {}) } } }));
      try { const s = await store.putAgent(patch); setData(s); }
      catch (e) { if (liveFlag) throw e; flash("Erro: " + (e.message || e)); }
    },
    setAlloc: async (v) => { setData((d) => ({ ...d, agent: { ...d.agent, allocPct: v } })); try { await store.putAgent({ allocPct: v }); } catch (e) { flash("Erro: " + (e.message || e)); } },
    setAgentInterval: async (v) => { setData((d) => ({ ...d, agent: { ...d.agent, intervalMin: v } })); try { await store.putAgent({ intervalMin: v }); } catch (e) { flash("Erro: " + (e.message || e)); } },
    saveBudget: (v) => {
      // orçamento simulado: controlado + persistido com debounce. O patch vai
      // pra cfgPending (não só o timer) — é o que permite flushCfg() mandar
      // este valor de imediato se o app for pra segundo plano, se o campo
      // perder o foco, ou se outro campo de config for salvo antes dos 600ms.
      setData((d) => ({ ...d, config: { ...d.config, initialBudget: v } }));
      cfgPending.current = { ...(cfgPending.current || {}), initialBudget: v };
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => { flushCfg(); }, 600);
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
      cfgPending.current = { ...(cfgPending.current || {}), userName: v };
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => { flushCfg(); }, 600);
    },
    // Manda AGORA o que estiver pendente (orçamento/nome/qualquer editConfig
    // em voo). onBlur do campo de orçamento chama isto — sair do campo não
    // pode depender só do relógio de 600ms.
    flushCfg,
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
      // FASE 8B (N4): o prompt do stop/alvo tem versão por MODO — a mesa usa
      // carteiraStopAlvoOperador; o professor, carteiraStopAlvo (fallback).
      const lp = (data && data.llmPrompts) || {};
      const prompt = (((data.config || {}).appMode === "operador") ? (lp.carteiraStopAlvoOperador || lp.carteiraStopAlvo) : lp.carteiraStopAlvo) || "";
      setStopAlvo((s) => ({ ...s, [t]: { ...(s[t] || {}), loading: true, error: null } }));
      try {
        const r = await store.analyzeStopAlvo(t, { prompt });
        const prop = r.proposal || {};
        setStopAlvo((s) => ({ ...s, [t]: { loading: false, stop: prop.stop != null ? prop.stop : null, alvo: prop.alvo != null ? prop.alvo : null, explicacao: r.explicacao || "", operar: r.operar, at: r.at, snapshotId: r.snapshotId || null, snapshotAt: r.snapshotAt || null, cenarios: r.cenarios || [], modelos: r.modelosUtilizados || [] } }));
      } catch (e) {
        setStopAlvo((s) => ({ ...s, [t]: { ...(s[t] || {}), loading: false, error: e.message || String(e) } }));
      }
    },
    applyStopAlvoFor: async (t, stop, alvo) => {
      try {
        const s = await store.putPosition(t, { stop, alvo });
        setData(s);
        flash("Stop e alvo aplicados em " + t + ".");
        try {
          const s2 = await store.pushAnalysisLog(t, { tipo: "stop/alvo", stop, alvo, preco: (quotes[t] || {}).price || null });
          if (s2 && s2.analysisLog) setData(s2);
        } catch { /* best-effort */ }
      } catch (e) { flash("Erro ao aplicar: " + (e.message || e)); }
      setStopAlvoFor(null);
    },
    openAbout: () => setAboutOpen(true),
    closeAbout: () => setAboutOpen(false),
    // Camada de entendimento. `openConceito` leva os NÚMEROS do card junto —
    // a explicação é daquele ativo naquele instante, não de manual.
    // `trilha` guarda os conceitos por onde a pessoa passou nesta abertura —
    // é o que dá o "‹ voltar" da cadeia. Abrir pelo card sempre recomeça.
    openConceito: (cid, dados) => setConceitoAberto({ cid, dados: dados || null, trilha: [] }),
    // Abre o conceito primário do SETOR (registro do backend) e conta a
    // descoberta — `gesto` (toques no sublinhado) × `botao` (sr-only) mede se
    // a convenção do pontilhado está sendo encontrada. O nome do campo fica
    // `gesto` por estabilidade do merge monotônico nos dois stores.
    abrirSetor: (setorId, cid, dados, origem) => {
      setConceitoAberto({ cid, dados: dados || null, trilha: [], setor: setorId });
      setData((d) => {
        if (!d) return d;
        const g = { aberturas: 0, gesto: 0, botao: 0, ...((d.config && d.config.gestoUso) || {}) };
        const k = origem === "toque" ? "gesto" : "botao";
        g[k] = (g[k] || 0) + 1;
        // `.catch` na promessa (padrão do marcarConceitoVisto): falhar aqui só
        // perde um tique de medição — nunca a folha.
        store.putConfig({ gestoUso: g }).catch(() => { /* silencioso */ });
        return { ...d, config: { ...d.config, gestoUso: g } };
      });
    },
    // navegar pela cadeia sai do setor: a tela passa a ser o conceito.
    trocarConceito: (cid) => setConceitoAberto((c) => (c ? { ...c, cid, setor: null, trilha: [...(c.trilha || []), c.cid] } : c)),
    voltarConceito: () => setConceitoAberto((c) => {
      const tr = (c && c.trilha) || [];
      if (!tr.length) return c;
      return { ...c, cid: tr[tr.length - 1], trilha: tr.slice(0, -1) };
    }),
    closeConceito: () => setConceitoAberto(null),
    // Marca o conceito como visto: a via proativa dispara UMA vez; depois de
    // marcado, a explicação segue a um toque na mesma afordância.
    marcarConceitoVisto: (cid) => {
      setData((d) => {
        if (!d) return d;
        const atual = Array.isArray(d.config.conceitosVistos) ? d.config.conceitosVistos : [];
        if (atual.includes(cid)) return d;
        return { ...d, config: { ...d.config, conceitosVistos: [...atual, cid] } };
      });
      // `.catch` na PROMESSA, não `try/catch`: o try síncrono não pega um
      // reject (é o padrão herdado do closeTour, que tem o mesmo furo).
      // Falhar aqui só faz a folha reaparecer — melhor que quebrar o fluxo.
      store.putConfig({ conceitosVistos: [cid] }).catch(() => { /* silencioso */ });
    },
    reservarDonoProativo,
    // qa/38 (Help): tour de primeiro uso. Ao fechar, marca tourSeen no doc
    // local (não reaparece); best-effort no servidor.
    openTour: () => setTourOpen(true),
    closeTour: () => {
      setTourOpen(false);
      setData((d) => (d ? { ...d, config: { ...d.config, tourSeen: true } } : d));
      // `.catch` na promessa: o try/catch síncrono que estava aqui não pegava
      // um reject — o tour reapareceria no próximo boot em silêncio.
      store.putConfig({ tourSeen: true }).catch(() => { /* silencioso */ });
    },
    setNotif: async (patch) => {
      const p = { ...patch };
      // momento certo: ao LIGAR o mestre, pede permissão do sistema
      if (patch.enabled === true) {
        const perm = await notify.requestPermission();
        if (perm !== "granted") {
          p.enabled = false;
          if (perm === "denied") flash("Permissão negada. Ative em Ajustes → Notificações → Boris+.");
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
    // Antes: cancelava o timer pendente de OUTRO campo (orçamento/nome) sem
    // nunca enviar o patch dele — tocar em candlePeriod/provider/model logo
    // depois de editar o orçamento apagava o orçamento em silêncio. Agora:
    // manda o que estiver pendente primeiro, depois o patch deste campo.
    saveConfig: async (patch) => {
      await flushCfg();
      try { const s = await store.putConfig(patch); setData(s); setTest({ status: null, msg: "" }); }
      catch (e) { flash("Config: " + (e.message || e)); }
    },
    editConfig: (patch) => {
      // atualiza o campo na hora (controlado) e persiste com debounce
      setData((d) => ({ ...d, config: { ...d.config, ...patch } }));
      cfgPending.current = { ...(cfgPending.current || {}), ...patch };
      if (cfgTimer.current) clearTimeout(cfgTimer.current);
      cfgTimer.current = setTimeout(() => { flushCfg(); }, 600);
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
    // FASE 8B (R2): edição/salvamento POR skill (estudo | operador)
    editSkill: (patch, alvo) => setData((d) => (alvo === "operador"
      ? { ...d, skillOperador: { ...(d.skillOperador || {}), ...patch } }
      : { ...d, skill: { ...d.skill, ...patch } })),
    saveSkill: async (alvo) => {
      const sk = alvo === "operador" ? (data.skillOperador || {}) : data.skill;
      try { const s = await store.putSkill({ name: sk.name, text: sk.text, modo: alvo === "operador" ? "operador" : undefined }); setData(s); flash("Skill salva."); }
      catch (e) { flash("Skill: " + (e.message || e)); }
    },
    restoreSkill: async (alvo) => {
      try { const s = await store.restoreSkill(alvo === "operador" ? "operador" : undefined); setData(s); flash("Instruções restauradas ao padrão."); }
      catch (e) { flash("Erro: " + (e.message || e)); }
    },
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
  // FASE 4 (1.1): TODO estado LIDO no corpo do A precisa estar nas deps —
  // sellModal ausente deixava confirmSell com closure de null (venda muda,
  // botão silenciosamente inerte). Guardado por web/tests/test_wiring_deps.mjs.
  }), [data, catalogSel, buyModal, sellModal, keyDraft, refreshQuotes, flash, analysisModel, wlScanLoading, destaque, quotes, flushCfg]);

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
      // FASE 8B (B4): título e corpo na VOZ do modo (professor × mesa)
      if (n.stop !== false && p.stop != null) {
        if (q.price <= p.stop && st.stopArmed) { notify.notifyIfEnabled(n, "stop", cp.notifStopTitulo(p.t), cp.notifStopCorpo(p.t, price(q.price), price(p.stop))); st.stopArmed = false; }
        else if (q.price > p.stop) st.stopArmed = true;
      }
      if (n.alvo !== false && p.alvo != null) {
        if (q.price >= p.alvo && st.alvoArmed) { notify.notifyIfEnabled(n, "alvo", cp.notifAlvoTitulo(p.t), cp.notifAlvoCorpo(p.t, price(q.price), price(p.alvo))); st.alvoArmed = false; }
        else if (q.price < p.alvo) st.alvoArmed = true;
      }
      if (n.variacao !== false && q.change != null && Math.abs(q.change) >= 5) {
        const key = new Date().toDateString() + (q.change >= 0 ? "+" : "-");
        if (st.varKey !== key) { notify.notifyIfEnabled(n, "variacao", cp.notifVarTitulo(p.t), cp.notifVarCorpo(p.t, pct(q.change), price(q.price))); st.varKey = key; }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quotes, data]);

  // Tela de abertura: na 1a vez (flag do STORE) mostra login/criar conta; o
  // onboarding anônimo (orçamento/risco) só aparece se escolher "usar sem conta".
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
    const m = portfolioMetrics(positions, quotes, data.cash);
    store.putSnapshot({ data: ymd, patrimonio: m.patr, caixa: m.cash, posicoesValor: m.posVal })
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

  // FASE 8 (A3): fonte única do reset de estados derivados na TROCA de escopo
  // (login/logout/exclusão) — evita vazar análises/cotações entre contas.
  const _resetScopeState = () => {
    setAnalysis({}); setExpanded({}); setQuotes({}); setWlScan(null); setDestaque({ stage: "idle" });
    _proativoDono.t = null;   // conta nova recomeça elegível à via proativa
    notifRef.current = {};
  };

  const ctx = {
    // qa/audit-2026-08-07 (item 5): fonte ÚNICA de "estamos em Modo Operador?"
    // — antes recalculado de forma independente em 10+ lugares do arquivo.
    // Novo código deve ler `ctx.operador`, não redevirar de data.config.appMode.
    // `data` pode ser null no boot (antes do 1º getState resolver) — o `ctx`
    // é montado incondicionalmente a cada render, então o guard vem primeiro.
    operador: !!(data && data.config && data.config.appMode === "operador"),
    data, quotes, analysis, expanded, analysisModel, setAnalysisModel, A, quotesAt, quotesLoading, test, keyDraft, setKeyDraft, cp,
    catalogSel, setCatalogSel, buyModal, setBuyModal, cycleBusy, addState, setAddState,
    sellModal, setSellModal, wlScan, wlScanLoading, destaque,
    themePref, themeKey, aboutOpen,
    stopAlvo, stopAlvoFor,
    didatica, conceitoAberto,   // camada de entendimento
    // A folha proativa ADIA enquanto houver outro overlay na tela: ela é
    // one-shot por conceito, para sempre, e abrir sob o portão de abertura ou
    // sob o tour queimaria a estreia sem ninguém ler.
    overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen && !borisIntroOpen,
    goMercado: () => setTab("mercado"),
    // FASE 2 (2.1): ponte Descobrir → Avaliar. Garante o ativo na watchlist,
    // navega para Avaliar e dispara a análise N2 daquele ativo.
    // FASE 5 (fix): mesma correção do addToWatchlist — addWatchlistTicker aceita
    // ativos fora do catálogo (o putWatchlist os descartava em silêncio).
    openAvaliar: async (t) => {
      try {
        if (!(data.watchlist || []).includes(t)) {
          const s = await store.addWatchlistTicker(t);
          setData(s);
        }
        setCarteiraView("main"); setPerfilView("hub"); setTab("mercado");
        A.analyze(t);
      } catch (e) { flash("Erro: " + (e.message || e)); }
    },
    openWelcome: () => setWelcomeOpen(true),
    openWelcomeAuth: () => { welcomeShownRef.current = true; setWelcomeAuthOpen(true); },
    openStopAlvo: (t) => { setStopAlvoFor(t); A.runStopAlvoFor(t); }, // FASE 3: abre popup do ativo e analisa só ele
    markOnboarded: async () => {
      setData((d) => (d ? { ...d, config: { ...d.config, onboarded: true } } : d));
      try { await store.putConfig({ onboarded: true }); } catch { /* silencioso */ }
    },
    // F6: fecha a apresentação do Boris e grava `borisIntroVisto` — nunca
    // mais reaparece sozinha (mesmo espelho de `markOnboarded`).
    marcarBorisIntroVisto: async () => {
      setBorisIntroOpen(false);
      setData((d) => (d ? { ...d, config: { ...d.config, borisIntroVisto: true } } : d));
      try { await store.putConfig({ borisIntroVisto: true }); } catch { /* silencioso */ }
    },
    // FASE 2 — conta opcional. Handlers guardados; erros sobem para o AuthModal.
    // FASE 8 (A3): toda TROCA de escopo (entrar OU sair) limpa os estados
    // derivados em memória — sem isso, análises/cotações do escopo anterior
    // vazavam para o novo (o merge {...seed, ...cur} do loadState preservava
    // o antigo). Fonte única: _resetScopeState.
    authUser,
    openAuth: () => setAuthOpen(true),
    // FASE 8B (N2): no NATIVO o estado pós-login vem SEMPRE do deviceStore
    // (local-first; o namespace já trocou) — o estado do servidor sobrescrevia
    // o doc do aparelho e a identidade (appMode/termo/risco) "se perdia".
    login: async ({ email, password }) => {
      const r = await auth.login({ email, password });
      if (r && r.user) setAuthUser(r.user);
      _resetScopeState();
      if (!isNative && r && r.state) setData(r.state); else await loadState();
      refreshQuotes();
      flash("Conectado.");
      return r;
    },
    register: async ({ email, password, name }) => {
      const r = await auth.register({ email, password, name });
      if (r && r.user) setAuthUser(r.user);
      _resetScopeState();
      if (!isNative && r && r.state) setData(r.state); else await loadState();
      refreshQuotes();
      flash("Conta criada.");
      return r;
    },
    // FASE 2 — login social (Apple/Google). A UI está pronta; o token nativo é
    // obtido pelos plugins Capacitor quando configurados. O servidor já valida.
    oauth: async ({ provider, idToken, name, authorizationCode }) => {
      const r = await auth.oauth({ provider, idToken, name: name || undefined, authorizationCode: authorizationCode || undefined });
      if (r && r.user) setAuthUser(r.user);
      _resetScopeState();
      if (!isNative && r && r.state) setData(r.state); else await loadState();
      refreshQuotes();
      flash("Conectado.");
      return r;
    },
    // FASE 8 (A3): sair da conta é um RESET completo, não só o token. Antes o
    // logout limpava token/escopo mas: (a) analysis/expanded/quotes/wlScan/
    // destaque seguiam NA MEMÓRIA com os dados da conta; (b) nada levava de
    // volta ao portão de entrada — o app "parecia" logado. Agora: limpa os
    // estados derivados, recarrega o escopo anônimo, atualiza cotações e
    // REABRE o welcome (saída visível e inequívoca).
    logout: async () => {
      await auth.logout();
      setAuthUser(null);
      _resetScopeState();
      await loadState();
      refreshQuotes();
      setCarteiraView("main"); setPerfilView("hub"); setTab("evolucao");
      welcomeShownRef.current = true; setWelcomeOpen(true);
      flash("Você saiu da conta.");
    },
    deleteAccount: async () => {
      await auth.deleteAccount();
      setAuthUser(null);
      _resetScopeState();
      await loadState();
      refreshQuotes();
      setCarteiraView("main"); setPerfilView("hub"); setTab("evolucao");
      welcomeShownRef.current = true; setWelcomeOpen(true);
      flash("Conta excluída.");
    },
  };

  // chips do topo
  const { patr, dia } = useMemo(() => {
    if (!data) return { patr: null, dia: 0 };
    const m = portfolioMetrics(data.positions, quotes, data.cash);
    return { patr: m.patr, dia: m.dayVal };
  }, [data, quotes]);

  const tickerItems = useMemo(() => {
    if (!data) return [];
    return (data.watchlist || []).map((t) => { const q = quotes[t] || {}; return { t, priceStr: price(q.price), chStr: pct(q.change), color: (q.change || 0) >= 0 ? T.positive : T.negative, arrow: (q.change || 0) >= 0 ? "▲" : "▼" }; });
  }, [data, quotes]);

  // F4 (Boris em todas as telas): qual aba o pet está explicando agora.
  // Histórico é sub-tela de Carteira (carteiraView), as demais mapeiam 1:1
  // com `tab`. As sub-telas do Perfil (config/ia/notificações/…) todas caem
  // em "perfil" — a tabela do plano não pede granularidade ali.
  const petTela = tab === "carteira" ? (carteiraView === "historico" ? "historico" : "carteira") : tab;

  // O snapshot por tela é o MESMO view-model que a tela já usa para renderizar
  // (D6 do plano): nada de raspar tela, nada de conta nova. "mercado" segue
  // FORA daqui de propósito — o formato dele já existe e não muda (vem de
  // `r.itens`, dentro do próprio PetSheet, depois que /api/pet/resumo responde).
  const petSnapshot = useMemo(() => {
    if (!data) return {};
    switch (petTela) {
      case "carteira": {
        const m = portfolioMetrics(data.positions, quotes, data.cash);
        return {
          posicoes: (data.positions || []).map((p) => ({ ticker: p.t, qty: p.qty, precoMedio: p.avg, stop: p.stop, alvo: p.alvo })),
          caixa: data.cash,
          resultadoAberto: m.openPnL,
          resultadoAbertoPct: m.openPct,
          patrimonio: m.patr,
        };
      }
      case "evolucao": {
        const m = portfolioMetrics(data.positions, quotes, data.cash);
        const diaPct = dayReturnPct(m.patr, m.dayVal);
        const hoje = new Date().toISOString().slice(0, 10);
        const ec = equityCurve(data.equitySnapshots, (data.config || {}).initialBudget, m.patr, hoje);
        return {
          patrimonio: m.patr,
          resultadoDia: m.dayVal,
          resultadoDiaPct: diaPct,
          retornoAcumuladoPct: ec.retAcum,
          drawdownPct: ec.drawdown,
        };
      }
      case "radar": {
        // O Radar em si guarda o resultado da varredura em estado LOCAL da tela
        // (não em `ctx`) — reaproveitar exigiria içar esse estado. `wlScan` é o
        // scan da MESMA família (confluência + setup, `store.scan`) que já vive
        // em `ctx` e alimenta a Home; é o candidato mais próximo sem içar
        // estado. Decisão registrada aqui: candidatos ficam restritos à
        // watchlist, não ao universo completo do Radar.
        const results = (wlScan && wlScan.results) || [];
        return {
          candidatos: results.slice(0, 12).map((r) => ({ ticker: r.ticker, confluencia: r.confluencia, melhorSetup: r.melhorSetup, decisao: r.plano && r.plano.decisao })),
        };
      }
      case "agente": {
        const ag = data.agent || {};
        return {
          ativo: !!ag.serverEnabled,
          modo: ag.mode || (ag.autonomous ? "executar" : "sinalizar"),
          regras: ag.rules || {},
        };
      }
      case "historico": {
        const h = data.history || [];
        const fechadas = h.filter((x) => x && x.pnl != null);
        const pnlTotal = fechadas.reduce((s, x) => s + (Number(x.pnl) || 0), 0);
        return {
          operacoes: h.slice(-12).map((x) => ({ data: x.date, tipo: x.type, ticker: x.t, qty: x.qty, preco: x.price, pnl: x.pnl })),
          totalOperacoes: h.length,
          pnlTotalFechadas: pnlTotal,
        };
      }
      case "perfil": {
        const cfg = data.config || {};
        const prof = data.profile || {};
        return {
          modo: cfg.appMode || "estudo",
          orcamentoInicial: cfg.initialBudget,
          risco: prof.risco,
          horizonte: prof.horizonte,
          notificacoesAtivas: !!(cfg.notif && cfg.notif.enabled),
        };
      }
      default:
        return {};
    }
  }, [petTela, data, quotes, wlScan]);

  const shell = {
    // O shell REDECLARA o bloco de tema (.b3-theme-dark/-light), então precisa
    // redeclarar o modo junto. O override do modo é um seletor COMPOSTO
    // (.b3-mode-operador.b3-theme-dark) e as duas classes têm que estar no
    // MESMO elemento: com só "b3-theme-dark" aqui, a regra base do tema vencia
    // dentro do shell e todo var(--accent) da árvore voltava pro acento do
    // ESTUDO — o modo só sobrevivia no <html>, acima do app inteiro. Defeito
    // antigo que ficou invisível enquanto o acento do Estudo era o âmbar da
    // marca (parecia cor de marca); com o azul do Brand Book v2 ele apareceu na
    // hora, porque o Operador passou a se pintar de Estudo.
    className: "b3 b3-shell b3-theme-" + themeKey + (appMode === "operador" ? " b3-mode-operador" : ""),
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
    <ThemeCtx.Provider value={{ key: themeKey, mode: appMode }}>
    <div {...shell}>
      <GlobalStyle />
      {/* qa/mock v2: FRISO de modo — barra fina no topo na cor do modo (sinal
          redundante de identidade, além do acento + linha de modo no Topbar). */}
      <div aria-hidden style={{ height: "3px", flex: "none", background: `linear-gradient(90deg, ${T.accent}, ${T.accentSoft})` }} />
      <Ticker items={tickerItems} live={Object.keys(quotes).length > 0} />
      <Topbar patr={patr} dia={dia} caixa={data.cash} name={firstName} modeChip={cp.chipModo} onProfile={() => { setPerfilView("hub"); setTab("perfil"); }} />

      <main ref={mainRef} style={{ position: "relative", flex: 1, minHeight: 0, overflowY: "auto", WebkitOverflowScrolling: "touch" }}>
        {pullY > 0 && (
          <div style={{ position: "absolute", top: "8px", left: "50%", transform: "translateX(-50%)", zIndex: 5, opacity: Math.min(1, pullY / 70), color: T.accent, fontSize: "12px", fontWeight: 700, display: "flex", alignItems: "center", gap: "7px", pointerEvents: "none" }}>
            <span className={pullY >= 70 ? "spin" : undefined} style={{ display: "inline-block" }}>↻</span>
            {pullY >= 70 ? "Solte para atualizar" : "Puxe para atualizar"}
          </div>
        )}
        <div style={{ maxWidth: "1060px", margin: "0 auto", padding: "24px 18px 34px", transform: pullY ? `translateY(${pullY}px)` : undefined, transition: pullY ? "none" : "transform .2s ease" }}>
          {tab === "evolucao" && <EvolucaoScreen ctx={ctx} />}
          {tab === "mercado" && <MercadoScreen ctx={ctx} />}
          {tab === "radar" && <RadarScreen ctx={ctx} />}
          {tab === "agente" && <AgenteScreen ctx={ctx} />}
          {tab === "carteira" && (carteiraView === "historico"
            ? (<><BackHeader title="Histórico de operações" onBack={() => setCarteiraView("main")} /><HistoricoScreen ctx={ctx} /></>)
            : (<><CapitalCurve ctx={ctx} /><CarteiraScreen ctx={ctx} /><div style={{ marginTop: "14px" }}><button onClick={() => setCarteiraView("historico")} style={{ width: "100%", minHeight: "48px", padding: "13px", borderRadius: "13px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, fontWeight: 700, fontSize: "13.5px", display: "flex", alignItems: "center", justifyContent: "space-between" }}><span>Ver histórico de operações</span><span aria-hidden style={{ color: T.textFaint }}>›</span></button></div></>))}
          {tab === "perfil" && (perfilView === "config"
            ? (<><BackHeader title="Conta & preferências" onBack={() => setPerfilView("hub")} /><ConfigScreen ctx={ctx} /></>)
            : perfilView === "ia"
              ? (<><BackHeader title="Configurações de IA" onBack={() => setPerfilView("hub")} /><AiConfigScreen ctx={ctx} /></>)
              : perfilView === "notificacoes"
                ? (<><BackHeader title="Notificações" onBack={() => setPerfilView("hub")} /><NotificacoesScreen ctx={ctx} /></>)
                : perfilView === "eficiencia"
                  ? (<><BackHeader title="Eficiência da IA" onBack={() => setPerfilView("hub")} /><EficienciaIAScreen ctx={ctx} /></>)
                  : perfilView === "atividade"
                    ? (<><BackHeader title="Atividade da IA" onBack={() => setPerfilView("hub")} /><AtividadeIAScreen ctx={ctx} /></>)
                  : perfilView === "logs"
                    ? (<><BackHeader title="Logs & debug" onBack={() => setPerfilView("hub")} /><LogsDebugScreen ctx={ctx} /></>)
                    : perfilView === "ajuda"
                      ? (<><BackHeader title="Como funciona" onBack={() => setPerfilView("hub")} /><AjudaScreen ctx={ctx} /></>)
                      : <PerfilHub ctx={ctx} onOpen={setPerfilView} />)}
        </div>
      </main>

      <BottomNav tab={tab} setTab={navigate} cp={cp} />

      {catalogOpen && <CatalogModal ctx={ctx} />}
      {buyModal && <BuyModal ctx={ctx} />}
      {sellModal && <SellModal ctx={ctx} />}
      {techFor && (
        <TechnicalModal
          ticker={techFor}
          name={(data.catalog.find((c) => c.t === techFor) || {}).n}
          quote={quotes[techFor]}
          position={data.positions.find((p) => p.t === techFor)}
          period={(data.config && data.config.candlePeriod) || "1y"}
          onClose={A.closeTech}
        />
      )}
      {aboutOpen && <AboutModal onClose={A.closeAbout} />}
      {tourOpen && <TourModal ctx={ctx} />}
      {/* O PET: em QUALQUER aba, em QUALQUER modo de trabalho (Fase 1 da
          auditoria de UX, 2026-08-08, reverteu a restrição a Operador — o
          vocabulário já variava por modo em assistente.py/_pet_resumo_*;
          faltava só deixar o FAB aparecer) — e NUNCA abre sozinho. O FAB
          some sob overlays para não competir com folha aberta. */}
      {didatica && didatica.ligada && ctx.overlayLivre && (
        <PetFab onOpen={abrirPet} />
      )}
      {petOpen && <PetSheet didatica={didatica} tela={petTela} snapshot={petSnapshot} onClose={() => setPetOpen(false)} />}
      {/* F6: apresentação do Boris, 1x — "Conversar agora" abre a MESMA folha
          do pet que o FAB abriria (reaproveita petOpen, não duplica chat);
          "Depois" só fecha. Os dois marcam borisIntroVisto (nunca mais volta
          sozinha). */}
      {borisIntroOpen && (
        <BorisIntro
          onConversar={() => { ctx.marcarBorisIntroVisto(); abrirPet(); }}
          onDepois={() => ctx.marcarBorisIntroVisto()}
        />
      )}
      {conceitoAberto && (
        <ConceitoSheet cid={conceitoAberto.cid} dados={conceitoAberto.dados}
          setor={conceitoAberto.setor || null}
          didatica={didatica} onClose={A.closeConceito}
          // Troca o conceito MANTENDO os dados do card: a allowlist do backend
          // filtra o que serve a cada um, então o encadeamento segue ancorado
          // no mesmo ativo em vez de virar texto de manual.
          onTrocar={A.trocarConceito}
          voltar={(conceitoAberto.trilha || []).length ? A.voltarConceito : null} />
      )}
      {authOpen && <AuthModal ctx={ctx} onClose={() => setAuthOpen(false)} />}
      {stopAlvoFor && <StopAlvoModal ctx={ctx} />}
      {welcomeAuthOpen && (
        <WelcomeAuthScreen
          ctx={ctx}
          onAuthed={() => { setWelcomeAuthOpen(false); ctx.markOnboarded(); }}
          onSkip={() => {
            // BLOCO 2 (boot gate): "usar sem conta" só roda o onboarding
            // (orçamento/risco) para quem NUNCA concluiu; veterano entra direto.
            setWelcomeAuthOpen(false);
            if (!(data.config && data.config.onboarded)) setWelcomeOpen(true);
          }}
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
