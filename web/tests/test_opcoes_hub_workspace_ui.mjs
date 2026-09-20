// Fase 34, plano 34-01 (2026-09-20) — guardião do split hub/workspace da
// sub-aba "Setups" da aba Opções.
//
// Este arquivo nasce com só a metade "fundação" da fase (34-01): o
// componente `WorkspaceHeader.jsx` e as 4 chaves de copy novas. O split de
// `OpcoesScreen.jsx` em si (hub × workspace) entra nos planos 34-02/34-03,
// que ACRESCENTAM asserções a ESTE MESMO arquivo — não criam um terceiro
// guardião.
//
// Cada item abaixo nomeia o defeito que ele reprova. Nenhum é decorativo:
//
//  1. **`WorkspaceHeader.jsx` sem export default** — o 34-02 importa o
//     componente por nome; sem export correto, o import quebra em silêncio
//     se o guardião não travar a forma exata.
//  2. **`WorkspaceHeader.jsx` deixando de ser props-only** (hook, `ctx.`/
//     `store.`, import de `App.jsx`) — o orquestrador é o único dono de
//     estado compartilhado (REORG-03/04 da Fase 33); um componente de seção
//     que passa a ler estado por conta própria quebra esse invariante em
//     silêncio.
//  3. **`WorkspaceHeader.jsx` renderizando `.manchete`** — o guardrail CVM
//     (CLAUDE.md princípio 5) exige que só o motor determinístico decida a
//     manchete; a allowlist `RENDERIZADORES_DE_MANCHETE` de
//     `test_opcoes_subabas_ui.mjs` não muda nesta fase, e este componente não
//     entra nela.
//  4. **Botão de voltar perdendo o alvo de toque de 44px ou o rótulo de
//     copy** — regressão silenciosa de acessibilidade/i18n.
//  5. **`WorkspaceHeader.jsx` usando cor de destaque (accent)** — o botão é
//     navegação, não a ação primária da tela (Color do UI-SPEC reserva
//     accent só para a pill ativa).
//  6. **Alguma das 4 chaves novas de copy faltando ou vazia num dos dois
//     modos** — quebraria em produção só no modo que não foi aberto à mão.
//  7. **`SecaoSetups.jsx` perdendo `cp.opcoesSetupsTitulo`/
//     `cp.opcoesCriarTitulo`** — guarda contra o "não renomear" do UI-SPEC;
//     a asserção nasce aqui porque é o 34-03 que mexe no arredor dela.
//
// Roda sem build: `node web/tests/test_opcoes_hub_workspace_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");

const workspaceHeaderBruto = readFileSync(join(dirOpcoes, "WorkspaceHeader.jsx"), "utf8");
const secaoSetupsBruto = readFileSync(join(dirOpcoes, "SecaoSetups.jsx"), "utf8");

// Sem comentários: eles citam os mesmos termos ao explicar as decisões (o
// próprio doc-comment de WorkspaceHeader.jsx menciona "hook"/"manchete" ao
// explicar por que não os usa), e contá-los faria o guardião se
// auto-invalidar (mesmo padrão de test_opcoes_subabas_ui.mjs).
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const workspaceHeader = semComentario(workspaceHeaderBruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 0) parse mudo: um arquivo vazio faria toda negativa abaixo passar de
// graça, sem medir nada de verdade -------------------------------------------
ok("WorkspaceHeader.jsx foi lido e tem corpo (>200 caracteres)",
   workspaceHeaderBruto.length > 200);

// ---- 1) export default correto ----------------------------------------------
ok("WorkspaceHeader.jsx exporta `export default function WorkspaceHeader`",
   /export default function WorkspaceHeader/.test(workspaceHeaderBruto));

// ---- 2) props-only: zero hook, zero ctx./store., zero import de App.jsx ----
ok("WorkspaceHeader.jsx não usa useState/useEffect/useMemo/useRef",
   !/\buse(State|Effect|Memo|Ref)\b/.test(workspaceHeader));
ok("WorkspaceHeader.jsx não lê `ctx.` nem `store.`",
   !/\bctx\./.test(workspaceHeader) && !/\bstore\./.test(workspaceHeader));
ok("WorkspaceHeader.jsx não importa App.jsx",
   !/from\s+["'][^"']*App\.jsx["']/.test(workspaceHeaderBruto));

// ---- 3) sem manchete (guardrail CVM) ----------------------------------------
ok("WorkspaceHeader.jsx não renderiza `.manchete`",
   !/\.manchete\b/.test(workspaceHeader));

// ---- 4) botão de voltar: 44px + copy ----------------------------------------
ok("WorkspaceHeader.jsx declara `minHeight: \"44px\"` no botão de voltar",
   /minHeight:\s*"44px"/.test(workspaceHeader));
ok("WorkspaceHeader.jsx usa `cp.opcoesVoltarAoHub`",
   /cp\.opcoesVoltarAoHub/.test(workspaceHeader));

// ---- 5) sem cor de destaque (accent é só da pill ativa) ---------------------
ok("WorkspaceHeader.jsx não usa `T.accent`",
   !/T\.accent/.test(workspaceHeader));

// ---- 6) paridade de locale das 4 chaves novas -------------------------------
const CHAVES_NOVAS = [
  "opcoesVoltarAoHub", "opcoesAbaAnalisar", "opcoesAbaComparar", "opcoesAbaSetupsSalvos",
];
const chavesFaltando = CHAVES_NOVAS.filter(
  (k) => !COPY.estudo[k] || !COPY.operador[k]);
ok("as 4 chaves novas existem em COPY.estudo e COPY.operador, nenhuma vazia"
   + (chavesFaltando.length ? " (faltando/vazia: " + chavesFaltando.join(", ") + ")" : ""),
   chavesFaltando.length === 0);

// ---- 7) SecaoSetups.jsx intocada (regressão do "não renomear" do UI-SPEC) --
ok("SecaoSetups.jsx continua com `cp.opcoesSetupsTitulo`",
   /cp\.opcoesSetupsTitulo/.test(secaoSetupsBruto));
ok("SecaoSetups.jsx continua com `cp.opcoesCriarTitulo`",
   /cp\.opcoesCriarTitulo/.test(secaoSetupsBruto));

if (fails > 0) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram");
