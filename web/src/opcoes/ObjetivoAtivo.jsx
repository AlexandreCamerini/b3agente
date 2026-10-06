/**
 * ObjetivoAtivo.jsx — Fase 48 (48-08): tela 2 (objetivo por ativo) do UI-SPEC.
 *
 * 3 cards na ORDEM que o backend entrega (proteger, renda, collar). Objetivo
 * inviável fica `aria-disabled` com o MOTIVO escrito no card — nunca oculto.
 * Zero cálculo; texto via `opcoesEscadaTxt`; zero import de App.jsx.
 */
import { opcoesEscadaTxt } from "../copy.js";
import TermoOpcoes from "./TermoOpcoes.jsx";
import { T, FOCO, TIPO, DISPLAY, ALVO_MIN, SR_ONLY, reduzido, transicaoTela } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

const BOTAO = {
  minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, ...TIPO.label, cursor: "pointer",
};

export default function ObjetivoAtivo({
  cp, mode, ticker, escada, estruturaAberta, pernasAbertas, onEscolher, onMontarDoZero, onVoltar,
  didatica, A, kbCatalogo, onAbrirVerbete, onTentarDeNovo, onIrCarteira,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const e = escada || {};
  const dados = e.dados || null;
  const objetivos = dados && Array.isArray(dados.objetivos) ? dados.objetivos : [];
  const qtd = dados && dados.posicao && ehNum(dados.posicao.qty) ? String(dados.posicao.qty) : "—";
  const semPosicao = dados && dados.estado === "sem_posicao";
  // Fase 48 gap G-01 (2026-10-05): quando os objetivos caem pela mesma causa, o backend
  // manda UMA frase real (objetivosMotivo) + dica; os cards só apontam para ela.
  const motivoUnico = dados && dados.objetivosMotivo && dados.objetivosMotivo.texto ? dados.objetivosMotivo : null;
  const idMotivo = "objetivos-motivo-" + ticker;

  return (
    <section style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px", ...transicaoTela(reduzido()) }}>
      <div>
        <button type="button" onClick={onVoltar} {...comFoco} style={{ ...BOTAO, border: "none", color: T.accent, paddingLeft: 0 }}>
          {tx("voltar")}
        </button>
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("aviso_virtual")}</div>
      </div>

      <header>
        <h2 tabIndex={-1} style={{ margin: 0, ...TIPO.titulo, fontFamily: DISPLAY, color: T.textPrimary }}>
          {tx("pergunta_objetivo", { qtd })}
          {ticker ? <span style={{ color: T.textMuted }}>{" · " + ticker}</span> : null}
        </h2>
        <p style={{ margin: "4px 0 0", ...TIPO.corpo, color: T.textSecondary }}>{tx("pergunta_objetivo_sub")}</p>
      </header>

      {/* Fase 48 gap G-02 (2026-10-05): a saída das pernas vem antes de qualquer estado da escada. */}
      {pernasAbertas || null}

      {estruturaAberta || null}

      {e.carregando ? (
        <div role="status" style={{ position: "relative", display: "flex", flexDirection: "column", gap: "16px" }}>
          <span style={SR_ONLY}>{tx("carregando")}</span>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ minHeight: "64px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }} />
          ))}
        </div>
      ) : e.erro ? (
        <div role="alert" style={{ padding: "12px", borderRadius: "12px", border: `1px solid ${T.warn}`, ...TIPO.corpo, color: T.textPrimary, display: "flex", flexDirection: "column", gap: "8px" }}>
          <span>{tx("erro_fonte")}</span>
          <button type="button" onClick={onTentarDeNovo} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start" }}>
            {tx("tentar_de_novo")}
          </button>
        </div>
      ) : semPosicao ? (
        <div style={{ padding: "16px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{dados.motivoTexto || tx("dado_insuficiente")}</div>
          {onIrCarteira && (
            <button type="button" onClick={onIrCarteira} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start", color: T.accent, borderColor: T.accent }}>
              {tx("hub_vazio_cta")}
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {motivoUnico ? (
            <div id={idMotivo} role="status" style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ ...TIPO.corpo, color: T.textPrimary }}>{motivoUnico.texto}</div>
              {motivoUnico.dica ? <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{motivoUnico.dica}</div> : null}
            </div>
          ) : null}
          {objetivos.map((o) => {
            const indisponivel = o.disponivel === false;
            const escolher = () => { if (!indisponivel && onEscolher) onEscolher(o.id); };
            const motivo = indisponivel
              ? (motivoUnico
                ? tx("objetivo_indisponivel_ver_motivo", { objetivo: o.titulo || "—" })
                : tx("objetivo_indisponivel", { objetivo: o.titulo || "—", motivo: o.motivo || "—" }))
              : null;
            const aoTeclar = (ev) => {
              if (ev.target !== ev.currentTarget) return;
              if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); escolher(); }
            };
            return (
              <div key={o.id} role="button" tabIndex={0}
                aria-disabled={indisponivel ? "true" : undefined}
                aria-describedby={indisponivel && motivoUnico ? idMotivo : undefined}
                onClick={indisponivel ? undefined : escolher}
                onKeyDown={indisponivel ? undefined : aoTeclar}
                {...comFoco}
                style={{
                  minHeight: 64, padding: "12px", borderRadius: "12px", background: T.bgPanel,
                  border: `1px solid ${T.borderSubtle}`, color: T.textPrimary,
                  cursor: indisponivel ? "not-allowed" : "pointer",
                  opacity: indisponivel ? 0.7 : 1, display: "flex", flexDirection: "column", gap: "8px",
                }}>
                <div style={{ ...TIPO.titulo, fontFamily: DISPLAY }}>{o.titulo || "—"}</div>
                <div style={{ ...TIPO.corpo, color: T.textSecondary }}>
                  <TermoOpcoes texto={o.descricao} termos={o.termos} dados={{ ticker }}
                    A={A} didatica={didatica} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
                </div>
                {o.perde ? <div style={{ ...TIPO.corpo, color: T.textMuted }}>{o.perde}</div> : null}
                {/* Fase 48 (48-13): motivo em textPrimary — warn sobre bgPanel mede 4,32:1 no tema claro (< AA); o texto do motivo já carrega o aviso. */}
                {motivo ? <div style={{ ...TIPO.label, color: T.textPrimary }}>{motivo}</div> : null}
                {indisponivel && !motivoUnico && o.dica ? <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{o.dica}</div> : null}
              </div>
            );
          })}
        </div>
      )}

      <button type="button" onClick={onMontarDoZero} {...comFoco}
        style={{ ...BOTAO, border: "none", color: T.accent, alignSelf: "flex-start", textDecoration: "underline" }}>
        {tx("montar_do_zero")}
      </button>
    </section>
  );
}
