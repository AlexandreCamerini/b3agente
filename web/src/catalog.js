// Catalogo e estado-padrao embutidos no cliente, para o app iOS funcionar
// com persistencia 100% no aparelho (config/watchlist/carteira), sem depender
// do servidor para esses dados. O servidor so e usado para cotacoes e analise.

export const CATALOG = [
  { t: "PETR4", n: "Petrobras PN" },
  { t: "PETR3", n: "Petrobras ON" },
  { t: "VALE3", n: "Vale ON" },
  { t: "ITUB4", n: "Itau Unibanco PN" },
  { t: "BBDC4", n: "Bradesco PN" },
  { t: "BBAS3", n: "Banco do Brasil ON" },
  { t: "B3SA3", n: "B3 ON" },
  { t: "ABEV3", n: "Ambev ON" },
  { t: "WEGE3", n: "WEG ON" },
  { t: "ELET3", n: "Eletrobras ON" },
  { t: "RENT3", n: "Localiza ON" },
  { t: "PRIO3", n: "PRIO ON" },
  { t: "SUZB3", n: "Suzano ON" },
  { t: "EQTL3", n: "Equatorial ON" },
  { t: "RADL3", n: "Raia Drogasil ON" },
  { t: "VIVT3", n: "Telefonica Brasil (Vivo) ON" },
  { t: "ITSA4", n: "Itausa PN" },
  { t: "JBSS3", n: "JBS ON" },
  { t: "BPAC11", n: "BTG Pactual UNT" },
  { t: "RDOR3", n: "Rede D'Or ON" },
];

export const CATALOG_TICKERS = CATALOG.map((c) => c.t);

export function defaultSkillText() {
  return [
    "# Skill: Mesa B3 - Analista Tecnico Educacional",
    "",
    "Persona: analista tecnico de mesa de operacoes da B3. Tom calmo, direto",
    "e didatico, como quem explica para um investidor pessoa fisica.",
    "",
    "Voce recebe, a cada analise, a cotacao atual e o historico de ~1 mes",
    "(candles diarios) de UM ativo. Produza uma leitura tecnica EDUCACIONAL.",
    "",
    "Regras invioláveis:",
    "- Conteudo EDUCACIONAL e dinheiro SIMULADO. Deixe claro.",
    "- NUNCA prometa lucro nem use linguagem de ganho garantido.",
    "- SEMPRE destaque gerenciamento de risco e uso de stop.",
    "- Se o cenario for indefinido, diga que o melhor e NAO operar.",
    "- Nada do que voce escreve e recomendacao de investimento.",
    "",
    "Seja conciso (250-400 palavras), linguagem simples antes do jargao.",
  ].join("\n");
}

// FASE 2: coleção de prompts da solução, indexada por chave (extensível —
// novas chaves entram aqui sem mudar a interface de persistência). Cada prompt
// mantém o enquadramento educacional obrigatório (sugestão por perfil, nunca
// recomendação de compra/venda).
export function defaultLlmPrompts() {
  return {
    carteiraStopAlvo: `Você é um analista técnico educacional da B3. Sua tarefa é analisar CADA
ATIVO INDIVIDUALMENTE e propor, para cada um, um STOP e um ALVO.
Base da análise:
- Use PRIMEIRO as informações do ativo fornecidas nesta requisição (preço
  atual, histórico e indicadores passados). NÃO invente dados que não foram
  fornecidos.
- Complemente com seu conhecimento geral sobre o ativo e o contexto de
  mercado, deixando claro quando algo é contexto geral e não dado fornecido.
- Considere o PERFIL do investidor (apetite a risco, horizonte e tolerância
  de perda por operação) como o fator que dimensiona os números.
Cada análise é INDIVIDUAL: avalie cada ativo isoladamente. Não produza um
número único para a carteira inteira; o stop/alvo de um ativo não influencia
o do outro.
Regras invioláveis:
- Conteúdo EDUCACIONAL e dinheiro SIMULADO — deixe isso explícito.
- A proposta é uma SUGESTÃO por perfil, NÃO recomendação de compra ou venda,
  nem sinal de entrada.
- NUNCA prometa lucro nem use linguagem de ganho garantido.
- Dimensione o STOP para limitar a perda por operação conforme a tolerância
  do perfil.
- Defina o ALVO por uma relação risco:retorno coerente com o horizonte.
- Se os dados forem insuficientes ou estiverem distorcidos (baixa liquidez,
  evento de redução de capital, etc.) ou o cenário estiver indefinido, diga
  que o melhor é AGUARDAR / não operar — não force números.
Para cada ativo, explique em 2 a 4 frases, em linguagem simples, o raciocínio
por trás dos números.
Formato de saída: retorne SOMENTE um JSON (nada fora dele), um objeto por
ativo:
[
  {
    "ativo": "PETR4",
    "precoAtual": 38.50,
    "stop": 36.20,
    "alvo": 43.00,
    "explicacao": "…2 a 4 frases…",
    "operar": true
  }
]
Quando recomendar aguardar, use "operar": false e stop/alvo como null,
explicando o porquê em "explicacao".`,
  };
}

export function defaultState() {
  return {
<<<<<<< HEAD
    config: { provider: "anthropic", model: "", keySource: "env", apiKey: "", baseUrl: "", serverUrl: "", initialBudget: 10000.0, theme: "dark", userName: "", onboarded: false, candlePeriod: "1y", streak: { days: 0, last: "" }, notif: { enabled: false, stop: true, alvo: true, agente: true, variacao: true } },
=======
    config: { provider: "anthropic", model: "", keySource: "env", apiKey: "", baseUrl: "", serverUrl: "", initialBudget: 10000.0, theme: "dark", userName: "", onboarded: false, streak: { days: 0, last: "" }, notif: { enabled: false, stop: true, alvo: true, agente: true, variacao: true } },
>>>>>>> 908c0a22284b7e560215d00545d61d119f7b5026
    llmPrompts: defaultLlmPrompts(),
    skill: { name: "Mesa B3 - Educacional v1", text: defaultSkillText() },
    watchlist: ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "B3SA3"],
    cash: 10000.0,
    positions: [
      { t: "PETR4", qty: 300, avg: 36.8, stop: null, alvo: null },
      { t: "ITUB4", qty: 200, avg: 31.1, stop: null, alvo: null },
      { t: "VALE3", qty: 100, avg: 63.4, stop: null, alvo: null },
    ],
    history: [
      { date: "18/06/2026 11:02", type: "COMPRA", t: "PETR4", qty: 300, price: 36.8, pnl: null },
      { date: "17/06/2026 10:12", type: "COMPRA", t: "ITUB4", qty: 200, price: 31.1, pnl: null },
      { date: "12/06/2026 09:58", type: "COMPRA", t: "VALE3", qty: 100, price: 63.4, pnl: null },
    ],
    agent: {
      autonomous: false,
      allocPct: 5,
      intervalMin: 15,
      events: [{ time: "Inicio", kind: "info", text: "Bem-vindo. Configure o modelo de IA na aba Config e peca uma analise na aba Mercado." }],
    },
    analyses: {}, equitySnapshots: [],
    profile: {
      risco: "moderado",
      horizonte: "swing",
      toleranciaPerdaPct: 2.0,
      objetivo: "crescimento",
      experiencia: "intermediario",
    },
    custom: [],
  };
}
