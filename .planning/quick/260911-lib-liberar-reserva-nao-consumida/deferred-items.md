# Deferidos — quick 260911-lib

## D-01 — recusa por RATE LIMIT se apresenta como "Cota do dia esgotada"

**Descoberto em:** medição dos valores default durante a correção da reserva
(2026-09-11). **Fora do escopo desta task** (o plano cobre só a devolução da
reserva); nada foi alterado.

`_cap_check` descarta o `_motivo` do `metering.check` de propósito — o texto do
metering fala de BYOK e de "análises com a IA do app", que não é o que
acontece na aba Opções (§3.2 do PLANO). O efeito colateral é que as DUAS
recusas do `check` (cota diária estourada e rate limit de 20/min) saem com a
MESMA mensagem: `"Cota do dia da aba Opções esgotada."`

Medido com os defaults (cota 60/dia, rate 20/min), DEPOIS desta correção:

```
apos 20 leituras: usado=0 reservado=0 rl=20
primeira recusa: 21 ('mcp_cota', usado=0, limite=60)
```

A 21ª leitura em menos de um minuto é recusada legitimamente — mas pelo rate
limit, não pela cota. A resposta afirma "cota esgotada" com `usado: 0,
limite: 60` no mesmo corpo: é a mesma classe de afirmação falsa do A-08 e do
A-07, só que no eixo do motivo em vez do número. O usuário que lê isso conclui
que acabou o dia dele, quando bastava esperar alguns segundos.

**Correção sugerida (não feita):** separar os dois códigos no `_cap_check` —
`mcp_cota` (cota do dia) e `mcp_ritmo` (muitas chamadas em pouco tempo, com o
tempo de espera), mantendo o copy próprio da aba em ambos. Mexe em contrato de
resposta que a UI da aba lê, então pede decisão do dono e provavelmente
acompanha a Fase 3 do `docs/PLANO-aba-opcoes.md`.
