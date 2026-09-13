// Fase 27, plano 27-02 (2026-09-13) — guardião do bloco "SEUS VIGIAS".
//
// O defeito que originou a fase: o Alex disse que "os setups criados na aba de
// opções não estão sendo gravados". Não havia falha de escrita — havia três
// fatos que somados eram indistinguíveis disso, e o principal é que um setup
// só era visível com o ticker dele aberto. O bloco "Seus vigias" é a correção:
// ele existe FORA de qualquer ticker e aparece assim que a aba abre.
//
// O que este arquivo tranca, e por que cada coisa só se prova lendo o fonte:
//
//  1. O BLOCO VEM ANTES DA CARTEIRA (D4 do 27-CONTEXT: "vigias antes da
//     carteira"). Renderizá-lo depois do seletor o empurraria para baixo da
//     dobra em 375 px, e um vigia que a pessoa não vê ao abrir é o mesmo que
//     um vigia que não existe — que é literalmente o defeito da fase.
//
//  2. CUSTO ZERO AO ABRIR, CUSTO DECLARADO AO ATUALIZAR. O efeito de mount só
//     pode chamar `store.mcpVigias` (índice local, custo 0 por contrato da
//     rota, 27-01). `store.mcpSetupsListar` custa 2 no cap compartilhado
//     (ADR-027 §3.3) e tem UMA porta: o botão. Um efeito que a chamasse
//     debitaria 2 de todo mundo que só abriu a aba — em silêncio, porque a
//     tela não muda e só o contador sobe.
//
//  3. O NOME QUE A PESSOA LÊ É O DELA. O `nomeNoServico` carrega os 8
//     hexadecimais do hash da conta; ele é endereço no armazém compartilhado
//     do serviço, não rótulo. Exibi-lo é o dano que a injeção nº 4 do 27-01
//     mediu ("o hash vira o nome que a pessoa lê").
//
//  4. SEM MEDIÇÃO NÃO HÁ VEREDITO. Enquanto só o índice respondeu, o estado é
//     travessão COM motivo. Um default negativo afirmaria uma medição que
//     ninguém fez (princípio 4 do CLAUDE.md) — a mesma simetria que a tela já
//     aplica aos setups do ticker ("sem avaliação NÃO vira leitura negativa").
//
//  5. VIGIA DE ATIVO FORA DA CARTEIRA NÃO SOME. Ele existe e continua sendo
//     conferido; escondê-lo repetiria o defeito da fase.
//
// Roda sem build: `node web/tests/test_opcoes_vigias_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dir = join(here, "..", "src", "opcoes");
const ler = (f) => readFileSync(join(dir, f), "utf8");

// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões (este
// arquivo inteiro fala de `mcpSetupsListar` dentro de efeito para dizer que é
// proibido), e contá-los faria o guardião se auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const tela = semComentario(ler("OpcoesScreen.jsx"));
const hook = semComentario(ler("useOpcoesMcp.js"));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) o bloco existe e vem ANTES do seletor de ativos (D4) ---------------
const iBloco = tela.indexOf("cp.opcoesVigiasTitulo");
// Âncora no `const seletor = (`, e não em `carteira.map(` — a derivação dos
// tickers em carteira (usada pelo próprio bloco de vigias, para saber quais
// deles ainda têm lastro) também mapeia `carteira`, e casar nela compararia o
// bloco consigo mesmo.
const iSeletorFonte = tela.indexOf("const seletor = (");
ok("o bloco de vigias existe na tela", iBloco >= 0);
ok("o seletor de ativos existe na tela", iSeletorFonte >= 0);
ok("o bloco de vigias é montado ANTES do seletor de ativos (vigias antes da carteira)",
   iBloco >= 0 && iSeletorFonte > iBloco);
const iRenderBloco = tela.indexOf("{blocoVigias}");
const iRenderSeletor = tela.indexOf("carteira.length > 0 ? seletor");
ok("o bloco de vigias é RENDERIZADO antes do seletor",
   iRenderBloco >= 0 && iRenderSeletor > iRenderBloco);
// Sem `ticker` no caminho: o bloco existe fora de qualquer ativo — é essa
// independência que corrige o defeito 2 do 27-CONTEXT.
ok("o bloco é renderizado sem depender de haver ticker escolhido",
   /\n\s*\{blocoVigias\}\n/.test(tela));

// ---- 2) custo zero ao abrir; custo 2 só no clique --------------------------
const efeitos = hook.split("useEffect(").slice(1).map((t) => t.split("}, [")[0]);
ok("o hook tem um efeito que lê o índice de vigias (store.mcpVigias)",
   efeitos.some((corpo) => corpo.includes("store.mcpVigias")));
ok("NENHUM efeito chama store.mcpSetupsListar (custo 2 só em clique explícito)",
   efeitos.every((corpo) => !corpo.includes("mcpSetupsListar")));
ok("store.mcpSetupsListar tem UMA porta, e ela é um useCallback (atualizarVigias)",
   /const atualizarVigias = useCallback\(/.test(hook)
   && (hook.match(/store\.mcpSetupsListar/g) || []).length === 1);
ok("o efeito do índice não depende de ticker (o bloco existe fora de qualquer ativo)",
   /store\.mcpVigias\(\)[\s\S]{0,400}\}, \[store\]\);/.test(hook));
ok("o índice é recarregado depois de gravar E de desativar um vigia (custo zero)",
   (hook.match(/recarregarVigias\(\);/g) || []).length >= 2);
ok("o hook exporta os dois trios e a ação de atualizar",
   /vigias, vigiasVivos, atualizarVigias, recarregarVigias,/.test(hook));

// ---- 3) o botão declara o custo NO PRÓPRIO CONTROLE -------------------------
const iBotao = tela.indexOf("onClick={atualizarVigias}");
ok("existe o botão que dispara a atualização", iBotao >= 0);
const botao = iBotao >= 0 ? tela.slice(iBotao, tela.indexOf("</button>", iBotao)) : "";
ok("o rótulo do botão vem do copy (cp.opcoesVigiasAtualizar)",
   /cp\.opcoesVigiasAtualizar/.test(botao));
ok("o custo é declarado DENTRO do botão, reusando cp.opcoesCustoChamadas",
   /cp\.opcoesCustoChamadas/.test(botao));
ok("o custo é a constante nomeada, espelho do _cap_check(uid, 2) do backend",
   /const CUSTO_LISTAR_VIGIAS = 2;/.test(tela) && /CUSTO_LISTAR_VIGIAS/.test(botao));
ok("o botão tem alvo de toque de 44 px (reusa BOTAO)", /\.\.\.BOTAO/.test(botao));

// ---- 4) o nome exibido é o da PESSOA, nunca o do armazém -------------------
const iCartao = tela.indexOf("function CartaoDeVigia");
ok("existe componente próprio para o cartão do vigia", iCartao >= 0);
const cartao = iCartao >= 0 ? tela.slice(iCartao, tela.indexOf("\n}", iCartao) + 2) : "";
ok("o cartão lê o nome do usuário (nome no índice, name na listagem do dia)",
   /v\.nome \|\| v\.name/.test(cartao));
ok("o cartão NÃO toca em nomeNoServico (é endereço no armazém, não rótulo)",
   !/nomeNoServico/.test(cartao));

// ---- 5) sem medição não há veredito ----------------------------------------
ok("o estado ausente usa cp.opcoesVigiasSemEstado (travessão COM motivo)",
   /cp\.opcoesVigiasSemEstado|c\.opcoesVigiasSemEstado/.test(cartao));
ok("o fonte da tela não carrega a string \"não armado\" como default do bloco",
   !/não armado/i.test(tela));
ok("armed/streak só aparecem sob o estado MEDIDO (ramo temEstado)",
   /temEstado \?/.test(cartao) && /v\.armed === true/.test(cartao));
ok("o motivo do backend (vigia sumido do armazém) vai VERBATIM",
   /v\.motivo \?/.test(cartao) && /\{v\.motivo\}/.test(cartao));

// ---- 6) clicar no cartão leva ao ativo do vigia (SC-1) ---------------------
ok("o cartão navega para o ticker do vigia",
   /onIr\(v\.ticker\)/.test(cartao) && /onIr=\{irParaVigia\}/.test(tela));
ok("navegar NÃO é alternar (clicar no vigia do ativo já aberto não o fecha)",
   /const irParaVigia = \(t\) => \{ if \(t && t !== ticker\) escolherTicker\(t\); \};/.test(tela));
ok("vigia de ativo fora da carteira NÃO some — ele ganha a explicação",
   /naCarteira \? null : \(/.test(cartao) && /opcoesVigiaForaDaCarteira/.test(cartao));

// ---- 7) as chaves novas existem nos DOIS modos -----------------------------
const CHAVES = ["opcoesVigiasTitulo", "opcoesVigiasVazio", "opcoesVigiasSemEstado",
  "opcoesVigiasAtualizar", "opcoesVigiaForaDaCarteira"];
for (const modo of ["estudo", "operador"]) {
  for (const k of CHAVES) {
    ok(`COPY.${modo}.${k} existe e não é vazio`,
       typeof COPY[modo][k] === "string" && !!COPY[modo][k].trim());
  }
  ok(`${modo}: o texto de "sem estado" abre com travessão e diz o porquê`,
     /^—/.test(COPY[modo].opcoesVigiasSemEstado)
     && /pedid|medi/i.test(COPY[modo].opcoesVigiasSemEstado));
  ok(`${modo}: o texto de "sem estado" não afirma medição nenhuma`,
     !/não armado|não disparou|sem disparo/i.test(COPY[modo].opcoesVigiasSemEstado));
  ok(`${modo}: o vigia fora da carteira é declarado como AINDA conferido`,
     /conferid/i.test(COPY[modo].opcoesVigiaForaDaCarteira));
}
// Voz por modo nos textos longos. O TÍTULO é igual nos dois de propósito (é o
// nome da coisa, como `tituloOpcoes`) — travado como igual para que a
// divergência, se vier, seja decisão e não acidente.
ok("o texto de vazio DIFERE entre Estudo e Operador",
   COPY.estudo.opcoesVigiasVazio !== COPY.operador.opcoesVigiasVazio);
ok("o texto de sem-estado DIFERE entre Estudo e Operador",
   COPY.estudo.opcoesVigiasSemEstado !== COPY.operador.opcoesVigiasSemEstado);
ok("o título do bloco é o MESMO nos dois modos (decisão registrada)",
   COPY.estudo.opcoesVigiasTitulo === COPY.operador.opcoesVigiasTitulo);

// A frase de custo passou a servir DUAS contas diferentes (vencimentos e
// vigias), então ela não pode mais carregar a composição de uma delas — senão
// o botão dos vigias mostraria o número certo com a explicação errada.
for (const modo of ["estudo", "operador"]) {
  const frase = COPY[modo].opcoesCustoChamadas(2);
  ok(`${modo}: a frase de custo é genérica (sem a composição dos vencimentos)`,
     !/vencimento/i.test(frase));
  ok(`${modo}: a composição dos vencimentos tem chave própria`,
     typeof COPY[modo].opcoesCustoVencimentos === "string"
     && /vencimento/i.test(COPY[modo].opcoesCustoVencimentos));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
