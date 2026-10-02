// Guardião não se apaga — lógica pura da Fase 46.1 (G-07, G-08, AL-02, MD-01, MD-05).
// Origem: 46.1-03 (2026-10-02). Roda isolado: `node web/tests/test_fase461_logica.mjs`.
import * as E from "../src/estruturaCard.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ---- G-07 nomeEmpresaCard
const N = E.nomeEmpresaCard;
ok("nome: catálogo quando q.name vazio", N("PETR4", { name: "" }, [{ t: "PETR4", n: "Petrobras PN" }], null) === "Petrobras PN");
ok("nome: q.name com trim", N("UGPA3", { name: " Ultrapar Participações S.A. " }, [], null) === "Ultrapar Participações S.A.");
ok("nome: custom n = ticker não é nome", N("UGPA3", null, [{ t: "UGPA3", n: "UGPA3" }], null) === null);
ok("nome: último nome visto", N("UGPA3", { name: "" }, [], "Ultrapar") === "Ultrapar");
ok("nome: q.name > último > catálogo", N("X1", { name: "A" }, [{ t: "X1", n: "C" }], "B") === "A" && N("X1", {}, [{ t: "X1", n: "C" }], "B") === "B");
ok("nome: igual ao ticker (case-insens.) inválido", N("UGPA3", { name: "ugpa3" }, [], null) === null && N("UGPA3", {}, [], "Ugpa3") === null);
ok("nome: catálogo não-array e q null não quebram", N("A", null, null, null) === null && N("A", undefined, "x", undefined) === null);

// ---- AL-02 sigPosicaoLeitura / situacaoLeituraPlano
const X = (o) => ({ t: "UGPA3", qty: 100, avg: 10, stop: 9, alvo: 12, qtyTravada: 0, setupEntrada: null, compras: [], preco: 10, ...o });
const S = E.sigPosicaoLeitura;
ok("sig ignora preço", S(X({ preco: 10 })) === S(X({ preco: 11 })));
ok("sig muda com qty/avg/stop/alvo/qtyTravada/setup/compras",
  [{ qty: 200 }, { avg: 11 }, { stop: 8 }, { alvo: 13 }, { qtyTravada: 50 }, { setupEntrada: "rompimento" }, { compras: [{ q: 1 }] }].every((o) => S(X(o)) !== S(X())));
const sig = S(X());
const lei = { resultado: 5, _sigPos: sig };
const SL = (a) => E.situacaoLeituraPlano(a);
let s = SL({ status: "ok", leitura: lei, sigAtual: sig });
ok("ok + mesma sig", s.situacao === "ok" && s.leitura === lei);
s = SL({ status: "carregando", leitura: lei, sigAtual: sig });
ok("carregando + mesma sig mantém ok", s.situacao === "ok" && s.leitura === lei);
s = SL({ status: "carregando", leitura: { ...lei, _sigPos: "outra" }, sigAtual: sig });
ok("carregando + sig diferente", s.situacao === "carregando" && s.leitura === null);
s = SL({ status: "carregando", leitura: undefined, sigAtual: sig });
ok("carregando sem leitura", s.situacao === "carregando" && s.leitura === null);
s = SL({ status: "falha", leitura: lei, sigAtual: sig });
ok("falha + mesma sig -> desatualizada (cópia)", s.situacao === "desatualizada" && s.leitura !== lei && s.leitura.desatualizada === true && s.leitura.resultado === 5 && lei.desatualizada === undefined);
s = SL({ status: "falha", leitura: { ...lei, _sigPos: "outra" }, sigAtual: sig });
ok("falha + sig diferente -> falha", s.situacao === "falha" && s.leitura === null);
s = SL({ status: "falha", leitura: undefined, sigAtual: sig });
ok("falha sem leitura", s.situacao === "falha" && s.leitura === null);
s = SL({ status: "ok", leitura: undefined, sigAtual: sig });
ok("ok sem leitura do ticker -> falha", s.situacao === "falha" && s.leitura === null);
s = SL({ status: "ok", leitura: { ...lei, _sigPos: "outra" }, sigAtual: sig });
ok("ok + sig diferente -> carregando", s.situacao === "carregando" && s.leitura === null);

// ---- Task 2: linhasResultadoV6
const L = (a) => E.linhasResultadoV6(a);
const perna = (o) => ({ id: "UGPAK42", resultado: null, ...o });
const resEst = (o) => ({ total: null, acoes: -100, incompleto: true, pernasSemCotacao: ["UGPAK42"], pernasSemDados: [], ...o });
let q = L({ estrutura: { resultado: resEst(), pernas: [perna({ motivoSemCotacao: "fora_da_cadeia" })] } });
ok("G-08 nota fora_da_cadeia + chip", eq(q.notas, [{ chave: "causa_fora_da_cadeia", vals: { contratos: "UGPAK42" } }]) && q.chipCabecalho === "chip_total_suspenso");
ok("G-08 cabecalho intacto", eq(q.cabecalho, { valor: null, legenda: null, vals: {}, suspenso: true }));
q = L({ estrutura: { resultado: resEst(), pernas: [
  perna({ id: "A", motivoSemCotacao: "sem_negocio" }),
  perna({ id: "B", motivoSemCotacao: "fonte_indisponivel" }),
  perna({ id: "C", motivoSemCotacao: "sem_negocio" }),
  perna({ id: "D", motivoSemCotacao: "fora_da_cadeia" }),
] } });
ok("G-08 ordem das causas e agrupamento", eq(q.notas.map((n) => n.chave), ["causa_fonte_indisponivel", "causa_fora_da_cadeia", "causa_sem_negocio"]) && q.notas[2].vals.contratos === "A, C");
q = L({ estrutura: { resultado: resEst(), pernas: [perna({}), perna({ id: "Z", motivoSemCotacao: "lixo" })] } });
ok("G-08 ausente/desconhecido -> sem_cotacao", eq(q.notas, [{ chave: "causa_sem_cotacao", vals: { contratos: "UGPAK42, Z" } }]));
q = L({ estrutura: { resultado: resEst({ pernasSemDados: ["UGPAK42"] }), pernas: [perna({ motivoSemCotacao: "sem_cotacao" })] } });
ok("G-08 perna sem dados não gera nota", q.notas.length === 0);
q = L({ estrutura: { resultado: resEst({ total: 50, incompleto: false, pernasSemCotacao: [] }), pernas: [perna({ resultado: 150 })] } });
ok("G-08 total presente -> sem notas/chip", q.notas.length === 0 && q.chipCabecalho === null);

// caminho plano
q = L({ estrutura: null, leituraPlano: null, situacaoPlano: "carregando" });
ok("plano carregando", q.linhas[0].motivo === "motivo_lendo" && q.chipCabecalho === null);
q = L({ estrutura: null, leituraPlano: null, situacaoPlano: "falha" });
ok("plano falha nunca diz cotação indisponível", q.linhas[0].motivo === "motivo_leitura_indisponivel" && q.chipCabecalho === null && q.cabecalho.suspenso === true);
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 1, desatualizada: true }, situacaoPlano: "desatualizada" });
ok("plano desatualizada", q.cabecalho.valor === 120 && q.chipCabecalho === "chip_desatualizado");
q = L({ estrutura: null, leituraPlano: { resultado: null }, situacaoPlano: "ok" });
ok("plano ok sem resultado (atual)", q.linhas[0].motivo === "motivo_cotacao_indisponivel" && q.chipCabecalho === "chip_total_suspenso");
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 2 } });
ok("plano ok com resultado: sem chip", q.chipCabecalho === null && q.notas.length === 0 && q.cabecalho.legenda === "legenda_resultado_variacao");
// MD-05
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 2 }, estruturaPendente: true });
ok("MD-05 legenda só ações", q.cabecalho.legenda === "legenda_resultado_so_acoes" && eq(q.cabecalho.vals, {}));
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 2 }, estruturaPendente: false });
ok("MD-05 sem pendência: legenda atual", q.cabecalho.legenda === "legenda_resultado_variacao");

// ---- estadoPrincipalV6 (MD-01, desatualizada)
const P = (o) => ({ t: "UGPA3", qty: 1000, qtyTravada: 0, stop: 10, alvo: 20, ...o });
const est = (o) => ({ estado: "vigente", estadoTexto: "txt", resultado: { incompleto: false }, ...o });
let r = E.estadoPrincipalV6({ p: P({ stop: null, alvo: null }), estrutura: est({ stopTexto: "Protegida pela put" }), leituraPlano: { preco: 15 } });
ok("MD-01 protegida pela put sem stop -> sem estado", r.principal === null);
r = E.estadoPrincipalV6({ p: P({ stop: null, alvo: null }), estrutura: est(), leituraPlano: { preco: 15 } });
ok("MD-01 sem stopTexto -> sem plano", r.principal && r.principal.chave === "estado_sem_plano");
r = E.estadoPrincipalV6({ p: P({ stop: null, alvo: null, qtyTravada: 1000 }), estrutura: est({ stopTexto: "Protegida pela put" }), leituraPlano: null });
ok("MD-01 travadas mantém precedência", r.principal.chave === "estado_travadas_todas");
r = E.estadoPrincipalV6({ p: P(), estrutura: null, leituraPlano: { desatualizada: true, posicaoNoPlano: "abaixo_stop", preco: 9 } });
ok("desatualizada não emite estado de risco", r.principal === null);
r = E.estadoPrincipalV6({ p: P(), estrutura: null, leituraPlano: { desatualizada: true, preco: null } });
ok("desatualizada sem preço não emite cotação indisponível", r.principal === null);

if (fails) { console.log(fails + " falha(s)"); process.exit(1); }
console.log("tudo ok");
