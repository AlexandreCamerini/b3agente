/**
 * ConfirmarEstrutura.jsx — Fase 48 (48-08): tela 4 (confirmar) do UI-SPEC.
 *
 * Execução pelo MESMO despacho existente (`onExecutar` ->
 * `A.executarCandidatoCurado` -> `executarCandidato.js`), com o candidato
 * COPIADO de `degrau.execucao` — zero aritmética financeira (T-48-28). No
 * Estudo não há botão (o 403 do servidor é a defesa real, T-48-29). O
 * consentimento de liquidez DIFÍCIL só entra por identidade `=== true`
 * (T-48-30), mesmo padrão de ExecutarProposta.jsx.
 */
import { useState } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import { ehRecusaLiquidezDificil } from "./ExecutarProposta.jsx";
import { Aviso } from "./uiOpcoes.jsx";
import TermoOpcoes from "./TermoOpcoes.jsx";
import { T, FOCO, TIPO, MONO, DISPLAY, ALVO_MIN, CTA_MIN, reduzido, transicaoTela } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);
// Só formatação de exibição (pt-BR, 2 casas); ausente vira "—", nunca 0.
const br = (v) => (ehNum(v) ? v.toFixed(2).replace(".", ",") : "—");

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

const BOTAO = {
  minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, ...TIPO.label, cursor: "pointer",
};

const INICIAL = { busy: false, erro: null, aceite: false };

export default function ConfirmarEstrutura({
  cp, mode, operador, ticker, degrau, onExecutar, onConcluido, onVoltar, onCriarVigia,
  didatica, A, kbCatalogo, onAbrirVerbete,
}) {
  const [st, setSt] = useState(INICIAL);
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const d = degrau || {};
  const ex = d.execucao || {};
  const strikes = d.strikes || {};
  const porAcao = d.porAcao || {};
  const temPut = ehNum(strikes.put);
  const temCall = ehNum(strikes.call);
  const contratos = ex.contratos;
  const qtd = ehNum(ex.qtyAcoes) ? ex.qtyAcoes : d.qtdAcoes;

  const executar = async () => {
    setSt((s) => ({ ...s, busy: true, erro: null }));
    const cand = {
      tipo: ex.tipo, ticker, contractSymbol: ex.contractSymbol, expiration: ex.expiration,
      contratos: ex.contratos, qtyAcoes: ex.qtyAcoes, idCandidato: ex.idCandidato,
      pernasContratos: ex.pernasContratos,
    };
    try {
      await onExecutar(cand, { aceitaLiquidezDificil: st.aceite === true, origem: "escada" });
      setSt(INICIAL);
      if (onConcluido) onConcluido();
    } catch (err) {
      // verbatim do servidor/motor; sem reenvio automático
      setSt({ busy: false, erro: (err && err.message) || String(err), aceite: false });
    }
  };

  const recusaLiquidez = ehRecusaLiquidezDificil(st.erro);
  const travado = st.busy || (recusaLiquidez && st.aceite !== true);

  let acao;
  if (!operador) {
    acao = <div style={{ ...TIPO.corpo, color: T.textMuted, fontStyle: "italic" }}>{tx("estudo_nao_executa")}</div>;
  } else if (ex.executavel !== true) {
    acao = ex.motivo ? <Aviso>{ex.motivo}</Aviso> : null;
  } else {
    acao = (
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {st.erro && (
          <div role="alert" style={{ padding: "12px", borderRadius: "12px", border: `1px solid ${T.negative}`, ...TIPO.corpo, color: T.textPrimary }}>
            {tx("ordem_rejeitada", { motivo: st.erro })}
          </div>
        )}
        {recusaLiquidez && (
          <label style={{ display: "flex", alignItems: "flex-start", gap: "8px", ...TIPO.corpo, color: T.textSecondary }}>
            <input type="checkbox" checked={st.aceite === true}
              onChange={(ev) => setSt((s) => ({ ...s, aceite: ev.target.checked }))}
              style={{ marginTop: "4px", minWidth: "20px", minHeight: "20px" }} />
            <span>{cp && cp.curadoriaLiquidezConsentir}</span>
          </label>
        )}
        <button type="button" onClick={executar} disabled={travado} {...comFoco}
          style={{
            minHeight: CTA_MIN + "px", width: "100%", padding: "8px 16px", borderRadius: "12px",
            border: "none", background: T.accent, color: T.onAccent, ...TIPO.titulo,
            opacity: travado ? 0.55 : 1, cursor: travado ? "default" : "pointer",
          }}>
          {st.busy ? tx("consultando") : tx("cta_executar")}
        </button>
        <div style={{ ...TIPO.label, fontWeight: 400, color: T.textMuted, textAlign: "center" }}>{tx("sem_custo")}</div>
      </div>
    );
  }

  return (
    <section style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px", ...transicaoTela(reduzido()) }}>
      <div>
        <button type="button" onClick={onVoltar} {...comFoco} style={{ ...BOTAO, border: "none", color: T.accent, paddingLeft: 0 }}>
          {tx("voltar")}
        </button>
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("aviso_virtual")}</div>
      </div>

      <h2 tabIndex={-1} style={{ margin: 0, ...TIPO.titulo, fontFamily: DISPLAY, color: T.textPrimary }}>
        {tx("confirmar_titulo")}
        {ticker ? <span style={{ color: T.textMuted, ...MONO }}>{" · " + ticker}</span> : null}
      </h2>

      <div aria-live="polite" style={{ ...TIPO.corpo, color: T.textPrimary }}>
        {d.fraseRisco || tx("dado_insuficiente")}
      </div>

      <div style={{ padding: "12px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, display: "flex", flexDirection: "column", gap: "8px", ...TIPO.corpo }}>
        <div>
          <span style={{ ...TIPO.label, color: T.textMuted }}>{tx("confirmar_estrutura")}</span>{" "}
          <span style={{ color: T.textPrimary }}>
            <TermoOpcoes texto={d.nome || "—"} termos={Array.isArray(d.termos) ? d.termos : []} dados={{ ticker }}
              A={A} didatica={didatica} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
          </span>
        </div>
        <div>
          <span style={{ ...TIPO.label, color: T.textMuted }}>{tx("confirmar_vencimento")}</span>{" "}
          <span style={{ color: T.textPrimary }}>{d.vencimentoTexto || "—"}</span>
        </div>
        {temPut && (
          <div style={{ color: T.textPrimary }}>
            {tx("perna_put_comprada", { strike: br(strikes.put), premio: br(porAcao.premioPago) })}
          </div>
        )}
        {temCall && (
          <div style={{ color: T.textPrimary }}>
            {tx("perna_call_vendida", { strike: br(strikes.call), premio: br(porAcao.premioRecebido) })}
          </div>
        )}
        <div style={{ color: T.textSecondary }}>
          {tx("confirmar_lote", { contratos: ehNum(contratos) ? contratos : "—", qtd: ehNum(qtd) ? qtd : "—" })}
        </div>
        <div style={{ color: T.textSecondary }}>
          {temCall ? tx("lastro_trava", { qtd: ehNum(qtd) ? qtd : "—" }) : tx("lastro_livre")}
        </div>
      </div>

      {acao}

      {onCriarVigia && (
        <button type="button" onClick={onCriarVigia} {...comFoco}
          style={{ ...BOTAO, width: "100%", color: T.accent, borderColor: T.accent }}>
          {tx("cta_criar_vigia")}
        </button>
      )}
    </section>
  );
}
