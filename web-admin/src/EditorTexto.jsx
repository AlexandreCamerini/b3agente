/**
 * EditorTexto.jsx — editor PADRÃO de texto longo do portal admin (ADR-014).
 *
 * Todo campo de texto longo do `web-admin/` usa este componente. Campo curto
 * (número, provider, model) NÃO usa — herda só as convenções de alvo de toque
 * e fonte 16px do `inputStyle`.
 *
 * ─── CONTRATO INEGOCIÁVEL: BYTE-EXATO ──────────────────────────────────────
 * O texto que entra sai IDÊNTICO. Nada de `trim()`, normalização de aspas,
 * conversão de fim de linha, reindentação ou qualquer round-trip por AST.
 *
 * Não é preciosismo: `server/app/store.py:21` faz
 *     sha256(texto.encode()).hexdigest() in defaults.LEGACY_PROMPT_SHA256
 * para decidir se uma conta NUNCA editou o prompt (e portanto pode receber o
 * default novo numa migração) ou se aquilo é edição pessoal, intocável. Um
 * único byte alterado por "ajuda" do editor muda o hash e quebra essa decisão
 * EM SILÊNCIO — ninguém vê erro, a migração só para de acontecer.
 *
 * Por isso o editor é CodeMirror (editor de TEXTO, que só realça) e nunca um
 * WYSIWYG. E por isso a prévia é READ-ONLY: ela renderiza uma cópia, jamais
 * escreve de volta. Guardado por web/tests/test_editor_texto_byte_exato.mjs.
 *
 * O prompt também carrega bloco JSON literal (o contrato de saída que a UI
 * parseia) — indentação e aspas ali são semânticas, não formatação.
 */
import { useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { parser as mdParser } from "@lezer/markdown";
import { Language, defineLanguageFacet, HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";

// A linguagem é montada AQUI, a partir do parser do @lezer/markdown, em vez de
// usar `markdown()` do @codemirror/lang-markdown. Dois motivos, ambos medidos:
//
// 1. TAMANHO: `lang-markdown` arrasta `lang-html` + `lang-javascript` +
//    `lang-css` para colorir bloco de código EMBUTIDO no markdown — gramáticas
//    que prompt nenhum daqui usa. Custavam 194KB (74KB gzip), 35% do chunk.
// 2. COERÊNCIA COM O CONTRATO BYTE-EXATO: `markdown()` instala um keymap que
//    continua lista sozinho (Enter num item insere "- " na linha nova). É o
//    mesmo tipo de escrita-não-solicitada que fez `closeBrackets` ser desligado.
//
// Perde-se o GFM (tabela, ~riscado~, task list), que o CommonMark do parser
// base não cobre — nenhum prompt usa. Se um dia usar, o caminho é acrescentar
// a extensão GFM do @lezer/markdown, não voltar para o lang-markdown inteiro.
const mdLang = new Language(defineLanguageFacet({}), mdParser, [], "markdown");

const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";

// ─── prévia ────────────────────────────────────────────────────────────────
// Renderizador MÍNIMO, afinado para FONTE DE PROMPT — deliberadamente diferente
// do `web/src/markdown.jsx`, que serve à SAÍDA da LLM e por isso dá trim,
// desescapa \n literais, remove cercas e extrai `corpo` de JSON. Tudo isso
// mentiria sobre o conteúdo de um prompt. Aqui: só realce estrutural, e bloco
// de código/JSON preservado como está.
function Inline({ text, T }) {
  const out = [];
  let rest = String(text ?? "");
  let key = 0, guard = 0;
  const re = /(\*\*([^*]+)\*\*|`([^`]+)`)/;
  while (guard++ < 400) {
    const m = re.exec(rest);
    if (!m) { if (rest) out.push(rest); break; }
    if (m.index > 0) out.push(rest.slice(0, m.index));
    if (m[2] != null) out.push(<strong key={key++}>{m[2]}</strong>);
    else out.push(
      <code key={key++} style={{ fontFamily: MONO, fontSize: "0.92em", background: "rgba(255,255,255,0.07)", padding: "0 4px", borderRadius: "4px" }}>{m[3]}</code>
    );
    rest = rest.slice(m.index + m[0].length);
  }
  return <>{out}</>;
}

export function PreviaMarkdown({ texto, T }) {
  const linhas = String(texto ?? "").split("\n");
  const blocos = [];
  let para = [], code = null;
  const fechaPara = () => { if (para.length) { blocos.push({ t: "p", linhas: para }); para = []; } };
  const fechaCode = () => { if (code) { blocos.push({ t: "code", linhas: code }); code = null; } };

  for (const linha of linhas) {
    // Bloco LITERAL = cerca ``` ou estrutura JSON (o contrato de saída que a UI
    // parseia). Indentação sozinha NÃO conta: os prompts quebram item de lista
    // com recuo de continuação, e tratar isso como código engolia o texto
    // inteiro num <pre> — defeito visto ao vivo, não hipotético.
    const ehJson = /^\s*[[\]{}]\s*,?\s*$/.test(linha) || /^\s*"[^"]+"\s*:/.test(linha);
    if (code !== null) {
      // sai do bloco na cerca de fechamento, ou quando a estrutura acaba
      if (/^\s*```/.test(linha)) { fechaCode(); continue; }
      if (!ehJson && linha.trim() && !/^\s+/.test(linha)) { fechaCode(); }
      else { code.push(linha); continue; }
    }
    if (/^\s*```/.test(linha)) { fechaPara(); code = []; continue; }
    if (ehJson) { fechaPara(); code = [linha]; continue; }
    if (!linha.trim()) { fechaPara(); continue; }

    const h = /^(#{1,4})\s*(.+)$/.exec(linha);
    if (h) { fechaPara(); blocos.push({ t: "h", nivel: h[1].length, texto: h[2] }); continue; }
    const bul = /^\s*[-*•]\s+(.*)$/.exec(linha);
    if (bul) { fechaPara(); blocos.push({ t: "li", texto: bul[1] }); continue; }

    // Continuação: linha recuada logo depois de um item de lista pertence a ele.
    const ultimo = blocos[blocos.length - 1];
    if (/^\s+/.test(linha) && !para.length && ultimo && ultimo.t === "li") {
      ultimo.texto += " " + linha.trim();
      continue;
    }
    para.push(linha);
  }
  fechaPara(); fechaCode();

  return (
    <div style={{ display: "grid", gap: "8px", padding: "12px 2px" }}>
      {blocos.map((b, i) => {
        if (b.t === "h") {
          return (
            <div key={i} style={{ fontSize: b.nivel <= 1 ? "15px" : "13.5px", fontWeight: 800, color: T.accent, marginTop: i ? "6px" : 0 }}>
              <Inline text={b.texto} T={T} />
            </div>
          );
        }
        if (b.t === "li") {
          return (
            <div key={i} style={{ display: "flex", gap: "8px", fontSize: "13px", lineHeight: 1.55, color: T.muted }}>
              <span style={{ color: T.accent, flex: "none" }}>•</span>
              <span><Inline text={b.texto} T={T} /></span>
            </div>
          );
        }
        if (b.t === "code") {
          return (
            <pre key={i} style={{ margin: 0, padding: "10px 12px", borderRadius: "8px", background: T.bg, border: `1px solid ${T.borderFaint}`, fontFamily: MONO, fontSize: "11.5px", lineHeight: 1.5, color: T.text, overflowX: "auto" }}>
              {b.linhas.join("\n")}
            </pre>
          );
        }
        return (
          <p key={i} style={{ margin: 0, fontSize: "13px", lineHeight: 1.6, color: T.text }}>
            {b.linhas.map((l, j) => <span key={j}>{j > 0 && <br />}<Inline text={l} T={T} /></span>)}
          </p>
        );
      })}
    </div>
  );
}

// ─── editor ────────────────────────────────────────────────────────────────
// Tema do CodeMirror derivado dos tokens `T` do portal (dark-only, Brand Book
// v2) — nada de importar um tema pronto e ter duas paletas na mesma tela.
const temaDe = (T, largo) => EditorView.theme({
  "&": { backgroundColor: T.bg, color: T.text, fontSize: largo ? "12px" : "16px", borderRadius: "8px", border: `1px solid ${T.border}` },
  ".cm-content": { fontFamily: MONO, caretColor: T.accent, padding: "10px 0" },
  ".cm-gutters": { backgroundColor: T.bg, color: T.faint, border: "none" },
  ".cm-activeLine": { backgroundColor: "rgba(255,255,255,0.03)" },
  ".cm-activeLineGutter": { backgroundColor: "transparent", color: T.muted },
  "&.cm-focused": { outline: `2px solid ${T.accent}`, outlineOffset: "1px" },
  ".cm-selectionBackground, &.cm-focused .cm-selectionBackground, ::selection": { backgroundColor: "rgba(212,175,55,0.25)" },
  ".cm-scroller": { lineHeight: 1.5 },
}, { dark: true });

// Realce da SINTAXE markdown, nos tokens do portal. Sem isto o CodeMirror
// renderiza tudo na mesma cor e não haveria ganho nenhum sobre um <textarea>.
const realceDe = (T) => syntaxHighlighting(HighlightStyle.define([
  { tag: tags.heading, color: T.accent, fontWeight: "800" },
  { tag: tags.strong, color: T.text, fontWeight: "800" },
  { tag: tags.emphasis, color: T.text, fontStyle: "italic" },
  { tag: tags.monospace, color: T.positive },              // `código` inline
  { tag: tags.list, color: T.accent },
  { tag: tags.link, color: T.positive },
  { tag: tags.quote, color: T.muted, fontStyle: "italic" },
  { tag: tags.processingInstruction, color: T.faint },     // os próprios #, -, `
]));

/**
 * @param {string}   valor       texto atual (fonte da verdade)
 * @param {Function} onChange    recebe o texto CRU, sem transformação nenhuma
 * @param {object}   T           tokens de tema do portal
 * @param {boolean}  largo       true = desktop (vem do useMediaQuery(LARGO))
 * @param {string}   titulo      cabeçalho do modo tela cheia
 * @param {Function} onFechar    cancelar
 * @param {node}     acoes       botões de confirmação (Publicar/Salvar)
 */
export function EditorTexto({ valor, onChange, T, largo, titulo, onFechar, acoes }) {
  const [aba, setAba] = useState("editar");

  const abaBtn = (id, rotulo) => (
    <button onClick={() => setAba(id)}
            style={{ padding: largo ? "7px 12px" : "11px 16px", borderRadius: "8px", border: "none", cursor: "pointer",
                     background: aba === id ? T.accent : "transparent", color: aba === id ? T.onAccent : T.muted,
                     fontFamily: "inherit", fontSize: "12.5px", fontWeight: 700 }}>
      {rotulo}
    </button>
  );

  const corpo = (
    <>
      <div style={{ display: "flex", gap: "6px", marginBottom: "8px" }}>
        {abaBtn("editar", "Editar")}
        {abaBtn("previa", "Prévia")}
        {!largo && (
          <span style={{ marginLeft: "auto", alignSelf: "center", fontSize: "10.5px", color: T.faint }}>
            {String(valor ?? "").length} chars
          </span>
        )}
      </div>
      {/* no mobile este wrapper é quem estica: flex:1 + minHeight:0 (sem o
          minHeight um filho rolável nunca encolhe dentro de um flex column) */}
      <div style={largo ? undefined : { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      {aba === "editar" ? (
        <CodeMirror
          value={valor}
          // `v` é o texto cru do documento — nada entre isto e o estado.
          onChange={(v) => onChange(v)}
          height={largo ? "340px" : "100%"}
          // O tema vai pela PROP, não em `extensions`: o @uiw aplica o tema
          // light padrão dele DEPOIS das extensions e vencia o nosso — o editor
          // saía com fundo branco e texto claro, ilegível (visto ao vivo).
          theme={temaDe(T, largo)}
          extensions={[mdLang, EditorView.lineWrapping, realceDe(T)]}
          basicSetup={{
            lineNumbers: largo,          // no celular, número de linha só rouba largura
            foldGutter: false,
            highlightActiveLine: true,
            autocompletion: false,       // prompt não tem vocabulário a completar
            // Fechar colchete/aspas sozinho INSERE byte que o admin não digitou
            // — no meio de um contrato JSON literal isso corrompe o prompt.
            closeBrackets: false,
            bracketMatching: true,
          }}
          style={{ height: largo ? "auto" : "100%", overflow: "hidden", borderRadius: "8px" }}
        />
      ) : (
        <div style={{ border: `1px solid ${T.border}`, borderRadius: "8px", background: T.bg, padding: "0 12px", height: largo ? "340px" : "100%", overflowY: "auto" }}>
          <PreviaMarkdown texto={valor} T={T} />
        </div>
      )}
      </div>
    </>
  );

  // Desktop: inline no card, como sempre foi.
  if (largo) {
    return (
      <div style={{ marginTop: "8px" }}>
        {corpo}
        <div style={{ display: "flex", gap: "8px", marginTop: "8px", flexWrap: "wrap" }}>{acoes}</div>
      </div>
    );
  }

  // Mobile: TELA CHEIA. O editor embutido no card dava 152px visíveis para um
  // prompt de ~1200px (medido) — 8 telas de rolagem DENTRO de uma página que
  // também rolava. Aqui o texto ganha a viewport e as ações ficam fixas.
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 50, background: T.bg,
      display: "flex", flexDirection: "column", padding: "12px 16px",
      // O browser in-app do iOS desenha a própria barra embaixo; sem isto os
      // botões de ação ficam atrás dela.
      paddingBottom: "calc(12px + env(safe-area-inset-bottom))",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
        <div style={{ flex: 1, minWidth: 0, fontSize: "13px", fontWeight: 700, color: T.text, overflowWrap: "anywhere" }}>{titulo}</div>
        <button onClick={onFechar}
                style={{ flex: "0 0 auto", minHeight: "44px", padding: "0 14px", borderRadius: "8px", border: `1px solid ${T.border}`,
                         background: "transparent", color: T.muted, fontFamily: "inherit", fontSize: "12px", cursor: "pointer" }}>
          Fechar
        </button>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>{corpo}</div>
      <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>{acoes}</div>
    </div>
  );
}
