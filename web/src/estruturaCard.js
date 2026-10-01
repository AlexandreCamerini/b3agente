import { qtyLivre } from "./finance.js";

// Fase 45 (CARD-01..06) — decisão de exibição do card de Posição estruturada.
// Módulo puro: sem React, sem I/O, sem store. Decide O QUE mostrar, nunca
// calcula P&L — todo número vem de `estrutura` do motor determinístico
// (princípio 5 / P9). Testável em Node sem build.

// Tickers da carteira que têm ao menos uma perna de opção aberta (D-01/D-02):
// sem pernas -> o card segue sendo o atual.
export function tickersComPernas(positions, optionPositions) {
  if (!Array.isArray(positions) || !Array.isArray(optionPositions)) return [];
  const comPernas = new Set(optionPositions.filter((o) => o && o.underlying).map((o) => o.underlying));
  return positions.filter((p) => p && comPernas.has(p.t)).map((p) => p.t);
}

// Chave estável do efeito de recarga (UI-SPEC §Busca e recarga): não depende
// da identidade do array nem da ordem das pernas; muda com buy/sell/fechar e
// com a troca Estudo<->Operador (a frase do motor vem no modo do servidor).
export function assinaturaEstrutura(t, positions, optionPositions, operador) {
  const p = (Array.isArray(positions) ? positions : []).find((x) => x && x.t === t);
  const pernas = (Array.isArray(optionPositions) ? optionPositions : [])
    .filter((o) => o && o.underlying === t)
    .map((o) => `${o.id}:${o.qty}:${o.side || ""}`)
    .sort();
  const acao = p ? `${p.qty}:${p.avg}` : "-:-";
  return `${t}:${acao}|${pernas.join(",")}|${operador ? "op" : "es"}`;
}

// "atual" (sem pernas locais, D-02) | "carregando" | "falha" | "estruturada".
// `estrutura: null` NÃO significa "sem opções" (a rota engole exceção em null):
// com pernas locais é falha (D-03).
export function estadoLeitura(temPernas, entrada) {
  if (!temPernas) return "atual";
  if (!entrada || entrada.status === "carregando") return "carregando";
  if (entrada.status === "falha") return "falha";
  if (entrada.status === "ok" && entrada.estrutura) return "estruturada";
  return "falha";
}

// CARD-05: o aviso "sem stop" nunca aparece em carregando/falha; na
// estruturada só quando não há stop e o motor não declarou proteção pela put.
export function mostraAvisoSemStop(p, modoLeitura, estrutura) {
  if (!p || p.stop != null) return false;
  if (modoLeitura === "atual") return true;
  if (modoLeitura !== "estruturada") return false;
  return !(estrutura && estrutura.stopTexto != null);
}

// R:R nunca renderiza "—": só existe com stop E alvo.
// Fase 45 (code review WR-05): quando o preço atual é informado, o R:R só
// aparece se a fórmula produz número finito e positivo (preço acima do stop e
// abaixo do alvo). Continua sendo a exceção deliberada ao D-02 (o gate de
// stop/alvo é o mesmo nos dois cards). Sem `cur` (undefined) vale só o gate
// antigo de stop/alvo, para os chamadores que não conhecem o preço.
export function valorRR(p, cur) {
  if (!p || p.stop == null || p.alvo == null) return null;
  if (typeof cur !== "number" || !isFinite(cur) || cur <= p.stop) return null;
  const rr = (p.alvo - cur) / (cur - p.stop);
  return isFinite(rr) && rr > 0 ? rr : null;
}

export function mostraRR(p, cur) {
  if (cur === undefined) return !!p && p.stop != null && p.alvo != null;
  return valorRR(p, cur) != null;
}

// D-11: pill "travada" só com qtyTravada > 0; collar usa a variante própria.
export function tipoPillTravada(estrutura, qtyTravada) {
  if (!(qtyTravada > 0)) return null;
  return estrutura && estrutura.nome === "collar" ? "collar" : "padrao";
}

// Só fatia a string AAAA-MM-DD (sem Date: sem efeito de fuso).
export function ddmmDeIso(iso) {
  const m = typeof iso === "string" ? iso.match(/^\d{4}-(\d{2})-(\d{2})/) : null;
  return m ? `${m[2]}/${m[1]}` : null;
}

// Chip de vencimento. O estado "vencida" vem do motor e tem precedência;
// âmbar só com 0 <= dias <= 5 (D-11).
export function chipVencimento(estrutura) {
  if (!estrutura) return null;
  const ddmm = ddmmDeIso(estrutura.vencimentoReferencia);
  if (!ddmm) return null;
  const dias = estrutura.diasParaVencimento;
  if (estrutura.estado === "vencida") return { tipo: "vencida", ddmm, dias, ambar: false };
  if (typeof dias !== "number" || !isFinite(dias)) return { tipo: "vence", ddmm, dias: null, ambar: false };
  if (dias < 0) return { tipo: "vencida", ddmm, dias, ambar: false };
  if (dias === 0) return { tipo: "hoje", ddmm, dias, ambar: true };
  return { tipo: "vence", ddmm, dias, ambar: dias <= 5 };
}

// Domínio da régua: min/max dos valores numéricos (piso, teto, PM, hoje,
// stop, alvo). Menos de 2 valores distintos -> sem régua.
export function dominioRegua(valores) {
  const nums = (Array.isArray(valores) ? valores : []).filter((v) => typeof v === "number" && isFinite(v));
  if (nums.length < 2) return null;
  const min = Math.min(...nums), max = Math.max(...nums);
  return max > min ? { min, max } : null;
}

// Mesma fórmula do posOf da régua de plano (8%-92%), com clamp.
export function posRegua(v, dominio) {
  if (!dominio || typeof v !== "number" || !isFinite(v)) return 8;
  const pos = 8 + ((v - dominio.min) / ((dominio.max - dominio.min) || 1)) * 84;
  return Math.min(92, Math.max(8, pos));
}

// Sinal de um resultado monetário: zero exato é neutro (sem "+", sem verde);
// null = indisponível. Só decide a apresentação, não calcula nada.
export function sinalResultado(v) {
  if (typeof v !== "number" || !isFinite(v)) return null;
  return v === 0 ? "zero" : v > 0 ? "pos" : "neg";
}

// Kicker do resultado: "só as ações" só quando o número das ações existe;
// com ações também indisponíveis o rótulo não pode prometer um número ausente.
export function kickerResultadoSoAcoes(resultado) {
  return !!resultado && typeof resultado.acoes === "number" && isFinite(resultado.acoes);
}

// Tom visual do bloco de estado (COR-01: só o âmbar de atenção destoa).
export function tomDoEstado(estado) {
  if (estado === "ate_5_dias" || estado === "exercicio_provavel") return "atencao";
  if (estado === "premio_indisponivel") return "info";
  if (estado === "vencida") return "encerrada";
  return "linha";
}

// ---------------------------------------------------------------------------
// Fase 46 (Carteira v6) — helpers puros do card v6. Só decidem apresentação:
// devolvem chaves de CARTAO_POSICAO + vals (a UI resolve o texto) e nunca
// fazem aritmética sobre campo financeiro (D-01/D-04, princípio 5).
// ---------------------------------------------------------------------------

// UI-SPEC "régua/trilho": rótulo nas pontas ancora para dentro (não vaza do
// card a partir de 320 px); no miolo fica centrado. x em % (0-100).
export function ancoraRotulo(x) {
  if (typeof x !== "number" || !isFinite(x)) return "centro";
  if (x < 22) return "inicio";
  if (x > 78) return "fim";
  return "centro";
}

const DIST_MIN_ROTULO = 30;

// D-17: anti-colisão determinística. Cada item vai para a MENOR linha em que
// fica a >= 30 (%) de todo item já posto nela. Mesma ordem; x inválido omitido.
export function rotulosSemColisao(itens) {
  const postos = [];
  const saida = [];
  for (const it of Array.isArray(itens) ? itens : []) {
    if (!it || typeof it.x !== "number" || !isFinite(it.x)) continue;
    let linha = 0;
    while (postos.some((q) => q.linha === linha && Math.abs(q.x - it.x) < DIST_MIN_ROTULO)) linha++;
    postos.push({ x: it.x, linha });
    saida.push({ ...it, linha });
  }
  return saida;
}

// D-17 / UI-SPEC "Flip 3D": 170 ms de saída + 170 ms de entrada; com movimento
// reduzido a troca é imediata (0 ms, sem timer).
export function flipDuracaoMs(reduzido) {
  return reduzido ? { saida: 0, entrada: 0, total: 0 } : { saida: 170, entrada: 170, total: 340 };
}

// UI-SPEC "Flip 3D": lê a preferência NA HORA do clique (não a constante
// de movimento do App.jsx, lida uma só vez no carregamento).
export function prefereMovimentoReduzido(win) {
  try {
    if (!win || typeof win.matchMedia !== "function") return false;
    const m = win.matchMedia("(prefers-reduced-motion: reduce)");
    return !!(m && m.matches);
  } catch {
    return false;
  }
}

// Face aberta por padrão: com pernas de opção abre em Opções, senão em Ação.
export function faceInicial(nPernas) {
  return nPernas > 0 ? "opcoes" : "acao";
}

// D-13 (+ ajuste UI-SPEC, Pergunta 1): UM estado principal por prioridade —
// risco do motor > ações travadas > sem plano/incompleto > fora do plano >
// dentro do plano (só sem opções) — e o resto como linhas extras. Fora/dentro
// do plano vem do enum `posicaoNoPlano` do backend (D-06): nunca compara preço
// com stop/alvo aqui.
export function estadoPrincipalV6({ p, estrutura, leituraPlano } = {}) {
  const linha = (chave, vals, tom, glifo) => ({ chave, vals, tom, glifo });
  const extras = [];
  let principal = null;
  const est = estrutura && estrutura.estado;
  const texto = estrutura ? estrutura.estadoTexto : undefined;

  if (est === "vencida") principal = linha("motor", { texto }, "encerrada", "ⓘ");
  else if (est === "exercicio_provavel") principal = linha("motor", { texto }, "atencao", "⚠");
  else if (p) {
    const qty = Number(p.qty) || 0;
    const travada = Number(p.qtyTravada) || 0;
    const livre = qtyLivre(p);
    if (travada > 0 && livre === 0) principal = linha("estado_travadas_todas", {}, "info", "ⓘ");
    else if (travada > 0 && livre > 0 && livre < qty) {
      principal = linha("estado_travadas_parcial", { n: travada, m: qty, k: livre }, "info", "ⓘ");
    } else if (p.stop == null && p.alvo == null) principal = linha("estado_sem_plano", {}, "atencao", "⚠");
    else if (p.alvo == null) principal = linha("estado_falta_alvo", {}, "atencao", "⚠");
    else if (p.stop == null) principal = linha("estado_falta_stop", {}, "atencao", "⚠");
    else {
      const pos = leituraPlano ? leituraPlano.posicaoNoPlano : null;
      if (pos === "abaixo_stop") principal = linha("estado_abaixo_stop", {}, "atencao", "⚠");
      else if (pos === "acima_alvo") principal = linha("estado_acima_alvo", {}, "atencao", "⚠");
      else if (pos === "dentro" && !estrutura) principal = linha("estado_dentro", {}, "neutro", "✓");
    }
  }

  if (estrutura && estrutura.resultado && estrutura.resultado.incompleto) {
    extras.push(linha("extra_resultado_parcial", {}, "info", "ⓘ"));
  }
  if (!estrutura && leituraPlano && leituraPlano.preco == null) {
    extras.push(linha("extra_cotacao_indisponivel", {}, "info", "ⓘ"));
  }
  if (est === "premio_indisponivel") extras.push(linha("motor", { texto }, "info", "ⓘ"));
  return { principal, extras };
}

// D-04: o slider lê o ponto da grade do backend por ÍNDICE (clamp), sem
// aritmética sobre preço/resultado. Índice não inteiro arredonda (só o índice).
export function pontoDoIndice(simulador, i) {
  const pontos = simulador && Array.isArray(simulador.pontos) ? simulador.pontos : null;
  if (!pontos || !pontos.length || typeof i !== "number" || !isFinite(i)) return null;
  const k = Math.min(pontos.length - 1, Math.max(0, Math.round(i)));
  return pontos[k] || null;
}

// D-04: índice (na grade) de um ponto nomeado (hoje/equilibrio/teto/alta_forte);
// null quando ausente, null no backend ou fora da grade.
export function indiceNomeado(simulador, nome) {
  const pontos = simulador && Array.isArray(simulador.pontos) ? simulador.pontos : null;
  const nomeados = simulador && simulador.nomeados;
  if (!pontos || !nomeados) return null;
  const v = nomeados[nome];
  return Number.isInteger(v) && v >= 0 && v < pontos.length ? v : null;
}

// D-06 / UI-SPEC "Simulador": zona (rótulo do backend) -> borda + glifo (a cor
// nunca é o único canal). Zona desconhecida cai no neutro.
export function zonaVisual(zona) {
  if (zona === "perda_travada" || zona === "prejuizo") return { borda: "negative", glifo: "▾" };
  if (zona === "ganho") return { borda: "borderDashed", glifo: "▬" };
  if (zona === "ganho_travado") return { borda: "positive", glifo: "▴" };
  return { borda: "borderSubtle", glifo: "ⓘ" };
}

// UI-SPEC "Grade 3x2": 3 colunas, mas 2 abaixo de 340 px úteis ou com texto
// >= 130 %. Entrada inválida -> 2 (layout mais seguro).
export function colunasDaGrade(larguraUtilPx, escalaTexto) {
  if (typeof larguraUtilPx !== "number" || !isFinite(larguraUtilPx)) return 2;
  if (typeof escalaTexto !== "number" || !isFinite(escalaTexto)) return 2;
  return larguraUtilPx < 340 || escalaTexto >= 1.3 ? 2 : 3;
}

// Pool simples com teto de concorrência (cada chamada consome cota do
// provedor). Resolve na ordem de entrada; uma rejeição não interrompe as demais.
export function executarComTeto(thunks, limite) {
  const lista = Array.isArray(thunks) ? thunks : [];
  const resultados = new Array(lista.length);
  let proximo = 0;
  async function trabalhador() {
    while (proximo < lista.length) {
      const i = proximo++;
      try {
        resultados[i] = { ok: true, valor: await lista[i]() };
      } catch (erro) {
        resultados[i] = { ok: false, erro };
      }
    }
  }
  const n = Math.max(1, Math.min(limite || 1, lista.length));
  return Promise.all(Array.from({ length: n }, trabalhador)).then(() => resultados);
}

// Fase 45 (code review WR-01/WR-02): fila ÚNICA com teto de concorrência para
// as leituras de estrutura (cada chamada consome cota da brapi). Diferente de
// `executarComTeto`, cada item traz `vale()`, conferido só quando chega a vez
// de rodar: se a leitura já não é a vigente (desmontou, trocou de escopo,
// assinatura mudou) o item é abandonado SEM chamar a API. `cancelar()` abandona
// tudo que ainda está pendente (o que já está em voo termina e é descartado
// pelo próprio guard da resposta). Resolve sempre, nunca rejeita:
// { abandonada: true } | { ok, valor } | { ok: false, erro }.
export function criarFilaLeituras(limite) {
  const teto = Math.max(1, limite || 1);
  const pendentes = [];
  let ativos = 0;
  function andar() {
    while (ativos < teto && pendentes.length) {
      const item = pendentes.shift();
      let vigente = false;
      try { vigente = !!item.vale(); } catch { vigente = false; }
      if (!vigente) { item.resolver({ abandonada: true }); continue; }
      ativos++;
      let prom;
      try { prom = Promise.resolve(item.rodar()); } catch (erro) { prom = Promise.reject(erro); }
      prom.then(
        (valor) => item.resolver({ ok: true, valor }),
        (erro) => item.resolver({ ok: false, erro })
      ).then(() => { ativos--; andar(); });
    }
  }
  return {
    enfileirar(rodar, vale) {
      return new Promise((resolver) => { pendentes.push({ rodar, vale, resolver }); andar(); });
    },
    cancelar() {
      pendentes.splice(0).forEach((item) => item.resolver({ abandonada: true }));
    },
    estado() { return { ativos, pendentes: pendentes.length }; },
  };
}
