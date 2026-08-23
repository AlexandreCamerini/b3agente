// Fase 5 (v1.1) — guardião de FIX-C21 do REPORT-01.
//
// C-21 (Médio): 10 de 12 pontos de leitura de `appMode` em App.jsx
// recalculavam de forma independente, em vez de ler a fonte única
// (`ctx.operador` fora de App(), a variável local `appMode` dentro de
// App()). `ctx.operador` existe desde 2026-08-07 com o comentário "Novo
// código deve ler ctx.operador", mas nada travava uma leitura nova voltando
// a recomputar — dívida silenciosa. Este é o tipo de erro que já produziu
// DOIS incidentes de paridade documentados neste projeto (sincronização de
// `appMode` entre device/servidor, carteira nativa divergindo do backend).
//
// Este guardião fecha a CLASSE do erro, não a instância: qualquer leitura
// nova de `data.config.appMode` (ou equivalente) fora da derivação única em
// App() volta a quebrar este teste, mesmo que o autor não conheça o
// histórico de C-21.
//
// Padrão "static source inspection" da casa (mesmo de
// test_fase3_fonte_technicals.mjs): readFileSync + regex sobre o fonte
// (App.jsx não é importável fora do build). Roda sem build:
// `node web/tests/test_fase5_appmode_fonte_unica.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — o fonte tem comentários que
// citam `.appMode` de propósito (histórico, explicação da migração). Contar
// sem filtrar tornaria o guardião auto-invalidável (falharia sempre, mesmo
// sem regressão real). Só remove linhas cujo conteúdo, após trim, COMEÇA
// com `//` — comentário de fim de linha (código + `// nota`) continua
// contado, porque a leitura de código dele já foi migrada e não deve conter
// `.appMode` de qualquer forma.
const linhasSemComentario = src
  .split("\n")
  .filter((linha) => !/^\s*\/\//.test(linha));
const fonteSemComentario = linhasSemComentario.join("\n");

// (a) exatamente 1 ocorrência de `.appMode` em posição de LEITURA fora de
// comentário — a derivação única dentro de App().
const leituras = fonteSemComentario.match(/\.appMode/g) || [];
ok("existe exatamente 1 leitura de `.appMode` fora de comentário no fonte", leituras.length === 1);

const linhaDaLeitura = linhasSemComentario.find((l) => /\.appMode/.test(l)) || "";
ok("a única leitura de `.appMode` está na linha da derivação `const appMode =`",
   /const appMode = /.test(linhaDaLeitura));

// (b) a montagem de `ctx` deriva de `appMode` (variável local), não recomputa
// de `data.config.appMode` — a própria fonte única parou de recomputar.
ok("a montagem de `ctx` contém `operador: appMode === \"operador\"` (deriva da derivação local, não recomputa)",
   /operador:\s*appMode === "operador"/.test(src));

// (c) `ctx.operador` aparece pelo menos 7 vezes — prova que houve MIGRAÇÃO
// (leituras trocadas por consumo da fonte única), não simples remoção das
// leituras (o que deixaria os componentes sem saber o modo).
const ctxOperadorMatches = src.match(/ctx\.operador/g) || [];
ok("`ctx.operador` aparece pelo menos 7 vezes (prova de migração, não de remoção)",
   ctxOperadorMatches.length >= 7);

// (d) as duas ESCRITAS de appMode continuam existindo — o guardião não pode
// induzir alguém a apagar a troca de modo (ModoTrabalhoCard.escolher() e a
// aceitação do termo do Operador).
ok("a escrita `saveConfig({ appMode: m })` (troca de modo) continua existindo",
   /saveConfig\(\{ appMode: m \}\)/.test(src));
ok("a escrita `appMode: \"operador\"` (aceitação do termo) continua existindo",
   /appMode: "operador"/.test(src));

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
