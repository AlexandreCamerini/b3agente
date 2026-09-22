/**
 * ExplicacaoPayoff.jsx — Fase 37 (37-02), camada explicativa determinística
 * do payoff (EXPL-01/02/03, D-06/D-07 do 37-CONTEXT.md).
 *
 * Componente puro: zero `fetch`, zero `useEffect`, zero `useState`, zero
 * I/O. Descreve TODOS os segmentos de `segmentos_da_curva()` (Fase 36) em
 * português leigo — o segmento onde o spot está primeiro, os demais na
 * ordem espacial esquerda→direita restante — sem nunca usar o vocabulário
 * técnico banido (strike, prêmio, delta, theta, volatilidade implícita,
 * exercício, rolagem, ITM/OTM/ATM, "perna"; ver EXPL-02, guardião estático
 * em `web/tests/test_explicacao_payoff.mjs`).
 *
 * Ainda NÃO conectado a nenhuma tela real — a conexão é o Plano 37-05
 * (wave 3, `37-02-PLAN.md`). Este plano entrega o componente e o
 * vocabulário, testável isoladamente por `montarTexto` (exportado à parte
 * para não exigir DOM/render no guardião).
 *
 * `formatarRazao()` é importada de `uiOpcoes.jsx` e nunca reformatada aqui
 * — é a mitigação estrutural de T-37-04/EXPL-03 (razão G/P divergente entre
 * `RazaoGanhoPerda` e este componente).
 */
import { Kicker, Aviso, formatarRazao } from "./uiOpcoes.jsx";

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");

// Localiza o índice do segmento cujo intervalo [de, ate] contém `spot` — ou,
// para a cauda (`ate === null`), cujo `spot >= de`. Retorna -1 se `spot` não
// é número ou não cai em nenhum segmento (segmentos malformados/vazios).
function encontrarIndiceDoSpot(segmentos, spot) {
  if (!ehNum(spot)) return -1;
  for (let i = 0; i < segmentos.length; i++) {
    const seg = segmentos[i];
    if (!seg) continue;
    if (seg.ate === null) {
      if (spot >= seg.de) return i;
    } else if (spot >= seg.de && spot <= seg.ate) {
      return i;
    }
  }
  return -1;
}

// Escolhe a chave de copy certa para um segmento, dado o prefixo
// ("Spot"/"Outro") — mesma árvore de decisão para as duas famílias de
// template, só o conjunto de chaves muda. Prioridade: platô > direção;
// dentro de cada um, cauda (ate: null) > finito. A cauda com inclinação
// "positiva"/"negativa" NUNCA usa o template finito (D-06/D-07, regra
// explícita do plano) — e como platô/direção são mutuamente exclusivos por
// contrato de `segmentos_da_curva()` (inclinacao "zero" <-> ePlato), a
// mesma árvore serve para os dois prefixos sem ramificação extra.
function escolherTemplate(seg, prefixo, cp) {
  const c = cp || {};
  const tail = seg.ate === null;
  if (seg.ePlato) {
    const chaveCaudaPlato = "opcoesExplic" + prefixo + "CaudaPlato";
    if (tail && c[chaveCaudaPlato]) return c[chaveCaudaPlato];
    return c["opcoesExplic" + prefixo + "Plato"];
  }
  if (seg.inclinacao === "positiva") {
    return tail ? c["opcoesExplic" + prefixo + "CaudaGanho"] : c["opcoesExplic" + prefixo + "Positiva"];
  }
  // "negativa" (única alternativa restante para um segmento não-plato)
  return tail ? c["opcoesExplic" + prefixo + "CaudaPerda"] : c["opcoesExplic" + prefixo + "Negativa"];
}

function interpolar(template, seg, spot) {
  if (!template) return "";
  return template
    .replace(/\{spot\}/g, fmt(spot))
    .replace(/\{de\}/g, fmt(seg.de))
    .replace(/\{ate\}/g, fmt(seg.ate));
}

// Função pura, testável isoladamente (sem DOM/render) — monta o texto
// completo: frase do segmento do spot primeiro, depois as demais na ordem
// original (pulando o índice do spot), e por último — só quando a razão tem
// valor numérico — a citação da razão G/P via `formatarRazao()` (nunca
// reformatada aqui, D-05/EXPL-03).
export function montarTexto(segmentos, spot, razao, cp) {
  if (!Array.isArray(segmentos) || segmentos.length === 0) return "";
  const c = cp || {};
  const idxSpot = encontrarIndiceDoSpot(segmentos, spot);
  const linhas = [];

  if (idxSpot >= 0) {
    const seg = segmentos[idxSpot];
    const template = escolherTemplate(seg, "Spot", c);
    linhas.push(interpolar(template, seg, spot));
  }

  segmentos.forEach((seg, i) => {
    if (i === idxSpot || !seg) return;
    const template = escolherTemplate(seg, "Outro", c);
    linhas.push(interpolar(template, seg, spot));
  });

  if (ehNum(razao && razao.valor)) {
    linhas.push(formatarRazao(razao));
  }

  return linhas.filter(Boolean).join("\n");
}

export default function ExplicacaoPayoff({ segmentos, spot, razao, cp }) {
  if (!Array.isArray(segmentos) || segmentos.length === 0) return null;
  const c = cp || {};
  const texto = montarTexto(segmentos, spot, razao, c);
  if (!texto) return null;
  return (
    <>
      <Kicker>{c.opcoesComoLerTitulo || "Como ler esta estrutura"}</Kicker>
      <Aviso>{texto}</Aviso>
    </>
  );
}
