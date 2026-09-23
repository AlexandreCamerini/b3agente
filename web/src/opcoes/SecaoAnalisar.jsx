/**
 * SecaoAnalisar.jsx — Fase 33 (33-05), extração de OpcoesScreen.jsx.
 *
 * Job 3 do PROJECT.md ("analisar um ticker manualmente") — hoje inline em
 * OpcoesScreen.jsx ("LEITURA DO ATIVO" + "O QUE DÁ PARA MONTAR"). Comportamento
 * idêntico, zero funcionalidade nova (D-03 do 33-CONTEXT.md). Recebe TUDO por
 * prop; não chama `useOpcoesMcp`/`store.*` diretamente — só o orquestrador
 * (OpcoesScreen) chama o hook (padrão Emenda 3 do ADR-027, já replicado por
 * SecaoVigias.jsx/SecaoDescobrir.jsx/SecaoSetups.jsx/SecaoComparar.jsx nas
 * Fases 33-01/02/03/04). Último dos 5 jobs a sair — o mais entrelaçado com
 * `SubAbaOperar`, por causa do fold-in D-04a (ver nota no próprio
 * `SubAbaOperar`, em OpcoesScreen.jsx).
 *
 * `ticker`/`tese`/`vencimento`/`lote` chegam por prop com seus setters —
 * proibido `useState` para qualquer um deles (Pitfall 6 do 33-RESEARCH.md;
 * varredura de diretório em test_opcoes_vigias_ui.mjs trava isso para os 5
 * `Secao*.jsx` da fase). `painel` (`"" | "cadeia" | "operaveis"`) é o ÚNICO
 * estado local: é visual e exclusivo deste job (ARCHITECTURE.md, "Estado
 * local que atravessa jobs").
 *
 * Nada é recalculado: `behavior`, `razaoGanhoPerda`, breakevens e valores em
 * reais chegam prontos do backend. `loteNum` (a forma numérica que
 * `montarProposta` exige) é derivado AQUI a partir da string crua de `lote` —
 * mesmo um-liner que `SecaoComparar.jsx` já usa para `loteNum`/`alvoNum`/
 * `stopNum` (Option B, 33-04-SUMMARY.md), formatação de UMA linha, não a
 * conta de negócio que esta extração proíbe recalcular.
 *
 * NOTA 2026-09-23 (quick 260923-ndy, Task 2): "zero funcionalidade nova
 * (D-03)" acima descreve a extração da Fase 33 — histórico, não se
 * reescreve. Esta quick ACRESCENTA funcionalidade nova e deliberada: o
 * bloco `<ExecutarProposta>` logo depois de `<Pernas>`, fechando o buraco
 * de fluxo achado ao vivo pelo Alex (a estrutura montada em Analisar não
 * tinha caminho de execução). Recebe `operador`/`onExecutarProposta` por
 * prop — mesmo padrão de "tudo por prop" do resto deste arquivo.
 *
 * `Linha`/`RazaoGanhoPerda`/`ErroDoMcp`/`Kicker`/`Aviso` vêm de `uiOpcoes.jsx`
 * (job 3 e job 4/`SecaoComparar.jsx` usam a MESMA implementação). `Pernas`,
 * `TabelaDeOpcoes` e `LacunasDaLeitura` migraram para DENTRO deste arquivo —
 * único consumidor de cada uma depois desta extração (nenhum outro lugar de
 * `web/src/opcoes/` os chama).
 */
import { useState, useEffect } from "react";
import { Kicker, Aviso, ErroDoMcp, Linha, RazaoGanhoPerda } from "./uiOpcoes.jsx";
import PayoffChart from "./PayoffChart.jsx";
import ExplicacaoPayoff from "./ExplicacaoPayoff.jsx";
import ExecutarProposta from "./ExecutarProposta.jsx";

// Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` —
// espelho declarado, mesmo padrão dos irmãos desta pasta. Zero import do
// núcleo do app (seria ciclo, ADR-027 Decisão 3).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
// Fase 35 (35-02, D-03): onAccent é o token calibrado para texto SOBRE
// preenchimento de accent — token fora deste array vira `undefined` calado.
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "accent", "accentTint10", "onAccent"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const pct = (v, casas = 2) => (ehNum(v) ? fmt(v, casas) + "%" : "—");
// `hv21`/`hv63` chegam como FRAÇÃO (0,31 = 31%). A conversão para % é
// formatação da mesma grandeza, não conta nova — mesmo espelho de
// OpcoesScreen.jsx antes desta extração.
const fracPct = (v) => (ehNum(v) ? fmt(v * 100, 1) + "%" : "—");
const txt = (v) => (typeof v === "string" && v ? v : "—");
// `range_63_sessions` chega SEMPRE como dicionário — com os dois extremos
// nulos quando a janela de 63 pregões não fechou. Sem esta checagem o valor
// vira "— – —", travessão travestido de faixa (24-11). Ausência é UM
// travessão, e o porquê dela aparece no rodapé do bloco.
const faixa = (v) => ((v && (ehNum(v.lowest) || ehNum(v.highest)))
  ? fmt(v.lowest) + " – " + fmt(v.highest) : "—");
const num = (v) => {
  const n = Number(v);
  return isFinite(n) ? n : null;
};

const CAIXA = {
  border: `1px solid ${T.borderSubtle}`, borderRadius: "12px",
  padding: "12px 14px", background: T.bgPanel,
};
const CAMPO = {
  minHeight: "44px", width: "100%", boxSizing: "border-box", padding: "8px 10px",
  borderRadius: "10px", border: `1px solid ${T.borderSubtle}`,
  background: T.bgBase, color: T.textPrimary, fontSize: "14px",
};
const ROTULO = { display: "block", fontSize: "12.5px", color: T.textSecondary, margin: "12px 0 4px" };
const AJUDA = { fontSize: "11px", color: T.textMuted, marginTop: "4px", lineHeight: 1.45 };
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
// Botão desabilitado FICA VISÍVEL, em vez de sumir — mesma regra dos irmãos
// desta pasta.
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);
const CUSTO_NO_BOTAO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.textMuted, marginTop: "3px",
};

// Fase 35 (35-02, D-03): MESMA geometria do BOTAO acima — só troca
// border/background/color para o preenchimento sólido de accent. color é
// T.onAccent, nunca #fff literal (reprova AA em Dark·Estudo 2,90:1 e
// Dark·Operador 2,10:1, medido em 35-UI-SPEC.md). Aplica-se a exatamente
// 3 botões do app (D-04): este é o de "Montar estrutura".
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: T.onAccent,
  fontWeight: 700, fontSize: "13px",
};
// D-05: 0,55 (não o 0,45 do neutro acima) — um preenchido a 0,45 ainda lê
// como vívido/clicável sobre fundo escuro. Precedente em produção:
// CuradoriaEstruturas.jsx:268. A regra de nunca sumir vale igual — só
// opacity/cursor mudam, nunca display: none.
const desabilitadoPrimario = (cond) => (cond ? { opacity: 0.55, cursor: "not-allowed" } : null);
const CUSTO_NO_BOTAO_PRIMARIO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.onAccent, marginTop: "3px",
};
// D-06: T.textMuted, NUNCA T.positive/T.negative — esse par é reservado a
// direção financeira (PropostaLastreada.jsx:183); reusá-lo para "sucesso de
// UI" colidiria com "alta"/"baixa" no mesmo campo visual.
const MARCA_RESULTADO = {
  display: "flex", alignItems: "center", gap: "5px",
  fontSize: "11px", color: T.textMuted, marginTop: "6px",
};

// Rolagem horizontal no CONTAINER da tabela, nunca no `body` — mesmo espelho
// de OpcoesScreen.jsx antes desta extração.
const ROLAGEM = { overflowX: "auto", WebkitOverflowScrolling: "touch", margin: "8px 0" };
const TABELA = { borderCollapse: "collapse", fontSize: "12px", minWidth: "460px", width: "100%" };
const TH = { textAlign: "left", padding: "6px 8px", color: T.textMuted, fontWeight: 700, borderBottom: `1px solid ${T.borderSubtle}`, whiteSpace: "nowrap" };
const TD = { padding: "6px 8px", color: T.textSecondary, borderBottom: `1px solid ${T.borderFaint}`, whiteSpace: "nowrap", fontVariantNumeric: "tabular-nums" };
const LADO = { buy: "compra", sell: "venda" };

// aba-opcoes 24-11 (achado ao vivo 2026-09-11): a LEITURA DO ATIVO mostrava
// travessão em cinco campos sem dizer por quê. UM mapa só de rótulo↔campo,
// para que a explicação e a tabela falem o MESMO vocabulário.
const ROTULO_LEITURA = {
  trend: "Tendência",
  rsi14: "RSI 14",
  hv21: "HV 21",
  hv63: "HV 63",
  sma63: "Média de 63",
  distance_from_sma21_pct: "Distância da média 21",
  distance_from_sma63_pct: "Distância da média 63",
  range_63_sessions: "Faixa de 63 pregões",
  change_21_sessions_pct: "Variação em 21 pregões",
};

// Os motivos vão AGRUPADOS no rodapé do bloco. O motivo é do backend e vai
// VERBATIM: aqui só se juntam os rótulos. Sem `lacunas`, nada é renderizado —
// estado normal é silêncio.
function LacunasDaLeitura({ lacunas, cp }) {
  const itens = (Array.isArray(lacunas) ? lacunas : []).filter(
    (x) => x && x.motivo && Array.isArray(x.campos) && x.campos.length);
  if (!itens.length) return null;
  return (
    <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "4px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
      {itens.map((x, i) => (
        <div key={i} style={{ marginTop: i ? "3px" : 0 }}>
          {cp.opcoesLacuna
            ? cp.opcoesLacuna(x.campos.map((c) => ROTULO_LEITURA[c] || c), x.motivo)
            : x.motivo}
        </div>
      ))}
    </div>
  );
}

// Pernas da estrutura. `side` e os números vêm do serviço; nada é recalculado
// — inclusive a quantidade, que é do contrato e não do lote.
function Pernas({ pernas, cp }) {
  const lista = Array.isArray(pernas) ? pernas.filter((p) => p && typeof p === "object") : [];
  if (!lista.length) return null;
  return (
    <>
      <div style={ROLAGEM}>
        <table style={TABELA}>
          <thead>
            <tr>
              <th style={TH}>Contrato</th><th style={TH}>Lado</th><th style={TH}>Qtd.</th>
              <th style={TH}>Strike</th><th style={TH}>Prêmio</th><th style={TH}>Delta</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((p, i) => (
              <tr key={(p.contract || "perna") + "-" + i}>
                <td style={{ ...TD, color: T.textPrimary, fontWeight: 700 }}>{txt(p.contract)}</td>
                <td style={TD}>{LADO[p.side] || txt(p.side)}</td>
                <td style={TD}>{ehNum(p.quantity) ? p.quantity : "—"}</td>
                <td style={TD}>{fmt(p.strike)}</td>
                <td style={TD}>{fmt(p.premium)}</td>
                <td style={TD}>{fmt(p.delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={AJUDA}>{(cp && cp.opcoesDeltaAjuda) || ""}</div>
    </>
  );
}

// Cadeia e operáveis: MESMA tabela, porque as duas rotas devolvem a mesma
// linha do serviço (chaves em PT-BR, ao contrário das pernas). `situacao_sigma`
// é coluna de primeira classe: é ela que explica por que delta e volatilidade
// vêm vazios em ~10% dos contratos — sem ela, o travessão vira "o app não
// sabe" quando o serviço declarou o motivo.
function TabelaDeOpcoes({ linhas }) {
  const lista = Array.isArray(linhas) ? linhas.filter((o) => o && typeof o === "object") : [];
  if (!lista.length) return null;
  return (
    <div style={ROLAGEM}>
      <table style={TABELA}>
        <thead>
          <tr>
            <th style={TH}>Contrato</th><th style={TH}>Tipo</th><th style={TH}>Strike</th>
            <th style={TH}>Prêmio</th><th style={TH}>Delta</th><th style={TH}>Vol. impl.</th>
            <th style={TH}>Negócios</th><th style={TH}>Vencimento</th><th style={TH}>Obs.</th>
          </tr>
        </thead>
        <tbody>
          {lista.map((o, i) => (
            <tr key={(o.contrato || "opcao") + "-" + i}>
              <td style={{ ...TD, color: T.textPrimary, fontWeight: 700 }}>{txt(o.contrato)}</td>
              <td style={TD}>{txt(o.tipo)}</td>
              <td style={TD}>{fmt(o.strike)}</td>
              <td style={TD}>{fmt(o.premio)}</td>
              <td style={TD}>{fmt(o.delta)}</td>
              <td style={TD}>{fracPct(o.volatilidade_implicita)}</td>
              <td style={TD}>{ehNum(o.total_negocios) ? o.total_negocios : "—"}</td>
              <td style={TD}>{txt(o.dt_vencimento)}</td>
              <td style={TD}>{txt(o.situacao_sigma)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SecaoAnalisar({
  ticker, temLeitura, semCandles, behavior, lacunas, pregao, expirations,
  tese, setTese, temTese, vencimento, setVencimento, vencimentos,
  lote, setLote, loteOk,
  proposta, montarProposta,
  cadeia, operaveis, abrirCadeia, abrirOperaveis,
  custos, cp, palette,
  operador, onExecutarProposta,
}) {
  // "" | "cadeia" | "operaveis" — visual, exclusivo deste job (Pitfall 6).
  const [painel, setPainel] = useState("");

  // Trocar de ativo fecha o painel de cadeia/operáveis — mesma garantia que
  // `escolherTicker` (OpcoesScreen.jsx) já dava antes desta extração
  // (`setPainel("")` no mesmo handler que trocava o ticker). Este componente
  // não desmonta ao trocar de ticker (fica na mesma posição da árvore), então
  // o reset precisa de efeito próprio, chaveado no `ticker` recebido por prop.
  useEffect(() => {
    setPainel("");
  }, [ticker]);

  // Forma numérica que o corpo de `montarProposta` exige — mesmo um-liner de
  // `SecaoComparar.jsx` (loteNum/alvoNum/stopNum, Option B). Formatação de
  // uma linha, não a conta de negócio que esta extração proíbe recalcular.
  const loteNum = ehNum(num(lote)) ? Math.trunc(num(lote)) : null;

  return (
    <>
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
            <Linha rotulo="Faixa de 63 pregões" valor={faixa(behavior.range_63_sessions)} />
            <Linha rotulo="Variação em 21 pregões" valor={pct(behavior.change_21_sessions_pct, 1)} />
          </div>
          <div style={{ fontSize: "11.5px", color: T.textMuted, marginTop: "6px" }}>
            {"Leitura referente ao pregão de " + (behavior.trading_date || pregao || "—") + "."}
          </div>
          {/* 24-11 — o rodapé continua, e diz POR QUE os campos vazios estão
              vazios. A tabela acima segue com travessão: o objetivo é
              explicar a ausência, não preenchê-la. */}
          <LacunasDaLeitura lacunas={lacunas} cp={cp} />
        </>
      ) : semCandles ? (
        <div style={{ marginTop: "14px" }}>
          <Aviso>
            O serviço não tem candles para este ativo — sem leitura de
            comportamento. Os setups abaixo continuam valendo.
          </Aviso>
        </div>
      ) : null}

      {Array.isArray(expirations) && expirations.length > 0 ? (
        <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "10px" }}>
          {"Vencimentos disponíveis: " + expirations.join(" · ")}
        </div>
      ) : null}

      {/* ============================================ ANALISAR (F3) --
          Depois da leitura: a ordem da tela é a ordem do raciocínio — leio o
          ativo, vejo o que dá para montar. Sem leitura não há de onde a tese
          sair, então a seção inteira depende de `temLeitura`. */}
      {temLeitura ? (
        <>
          <Kicker>{cp.opcoesAnalisarTitulo || "O QUE DÁ PARA MONTAR"}</Kicker>
          <div style={CAIXA}>
            {/* Nenhuma tese vem pré-selecionada: o serviço não escolhe
                direção (é 422 `tese_ausente` sem ela) e a tela não pode
                escolher no lugar de quem opera. */}
            <div id="opcoes-tese-rotulo" style={{ ...ROTULO, margin: "0 0 6px" }}>
              {cp.opcoesTeseRotulo || "Qual é a sua tese para este ativo?"}
            </div>
            <div role="group" aria-labelledby="opcoes-tese-rotulo" style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {[["bullish", cp.opcoesTeseAlta || "Alta"],
                ["bearish", cp.opcoesTeseBaixa || "Baixa"],
                ["neutral", cp.opcoesTeseNeutra || "Neutra"]].map(([valor, rotulo]) => (
                  <button
                    key={valor}
                    onClick={() => setTese(valor === tese ? "" : valor)}
                    aria-pressed={valor === tese}
                    style={{ ...BOTAO, flex: "1 1 90px", ...(valor === tese ? { borderColor: T.accent, background: T.accentTint10, color: T.accent } : null) }}
                  >
                    {rotulo}
                  </button>
                ))}
            </div>

            {/* "o serviço escolhe" é o default HONESTO: `propose_option_setups`
                sem `expiration` decide pelo critério dele, e fingir que fomos
                nós que escolhemos o primeiro da lista seria a tela assumindo
                uma decisão que não tomou. */}
            <label htmlFor="opcoes-venc" style={ROTULO}>Vencimento</label>
            <select id="opcoes-venc" value={vencimento} onChange={(ev) => setVencimento(ev.target.value)} style={CAMPO}>
              <option value="">o serviço escolhe</option>
              {vencimentos.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>

            <label htmlFor="opcoes-lote" style={ROTULO}>{cp.opcoesLoteRotulo || "Lote (ações)"}</label>
            <input
              id="opcoes-lote" type="number" step="100" min="100" inputMode="numeric"
              value={lote} onChange={(ev) => setLote(ev.target.value)}
              aria-describedby="opcoes-lote-ajuda" style={CAMPO}
            />
            <div id="opcoes-lote-ajuda" style={AJUDA}>{cp.opcoesLoteAjuda || ""}</div>

            {/* Fase 27 (27-05): o custo DENTRO do controle, na segunda linha
                do próprio botão — mesmo padrão dos demais controles da aba.
                Uma forma só de dizer custo (`opcoesCustoChamadas`) em toda a
                aba: duas divergiriam na primeira manutenção feita só numa
                delas. */}
            <button
              onClick={() => montarProposta({ direction: tese, expiration: vencimento || undefined, lote: loteNum })}
              disabled={!temTese || !loteOk}
              style={{ ...BOTAO_PRIMARIO, width: "100%", marginTop: "12px", ...desabilitadoPrimario(!temTese || !loteOk) }}
            >
              <span style={{ display: "block" }}>{cp.opcoesMontarEstrutura || "Montar estrutura"}</span>
              <span style={CUSTO_NO_BOTAO_PRIMARIO}>
                {(cp.opcoesCustoChamadas || ((n) => String(n)))(custos.proposta)}
              </span>
            </button>

            {/* Fase 35 (35-02, D-06): marca neutra de resultado — o botão
                acima NÃO some nem desabilita depois do clique (trocar
                tese/lote e montar de novo é uso legítimo, comparar
                cenários). Gate é resultado COM CONTEÚDO — nunca carregando,
                nunca erro, nunca vazio-com-motivo: afirmar "montada" sobre
                uma resposta sem estrutura seria afirmar resultado que não
                existe (princípio 4 do CLAUDE.md). */}
            {proposta.dados && (proposta.dados.estruturas || []).length ? (
              <div style={MARCA_RESULTADO}>
                <span>✓</span>
                <span>{cp.opcoesEstruturaMontada || "Estrutura montada"}</span>
              </div>
            ) : null}

            {/* carregando → erro → vazio com motivo → dados */}
            <div style={{ marginTop: "10px" }}>
              {proposta.carregando ? (
                <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
              ) : proposta.erro ? (
                <ErroDoMcp erro={proposta.erro} cp={cp} />
              ) : proposta.dados && !(proposta.dados.estruturas || []).length ? (
                <Aviso>
                  {/* Motivo do serviço, VERBATIM. Sem motivo nenhum, a tela
                      diz que não houve motivo — não preenche com um palpite
                      sobre o porquê. */}
                  {proposta.dados.motivo || proposta.dados.nota
                    || "O serviço não montou estrutura para esta tese e não informou o motivo. Nada foi estimado no lugar."}
                </Aviso>
              ) : proposta.dados ? (
                <>
                  <PayoffChart
                    estrutura={proposta.dados.estruturas[0]}
                    emReais={proposta.dados.emReais}
                    cp={cp}
                    palette={palette}
                    dominio={proposta.dados.dominio}
                    segmentos={proposta.dados.segmentos}
                    valorHoje={proposta.dados.valorHoje}
                  />
                  <RazaoGanhoPerda razao={proposta.dados.razaoGanhoPerda} cp={cp} />
                  <ExplicacaoPayoff
                    segmentos={proposta.dados.segmentos}
                    spot={proposta.dados.dominio && proposta.dados.dominio.spot}
                    razao={proposta.dados.razaoGanhoPerda}
                    cp={cp}
                  />
                  <Pernas pernas={proposta.dados.estruturas[0].legs} cp={cp} />
                  {/* Quick 260923-ndy (Task 2): bloco de execução da
                      estrutura que o usuário acabou de montar — gate de
                      Estudo, motivo/erro verbatim e consentimento de
                      liquidez ficam DENTRO do componente. */}
                  <ExecutarProposta
                    dados={proposta.dados}
                    operador={operador}
                    onExecutar={onExecutarProposta}
                    cp={cp}
                  />
                </>
              ) : null}
            </div>

            {/* Duas consultas secundárias, cada uma custando 1 chamada.
                Reabrir o painel refaz o pedido — e o cache L1 do serviço
                (15 min) devolve sem tocar a rede, sem consumir cap. */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "14px" }}>
              <button
                onClick={() => { const abrir = painel !== "cadeia"; setPainel(abrir ? "cadeia" : ""); if (abrir) abrirCadeia({ expiration: vencimento || undefined }); }}
                aria-pressed={painel === "cadeia"}
                style={{ ...BOTAO, flex: "1 1 150px" }}
              >
                <span style={{ display: "block" }}>{cp.opcoesVerCadeia || "Ver a cadeia"}</span>
                <span style={CUSTO_NO_BOTAO}>
                  {(cp.opcoesCustoChamadas || ((n) => String(n)))(custos.cadeia)}
                </span>
              </button>
              <button
                onClick={() => { const abrir = painel !== "operaveis"; setPainel(abrir ? "operaveis" : ""); if (abrir) abrirOperaveis({ expiration: vencimento || undefined }); }}
                aria-pressed={painel === "operaveis"}
                style={{ ...BOTAO, flex: "1 1 150px" }}
              >
                <span style={{ display: "block" }}>{cp.opcoesVerOperaveis || "Ver as operáveis"}</span>
                <span style={CUSTO_NO_BOTAO}>
                  {(cp.opcoesCustoChamadas || ((n) => String(n)))(custos.operaveis)}
                </span>
              </button>
            </div>

            {painel === "cadeia" ? (
              <div style={{ marginTop: "10px" }}>
                {cadeia.carregando ? (
                  <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                ) : cadeia.erro ? (
                  <ErroDoMcp erro={cadeia.erro} cp={cp} />
                ) : cadeia.dados && !(cadeia.dados.opcoes || []).length ? (
                  <Aviso>A cadeia deste ativo voltou sem contrato para os filtros pedidos. Nada foi estimado no lugar.</Aviso>
                ) : cadeia.dados ? (
                  <>
                    <div style={{ fontSize: "11.5px", color: T.textMuted }}>
                      {"Contratos: " + (ehNum(cadeia.dados.retornados) ? cadeia.dados.retornados : "—")
                        + " de " + (ehNum(cadeia.dados.encontrados) ? cadeia.dados.encontrados : "—")}
                    </div>
                    {cadeia.dados.truncado ? (
                      <div style={{ marginTop: "8px" }}>
                        <Aviso>{(cp.opcoesCadeiaTruncada || ((t) => t))(cadeia.dados.truncado)}</Aviso>
                      </div>
                    ) : null}
                    <TabelaDeOpcoes linhas={cadeia.dados.opcoes} />
                    <div style={AJUDA}>{cp.opcoesDeltaAjuda || ""}</div>
                  </>
                ) : null}
              </div>
            ) : null}

            {painel === "operaveis" ? (
              <div style={{ marginTop: "10px" }}>
                {operaveis.carregando ? (
                  <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
                ) : operaveis.erro ? (
                  <ErroDoMcp erro={operaveis.erro} cp={cp} />
                ) : operaveis.dados && !(operaveis.dados.opcoes || []).length ? (
                  <Aviso>
                    {/* Peneira vazia NÃO é "não há opções": é "nenhuma passou
                        no critério". Por isso o critério aparece junto — a
                        pessoa precisa saber o que sumiu com os strikes dela. */}
                    {(cp.opcoesCriterioOperaveis || (() => ""))(operaveis.dados.criterioAplicado)}
                    {"\n\nNenhum contrato passou nessa peneira neste ativo."}
                  </Aviso>
                ) : operaveis.dados ? (
                  <>
                    <div style={{ fontSize: "11.5px", color: T.textSecondary, lineHeight: 1.5 }}>
                      {(cp.opcoesCriterioOperaveis || (() => ""))(operaveis.dados.criterioAplicado)}
                    </div>
                    {operaveis.dados.criterio ? (
                      <div style={{ ...AJUDA, whiteSpace: "pre-wrap" }}>
                        {/* Texto do serviço, verbatim (vem em inglês) —
                            reescrever seria a tela falando pelo serviço. */}
                        {"Como o serviço descreveu a peneira: " + operaveis.dados.criterio}
                      </div>
                    ) : null}
                    <TabelaDeOpcoes linhas={operaveis.dados.opcoes} />
                    <div style={AJUDA}>
                      {ehNum(operaveis.dados.excluidos) ? "Descartados pela peneira: " + operaveis.dados.excluidos + ". " : ""}
                      {cp.opcoesDeltaAjuda || ""}
                    </div>
                    {operaveis.dados.nota ? (
                      <div style={{ ...AJUDA, whiteSpace: "pre-wrap" }}>{operaveis.dados.nota}</div>
                    ) : null}
                  </>
                ) : null}
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </>
  );
}
