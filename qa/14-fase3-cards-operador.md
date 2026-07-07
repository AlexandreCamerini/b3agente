# QA 14 — FASE 3: Cards (mock v2 aprovado) + Operador IA instrumentado

Data: 06/07/2026 · Escopo: `web/src/App.jsx`, `web/src/api.js`, `web/src/persistence.js`,
`server/app/agent.py`, `server/app/main.py` · Testes: `server/tests/test_fase3_operador.py`

---

## Parte A — Os 3 cards (mock v2 aprovado pelo Alex)

Anatomia unificada **header → leitura → dados → ações**; azul só em interativo;
verde/vermelho só sinal; números em fonte mono. Componentes novos de módulo:
`PlanRuler` (régua universal do plano/risco), `PosPill` ("no portfólio · qtd" —
regra global em qualquer card com posição) e `comprasDaPosicao(history, t)`.

**Radar** — pill de posição no header; régua "PLANO DO SETUP (didático)"
(invalidação → gatilho → alvo, com o ponto "agora") quando o melhor setup traz
os 3 níveis; chips de condições truncados em 3 (+N expande os critérios); saiu
o botão "Análise completa" e entrou **"+ Watchlist"** (já na lista → "✓ Na
watchlist" quieto). Ação nova global: `A.addToWatchlist(t)` adiciona sem
navegar e dá flash.

**Watchlist** — pill de posição no header (o badge "em carteira" antigo saiu);
uma única ação-bloco de compra (o CTA contextual C1 pós-análise continua; sem
análise, "Simular compra…" neutro); ações secundárias viraram **linha de
links**: ✨ Analisar/Reanalisar · 📈 Indicadores · Ver análise ▾.

**Portfólio** — PM na sublinha do header; as 4 células viraram a régua
"POSIÇÃO NO RISCO" (stop → P. MÉDIO/agora → alvo, com −%/+% e CTA "definir ▸"
quando faltar nível); bloco novo **"Compras desta posição (N)"** com cada
COMPRA (data · qtd × preço · total) e a memória do PM (Σvalor ÷ Σcotas;
lembrete de que venda parcial não altera PM) — a lista reinicia quando a
posição zera; ações-bloco [📈 Stop/alvo (IA)] [Simular venda…]; linha de links
[✎ Editar stop/alvo · Reanalisar · Histórico de análises (N)]; os inputs de
stop/alvo agora só aparecem com "✎ Editar" ativo (salvam no blur e a régua
reflete na hora).

## Parte B — Operador IA: diagnóstico do timeout e correções

Causa raiz em 3 pontos, todos corrigidos:

1. **`POST /api/agent/run-now` rodava o ciclo INTEIRO dentro da request.** Com
   o Yahoo rate-limitado no Railway (causa recorrente conhecida), o fallback
   1-a-1 + retries estoura os 15s do cliente ⇒ timeout determinístico.
   **Fix:** o endpoint dispara o ciclo em background (`asyncio.create_task`) e
   responde na hora; o resultado entra no Diário.
2. **Estado fantasma na ativação.** Timeout em `putAgent` caía na fila
   otimista do sync ⇒ a UI mostrava "ligado" sem o servidor ter ligado.
   **Fix:** `serverEnabled` agora vai por `sync.live` (sem fila/otimista): ou
   o servidor confirma, ou o erro aparece; a UI mostra "confirmando…" e o selo
   "✓ confirmado no servidor" vem do `GET /api/agent/status`
   (`meuServerEnabled`).
3. **Falta de observabilidade.** Nada dizia o que rodou, quanto demorou ou por
   que falhou. **Fix:** `run_cycle_for` instrumentado (guard de sobreposição,
   duração, origem manual/agendado, erro SEMPRE logado como `kind=error`,
   aviso "SEM cotação: … provável rate-limit"); anel `RUN_HISTORY` com as
   últimas 12 passadas do scheduler + `proximaPassadaEmS` no status; novo
   `GET /api/agent/log` (Diário, por usuário); middleware marca `[slow]`
   requests >2s nos logs do Railway (mostra QUEM segurou o servidor quando
   alguém vê timeout).

UI do Operador: toggle com confirmação; status enriquecido (duração da última
passada, próxima passada, erro do último ciclo); card **DIÁRIO DO OPERADOR**
(timeline do log do servidor, poll 15s, fallback local sem conta) + mini-lista
PASSADAS DO SCHEDULER; "Rodar ciclo agora" responde na hora e o Diário
atualiza em 3s/10s. O card antigo "REGISTRO DO AGENTE" foi desativado
(substituído pelo Diário).

## Validação executada

- `python3 -m py_compile app/*.py` OK; **21 suítes backend OK** (4 [X] apenas
  por `httpx` ausente no sandbox — passam no pytest completo).
- `test_fase3_operador.py`: **6/6** (status, duração/origem no Diário, erro →
  log, guard de sobreposição, anel do scheduler, aviso SEM cotação).
- Web: **9/9 suítes .mjs**, `node --check` em api/persistence/sync,
  parse Babel do `App.jsx` OK, greps de wiring OK.

## Roteiro do hard stop (iPhone físico + Railway)

1. **Radar:** varrer; num card com setup ver a régua do plano com "agora";
   tocar "+ Watchlist" → flash + botão vira "✓ Na watchlist"; num ativo com
   posição, ver a pill "no portfólio · qtd".
2. **Watchlist:** card com 1 ação de compra + linha de links; pill de
   quantidade quando houver posição; análise/indicadores pelos links.
3. **Portfólio:** régua POSIÇÃO NO RISCO com stop/alvo e "agora"; "✎ definir
   stop" quando faltar; abrir "Compras desta posição" e conferir a memória do
   PM; editar stop pelo "✎ Editar" e ver a régua refletir.
4. **Operador (o bug):** ligar "Agente no servidor" → "confirmando…" →
   flash "ATIVADO ✓" + selo "✓ confirmado no servidor". Se falhar, a mensagem
   explica e os logs do Railway mostram `[slow]` no culpado.
5. **Rodar ciclo agora** → resposta imediata ("ciclo iniciado…") e, em ~10s,
   a passada aparece no Diário com duração; sem cotação (rate-limit), o aviso
   diagnóstico aparece no Diário em vez de sumir.
6. **Railway:** `railway logs` → conferir linhas `[req]`/`[slow]` e
   `[agent]…` durante o teste.

---

## Correções pós-hard-stop (06/07/2026)

Quatro problemas relatados pelo Alex após o teste no aparelho, todos corrigidos:

**1) Botão "Simular venda" do Portfólio não funcionava.** Bug real (pré-existente,
sobrevivente ao refactor): o botão chamava `ctx.openSell(t)`, mas `openSell` só
existe dentro de `A` (o objeto de ações), não em `ctx` diretamente — a chamada
lançava erro e nada abria. Corrigido para `ctx.A.openSell(t)`, no mesmo padrão
já usado por `addToWatchlist`.

**2) Formatação das análises do Radar (Leitura da IA).** Os campos estruturados
do N1 (resumo, leitura de cada setup, cenários, riscos, invalidação) eram
renderizados como texto cru — quando a IA usa `**negrito**` para destacar um
nível ou termo, o usuário via os asteriscos literais em vez do destaque. Todos
os campos passaram a usar `MdInline` (o mesmo parser inline já usado no resto
do app), incluindo os "Fatos relevantes" da análise da Watchlist, por
consistência.

**3) Observabilidade do push não funcionava.** `push.send_to_user` devolvia só
um `int` (quantos aceitos) — o servidor não sabia DISTINGUIR "APNs não
configurado" de "sem token registrado" de "token(s) rejeitado(s) pela Apple",
então toda falha virava a mesma mensagem genérica, e nada era gravado no
Diário. Agora `send_to_user` devolve um diagnóstico completo
(`{sent, total, detalhes}`), e tanto `POST /api/push/register-token` quanto
`POST /api/push/test` gravam no Diário (`agentLog`) o resultado exato de cada
tentativa — inclusive qual token foi rejeitado e por qual motivo HTTP/reason
da Apple. Testes: `test_push_send_to_user_sem_configuracao_e_diagnostico`,
`test_push_sem_token_registrado`.

**4) Observabilidade movida para o Perfil + duplicação do Operador IA removida.**
O card de status detalhado + Diário + "Rodar ciclo agora"/"Testar push agora"
saiu da aba Operador IA e virou uma tela própria (`ObservabilidadeScreen`),
acessada por Perfil → **Observabilidade** — que substituiu o antigo drill
"Agente autônomo" (esse apontava para a MESMA tela do Operador IA, duplicando
a aba principal). A aba Operador IA agora só tem configuração (toggle com
confirmação, modo, regras, tetos, ativar push do aparelho); o Diário e os
testes de diagnóstico moraram para Observabilidade.

Regressão: 22 suítes backend OK (test_fase3_operador.py agora 8/8) + 9 suítes
web OK + parse do App.jsx OK.
