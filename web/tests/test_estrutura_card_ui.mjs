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
  // Fase 46 (D-15, 2026-09-30): o chip de estratégia subiu para a linha de meta do card fechado
  // (CartaoPosicao); mesma regra: sem nomeTexto cai no texto genérico, nunca "null".
  const cf = limpo(functionBody("CartaoPosicao"));
  // 46-UAT (2026-10-01, G-04): a meta virou chips; chipsMetaV6 (estruturaCard.js) cai em chip_estrategia_generica
  // sem nomeTexto e CartaoPosicao monta <ChipsMetaV6 (nunca "null").
  const ecSrc = readFileSync(new URL("../src/estruturaCard.js", import.meta.url), "utf8");
  ok("chip (code review WR-06): nome sem nomeTexto cai no genérico (agora na meta de CartaoPosicao)", /chip_estrategia_generica/.test(ecSrc) && /<ChipsMetaV6/.test(cf) && !/e\.nome && e\.nomeTexto/.test(c));
  ok("régua (code review WR-06): aria-label com fallback quando nomeTexto é nulo", /cp\.estruturaFaixaAria\(e\.nomeTexto \|\| cp\.estruturaGrupoAria,/.test(r));
}

// --- W-001: R:R do card atual -----------------------------------------------
// Fase 45 (code review WR-05): reversão deliberada — o gate agora recebe o preço
// (mostraRR(p, cur)) e o legado não renderiza mais "R:R atual —".
// Fase 46 (D-15, 2026-09-30): o R:R vem pronto do backend (leitura.rr) na FaceAcao; só aparece quando != null, nunca "—".
ok("R:R atual na FaceAcao: só com leitura.rr != null, sem '—' (substitui o gate mostraRR do card legado)", /L\.rr != null && linha\("rr"/.test(limpo(functionBody("FaceAcao"))) && !/rr == null \? "—" : rr\.toFixed/.test(src));

// --- CarteiraScreen ---------------------------------------------------------
const cart = limpo(functionBody("CarteiraScreen"));
ok("CarteiraScreen usa estadoLeitura", /estadoLeitura\(/.test(cart));
// Fase 46 (D-15, 2026-09-30): CardPosicaoEstruturada agora é a face Opções montada por CartaoPosicao, só com
// leitura estruturada (e = null fora dela) e com pernas (nPernas > 0).
const cartaoFace = limpo(functionBody("CartaoPosicao"));
ok("CardPosicaoEstruturada só em estruturada (face Opções de CartaoPosicao)", /const e = modoLeitura === "estruturada" && leituraEstrutura \?/.test(cartaoFace) && /nPernas > 0 \?/.test(cartaoFace) && /<CardPosicaoEstruturada/.test(cartaoFace) && !/<CardPosicaoEstruturada/.test(cart));
// Fase 46 (D-15, 2026-09-30): o aviso "Posição sem stop definido" virou a linha de estado do card fechado
// (estado_sem_plano / estado_falta_stop, vindos de estadoPrincipalV6); o front não o recompõe.
ok("aviso 'sem stop' agora é estado do backend (estado_sem_plano via estadoPrincipalV6), sem texto fixo no front", /estado_sem_plano/.test(readFileSync(join(here, "..", "src", "estruturaCard.js"), "utf8")) && !/Posição sem stop definido/.test(src));
// Fase 46 (D-15, 2026-09-30): a linha role=status (lendo/indisponivel) saiu do
// ramo simples de CarteiraScreen e foi para o card fechado v6 (CartaoPosicao),
// que a mostra para toda posição com pernas; mesma asserção, novo endereço.
const cartao46 = limpo(functionBody("CartaoPosicao"));
ok("linha role=status 'lendo' (agora em CartaoPosicao)", /role="status"/.test(cartao46) && /"lendo"/.test(cartao46));
ok("linha role=status 'indisponivel' (agora em CartaoPosicao)", /"indisponivel"/.test(cartao46));
ok("CarteiraScreen renderiza CartaoPosicao (Fase 46)", /<CartaoPosicao/.test(cart));
// Fase 46 (D-15, 2026-09-30): a régua legada "POSIÇÃO NO RISCO" saiu de CarteiraScreen; a régua stop/alvo é ReguaPlano no card fechado.
ok("régua stop/alvo da Carteira é ReguaPlano (fechado v6); PlanRuler legado fora de CarteiraScreen", /<ReguaPlano /.test(cartaoFace) && !/POSIÇÃO NO RISCO/.test(cart));

// --- CardPosicaoEstruturada -------------------------------------------------
const cardE = limpo(functionBody("CardPosicaoEstruturada"));
ok("CardPosicaoEstruturada existe", cardE.length > 0);
ok("D-09: sem 'Compras desta posição'", !/Compras desta posição/.test(cardE));
ok("D-07: sem PlanRuler", !/PlanRuler/.test(cardE));
ok("Encerrar navega via goOpcoes(oportunidades, abrirTicker)", /goOpcoes\("oportunidades", \{ abrirTicker: p\.t \}\)/.test(cardE));
ok("aria-describedby presente", /aria-describedby/.test(cardE));
// Fase 46 (D-15, 2026-09-30): o grupo de chips (role=group) subiu para o card fechado; o grupo desta face é o SeletorFace.
ok('role="group" presente (SeletorFace aria-pressed)', /role="group"/.test(limpo(functionBody("SeletorFace"))) && /aria-pressed=\{sel\}/.test(limpo(functionBody("SeletorFace"))));
ok("não executa nada (store./buy/sell/fecharLastreada)", !/store\./.test(cardE) && !/\.buy\(/.test(cardE) && !/\.sell\(/.test(cardE) && !/fecharLastreada/.test(cardE));
ok("sem dangerouslySetInnerHTML", !/dangerouslySetInnerHTML/.test(cardE));
ok("sem hex literal", !/#[0-9a-fA-F]{3,6}\b/.test(cardE));
ok("pesos só 400/700", !/fontWeight:\s*(600|800)/.test(cardE));
// Fase 46 (D-15, 2026-09-30): a face Opções adota a tipografia v6 (TIPO_CARD 20/14/12); TAM_TOTAL_ESTRUTURA saiu do card.
ok("fontSize só TIPO_CARD.* (tipografia v6)", (cardE.match(/fontSize:\s*[^,}]+/g) || []).every((f) => /fontSize:\s*TIPO_CARD\.(titulo|corpo|rotulo)/.test(f)));
ok("caixas bgBase levam background como primeira chave", !/backgroundColor/.test(cardE));
ok("TAM_TOTAL_ESTRUTURA = 24", /^const TAM_TOTAL_ESTRUTURA = 24;/m.test(src));
// Reversão deliberada (45-04): a âncora de 45-03 foi consumida; agora exige a régua no lugar.
// Fase 46 (D-15, 2026-09-30): a faixa no vencimento é desenhada por FaixaVencimento no card fechado (46-05); a
// ReguaFaixa da 45 permanece definida (guardiões de régua/ritmo a medem) mas não é mais
// renderizada na face Opções — candidata a remoção quando o ritmo SP deixar de citá-la.
ok("âncora do 45-04 consumida; ReguaFaixa segue definida e a faixa v6 é FaixaVencimento", !/45-04: régua de faixa \+ bloco de limites/.test(src) && !!functionBody("ReguaFaixa") && /<FaixaVencimento /.test(limpo(functionBody("CartaoPosicao"))));

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
  // Fase 46 (D-15, 2026-09-30): os badges de trava saíram da face Opções (estado_travadas_* no card fechado);
  // se algum voltar, mantém o contorno.
  ok("todo <TravaPill dentro do card estruturado tem contorno (se houver)", dentro.every((m) => /\bcontorno\b/.test(m[0])));
  ok("nenhum <TravaPill fora do card estruturado tem contorno", fora.length >= 1 && fora.every((m) => !/\bcontorno\b/.test(m[0])));
}
for (const [nome, corpo] of [["CardPosicaoEstruturada", cardE], ["ReguaFaixa", reguaE]]) {
  // Fase 46 (D-15, 2026-09-30): CardPosicaoEstruturada usa TIPO_CARD.*; ReguaFaixa (legada) mantém px literais.
  ok(`${nome}: fontSize sempre string px permitida`, (corpo.match(/fontSize:\s*[^,}]+/g) || []).every((f) => /fontSize:\s*("(10\.5|11\.5|13|16)px"|TAM_TOTAL_ESTRUTURA \+ "px"|TIPO_CARD\.(titulo|corpo|rotulo))/.test(f)) && !/fontSize:\s*\d/.test(corpo));
  ok(`${nome}: sem fontWeight 600/800`, !/fontWeight:\s*(600|800)/.test(corpo));
  ok(`${nome}: sem hex literal`, !/#[0-9a-fA-F]{3,6}\b/.test(corpo));
  ok(`${nome}: sem linear-gradient`, !/linear-gradient/.test(corpo));
  ok(`${nome}: sem backgroundColor`, !/backgroundColor/.test(corpo));
  ok(`${nome}: sem innerHTML`, !/dangerouslySetInnerHTML/.test(corpo));
}
ok("ReguaFaixa: role=img e cp.estruturaFaixaAria", reguaE.length > 0 && /role="img"/.test(reguaE) && /cp\.estruturaFaixaAria\(/.test(reguaE));
ok("ReguaFaixa usa dominioRegua/posRegua", /dominioRegua\(/.test(reguaE) && /posRegua\(/.test(reguaE));
// Fase 46 (D-15, 2026-09-30): R:R e aviso sem stop saíram da face Opções: R:R é leitura.rr do backend na FaceAcao
// (nunca recalculado no front) e o aviso é o estado do card fechado.
ok("R:R fora da face Opções; no front não há valorRR/mostraRR em FaceAcao", !/R:R/.test(cardE) && !/valorRR\(|mostraRR\(/.test(limpo(functionBody("FaceAcao"))));
ok('sem texto fixo "Posição sem stop definido" na face Opções', !/Posição sem stop definido/.test(cardE));
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
  // Fase 46 (D-15, 2026-09-30): o resultado total subiu para o card fechado: sem total do motor mostra "Parcial"
  // (nunca soma parcial como se fosse total).
  const cf = limpo(functionBody("CartaoPosicao"));
  // 46-UAT (2026-10-01, G-01): sem total o card mostra "—" + chip "total suspenso" (res.cabecalho.suspenso),
  // nunca soma parcial nem a palavra "Parcial"; linhasResultadoV6 lê resultado.total.
  const ecSrc2 = readFileSync(new URL("../src/estruturaCard.js", import.meta.url), "utf8");
  ok("resultado total do card fechado: r.total != null senão 'Parcial'", /res\.cabecalho\.suspenso/.test(cf) && /"chip_total_suspenso"/.test(cf) && !/Parcial/.test(cf) && /numOk\(r\.total\)/.test(ecSrc2) && !/<ReguaFaixa/.test(card));
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
  // Fase 46 (D-15, 2026-09-30): o link saiu do callout (que subiu ao card fechado) e vive na face Opções como
  // botão próprio de 44 px, sem caixa — não há mais folga a compensar.
  ok("link Ver histórico (estado encerrada) na face Opções, alvo 44 px, ctx.goHistoricoOperacoes",
    /tomDoEstado\(e\.estado\) === "encerrada"/.test(card) && /onClick=\{ctx\.goHistoricoOperacoes\}/.test(card) && /cp\.estruturaVerHistorico/.test(card) && /minHeight: 44, textAlign: "left"/.test(card));
}

// --- pós-teste local (correção 4): % do capital com vírgula pt-BR ----------
// O card LEGADO mantém o ponto decimal (fora de escopo desta correção).
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  // Fase 46 (D-15, 2026-09-30): o "% do capital" vive na FaceAcao (helper pctDoCapital); mesma regra da vírgula.
  const fa = limpo(functionBody("FaceAcao"));
  ok("% do capital (FaceAcao) usa vírgula", /pctCap\.toFixed\(1\)\.replace\("\.", ","\)/.test(fa) && !/\{pctCap\.toFixed\(1\)\}%/.test(fa));
}

// --- pós-teste local (correção 5): zero exato neutro, sem sinal ------------
// numDe/corDe do card novo tratam zero à parte; moneySigned global intocado.
{
  const card = limpo(functionBody("CardPosicaoEstruturada"));
  ok("numDe/corDe usam sinalResultado (zero neutro)", /const corDe[^\n]*sinalResultado\(v\) === "zero"[^\n]*T\.textMuted/.test(card) && /const numDe[^\n]*sinalResultado\(v\) === "zero"/.test(card));
  // Fase 46 (D-15, 2026-09-30): o total do resultado é desenhado em CartaoPosicao (numDe local).
  const cf2 = limpo(functionBody("CartaoPosicao"));
  // 46-UAT (2026-10-01, G-05): o total passa por rsSinalNbsp (zero neutro, NBSP), nunca moneySigned/money.
  ok("total do resultado passa por numDe (não moneySigned direto)", /rsSinalNbsp\(/.test(cf2) && !/moneySigned\(/.test(cf2));
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
