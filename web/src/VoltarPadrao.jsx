// Onda B (2026-10-08, decisão 4) — quick 261008-1ar: botão Voltar ÚNICO de navegação.
// Duas variantes, mesma altura de alvo (44px), mesmo foco (o chamador pode passar
// onFocus/onBlur via ...rest):
//   - sem `rotulo`: ícone ‹ (BackHeader das sub-telas)
//   - com `rotulo`: texto VERBATIM (o copy "‹ voltar" é travado por guardião)
// Cancelar de modais de compra/venda NÃO usa este componente (não é navegação).
// Sem import de App.jsx; SSR-safe (sem window).
export default function VoltarPadrao({ onClick, rotulo, ariaLabel, style, ...rest }) {
  if (rotulo) {
    return (
      <button
        type="button"
        onClick={onClick}
        {...(ariaLabel ? { "aria-label": ariaLabel } : null)}
        {...rest}
        style={{
          minHeight: "44px", padding: "0 12px 0 0", border: "none", background: "transparent",
          color: "var(--accent)", fontSize: "12px", fontWeight: 700, lineHeight: 1.4, cursor: "pointer",
          ...style,
        }}
      >
        {rotulo}
      </button>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel || "Voltar"}
      {...rest}
      style={{
        minWidth: "44px", minHeight: "44px", display: "flex", alignItems: "center", justifyContent: "center",
        borderRadius: "10px", border: "none", background: "transparent", color: "var(--text-secondary)",
        cursor: "pointer",
        ...style,
      }}
    >
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden><polyline points="15 5 8 12 15 19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
    </button>
  );
}
