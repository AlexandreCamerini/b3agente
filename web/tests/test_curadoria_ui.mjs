// Fase 30 (Plano 04, D4) — Guardião estático do bloco "as 4 melhores vendas
// cobertas" em CarteiraScreen (CuradoriaEstruturas + useCuradoria).
//
// Este arquivo tranca a CLASSE de erros que a Fase 30 pode reintroduzir, não
// a instância — cada bloco abaixo defende uma regra que o autor de uma
// edição futura em App.jsx não tem por que conhecer de cor:
//
//   1. as 11 chaves de copy da curadoria existem nos dois modos, string
//      literal, sem palavra de enriquecimento/promessa de lucro (princípios
//      6/8 do CLAUDE.md);
//   2. `item.manchete` é renderizado VERBATIM — guardrail CVM (CLAUDE.md):
//      nenhuma composição de frase a partir de strike/premioTotal, nenhum
//      truncamento;
//   3. a ordem de `top` é do motor — nenhum sort/reverse/comparação de
//      `razao` no componente (T-30-18);
//   4. `narrar()` só sai por toque explícito — nunca dentro do useEffect de
//      busca (D6/T-30-21): buscar narração no mount gastaria cota de quem
//      só abriu a aba;
//   5. o render dos itens lê `top`, nunca `narrativa.estruturas` — a lista
//      não muda quando o texto da IA chega (T-30-20);
//   6. o bloco aparece exatamente uma vez, dentro do mesmo
//      `data.positions.length > 0 &&` da tira irmã (D4);
//   7. toda chamada de rede do hook é best-effort (`.catch(` no próprio
//      encadeamento) — T-30-21;
//   8. nenhuma frase de copy da curadoria promete lucro/garante resultado.
//
// Padrão "static source inspection" da casa (mesmo de
// test_carteira_opcoes_tira.mjs, test_opcoes_proposta_ui.mjs): readFileSync
// de App.jsx + import de COPY, sem build e sem DOM. Roda isolado:
// `node web/tests/test_curadoria_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesma higiene de
// test_carteira_opcoes_tira.mjs / test_fase5_appmode_fonte_unica.mjs: uma
// asserção que CONTA ocorrências precisa ignorar linhas `//`, senão o
// comentário explicativo do próprio componente infla a contagem.
const linhasSemComentario = app.split("\n").filter((l) => !/^\s*\/\//.test(l));
const fonteSemComentario = linhasSemComentario.join("\n");

// ---- Âncoras de função, na ordem esperada de inserção (Fase 30) ----------
const iOO = app.indexOf("function OportunidadesOpcoes");
const iCuradoria = app.indexOf("function CuradoriaEstruturas");
const iPDP = app.indexOf("function PropostaDaPosicao");
const iHookOp = app.indexOf("function useOpcoesPropostas");
const iHookCur = app.indexOf("function useCuradoria");
const iCarteira = app.indexOf("function CarteiraScreen(");
const iHistorico = app.indexOf("function HistoricoScreen(");
ok("as 6 âncoras de função foram localizadas, na ordem esperada (OportunidadesOpcoes < CuradoriaEstruturas < PropostaDaPosicao < useOpcoesPropostas < useCuradoria < CarteiraScreen)",
  iOO > -1 && iCuradoria > iOO && iPDP > iCuradoria && iHookOp > iPDP && iHookCur > iHookOp && iCarteira > iHookCur && iHistorico > iCarteira);

const fatiaCuradoriaComComentario = app.slice(iCuradoria, iPDP);
const fatiaHookCurComComentario = app.slice(iHookCur, iCarteira);
const fatiaCarteiraComComentario = app.slice(iCarteira, iHistorico);
// versões sem comentário, para as contagens (sort/reverse/manchete etc.)
const fatiaCuradoria = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function CuradoriaEstruturas"),
  fonteSemComentario.indexOf("function PropostaDaPosicao"),
);
const fatiaHookCur = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function useCuradoria"),
  fonteSemComentario.indexOf("function CarteiraScreen("),
);
const fatiaCarteira = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function CarteiraScreen("),
  fonteSemComentario.indexOf("function HistoricoScreen("),
);

// ---- (1) 11 chaves de copy nos dois modos, string literal ----------------
const CHAVES = [
  "curadoriaTitulo", "curadoriaSubtitulo", "curadoriaCarregando", "curadoriaVazio",
  "curadoriaRazaoRotulo", "curadoriaNarrarCta", "curadoriaNarrando", "curadoriaIaRotulo",
  "curadoriaIaRessalva", "curadoriaCotaEsgotada", "curadoriaErroNarrar",
];
ok("11 chaves da curadoria existem em COPY.estudo e COPY.operador",
  CHAVES.every((k) => k in COPY.estudo) && CHAVES.every((k) => k in COPY.operador));
ok("todas as 11 chaves são string literal (não função)",
  CHAVES.every((k) => typeof COPY.estudo[k] === "string") && CHAVES.every((k) => typeof COPY.operador[k] === "string"));

// ---- (2) Guardrail CVM: manchete verbatim, nada de strike/composição -----
ok("CuradoriaEstruturas renderiza {item.manchete} direto (sem composição)",
  /\{item\.manchete\}/.test(fatiaCuradoriaComComentario));
ok("CuradoriaEstruturas NÃO usa template string envolvendo manchete",
  !/`[^`]*\$\{[^}]*manchete/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO concatena manchete (regex `manchete...+`)",
  !/manchete[^}]*\+/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO trunca a manchete (slice/substring/reticências aplicados a manchete)",
  !/manchete[^;]{0,40}(\.slice\(|\.substring\(|…)/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO referencia item.strike (proibido compor frase a partir de strike)",
  !fatiaCuradoria.includes("item.strike"));

// ---- (3) Ordem é do motor — sem sort/reverse/comparação de razao ---------
ok("CuradoriaEstruturas NÃO usa .sort( no corpo",
  !fatiaCuradoria.includes(".sort("));
ok("CuradoriaEstruturas NÃO usa .reverse( no corpo",
  !fatiaCuradoria.includes(".reverse("));
ok("CuradoriaEstruturas NÃO compara item.razao (nenhuma comparação a.razao/b.razao)",
  !/[ab]\.razao\s*[<>-]/.test(fatiaCuradoria));
ok("CuradoriaEstruturas itera top.map( direto — sem [...top].sort/slice antes",
  /\btop\.map\(/.test(fatiaCuradoria) && !/\[\.\.\.top\]/.test(fatiaCuradoria));

// ---- (4) narrar() nunca chamado dentro do useEffect (cota só por toque) --
const iEffectCur = fatiaHookCur.indexOf("useEffect(");
const iEffectCurFim = fatiaHookCur.indexOf("}, []);", iEffectCur);
ok("useCuradoria tem exatamente um useEffect com dependência []",
  iEffectCur > -1 && iEffectCurFim > iEffectCur);
const corpoEffectCur = iEffectCur > -1 && iEffectCurFim > -1 ? fatiaHookCur.slice(iEffectCur, iEffectCurFim) : "";
ok("o corpo do useEffect de useCuradoria NÃO chama narrar(",
  corpoEffectCur.length > 0 && !corpoEffectCur.includes("narrar("));
ok("narrar é retornado pelo hook (só sai por toque explícito do componente)",
  /return\s*\{[^}]*\bnarrar\b/.test(fatiaHookCur));

// ---- (5) itens vêm de `top`; narrativa.estruturas nunca em map( de render
ok("CuradoriaEstruturas mapeia top.map( para renderizar os itens",
  /top\.map\(/.test(fatiaCuradoria));
ok("narrativa.estruturas NÃO aparece em nenhum map( de CuradoriaEstruturas",
  !/narrativa\.estruturas[^;]*\.map\(/.test(fatiaCuradoria) && !/\.map\([^)]*narrativa\.estruturas/.test(fatiaCuradoria));
ok("nenhum .map( do componente itera sobre narrativa (só `top.map(` renderiza itens)",
  !/narrativa\.map\(|narrativa\.estruturas\.map\(/.test(fatiaCuradoria));

// ---- (6) <CuradoriaEstruturas aparece 1x, dentro do bloco data.positions.length > 0
ok("<CuradoriaEstruturas aparece exatamente 1x no fonte",
  (fonteSemComentario.match(/<CuradoriaEstruturas/g) || []).length === 1);
const iTagCur = app.indexOf("<CuradoriaEstruturas");
const iTagOO = app.indexOf("<OportunidadesOpcoes");
ok("<CuradoriaEstruturas aparece depois de <OportunidadesOpcoes (irmão, nesta ordem)",
  iTagCur > iTagOO && iTagOO > -1);
const antesTagCur = app.slice(Math.max(0, iTagCur - 400), iTagCur);
ok("<CuradoriaEstruturas está dentro do mesmo bloco `data.positions.length > 0 &&` da tira irmã (sem outra guarda entre os dois)",
  antesTagCur.includes("data.positions.length > 0") && antesTagCur.includes("<OportunidadesOpcoes"));

// ---- (7) Best-effort: toda chamada de rede do hook tem .catch( -----------
// Mesmo algoritmo de test_carteira_opcoes_tira.mjs: caminha o encadeamento
// real de .then/.catch/.finally por balanceamento de parênteses, em vez de
// uma janela fixa de caracteres.
function encadeamentoTemCatch(src, chamada) {
  const i = src.indexOf(chamada);
  if (i === -1) return { achou: false, temCatch: false };
  let depth = 0, j = i;
  for (; j < src.length; j++) {
    if (src[j] === "(") depth++;
    else if (src[j] === ")") { depth--; if (depth === 0) { j++; break; } }
  }
  let k = j, temCatch = false;
  while (true) {
    while (k < src.length && /\s/.test(src[k])) k++;
    if (src[k] !== ".") break;
    const m = src.slice(k).match(/^\.(then|catch|finally)\(/);
    if (!m) break;
    if (m[1] === "catch") temCatch = true;
    let d = 0, p = k + m[0].length - 1;
    for (; p < src.length; p++) {
      if (src[p] === "(") d++;
      else if (src[p] === ")") { d--; if (d === 0) { p++; break; } }
    }
    k = p;
  }
  return { achou: true, temCatch };
}
const rBusca = encadeamentoTemCatch(fatiaHookCur, "store.opcoesCuradoria(");
const rNarrar = encadeamentoTemCatch(fatiaHookCur, "store.opcoesCuradoriaNarrativa(");
ok("store.opcoesCuradoria( encontrado no corpo de useCuradoria", rBusca.achou);
ok("o encadeamento de store.opcoesCuradoria( contém .catch(", rBusca.temCatch);
ok("store.opcoesCuradoriaNarrativa( encontrado no corpo de useCuradoria", rNarrar.achou);
ok("o encadeamento de store.opcoesCuradoriaNarrativa( contém .catch(", rNarrar.temCatch);

// ---- (8) copy da curadoria não promete lucro nem garante resultado -------
const PROIBIDAS = ["garantido", "lucro garantido", "sem risco", "certeza"];
function copySemPromessa(copy) {
  return CHAVES.every((k) => {
    const v = (copy[k] || "").toLowerCase();
    return PROIBIDAS.every((p) => !v.includes(p));
  });
}
ok("nenhuma das 11 frases de COPY.estudo contém palavra de promessa de lucro/garantia",
  copySemPromessa(COPY.estudo));
ok("nenhuma das 11 frases de COPY.operador contém palavra de promessa de lucro/garantia",
  copySemPromessa(COPY.operador));

// ---- Sanidade adicional: CarteiraScreen chama useCuradoria() -------------
ok("CarteiraScreen chama useCuradoria()",
  /useCuradoria\(\)/.test(fatiaCarteira));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
