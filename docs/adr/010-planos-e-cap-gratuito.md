# ADR-010: Modelo de planos — cap gratuito e features pagas

**Status:** Proposto — a parte técnica (o que já existe, o que falta nascer)
está pronta para implementação; a parte comercial (preço, loja, o que
exatamente entra em cada tier) **depende de decisão do Alex** e fica marcada
como pendente, não decidida aqui.
**Data:** 2026-08-11 · **Companion:** [`qa/45-auditoria-configuracao.md`](../../qa/45-auditoria-configuracao.md) (decisões 6-8)

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
- `qa/45-auditoria-configuracao.md` — decisões 6, 7, 8 (este ADR as formaliza).
