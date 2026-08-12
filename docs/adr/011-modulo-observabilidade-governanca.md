# ADR-011: Módulo de Observabilidade e Governança de Dados

**Status:** Proposto — a parte de arquitetura de leitura (o que o módulo
mostra, de onde, e como fica seguro) está pronta para implementação; a parte
de hospedagem/infra (onde a aplicação nova roda) e qualquer capacidade de
ESCRITA além do que já existe hoje **dependem de decisão do Alex** e ficam
marcadas como pendentes, não decididas aqui.
**Data:** 2026-08-12 · **Companion:** [`qa/46-auditoria-observabilidade-governanca.md`](../../qa/46-auditoria-observabilidade-governanca.md) (as sete decisões, com evidência)

---

## Contexto

O Boris+ acumulou, ao longo de várias entregas, uma quantidade grande de
processos de fundo (scheduler do agente, roteamento e orçamento de
cotações, uso de IA, push, cache de candles), 4 tabelas físicas SQLite
(uma delas — `kv` — multiplexando ~15 domínios de dado distintos por
prefixo de chave) e uma superfície de configuração de ~38 variáveis de
ambiente — tudo isso hoje observável de forma parcial e fragmentada dentro
de `LogsDebugScreen`/`FonteDadosScreen` (`web/src/App.jsx`), atrás de um
portão de admin binário (`_is_obs_admin`, `server/app/main.py:382-390`).

O pedido do Alex foi por uma **aplicação** dedicada de gestão desses dados
— não mais uma tela dentro do app consumidor — cobrindo observabilidade de
processos, navegador de tabelas, e uma trilha de eficiência para AÇÕES
automáticas do agente (distinta da trilha de eficiência de ANÁLISES de IA
que já existe). A auditoria (`qa/46`) confirmou, com evidência, que:
(a) boa parte do dado que esse módulo precisa **já existe**, só não tem UI;
(b) a trilha de eficiência de ações automáticas **não existe** — é a
lacuna estrutural mais relevante encontrada; (c) o maior buraco de
governança de configuração é `plan.py` (caps de monetização sem nenhuma
superfície), fora do escopo de leitura deste módulo.

## Decisão

### O que é arquitetura de leitura (decidido aqui)

1. **Aplicação separada do Boris+ consumidor, mesmo backend.** Novo
   frontend (SPA própria), reusando 100% dos endpoints e do modelo de auth
   já existentes (`_is_obs_admin`, Bearer token, `/api/obs/*`,
   `/api/admin/*`). Motivo: o público (Alex/operação) e o padrão de UI
   (grade densa, drill-down, tabela paginada) são estruturalmente
   diferentes do app mobile-first de simulação — e dado sensível (PII de
   `users`, tokens de `sessions`) não deveria trafegar no bundle público do
   app consumidor mesmo que a rota fique "escondida".
2. **O módulo é somente-leitura sobre o que já existe, mais uma trilha
   nova (ações automáticas) que reusa infraestrutura existente.** Ele NÃO
   recalcula custo, uso de IA ou orçamento do zero — lê `candle_provider.
   snapshot()`, `metering.snapshot()`/`global_snapshot()`,
   `brapi_budget.snapshot()`, `ai_activity.snapshot()`, `analysis_outcomes.
   compute_stats()`, tudo já implementado. A única peça nova de dado é o
   campo `origem` em `history` (Decisão 5 do `qa/46`) — não é um sistema de
   métricas paralelo, é uma tag numa estrutura que já existe.
3. **Navegador de tabelas nunca expõe segredo cru.** `sessions.token`,
   `users.pass_hash`, `kv["siwaRefresh"]`, `kv["pushTokens"]` nunca saem do
   backend em claro — o endpoint novo de leitura de tabelas aplica
   masking por campo conhecido, não por tabela inteira (a tabela `kv`
   mistura sensibilidades diferentes na mesma linha física).
4. **Fronteira de acesso permanece binária nesta rodada** (mesmo
   `_is_obs_admin` de hoje) — este ADR não introduz papéis/RBAC. Se o
   time de operação crescer além do Alex, isso é revisão futura.
5. **O que falta nascer, tecnicamente**, para viabilizar cada área do
   módulo (mapeado em detalhe na Decisão 7 do `qa/46`, Fases 1 e 2):
   (a) expor na API campos que o backend já calcula mas nenhuma UI lê hoje
   (heartbeat do scheduler, radar diário, avaliação de análises, proteção
   sem operador, detalhamento por fatia do orçamento brapi, breakdown por
   modelo de uso de IA, `candle_cache.stats()` — a função já existe, só
   falta o endpoint); (b) endpoints read-only novos para o navegador de
   tabelas, com o masking da decisão 3; (c) o campo `origem` em `history` +
   uma função de agregação por tipo de ação automática, espelhando o
   formato de `analysis_outcomes.compute_stats()` sem tocar naquele módulo.

### O que é pendente de decisão do Alex

- **Onde a aplicação nova é hospedada** — serviço Railway próprio?
  Subdomínio (`admin.boris.semente.dev`)? Mesmo container do backend
  servindo um segundo `web_dist`? Este ADR não escolhe infraestrutura.
- **Autenticação da aplicação nova** — reusa o mesmo login (email/OAuth) do
  app consumidor, restrito por `_is_obs_admin`, ou ganha um fluxo próprio
  (mais isolado, mais fricção de manutenção)? A auditoria recomenda reusar
  o que existe (menos superfície nova de autenticação = menos risco), mas
  a escolha final é do Alex.
- **Qualquer capacidade de ESCRITA além do que já existe hoje** — editar
  `_FRACOES` do orçamento brapi em runtime, ativar os caps de `plan.py`,
  mudar `B3_SCAN_UNIVERSE` sem deploy. Nenhuma dessas é parte deste ADR;
  são decisões de produto/monetização já endereçadas (ou pendentes) no
  ADR-010.
- **RBAC / nível intermediário de acesso** — se algum dia fizer sentido
  "ver métrica agregada sem ver PII individual", é um projeto à parte.

## Consequências

- Nenhuma mudança de comportamento do app consumidor — este módulo é uma
  aplicação nova, não uma alteração de `web/src/App.jsx` além do necessário
  para eventualmente aposentar a duplicação hoje existente em
  `LogsDebugScreen`/`FonteDadosScreen` (fora de escopo decidir isso agora;
  as duas telas continuam existindo até uma decisão explícita de
  descontinuar).
- A trilha de eficiência de ações automáticas começa vazia no dia em que
  for ativada — não há como reconstruir retroativamente a origem de
  `history` já gravado.
- Reusar o backend existente (em vez de duplicar cálculo) significa que
  qualquer correção/evolução nas fontes de verdade (`candle_provider`,
  `metering`, `brapi_budget`, `analysis_outcomes`) se propaga automaticamente
  para o módulo novo — não há uma segunda implementação para manter em
  sincronia.

## Referência cruzada

- `qa/46-auditoria-observabilidade-governanca.md` — auditoria completa,
  as sete decisões com trade-off, riscos abertos.
- `docs/adr/008-fonte-de-cotacoes-selecionavel.md` — orçamento/fatias da
  brapi que o módulo lê, não recalcula.
- `docs/adr/010-planos-e-cap-gratuito.md` — decisão comercial de
  monetização; o maior gap de governança de configuração (`plan.py`) fica
  sob aquele ADR, não sob este.
- `qa/42-finops.md` — único custo em dinheiro medido fora do código
  (mensalidade Railway).
- `server/app/analysis_outcomes.py` — trilha de eficiência de ANÁLISES de
  IA, deliberadamente não tocada por este módulo (a trilha de AÇÕES é
  nova, reusa `history`, não `analysis_outcomes`).
