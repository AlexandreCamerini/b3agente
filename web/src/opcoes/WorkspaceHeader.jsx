/**
 * WorkspaceHeader.jsx — Fase 34 (34-01), fundação do split hub/workspace.
 *
 * Existe para D-05/NAV-03: um único caminho de volta ao hub — nome do ticker
 * selecionado + botão "Voltar", sem breadcrumb e sem pilha de navegação. O
 * reset de tese/vencimento/alvo/stop NÃO mora aqui: mora em `escolherTicker`,
 * no orquestrador (`OpcoesScreen.jsx`) — este componente só dispara o
 * callback que o chamador decide o que fazer com ele (D-03 do
 * 34-CONTEXT.md).
 *
 * Props-only, zero hook, zero leitura de `ctx`/store: o orquestrador é o
 * único dono do estado compartilhado (REORG-03/04 da Fase 33, invariante que
 * esta fase não pode quebrar).
 */

// Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` —
// espelho declarado, mesmo padrão de SecaoVigias.jsx/OportunidadesOpcoes.jsx.
// Zero import do núcleo do app (seria ciclo, ADR-027 Decisão 3).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["borderSubtle", "bgPanel", "textPrimary", "textSecondary"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Botão de navegação, não a ação primária da tela — por isso usa o estilo
// neutro `BOTAO` (mesmo espelho de OpcoesScreen.jsx:122-126), nunca a cor de
// destaque reservada à pill ativa (Color do UI-SPEC).
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};

export default function WorkspaceHeader({ ticker, onVoltar, cp }) {
  return (
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "14px", padding: "12px 14px", background: T.bgPanel }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
        <span style={{ fontSize: "15px", fontWeight: 800, color: T.textPrimary }}>{ticker}</span>
        <button type="button" onClick={onVoltar} style={BOTAO}>
          {(cp && cp.opcoesVoltarAoHub) || "Voltar"}
        </button>
      </div>
    </div>
  );
}
