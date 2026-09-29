# Phase 44: Motor — estrutura por ativo - Discussion Log

> **Audit trail only.** Decisões estão em 44-CONTEXT.md.

**Date:** 2026-09-29
**Areas discussed:** Contrato da API, Marcação do prêmio, Motivos e casos de borda
(Não discutida: Estados e limiares → Claude's Discretion)

## Contrato da API
- Onde sai: **módulo novo + campo aditivo `estrutura`** (alt.: rota nova por ativo; rota de lista de todas)
- iOS: **só servidor** (alt.: espelho JS; verificar antes)

## Marcação do prêmio
- Preço da perna: **lado que fecha (ask p/ vendida, bid p/ comprada; fallback last carimbado)** (alt.: mid; last)
- Perna sem cotação: **total null + parcial exposto** (alt.: só a perna null)

## Motivos e casos de borda
- Alias sem_setup: **chaves e frases próprias** (alt.: só no payload novo)
- Gate/encerrar: **estado explícito `aberta_sem_proposta` + bloqueio com motivo** (alt.: reusar "degradado")
- Vencimentos divergentes: **faixa null + motivo** (alt.: faixa na perna mais curta)
- Qtd opção ≠ ações: **faixa só na parte coberta + flag descoberta** (alt.: null se não casar)

## Claude's Discretion
Limiar de exercício provável, janela ≤5 dias, precedência de estados, nomes de campos e formato das frases.

## Deferred Ideas
Quick task de textos de vazio; espelho JS offline.
