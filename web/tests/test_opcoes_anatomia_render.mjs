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

// 10. fonte
const src = readFileSync(new URL("../src/opcoes/AnatomiaPerna.jsx", import.meta.url), "utf8");
ok("10. fonte sem /executavel|frescor|liquida/ (inclusive comentários)", !/executavel|frescor|liquida/.test(src));
ok("10. fonte sem chamada direta a sellOption nem dangerouslySetInnerHTML", !/sellOption|dangerouslySetInnerHTML/.test(src));
ok("10. verbete opc-equilibrio ligado ao termo", /opc-equilibrio/.test(src));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
