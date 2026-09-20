/**
 * SecaoSetups.jsx — Fase 33 (33-03), extração de OpcoesScreen.jsx.
 *
 * Job 5 do PROJECT.md ("gerenciar/criar setups salvos") — hoje inline em
 * OpcoesScreen.jsx (listagem "SETUPS GRAVADOS" + porta "CRIAR UM SETUP").
 * Comportamento idêntico, zero funcionalidade nova (D-03 do 33-CONTEXT.md).
 * Recebe TUDO por prop; não lê o estado bruto nem chama hook de dado nenhum
 * diretamente — só o orquestrador (OpcoesScreen) faz isso (padrão Emenda 3
 * do ADR-027, já replicado por SecaoVigias.jsx/SecaoDescobrir.jsx nas Fases
 * 33-01/33-02).
 *
 * `CriarSetup.jsx` NÃO é reescrito nem renomeado (D-01 do 33-CONTEXT.md) —
 * esta seção só o ENVOLVE, exatamente como `OpcoesScreen.jsx` fazia antes.
 * `CriarSetup` é deliberadamente um componente sem fonte de dado própria
 * (comentário original em OpcoesScreen.jsx); esta seção não é diferente:
 * a tabela de custo chega por PROP (`custos`), nunca importada daqui.
 *
 * Regra que esta extração NÃO pode afrouxar (Fase 27, 27-02): a partir da
 * `/leitura`, cada setup tem DOIS nomes — `nomeNoServico` é a chave no
 * ARMAZÉM compartilhado do serviço (com o prefixo de 8 hexadecimais da
 * conta), `name` é o nome que a PESSOA escreveu. Tudo que VIAJA ao serviço
 * (`abrirGrafico`, `BotaoDesativar`) usa `chave = s.nomeNoServico || s.name`;
 * tudo que a pessoa LÊ usa `s.name`. Confundir os dois manda um nome sem
 * prefixo ao serviço — 422 `setup_desconhecido`, o defeito real do 27-02.
 */
import { Kicker, Aviso } from "./uiOpcoes.jsx";
import SetupChart from "./SetupChart.jsx";
import CriarSetup, { BotaoDesativar } from "./CriarSetup.jsx";

// Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` —
// espelho declarado, mesmo padrão dos irmãos desta pasta. Zero import do
// núcleo do app (seria ciclo, ADR-027 Decisão 3).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["borderSubtle", "bgPanel", "textPrimary", "textMuted", "textSecondary", "textFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const txt = (v) => (typeof v === "string" && v ? v : "—");

// Fase 27 (27-05) — a SEGUNDA LINHA do botão, onde o custo é declarado. Mesmo
// padrão dos irmãos desta pasta (espelho declarado local, nunca importado do
// núcleo do app).
const CUSTO_NO_BOTAO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.textMuted, marginTop: "3px",
};

export default function SecaoSetups({
  ticker, setups, naoAvaliado, grafico, abrirGrafico, fecharGrafico,
  setupNovo, compilarSetup, confirmarSetup, desativarSetup,
  podeCriarSetup, custos, cp, ctx, palette,
}) {
  const listaSetups = Array.isArray(setups) ? setups : [];
  return (
    <>
      <Kicker>{cp.opcoesSetupsTitulo || "SETUPS GRAVADOS"}</Kicker>

      {naoAvaliado ? (
        <div style={{ marginBottom: "10px" }}>
          <Aviso>
            {(cp.opcoesNaoAvaliado || ((m) => "Setups não avaliados hoje." + (m ? " " + m : "")))(
              naoAvaliado.reason)}
          </Aviso>
        </div>
      ) : null}

      {listaSetups.length === 0 ? (
        <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {listaSetups.map((s) => {
            const av = s.avaliacao;
            // Fase 27 (27-02) — DOIS nomes, e confundi-los quebra a tela.
            // A partir do 27-01 a `/leitura` devolve `name` = o nome que a
            // PESSOA escreveu e `nomeNoServico` = a chave real no armazém
            // compartilhado (com o prefixo de 8 hexadecimais da conta).
            // Tudo que VIAJA ao serviço — `/grafico`, `/desativar` — usa
            // `nomeNoServico`; tudo que a pessoa LÊ usa `name`. Mandar o
            // nome sem prefixo ao serviço leva 422 `setup_desconhecido`.
            const chave = s.nomeNoServico || s.name;
            const aberto = grafico.setup === chave;
            return (
              <div key={chave} style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px 14px", background: T.bgPanel }}>
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

                {/* Fase 27 (27-05): só ABRIR custa (1 chamada); fechar é
                    local. O rótulo de custo acompanha a ação que cobra e
                    some quando o botão vira "Fechar gráfico" — declarar
                    custo numa ação de graça mentiria na outra direção.

                    O custo entra TAMBÉM no `aria-label`: ele SUBSTITUI o
                    texto do botão para quem usa leitor de tela, então um
                    custo que vivesse só no <span> seria invisível
                    justamente para quem não pode conferir na tela. */}
                <button
                  onClick={() => (aberto ? fecharGrafico() : abrirGrafico(chave))}
                  aria-pressed={aberto}
                  aria-label={(aberto ? "Fechar" : "Ver") + " disparos do setup " + s.name
                    + (aberto ? "" : ". " + (cp.opcoesCustoChamadas || ((n) => String(n)))(custos.grafico))}
                  style={{ marginTop: "10px", width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.borderSubtle}`, background: "transparent", color: T.textSecondary, fontWeight: 700, fontSize: "13px" }}
                >
                  <span style={{ display: "block" }}>
                    {aberto ? "Fechar gráfico" : (cp.opcoesGraficoTitulo || "Disparos do setup")}
                  </span>
                  {aberto ? null : (
                    <span style={CUSTO_NO_BOTAO}>
                      {(cp.opcoesCustoChamadas || ((n) => String(n)))(custos.grafico)}
                    </span>
                  )}
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

                {/* Desativar é ESCRITA: mesma permissão da seção de
                    criação, e em dois toques (ver `BotaoDesativar`). O
                    resultado aparece logo abaixo, na seção de criação —
                    as duas ações compartilham o mesmo trio de estado
                    porque são a mesma conversa com o serviço. */}
                {podeCriarSetup ? (
                  <BotaoDesativar
                    nome={chave}
                    nomeVisivel={s.name}
                    onDesativar={desativarSetup}
                    ocupado={setupNovo.carregando}
                    custos={custos}
                    cp={cp}
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      )}

      {/* ======================================== CRIAR SETUP (F5) --
          Depois da lista: criar vem depois de ver o que já existe —
          com a lista acima, a pessoa não grava um segundo vigia para a
          condição que já vigia. A permissão só ESCONDE; quem recusa é o
          backend (ADR-013). */}
      {podeCriarSetup ? (
        <>
          <Kicker>{cp.opcoesCriarTitulo || "CRIAR UM SETUP"}</Kicker>
          {/* Fase 27 (27-05): a tabela de custo chega por PROP, como tudo
              o mais que este componente recebe. Importá-la seria uma
              segunda porta de acoplamento de graça — e `CriarSetup` é
              deliberadamente um componente sem fonte de dado própria. */}
          <CriarSetup
            ticker={ticker}
            estado={setupNovo}
            onCompilar={compilarSetup}
            onConfirmar={confirmarSetup}
            custos={custos}
            cp={cp}
          />
        </>
      ) : null}
    </>
  );
}
