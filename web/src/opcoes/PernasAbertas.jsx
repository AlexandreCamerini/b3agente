/**
 * PernasAbertas.jsx — Fase 48 gap G-02 (2026-10-05).
 * Zero cálculo; resultado só do motor (estrutura.pernas[].resultado); a saída
 * só é vetada pelo motor (encerrar.permitido). Lista toda perna aberta do ativo
 * e encerra a comprada sem lastro por A.sellOption, com confirmação em 2 passos.
 * Ausência de número vira travessão, nunca zero. Zero import de App.jsx.
 *
 * Fase 49 (2026-10-06): contêiner da anatomia (posição → pernas); a lista do
 * 48-16 é o fallback e a saída nunca depende do cálculo.
 * O store chega por prop (leitura grátis); nada é somado nem estimado aqui.
 */
import { useEffect, useState } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import { T, FOCO, TIPO, ALVO_MIN, NUM } from "./fluxoEstilo.js";
import { useAnatomia } from "./useAnatomia.js";
import PosicaoTotal from "./PosicaoTotal.jsx";
import AnatomiaPerna, { encerrarVetado, encerrarAviso } from "./AnatomiaPerna.jsx";

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

const MOTIVOS_SEM_COTACAO = ["fonte_indisponivel", "fora_da_cadeia", "sem_negocio", "sem_cotacao"];

// Id que já não é perna aberta nunca vai à rota (ela devolve 400 para id fora
// das pernas abertas); "ACOES" é o único id fixo aceito.
export function excluirParaRota(excluidas, ids) {
  const lista = Array.isArray(excluidas) ? excluidas : [];
  const abertas = Array.isArray(ids) ? ids : [];
  return lista.filter((x) => x === "ACOES" || abertas.includes(x));
}

// Linha do 48-16, intacta: usada como fallback e para posição sem item na anatomia.
function LinhaPerna48({ pos, motor, tx, carregandoEstrutura, confirmando, setConfirmando, ocupado, encerrar }) {
  const m = motor.find((p) => p && p.id === pos.id) || null;
  const tipo = String((m && m.tipo) || pos.optionType || "").toUpperCase() || "—";
  const lado = (m && m.lado) || (pos.side === "vendida" ? "venda" : "compra");
  const strike = m && ehNum(m.strike) ? m.strike : pos.strike;
  const venc = (m && m.vencimento) || pos.expiration;
  const qtd = m && ehNum(m.quantidade) ? m.quantidade : pos.qty;
  const entrada = m && ehNum(m.premioEntrada) ? m.premioEntrada : pos.avg;
  const atual = m && ehNum(m.premioAtual) ? m.premioAtual : null;
  const resultado = m && ehNum(m.resultado) ? m.resultado : null;
  // motivoSemCotacao é enum fechado do motor: vira frase, nunca o enum cru.
  const frasePorMotivo = m && m.motivoSemCotacao
    ? tx(MOTIVOS_SEM_COTACAO.includes(m.motivoSemCotacao) ? "anat_hoje_" + m.motivoSemCotacao : "anat_hoje_sem_cotacao")
    : null;
  const semNumero = resultado === null
    ? (frasePorMotivo || (carregandoEstrutura ? tx("pernas_carregando") : null))
    : null;
  // WR-02 (49-REVIEW): mesma regra do card da anatomia — premio_indisponivel é aviso, não veto.
  const vetado = encerrarVetado(m && m.encerrar);
  const avisoEnc = encerrarAviso(m && m.encerrar);
  const encerravel = !pos.lastro && pos.side !== "vendida";
  const idVeto = "perna-veto-" + pos.id;
  const emConfirmacao = confirmando === pos.id;
  const emCurso = ocupado === pos.id;
  return (
    <li style={{ padding: "12px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}`, display: "flex", flexDirection: "column", gap: "4px" }}>
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
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <button type="button" aria-label={tx("pernas_encerrar_aria", { id: pos.id })}
            aria-describedby={avisoEnc ? idVeto : undefined}
            onClick={() => setConfirmando(pos.id)} {...comFoco} style={{ ...BOTAO, alignSelf: "flex-start" }}>
            {tx("pernas_encerrar")}
          </button>
          {avisoEnc ? <div id={idVeto} style={{ ...TIPO.corpo, color: T.textPrimary }}>{avisoEnc}</div> : null}
        </div>
      )}
    </li>
  );
}

const LISTA = { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "8px" };

export default function PernasAbertas({
  mode, ticker, optionPositions, estrutura, carregandoEstrutura, A, store,
  anatomia: anatomiaInjetada, didatica, kbCatalogo, onAbrirVerbete,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const [confirmando, setConfirmando] = useState(null);
  const [ocupado, setOcupado] = useState(null);
  const [excluidas, setExcluidas] = useState([]);
  const [idxEscolhido, setIdxEscolhido] = useState(null);
  const [selecionada, setSelecionada] = useState(null);

  const abertas = (Array.isArray(optionPositions) ? optionPositions : [])
    .filter((o) => o && o.underlying === ticker && ehNum(o.qty) && o.qty > 0);
  const ids = abertas.map((o) => o.id);
  const excluirValido = excluirParaRota(excluidas, ids);
  const lido = useAnatomia(anatomiaInjetada ? null : store, ticker, excluirValido, ids, mode);
  const dados = anatomiaInjetada || lido.dados;

  // Outro ativo, outra leitura: escolhas locais não atravessam o ticker.
  useEffect(() => {
    setExcluidas([]); setIdxEscolhido(null); setSelecionada(null);
  }, [ticker]);

  if (abertas.length === 0) return null;

  const motor = (estrutura && Array.isArray(estrutura.pernas) ? estrutura.pernas
    : (dados && dados.estrutura && Array.isArray(dados.estrutura.pernas) ? dados.estrutura.pernas : []));
  const idTitulo = "pernas-titulo-" + ticker;

  const encerrar = async (id) => {
    setOcupado(id);
    try {
      if (A && typeof A.sellOption === "function") await A.sellOption(id);
    } finally {
      setOcupado(null);
      setConfirmando(null);
      setExcluidas((xs) => xs.filter((x) => x !== id));
      setSelecionada((s) => (s === id ? null : s));
      if (lido.recarregar) lido.recarregar();
    }
  };

  const comAnatomia = !!(dados && dados.estado === "ok" && dados.anatomia);
  const anat = comAnatomia ? dados.anatomia : null;
  const grade = anat && anat.grade ? anat.grade : {};
  const idx = Number.isInteger(idxEscolhido) ? idxEscolhido : (Number.isInteger(grade.indiceInicial) ? grade.indiceInicial : 0);
  const totalOk = !!(anat && anat.total && Array.isArray(anat.total.pontos));

  const alternar = (id) => {
    setExcluidas((xs) => (xs.includes(id) ? xs.filter((x) => x !== id) : [...xs, id]));
    setSelecionada((s) => (s === id ? null : s));
  };
  const verSemEsta = (id) => {
    setSelecionada((s) => (s === id ? null : id));
    setExcluidas((xs) => xs.filter((x) => x !== id));
    // Sem rolagem programática: o guardião de consolidação proíbe esse padrão em
    // web/src/opcoes/ (Pitfall 4); o painel total já fica logo acima das pernas.
  };

  const linha = (pos) => (
    <LinhaPerna48 key={pos.id} pos={pos} motor={motor} tx={tx} carregandoEstrutura={carregandoEstrutura}
      confirmando={confirmando} setConfirmando={setConfirmando} ocupado={ocupado} encerrar={encerrar} />
  );

  if (comAnatomia) {
    const pernasMotor = Array.isArray(anat.pernas) ? anat.pernas : [];
    return (
      <section aria-labelledby={idTitulo} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div>
          <PosicaoTotal mode={mode} ticker={ticker} anatomia={anat} excluidas={excluidas} onAlternar={alternar}
            idx={idx} onIdx={setIdxEscolhido} selecionada={selecionada}
            recalculando={!!lido.carregando && !anatomiaInjetada} />
        </div>
        <h3 id={idTitulo} style={{ margin: 0, ...TIPO.titulo, color: T.textPrimary }}>{tx("anat_pernas_titulo")}</h3>
        <ul style={LISTA}>
          {abertas.map((pos) => {
            const perna = pernasMotor.find((p) => p && p.id === pos.id) || null;
            if (!perna) return linha(pos);
            return (
              <li key={pos.id}>
                <AnatomiaPerna mode={mode} ticker={ticker} perna={perna} pos={pos} grade={grade} cursorIdx={idx}
                  selecionada={selecionada === pos.id} onVerSemEsta={totalOk ? verSemEsta : null}
                  onEncerrar={encerrar} ocupado={ocupado} A={A} didatica={didatica}
                  kbCatalogo={kbCatalogo} onAbrirVerbete={onAbrirVerbete} />
              </li>
            );
          })}
        </ul>
      </section>
    );
  }

  const falhou = !!lido.erro || !!(dados && dados.estado === "erro");
  return (
    <section aria-labelledby={idTitulo} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <h3 id={idTitulo} style={{ margin: 0, ...TIPO.titulo, color: T.textPrimary }}>{tx("pernas_titulo")}</h3>
      {lido.carregando && !falhou ? (
        <div role="status" style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("anat_carregando")}</div>
      ) : null}
      {falhou ? (
        <div role="status" style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-start" }}>
          <div style={{ ...TIPO.corpo, color: T.textPrimary }}>{(dados && dados.motivoTexto) || tx("anat_erro")}</div>
          <button type="button" onClick={() => lido.recarregar && lido.recarregar()} {...comFoco} style={BOTAO}>
            {tx("tentar_de_novo")}
          </button>
        </div>
      ) : null}
      <ul style={LISTA}>{abertas.map(linha)}</ul>
    </section>
  );
}
