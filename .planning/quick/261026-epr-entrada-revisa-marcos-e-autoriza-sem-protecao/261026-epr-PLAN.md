---
phase: quick-261026-epr
plan: 01
type: execute
wave: 1
depends_on: [quick-261023-msp]
files_modified:
  - server/app/marcos_servico.py
  - server/app/main.py
  - server/app/skill_ref.py
  - web/src/copy.js
  - web/src/api.js
  - web/src/persistence.js
  - web/src/App.jsx
  - server/tests/test_marcos_compra.py (novo)
  - web/tests/test_vocabulario_espelho.mjs
  - web/tests/test_marcos_compra_ui.mjs (novo)
autonomous: true
---

# Quick 261026-epr: a entrada revisa os marcos no preço atual e permite comprar sem stop e alvo com autorização explícita

## Contexto

Pedido do Alex em 2026-10-26, com captura do BBDC3 no iPhone:

> "Entender por que não consigo realizar a entrada no ativo. Temos que ter a possibilidade de rever os valores de acordo com os valores atuais do mercado e possibilitar a entrada no ativo sem o stop e alvo com a autorização do usuário."

Diagnóstico do orquestrador:
- O `BuyModal` (App.jsx ~9337) não bloqueia: ele só exige caixa e cotação. `POST /api/buy` executa compra manual mesmo sem marcos (D-06 esclarecida).
- O que trava a percepção é o fluxo pós-compra: `confirmBuy` abre o `StopAlvoModal`. Na produção atual (F10-20261022-01, sem a quick 261023-msp) o motor recusa por "teto próximo" e o "Aplicar" falha.
- O usuário nunca vê a proteção antes de comprar e não tem como recusá-la conscientemente.
- A queda de 26/10 (BBDC3 18,06 → 14,22) é real nas duas fontes (brapi e Yahoo). Não é bug de dado.

Já em `main` (261023-msp, não publicado):
- `marcos_para_posicao` usa a precedência: gravado > plano do setup do card > suporte com alvo de 1,5R.
- Posição aberta nunca recusa por R:R.

## Guardrails (CLAUDE.md)

- Número de stop e alvo sai SÓ do servidor (motor). O cliente manda no máximo flags: nunca stop, alvo, gatilho ou invalidação (T-50-13).
- Paridade `deviceStore` ↔ `serverStore` e `skill_ref` ↔ `copy.js`.
- O front não compõe vocabulário (skill didatica-boris).
- Guardiões não se apagam.

## Tarefa 1: fonte única dos marcos de COMPRA (servidor)

Em `server/app/marcos_servico.py`, criar `marcos_para_compra(snap, setup_nome, preco)`. É a fonte única do que uma compra manual grava e do que a prévia mostra.

1. Se há `setup_nome` (e o lado não é baixa): `marcos_de_setup(snap, setup_nome, preco)`. Se for válido, aplicar `setups.revalidar_na_execucao(stop, alvo, preco, gatilho, invalidacao)`; se `ok`, devolver esses marcos (`fonte: "setup"`, rr do rv).
2. Senão: `marcos_para_posicao(snap, preco, avg=preco, pos=None)`. Se for válido, aplicar `revalidar_na_execucao(stop, alvo, preco)` (sem gatilho); se `ok`, devolver esses marcos, preservando `fonte`/`parecer`. Quando o setup falhou no passo 1, acrescentar ao `parecer` o motivo do setup.
3. Nada serviu: devolver `valido: False` com o motivo (do setup, se houve; senão o da posição).

Em `server/app/main.py`, `POST /api/buy` (~2900-2950) passa a ler `body.get("protecao")`:
- `"sem"`: autorização explícita do usuário.
  - `marcos=None`; não calcula nada.
  - `marcos_texto = skill_ref.marcos_plano_txt(modo, "compra_sem_marcos_autorizada", ticker=t)`.
  - Vale também para o caminho de ordem pendente.
- `"motor"`: usa `marcos_para_compra(snap_m, setup_nome or None, price)`. Válido → grava, como hoje. Inválido → executa sem marcos com `compra_sem_marcos` + motivo, como hoje (compra manual nunca é recusada por plano).
- Ausente ou outro valor: comportamento ATUAL intacto (só o caminho de setup), por compatibilidade com builds antigos do app.

Em `POST /api/marcos/{t}`:
- Com `body.compra is True`, devolve `marcos_para_compra(snap, setup, preco)`. É a prévia; o `preco` do corpo continua só referência de cálculo, como hoje.
- Com `body.recalcular is True` (sem `compra`), chama `marcos_para_posicao(..., pos=None)`, que ignora o gravado e mantém o `avg` do servidor. Isso é "rever no preço atual" para posição aberta.

Pendentes (`pending_orders.criar_compra` / `executar_pendentes`): recebem os mesmos `marcos` do novo caminho. A revalidação na execução já existe; conferir que `gatilho`/`invalidacao` ausentes não quebram nada.

Guardiões pytest em `server/tests/test_marcos_compra.py`:
- prévia (`/api/marcos` com `compra:true`) e compra (`/api/buy` com `protecao:"motor"`) gravam os MESMOS stop/alvo no mesmo snapshot;
- `protecao:"sem"` executa sem marcos, mesmo com setup válido, e devolve o texto autorizado;
- sem `protecao`, o comportamento antigo se mantém;
- `recalcular:true` ignora o gravado.

Seguir os padrões de `tests/test_marcos_rotas.py`: stubs de snapshot/quote, sem rede.

## Tarefa 2: vocabulário (skill_ref ↔ copy.js, dois modos, guardião de espelho)

Chaves novas em `MARCOS_PLANO` (texto de estudo didático; texto do operador curto, de mesa):
- `compra_previa_titulo`: título da prévia no BuyModal (ex.: "PROTEÇÃO DO MOTOR NESTA ENTRADA").
- `compra_previa_recalcular`: botão (ex.: "Recalcular com o preço atual").
- `compra_gravar_protecao`: opção marcada por padrão (ex.: "Gravar este stop e alvo na compra").
- `compra_sem_protecao_check`: autorização explícita. Ex. operador: "Entrar sem stop e alvo — a posição fica sem proteção automática até eu definir." Ex. estudo: explicação clara do risco, sem infantilizar.
- `compra_sem_protecao_motivo`: prefixo quando o motor não traçou proteção (ex.: "O motor não traçou proteção agora:").
- `compra_sem_marcos_autorizada`: texto do servidor com `{ticker}` (ex.: "{ticker} comprado sem stop e alvo, por sua escolha. Defina a proteção quando quiser no card.").
- `modal_recalcular`: botão no `StopAlvoModal` (ex.: "Recalcular com o preço atual").

Sem literal de R:R mínimo (guardião `test_rr_min_fonte_unica.mjs`). Acrescentar as chaves à lista de `MARCOS_PLANO` em `web/tests/test_vocabulario_espelho.mjs`.

## Tarefa 3: front

`web/src/api.js`:
- `buy: (t, qty, meta, protecao)` envia `protecao` no corpo só quando definido;
- `marcos` sem mudança de assinatura (o corpo já é livre).

`web/src/persistence.js`:
- `serverStore.buy(t, qty, meta, protecao)` e `deviceStore.buy(t, qty, meta, protecao)` repassam `protecao`.
- O ramo sem sessão do `deviceStore` (legado) espelha a regra: `"sem"` não pede marcos; senão chama `api.marcos(t, { setup, preco, compra: true })` e usa o resultado se válido (revalidando como já faz).
- Manter `test_api_parity.mjs` verde.

`web/src/App.jsx` `BuyModal` (~9337):
- Ao abrir, buscar a prévia: `store.marcos(t, { compra: true, setup: meta?.setup, preco: q.price })`. Estados: carregando, válido, inválido com motivo, erro de rede.
- Botão `compra_previa_recalcular` refaz a busca com a cotação atual de `quotes[t]`.
- Prévia válida: mostrar STOP / ALVO / R:R (+ `parecer`, se houver) e o checkbox `compra_gravar_protecao`, marcado por padrão. Desmarcado = `protecao: "sem"`.
- Prévia inválida ou erro: mostrar `compra_sem_protecao_motivo` + motivo, e o checkbox `compra_sem_protecao_check`, DESMARCADO. "Confirmar compra" fica desabilitado até ele ser marcado (autorização explícita). Nesse caso `protecao: "sem"`.
- Prévia válida com gravar marcado: `protecao: "motor"`.
- `confirmBuy` recebe a escolha via `buyModal` (ex.: `buyModal.protecao`) e chama `store.buy(t, qty, meta, protecao)`.

Pós-compra (`confirmBuy` ~10215):
- Com `protecao === "sem"`, NÃO abre o `StopAlvoModal` nem roda `runStopAlvoFor`: o usuário já decidiu, e isso evita custo de IA. Só o toast com `s.marcosTexto`.
- Nos demais casos, mantém o fluxo atual.

`StopAlvoModal` (~4169):
- Botão `modal_recalcular` chama `store.marcos(t, { preco: cotação atual, recalcular: true })` e substitui `busca.data`.
- O modal deve então preferir `busca.data` aos `r.marcos` do N3 quando o usuário recalculou (flag local); hoje `r.marcos` tem precedência.
- Aplicar continua aplicando os números exibidos (do motor).

Acessibilidade:
- checkbox com label clicável, alvo ≥ 44px;
- estado de carregando anunciado (`aria-live="polite"` na prévia).

Guardião `web/tests/test_marcos_compra_ui.mjs`, estático, no padrão de `test_marcos_ui.mjs`:
- BuyModal chama `store.marcos` com `compra: true`;
- Confirmar fica desabilitado sem autorização quando a prévia é inválida;
- `confirmBuy` não abre o modal com `protecao "sem"`;
- StopAlvoModal envia `recalcular: true`.

## Fora do escopo

Publicação, sizing sobre patrimônio, mudança de prompt da IA.

## Regras de execução

- Não ler o `App.jsx` inteiro: usar Grep + Read com offset/limit.
- Rodar só os testes tocados (pytest de marcos/rotas/skill_ref/vocabulário e os `.mjs` de vocabulário/marcos/api_parity/rr_min).
- No final, `cd web && npx vite build`.
- NÃO rodar a suíte canônica nem `cap copy` (o orquestrador roda).
- Um commit por tarefa: `feat|fix(quick-261026-epr): ...`, terminando com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Não commitar PLAN/SUMMARY/STATE. Sem git stash, sem `gsd-sdk state.*`, sem ler `.env`.
- Escrever `261026-epr-SUMMARY.md` neste diretório, com frontmatter `status`.
- Decisão de produto não coberta aqui: não inventar; registrar como pendente.
