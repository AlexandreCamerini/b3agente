# 43-05 — Checkpoint humano (preparação automática feita)

Data: 2026-09-27. Planos 43-01..43-04 completos e commitados localmente em `v2/interacao-estrutural` (sem push).

## Preparação automática (Task 1, itens a–d)

| Item | Resultado |
|---|---|
| a. `bash scripts/executar.sh --testes` (fora do sandbox) | exit 0 — **3060 pytest passed / 5 skipped / 3 xfailed + 171/171 `.mjs`** (baseline Fase 42: 3050 + 168) |
| b. `npx vite build` + `npx cap copy ios` | exit 0 / exit 0 |
| c. Motor (`setups/kpi/signal_ledger/regime` + testes deles) desde `bf7bd84` | diff vazio |
| d. App local (API :8787 + Vite :5174, viewport 375px) | no ar |

**D-18, área de toque do fundamento.** O ambiente local não tem dado de fundamento, então o chip não renderiza aqui. A medida foi feita no chip irmão da mesma receita (`SinalChip peso="contexto"`, "REGIME LATERAL"), que renderiza com 24px de altura e padding 4px 8px. Com o `SetorAlvo` de fundamento (padding `SP[3]`/`SP[2]` = 12px/8px), a caixa de toque fica em **48px de altura** × (largura do chip + 16px). O chip mantém o rótulo "FUNDAMENTO" + valor na `LinhaContexto` (a D-17 tirou o rótulo só da `FundamentoTabela`), então a largura passa de 100px. A ressalva de ~43px de largura do `43-VERIFICATION.md` supunha um chip só com o glifo A/B/C: **resolvida**.

**Verificação independente** (`43-VERIFICATION.md`): 5/5 critérios de código verificados (guardrail CVM, microtexto com paridade byte a byte, SP sem px solto, guardiões com nota, motor intocado). O único item `human_needed` era a D-18, resolvida acima.

**Observação de dado real (não é bug):** vários ativos locais estão em "amostra insuficiente" com `nJanela = 0` (0 ocorrências na janela 2025) e `n` total de 109 a 352. A frase no Operador fica "Critérios ok · amostra insuficiente (n=0 — pouco para medir)": o 0 é real, não um null virando 0. A frase não cita a janela nem o n total.

## Roteiro e DPs
Texto exato em `43-05-PLAN.md`, Task 1. Resposta esperada: "aprovado" com DP-1, DP-2 e DP-3 respondidas por nome.
