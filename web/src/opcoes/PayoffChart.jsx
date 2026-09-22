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
import { useId, useMemo } from "react";
import { extentOf } from "../chartutil.js";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root`.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// H/PAD_T/PAD_B cresceram no plano 31-03 (D-07, legibilidade em 375px): o
// viewBox é a única "unidade" que este SVG tem — tipografia maior sem mais
// respiro vertical corta rótulo no eixo. W fica em 320 de propósito: é a
// razão de aspecto que casa com a largura útil de um cartão em 375px, e
// mudá-la mudaria o enquadramento da curva, não a legibilidade.
const W = 320, H = 192;
// PAD_E cresceu de 10 para 48 no plano 37-04 (CHART-01): orçamento pro pior
// caso de rótulo do eixo Y de 2 casas ("-99,99", 6 chars) a FONTE_MIN=11,5px
// — ver `37-UI-SPEC.md` §1.1 pela conta completa. Desloca a borda esquerda
// da curva ~38px pra dentro, mesma categoria de troca que H/PAD_T/PAD_B já
// fizeram uma vez (Fase 31 D-07, legibilidade sobre área bruta de plot).
const PAD_E = 48, PAD_D = 10, PAD_T = 18, PAD_B = 32;

// Piso de legibilidade (D-07): com viewBox de 320 de largura e um container
// de ~315px num aparelho de 375px, a escala é ~0,98 — o tamanho em
// user-space é praticamente o tamanho em CSS px, então fontSize="9.5" era
// 9,5px reais na tela, abaixo do piso de legibilidade.
const FONTE_MIN = 11.5;
const FONTE_SETA = 14;

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

export default function PayoffChart({ estrutura, emReais, cp, palette, dominio }) {
  const e = estrutura || {};
  const c = cp || {};
  const P = palette || {};
  // `useId` traz `:` no valor; fora dele o id vira referência inválida em
  // `url(#…)`. Vários gráficos convivem na mesma tela (um por vencimento), e
  // dois `clipPath` com o mesmo id pintariam a curva errada.
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");

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

    const sx = (u) => PAD_E + ((u - x0) / (x1 - x0 || 1)) * (W - PAD_E - PAD_D);
    const sy = (r) => PAD_T + (1 - (r - ymin) / (ymax - ymin || 1)) * (H - PAD_T - PAD_B);

    const d = curva
      .map((p, i) => (i ? "L" : "M") + sx(p.underlying).toFixed(1) + " " + sy(p.result).toFixed(1))
      .join(" ");

    return {
      d, sx, sy, x0, x1, ymin, ymax,
      yZero: sy(0),
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
      <div style={{ fontSize: "13px", fontWeight: 700, color: T.textPrimary }}>
        {nome}{vencimento ? " · " + vencimento : ""}
      </div>
      <div style={{ fontSize: "11.5px", color: T.textSecondary, marginTop: "3px", fontVariantNumeric: "tabular-nums" }}>
        {(c.opcoesPorAcaoRotulo || "por ação") + ": custo " + fmt(e.net_cost)
          + " · ganho máx. " + ganhoTxt + " · perda máx. " + perdaTxt}
      </div>
      {emReais ? (
        <div style={{ fontSize: "11.5px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
          {/* Exibição pura: as três cifras chegaram multiplicadas do backend. */}
          {(c.opcoesEmReaisRotulo || "em reais") + ": custo " + moeda(emReais.custoLiquido)
            + " · ganho máx. " + (ganhoIlimitado ? (c.opcoesGanhoIlimitado || "sem teto") : moeda(emReais.ganhoMaximo))
            + " · perda máx. " + (perdaIlimitada ? (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço") : moeda(emReais.perdaMaxima))}
        </div>
      ) : null}
      {/* Bloco de PREÇO, deliberadamente separado do bloco acima: o empate é
          preço do ativo, não dinheiro da posição (D-24.2). */}
      <div style={{ fontSize: "11.5px", color: T.textSecondary, marginTop: "2px", fontVariantNumeric: "tabular-nums" }}>
        {(c.opcoesBreakevenRotulo || "Breakeven") + ": "
          + (breakevens.length ? breakevens.map((b) => fmt(b)).join(" · ") : "—")}
      </div>
      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "2px", lineHeight: 1.45 }}>
        {c.opcoesBreakevenAjuda || ""}
      </div>
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
      <div style={{ fontSize: "12.5px", color: T.textMuted, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
        {c.opcoesSemEstrutura || "O serviço não mandou os pontos da curva desta estrutura."}
      </div>,
    );
  }

  const { d, sx, sy, x0, x1, ymin, ymax, yZero, curva, cenarios, marcas } = desenho;
  // CHART-02: só os strikes que caem dentro da janela visível ganham marca
  // no eixo — mesma disciplina de `marcas` (breakevens) acima.
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
      : "");

  return caixa(
    <>
      <svg
        role="img"
        aria-label={descricao}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "auto", display: "block", maxWidth: "100%" }}
      >
        <title>{descricao}</title>
        <defs>
          {/* Duas metades da mesma curva: o traço acima do zero é lucro, o de
              baixo é prejuízo. Recorte por retângulo em vez de partir a
              poligonal nos cruzamentos — mesmo resultado, sem uma segunda
              implementação do cálculo de breakeven. */}
          <clipPath id={"lucro-" + uid}>
            <rect x="0" y="0" width={W} height={Math.max(0, Math.min(H, yZero))} />
          </clipPath>
          <clipPath id={"perda-" + uid}>
            <rect x="0" y={Math.max(0, Math.min(H, yZero))} width={W} height={Math.max(0, H - yZero)} />
          </clipPath>
        </defs>

        {/* 1. linha do zero */}
        <line x1={PAD_E} y1={yZero} x2={W - PAD_D} y2={yZero}
          stroke={T.borderSubtle} strokeWidth="1" strokeDasharray="3 3" />

        {/* 1b. eixo Y (CHART-01): até 3 marcas (topo/zero/base), coluna
            esquerda em x=44, tick de 4px até PAD_E=48. A linha acima é o
            TRAÇO do zero na área do gráfico; isto é o EIXO (tick+número) —
            propósitos diferentes, nunca fundidos num só desenho. */}
        {(() => {
          const yTopo = sy(dominio?.yMax ?? ymax);
          const suprimirTopo = dominio?.ganhoIlimitado === true || Math.abs(yTopo - yZero) < 3;
          const yBase = sy(dominio?.yMin ?? ymin);
          const suprimirBase = dominio?.perdaIlimitada === true || Math.abs(yBase - yZero) < 3;
          const marcasEixo = [
            !suprimirTopo ? { y: yTopo, label: fmt(dominio?.yMax ?? ymax) } : null,
            { y: yZero, label: c.opcoesEixoZeroRotulo || "R$ 0" },
            !suprimirBase ? { y: yBase, label: fmt(dominio?.yMin ?? ymin) } : null,
          ].filter(Boolean);
          return marcasEixo.map((mrc, i) => (
            <g key={"eixo-y-" + i}>
              <line x1={44} y1={mrc.y} x2={PAD_E} y2={mrc.y} stroke={T.textMuted} strokeWidth="1" />
              <text x={44} y={mrc.y} textAnchor="end" dominantBaseline="central"
                fontSize={FONTE_MIN} fill={T.textMuted}>{mrc.label}</text>
            </g>
          ));
        })()}

        {/* 2. a curva, nas duas cores de P&L. Só traço: NENHUM `fill` em
            lugar nenhum — é o que garante que um lado ilimitado não apareça
            fechado por um retângulo. */}
        <path d={d} fill="none" stroke={corLucro} strokeWidth="2" clipPath={`url(#lucro-${uid})`} />
        <path d={d} fill="none" stroke={corPerda} strokeWidth="2" clipPath={`url(#perda-${uid})`} />

        {/* 3. breakevens + strikes (CHART-02): a mesma marca medida no eixo
            X, em preço, mescladas num único array ordenado por X antes de
            decidir o que cabe (regra (d) do plano 31-03, estendida pelo
            37-04) — a LINHA do preço é SEMPRE desenhada — é dado, não
            decoração — e só o TEXTO se suprime quando dois rótulos ficam
            próximos demais para não se sobrepor. Em empate de slot,
            breakeven vem primeiro no array de entrada (ordenação estável) e
            GANHA a exibição do texto. A descrição completa de todos os
            breakevens/strikes continua no aria-label/<title> do SVG acima,
            então nada de dado desaparece — só o texto ilegível/duplicado
            some da tela. */}
        {(() => {
          const itens = [
            ...marcas.map((v) => ({ valor: v, tipoMarca: "breakeven" })),
            ...strikesVisiveis.map((v) => ({ valor: v, tipoMarca: "strike" })),
          ].sort((a, b) => sx(a.valor) - sx(b.valor));
          let ultimoX = -Infinity;
          return itens.map((item, i) => {
            const x = sx(item.valor);
            const mostrarTexto = x - ultimoX >= 44;
            if (mostrarTexto) ultimoX = x;
            const ancora = x < PAD_E + 18 ? "start" : x > W - 28 ? "end" : "middle";
            const ehBreakeven = item.tipoMarca === "breakeven";
            return (
              <g key={"marca-" + i}>
                <line x1={x} y1={PAD_T} x2={x} y2={H - PAD_B}
                  stroke={ehBreakeven ? T.textMuted : T.borderFaint} strokeWidth="1"
                  strokeDasharray={ehBreakeven ? "2 4" : "1 3"} />
                {mostrarTexto ? (
                  <text x={x} y={H - PAD_B + 12} textAnchor={ancora} fontSize={FONTE_MIN} fill={T.textMuted}>{fmt(item.valor)}</text>
                ) : null}
              </g>
            );
          });
        })()}

        {/* 4. cenários do serviço (±1σ e os nomeados alvo/stop) + spot
            (CHART-02, "hoje"). Mesma regra de supressão: o CÍRCULO (marca) é
            sempre desenhado, só o texto some quando um rótulo já desenhado
            fica a menos de 52 em x E menos de 14 em y — perto o bastante pra
            colidir. O spot entra PRIMEIRO na lista de colisão — CHART-02
            exige spot sempre marcado, então ele nunca perde o texto; um
            cenário que colida com ele é quem cede. */}
        {(() => {
          const temSpot = dominio && ehNum(dominio.spot);
          const xSpot = temSpot ? sx(dominio.spot) : null;
          const ySpot = temSpot ? (() => {
            for (let i = 0; curva && i < curva.length - 1; i++) {
              const a = curva[i], b = curva[i + 1];
              if (dominio.spot >= a.underlying && dominio.spot <= b.underlying) return sy(entre(a, b, dominio.spot));
            }
            return yZero;
          })() : null;
          const desenhados = temSpot ? [{ x: xSpot, y: ySpot }] : [];
          const marcasCenario = cenarios.map((s, i) => {
            const x = sx(s.underlying);
            const y = ehNum(s.result) ? sy(s.result) : yZero;
            const colide = desenhados.some((p) => Math.abs(x - p.x) < 52 && Math.abs(y - p.y) < 14);
            const mostrarTexto = !colide;
            if (mostrarTexto) desenhados.push({ x, y });
            const ancora = x > W - 52 ? "end" : "start";
            return (
              <g key={"ce-" + i}>
                <circle cx={x} cy={y} r="3" fill={T.textPrimary} />
                {mostrarTexto ? (
                  <text x={ancora === "end" ? x - 5 : x + 5} y={y - 5} textAnchor={ancora}
                    fontSize={FONTE_MIN} fill={T.textSecondary}>
                    {typeof s.name === "string" ? s.name : "—"}
                  </text>
                ) : null}
              </g>
            );
          });
          const anchoraSpot = xSpot > W - 52 ? "end" : "start";
          return (
            <>
              {marcasCenario}
              {temSpot ? (
                <g key="spot">
                  <line x1={xSpot} y1={PAD_T} x2={xSpot} y2={H - PAD_B} stroke={T.textPrimary} strokeWidth="1" />
                  <circle cx={xSpot} cy={ySpot} r="3" fill={T.textPrimary} />
                  <text x={anchoraSpot === "end" ? xSpot - 5 : xSpot + 5} y={ySpot - 5} textAnchor={anchoraSpot}
                    fontSize={FONTE_MIN} fill={T.textPrimary}>
                    {(c.opcoesHojePrefixoEixo || "hoje") + " " + fmt(dominio.spot)}
                  </text>
                </g>
              ) : null}
            </>
          );
        })()}

        {/* 5. lado sem limite: seta na borda, sem fechar a curva, agora com
            rótulo curto colado (CHART-03) — a leitura completa segue na
            legenda abaixo (cabe e é lida por leitor de tela lá). */}
        {ganhoIlimitado ? (
          <>
            <text aria-hidden x={W - PAD_D - 16} y={PAD_T + 8} textAnchor="end" fontSize={FONTE_MIN} fill={corLucro}>
              {c.opcoesGanhoIlimitado || "sem teto"}
            </text>
            <text aria-hidden x={W - PAD_D} y={PAD_T + 8} textAnchor="end" fontSize={FONTE_SETA} fill={corLucro}>↑</text>
          </>
        ) : null}
        {perdaIlimitada ? (
          <>
            <text aria-hidden x={W - PAD_D - 16} y={H - PAD_B - 2} textAnchor="end" fontSize={FONTE_MIN} fill={corPerda}>
              {c.opcoesPerdaIlimitadaCurta || "sem piso"}
            </text>
            <text aria-hidden x={W - PAD_D} y={H - PAD_B - 2} textAnchor="end" fontSize={FONTE_SETA} fill={corPerda}>↓</text>
          </>
        ) : null}
      </svg>

      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "6px", lineHeight: 1.45 }}>
        {"Eixo horizontal: preço do ativo no vencimento (" + fmt(x0) + " a " + fmt(x1) + "). "}
        {"Eixo vertical: resultado " + (c.opcoesPorAcaoRotulo || "por ação") + "."}
        {" " + (c.opcoesEixoVerticalLoteAjuda || "Multiplique pelo lote para o valor total.")}
        {ganhoIlimitado ? " Ganho: " + (c.opcoesGanhoIlimitado || "sem teto") + "." : ""}
        {perdaIlimitada ? " Perda: " + (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço") + "." : ""}
      </div>
    </>,
  );
}
