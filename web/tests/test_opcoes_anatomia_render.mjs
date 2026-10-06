// Fase 49 (2026-10-06) — guardião SSR da anatomia da perna (ANAT-01/02/06/07/08). Guardião não se apaga. Roda: node web/tests/test_opcoes_anatomia_render.mjs
// Renderiza AnatomiaPerna/GraficoAnatomia (react-dom/server, sem DOM) com o contrato
// do motor (anatomia_perna). Textos esperados vêm de opcoesEscadaTxt, nunca redigitados.
import { register } from "node:module";
import { createElement as h } from "react";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { opcoesEscadaTxt } from "../src/copy.js";

register("./_jsx_loader.mjs", import.meta.url);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const AnatomiaPerna = (await import("../src/opcoes/AnatomiaPerna.jsx")).default;
const GraficoAnatomia = (await import("../src/opcoes/GraficoAnatomia.jsx")).default;

const html = (el) => renderToStaticMarkup(el);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
const tx = (m, k, v) => opcoesEscadaTxt(m, k, v);
const tem = (out, s) => out.includes(esc(s));

const precos = [44, 46, 48, 50, 52];
const grade = { precos, passo: 2, indiceInicial: 2, hoje: 48 };
const pontos = [-21, -21, -21, 9, 29];
const tabela = precos.map((p, i) => ({ preco: p, resultado: pontos[i] }));

const perna = (extra) => ({
  id: "ITUBJ492", tipo: "CALL", lado: "compra", strike: 49.2, quantidade: 100, premioEntrada: 0.21,
  vencimento: "2026-10-09", vencimentoTexto: "09/10", dias: 3,
  prazoTexto: tx("estudo", "anat_prazo_dias", { dias: 3, vencimento: "09/10" }),
  valorPremio: 21, piorCaso: -21, piorIlimitado: false, piorTexto: null, equilibrio: 49.47,
  frase: tx("estudo", "anat_frase_call_compra", { valor: "21,00", premio: "0,21", qtd: 100, ticker: "ITUB4", strike: "49,20", vencimento: "09/10" }),
  condicao: tx("estudo", "anat_cond_call_compra", { ticker: "ITUB4", equilibrio: "49,47" }),
  pontos, marcadores: [{ chave: "strike", preco: 49.2 }, { chave: "equilibrio", preco: 49.47 }], tabela,
  aria: "ARIA-PERNA", incluida: true, motivoTexto: null,
  hoje: { valor: null, premioAtual: null, motivoTexto: "MOTIVO-HOJE" }, encerrar: null,
  ...extra,
});
const pos = { id: "ITUBJ492", underlying: "ITUB4", optionType: "call", strike: 49.2, qty: 100, avg: 0.21 };
const base = { mode: "estudo", ticker: "ITUB4", grade, cursorIdx: 2, onVerSemEsta: () => {}, onEncerrar: () => {}, A: {}, didatica: { ligada: false } };
const card = (p, extra) => html(h(AnatomiaPerna, { ...base, perna: p, pos, ...extra }));

// 1. caso base: perna comprada sem cotação de hoje
const a = card(perna());
const p0 = perna();
ok("1. frase do motor", tem(a, p0.frase));
ok("1. condição do motor", tem(a, p0.condicao));
ok("1. prazo em dias", a.includes("vence em 3 dias (09/10)"));
ok("1. rótulo Pior caso e valor −R$ 21,00", tem(a, tx("estudo", "anat_rotulo_pior")) && a.includes("−R$ 21,00"));
ok("1. Equilíbrio e 49,47", tem(a, tx("estudo", "anat_rotulo_equilibrio")) && a.includes("49,47"));
ok("1. Hoje sem cotação: chip + motivo do motor", tem(a, tx("estudo", "anat_sem_cotacao_chip")) && a.includes("MOTIVO-HOJE"));
ok("1. nota de que o quadro não depende de cotação", tem(a, tx("estudo", "anat_hoje_nota")));
ok('1. gráfico role="img" + hachura', a.includes('role="img"') && a.includes("<pattern"));
ok("1. tabela alternativa (details + table, 5 linhas)", a.includes("<details") && a.includes("<table") && (a.split("<tbody>")[1] || "").split("<tr").length - 1 === 5);
ok("1. nunca 0,00 como Hoje", !a.includes("R$ 0,00") && !a.includes("+R$ 0,00"));
ok("1. botão Ver sem esta perna", tem(a, tx("estudo", "anat_ver_sem_esta")));
ok("1. Encerrar habilitado (sem disabled/aria-disabled)", tem(a, tx("estudo", "pernas_encerrar")) && !/<button[^>]*disabled/.test(a) && !a.includes('aria-disabled="true"'));
ok("1. sem dangerouslySetInnerHTML (texto do motor escapado)", !a.includes("dangerouslySetInnerHTML"));

// 2. Hoje com número
const b = card(perna({ hoje: { valor: -5, premioAtual: 0.16, motivoTexto: null } }));
ok("2. Hoje mostra −R$ 5,00 e não mostra Sem cotação", b.includes("−R$ 5,00") && !tem(b, tx("estudo", "anat_sem_cotacao_chip")));

// 3. pior caso ilimitado
const c = card(perna({ piorCaso: null, piorIlimitado: true, piorTexto: "PIOR-TEXTO-MOTOR" }));
ok("3. ilimitado: texto do motor e rótulo, nunca 0,00", tem(c, tx("estudo", "anat_pior_ilimitado")) && c.includes("PIOR-TEXTO-MOTOR") && !c.includes("R$ 0,00"));

// 4. dados insuficientes
const d = card(perna({ pontos: null, tabela: [], piorCaso: null, equilibrio: null, frase: "", condicao: "", motivoTexto: "MOTIVO-INSUF", hoje: { valor: null, premioAtual: null, motivoTexto: null } }));
ok("4. mostra motivo do motor", d.includes("MOTIVO-INSUF"));
ok("4. sem gráfico e sem botão Ver sem esta", !d.includes('role="img"') && !tem(d, tx("estudo", "anat_ver_sem_esta")));
ok("4. Encerrar continua presente e pior caso/equilíbrio viram travessão", tem(d, tx("estudo", "pernas_encerrar")) && d.includes("—") && !d.includes("R$ 0,00"));

// 5. veto do motor
const e = card(perna({ encerrar: { permitido: false, motivo: "x", texto: "VETO-MOTOR" } }));
ok("5. encerrar.permitido false: aria-disabled + texto + describedby", e.includes('aria-disabled="true"') && e.includes("VETO-MOTOR") && e.includes("aria-describedby"));
const e2 = card(perna({ encerrar: { permitido: true, motivo: null, texto: null } }));
ok("5. encerrar.permitido true: habilitado", !e2.includes('aria-disabled="true"'));

// 6. lastro e vendida
const f = card(perna(), { pos: { ...pos, lastro: { t: "ITUB4", qty: 100 } } });
ok("6. lastro: sem botão Encerrar, texto na estrutura", !f.includes(">" + esc(tx("estudo", "pernas_encerrar")) + "<") && tem(f, tx("estudo", "pernas_na_estrutura")));
const g = card(perna({ lado: "venda" }), { pos: { ...pos, side: "vendida" } });
ok("6. vendida: sem botão Encerrar, texto sem ação", !g.includes(">" + esc(tx("estudo", "pernas_encerrar")) + "<") && tem(g, tx("estudo", "pernas_vendida_sem_acao")));

// 7. confirmação informada
const k = card(perna({ hoje: { valor: -5, premioAtual: 0.16, motivoTexto: null } }), { confirmandoInicial: true });
ok("7. confirmação com cotação: prêmio e resultado interpolados", k.includes("R$ 0,16") && k.includes("−R$ 5,00") && k.includes("Nenhuma ordem real"));
ok("7. confirmação é grupo com Cancelar e Confirmar", k.includes('role="group"') && tem(k, tx("estudo", "pernas_cancelar")) && tem(k, tx("estudo", "pernas_confirmar_sim")));
const k2 = card(perna(), { confirmandoInicial: true });
ok("7. confirmação sem cotação: não dá para calcular", k2.includes("não dá para calcular") && k2.includes("Nenhuma ordem real"));
const k3 = card(perna(), { ocupado: "ITUBJ492" });
ok("7. ocupado: Encerrando… com status", tem(k3, tx("estudo", "pernas_encerrando")) && k3.includes('aria-busy="true"'));

// 8. selecionada e modo operador
const s = card(perna(), { selecionada: true });
ok("8. selecionada: aria-pressed true e rótulo Voltar ao total", s.includes('aria-pressed="true"') && tem(s, tx("estudo", "anat_ver_total")));
const sem = card(perna(), { onVerSemEsta: null });
ok("8. sem onVerSemEsta: sem botão", !tem(sem, tx("estudo", "anat_ver_sem_esta")));
const op = html(h(AnatomiaPerna, {
  ...base, mode: "operador", pos,
  perna: perna({ frase: tx("operador", "anat_frase_call_compra", { valor: "21,00", premio: "0,21", qtd: 100, ticker: "ITUB4", strike: "49,20", vencimento: "09/10" }) }),
}));
ok("8. operador: frase do operador e rótulo Perda máx.", tem(op, tx("operador", "anat_frase_call_compra", { valor: "21,00", premio: "0,21", qtd: 100, ticker: "ITUB4", strike: "49,20", vencimento: "09/10" })) && tem(op, tx("operador", "anat_rotulo_pior")) && tx("operador", "anat_rotulo_pior") === "Perda máx.");

// 9. GraficoAnatomia isolado
const gr = html(h(GraficoAnatomia, { precos, series: [{ id: "p", valores: [1, null, -3, 2, 4], traco: 0 }], area: [1, null, -3, 2, 4], marcadores: [{ preco: 48, rotulo: "K 48" }], cursorIdx: 2, titulo: "T-GRAF", descricao: "D-GRAF" }));
ok('9. gráfico: role="img", title, desc, hachura e marcador', gr.includes('role="img"') && gr.includes("<title") && gr.includes("T-GRAF") && gr.includes("D-GRAF") && gr.includes("<pattern") && gr.includes("K 48"));
ok("9. gráfico: null quebra o traço (dois segmentos M)", ((gr.match(/ d="M[^"]*"/g) || []).some((x) => (x.match(/M/g) || []).length >= 2)));
ok("9. gráfico: ids únicos por instância", html(h("div", null, h(GraficoAnatomia, { precos, series: [], area: pontos, titulo: "a", descricao: "b" }), h(GraficoAnatomia, { precos, series: [], area: pontos, titulo: "a", descricao: "b" }))).match(/<pattern id="([^"]+)"/g).length === 2);
ok("9. gráfico: menos de 2 preços não desenha", html(h(GraficoAnatomia, { precos: [1], series: [], titulo: "a", descricao: "b" })) === "");
// WR-05 (49-REVIEW, 2026-10-06): com perna selecionada, o total segue distinguível da perna 0
const grT = html(h(GraficoAnatomia, { precos, series: [
  { id: "p0", valores: [1, 2, -3, 2, 4], traco: 0, apagada: false, destaque: true },
  { id: "total", tipo: "total", valores: [1, 2, -3, 2, 4], apagada: true }], area: [1, 2, -3, 2, 4], titulo: "a", descricao: "b" }));
ok("9. gráfico: total com seleção ganha halo e cor de texto próprios (não colide com a perna 0)",
  (grT.match(/<path d="M[^"]*" fill="none"/g) || []).length === 3 && grT.includes("stroke-width=\"6\""));

// 10. fonte
const src = readFileSync(new URL("../src/opcoes/AnatomiaPerna.jsx", import.meta.url), "utf8");
ok("10. fonte sem /executavel|frescor|liquida/ (inclusive comentários)", !/executavel|frescor|liquida/.test(src));
ok("10. fonte sem chamada direta a sellOption nem dangerouslySetInnerHTML", !/sellOption|dangerouslySetInnerHTML/.test(src));
ok("10. verbete opc-equilibrio ligado ao termo", /opc-equilibrio/.test(src));

// ---- Fase 49 (2026-10-06) — PosicaoTotal
const PosicaoTotal = (await import("../src/opcoes/PosicaoTotal.jsx")).default;
const precosT = [44, 46, 48, 50, 52];
const gradeT = { precos: precosT, passo: 2, indiceInicial: 2, hoje: 48 };
const mkPerna = (id, tipo, strike, pts) => ({ id, tipo, lado: "compra", strike, pontos: pts, incluida: true, tabela: [], marcadores: [] });
const pCall = mkPerna("ITUBJ493W2", "CALL", 49.2, [-21, -21, -21, 9, 29]);
const pPut = mkPerna("ITUBV465W2", "PUT", 46.5, [200, 100, -240, -300, -300]);
const pCall2 = mkPerna("ITUBJ500W2", "CALL", 50, [-10, -10, -10, -10, 30]);
const totalPts = [169, 69, -277, -301, -241];
const anatT = (extra) => ({
  vencimentoTexto: "09/10", grade: gradeT, excluidas: [],
  acoes: { quantidade: 100, precoMedio: null, incluidas: false, pontos: null, texto: "ACOES-FORA" },
  pernas: [pCall, pPut, pCall2],
  total: {
    pontos: totalPts, incluidas: ["ITUBJ493W2", "ITUBV465W2", "ITUBJ500W2"],
    semEsta: { ITUBJ493W2: [1, 2, -256, 3, 4], ITUBV465W2: [1, 2, -37, 3, 4], ITUBJ500W2: [1, 2, 3, 4, 5] },
    motivoTexto: null, aria: "ARIA-TOTAL", tabela: precosT.map((p, i) => ({ preco: p, resultado: totalPts[i] })),
    marcadores: [{ chave: "strike", preco: 49.2, id: "ITUBJ493W2" }, { chave: "hoje", preco: 48, id: null }],
  },
  ...extra,
});
const tot = (a, extra) => html(h(PosicaoTotal, { mode: "estudo", ticker: "ITUB4", anatomia: a, excluidas: [], onAlternar: () => {}, idx: 2, onIdx: () => {}, selecionada: null, recalculando: false, ...extra }));
const t1 = tot(anatT());
ok("T1. título, 3 chips ligados, slider com 48,00 e não previsão",
  tem(t1, tx("estudo", "anat_total_titulo", { vencimento: "09/10" })) && (t1.match(/aria-pressed="true"/g) || []).length === 3 && t1.includes("48,00") && t1.includes("não previsão"));
ok("T1. leitura do total, ações fora, img, details, aria-live",
  tem(t1, tx("estudo", "anat_leitura_total", { preco: "48,00", valor: "−R$ 277,00" })) && t1.includes("ACOES-FORA") && t1.includes('role="img"') && t1.includes("<details") && t1.includes('aria-live="polite"'));
ok("T1. sem chip de ações quando precoMedio é null", !t1.includes(tx("estudo", "anat_chip_acoes", { qtd: "100" })));
const t2 = tot(anatT(), { selecionada: "ITUBV465W2" });
ok("T2. com/sem e contribuição lidos do motor", t2.includes("−R$ 277,00") && t2.includes("−R$ 37,00") && t2.includes("−R$ 240,00"));
const a3 = anatT(); a3.total.semEsta.ITUBV465W2 = null;
ok("T3. semEsta null usa anat_sem_esta_vazio", tem(tot(a3, { selecionada: "ITUBV465W2" }), tx("estudo", "anat_sem_esta_vazio", { id: "ITUBV465W2" })));
const t4 = tot(anatT(), { excluidas: ["ITUBJ493W2"] });
ok("T4. perna excluída fica aria-pressed=false", (t4.match(/aria-pressed="false"/g) || []).length === 1 && (t4.match(/aria-pressed="true"/g) || []).length === 2);
const a5 = anatT({ acoes: { quantidade: 100, precoMedio: 40, incluidas: true, pontos: null, texto: "ACOES-DENTRO" } });
const t5 = tot(a5);
ok("T5. chip de ações com pm do motor ligado", tem(t5, tx("estudo", "anat_chip_acoes", { qtd: "100" })) && (t5.match(/aria-pressed="true"/g) || []).length === 4);
const a6 = anatT(); a6.total = { pontos: null, incluidas: [], semEsta: {}, motivoTexto: "NAO-HA-DADOS", aria: null, tabela: [], marcadores: [] };
const t6 = tot(a6);
ok("T6. total null mostra motivo em status, sem img nem slider", t6.includes("NAO-HA-DADOS") && t6.includes('role="status"') && !t6.includes('role="img"') && !t6.includes('type="range"'));
const a7 = anatT({ acoes: null }); a7.total = { pontos: null, incluidas: ["A", "B"], semEsta: {}, motivoTexto: "Não há dados suficientes para concluir. VENCIMENTOS-DIFERENTES", aria: null, tabela: [], marcadores: [] };
const t7 = tot(a7, { selecionada: "ITUBV465W2" });
ok("T7. vencimentos diferentes com perna selecionada mostra só o motivo, sem R$",
  t7.includes("Não há dados suficientes para concluir.") && !t7.includes("R$") && !t7.includes("Ela contribui") && !t7.includes("R$ 0,00"));
ok("T8. recalculando mostra anat_recalculando em status", tem(tot(anatT(), { recalculando: true }), tx("estudo", "anat_recalculando")));
const srcT = readFileSync(new URL("../src/opcoes/PosicaoTotal.jsx", import.meta.url), "utf8");
ok("T9. fonte sem palavras proibidas, reduce nem zero substituto", !/executavel|frescor|liquida|reduce\(|\?\? 0|\|\| 0/.test(srcT));

// ---- Fase 49 (2026-10-06) — PernasAbertas contêiner
const PernasAbertasMod = await import("../src/opcoes/PernasAbertas.jsx");
const PernasAbertas = PernasAbertasMod.default;
const mkPos = (id, ex) => ({ id, underlying: "ITUB4", optionType: "call", strike: 49.2, expiration: "2026-10-09", qty: 100, avg: 0.85, ...ex });
const posA = mkPos("ITUBJ493W2");
const posB = mkPos("ITUBV465W2", { optionType: "put", strike: 46.5 });
const posL = mkPos("ITUBJ500W2", { lastro: { t: "ITUB4", qty: 100 } });
const pernaMotor = (id, tipo, strike, pts) => ({
  id, tipo, lado: "compra", strike, quantidade: 100, premioEntrada: 0.85, vencimentoTexto: "09/10", prazoTexto: "PRAZO-" + id,
  piorCaso: -85, piorIlimitado: false, equilibrio: 50, frase: "FRASE-" + id, condicao: "COND-" + id, pontos: pts,
  marcadores: [], tabela: [], aria: "ARIA-" + id, incluida: true, motivoTexto: null, hoje: { valor: null, premioAtual: null, motivoTexto: null }, encerrar: null,
});
const dadosOk = (extra) => ({
  ticker: "ITUB4", modo: "estudo", estado: "ok", motivoTexto: null, custoMcp: 0, estrutura: null,
  anatomia: { ...anatT(), pernas: [pernaMotor("ITUBJ493W2", "CALL", 49.2, pCall.pontos), pernaMotor("ITUBV465W2", "PUT", 46.5, pPut.pontos), pernaMotor("ITUBJ500W2", "CALL", 50, pCall2.pontos)] },
  ...extra,
});
const cont = (props) => html(h(PernasAbertas, { mode: "estudo", ticker: "ITUB4", A: {}, ...props }));
const c1 = cont({ optionPositions: [posA, posB, posL], anatomia: dadosOk() });
const iTot = c1.indexOf(esc(tx("estudo", "anat_total_titulo", { vencimento: "09/10" })));
const iPern = c1.indexOf(esc(tx("estudo", "anat_pernas_titulo")));
const iCard = c1.indexOf("FRASE-ITUBJ493W2");
ok("C1. ordem: gráfico total, título das pernas, primeiro card", iTot >= 0 && iTot < iPern && iPern < iCard);
ok("C1. 3 cards (um por perna aberta)", (c1.match(/<article/g) || []).length === 3 && c1.includes("FRASE-ITUBV465W2") && c1.includes("FRASE-ITUBJ500W2"));
ok("C1. Encerrar só nas compradas sem lastro (2)", (c1.match(new RegExp(">" + tx("estudo", "pernas_encerrar") + "<", "g")) || []).length === 2);
const c1b = cont({ optionPositions: [posA, mkPos("SEM-ITEM1")], anatomia: dadosOk() });
ok("C2. posição sem item na anatomia cai na linha do 48-16", c1b.includes("SEM-ITEM1") && c1b.includes("FRASE-ITUBJ493W2"));
const c3 = cont({ optionPositions: [posA, posB], anatomia: { ticker: "ITUB4", estado: "erro", motivoTexto: "ERRO-ANAT" } });
ok("C3. erro: lista 48-16 + motivo + tentar de novo; Encerrar habilitado",
  c3.includes("ERRO-ANAT") && c3.includes(tx("estudo", "tentar_de_novo")) && (c3.match(new RegExp(">" + tx("estudo", "pernas_encerrar") + "<", "g")) || []).length === 2 && !c3.includes('aria-disabled="true"') && c3.includes(tx("estudo", "pernas_titulo")));
const c4 = cont({ optionPositions: [posA], estrutura: { pernas: [{ id: "ITUBJ493W2", resultado: null, motivoSemCotacao: "sem_negocio", encerrar: { permitido: true } }] } });
ok("C4. enum sem_negocio vira a frase, não o enum cru", c4.includes(esc(tx("estudo", "anat_hoje_sem_negocio"))) && !c4.includes("sem_negocio"));
ok("C5. excluirParaRota nunca leva id encerrado", JSON.stringify(PernasAbertasMod.excluirParaRota(["ITUBJ493W2", "ACOES"], ["ITUBV465W2"])) === JSON.stringify(["ACOES"]));
const c6d = dadosOk(); c6d.anatomia.total = { pontos: null, incluidas: [], semEsta: {}, motivoTexto: "MOTIVO-TOTAL", aria: null, tabela: [], marcadores: [] };
ok("C6. total null: nenhum botão Ver sem esta perna", !cont({ optionPositions: [posA, posB], anatomia: c6d }).includes(tx("estudo", "anat_ver_sem_esta")));
ok("C6b. total ok: botão Ver sem esta perna aparece", c1.includes(tx("estudo", "anat_ver_sem_esta")));
const srcP = readFileSync(new URL("../src/opcoes/PernasAbertas.jsx", import.meta.url), "utf8");
ok("C7. fonte: 1 sellOption, sem palavras proibidas", (srcP.match(/A\.sellOption\(/g) || []).length === 1 && !/executavel|frescor|liquida/.test(srcP));
ok("C8. encerrar perna que estava excluída não gera 400: setExcluidas antes de recarregar",
  srcP.indexOf("setExcluidas((xs) => xs.filter((x) => x !== id))") > 0 && srcP.indexOf("setExcluidas((xs) => xs.filter((x) => x !== id))") < srcP.indexOf("lido.recarregar()"));
ok("C9. hook recebe a lista filtrada", /useAnatomia\(anatomiaInjetada \? null : store, ticker, excluirValido, ids, mode\)/.test(srcP));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
