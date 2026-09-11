---
quick_id: 260911-ctd
phase: quick-260911-ctd
plan: 01
type: quick
wave: 1
depends_on: [260911-cf1]
files_modified: [server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py]
autonomous: true
---

<objective>
**Quinta e última ocorrência** da família do `qty` falsy, achada pelo executor
da quick 260911-cf1 enquanto corrigia a quarta. Em
`server/app/main.py:2854` (`POST /api/options/lastreada/fechar`):

```python
contratos_n = int(contratos_body) if isinstance(contratos_body, (int, float)) and contratos_body > 0 else None
```

`contratos: 0`, `-3` e `"abc"` caem TODOS em `None`, que nesta rota significa
**fechar a operação lastreada inteira**.
</objective>

<context>
**Pior que as quatro anteriores em dois aspectos:**

1. O `isinstance` engole o não numérico em silêncio. Nas outras rotas `"abc"`
   ao menos explodia (500 feio, mas visível); aqui vira fechamento total sem
   ruído nenhum.
2. **A tela MANDA esse campo.** `web/src/App.jsx:3529` chama
   `A.fecharLastreada({ contractSymbol: p.contractSymbol, contratos: p.contratos })`.
   Se `p.contratos` vier `0`/`undefined` por qualquer caminho da proposta, o
   usuário fecha tudo achando que fecha parte. As quatro anteriores eram só
   alcançáveis por chamada direta à API.

Família já fechada: `/api/sell` (F10-20260819), `/api/buy` (A-00),
`/api/options/buy` (A-00b), `/api/options/sell` (D-1, quick 260911-cf1).

A rota tem DOIS ramos que consomem `contratos_n` (`main.py:2856-2859`):
`side == "vendida"` → `store.fechar_call_coberta(..., contratos=contratos_n)`;
`side == "comprada"` → `qty = contratos_n * 100 if contratos_n else None` e
`store.sell_option(..., qty=qty)`. **Os dois precisam da guarda**, e o segundo
tem um `if contratos_n` que é outro falsy esperando — cuide dele também.
</context>

<tasks>
<task type="auto">
  <name>Task 1: fechar lastreada distingue ausente de inválido</name>
  <files>server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py</files>
  <action>
  Espelhar o padrão já aplicado quatro vezes:
  - `contratos` AUSENTE (`None`) continua significando fechar TUDO — contrato
    atual, a tela depende; PRESERVE e trave em teste;
  - ZERO, NEGATIVO ou não numérico → 400 `"Quantidade inválida."` (mesma
    string das outras quatro; sem variante nova);
  - rejeição de conta logada grava no histórico no padrão que a rota já usa
    (confira o `tipo` que ela usa hoje e siga; não invente).
  Comentário de decisão citando que esta é a QUINTA e última da família, com
  ponteiro para F10-20260819 (a origem) e para a quick 260911-cf1 (a quarta),
  e nomeando o agravante: aqui a tela manda o campo.

  Cuidado com o ramo `comprada`: `qty = contratos_n * 100 if contratos_n else None`
  é o MESMO padrão falsy. Depois da guarda, `contratos_n` só pode ser `None`
  (ausente = tudo) ou inteiro positivo, então o `if` pode virar
  `is not None` — verifique e ajuste, senão a guarda nova fica meia.

  Testes em `test_fase5_rejeicao_rotas.py`, para os DOIS ramos (`vendida` e
  `comprada`): zero → 400 **e posição intacta**; negativo → 400; `"abc"` → 400
  (não 200, não 500); ausente → continua fechando tudo (guardião do contrato,
  tem de passar nos dois lados da prova). Tabela do docstring atualizada.
  </action>
  <verify>
  RED/GREEN obrigatório contra o código de ANTES (`git show HEAD:server/app/main.py`
  para arquivo temporário FORA do repo — NUNCA `git stash`): provar que
  `contratos: "abc"` fechava TUDO silenciosamente, nos dois ramos.
  Depois: `bash scripts/executar.sh --testes`.
  </verify>
  <done>Nenhuma entrada inválida fecha operação; ausente continua fechando tudo.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. Front NÃO é editado. Deploy só-backend — NÃO fazer.
Com esta entrega a família inteira (5 rotas) tem a mesma guarda e a mesma
mensagem.
</success_criteria>
