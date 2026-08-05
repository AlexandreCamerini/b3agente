# Inventário — o que o app AFIRMA sem explicar

Levantado em 2026-08-05 lendo `web/src/App.jsx`. Antecipado da Fase 3 por
recomendação da revisão sênior: é ele que decide contra qual tela o formato do
conceito deve ser calibrado. A resposta veio na primeira contagem — o card do
ativo afirma **dezoito** coisas, e a maioria em jargão.

A lacuna que este documento mapeia é específica: existe didática para o que a
**LLM escreve** (`skill_ref.DIDATICA` manda a análise ensinar a cadeia
indicador → correlação → decisão). Não existe nenhuma para o que o **app
afirma sozinho** — timing, confluência, R, fundamento, régua de risco são
determinísticos, nenhuma LLM os produziu, então nenhuma LLM os explica.

Legenda de prioridade:
**P1** — o iniciante não consegue agir sem entender, ou pode agir errado.
**P2** — dá para conviver sem entender, mas o entendimento muda a leitura.
**P3** — cosmético ou autoexplicativo.

---

## `AtivoCard` — o card do ativo (`App.jsx:2265`)

É a superfície mais densa do app e serve **Watchlist e Radar ao mesmo tempo**.
A watchlist padrão tem 6 ativos: tudo abaixo se repete seis vezes na mesma
rolagem. Isso é o que reprova qualquer explicação que apareça sozinha *na
lista* — ela apareceria seis vezes, ou uma vez por sorteio de corrida.

| # | O que afirma | Onde | P | Conceito |
|---|---|---|---|---|
| 1 | Preço e variação % do dia | topo | P3 | — |
| 2 | Mini-gráfico → "velas ⤢" | topo | P3 | — |
| 3 | `em carteira · N cotas · PM x` | resumo da posição | P2 | `precoMedio` |
| 4 | Resultado em R$ e % | resumo da posição | P2 | — |
| 5 | **Manchete**: "DECISÃO DA MESA" / "PLANO EDUCACIONAL" + veredito | 2373 | **P1** | `veredito` |
| 6 | **Estado do timing** (armado/atingido/esticado/sem dado) | `TimingBadge` | **P1** | **`gatilho`** |
| 7 | `barra 15m de HH:MM` | `TimingBadge` | **P1** | `barra15m` |
| 8 | `a 0,9R do gatilho` | `TimingBadge` | **P1** | `r` |
| 9 | Ressalva do atraso de ~15 min | `TimingBadge` | P2 | `barra15m` |
| 10 | chip `direção` | 2390 | P2 | `veredito` |
| 11 | chip `convicção` | 2391 | P2 | `conviccao` |
| 12 | chip `qualidade` | 2392 | P2 | `conviccao` |
| 13 | chip `confluência N%` | 2393 | **P1** | `confluencia` |
| 14 | chip `fundamento A/B/C` | 2394 | **P1** | `fundamento` |
| 15 | nome do melhor setup ("rompimento", "pullback"…) | 2395 | P2 | `setup` |
| 16 | **Régua** `POSIÇÃO NO RISCO` — STOP · P. MÉDIO · ALVO com % | `PlanRuler` 2420 | **P1** | `stop`, `alvo` |
| 17 | `R:R 1.8 · 12 dias · 7% do patrimônio` | 2432 | **P1** | `r`, `rr` |
| 18 | CTA condicionado à leitura ("sugestão N ações" / "Simular mesmo assim") | 2470+ | **P1** | `sizing` |

**Observação de produto, não de didática:** o item 18 já resolve bem o caso
desfavorável — troca a sugestão de quantidade por um botão discreto e uma frase
honesta. É o padrão a imitar nos demais.

---

## Demais telas

Levantamento de superfície (nomes e prioridade); o detalhe entra na Fase 3.

| Tela | Afirma sem explicar | P |
|---|---|---|
| **Radar** (`RadarScreen`, 4413) | ranking por confluência; "leitura rápida"; o que a varredura cobre e o que não cobre | P1 |
| **Portfólio** | patrimônio simulado, resultado do dia, régua por posição, R acumulado | P1 |
| **Operador IA** (`AgenteScreen`, 2999) | "Executar" × "Apenas sinalizar"; intervalo de reavaliação; que o laço só roda com conta; proteção armada com Operador desligado | **P1** — é a tela onde não entender tem consequência simulada real |
| **Eficiência da IA** | taxa de acerto, expectância em R, calibração, "n insuficiente" | P2 |
| **Perfil** | risco/horizonte/tolerância e como dimensionam o stop | P2 |

---

## Conclusões que mudam a execução

1. **`gatilho` continua o caso certo para calibrar** — é P1, aparece em todas
   as superfícies do card, e arrasta `r` e `barra15m` junto. Calibrar contra
   ele já exercita "conceito que cita outro conceito".
2. **A via proativa não pode viver na lista.** Seis cards, um `conceitosVistos`
   global: ou aparece seis vezes ou vira corrida. Ela vive numa instância só —
   o card expandido — e na lista fica apenas a afordância permanente.
3. **Nada cabe no fluxo vertical do card.** O `TimingBadge` já ocupa três
   linhas dentro de um card que ainda carrega régua, camada de opções e CTA. A
   explicação abre **sobre** o card (folha), não dentro dele.
4. **Uma afordância só para todos os conceitos.** Dezoito afirmações não
   comportam dezoito interações diferentes. Um mesmo gesto — tocar no rótulo —
   serve os dezoito.
5. **O Operador IA é a próxima prioridade depois do card**, não o Radar: é a
   única tela onde não entender produz consequência (na carteira simulada).

---

## Por que são 6 afordâncias para 7 conceitos

`alvo` **não tem "?" próprio, de propósito.** Ele nunca aparece sozinho no
card: vive na régua, ao lado do stop, e faz sentido justamente em relação a
ele (é a razão entre os dois que decide se o plano compensa). Um sétimo "?"
colado ali seria a densidade que a conclusão 3 manda evitar. O acesso a `alvo`
vem pelo "veja também" de `stop` e de `r` — que é como esses três se explicam
de qualquer forma.

Exceção: quando a posição tem alvo e **não** tem stop, a régua ainda aparece;
aí a afordância da régua vira `alvo`, porque sem stop não há de onde encadear.
