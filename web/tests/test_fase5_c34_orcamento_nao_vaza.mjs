// Fase 5 (v1.1) — guardião de CONFIRMAÇÃO de FIX-C34 do REPORT-01.
//
// Por que este arquivo não constrói NADA novo (leia isto antes de "consertar"
// C-34 daqui a seis meses):
//
// O texto ORIGINAL do achado C-34 (painel de orçamento brapi 100% admin-only)
// diz explicitamente: "não é necessário expor orçamento bruto ao usuário
// final... mesma mudança de C-30 resolve as duas questões." O Copywriting
// Contract da Fase 3 (FIX-C30, `03-01-SUMMARY.md`) decidiu, DELIBERADAMENTE,
// que o qualificador de degradado em TechnicalModal não menciona
// orçamento/cota/mês/limite ao usuário final — só o EFEITO (dado mais
// velho), nunca a CAUSA. Construir um "medidor de consumo × limite" agora
// contradiria essa decisão de produto já tomada e shippada.
//
// Portanto o escopo de C-34 na Fase 5 é CONFIRMAR que esse comportamento
// segue valendo — fechamento por CONFIRMAÇÃO, não por feature nova.
//
// SUPERSESSÃO REGISTRADA: o Success Criteria 4 do ROADMAP (escrito em
// 2026-08-18, ANTES da entrega de FIX-C30 em 2026-08-2x) pedia um "medidor
// visível ao usuário final". Essa frase foi SUPERADA pela decisão de produto
// documentada acima — a verificação da Fase 5 NÃO deve tratar a ausência de
// medidor como lacuna. Reabrir essa decisão (expor medidor de verdade) é
// escolha explícita do Alex a tomar, não inferência do texto do ROADMAP.
//
// Este arquivo NÃO altera test_fase3_fonte_technicals.mjs em nada — a
// duplicação de asserção abaixo é DELIBERADA: se o guardião da Fase 3 for um
// dia relaxado/removido, este ainda grita.
//
// Padrão "static source inspection" da casa. Roda sem build:
// `node web/tests/test_fase5_c34_orcamento_nao_vaza.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const QUALIFICADOR = "dado pode estar mais desatualizado que o habitual";

// (a) o qualificador continua no fonte, exatamente 1x — mesma invariante que
// test_fase3_fonte_technicals.mjs trava, duplicada de propósito aqui.
const qualificadorMatches = src.match(new RegExp(QUALIFICADOR, "g")) || [];
ok(`qualificador de degradado aparece exatamente 1x (achado ${qualificadorMatches.length})`, qualificadorMatches.length === 1);

// (b) condicionado a data.degradado e usando T.warn — mesma invariante de
// test_fase3_fonte_technicals.mjs.
ok("qualificador condicionado a data.degradado", /data\.degradado/.test(src));
ok("qualificador usa T.warn", /data\.degradado[\s\S]{0,80}T\.warn/.test(src));

// (c) a ASSERÇÃO DE NÃO-VAZAMENTO propriamente dita: a vizinhança do
// qualificador (janela de ~200 caracteres em torno da ocorrência) NÃO
// contém as palavras orçamento/cota/limite, nem o caractere `%`. Se alguém
// "consertar" C-34 mencionando a CAUSA (orçamento) ao lado do EFEITO
// (degradado) já visível ao usuário final, este assert quebra.
const idx = src.indexOf(QUALIFICADOR);
if (idx < 0) {
  ok("qualificador encontrado no fonte (pré-requisito para checar vizinhança)", false);
} else {
  const janela = src.slice(Math.max(0, idx - 200), Math.min(src.length, idx + QUALIFICADOR.length + 200));
  const termosProibidos = ["orçamento", "orcamento", "cota", "limite", "%"];
  for (const termo of termosProibidos) {
    ok(
      `vizinhança do qualificador (±200 chars) não contém "${termo}"`,
      !janela.toLowerCase().includes(termo.toLowerCase())
    );
  }
}

// (d) os NÚMEROS de orçamento em FonteDadosScreen continuam vindo de
// adminSummary/admin.usoIA — a fonte admin-only não foi trocada por um
// caminho acessível ao usuário final.
ok(
  "FonteDadosScreen lê orçamento de admin.usoIA (fonte admin-only)",
  /admin\.usoIA/.test(src) && /candles\.orcamentoBrapi/.test(src)
);

// (e) a seção de orçamento continua CONDICIONADA a adminDenied — conta
// não-admin (usuário final comum) não vê os números, mesmo dentro do app
// consumidor.
ok(
  "adminDenied continua gateando a visibilidade da seção de orçamento",
  /!adminDenied && admin && admin\.usoIA && admin\.usoIA\.candles/.test(src)
);

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
