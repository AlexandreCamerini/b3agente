/**
 * SecaoComparar.jsx — Fase 33 (33-04), extração de OpcoesScreen.jsx.
 *
 * Job 4 do PROJECT.md ("comparar os vencimentos") — hoje inline em
 * OpcoesScreen.jsx ("COMPARAR OS VENCIMENTOS"). Comportamento idêntico, zero
 * funcionalidade nova (D-03 do 33-CONTEXT.md). Recebe TUDO por prop; não
 * chama `useOpcoesMcp`/`store.*` diretamente — só o orquestrador
 * (OpcoesScreen) chama o hook (padrão Emenda 3 do ADR-027, já replicado por
 * SecaoVigias.jsx/SecaoDescobrir.jsx/SecaoSetups.jsx nas Fases 33-01/02/03).
 *
 * O ponto mais sensível deste bloco (33-04-PLAN.md): a declaração de custo
 * (`cp.opcoesCustoChamadas(chamadasPrevistas)`) aparece no fonte ANTES do
 * disparo de `verPossibilidades(...)` — descobrir que a consulta custou até
 * 13 chamadas depois de gastá-las não é aviso, é recibo. `chamadasPrevistas`
 * chega PRONTA por prop: `N_MAX_VENCIMENTOS`/`Math.min(...)`/`2 * N + 1`
 * continuam SÓ no orquestrador (uma conta só, cruzada com o backend por
 * `test_opcoes_custo_declarado.mjs`) — duas contas do mesmo custo divergem na
 * primeira manutenção feita só numa delas. `vencimentos.length` e
 * `consultados.length` substituem o `N` cru do orquestrador nesta seção — são
 * a MESMA grandeza (`consultados = vencimentos.slice(0, N)` lá), sem abrir
 * uma prop só para carregar um número que já está implícito no tamanho do
 * array.
 *
 * `tese`/`lote` são o MESMO formulário do job 3 (Analisar) — chegam
 * somente-leitura, nunca redeclarados aqui (Pitfall 6 do 33-RESEARCH.md).
 * `alvo`/`stop` são exclusivos deste job, mas os setters também vêm do
 * orquestrador para não resetarem entre re-renders da mesma sessão de
 * navegação. `loteNum`/`alvoNum`/`stopNum` (a forma numérica que o corpo da
 * chamada exige) são derivados AQUI a partir das strings cruas — o MESMO
 * um-liner de `OpcoesScreen.jsx` (formatação de UMA linha, espelho declarado
 * local, mesma regra já registrada em `uiOpcoes.jsx`), não a conta de custo
 * que esta extração proíbe recalcular.
 *
 * `RazaoGanhoPerda`/`Linha` migraram para `uiOpcoes.jsx` nesta extração —
 * job 3 (que continua em `OpcoesScreen.jsx` até o 33-05) e este job usam a
 * MESMA implementação, evitando duas cópias que divergiriam na primeira
 * correção feita só numa delas. `Cenarios` só tinha este consumidor, então
 * entrou direto aqui, sem virar primitivo compartilhado.
 */
import { Kicker, Aviso, ErroDoMcp, Linha, RazaoGanhoPerda } from "./uiOpcoes.jsx";
import PayoffChart from "./PayoffChart.jsx";

// Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` —
// espelho declarado, mesmo padrão dos irmãos desta pasta. Zero import do
// núcleo do app (seria ciclo, ADR-027 Decisão 3).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
// Fase 35 (35-02, D-03): este arquivo não tinha accent nem onAccent — sem
// os dois o botão preenchido ficaria sem fundo E sem cor de texto.
const TOKENS = ["textSecondary", "textMuted", "borderSubtle", "bgPanel", "bgBase", "textPrimary", "accent", "onAccent"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const txt = (v) => (typeof v === "string" && v ? v : "—");
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

// Fase 35 (35-02, D-03): MESMA geometria do BOTAO acima — só troca
// border/background/color para o preenchimento sólido de accent. color é
// T.onAccent, nunca #fff literal. Aplica-se a exatamente 3 botões do app
// (D-04): este é o de "Ver possibilidades". NÃO declarar
// CUSTO_NO_BOTAO_PRIMARIO aqui: o custo deste fluxo é linha própria ANTES
// do botão (acima), não subtexto dentro dele.
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: T.onAccent,
  fontWeight: 700, fontSize: "13px",
};
// D-05: 0,55 (não o 0,45 do neutro acima) — precedente CuradoriaEstruturas.jsx:268.
const desabilitadoPrimario = (cond) => (cond ? { opacity: 0.55, cursor: "not-allowed" } : null);
// D-06: T.textMuted, NUNCA T.positive/T.negative — reservados a direção
// financeira (PropostaLastreada.jsx:183).
const MARCA_RESULTADO = {
  display: "flex", alignItems: "center", gap: "5px",
  fontSize: "11px", color: T.textMuted, marginTop: "6px",
};

// Cenários em REAIS, já multiplicados pelo backend. O preço do objeto viaja
// verbatim (é preço, não dinheiro da posição) e o resultado ausente é
// travessão — 0 aqui seria "empata neste cenário", que é outra afirmação.
// Único consumidor (job 4): não virou primitivo de uiOpcoes.jsx.
function Cenarios({ emReais, cp }) {
  const lista = (emReais && Array.isArray(emReais.cenarios) ? emReais.cenarios : [])
    .filter((s) => s && typeof s === "object");
  if (!lista.length) return null;
  return (
    <div style={{ marginTop: "8px" }}>
      <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".06em", color: T.textMuted, marginBottom: "4px" }}>
        {((cp && cp.opcoesCenariosTitulo) || "Cenários").toUpperCase()}
      </div>
      {lista.map((s, i) => (
        <Linha
          key={(s.name || "cenario") + "-" + i}
          rotulo={txt(s.name) + " · ativo a " + fmt(s.underlying)}
          valor={ehNum(s.resultado) ? "R$ " + fmt(s.resultado) : "—"}
        />
      ))}
    </div>
  );
}

export default function SecaoComparar({
  ticker, tese, temTese, lote, loteOk, alvo, setAlvo, stop, setStop,
  vencimentos, consultados, chamadasPrevistas, possibilidades, verPossibilidades,
  custos, cp, palette,
}) {
  // Forma numérica que o corpo de `verPossibilidades` exige — mesmo um-liner
  // de `OpcoesScreen.jsx` (o job 3 tem a própria cópia de `loteNum`, para
  // `montarProposta`). É formatação, não a conta de custo que esta extração
  // proíbe recalcular (`N_MAX_VENCIMENTOS`/`2 * N + 1` nunca aparecem aqui).
  const loteNum = ehNum(num(lote)) ? Math.trunc(num(lote)) : null;
  const alvoNum = ehNum(num(alvo)) && num(alvo) > 0 ? num(alvo) : undefined;
  const stopNum = ehNum(num(stop)) && num(stop) > 0 ? num(stop) : undefined;

  return (
    <>
      {/* ==================================== POSSIBILIDADES (F3) -- */}
      <Kicker>{cp.opcoesPossibilidadesTitulo || "COMPARAR OS VENCIMENTOS"}</Kicker>
      <div style={CAIXA}>
        {consultados.length === 0 ? (
          <Aviso>{cp.opcoesSemVencimento || "Nenhum vencimento aberto na leitura deste ativo."}</Aviso>
        ) : (
          <>
            {/* O custo ANTES do clique. `chamadasPrevistas` (2 * N + 1) sai
                pronto do orquestrador, derivado dos vencimentos que a leitura
                já trouxe, sem consultar nada: descobrir o preço depois de
                pagar não é aviso, é recibo. */}
            <div style={{ fontSize: "12.5px", color: T.textSecondary, lineHeight: 1.5 }}>
              {(cp.opcoesCustoChamadas || ((n) => String(n)))(chamadasPrevistas)}
            </div>
            {/* Fase 27 (27-02): a COMPOSIÇÃO do custo saiu de
                `opcoesCustoChamadas` (que agora também serve ao botão dos
                vigias, cuja conta é outra) e passou a ter chave própria. O
                número continua vindo da mesma frase de sempre, logo acima. */}
            <div style={{ ...AJUDA, marginTop: "6px" }}>
              {cp.opcoesCustoVencimentos || ""}
            </div>
            <div style={{ ...AJUDA, marginTop: "6px" }}>
              {"Vencimentos consultados: " + consultados.join(" · ")}
              {vencimentos.length > consultados.length
                ? " (os " + consultados.length + " primeiros de " + vencimentos.length + ")"
                : ""}
            </div>

            <label htmlFor="opcoes-alvo" style={ROTULO}>{cp.opcoesAlvoRotulo || "Alvo (opcional)"}</label>
            <input id="opcoes-alvo" type="number" step="0.01" min="0" inputMode="decimal"
              value={alvo} onChange={(ev) => setAlvo(ev.target.value)} style={CAMPO} />
            <label htmlFor="opcoes-stop" style={ROTULO}>{cp.opcoesStopRotulo || "Stop (opcional)"}</label>
            <input id="opcoes-stop" type="number" step="0.01" min="0" inputMode="decimal"
              value={stop} onChange={(ev) => setStop(ev.target.value)} style={CAMPO} />

            <button
              onClick={() => verPossibilidades({
                direction: tese, lote: loteNum, alvo: alvoNum, stop: stopNum,
                expirations: consultados,
              })}
              disabled={!temTese || !loteOk}
              style={{ ...BOTAO_PRIMARIO, width: "100%", marginTop: "12px", ...desabilitadoPrimario(!temTese || !loteOk) }}
            >
              {cp.opcoesVerPossibilidades || "Ver possibilidades"}
            </button>

            {/* Fase 35 (35-02, D-06): marca neutra de resultado — o botão
                acima NÃO some nem desabilita depois do clique (trocar
                tese/alvo/stop e comparar de novo é uso legítimo). Gate é
                resultado COM CONTEÚDO — nunca carregando/erro/vazio. */}
            {possibilidades.dados && (possibilidades.dados.possibilidades || []).length ? (
              <div style={MARCA_RESULTADO}>
                <span>✓</span>
                <span>{cp.opcoesPossibilidadesVistas || "Possibilidades carregadas"}</span>
              </div>
            ) : null}
          </>
        )}

        <div style={{ marginTop: "10px" }}>
          {possibilidades.carregando ? (
            <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
          ) : possibilidades.erro ? (
            <ErroDoMcp erro={possibilidades.erro} cp={cp} />
          ) : possibilidades.dados && !(possibilidades.dados.possibilidades || []).length ? (
            <Aviso>{possibilidades.dados.motivo || cp.opcoesSemVencimento || ""}</Aviso>
          ) : possibilidades.dados ? (
            <div style={{ display: "grid", gap: "10px" }}>
              {/* Um vencimento que falhou NÃO apaga os outros — é a razão de
                  o backend não abortar o laço, e a lista aqui é uniforme
                  justamente para não precisar testar existência de chave. */}
              {possibilidades.dados.possibilidades.map((item) => (
                <div key={item.vencimento}>
                  {item.erro ? (
                    <Aviso tom="forte">{item.vencimento + ": " + item.erro}</Aviso>
                  ) : !item.estrutura ? (
                    <Aviso>
                      {item.vencimento + ": "
                        + (item.motivo || "o serviço não montou estrutura e não informou o motivo.")}
                    </Aviso>
                  ) : (
                    <>
                      <PayoffChart estrutura={item.estrutura} emReais={item.emReais} cp={cp} palette={palette} />
                      <RazaoGanhoPerda razao={item.razaoGanhoPerda} cp={cp} />
                      <Cenarios emReais={item.emReais} cp={cp} />
                    </>
                  )}
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Ressalva FIXA, não tooltip opcional: ela acompanha todo número de
            cenário que a seção mostra. */}
        <div style={{ ...AJUDA, marginTop: "12px" }}>{cp.opcoesSigmaAjuda || ""}</div>
      </div>
    </>
  );
}
