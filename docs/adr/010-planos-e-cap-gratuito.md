# ADR-010: Modelo de planos — cap gratuito e features pagas

**Status:** Parcialmente aceito — a parte TÉCNICA foi ativada na v1.3 (Fase
12, 2026-08-29): ver a atualização registrada ao final deste documento. A
parte COMERCIAL (preço, loja/IAP, validação de recibo) continua **pendente
de decisão do Alex**, como descrito abaixo.
**Data:** 2026-08-11 · **Origem:** as decisões 6-8 de `qa/45-auditoria-
configuracao.md` (auditoria de configuração do PR #13) formalizam este ADR.
Esse PR foi fechado sem merge em 2026-08-12 — a auditoria de UI que o
acompanhava ficou desatualizada por PRs seguintes (#14, #15), mas as
decisões de modelo de planos abaixo continuam válidas e não dependem
daquele documento; ficam autocontidas aqui.

---

## Contexto

O produto sempre teve ganchos de freemium centralizados e inativos
(`server/app/plan.py`, criado antes desta rodada): `PLAN_FREE`/`PLAN_PRO`,
hooks `can_add_ticker`/`can_analyze`/`requires_subscription`, todos hoje
liberando tudo. A estratégia de custo já estava declarada na docstring do
módulo: **BYOK** (o usuário pluga a própria chave de LLM) viabiliza um tier
gratuito generoso, porque o app não paga a inferência de quem usa a própria
chave.

Este ADR não substitui essa estrutura — fecha o que faltava decidir em cima
dela: onde o cap incide, como se mede, e a separação entre o que é
mensurável hoje no código e o que é decisão de precificação.

## Decisão

### O que é técnico (decidido aqui)

1. **Unidade do cap: por conta.** Reusa o mesmo padrão que `metering.py` já
   aplica ao uso de IA gerenciada (`check`/`consume`/`snapshot` por
   `user_id`) — não um contador novo.
2. **O cap comercial e a cota da brapi são camadas independentes.** A cota da
   brapi (`brapi_budget.py`) é o teto físico do app inteiro, compartilhado
   por todos os usuários — protege o app de estourar o plano gratuito da API
   externa. O cap comercial é por conta, dentro do que o app físico já
   suporta — protege o modelo de negócio. Nenhum dos dois substitui o outro;
   um usuário pago consome da MESMA cota física da brapi, só que sem limite
   comercial próprio.
3. **A fonte de cotação não é diferencial de plano.** brapi com Yahoo de
   reserva é infraestrutura do app, igual para todo mundo — cobrar por "ver
   de qual fonte veio o preço" contrariaria o princípio #3 do CLAUDE.md
   (transparência de dado é obrigação, não benefício).
4. **Comportamento ao atingir o cap**: a ação específica é recusada com o
   motivo exato (os hooks já retornam essa mensagem pronta), o resto do app
   continua funcionando normalmente, e a tela mostra o número real
   ("análises deste mês: 30/30") — nunca estimado, nunca escondido. Sem
   linguagem de "assine e resolve na hora" (proibição de enriquecimento
   rápido do CLAUDE.md).
5. **O que falta nascer, tecnicamente**: os hooks `can_add_ticker`/
   `can_analyze` existem mas nunca são exercitados com limite real (comparam
   contra `None`, que é sempre "permitido"). Ativar o cap é: (a) trocar
   `ACTIVE_PLAN` para resolver por usuário via recibo validado — já é o
   design documentado no módulo —, (b) alimentar `can_analyze` com um
   contador real no padrão `metering.py`, (c) `requires_subscription` passar
   a checar o recibo em vez de sempre `False`. Nenhuma dessas mudanças altera
   comportamento até o dia em que `PLAN_FREE` ganhar um limite que não seja
   `None`.

### O que é comercial (pendente — decisão do Alex)

- **Valor exato dos limites do gratuito** (quantos ativos na watchlist,
  quantas análises/mês). `plan.py` já tem os campos; falta o número.
- **Preço, moeda, loja** (App Store IAP / Google Play) e a mecânica de
  validação de recibo server-side (`requires_subscription` já está desenhado
  para isso, mas não implementado).
- **Lista definitiva de features avançadas do plano pago.** Candidatas
  identificadas nesta auditoria, para decisão — não compromisso:
  - IA gerenciada pelo app (sem exigir chave própria), com cota mais folgada
    que o teto hoje protegido por `B3_MANAGED_DAILY_QUOTA`/
    `B3_MANAGED_GLOBAL_DAILY_CAP` (`qa/42`).
  - Ajuste de intervalo de atualização de cotação (hoje admin-only pelo
    `POST /api/obs/brapi/projecao`) — só faz sentido como feature paga se o
    ajuste deixar de ser um recurso compartilhado entre todos os usuários,
    o que exigiria repensar a arquitetura de orçamento por-usuário, não só
    por-app. Fica registrado como pergunta, não como decisão.
  - Recorte de eficiência por regime de mercado (qa/44, Fase B2, quando
    tiver amostra suficiente).
  - Alvo dinâmico (`docs/adr/` F3, já implementado, hoje opt-in gratuito —
    decidir se continua assim ou vira paga).

## Consequências

- Nenhuma mudança de comportamento até que `PLAN_FREE` receba um limite
  numérico — este ADR é preparação, não ativação.
- Quando a ativação vier, ela é reversível e gradual: um valor por vez em
  `PLAN_FREE`, com os hooks já prontos para reagir.
- A separação cap-comercial vs. cota-física (decisão 2) evita o erro de
  "vender acesso a algo que o app não pode fisicamente entregar em escala" —
  a brapi tem 15.000 requisições/mês pro app inteiro, não por usuário; o
  plano comercial nunca pode prometer mais do que essa física sustenta.

## Referência cruzada

- `server/app/plan.py` — estrutura de planos e hooks.
- `server/app/metering.py` — padrão de contador por usuário a reusar.
- `server/app/brapi_budget.py` — cota física, camada separada.
- `qa/42-finops.md` — custo real medido do app hoje.
- `qa/46-auditoria-observabilidade-governanca.md` — auditoria de
  configuração vigente (a `qa/45` original foi fechada sem merge em
  2026-08-12; o inventário de configuração atual vive lá).

## Atualização — ativação técnica (v1.3, Fase 12, 2026-08-29)

Os dois números do gratuito foram decididos e ligados: `PLAN_FREE.max_watchlist
= 10`, `PLAN_FREE.max_analyses_per_month = 30`. `PLAN_PRO` segue com os dois
campos `None` (ilimitado) — **por decisão** de escopo do milestone (sem
loja/IAP na v1.3), não por lacuna técnica.

Do item 5 ("o que falta nascer, tecnicamente") desta decisão:

- (a) resolução do plano por conta — já tinha sido fechada no ADR-013
  (`current_plan`/`_plano_do_escopo`), não era pendência desta fase;
- (b) `can_analyze` alimentado pelo ledger real de `metering.month_used` —
  já tinha sido fechado na Fase 5 (C-33); a Fase 12 foi a primeira vez que
  esse caminho foi exercitado com um limite real (antes comparava sempre
  contra `None`);
- (c) `requires_subscription` continua sempre `False` — segue pendente,
  agora rastreado como CAP-08/CAP-09 (v2, ver REQUIREMENTS.md).

**Bypass fechado nesta fase:** `PUT /api/watchlist` gravava a lista final
inteira sem passar por nenhum gate — e era exatamente o caminho que o front
usa para adicionar em massa pelo catálogo. Passou a checar o limite, com a
semântica "só bloqueia crescimento" (D-03 do `12-CONTEXT.md`): remoção e
reordenação nunca são recusadas.

**Grandfather clause (D-04):** contas que já tinham mais de 10 ativos antes
da ativação não perdem nada — o gate só impede crescer além do que já
tinham. Coerente com a consequência já registrada acima de que a ativação é
"reversível e gradual".

**Copy:** a frase de recusa de `can_add_ticker` perdeu o "Faça upgrade para
adicionar mais.", alinhada ao princípio 8 do CLAUDE.md e à decisão 4 deste
ADR (CAP-07).

**Consequência aceita do BYOK (não é bug):** o acumulado mensal de análises
só é incrementado por `metering.consume`, que roda no caminho da IA
GERENCIADA. Uma conta free usando BYOK (chave própria) não incrementa esse
acumulado e, portanto, nunca esbarra nas 30 análises/mês. Isso é consistente
com o pilar de custo já declarado neste ADR (BYOK viabiliza um tier gratuito
generoso porque o app não paga a inferência de quem usa a própria chave) —
mas significa que o cap de análises protege o CUSTO DO APP, não o volume
absoluto de uso da conta. Registrado aqui como consequência explícita do
desenho, para não virar surpresa depois.

**O que ainda falta na interface:** os dois números reais (uso/limite de
watchlist e de análises) ainda não aparecem na tela — CAP-06, atribuído à
Fase 13, junto com o endpoint novo que expõe `max_watchlist`/contagem atual
da watchlist (hoje só `/api/ai/quota` expõe o par de análises).
