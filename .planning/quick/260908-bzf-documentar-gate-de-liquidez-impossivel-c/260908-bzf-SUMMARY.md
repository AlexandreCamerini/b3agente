---
quick_id: 260908-bzf
status: complete
date: 2026-09-08
tipo: documentacao-apenas
files_modified:
  - docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md
  - docs/adr/020-centralizacao-de-dados-no-mydata.md
  - .planning/STATE.md
---

# Summary — 260908-bzf

## O que foi entregue

Documentação de um achado medido, sem nenhuma mudança de código.

1. **`docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`** (novo) — a medição
   contra produção ao vivo: tabela do gate por ticker, cadeia completa do
   PETR4 com scores contrato a contrato, a aritmética que produz o teto de 35,
   a tabela de volume mínimo por faixa de spread (com as duas faixas
   impossíveis), as três opções de recalibração com seus custos, os comandos
   para reproduzir, e a nota sobre docs desatualizados.

2. **`docs/adr/020-...md`** — adendo datado fechando o follow-up do
   `openInterest`, que estava aberto desde a migração. Texto original intocado.

3. **`.planning/STATE.md`** — blocker em Blockers/Concerns + linha na tabela de
   Quick Tasks.

## O achado

Produção roda `B3_OPTIONS_PROVIDER=mydata`. O provedor responde
(`providerStatus: "ok"`), mas o gate de liquidez reprova quase tudo:

| ticker | `liquida` |
|---|---|
| ABEV3 | false |
| PETR4 | false |
| VALE3 | true (42,0 — raspando) |
| ITUB4 | false |

Os 60 contratos de PETR4 empatam em `liquidity_score = 35,0` contra corte 40.
O melhor tem 88.100 unidades negociadas e é classificado como ilíquido.

Causa: duas parcelas do score se perdem. O `oi_score` (até 40 pontos) some
porque o COTAHIST não publica open interest, e a penalidade de spread cai no
padrão 25 ("desconhecido") porque o livro chega com um lado zerado. Sobra o
teto de volume, 35 pontos — **impossível cruzar 40 em qualquer volume**.

## Onde eu errei antes de acertar

A primeira investigação presumiu `B3_OPTIONS_PROVIDER=yahoo`, a partir do
default do código (`options_provider.py`) e de quatro documentos que ainda
afirmam que yahoo é "o default de produção" (ADR-021, ADR-022,
`OPERACAO-ciclo-de-vida-put.md`, `OPERACAO-ponte-gatilho-put.md`). Testei o
Yahoo, ele devolveu cadeia vazia para todo ticker da B3, e a explicação
fechava — mas media um caminho que produção não usa. O Alex corrigiu.

A lição registrada no documento: sobre o que cada environment roda, a fonte de
verdade é a tabela de configuração em `STAGING.md` (medida no ato de duplicar o
environment), não o default do código nem ADRs que descrevem a época em que
foram escritos.

## O que NÃO foi feito, deliberadamente

Nenhuma alteração em `options_quant.py`, no corte de 40, ou no adaptador do
mydata. Decisão do Alex entre quatro opções apresentadas: **"só documentar por
enquanto"**. Recalibrar o gate muda o que o app afirma sobre liquidez, e
afrouxá-lo faria um simulador educacional propor estrutura sobre opção
genuinamente fina — decisão de produto, não de implementação.

## Validação

Documentação apenas — nenhum arquivo de código ou teste tocado, logo a suíte
não é afetada (a última execução completa nesta branch, em `F10-20260908-01`,
mediu 2049 passed / 1 skipped).

A medição é reproduzível pelos comandos publicados no documento; as duas rotas
usadas (`/api/options/gate/{t}` e `/api/options/chain/{t}`) são públicas, sem
credencial.
