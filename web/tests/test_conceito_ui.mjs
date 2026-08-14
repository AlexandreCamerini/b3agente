// Camada de entendimento (Fase 2) — a explicação do `gatilho` na UI.
//
// Os contratos que estes guardiões travam:
//
//  1. DUAS VIAS. Proativa na estreia, permanente em um toque depois. A
//     primeira vez é empurrão, não a única porta.
//  2. A PROATIVA ABRE UMA VEZ, NUMA INSTÂNCIA SÓ. O AtivoCard renderiza por
//     ticker e a watchlist padrão tem 6: os seis montam juntos, todos leem
//     "ainda não viu". Sem eleição, ou abre seis vezes ou uma corrida decide.
//     A revisão sênior pediu amarrar isso ao card EXPANDIDO — descobrimos em
//     execução que `expanded` só liga depois de `A.analyze`, que exige modelo
//     de IA configurado e CUSTA DINHEIRO: a via proativa ficaria inalcançável
//     justamente para o iniciante absoluto que ela existe para atender. O
//     mecanismo virou ELEIÇÃO DE INSTÂNCIA (`_proativoDono`), que preserva a
//     garantia sem o pedágio. Medido ao vivo: 5 afordâncias, 1 folha.
//     Não volte a amarrar em `expanded`.
//  3. OPERADOR SEM CAMADA PROATIVA. Decisão fechada da spec.
//  4. A FOLHA ADIA, NÃO QUEIMA. Sendo one-shot por conceito para sempre, ela
//     não pode abrir sob outro overlay — ninguém leria, e não há segunda vez.
//
// Roda sem build: `node web/tests/test_conceito_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------------------ a folha
// Asserções sobre o que NÃO pode mudar (o contrato), não sobre a assinatura
// literal: regex sobre fonte quebra quando o código melhora e passa quando ele
// regride. Este arquivo já deu esse problema duas vezes.
ok("ConceitoSheet existe e busca o conceito ANCORADO (dados do card no corpo)",
   /function ConceitoSheet\(/.test(app) && /store\.conceito\(cid, \{ dados \}\)/.test(app));
ok("a folha abre SOBRE o card (não empurra o fluxo vertical da lista)",
   /position: "fixed", inset: 0, zIndex: 75/.test(app)
   && /alignItems: "flex-end"/.test(app));
ok("ordem dos blocos: o que o app NÃO faz vem primeiro",
   /\["naoAcontece", "O QUE O APP NÃO FAZ"\],\s*\n\s*\["oQueE", "O QUE É"\],\s*\n\s*\["oQueAcontece", "O QUE ACONTECE"\]/.test(app));
ok("bloco vazio não vira seção vazia (campo ausente sumiu no backend)",
   /\(c\[chave\] \|\| \[\]\)\.length > 0/.test(app));
ok("falha de rede na folha não quebra o card",
   /Não consegui carregar a explicação agora\. O card continua válido\./.test(app));

// --------------------------------------------------------------- duas vias
// A via permanente é TOQUE no termo SUBLINHADO (padrão Duolingo) — o "?" de
// 18px repetido era ruído, e o toque longo caiu no teste ao vivo (sem
// indicação + seleção de texto). O contrato: setor declarado, conceito
// primário do REGISTRO do backend (didatica.setores), indicação no próprio
// termo. Os detalhes do toque têm guardião próprio: test_setor_toque.mjs.
ok("via PERMANENTE: tocar o setor abre o conceito ancorado (SetorAlvo)",
   /function SetorAlvo\(\{ setorId, dados, rotulo, A, didatica/.test(app)
   && /A\.abrirSetor\(setorId, cid, dados, origem\)/.test(app));
ok("o conceito do setor vem do REGISTRO do backend, nunca de dict do front",
   /didatica\.setores\) \? didatica\.setores\[setorId\] : null/.test(app));
ok("nenhum ConceitoDot sobrou no card (a indicação é o sublinhado pontilhado)",
   !/ConceitoDot/.test(app) && /const SUBLINHADO = /.test(app));
ok("via PROATIVA: abre uma vez e marca como visto",
   /A\.openConceito\("gatilho", dados\);\s*\n\s*A\.marcarConceitoVisto\("gatilho"\);/.test(app));
ok("proativa só dispara se ainda NÃO foi vista",
   /\(vistos \|\| \[\]\)\.includes\("gatilho"\)/.test(app));
ok("proativa é guardada por ref (não reabre a cada render)",
   /proativoFeitoRef/.test(app));

// ------------------------- a via proativa abre UMA vez, numa instância só
// 6 cards montam juntos e todos leem "ainda não viu". Sem eleição, ou abre
// seis vezes ou uma corrida decide qual abre.
ok("existe eleição de instância única (o 1º badge vira dono)",
   /const _proativoDono = \{ t: null \};/.test(app)
   && /if \(_proativoDono\.t && _proativoDono\.t !== t\) return;/.test(app));
ok("a eleição é liberada ao trocar de conta", /_proativoDono\.t = null;/.test(app));
ok("o Radar fica fora da via proativa (vitrine, não lugar de aprender)",
   /proativo=\{contexto !== "radar" && overlayLivre\}/.test(app));
ok("a folha ADIA enquanto houver outro overlay (não queima a estreia)",
   /overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto/.test(app));
ok("a folha fica ACIMA de todos os outros overlays (zIndex 86 > portão 85)",
   /zIndex: 86, background: T\.scrim, display: "flex", alignItems: "flex-end"/.test(app));

// ------------------------------------------------ acessibilidade do gesto
// VoiceOver e teclado não têm "segurar 600ms" — cada setor carrega um botão
// só-para-leitor que abre a mesma folha. O gesto é a via visual, nunca a única.
ok("cada setor tem caminho acessível equivalente (botão sr-only)",
   /aria-label=\{"O que é " \+ rotulo \+ "\?"\} style=\{SR_ONLY\}/.test(app)
   && /clipPath: "inset\(50%\)"/.test(app));

// ------------------------------------ Fase 3: cobertura e encadeamento
// O inventário conta 18 afirmações no card. O gesto é UM só; a cobertura vem
// dos SETORES declarados — cada bloco que afirma número tem o seu.
for (const [setor, onde] of [["barra", "carimbo da hora no badge"], ["analise", "linha de chips"],
                             ["fundamento", "chip do fundamento"], ["r", "linha R:R"]]) {
  ok(`setor '${setor}' declarado (${onde})`,
     new RegExp('setorId="' + setor + '"').test(app));
}
// `risco` e `alvo` dividem a régua: o setor segue o número EXIBIDO.
ok("a régua declara o setor conforme o número exibido (risco vs alvo)",
   /setorId=\{pos\.stop != null \? "risco" : "alvo"\}/.test(app));
// UM bundle para todos os dots. Bundles parciais por dot quebravam o
// encadeamento: seguir da confluência para o stop entregava o conceito sem
// `stop` nem `precoAtual`, e a pessoa recebia texto de manual — a ancoragem
// falhando justamente no caminho construído para ela.
ok("existe um bundle ÚNICO de dados do card, usado por todos os dots",
   /const dadosDoCard = \{/.test(app)
   && (app.match(/dados=\{dadosDoCard\}/g) || []).length >= 4);
ok("'veja também' encadeia mantendo os mesmos dados",
   /onTrocar=\{A\.trocarConceito\}/.test(app)
   && /trocarConceito: \(cid\) => setConceitoAberto\(\(c\) => \(c \? \{ \.\.\.c, cid/.test(app));
ok("a cadeia tem VOLTA (trilha), não só 'fechar tudo'",
   /voltarConceito: \(\) => setConceitoAberto/.test(app)
   && /‹ voltar/.test(app));
ok("a régua com só alvo não explica um stop que não está no card",
   /setorId=\{pos\.stop != null \? "risco" : "alvo"\}/.test(app));
ok("'veja também' só mostra conceito que o catálogo conhece",
   /\(didatica\.conceitos \|\| \[\]\)\.find\(\(x\) => x && x\.id === vid\)/.test(app));

// ------------------------------- o push não pode travar a estreia didática
// O universo do push é watchlist ∪ POSIÇÕES, mas a tela lista só a watchlist.
// Reservar o dono antes de confirmar que o card existe prenderia a eleição num
// ticker que nunca monta — e NENHUM card abriria a folha até o logout.
ok("o toque no push garante o ativo na watchlist antes de navegar",
   /if \(!wl\.includes\(t\)\) await store\.putWatchlist\(\[\.\.\.wl, t\]\)/.test(app));
ok("a reserva da eleição só ocorre depois de confirmar que o card existe",
   /if \(!el\) return;\s*\n\s*reservarDonoProativo\(t\);/.test(app));

// ----------------------------------- a afordância sobrevive ao pregão fechado
// `timing.avaliar` monta entrada/stop ANTES de decidir o estado: fora do
// pregão o `sem_dado` volta COM os números do plano. Amarrar a afordância ao
// estado vivo apagava a explicação das 18h às 10h.
ok("permanente exige só o PLANO; proativa exige estado vivo",
   /const temPlano = !!r && r\.entrada != null;/.test(app)
   && /const didaticaOk = !!\(didatica && didatica\.ligada\) && temPlano;/.test(app)
   && /if \(!didaticaOk \|\| !estadoVivo \|\|/.test(app));

// ------------------------------------------- Fase 0b: o push tem DESTINO
// qa/47 (Fase 2, 2026-08-14): assinatura ganhou `kind` (analytics de
// notification_tapped) — guardião atualizado, comportamento de navegação
// intacto (as 2 asserções seguintes continuam cobrindo isso).
ok("toque no push leva ao ativo (aba + scroll até o card)",
   /notify\.onPushTap\(async \(t, kind\) => \{/.test(app)
   && /setTab\("mercado"\)/.test(app)
   && /document\.getElementById\("ativo-" \+ t\)/.test(app));
ok("o card do ativo tem id para o scroll", /id=\{"ativo-" \+ t\}/.test(app));

// --------------------------------------- Fase 0b: o interruptor é OPT-IN
// `row` trata ausente como LIGADO (opt-out) — certo para avisos da SUA
// carteira. O aviso de mercado é a única classe disparada por evento externo:
// nasce desligada, e por isso tem variante própria.
ok("a classe `gatilho` usa a variante OPT-IN do interruptor",
   /const rowOptIn = \(key, label, desc\)/.test(app)
   && /on=\{nf\.enabled && nf\[key\] === true\}/.test(app)
   && /rowOptIn\("gatilho"/.test(app));
ok("o texto do interruptor declara o atraso, o teto e que não é ordem",
   /~15 min de atraso do feed e nunca é ordem/.test(app));

// ------------------------------------------------- isolamento do Operador
ok("Operador não recebe camada proativa",
   /if \(!proativo \|\| operador \|\| proativoFeitoRef\.current\) return;/.test(app));

// -------------------------------------------------------------- honestidade
ok("sem condição a explicar (sem_dado / fora do pregão / barra de ontem) não há afordância",
   /\["armado", "gatilho", "esticado"\]\.includes\(r\.estado\)/.test(app)
   && /&& !r\.foraDoPregao && !r\.barraDeOutroDia/.test(app));
ok("os números que a folha recebe são os do card, não recalculados",
   /ticker: t, entrada: r\.entrada, stop: r\.stop,/.test(app));

// ---------------------------------------------- chave de desligamento remota
ok("catálogo vem do backend e a camada some quando `ligada` é false",
   /store\.conceitos\(modoApp\)/.test(app)
   && /!!\(didatica && didatica\.ligada\)/.test(app));
ok("falha ao buscar o catálogo desliga a camada, não quebra o app",
   /setDidatica\(\{ ligada: false, conceitos: \[\] \}\)/.test(app));

// ------------------------------------------------------------- persistência
ok("marcarConceitoVisto persiste nos dois lados (estado local + store)",
   /store\.putConfig\(\{ conceitosVistos: \[cid\] \}\)/.test(app));
ok("marcar visto é idempotente (não duplica no estado local)",
   /if \(atual\.includes\(cid\)\) return d;/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
