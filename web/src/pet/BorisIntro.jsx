/**
 * BorisIntro.jsx — F6: apresentação do Boris, mostrada UMA ÚNICA VEZ, na
 * primeira vez que a pessoa chega na aba inicial (Mercado/Watchlist) depois
 * de passar pelo gate de login/onboarding (`WelcomeAuthScreen`/`OnboardingModal`,
 * que continuam intocados — esta é uma tela DIFERENTE, mostrada DEPOIS deles).
 *
 * Ordem do conteúdo é REGRA, não estética (decisão D8 do plano):
 *   1) o que o Boris NÃO faz (não recomenda, não envia ordem, carteira simulada)
 *   2) o que ele sabe (a base de conhecimento determinística, F2)
 *   3) como chamá-lo (o FAB — a coruja flutuante, presente em toda tela)
 * Os dois botões finais reaproveitam o que já existe: "Conversar agora" abre
 * a MESMA folha do pet (`PetSheet`/`PetFab`, F4/F5) que qualquer toque no FAB
 * abriria — nenhum estado novo de chat é criado aqui. "Depois" só fecha.
 *
 * Vocabulário: as frases abaixo ecoam o registro já estabelecido em
 * `server/app/assistente.py` (_regras: "Nada aqui é recomendação de
 * investimento... A carteira é simulada; nenhuma ordem é enviada a corretora
 * nenhuma.") e `server/app/kb.py` (verbete "mkt-carteira-simulada" e o
 * docstring das 9 famílias: indicadores, estrutura, familias, modelos,
 * setups, plano_risco, fundamentos, mercado_b3, estados_app) — não são
 * frases novas inventadas do zero.
 *
 * Mesmos tokens de tema (`var(--x)`) que `BorisChat.jsx` já usa, pelo mesmo
 * motivo: importar `T`/`card` de `App.jsx` criaria import circular (App.jsx
 * importa este arquivo).
 */
import Boris from "./Boris.jsx";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgPanel", "bgCard", "borderSubtle", "textPrimary", "textSecondary",
  "textMuted", "textFaint", "accent", "accentTint", "onAccent", "scrim", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const IA_GRAD = { background: "linear-gradient(135deg,var(--accent),var(--accent-soft))", WebkitBackgroundClip: "text", backgroundClip: "text", WebkitTextFillColor: "transparent" };

export default function BorisIntro({ onConversar, onDepois }) {
  return (
    <div role="dialog" aria-label="Conheça o Boris, o assistente do BolsIA"
      style={{ position: "fixed", inset: 0, zIndex: 87, background: T.scrim, display: "flex", alignItems: "center", justifyContent: "center", padding: "18px", overflowY: "auto" }}>
      <div style={{ width: "100%", maxWidth: "420px", background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderRadius: "18px", padding: "24px 22px", boxSizing: "border-box" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", marginBottom: "16px" }}>
          <Boris size={110} />
          <div style={{ fontSize: "18px", fontWeight: 800, marginTop: "6px", letterSpacing: "-0.01em" }}>
            Este é o <span style={IA_GRAD}>Boris</span>
          </div>
          <div style={{ fontSize: "12.5px", color: T.textFaint, marginTop: "2px" }}>
            O assistente do BolsIA nesta tela e em todas as outras
          </div>
        </div>

        {/* 1) O que ele NÃO faz — primeiro, sempre primeiro. */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
          <span aria-hidden style={{ fontSize: "16px", lineHeight: 1.4, flex: "none" }}>🚫</span>
          <p style={{ margin: 0, fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6 }}>
            O Boris <b>não recomenda</b> compra ou venda e <b>não envia ordem</b> para
            corretora nenhuma — a carteira é <b>simulada</b>. Nada do que ele diz é
            recomendação de investimento nem promessa de resultado.
          </p>
        </div>

        {/* 2) O que ele sabe — a base de conhecimento (F2), em uma frase. */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
          <span aria-hidden style={{ fontSize: "16px", lineHeight: 1.4, flex: "none" }}>📚</span>
          <p style={{ margin: 0, fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6 }}>
            Ele conhece indicadores, estrutura de preço, modelos, setups e o
            vocabulário da B3 — a mesma base de estudo que o app usa para
            explicar cada tela.
          </p>
        </div>

        {/* 3) Como chamá-lo — o FAB, presente em toda tela. */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
          <span aria-hidden style={{ fontSize: "16px", lineHeight: 1.4, flex: "none" }}>🦉</span>
          <p style={{ margin: 0, fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.6 }}>
            Para chamá-lo, toque na coruja flutuante — ela fica disponível em
            qualquer tela do Estudo, a qualquer momento.
          </p>
        </div>

        <button onClick={onConversar}
          style={{ width: "100%", minHeight: "46px", marginBottom: "10px", borderRadius: "11px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 800, fontSize: "14px" }}>
          Conversar agora
        </button>
        <button onClick={onDepois}
          style={{ width: "100%", minHeight: "40px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textMuted, fontWeight: 700, fontSize: "13px" }}>
          Depois
        </button>
      </div>
    </div>
  );
}
