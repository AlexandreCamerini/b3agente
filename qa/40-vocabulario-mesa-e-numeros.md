# qa/40 — Reporte do Alex: "Estudar alta" no Operador + números inventados

> Build: **F9-20260710-13**. Dois pontos do Alex: (1) modelos PROIBIDOS de
> inventar textos ou números; (2) "continua mostrando estudar alta/baixa no
> perfil operador". Diagnóstico: eram TRÊS fontes distintas — o fix do qa/39
> (N2) estava certo, mas cobria só uma.

## Causas do "Estudar alta" na mesa

1. **Pills de `veredito` (cliente)** — o veredito do scanner é vocabulário de
   ESTUDO por construção e era renderizado cru no hero da home, na lista de
   setups da home e na linha da Watchlist, em qualquer modo. Fix: helper
   `decisaoDoModo(item, operador)` — na mesa a pill mostra a DECISÃO do plano
   determinístico (COMPRAR/VENDER/AGUARDAR CONFIRMAÇÃO/NÃO OPERAR), que o
   scan sempre anexa; no estudo, o veredito de sempre. Fallback do Radar
   blindado também (cache antigo sem plano não vaza).
2. **`/api/analyze` legado (servidor)** — o caminho da análise da aba
   Mercado era SEMPRE educacional (skill+GUARDRAILS+FORMAT fixos). Fix:
   branch por modo (GUARDRAILS_PRO/FORMAT_PRO) + re-map PRO + teto de
   convicção — piso do SERVIDOR, vale mesmo que o cliente mande skill errada.
3. **Análises antigas persistidas** — mantêm o texto da época em que foram
   geradas; reanalisar atualiza para a voz do modo. (Não é bug: análise é
   um documento datado.)

## "Modelo não inventa número" — enforcement adicionado

`kpi.parse_rich` agora SANEIA os níveis devolvidos pelo modelo: preço ≤ 0
(o "0.0" do template passava como proposta!), stop==alvo, ou geometria
incoerente com a direção declarada (alta exige alvo>stop; baixa o inverso)
⇒ níveis viram **None** ("sem dado" > número inventado). Vale para TODOS os
caminhos que passam pelo parse (N2 estruturado e legado). Complementa o
qa/39 (R:R recomputado no N3, alvo do lado certo no plano determinístico,
proibição de citar eventos fora dos dados nos prompts).

## Guardiões

- `server/tests/test_qa40.py` (3): legado fala a língua da mesa (LLM fake),
  FORMAT_PRO no system do operador, sanidade dos números (4 casos).
- `web/tests/test_decisao_modo.mjs` (6): helper existe, NENHUMA pill renderiza
  veredito cru, home+watchlist via helper, flag `operador` em escopo nas duas
  telas (pegou um ReferenceError latente durante o desenvolvimento).
- `test_modo_operador.mjs` atualizado para o novo contrato.

## Validação

**275 pytest** + web (2 ambientais) + parse OK.

## Hard stop (F9-20260710-13, MODO OPERADOR)

1. Home (hero e lista): pills mostram COMPRAR/VENDER/AGUARDAR CONFIRMAÇÃO/
   NÃO OPERAR — nunca "Estudar alta/baixa".
2. Watchlist: linha do ativo idem; botão "Plano completo" → análise nova
   responde na voz da mesa (análises ANTIGAS mantêm o texto da época —
   reanalise para atualizar).
3. Convicção nunca "Muito Alto"/"Alto".
4. Nenhuma proposta de stop/alvo com 0,00 ou geometria invertida.
