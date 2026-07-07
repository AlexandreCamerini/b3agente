# QA 11 — Rodada final autorizada (Radar · Operador IA · APNs · robustez)

## A — Robustez (o erro do ELET3)
- `candle_cache.load`: 404/erro do provedor → retry em 1y → erro AMIGÁVEL
  ("Sem histórico disponível para {t} no provedor…") sem stack técnico;
  falha do delta serve o cache (status `stale`). Card mostra a mensagem e o
  botão Analisar segue como retry. Botão ✎ da watchlist mantido (o defeito
  era o tratamento de erro, não o botão).

## B — SweepGauge (progresso em toda espera longa)
- Backend: scan grava progresso incremental; GET /api/scan/progress.
  1ª varredura = aquecer cache; seguintes = só atualizar análise (fase exibida).
- <SweepGauge/>: anel de varredura estilo radar; determinado (ticker atual
  pulsando + contador feitos/total + micro-log dos 3 últimos) e indeterminado
  (etapas nomeadas rotacionando). Plugado em: scan (com polling 0,9s), deep
  (N1), análise do ativo (N2, compacto) e alvo/stop (N3, compacto).

## C — Avaliar: UM fluxo de compra
- Botão "Comprar" avulso REMOVIDO. CTA único condicionado à leitura:
  "Estudar alta" → primário com sugestão de quantidade; neutra → "Simular
  compra…" sem sugestão; "Estudar baixa/Não operar" → aviso + "Simular mesmo
  assim" discreto. NUNCA sugere quantidade contra a leitura. Sem análise →
  CTA neutro. Chip "Modelo:" só no expandido (faxina C2).

## D — Operador IA (ex-Automatizar)
- Aba/tela renomeadas ("Operador IA"; ids preservados). Status VIVO do
  servidor (GET /api/agent/status): pregão aberto?, intervalo, kill-switch,
  último ciclo, push configurado/aparelhos — atualiza a cada 20s.
- "▶ Rodar ciclo agora (servidor)" (POST /api/agent/run-now): demonstração
  imediata fora do pregão (respeita o kill-switch). "Testar push agora"
  (POST /api/push/test) com mensagens de erro acionáveis.
- Cartão local reetiquetado ("Modo local — com o app aberto").

## E — APNs automatizado
- scripts/configurar-apns.sh (parâmetros REAIS: LC65399YC9 · 22Y76F52NJ ·
  com.exemplo.b3agente): valida a chave, aplica via Railway CLI ou copia ao
  clipboard + instruções, e VERIFICA no /api/agent/status até "configurado".
- *.p8 bloqueado no .gitignore, no git-do-zero e auditado no verificar-arquivos.

## Validação: backend 128/128 ✅ · web ✅ · balance 0/0/0 ✅ · py_compile ✅ ·
node --check ✅ · manifesto ✅ · configurar-apns.sh ensaiado com a chave real ✅.

## Roteiro de apresentação (device)
1. Radar → varrer → SweepGauge girando com contador/tickers → resultados.
2. Card → Aprofundar com IA (gauge de etapas) → Análise completa → Avaliar.
3. Avaliar: leitura favorável → CTA com sugestão → comprar → cenários N3 →
   aplicar. Leitura ruim em outro ativo → aviso + "Simular mesmo assim".
4. Operador IA: status vivo → ▶ Rodar ciclo agora → registro na hora →
   Testar push → notificação no aparelho.
5. Ativo problemático (ex.: ELET3): mensagem amigável, app segue vivo.
