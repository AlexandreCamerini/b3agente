// FASE 8B (B1/B2/B4) — Guardião: "dois apps em um" de verdade.
//
// Contratos trancados:
//  1) copy.js: chaves espelhadas nos dois modos; vocabulário de ordem proibido
//     no ramo ESTUDO; fallback seguro para modo desconhecido;
//  2) B1: as telas leem ctx.cp.* — os textos sensíveis não estão mais
//     hardcodados no App.jsx (títulos, botões, empty states, toasts, saudação);
//  3) B2: override de tema .b3-mode-operador (verde #34d399), classe aplicada
//     no html, chip do modo no Topbar, theme-color por modo, transição só na troca;
//  4) B4: notificações (stop/alvo/variação) na voz do modo; managed preserva
//     o appMode; N3 ganha a camada de mesa no modo operador.
// Roda sem build: `node web/tests/test_copy_theme.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY, copyFor } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const mainPy = readFileSync(join(here, "..", "..", "server", "app", "main.py"), "utf8");
const llmPy = readFileSync(join(here, "..", "..", "server", "app", "llm.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) copy.js íntegro -----------------------------------------------------
const e = Object.keys(COPY.estudo).sort(), o = Object.keys(COPY.operador).sort();
ok("chaves espelhadas nos dois modos (" + e.length + ")", JSON.stringify(e) === JSON.stringify(o));
const estTxt = JSON.stringify(Object.values(COPY.estudo).map((v) => (typeof v === "function" ? v("X", "Y", "Z") + v(null, 0, 0) : v)));
ok("ramo ESTUDO sem vocabulário de ordem", !/registrar entrada|registrar saída|execute a saída|COMPRAR|VENDER/i.test(estTxt.replace(/Simular compra|Simular venda|venda simulada|compra simulada/gi, "")));
ok("fallback para modo desconhecido = estudo", copyFor("banana") === COPY.estudo);

// ---- 2) B1: telas leem cp.* (sem texto sensível hardcodado) -----------------
for (const [nome, usado, proibido] of [
  ["título do Radar", "cp.tituloRadar", ">Radar de mercado</h1>"],
  ["título da Watchlist", "cp.tituloWatchlist", ">Watchlist</h1>"],
  ["título do Portfólio", "cp.tituloPortfolio", ">Portfólio</h1>"],
  ["botão comprar", "cp.btnComprar", ">Simular compra"],
  ["botão vender", "cp.btnVender", ">Simular venda"],
  ["botão aprofundar", "cp.btnAprofundar", ': "Aprofundar com IA"}'],
  ["empty da watchlist", "cp.vazioWatchlist", ">Sua watchlist está vazia<"],
  ["empty do portfólio", "cp.vazioPortfolio", ">Você ainda não tem posições."],
]) {
  ok(nome + " vem do copy.js", app.includes(usado) && !app.includes(proibido));
}
ok("saudação + resumo do dia na voz do modo", app.includes("cp.saudacao(") && app.includes("cp.resumoDia("));
ok("toasts de compra/venda na voz do modo", app.includes("cp.toastCompra(") && app.includes("cp.toastVenda("));
ok("nav fala a língua do modo", app.includes('["mercado", (cp && cp.tituloWatchlist)'));

// ---- qa/34: fraseologia nas superfícies secundárias ---------------------------
// Auditoria (item B, resto): trechos hardcodados na voz de Estudo vazavam para
// o Operador; 3 chaves diferenciadas existiam no dicionário mas nunca chegavam
// à tela (órfãs). Cada assert tranca um dos gaps corrigidos.
ok("qa/34: aba do Radar fala a língua do modo (Radar × Mesa)",
  app.includes('["radar", (cp && cp.tabRadar)') && COPY.estudo.tabRadar !== COPY.operador.tabRadar);
ok("qa/34: onboarding da home na voz do modo",
  app.includes("cp.welcomeTitulo") && app.includes("cp.welcomeCorpo") && app.includes("cp.welcomeCta")
  && !app.includes("Bem-vindo ao seu simulador"));
ok("qa/34: subtítulo da watchlist na voz do modo",
  app.includes("cp.subtituloWatchlist") && !app.includes("Seus ativos em estudo, ordenados"));
ok("qa/34: botão de análise usa a chave (fim da órfã btnAnalise)",
  app.includes('"✨ " + cp.btnAnalise') && !app.includes('"✨ Analisar com IA"'));
ok("qa/34: subtítulo do portfólio ligado (fim da órfã subtituloPortfolio)",
  app.includes("cp.subtituloPortfolio"));
ok("qa/34: bloco 'como analisa' na voz do modo (fim do 'sempre de estudo' na mesa)",
  app.includes("cp.comoAnalisaTitulo") && app.includes("cp.comoAnalisaCorpo")
  && !app.includes("O veredito é sempre de estudo"));
ok("qa/34: CTA de monitoramento do Radar na voz do modo",
  app.includes("{cp.btnAddMonitor}") && app.includes("{cp.jaMonitorado}"));
ok("qa/34: notifVarTitulo diverge entre os modos (era a única chave idêntica)",
  COPY.estudo.notifVarTitulo("X") !== COPY.operador.notifVarTitulo("X"));
ok("qa/34: marcaSufixo removida dos dois modos (chave órfã — modeline a substituiu)",
  !("marcaSufixo" in COPY.estudo) && !("marcaSufixo" in COPY.operador));

// ---- 3) B2: tema por modo ----------------------------------------------------
// Fase 3 (rebranding Boris+, 2026-08-08): o verde do Operador convergiu pro
// MESMO verde da marca (--brand-green, #34d399) — antes uma tonalidade
// própria (#22c55e) sem lastro no Brand Book (que só define um verde/um
// vermelho pro sistema inteiro, não um por modo).
// 08/08/2026: o acento do Operador deixou de ser verde e virou DOURADO
// (#d4af37), por paleta nova do Alex. O verde da marca voltou a ser só sinal
// de compra. O que este guardião sempre quis provar continua igual — que
// existe um override de modo, com acento PRÓPRIO, preso ao seletor composto —
// então o teste passa a checar isso, e não um hex específico (esse fica em
// test_brand_book_v2_tokens.mjs, junto com a medição de contraste).
ok("override .b3-mode-operador tem acento próprio, diferente do Estudo",
   (() => {
     const bloco = (nome) => {
       const i = app.indexOf(`const ${nome} = `);
       if (i < 0) return "";
       let d = 0, ini = app.indexOf("{", i), j = ini;
       for (; j < app.length; j++) { if (app[j] === "{") d++; else if (app[j] === "}") { d--; if (!d) break; } }
       return app.slice(ini, j + 1);
     };
     const acento = (b, esquema) => {
       const i = b.indexOf(esquema + ": {");
       const m = /accent: "(#[0-9a-f]{6})"/i.exec(b.slice(i));
       return m && m[1].toLowerCase();
     };
     const estudo = acento(bloco("PALETTE"), "dark");
     const operador = acento(bloco("MODE_OPERADOR"), "dark");
     return !!estudo && !!operador && estudo !== operador
       && app.includes("b3-mode-operador.b3-theme-dark");
   })());
ok("classe aplicada no html pelo appMode", app.includes('html.classList.toggle("b3-mode-operador", appMode === "operador")'));
ok("chip do modo no Topbar", app.includes("modeChip={cp.chipModo}") && app.includes("{modeChip && (<>"));
// Brand Book v2: a barra do navegador deixou de repetir hex à mão e passou a
// ler o bgBase do esquema em vigor (tema × modo) — é o que garante que ela
// acompanhe TAMBÉM o tema, não só o modo (Operador no claro pintava escuro).
ok("theme-color acompanha o modo E o tema (lê o bgBase do esquema)",
   /const esquema = appMode === "operador"/.test(app) && app.includes('meta.setAttribute("content", esquema.bgBase)'));
// O shell redeclara o tema — tem que redeclarar o modo junto, senão o
// override composto (.b3-mode-operador.b3-theme-*) não alcança a árvore.
ok("shell carrega a classe do modo junto com a do tema",
   app.includes('"b3 b3-shell b3-theme-" + themeKey + (appMode === "operador" ? " b3-mode-operador" : "")'));
ok("transição só durante a troca (classe temporária)", app.includes("b3-mode-switch") && app.includes('html.classList.remove("b3-mode-switch")'));

// ---- 4) B4: notificações + backend ------------------------------------------
ok("notificações de stop/alvo/variação na voz do modo",
  app.includes("cp.notifStopTitulo(") && app.includes("cp.notifAlvoTitulo(") && app.includes("cp.notifVarTitulo("));
ok("managed preserva o appMode (mesa não vira professor)", mainPy.includes('{**mcfg, "appMode": (config or {}).get("appMode")'));
ok("N3 ganha a camada de mesa no modo operador", llmPy.includes("is_operador(config)") && llmPy.includes("Fale como mesa de opera"));

// ---- UX: prevenções de plataforma -------------------------------------------
ok("inputs com 16px (sem zoom automático do Safari)", app.includes("font-size:16px"));
ok("sem flash cinza de toque do iOS", app.includes("-webkit-tap-highlight-color: transparent"));

// ---- FASE 8B (N1–N5): identidade COMPLETA e que não se perde -----------------
// N1: gráficos/canvas também trocam de identidade (usePalette mescla o modo)
ok("ThemeCtx carrega tema + modo", app.includes('ThemeCtx.Provider value={{ key: themeKey, mode: appMode }}'));
ok("usePalette mescla o override do modo (gráficos verdes na mesa)", app.includes("...base, ...(MODE_OPERADOR[key] || {})"));
// N2: iOS local-first — estado do servidor NUNCA sobrescreve o doc do aparelho
ok("boot (auth.me) não sobrescreve o doc local no nativo", app.includes("if (isNative) await loadState();"));
ok("login/register/oauth preservam o doc local no nativo", (app.match(/if \(!isNative && r && r\.state\) setData\(r\.state\); else await loadState\(\);/g) || []).length === 3);
// N2 (revisado 2026-08-07, auditoria de controle de ordens): trocar de modo
// não navega mais — REINICIA o app inteiro. `appMode` é lido de forma
// independente em mais de 10 lugares; só um reload garante que todos
// reflitam a identidade nova. Ver docs/auditoria-controle-ordens-parametros.md.
ok("troca de modo REINICIA o app (reload), nas DUAS portas de entrada (escolher/ativar)",
   (app.match(/setTimeout\(\(\) => window\.location\.reload\(\), 700\)/g) || []).length === 2);
// N4: prompts LLM por modo (professor × mesa), com fallback
ok("copy: prompt do stop/alvo escolhido pelo modo", app.includes("lp.carteiraStopAlvoOperador || lp.carteiraStopAlvo"));
ok("defaults do cliente têm o prompt da mesa", readFileSync(join(here, "..", "src", "catalog.js"), "utf8").includes("carteiraStopAlvoOperador"));
ok("defaults do servidor têm o prompt da mesa", readFileSync(join(here, "..", "..", "server", "app", "defaults.py"), "utf8").includes("carteiraStopAlvoOperador"));
ok("rota escolhe o prompt pelo modo com fallback", mainPy.includes('"carteiraStopAlvoOperador" if modo == "operador" else "carteiraStopAlvo"'));
ok("UI de prompts rotula os dois modos", app.includes("Stop/alvo · Modo Operador (mesa)"));
// N5: superfícies secundárias na voz do modo
for (const k of ["cp.kickerSetups", "cp.btnLevarWatchlist", "cp.btnVerWatchlist", "cp.tituloLeituraIA(t)", "ctx.cp.confirmarCompra", "ctx.cp.confirmarVenda"]) {
  ok("superfície usa " + k, app.includes(k));
}

// ---- FASE 8B (R1–R4): rodada de garantia -------------------------------------
// R1: pedir permissão disponível também no estado denied (deadlock pós-reinstalação)
ok("R1: Pedir permissão em default E denied", app.includes('perm !== "granted" && perm !== "unsupported" && <button onClick={onRequestPermission}'));
// R2: skill por modo, selecionável pelo nome
ok("R2: SkillSection com seletor pelo nome", app.includes("Skill (pelo nome)") && app.includes("<SkillSection ctx={ctx}"));
ok("R2: análise nativa envia a skill do modo", readFileSync(join(here, "..", "src", "persistence.js"), "utf8").includes('doc.config.appMode === "operador" ? doc.skillOperador : doc.skill'));
ok("R2: rota N2 escolhe a skill pelo modo", mainPy.includes('"skillOperador" if modo == "operador" else "skill"'));
ok("R2: defaults da skill de mesa nos dois lados",
  readFileSync(join(here, "..", "src", "catalog.js"), "utf8").includes("defaultSkillTextOperador") &&
  readFileSync(join(here, "..", "..", "server", "app", "defaults.py"), "utf8").includes("default_skill_text_operador"));
// R3: paleta idêntica ao mock + positivos/negativos/textos do modo
// Fase 3 (rebranding Boris+): valores retunados pra família da marca — ver
// comentário de MODE_OPERADOR em App.jsx.
// (v2: o vermelho/rosa da marca também virou constante — BRAND.red.)
ok("R3: card do Operador (#141926) e negativo (vermelho da marca)", app.includes('bgCard: "#141926"') && /negative: (BRAND\.red|"#f26d6d")/.test(app));
ok("R3: textos frios do Operador (muted/faint)", app.includes('textMuted: "#93a3c0"') && app.includes('textFaint: "#5b6890"'));
// qa/mock v2 (racionalização): o badge deixou de ser pill (sólido→contornado)
// e virou uma LINHA de modo sob o wordmark — ponto (halo accentTint) + rótulo
// (color T.accent). Simétrico nos dois modos. Guardião completo do novo padrão
// em test_mode_badge_outlined.mjs.
ok("R3: chip do modo como linha (ponto accentTint + rótulo T.accent)", app.includes("{modeChip && (<>") && /boxShadow: `0 0 0 3px \$\{T\.accentTint\}`/.test(app));
// R4: decisões da mesa no REC_STYLE + filtros/nota/histórico por modo
ok("R4: REC_STYLE cobre COMPRAR/VENDER/AGUARDAR/NÃO OPERAR", app.includes('"COMPRAR": [T.positive') && app.includes('"NÃO OPERAR": [T.textMuted'));
ok("R4: filtros da watchlist por modo", app.includes("cp.filtroAlta") && app.includes("cp.filtroBaixa"));
ok("R4: nota do stop/alvo e histórico por modo", app.includes("ctx.cp.notaStopAlvo") && app.includes("cp.vazioHistorico"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
