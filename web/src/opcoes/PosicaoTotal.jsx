/**
 * PosicaoTotal.jsx — Fase 49 (2026-10-06), ANAT-04/05/07.
 * Gráfico total do ativo. Lê pontos/semEsta do motor por índice da grade;
 * ligar/desligar chip pede nova leitura (onAlternar), nunca soma no cliente.
 * O preço do slider é hipótese do usuário, rotulada como tal. Ausência de
 * número vira travessão ou a frase do motor, nunca zero.
 *
 * Onda H (2026-10-08, quick 261008-oos): chip com estado explícito (ligado =
 * preenchido com contorno de destaque; desligado = contorno apagado, amostra
 * esmaecida), em grade de 3 colunas (até 6 itens em 2 linhas no iPhone;
 * decisão H-D5); legenda do gráfico começa com a amostra do traço do total.
 */
import { useId } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import GraficoAnatomia, { TRACOS } from "./GraficoAnatomia.jsx";
import { T, FOCO, TIPO, MONO, NUM, ALVO_MIN } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace("-", "−")
    : "—";
const fmtBRL = (v) => (ehNum(v) ? (v < 0 ? "−" : "") + "R$ " + fmt(Math.abs(v)) : "—");
const fmtBRLsinal = (v) => (ehNum(v) ? (v > 0 ? "+" : "") + fmtBRL(v) : "—");

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

function Amostra({ traco, apagada }) {
  const d = TRACOS[traco % TRACOS.length];
  return (
    <svg width="16" height="10" viewBox="0 0 16 10" aria-hidden="true" focusable="false" style={{ flexShrink: 0, opacity: apagada ? 0.4 : 1 }}>
      <line x1="0" y1="5" x2="16" y2="5" style={{ stroke: T.accent }} strokeWidth="1.5" strokeDasharray={d || undefined} />
    </svg>
  );
}

function Chip({ ligado, onClick, traco, children }) {
  return (
    <button type="button" aria-pressed={ligado} onClick={onClick} {...comFoco}
      style={{
        minHeight: ALVO_MIN + "px", padding: "4px 8px", borderRadius: "999px", boxSizing: "border-box", minWidth: 0,
        background: ligado ? T.accentTint10 : "transparent",
        border: ligado ? `1px solid ${T.accent}` : `1px solid ${T.borderSubtle}`,
        color: ligado ? T.textPrimary : T.textMuted, ...TIPO.label, cursor: "pointer",
        display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "6px",
      }}>
      {traco !== null ? <Amostra traco={traco} apagada={!ligado} /> : null}
      <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{children}</span>
    </button>
  );
}

export default function PosicaoTotal({ mode, ticker, anatomia, excluidas, onAlternar, idx, onIdx, selecionada, recalculando, obsoleto }) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const uid = String(useId()).replace(/[^A-Za-z0-9_-]/g, "");
  if (!anatomia) return null;
  const idTitulo = "anat-total-" + uid;
  const idSlider = "anat-slider-" + uid;
  const grade = anatomia.grade || {};
  const precos = Array.isArray(grade.precos) ? grade.precos : [];
  const total = anatomia.total || {};
  // CR-01 (49-REVIEW): releitura falhou => os pontos guardados são de outra hipótese; não se exibem.
  const pontos = !obsoleto && Array.isArray(total.pontos) ? total.pontos : null;
  const semEsta = total.semEsta || {};
  const pernas = (Array.isArray(anatomia.pernas) ? anatomia.pernas : []).filter((p) => p && Array.isArray(p.pontos));
  const acoes = anatomia.acoes && typeof anatomia.acoes === "object" ? anatomia.acoes : null;
  const ex = Array.isArray(excluidas) ? excluidas : [];
  const i = Number.isInteger(idx) && idx >= 0 && idx < precos.length
    ? idx
    : (Number.isInteger(grade.indiceInicial) && grade.indiceInicial >= 0 && grade.indiceInicial < precos.length ? grade.indiceInicial : 0);
  const preco = fmt(precos[i]);
  const titulo = anatomia.vencimentoTexto
    ? tx("anat_total_titulo", { vencimento: anatomia.vencimentoTexto })
    : tx("anat_total_titulo_sem_data");

  const perna = selecionada ? pernas.find((p) => p.id === selecionada) || null : null;

  let leitura = null;
  if (obsoleto) {
    leitura = <span role="status">{tx("anat_desatualizado")}</span>;
  } else if (!pontos) {
    leitura = total.motivoTexto ? <span role="status">{total.motivoTexto}</span> : null;
  } else if (perna) {
    const sem = Array.isArray(semEsta[perna.id]) ? semEsta[perna.id] : null;
    leitura = sem
      ? tx("anat_leitura_com_sem", { preco, id: perna.id, com: fmtBRLsinal(pontos[i]), sem: fmtBRLsinal(sem[i]), contrib: fmtBRLsinal(perna.pontos[i]) })
      : tx("anat_sem_esta_vazio", { id: perna.id });
  } else {
    leitura = tx("anat_leitura_total", { preco, valor: fmtBRLsinal(pontos[i]) });
  }

  const series = [];
  if (pontos) {
    pernas.forEach((p, k) => {
      if (p.incluida === false || ex.includes(p.id)) return;
      series.push({ id: p.id, valores: p.pontos, traco: k % 4, apagada: !!selecionada && selecionada !== p.id, destaque: selecionada === p.id });
    });
    series.push({ id: "total", tipo: "total", valores: pontos, apagada: !!selecionada });
  }
  const rotMarc = (m) =>
    m.chave === "strike" ? tx("anat_marcador_strike", { strike: fmt(m.preco) })
      : m.chave === "precoMedio" ? tx("anat_marcador_pm")
        : m.chave === "hoje" ? tx("anat_marcador_hoje") : tx("anat_marcador_equilibrio");
  const marcadores = (Array.isArray(total.marcadores) ? total.marcadores : []).map((m) => ({ preco: m.preco, rotulo: rotMarc(m), comPreco: m.chave !== "strike" }));
  const tabela = Array.isArray(total.tabela) ? total.tabela : [];
  const pmOk = !!(acoes && ehNum(acoes.precoMedio));

  return (
    <section aria-labelledby={idTitulo}
      style={{ padding: "16px", borderRadius: "18px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, boxSizing: "border-box", display: "flex", flexDirection: "column", gap: "12px" }}>
      <h3 id={idTitulo} style={{ margin: 0, ...TIPO.titulo, color: T.textPrimary }}>{titulo}</h3>

      <div role="group" aria-label={tx("anat_chips_aria")} style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "6px" }}>
        {pernas.map((p, k) => (
          <Chip key={p.id} ligado={!ex.includes(p.id)} traco={k % 4} onClick={() => onAlternar && onAlternar(p.id)}>
            {tx("anat_chip_perna", { tipo: String(p.tipo || "—"), strike: fmt(p.strike) })}
          </Chip>
        ))}
        {pmOk ? (
          <Chip ligado={!ex.includes("ACOES")} traco={null} onClick={() => onAlternar && onAlternar("ACOES")}>
            {tx("anat_chip_acoes", { qtd: ehNum(acoes.quantidade) ? String(acoes.quantidade) : "—" })}
          </Chip>
        ) : null}
      </div>

      {pontos ? (
        <>
          <GraficoAnatomia precos={precos} series={series} area={pontos} marcadores={marcadores} cursorIdx={i}
            titulo={titulo} descricao={total.aria || titulo} />
          <div style={{ ...TIPO.label, color: T.textSecondary, display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <svg width="16" height="10" viewBox="0 0 16 10" aria-hidden="true" focusable="false" style={{ flexShrink: 0 }}>
              <line x1="0" y1="5" x2="16" y2="5" style={{ stroke: T.textPrimary }} strokeWidth="3" />
            </svg>
            <span>{tx("anat_tabela_total")} · {tx("anat_legenda_perda")} · {tx("anat_legenda_ganho")}</span>
          </div>
        </>
      ) : null}

      {pontos && precos.length > 1 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <label htmlFor={idSlider} style={{ ...TIPO.corpo, color: T.textPrimary }}>
            {tx("anat_slider_rotulo", { ticker: ticker || "", preco })}
          </label>
          <input id={idSlider} type="range" min={0} max={precos.length - 1} step={1} value={i}
            onChange={(e) => onIdx && onIdx(Number(e.target.value))} aria-valuetext={"R$ " + preco} {...comFoco}
            style={{ width: "100%", minHeight: ALVO_MIN + "px", accentColor: T.accent }} />
        </div>
      ) : null}

      <div aria-live="polite" style={{ ...TIPO.corpo, color: T.textPrimary, ...NUM }}>{leitura}</div>

      {acoes && acoes.texto ? <p style={{ margin: 0, ...TIPO.corpo, color: T.textSecondary }}>{acoes.texto}</p> : null}

      {recalculando ? <div role="status" style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("anat_recalculando")}</div> : null}

      {pontos ? (
        <details>
          <summary {...comFoco}
            style={{ minHeight: "44px", display: "flex", alignItems: "center", cursor: "pointer", ...TIPO.label, color: T.textSecondary }}>
            {tx("anat_ver_tabela")}
          </summary>
          <div data-sem-gesto-voltar style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", ...TIPO.corpo, color: T.textSecondary }}>
              <thead>
                <tr>
                  <th scope="col" style={{ textAlign: "left", ...TIPO.label }}>{tx("anat_tabela_preco", { ticker: ticker || "" })}</th>
                  <th scope="col" style={{ textAlign: "right", ...TIPO.label }}>{tx("anat_tabela_total")}</th>
                </tr>
              </thead>
              <tbody>
                {tabela.map((l, k) => (
                  <tr key={k}>
                    <td style={{ ...MONO }}>R$ {fmt(l.preco)}</td>
                    <td style={{ ...MONO, ...NUM, textAlign: "right" }}>{fmtBRLsinal(l.resultado)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </section>
  );
}
