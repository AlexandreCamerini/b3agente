// Fase 3 (v1.1) — guardião de C-11 e C-30 do REPORT-01, leg do App.jsx.
//
// C-11 (Crítico): TechnicalModal renderizava "Fonte: Yahoo Finance" como
// string literal, sem ler proveniência real — informação ativamente falsa
// quando o dado vinha da brapi. Trava que a string fixa não volta e que o
// fallback honesto ("—") existe quando data.source está ausente.
//
// C-30 (Crítico): quando a fatia spot do orçamento brapi passa de 80%, o TTL
// do cache triplica e os dados ficam até 3x mais velhos sem nenhum aviso.
// Trava o qualificador âmbar na linha de fonte do painel técnico e a nova
// linha "estado do orçamento" em FonteDadosScreen.
//
// Padrão "static source inspection" da casa: readFileSync + regex sobre o
// fonte (App.jsx não é importável fora do build). Roda sem build:
// `node web/tests/test_fase3_fonte_technicals.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", p), "utf8");
const src = read("src/App.jsx");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// (a) a string fixa incorreta não volta ao fonte
ok("string fixa 'Yahoo Finance' não existe mais no fonte", src.includes("Yahoo Finance") === false);

// (b) FONTE_LABEL(data.source) é usado na linha de fonte do TechnicalModal
ok("FONTE_LABEL(data.source) aparece no fonte", /FONTE_LABEL\(data\.source\)/.test(src));

// (c) fallback honesto: ausência declarada, nunca um palpite
ok(
  "fallback honesto 'data.source ? FONTE_LABEL(data.source) : \"—\"' existe",
  /data\.source\s*\?\s*FONTE_LABEL\(data\.source\)\s*:\s*"—"/.test(src)
);

// (d) o texto exato do qualificador de degradado aparece 1x
const qualificadorMatches = src.match(/dado pode estar mais desatualizado que o habitual/g) || [];
ok("qualificador de degradado aparece exatamente 1x", qualificadorMatches.length === 1);

// (e) o qualificador está condicionado a data.degradado e usa T.warn
ok("qualificador condicionado a data.degradado", /data\.degradado/.test(src));
ok("qualificador usa T.warn (semântica já estabelecida)", /data\.degradado[\s\S]{0,80}T\.warn/.test(src));

// (f) FonteDadosScreen ganha a linha "estado do orçamento"
const estadoOrcamentoMatches = src.match(/estado do orçamento:/g) || [];
const ttlMatches = src.match(/degradado \(TTL 3×\)/g) || [];
ok("'estado do orçamento:' aparece 1x", estadoOrcamentoMatches.length === 1);
ok("'degradado (TTL 3×)' aparece 1x", ttlMatches.length === 1);

// (g) o helper FONTE_LABEL continua definido e não foi reescrito
ok("helper FONTE_LABEL continua definido verbatim", /const FONTE_LABEL = \(source\) =>/.test(src));

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
