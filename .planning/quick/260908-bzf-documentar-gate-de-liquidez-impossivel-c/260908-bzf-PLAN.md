---
quick_id: 260908-bzf
description: documentar gate de liquidez impossivel com mydata sem open interest
date: 2026-09-08
status: complete
tipo: documentacao-apenas
---

# Quick 260908-bzf — documentar o gate de liquidez impossível com mydata

## Origem

O Alex reportou que a tira "Oportunidades de opções" não aparece no Portfólio.
A investigação começou errada — presumi `B3_OPTIONS_PROVIDER=yahoo` a partir do
default do código e de ADRs desatualizados (021/022, `OPERACAO-*`), e testei
uma fonte que produção não usa. O Alex corrigiu: produção roda `mydata`. A
tabela de configuração em `STAGING.md` confirma.

## Achado (medido, não estimado)

Contra produção ao vivo, rotas públicas sem autenticação:

- `GET /api/options/gate/{t}` — ABEV3 `false`, PETR4 `false`, VALE3 `true`,
  ITUB4 `false`; `providerStatus: "ok"` em todos (a fonte responde; quem
  reprova é o gate).
- `GET /api/options/chain/PETR4` — os 60 contratos empatam em
  `liquidity_score = 35,0` contra corte 40. O melhor tem 88.100 unidades
  negociadas.

Causa: `oi_score` some (mydata grava `openInterest: None` fixo,
`options_provider_mydata.py:107` — COTAHIST não publica) e a penalidade de
spread cai no padrão 25 ("desconhecido") porque o livro chega com um lado
zerado. Teto resultante 35 < corte 40 — **impossível em qualquer volume**.

ADR-020 previu o risco e o deixou aberto ("achado registrado para o checkpoint
de virada, não corrigido nesta fase"). A virada aconteceu, o acompanhamento
não.

## Escopo — DOCUMENTAÇÃO APENAS

Decisão do Alex entre quatro opções: **"só documentar por enquanto"**.
Nenhuma mudança de código, de calibração do score ou do corte. Recalibrar o
gate muda o que o app afirma sobre liquidez — é decisão de produto, adiada
deliberadamente.

## Tasks

1. **`docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`** (novo) — a medição
   completa: tabela do gate, cadeia do PETR4, a aritmética do teto, a faixa de
   impossibilidade, as três opções de recalibração com custos, como reproduzir,
   e a nota sobre os docs desatualizados que dizem "yahoo é o default de
   produção". Segue o padrão de nome de `docs/MEDICAO-Mydata-2026-08-27.md`.

2. **`docs/adr/020-centralizacao-de-dados-no-mydata.md`** — adendo datado
   fechando o follow-up do `openInterest`. Texto original intocado (ADR
   registra decisão da época; adendo não reescreve histórico).

3. **`.planning/STATE.md`** — entrada em Blockers/Concerns + linha na tabela
   de Quick Tasks.

## Por que sem planner/executor

Todos os fatos vieram de medição feita nesta sessão contra produção. Um
subagente só os transcreveria relendo o mesmo código, a um custo
desproporcional para um trabalho sem código. Garantias do GSD preservadas:
artefato de plano, SUMMARY, commit atômico, STATE.md.

## Critério de aceite

- Um leitor futuro consegue reproduzir a medição pelos comandos do documento.
- O follow-up do ADR-020 deixa de estar em aberto.
- Nenhum arquivo em `server/app/` ou `web/src/` modificado.
