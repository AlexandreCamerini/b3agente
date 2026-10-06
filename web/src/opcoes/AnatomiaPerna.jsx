/**
 * AnatomiaPerna.jsx — Fase 49 (2026-10-06), ANAT-01/02/06/07/08.
 * Zero cálculo: frase, números e curva vêm do motor (anatomia_perna). A saída
 * só é vetada por encerrar.permitido === false do motor. Zero import de
 * App.jsx/store; quem vende é onEncerrar (PernasAbertas).
 * Ausência de número vira travessão ou o chip "Sem cotação" com o motivo do
 * motor, nunca zero. Perda aparece por sinal "−", rótulo e hachura, não só cor.
 */
import { useEffect, useId, useRef, useState } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import TermoOpcoes from "./TermoOpcoes.jsx";
import GraficoAnatomia from "./GraficoAnatomia.jsx";
import { T, FOCO, TIPO, MONO, NUM, ALVO_MIN } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);

const fmt = (v) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace("-", "−")
    : "—";
// "−R$ 21,00" (módulo do valor, sinal tipográfico)
const fmtBRL = (v) => (ehNum(v) ? (v < 0 ? "−" : "") + "R$ " + fmt(Math.abs(v)) : "—");
// "+R$ 5,00" / "−R$ 5,00" / "R$ 0,00" (zero real do motor, nunca ausência)
const fmtBRLsinal = (v) => (ehNum(v) ? (v > 0 ? "+" : "") + fmtBRL(v) : "—");

// WR-02 (49-REVIEW, 2026-10-06): invariante 48-16 — Encerrar nunca é vetado por
// falta de cotação ou de negócio. `premio_indisponivel` vira AVISO (texto do
// motor ao lado do botão habilitado; a confirmação já diz o que não se sabe e a
// rota de venda recusa com mensagem própria se não houver prêmio). Só os vetos
// estruturais do motor (vencida, dados_invalidos e afins) desabilitam o botão.
export const MOTIVO_SO_AVISO = "premio_indisponivel";
export const encerrarVetado = (enc) => !!(enc && enc.permitido === false && enc.motivo !== MOTIVO_SO_AVISO);
export const encerrarAviso = (enc) =>
  enc && enc.permitido === false && enc.motivo === MOTIVO_SO_AVISO && enc.texto ? enc.texto : null;

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

const BOTAO = {
  minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, ...TIPO.label, cursor: "pointer",
};

function Stat({ rotulo, children }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      <span style={{ ...TIPO.label, color: T.textSecondary }}>{rotulo}</span>
      <span style={{ ...TIPO.titulo, ...MONO, color: T.textPrimary }}>{children}</span>
    </div>
  );
}

export default function AnatomiaPerna({
  mode, ticker, perna, pos, grade, cursorIdx, selecionada, onVerSemEsta, onEncerrar,
  ocupado, A, didatica, kbCatalogo, onAbrirVerbete, confirmandoInicial,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const uid = String(useId()).replace(/[^A-Za-z0-9_-]/g, "");
  const [confirmando, setConfirmando] = useState(!!confirmandoInicial);
  const refEncerrar = useRef(null);
  const refCancelar = useRef(null);
  const aberto = useRef(false);

  useEffect(() => {
    if (confirmando && refCancelar.current) {
      refCancelar.current.focus();
      aberto.current = true;
    } else if (!confirmando && aberto.current && refEncerrar.current) {
      aberto.current = false;
      refEncerrar.current.focus();
    }
  }, [confirmando]);

  if (!perna) return null;
  const idTitulo = "anat-titulo-" + uid;
  const idVeto = "anat-veto-" + uid;
  const idConfirma = "anat-confirma-" + uid;
  const hoje = perna.hoje || {};
  const pontos = Array.isArray(perna.pontos) ? perna.pontos : null;
  const tabela = Array.isArray(perna.tabela) ? perna.tabela : [];
  const precos = grade && Array.isArray(grade.precos) ? grade.precos : [];

  const encerravel = !!pos && !pos.lastro && pos.side !== "vendida";
  const vetado = encerrarVetado(perna.encerrar);
  const avisoEnc = encerrarAviso(perna.encerrar);
  const emCurso = ocupado === perna.id;

  const piorValor = perna.piorIlimitado ? tx("anat_pior_ilimitado") : fmtBRL(perna.piorCaso);
  const lado = tx(perna.lado === "venda" ? "perna_lado_venda" : "perna_lado_compra");
  const rotuloEq = tx("anat_rotulo_equilibrio");

  const marcadores = (Array.isArray(perna.marcadores) ? perna.marcadores : []).map((m) => ({
    preco: m.preco,
    rotulo: m.chave === "strike" ? tx("anat_marcador_strike", { strike: fmt(m.preco) }) : tx("anat_marcador_equilibrio"),
  }));

  const textoConfirma = ehNum(hoje.premioAtual)
    ? tx("anat_confirmar_com_cotacao", { id: perna.id, premio: fmt(hoje.premioAtual), resultado: fmtBRLsinal(hoje.valor) })
    : tx("anat_confirmar_sem_cotacao", { id: perna.id });

  const confirmar = async () => {
    if (typeof onEncerrar === "function") await onEncerrar(perna.id);
    setConfirmando(false);
  };

  return (
    <article aria-labelledby={idTitulo}
      style={{
        padding: "16px", borderRadius: "18px", background: T.bgPanel, boxSizing: "border-box",
        border: selecionada ? `2px solid ${T.accent}` : `1px solid ${T.borderSubtle}`,
        display: "flex", flexDirection: "column", gap: "12px",
      }}>
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <h4 id={idTitulo} style={{ margin: 0, ...TIPO.titulo, ...MONO, color: T.textPrimary }}>{perna.id}</h4>
          <span style={{ ...TIPO.label, color: T.textSecondary, border: `1px solid ${T.borderSubtle}`, borderRadius: "999px", padding: "2px 8px" }}>
            {String(perna.tipo || "—")} {lado}
          </span>
        </div>
        <span style={{ ...TIPO.label, color: T.textPrimary, fontWeight: 700 }}>{perna.prazoTexto || "—"}</span>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {perna.motivoTexto ? (
            <p role="status" style={{ margin: 0, ...TIPO.corpo, color: T.textPrimary }}>{perna.motivoTexto}</p>
          ) : null}
          {perna.frase ? <p style={{ margin: 0, fontSize: "16px", lineHeight: 1.5, fontWeight: 400, color: T.textPrimary }}>{perna.frase}</p> : null}
          {perna.condicao ? <p style={{ margin: 0, ...TIPO.corpo, color: T.textSecondary }}>{perna.condicao}</p> : null}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "12px" }}>
            <Stat rotulo={tx("anat_rotulo_pior")}>{piorValor}</Stat>
            <Stat rotulo={
              <TermoOpcoes texto={rotuloEq} termos={[{ rotulo: rotuloEq, kb: "opc-equilibrio" }]}
                A={A} didatica={didatica} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
            }>{ehNum(perna.equilibrio) ? "R$ " + fmt(perna.equilibrio) : "—"}</Stat>
            <Stat rotulo={tx("anat_rotulo_hoje")}>
              {ehNum(hoje.valor)
                ? fmtBRLsinal(hoje.valor)
                : (
                  <span style={{ ...TIPO.label, color: T.textPrimary, border: `1px dashed ${T.warn}`, borderRadius: "999px", padding: "2px 10px", display: "inline-block" }}>
                    {tx("anat_sem_cotacao_chip")}
                  </span>
                )}
            </Stat>
          </div>

          {perna.piorTexto ? <p style={{ margin: 0, ...TIPO.corpo, color: T.textPrimary }}>{perna.piorTexto}</p> : null}
          {hoje.motivoTexto ? <p style={{ margin: 0, ...TIPO.corpo, color: T.textPrimary }}>{hoje.motivoTexto}</p> : null}
          <p style={{ margin: 0, ...TIPO.corpo, color: T.textSecondary }}>{tx("anat_hoje_nota")}</p>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "flex-start" }}>
            {pontos && typeof onVerSemEsta === "function" ? (
              <button type="button" aria-pressed={!!selecionada} onClick={() => onVerSemEsta(perna.id)} {...comFoco}
                style={{ ...BOTAO, color: selecionada ? T.accent : T.textSecondary, borderColor: selecionada ? T.accent : T.borderSubtle }}>
                {tx(selecionada ? "anat_ver_total" : "anat_ver_sem_esta")}
              </button>
            ) : null}

            {!encerravel ? (
              <div style={{ ...TIPO.corpo, color: T.textSecondary }}>
                {tx(pos && pos.lastro ? "pernas_na_estrutura" : "pernas_vendida_sem_acao")}
              </div>
            ) : emCurso ? (
              <div role="status" aria-busy="true" style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("pernas_encerrando")}</div>
            ) : vetado ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <button type="button" aria-disabled="true" aria-label={tx("pernas_encerrar_aria", { id: perna.id })}
                  aria-describedby={idVeto} {...comFoco}
                  style={{ ...BOTAO, alignSelf: "flex-start", cursor: "not-allowed", opacity: 0.7 }}>
                  {tx("pernas_encerrar")}
                </button>
                <div id={idVeto} style={{ ...TIPO.corpo, color: T.textPrimary }}>{(perna.encerrar && perna.encerrar.texto) || "—"}</div>
              </div>
            ) : confirmando ? null : (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <button type="button" ref={refEncerrar} aria-label={tx("pernas_encerrar_aria", { id: perna.id })}
                  aria-describedby={avisoEnc ? idVeto : undefined}
                  onClick={() => setConfirmando(true)} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start" }}>
                  {tx("pernas_encerrar")}
                </button>
                {avisoEnc ? <div id={idVeto} style={{ ...TIPO.corpo, color: T.textPrimary }}>{avisoEnc}</div> : null}
              </div>
            )}
          </div>

          {encerravel && !emCurso && !vetado && confirmando ? (
            <div role="group" aria-labelledby={idConfirma}
              style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "12px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}` }}>
              <p id={idConfirma} style={{ margin: 0, ...TIPO.corpo, color: T.textPrimary }}>{textoConfirma}</p>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <button type="button" ref={refCancelar} onClick={() => setConfirmando(false)} {...comFoco} style={BOTAO}>
                  {tx("pernas_cancelar")}
                </button>
                <button type="button" onClick={confirmar} {...comFoco} style={{ ...BOTAO, color: T.accent, borderColor: T.accent }}>
                  {tx("pernas_confirmar_sim")}
                </button>
              </div>
            </div>
          ) : null}
        </div>

        {pontos ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <GraficoAnatomia compacto precos={precos} series={[{ id: perna.id, valores: pontos, traco: 0 }]}
              area={pontos} marcadores={marcadores} cursorIdx={cursorIdx}
              titulo={perna.aria} descricao={perna.condicao || perna.aria} />
            <div style={{ ...TIPO.label, color: T.textSecondary }}>{tx("anat_legenda_perda")} · {tx("anat_legenda_ganho")}</div>
            <details>
              <summary {...comFoco}
                style={{ minHeight: ALVO_MIN + "px", display: "flex", alignItems: "center", cursor: "pointer", ...TIPO.label, color: T.textSecondary }}>
                {tx("anat_ver_tabela")}
              </summary>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", ...TIPO.corpo, color: T.textSecondary }}>
                  <thead>
                    <tr>
                      <th scope="col" style={{ textAlign: "left", ...TIPO.label }}>{tx("anat_tabela_preco", { ticker: ticker || "" })}</th>
                      <th scope="col" style={{ textAlign: "right", ...TIPO.label }}>{tx("anat_tabela_perna")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tabela.map((l, i) => (
                      <tr key={i}>
                        <td style={{ ...MONO }}>R$ {fmt(l.preco)}</td>
                        <td style={{ ...MONO, ...NUM, textAlign: "right" }}>{fmtBRLsinal(l.resultado)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </div>
        ) : null}
      </div>
    </article>
  );
}
