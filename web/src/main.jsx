import React from "react";
import { createRoot } from "react-dom/client";
import { Capacitor } from "@capacitor/core";
import App from "./App.jsx";

// C1 — Rede de segurança: qualquer exceção de render em QUALQUER ponto da árvore
// cai aqui em vez de desmontar a página (tela branca). Mostra aviso legível com
// botão de recarregar + detalhe técnico (útil também no iPhone via Web Inspector).
// Estilos inline, sem dependência do tema, para funcionar mesmo se o erro vier do
// próprio App. Paleta alinhada à marca Boris+ (escuro #10121a / acento #f2a93b).
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) {
    try { console.error("[b3] erro de render capturado:", error, info && info.componentStack); } catch { /* ignore */ }
  }
  render() {
    if (!this.state.error) return this.props.children;
    const msg = (this.state.error && this.state.error.message) || String(this.state.error);
    return (
      <div style={{ minHeight: "100vh", boxSizing: "border-box", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px", paddingTop: "calc(24px + env(safe-area-inset-top))", background: "#10121a", color: "#eef1f8", fontFamily: "'Nunito', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif" }}>
        <div style={{ width: "100%", maxWidth: "420px", textAlign: "center" }}>
          <div style={{ fontSize: "17px", fontWeight: 700, marginBottom: "8px" }}>Algo saiu do lugar</div>
          <p style={{ fontSize: "13px", lineHeight: 1.5, color: "#9aa6b6", margin: "0 0 16px" }}>
            O app encontrou um erro ao desenhar a tela, mas seus dados continuam salvos. Recarregue para continuar.
          </p>
          <button
            onClick={() => { try { location.reload(); } catch { /* ignore */ } }}
            style={{ minHeight: "44px", padding: "11px 22px", borderRadius: "9px", border: "1px solid #f2a93b", background: "rgba(242,169,59,.15)", color: "#f2a93b", fontWeight: 700, fontSize: "14px", cursor: "pointer" }}
          >
            Recarregar
          </button>
          <details style={{ marginTop: "16px", textAlign: "left" }}>
            <summary style={{ fontSize: "12px", color: "#8a96a6", cursor: "pointer" }}>Detalhe técnico</summary>
            <pre style={{ marginTop: "8px", padding: "10px", borderRadius: "8px", background: "rgba(255,255,255,.04)", color: "#9aa6b6", fontSize: "11px", lineHeight: 1.4, whiteSpace: "pre-wrap", wordBreak: "break-word", overflowX: "auto" }}>{msg}</pre>
          </details>
        </div>
      </div>
    );
  }
}

createRoot(document.getElementById("root")).render(
  <ErrorBoundary>
    <React.StrictMode>
      <App />
    </React.StrictMode>
  </ErrorBoundary>
);

if (Capacitor.isNativePlatform()) {
  // Native (iOS): match the status bar to the dark theme.
  import("@capacitor/status-bar")
    .then(({ StatusBar, Style }) => {
      StatusBar.setStyle({ style: Style.Dark }).catch(() => {});
    })
    .catch(() => {});
  // FASE 4 (Bloco 2): ponte de login social (Apple/Google) — só no nativo;
  // falha de import não derruba o app (botões mantêm o aviso amigável).
  import("./social.js")
    .then(({ registerSocialBridge }) => registerSocialBridge())
    .catch(() => {});
} else if ("serviceWorker" in navigator) {
  // Web (desktop / mobile browser): enable the installable PWA.
  import("virtual:pwa-register")
    .then(({ registerSW }) => registerSW({ immediate: true }))
    .catch(() => {});
}
