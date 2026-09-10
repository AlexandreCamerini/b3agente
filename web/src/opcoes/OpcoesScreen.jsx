/**
 * OpcoesScreen.jsx — aba-opcoes F2 (ADR-027, quick 260910-biz, 2026-09-10).
 *
 * Primeira superfície real da aba Opções: o que o serviço `mcp.semente.dev`
 * já sabe sobre um ticker — comportamento recente, catálogo de estruturas,
 * vencimentos e os setups gravados com a avaliação do dia. Sem cadeia, sem
 * payoff, sem veredito (Fases 3–4 do `docs/PLANO-aba-opcoes.md`).
 *
 * Regras que esta tela NÃO negocia:
 * · nenhum número é recalculado aqui — tudo vem do serviço, e campo ausente
 *   vira travessão, nunca 0 (princípio 4/5 do CLAUDE.md);
 * · "em dia" só aparece com frescor MEDIDO — "não medido" que vira silêncio
 *   é lido como "em dia" (ADR-027, Decisão 8); e "nada foi consultado" não
 *   vira "não medido" — achado ao vivo 2026-09-10 (quick 260910-d57);
 * · erro escolhido por `code` conhecido (ADR-027), nunca pela chamada que
 *   respondeu primeiro — mesmo achado ao vivo;
 * · o motivo de uma recusa do serviço vai VERBATIM, sem reescrita;
 * · vazio nunca é silêncio: todo estado vazio diz o porquê.
 */
import { useState } from "react";
import { useOpcoesMcp } from "./useOpcoesMcp.js";
import SetupChart from "./SetupChart.jsx";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root` — padrão de
// `pet/BorisChat.jsx`. Zero import de `App.jsx` (seria ciclo).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const pct = (v, casas = 2) => (ehNum(v) ? fmt(v, casas) + "%" : "—");
// `hv21`/`hv63` chegam como FRAÇÃO (0,31 = 31%). A conversão para % é
// formatação da mesma grandeza, não conta nova — é exatamente como o portal
// do próprio serviço a exibe. Sem valor, travessão.
const fracPct = (v) => (ehNum(v) ? fmt(v * 100, 1) + "%" : "—");
const txt = (v) => (typeof v === "string" && v ? v : "—");

function Linha({ rotulo, valor }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
      <span style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</span>
      <span style={{ fontSize: "12.5px", color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{valor}</span>
    </div>
  );
}

function Kicker({ children }) {
  return (
    <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", color: T.textMuted, margin: "18px 0 8px" }}>
      {children}
    </div>
  );
}

function Aviso({ children, tom }) {
  return (
    <div style={{ border: `1px solid ${tom === "forte" ? T.negative : T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel, color: T.textSecondary, fontSize: "12.5px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

export default function OpcoesScreen({ ctx }) {
  const cp = (ctx && ctx.cp) || {};
  const store = ctx && ctx.store;
  const palette = (ctx && ctx.palette) || {};
  // Universo = a watchlist do usuário. Não se inventa um universo aqui, e
  // não há chamada extra para descobrir tickers.
  const watchlist = (ctx && ctx.data && ctx.data.watchlist) || [];
  const [ticker, setTicker] = useState("");
  const { status, leitura, grafico, abrirGrafico, fecharGrafico } = useOpcoesMcp(store, ticker);

  const l = leitura.dados;
  const behavior = l && l.behavior;
  const setups = (l && Array.isArray(l.setups) && l.setups) || [];
  const naoAvaliado = l && l.setupsNaoAvaliados;

  // O frescor da leitura manda; sem leitura, o do `/status` (que é o
  // medido de verdade, com cache de 600 s no cliente MCP).
  const frescor = (l && l.frescor) || (status.dados && status.dados.frescor) || null;
  const pregao = (l && l.pregao) || (status.dados && status.dados.pregao) || null;
  const fonte = (l && l.fonte) || (status.dados && status.dados.fonte) || null;

  // Chip de frescor em TRÊS variantes, pela ORIGEM da informação — nunca um
  // default genérico que sobra quando ninguém respondeu:
  //   (a) `!frescor` — nada foi consultado ainda (achado ao vivo, produção
  //       sem a Fase 2: `/leitura` 404 e `frescor` fica nulo). O chip não
  //       afirma nada: fica de fora. Mesma simetria que este arquivo já
  //       aplica aos setups ("sem avaliação NÃO vira não armado: ausência de
  //       leitura não é leitura negativa") — aqui, ausência de resposta não
  //       vira "não medido". Omitir em vez de travessão porque o cabeçalho
  //       já tem `Pregão: —`; um segundo traço solto ao lado seria ruído sem
  //       ganho de informação.
  //   (b) `frescor.medido === false` — o serviço respondeu e não mediu:
  //       "não medido" continua, e agora é verdade (houve resposta).
  //   (c) `frescor.medido === true` — em dia / atrasado com idade.
  let chip = null;
  if (frescor && frescor.medido === false) {
    chip = cp.opcoesFrescorNaoMedido || "frescor não medido";
  } else if (frescor && frescor.medido) {
    const critica = (frescor.classes || [])[0];
    const idade = critica && ehNum(critica.idadeHoras) ? " (" + fmt(critica.idadeHoras, 0) + " h)" : "";
    chip = frescor.bloqueia
      ? (cp.opcoesFrescorAtrasado || "dado atrasado") + idade
      : (cp.opcoesFrescorEmDia || "dado em dia");
  }

  const erro = escolherErroOpcoes(leitura.erro, status.erro);
  const carregando = status.carregando || leitura.carregando;
  const semTicker = !ticker;
  const semCandles = !!(behavior && behavior.status === "sem_candles");
  const temLeitura = !!(behavior && !semCandles);
  const nadaParaMostrar = semTicker || (!temLeitura && setups.length === 0);

  const cabecalho = (
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "14px", padding: "12px 14px", background: T.bgPanel }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "baseline", justifyContent: "space-between" }}>
        <div style={{ fontSize: "12.5px", color: T.textSecondary }}>
          {(cp.opcoesPregaoRotulo || "Pregão") + ": "}
          <strong style={{ color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{pregao || "—"}</strong>
        </div>
        <div style={{ fontSize: "12px", color: T.textMuted }}>
          {/* Mesma regra do chip: sem resposta do serviço, não se afirma
              origem — o default literal "mcp.semente.dev" mentia a fonte
              mesmo com `/status`/`/leitura` fora do ar. Travessão aqui (não
              omissão) porque este rótulo já convive ao lado do "Pregão: —"
              no mesmo padrão visual. */}
          {(cp.opcoesFonteRotulo || "Fonte") + ": " + (fonte || "—")}
        </div>
        {chip ? (
          <span style={{ fontSize: "11.5px", fontWeight: 700, color: T.textSecondary, border: `1px solid ${T.borderSubtle}`, borderRadius: "999px", padding: "3px 9px" }}>
            {chip}
          </span>
        ) : null}
      </div>
      {frescor && frescor.bloqueia && frescor.warning ? (
        <div style={{ marginTop: "8px", fontSize: "12px", color: T.textSecondary, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
          {frescor.warning}
        </div>
      ) : null}
    </div>
  );

  const seletor = (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", margin: "14px 0 4px" }}>
      {watchlist.map((t) => (
        <button
          key={t}
          onClick={() => setTicker(t === ticker ? "" : t)}
          aria-pressed={t === ticker}
          style={{ minHeight: "44px", padding: "8px 14px", borderRadius: "11px", border: `1px solid ${t === ticker ? T.accent : T.borderSubtle}`, background: t === ticker ? T.accentTint10 : T.bgPanel, color: t === ticker ? T.accent : T.textSecondary, fontWeight: 700, fontSize: "13px" }}
        >
          {t}
        </button>
      ))}
    </div>
  );

  return (
    <section>
      <h1 style={{ fontSize: "22px", fontWeight: 800, margin: "0 0 4px" }}>{cp.tituloOpcoes || "Opções"}</h1>
      <p style={{ fontSize: "13px", color: T.textSecondary, margin: "0 0 14px", lineHeight: 1.5 }}>
        {cp.subtituloOpcoes || ""}
      </p>

      {cabecalho}
      {watchlist.length > 0 ? seletor : null}

      {/* ------------------------------------------------ 1. CARREGANDO --
          Antes do vazio, sempre: vazio pintado durante a consulta afirma
          "não há nada" sem ninguém ter medido. */}
      {carregando ? (
        <div style={{ marginTop: "14px" }}>
          <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
        </div>
      ) : erro ? (
        /* ------------------------------------------ 2. ERRO / DEGRADAÇÃO --
           Escolhido pelo `code` do backend (ADR-027), nunca por raspagem da
           mensagem. Cada código tem seu estado próprio — nenhum vira tela
           em branco. */
        <div style={{ marginTop: "14px" }}>
          {erro.code === "mcp_nao_configurado" ? (
            <Aviso>{cp.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>
          ) : erro.code === "mcp_cota" || erro.code === "mcp_teto_servico" ? (
            <Aviso>
              {(cp.opcoesCota || ((r) => "Cota esgotada." + (r ? " Reinicia às " + r + "." : "")))(
                erro.detail && erro.detail.reinicia)}
            </Aviso>
          ) : erro.code === "mcp_indisponivel" ? (
            <Aviso>{cp.opcoesIndisponivel || "Serviço de opções sem resposta agora."}</Aviso>
          ) : (
            /* Inclui `mcp_erro_de_tool`: a mensagem já vem multi-linha com
               "Como corrigir:" / "Dica:" do enrichErrorMessage — vai CRUA,
               em nó de texto (React escapa), com pre-wrap. */
            <Aviso tom="forte">{erro.message}</Aviso>
          )}
        </div>
      ) : nadaParaMostrar ? (
        /* ------------------------------------------ 3. VAZIO COM MOTIVO --
           Vazio nunca é silêncio. */
        <div style={{ marginTop: "14px", display: "grid", gap: "10px" }}>
          {semTicker ? (
            <Aviso>{cp.opcoesEscolherAtivo || "Escolha um ativo para ver a leitura."}</Aviso>
          ) : null}
          {semCandles ? (
            <Aviso>
              O serviço não tem candles para este ativo, então não há leitura de
              comportamento para mostrar. Nada foi estimado no lugar.
            </Aviso>
          ) : null}
          {!semTicker && setups.length === 0 ? (
            <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
          ) : null}
        </div>
      ) : (
        /* ------------------------------------------------------ 4. DADOS -- */
        <div>
          {temLeitura ? (
            <>
              <Kicker>{cp.opcoesLeituraTitulo || "LEITURA DO ATIVO"}</Kicker>
              <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "4px 14px 10px", background: T.bgPanel }}>
                <Linha rotulo="Tendência" valor={txt(behavior.trend)} />
                <Linha rotulo="Fechamento" valor={fmt(behavior.close)} />
                <Linha rotulo="RSI 14" valor={fmt(behavior.rsi14, 1)} />
                <Linha rotulo="HV 21" valor={fracPct(behavior.hv21)} />
                <Linha rotulo="HV 63" valor={fracPct(behavior.hv63)} />
                <Linha rotulo="Distância da média 21" valor={pct(behavior.distance_from_sma21_pct, 1)} />
                <Linha rotulo="Distância da média 63" valor={pct(behavior.distance_from_sma63_pct, 1)} />
                <Linha
                  rotulo="Faixa de 63 pregões"
                  valor={behavior.range_63_sessions
                    ? fmt(behavior.range_63_sessions.lowest) + " – " + fmt(behavior.range_63_sessions.highest)
                    : "—"}
                />
                <Linha rotulo="Variação em 21 pregões" valor={pct(behavior.change_21_sessions_pct, 1)} />
              </div>
              <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px" }}>
                {"Leitura referente ao pregão de " + (behavior.trading_date || pregao || "—") + "."}
              </div>
            </>
          ) : semCandles ? (
            <div style={{ marginTop: "14px" }}>
              <Aviso>
                O serviço não tem candles para este ativo — sem leitura de
                comportamento. Os setups abaixo continuam valendo.
              </Aviso>
            </div>
          ) : null}

          {Array.isArray(l && l.expirations) && l.expirations.length > 0 ? (
            <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "10px" }}>
              {"Vencimentos disponíveis: " + l.expirations.join(" · ")}
            </div>
          ) : null}

          <Kicker>{cp.opcoesSetupsTitulo || "SETUPS GRAVADOS"}</Kicker>

          {naoAvaliado ? (
            <div style={{ marginBottom: "10px" }}>
              <Aviso>
                {(cp.opcoesNaoAvaliado || ((m) => "Setups não avaliados hoje." + (m ? " " + m : "")))(
                  naoAvaliado.reason)}
              </Aviso>
            </div>
          ) : null}

          {setups.length === 0 ? (
            <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
          ) : (
            <div style={{ display: "grid", gap: "10px" }}>
              {setups.map((s) => {
                const av = s.avaliacao;
                const aberto = grafico.setup === s.name;
                return (
                  <div key={s.name} style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px 14px", background: T.bgPanel }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "baseline" }}>
                      <div style={{ fontSize: "14px", fontWeight: 700, color: T.textPrimary }}>{s.name}</div>
                      <div style={{ fontSize: "11.5px", color: T.textMuted }}>{"registro: " + txt(s.status)}</div>
                    </div>

                    {av ? (
                      <div style={{ fontSize: "12.5px", color: T.textSecondary, marginTop: "6px" }}>
                        {"avaliação: " + txt(av.status)}
                        {" · armado: " + (s.armed === true ? "sim" : s.armed === false ? "não" : "—")}
                        {" · sequência: " + (ehNum(s.streak) ? s.streak : "—")
                          + "/" + (ehNum(s.required_streak) ? s.required_streak : "—")}
                      </div>
                    ) : (
                      /* Sem avaliação NÃO vira "não armado": ausência de
                         leitura não é leitura negativa. */
                      <div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "6px" }}>
                        {"sem avaliação hoje · exige "
                          + (ehNum(s.required_streak) ? s.required_streak : "—")
                          + " pregão(s) seguidos"}
                      </div>
                    )}

                    {Array.isArray(s.conditions) && s.conditions.length > 0 ? (
                      <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none" }}>
                        {s.conditions.map((c, i) => (
                          <li key={i} style={{ fontSize: "12.5px", color: T.textSecondary, padding: "3px 0" }}>
                            <span aria-hidden style={{ marginRight: "6px", color: T.textFaint }}>
                              {c && c.met ? "✓" : "·"}
                            </span>
                            {(c && (c.summary || c.label)) || "—"}
                            <span style={{ color: T.textFaint }}>{c && c.met ? " (atendida)" : " (não atendida)"}</span>
                          </li>
                        ))}
                      </ul>
                    ) : null}

                    {s.backtest_na_criacao && ehNum(s.backtest_na_criacao.disparos) ? (
                      <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "8px" }}>
                        {"Na criação, este setup disparou " + s.backtest_na_criacao.disparos
                          + " vez(es) no histórico. Contagem passada, não expectativa."}
                      </div>
                    ) : null}

                    <button
                      onClick={() => (aberto ? fecharGrafico() : abrirGrafico(s.name))}
                      aria-pressed={aberto}
                      aria-label={(aberto ? "Fechar" : "Ver") + " disparos do setup " + s.name}
                      style={{ marginTop: "10px", width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}
                    >
                      {aberto ? "Fechar gráfico" : (cp.opcoesGraficoTitulo || "Disparos do setup")}
                    </button>

                    {aberto ? (
                      <div style={{ marginTop: "10px" }}>
                        {grafico.carregando ? (
                          <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                        ) : grafico.erro ? (
                          <Aviso tom="forte">{grafico.erro.message}</Aviso>
                        ) : grafico.dados ? (
                          <SetupChart ctx={ctx} grafico={grafico.dados} palette={palette} cp={cp} />
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <p style={{ marginTop: "20px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.55 }}>
        {cp.opcoesDisclaimer || ""}
      </p>
    </section>
  );
}

// Códigos de degradação do ADR-027 que dizem à pessoa O QUE FAZER ("não
// configurado", "sem cota", "fora do ar"). Um erro SEM código conhecido (ex.:
// 404 genérico de rota) não carrega essa informação. Declarado no fim do
// arquivo (não antes do componente) para não empurrar a string literal
// "mcp_nao_configurado" para antes do primeiro uso real dela na cadeia de
// estados (carregando → erro → vazio → dados) — `function`/`const` de módulo
// já estão avaliados quando o componente roda, independente da ordem física.
const CODIGOS_ACIONAVEIS = ["mcp_nao_configurado", "mcp_cota", "mcp_teto_servico", "mcp_indisponivel"];

// Achado ao vivo (2026-09-10): `leitura.erro || status.erro` deixava o 404 da
// leitura (dispara sempre que a pessoa escolhe um ticker, mesmo com o
// serviço fora do ar) mascarar o `mcp_nao_configurado` do `/status` — que é
// o único dos dois que diz o que fazer. Escolha por ACIONABILIDADE: erro COM
// `code` conhecido vence erro SEM código, venha de onde vier; com os dois
// codificados (ou os dois sem código), a leitura vence — é a chamada que a
// pessoa disparou ao escolher o ticker.
function escolherErroOpcoes(erroLeitura, erroStatus) {
  const acionavel = (e) => !!(e && CODIGOS_ACIONAVEIS.includes(e.code));
  if (!erroLeitura) return erroStatus;
  if (!erroStatus) return erroLeitura;
  if (acionavel(erroStatus) && !acionavel(erroLeitura)) return erroStatus;
  return erroLeitura;
}
