// C-07 (REPORT-01) — Guardião: a tela de Modo de Trabalho nomeia
// explicitamente a aba "Operador IA" e diz que ela pode vender sozinho
// conforme as regras configuradas, para que quem liga o Modo Operador
// entenda o que está habilitando junto (link causal entre modo e automação).
// Formato estático espelhando test_concentracao_carteira.mjs — sem build.
// Roda sem build: `node web/tests/test_c07_modo_operador_nomeia_operador_ia.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 2026-09-10 (aba-opcoes F2, quick 260910-biz) — frase ATUALIZADA, não
// removida. O contrato do C-07 é intacto: a tela de Modo de Trabalho tem de
// NOMEAR o Operador IA e dizer que ele pode vender sozinho conforme as
// regras configuradas. O que mudou foi só o substantivo: o Operador IA
// deixou de ser uma ABA da barra inferior (que passou a ter "Opções" no 5º
// lugar) e virou sub-tela do Portfólio (D-0.1 do `docs/PLANO-aba-opcoes.md`).
// Manter "aba" aqui obrigaria a tela a mentir sobre onde a coisa fica.
// Texto anterior, para o histórico:
//   "Inclui a aba Operador IA — o agente que pode vender sozinho conforme as
//    regras que você configurar."
const FRASE_NOVA = "Inclui o Operador IA (dentro do Portfólio) — o agente que pode vender sozinho conforme as regras que você configurar.";

// ---- isola o corpo de ModoTrabalhoCard -------------------------------------
const iniModo = app.indexOf("function ModoTrabalhoCard(");
const iniTermoModal = app.indexOf("function TermoOperadorModal(");
if (iniModo === -1 || iniTermoModal === -1 || iniTermoModal <= iniModo) {
  throw new Error("Não foi possível isolar ModoTrabalhoCard — re-grep necessário (nomes/ordem mudaram).");
}
const blocoModo = app.slice(iniModo, iniTermoModal);

ok("recorte de ModoTrabalhoCard não veio vazio", blocoModo.length > 200);
ok("recorte nomeia a aba 'Operador IA'", blocoModo.includes("Operador IA"));
ok("recorte contém a frase nova verbatim", blocoModo.includes(FRASE_NOVA));

// ---- a frase é ADITIVA no ramo lido por quem está em Estudo ----------------
ok("ramo Estudo preserva o texto original ('Carteira simulada e leitura didática')",
  blocoModo.includes("Carteira simulada e leitura didática"));
ok("frase nova aparece junto do texto original do ramo Estudo (mesma adição)", (() => {
  const iEstudo = blocoModo.indexOf("Carteira simulada e leitura didática");
  const iFraseAposEstudo = blocoModo.indexOf(FRASE_NOVA, iEstudo);
  // a frase precisa aparecer DEPOIS do início do texto original do ramo
  // estudo, a uma distância curta (mesmo JSX fragment) — prova que entrou
  // no mesmo bloco, não em outro lugar da tela.
  return iEstudo > -1 && iFraseAposEstudo > -1 && (iFraseAposEstudo - iEstudo) < 400;
})());

// ---- não-regressão: nudge da linha 2215 continua verbatim ------------------
ok("frase de nudge (test_prontidao_operador.mjs) segue verbatim no arquivo",
  app.includes("O Modo Operador libera decisões diretas — mas ele parte do que você já entende. Vale a pena estudar pelo menos um ativo antes de ativar."));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE C-07 (OPERADOR IA) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
