// FIX-C22 (Fase 5, 2026-08-23) — guardião da MIGRAÇÃO de default legado da
// skill no aparelho.
//
// Task 1 deste plano reconciliou web/src/catalog.js com o servidor
// (SKILL_TEXT_ESTUDO/SKILL_TEXT_OPERADOR agora byte-idênticos a
// default_skill_text()/default_skill_text_operador() de defaults.py) e
// travou a paridade com um guardião Python
// (test_a8ii_paridade_defaults_skill_com_catalog_js). Isso sozinho NÃO fecha
// o achado para quem já tem o app instalado: o iPhone é local-first — quem
// já tinha o texto de geração ANTERIOR gravado no aparelho continuaria
// mandando essa persona antiga no corpo de /api/technical/analyze para
// sempre, porque nada reescreve o doc já salvo.
//
// Este teste prova o contrato de migração em web/src/persistence.js
// (deviceStore, dentro de `ensure()` — o "ensureShape" do plano): default
// LEGADO sobe para o canônico; texto EDITADO pelo usuário nunca é tocado
// (mesmo contrato de `_eh_default_antigo` em server/app/store.py). Exercita
// o código real (não inspeção estática) — seed de localStorage por escopo +
// `store._setDeviceScope()` para forçar `ensure()` a reler cada doc.
//
// Roda sem device nem build: `node web/tests/test_fase5_skill_migracao_legado.mjs`.

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};
// getState() sem sessão não deveria chamar rede — mas se algo mudar e passar
// a chamar, falha alto (nunca um "passou por acidente" via fetch real).
globalThis.fetch = async () => { throw new Error("fetch não deveria ser chamado sem sessão"); };

const { store, isNative } = await import("../src/persistence.js");
const { LEGACY_SKILL_TEXTS, defaultSkillText, defaultSkillTextOperador } = await import("../src/catalog.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("ambiente nativo detectado (deviceStore em uso)", isNative === true);

// -- sanidade da lista de migração: nunca vazia, nunca contém o default vigente
// (senão a migração reescreveria o default atual em loop — mesmo sanity
// check de test_hashes_legados_existem_e_nao_incluem_o_default_atual no servidor) --
ok("LEGACY_SKILL_TEXTS não está vazia", Array.isArray(LEGACY_SKILL_TEXTS) && LEGACY_SKILL_TEXTS.length >= 2);
ok("LEGACY_SKILL_TEXTS não contém o SKILL_TEXT_ESTUDO canônico atual",
   !LEGACY_SKILL_TEXTS.includes(defaultSkillText()));
ok("LEGACY_SKILL_TEXTS não contém o SKILL_TEXT_OPERADOR canônico atual",
   !LEGACY_SKILL_TEXTS.includes(defaultSkillTextOperador()));

const seed = (scope, doc) => {
  const key = "b3-agente-state-v1::u:" + scope;
  mem.set(key, JSON.stringify(doc));
};

// ---- (1) skill.text legado ⇒ sobe para o canônico após ensure() ----------
{
  seed("legadoEstudo", { skill: { name: "Mesa B3 - Educacional v1", text: LEGACY_SKILL_TEXTS[0] } });
  store._setDeviceScope("legadoEstudo");
  const r = await store.getState();
  ok("skill.text legado (Estudo) migra para o canônico",
     r.skill.text === defaultSkillText());
}

// ---- (2) skillOperador.text legado ⇒ sobe para o canônico -----------------
{
  seed("legadoOperador", { skillOperador: { name: "Mesa B3 - Operador v1", text: LEGACY_SKILL_TEXTS[1] } });
  store._setDeviceScope("legadoOperador");
  const r = await store.getState();
  ok("skillOperador.text legado migra para o canônico",
     r.skillOperador.text === defaultSkillTextOperador());
}

// ---- (3) skill.text EDITADO pelo usuário ⇒ intocado ------------------------
{
  const editado = "MEU TEXTO DE SKILL PERSONALIZADO — não é default de geração nenhuma";
  seed("editadoEstudo", { skill: { name: "Minha skill", text: editado } });
  store._setDeviceScope("editadoEstudo");
  const r = await store.getState();
  ok("skill.text EDITADO pelo usuário permanece intocado", r.skill.text === editado);
}

// ---- (4) skillOperador.text EDITADO pelo usuário ⇒ intocado ----------------
{
  const editado = "MEU TEXTO DE MESA PERSONALIZADO — edição real do usuário";
  seed("editadoOperador", { skillOperador: { name: "Minha mesa", text: editado } });
  store._setDeviceScope("editadoOperador");
  const r = await store.getState();
  ok("skillOperador.text EDITADO pelo usuário permanece intocado", r.skillOperador.text === editado);
}

// ---- (5) doc sem skill/skillOperador salvo (1º boot) ⇒ nasce no canônico --
{
  store._setDeviceScope("semDocPrevio");
  const r = await store.getState();
  ok("doc novo (sem skill salvo) nasce com SKILL_TEXT_ESTUDO canônico", r.skill.text === defaultSkillText());
  ok("doc novo (sem skillOperador salvo) nasce com SKILL_TEXT_OPERADOR canônico",
     r.skillOperador.text === defaultSkillTextOperador());
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DA MIGRAÇÃO DE SKILL LEGADA PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
