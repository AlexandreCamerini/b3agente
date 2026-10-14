// Quick 261013-vai (2026-10-14), D4 — Guardião do bloqueio visual das ordens de opção com o
// pregão CONFIRMADO fechado (leitura de fonte, sem build).
//
// Contrato: OpcoesScreen deriva `bloqueioMercado` de `mercadoAberto === false` (nunca de
// null/erro: o servidor é a autoridade e responde 409) a partir de copy.js e repassa a cada
// componente de execução. Cada um inclui a prop na trava do botão, mostra o motivo com `id` e
// liga o botão por `aria-describedby`. Nenhum `disabled=` NOVO (contagem por arquivo igual à de
// antes da quick, medida em 2026-10-14). Stop/alvo/plano nunca referenciam o bloqueio.
//
// Roda sem build: `node web/tests/test_opcoes_mercado_fechado_ui.mjs`.

import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const dir = join(here, "..", "src", "opcoes");
const ler = (n) => readFileSync(join(dir, n), "utf8");
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const semComentarios = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

const tela = ler("OpcoesScreen.jsx");

// ---- OpcoesScreen -----------------------------------------------------------
ok("OpcoesScreen deriva bloqueioMercado só de mercadoAberto === false",
  /const bloqueioMercado = mercadoAberto === false\s*\?/.test(tela));
ok("OpcoesScreen usa botao_bloqueado com abertura e botao_bloqueado_sem_hora sem ela (nunca '?')",
  /ctx\.mercado\.abertura\s*\?\s*execucaoForaPregaoTxt\(mode, "botao_bloqueado", \{ abertura: ctx\.mercado\.abertura \}\)\s*:\s*execucaoForaPregaoTxt\(mode, "botao_bloqueado_sem_hora"\)/.test(tela));
const montagens = {
  PernasAbertas: 2, ConfirmarEstrutura: 1, SecaoAnalisar: 1, PropostaDoAtivo: 1, CandidatoOpcao: 1, PropostaLastreada: 1,
};
for (const [comp, n] of Object.entries(montagens)) {
  const re = new RegExp("<" + comp + "\\s+bloqueioMercado=\\{bloqueioMercado\\}", "g");
  ok(`OpcoesScreen passa bloqueioMercado a <${comp}> (${n}x)`, (tela.match(re) || []).length === n);
}
ok("PropostaDoAtivo recebe a prop na assinatura", /function PropostaDoAtivo\(\{[^}]*bloqueioMercado[^}]*\}\)/.test(tela));

// ---- Repasse ----------------------------------------------------------------
ok("SecaoAnalisar repassa a ExecutarProposta", /<ExecutarProposta[\s\S]{0,300}bloqueioMercado=\{bloqueioMercado\}/.test(ler("SecaoAnalisar.jsx")));
ok("AbaRecomendadas repassa a CuradoriaEstruturas", /<CuradoriaEstruturas[\s\S]{0,900}bloqueioMercado=\{bloqueioMercado\}/.test(ler("AbaRecomendadas.jsx")));

// ---- Componentes de execução ------------------------------------------------
// [arquivo, regex da trava, regex do id do motivo]
const execucao = [
  ["ConfirmarEstrutura.jsx", /const travado = [^;]*\|\| !!bloqueioMercado;/, /id="confirmar-bloqueio-mercado"/, /aria-describedby=\{bloqueioMercado \? "confirmar-bloqueio-mercado"/],
  ["ExecutarProposta.jsx", /const travado = [^;]*\|\| !!bloqueioMercado;/, /id="executar-proposta-bloqueio-mercado"/, /aria-describedby=\{bloqueioMercado \? "executar-proposta-bloqueio-mercado"/],
  ["CuradoriaEstruturas.jsx", /const executarTravado = [^;]*\|\| !!bloqueioMercado;/, /id="curadoria-bloqueio-mercado"/, /aria-describedby=\{bloqueioMercado \? "curadoria-bloqueio-mercado"/],
];
for (const [arq, trava, idMotivo, describedby] of execucao) {
  const s = semComentarios(ler(arq));
  ok(`${arq}: bloqueioMercado entra na DEFINIÇÃO da trava`, trava.test(s));
  ok(`${arq}: motivo renderizado com id`, idMotivo.test(s));
  ok(`${arq}: botão aponta aria-describedby para o motivo`, describedby.test(s));
}
for (const arq of ["CandidatoOpcao.jsx", "PropostaLastreada.jsx"]) {
  const s = semComentarios(ler(arq));
  ok(`${arq}: disabled={busy || degradado} intacto`, s.includes("disabled={busy || degradado}"));
  ok(`${arq}: aria-disabled + aria-describedby com o motivo de mercado`, s.includes('aria-disabled={bloqueioMercado ? "true" : undefined}') && s.includes("aria-describedby={bloqueioMercado ? idBloqueio : undefined}"));
  ok(`${arq}: motivo renderizado com id={idBloqueio}`, /<p id=\{idBloqueio\} role="status"/.test(s));
}
{
  const s = semComentarios(ler("CandidatoOpcao.jsx"));
  ok("CandidatoOpcao: onClick não executa enquanto bloqueado", s.includes("onClick={() => { if (bloqueioMercado) return; onAceitar(p); }}"));
  const p = semComentarios(ler("PropostaLastreada.jsx"));
  ok("PropostaLastreada: onClick sem handler enquanto bloqueado", p.includes("onClick={bloqueioMercado ? undefined : (posAberta ? onFechar : onAbrir)}"));
}
{
  const s = semComentarios(ler("PernasAbertas.jsx"));
  ok("PernasAbertas: ramo bloqueioMercado com aria-disabled, sem disabled nativo, motivo e describedby",
    /bloqueioMercado \? \(\s*<div[^>]*>\s*<button type="button" aria-disabled="true"[\s\S]{0,400}aria-describedby=\{idMercado\}[\s\S]{0,500}<div id=\{idMercado\} role="status"/.test(s));
  ok("PernasAbertas: o ramo de mercado vem antes da confirmação (bloqueia também o 2º passo)", s.indexOf(") : bloqueioMercado ? (") > 0 && s.indexOf(") : bloqueioMercado ? (") < s.indexOf(") : emConfirmacao ? ("));
}

// ---- Nenhum disabled= novo --------------------------------------------------
// Contagem de `disabled=` nativo (excluído aria-disabled) por arquivo ANTES da quick, medida em 2026-10-14.
const ANTES = {
  "ConfirmarEstrutura.jsx": 1, "ExecutarProposta.jsx": 1, "CuradoriaEstruturas.jsx": 2, "CandidatoOpcao.jsx": 1,
  "PropostaLastreada.jsx": 1, "PernasAbertas.jsx": 0, "SecaoAnalisar.jsx": 1, "AbaRecomendadas.jsx": 0, "OpcoesScreen.jsx": 0,
};
for (const [arq, n] of Object.entries(ANTES)) {
  const c = (semComentarios(ler(arq)).match(/(?<!aria-)disabled=/g) || []).length;
  ok(`${arq}: ${n} disabled= nativo (nenhum novo)`, c === n);
}

// ---- Stop/alvo/plano livres -------------------------------------------------
{
  const s = semComentarios(ler("PernasAbertas.jsx"));
  // o bloqueio só aparece no ramo de encerrar (assinatura, repasse, ramo): nada de stop/alvo depende dele
  const usos = (s.match(/bloqueioMercado/g) || []).length;
  ok("PernasAbertas: bloqueioMercado só no ramo de encerrar (props + ramo + repasse)", usos <= 6);
  const prop = semComentarios(ler("PropostaLastreada.jsx"));
  ok("PropostaLastreada: bloqueioMercado não aparece em stop/alvo/plano", !/(stop|alvo|plano)[^\n]{0,80}bloqueioMercado|bloqueioMercado[^\n]{0,80}(putOptionPosition|aplicarProtecao)/i.test(prop));
}

// ---- Texto só de copy.js ----------------------------------------------------
{
  const ruins = readdirSync(dir).filter((n) => /\.jsx?$/.test(n)).filter((n) => /Mercado fechado/.test(semComentarios(ler(n))));
  ok("nenhum 'Mercado fechado' hardcoded em opcoes/ (texto vem só de copy.js)" + (ruins.length ? " — " + ruins.join(",") : ""), ruins.length === 0);
}

if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
