/**
 * PernasAbertas.jsx — Fase 48 gap G-02 (2026-10-05).
 * Zero cálculo; resultado só do motor (estrutura.pernas[].resultado); a saída
 * só é vetada pelo motor (encerrar.permitido). Lista toda perna aberta do ativo
 * e encerra a comprada sem lastro por A.sellOption, com confirmação em 2 passos.
 * Ausência de número vira travessão, nunca zero. Zero import de App.jsx/store.
 */
import { useState } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import { T, FOCO, TIPO, ALVO_MIN, NUM } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace("-", "−")
    : "—";
const ddmm = (iso) => (typeof iso === "string" && iso.length >= 10 ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}` : "—");

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

const BOTAO = {
  minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, ...TIPO.label, cursor: "pointer",
};

export default function PernasAbertas({ mode, ticker, optionPositions, estrutura, carregandoEstrutura, A }) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const [confirmando, setConfirmando] = useState(null);
  const [ocupado, setOcupado] = useState(null);

  const abertas = (Array.isArray(optionPositions) ? optionPositions : [])
    .filter((o) => o && o.underlying === ticker && ehNum(o.qty) && o.qty > 0);
  if (abertas.length === 0) return null;

  const motor = estrutura && Array.isArray(estrutura.pernas) ? estrutura.pernas : [];
  const idTitulo = "pernas-titulo-" + ticker;

  const encerrar = async (id) => {
    setOcupado(id);
    try {
      if (A && typeof A.sellOption === "function") await A.sellOption(id);
    } finally {
      setOcupado(null);
      setConfirmando(null);
    }
  };

  return (
    <section aria-labelledby={idTitulo} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <h3 id={idTitulo} style={{ margin: 0, ...TIPO.titulo, color: T.textPrimary }}>{tx("pernas_titulo")}</h3>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
        {abertas.map((pos) => {
          const m = motor.find((p) => p && p.id === pos.id) || null;
          const tipo = String((m && m.tipo) || pos.optionType || "").toUpperCase() || "—";
          const lado = (m && m.lado) || (pos.side === "vendida" ? "venda" : "compra");
          const strike = m && ehNum(m.strike) ? m.strike : pos.strike;
          const venc = (m && m.vencimento) || pos.expiration;
          const qtd = m && ehNum(m.quantidade) ? m.quantidade : pos.qty;
          const entrada = m && ehNum(m.premioEntrada) ? m.premioEntrada : pos.avg;
          const atual = m && ehNum(m.premioAtual) ? m.premioAtual : null;
          const resultado = m && ehNum(m.resultado) ? m.resultado : null;
          const semNumero = resultado === null
            ? ((m && m.motivoSemCotacao) || (carregandoEstrutura ? tx("pernas_carregando") : null))
            : null;
          const vetado = !!(m && m.encerrar && m.encerrar.permitido === false);
          const encerravel = !pos.lastro && pos.side !== "vendida";
          const idVeto = "perna-veto-" + pos.id;
          const emConfirmacao = confirmando === pos.id;
          const emCurso = ocupado === pos.id;
          return (
            <li key={pos.id} style={{ padding: "12px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ ...TIPO.label, color: T.textPrimary, ...NUM }}>{pos.id}</div>
              <div style={{ ...TIPO.corpo, color: T.textPrimary, ...NUM }}>
                {tx("pernas_linha", {
                  tipo, lado: tx(lado === "venda" ? "perna_lado_venda" : "perna_lado_compra"),
                  strike: fmt(strike), vencimento: ddmm(venc), qtd: ehNum(qtd) ? String(qtd) : "—",
                })}
              </div>
              <div style={{ ...TIPO.corpo, color: T.textSecondary, ...NUM }}>
                {tx("pernas_premio", { entrada: fmt(entrada), atual: fmt(atual) })}
              </div>
              <div style={{ ...TIPO.corpo, color: T.textPrimary, ...NUM }}>
                {tx("pernas_resultado", { valor: fmt(resultado) })}
              </div>
              {semNumero ? <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{semNumero}</div> : null}

              {!encerravel ? (
                <div style={{ ...TIPO.corpo, color: T.textSecondary }}>
                  {tx(pos.lastro ? "pernas_na_estrutura" : "pernas_vendida_sem_acao")}
                </div>
              ) : emCurso ? (
                <div role="status" aria-busy="true" style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("pernas_encerrando")}</div>
              ) : emConfirmacao ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div role="status" style={{ ...TIPO.corpo, color: T.textPrimary }}>{tx("pernas_confirmar", { id: pos.id })}</div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <button type="button" onClick={() => encerrar(pos.id)} {...comFoco}
                      style={{ ...BOTAO, color: T.accent, borderColor: T.accent }}>{tx("pernas_confirmar_sim")}</button>
                    <button type="button" onClick={() => setConfirmando(null)} {...comFoco} style={BOTAO}>{tx("pernas_cancelar")}</button>
                  </div>
                </div>
              ) : vetado ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <button type="button" aria-disabled="true" aria-label={tx("pernas_encerrar_aria", { id: pos.id })}
                    aria-describedby={idVeto} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start", cursor: "not-allowed", opacity: 0.7 }}>
                    {tx("pernas_encerrar")}
                  </button>
                  <div id={idVeto} style={{ ...TIPO.corpo, color: T.textPrimary }}>{(m.encerrar && m.encerrar.texto) || "—"}</div>
                </div>
              ) : (
                <button type="button" aria-label={tx("pernas_encerrar_aria", { id: pos.id })}
                  onClick={() => setConfirmando(pos.id)} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start" }}>
                  {tx("pernas_encerrar")}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
