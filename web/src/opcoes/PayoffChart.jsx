/**
 * PayoffChart.jsx — aba-opcoes F3 (ADR-027, plano 24-02, 2026-09-11).
 *
 * A curva de resultado no vencimento de UMA estrutura, com o eixo X em PREÇO
 * DO OBJETO. SVG puro, e não `lightweight-charts`: aquela biblioteca desenha
 * série TEMPORAL, e aqui o eixo horizontal é preço — torcer a ferramenta para
 * fingir tempo custaria mais do que o SVG inteiro.
 *
 * Regras que este arquivo NÃO negocia:
 * · **nenhuma conta nova.** `net_cost`/`max_gain`/`max_loss` por ação vêm do
 *   serviço; os mesmos números em reais vêm prontos de `emReais`, calculado
 *   uma única vez no backend (D-24.2). Multiplicar aqui criaria uma segunda
 *   versão da mesma conta, e duas versões divergem na primeira correção feita
 *   só de um lado;
 * · **breakeven é PREÇO, não dinheiro** — fica fora de qualquer bloco de
 *   reais e nunca encosta no lote;
 * · **ilimitado não vira teto.** Com `unlimited_gain`/`unlimited_loss`, a
 *   curva não é fechada naquele lado e a legenda diz que não há limite.
 *   Desenhar um teto que o serviço não declarou é a mentira mais cara
 *   possível neste arquivo;
 * · `null` vira travessão, nunca 0 — 0 é um resultado, ausência não é.
 *
 * Zero import de `App.jsx` (seria ciclo): o bloco de tokens é local, padrão
 * de `SetupChart.jsx`/`pet/BorisChat.jsx`.
 */
import { useId, useMemo, useRef } from "react";
import { extentOf } from "../chartutil.js";
import { Kicker, ErroDoMcp } from "./uiOpcoes.jsx";
import { montarGeometria, afastarPontos, MARC_R } from "./payoffEixos.js";
import { useLarguraMedida, EixoY, EixoX, MarcadoresVerticais, LegendaMarcadores } from "./PayoffPrimitivas.jsx";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root`.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim",
  "onAccent", "positive"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Onda H2 (2026-10-08, quick 261008-w9i): viewBox = largura medida; eixos, marcadores
// numerados e legenda da linguagem comum (payoffEixos.js + PayoffPrimitivas.jsx).
// Decisões H2-D1..D9 no PLAN do quick.

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const moeda = (v) => (ehNum(v) ? "R$ " + fmt(v, 2) : "—");

// Resultado interpolado entre dois nós da curva. Não é invenção de dado: o
// payoff no vencimento é linear POR PARTES, com quebra exatamente nos strikes
// — e os nós que o serviço manda SÃO os strikes (mais o S=0). Entre dois nós
// vizinhos, a reta é o próprio contrato da função.
const entre = (a, b, x) =>
  a.result + (b.result - a.result) * ((x - a.underlying) / (b.underlying - a.underlying));

// Recorta a poligonal à janela visível, interpolando nos cortes. É ZOOM, não
// edição: a janela existe porque o primeiro nó costuma ser S=0 e desenhar de
// 0 a 40 esmaga a região onde a decisão acontece (strikes, breakeven e
// cenários) contra a borda direita.
function recortar(pontos, x0, x1) {
  const fora = [];
  for (let i = 0; i < pontos.length; i++) {
    const p = pontos[i];
    const ant = pontos[i - 1], prox = pontos[i + 1];
    if (p.underlying < x0) {
      if (prox && prox.underlying > x0) fora.push({ underlying: x0, result: entre(p, prox, x0) });
      continue;
    }
    if (p.underlying > x1) {
      if (ant && ant.underlying < x1) fora.push({ underlying: x1, result: entre(ant, p, x1) });
      break;                       // ordenado por preço: daqui em diante é tudo fora
    }
    fora.push(p);
  }
  return fora;
}

export default function PayoffChart({ estrutura, emReais, cp, palette, dominio, segmentos, valorHoje }) {
  // `segmentos` chega pronto do backend (Fase 36/37-01) mas este componente
  // não o consome — quem lê `segmentos` é `ExplicacaoPayoff.jsx` (37-02),
  // um irmão desta árvore, não este arquivo (interfaces do 37-04-PLAN.md).
  void segmentos;
  const e = estrutura || {};
  const c = cp || {};
  const P = palette || {};
  // `useId` traz `:` no valor; fora dele o id vira referência inválida em
  // `url(#…)`. Vários gráficos convivem na mesma tela (um por vencimento), e
  // dois `clipPath` com o mesmo id pintariam a curva errada.
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const refPlot = useRef(null);
  const largura = useLarguraMedida(refPlot, 340);

  const nome = typeof e.name === "string" && e.name ? e.name : "—";
  // Vencimento não existe no envelope de `evaluate_option_structure`; a perna
  // carrega o dela. Ler daqui é leitura, não dedução.
  const vencimento = ((e.legs || []).find((p) => p && typeof p.expiration === "string") || {}).expiration || null;
  const ganhoIlimitado = e.unlimited_gain === true;
  const perdaIlimitada = e.unlimited_loss === true;
  const breakevens = (Array.isArray(e.breakevens) ? e.breakevens : []).filter(ehNum);
  // CHART-02: strikes únicos das pernas de opção (nunca da perna ACAO, que
  // não carrega `kind`/`strike` numérico) — marcados no eixo junto dos
  // breakevens, nunca calculados aqui (só leitura de `e.legs`).
  const strikesUnicos = [...new Set(
    (Array.isArray(e.legs) ? e.legs : [])
      .filter((p) => p && (p.kind === "CALL" || p.kind === "PUT") && ehNum(p.strike))
      .map((p) => p.strike),
  )];

  const desenho = useMemo(() => {
    const pontos = (Array.isArray(e.payoff) ? e.payoff : [])
      .filter((p) => p && ehNum(p.underlying) && ehNum(p.result))
      .map((p) => ({ underlying: p.underlying, result: p.result }))
      .sort((a, b) => a.underlying - b.underlying);
    if (pontos.length < 2) return null;

    const bloco = e.scenarios && typeof e.scenarios === "object" ? e.scenarios : {};
    const cenarios = (Array.isArray(bloco.scenarios) ? bloco.scenarios : [])
      .filter((s) => s && ehNum(s.underlying));

    // CHART-04: quando o backend já mandou as 4 bordas do domínio
    // (`dominio_da_curva()`, Fase 36), usa-as DIRETO — sem recalcular janela
    // local. Com QUALQUER uma ausente, cai no cálculo local de sempre
    // (fallback que mantém `CuradoriaEstruturas.jsx`/qualquer chamador que
    // não passa `dominio` idêntico a antes deste plano, D-09).
    const dominioCompleto = dominio
      && ehNum(dominio.xMin) && ehNum(dominio.xMax)
      && ehNum(dominio.yMin) && ehNum(dominio.yMax);

    let x0, x1, ymin, ymax;
    if (dominioCompleto) {
      x0 = dominio.xMin; x1 = dominio.xMax;
      ymin = dominio.yMin; ymax = dominio.yMax;
    } else {
      // Janela: onde a decisão acontece. O nó em S=0 fica de fora do cálculo
      // do foco (preço zero não é cenário de ninguém), mas a curva ATÉ ele
      // segue valendo — o recorte interpola em vez de descartar.
      const foco = [
        ...pontos.filter((p) => p.underlying > 0).map((p) => p.underlying),
        ...breakevens,
        ...cenarios.map((s) => s.underlying),
      ];
      const base = foco.length ? foco : pontos.map((p) => p.underlying);
      x0 = Math.min(...base); x1 = Math.max(...base);
      if (x1 === x0) { const d = Math.max(Math.abs(x0) * 0.05, 0.5); x0 -= d; x1 += d; }
      const folga = (x1 - x0) * 0.08;
      x0 = Math.max(0, x0 - folga);            // preço negativo não existe
      x1 += folga;
    }

    // Curva: SEMPRE recortada/interpolada dentro da janela acima, venha ela
    // do backend ou do cálculo local — é o mesmo "zoom", não edição.
    let curva = recortar(pontos, x0, x1);
    // Janela que não deixou curva nenhuma é janela errada: melhor a curva
    // inteira esmagada do que um retângulo vazio, que se lê como "zero".
    if (curva.length < 2) { curva = pontos; x0 = pontos[0].underlying; x1 = pontos[pontos.length - 1].underlying; }

    // Cauda direita só quando o serviço declarou os DOIS lados limitados:
    // aí a inclinação além do último strike é zero por definição (é o que
    // "limitado dos dois lados" significa), e estender na horizontal é
    // leitura do que ele afirmou. Com `unlimited_*`, a inclinação existe mas
    // a magnitude é desconhecida — e chutá-la seria desenhar preço.
    const ultimo = pontos[pontos.length - 1];
    if (!ganhoIlimitado && !perdaIlimitada && x1 > ultimo.underlying
        && curva[curva.length - 1].underlying <= ultimo.underlying) {
      curva = [...curva, { underlying: x1, result: ultimo.result }];
    }

    // Zero SEMPRE na escala: é a linha que separa lucro de prejuízo, e sem
    // ela a curva não significa nada. Só recalcula localmente quando o
    // domínio não veio pronto do backend.
    if (!dominioCompleto) {
      [ymin, ymax] = extentOf([[...curva.map((p) => p.result),
        ...cenarios.filter((s) => ehNum(s.result)).map((s) => s.result), 0]]);
    }

    return {
      x0, x1, ymin, ymax,
      curva,
      cenarios: cenarios.filter((s) => s.underlying >= x0 && s.underlying <= x1),
      marcas: breakevens.filter((b) => b >= x0 && b <= x1),
    };
  }, [e.payoff, e.scenarios, breakevens.join(","), ganhoIlimitado, perdaIlimitada, dominio]);

  // Cores de P&L — o ÚNICO lugar desta tela onde verde e vermelho são
  // permitidos, porque aqui eles significam lucro e prejuízo, não juízo.
  // `var(--x)` resolve no fallback porque isto é SVG (DOM), não canvas: a
  // trava de hex do `SetupChart` vale para o PriceChart, que pinta em canvas.
  const corLucro = P.positive || T.accent;
  const corPerda = P.negative || T.negative;

  const ganhoTxt = ganhoIlimitado
    ? (c.opcoesGanhoIlimitado || "sem teto")
    : fmt(e.max_gain);
  const perdaTxt = perdaIlimitada
    ? (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço")
    : fmt(e.max_loss);

  const cabecalho = (
    <div style={{ marginBottom: "8px" }}>
      {/* CHART-05: "No vencimento" e "Hoje" são dois pesos IGUAIS, mesma
          lógica da frase-ponte D-05 da Fase 32 ("nenhuma é mais certa que a
          outra") — nunca hierarquia primário/secundário entre os dois. */}
      <Kicker>{(c.opcoesNoVencimentoTitulo || "No vencimento") + (vencimento ? " · " + vencimento : "")}</Kicker>
      <div style={{ fontSize: "13px", fontWeight: 700, color: T.textPrimary }}>
        {nome}{vencimento ? " · " + vencimento : ""}
      </div>
      <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "3px", fontVariantNumeric: "tabular-nums" }}>
        {(c.opcoesPorAcaoRotulo || "por ação") + ": custo " + fmt(e.net_cost)
          + " · ganho máx. " + ganhoTxt + " · perda máx. " + perdaTxt}
      </div>
      {emReais ? (
        <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
          {/* Exibição pura: as três cifras chegaram multiplicadas do backend. */}
          {(c.opcoesEmReaisRotulo || "em reais") + ": custo " + moeda(emReais.custoLiquido)
            + " · ganho máx. " + (ganhoIlimitado ? (c.opcoesGanhoIlimitado || "sem teto") : moeda(emReais.ganhoMaximo))
            + " · perda máx. " + (perdaIlimitada ? (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço") : moeda(emReais.perdaMaxima))}
        </div>
      ) : null}
      {/* Bloco de PREÇO, deliberadamente separado do bloco acima: o empate é
          preço do ativo, não dinheiro da posição (D-24.2). */}
      <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
        {(c.opcoesBreakevenRotulo || "Breakeven") + ": "
          + (breakevens.length ? breakevens.map((b) => fmt(b)).join(" · ") : "—")}
      </div>
      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "2px", lineHeight: 1.45 }}>
        {c.opcoesBreakevenAjuda || ""}
      </div>
      {/* CHART-05: bloco "Hoje · valor de mercado", ausente por completo
          (nem o Kicker aparece) quando `valorHoje` não foi tentado —
          distinto de "tentado e falhou" (erro) e de "tentado e deu certo"
          (dados). Decisão do CHAMADOR (SecaoAnalisar.jsx/SecaoComparar.jsx,
          Plano 37-05), nunca inferida aqui. */}
      {valorHoje != null ? (
        <>
          <Kicker>{c.opcoesHojeTitulo || "Hoje · valor de mercado"}</Kicker>
          {valorHoje.erro ? (
            <ErroDoMcp erro={valorHoje.erro} cp={cp} />
          ) : valorHoje.dados ? (
            <>
              <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
                {(c.opcoesPorAcaoRotulo || "por ação") + ": " + moeda(valorHoje.dados.porAcao)}
              </div>
              {ehNum(valorHoje.dados.emReais) ? (
                <div style={{ fontSize: "12px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
                  {(c.opcoesEmReaisRotulo || "em reais") + ": " + moeda(valorHoje.dados.emReais)}
                </div>
              ) : null}
              <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "2px", lineHeight: 1.45 }}>
                {c.opcoesHojeAjuda || ""}
              </div>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );

  const caixa = (filho) => (
    <div style={{
      border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel,
      // filho de grid/flex tem `min-width: auto` por padrão e pode estourar
      // a coluna em 375px (D-07) — `minWidth: 0` deixa o próprio SVG encolher
      // até a largura real do container em vez de vazar.
      minWidth: 0, maxWidth: "100%",
    }}>
      {cabecalho}
      {filho}
    </div>
  );

  // Sem pontos suficientes não há curva — e um SVG em branco se lê como
  // "resultado zero". O cabeçalho fica: as cifras existem mesmo quando a
  // resposta não trouxe a curva (é o caso de `/proposta`, que monta a
  // estrutura sem avaliá-la ponto a ponto).
  if (!desenho) {
    return caixa(
      <div style={{ fontSize: "13px", color: T.textMuted, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
        {c.opcoesSemEstrutura || "O serviço não mandou os pontos da curva desta estrutura."}
      </div>,
    );
  }

  const { x0, x1, ymin, ymax, curva, cenarios, marcas } = desenho;
  const semTeto = ganhoIlimitado || dominio?.ganhoIlimitado === true;
  const semPiso = perdaIlimitada || dominio?.perdaIlimitada === true;
  // CHART-02: só os strikes dentro da janela visível ganham marcador.
  const strikesVisiveis = strikesUnicos.filter((v) => v >= x0 && v <= x1);
  const descricao = "Curva de resultado no vencimento de " + nome
    + (vencimento ? ", vencimento " + vencimento : "")
    + ", por preço do ativo entre " + fmt(x0) + " e " + fmt(x1) + " reais. "
    + "Custo líquido " + fmt(e.net_cost) + " por ação"
    + (emReais ? " (" + moeda(emReais.custoLiquido) + " no lote)" : "") + ". "
    // "por ação" só cola no que é número: "perda máxima sem piso declarado
    // pelo serviço por ação" não é frase, e leitor de tela lê tudo em voz.
    + "Ganho máximo " + ganhoTxt + (ganhoIlimitado ? "" : " por ação")
    + ", perda máxima " + perdaTxt + (perdaIlimitada ? "" : " por ação") + ". "
    + (breakevens.length
      ? "Empata com o ativo em " + breakevens.map((b) => fmt(b)).join(" ou ") + "."
      : "O serviço não informou preço de empate.")
    // CHART-02 (acessibilidade): todos os strikes, não só os visíveis na
    // tela — mesma disciplina do breakeven acima.
    + (strikesUnicos.length
      ? " Strikes desta estrutura: " + strikesUnicos.map((v) => fmt(v)).join(", ") + "."
      : "")
    + (dominio && ehNum(dominio.spot) ? " Preço do ativo hoje: " + fmt(dominio.spot) + "." : "");

  // Marcadores verticais numerados (ordem de entrada: breakevens, strikes, spot;
  // a numeração final é por preço, feita em montarGeometria).
  const marcadoresIn = [
    ...marcas.map((v) => ({ preco: v, rotulo: c.opcoesBreakevenRotulo || "Breakeven", comPreco: true, traco: "2 4" })),
    ...strikesVisiveis.map((v) => ({ preco: v, rotulo: c.opcoesLegStrike || "Strike", comPreco: true, traco: "1 3" })),
  ];
  if (dominio && ehNum(dominio.spot) && dominio.spot >= x0 && dominio.spot <= x1) {
    marcadoresIn.push({ preco: dominio.spot, rotulo: c.opcoesLegHoje || "Preço do ativo hoje", comPreco: true, traco: "none" });
  }
  const geo = montarGeometria({ largura, x0, x1, yMin: ymin, yMax: ymax, marcadores: marcadoresIn, semTeto, semPiso });

  const d = curva
    .map((p, i) => (i ? "L" : "M") + geo.sx(p.underlying).toFixed(1) + " " + geo.sy(p.result).toFixed(1))
    .join(" ");
  const yCorte = Math.max(0, Math.min(geo.H, geo.yZero));

  // Cenários do serviço: círculos numerados SOBRE a curva (a partir de k+1). Sem
  // `result` numérico não há ponto (null != 0): o cenário só aparece na legenda.
  const cenNum = cenarios.map((s, i) => ({ s, n: geo.marcadores.length + i + 1 }));
  const noCurva = cenNum.filter(({ s }) => ehNum(s.result));
  const afast = afastarPontos(noCurva.map(({ s }) => ({ x: geo.sx(s.underlying), y: geo.sy(s.result) })), 20);

  const fonteLeg = { fontSize: "12px", color: T.textSecondary, lineHeight: 1.45 };

  return caixa(
    <>
      <div ref={refPlot} style={{ minWidth: 0 }}>
        <svg
          role="img"
          aria-label={descricao}
          viewBox={`0 0 ${geo.W} ${geo.H}`}
          preserveAspectRatio="xMidYMid meet"
          style={{ width: "100%", height: "auto", display: "block", maxWidth: "100%" }}
        >
          <title>{descricao}</title>
          <defs>
            {/* Duas metades da mesma curva: acima do zero é lucro, abaixo é
                prejuízo. Recorte por retângulo, sem segunda implementação do
                cálculo de breakeven. */}
            <clipPath id={"lucro-" + uid}>
              <rect x="0" y="0" width={geo.W} height={yCorte} />
            </clipPath>
            <clipPath id={"perda-" + uid}>
              <rect x="0" y={yCorte} width={geo.W} height={Math.max(0, geo.H - yCorte)} />
            </clipPath>
          </defs>

          <EixoY geo={geo} semTeto={semTeto} semPiso={semPiso} />
          <MarcadoresVerticais geo={geo} />

          {/* A curva, nas duas cores de P&L. Só traço: NENHUM preenchimento em
              lugar nenhum, para que um lado ilimitado não pareça fechado. */}
          <path d={d} fill="none" strokeWidth="3" style={{ stroke: corLucro }} clipPath={`url(#lucro-${uid})`} />
          <path d={d} fill="none" strokeWidth="3" style={{ stroke: corPerda }} clipPath={`url(#perda-${uid})`} />

          <EixoX geo={geo} formatar={fmt} />

          {noCurva.map(({ s, n }, i) => {
            const p = afast[i];
            const cy = p.y + p.dy;
            return (
              <g key={"ce-" + i} aria-hidden="true">
                {p.dy !== 0 ? (
                  <line x1={p.x} x2={p.x} y1={p.y} y2={cy} style={{ stroke: T.textSecondary }} strokeWidth="1" />
                ) : null}
                <circle cx={p.x} cy={cy} r={MARC_R} style={{ fill: T.accent }} />
                <text x={p.x} y={cy} textAnchor="middle" dominantBaseline="central"
                  style={{ fontSize: "12px", fontWeight: 700, fill: T.onAccent }}>{n}</text>
              </g>
            );
          })}
        </svg>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "6px" }}>
        <div style={{ ...fonteLeg, display: "flex", alignItems: "center", gap: "8px" }}>
          <svg aria-hidden="true" width="16" height="10" style={{ flexShrink: 0 }}>
            <line x1="0" x2="16" y1="5" y2="5" strokeWidth="3" style={{ stroke: T.textPrimary }} />
          </svg>
          <span>{(c.opcoesSerieTotal || "Resultado no vencimento") + " · " + (c.opcoesSerieLeitura || "acima de R$ 0 ganha; abaixo, perde")}</span>
        </div>
        <LegendaMarcadores
          itens={[
            ...geo.marcadores,
            ...cenNum.map(({ s, n }) => ({ n, rotulo: typeof s.name === "string" ? s.name : "—", comPreco: true, preco: s.underlying })),
          ]}
          formatarPreco={fmt}
        />
        {semTeto ? (
          <div style={fonteLeg}><span aria-hidden="true">↑</span> {c.opcoesGanhoIlimitado || "sem teto"}</div>
        ) : null}
        {semPiso ? (
          <div style={fonteLeg}><span aria-hidden="true">↓</span> {c.opcoesPerdaIlimitadaCurta || "sem piso"}</div>
        ) : null}
      </div>

      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "6px", lineHeight: 1.45 }}>
        {"Eixo horizontal: preço do ativo no vencimento (" + fmt(x0) + " a " + fmt(x1) + "). "}
        {"Eixo vertical: resultado " + (c.opcoesPorAcaoRotulo || "por ação") + "."}
        {" " + (c.opcoesEixoVerticalLoteAjuda || "Multiplique pelo lote para o valor total.")}
        {" Linha " + (c.opcoesEixoZeroRotulo || "R$ 0") + ": empate."}
        {ganhoIlimitado ? " Ganho: " + (c.opcoesGanhoIlimitado || "sem teto") + "." : ""}
        {perdaIlimitada ? " Perda: " + (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço") + "." : ""}
      </div>
    </>,
  );
}
