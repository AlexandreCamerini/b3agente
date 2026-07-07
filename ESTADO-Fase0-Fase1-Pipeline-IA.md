# ESTADO — Rodada UX + Pipeline IA em 3 níveis
**Data:** 2026-07-02 · **Decisões registradas:** conta Apple Developer PAGA
confirmada → F3.3b (push/APNs) LIBERADA quando chegar a Fase 3 · modelo
HÍBRIDO por custo confirmado.

## ✋ GATE ABERTO — Fase 0 (UX)
`PROPOSTA-UX.md` entregue: inventário das 6 telas, 7 duplicatas mapeadas
(D1–D7), wireframe textual da jornada DESCOBRIR→AVALIAR→OPERAR→AUTOMATIZAR→
ACOMPANHAR, checklist de preservação item a item e migração incremental
M1–M6. **Nenhuma mudança de UI foi feita.** Aguarda aprovação (ou escolha
das alternativas (a)/(b) do rodapé) para iniciar a Fase 2.

## ✅ FASE 1 — backend implementado (paralelo permitido pelo gate)
### Especificação (pedido do Alex: skill analise-tecnica-b3)
`ESPEC-Analises-Tecnicas.md`: matriz determinístico × LLM completa, contrato
de dados + regras de validação da skill aplicadas no backend, instruções de
system prompt por nível — metodologia da skill (confluência, invalidação,
teto de confiança, stop por ATR/estrutura, cenários) traduzida ao vocabulário
educacional fixo (guardrail preservado: decisão operacional da skill NÃO
entra; vira plano de estudo).

### 1.1 N1 · /api/scan/deep (+ /estimate)
- `scan_deep.py` novo: top-N por confluência (`radarAiTopN` default 5, teto
  10), ignora ativos sem setup, cache por (ticker, período, DIA), erro por
  ativo isolado, disclaimer no payload.
- `llm.analyze_deep`: OPERADOR_EDUCACIONAL (regras da skill) + DEEP_FORMAT
  (leituraSetups com critérios presentes/AUSENTES, cenários alta/baixa/neutro,
  invalidação, confiança com teto "moderada" sem 2º timeframe,
  modelosUtilizados obrigatório).
- Metering: cota checada ANTES; consumida POR chamada bem-sucedida; cache
  não gasta. Estimate mostra chamadas novas antes de rodar (UI da Fase 2).

### 1.2 N2 · 5 famílias
- `indicators.adx()` (Wilder) + DI± integrados a compute/summary (adxState).
- `technical_models._candle_patterns`: engolfo ±, martelo, estrela cadente,
  doji (determinístico, rótulos descritivos).
- `build_context` ganhou `families` (leitura por família + confluência ENTRE
  famílias com síntese) e `dataQuality` (contrato da skill: serieCurta,
  volumeAusente, multiTimeframe=false → tetoConfianca).
- Prompt estruturado (N2) instruído a usar families/dataQuality e a terminar
  o corpo com "## Modelos utilizados".

### 1.3 N3 · alvo & stop
- `carteira_stopalvo` monta contexto técnico explícito (ATR14, suportes/
  resistências, bandas, viés, mín/máx locais, referências, dataQuality) e o
  injeta em `analyze_carteira(tech_context=...)`.
- Resposta estendida: `cenarios[3]` conservador/moderado/agressivo com stop,
  alvo, riscoRetorno, memoriaCalculo; R:R<1,5 marcado `rrDesfavoravel`
  (regra da skill). `modelosUtilizados` incluído. Compatível com o formato
  antigo (sem cenários) — prompt configurável do usuário intacto.

### 1.4 Testes (novos)
`test_scan_deep.py` (top-N/teto/cache-dia/estimate/erro isolado) ·
`test_pipeline_n2_n3.py` (families/ADX/padrões/dataQuality/cenários) ·
`test_guardrail_imperativo.py` (varre textos fixos e prompts por verbo de
ordem; whitelista linhas de proibição declarada; sobrevenda ≠ falso positivo).

## Validação
py_compile total ✅ · **suítes backend 111/111** ✅ (httpx stubado só no
ambiente de empacote; real via requirements) · node --check ✅ · App.jsx
INALTERADO (balance n/a) · grep de wiring ✅ · guardrail anti-imperativo ✅.

## Próximos passos
1. **Alex:** aprovar/ajustar PROPOSTA-UX.md (destrava Fase 2 e M1–M6).
2. Deploy desta entrega (git push) — endpoints novos já utilizáveis via API.
3. Fase 2 (flow oportunidade→carteira) após o gate ✋ device.
4. Fase 3 (agente server-side) + F3.3b push/APNs (LIBERADA — doc própria:
   chave APNs, capability, plugin, endpoint de token).
