# Módulo de planos comerciais do Boris+

## Context

Hoje o plano da conta é um rótulo com **um** efeito real: `plan.can_analyze`
barra em 30 análises/mês no free. Todo o resto do controle de uso — cota
diária da IA gerenciada, rate por minuto, teto global, os três tetos da aba
Opções — é global, igual para todo mundo.

O alvo é o plano virar o eixo que decide (a) quais funções do app a conta
acessa e (b) qual o limite de cada ponto de controle de IA, configurável no
portal e visível para o usuário.

**O mapeamento encontrou dois defeitos que precisam vir antes.** O contador
mensal que o gate comercial lê está errado nos dois sentidos:

1. `main.py:861-863` — o ingest de analytics chama `metering.consume` **sem
   `month_section`**, e o default é `MONTH_SECTION = "aiUsageMonth"`. Um lote
   de N eventos de telemetria soma **N** ao contador de análises do plano. O
   guardião que exige `month_section` própria (`test_mcp_guardioes.py:258`) só
   varre `options_mcp_api.py`, não `main.py`.
2. `main.py:1817`, `:2224`, `:3562` — `/api/scan/deep`,
   `/api/carteira-stopalvo` e `/api/assistente` chamam `_ai_apply_managed`
   direto, **pulando o gate mensal**. Só `/api/analyze`,
   `/api/technical/analyze` e `/setups/compilar` passam por `_gate_analise`.

   **Correção (25-01, medida com teste):** este item estava impreciso e a
   diferença importa para a Fase 3. As três rotas **já CONTAM** no ledger que
   o plano lê — o `consume` de `_ai_apply_managed` usa o `MONTH_SECTION`
   default. O que falta nelas é o **gate**, não a contagem: elas gastam acima
   do cap e registram o excesso. Há teste dedicado, verde hoje.

Tornar esse número configurável por plano antes de consertá-lo daria controle
fino sobre uma medição errada. Por isso a Fase 0 é o conserto.

### Decisões tomadas (Alex, 2026-09-12)

| # | Decisão |
|---|---|
| D1 | `owner` resiste à revogação por **defesa em profundidade**: a rota recusa (403) **e** o bootstrap reconcede. |
| D2 | **RBAC = administração; plano = produto.** `opcoes.criar_setup` **migra** para o plano — vira a primeira função de produto comercializável. |
| D3 | `owner` ignora **só o cap comercial**, nunca o teto físico. |

### O que NÃO varia por plano, e por quê

O ADR-010 (decisão 2) separa **teto físico** de **cap comercial**: *"um
usuário pago consome da MESMA cota física"*. Então permanecem globais:

- `managed.global_daily_cap()` — teto da chave do servidor
- `options_mcp_api.cota_global_dia()` e `TETO_SERVICO_DIA = 2000` — teto do serviço MCP, compartilhado por toda a base
- `brapi_budget.cota_mes()` (15.000/mês) e `mydata_budget` — cota das fontes
- rate por minuto — é proteção contra flood, não produto

Vender acima disso é prometer o que a física não entrega.

---

## Fase 0 — consertar o contador (bloqueia todo o resto)

**Arquivos:** `server/app/main.py`, `server/tests/test_mcp_guardioes.py` (ou guardião novo)

1. `main.py:861-863` passa a usar uma `month_section` própria
   (`"analyticsEventsMonth"`). Telemetria para de consumir cota de análise.
2. As três rotas que pulam o gate mensal passam por `_gate_analise`. **Atenção:**
   `/api/scan/deep` reserva `custo=n` (até 10) — o gate mensal precisa receber
   o mesmo custo, senão conta 1 onde gasta 10.
3. Estender o guardião de `month_section` para varrer `main.py` também — hoje
   ele só olha `options_mcp_api.py`, e foi por isso que o defeito passou.
4. `metering.snapshot()` (`metering.py:352-358`) — **correção (25-01):** ele
   não "ignorava" `section`; usava para o dia e lia o mês sempre de
   `aiUsageMonth`. O defeito era **mistura de baldes**, não parâmetro morto.
   Resolvido com um `month_section` próprio, e não derivando o nome do mensal
   a partir do diário — as chaves de kv são independentes, e derivar seria
   adivinhar uma convenção que não existe.

**Risco:** ligar o gate mensal em três rotas que hoje não o têm pode barrar
usuários que antes passavam. Medir o impacto com `metering.month_used` antes
de ativar; se for alto, ativar junto com os limites novos da Fase 2.

---

## Fase 1 — papel `owner`

**Arquivos:** `server/app/rbac.py`, `server/app/main.py`, `server/app/agent.py`, `web-admin/src/App.jsx`, testes do ADR-013

- `OWNER = "owner"` em `rbac.py`, resolvido em `permissoes_do_papel`
  (`rbac.py:47-53`) pela **união dinâmica de `GRUPOS`** — o mesmo mecanismo
  que `ROLE_ADMIN` já usa, então permissão futura entra sozinha.
- **Irrevogável (D1):** `revoke_role` (`rbac.py:75-77`) passa a recusar
  `owner`; a rota `POST /api/admin/users/{id}/roles` (`main.py:1145-1146`, o
  ramo `revogar`, que hoje **não tem verificação nenhuma**) responde 403 com a
  razão. E `ensure_bootstrap_role` reconcede se escapar por outro caminho.
- **Âncora:** `B3_OWNER_EMAIL`, default `alexandre.camerini@gmail.com`.
  Diferente de `_is_admin_bootstrap`, **não** tem fallback de "primeira conta".
- **Concessão:** só um `owner` concede `owner` — mesmo padrão do freio de
  `role_admin` em `main.py:1153`, que hoje compara por nome literal.

**Pontos que quebram e precisam entrar junto:**
- `main.py:1124` — `gruposDisponiveis` vira `sorted(GRUPOS) + [ROLE_ADMIN]`;
  o portal renderiza **um botão de toggle por item** (`web-admin/src/App.jsx:1065-1078`).
  `owner` ali viraria um botão de revogar. Excluir da lista ou renderizar sem toggle.
- `agent.py:334-336` itera `rbac.GRUPOS` para escolher destinatários de push —
  papel fora de `GRUPOS` fica invisível.
- `test_adr013_rbac.py:94-99` e `:119` cravam **9 permissões**; `:144` crava a
  lista exata de papéis.

**Sobre o A-12:** fecha **parcialmente**. O `owner` não usa a regra da primeira
conta, então o papel máximo passa a depender de env explícita. Mas
`_is_admin_bootstrap` (`rbac.py:145-146`) continua existindo para
`role_admin`, e **três testes dependem dele** (`test_adr013_rbac.py:86-99`,
`:113-119`, `test_opcoes_dsl.py:83-86`) — é contrato testado, não bug
esquecido. Remover o fallback é decisão separada, com atualização de guardião.

---

## Fase 2 — catálogo de planos

**Arquivos:** `server/app/plan.py`, `server/tests/`

`plan.py:31-42` é hoje o **único** bloco de limites 100% literal do app — todos
os outros já têm env, e três já têm kv + admin + auditoria.

- Catálogo por plano: `id`, rótulo, **limites por ponto de controle** e
  **funções liberadas** (lista de chaves de função, ex.: `opcoes.criar_setup`
  vindo da D2).
- Precedência **memória → kv → env → default**, copiando
  `options_mcp_api.py:481-554` (`_valor_e_origem`) — é a implementação mais
  completa das quatro que existem: valida por camada, recusa `bool` e `<= 0`,
  e devolve a **origem** (`kv`/`env`/`default`) para a UI dizer quem manda.
- `free` e `pro` sem configuração preservam **exatamente** o comportamento de
  hoje. Teste obrigatório — é o que impede a refatoração de virar mudança de
  política silenciosa.
- Limite ausente = sem limite, **nunca zero**. Zero desliga acesso; ausência é
  "não configurado". (`main.py:790` já recusa zero na cota de Opções pelo mesmo
  motivo.)
- `plan_at_least` (`plan.py:68-75`) é órfão e `require_plan()` não existe —
  decidir entre implementar ou remover, não deixar o docstring mentindo.

---

## Fase 3 — gates leem o plano

**Arquivos:** `server/app/main.py`, `server/app/options_mcp_api.py`

- `_gate_analise` (`main.py:524-571`) continua o ponto único por requisição, e
  a ordem de hoje (BYOK → plano → metering) fica.
- **D3:** `owner` pula o gate comercial e **não** pula o teto físico.
- **D2:** `require_criar_setup` (`options_mcp_api.py:406-427`) passa a
  consultar o plano em vez da permissão. A permissão `opcoes.criar_setup` sai
  de `GRUPOS["opcoes"]` — o que muda `ENTIDADES_POR_PERMISSAO` (`rbac.py:121`)
  e os testes em `test_opcoes_dsl.py:341-348`.
- Fail-closed preservado: `_plano_do_escopo` (`main.py:129-141`) já degrada
  para o plano menos privilegiado em qualquer exceção.
- A recusa diz **qual** limite bateu. Hoje `options_mcp_api.py:2326` distingue
  `plano_analises` de `ia_gerenciada` **raspando a string `"analises/mes"`** —
  acoplamento frágil que deve virar código de erro estruturado nesta fase.

---

## Fase 4 — módulo no portal

**Arquivos:** `web-admin/src/App.jsx`, `web-admin/src/api.js`, `server/app/main.py`, `server/app/rbac.py`

Copiar o card `CotaOpcoes` (`web-admin/src/App.jsx:797-902`), que é o padrão
mais completo do portal: prévia (`simular` × `aplicar` como chamadas
**separadas**, `api.js:63-66`), **origem** de cada valor
(`ORIGEM_ROTULO`, `App.jsx:789`), consumo real ao lado do limite, e campo vazio
significando "não mexer".

- Rotas `GET`/`POST /api/admin/planos`, permissão `usuarios.gerenciar`
  (é gestão comercial, mesmo eixo de `POST /api/admin/users/{id}/plan`).
- Auditoria **por campo alterado**, entidade `plano_config`, e a entidade entra
  em `ENTIDADES_POR_PERMISSAO` — `rbac.py:86-93` declara que o mapa cobre toda
  entity gravada, e isso já foi esquecido três vezes.
- Lista de planos e de pontos de controle vem do backend. Nenhuma literal na UI.

---

## Fase 5 — plano visível no app

**Arquivos:** `web/src/App.jsx`, `web/src/copy.js`, `web/src/plan.js`, `server/app/main.py`

Estado atual: **nada em `web/src/` lê `authUser.plan`**, embora `_public_user`
(`main.py:213-221`) já o devolva. O único lugar onde o usuário vê o nome do
plano é um sufixo no modal de catálogo (`App.jsx:7615`). Não existe **nenhuma**
chave de copy sobre plano.

- **Delegar a um subagente de UX** a decisão de onde o plano fica
  permanentemente visível e onde aparece na recusa. Contexto a passar: o hub de
  Perfil (`App.jsx:2509-2612`) e seus grupos, a tela "Atividade da IA"
  (`App.jsx:5905-5998`, onde "análises deste mês: N/limite" já vive), e o
  componente `QuotaSeg` (`App.jsx:459-472`), que já tem semântica de três
  estados (carregando / falhou / dado).
- Textos vão para `copy.js` nos **dois modos**, chaves idênticas (há guardião).
  Hoje as frases de plano estão hardcodadas em `plan.js:27,39,47`, fora do
  dicionário.
- **Não hardcodar número**: `plan.js:1-12` proíbe explicitamente, e o critério
  6 do ROADMAP da Fase 13 também. O limite chega sempre do endpoint.
- Corrigir junto: `/api/ai/quota` (`main.py:574-593`) devolve
  `monthUsed`/`monthLimit` para quem tem BYOK — números que não decidem nada
  desde o 24-16; e o anônimo recebe `monthLimit: None` enquanto
  `/api/watchlist/quota` devolve o limite real (inconsistência entre os dois).
- Sem linguagem de upgrade agressivo: o ADR-010 (decisão 4) proíbe "assine e
  resolve na hora".

---

## Verificação

Por fase, nesta ordem:

1. **Teste que falha sem a mudança** — provar RED antes, colar a saída no resumo.
2. `bash scripts/executar.sh --testes` **fora do sandbox**
   (`dangerouslyDisableSandbox: true`; dentro dele ~26 falhas são falsas, por SSL).
   Baseline atual: `2565 passed, 5 skipped` + 131 `.mjs`.
3. `cd web && npx vite build` e `cd web-admin && npx vite build` conforme o que for tocado.
4. **Fase 0:** teste que prova que um lote de analytics **não** move
   `metering.month_used`; e que as três rotas passam a contar no gate mensal.
5. **Fase 1:** teste que prova que `owner` não pode ser revogado por rota
   nenhuma, e que a reconciliação é idempotente.
6. **Fase 2:** teste que prova que `free`/`pro` sem configuração se comportam
   exatamente como hoje.
7. **Fase 3:** teste que prova que `owner` passa o cap comercial e **não** passa
   o teto global.

Nada é publicado sem OK humano. Publicação do portal (`publicar-admin.sh`) só
**depois** do deploy do backend — portal novo contra backend velho chama rota
inexistente.

## Pendências herdadas

- **24-17 commitado e não publicado** (rota de plano no portal). Se este módulo
  for junto, publicar tudo de uma vez.
- Quatro janelas de tempo convivem no metering: UTC (`metering.py:106`), São
  Paulo (`options_mcp_api.py:634`), BRT (`brapi_budget.py:43`) e a do
  assistente. Um limite "por dia" configurável precisa dizer **qual dia**.
