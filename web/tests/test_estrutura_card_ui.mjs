// Fase 45 (plano 45-03, CARD-01/03/04/05/06) — guardião estático do card de
// Posição estruturada. Lê App.jsx como TEXTO (sem build, sem DOM), mesmo padrão
// de test_ritmo_sp.mjs (functionBody/semComentarios copiadas dali).
// Guardião não se apaga; reversão deliberada atualiza com nota.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}
function semComentariosJsx(body) {
  return (body || "").replace(/\{\/\*[\s\S]*?\*\/\}/g, "");
}
const limpo = (b) => semComentarios(semComentariosJsx(b));

// --- useEstruturasPosicao ---------------------------------------------------
const hook = limpo(functionBody("useEstruturasPosicao"));
ok("hook existe", hook.length > 0);
ok("hook chama store.optionsProposta(t, true)", /store\.optionsProposta\(t, true\)/.test(hook));
// Fase 45 (code review WR-01/WR-02): reversão deliberada — o pool efêmero
// `executarComTeto(..., 3)` deu lugar a UMA fila por instância do hook.
ok("hook usa fila única criarFilaLeituras(3) via filaRef", /filaRef\s*=\s*useRef\(null\)/.test(hook) && /criarFilaLeituras\(3\)/.test(hook) && !/executarComTeto\(/.test(hook));
ok("hook (code review WR-01): thunk só roda se vale() — vivo e assinatura vigente", /valeLer\s*=/.test(hook) && /vivoRef\.current/.test(hook) && /pedidasRef\.current\[t\]\s*===\s*assinatura/.test(hook));
ok("hook (code review WR-01): efeito e atualizar enfileiram na mesma filaRef com vale", (hook.match(/filaRef\.current\.enfileirar\(/g) || []).length === 2);
ok("hook não tem polling (setInterval/setTimeout)", !/setInterval|setTimeout/.test(hook));
ok("hook: seqRef é useRef(0)", /seqRef\s*=\s*useRef\(0\)/.test(hook));
ok("hook: seqRef nunca zerado", !/seqRef\.current\s*=\s*(0|\{\})/.test(hook) && !/seqRef\.current\s*=\s*(0|\{\})/.test(src));
ok("hook: troca de escopo invalida por incremento", /corteRef\.current\s*=\s*\+\+seqRef\.current/.test(hook));
ok("hook: resposta só aceita se meu > corteRef e meu === ultimoRef", /meu === ultimoRef\.current\[t\]/.test(hook) && /meu > corteRef\.current/.test(hook));
ok("hook: efeito de troca de escopo depende de escopoSeq", /\[escopoSeq\]\)/.test(hook));

// Fase 45 (code review WR-02): cancelamento e época na fila única.
ok("hook (code review WR-02): desmontar cancela a fila pendente", /vivoRef\.current = false;\s*filaRef\.current\.cancelar\(\)/.test(hook));
ok("hook (code review WR-02): troca de escopo cancela a fila antes de avançar o corte", /filaRef\.current\.cancelar\(\);\s*corteRef\.current\s*=\s*\+\+seqRef\.current/.test(hook));
ok("hook (code review WR-02): vale() confere a época (corteRef) capturada ao enfileirar", /const epoca = corteRef\.current/.test(hook) && /corteRef\.current === epoca/.test(hook));
ok("hook (code review WR-02): uma só fila por instância (criarFilaLeituras 1x)", (hook.match(/criarFilaLeituras\(/g) || []).length === 1);

// Fase 45 (code review WR-03): campo parcial do motor nunca vira "null" na perna.
{
  const c = limpo(functionBody("CardPosicaoEstruturada"));
  ok("perna (code review WR-03): quantidade só renderiza quando != null", /perna\.quantidade != null \? " " \+ cp\.estruturaQtdPerna\(perna\.quantidade\) : ""/.test(c) && !/\} \{cp\.estruturaQtdPerna/.test(c));
  ok("perna (code review WR-03): tipo vazio com fallback e trim", /estruturaPernaLinha\(perna\.tipo \|\| ""/.test(c) && /\)\.trim\(\)/.test(c));
  ok("perna (code review WR-03): prêmio de entrada null sem seta nem R$ solto", /perna\.premioEntrada == null \?/.test(c) && /cp\.semPremioPerna/.test(c) && /cp\.estruturaPremioSoAtual\(/.test(c));
}

// Fase 45 (code review WR-04): Encerrar bloqueado sempre tem motivo e continua focável.
{
  const c = limpo(functionBody("CardPosicaoEstruturada"));
  ok("encerrar (code review WR-04): sem disabled nativo, com aria-disabled e onClick que não navega", !/(?<!aria-)disabled=\{bloqueado\}/.test(c) && /aria-disabled=\{bloqueado\}/.test(c) && /onClick=\{bloqueado \? undefined :/.test(c));
  ok("encerrar (code review WR-04): motivo com fallback neutro e describedby só com id renderizado", /motivoEncerrar = bloqueado \? \(\(e\.encerrar && e\.encerrar\.texto\) \|\| cp\.encerrarSemMotivo\)/.test(c) && /aria-describedby=\{motivoEncerrar \? "encerrar-motivo-" \+ p\.t : undefined\}/.test(c) && /\{motivoEncerrar && <div id=\{"encerrar-motivo-" \+ p\.t\}/.test(c));
}

// Fase 45 (code review WR-06): nomeTexto nulo nunca vira "null"/chip sem nome.
{
  const c = limpo(functionBody("CardPosicaoEstruturada"));
  const r = limpo(functionBody("ReguaFaixa"));
  ok("chip (code review WR-06): nome sem nomeTexto cai no chip genérico", /e\.nome && e\.nomeTexto \? estruturaCardTxt\(modo, "chip_estrutura"/.test(c) && /estruturaCardTxt\(modo, "chip_estrutura_generica"\)/.test(c));
  ok("régua (code review WR-06): aria-label com fallback quando nomeTexto é nulo", /cp\.estruturaFaixaAria\(e\.nomeTexto \|\| cp\.estruturaGrupoAria,/.test(r));
}

// --- W-001: R:R do card atual -----------------------------------------------
// Fase 45 (code review WR-05): reversão deliberada — o gate agora recebe o preço
// (mostraRR(p, cur)) e o legado não renderiza mais "R:R atual —".
ok("card atual: R:R atual sob mostraRR(p, cur) &&, sem '—'", /mostraRR\(p, cur\) && \(<span>R:R atual/.test(src) && !/rr == null \? "—" : rr\.toFixed/.test(src) && /const rr = valorRR\(p, cur\);/.test(src));

// --- CarteiraScreen ---------------------------------------------------------
const cart = limpo(functionBody("CarteiraScreen"));
ok("CarteiraScreen usa estadoLeitura", /estadoLeitura\(/.test(cart));
ok("CardPosicaoEstruturada só em estruturada", /modoLeitura === "estruturada" \? \(\s*<CardPosicaoEstruturada/.test(cart));
ok("aviso 'sem stop' do card atual guardado por mostraAvisoSemStop(", /mostraAvisoSemStop\([^)]*\) && <div[^>]*>⚠ Posição sem stop definido/.test(cart));
// Fase 46 (D-15, 2026-09-30): a linha role=status (lendo/indisponivel) saiu do
// ramo simples de CarteiraScreen e foi para o card fechado v6 (CartaoPosicao),
// que a mostra para toda posição com pernas; mesma asserção, novo endereço.
const cartao46 = limpo(functionBody("CartaoPosicao"));
ok("linha role=status 'lendo' (agora em CartaoPosicao)", /role="status"/.test(cartao46) && /"lendo"/.test(cartao46));
ok("linha role=status 'indisponivel' (agora em CartaoPosicao)", /"indisponivel"/.test(cartao46));
ok("CarteiraScreen renderiza CartaoPosicao (Fase 46)", /<CartaoPosicao/.test(cart));
ok("PlanRuler 'POSIÇÃO NO RISCO' segue no card atual", /caption="POSIÇÃO NO RISCO"/.test(cart));

// --- CardPosicaoEstruturada -------------------------------------------------
const cardE = limpo(functionBody("CardPosicaoEstruturada"));
ok("CardPosicaoEstruturada existe", cardE.length > 0);
ok("D-09: sem 'Compras desta posição'", !/Compras desta posição/.test(cardE));
ok("D-07: sem PlanRuler", !/PlanRuler/.test(cardE));
ok("Encerrar navega via goOpcoes(oportunidades, abrirTicker)", /goOpcoes\("oportunidades", \{ abrirTicker: p\.t \}\)/.test(cardE));
ok("aria-describedby presente", /aria-describedby/.test(cardE));
ok('role="group" presente', /role="group"/.test(cardE));
ok("não executa nada (store./buy/sell/fecharLastreada)", !/store\./.test(cardE) && !/\.buy\(/.test(cardE) && !/\.sell\(/.test(cardE) && !/fecharLastreada/.test(cardE));
ok("sem dangerouslySetInnerHTML", !/dangerouslySetInnerHTML/.test(cardE));
ok("sem hex literal", !/#[0-9a-fA-F]{3,6}\b/.test(cardE));
ok("pesos só 400/700", !/fontWeight:\s*(600|800)/.test(cardE));
ok("fontSize sempre string px (ou TAM_TOTAL_ESTRUTURA + px)", (cardE.match(/fontSize:\s*[^,}]+/g) || []).every((f) => /fontSize:\s*("(10\.5|11\.5|13|16)px"|TAM_TOTAL_ESTRUTURA \+ "px")/.test(f)));
ok("caixas bgBase levam background como primeira chave", !/backgroundColor/.test(cardE));
ok("TAM_TOTAL_ESTRUTURA = 24", /^const TAM_TOTAL_ESTRUTURA = 24;/m.test(src));
// Reversão deliberada (45-04): a âncora de 45-03 foi consumida; agora exige a régua no lugar.
ok("âncora do 45-04 consumida e ReguaFaixa renderizada", !/45-04: régua de faixa \+ bloco de limites/.test(src) && /<ReguaFaixa e=\{e\} p=\{p\} cp=\{cp\} \/>/.test(cardE));

// --- 45-04: TravaPill opt-in, régua, tipografia, cor fora de bgBase ---------
const trava = functionBody("TravaPill") || "";
const reguaE = limpo(functionBody("ReguaFaixa"));
ok("TravaPill: assinatura com contorno = false", /function TravaPill\(\{ qty, cp, texto, contorno = false \}\)/.test(src));
ok("TravaPill legado preservado (negativeTint10 + 800)", /background: T\.negativeTint10/.test(trava) && /fontWeight: 800/.test(trava));
ok("TravaPill contorno: transparent + border negative + 700", /background: "transparent", border: `1px solid \$\{T\.negative\}`/.test(trava) && /fontWeight: 700/.test(trava));
{
  const chamadas = [...src.matchAll(/<TravaPill\b[^>]*>/g)];
  const dentro = chamadas.filter((m) => cardE.includes(m[0]));
  const fora = chamadas.filter((m) => !cardE.includes(m[0]));
  ok("todo <TravaPill dentro do card estruturado tem contorno (>= 2)", dentro.length >= 2 && dentro.every((m) => /\bcontorno\b/.test(m[0])));
  ok("nenhum <TravaPill fora do card estruturado tem contorno", fora.length >= 1 && fora.every((m) => !/\bcontorno\b/.test(m[0])));
}
for (const [nome, corpo] of [["CardPosicaoEstruturada", cardE], ["ReguaFaixa", reguaE]]) {
  ok(`${nome}: fontSize sempre string px permitida`, (corpo.match(/fontSize:\s*[^,}]+/g) || []).every((f) => /fontSize:\s*("(10\.5|11\.5|13|16)px"|TAM_TOTAL_ESTRUTURA \+ "px")/.test(f)) && !/fontSize:\s*\d/.test(corpo));
  ok(`${nome}: sem fontWeight 600/800`, !/fontWeight:\s*(600|800)/.test(corpo));
  ok(`${nome}: sem hex literal`, !/#[0-9a-fA-F]{3,6}\b/.test(corpo));
  ok(`${nome}: sem linear-gradient`, !/linear-gradient/.test(corpo));
  ok(`${nome}: sem backgroundColor`, !/backgroundColor/.test(corpo));
  ok(`${nome}: sem innerHTML`, !/dangerouslySetInnerHTML/.test(corpo));
}
ok("ReguaFaixa: role=img e cp.estruturaFaixaAria", reguaE.length > 0 && /role="img"/.test(reguaE) && /cp\.estruturaFaixaAria\(/.test(reguaE));
ok("ReguaFaixa usa dominioRegua/posRegua", /dominioRegua\(/.test(reguaE) && /posRegua\(/.test(reguaE));
ok("R:R no card só sob mostraRR(", /mostraRR\(/.test(cardE) && (cardE.match(/R:R/g) || []).length === 1 && /const rr = valorRR\(p, cur\)/.test(cardE) && /mostraRR\(p, cur\) && <span>R:R atual/.test(cardE));  // Fase 45 (code review WR-05): assinatura com preço
ok('aviso sem stop via mostraAvisoSemStop(p, "estruturada", e)', /mostraAvisoSemStop\(p, "estruturada", e\)/.test(cardE) && !/Posição sem stop definido/.test(cardE));
ok("botões definir stop/alvo nunca desabilitados", !/onEditarStopAlvo[^\n]*disabled/.test(cardE));
{
  const re = /style=\{\{\s*background: T\.bgBase[,\s}]/g;
  let achou = 0, viol = 0, m;
  for (const [corpo] of [[cardE], [reguaE]]) {
    re.lastIndex = 0;
    while ((m = re.exec(corpo))) {
      const ini = corpo.lastIndexOf("<", m.index);
      const tag = /^<(\w+)/.exec(corpo.slice(ini))[1];
      let depth = 0, fim = ini;
      const tr = new RegExp(`<${tag}\\b|</${tag}>`, "g");
      tr.lastIndex = ini;
      let t;
      while ((t = tr.exec(corpo))) {
        if (t[0].startsWith("</")) depth--; else depth++;
        if (depth === 0) { fim = t.index + t[0].length; break; }
      }
      achou++;
      if (/T\.(positive|negative|accent)\b/.test(corpo.slice(ini, fim))) viol++;
    }
  }
  ok("caixas bgBase encontradas (>= 1)", achou >= 1);
  ok("nenhuma caixa bgBase contém T.positive/T.negative/T.accent", viol === 0);
}

// --- pós-teste local (correção 1): kicker neutro sem número das ações ------
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  ok("kicker so-acoes condicionado a kickerResultadoSoAcoes(r), senão RESULTADO DA ESTRUTURA",
    /kickerResultadoSoAcoes\(r\)\s*\?\s*cp\.estruturaResultadoSoAcoesRotulo\s*:\s*cp\.estruturaResultadoRotulo/.test(card));
}

// --- pós-teste local (correção 2): rótulo "hoje" não vaza do card ----------
{
  const regua = limpo(functionBody("ReguaFaixa"));
  ok("rótulo hoje da régua encosta à esquerda/direita nas pontas (sem translate -50% fixo)",
    /posRegua\(hoje, dom\) < 30 \? \{ left: 0 \}/.test(regua) && /posRegua\(hoje, dom\) > 70 \? \{ right: 0 \}/.test(regua));
}

// --- pós-teste local (correção 3): link do callout vencida sem linha em branco ---
// O alvo de toque de 44px é mantido; a folga vertical do texto centralizado é
// absorvida por margem negativa SP[3], então o vão visível segue SP[2] (gap).
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  ok("link Ver histórico compensa o minHeight 44 com margin -SP[3]",
    /cp\.estruturaVerHistorico[\s\S]{0,10}/.test(card) && /flexBasis: "100%", textAlign: "left", margin: `-\$\{SP\[3\]\}px 0`/.test(card));
}

// --- pós-teste local (correção 4): % do capital com vírgula pt-BR ----------
// O card LEGADO mantém o ponto decimal (fora de escopo desta correção).
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  ok("% do capital do card novo usa vírgula", /pctCap\.toFixed\(1\)\.replace\("\.", ","\)/.test(card) && !/\{pctCap\.toFixed\(1\)\}%/.test(card));
}

// --- pós-teste local (correção 5): zero exato neutro, sem sinal ------------
// numDe/corDe do card novo tratam zero à parte; moneySigned global intocado.
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  ok("numDe/corDe usam sinalResultado (zero neutro)", /const corDe[^\n]*sinalResultado\(v\) === "zero"[^\n]*T\.textMuted/.test(card) && /const numDe[^\n]*sinalResultado\(v\) === "zero"/.test(card));
  ok("total do resultado passa por numDe (não moneySigned direto)", /numDe\(r\.total\)/.test(card) && !/moneySigned\(r\.total\)/.test(card));
  ok("moneySigned global mantém '+R$ ' para n >= 0", /const moneySigned = \(n\) => .*"\+R\$ "/.test(src));
}

// --- ctx --------------------------------------------------------------------
ok("ctx.escopoSeq = escopoOpcoes", /escopoSeq: escopoOpcoes/.test(src));
const gh = /goHistoricoOperacoes:\s*\(\)\s*=>\s*\{([^}]*)\}/.exec(src);
ok("goHistoricoOperacoes chama setPerfilView/setTab/setCarteiraView", !!gh && /setPerfilView\(/.test(gh[1]) && /setTab\(/.test(gh[1]) && /setCarteiraView\("historico"\)/.test(gh[1]));
ok("declara setPerfilView/setTab/setCarteiraView", /\[\s*\w+\s*,\s*setPerfilView\s*\]\s*=\s*useState/.test(src) && /\[\s*\w+\s*,\s*setTab\s*\]\s*=\s*useState/.test(src) && /\[\s*\w+\s*,\s*setCarteiraView\s*\]\s*=\s*useState/.test(src));
ok("render condicional carteiraView === 'historico'", /carteiraView\s*===\s*["']historico["']/.test(src));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
