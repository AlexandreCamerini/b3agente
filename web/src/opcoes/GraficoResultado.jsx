/**
 * GraficoResultado.jsx — Fase 48 (48-09): "Resultado no vencimento" (tela 3).
 *
 * Só LÊ `degrau.grafico` do backend (pontos, marcadores, legenda, tabela, aria).
 * Nenhuma conta financeira aqui: a escala do desenho (min/max dos valores
 * plotados) é geometria, não resultado. Perda e ganho têm o mesmo peso visual
 * (mesma opacidade de preenchimento); cor nunca é a única pista (sinal "−",
 * rótulo "perde", número em R$). O gráfico redesenha sem animação.
 */
import { useEffect, useState } from "react";
import { opcoesEscadaTxt } from "../copy.js";
import TermoOpcoes from "./TermoOpcoes.jsx";
import { T, FOCO, TIPO, MONO, ALVO_MIN } from "./fluxoEstilo.js";

const W = 340;
const H = 214;
const PAD_X = 12;
const PAD_Y = 16;
const OPACIDADE = 0.2; // a MESMA para ganho e perda

const ehNum = (v) => typeof v === "number" && isFinite(v);

const fmt = (v) =>
  ehNum(v)
    ? v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace("-", "−")
    : "—";

const comFoco = {
  onFocus: (e) => Object.assign(e.currentTarget.style, FOCO),
  onBlur: (e) => { e.currentTarget.style.outline = "none"; },
};

// Índice do ponto mais próximo de `hoje` (busca por comparação de preços).
function indiceInicial(pontos, hoje) {
  if (!Array.isArray(pontos) || !pontos.length || !ehNum(hoje)) return 0;
  let i = 0;
  while (i < pontos.length && pontos[i].preco < hoje) i++;
  if (i === 0) return 0;
  if (i >= pontos.length) return pontos.length - 1;
  return (hoje - pontos[i - 1].preco) <= (pontos[i].preco - hoje) ? i - 1 : i;
}

function Botao({ ativo, onClick, children }) {
  return (
    <button type="button" aria-pressed={ativo} onClick={onClick} {...comFoco}
      style={{
        minHeight: ALVO_MIN + "px", padding: "8px 16px", ...TIPO.label, cursor: "pointer",
        borderRadius: "999px", color: ativo ? T.accent : T.textSecondary,
        border: `1px solid ${ativo ? T.accent : T.borderSubtle}`,
        background: ativo ? T.accentTint10 : "transparent",
      }}>
      {children}
    </button>
  );
}

export default function GraficoResultado({
  cp, mode, ticker, degrau, unidade, onTrocarUnidade,
  didatica, A, kbCatalogo, onAbrirVerbete,
}) {
  const tx = (k, v) => opcoesEscadaTxt(mode, k, v);
  const u = unidade === "acao" ? "porAcao" : "total";
  const g = degrau && degrau.grafico ? degrau.grafico : null;
  const pontos = g && Array.isArray(g.pontos) ? g.pontos : [];
  const [idx, setIdx] = useState(() => indiceInicial(pontos, g && g.hoje));
  const chave = degrau ? String(degrau.id) + "|" + String(degrau.nome) + "|" + String(degrau.vencimento) + "|" + pontos.length : "";
  useEffect(() => { setIdx(indiceInicial(pontos, g && g.hoje)); /* eslint-disable-next-line */ }, [chave]);

  const qtd = degrau && ehNum(degrau.qtdAcoes) ? String(degrau.qtdAcoes) : "—";

  const cabecalho = (
    <>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
        <div>
          <h3 style={{ margin: 0, ...TIPO.titulo, color: T.textPrimary }}>{tx("grafico_titulo")}</h3>
          <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{tx("grafico_subtitulo")}</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <Botao ativo={u === "total"} onClick={() => onTrocarUnidade && onTrocarUnidade("total")}>
            {tx("unidade_total", { qtd })}
          </Botao>
          <Botao ativo={u === "porAcao"} onClick={() => onTrocarUnidade && onTrocarUnidade("acao")}>
            {tx("unidade_acao")}
          </Botao>
        </div>
      </div>
    </>
  );

  // Sem gráfico: motivo do backend no lugar do SVG, MESMA altura (sem layout shift).
  if (!g || !pontos.length) {
    const motivo = (degrau && degrau.motivoSemGrafico) || tx("dado_insuficiente");
    return (
      <section style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {cabecalho}
        <div style={{
          width: "100%", aspectRatio: `${W} / ${H}`, display: "flex", alignItems: "center", justifyContent: "center",
          padding: "16px", boxSizing: "border-box", borderRadius: "12px", background: T.bgPanel,
          border: `1px solid ${T.borderSubtle}`, color: T.textSecondary, ...TIPO.corpo, textAlign: "center",
        }}>
          {tx("sem_grafico", { motivo })}
        </div>
      </section>
    );
  }

  // Escala do DESENHO (não é conta financeira).
  const valores = [];
  for (const p of pontos) {
    if (p.soAcoes && ehNum(p.soAcoes[u])) valores.push(p.soAcoes[u]);
    if (p.comEstrutura && ehNum(p.comEstrutura[u])) valores.push(p.comEstrutura[u]);
  }
  valores.push(0);
  const yMin = Math.min(...valores);
  const yMax = Math.max(...valores);
  const dx = g.xMax - g.xMin;
  const dy = yMax - yMin;
  const X = (preco) => PAD_X + ((preco - g.xMin) / (dx || 1)) * (W - 2 * PAD_X);
  const Y = (val) => PAD_Y + ((yMax - val) / (dy || 1)) * (H - 2 * PAD_Y);
  const y0 = Y(0);

  const linha = (serie) => {
    let d = "";
    let aberto = false;
    for (const p of pontos) {
      const v = p[serie] ? p[serie][u] : null;
      if (!ehNum(v) || !ehNum(p.preco)) { aberto = false; continue; }
      d += (aberto ? "L" : "M") + X(p.preco).toFixed(1) + " " + Y(v).toFixed(1) + " ";
      aberto = true;
    }
    return d.trim();
  };
  const dEstrutura = linha("comEstrutura");
  const dAcoes = linha("soAcoes");
  const validos = pontos.filter((p) => p.comEstrutura && ehNum(p.comEstrutura[u]) && ehNum(p.preco));
  const dArea = validos.length > 1
    ? "M" + X(validos[0].preco).toFixed(1) + " " + y0.toFixed(1) + " "
      + validos.map((p) => "L" + X(p.preco).toFixed(1) + " " + Y(p.comEstrutura[u]).toFixed(1)).join(" ")
      + " L" + X(validos[validos.length - 1].preco).toFixed(1) + " " + y0.toFixed(1) + " Z"
    : "";

  const ptsOk = idx >= 0 && idx < pontos.length ? pontos[idx] : pontos[0];
  const marcadores = Array.isArray(g.marcadores) ? g.marcadores : [];
  const legenda = Array.isArray(g.legenda) ? g.legenda : [];
  const ausentes = Array.isArray(g.ausentes) ? g.ausentes : [];
  const tabela = Array.isArray(g.tabela) ? g.tabela : [];
  const ariaTxt = g.aria && g.aria[u] ? g.aria[u] : tx("dado_insuficiente");
  const dados = degrau.termos || null;

  const efeito = ptsOk.efeito;
  const dif = ptsOk.diferenca ? ptsOk.diferenca[u] : null;
  let fraseEse;
  if (efeito === "melhora" && ehNum(dif)) fraseEse = tx("ese_melhora", { d: fmt(dif) });
  else if (efeito === "reduz" && ehNum(dif)) fraseEse = tx("ese_reduz", { d: fmt(dif) });
  else if (efeito === "igual") fraseEse = tx("ese_igual");
  else fraseEse = tx("dado_insuficiente");

  const eixo = { fontSize: "12px", fontFamily: MONO.fontFamily, fill: T.textMuted };

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {cabecalho}

      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="auto" role="img" aria-label={ariaTxt}
        style={{ display: "block", width: "100%", height: "auto", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }}>
        <defs>
          <clipPath id="opc-clip-pos"><rect x="0" y="0" width={W} height={Math.max(0, y0)} /></clipPath>
          <clipPath id="opc-clip-neg"><rect x="0" y={y0} width={W} height={Math.max(0, H - y0)} /></clipPath>
        </defs>
        {dArea ? (
          <>
            <path d={dArea} clipPath="url(#opc-clip-pos)" style={{ fill: T.positive }} fillOpacity={OPACIDADE} />
            <path d={dArea} clipPath="url(#opc-clip-neg)" style={{ fill: T.negative }} fillOpacity={OPACIDADE} />
          </>
        ) : null}
        <line x1={PAD_X} x2={W - PAD_X} y1={y0} y2={y0} style={{ stroke: T.textMuted }} strokeWidth="1" />
        <text x={PAD_X} y={y0 - 4} style={eixo}>R$ 0</text>
        {ehNum(g.precoMedio) ? (
          <g>
            <line x1={X(g.precoMedio)} x2={X(g.precoMedio)} y1={PAD_Y} y2={H - PAD_Y}
              style={{ stroke: T.textFaint }} strokeWidth="1" strokeDasharray="1 3" />
            <text x={X(g.precoMedio) + 4} y={H - 4} style={eixo}>{tx("linha_preco_medio")} {fmt(g.precoMedio)}</text>
          </g>
        ) : null}
        {dAcoes ? <path d={dAcoes} fill="none" style={{ stroke: T.textFaint }} strokeWidth="2" strokeDasharray="6 4" /> : null}
        {dEstrutura ? <path d={dEstrutura} fill="none" style={{ stroke: T.accent }} strokeWidth="2" /> : null}
        <text x={PAD_X} y={H - 4} style={eixo}>{fmt(g.xMin)}</text>
        <text x={W - PAD_X} y={H - 4} textAnchor="end" style={eixo}>{fmt(g.xMax)}</text>
        {marcadores.map((m) => {
          const v = m.valor ? m.valor[u] : null;
          if (!ehNum(m.preco) || !ehNum(v)) return null;
          return (
            <g key={m.n} aria-hidden="true">
              <circle cx={X(m.preco)} cy={Y(v)} r="9" style={{ fill: T.accent }} />
              <text x={X(m.preco)} y={Y(v) + 4} textAnchor="middle" style={{ fontSize: "12px", fontWeight: 700, fill: T.onAccent }}>{m.n}</text>
            </g>
          );
        })}
      </svg>

      <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
        {legenda.map((it) => {
          const v = it.valor ? it.valor[u] : null;
          const perde = ehNum(v) && v < 0;
          return (
            <li key={it.n} style={{ display: "flex", gap: "8px", alignItems: "flex-start", ...TIPO.corpo, color: T.textSecondary }}>
              <span aria-hidden="true" style={{ minWidth: "24px", height: "24px", borderRadius: "999px", background: T.accent, color: T.onAccent, ...TIPO.label, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{it.n}</span>
              <span>
                <span style={{ color: T.textPrimary }}>
                  <TermoOpcoes texto={it.rotulo} termos={[{ rotulo: it.rotulo, setor: it.setor, kb: it.kb }]}
                    A={A} didatica={didatica} kbCatalogo={kbCatalogo} dados={dados} onAbrirVerbete={onAbrirVerbete} />
                </span>
                {" "}
                <span style={{ ...MONO, color: T.textPrimary }}>R$ {fmt(v)}</span>
                {perde ? <span style={{ color: T.textPrimary, fontWeight: 700 }}> {"(perde)"}</span> : null}
                {it.frase ? <span> {it.frase}</span> : null}
              </span>
            </li>
          );
        })}
        {ausentes.map((a) => (
          <li key={a.chave} style={{ ...TIPO.corpo, color: T.textMuted }}>{a.texto}</li>
        ))}
      </ol>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "16px", borderRadius: "12px", background: T.bgPanel, border: `1px solid ${T.borderSubtle}` }}>
        <label htmlFor="opc-ese-range" style={{ ...TIPO.titulo, color: T.textPrimary }}>
          {tx("ese_pergunta", { ticker: ticker || "", preco: fmt(ptsOk.preco) })}
        </label>
        <input id="opc-ese-range" type="range" min={0} max={pontos.length - 1} step={1} value={idx}
          onChange={(e) => setIdx(Number(e.target.value))} {...comFoco}
          style={{ width: "100%", minHeight: ALVO_MIN + "px", accentColor: "var(--accent)" }} />
        <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", ...TIPO.corpo, color: T.textSecondary }}>
          <div>{tx("linha_so_acoes")}<br /><span style={{ ...MONO, color: T.textPrimary }}>R$ {fmt(ptsOk.soAcoes ? ptsOk.soAcoes[u] : null)}</span></div>
          <div style={{ textAlign: "right" }}>{tx("linha_com_estrutura")}<br /><span style={{ ...MONO, color: T.textPrimary }}>R$ {fmt(ptsOk.comEstrutura ? ptsOk.comEstrutura[u] : null)}</span></div>
        </div>
        <div style={{ ...TIPO.corpo, color: T.textSecondary }}>{fraseEse}</div>
      </div>

      <details>
        <summary {...comFoco} style={{ minHeight: ALVO_MIN + "px", display: "flex", alignItems: "center", cursor: "pointer", ...TIPO.label, color: T.textSecondary }}>
          {tx("tabela_ver")}
        </summary>
        <div data-sem-gesto-voltar style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", ...TIPO.corpo, color: T.textSecondary }}>
            <thead>
              <tr>
                <th scope="col" style={{ textAlign: "left", ...TIPO.label }}>{tx("tabela_preco")}</th>
                <th scope="col" style={{ textAlign: "right", ...TIPO.label }}>{tx("tabela_so_acoes")}</th>
                <th scope="col" style={{ textAlign: "right", ...TIPO.label }}>{tx("tabela_com_estrutura")}</th>
              </tr>
            </thead>
            <tbody>
              {tabela.map((l, i) => (
                <tr key={i}>
                  <td style={{ ...MONO }}>{fmt(l.preco)}</td>
                  <td style={{ ...MONO, textAlign: "right" }}>{fmt(l.soAcoes ? l.soAcoes[u] : null)}</td>
                  <td style={{ ...MONO, textAlign: "right" }}>{fmt(l.comEstrutura ? l.comEstrutura[u] : null)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
