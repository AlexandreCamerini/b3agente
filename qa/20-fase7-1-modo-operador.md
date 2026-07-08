# QA 20 — FASE 7.1: Modo Operador (fundação)
*08/07/2026 · escopo aprovado em `PROPOSTA-MODO-OPERADOR.md` + mock `qa/mocks/modo-operador.html`*

## O que entrou nesta fase (F7.1)

### Backend — plano operacional determinístico
- `setups.plano_operacional(setup, close)` (novo, puro): deriva decisão e plano
  dos números que os detectores JÁ produzem (gatilho/invalidação/alvo). Regras
  objetivas da persona `analise-tecnica-b3`:
  - decisão ∈ COMPRAR · VENDER · AGUARDAR CONFIRMAÇÃO · NÃO OPERAR;
  - stop = SEMPRE a invalidação do setup (nunca arbitrário);
  - alvo1 = 1R (parcial); alvo2 = projeção do setup (2R ou regra própria);
  - **R:R mínimo 1,5:1 no alvo final** — abaixo, NÃO OPERAR com o texto
    canônico "não há operação com vantagem estatística clara";
  - gatilho já rompido: até 0,5R além → entrada A MERCADO com R:R recalculado
    do preço real (e re-corte); além disso → NÃO OPERAR (não persegue preço);
  - compressão (neutro) → AGUARDAR CONFIRMAÇÃO; geometria incoerente → NÃO OPERAR.
- `setups.plano_do_resultado(sres, close)`: melhor direcional > neutro > nada.
- `scanner.py` anexa `plano` a cada resultado do scan (payload compartilhado —
  por isso o SIZING fica no cliente: capital de usuário não entra no cache).
- `detect_setups` (Modo Estudo) permanece byte-a-byte com o mesmo shape.

### Config — modo, termo e risco (dois stores, mesma regra)
- `config.appMode: "estudo"|"operador"` (padrão estudo) · `config.operadorTermo:
  {aceitoEm, versao}` · `config.risco: {pctPorTrade (0.25–5, padrão 1), capital}`.
- **Regra de segurança espelhada** (store.py e deviceStore): "operador" NUNCA
  liga sem termo aceito — patch sem termo é ignorado silenciosamente.
- Backfill nos dois lados para docs/contas antigos.

### UI
- **Perfil → card "Modo de trabalho"**: seletor Estudo/Operador; 1ª ativação
  abre o Termo de Responsabilidade (rolagem obrigatória até o fim + checkbox;
  aceite grava `{aceitoEm, versao}` no MESMO patch do modo). Texto do termo e
  versão são fonte única em `disclaimers.js` (`operadorTermo`, `TERMO_OPERADOR_
  VERSAO`).
- **Radar (modo operador)**: pill de decisão colorida no lugar do veredito
  educacional; bloco do plano (entrada com tipo, stop, alvo1/alvo2, R:R) e
  posição sugerida (`sizingPlano` em finance.js — lote de 100, risco = capital
  × pct; usa capital operacional da config ou o simulado COM aviso). Decisões
  não-operáveis mostram o motivo direto. Disclaimer do rodapé troca para o da
  persona (`DISCLAIMERS.operador`).
- **Modo Estudo 100% intocado**: plano nem é lido fora do modo operador.

## Testes

- `server/tests/test_plano_operacional.py` (novo, 11 testes): compra/venda,
  corte por R:R, entrada a mercado com R:R real, não-perseguição, esticado,
  neutro, geometria, vazios, prioridade direcional e guardião do vocabulário
  educacional intocado.
- `web/tests/test_modo_operador.mjs` (novo, 23 asserções): sizing executável
  (6 casos), defaults/regra do termo nos stores, card+termo do Perfil, gating
  do Radar e disclaimers.
- Regressão completa: **18 suítes backend offline + 18 web — 0 falhas**
  (scanner/setups/setups_br inalterados e verdes).

## Fora desta fase (próximas)
F7.2 formato PRO no N1/N2 + checklist pré-operação · F7.3 trades reais +
monitor de planos com push · F7.4 painel de assertividade.

## Hard stop — validação no iPhone/web
1. Perfil → Modo de trabalho → Operador → termo abre; sem rolar até o fim o
   aceite fica bloqueado; aceitar ativa e o card mostra data/versão do aceite.
2. Radar no modo operador: cards com COMPRAR/VENDER mostram plano completo e
   posição sugerida; cards sem vantagem mostram NÃO OPERAR + motivo; voltar ao
   Estudo restaura os vereditos educacionais.
3. Reabrir o app: o modo escolhido persiste (e o termo não re-aparece).
4. Conta nova/anônima: nasce em Estudo.
