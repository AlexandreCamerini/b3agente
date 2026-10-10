/**
 * HubOpcoes.jsx — Fase 48 (48-08): tela 1 (hub) do UI-SPEC. Cards da CARTEIRA
 * (só ativos com posição; quick 261006-axi, 2026-10-06: ativos com perna aberta
 * e sem ações entram como card "sem ações", `pos.semAcoes`), seção Atenção (vigias) com custo declarado antes do
 * clique, frescor, aviso de dinheiro virtual e todos os estados.
 *
 * Zero cálculo: todo número vem pronto do backend ou da carteira; campo
 * ausente vira "—". Todo texto vem de `opcoesEscadaTxt` (espelho do motor).
 * Zero import de App.jsx (ciclo).
 */
import { opcoesEscadaTxt } from "../copy.js";
import { qtyLivre } from "../finance.js";
import ReguaRegime from "./ReguaRegime.jsx";
import { formatarVolatilidade } from "./unidades.js";
import TermoOpcoes from "./TermoOpcoes.jsx";
import { T, FOCO, TIPO, MONO, NUM, DISPLAY, ALVO_MIN, reduzido, transicaoTela } from "./fluxoEstilo.js";

const ehNum = (v) => typeof v === "number" && isFinite(v);
const vz = (v) => (ehNum(v) ? String(v).replace(".", ",") : "—");

const TERMO_LASTRO = [{ rotulo: "lastro", kb: "opc-lastro" }];

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};
const teclaAtiva = (fn) => (e) => {
  if (e.target !== e.currentTarget) return; // Enter/Espaço em controle interno não ativa o card
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fn(); }
};

const BOTAO = {
  minHeight: ALVO_MIN + "px", padding: "8px 16px", borderRadius: "12px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, ...TIPO.label, cursor: "pointer",
};

function Chip({ children }) {
  return (
    <span style={{ ...TIPO.label, ...MONO, padding: "4px 8px", borderRadius: "999px", background: T.bgBase, border: `1px solid ${T.borderSubtle}`, color: T.textSecondary }}>
      {children}
    </span>
  );
}

function Skeleton({ cp, mode }) {
  return (
    <div role="status" style={{ minHeight: "64px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, ...(reduzido() ? {} : { opacity: 0.7 }) }}>
      <span style={{ position: "absolute", width: "1px", height: "1px", overflow: "hidden", clipPath: "inset(50%)" }}>
        {opcoesEscadaTxt(mode, "carregando")}
      </span>
    </div>
  );
}

function Frescor({ mode, frescor }) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const f = frescor || {};
  const sit = typeof f.situacao === "string" ? f.situacao.replace(/-/g, "_") : "";
  const situacaoTxt = ["em_dia", "atrasado", "fim_pregao"].includes(sit)
    ? opcoesEscadaTxt(mode, "situacao_" + sit)
    : (typeof f.situacao === "string" && f.situacao ? f.situacao : "—");
  const linha = opcoesEscadaTxt(mode, "frescor", {
    fonte: f.fonte || "—", data: f.pregao || "—", situacao: situacaoTxt,
  });
  const fechado = f.mercadoAberto === false;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px", marginTop: "4px" }}>
      <span style={{ ...TIPO.corpo, color: T.textMuted }}>{linha}</span>
      {fechado && (
        <span style={{ ...TIPO.label, padding: "2px 8px", borderRadius: "999px", border: `1px solid ${T.warn}`, color: T.warn }}>
          {tx("mercado_fechado", { data: f.pregao || "—" })}
        </span>
      )}
      {f.atrasado === true && (
        <span style={{ ...TIPO.label, color: T.warn }}>{opcoesEscadaTxt(mode, "atrasado_frase")}</span>
      )}
    </div>
  );
}

function CardAtivo({ cp, mode, pos, tecnico, estrutura, nVigias, onAbrir, didatica, A, kbCatalogo, onAbrirVerbete }) {
  const t = pos.ticker;
  const dados = tecnico && tecnico.dados;
  const vol = dados && dados.volatilidade;
  const niveis = dados && dados.niveis;
  const sub = pos.semAcoes === true
    ? opcoesEscadaTxt(mode, "card_subtitulo_sem_acoes") || ""
    : opcoesEscadaTxt(mode, "card_subtitulo", { qtd: vz(pos.qty), livres: vz(qtyLivre(pos)) }) || "";
  const nomeEstr = estrutura && estrutura.nome;
  const rodape = nomeEstr
    ? opcoesEscadaTxt(mode, "card_estrutura_aberta", { nome: nomeEstr })
    : opcoesEscadaTxt(mode, "card_sem_estrutura");
  const abrir = () => onAbrir && onAbrir(t);
  return (
    <div role="button" tabIndex={0} onClick={abrir} onKeyDown={teclaAtiva(abrir)} {...comFoco}
      style={{ minHeight: 64, padding: "12px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, color: T.textPrimary, cursor: "pointer", display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "8px" }}>
        <span style={{ ...TIPO.titulo, ...MONO }}>{t}</span>
        <span aria-hidden="true" style={{ ...TIPO.titulo, color: T.textMuted }}>›</span>
      </div>
      <div style={{ ...TIPO.corpo, color: T.textSecondary }}>
        <TermoOpcoes texto={sub} termos={TERMO_LASTRO} A={A} didatica={didatica} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
      </div>
      {dados && dados.regua ? <ReguaRegime regua={dados.regua} cp={cp} semAjuda /> : null}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        <Chip>{"HV21 " + (vol ? formatarVolatilidade(vol.hv21Pct, vol.unidade) : "—")}</Chip>
        <Chip>{"suporte " + vz(niveis && niveis.nearestSupport)}</Chip>
        <Chip>{"resistência " + vz(niveis && niveis.nearestResistance)}</Chip>
      </div>
      <div style={{ ...TIPO.label, color: T.textMuted, display: "flex", justifyContent: "space-between", gap: "8px" }}>
        <span>{rodape}</span>
        <span style={{ whiteSpace: "nowrap", flexShrink: 0 }}>{opcoesEscadaTxt(mode, "card_vigias", { n: nVigias })}</span>
      </div>
    </div>
  );
}

export default function HubOpcoes({
  cp, mode, carteira, opcoesPorTicker, tecnicoPorTicker, vigiasLista, vigiasComEstado,
  carregandoVigias, onAtualizarVigias, custoAtualizar, onVerTodosVigias, onAbrirAtivo,
  onIrCarteira, frescor, didatica, A, kbCatalogo, onAbrirVerbete, erroFonte, onTentarDeNovo,
  carregando,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const red = reduzido();
  const lista = Array.isArray(carteira) ? carteira : [];
  // Onda F (2026-10-08): legenda da régua uma vez no topo da lista; só se ao menos um card desenha régua.
  const algumaRegua = lista.some((p) => { const d = tecnicoPorTicker && tecnicoPorTicker[p.ticker] && tecnicoPorTicker[p.ticker].dados; return !!(d && d.regua && Array.isArray(d.regua.itens) && d.regua.itens.length); });
  const vigias = Array.isArray(vigiasLista) ? vigiasLista : [];
  const armados = vigias.filter((v) => v && v.armed === true);
  const nVigiasDe = (t) => vigias.filter((v) => v && v.ticker === t).length;

  return (
    <section aria-label={cp && cp.tituloOpcoes} style={{ padding: "16px 0", display: "flex", flexDirection: "column", gap: "16px", ...transicaoTela(red) }}>
      <header>
        <h1 tabIndex={-1} style={{ margin: 0, ...TIPO.display, fontFamily: DISPLAY, color: T.textPrimary }}>
          {(cp && cp.tituloOpcoes) || "—"}
        </h1>
        <Frescor mode={mode} frescor={frescor} />
        <div style={{ ...TIPO.corpo, color: T.textSecondary, marginTop: "4px" }}>{tx("aviso_virtual")}</div>
      </header>

      {erroFonte ? (
        <div role="alert" style={{ padding: "12px", borderRadius: "12px", border: `1px solid ${T.warn}`, color: T.textPrimary, ...TIPO.corpo, display: "flex", flexDirection: "column", gap: "8px" }}>
          <span>{tx("erro_fonte")}</span>
          <button type="button" onClick={onTentarDeNovo} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start" }}>
            {tx("tentar_de_novo")}
          </button>
        </div>
      ) : (
        <>
          {vigias.length > 0 && (
            <div>
              <h2 style={{ margin: "0 0 8px", ...TIPO.label, letterSpacing: ".08em", textTransform: "uppercase", color: T.textMuted }}>
                {tx("hub_atencao")}
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {vigiasComEstado && armados.map((v, i) => (
                  <div key={(v.id || v.ticker || "v") + i} style={{ padding: "12px", borderRadius: "12px", background: T.bgPanel, borderLeft: `3px solid ${T.accent}`, ...TIPO.corpo, color: T.textPrimary }}>
                    <span style={{ ...TIPO.titulo, ...MONO }}>{v.ticker || "—"}</span>
                    {" "}
                    <span style={{ color: T.textSecondary }}>{v.nome || v.name || ""}</span>
                  </div>
                ))}
                {vigiasComEstado && armados.length === 0 && (
                  <div style={{ ...TIPO.corpo, color: T.textMuted }}>{tx("hub_nenhum_armado")}</div>
                )}
                <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
                  <button type="button" onClick={onAtualizarVigias} disabled={carregandoVigias === true} {...comFoco}
                    style={{ ...BOTAO, color: T.accent, opacity: carregandoVigias ? 0.55 : 1 }}>
                    <span style={{ display: "block" }}>{carregandoVigias ? tx("consultando") : tx("hub_atualizar")}</span>
                    <span style={{ display: "block", ...TIPO.label, fontWeight: 400, color: T.textMuted }}>
                      {tx("hub_atualizar_custo", { n: vz(custoAtualizar) })}
                    </span>
                  </button>
                  {onVerTodosVigias && (
                    <button type="button" onClick={onVerTodosVigias} {...comFoco} style={{ ...BOTAO, border: "none", color: T.textSecondary }}>
                      {"ver todos ›"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          <div>
            <h2 style={{ margin: "0 0 8px", ...TIPO.label, letterSpacing: ".08em", textTransform: "uppercase", color: T.textMuted }}>
              {tx("hub_carteira")}
            </h2>
            {carregando ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px", position: "relative" }}>
                <Skeleton cp={cp} mode={mode} />
                <Skeleton cp={cp} mode={mode} />
              </div>
            ) : lista.length === 0 ? (
              <div style={{ padding: "16px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ ...TIPO.titulo, color: T.textPrimary }}>{tx("hub_vazio_titulo")}</div>
                <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("hub_vazio_corpo")}</div>
                <button type="button" onClick={onIrCarteira} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start", color: T.accent, borderColor: T.accent }}>
                  {tx("hub_vazio_cta")}
                </button>
              </div>
            ) : (
              <>
              {algumaRegua ? <div style={{ ...TIPO.corpo, color: T.textMuted, marginBottom: "8px" }}>{cp && cp.opcoesReguaAjuda}</div> : null}
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {lista.map((p) => (
                  <CardAtivo key={p.ticker} cp={cp} mode={mode} pos={p}
                    tecnico={tecnicoPorTicker && tecnicoPorTicker[p.ticker]}
                    estrutura={opcoesPorTicker && opcoesPorTicker[p.ticker] && opcoesPorTicker[p.ticker].estrutura}
                    nVigias={nVigiasDe(p.ticker)} onAbrir={onAbrirAtivo}
                    didatica={didatica} A={A} kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
                ))}
              </div>
              </>
            )}
            <div style={{ ...TIPO.corpo, ...NUM, color: T.textMuted, marginTop: "16px" }}>{tx("hub_aviso_custo")}</div>
          </div>
        </>
      )}
    </section>
  );
}
