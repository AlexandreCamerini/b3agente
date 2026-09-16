// Fase 30 (Plano 04, D4) — Guardião estático do bloco "as 4 melhores
// oportunidades de opções" (CuradoriaEstruturas + useCuradoria). Estendido na
// Fase 31 (Plano 04, D-04/D-05/D-07/D-08), no Quick 260915-j5l (2026-09-15),
// no Quick 260915-ndt (2026-09-15) e na Fase 32 (32-02, 2026-09-15).
//
// NOTA (2026-09-15, Fase 32, 32-02): `CuradoriaEstruturas` (e o mapa interno
// `ROTULO_TIPO_CURADORIA`) saíram de App.jsx para
// web/src/opcoes/CuradoriaEstruturas.jsx (ADR-027 Emenda 3). As âncoras de
// DEFINIÇÃO passam a apontar para o módulo — este arquivo lê os DOIS fontes
// (App.jsx + o módulo). `useCuradoria`/`CarteiraScreen` CONTINUAM em App.jsx
// (só o componente de UI se moveu; o hook subiu para App(), ver Decisão A do
// 32-02-PLAN.md). As âncoras de USO (call site, `<CuradoriaEstruturas`)
// continuam em App.jsx até o Plano 32-03, que move o bloco de tela.
//
// NOTA (2026-09-15, Fase 32, 32-03): o bloco cross-carteira mudou de TELA —
// de `CarteiraScreen` (`App.jsx`) para o topo da sub-aba Setups
// (`OpcoesScreen.jsx`, irmão de `OportunidadesOpcoes`, D-04/D-07). As
// âncoras de USO passam a apontar para lá; `App.jsx` não renderiza mais
// `<CuradoriaEstruturas` — Posições passa a ter uma linha de chamada
// (`LinhaChamadaOpcoes`) no lugar, contagem lida de `ctx.curadoria.top.length`
// (D-03). `CarteiraScreen` deixou de DESESTRUTURAR `ctx.curadoria` (não
// tinha mais consumidor local depois da migração) — passa o objeto inteiro
// como prop para `LinhaChamadaOpcoes`.
//
// Este arquivo tranca a CLASSE de erros que a Fase 30/31/32/quick pode
// reintroduzir, não a instância — cada bloco abaixo defende uma regra que o
// autor de uma edição futura não tem por que conhecer de cor:
//
//   1. as chaves `curadoria*` de copy existem nos dois modos, string
//      literal, sem palavra de enriquecimento/promessa de lucro (princípios
//      6/8 do CLAUDE.md). NOTA (Fase 31/D-04): eram 11 na Fase 30 (só venda
//      coberta); 18 na Fase 31 (as 4 estruturas do motor). NOTA (Quick
//      260915-j5l, 2026-09-15): 25 — o clique passou a abrir uma
//      confirmação INLINE por card (em vez de rolar para o acordeão de UMA
//      posição), ganhando `curadoriaExecutarCta`, `curadoriaExecutando`,
//      `curadoriaFechar`, `curadoriaExecutada`, `curadoriaLiquidezConsentir`,
//      `curadoriaEstudoNaoExecuta` e `curadoriaVerPosicao`. NOTA (Quick
//      260915-ndt, 2026-09-15): agora são 26 — `curadoriaPremioRotulo` nova,
//      corrige o painel inline usando o rótulo da RAZÃO ao lado do PRÊMIO EM
//      REAIS (ver itens 23-25 abaixo). Reversão deliberada, não apagamento —
//      mesmo guardrail do CLAUDE.md ("guardiões de teste não se apagam,
//      reversão deliberada atualiza o guardião com nota");
//   2. `item.manchete` é renderizado VERBATIM — guardrail CVM (CLAUDE.md):
//      nenhuma composição de frase a partir de strike/premioTotal, nenhum
//      truncamento;
//   3. a ordem de `top` é do motor — nenhum sort/reverse/comparação de
//      `razao` no componente (T-30-18);
//   4. `narrar()` só sai por toque explícito — nunca dentro do useEffect de
//      busca (D6/T-30-21): buscar narração no mount gastaria cota de quem
//      só abriu a aba;
//   5. o render dos itens lê `top`, nunca `narrativa.estruturas` — a lista
//      não muda quando o texto da IA chega (T-30-20);
//   6. o bloco aparece exatamente uma vez, dentro do mesmo
//      `data.positions.length > 0 &&` da tira irmã (D4);
//   7. toda chamada de rede do hook é best-effort (`.catch(` no próprio
//      encadeamento) — T-30-21;
//   8. nenhuma frase de copy da curadoria promete lucro/garante resultado;
//   9. (Fase 31, D-04) a chave de render é `item.idCandidato` — collar não
//      tem `contractSymbol` único, e `key={item.contractSymbol}` colidiria
//      com `null`;
//   10. (Fase 31, D-04) existe rótulo de tipo para os 4 tipos do motor,
//      resolvido por um mapa tipo→chave de copy, nunca hardcoded na
//      manchete;
//   11. (Fase 31, D-02/D-03) a linha de resumo da varredura lê
//      `meta.candidatosPorTipo`;
//   12. (Fase 31, D-07/D-08) existe exatamente UM `<PayoffChart` renderizado
//      no bloco — uma curva, nunca overlay;
//   13. (Fase 31, D-05) nenhuma copy da curadoria convida a ligar o flag de
//      opção a descoberto — o gate não é substituído por marketing;
//   14. (Quick 260915-j5l) o card NÃO chama mais `onAbrir(item.ticker)` no
//      `onClick` principal — era o bug: o clique descartava o candidato
//      inteiro (idCandidato/contractSymbol/pernasContratos/tipo) e abria o
//      acordeão genérico de UMA posição, sempre venda coberta;
//   15. (Quick 260915-j5l) `onExecutar` recebe o ITEM inteiro
//      (`onExecutar(item`), nunca só o ticker;
//   16. (Quick 260915-j5l) o despacho por tipo mora em
//      `web/src/opcoes/executarCandidato.js`, importado por App.jsx —
//      `CuradoriaEstruturas` não contém nenhum literal de rota
//      (`/api/options/`): rota escrita na UI seria a segunda cópia do
//      contrato;
//   17. (Quick 260915-j5l) o painel inline lê `item.estrutura`/
//      `item.premioTotal` e não chama `store.`/`api.` dentro do componente
//      (sem rede nova no clique — T-J5L-05);
//   18. (Quick 260915-j5l) `porLote` do painel é null-safe
//      (`typeof v === "number"`) — `null * 100 === 0` inventaria "perda
//      máxima R$ 0,00" (princípio 4 do CLAUDE.md, "null nunca 0.0");
//   19. (Quick 260915-j5l) a caixa de erro do painel usa `T.warn` e nunca
//      `T.negative` — vermelho é de P&L, precedente do `LimiteAtingido` da
//      Fase 25;
//   20. (Quick 260915-j5l) nenhum `window.confirm(` dentro de
//      `CuradoriaEstruturas` — a confirmação é inline (decisão do Alex,
//      2026-09-15);
//   21. (Quick 260915-j5l) `aceitaLiquidezDificil` nunca é enviado sem o
//      consentimento do card — o identificador só aparece no componente
//      junto do estado de consentimento (`liquidezOk`), nunca como literal
//      `true` solto (T-J5L-04);
//   22. (Quick 260915-j5l) o botão de executar mora dentro de um ramo
//      guardado por `operador` — Modo Estudo sem CTA (defesa em UI
//      espelhando o 403 do servidor, T-14-23).
//   23. (Quick 260915-ndt) o rótulo ao lado de `money(item.premioTotal)` no
//      painel inline é `cp.curadoriaPremioRotulo`, nunca
//      `curadoriaRazaoRotulo` — o defeito era mostrar "prêmio / perda
//      máxima  R$ 847,00" com o número do prêmio sob o rótulo da razão.
//   24. (Quick 260915-ndt) `cp.curadoriaRazaoRotulo` aparece EXATAMENTE 1x
//      em `CuradoriaEstruturas` — só no card, ao lado de `item.razao`; dois
//      usos é a regressão que esta quick fecha.
//   25. (Quick 260915-ndt) `curadoriaPremioRotulo` !== `curadoriaRazaoRotulo`
//      nos dois modos — rótulos iguais para números diferentes é o defeito.
//   26. (Fase 32, 32-02, Decisão A) o efeito de busca de useCuradoria tem
//      dependência `[ativo, nonce]` (não mais `[]`) e uma guarda
//      `if (!ativo) return` ANTES de `store.opcoesCuradoria(` — sem essa
//      guarda o hook buscaria em TODO boot do app (T-32-03, consumo
//      auto-infligido de mydata_budget).
//   27. (Fase 32, 32-02, Decisão A) `useCuradoria(` aparece exatamente 2x em
//      App.jsx (a definição do hook + a única chamada, em App()) — trava
//      "uma fonte, duas leituras" (D-03): duas instâncias divergiriam por
//      timing, exatamente o que D-03 proíbe.
//
// Padrão "static source inspection" da casa (mesmo de
// test_carteira_opcoes_tira.mjs, test_opcoes_proposta_ui.mjs): readFileSync
// de App.jsx + do módulo + import de COPY, sem build e sem DOM. Roda
// isolado: `node web/tests/test_curadoria_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const modulo = readFileSync(join(here, "..", "src", "opcoes", "CuradoriaEstruturas.jsx"), "utf8");
// Fase 32 (32-03): o call site (`<CuradoriaEstruturas`) mudou de tela —
// precisa ler OpcoesScreen.jsx para as âncoras de USO abaixo. Declarado no
// topo (não dentro de uma seção numerada) porque a seção (27) — física e
// numericamente ANTERIOR à seção (6) neste arquivo, que cresceu por
// inserção histórica fora de ordem — também precisa dele.
const telaOpcoes = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");
const telaOpcoesSemComentario = telaOpcoes.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesma higiene de
// test_carteira_opcoes_tira.mjs / test_fase5_appmode_fonte_unica.mjs: uma
// asserção que CONTA ocorrências precisa ignorar linhas `//`, senão o
// comentário explicativo do próprio componente infla a contagem.
const linhasSemComentario = app.split("\n").filter((l) => !/^\s*\/\//.test(l));
const fonteSemComentario = linhasSemComentario.join("\n");
const moduloSemComentario = modulo.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

// ---- Âncoras de função em App.jsx, na ordem esperada de inserção --------
// ATUALIZADO 2026-09-15 (Fase 32, 32-02): `OportunidadesOpcoes` e
// `CuradoriaEstruturas` saíram de App.jsx — restam PropostaDaPosicao <
// useOpcoesPropostas < useCuradoria < CarteiraScreen < HistoricoScreen.
// ATUALIZADO 2026-09-15 (Fase 32, 32-03): a DEFINIÇÃO de `useOpcoesPropostas`
// também saiu de App.jsx (para ./opcoes/useOpcoesPropostas.js) — só a
// CHAMADA sobrevive, dentro de CarteiraScreen, até o Plano 32-04. A âncora
// de função é substituída por `LinhaChamadaOpcoes` (novo componente,
// inserido entre `useCuradoria` e `CarteiraScreen`): PropostaDaPosicao <
// useCuradoria < LinhaChamadaOpcoes < CarteiraScreen < HistoricoScreen.
// ATUALIZADO 2026-09-16 (Fase 32, 32-04, deviation Rule 1): `PropostaDaPosicao`
// foi REMOVIDA de App.jsx — não é mais uma âncora válida. Restam 4:
// useCuradoria < LinhaChamadaOpcoes < CarteiraScreen < HistoricoScreen.
const iHookCur = app.indexOf("function useCuradoria");
const iLinhaChamada = app.indexOf("function LinhaChamadaOpcoes");
const iCarteira = app.indexOf("function CarteiraScreen(");
const iHistorico = app.indexOf("function HistoricoScreen(");
ok("(Fase 32/32-04) as 4 âncoras de função foram localizadas, na ordem esperada (useCuradoria < LinhaChamadaOpcoes < CarteiraScreen < HistoricoScreen)",
  iHookCur > -1 && iLinhaChamada > iHookCur && iCarteira > iLinhaChamada && iHistorico > iCarteira);
ok("(Fase 32/32-03) function useOpcoesPropostas NÃO existe mais em App.jsx (definição saiu para o módulo)",
  !/function useOpcoesPropostas/.test(fonteSemComentario));
ok("(Fase 32/32-04) function PropostaDaPosicao NÃO existe mais em App.jsx",
  !/function PropostaDaPosicao/.test(fonteSemComentario));

const fatiaHookCurComComentario = app.slice(iHookCur, iCarteira);
const fatiaCarteiraComComentario = app.slice(iCarteira, iHistorico);
const fatiaHookCur = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function useCuradoria"),
  fonteSemComentario.indexOf("function CarteiraScreen("),
);
const fatiaCarteira = fonteSemComentario.slice(
  fonteSemComentario.indexOf("function CarteiraScreen("),
  fonteSemComentario.indexOf("function HistoricoScreen("),
);

// A "fatia" do componente CuradoriaEstruturas agora É o módulo inteiro —
// substitui o antigo `app.slice(iCuradoria, iPDP)`.
const fatiaCuradoriaComComentario = modulo;
const fatiaCuradoria = moduloSemComentario;

// ---- (1) 26 chaves de copy nos dois modos, string literal -----------------
// NOTA (Fase 31, Plano 04, D-04): eram 11 na Fase 30 (só venda coberta);
// 18 na Fase 31 (4 estruturas do motor). NOTA (Quick 260915-j5l,
// 2026-09-15): 25 — reversão deliberada, guardião atualizado com nota, não
// apagado. As 7 novas nascem da confirmação inline por card. NOTA (Quick
// 260915-ndt, 2026-09-15): 26 — `curadoriaPremioRotulo` nova, corrige o
// painel inline usando o rótulo da RAZÃO (`curadoriaRazaoRotulo`) ao lado
// do PRÊMIO EM REAIS (`money(item.premioTotal)`) — mesmo rótulo, dois
// números diferentes, defeito de produto financeiro (princípio 4).
const CHAVES = [
  "curadoriaTitulo", "curadoriaSubtitulo", "curadoriaCarregando", "curadoriaVazio",
  "curadoriaRazaoRotulo", "curadoriaNarrarCta", "curadoriaNarrando", "curadoriaIaRotulo",
  "curadoriaIaRessalva", "curadoriaCotaEsgotada", "curadoriaErroNarrar",
  "curadoriaRazaoAjuda", "curadoriaTipoCallCoberta", "curadoriaTipoPutProtecao",
  "curadoriaTipoCollar", "curadoriaTipoDescoberto", "curadoriaVarreduraRotulo",
  "curadoriaPayoffRotulo",
  "curadoriaExecutarCta", "curadoriaExecutando", "curadoriaFechar", "curadoriaExecutada",
  "curadoriaLiquidezConsentir", "curadoriaEstudoNaoExecuta", "curadoriaVerPosicao",
  "curadoriaPremioRotulo",
];
ok("26 chaves da curadoria existem em COPY.estudo e COPY.operador",
  CHAVES.every((k) => k in COPY.estudo) && CHAVES.every((k) => k in COPY.operador));
ok("todas as 26 chaves são string literal (não função)",
  CHAVES.every((k) => typeof COPY.estudo[k] === "string") && CHAVES.every((k) => typeof COPY.operador[k] === "string"));
// Paridade de CONJUNTO (não só a lista fixa acima): qualquer chave
// `curadoria*` nova que um dos dois modos ganhe sem a irmã no outro cai
// aqui, mesmo que ninguém lembre de atualizar CHAVES.
const chavesCuradoriaDe = (copy) => Object.keys(copy).filter((k) => k.startsWith("curadoria")).sort();
ok("(Fase 31) o CONJUNTO de chaves curadoria* é idêntico nos dois modos",
  JSON.stringify(chavesCuradoriaDe(COPY.estudo)) === JSON.stringify(chavesCuradoriaDe(COPY.operador)));

// ---- (2) Guardrail CVM: manchete verbatim, nada de strike/composição -----
ok("CuradoriaEstruturas renderiza {item.manchete} direto (sem composição)",
  /\{item\.manchete\}/.test(fatiaCuradoriaComComentario));
ok("CuradoriaEstruturas NÃO usa template string envolvendo manchete",
  !/`[^`]*\$\{[^}]*manchete/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO concatena manchete (regex `manchete...+`)",
  !/manchete[^}]*\+/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO trunca a manchete (slice/substring/reticências aplicados a manchete)",
  !/manchete[^;]{0,40}(\.slice\(|\.substring\(|…)/.test(fatiaCuradoria));
ok("CuradoriaEstruturas NÃO referencia item.strike (proibido compor frase a partir de strike)",
  !fatiaCuradoria.includes("item.strike"));

// ---- (3) Ordem é do motor — sem sort/reverse/comparação de razao ---------
ok("CuradoriaEstruturas NÃO usa .sort( no corpo",
  !fatiaCuradoria.includes(".sort("));
ok("CuradoriaEstruturas NÃO usa .reverse( no corpo",
  !fatiaCuradoria.includes(".reverse("));
ok("CuradoriaEstruturas NÃO compara item.razao (nenhuma comparação a.razao/b.razao)",
  !/[ab]\.razao\s*[<>-]/.test(fatiaCuradoria));
ok("CuradoriaEstruturas itera top.map( direto — sem [...top].sort/slice antes",
  /\btop\.map\(/.test(fatiaCuradoria) && !/\[\.\.\.top\]/.test(fatiaCuradoria));

// ---- (9, Fase 31/D-04) chave de render é <var>.idCandidato ----------------
// Collar não tem contractSymbol único (2 pernas) — key={<var>.contractSymbol}
// colidiria em null. O fallback (|| <var>.contractSymbol) é aceitável, mas
// idCandidato precisa vir PRIMEIRO na expressão de key.
// NOTA (2026-09-16, IN-02/32-REVIEW.md, quick 260916-cod): o parâmetro do
// `.map()` foi renomeado de `item` (sombreava o `item` = candidato ABERTO,
// declarado no escopo do componente) para `cand` — renome local, sem mudança
// de comportamento. Guardião ATUALIZADO para a nova string, não apagado.
ok("(Fase 31) a chave de render do carrossel é cand.idCandidato",
  /key=\{cand\.idCandidato/.test(fatiaCuradoria));
ok("(Fase 31) key={cand.contractSymbol} sozinho (sem idCandidato) NÃO aparece no bloco",
  !/key=\{cand\.contractSymbol\}/.test(fatiaCuradoria));

// ---- (4) narrar() nunca chamado dentro do useEffect (cota só por toque) --
// ATUALIZADO 2026-09-15 (Fase 32, 32-02, Decisão A): o marcador de fim do
// efeito mudou de `}, []);` para `}, [ativo, nonce]);` — ver item (26).
const iEffectCur = fatiaHookCur.indexOf("useEffect(");
const iEffectCurFim = fatiaHookCur.indexOf("}, [ativo, nonce]);", iEffectCur);
ok("useCuradoria tem exatamente um useEffect com dependência [ativo, nonce]",
  iEffectCur > -1 && iEffectCurFim > iEffectCur);
const corpoEffectCur = iEffectCur > -1 && iEffectCurFim > -1 ? fatiaHookCur.slice(iEffectCur, iEffectCurFim) : "";
ok("o corpo do useEffect de useCuradoria NÃO chama narrar(",
  corpoEffectCur.length > 0 && !corpoEffectCur.includes("narrar("));
ok("narrar é retornado pelo hook (só sai por toque explícito do componente)",
  /return\s*\{[^}]*\bnarrar\b/.test(fatiaHookCur));

// ---- (26, Fase 32/32-02, Decisão A) guarda de flag desligada -------------
ok("(Fase 32) o corpo do useEffect de useCuradoria tem `if (!ativo) return` ANTES de store.opcoesCuradoria(",
  corpoEffectCur.length > 0 && corpoEffectCur.indexOf("if (!ativo) return") > -1
  && corpoEffectCur.indexOf("if (!ativo) return") < corpoEffectCur.indexOf("store.opcoesCuradoria("));
ok("(Fase 32) recarregar é retornado pelo hook",
  /return\s*\{[^}]*\brecarregar\b/.test(fatiaHookCur));

// ---- (27, Fase 32/32-02, Decisão A) useCuradoria( aparece 2x em App.jsx --
ok("(Fase 32) useCuradoria( aparece exatamente 2x em App.jsx (definição + chamada única em App())",
  (fonteSemComentario.match(/useCuradoria\(/g) || []).length === 2);
// ATUALIZADO (Fase 32, 32-03): CarteiraScreen deixou de DESESTRUTURAR
// ctx.curadoria (o consumidor local — o painel de CuradoriaEstruturas —
// migrou para OpcoesScreen.jsx). A fonte única continua sendo UMA: agora
// CarteiraScreen passa o objeto INTEIRO como prop para LinhaChamadaOpcoes,
// e OpcoesScreen.jsx lê o mesmo ctx.curadoria (via blocoCuradoria) — D-03
// (uma fonte, duas leituras) provado nos DOIS destinos, nenhuma segunda
// instância do hook em lugar nenhum.
ok("(Fase 32/32-03) CarteiraScreen NÃO desestrutura mais ctx.curadoria (consumidor migrou para OpcoesScreen.jsx)",
  !/\}\s*=\s*ctx\.curadoria;/.test(fatiaCarteira));
ok("(Fase 32/32-03) CarteiraScreen passa ctx.curadoria inteiro como prop para LinhaChamadaOpcoes",
  /curadoria=\{ctx\.curadoria\}/.test(fatiaCarteira));
ok("(Fase 32/32-03) OpcoesScreen.jsx (blocoCuradoria) lê ctx.curadoria.top/meta/carregando/erro — mesma fonte, segunda leitura",
  /ctx\.curadoria\.top/.test(telaOpcoesSemComentario) && /ctx\.curadoria\.meta/.test(telaOpcoesSemComentario));

// ---- (5) itens vêm de `top`; narrativa.estruturas nunca em map( de render
ok("CuradoriaEstruturas mapeia top.map( para renderizar os itens",
  /top\.map\(/.test(fatiaCuradoria));
ok("narrativa.estruturas NÃO aparece em nenhum map( de CuradoriaEstruturas",
  !/narrativa\.estruturas[^;]*\.map\(/.test(fatiaCuradoria) && !/\.map\([^)]*narrativa\.estruturas/.test(fatiaCuradoria));
ok("nenhum .map( do componente itera sobre narrativa (só `top.map(` renderiza itens)",
  !/narrativa\.map\(|narrativa\.estruturas\.map\(/.test(fatiaCuradoria));

// ---- (6, Fase 32/32-03) <CuradoriaEstruturas aparece 1x em OpcoesScreen.jsx,
// no topo da sub-aba Setups — call site migrou de CarteiraScreen (App.jsx)
// para lá (D-04/D-07). App.jsx NÃO renderiza mais o componente.
ok("(Fase 32/32-03) <CuradoriaEstruturas aparece exatamente 1x no fonte de OpcoesScreen.jsx",
  (telaOpcoesSemComentario.match(/<CuradoriaEstruturas/g) || []).length === 1);
ok("(Fase 32/32-03) <CuradoriaEstruturas aparece 0x em App.jsx (call site saiu de CarteiraScreen)",
  (fonteSemComentario.match(/<CuradoriaEstruturas/g) || []).length === 0);
const iTagCur = telaOpcoesSemComentario.indexOf("<CuradoriaEstruturas");
const iTagOO = telaOpcoesSemComentario.indexOf("<OportunidadesOpcoes");
ok("(Fase 32/32-03) <CuradoriaEstruturas aparece depois de <OportunidadesOpcoes (irmão, nesta ordem) em OpcoesScreen.jsx",
  iTagCur > iTagOO && iTagOO > -1);
// A ordem exigida é a de MONTAGEM na árvore ({blocoOportunidades} antes de
// {blocoCuradoria}, ambos antes de {blocoVigias}, dentro do ramo
// subaba === "setups") — não mais "dentro do mesmo bloco
// data.positions.length > 0", que era a guarda de CarteiraScreen e não
// existe mais neste destino.
const iUsoBlocoOO = telaOpcoesSemComentario.indexOf("{blocoOportunidades}");
const iUsoBlocoCur = telaOpcoesSemComentario.indexOf("{blocoCuradoria}");
const iUsoBlocoVigias = telaOpcoesSemComentario.indexOf("{blocoVigias}");
ok("(Fase 32/32-03) {blocoCuradoria} é usado depois de {blocoOportunidades} e antes de {blocoVigias} em OpcoesScreen.jsx",
  iUsoBlocoOO > -1 && iUsoBlocoCur > iUsoBlocoOO && iUsoBlocoVigias > iUsoBlocoCur);

// ---- (7) Best-effort: toda chamada de rede do hook tem .catch( -----------
// Mesmo algoritmo de test_carteira_opcoes_tira.mjs: caminha o encadeamento
// real de .then/.catch/.finally por balanceamento de parênteses, em vez de
// uma janela fixa de caracteres.
function encadeamentoTemCatch(src, chamada) {
  const i = src.indexOf(chamada);
  if (i === -1) return { achou: false, temCatch: false };
  let depth = 0, j = i;
  for (; j < src.length; j++) {
    if (src[j] === "(") depth++;
    else if (src[j] === ")") { depth--; if (depth === 0) { j++; break; } }
  }
  let k = j, temCatch = false;
  while (true) {
    while (k < src.length && /\s/.test(src[k])) k++;
    if (src[k] !== ".") break;
    const m = src.slice(k).match(/^\.(then|catch|finally)\(/);
    if (!m) break;
    if (m[1] === "catch") temCatch = true;
    let d = 0, p = k + m[0].length - 1;
    for (; p < src.length; p++) {
      if (src[p] === "(") d++;
      else if (src[p] === ")") { d--; if (d === 0) { p++; break; } }
    }
    k = p;
  }
  return { achou: true, temCatch };
}
const rBusca = encadeamentoTemCatch(fatiaHookCur, "store.opcoesCuradoria(");
const rNarrar = encadeamentoTemCatch(fatiaHookCur, "store.opcoesCuradoriaNarrativa(");
ok("store.opcoesCuradoria( encontrado no corpo de useCuradoria", rBusca.achou);
ok("o encadeamento de store.opcoesCuradoria( contém .catch(", rBusca.temCatch);
ok("store.opcoesCuradoriaNarrativa( encontrado no corpo de useCuradoria", rNarrar.achou);
ok("o encadeamento de store.opcoesCuradoriaNarrativa( contém .catch(", rNarrar.temCatch);

// ---- (8) copy da curadoria não promete lucro nem garante resultado -------
const PROIBIDAS = ["garantido", "lucro garantido", "sem risco", "certeza"];
function copySemPromessa(copy) {
  return CHAVES.every((k) => {
    const v = (copy[k] || "").toLowerCase();
    return PROIBIDAS.every((p) => !v.includes(p));
  });
}
ok("nenhuma das 26 frases de COPY.estudo contém palavra de promessa de lucro/garantia",
  copySemPromessa(COPY.estudo));
ok("nenhuma das 26 frases de COPY.operador contém palavra de promessa de lucro/garantia",
  copySemPromessa(COPY.operador));

// ---- (10, Fase 31/D-04) rótulo de tipo para os 4 tipos do motor ----------
// O mapa tipo→chave de copy vive ANTES da função, DENTRO do módulo (Fase 32,
// 32-02: interno, não exportado) — não dentro dela.
const iRotuloTipo = modulo.indexOf("ROTULO_TIPO_CURADORIA = {");
const iExportCuradoria = modulo.indexOf("export default function CuradoriaEstruturas");
ok("(Fase 31) existe um mapa ROTULO_TIPO_CURADORIA definido antes de CuradoriaEstruturas, dentro do módulo",
  iRotuloTipo > -1 && iExportCuradoria > -1 && iRotuloTipo < iExportCuradoria);
const fatiaMapaTipo = iRotuloTipo > -1 ? modulo.slice(iRotuloTipo, iExportCuradoria) : "";
const TIPOS_MOTOR = ["call_coberta", "put_protecao", "collar", "opcao_a_descoberto"];
ok("(Fase 31) o mapa de rótulo cobre os 4 tipos do motor (call_coberta/put_protecao/collar/opcao_a_descoberto)",
  TIPOS_MOTOR.every((t) => fatiaMapaTipo.includes(t + ":")));
ok("(Fase 31) cada tipo aponta para uma chave curadoriaTipo* de copy",
  (fatiaMapaTipo.match(/curadoriaTipo\w+/g) || []).length === 4);
// NOTA (2026-09-16, IN-02): idem — `item.tipo` do card virou `cand.tipo`
// (renome local, mesmo rename da regra 9).
ok("(Fase 31) o chip de tipo é renderizado no card (lookup dinâmico do mapa, nunca hardcoded)",
  /ROTULO_TIPO_CURADORIA\[cand\.tipo\]/.test(fatiaCuradoria));
ok("(Fase 32) ROTULO_TIPO_CURADORIA NÃO é exportado (interno ao módulo)",
  !/export\s+(const|\{[^}]*ROTULO_TIPO_CURADORIA)/.test(modulo.replace(/export default function CuradoriaEstruturas/, "")));
ok("(Fase 32) App.jsx NÃO define mais ROTULO_TIPO_CURADORIA",
  !app.includes("ROTULO_TIPO_CURADORIA"));

// ---- (11, Fase 31/D-02/D-03) resumo da varredura lê meta.candidatosPorTipo
ok("(Fase 31) a linha de resumo lê meta.candidatosPorTipo",
  fatiaCuradoria.includes("meta.candidatosPorTipo"));
ok("(Fase 31) a linha de resumo lê meta.tetoVencimentos",
  fatiaCuradoria.includes("meta.tetoVencimentos"));
ok("(Fase 31) campo ausente do resumo vira travessão, não 0 (princípio 4 do CLAUDE.md)",
  fatiaCuradoria.includes('"—"'));

// ---- (12, Fase 31/D-07/D-08) exatamente UM <PayoffChart no bloco ---------
ok("(Fase 31) <PayoffChart aparece exatamente 1x dentro de CuradoriaEstruturas (uma curva, sem overlay)",
  (fatiaCuradoria.match(/<PayoffChart/g) || []).length === 1);
ok("(Fase 31) o payoff renderizado é do item nº 1 (top[0]), não de um índice arbitrário",
  fatiaCuradoria.includes("top[0].estrutura"));

// ---- (13, Fase 31/D-05) nenhuma copy da curadoria convida a ligar o flag -
// D-05: conta sem permitirOpcaoADescoberto não vê oportunidade a descoberto
// NEM com aviso — é proibido criar texto tipo "ative o flag para ver mais".
const PROIBIDAS_D05 = ["flag", "ative", "libere", "desbloque"];
function copySemConviteAoFlag(copy) {
  return CHAVES.every((k) => {
    const v = (copy[k] || "").toLowerCase();
    return PROIBIDAS_D05.every((p) => !v.includes(p));
  });
}
ok("(Fase 31/D-05) nenhuma das 26 frases de COPY.estudo convida a ligar o flag de opção a descoberto",
  copySemConviteAoFlag(COPY.estudo));
ok("(Fase 31/D-05) nenhuma das 26 frases de COPY.operador convida a ligar o flag de opção a descoberto",
  copySemConviteAoFlag(COPY.operador));

// ---- (14, Quick 260915-j5l) o card NÃO chama mais onAbrir(item.ticker) ---
// no onClick PRINCIPAL — era o bug: o clique descartava o candidato
// inteiro. onAbrir sobrevive só como link secundário dentro do painel
// (rotulado cp.curadoriaVerPosicao) — por isso a prova é POSICIONAL, não
// "zero ocorrências": a ÚNICA chamada onAbrir(item.ticker) do módulo tem
// de estar perto do rótulo curadoriaVerPosicao, nunca dentro do bloco do
// botão do card (identificado por key={cand.idCandidato — NOTA 2026-09-16,
// IN-02: era key={item.idCandidato antes do renome do parâmetro do `.map`;
// `item.ticker` do onAbrir continua correto — é o `item` ABERTO do painel,
// variável diferente, não tocada por este renome).
const iCardBtn = fatiaCuradoria.indexOf("key={cand.idCandidato");
const iCardBtnStyleAttr = fatiaCuradoria.indexOf("...carouselItemStyle", iCardBtn);
const trechoOnClickDoCard = iCardBtn > -1 && iCardBtnStyleAttr > -1 ? fatiaCuradoria.slice(iCardBtn, iCardBtnStyleAttr) : "";
ok("(Quick 260915-j5l) o card foi localizado (key={cand.idCandidato) e tem o atributo de estilo do carrossel na sequência esperada",
  trechoOnClickDoCard.length > 0);
ok("(Quick 260915-j5l) o onClick do card principal NÃO chama onAbrir( — o clique deixou de descartar o candidato inteiro",
  !trechoOnClickDoCard.includes("onAbrir("));
ok("(Quick 260915-j5l) o onClick do card principal ALTERNA abertoId (toggle, com setAbertoId)",
  /onClick=\{\(\)\s*=>\s*setAbertoId/.test(trechoOnClickDoCard));
const ocorrenciasOnAbrirTicker = (fatiaCuradoria.match(/onAbrir\(item\.ticker\)/g) || []).length;
ok("(Quick 260915-j5l) onAbrir(item.ticker) aparece exatamente 1x no módulo (só o link secundário do painel)",
  ocorrenciasOnAbrirTicker === 1);
const iOnAbrirTicker = fatiaCuradoria.indexOf("onAbrir(item.ticker)");
const iVerPosicaoCopy = fatiaCuradoria.indexOf("curadoriaVerPosicao");
ok("(Quick 260915-j5l) a única chamada onAbrir(item.ticker) precede o rótulo curadoriaVerPosicao no mesmo botão (é o link do painel, não o onClick do card)",
  iOnAbrirTicker > -1 && iVerPosicaoCopy > iOnAbrirTicker && (iVerPosicaoCopy - iOnAbrirTicker) < 500);

// ---- (15, Quick 260915-j5l) onExecutar recebe o ITEM, nunca só o ticker --
ok("(Quick 260915-j5l) onExecutar é chamado com o item inteiro (onExecutar(item, )",
  /onExecutar\(item,/.test(fatiaCuradoria));
ok("(Quick 260915-j5l) onExecutar NUNCA é chamado só com item.ticker",
  !/onExecutar\(item\.ticker/.test(fatiaCuradoria));

// ---- (16, Quick 260915-j5l) despacho por tipo mora em executarCandidato.js
ok("(Quick 260915-j5l) App.jsx importa executarCandidato de ./opcoes/executarCandidato.js",
  /from\s+"\.\/opcoes\/executarCandidato\.js"/.test(app));
ok("(Quick 260915-j5l) CuradoriaEstruturas NÃO contém literal de rota /api/options/ — rota escrita na UI seria a segunda cópia do contrato",
  !fatiaCuradoria.includes("/api/options/"));

// ---- (17, Quick 260915-j5l) painel inline sem chamada de store/api -------
ok("(Quick 260915-j5l) o painel lê item.estrutura",
  fatiaCuradoria.includes("item.estrutura"));
ok("(Quick 260915-j5l) o painel lê item.premioTotal",
  fatiaCuradoria.includes("item.premioTotal"));
ok("(Quick 260915-j5l) CuradoriaEstruturas NÃO chama store.<metodo>( dentro do componente (sem rede nova no clique)",
  !/\bstore\.\w+\(/.test(fatiaCuradoria));
ok("(Quick 260915-j5l) CuradoriaEstruturas NÃO chama api.<metodo>( dentro do componente",
  !/\bapi\.\w+\(/.test(fatiaCuradoria));

// ---- (18, Quick 260915-j5l) porLote do painel é null-safe -----------------
ok('(Quick 260915-j5l) porLote checa typeof v === "number" (null-safe, "null nunca 0.0")',
  fatiaCuradoria.includes('typeof v === "number"'));
ok("(Quick 260915-j5l) perda_maxima/breakevens passam por porLote/price — nenhuma multiplicação direta de estAberto.perda_maxima fora do helper",
  !/estAberto\.perda_maxima\s*\*/.test(fatiaCuradoria));

// ---- (19, Quick 260915-j5l) caixa de erro usa T.warn, nunca T.negative ---
ok("(Quick 260915-j5l) a caixa de erro do painel usa color: T.warn",
  /execAtual\.erro[\s\S]{0,300}?color:\s*T\.warn/.test(fatiaCuradoria));
ok("(Quick 260915-j5l) CuradoriaEstruturas NÃO usa T.negative em lugar nenhum (vermelho é de P&L, não de recusa)",
  !fatiaCuradoria.includes("T.negative"));

// ---- (20, Quick 260915-j5l) nenhum window.confirm( — confirmação é inline
ok("(Quick 260915-j5l) CuradoriaEstruturas NÃO usa window.confirm(",
  !fatiaCuradoria.includes("window.confirm("));

// ---- (21, Quick 260915-j5l) aceitaLiquidezDificil sempre junto de liquidezOk
ok("(Quick 260915-j5l) aceitaLiquidezDificil é derivado de liquidezOk (identidade, nunca um `true` solto)",
  /aceitaLiquidezDificil:\s*!!liquidezOk/.test(fatiaCuradoria));
// Toda ATRIBUIÇÃO a `aceitaLiquidezDificil:` no componente tem de carregar
// `liquidezOk` na própria expressão — nenhuma outra ocorrência (ex.: um
// `aceitaLiquidezDificil: true` solto) é permitida.
const atribuicoesLiquidez = [...fatiaCuradoria.matchAll(/aceitaLiquidezDificil:\s*([^\s,}]+)/g)].map((m) => m[1]);
ok("(Quick 260915-j5l) TODA atribuição a aceitaLiquidezDificil: referencia liquidezOk (nenhum true solto)",
  atribuicoesLiquidez.length > 0 && atribuicoesLiquidez.every((v) => v.includes("liquidezOk")));

// ---- (22, Quick 260915-j5l) CTA de executar dentro de ramo guardado por operador
const iOperadorBloco = fatiaCuradoria.indexOf("{operador && (");
const iEstudoBloco = fatiaCuradoria.indexOf("{!operador && (");
const iExecutarCta = fatiaCuradoria.indexOf("curadoriaExecutarCta");
ok("(Quick 260915-j5l) existe um ramo {!operador && ( com curadoriaEstudoNaoExecuta (Modo Estudo sem CTA)",
  iEstudoBloco > -1 && fatiaCuradoria.indexOf("curadoriaEstudoNaoExecuta", iEstudoBloco) > iEstudoBloco);
ok("(Quick 260915-j5l) o CTA de executar (curadoriaExecutarCta) está DEPOIS do início do ramo {operador && ( — nunca fora dele",
  iOperadorBloco > -1 && iExecutarCta > iOperadorBloco);

// ---- (23, Quick 260915-ndt) painel inline: rótulo do PRÊMIO é
// curadoriaPremioRotulo, não curadoriaRazaoRotulo -----------------------
// Defeito corrigido: o painel usava cp.curadoriaRazaoRotulo (rótulo da
// RAZÃO) ao lado de money(item.premioTotal) (o PRÊMIO EM REAIS).
// NOTA (2026-09-16, IN-02, quick 260916-cod): antes do renome do parâmetro
// do `.map` (item → cand), CARD e PAINEL compartilhavam o literal
// "money(item.premioTotal)" e a prova era POSICIONAL (2ª ocorrência =
// painel). Depois do renome, o CARD usa "money(cand.premioTotal)" e só o
// PAINEL usa "money(item.premioTotal)" — a prova fica mais simples (cada
// variável aparece exatamente 1x), sem perder a checagem original: card
// rotulado por curadoriaRazaoRotulo (ao lado de cand.razao, regra 24 abaixo)
// e painel rotulado por curadoriaPremioRotulo (checado aqui).
const ocorrenciasMoneyPremioTotalCard = [...fatiaCuradoria.matchAll(/money\(cand\.premioTotal\)/g)];
const ocorrenciasMoneyPremioTotalPainel = [...fatiaCuradoria.matchAll(/money\(item\.premioTotal\)/g)];
ok("(Quick 260915-ndt) money(cand.premioTotal) aparece exatamente 1x em CuradoriaEstruturas (card)",
  ocorrenciasMoneyPremioTotalCard.length === 1);
ok("(Quick 260915-ndt) money(item.premioTotal) aparece exatamente 1x em CuradoriaEstruturas (painel)",
  ocorrenciasMoneyPremioTotalPainel.length === 1);
const iMoneyPainel = ocorrenciasMoneyPremioTotalPainel.length === 1 ? ocorrenciasMoneyPremioTotalPainel[0].index : -1;
const iPremioRotuloAntesDoPainel = iMoneyPainel > -1 ? fatiaCuradoria.lastIndexOf("curadoriaPremioRotulo", iMoneyPainel) : -1;
ok("(Quick 260915-ndt) o rótulo mais próximo ANTES do money(item.premioTotal) do painel é cp.curadoriaPremioRotulo",
  iPremioRotuloAntesDoPainel > -1 && (iMoneyPainel - iPremioRotuloAntesDoPainel) < 200);

// ---- (24, Quick 260915-ndt) curadoriaRazaoRotulo aparece EXATAMENTE 1x —
// a regressão que esta quick fecha (dois usos = rótulo da razão de volta
// sobre um número que não é razão) -----------------------------------------
const ocorrenciasRazaoRotulo = (fatiaCuradoria.match(/curadoriaRazaoRotulo/g) || []).length;
ok("(Quick 260915-ndt) cp.curadoriaRazaoRotulo aparece exatamente 1x em CuradoriaEstruturas (só no card, ao lado de item.razao)",
  ocorrenciasRazaoRotulo === 1);

// ---- (25, Quick 260915-ndt) rótulos DIFERENTES para números diferentes,
// nos dois modos — rótulos iguais para números diferentes é o defeito ------
ok("(Quick 260915-ndt) COPY.estudo.curadoriaPremioRotulo !== COPY.estudo.curadoriaRazaoRotulo",
  COPY.estudo.curadoriaPremioRotulo !== COPY.estudo.curadoriaRazaoRotulo);
ok("(Quick 260915-ndt) COPY.operador.curadoriaPremioRotulo !== COPY.operador.curadoriaRazaoRotulo",
  COPY.operador.curadoriaPremioRotulo !== COPY.operador.curadoriaRazaoRotulo);

// ---- Sanidade adicional: nem App.jsx, nem OpcoesScreen.jsx, nem o módulo
// importam um do outro em ciclo -------------------------------------------
// (Fase 32, 32-02): CuradoriaEstruturas.jsx NÃO pode importar App.jsx.
// ATUALIZADO (Fase 32, 32-03): o CONSUMIDOR mudou — App.jsx não renderiza
// mais o componente, então não precisa mais importá-lo; quem importa agora
// é OpcoesScreen.jsx (mesmo módulo terceiro, consumidor diferente).
ok("(Fase 32) CuradoriaEstruturas.jsx NÃO importa App.jsx",
  !/from\s+"[^"]*App\.jsx"/.test(modulo));
ok("(Fase 32/32-03) App.jsx NÃO importa mais CuradoriaEstruturas (call site saiu para OpcoesScreen.jsx)",
  !/from\s+"\.\/opcoes\/CuradoriaEstruturas\.jsx"/.test(app));
ok("(Fase 32/32-03) OpcoesScreen.jsx importa CuradoriaEstruturas de ./CuradoriaEstruturas.jsx",
  /from\s+"\.\/CuradoriaEstruturas\.jsx"/.test(telaOpcoes));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
