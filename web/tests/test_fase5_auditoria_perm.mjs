// Fase 5, FIX-C39 — Guardião estático da regra de acesso explícita da aba
// "Auditoria" no portal admin (web-admin/src/App.jsx, array VIEWS + filtro
// `visiveis`).
//
// Origem: das 10 abas do portal, "Auditoria" era a única sem campo `perm`
// declarado — funcionava (`!v.perm ||` no filtro sempre deixava passar),
// mas a regra de acesso ("qualquer permissão administrativa") ficava
// IMPLÍCITA em vez de declarada como as outras 9. O backend já gateia
// certo (`require_any_admin_permission()`); o risco aqui é de processo, não
// de segurança: alguém "consertando" a inconsistência visual atribuindo uma
// permissão REAL (ex. "observabilidade.ver") e estreitando silenciosamente
// o acesso. Este guardião trava que:
//   • a sentinela PERM_ANY = "*" está declarada;
//   • a entrada "auditoria" carrega perm: PERM_ANY (não uma string real);
//   • o filtro trata PERM_ANY explicitamente, sem alterar a regra efetiva;
//   • NENHUMA das 7 permissões reais usadas pelas outras abas aparece na
//     entrada de auditoria — é a asserção de NÃO-regressão de acesso;
//   • as outras 9 entradas mantêm as permissões originais, intactas.
//
// web-admin/ não tem suíte de teste própria — este guardião segue o mesmo
// precedente de web/tests/test_fase3_custos_falha_brapi.mjs: lê o fonte de
// web-admin/ por readFileSync, roda sem build.
//
// Roda sem build: `node web/tests/test_fase5_auditoria_perm.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ─── sentinela declarada ────────────────────────────────────────────────────
ok('const PERM_ANY = "*" declarada', /const PERM_ANY = "\*"/.test(appAdmin));

// ─── entrada de auditoria usa a sentinela, não uma permissão real ─────────
const idxAuditoria = appAdmin.indexOf('id: "auditoria"');
ok('entrada id: "auditoria" encontrada', idxAuditoria !== -1);
if (idxAuditoria !== -1) {
  const fimLinha = appAdmin.indexOf("\n", idxAuditoria);
  const linha = appAdmin.slice(idxAuditoria, fimLinha === -1 ? undefined : fimLinha);
  ok('entrada de auditoria carrega perm: PERM_ANY', /perm:\s*PERM_ANY/.test(linha));

  // As 7 permissões reais usadas pelas outras 9 abas — nenhuma pode aparecer
  // na entrada de auditoria (travaria "conserto" que estreita o acesso real).
  const permissoesReais = [
    "observabilidade.ver",
    "operador_ia.ver",
    "execucao_automatica.ver",
    "llm.configurar",
    "fontes_dados.configurar",
    "prompts.editar",
    "usuarios.gerenciar",
  ];
  for (const p of permissoesReais) {
    ok(`entrada de auditoria NÃO cita a permissão real "${p}"`, !linha.includes(p));
  }
}

// ─── filtro trata a sentinela explicitamente ───────────────────────────────
ok('filtro visiveis trata v.perm === PERM_ANY explicitamente',
   /VIEWS\.filter\(\(v\) => !v\.perm \|\| v\.perm === PERM_ANY \|\| perms\.includes\(v\.perm\)\)/.test(appAdmin));

// ─── as outras 9 entradas mantêm as permissões originais ──────────────────
const outrasEntradas = [
  ['id: "visaoGeral"', "observabilidade.ver"],
  ['id: "custos"', "observabilidade.ver"],
  ['id: "comportamento"', "observabilidade.ver"],
  ['id: "eficienciaIA"', "operador_ia.ver"],
  ['id: "automacao"', "execucao_automatica.ver"],
  ['id: "mudancaLLM"', "llm.configurar"],
  ['id: "fontesDados"', "fontes_dados.configurar"],
  ['id: "prompts"', "prompts.editar"],
  ['id: "usuarios"', "usuarios.gerenciar"],
];
for (const [id, perm] of outrasEntradas) {
  const idx = appAdmin.indexOf(id);
  ok(`entrada ${id} encontrada`, idx !== -1);
  if (idx !== -1) {
    const fimLinha = appAdmin.indexOf("\n", idx);
    const linha = appAdmin.slice(idx, fimLinha === -1 ? undefined : fimLinha);
    ok(`entrada ${id} mantém perm: "${perm}" (sem regressão)`, linha.includes(`perm: "${perm}"`));
  }
}

// ─── apenas UMA linha do array VIEWS mudou (a de auditoria) ───────────────
ok("exatamente 10 entradas em VIEWS (nenhuma removida/adicionada)",
   (appAdmin.match(/^\s*\{ id: "/gm) || []).length === 10);

console.log(fails === 0 ? "\nTODOS OS TESTES PASSARAM" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
