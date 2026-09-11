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

const W = 320, H = 180;
const PAD_E = 10, PAD_D = 10, PAD_T = 14, PAD_B = 26;

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

export default function PayoffChart({ estrutura, emReais, cp, palette }) {
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

  const desenho = useMemo(() => {
    const pontos = (Array.isArray(e.payoff) ? e.payoff : [])
      .filter((p) => p && ehNum(p.underlying) && ehNum(p.result))
      .map((p) => ({ underlying: p.underlying, result: p.result }))
      .sort((a, b) => a.underlying - b.underlying);
    if (pontos.length < 2) return null;

    const bloco = e.scenarios && typeof e.scenarios === "object" ? e.scenarios : {};
    const cenarios = (Array.isArray(bloco.scenarios) ? bloco.scenarios : [])
      .filter((s) => s && ehNum(s.underlying));

    // Janela: onde a decisão acontece. O nó em S=0 fica de fora do cálculo do
    // foco (preço zero não é cenário de ninguém), mas a curva ATÉ ele segue
    // valendo — o recorte interpola em vez de descartar.
    const foco = [
      ...pontos.filter((p) => p.underlying > 0).map((p) => p.underlying),
      ...breakevens,
      ...cenarios.map((s) => s.underlying),
    ];
    const base = foco.length ? foco : pontos.map((p) => p.underlying);
    let x0 = Math.min(...base), x1 = Math.max(...base);
    if (x1 === x0) { const d = Math.max(Math.abs(x0) * 0.05, 0.5); x0 -= d; x1 += d; }
    const folga = (x1 - x0) * 0.08;
    x0 = Math.max(0, x0 - folga);             // preço negativo não existe
    x1 += folga;

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
    // ela a curva não significa nada.
    const [ymin, ymax] = extentOf([[...curva.map((p) => p.result),
      ...cenarios.filter((s) => ehNum(s.result)).map((s) => s.result), 0]]);

    const sx = (u) => PAD_E + ((u - x0) / (x1 - x0 || 1)) * (W - PAD_E - PAD_D);
    const sy = (r) => PAD_T + (1 - (r - ymin) / (ymax - ymin || 1)) * (H - PAD_T - PAD_B);

    const d = curva
      .map((p, i) => (i ? "L" : "M") + sx(p.underlying).toFixed(1) + " " + sy(p.result).toFixed(1))
      .join(" ");

    return {
      d, sx, sy, x0, x1,
      yZero: sy(0),
      cenarios: cenarios.filter((s) => s.underlying >= x0 && s.underlying <= x1),
      marcas: breakevens.filter((b) => b >= x0 && b <= x1),
    };
  }, [e.payoff, e.scenarios, breakevens.join(","), ganhoIlimitado, perdaIlimitada]);

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
    <div style={{ border: `1px solid ${T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel }}>
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

  const { d, sx, sy, x0, x1, yZero, cenarios, marcas } = desenho;
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
      : "O serviço não informou preço de empate.");

  return caixa(
    <>
      <svg
        role="img"
        aria-label={descricao}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "auto", display: "block" }}
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

        {/* 2. a curva, nas duas cores de P&L. Só traço: NENHUM `fill` em
            lugar nenhum — é o que garante que um lado ilimitado não apareça
            fechado por um retângulo. */}
        <path d={d} fill="none" stroke={corLucro} strokeWidth="2" clipPath={`url(#lucro-${uid})`} />
        <path d={d} fill="none" stroke={corPerda} strokeWidth="2" clipPath={`url(#perda-${uid})`} />

        {/* 3. breakevens: a única marca medida no eixo X, em preço */}
        {marcas.map((b, i) => {
          const x = sx(b);
          const ancora = x < 22 ? "start" : x > W - 22 ? "end" : "middle";
          return (
            <g key={"be-" + i}>
              <line x1={x} y1={PAD_T} x2={x} y2={H - PAD_B} stroke={T.textMuted} strokeWidth="1" strokeDasharray="2 4" />
              <text x={x} y={H - PAD_B + 12} textAnchor={ancora} fontSize="9.5" fill={T.textMuted}>{fmt(b)}</text>
            </g>
          );
        })}

        {/* 4. cenários do serviço (±1σ e os nomeados alvo/stop) */}
        {cenarios.map((s, i) => {
          const x = sx(s.underlying);
          const y = ehNum(s.result) ? sy(s.result) : yZero;
          const ancora = x > W - 44 ? "end" : "start";
          return (
            <g key={"ce-" + i}>
              <circle cx={x} cy={y} r="3" fill={T.textPrimary} />
              <text x={ancora === "end" ? x - 5 : x + 5} y={y - 5} textAnchor={ancora}
                fontSize="9.5" fill={T.textSecondary}>
                {typeof s.name === "string" ? s.name : "—"}
              </text>
            </g>
          );
        })}

        {/* 5. lado sem limite: seta na borda, sem fechar a curva. O texto vai
            na legenda abaixo (cabe e é lido por leitor de tela lá). */}
        {ganhoIlimitado ? (
          <text aria-hidden x={W - PAD_D} y={PAD_T + 8} textAnchor="end" fontSize="11" fill={corLucro}>↑</text>
        ) : null}
        {perdaIlimitada ? (
          <text aria-hidden x={W - PAD_D} y={H - PAD_B - 2} textAnchor="end" fontSize="11" fill={corPerda}>↓</text>
        ) : null}
      </svg>

      <div style={{ fontSize: "11px", color: T.textMuted, marginTop: "6px", lineHeight: 1.45 }}>
        {"Eixo horizontal: preço do ativo no vencimento (" + fmt(x0) + " a " + fmt(x1) + "). "}
        {"Eixo vertical: resultado " + (c.opcoesPorAcaoRotulo || "por ação") + "."}
        {ganhoIlimitado ? " Ganho: " + (c.opcoesGanhoIlimitado || "sem teto") + "." : ""}
        {perdaIlimitada ? " Perda: " + (c.opcoesPerdaIlimitada || "sem piso declarado pelo serviço") + "." : ""}
      </div>
    </>,
  );
}
