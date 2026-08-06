// Toque longo — o GESTO da camada de entendimento (SetorAlvo).
//
// Os contratos que estes guardiões travam, e por quê:
//
//  1. CANCELAMENTO É O QUE FAZ O GESTO CONVIVER. Mover >10px é rolagem;
//     segundo dedo é pinça/scroll; pointercancel é o sistema tomando o toque.
//     Sem qualquer um desses, segurar-para-rolar abriria folha no meio da
//     lista — o gesto viraria inimigo da navegação.
//  2. O SETOR MAIS INTERNO VENCE, por construção (stopPropagation no
//     pointerdown): o carimbo da hora dentro do badge explica a barra; o
//     resto do badge explica o gatilho. Nada de elementFromPoint nem
//     heurística de proximidade — a explicação é reprodutível.
//  3. A FOLHA ABRE NO SOLTAR. Abrir com o dedo ainda na tela deixava o
//     pointerup cair no scrim recém-montado e fechar a folha no mesmo gesto.
//  4. 600ms, NÃO 2s. O callout do iOS ensina ~500ms; o callout e a seleção
//     são suprimidos SÓ nos setores (não na página).
//  5. MEDIÇÃO DE DESCOBERTA. `gesto` × `botao` × `aberturas` é o que calibra
//     o N da dica e os 600ms com dado real — contadores monotônicos nos DOIS
//     stores (max, nunca substituição).
//  6. `tela: "setor:<id>"` no assistente SÓ quando a folha veio do gesto;
//     navegar a cadeia volta para `conceito:<cid>`.
//
// Roda sem build: `node web/tests/test_setor_gesto.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// o corpo do componente, isolado — asserções de AUSÊNCIA precisam de escopo
const setorAlvo = app.slice(app.indexOf("function SetorAlvo("), app.indexOf("function DicaGesto("));
ok("SetorAlvo existe e é isolável para as asserções de ausência", setorAlvo.length > 200);

// ---------------------------------------------------------------- o relógio
ok("o gesto arma em 600ms (não 2s)", /const GESTO_MS = 600;/.test(app));
ok("a tolerância de movimento é 10px", /const GESTO_TOLERANCIA_PX = 10;/.test(app));

// ------------------------------------------------------------ cancelamentos
ok("mover além da tolerância CANCELA o gesto (é rolagem)",
   /Math\.hypot\(e\.clientX - s\.x, e\.clientY - s\.y\) > GESTO_TOLERANCIA_PX\) limpar\(\)/.test(setorAlvo));
ok("segundo dedo cancela (pointerdown com gesto já armando)",
   /if \(s\.t \|\| s\.armado\) \{ limpar\(\); return; \}/.test(setorAlvo));
ok("pointercancel e pointerleave também limpam",
   /onPointerCancel=\{limpar\} onPointerLeave=\{limpar\}/.test(setorAlvo));
ok("a rolagem NÃO é sequestrada (nenhum touchAction: none no setor)",
   !/touchAction/.test(setorAlvo));

// ------------------------------------------------- resolução do setor interno
ok("o setor mais interno vence: o pointerdown não sobe para o de fora",
   /onPointerDown = \(e\) => \{\s*\n\s*e\.stopPropagation\(\);/.test(setorAlvo));
ok("o carimbo da barra é setor DENTRO do badge do timing (caso real de aninhamento)",
   /setorId="timing"/.test(app) && /setorId="barra"/.test(app));
ok("o chip do fundamento é setor DENTRO da linha de análise",
   /setorId="analise"/.test(app) && /setorId="fundamento"/.test(app));

// -------------------------------------------------------- abrir e não vazar
ok("a folha abre no SOLTAR do dedo (não no estouro do timer)",
   /onPointerUp = \(\) => \{[\s\S]*?if \(s\.armado\) \{ s\.disparado = true; abrir\("gesto"\); \}/.test(setorAlvo));
ok("o clique fantasma pós-gesto não vaza para o conteúdo do setor",
   /onClickCapture/.test(setorAlvo) && /e\.stopPropagation\(\); e\.preventDefault\(\);/.test(setorAlvo));
ok("callout e seleção do iOS suprimidos SÓ no setor",
   /WebkitTouchCallout: "none", WebkitUserSelect: "none", userSelect: "none"/.test(setorAlvo));

// -------------------------------------------------- registro vem do backend
ok("sem registro (backend antigo / camada desligada) o setor vira contêiner comum",
   /if \(!cid \|\| !A \|\| !ativo\) return <div style=\{style\}>\{children\}<\/div>;/.test(setorAlvo));
ok("o timing só arma o gesto com PLANO (ativo={didaticaOk})",
   /setorId="timing" dados=\{dados\}[\s\S]{0,200}ativo=\{didaticaOk\}/.test(app));

// ------------------------------------------------------------ dica do gesto
ok("a dica ensina o gesto e morre por contagem de aberturas",
   /const DICA_GESTO_ABERTURAS = 5;/.test(app)
   && /gestoUso\.aberturas\) \|\| 0\) >= DICA_GESTO_ABERTURAS\) return null;/.test(app));
ok("a dica fica fora do Radar (vitrine, não lugar de aprender)",
   /\{contexto !== "radar" && \(\s*\n\s*<DicaGesto/.test(app));
ok("o boot conta a abertura e PARA de gravar depois que a dica morreu",
   /if \(g\.aberturas >= DICA_GESTO_ABERTURAS \+ 3\) return;/.test(app));

// --------------------------------------------------- medição de descoberta
ok("abrirSetor conta gesto × botão (é o que calibra N e 600ms com dado real)",
   /abrirSetor: \(setorId, cid, dados, origem\)/.test(app)
   && /origem === "gesto" \? "gesto" : "botao"/.test(app)
   && /store\.putConfig\(\{ gestoUso: g \}\)/.test(app));

// ------------------------------------- paridade dos DOIS stores (gestoUso)
ok("deviceStore espelha gestoUso com merge MONOTÔNICO (max, nunca substituição)",
   /if \(patch\.gestoUso && typeof patch\.gestoUso === "object"\)/.test(persistence)
   && /Math\.max\(base\[k\] \|\| 0, Math\.min\(Math\.floor\(v\), 100000\)\)/.test(persistence));
ok("deviceStore garante o default de gestoUso em docs antigos",
   /doc\.config\.gestoUso = \{ aberturas: 0, gesto: 0, botao: 0 \}/.test(persistence));

// -------------------------------------------------- assistente com o setor
ok("a folha carrega o setor de origem e o assistente pergunta de lá",
   /setor=\{conceitoAberto\.setor \|\| null\}/.test(app)
   && /tela: setor \? "setor:" \+ setor : "conceito:" \+ cid/.test(app));
ok("navegar a cadeia SAI do setor (tela volta a ser o conceito)",
   /trocarConceito: \(cid\) => setConceitoAberto\(\(c\) => \(c \? \{ \.\.\.c, cid, setor: null/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
