/**
 * TermoOpcoes.jsx — Fase 48 (48-08): termo clicável inline (UI-SPEC "Termos
 * clicáveis"). Mesma técnica do app: SUBLINHADO (convenção única, importada),
 * toque simples + botão sr-only "O que é X?". Termo sem registro vira texto
 * comum — nunca sublinhado órfão.
 */
import { SUBLINHADO } from "../entendimento.jsx";
import { verbeteDoCatalogo } from "../glossario.js";
import { SR_ONLY, FOCO } from "./fluxoEstilo.js";

// PURA. Marca só a PRIMEIRA ocorrência de cada `termo.rotulo` (case-sensitive).
// Ocorrências sobrepostas: a que começa antes vence; a outra é descartada.
export function marcarTermos(texto, termos) {
  if (typeof texto !== "string") return [];
  const lista = Array.isArray(termos) ? termos : [];
  const achados = [];
  for (const termo of lista) {
    if (!termo || typeof termo.rotulo !== "string" || !termo.rotulo) continue;
    const i = texto.indexOf(termo.rotulo);
    if (i < 0) continue;
    achados.push({ ini: i, fim: i + termo.rotulo.length, termo });
  }
  achados.sort((a, b) => a.ini - b.ini);
  const segs = [];
  let cursor = 0;
  for (const a of achados) {
    if (a.ini < cursor) continue;
    if (a.ini > cursor) segs.push({ texto: texto.slice(cursor, a.ini), termo: null });
    segs.push({ texto: texto.slice(a.ini, a.fim), termo: a.termo });
    cursor = a.fim;
  }
  if (cursor < texto.length) segs.push({ texto: texto.slice(cursor), termo: null });
  if (!segs.length && texto) segs.push({ texto, termo: null });
  return segs;
}

const teclaAtiva = (e, fn) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); fn(); }
};

export default function TermoOpcoes({ texto, termos, A, didatica, kbCatalogo, dados, onAbrirVerbete }) {
  const segs = marcarTermos(texto, termos);
  return (
    <>
      {segs.map((s, i) => {
        const t = s.termo;
        if (!t) return <span key={i}>{s.texto}</span>;

        // (a) setor da camada didática
        const cid = t.setor && didatica && didatica.ligada && didatica.setores ? didatica.setores[t.setor] : null;
        if (cid && A) {
          const abrir = (origem) => A.abrirSetor(t.setor, cid, (dados && dados[t.setor]) || dados, origem);
          return (
            <span key={i} style={{ position: "relative" }}>
              <span role="button" tabIndex={0}
                style={{ ...SUBLINHADO, cursor: "pointer" }}
                onClick={(e) => { e.stopPropagation(); abrir("toque"); }}
                onKeyDown={(e) => teclaAtiva(e, () => abrir("toque"))}
                onFocus={(e) => Object.assign(e.currentTarget.style, FOCO)}
                onBlur={(e) => { e.currentTarget.style.outline = "none"; }}>
                {s.texto}
              </span>
              <button type="button" aria-label={"O que é " + t.rotulo + "?"} style={SR_ONLY}
                onClick={(e) => { e.stopPropagation(); abrir("botao"); }}>?</button>
            </span>
          );
        }

        // (b) verbete KB (só com a camada ligada e o verbete no catálogo)
        if (t.kb && didatica && didatica.ligada && typeof onAbrirVerbete === "function"
          && verbeteDoCatalogo(kbCatalogo, t.kb)) {
          const abrir = () => onAbrirVerbete(t.kb);
          return (
            <span key={i} style={{ position: "relative" }}>
              <span role="button" tabIndex={0}
                style={{ ...SUBLINHADO, cursor: "pointer" }}
                onClick={(e) => { e.stopPropagation(); abrir(); }}
                onKeyDown={(e) => teclaAtiva(e, abrir)}
                onFocus={(e) => Object.assign(e.currentTarget.style, FOCO)}
                onBlur={(e) => { e.currentTarget.style.outline = "none"; }}>
                {s.texto}
              </span>
              <button type="button" aria-label={"O que é " + t.rotulo + "?"} style={SR_ONLY}
                onClick={(e) => { e.stopPropagation(); abrir(); }}>?</button>
            </span>
          );
        }

        // (c) sem registro: texto comum
        return <span key={i}>{s.texto}</span>;
      })}
    </>
  );
}
