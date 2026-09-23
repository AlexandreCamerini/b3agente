/**
 * glossario.js — Fase 38 (38-03): ponte entre as duas fontes didáticas
 * determinísticas — a explicação ANCORADA nos números do card
 * (`conceitos.py`, via `POST /api/conceito/{cid}`) e o glossário GENÉRICO da
 * KB (`kb.py`, via o catálogo de 38-01, `GET /api/kb/catalogo`).
 *
 * Módulo PURO: zero import de React, App.jsx ou persistence.js — importável
 * por App.jsx, entendimento.jsx e opcoes/OpcoesScreen.jsx sem criar ciclo
 * (mesmo isolamento do ADR-027 que entendimento.jsx já respeita).
 *
 * O 38-04 estende este mesmo arquivo com os filtros de busca da KB.
 */

// Catálogo válido: objeto com as duas listas do formato de
// GET /api/kb/catalogo (38-01) — `familias`/`verbetes`, sempre arrays.
// Qualquer forma inesperada (undefined, {}, resposta parcial) é inválida —
// nunca renderizar lista parcial/inventada (princípio 4 do CLAUDE.md).
export function catalogoKbValido(r) {
  return !!r && typeof r === "object" && Array.isArray(r.verbetes) && Array.isArray(r.familias);
}

// Verbete do catálogo pelo id: null quando o catálogo não é válido, o id não
// existe, ou o verbete não tem `texto` (nunca renderizar corpo vazio — o
// backend já exclui verbete de texto vazio do catálogo, isto é defesa em
// profundidade do lado do cliente).
export function verbeteDoCatalogo(cat, vid) {
  if (!catalogoKbValido(cat)) return null;
  const v = cat.verbetes.find((x) => x && x.id === vid);
  if (!v || typeof v.texto !== "string" || !v.texto) return null;
  return v;
}
