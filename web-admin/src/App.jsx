import { useState, useEffect, useCallback } from "react";
import { api, getToken, setToken } from "./api.js";

// ADR-011 Decisão 6: vocabulário visual de ops densa em dado — grid de
// status, fonte MONO pra número/timestamp, sem paradigma mobile-first do
// app consumidor. Paleta mínima, própria desta app (não reusa web/src/App.jsx).
const T = {
  bg: "#0b0e14", card: "#12151d", border: "#232838",
  text: "#e7ebf3", muted: "#8b93a7", faint: "#5b6377",
  accent: "#4f8cff", positive: "#3ecb8f", negative: "#f2555a", warn: "#e0a33e",
};
const MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

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

function VisaoGeral() {
  const { loading, error, data, reload } = useFetch(() => api.agentStatus(), []);
  return (
    <Card title="Visão Geral" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
      <Estado loading={loading} error={error}>
        {data && (
          <>
            <Kv label="Kill-switch" value={data.killSwitch ? "LIGADO" : "desligado"} tone={data.killSwitch ? "negative" : undefined} />
            <Kv label="Pregão" value={data.pregaoAberto ? "aberto" : "fechado"} />
            <Kv label="Usuários habilitados (Operador)" value={data.usuariosHabilitados} />
            <Kv label="Proteção sem Operador" value={data.protecaoSemOperador} tone={data.protecaoSemOperador > 0 ? "warn" : undefined} />
            <Kv label="Heartbeat — laço vivo" value={data.heartbeat?.lacoVivo ? "sim" : "NÃO"} tone={data.heartbeat?.lacoVivo ? "positive" : "negative"} />
            <Kv label="Heartbeat — última batida" value={data.heartbeat?.atBRT || "—"} />
            <Kv label="Próxima passada" value={data.proximaPassadaEmS != null ? data.proximaPassadaEmS + "s" : "—"} />
            <Kv label="Último ciclo — executadas" value={data.ultimoCiclo?.executadas ?? "—"} />
            <Kv label="Último ciclo — erro" value={data.ultimoCiclo?.erro || "nenhum"} tone={data.ultimoCiclo?.erro ? "negative" : undefined} />
            <Kv label="Radar diário — última varredura" value={data.radarDiario?.date || "nunca rodou"} />
            <Kv label="Radar diário — erro" value={data.radarDiario?.erro || "nenhum"} tone={data.radarDiario?.erro ? "negative" : undefined} />
            <Kv label="Avaliação de análises — última" value={data.avaliacaoAnalises?.date || "nunca rodou"} />
            <Kv label="Aquecimento de fundamentos — última" value={data.aquecimentoFundamentos?.date || "nunca rodou"} />
            <Kv label="Aquecimento de fundamentos — aquecidos" value={data.aquecimentoFundamentos?.aquecidos ?? "—"} />
            <Kv label="Intraday — última passada" value={data.intraday?.atLabel || "nunca rodou"} />
            <Kv label="Intraday — ativos com lacuna" value={data.intraday?.comLacuna ?? "—"} />
            <Kv label="Push automático — falhas hoje" value={data.pushAutomaticoFalhasHoje?.falhas ?? 0} tone={(data.pushAutomaticoFalhasHoje?.falhas ?? 0) > 0 ? "warn" : undefined} />
          </>
        )}
      </Estado>
    </Card>
  );
}

function Custos() {
  const { loading, error, data, reload } = useFetch(() => api.obsUsage(), []);
  return (
    <>
      <Card title="Uso de IA" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error}>
          {data && (
            <>
              <Kv label="IA gerenciada ativa" value={data.iaGerenciadaAtiva ? "sim" : "não"} />
              <Kv label="Cota por usuário/dia" value={data.cotaPorUsuarioDia ?? "ilimitada"} />
              <Kv label="Teto global/dia" value={data.tetoGlobalDia ?? "ilimitado"} />
              <Kv label="Análises gerenciadas — usado hoje" value={data.analisesGerenciadas?.used ?? "—"} />
              <Kv label="Análises gerenciadas — restante hoje" value={data.analisesGerenciadas?.remaining ?? "—"} />
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
            </>
          )}
        </Estado>
      </Card>
      <Card title="Cache de candles (L2)">
        <Estado loading={loading} error={error} empty={data && Object.keys(data.cacheCandles || {}).length === 0}>
          {data && (
            <div style={{ fontSize: "12.5px", color: T.muted }}>
              {Object.keys(data.cacheCandles || {}).length} série(s) em cache — {Object.entries(data.cacheCandles || {}).slice(0, 20).map(([k, v]) => `${k} (${v.n})`).join(" · ")}
            </div>
          )}
        </Estado>
      </Card>
      <div style={{ fontSize: "11.5px", color: T.faint, lineHeight: 1.5 }}>
        Mensalidade do Railway não é medida no código — ver qa/42-finops.md (custo externo, atualizado manualmente).
      </div>
    </>
  );
}

function Comportamento() {
  const [dias, setDias] = useState(30);
  const { loading, error, data, reload } = useFetch(() => api.analyticsSummary(dias), [dias]);
  return (
    <>
      <Card title="Adoção por feature" right={
        <select value={dias} onChange={(e) => setDias(Number(e.target.value))} style={selectStyle}>
          <option value={7}>7 dias</option>
          <option value={30}>30 dias</option>
          <option value={90}>90 dias</option>
        </select>
      }>
        <Estado loading={loading} error={error} empty={data && (data.adocaoPorFeature || []).length === 0}>
          {data && (data.adocaoPorFeature || []).map((r) => (
            <Kv key={r.event} label={r.event} value={r.count + " eventos · " + r.usuariosDistintos + " usuário(s)"} />
          ))}
        </Estado>
      </Card>
      <Card title="Funil onboarding → trade_simulated">
        <Estado loading={loading} error={error} empty={data && (data.funil?.passos || []).length === 0}>
          {data && (data.funil?.passos || []).map((p) => (
            <Kv key={p.passo} label={p.passo} value={p.usuarios + " usuário(s)"} />
          ))}
        </Estado>
      </Card>
      <Card title="Shown vs. dismissed" right={<button onClick={reload} style={btnGhost}>↻ atualizar</button>}>
        <Estado loading={loading} error={error} empty={data && (data.shownVsDismissed || []).length === 0}>
          {data && (data.shownVsDismissed || []).map((r) => (
            <Kv key={r.feature} label={r.feature} value={r.shown + " mostrado(s) · " + r.dismissed + " fechado(s)"} />
          ))}
        </Estado>
      </Card>
    </>
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
      // Login válido não implica admin — a própria API decide (_is_obs_admin).
      // Confirma ANTES de considerar a sessão desta app estabelecida.
      await api.obsUsage();
      onLogin(r.user);
    } catch (e2) {
      if (e2 && e2.status === 403) {
        setToken(null);
        setError("Login correto, mas esta conta não tem acesso administrativo (B3_ADMIN_EMAILS).");
      } else {
        setToken(null);
        setError((e2 && e2.message) || "Falha no login.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: T.bg }}>
      <form onSubmit={submit} style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: "12px", padding: "28px", width: "320px" }}>
        <div style={{ fontSize: "15px", fontWeight: 800, color: T.text, marginBottom: "4px" }}>Boris+ · Observabilidade</div>
        <div style={{ fontSize: "12px", color: T.muted, marginBottom: "18px" }}>Acesso restrito ao administrador.</div>
        <input type="email" placeholder="e-mail" value={email} onChange={(e) => setEmail(e.target.value)} required
               style={inputStyle} />
        <input type="password" placeholder="senha" value={password} onChange={(e) => setPassword(e.target.value)} required
               style={{ ...inputStyle, marginTop: "8px" }} />
        {error && <div style={{ color: T.negative, fontSize: "12px", marginTop: "10px" }}>{error}</div>}
        <button type="submit" disabled={busy} style={{ marginTop: "16px", width: "100%", padding: "10px", borderRadius: "8px", border: "none", background: T.accent, color: "#fff", fontWeight: 700, fontSize: "13px", cursor: "pointer", opacity: busy ? 0.6 : 1 }}>
          {busy ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
const inputStyle = { width: "100%", boxSizing: "border-box", padding: "10px 12px", borderRadius: "8px", border: `1px solid ${T.border}`, background: T.bg, color: T.text, fontSize: "13px" };

const VIEWS = [
  { id: "visaoGeral", label: "Visão Geral", C: VisaoGeral },
  { id: "custos", label: "Custos", C: Custos },
  { id: "comportamento", label: "Comportamento do Usuário", C: Comportamento },
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
  const [view, setView] = useState("visaoGeral");

  useEffect(() => {
    if (!getToken()) { setChecking(false); return; }
    api.obsUsage()
      .then(() => { setLoggedIn(true); setChecking(false); }) // token válido — mantém sessão; e-mail some do header até recarregar, aceitável (não afeta acesso)
      .catch(() => { setToken(null); setChecking(false); });
  }, []);

  const handleLogin = (u) => { setUser(u); setLoggedIn(true); };
  const handleLogout = () => { setToken(null); setUser(null); setLoggedIn(false); };

  if (checking) return <div style={{ minHeight: "100vh", background: T.bg, color: T.muted, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px" }}>Verificando sessão…</div>;
  if (!loggedIn) return <Login onLogin={handleLogin} />;

  const ViewC = VIEWS.find((v) => v.id === view)?.C || VisaoGeral;
  return (
    <div style={{ minHeight: "100vh", background: T.bg, color: T.text, fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif" }}>
      <div style={{ borderBottom: `1px solid ${T.border}`, padding: "12px 20px", display: "flex", alignItems: "center", gap: "20px" }}>
        <div style={{ fontWeight: 800, fontSize: "14px" }}>Boris+ · Observabilidade</div>
        <nav style={{ display: "flex", gap: "4px", flex: 1 }}>
          {VIEWS.map((v) => (
            <button key={v.id} onClick={() => setView(v.id)}
                    style={{ padding: "7px 12px", borderRadius: "6px", border: "none", cursor: "pointer",
                             background: view === v.id ? T.accent : "transparent",
                             color: view === v.id ? "#fff" : T.muted, fontSize: "12.5px", fontWeight: 700 }}>
              {v.label}
            </button>
          ))}
        </nav>
        {user?.email && <span style={{ fontSize: "12px", color: T.faint }}>{user.email}</span>}
        <button onClick={handleLogout} style={btnGhost}>Sair</button>
      </div>
      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "20px" }}>
        <ViewC />
      </div>
    </div>
  );
}
