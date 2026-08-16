import { useState, useEffect, useCallback } from "react";
import { api, getToken, setToken } from "./api.js";

// ADR-012 (Fase 5): tokens do Brand Book v2, tema escuro, acento do modo
// Operador (dourado) — SUPERSEDE a Decisão 6 do ADR-011 ("paleta mínima,
// própria desta app"), decisão explícita do Alex (2026-08-14). Valores
// copiados literal de web/src/App.jsx (PALETTE.dark + MODE_OPERADOR.dark +
// BRAND) — portal dark-only, não precisa do proxy CSS-var/tema-claro de lá.
const T = {
  bg: "#10121a", card: "#1b1f2e", border: "#2c3245", borderFaint: "#20242f",
  text: "#eef1f8", muted: "#9aa3bd", faint: "#6f7797",
  accent: "#d4af37", onAccent: "#241b06", positive: "#34d399", negative: "#f26d6d", warn: "#fbbf24",
};
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
const SANS = "'Nunito', -apple-system, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif";
const DISPLAY = "'Fredoka', " + SANS;

function Kv({ label, value, tone }) {
  const col = tone === "positive" ? T.positive : tone === "negative" ? T.negative : tone === "warn" ? T.warn : T.text;
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.border}`, fontSize: "13px" }}>
      <span style={{ color: T.muted }}>{label}</span>
      <span style={{ fontFamily: MONO, fontWeight: 700, color: col, textAlign: "right" }}>{value}</span>
    </div>
  );
}

function Card({ title, children, right }) {
  return (
    <div style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: "10px", padding: "16px", marginBottom: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
        <div style={{ fontSize: "11px", fontWeight: 800, color: T.faint, letterSpacing: "0.06em", textTransform: "uppercase" }}>{title}</div>
        {right}
      </div>
      {children}
    </div>
  );
}

function Estado({ loading, error, empty, children }) {
  if (loading) return <div style={{ color: T.muted, fontSize: "13px", padding: "8px 0" }}>Carregando…</div>;
  if (error) return <div style={{ color: T.negative, fontSize: "13px", padding: "8px 0" }}>Erro: {error}</div>;
  if (empty) return <div style={{ color: T.faint, fontSize: "13px", padding: "8px 0" }}>Nenhum dado neste filtro.</div>;
  return children;
}

// Fetch genérico por view: cada tela chama `fetcher` no mount/troca de aba;
// nunca faz polling (ADR-011 Decisão 3 — drill-down, não tempo real).
function useFetch(fetcher, deps) {
  const [state, setState] = useState({ loading: true, error: null, data: null });
  const reload = useCallback(() => {
    setState({ loading: true, error: null, data: null });
    fetcher().then((data) => setState({ loading: false, error: null, data }))
      .catch((e) => setState({ loading: false, error: (e && e.message) || String(e), data: null }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { reload(); }, [reload]);
  return { ...state, reload };
}

// ADR-012 (Fase 4): converte a série {day,value} de /api/analytics/tendencias
// pro formato {count} que Sparkline já espera (mesmo componente da Fase 2,
// sem duplicar lógica de desenho).
const paraSparkline = (serie) => (serie || []).map((p) => ({ count: p.value }));

// ADR-012 (Fase 5): resumo executivo — KPIs de maior nível no topo de cada
// tela, drill-down em cards abaixo. Mesmo componente Kpi já usado em
// Eficiência da IA/Automação (Fases 1/3), só reaproveitado aqui.
const card = { background: T.card, border: `1px solid ${T.border}`, borderRadius: "12px" };
function ResumoExecutivo({ children }) {
  return (
    <div style={{ ...card, padding: "16px 18px", marginBottom: "16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
      {children}
    </div>
  );
}

function VisaoGeral() {
  const { loading, error, data, reload } = useFetch(() => api.agentStatus(), []);
  const { data: tend } = useFetch(() => api.tendencias(30), []);
  return (
    <>
      {data && (
        <ResumoExecutivo>
          <Kpi label="KILL-SWITCH" value={data.killSwitch ? "LIGADO" : "desligado"} tone={data.killSwitch ? "negative" : "positive"} />
          <Kpi label="PREGÃO" value={data.pregaoAberto ? "aberto" : "fechado"} />
          <Kpi label="LAÇO VIVO" value={data.heartbeat?.lacoVivo ? "sim" : "NÃO"} tone={data.heartbeat?.lacoVivo ? "positive" : "negative"} />
          <Kpi label="USUÁRIOS C/ OPERADOR" value={data.usuariosHabilitados} />
          <Kpi label="PROTEÇÃO SEM OPERADOR" value={data.protecaoSemOperador} tone={data.protecaoSemOperador > 0 ? "negative" : "positive"} />
        </ResumoExecutivo>
      )}
      <Card title="Ciclo do agente" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error}>
          {data && (
            <>
              <Kv label="Heartbeat — última batida" value={data.heartbeat?.atBRT || "—"} />
              <Kv label="Próxima passada" value={data.proximaPassadaEmS != null ? data.proximaPassadaEmS + "s" : "—"} />
              <Kv label="Último ciclo — executadas" value={data.ultimoCiclo?.executadas ?? "—"} />
              <Kv label="Último ciclo — erro" value={data.ultimoCiclo?.erro || "nenhum"} tone={data.ultimoCiclo?.erro ? "negative" : undefined} />
            </>
          )}
        </Estado>
      </Card>
      <Card title="Radar, aquecimento & push">
        <Estado loading={loading} error={error}>
          {data && (
            <>
              <Kv label="Radar diário — última varredura" value={data.radarDiario?.date || "nunca rodou"} />
              <Kv label="Radar diário — erro" value={data.radarDiario?.erro || "nenhum"} tone={data.radarDiario?.erro ? "negative" : undefined} />
              <EventoComSerie label="Radar diário — duração" value={data.radarDiario?.duracaoS != null ? data.radarDiario.duracaoS + "s" : "—"} serie={paraSparkline(tend?.radar_diario_duracao_s)} />
              <Kv label="Avaliação de análises — última" value={data.avaliacaoAnalises?.date || "nunca rodou"} />
              <Kv label="Aquecimento de fundamentos — última" value={data.aquecimentoFundamentos?.date || "nunca rodou"} />
              <Kv label="Aquecimento de fundamentos — aquecidos" value={data.aquecimentoFundamentos?.aquecidos ?? "—"} />
              <Kv label="Intraday — última passada" value={data.intraday?.atLabel || "nunca rodou"} />
              <Kv label="Intraday — ativos com lacuna" value={data.intraday?.comLacuna ?? "—"} />
              <EventoComSerie label="Push automático — falhas hoje" value={data.pushAutomaticoFalhasHoje?.falhas ?? 0} serie={paraSparkline(tend?.push_automatico_falhas_dia)} />
            </>
          )}
        </Estado>
      </Card>
    </>
  );
}

function Custos() {
  const { loading, error, data, reload } = useFetch(() => api.obsUsage(), []);
  const { data: tend } = useFetch(() => api.tendencias(30), []);
  const tokensDia = Object.values(data?.tokens?.porModelo || {}).reduce((s, v) => s + (v.inputTokens || 0) + (v.outputTokens || 0), 0);
  return (
    <>
      {data && (
        <ResumoExecutivo>
          <Kpi label="IA GERENCIADA" value={data.iaGerenciadaAtiva ? "ativa" : "desligada"} />
          <Kpi label="ANÁLISES HOJE" value={(data.analisesGerenciadas?.used ?? "—") + "/" + (data.tetoGlobalDia ?? "∞")} />
          <Kpi label="TOKENS/DIA" value={tokensDia} />
          {data.candles?.orcamentoBrapi && <Kpi label="GASTO BRAPI HOJE" value={data.candles.orcamentoBrapi.total} tone={data.candles.orcamentoBrapi.total > data.candles.orcamentoBrapi.cotaMes ? "negative" : undefined} />}
          <Kpi label="SÉRIES EM CACHE" value={Object.keys(data.cacheCandles || {}).length} />
        </ResumoExecutivo>
      )}
      <Card title="Uso de IA" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error}>
          {data && (
            <>
              <Kv label="Cota por usuário/dia" value={data.cotaPorUsuarioDia ?? "ilimitada"} />
              <Kv label="Teto global/dia" value={data.tetoGlobalDia ?? "ilimitado"} />
              <EventoComSerie label="Análises gerenciadas — usado hoje" value={(data.analisesGerenciadas?.used ?? "—") + " · restante " + (data.analisesGerenciadas?.remaining ?? "—")} serie={paraSparkline(tend?.ia_analises_gerenciadas_dia)} />
              <EventoComSerie label="Tokens/dia (todos os modelos)" value={tokensDia + " tokens"} serie={paraSparkline(tend?.custo_ia_tokens_dia)} />
              {Object.entries(data.tokens?.porModelo || {}).map(([modelo, v]) => (
                <Kv key={modelo} label={"Tokens hoje — " + modelo} value={(v.total ?? v.tokens ?? JSON.stringify(v))} />
              ))}
            </>
          )}
        </Estado>
      </Card>
      <Card title="Orçamento brapi (ADR-008)">
        <Estado loading={loading} error={error}>
          {data && !data.candles?.orcamentoBrapi && (
            <div style={{ color: T.faint, fontSize: "13px" }}>Provedor de candles vigente não é brapi (é {data.candles?.provedor || "—"}) — orçamento não se aplica.</div>
          )}
          {data && data.candles?.orcamentoBrapi && (
            <>
              <Kv label="Cota do mês" value={data.candles.orcamentoBrapi.cotaMes} />
              <Kv label="Gasto no dia" value={data.candles.orcamentoBrapi.total} />
              <Kv label="Intervalo do spot vigente" value={data.candles.orcamentoBrapi.spotIntervaloS + "s"} />
              {Object.entries(data.candles.orcamentoBrapi.fatias || {}).map(([fatia, f]) => (
                <Kv key={fatia} label={"Fatia " + fatia} value={f.gasto + " / " + f.limite + (f.degradado ? " (degradado)" : "")} tone={f.degradado ? "warn" : undefined} />
              ))}
              <EventoComSerie label="Requisições (janela 3 dias)" value={data.candles.requisicoes ?? "—"} serie={paraSparkline(tend?.brapi_requisicoes_janela3d)} />
              <EventoComSerie label="Erros (janela 3 dias)" value={data.candles.erros ?? "—"} serie={paraSparkline(tend?.brapi_erros_janela3d)} />
            </>
          )}
        </Estado>
      </Card>
      <Card title="Cache de candles (L2)">
        <Estado loading={loading} error={error}>
          {data && (
            <>
              <EventoComSerie label="Séries em cache" value={Object.keys(data.cacheCandles || {}).length} serie={paraSparkline(tend?.cache_candles_series)} />
              <div style={{ fontSize: "12.5px", color: T.muted, marginTop: "6px" }}>
                {Object.keys(data.cacheCandles || {}).length === 0
                  ? "Nenhuma série em cache agora."
                  : Object.entries(data.cacheCandles || {}).slice(0, 20).map(([k, v]) => `${k} (${v.n})`).join(" · ")}
              </div>
            </>
          )}
        </Estado>
      </Card>
      <div style={{ fontSize: "11.5px", color: T.faint, lineHeight: 1.5 }}>
        Mensalidade do Railway não é medida no código — ver qa/42-finops.md (custo externo, atualizado manualmente).
        Gráficos de tendência são snapshot do momento em que o job diário rodou (ADR-012) — podem divergir do valor "ao vivo" acima se o dia já avançou desde a última passada.
      </div>
    </>
  );
}

// ADR-012 (Fase 2): tendência no tempo de um evento — pontos diários de
// analytics_daily (persistido, sobrevive além de RETENCAO_DIAS) + hoje ao
// vivo. Sem cor por sinal (é contagem, nunca negativa) — mais simples que RCurve.
function Sparkline({ pts, width = 110, height = 26 }) {
  const vals = (pts || []).map((p) => p.count).filter((v) => typeof v === "number" && isFinite(v));
  if (vals.length < 2) return <span style={{ fontSize: "10px", color: T.faint }}>sem série</span>;
  const mn = Math.min(...vals), mx = Math.max(...vals), sp = (mx - mn) || 1;
  const x = (i) => (i / (vals.length - 1)) * (width - 2) + 1;
  const y = (v) => (height - 2) - ((v - mn) / sp) * (height - 4);
  const d = vals.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ display: "block", flexShrink: 0 }} aria-hidden>
      <path d={d} fill="none" stroke={T.accent} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function EventoComSerie({ label, value, serie }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.border}` }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: "13px", color: T.muted }}>{label}</div>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: "12.5px", color: T.text }}>{value}</div>
      </div>
      <Sparkline pts={serie} />
    </div>
  );
}

function Comportamento() {
  const [dias, setDias] = useState(30);
  const { loading, error, data, reload } = useFetch(() => api.analyticsSummary(dias), [dias]);
  const serieMap = {};
  (data?.serieDiariaPorEvento || []).forEach((s) => { serieMap[s.event] = s.serie; });
  const passos = data?.funil?.passos || [];
  const conversao = passos.length >= 2 && passos[0].usuarios > 0 ? Math.round(100 * passos[passos.length - 1].usuarios / passos[0].usuarios) : null;
  return (
    <>
      {data && (
        <ResumoExecutivo>
          <Kpi label="EVENTOS NO PERÍODO" value={(data.adocaoPorFeature || []).reduce((s, r) => s + r.count, 0)} />
          <Kpi label="USUÁRIOS ATIVOS (TOPO)" value={passos[0]?.usuarios ?? "—"} />
          <Kpi label="CONVERSÃO DO FUNIL" value={conversao == null ? "—" : conversao + "%"} tone={conversao == null ? undefined : (conversao >= 20 ? "positive" : undefined)} />
        </ResumoExecutivo>
      )}
      <Card title="Adoção por feature" right={
        <select value={dias} onChange={(e) => setDias(Number(e.target.value))} style={selectStyle}>
          <option value={7}>7 dias</option>
          <option value={30}>30 dias</option>
          <option value={90}>90 dias</option>
        </select>
      }>
        <Estado loading={loading} error={error} empty={data && (data.adocaoPorFeature || []).length === 0}>
          {data && (data.adocaoPorFeature || []).map((r) => (
            <EventoComSerie key={r.event} label={r.event} value={r.count + " eventos · " + r.usuariosDistintos + " usuário(s)"} serie={serieMap[r.event]} />
          ))}
        </Estado>
      </Card>
      <Card title="Funil onboarding → trade_simulated">
        <Estado loading={loading} error={error} empty={data && (data.funil?.passos || []).length === 0}>
          {data && (data.funil?.passos || []).map((p) => (
            <Kv key={p.passo} label={p.passo} value={p.usuarios + " usuário(s)"} />
          ))}
        </Estado>
        <div style={{ marginTop: "8px", fontSize: "10.5px", color: T.faint, lineHeight: 1.5 }}>
          Sem gráfico de tendência aqui: o funil depende da ORDEM de eventos por usuário, que só existe no dado bruto (90 dias de retenção) — o rollup diário não guarda isso.
        </div>
      </Card>
      <Card title="Shown vs. dismissed" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error} empty={data && (data.shownVsDismissed || []).length === 0}>
          {data && (data.shownVsDismissed || []).map((r) => (
            <div key={r.feature} style={{ padding: "7px 0", borderBottom: `1px solid ${T.border}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", fontSize: "13px" }}>
                <span style={{ color: T.muted }}>{r.feature}</span>
                <span style={{ fontFamily: MONO, fontWeight: 700, color: T.text }}>{r.shown} mostrado(s) · {r.dismissed} fechado(s)</span>
              </div>
              <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <span style={{ fontSize: "9.5px", color: T.faint }}>mostrado</span>
                  <Sparkline pts={serieMap[r.feature + "_shown"]} width={70} height={20} />
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <span style={{ fontSize: "9.5px", color: T.faint }}>fechado</span>
                  <Sparkline pts={serieMap[r.feature + "_dismissed"]} width={70} height={20} />
                </div>
              </div>
            </div>
          ))}
        </Estado>
      </Card>
    </>
  );
}

// ADR-012 (Fase 1): agregado cross-usuário de "Eficiência da IA" — mesmo
// motor de analysis_outcomes.compute_stats que já roda por-usuário no app
// consumidor (EficienciaIAScreen, web/src/App.jsx). Componente de gráfico e
// leitura de célula portados de lá (mesmo padrão visual, sem lib nova).
function RCurve({ pts, width = 300, height = 64 }) {
  const vals = (pts || []).filter((v) => typeof v === "number" && isFinite(v));
  if (!vals.length) return null;
  const serie = vals.length === 1 ? [0, vals[0]] : [0, ...vals]; // ancora em 0
  const mn = Math.min(0, ...serie), mx = Math.max(0, ...serie), sp = (mx - mn) || 1;
  const x = (i) => (i / (serie.length - 1)) * (width - 2) + 1;
  const y = (v) => (height - 3) - ((v - mn) / sp) * (height - 6);
  const d = serie.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
  const up = vals[vals.length - 1] >= 0;
  const y0 = y(0);
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ display: "block", height }} aria-hidden>
      <line x1="1" y1={y0.toFixed(1)} x2={width - 1} y2={y0.toFixed(1)} stroke={T.faint} strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
      <path d={d} fill="none" stroke={up ? T.positive : T.negative} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Celula({ rotulo, c, minN }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "12px", padding: "5px 0", color: T.muted, borderBottom: `1px solid ${T.border}` }}>
      <span>{rotulo} <span style={{ color: T.faint, fontFamily: MONO }}>n={c.n}</span></span>
      {c.insuficiente
        ? <span style={{ color: T.faint }}>n insuficiente (mín. {minN || 10})</span>
        : <b style={{ fontFamily: MONO, color: c.taxaAcerto >= 50 ? T.positive : T.negative }}>{c.taxaAcerto}%{c.rMedio != null ? ` · ${c.rMedio >= 0 ? "+" : ""}${c.rMedio}R` : ""}</b>}
    </div>
  );
}

function Kpi({ label, value, tone }) {
  const col = tone === "positive" ? T.positive : tone === "negative" ? T.negative : T.text;
  return (
    <div style={{ flex: "1 1 100px", minWidth: "90px" }}>
      <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 800, color: value == null ? T.faint : col }}>{value == null ? "—" : value}</div>
      <div style={{ fontSize: "10px", color: T.faint, fontWeight: 700, letterSpacing: "0.04em" }}>{label}</div>
    </div>
  );
}

function EficienciaIA() {
  const { loading, error, data, reload } = useFetch(() => api.iaEficiencia(), []);
  const minN = data?.minN || 10;
  return (
    <>
      <Card title="Eficiência da IA — agregado de todos os usuários" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error} empty={data && data.totalAnalises === 0}>
          {data && data.totalAnalises > 0 && (
            <>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <Kpi label="TAXA DE ACERTO" value={data.taxaAcerto == null ? null : data.taxaAcerto + "%"} tone={data.taxaAcerto == null ? undefined : (data.taxaAcerto >= 50 ? "positive" : "negative")} />
                <Kpi label="R MÉDIO / ANÁLISE" value={data.rMedio == null ? null : (data.rMedio >= 0 ? "+" : "") + data.rMedio + "R"} tone={data.rMedio == null ? undefined : (data.rMedio >= 0 ? "positive" : "negative")} />
                <Kpi label="AVALIADAS" value={data.avaliadas} />
                <Kpi label="AGUARDANDO PRAZO" value={data.pendentes} />
              </div>
              {data.porSetup && Object.keys(data.porSetup).length > 0 && (
                <p style={{ marginTop: "10px", marginBottom: 0, fontSize: "11.5px", color: T.muted, lineHeight: 1.6 }}>
                  Por setup:{" "}
                  {Object.entries(data.porSetup).map(([s, v], i, arr) => (
                    <span key={s} style={{ fontFamily: MONO }}>{s} <b>{v.acerto}/{v.total}</b>{i < arr.length - 1 ? " · " : ""}</span>
                  ))}
                </p>
              )}
            </>
          )}
        </Estado>
        <div style={{ marginTop: "10px", fontSize: "10.5px", color: T.faint, lineHeight: 1.5 }}>
          Autoavaliação interna do sistema (prazo fixo de 10 pregões por análise, só quem tinha stop/alvo definidos) — não é garantia de resultado futuro.
          {data?.computedAt && <> Calculado em {new Date(data.computedAt).toLocaleString("pt-BR")}.</>}
        </div>
      </Card>

      {data && data.totalAnalises > 0 && (
        <Card title="Expectância">
          {data.expectanciaInsuficiente ? (
            <div style={{ fontSize: "12px", color: T.faint, lineHeight: 1.5 }}>
              {data.avaliadas === 0
                ? `Aguardando o prazo — expectância e profit factor aparecem quando ${minN} análises completarem os 10 pregões.`
                : `n insuficiente — a partir de ${minN} análises avaliadas (hoje: ${data.avaliadas}).`}
            </div>
          ) : (
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <Kpi label="EXPECTÂNCIA / ANÁLISE" value={data.expectancia == null ? null : (data.expectancia >= 0 ? "+" : "") + data.expectancia + "R"} tone={data.expectancia == null ? undefined : (data.expectancia >= 0 ? "positive" : "negative")} />
              <Kpi label="PROFIT FACTOR" value={data.profitFactor == null ? null : (data.profitFactor === "inf" ? "∞" : data.profitFactor)} tone={data.profitFactor == null ? undefined : ((data.profitFactor === "inf" || data.profitFactor >= 1) ? "positive" : "negative")} />
            </div>
          )}
        </Card>
      )}

      {data && data.totalAnalises > 0 && (
        <Card title="Calibração da confiança declarada">
          {data.avaliadas === 0 ? (
            <div style={{ fontSize: "12px", color: T.faint }}>Aguardando o prazo — a calibração aparece conforme as análises completam os 10 pregões.</div>
          ) : (
            <>
              {["alta", "moderada", "baixa", "—"].filter((k) => data.porConfianca && data.porConfianca[k]).map((k) => (
                <Celula key={k} rotulo={k === "—" ? "sem declaração" : "confiança " + k} c={data.porConfianca[k]} minN={minN} />
              ))}
            </>
          )}
        </Card>
      )}

      {data && data.totalAnalises > 0 && (
        <Card title="Curva de R acumulado">
          {(!data.curvaR || data.curvaR.length === 0) ? (
            <div style={{ fontSize: "12px", color: T.faint }}>Aguardando o prazo — a curva aparece conforme as análises completam os 10 pregões.</div>
          ) : (
            <>
              <RCurve pts={data.curvaR} />
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "10px" }}>
                <Kpi label="R ACUMULADO" value={data.rAcumulado == null ? null : (data.rAcumulado >= 0 ? "+" : "") + data.rAcumulado + "R"} tone={data.rAcumulado == null ? undefined : (data.rAcumulado >= 0 ? "positive" : "negative")} />
                <Kpi label="DRAWDOWN MÁX." value={data.drawdownMax == null ? "n insuf." : "−" + data.drawdownMax + "R"} tone={data.drawdownMax == null ? undefined : "negative"} />
              </div>
            </>
          )}
        </Card>
      )}
    </>
  );
}

const ORIGEM_LABEL = { manual: "Manual", automatico: "Automático (Operador)", sistema: "Sistema (expiração)", desconhecida: "Desconhecida (histórico antigo)" };

// ADR-013 — kill-switch do agente em runtime (antes só B3_AGENT_KILL/env).
// `execucao_automatica.ver` já dá a leitura (embutida na tela); o TOGGLE em
// si só aparece pra quem também tem `.controlar` — a UI esconde o botão,
// mas a rota valida a permissão de novo no backend de qualquer jeito.
function KillSwitchBox({ user, reload }) {
  const podeControlar = (user?.permissions || []).includes("execucao_automatica.controlar");
  const { loading, error, data, reload: reloadKs } = useFetch(() => api.killSwitchGet(), []);
  const [busy, setBusy] = useState(false);
  const [erroAcao, setErroAcao] = useState("");

  const alternar = async () => {
    setBusy(true); setErroAcao("");
    try {
      await api.killSwitchPut(!data.on);
      await reloadKs();
      if (reload) reload();
    } catch (e) {
      setErroAcao((e && e.message) || "Falha ao alternar o kill-switch.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Kill-switch do Operador (execução automática)">
      <Estado loading={loading} error={error}>
        {data && (
          <>
            <Kv label="Estado vigente" value={data.on ? "LIGADO (agente parado)" : "desligado (agente roda normalmente)"}
                tone={data.on ? "negative" : "positive"} />
            <div style={{ marginTop: "10px", fontSize: "11px", color: T.faint, lineHeight: 1.5 }}>
              Override em runtime sobre a env B3_AGENT_KILL — some no próximo deploy só se ninguém mexer aqui de novo.
            </div>
            {podeControlar ? (
              <button onClick={alternar} disabled={busy}
                      style={{ ...btnGhost, marginTop: "10px", opacity: busy ? 0.6 : 1,
                               borderColor: data.on ? T.positive : T.negative, color: data.on ? T.positive : T.negative }}>
                {busy ? "Aplicando…" : data.on ? "Desligar kill-switch" : "Ligar kill-switch"}
              </button>
            ) : (
              <div style={{ marginTop: "10px", fontSize: "11px", color: T.faint }}>Sem permissão para alternar (requer execucao_automatica.controlar).</div>
            )}
            {erroAcao && <div style={{ color: T.negative, fontSize: "12px", marginTop: "8px" }}>{erroAcao}</div>}
          </>
        )}
      </Estado>
    </Card>
  );
}

// ADR-012 (Fase 3): eficiência das operações automáticas — contagem/PnL por
// origem + correlação análise↔operação por snapshotId.
function Automacao({ user }) {
  const { loading, error, data, reload } = useFetch(() => api.automacao(), []);
  const cor = data?.correlacaoAnaliseOperacao;
  return (
    <>
      <KillSwitchBox user={user} />
      <Card title="Ordens por origem" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error} empty={data && data.totalOrdens === 0}>
          {data && data.totalOrdens > 0 && Object.entries(data.porOrigem || {}).map(([origem, v]) => (
            <Kv key={origem} label={ORIGEM_LABEL[origem] || origem}
                value={v.ordens + " ordem(ns) · PnL " + (v.pnlContagem > 0 ? (v.pnlTotal >= 0 ? "+" : "") + "R$ " + v.pnlTotal.toFixed(2) + " (" + v.pnlContagem + " venda(s))" : "— (sem venda ainda)")}
                tone={v.pnlContagem === 0 ? undefined : (v.pnlTotal >= 0 ? "positive" : "negative")} />
          ))}
        </Estado>
        <div style={{ marginTop: "10px", fontSize: "10.5px", color: T.faint, lineHeight: 1.5 }}>
          "Sistema" = liquidação por expiração de opção (ADR-005) — não é decisão do Operador, por isso separada de "Automático".
          {data?.computedAt && <> Calculado em {new Date(data.computedAt).toLocaleString("pt-BR")}.</>}
        </div>
      </Card>

      {cor && (
        <Card title="Análise → operação (correlação por snapshotId)">
          <Estado loading={loading} error={error} empty={cor.ordensDeEntrada === 0}>
            {cor.ordensDeEntrada > 0 && (
              <>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <Kpi label="ORDENS DE ENTRADA" value={cor.ordensDeEntrada} />
                  <Kpi label="COBERTURA (COM SNAPSHOT)" value={cor.coberturaPct == null ? null : cor.coberturaPct + "%"} />
                  <Kpi label="VINCULADAS A ANÁLISE" value={cor.vinculadasComAnaliseRegistrada} />
                  <Kpi label="RESOLVIDAS" value={cor.resolvidas} />
                  <Kpi label="SEGUIU ANÁLISE C/ SUCESSO" value={cor.seguiuAnaliseComSucesso} tone={cor.resolvidas > 0 ? (cor.seguiuAnaliseComSucesso / cor.resolvidas >= 0.5 ? "positive" : "negative") : undefined} />
                </div>
              </>
            )}
          </Estado>
          <div style={{ marginTop: "10px", fontSize: "10.5px", color: T.faint, lineHeight: 1.5 }}>
            Cobertura é parcial por natureza: `snapshotId` é campo opcional enviado pelo cliente na hora da ordem, nem toda ordem carrega — o número acima nunca é escondido atrás de uma métrica que pareça completa.
            Não mede tempo de reação nem slippage vs. previsto (esse dado não existe no sistema hoje).
          </div>
        </Card>
      )}
    </>
  );
}

// ADR-013 — "Mudança de LLM": provider/model/cota/rate/teto global da IA
// gerenciada, hoje só env (B3_MANAGED_LLM_*). `apiKey`/`baseUrl` NUNCA
// entram aqui — segredo, fora do escopo desta tela por desenho do backend.
function MudancaDeLLM({ user }) {
  const podeEditar = (user?.permissions || []).includes("llm.configurar");
  const { loading, error, data, reload } = useFetch(() => api.configIaGet(), []);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { if (data && !form) setForm(data); }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  const campo = (chave, label, placeholder) => (
    <div style={{ marginBottom: "10px" }}>
      <label style={{ display: "block", fontSize: "11px", color: T.muted, marginBottom: "4px" }}>{label}</label>
      <input value={form?.[chave] ?? ""} placeholder={placeholder} disabled={!podeEditar}
             onChange={(e) => setForm({ ...form, [chave]: e.target.value })}
             style={inputStyle} />
    </div>
  );

  const salvar = async () => {
    setBusy(true); setMsg("");
    try {
      // Achado de revisão: campo vazio era simplesmente OMITIDO do body —
      // não existia jeito de limpar um override já salvo. Agora manda TODOS
      // os 5 campos sempre; vazio vira `null` explícito, que o backend lê
      // como "reverte pro env" (db.admin_config_delete).
      const payload = {};
      for (const k of ["llmProvider", "llmModel"]) payload[k] = form[k] || null;
      for (const k of ["llmDailyQuota", "llmRatePerMin", "llmGlobalDailyCap"]) {
        if (form[k] === "" || form[k] == null) { payload[k] = null; continue; }
        const n = Number(form[k]);
        if (!Number.isNaN(n)) payload[k] = n;
      }
      const r = await api.configIaPut(payload);
      setMsg(Object.keys(r.alterado || {}).length ? "Salvo — auditado." : "Nada mudou.");
      // Achado de revisão: `form` nunca resincronizava com o servidor depois
      // de salvar (o guard `!form` do efeito abaixo virava um one-shot).
      // Limpar aqui faz o efeito rodar de novo quando o `reload()` trouxer
      // o estado FRESCO — sem isso a UI podia mostrar um valor que já não
      // era mais o vigente (ex.: um segundo admin mudou em paralelo).
      setForm(null);
      reload();
    } catch (e) {
      setMsg((e && e.message) || "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Mudança de LLM — IA gerenciada" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
      <Estado loading={loading} error={error}>
        {form && (
          <>
            {campo("llmProvider", "Provider (override)", "vazio = usa B3_MANAGED_LLM_PROVIDER")}
            {campo("llmModel", "Model (override)", "vazio = usa B3_MANAGED_LLM_MODEL")}
            {campo("llmDailyQuota", "Cota diária por usuário", "vazio = usa B3_MANAGED_DAILY_QUOTA")}
            {campo("llmRatePerMin", "Rate por minuto", "vazio = usa B3_MANAGED_RATE_PER_MIN")}
            {campo("llmGlobalDailyCap", "Teto global/dia", "vazio = usa B3_MANAGED_GLOBAL_DAILY_CAP")}
            {podeEditar && (
              <button onClick={salvar} disabled={busy}
                      style={{ marginTop: "6px", padding: "8px 14px", borderRadius: "8px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 700, fontSize: "12.5px", cursor: "pointer", opacity: busy ? 0.6 : 1 }}>
                {busy ? "Salvando…" : "Salvar (auditado)"}
              </button>
            )}
            {msg && <div style={{ marginTop: "8px", fontSize: "12px", color: T.muted }}>{msg}</div>}
            <div style={{ marginTop: "12px", fontSize: "10.5px", color: T.faint, lineHeight: 1.5 }}>
              A chave da IA (apiKey) e a baseUrl continuam só em env — não editáveis por aqui.
            </div>
          </>
        )}
      </Estado>
    </Card>
  );
}

// ADR-013 — generaliza o padrão que POST /api/obs/brapi/projecao já usava
// (a primeira rota admin-write migrada pro audit log).
function FontesDeDados({ user }) {
  const podeEditar = (user?.permissions || []).includes("fontes_dados.configurar");
  const { loading, error, data, reload } = useFetch(() => api.brapiProjecao(), []);
  const [intervalo, setIntervalo] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const aplicar = async () => {
    const n = Number(intervalo);
    if (!n || n < 30) { setMsg("Informe um intervalo válido (segundos, ≥ 30)."); return; }
    setBusy(true); setMsg("");
    try {
      await api.brapiProjecaoAplicar(n);
      setMsg("Aplicado — auditado.");
      reload();
    } catch (e) {
      setMsg((e && e.message) || "Falha ao aplicar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Fontes de dados — orçamento brapi" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
      <Estado loading={loading} error={error}>
        {data && (
          <>
            <Kv label="Intervalo vigente entre atualizações de spot" value={data.vigenteS + "s"} />
            <Kv label="Chamadas/mês projetadas no intervalo vigente" value={data.projecao?.chamadasMes ?? "—"} />
            {podeEditar && (
              <div style={{ marginTop: "10px", display: "flex", gap: "8px", alignItems: "center" }}>
                <input value={intervalo} onChange={(e) => setIntervalo(e.target.value)} placeholder="novo intervalo (s)"
                       style={{ ...inputStyle, width: "160px" }} />
                <button onClick={aplicar} disabled={busy}
                        style={{ padding: "9px 14px", borderRadius: "8px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 700, fontSize: "12.5px", cursor: "pointer", opacity: busy ? 0.6 : 1 }}>
                  {busy ? "Aplicando…" : "Aplicar (auditado)"}
                </button>
              </div>
            )}
            {msg && <div style={{ marginTop: "8px", fontSize: "12px", color: T.muted }}>{msg}</div>}
          </>
        )}
      </Estado>
    </Card>
  );
}

// ADR-013 (Decisão 5a) — prompts default GLOBAIS editáveis. NUNCA sobrescreve
// a edição PESSOAL de um usuário (`PUT /api/llm-prompts`, dele mesmo) — essa
// sempre tem prioridade; mecanismo no backend (`store._eh_default_antigo`).
function Prompts({ user }) {
  const podeEditar = (user?.permissions || []).includes("prompts.editar");
  const { loading, error, data, reload } = useFetch(() => api.promptsGet(), []);
  const [chaveAberta, setChaveAberta] = useState(null);
  const [texto, setTexto] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const abrir = (chave, atual) => { setChaveAberta(chave); setTexto(atual); setMsg(""); };

  const publicar = async () => {
    setBusy(true); setMsg("");
    try {
      await api.promptsPut(chaveAberta, texto);
      setMsg("Publicado — auditado. Contas que nunca editaram o próprio prompt migram no próximo login; quem editou fica intocado.");
      reload();
    } catch (e) {
      setMsg((e && e.message) || "Falha ao publicar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Prompts — default global">
      <Estado loading={loading} error={error}>
        {data && Object.entries(data).map(([chave, info]) => (
          <div key={chave} style={{ padding: "10px 0", borderBottom: `1px solid ${T.border}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "13px", color: T.text, fontWeight: 700 }}>{chave}</span>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <span style={{ fontSize: "10.5px", color: info.temOverride ? T.accent : T.faint }}>
                  {info.temOverride ? "editado pelo admin" : "default de código"}
                </span>
                {podeEditar && chaveAberta !== chave && (
                  <button onClick={() => abrir(chave, info.ativo)} style={btnGhost}>editar</button>
                )}
              </div>
            </div>
            {chaveAberta === chave && (
              <div style={{ marginTop: "8px" }}>
                <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={10}
                          style={{ ...inputStyle, fontFamily: MONO, fontSize: "11.5px", resize: "vertical" }} />
                <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                  <button onClick={publicar} disabled={busy}
                          style={{ padding: "7px 12px", borderRadius: "8px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 700, fontSize: "12px", cursor: "pointer", opacity: busy ? 0.6 : 1 }}>
                    {busy ? "Publicando…" : "Publicar (auditado)"}
                  </button>
                  <button onClick={() => setChaveAberta(null)} style={btnGhost}>cancelar</button>
                </div>
                {msg && <div style={{ marginTop: "8px", fontSize: "11.5px", color: T.muted, lineHeight: 1.5 }}>{msg}</div>}
              </div>
            )}
          </div>
        ))}
      </Estado>
    </Card>
  );
}

// ADR-013 — Usuários e papéis: atribuir/revogar um dos 7 grupos de macro
// função. SEM override de plano nesta rodada (decisão do Alex) — só leitura.
function Usuarios({ user }) {
  const { loading, error, data, reload } = useFetch(() => api.usersGet(), []);
  const [busyKey, setBusyKey] = useState(null);
  const [msg, setMsg] = useState("");

  const alternar = async (uid, role, tem) => {
    setBusyKey(uid + role); setMsg("");
    try {
      await api.userRole(uid, role, tem ? "revogar" : "conceder");
      reload();
    } catch (e) {
      setMsg((e && e.message) || "Falha ao alterar papel.");
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <Card title="Usuários e papéis">
      <Estado loading={loading} error={error} empty={data && (data.usuarios || []).length === 0}>
        {data && data.usuarios.map((u) => (
          <div key={u.id} style={{ padding: "10px 0", borderBottom: `1px solid ${T.border}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
              <span style={{ color: T.text }}>{u.email || u.id.slice(0, 10)}</span>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: T.faint }}>plano: {u.plan || "free"}</span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "6px" }}>
              {(data.gruposDisponiveis || []).map((role) => {
                const tem = (u.roles || []).includes(role);
                return (
                  <button key={role} onClick={() => alternar(u.id, role, tem)} disabled={busyKey === u.id + role}
                          style={{ ...btnGhost, fontSize: "10.5px", padding: "3px 8px",
                                   background: tem ? T.accent : "transparent", color: tem ? T.onAccent : T.muted,
                                   borderColor: tem ? T.accent : T.border, opacity: busyKey === u.id + role ? 0.5 : 1 }}>
                    {role}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </Estado>
      {msg && <div style={{ marginTop: "8px", fontSize: "12px", color: T.negative }}>{msg}</div>}
    </Card>
  );
}

// ADR-013 — toda escrita admin (config, fontes, prompts, papéis) grava aqui,
// sem exceção "por enquanto".
function Auditoria() {
  const { loading, error, data, reload } = useFetch(() => api.auditGet(200), []);
  return (
    <Card title="Auditoria" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
      <Estado loading={loading} error={error} empty={data && (data.eventos || []).length === 0}>
        {data && data.eventos.map((e) => (
          <div key={e.id} style={{ padding: "8px 0", borderBottom: `1px solid ${T.border}`, fontSize: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: T.muted }}>
              <span>{e.entity}{e.field ? " · " + e.field : ""}{e.entityId ? " · " + e.entityId : ""}</span>
              <span style={{ fontFamily: MONO, fontSize: "10.5px", color: T.faint }}>{new Date(e.at).toLocaleString("pt-BR")}</span>
            </div>
            <div style={{ fontFamily: MONO, fontSize: "11px", color: T.text, marginTop: "2px" }}>
              {JSON.stringify(e.oldValue)} → {JSON.stringify(e.newValue)}
            </div>
          </div>
        ))}
      </Estado>
    </Card>
  );
}

const btnGhost = { background: "transparent", border: `1px solid ${T.border}`, color: T.muted, borderRadius: "6px", padding: "4px 10px", fontSize: "11.5px", cursor: "pointer" };
const selectStyle = { background: T.bg, border: `1px solid ${T.border}`, color: T.text, borderRadius: "6px", padding: "4px 8px", fontSize: "12px" };

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const r = await api.login(email.trim(), password);
      setToken(r.token);
      // ADR-013: login válido não implica NENHUM papel administrativo — a
      // própria API decide (`permissions` em /api/auth/me). Não checa mais
      // uma permissão específica (obs/usage): alguém com só `prompts.editar`
      // é uma conta administrativa válida mesmo sem ver Observabilidade.
      if (!(r.user.permissions || []).length) {
        setToken(null);
        setError("Login correto, mas esta conta não tem nenhum papel administrativo.");
        return;
      }
      onLogin(r.user);
    } catch (e2) {
      setToken(null);
      setError((e2 && e2.message) || "Falha no login.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: T.bg, fontFamily: SANS }}>
      <form onSubmit={submit} style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: "12px", padding: "28px", width: "320px" }}>
        <div style={{ fontFamily: DISPLAY, fontSize: "16px", fontWeight: 600, color: T.text, marginBottom: "4px" }}>Boris+ · Observabilidade</div>
        <div style={{ fontSize: "12px", color: T.muted, marginBottom: "18px" }}>Acesso restrito ao administrador.</div>
        <input type="email" placeholder="e-mail" value={email} onChange={(e) => setEmail(e.target.value)} required
               style={inputStyle} />
        <input type="password" placeholder="senha" value={password} onChange={(e) => setPassword(e.target.value)} required
               style={{ ...inputStyle, marginTop: "8px" }} />
        {error && <div style={{ color: T.negative, fontSize: "12px", marginTop: "10px" }}>{error}</div>}
        <button type="submit" disabled={busy} style={{ marginTop: "16px", width: "100%", padding: "10px", borderRadius: "8px", border: "none", background: T.accent, color: T.onAccent, fontWeight: 700, fontSize: "13px", cursor: "pointer", opacity: busy ? 0.6 : 1 }}>
          {busy ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
const inputStyle = { width: "100%", boxSizing: "border-box", padding: "10px 12px", borderRadius: "8px", border: `1px solid ${T.border}`, background: T.bg, color: T.text, fontSize: "13px" };

// ADR-013: `perm` gate é COSMÉTICO — esconde a aba de quem não tem a
// permissão, mas toda rota que a tela chama valida de novo no backend
// (require_permission). Telas sem `perm` (as 5 originais) continuam abertas
// a qualquer papel administrativo, como sempre foram.
const VIEWS = [
  { id: "visaoGeral", label: "Visão Geral", C: VisaoGeral, perm: "observabilidade.ver" },
  { id: "custos", label: "Custos", C: Custos, perm: "observabilidade.ver" },
  { id: "comportamento", label: "Comportamento do Usuário", C: Comportamento, perm: "observabilidade.ver" },
  { id: "eficienciaIA", label: "Eficiência da IA", C: EficienciaIA, perm: "operador_ia.ver" },
  { id: "automacao", label: "Automação", C: Automacao, perm: "execucao_automatica.ver" },
  { id: "mudancaLLM", label: "Mudança de LLM", C: MudancaDeLLM, perm: "llm.configurar" },
  { id: "fontesDados", label: "Fontes de dados", C: FontesDeDados, perm: "fontes_dados.configurar" },
  { id: "prompts", label: "Prompts", C: Prompts, perm: "prompts.editar" },
  { id: "usuarios", label: "Usuários e papéis", C: Usuarios, perm: "usuarios.gerenciar" },
  { id: "auditoria", label: "Auditoria", C: Auditoria },
];

export default function App() {
  const [user, setUser] = useState(null);
  // `loggedIn` é a fonte da verdade pro render — NÃO chamar getToken() direto
  // no corpo do componente pra decidir a tela: um setState com o MESMO valor
  // (ex. setUser(null) quando `user` já era null, no logout de uma sessão
  // restaurada por token — nunca passou pelo onLogin) não dispara re-render,
  // e getToken() só seria reavaliado SE um re-render acontecesse. Bug real
  // encontrado ao testar: "Sair" limpava o token mas a tela não saía do ar.
  const [loggedIn, setLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);
  const [view, setView] = useState(null);

  useEffect(() => {
    if (!getToken()) { setChecking(false); return; }
    // ADR-013: usa /api/auth/me (não mais uma permissão específica) — o
    // mesmo endpoint já dispara o bootstrap idempotente do papel admin pra
    // sessões que existiam antes deste deploy.
    api.me()
      .then((r) => {
        if (!(r.user.permissions || []).length) { setToken(null); setChecking(false); return; }
        setUser(r.user); setLoggedIn(true); setChecking(false);
      })
      .catch(() => { setToken(null); setChecking(false); });
  }, []);

  const handleLogin = (u) => { setUser(u); setLoggedIn(true); };
  const handleLogout = () => { setToken(null); setUser(null); setLoggedIn(false); };

  if (checking) return <div style={{ minHeight: "100vh", background: T.bg, color: T.muted, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px" }}>Verificando sessão…</div>;
  if (!loggedIn) return <Login onLogin={handleLogin} />;

  // ADR-013: filtro cosmético por permissão — toda rota que a tela chama
  // valida de novo no backend, isto só evita mostrar uma aba que vai dar 403.
  const perms = user?.permissions || [];
  const visiveis = VIEWS.filter((v) => !v.perm || perms.includes(v.perm));
  const viewAtual = visiveis.find((v) => v.id === view) ? view : visiveis[0]?.id;
  const ViewC = visiveis.find((v) => v.id === viewAtual)?.C || VisaoGeral;
  return (
    <div style={{ minHeight: "100vh", background: T.bg, color: T.text, fontFamily: SANS }}>
      <div style={{ borderBottom: `1px solid ${T.border}`, padding: "12px 20px", display: "flex", alignItems: "center", gap: "20px" }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 600, fontSize: "15px" }}>Boris+ · Administração</div>
        <nav style={{ display: "flex", gap: "4px", flex: 1, flexWrap: "wrap" }}>
          {visiveis.map((v) => (
            <button key={v.id} onClick={() => setView(v.id)}
                    style={{ padding: "7px 12px", borderRadius: "6px", border: "none", cursor: "pointer",
                             background: viewAtual === v.id ? T.accent : "transparent",
                             color: viewAtual === v.id ? T.onAccent : T.muted, fontSize: "12.5px", fontWeight: 700 }}>
              {v.label}
            </button>
          ))}
        </nav>
        {user?.email && <span style={{ fontSize: "12px", color: T.faint }}>{user.email}</span>}
        <button onClick={handleLogout} style={btnGhost}>Sair</button>
      </div>
      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "20px" }}>
        <ViewC user={user} />
      </div>
    </div>
  );
}
