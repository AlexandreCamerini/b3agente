/**
 * markdown.jsx — renderizador de markdown SEGURO, compartilhado.
 *
 * Vivia dentro de `App.jsx`, o que deixava o chat do Boris de fora: ele não
 * pode importar de `App.jsx` (import circular — `App.jsx` importa o chat), e
 * por isso renderizava a resposta da IA como texto cru, com `**negrito**` e
 * `##` aparecendo literais na bolha.
 *
 * Sem HTML cru (XSS-safe): tudo vira nó React. Os tokens de cor chegam por
 * variável CSS — mesmo truque de `pet/BorisChat.jsx` —, então o módulo não
 * depende de `T` de `App.jsx` e serve aos dois.
 */
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textPrimary", "textSecondary", "accent"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";

// Renderizador de markdown SEGURO (subconjunto), em React puro — sem HTML cru,
// compatível com mobile. Suporta ## títulos, **negrito**, *itálico*, `código`,
// listas (- / *), listas numeradas e parágrafos.
export function MdInline({ text }) {
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
export function Markdown({ text }) {
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
