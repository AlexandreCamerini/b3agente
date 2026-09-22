/**
 * uiOpcoes.jsx — Fase 33 (33-01), extração de OpcoesScreen.jsx.
 *
 * Primitivos de UI compartilhados entre o orquestrador (OpcoesScreen.jsx) e
 * as seções job-to-be-done (`Secao*.jsx`, D-01 do 33-CONTEXT.md) que nascem
 * nesta fase (33-01..33-05). Existe para que `ErroDoMcp` — que ramifica nos
 * quatro códigos de erro do ADR-027 (`mcp_nao_configurado`/`mcp_cota`/
 * `mcp_teto_servico`/`mcp_indisponivel`/`mcp_erro_de_tool`) — tenha UMA
 * implementação só: duas cópias divergiriam na primeira correção feita só
 * numa delas, e o usuário veria mensagens diferentes para o mesmo código de
 * erro dependendo de qual seção o exibiu.
 *
 * Este módulo não importa o núcleo do app (o arquivo raiz do bundle
 * consumidor) nem `OpcoesScreen.jsx` (ADR-027, isolamento de duas vias —
 * Emenda 3, já aplicada por `OportunidadesOpcoes.jsx`/
 * `CuradoriaEstruturas.jsx` na Fase 32).
 *
 * Regra de duplicação aceita neste diretório: token de tema, constante de
 * estilo e formatador de UMA linha podem ser espelho declarado local em cada
 * arquivo de `web/src/opcoes/` (mesmo padrão de `OportunidadesOpcoes.jsx`/
 * `CuradoriaEstruturas.jsx`) — mas qualquer coisa com RAMIFICAÇÃO de lógica
 * (como os `if (erro.code === ...)` abaixo) vive numa fonte só, aqui.
 *
 * Fase 33 (33-04): `Linha`/`RazaoGanhoPerda` entram aqui pela mesma razão que
 * `ErroDoMcp` — job 3 (Analisar, em `OpcoesScreen.jsx`) e job 4 (Comparar, em
 * `SecaoComparar.jsx`) renderizam a MESMA razão ganho/perda; duas cópias
 * divergiriam na primeira correção feita só numa delas.
 */
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "borderSubtle", "negative", "bgPanel", "textSecondary", "textPrimary", "borderFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const AJUDA = { fontSize: "11px", color: T.textMuted, marginTop: "4px", lineHeight: 1.45 };

export function Kicker({ children }) {
  return (
    <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".08em", color: T.textMuted, margin: "18px 0 8px" }}>
      {children}
    </div>
  );
}

export function Aviso({ children, tom }) {
  return (
    <div style={{ border: `1px solid ${tom === "forte" ? T.negative : T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel, color: T.textSecondary, fontSize: "12.5px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

// Fase 33 (33-04): migrou de OpcoesScreen.jsx — linha rótulo↔valor genérica,
// reusada pela LEITURA DO ATIVO (job 3), por `RazaoGanhoPerda` logo abaixo e
// por `Cenarios` (SecaoComparar.jsx, job 4).
export function Linha({ rotulo, valor }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
      <span style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</span>
      <span style={{ fontSize: "12.5px", color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{valor}</span>
    </div>
  );
}

// Fase 37 (37-02, D-05/EXPL-03): fonte ÚNICA de formatação da razão G/P.
// Extraída de dentro de `RazaoGanhoPerda` (era a expressão inline abaixo) —
// a regressão confirmada em produção (razão exibida "1:1,00" vs. texto
// dizendo "1:0,67") era exatamente dois formatadores independentes do mesmo
// número divergindo. `ExplicacaoPayoff.jsx` importa e chama esta mesma
// função — nunca reformata `razao.valor` por conta própria.
export function formatarRazao(razao) {
  if (!razao) return "—";
  return ehNum(razao.valor) ? "1 : " + fmt(razao.valor) : (razao.motivo || "—");
}

// aba-opcoes 24-06 (achado F-01): a razão ganho/perda que o critério 1 do
// ROADMAP enumera. Migrou de OpcoesScreen.jsx nesta fase (33-04) — job 3
// (Analisar) e job 4 (Comparar, SecaoComparar.jsx) renderizam a MESMA razão.
//
// Ela chega PRONTA do backend (`_razao_ganho_perda`), adimensional: aqui não
// há divisão, não há lote e não há fallback numérico. Sem `valor`, o que
// aparece é o MOTIVO — e ele ocupa a linha inteira, com quebra, porque é ele
// que impede a leitura errada e não pode ser cortado em 375 px. Travessão
// mudo seria "o app não calculou"; um número seria pior, porque a pessoa
// compara 2,3 com 1,5 e decide.
export function RazaoGanhoPerda({ razao, cp }) {
  if (!razao) return null;
  const rotulo = cp.opcoesRazaoRotulo || "Razão ganho/perda";
  return (
    <div>
      {ehNum(razao.valor) ? (
        <Linha rotulo={rotulo} valor={formatarRazao(razao)} />
      ) : (
        <div style={{ padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
          <div style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</div>
          <div style={{ fontSize: "12.5px", color: T.textPrimary, marginTop: "3px", whiteSpace: "pre-wrap", lineHeight: 1.45 }}>
            {formatarRazao(razao)}
          </div>
        </div>
      )}
      <div style={AJUDA}>{cp.opcoesRazaoAjuda || ""}</div>
    </div>
  );
}

// ---------------------------------------------------------------- F3 --
// As duas peças que a cascata de estados do serviço MCP repete em toda a
// pasta opcoes/. O guardião lê a ORDEM das primeiras ocorrências no fonte de
// quem consome (carregando → erro → vazio → dados) — declaração de função é
// içada, então a ordem física aqui não afeta a execução de quem importa.

// A mesma cascata de códigos da cadeia de estados principal, para os trios
// sob demanda (vigias, proposta, cadeia, operáveis, possibilidades).
export function ErroDoMcp({ erro, cp }) {
  if (!erro) return null;
  const c = cp || {};
  if (erro.code === "mcp_nao_configurado") {
    return <Aviso>{c.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>;
  }
  if (erro.code === "mcp_cota" || erro.code === "mcp_teto_servico") {
    return (
      <Aviso>
        {(c.opcoesCota || ((r) => "Cota esgotada." + (r ? " Reinicia às " + r + "." : "")))(
          erro.detail && erro.detail.reinicia)}
      </Aviso>
    );
  }
  if (erro.code === "mcp_indisponivel") {
    return <Aviso>{c.opcoesIndisponivel || "Serviço de opções sem resposta agora."}</Aviso>;
  }
  // Inclui `mcp_erro_de_tool` e os 422 de pedido torto: a mensagem já vem
  // pronta e multi-linha do `enrichErrorMessage`, e vai crua (React escapa).
  return (
    <>
      <Aviso tom="forte">{erro.message}</Aviso>
      <RecusaCobrada erro={erro} cp={cp} />
    </>
  );
}

// 24-07 (achado F-04). A recusa da tool passou a DEBITAR uma chamada do cap:
// a viagem aconteceu e o serviço já a cobrou do teto compartilhado. Cobrar
// sem dizer que cobrou é a metade do defeito que a pessoa enxerga — a cota
// dela cai e a tela mostra só "o serviço recusou".
//
// As DUAS condições são necessárias, e nenhuma delas é zelo: os 422 de pedido
// torto (`kind_invalido`, `lote_invalido`, `ticker_ausente`) são recusa ANTES
// da rede e não custam chamada nenhuma. Afirmar cobrança neles seria inventar
// um débito — o mesmo erro do F-04, invertido e agora na tela.
export function RecusaCobrada({ erro, cp }) {
  if (!erro || erro.code !== "mcp_erro_de_tool") return null;
  const d = (erro.detail && typeof erro.detail === "object") ? erro.detail : {};
  if (d.cobrado !== true) return null;
  // Discreta de propósito: é informação de contabilidade, não alarme. Quem
  // precisa agir sobre a recusa lê a mensagem do serviço, acima.
  return (
    <div style={{ marginTop: "6px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
      {(cp || {}).opcoesRecusaCobrada
        || "Esta tentativa consumiu uma chamada da sua cota do dia."}
    </div>
  );
}
