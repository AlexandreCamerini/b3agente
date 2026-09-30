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
export function mostraRR(p) {
  return !!p && p.stop != null && p.alvo != null;
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
