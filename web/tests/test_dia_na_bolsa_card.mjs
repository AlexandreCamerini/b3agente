// Guardião do card "Seu dia na bolsa" (Fase 51, 51-08): lógica pura + regras
// visuais por leitura de fonte do JSX. Roda sem build: node web/tests/test_dia_na_bolsa_card.mjs
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import * as L from "../src/diaNaBolsaLogica.js";
import { diaNaBolsaTxt } from "../src/copy.js";

const aqui = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

// ---- lógica pura -----------------------------------------------------------
const card = {
  data: "2026-11-17", ordem: [1, 3, 2],
  familias: { "1": { linhas: [{ ticker: "A" }] }, "2": { linhas: [], carteiraIbov: null }, "3": { fato: { chave: "f3_gap" } } },
};
ok("familiasNaOrdem: só presentes, na ordem recebida", JSON.stringify(L.familiasNaOrdem(card)) === "[1,3]", JSON.stringify(L.familiasNaOrdem(card)));
ok("familiasNaOrdem: ordem do Operador respeitada", JSON.stringify(L.familiasNaOrdem({ ...card, ordem: [3, 1] })) === "[3,1]");
ok("familiasNaOrdem: sem card -> []", L.familiasNaOrdem(null).length === 0);
const lv = L.linhasVisiveis([1, 2, 3, 4, 5], 0);
ok("linhasVisiveis: máx 3 + excedente", lv.visiveis.length === 3 && lv.excedente === 2);
ok("linhasVisiveis: soma excedente do servidor", L.linhasVisiveis([1, 2], 4).excedente === 4);
ok("chaveExploracao estável", L.chaveExploracao("d", "plano", "X") === L.chaveExploracao("d", "plano", "X"));
ok("chaveExploracao distingue tipo/alvo/card",
  new Set([L.chaveExploracao("d", "plano", "X"), L.chaveExploracao("d", "ativo", "X"),
    L.chaveExploracao("d", "plano", "Y"), L.chaveExploracao("e", "plano", "X")]).size === 4);

const jan = [];
for (let i = 1; i <= 28; i++) jan.push({ data: `2026-10-${String(i).padStart(2, "0")}`, pregao: i % 7 !== 0 && i % 7 !== 6 });
ok("contarDiasDecisao: só dentro da janela, sem duplicar",
  L.contarDiasDecisao(["2026-10-01", "2026-10-01", "2026-10-02", "2026-09-01"], jan) === 2);
ok("contarDiasDecisao: vazio -> 0", L.contarDiasDecisao([], jan) === 0 && L.contarDiasDecisao(null, null) === 0);
ok("textoDecisao4Sem: zero", L.textoDecisao4Sem("estudo", 0, diaNaBolsaTxt).startsWith("Nenhum dia de decisão"));
ok("textoDecisao4Sem: um", L.textoDecisao4Sem("operador", 1, diaNaBolsaTxt) === "1 dia de decisão nas últimas 4 semanas");
ok("textoDecisao4Sem: X", L.textoDecisao4Sem("estudo", 5, diaNaBolsaTxt) === "5 dias de decisão nas últimas 4 semanas");
const dots = L.faixaDots(["2026-10-01"], jan);
ok("faixaDots: 28 itens", dots.length === 28);
ok("faixaDots: decisão", dots[0].tipo === "decisao");
ok("faixaDots: dia sem pregão é sem_pregao (não vazio)", dots.filter((d) => !jan.find((j) => j.data === d.data).pregao).every((d) => d.tipo === "sem_pregao"));
ok("faixaDots: vazio em pregão sem decisão", dots[1].tipo === "vazio");

const src = readFileSync(join(aqui, "../src/diaNaBolsaLogica.js"), "utf8");
ok("lógica sem toISOString (D-17)", !/toISOString/.test(src));

// ---- regras visuais por leitura de fonte do JSX ---------------------------
const jsxPath = join(aqui, "../src/diaNaBolsa.jsx");
ok("diaNaBolsa.jsx existe", existsSync(jsxPath));
if (existsSync(jsxPath)) {
  const bruto = readFileSync(jsxPath, "utf8");
  const semComent = bruto.split("\n").filter((l) => !/^\s*(\/\/|\*|\/\*|\{\/\*)/.test(l)).join("\n");
  ok("sem hex literal", !/#[0-9a-fA-F]{3,6}\b/.test(semComent));
  ok("diaNaBolsaTxt importado", /import\s*\{[^}]*diaNaBolsaTxt[^}]*\}\s*from\s*"\.\/copy\.js"/.test(semComent));
  ok("role=region", /role="region"/.test(semComent));
  ok("título h2", /<h2/.test(semComent));
  ok("alvo de toque 44", /minHeight:\s*(44|"44px")/.test(semComent));
  ok("sem dangerouslySetInnerHTML", !/dangerouslySetInnerHTML/.test(semComent));
  ok("vocabulário proibido ausente", !/perdeu|oportunidade/i.test(semComent));
  const m = semComent.match(/const estiloChip\s*=\s*\(?\s*\{[\s\S]*?\}\)?;/);
  ok("estiloChip único declarado", !!m);
  ok("estiloChip neutro (sem negative/positive)", !!m && !/T\.(negative|positive)/.test(m[0]) && /T\.bgPanel/.test(m[0]) && /T\.borderSubtle/.test(m[0]) && /T\.textPrimary/.test(m[0]));
  ok("chips usam estiloChip", (semComent.match(/estiloChip/g) || []).length >= 2);
  for (const ev of ["daily_card_shown", "daily_card_opened", "daily_card_explored"])
    ok("track " + ev, semComent.includes(`track("${ev}"`));
  const tracks = [...semComent.matchAll(/track\("daily_card_[a-z]+",\s*(\{[^}]*\})/g)].map((x) => x[1]);
  ok("track com props", tracks.length >= 3);
  ok("track sem ticker/preço", tracks.every((t) => !/ticker|preco|price|valor|stop|alvo/i.test(t)), tracks.join(" ; "));
  ok("export DiaNaBolsaCard e FaixaDecisao", /export function DiaNaBolsaCard/.test(semComent) && /export function FaixaDecisao/.test(semComent));
  ok("botão de retry usa erro_tentar", /"erro_tentar"/.test(semComent));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nTudo ok");
