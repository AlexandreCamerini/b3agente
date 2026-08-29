# Requirements: Boris+ (b3-agente) — v1.3 Cap comercial (plano gratuito)

**Defined:** 2026-08-29
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.

## v1 Requirements

Ativar de verdade os limites do plano gratuito que o ADR-010 já desenhou tecnicamente. Sem loja/IAP neste milestone — `PLAN_PRO` continua ilimitado.

### Limites do gratuito

- [x] **CAP-01**: Usuário no plano gratuito não consegue ter mais de 10 ativos na watchlist — ação de adicionar é recusada com o motivo exato
- [x] **CAP-02**: Usuário no plano gratuito não consegue pedir mais de 30 análises de IA no mês corrente — ação é recusada com o motivo exato
- [x] **CAP-03**: A contagem mensal de análises usada pelo gate de plano vem do ledger real de `metering.py` — nunca de um contador paralelo (contrato C-33)
- [x] **CAP-04**: Usuário no plano pago (pro) não sofre nenhum desses dois limites
- [x] **CAP-05**: Ao atingir qualquer limite, o resto do app continua funcionando normalmente — só a ação específica é recusada

### Interface

- [ ] **CAP-06**: Usuário vê o número real de uso/limite na tela (ex.: "análises deste mês: 12/30", "ativos: 7/10") — nunca estimado ou escondido
- [x] **CAP-07**: Mensagem de limite atingido nunca usa linguagem de upgrade urgente/enriquecimento rápido (princípio 8 do CLAUDE.md) — só o fato e o motivo

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Monetização (loja/IAP)

- **CAP-08**: Compra/assinatura do plano pago via App Store IAP / Google Play, com validação de recibo server-side (`requires_subscription`)
- **CAP-09**: Preço e moeda definidos e exibidos na UI

### Diferenciais do plano pago

- **CAP-10**: IA gerenciada pelo app sem exigir chave própria (BYOK), com cota mais folgada que o teto admin de hoje
- **CAP-11**: Alvo dinâmico (F3) exclusivo do plano pago (hoje opt-in gratuito)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Loja/IAP e validação de recibo | Decisão comercial maior (App Store + Google Play), fora do escopo desta ativação — v2 |
| Ajuste de intervalo de atualização de cotação como feature paga | ADR-010 registra como pergunta em aberto, não decisão — exigiria repensar orçamento por-usuário vs. por-app |
| Fonte de dado (brapi/Yahoo) como diferencial de plano | Rejeitado explicitamente no ADR-010 decisão 3 — infraestrutura é igual pra todo mundo |
| Recorte de eficiência por regime de mercado como feature paga | qa/44 Fase B2 ainda não tem amostra suficiente |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAP-01 | Phase 12 | Complete |
| CAP-02 | Phase 12 | Complete |
| CAP-03 | Phase 12 | Complete |
| CAP-04 | Phase 12 | Complete |
| CAP-05 | Phase 12 | Complete |
| CAP-06 | Phase 13 | Pending |
| CAP-07 | Phase 12 | Complete |
