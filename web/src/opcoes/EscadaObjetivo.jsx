/**
 * EscadaObjetivo.jsx — Fase 48 (48-09): tela 3 (escada + gráfico + risco + CTA).
 *
 * Só LÊ o backend: degraus, colunas (com `fracao` pronta), frase de risco,
 * custo da comparação (`comparar.rotulo`, mostrado ANTES do clique). Nenhuma
 * chamada de rede aqui: a consulta paga (matriz) é do hook, só por clique,
 * disparada via `comparar.onAbrir`. Zero cálculo financeiro; ausente = "—".
 * Frescor/mercado fechado vêm do container (48-10).
 */
import { useRef } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import GraficoResultado from "./GraficoResultado.jsx";
import {
  T, FOCO, TIPO, MONO, DISPLAY, ALVO_MIN, CTA_MIN, SR_ONLY, reduzido, transicaoDegrau, transicaoTela,
} from "./fluxoEstilo.js";
import VoltarPadrao from "../VoltarPadrao.jsx"; // Onda B (2026-10-08): Voltar único

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace("-", "−")
    : "—";

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

const idDe = (d) => (d && d.id != null ? d.id : d && d.nome);

export default function EscadaObjetivo({
  cp, mode, ticker, objetivo, escada, degrauId, vencimento, unidade,
  onEscolherVencimento, onEscolherDegrau, onTrocarUnidade, onEscolher, onVoltar,
  comparar, renderMatriz, didatica, A, kbCatalogo, onAbrirVerbete, onTentarDeNovo,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const u = unidade === "acao" ? "porAcao" : "total";
  const e = escada || {};
  const dados = e.dados || null;
  const degraus = dados && Array.isArray(dados.degraus) ? dados.degraus : [];
  const ausentes = dados && Array.isArray(dados.degrausAusentes) ? dados.degrausAusentes : [];
  const vencs = dados && Array.isArray(dados.vencimentos) ? dados.vencimentos : [];
  const vencAtivo = vencimento || (dados && dados.vencimento) || null;
  const refs = useRef({});
  const cmp = comparar || {};
  const erroMatriz = cmp.matriz && cmp.matriz.erro ? cmp.matriz.erro : null;
  const consultando = !!(cmp.matriz && cmp.matriz.carregando);

  const selecionado = degraus.find((d) => idDe(d) === degrauId) || null;
  const secao = objetivo ? tx("secao_" + objetivo) : null;
  const precoTxt = dados && ehNum(dados.precoObjeto) ? fmt(dados.precoObjeto) : "—";

  // Roving: tabIndex 0 só no marcado (ou no primeiro, se nenhum).
  const focavel = selecionado ? idDe(selecionado) : (degraus[0] ? idDe(degraus[0]) : null);

  const mover = (i, delta) => {
    if (!degraus.length) return;
    const j = (i + delta + degraus.length) % degraus.length;
    const alvo = degraus[j];
    if (onEscolherDegrau) onEscolherDegrau(idDe(alvo));
    const el = refs.current[idDe(alvo)];
    if (el && el.focus) el.focus();
  };
  const onTecla = (ev, i, d) => {
    const k = ev.key;
    if (k === "ArrowDown" || k === "ArrowRight") { ev.preventDefault(); mover(i, 1); }
    else if (k === "ArrowUp" || k === "ArrowLeft") { ev.preventDefault(); mover(i, -1); }
    else if (k === "Enter" || k === " ") { ev.preventDefault(); if (onEscolherDegrau) onEscolherDegrau(idDe(d)); }
  };

  const cotaEsgotada = (cmp.restamHoje === 0) || (dados && dados.comparar && dados.comparar.restamHoje === 0)
    || !!(erroMatriz && erroMatriz.code === "mcp_cota");
  const quando = (cmp.cap && cmp.cap.reinicia)
    || (cmp.matriz && cmp.matriz.dados && cmp.matriz.dados.cap && cmp.matriz.dados.cap.reinicia) || "—";
  const rotuloCusto = dados && dados.comparar ? dados.comparar.rotulo : null;

  const exec = selecionado && selecionado.execucao ? selecionado.execucao : null;
  const executavel = !!(selecionado && exec && exec.executavel === true);
  const motivoExec = selecionado && !executavel
    ? ((exec && exec.motivo) || selecionado.motivoSemGrafico || tx("dado_insuficiente")) : null;

  const semEstrutura = !e.carregando && !e.erro && dados && dados.estado === "ok" && !degraus.length;

  return (
    <section style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px", ...transicaoTela(reduzido()) }}>
      <div>
        <VoltarPadrao onClick={onVoltar} rotulo={tx("voltar")} {...comFoco} />
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("aviso_virtual")}</div>
      </div>

      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "8px", flexWrap: "wrap" }}>
        <h2 tabIndex={-1} style={{ margin: 0, ...TIPO.titulo, fontFamily: DISPLAY, color: T.textPrimary }}>{secao || tx("carregando")}</h2>
        <span style={{ ...TIPO.corpo, ...MONO, color: T.textSecondary }}>{tx("acao_a", { preco: precoTxt })}</span>
      </header>

      {e.erro ? (
        <div role="alert" style={{ padding: "16px", borderRadius: "12px", border: `1px solid ${T.warn}`, background: T.bgPanel, ...TIPO.corpo, color: T.textPrimary, display: "flex", flexDirection: "column", gap: "8px" }}>
          <span>{tx("erro_fonte")}</span>
          <button type="button" onClick={onTentarDeNovo} {...comFoco}
            style={{ alignSelf: "flex-start", minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textPrimary, ...TIPO.label, cursor: "pointer" }}>
            {tx("tentar_de_novo")}
          </button>
        </div>
      ) : null}

      {vencs.length ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
          {vencs.map((v) => {
            const ativo = v.iso === vencAtivo;
            return (
              <button key={v.iso} type="button" aria-pressed={ativo} onClick={() => onEscolherVencimento && onEscolherVencimento(v.iso)} {...comFoco}
                style={{ minHeight: "48px", padding: "8px", borderRadius: "12px", cursor: "pointer", ...TIPO.label,
                  color: ativo ? T.accent : T.textSecondary, border: `1px solid ${ativo ? T.accent : T.borderSubtle}`,
                  background: ativo ? T.accentTint10 : T.bgPanel }}>
                <div>{v.texto}</div>
                <div style={{ ...TIPO.corpo, color: T.textMuted }}>{tx("vencimento_dias", { dias: ehNum(v.dias) ? v.dias : "—" })}</div>
              </button>
            );
          })}
        </div>
      ) : null}

      {e.carregando ? (
        <div role="status" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <span style={SR_ONLY}>{tx("carregando")}</span>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ minHeight: "64px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }} />
          ))}
          <div style={{ width: "100%", aspectRatio: "340 / 214", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }} />
        </div>
      ) : null}

      {semEstrutura ? (
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>
          <div style={{ ...TIPO.titulo, color: T.textPrimary }}>{tx("sem_estrutura", { ticker: ticker || "" })}</div>
          {dados.motivoTexto ? <div>{dados.motivoTexto}</div> : null}
          <div>{tx("sem_estrutura_dica")}</div>
        </div>
      ) : null}

      {degraus.length || ausentes.length ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div role="radiogroup" aria-label={secao || ""} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {degraus.map((d, i) => {
              const id = idDe(d);
              const marcado = id === degrauId;
              const cols = Array.isArray(d.colunas) ? d.colunas : [];
              const st = d.strikes || {};
              const strikesTxt = [ehNum(st.put) ? "put " + fmt(st.put) : null, ehNum(st.call) ? "call " + fmt(st.call) : null]
                .filter(Boolean).join(" · ") || "—";
              return (
                <div key={id} role="radio" aria-checked={marcado} tabIndex={id === focavel ? 0 : -1}
                  ref={(el) => { refs.current[id] = el; }}
                  onClick={() => onEscolherDegrau && onEscolherDegrau(id)}
                  onKeyDown={(ev) => onTecla(ev, i, d)} {...comFoco}
                  style={{ minHeight: "64px", padding: "12px", borderRadius: "12px", cursor: "pointer", boxSizing: "border-box",
                    border: `1px solid ${marcado ? T.accent : T.borderSubtle}`,
                    background: marcado ? T.accentTint10 : T.bgPanel,
                    transform: marcado ? "translateY(-3px)" : "none", ...transicaoDegrau(reduzido()) }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                    <span style={{ ...TIPO.titulo, color: T.textPrimary }}>{d.rotulo || tx(d.nome) || "—"}</span>
                    <span style={{ ...TIPO.corpo, ...MONO, color: T.textSecondary }}>{strikesTxt}</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "8px" }}>
                    {cols.map((c) => {
                      const v = c.valor ? c.valor[u] : null;
                      const sem = !ehNum(c.fracao);
                      if (c.sinal == null && !ehNum(v)) {
                        return <div key={c.chave} style={{ ...TIPO.corpo, color: T.textMuted }}>{c.rotulo}</div>;
                      }
                      return (
                        <div key={c.chave} style={{ ...TIPO.corpo, color: T.textSecondary }}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                            <span>{c.rotulo}</span>
                            <span style={{ ...MONO, color: T.textPrimary }}>R$ {fmt(v)}</span>
                          </div>
                          <div style={{ height: "8px", borderRadius: "4px", background: T.borderSubtle }}>
                            {sem ? null : (
                              <div style={{ height: "8px", borderRadius: "4px", width: `${c.fracao * 100}%`,
                                background: c.sinal === "negativo" ? T.negative : (c.sinal === "positivo" ? T.positive : T.textMuted) }} />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
          {ausentes.map((a) => (
            <div key={"aus" + a.indice} aria-disabled="true"
              style={{ minHeight: "64px", padding: "12px", borderRadius: "12px", boxSizing: "border-box", border: `1px dashed ${T.borderSubtle}`, ...TIPO.corpo, color: T.textMuted }}>
              <span style={{ ...MONO }}>—</span> {tx("degrau_ausente", { motivo: a.motivo || "—" })}
            </div>
          ))}
          {objetivo === "renda" ? <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("nota_sem_piso")}</div> : null}
        </div>
      ) : null}

      {cmp.aberto ? (renderMatriz ? renderMatriz() : null) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <button type="button" disabled={cotaEsgotada || consultando || !dados || !dados.comparar}
            onClick={() => cmp.onAbrir && cmp.onAbrir()} {...comFoco}
            style={{ width: "100%", minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`,
              background: "transparent", color: T.textPrimary, ...TIPO.label, cursor: cotaEsgotada || consultando ? "not-allowed" : "pointer" }}>
            {consultando ? tx("consultando") : tx("comparar_rotulo")}
          </button>
          <div style={{ ...TIPO.corpo, color: T.textMuted }}>
            {cotaEsgotada ? tx("cota_esgotada", { quando }) : (rotuloCusto || "")}
          </div>
        </div>
      )}

      {selecionado ? (
        <GraficoResultado cp={cp} mode={mode} ticker={ticker} degrau={selecionado} unidade={unidade}
          onTrocarUnidade={onTrocarUnidade} didatica={didatica} A={A} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
      ) : null}

      <p aria-live="polite" style={{ margin: 0, ...TIPO.corpo, color: T.textPrimary }}>
        {selecionado ? (selecionado.fraseRisco || tx("dado_insuficiente")) : ""}
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <button type="button" disabled={!executavel} onClick={() => onEscolher && onEscolher()} {...comFoco}
          style={{ width: "100%", minHeight: CTA_MIN + "px", padding: "8px 16px", borderRadius: "12px", border: "none",
            background: executavel ? T.accent : T.borderSubtle, color: executavel ? T.onAccent : T.textMuted,
            ...TIPO.titulo, cursor: executavel ? "pointer" : "not-allowed" }}>
          {tx("cta_escolher")}
        </button>
        <div style={{ ...TIPO.corpo, color: T.textMuted }}>{executavel ? tx("sem_custo") : (motivoExec || "")}</div>
      </div>
    </section>
  );
}
