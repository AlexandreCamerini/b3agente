/**
 * VigiasSheet.jsx — Fase 39 (39-02), D-07 do 39-CONTEXT.md.
 *
 * "Vigia" vira ícone/badge com contador no cabeçalho da aba Opções, visível
 * independente de qual das 3 abas está ativa (D-01), abrindo um bottom
 * sheet local em vez de ser bloco fixo no hub. Ícone: OLHO — "vigia" no
 * vocabulário do produto é observar, não notificar (recomendação do
 * 39-UI-SPEC.md, não travada como decisão, adotada aqui).
 *
 * Isolamento ADR-027 (Emenda 3): módulo terceiro de `web/src/opcoes/`, ZERO
 * import de `App.jsx`. O shell do sheet (zIndex 86, geometria de
 * bottom-sheet) é o MESMO já em produção em `web/src/entendimento.jsx`
 * (`ConceitoSheet`) — copiado aqui, não importado, porque `entendimento.jsx`
 * é módulo de fora de `web/src/opcoes/` mas ainda assim não referencia
 * `App.jsx` (é o mesmo padrão de reuso de geometria que a Fase 38 já usa
 * para o "saiba mais" local desta aba).
 *
 * Sem fetch, sem `store.*`/`ctx.*` — os dois componentes recebem tudo por
 * prop. `VigiasSheet` é o shell puro; o conteúdo (`SecaoVigias.jsx` inteiro)
 * entra como `children`, wiring que fica para o Plano 04 (este plano só cria
 * o contrato).
 */
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgPanel", "borderSubtle", "textSecondary", "accent", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// D-07: número no badge SÓ quando `medido && n > 0` — nunca "0" antes de
// medir (princípio 4 do CLAUDE.md). `medido` vem de quem chama (mesmo
// critério que `temEstadoDosVigias` já usa em OpcoesScreen.jsx hoje).
export function VigiasBadge({ n, medido, onAbrir, cp }) {
  const c = cp || {};
  const rotuloFn = typeof c.opcoesVigiasAbrirSheet === "function"
    ? c.opcoesVigiasAbrirSheet
    : (k) => (k > 0 ? k + " vigias — abrir" : "Vigias — abrir");
  return (
    <button
      type="button"
      onClick={onAbrir}
      aria-label={rotuloFn(medido ? n : 0)}
      style={{ minHeight: "44px", padding: "8px 10px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textSecondary, display: "inline-flex", alignItems: "center", gap: "6px" }}
    >
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      {medido && n > 0 && (
        <span style={{ color: T.accent, fontWeight: 700, fontSize: "13px" }}>{n}</span>
      )}
    </button>
  );
}

// Shell reusado verbatim de `ConceitoSheet` (entendimento.jsx:200-209):
// zIndex 86 — a mesma folha que já abre acima de TODOS os outros overlays do
// app; VigiasSheet e ConceitoSheet nunca abrem ao mesmo tempo (não travado
// como requisito, citado para quem for ligar os dois não os empilhar por
// acidente, ver 39-UI-SPEC.md).
export function VigiasSheet({ aberto, onFechar, cp, children }) {
  if (!aberto) return null;
  const c = cp || {};
  return (
    <div
      onClick={onFechar}
      role="dialog"
      aria-modal="true"
      aria-label={c.opcoesVigiasSheetTitulo || "Seus vigias"}
      style={{ position: "fixed", inset: 0, zIndex: 86, background: T.scrim, display: "flex", alignItems: "flex-end", justifyContent: "center" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: "100%", maxWidth: "520px", background: T.bgPanel, borderTop: `1px solid ${T.borderSubtle}`, borderRadius: "18px 18px 0 0", padding: "16px 18px calc(18px + env(safe-area-inset-bottom))", maxHeight: "82vh", overflowY: "auto" }}
      >
        <div style={{ width: "38px", height: "4px", borderRadius: "999px", background: T.borderSubtle, margin: "0 auto 12px" }} aria-hidden />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onFechar}
            style={{ minHeight: "44px", padding: "0 4px", background: "transparent", border: "none", color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}
          >
            {c.opcoesVigiasFechar || "Fechar"}
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
