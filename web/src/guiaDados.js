// Dados do guia das telas: parse do arquivo-fonte único + validação de conteúdo
// (quick 261011-l5x). Puro: sem Vite, sem DOM — roda no Node dos testes e no bundle.
//
// A fonte única editável é site/js/telas-data.js (contrato: comentário de cabeçalho +
// `window.TELAS = <array JSON puro>;`). O site a executa como script; o app a importa
// com ?raw e passa o texto por parseTelasData. Nenhum passo de geração.

export function parseTelasData(texto) {
  const s = String(texto || "");
  const ancora = s.indexOf("window.TELAS =");
  if (ancora < 0) throw new Error("telas-data.js fora do contrato: falta `window.TELAS =`.");
  const ini = s.indexOf("[", ancora);
  const fim = s.lastIndexOf("]");
  if (ini < 0 || fim < ini) throw new Error("telas-data.js fora do contrato: array JSON não encontrado.");
  try {
    return JSON.parse(s.slice(ini, fim + 1));
  } catch (e) {
    throw new Error("telas-data.js fora do contrato: o array não é JSON puro (" + e.message + ").");
  }
}

// Stopwords (já sem acento) da métrica de sobreposição. Lista fixada pelo plano 261011-l5x.
export const STOPWORDS = new Set((
  "para com como pelo pela pelos pelas mais menos quando onde aqui isso esse essa este esta estes estas esses essas " +
  "aquele aquela entre sobre ainda tambem mesmo mesma cada todo toda todos todas outro outra seus suas voce tela " +
  "pode podem fica ficam esta estao sera sendo antes depois sempre nunca nada muito pouco qual quais porque entao " +
  "desde uma umas dos das nos nas num numa ser ter tem vai vao"
).split(/\s+/));

// Calibração (planner, 2026-10-11): 4.465 pares dos 95 textos antigos; os duplicados
// nomeados pontuavam 0,74 / 0,56 / 0,47 / 0,46 / 0,38 / 0,33; o maior par legítimo, 0,29.
// 0,35 barra os 5 primeiros e fica acima do legítimo. O par 0,33 sai pelo corte de
// conteúdo (ponto fundido), não pelo limiar. Não afrouxar durante a escrita; mudar
// exige nova medição registrada.
export const LIMIAR_SOBREPOSICAO = 0.35;

function tokens(s) {
  const base = String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const t = new Set();
  for (const w of base.split(/[^a-z0-9]+/)) {
    if (w.length >= 4 && !STOPWORDS.has(w)) t.add(w);
  }
  return t;
}

// Jaccard |A∩B| / |A∪B| sobre os tokens; 0 se a união for vazia.
export function sobreposicao(a, b) {
  const A = tokens(a), B = tokens(b);
  let inter = 0;
  for (const w of A) if (B.has(w)) inter++;
  const uniao = A.size + B.size - inter;
  return uniao === 0 ? 0 : inter / uniao;
}

export const NAV_PURA = ["Voltar", "Confirmar ou cancelar", "Editar e atualizar", "Perfil e ajustes", "Entrar na mesa",
  "Escolher este", "Abrir o card", "Continuar ou ativar", "Conversar agora ou depois", "Busca por ticker",
  "As cinco abas", "Seu nome"];
export const UNICOS = ["Operador IA", "Card do ativo", "Termos sublinhados", "Criar vigia"];
export const RE_AVISO = /recomendação de investimento|conteúdo educacional|nada aqui é|dinheiro (virtual|simulado|fictício)/i;
export const RE_PROMESSA = /garant|certeza|lucro certo|enriqu/i;
export const RE_FRACAO_EXEMPLO = /\b\d+\s+de\s+\d+\b/;

// Devolve a lista de violações (vazia = guia ok). `orcamento` = {id: máx. de pontos}.
// `existeImg(img)` é opcional (o teste passa fs.existsSync).
export function validarGuia(telas, orcamento = {}, existeImg = null) {
  const v = [];
  if (!Array.isArray(telas) || !telas.length) return ["guia vazio"];
  let total = 0;
  const textos = []; // {id, rot, texto}
  for (const t of telas) {
    const id = t && t.id;
    if (!id) { v.push("tela sem id"); continue; }
    if ("guard" in t) v.push(id + ": campo guard não pode existir (aviso é rodapé único)");
    if ("can" in t) v.push(id + ": campo can foi renomeado para pontos");
    const pontos = Array.isArray(t.pontos) ? t.pontos : [];
    if (!pontos.length) v.push(id + ": sem pontos");
    if (orcamento[id] != null && pontos.length > orcamento[id]) v.push(id + ": " + pontos.length + " pontos > orçamento " + orcamento[id]);
    total += pontos.length;
    if (typeof t.missao !== "string" || !t.missao.trim()) v.push(id + ": missao deve ser uma string");
    else textos.push({ id, rot: id + ":missão", texto: t.missao });
    const q = t.quiz;
    if (!q || !Array.isArray(q.o) || typeof q.a !== "number" || !q.o[q.a] || !q.why) v.push(id + ": quiz inválido (quiz.a deve apontar para quiz.o)");
    // visao (2026-10-12, quick 261012-09v): cartão "Visão geral" do guia aberto pelo Bóris.
    if (typeof t.visao !== "string" || !t.visao.trim()) v.push(id + ": visao deve ser uma string não vazia");
    else {
      const vr = id + ":visão";
      if (t.visao.length > 220) v.push(vr + ": visao > 220 caracteres");
      if (RE_AVISO.test(t.visao)) v.push(vr + ": aviso legal dentro da visão");
      if (RE_PROMESSA.test(t.visao)) v.push(vr + ": linguagem de promessa na visão");
      if (RE_FRACAO_EXEMPLO.test(t.visao)) v.push(vr + ": fração 'N de M' de exemplo na visão");
      // Compara só com os pontos da MESMA tela (não com outras telas nem com a missão).
      for (const p of pontos) {
        const sv = sobreposicao(t.visao, p.texto);
        if (sv >= LIMIAR_SOBREPOSICAO) v.push("sobreposição " + sv.toFixed(2) + " entre " + vr + " e " + id + ":" + p.titulo);
      }
    }
    if (existeImg && !existeImg(t.img)) v.push(id + ": imagem inexistente " + t.img);
    for (const p of pontos) {
      const rot = id + ":" + p.titulo;
      if (NAV_PURA.includes(p.titulo)) v.push(rot + ": ponto de navegação pura");
      if (typeof p.texto !== "string" || p.texto.length > 240) v.push(rot + ": texto > 240 caracteres");
      if (typeof p.titulo !== "string" || p.titulo.length > 40) v.push(rot + ": título > 40 caracteres");
      if (RE_AVISO.test(p.texto) || RE_AVISO.test(p.titulo)) v.push(rot + ": aviso legal dentro do ponto");
      if (RE_PROMESSA.test(p.texto)) v.push(rot + ": linguagem de promessa");
      if (RE_FRACAO_EXEMPLO.test(p.texto)) v.push(rot + ": fração 'N de M' de exemplo");
      for (const k of ["x", "y"]) if (!(p[k] >= 0 && p[k] <= 100)) v.push(rot + ": " + k + " fora de 0..100");
      textos.push({ id, rot, texto: p.texto });
    }
  }
  // 2026-10-12 (quick 261012-09v): teto 60 -> 65 (telas modos e opia + 1 ponto em opc; soma real 64).
  if (total < 50 || total > 65) v.push("total de pontos " + total + " fora de 50..65");
  for (const nome of UNICOS) {
    const n = telas.reduce((s, t) => s + (t.pontos || []).filter((p) => p.titulo === nome).length, 0);
    if (n > 1) v.push("título '" + nome + "' aparece em " + n + " pontos (máx. 1)");
  }
  // Sobreposição: todo par de textos de ponto do guia (qualquer tela) + a missão contra os textos da MESMA tela.
  for (let i = 0; i < textos.length; i++) {
    for (let j = i + 1; j < textos.length; j++) {
      const a = textos[i], b = textos[j];
      if ((a.rot.endsWith(":missão") || b.rot.endsWith(":missão")) && a.id !== b.id) continue;
      const s = sobreposicao(a.texto, b.texto);
      if (s >= LIMIAR_SOBREPOSICAO) v.push("sobreposição " + s.toFixed(2) + " entre " + textos[i].rot + " e " + textos[j].rot);
    }
  }
  return v;
}
