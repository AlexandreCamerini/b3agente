# QA 09 — Fase 2 · M1 (navegação da jornada) + 2.1 (Radar → IA/Avaliar)

## Escopo desta etapa (incremental, conforme PROPOSTA-UX aprovada)
M1 completo + item 2.1 do flow. As etapas M2 (watchlist no Descobrir),
2.2–2.5 e M5–M6 vêm nas próximas rodadas, cada uma com hard stop de device.

## M1 — Nova navegação (ids preservados, zero mudança de estado)
- BottomNav: **Descobrir**(radar) → **Avaliar**(mercado) → **Operar**(carteira)
  → **Automatizar**(agente, NOVO id/aba) → **Acompanhar**(evolucao).
- **Perfil migrou para o avatar da Topbar** (inicial do nome; ícone genérico
  sem nome). Hub/Config/atalhos internos intactos (perfilView preservado).
- **Agente promovido a casa própria** (AgenteScreen na aba `agente`); o
  atalho antigo via Perfil→agente continua funcionando (zero perda).
- **Opções virou interna de Avaliar**: botão "Opções ▸" no cabeçalho; a tela
  ganhou BackHeader ("← Estudo de opções") de volta para Avaliar.
- Ícone novo no NavIcon: `agente` (robô).

## 2.1 — Ações no card do Radar
- **"Aprofundar com IA"**: 1 chamada N1 para o ativo (`store.scanDeep`
  {period, tickers: t, topN: 1}); estado por ticker; botão vira
  "Leitura da IA ✓" quando pronta (cache do dia = sem custo, informado).
- **DeepModal** (novo): resumo, planoEstudo (vocabulário fixo), leitura por
  setup com critérios ✓/○, cenários de ESTUDO alta/baixa/neutro, riscos,
  invalidação, confiança, "+ Modelos utilizados" e disclaimer do payload.
  CTA "Análise completa →" encadeia para Avaliar.
- **"IA no top-N"** no cabeçalho: 1º toque busca o ESTIMATE e mostra
  "Confirmar: X chamadas de IA" (+ quem está no cache de hoje); 2º toque
  roda o lote e marca os cards com a leitura pronta.
- **"Análise completa →"** no card: `ctx.openAvaliar(t)` — garante o ativo
  na watchlist, navega para Avaliar e dispara a análise N2 do ativo.

## Camada de dados (invariante preservada)
- `api.js`: `scanDeep` (POST, timeout 240s) e `scanDeepEstimate` (GET).
- `persistence.js`: MESMA interface nos dois stores (serverStore delega;
  deviceStore delega com `ensure()` — padrão do `scan`).

## Validação
- Balance App.jsx: 0/0/0 ✅ · node --check (api, persistence, sync, notify) ✅
- Suítes web: todas ✅ (novo `test_deep_parity.mjs`: contrato GET/POST do
  deep + paridade dos stores; `test_radar.mjs` atualizado para o rótulo
  "Descobrir" da UX aprovada — id `radar` segue travado pelo teste)
- Backend: 115/115 ✅ (inalterado nesta rodada)
- Wiring: scanDeep em api(2)/persistence(6)/App(3); openAvaliar definido e
  usado (card + modal); aba agente definida e renderizada.

## Hard stop (device) — o que validar
1. Navegação: 5 abas na ordem da jornada; avatar abre o Perfil; "Opções ▸"
   em Avaliar abre e volta; aba Automatizar mostra o Agente.
2. Radar: "Aprofundar com IA" num card → modal com a leitura (logado com
   gerenciada OU BYOK); repetir no mesmo dia → "cache de hoje".
3. "IA no top-N": 1º toque mostra o custo; confirmar roda e marca os cards.
4. "Análise completa →" leva a Avaliar já analisando o ativo (mesmo um
   fora da watchlist — ele é adicionado).
5. Sem regressão: compra/venda, stop/alvo IA, welcome, notificações.
