/**
 * CuradoriaEstruturas.jsx — Fase 32 (32-02), extração de App.jsx.
 *
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3 — isolamento do núcleo) e `App.jsx` não pode
 * importar `OpcoesScreen.jsx` (seria ciclo). A fiação correta é de UMA VIA
 * para os dois lados — um módulo terceiro que ambos importam, nunca um
 * importando o outro. Isto é a Emenda 3 ao ADR-027 (registrada na Fase 28,
 * `PropostaLastreada.jsx`), aplicada agora aos três componentes que faltavam.
 *
 * (b) O que é: o bloco cross-posição "as 4 melhores estruturas" (Fase 30/31)
 * — o motor SEM gate de liquidez, movido sem redesenho. Manchete VERBATIM
 * do motor determinístico (guardrail CVM, CLAUDE.md princípio 5); `top` é
 * iterado NA ORDEM RECEBIDA (nenhum sort/reverse/comparação de `razao`).
 * `ROTULO_TIPO_CURADORIA` só é usado por este componente — fica interno ao
 * módulo, não exportado. Assinatura de props INALTERADA nesta task: o
 * componente ainda NÃO lê `erro` (a correção de exibição do estado de falha
 * de busca — `useCuradoria().erro` existe mas nunca é renderizado — é escopo
 * do Plano 03, que também move o bloco de tela; mover e corrigir na mesma
 * task esconderia um defeito do outro no diff).
 *
 * (c) Por que `T`/`MONO`/`price`/`money`/`carouselTrackStyle`/
 * `carouselItemStyle` são declarados AQUI em vez de importados de
 * `App.jsx`: importar de `App.jsx` reintroduziria exatamente o import que a
 * Emenda 3 proíbe. São espelho declarado — mesmo padrão de
 * `PropostaLastreada.jsx:22-49` (Fase 28).
 */
import { useState } from "react";
// Fase 31 (Plano 04, D-08): payoff do item nº 1 do bloco de curadoria —
// mesmo componente já em produção no caminho MCP (Fase 24/31-03).
import PayoffChart from "./PayoffChart.jsx";
import { estruturaParaPayoff } from "./estruturaParaPayoff.js";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgCard", "borderFaint", "borderSubtle", "textPrimary", "textSecondary", "textMuted", "textFaint", "accent", "positive", "warn"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Espelho declarado de App.jsx:264/293-295 (Fase 32, 32-02).
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const price = (n) => (n == null || isNaN(n) ? "—" : nf2.format(n));
const money = (n) => (n == null || isNaN(n) ? "—" : "R$ " + nf2.format(n));

// Espelho declarado de App.jsx:333-342 (Fase 32, 32-02) — padrão ÚNICO de
// rolagem horizontal do app (Fase 22, SYS-01).
const carouselTrackStyle = (extra) => ({
  display: "flex",
  overflowX: "auto",
  scrollSnapType: "x proximity",
  WebkitOverflowScrolling: "touch",
  ...extra,
});
const carouselItemStyle = (align = "start") => ({ scrollSnapAlign: align });

// Fase 30 (Plano 04, D4): bloco cross-posição "as 4 melhores vendas
// cobertas" — irmão de OportunidadesOpcoes acima (mesmo precedente de
// "resumo cross-posição de opções" nesta tela, 30-CONTEXT D4).
//
// GUARDRAIL CVM (CLAUDE.md) / T-30-18/T-30-19: `top` é iterado NA ORDEM
// RECEBIDA — nenhum sort/reverse/comparação de `razao` neste componente.
// A ordem é do motor (`item.posicaoNoRanking`); reordenar no front
// recriaria no cliente exatamente o poder que o backend nega à IA.
// `item.manchete` é renderizado VERBATIM — é PROIBIDO compor frase a
// partir de strike/contratos/premioTotal/optionType aqui.
// Fase 31 (Plano 04, D-04): mapa local tipo → chave de copy, usado só para
// o CHIP de categoria acima da manchete (nunca compõe a manchete em si,
// que continua vindo verbatim de item.manchete — guardrail CVM). Módulo,
// não estado: os 4 tipos são fechados (mesmo conjunto de
// server/app/opcoes_curadoria.py TIPOS).
const ROTULO_TIPO_CURADORIA = {
  call_coberta: "curadoriaTipoCallCoberta",
  put_protecao: "curadoriaTipoPutProtecao",
  collar: "curadoriaTipoCollar",
  opcao_a_descoberto: "curadoriaTipoDescoberto",
};

export default function CuradoriaEstruturas({ top, meta, carregando, erro, narrativa, narrando, erroNarrativa, onNarrar, onRecarregar, cp, onAbrir, onExecutar, operador, palette }) {
  // Quick 260915-j5l: clicar num card abre uma confirmação INLINE dentro do
  // próprio bloco (não rola a tela, não abre o acordeão antigo de UMA
  // posição). Estado indexado por idCandidato — NUNCA por ticker: dois
  // candidatos do mesmo ticker (ex.: call_coberta e put_protecao da mesma
  // posição) convivem no top-4 e precisam de estado independente.
  const [abertoId, setAbertoId] = useState(null);
  const [execucao, setExecucao] = useState({}); // {[id]: {busy, erro, ok}}
  const [liquidezOk, setLiquidezOk] = useState({}); // {[id]: true} — consentimento de liquidez DIFÍCIL
  const item = top.find((c) => (c.idCandidato || c.contractSymbol) === abertoId) || null;
  const idAberto = item ? (item.idCandidato || item.contractSymbol) : null;
  const execAtual = idAberto ? (execucao[idAberto] || {}) : {};
  // ATENÇÃO: `null * 100 === 0` em JS — porLote null-safe, mesmo padrão de
  // PropostaLastreada.jsx:200 ("null nunca 0.0", princípio 4 do CLAUDE.md).
  const porLote = item ? (v) => (typeof v === "number" ? v * (item.qtyAcoes || 0) : null) : null;
  const estAberto = item ? (item.estrutura || null) : null;
  const liquidezDificil = !!(item && item.liquidez && item.liquidez.faixa === "DIFÍCIL");
  const liquidezSemAviso = liquidezDificil && !item.liquidez.aviso;
  const consentido = idAberto ? !!liquidezOk[idAberto] : false;
  const executarTravado = execAtual.busy || (liquidezDificil && (liquidezSemAviso || !consentido));
  const handleExecutar = async () => {
    if (!item || !idAberto) return;
    setExecucao((s) => ({ ...s, [idAberto]: { busy: true, erro: null, ok: false } }));
    try {
      // aceitaLiquidezDificil nasce SÓ do estado de consentimento do card
      // (liquidezOk) — nunca um `true` solto (T-J5L-04).
      await onExecutar(item, { aceitaLiquidezDificil: !!liquidezOk[idAberto] });
      setExecucao((s) => ({ ...s, [idAberto]: { busy: false, erro: null, ok: true } }));
      // Fase 32 (32-03): depois de uma execução bem-sucedida, recarrega a
      // varredura — o candidato executado precisa sair da lista (senão o
      // top-4 continua oferecendo algo que já virou posição). Guardado por
      // `if (onRecarregar)` porque nem todo chamador precisa passar a
      // função (ex.: um teste isolado do componente).
      if (onRecarregar) onRecarregar();
    } catch (e) {
      // e.message VERBATIM — nenhuma composição/adivinhação de causa
      // (princípio 4 do CLAUDE.md, T-J5L-03). Sem reenvio automático: o
      // usuário decide o próximo clique.
      setExecucao((s) => ({ ...s, [idAberto]: { busy: false, erro: (e && e.message) || String(e), ok: false } }));
    }
  };

  // Fase 31 (Plano 04, D-04/D-05): resumo da varredura — evidência visível
  // de SC-2/SC-3 mesmo quando o top-4 fica todo de um tipo só (D-06). Lê
  // SÓ meta.candidatosPorTipo/tetoVencimentos; campo ausente vira "—",
  // NUNCA 0 inventado (princípio 4 do CLAUDE.md). Conta sem o flag de
  // opção a descoberto: candidatosPorTipo.opcao_a_descoberto === 0, sem
  // nenhum texto convidando a ligar o flag (D-05) — esta linha só lê o
  // número que o servidor já mandou, nunca compõe convite.
  const porTipo = (meta && meta.candidatosPorTipo) || null;
  const resumoVarredura = porTipo
    ? [
        (porTipo.call_coberta != null ? porTipo.call_coberta : "—") + " " + cp.curadoriaTipoCallCoberta,
        (porTipo.put_protecao != null ? porTipo.put_protecao : "—") + " " + cp.curadoriaTipoPutProtecao,
        (porTipo.collar != null ? porTipo.collar : "—") + " " + cp.curadoriaTipoCollar,
        (porTipo.opcao_a_descoberto != null ? porTipo.opcao_a_descoberto : "—") + " " + cp.curadoriaTipoDescoberto,
      ].join(" · ")
    : null;
  const tetoVencimentosTxt = meta && meta.tetoVencimentos != null ? meta.tetoVencimentos : "—";

  // Fase 31 (Plano 04, D-07/D-08): payoff do item nº 1 — uma curva só, sem
  // seletor, sem overlay. `top` continua sendo a ordem do motor (nenhum
  // sort/reverse aqui); o nº 1 é simplesmente top[0].
  const payoffPrimeiro = top.length > 0 ? estruturaParaPayoff(top[0].estrutura, top[0].ticker) : null;

  return (
    <div style={{ marginBottom: "14px" }}>
      {/* Cabeçalho FIXO nos três estados (itens/carregando/vazio) — mesmo
          precedente de OportunidadesOpcoes (NAV-03): a seção nunca
          desaparece em silêncio quando há posições. */}
      <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint, marginBottom: "4px" }}>{cp.curadoriaTitulo}</div>
      <div style={{ fontSize: "11.5px", color: T.textMuted, marginBottom: "8px", lineHeight: 1.4 }}>{cp.curadoriaSubtitulo}</div>
      {resumoVarredura && (
        <div style={{ fontSize: "10.5px", color: T.textFaint, marginBottom: "8px", lineHeight: 1.5 }}>
          {cp.curadoriaVarreduraRotulo}: {resumoVarredura} · até {tetoVencimentosTxt} vencimentos por posição
        </div>
      )}
      {top.length > 0 && (
        <div style={carouselTrackStyle({ gap: "10px", scrollbarWidth: "none", paddingBottom: "2px" })}>
          {top.map((item) => (
              <button
                key={item.idCandidato || item.contractSymbol}
                type="button"
                aria-label={(ROTULO_TIPO_CURADORIA[item.tipo] ? cp[ROTULO_TIPO_CURADORIA[item.tipo]] + " — " : "") + item.posicaoNoRanking + ". " + item.ticker}
                aria-expanded={abertoId === (item.idCandidato || item.contractSymbol)}
                // Quick 260915-j5l: o clique alterna a confirmação inline
                // (clicar de novo fecha) — NÃO chama mais onAbrir(ticker)
                // aqui, que descartava idCandidato/contractSymbol/
                // pernasContratos/tipo e levava ao acordeão genérico de UMA
                // posição, sempre venda coberta (o bug que este plano
                // corrige). onAbrir sobrevive abaixo, como link secundário
                // dentro do painel expandido.
                onClick={() => setAbertoId((atual) => (atual === (item.idCandidato || item.contractSymbol) ? null : (item.idCandidato || item.contractSymbol)))}
                style={{ ...carouselItemStyle("start"), flex: "0 0 220px", minWidth: "220px", minHeight: "44px", textAlign: "left", padding: "11px 12px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, cursor: "pointer" }}
              >
                <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.accent }}>{item.posicaoNoRanking}. {item.ticker}</div>
                {/* Fase 31 (Plano 04, D-04): chip de TIPO — categoria, nunca
                    a manchete. Fallback "" em tipo desconhecido. */}
                <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.03em", color: T.textFaint, textTransform: "uppercase", marginTop: "3px" }}>
                  {ROTULO_TIPO_CURADORIA[item.tipo] ? cp[ROTULO_TIPO_CURADORIA[item.tipo]] : ""}
                </div>
                {/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md);
                    nunca truncada/concatenada: cortar reescreveria a
                    afirmação do motor. */}
                <div style={{ fontSize: "12.5px", fontWeight: 700, color: T.textPrimary, marginTop: "4px", whiteSpace: "normal" }}>{item.manchete}</div>
                <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px" }}>{cp.curadoriaRazaoRotulo}: {item.razao != null ? item.razao.toFixed(2) : "—"}</div>
                <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "2px" }}>{money(item.premioTotal)} · {item.diasParaVencimento}d · {item.liquidez && item.liquidez.faixa}</div>
              </button>
          ))}
        </div>
      )}
      {/* Quick 260915-j5l: painel de confirmação inline — abaixo da lista
          de cards, dentro do MESMO container (nunca scrollIntoView, nunca
          modal). Renderiza só o candidato com idCandidato === abertoId; lê
          exclusivamente item.estrutura/item.premioTotal/item.liquidez —
          nenhuma chamada de store/api neste bloco (T-J5L-05: o estado da
          carteira já vem pronto de A.executarCandidatoCurado via setData). */}
      {item && (
        <div style={{ marginTop: "10px", padding: "14px", borderRadius: "11px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "13px", fontWeight: 800, color: T.textPrimary, lineHeight: 1.4 }}>{item.manchete}</div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "10px" }}>
            <span style={{ color: T.textSecondary }}>{cp.curadoriaPremioRotulo}</span>
            <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>{money(item.premioTotal)}</b>
          </div>
          {estAberto && (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "4px" }}>
                <span style={{ color: T.textSecondary }}>{cp.payoffPerdaMaxima}</span>
                <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>
                  {estAberto.perda_ilimitada ? cp.payoffIlimitado : "R$ " + price(porLote(estAberto.perda_maxima))}
                </b>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginTop: "4px" }}>
                <span style={{ color: T.textSecondary }}>{cp.payoffBreakeven}</span>
                <b style={{ fontFamily: MONO, fontWeight: 800, color: T.textPrimary }}>
                  {Array.isArray(estAberto.breakevens) && estAberto.breakevens.length ? estAberto.breakevens.map((b) => price(b)).join(" / ") : cp.payoffSemDado}
                </b>
              </div>
            </>
          )}
          {/* Modo Estudo (T-14-23, mesma defesa em UI de PropostaLastreada):
              NADA de botão executar — o 403 do servidor é a defesa real. */}
          {!operador && (
            <div style={{ fontSize: "12px", color: T.textMuted, lineHeight: 1.5, marginTop: "10px" }}>
              {item.didatica}
              <div style={{ marginTop: "6px", fontStyle: "italic" }}>{cp.curadoriaEstudoNaoExecuta}</div>
            </div>
          )}
          {operador && (
            <>
              {liquidezDificil && !liquidezSemAviso && (
                <label style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginTop: "10px", fontSize: "11.5px", color: T.textSecondary, lineHeight: 1.5 }}>
                  <input type="checkbox" checked={consentido} onChange={(e) => setLiquidezOk((s) => ({ ...s, [idAberto]: e.target.checked }))} style={{ marginTop: "2px" }} />
                  <span>{item.liquidez.aviso} {cp.curadoriaLiquidezConsentir}</span>
                </label>
              )}
              {/* liquidez DIFÍCIL sem aviso do servidor: nunca inferir
                  consentimento que o usuário não leu (T-J5L-04) — mesmo
                  texto de useAceiteLastreado ao lado. */}
              {liquidezSemAviso && (
                <div style={{ marginTop: "10px", fontSize: "11.5px", color: T.warn, lineHeight: 1.5 }}>
                  Não foi possível confirmar a liquidez desta operação — tente novamente.
                </div>
              )}
              {execAtual.erro && (
                <div style={{ marginTop: "10px", padding: "9px 10px", borderRadius: "8px", background: "color-mix(in srgb, " + T.warn + " 12%, transparent)", border: `1px solid ${T.warn}`, fontSize: "11.5px", color: T.warn, lineHeight: 1.5 }}>
                  {execAtual.erro}
                </div>
              )}
              {execAtual.ok ? (
                <div style={{ marginTop: "10px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
                  <span style={{ fontSize: "12px", color: T.positive, fontWeight: 700 }}>{cp.curadoriaExecutada}</span>
                  <button type="button" onClick={() => setAbertoId(null)} style={{ minHeight: "40px", padding: "8px 14px", borderRadius: "8px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontWeight: 700, fontSize: "12px" }}>{cp.curadoriaFechar}</button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleExecutar}
                  disabled={executarTravado}
                  style={{ marginTop: "10px", minHeight: "44px", width: "100%", padding: "10px", borderRadius: "10px", border: "none", background: T.accent, color: "#fff", fontWeight: 700, fontSize: "13px", opacity: executarTravado ? 0.55 : 1, cursor: executarTravado ? "default" : "pointer" }}
                >
                  {execAtual.busy ? cp.curadoriaExecutando : cp.curadoriaExecutarCta}
                </button>
              )}
            </>
          )}
          <button
            type="button"
            onClick={() => onAbrir(item.ticker)}
            style={{ marginTop: "10px", display: "block", background: "transparent", border: "none", padding: 0, color: T.accent, fontWeight: 700, fontSize: "11.5px", textDecoration: "none" }}
          >
            {cp.curadoriaVerPosicao}
          </button>
        </div>
      )}
      {/* Fase 31 (Plano 04, D-07/D-08): payoff do nº 1 — abaixo da lista,
          antes do bloco de narração. `emReais={null}` é deliberado: esta
          rota não manda o bloco em reais, e multiplicar no front criaria
          a segunda versão da conta que o repositório proíbe. */}
      {payoffPrimeiro && (
        <div style={{ marginTop: "10px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint, marginBottom: "4px" }}>{cp.curadoriaPayoffRotulo}</div>
          <PayoffChart estrutura={payoffPrimeiro} emReais={null} cp={cp} palette={palette} />
        </div>
      )}
      {/* carregando ANTES do vazio — mesma razão de OportunidadesOpcoes:
          sem esse ramo o bloco piscaria "sem estrutura" durante a busca. */}
      {top.length === 0 && carregando && (
        <div style={{ fontSize: "12px", color: T.textFaint, lineHeight: 1.5 }}>{cp.curadoriaCarregando}</div>
      )}
      {/* Fase 32 (32-03): correção de estado obrigatória (UI-SPEC, achado do
          checker). `erro` tem PRECEDÊNCIA sobre o ramo vazio abaixo — antes
          desta correção, uma busca que FALHAVA caía no mesmo ramo de "nada
          elegível", afirmando um resultado que ninguém mediu (princípio 4
          do CLAUDE.md). Cor de aviso — nunca a cor reservada a P&L. */}
      {top.length === 0 && !carregando && erro && (
        <div style={{ padding: "10px 11px", borderRadius: "9px", background: "color-mix(in srgb, " + T.warn + " 12%, transparent)", border: `1px solid ${T.warn}`, fontSize: "12px", color: T.warn, lineHeight: 1.5 }}>
          <div>{cp.curadoriaErroBusca}</div>
          {onRecarregar && (
            <button
              type="button"
              onClick={onRecarregar}
              style={{ marginTop: "10px", minHeight: "40px", padding: "8px 14px", borderRadius: "8px", border: `1px solid ${T.warn}`, background: "transparent", color: T.warn, fontWeight: 700, fontSize: "12px" }}
            >
              {cp.curadoriaErroBuscaCta}
            </button>
          )}
        </div>
      )}
      {/* ESTADO vazio (NAV-03) — sem CTA, nomeia o motivo. Exige `!erro`: a
          busca ter FALHADO não é o mesmo resultado que "varri e não achei
          nada elegível" (ramo acima). */}
      {top.length === 0 && !carregando && !erro && (
        <div style={{ padding: "10px 11px", borderRadius: "9px", background: T.bgCard, border: `1px solid ${T.borderFaint}`, fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
          {cp.curadoriaVazio}
        </div>
      )}
      {top.length > 0 && (
        <button
          type="button"
          onClick={onNarrar}
          disabled={narrando}
          style={{ marginTop: "8px", minHeight: "44px", width: "100%", padding: "10px", borderRadius: "10px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.accent, fontWeight: 700, fontSize: "12.5px" }}
        >
          {narrando ? cp.curadoriaNarrando : cp.curadoriaNarrarCta}
        </button>
      )}
      {/* Bloco de narrativa SEPARADO dos itens e rotulado. A lista de
          itens ACIMA lê `top`, NUNCA `narrativa.estruturas` — a ordem e
          os números não mudam quando o texto da IA chega (T-30-20). */}
      {narrativa && narrativa.texto && (
        <div style={{ marginTop: "8px", padding: "11px 12px", borderRadius: "10px", background: T.bgCard, border: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em", color: T.textFaint, marginBottom: "4px" }}>{cp.curadoriaIaRotulo}</div>
          <div style={{ fontSize: "12px", color: T.textSecondary, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{narrativa.texto}</div>
          <div style={{ fontSize: "10.5px", color: T.textFaint, marginTop: "6px", fontStyle: "italic" }}>{cp.curadoriaIaRessalva}</div>
        </div>
      )}
      {/* Erros de narração são ESTADO (texto, sem CTA) — nunca apagam os
          itens determinísticos acima. */}
      {erroNarrativa === "cota" && (
        <div style={{ marginTop: "8px", fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>{cp.curadoriaCotaEsgotada}</div>
      )}
      {erroNarrativa === "erro" && (
        <div style={{ marginTop: "8px", fontSize: "11.5px", color: T.textFaint, lineHeight: 1.5 }}>{cp.curadoriaErroNarrar}</div>
      )}
    </div>
  );
}
