/**
 * BorisChat.jsx — F5: conversa MULTI-TURNO com o Boris (bolhas + voz + STT).
 *
 * Inspirado no layout de `Downloads/BorisWidget.jsx` (referência de UX: bolhas,
 * textarea, botão de mic, indicador "pensando"), mas:
 *   - fala com `useBorisBrain` (contrato real de `/api/assistente`), não o
 *     `{message,history,client}` do anexo;
 *   - usa os tokens de tema do app (`T.*`, mesmos nomes de variável CSS que
 *     `App.jsx` define em `PALETTE`/`themeVarBlock`) em vez das cores fixas
 *     `C` do anexo;
 *   - a VOZ é dirigida pelo MESMO mecanismo que `PetSheet` já usa: quem é
 *     dono da fala é `falarTexto`/`calarVoz` (GC do Safari, cala ao fechar);
 *     este componente só liga `boris.talk()/.stop()` nos callbacks delas —
 *     não chama `Boris.speak()` direto, para não abrir um segundo caminho
 *     de voz. `falarTexto`/`calarVoz` chegam por PROP (donos ficam em
 *     `App.jsx`) — evita import circular entre este arquivo e `App.jsx`.
 */
import { useEffect, useRef, useState } from "react";
import { useBorisBrain } from "./useBorisBrain.js";
// O mesmo renderizador que a análise do card usa. Mora em `markdown.jsx` (e
// não em `App.jsx`) justamente para este arquivo poder importá-lo sem o
// import circular descrito no cabeçalho.
import { Markdown } from "../markdown.jsx";

// Mesmos NOMES de variável CSS que `App.jsx` (`const T = ...` sobre
// `PALETTE`) já injeta em `:root` — só os tokens que este componente usa.
// Não duplica cores: `var(--x)` aqui resolve para o MESMO valor, no MESMO
// tema (claro/escuro), sem precisar importar `T` de `App.jsx` (que criaria
// import circular, já que `App.jsx` importa este arquivo).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const MAX_PERGUNTA = 400; // mesmo teto de `assistente.MAX_PERGUNTA`

// STT é MELHORIA PROGRESSIVA: só existe se o navegador tiver a API. Ausência
// (Safari/WKWebView antigo, a maioria dos casos) não é erro — o botão some.
function useSTT() {
  const SR = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
  const [ouvindo, setOuvindo] = useState(false);
  const recRef = useRef(null);
  const iniciar = (onResultado) => {
    if (!SR || ouvindo) return;
    try {
      const rec = new SR();
      rec.lang = "pt-BR";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onresult = (e) => {
        const texto = e.results && e.results[0] && e.results[0][0] && e.results[0][0].transcript;
        if (texto) onResultado(texto);
      };
      rec.onerror = () => setOuvindo(false);
      rec.onend = () => setOuvindo(false);
      recRef.current = rec;
      setOuvindo(true);
      rec.start();
    } catch { setOuvindo(false); }
  };
  const parar = () => { try { recRef.current && recRef.current.stop(); } catch { /* já parou */ } setOuvindo(false); };
  return { suportado: !!SR, ouvindo, iniciar, parar };
}

export default function BorisChat({ tela, snapshot, sugestoes, borisRef, falarTexto, calarVoz }) {
  const { mensagens, enviar, pensando, erro } = useBorisBrain({ tela, snapshot });
  const [q, setQ] = useState("");
  const stt = useSTT();
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [mensagens, pensando]);

  // Desmontar (fechar o chat, trocar de tela) cala a voz — mesma regra do
  // resumo: coruja falando sozinha atrás de outra tela não pode existir.
  useEffect(() => () => { calarVoz && calarVoz(); }, [calarVoz]);

  const enviarAgora = async (texto) => {
    const pergunta = (texto == null ? q : texto).trim();
    if (!pergunta || pensando) return;
    setQ("");
    borisRef && borisRef.current && borisRef.current.setState("thinking");
    const resp = await enviar(pergunta);
    if (!resp) {
      // erro: a boca não fica presa em "pensando"
      borisRef && borisRef.current && borisRef.current.setState("idle");
      return;
    }
    const ok = falarTexto ? falarTexto(resp.texto, {
      onStart: () => borisRef && borisRef.current && borisRef.current.talk(),
      onEnd: () => borisRef && borisRef.current && borisRef.current.stop(),
    }) : false;
    if (!ok) borisRef && borisRef.current && borisRef.current.setState("idle");
  };

  const mic = () => {
    if (!stt.suportado || stt.ouvindo) return;
    stt.iniciar((texto) => { setQ(texto); enviarAgora(texto); });
  };

  return (
    <div>
      <div ref={listRef} style={{ maxHeight: "260px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px", padding: "2px", marginBottom: "10px" }}>
        {mensagens.length === 0 && (
          sugestoes && sugestoes.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "2px 0" }}>
              <div style={{ fontSize: "12.5px", color: T.textFaint }}>Pergunte ao Boris sobre esta tela:</div>
              {sugestoes.map((p, i) => (
                <button key={i} onClick={() => enviarAgora(p)} disabled={pensando}
                  style={{ textAlign: "left", padding: "9px 12px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontSize: "12.5px", fontWeight: 600 }}>
                  {p}
                </button>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: "12.5px", color: T.textFaint, padding: "6px 2px" }}>
              Pergunte qualquer coisa sobre esta tela — o Boris lembra o que vocês já conversaram aqui.
            </div>
          )
        )}
        {mensagens.map((m, i) => (
          <div key={i} style={{
            maxWidth: "88%", padding: "9px 12px", borderRadius: "14px", fontSize: "13px", lineHeight: 1.45,
            // `pre-wrap` só na fala do usuário: o que a pessoa digitou é texto
            // literal. A resposta do Boris vem em markdown e passa a ser
            // RENDERIZADA — antes caía aqui como texto cru e o `**negrito**`,
            // os `##` e as listas apareciam com os símbolos à mostra.
            whiteSpace: m.papel === "usuario" ? "pre-wrap" : "normal",
            alignSelf: m.papel === "usuario" ? "flex-end" : "flex-start",
            background: m.papel === "usuario" ? T.accentTint10 : T.bgBase,
            border: `1px solid ${m.papel === "usuario" ? T.accent : T.borderFaint}`,
            color: T.textPrimary,
            borderBottomRightRadius: m.papel === "usuario" ? "4px" : "14px",
            borderBottomLeftRadius: m.papel === "usuario" ? "14px" : "4px",
          }}>
            {/* Quem está falando, dito com todas as letras. A cor e o lado da
                bolha sozinhos não bastam: numa conversa longa, rolando, é
                fácil perder de vista de quem é a fala — e a do Boris carrega
                enquadramento educacional que a da pessoa não tem. */}
            {m.papel === "boris" && (
              <div style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "5px", fontSize: "10px", fontWeight: 800, letterSpacing: "0.05em", color: T.accent }}>
                <span aria-hidden>🦉</span> BORIS
                {m.fonte && m.fonte !== "llm" && <span style={{ color: T.textFaint, fontWeight: 600, letterSpacing: 0 }}>· da base do app</span>}
              </div>
            )}
            {m.papel === "boris" ? <Markdown text={m.texto} /> : m.texto}
            {m.papel === "boris" && m.fonte === "llm" && (
              <div style={{ marginTop: "6px", fontSize: "10px", color: T.textFaint }}>
                ⓘ Conteúdo educacional de IA · não é recomendação
                {m.restanteHojeBRL != null && (
                  <> · resta hoje ≈ R$ {Number(m.restanteHojeBRL).toFixed(2).replace(".", ",")}</>
                )}
              </div>
            )}
          </div>
        ))}
        {pensando && (
          <div style={{ alignSelf: "flex-start", color: T.textMuted, fontSize: "12.5px", padding: "4px 12px" }}>
            Boris está pensando…
          </div>
        )}
      </div>
      {erro && (
        <div style={{ marginBottom: "8px", fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
          {erro}
          <div style={{ color: T.textFaint, fontSize: "11px", marginTop: "4px" }}>Os cards da tela continuam valendo — eles não dependem da IA.</div>
        </div>
      )}
      <div style={{ display: "flex", gap: "8px", alignItems: "flex-end" }}>
        <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={1} maxLength={MAX_PERGUNTA}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarAgora(); } }}
          placeholder="Escreve pro Boris…"
          // fontSize 16px NÃO é escolha estética: abaixo disso o iOS dá zoom
          // automático ao focar o campo — e NÃO desfaz ao sair. Era isso que
          // "desconfigurava o tamanho da tela" a cada uso do chat: o app
          // ficava ampliado depois de fechar. Corrigir aqui preserva o
          // pinch-zoom do usuário, ao contrário de travar `maximum-scale` no
          // viewport, que tira a ampliação de quem precisa dela.
          style={{ flex: 1, boxSizing: "border-box", padding: "10px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "16px", resize: "vertical", minHeight: "40px" }} />
        {stt.suportado && (
          <button type="button" onClick={mic} disabled={pensando} aria-label="Falar com o Boris"
            style={{ minHeight: "40px", minWidth: "44px", borderRadius: "9px", border: `1px solid ${stt.ouvindo ? T.accent : T.borderSubtle}`, background: stt.ouvindo ? T.accentTint10 : "transparent", color: stt.ouvindo ? T.accent : T.textMuted, fontSize: "16px" }}>
            {stt.ouvindo ? "●" : "🎤"}
          </button>
        )}
        <button onClick={() => enviarAgora()} disabled={pensando || !q.trim()}
          style={{ minHeight: "40px", padding: "0 14px", borderRadius: "9px", border: "none", background: pensando || !q.trim() ? T.bgPanel : T.accentTint10, color: pensando || !q.trim() ? T.textFaint : T.accent, fontWeight: 800, fontSize: "12.5px" }}>
          Enviar
        </button>
      </div>
    </div>
  );
}
