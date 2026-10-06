/**
 * fluxoEstilo.js — Fase 48 (48-08): tokens e estilos compartilhados das telas
 * novas do fluxo (hub, objetivo, confirmar). Módulo sem JSX.
 *
 * Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` (padrão
 * VARKEY/TOKENS de OpcoesScreen.jsx). Zero hex literal; zero token novo.
 * Tipografia do contrato (48-UI-SPEC): 12/700, 14/400, 16/700, 24/700.
 */
import { prefereMovimentoReduzido } from "../estruturaCard.js";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "textPrimary", "textSecondary",
  "textMuted", "textFaint", "accent", "accentTint10", "positive", "negative", "warn",
  "onAccent"];
export const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

export const ALVO_MIN = 44;
export const CTA_MIN = 48;

// espelho de entendimento.jsx:85 (SR_ONLY não é exportado de lá).
export const SR_ONLY = { position: "absolute", width: "1px", height: "1px", padding: 0, margin: "-1px", overflow: "hidden", clipPath: "inset(50%)", whiteSpace: "nowrap", border: 0 };

// Foco visível: outline 2px accent, offset 2.
export const FOCO = { outline: `2px solid ${T.accent}`, outlineOffset: "2px" };

export const TIPO = {
  label: { fontSize: "12px", fontWeight: 700, lineHeight: 1.4 },
  corpo: { fontSize: "14px", fontWeight: 400, lineHeight: 1.5 },
  titulo: { fontSize: "16px", fontWeight: 700, lineHeight: 1.2 },
  display: { fontSize: "24px", fontWeight: 700, lineHeight: 1.2 },
};

// espelho de App.jsx:313 (Fredoka já carregada em index.html; sem @font-face novo).
export const DISPLAY = "'Fredoka', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

export const NUM = { fontVariantNumeric: "tabular-nums" };
export const MONO = { fontFamily: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace', fontVariantNumeric: "tabular-nums" };

export function reduzido() {
  return prefereMovimentoReduzido(typeof window !== "undefined" ? window : null);
}

// Só transform e opacity; reduced-motion desliga tudo.
export function transicaoTela(red) {
  return red ? {} : { transition: "opacity 200ms ease-out, transform 200ms ease-out" };
}

export function transicaoDegrau(red) {
  return red ? {} : { transition: "opacity 180ms ease-out, transform 180ms ease-out" };
}
