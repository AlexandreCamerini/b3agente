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

// ============================================================ Fase 38 (38-04)
// Filtros puros da tela de Glossário (KB-01). Três decisões declaradas no
// PLAN.md, não silenciosas:
//
// 1) SUBSTRING normalizada (não fronteira de palavra). `kb.buscar()` no
//    backend (server/app/kb.py) usa fronteira de palavra — D-02 trava ESSA
//    função, porque é consumida pelo assistente (`resolver()`). Esta tela
//    NUNCA chama `kb.buscar()`; é busca LIVE client-side, e quem digita "rs"
//    esperando achar RSI durante a digitação precisa de casamento por
//    prefixo, que fronteira de palavra não dá.
// 2) SEM LIMITE de resultados (D-03). O `limite=5` de `kb.buscar()` existe
//    para responder 1 pergunta do assistente — não é o contrato desta tela
//    de navegação, que mostra todos os que baterem.
// 3) A fórmula de pontuação do assistente (`kb._pontuar`, privada) NÃO é
//    replicada aqui de propósito (Don't Hand-Roll do RESEARCH da fase): duas
//    implementações da mesma pontuação divergiriam com o tempo. O posto
//    abaixo (0/1/2) é deliberadamente mais simples — título-prefixo >
//    título-contém > termo/id — e serve só para ordenar a lista visível.

// Minúsculas, sem acento, sem espaço nas pontas. Mesma normalização NFD de
// `kb._normalizar` (server/app/kb.py) reescrita em JS — front e backend
// concordam sobre acento/caixa sem compartilhar código entre as duas runtimes.
export function normalizarBusca(s) {
  return String(s ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

// Filtra `verbetes` (formato de GET /api/kb/catalogo) pelo `termo` digitado.
// Termo vazio/só-espaço devolve lista vazia (a tela mostra o acordeão de
// famílias nesse caso, não uma lista). T-38-14: só `String.prototype.
// includes/startsWith` — NENHUMA `RegExp` construída a partir do input, para
// que caractere especial digitado (`(`, `[`, `*`, `\`) nunca vire ReDoS ou
// exceção. Sem `slice`/limite de tamanho (D-03).
export function filtrarVerbetes(verbetes, termo) {
  const q = normalizarBusca(termo);
  if (!q) return [];
  const lista = Array.isArray(verbetes) ? verbetes : [];
  const casados = [];
  lista.forEach((v, idx) => {
    if (!v) return;
    const titulo = normalizarBusca(v.titulo);
    let posto;
    if (titulo.startsWith(q)) posto = 0;
    else if (titulo.includes(q)) posto = 1;
    else {
      const termos = Array.isArray(v.termos) ? v.termos : [];
      const bateTermo = termos.some((t) => normalizarBusca(t).includes(q));
      const bateId = normalizarBusca(v.id).includes(q);
      if (bateTermo || bateId) posto = 2;
    }
    if (posto === undefined) return;
    casados.push({ v, posto, idx });
  });
  // Ordenação ESTÁVEL: posto crescente, empate mantém a ordem original do
  // catálogo (o índice de descoberta serve de desempate explícito — não
  // depender da estabilidade de Array.prototype.sort do motor JS).
  casados.sort((a, b) => (a.posto - b.posto) || (a.idx - b.idx));
  return casados.map((c) => c.v);
}

// Agrupa `verbetes` pelas `familias` (formato [{id, rotulo}] do catálogo),
// na ORDEM de `familias` — não na ordem de descoberta dos verbetes. Só
// devolve família com pelo menos 1 verbete (família vazia não aparece como
// seção fantasma no acordeão). Verbete cuja `familia` não bate com nenhum id
// de `familias` simplesmente não entra em grupo nenhum — não é erro, é dado
// que a tela de navegação por família não sabe onde encaixar.
export function agruparPorFamilia(verbetes, familias) {
  const lista = Array.isArray(verbetes) ? verbetes : [];
  const fams = Array.isArray(familias) ? familias : [];
  return fams
    .map((f) => ({ id: f.id, rotulo: f.rotulo, verbetes: lista.filter((v) => v && v.familia === f.id) }))
    .filter((g) => g.verbetes.length > 0);
}
