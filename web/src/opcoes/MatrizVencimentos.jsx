/**
 * MatrizVencimentos.jsx — Fase 48 (48-09): matriz vencimento x degrau da
 * comparação paga (tela 3). Só renderiza o que o backend devolveu; a chamada
 * paga é do hook (useEscada.verMatriz), nunca daqui. Célula sem dado ou com
 * motivo vira "—" + motivo curto, `aria-disabled`, não selecionável.
 * Sem overflow horizontal em 375px (grid de 3 colunas flexíveis).
 */
import { opcoesEscadaTxt } from "../copy.js";
import { T, FOCO, TIPO, MONO, SR_ONLY } from "./fluxoEstilo.js";

const CELULA_MIN = 52;
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

export default function MatrizVencimentos({ cp, mode, objetivo, matriz, selecionado, onSelecionar, onTentarDeNovo }) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const m = matriz || {};
  const dados = m.dados || null;
  const linhas = dados && dados.matriz && Array.isArray(dados.matriz[objetivo]) ? dados.matriz[objetivo] : [];
  const ehRenda = objetivo === "renda";
  const ehCollar = objetivo === "collar";

  if (m.carregando) {
    return (
      <div role="status" style={{ ...TIPO.corpo, color: T.textSecondary }}>
        <span style={SR_ONLY}>{tx("consultando")}</span>
        <div style={{ minHeight: CELULA_MIN + "px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }} />
      </div>
    );
  }

  if (m.erro) {
    const cota = m.erro.code === "mcp_cota";
    return (
      <div role="alert" style={{ padding: "16px", borderRadius: "12px", border: `1px solid ${T.warn}`, background: T.bgPanel, ...TIPO.corpo, color: T.textPrimary, display: "flex", flexDirection: "column", gap: "8px" }}>
        <span>{cota ? tx("cota_esgotada", { quando: (m.erro.reinicia || "—") }) : (m.erro.message || tx("erro_fonte"))}</span>
        {cota ? null : (
          <button type="button" onClick={onTentarDeNovo} {...comFoco}
            style={{ alignSelf: "flex-start", minHeight: "44px", padding: "8px 16px", borderRadius: "12px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textPrimary, ...TIPO.label, cursor: "pointer" }}>
            {tx("tentar_de_novo")}
          </button>
        )}
      </div>
    );
  }

  if (!dados) return null;

  const cabecalho = [0, 1, 2].map((i) => tx(`degrau_${objetivo}_${i}`) || "—");
  const fr = dados.frescor || null;
  const situacao = fr && fr.medido === true && fr.bloqueia !== true ? tx("situacao_em_dia") : tx("situacao_fim_pregao");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "auto repeat(3, minmax(0, 1fr))", gap: "8px", alignItems: "end" }}>
        <span style={SR_ONLY}>{tx("comparar_rotulo")}</span>
        <span />
        {cabecalho.map((c, i) => (
          <span key={i} style={{ ...TIPO.label, color: T.textSecondary, overflowWrap: "anywhere" }}>{c}</span>
        ))}
      </div>

      {linhas.length === 0 ? (
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{dados.motivo || tx("dado_insuficiente")}</div>
      ) : null}

      {linhas.map((l, li) => {
        const celulas = Array.isArray(l.celulas) ? l.celulas : [];
        return (
          <div key={l.vencimento || li} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "auto repeat(3, minmax(0, 1fr))", gap: "8px", alignItems: "stretch" }}>
              <span style={{ ...TIPO.label, ...MONO, color: T.textPrimary, alignSelf: "center" }}>{ddmm(l.vencimento)}</span>
              {[0, 1, 2].map((i) => {
                const c = celulas[i] || null;
                const sem = !c || c.motivo || l.motivo;
                if (sem) {
                  return (
                    <div key={i} aria-disabled="true"
                      style={{ minHeight: CELULA_MIN + "px", padding: "8px", boxSizing: "border-box", borderRadius: "12px", border: `1px dashed ${T.borderSubtle}`, ...TIPO.corpo, color: T.textMuted }}>
                      <div style={{ ...MONO }}>{tx("matriz_sem_dado")}</div>
                      {c && c.motivo ? <div>{c.motivo}</div> : null}
                    </div>
                  );
                }
                const marcado = !!(selecionado && selecionado.vencimento === l.vencimento && selecionado.id === c.id);
                const principal = ehRenda ? c.total && c.total.ganhoMaximo : (c.total && c.total.perdaMaxima);
                const rotPrincipal = ehRenda ? tx("matriz_ganho") : tx("matriz_pior");
                let rotCusto;
                let valCusto;
                if (ehRenda) { rotCusto = tx("col_premio_recebido"); valCusto = c.total && c.total.premioRecebido; }
                else if (ehCollar) {
                  valCusto = c.total && c.total.liquido;
                  rotCusto = ehNum(valCusto) && valCusto < 0 ? tx("col_liquido_custa") : tx("col_liquido_recebe");
                } else { rotCusto = tx("col_custo_protecao"); valCusto = c.total && c.total.premioPago; }
                return (
                  <button key={i} type="button" aria-pressed={marcado} onClick={() => onSelecionar && onSelecionar(c, l.vencimento)} {...comFoco}
                    style={{ minHeight: CELULA_MIN + "px", padding: "8px", boxSizing: "border-box", borderRadius: "12px", cursor: "pointer", textAlign: "left",
                      border: `1px solid ${marcado ? T.accent : T.borderSubtle}`, background: marcado ? T.accentTint10 : T.bgPanel,
                      color: T.textPrimary, ...TIPO.corpo, minWidth: 0 }}>
                    <div style={{ color: T.textMuted }}>{rotPrincipal}</div>
                    <div style={{ ...MONO }}>R$ {fmt(principal)}</div>
                    <div style={{ color: T.textMuted }}>{rotCusto}</div>
                    <div style={{ ...MONO }}>R$ {fmt(valCusto)}</div>
                  </button>
                );
              })}
            </div>
            {l.motivo ? <div style={{ ...TIPO.corpo, color: T.textMuted }}>{l.motivo}</div> : null}
          </div>
        );
      })}

      <div style={{ ...TIPO.corpo, color: T.textMuted }}>
        {tx("frescor", { fonte: dados.fonte || "—", data: ddmm(dados.pregao), situacao })}
      </div>
    </div>
  );
}
