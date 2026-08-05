# ADR-006: A camada de entendimento é backend-first e determinística

**Status:** Aceito
**Data:** 2026-08-05
**Base:** `CHECKOUT-Didatica-Estudo-otimizado.md`, `docs/didatica-inventario.md`,
revisão sênior de aplicativos financeiros (5 rodadas).

---

## Contexto

O caso que originou: o card diz *"◔ PLANO ARMADO · a 0,9R do gatilho"*. Quem
nunca operou não sabe o que é gatilho, o que acontece quando é atingido, nem o
que "0,9R" significa. A pergunta chegou do próprio Alex, olhando a tela.

O inventário (`docs/didatica-inventario.md`) contou **dezoito** afirmações num
único card, a maioria em jargão. E localizou a lacuna com precisão: já existe
didática para o que a **LLM escreve** (`skill_ref.DIDATICA` manda a análise
ensinar a cadeia indicador → correlação → decisão). Não existia nenhuma para o
que o **app afirma sozinho** — timing, confluência, R, fundamento e régua de
risco são determinísticos, nenhuma LLM os produziu, então nenhuma LLM os
explicava.

---

## Decisão

**1. O texto didático é determinístico e mora no backend** (`conceitos.py`),
no mesmo padrão de `skill_ref.TIMING`: o servidor devolve a frase pronta, o
front nunca compõe vocabulário.

**2. Custo zero no caminho padrão.** Nenhuma chamada de LLM em nenhum caminho
de `conceitos.py`. A camada paga (assistente, ADR-007) é outra e é opt-in.

**3. Rotas NOVAS, `/api/timing` intocado.** A spec sugeria embutir o conceito
na resposta existente. Não foi feito: rota nova não muda rota velha, e assim
"o payload do Operador é idêntico ao de hoje" vira **fato estrutural** em vez
de promessa a ser testada. O guardião congela o conjunto de chaves de
`/api/timing` e falha se qualquer campo vazar, nos dois modos.

**4. Ancorado no dado em exibição, com descarte em vez de estimativa.** Cada
parágrafo pode citar `{campos}` do card. Campo ausente **derruba o parágrafo
inteiro** — nunca aparece com lacuna nem com número inventado (Princípio 1).

**5. `campos` é allowlist, não documentação.** Só as chaves declaradas entram
na interpolação, e os rótulos do modo são aplicados **depois** delas. Sem isso,
um chamador que mandasse `{"rotuloAtingido": "COMPRE AGORA"}` reescreveria o
vocabulário canônico por um dict — e o guardrail de verbo de ordem, que varre
o catálogo estático, não teria como pegar.

**6. Ordem das respostas: "o que o app NÃO faz" primeiro.** Para quem acabou de
ver "condição atingida" — ou pior, recebeu uma notificação — a primeira
pergunta é *"o app comprou alguma coisa?"*. Essa resposta não pode ser a
terceira.

**7. Duas vias de acesso.** Proativa na estreia (uma vez, uma instância só) e
permanente em um toque, para sempre, no mesmo lugar onde o termo aparece.

**8. Uma afordância só para todos os conceitos.** Dezoito interações diferentes
seriam dezoito coisas a aprender antes do conteúdo. Um gesto: tocar no "?" ao
lado do termo, alvo de 44×44 (mínimo da HIG). Os conceitos se encadeiam pelo
"veja também" **dentro da folha**, com os mesmos dados do card — o que mantém
a ancoragem e evita encher a tela de "?".

**9. Desligável por variável de ambiente.** `B3_DIDATICA_OFF=1` remove a camada
de um app **já instalado**, sem rebuild. Exercitada nos dois sentidos antes da
entrega: com a flag ligada, 0 afordâncias e 0 folhas, com os badges de timing
intactos; desligada, 5 afordâncias e alvo medido em 44×44 no DOM.

---

## Consequências

**Boas.** O Operador é imune por construção. O texto vive numa fonte só, sob o
mesmo guardrail de verbo de ordem que os prompts. O caminho de volta em
produção é uma variável, não um ciclo de TestFlight. E o encadeamento ensina a
cadeia real (gatilho → R → stop) em vez de dar definições soltas.

**Custos aceitos.** Uma chamada extra por conceito aberto (barata, sem LLM,
sem fetch). E o texto didático passa a ser conteúdo de produto: mudar um
limiar do produto exige revisar o que a explicação afirma — mitigado fazendo
os números virem da fonte canônica (`ZONA_PERSEGUICAO`, `RR_MIN`), nunca
literais.

**Modo de falha que este ADR previne.** Explicação que diz uma coisa e card
que mostra outra. Três lugares guardam o rótulo do estado (`skill_ref.TIMING`,
`conceitos.ROTULOS`, `TIMING_STYLE` no front); o espelho é travado por
`web/tests/test_vocabulario_espelho.mjs`.

---

## O que foi descartado, e por quê

- **Explicação gerada por LLM na camada padrão.** Custo por leitura e variação
  entre execuções, para um texto que não muda. A LLM entra só na pergunta
  livre (ADR-007).
- **Via proativa amarrada ao card expandido.** Era a recomendação da revisão, e
  foi implementada — até a execução mostrar que `expanded` só liga depois de
  `A.analyze`, que exige modelo de IA configurado e **custa dinheiro**. A via
  proativa ficaria inalcançável exatamente para o iniciante absoluto que ela
  atende. Substituída por eleição de instância (`_proativoDono`), que preserva
  a garantia ("uma folha, não seis") sem o pedágio.
- **Um "?" por afirmação.** Dezoito numa tela densa. Seis afordâncias + o
  encadeamento dentro da folha cobrem os sete conceitos.

---

## Defeitos que a verificação ao vivo pegou (e a revisão de código não)

Registrados porque são a justificativa de exigir verificação ao vivo por fase:

1. **`excedenteEmR` volta em DOIS estados** (`timing.py:126` esticado, `:130`
   gatilho) e eles pedem leituras **opostas**. Um parágrafo só para os dois
   dizia *"movimento esticado — não perseguir"* no instante exato em que a
   condição acabou de valer. Corrigido com parágrafos selecionados por estado.
2. **Risco por ação negativo.** Com stop no lucro (o que o trailing produz),
   `avg − stop` fica negativo e o card exibia *"1R vale R$ -4,12 por ação"* —
   número sem significado, no conceito que ensina a medir risco. Virou
   invariante de domínio: valor não-positivo não formata.
