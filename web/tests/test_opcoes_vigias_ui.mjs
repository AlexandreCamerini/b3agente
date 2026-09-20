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
import { readFileSync, readdirSync } from "fs";
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
// 2026-09-19, Fase 33 (33-01): o bloco "SEUS VIGIAS" virou componente próprio
// (`SecaoVigias.jsx`) — o marcador migrou de ARQUIVO, não regrediu (Pitfall 3
// do 33-RESEARCH/PITFALLS.md). A existência/incondicionalidade do bloco em si
// passa a ser medida na FONTE NOVA; a ORDEM de montagem (D4 da Fase 27:
// "vigias antes da carteira") continua medida em OpcoesScreen.jsx, que é onde
// as duas tags (`<SecaoVigias`/o seletor) são de fato renderizadas lado a
// lado.
const telaVigias = semComentario(ler("SecaoVigias.jsx"));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) o bloco existe e vem ANTES do seletor de ativos (D4) ---------------
const iBloco = telaVigias.indexOf("c.opcoesVigiasTitulo");
ok("o bloco de vigias existe em SecaoVigias.jsx", iBloco >= 0);

const iRenderBloco = tela.indexOf("<SecaoVigias");
const iRenderSeletor = tela.indexOf("carteira.length > 0 ? seletor");
ok("<SecaoVigias é renderizado em OpcoesScreen.jsx", iRenderBloco >= 0);
ok("o marcador do seletor existe em OpcoesScreen.jsx", iRenderSeletor >= 0);
ok("o bloco de vigias é RENDERIZADO antes do seletor (D4: vigias antes da carteira)",
   iRenderBloco >= 0 && iRenderSeletor >= 0 && iRenderSeletor > iRenderBloco);
// Sem `ticker` no caminho: o componente é montado incondicionalmente, fora de
// qualquer ativo — é essa independência que corrige o defeito 2 do
// 27-CONTEXT. O `-1` silencioso é o modo como este guardião ficaria inerte
// se `<SecaoVigias` não existisse: por isso a checagem `>= 0` roda ANTES de
// qualquer fatiamento, acima.
const antesDoRender = iRenderBloco >= 0 ? tela.slice(Math.max(0, iRenderBloco - 40), iRenderBloco) : "";
ok("o bloco é renderizado sem depender de haver ticker escolhido",
   iRenderBloco >= 0 && !/[?&]\s*$/.test(antesDoRender));

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
// 2026-09-19, Fase 33 (33-01): o botão fatiado agora vem de SecaoVigias.jsx.
// A garantia de fonte única do custo (nunca um literal) passa a exigir TRÊS
// pontas, não mais uma: a tabela `CUSTO_DA_ACAO` permanece em
// OpcoesScreen.jsx (FICOU lá por decisão do plano, guardiões ancoram nela);
// ela desce por prop (`custos={CUSTO_DA_ACAO}`) para `<SecaoVigias`; e o
// botão, dentro do componente novo, lê `custos.listarVigias` — nunca
// `CUSTO_DA_ACAO` reimportado nem um `2` digitado ali dentro.
const iBotao = telaVigias.indexOf("onClick={atualizarVigias}");
ok("existe o botão que dispara a atualização", iBotao >= 0);
const botao = iBotao >= 0 ? telaVigias.slice(iBotao, telaVigias.indexOf("</button>", iBotao)) : "";
ok("o rótulo do botão vem do copy (c.opcoesVigiasAtualizar)",
   /c\.opcoesVigiasAtualizar/.test(botao));
ok("o custo é declarado DENTRO do botão, reusando c.opcoesCustoChamadas",
   /c\.opcoesCustoChamadas/.test(botao));
// 2026-09-13 (Fase 27, plano 27-05) — a constante solta `CUSTO_LISTAR_VIGIAS`
// virou uma entrada da tabela `CUSTO_DA_ACAO`, que passou a declarar o custo
// de TODOS os controles da aba. O valor não mudou (2, espelho do
// `_cap_check(uid, 2)` da rota `setups_listar`); o que mudou é que agora há uma
// fonte só na tela em vez de uma constante por botão — duas formas de declarar
// a mesma grandeza divergiriam na primeira manutenção feita só numa delas.
//
// A asserção NÃO foi afrouxada: ela continua exigindo o número literal no
// fonte e continua exigindo que o componente NUNCA reimporte a constante
// (só receba o valor já resolvido por prop). O cruzamento com o backend (que
// esta aqui nunca fez) passou a existir em `test_opcoes_custo_declarado.mjs`,
// que lê os `_cap_check` do fonte Python.
ok("a tabela de custo permanece em OpcoesScreen.jsx, número inalterado",
   /const CUSTO_DA_ACAO = \{[\s\S]*?listarVigias: 2,/.test(tela));
ok("a tabela desce por prop para <SecaoVigias — nunca reimportada no componente",
   /custos=\{CUSTO_DA_ACAO\}/.test(tela) && !/CUSTO_DA_ACAO/.test(telaVigias));
ok("o custo é lido pela PROP custos.listarVigias, nunca um literal",
   /custos\.listarVigias/.test(botao));
ok("o botão tem alvo de toque de 44 px (reusa BOTAO)", /\.\.\.BOTAO/.test(botao));

// ---- 4) o nome exibido é o da PESSOA, nunca o do armazém -------------------
// 2026-09-19, Fase 33 (33-01): `CartaoDeVigia` migrou para dentro de
// SecaoVigias.jsx (uso exclusivo dele) — fatiado da fonte nova.
const iCartao = telaVigias.indexOf("function CartaoDeVigia");
ok("existe componente próprio para o cartão do vigia", iCartao >= 0);
const cartao = iCartao >= 0 ? telaVigias.slice(iCartao, telaVigias.indexOf("\n}", iCartao) + 2) : "";
ok("o cartão lê o nome do usuário (nome no índice, name na listagem do dia)",
   /v\.nome \|\| v\.name/.test(cartao));
ok("o cartão NÃO toca em nomeNoServico (é endereço no armazém, não rótulo)",
   !/nomeNoServico/.test(cartao));

// ---- 4b) o MESMO contrato na lista de setups do ticker ---------------------
// Achado de execução (27-02): o 27-01 mudou a `/leitura` para devolver `name`
// (nome da pessoa) E `nomeNoServico` (chave no armazém), mas a lista de setups
// do ticker continuava passando `s.name` para `abrirGrafico` e para
// `BotaoDesativar`. Com o backend novo isso manda ao serviço um nome SEM
// prefixo: 422 `setup_desconhecido` nos dois botões, em produção. Nenhum teste
// de render pegaria — a tela fica igual até alguém clicar.
//
// A regra é uma frase, e continua sendo a MESMA frase: o que VIAJA usa
// `nomeNoServico`; o que a pessoa LÊ usa `name`. Deduzir um do outro aqui
// recriaria o prefixo em JavaScript, e aí seriam duas implementações da mesma
// regra.
//
// 2026-09-20, Fase 33 (33-03): a lista de setups do ticker virou componente
// próprio (`SecaoSetups.jsx`) — só o ARQUIVO lido mudou (mesmo padrão da
// seção 4 acima, migrada no 33-01). A regra e as cinco asserções continuam
// idênticas.
const telaSetups = semComentario(ler("SecaoSetups.jsx"));
ok("a lista de setups deriva UMA chave de serviço, com fallback",
   /const chave = s\.nomeNoServico \|\| s\.name;/.test(telaSetups));
ok("o gráfico é aberto pela chave do ARMAZÉM, não pelo nome da pessoa",
   /abrirGrafico\(chave\)/.test(telaSetups) && !/abrirGrafico\(s\.name\)/.test(telaSetups));
ok("o painel aberto é casado pela chave do armazém",
   /grafico\.setup === chave/.test(telaSetups));
ok("desativar viaja com a chave do armazém e exibe o nome da pessoa",
   /nome=\{chave\}/.test(telaSetups) && /nomeVisivel=\{s\.name\}/.test(telaSetups)
   && !/nome=\{s\.name\}/.test(telaSetups));
ok("o que a pessoa LÊ continua sendo s.name", /\{s\.name\}<\/div>/.test(telaSetups));

// ---- 4c) nomeNoServico nunca chega a texto renderizado (T-33-08) ----------
// 2026-09-20, Fase 33 (33-03), injeção 3 da prova negativa: nenhum dos
// guardiões existentes (vigias, custo declarado, criar-setup, analisar,
// mcp-aba, subabas, consolidação) reprovava `{s.nomeNoServico}` renderizado
// dentro de SecaoSetups.jsx — o hash de 8 hexadecimais da conta apareceria na
// tela como se fosse o nome do setup (mesmo dano da injeção nº 4 do 27-01,
// desta vez no job 5). Asserção nova, por VARREDURA DE DIRETÓRIO (D-02):
// `nomeNoServico` só pode aparecer na forma exata da derivação da chave —
// qualquer outra ocorrência é candidata a estar sendo lida por uma pessoa.
const dirOpcoesTodo = join(here, "..", "src", "opcoes");
const arquivosOpcoesTodo = readdirSync(dirOpcoesTodo).filter((f) => /\.jsx?$/.test(f));
ok("sanidade: achou pelo menos 10 arquivos em web/src/opcoes/ (varredura por diretório)",
   arquivosOpcoesTodo.length >= 10, `achou ${arquivosOpcoesTodo.length}`);
// Duas formas SEGURAS, que não expõem o hash à leitura: a derivação da chave
// que viaja ao serviço, e o `key=` do React (reconciliação interna, nunca
// pintado na tela).
const DERIVACAO_SEGURA = /const chave = s\.nomeNoServico \|\| s\.name;/g;
const KEY_PROP_SEGURO = /key=\{[^}]*nomeNoServico[^}]*\}/g;
const violamNomeNoServico = arquivosOpcoesTodo.filter((f) => {
  const src = semComentario(ler(f));
  const semSeguro = src.replace(DERIVACAO_SEGURA, "").replace(KEY_PROP_SEGURO, "");
  return /nomeNoServico/.test(semSeguro);
});
ok("nenhum arquivo de web/src/opcoes/ expõe nomeNoServico fora da derivação da chave"
   + (violamNomeNoServico.length ? " (violam: " + violamNomeNoServico.join(", ") + ")" : ""),
   violamNomeNoServico.length === 0);
const criar = semComentario(ler("CriarSetup.jsx"));
// 2026-09-13 (Fase 27, plano 27-05) — a forma ganhou um SUFIXO: o custo da
// ação (1 chamada) passou a entrar no `aria-label`. A razão é a mesma que
// criou esta asserção: `aria-label` SUBSTITUI o texto do botão para quem usa
// leitor de tela, então um custo que vivesse só no <span> visível seria
// invisível justamente para quem não pode conferir na tela.
//
// O que a asserção protege continua idêntico (o nome anunciado é o LEGÍVEL,
// nunca a chave do armazém); ela só deixou de exigir que a expressão TERMINE
// ali. O `}` foi trocado por uma segunda asserção, positiva, sobre o sufixo —
// afrouxar sem repor seria abrir espaço para qualquer coisa depois do nome.
ok("o rótulo lido em voz alta usa o nome visível, nunca o do armazém",
   /aria-label=\{rotulo \+ " " \+ \(nomeVisivel \|\| nome \|\| ""\)/.test(criar));
ok("o custo também é falado em voz alta (o aria-label substitui o texto do botão)",
   /aria-label=\{rotulo \+ " " \+ \(nomeVisivel \|\| nome \|\| ""\) \+ "\. " \+ custo\}/.test(criar));

// ---- 5) sem medição não há veredito ----------------------------------------
ok("o estado ausente usa cp.opcoesVigiasSemEstado (travessão COM motivo)",
   /cp\.opcoesVigiasSemEstado|c\.opcoesVigiasSemEstado/.test(cartao));
// 2026-09-19, Fase 33 (33-01): a garantia passa a valer nos DOIS arquivos —
// o bloco migrou de OpcoesScreen.jsx para SecaoVigias.jsx, e "não armado"
// não pode ressurgir em nenhum dos dois.
ok("nem OpcoesScreen.jsx nem SecaoVigias.jsx carregam \"não armado\" como default do bloco",
   !/não armado/i.test(tela) && !/não armado/i.test(telaVigias));
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
