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
ok("hook usa executarComTeto(..., 3)", /executarComTeto\(/.test(hook) && /,\s*3\)/.test(hook));
ok("hook não tem polling (setInterval/setTimeout)", !/setInterval|setTimeout/.test(hook));
ok("hook: seqRef é useRef(0)", /seqRef\s*=\s*useRef\(0\)/.test(hook));
ok("hook: seqRef nunca zerado", !/seqRef\.current\s*=\s*(0|\{\})/.test(hook) && !/seqRef\.current\s*=\s*(0|\{\})/.test(src));
ok("hook: troca de escopo invalida por incremento", /corteRef\.current\s*=\s*\+\+seqRef\.current/.test(hook));
ok("hook: resposta só aceita se meu > corteRef e meu === ultimoRef", /meu === ultimoRef\.current\[t\]/.test(hook) && /meu > corteRef\.current/.test(hook));
ok("hook: efeito de troca de escopo depende de escopoSeq", /\[escopoSeq\]\)/.test(hook));

// --- W-001: R:R do card atual -----------------------------------------------
ok("card atual: R:R atual sob mostraRR(p) &&", /mostraRR\(p\) && \(<span>R:R atual/.test(src));

// --- CarteiraScreen ---------------------------------------------------------
const cart = limpo(functionBody("CarteiraScreen"));
ok("CarteiraScreen usa estadoLeitura", /estadoLeitura\(/.test(cart));
ok("CardPosicaoEstruturada só em estruturada", /modoLeitura === "estruturada" \? \(\s*<CardPosicaoEstruturada/.test(cart));
ok("aviso 'sem stop' do card atual guardado por mostraAvisoSemStop(", /mostraAvisoSemStop\([^)]*\) && <div[^>]*>⚠ Posição sem stop definido/.test(cart));
ok("linha role=status 'lendo'", /role="status"/.test(cart) && /"lendo"/.test(cart));
ok("linha role=status 'indisponivel'", /"indisponivel"/.test(cart));
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
ok("R:R no card só sob mostraRR(", /mostraRR\(/.test(cardE) && (cardE.match(/R:R/g) || []).length === 1 && /const rr = mostraRR\(p\)/.test(cardE));
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

// --- ctx --------------------------------------------------------------------
ok("ctx.escopoSeq = escopoOpcoes", /escopoSeq: escopoOpcoes/.test(src));
const gh = /goHistoricoOperacoes:\s*\(\)\s*=>\s*\{([^}]*)\}/.exec(src);
ok("goHistoricoOperacoes chama setPerfilView/setTab/setCarteiraView", !!gh && /setPerfilView\(/.test(gh[1]) && /setTab\(/.test(gh[1]) && /setCarteiraView\("historico"\)/.test(gh[1]));
ok("declara setPerfilView/setTab/setCarteiraView", /\[\s*\w+\s*,\s*setPerfilView\s*\]\s*=\s*useState/.test(src) && /\[\s*\w+\s*,\s*setTab\s*\]\s*=\s*useState/.test(src) && /\[\s*\w+\s*,\s*setCarteiraView\s*\]\s*=\s*useState/.test(src));
ok("render condicional carteiraView === 'historico'", /carteiraView\s*===\s*["']historico["']/.test(src));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
