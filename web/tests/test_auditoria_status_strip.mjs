// Auditoria 2026-08-07, itens 3+4 (docs/auditoria-controle-ordens-parametros.md):
// no topo de "Operador IA", ANTES de qualquer controle, uma linha sempre
// visível mostrava o Modo do app (Estudo × Operador) com link direto pra
// trocar — a distinção entre "esta tela configura parâmetros" e "o
// interruptor mestre mora em Perfil" ficava só implícita antes.
//
// REVERSÃO DELIBERADA (2026-09-05, Fase 21 do milestone v1.5, DEDUP-02):
// a tira acima (depois absorvida pelo card C-19, Fase 3) foi REMOVIDA de
// AgenteScreen — era 100% redundante com o card-herói funcional "OPERADOR
// NO SERVIDOR" logo abaixo, que já mostra a mesma informação de forma
// acionável (toggle real). A INTENÇÃO original desta auditoria sobrevive
// à reversão: "a distinção entre 'esta tela configura parâmetros' e 'o
// interruptor mestre mora em Perfil' não pode ficar só implícita" — isso
// continua garantido, só que agora pelo link textual "Trocar modo →",
// relocado para logo abaixo do parágrafo de introdução da tela, sem a
// tira/card de texto ao redor dele.
//
// Nenhuma informação sumiu: o modo do app (Estudo/Operador) segue visível
// globalmente pelo chip do Topbar (`modeChip={cp.chipModo}`, fora do switch
// de rotas); o link para o Perfil (onde mora o controle "Modo de trabalho")
// segue explícito e incondicional na tela.
//
// Este guardião NÃO foi apagado. Por instrução do CLAUDE.md ("Guardiões de
// teste não se apagam — reversão deliberada atualiza o guardião com
// nota."), ele foi REESCRITO para travar o ESTADO NOVO.
//
// Roda sem build: `node web/tests/test_auditoria_status_strip.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const inicio = app.indexOf("function AgenteScreen(");
if (inicio < 0) { console.error("FALHOU: função AgenteScreen não encontrada em App.jsx"); process.exit(1); }
const fimAprox = app.indexOf("\nfunction ", inicio + 10);
const screen = app.slice(inicio, fimAprox > inicio ? fimAprox : undefined);

// (1) A tira antiga não existe: "Modo do app:" aparece 0× em AgenteScreen.
ok('(1) a tira antiga não existe: "Modo do app:" aparece 0× em AgenteScreen',
   (screen.match(/Modo do app:/g) || []).length === 0);

// (2) A expressão de emoji da tira antiga não aparece mais.
ok('(2) a expressão {operador ? "📈 Operador" : "🎓 Estudo"} não aparece mais em AgenteScreen',
   !/\{operador \? "📈 Operador" : "🎓 Estudo"\}/.test(screen));

// (3) O caminho para o interruptor mestre segue explícito: existe pelo
// menos um A.go("perfil") em AgenteScreen.
const goPerfilHits = (screen.match(/A\.go\("perfil"\)/g) || []).length;
ok('(3) o caminho para o interruptor mestre segue explícito: existe A.go("perfil") em AgenteScreen',
   goPerfilHits >= 1);

// (4) Esse caminho é o link textual relocado — exatamente 1×, ANTES do
// card-herói.
const idxTrocar = screen.indexOf("Trocar modo →");
const idxHeroi = screen.indexOf("OPERADOR NO SERVIDOR");
const trocarHits = (screen.match(/Trocar modo →/g) || []).length;
ok('(4) "Trocar modo →" aparece exatamente 1× e vem ANTES do card-herói OPERADOR NO SERVIDOR',
   trocarHits === 1 && idxTrocar >= 0 && idxHeroi >= 0 && idxTrocar < idxHeroi);

// (5) O link é incondicional (não está dentro de {!operador && (...)}).
// Recorte: do fim do parágrafo de introdução até o comentário do card-herói
// (marcador estável "CARD-HERÓI"). Distinguir do link "Trocar para Modo
// Operador →", que É condicional e segue intocado (asserção separada).
const idxFimIntro = screen.indexOf("Status detalhado, Diário e testes ficam em");
const idxComentarioHeroi = screen.indexOf("CARD-HERÓI");
if (idxFimIntro < 0) { console.error('FALHOU: âncora do parágrafo de introdução ("Status detalhado, Diário e testes ficam em") não encontrada em AgenteScreen'); process.exit(1); }
if (idxComentarioHeroi < 0) { console.error('FALHOU: âncora do comentário do card-herói ("CARD-HERÓI") não encontrada em AgenteScreen'); process.exit(1); }
const recorte = screen.slice(idxFimIntro, idxComentarioHeroi);
ok('(5) o link "Trocar modo →" é incondicional — o recorte entre a introdução e o card-herói não contém "{!operador &&" antes do botão',
   recorte.includes("Trocar modo →") && !/\{!operador &&/.test(recorte));

// Não-regressão do link condicional irmão — "Trocar para Modo Operador →"
// segue intocado e continua guardado por {!operador && (...)}.
const trocarParaHits = (app.match(/Trocar para Modo Operador →/g) || []).length;
ok('(bônus) "Trocar para Modo Operador →" (link condicional distinto) segue presente e não foi afetado por esta reversão',
   trocarParaHits >= 1);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
