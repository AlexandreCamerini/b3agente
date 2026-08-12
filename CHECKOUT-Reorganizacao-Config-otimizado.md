# Auditoria e proposta: reorganização da configuração + fonte de cotações + monetização

Prompt para Claude Code no repositório `b3-agente` (Boris+). O entregável desta
rodada é **auditoria + diagnóstico + proposta aprovável** — nenhuma mudança de
comportamento.

## Premissas assumidas

1. Isto é trabalho de **arquitetura de informação e produto**, não implementação.
   Código só entra depois que o Alex aprovar a proposta.
2. O ADR-008 (brapi free master de diário/spot; Yahoo backup e dono do intraday;
   orçamento de 15k req/mês com fatias e hard stop) está em produção e é a base
   sobre a qual a "sessão de configuração da fonte" se apoia — não se re-litiga
   a decisão, se expõe e se refina.
3. "Estatística inteligente" significa **recomendação derivada de dado medido**
   (consumo real por fatia, cota restante, delay medido), com a conta explícita
   na tela — nunca um número que a IA estima.
4. Prioridade do produto segue a submissão na App Store. A proposta indica o que
   cabe antes e o que fica para depois.

Se alguma premissa estiver errada, diga em uma frase e siga com a leitura mais
razoável.

## Entregável

| Arquivo | Conteúdo |
|---|---|
| `qa/45-auditoria-configuracao.md` | Auditoria (inventário do que existe hoje, com `file:line`), diagnóstico (o que está fora do lugar e por quê dói), e proposta de organização em telas/seções, com o antes→depois de cada item |
| `docs/adr/010-planos-e-cap-gratuito.md` | ADR da monetização: o que é grátis, o que é pago, onde o cap incide, como se mede, o que acontece ao estourar |

Nenhum arquivo de `server/app/` ou `web/src/` muda nesta rodada. Se a proposta
depender de um endpoint ou campo novo, descreva o contrato no documento.

## O terreno (já verificado — não re-descubra)

| Fato | Onde |
|---|---|
| Perfil tem 7 tiles; "Conta" (abre auth) e "Conta & preferências" (abre config) são entradas distintas com nome sobreposto | `web/src/App.jsx:2092,2097` |
| "Logs & debug" acumula: rastreabilidade de snapshots, override do servidor da API (config real de aparelho), status do Operador, Diário, logs de admin e painel de Administração | `web/src/App.jsx:~4918` em diante |
| A seção "FONTE DE COTAÇÕES" (provedor, orçamento, projeção) nasceu dentro do painel de Administração, atrás do portão de admin | `web/src/App.jsx` (bloco `PAINEL DE ADMINISTRAÇÃO`) |
| Orçamento, fatias, `spot_intervalo_s`, `projecao()` e o endpoint que simula intervalo→custo já existem no backend | `server/app/brapi_budget.py`; `GET/POST /api/obs/brapi/projecao` |
| Registro de provedores é um dict fechado (`yahoo`, `brapi`) resolvido por env, com `CandleProvider` como contrato de 1 método | `server/app/candle_provider.py` (`_PROVEDORES`, `get_provider`) |
| Ganchos de freemium existem, centralizados e hoje todos liberando: `PLAN_FREE`/`PLAN_PRO`, `can_add_ticker`, `requires_subscription` | `server/app/plan.py` |
| Estratégia de custo declarada: BYOK (usuário pluga a própria chave de LLM) viabiliza tier gratuito generoso | `server/app/plan.py` (docstring) |
| Já existe medição de consumo de IA por usuário/dia com teto global | `server/app/metering.py`, `managed.py` |
| Delay medido em pregão: brapi ~70s, Yahoo ~907s | `docs/MEDICAO-Brapi-2026-08-11.md` |

## O que a auditoria precisa responder

Levante com evidência, não de memória. Cada achado aponta o arquivo e a linha.

1. **Inventário de toda superfície de configuração** — cada tela/seção, o que
   ela contém, quem pode ver (anônimo / logado / admin) e onde o valor persiste
   (device, servidor, env). Inclua o que mora em `Config`, `IA`, `Notificações`,
   `Logs & debug` e no painel de Administração.
2. **O que está fora do lugar** — configuração misturada com diagnóstico,
   dado de admin misturado com dado de usuário, e as duas entradas de "conta".
   Para cada caso: qual usuário se confunde, e em que momento.
3. **O que persiste onde** — quais ajustes são por aparelho, quais por conta,
   quais globais do servidor. Sinalize onde essa fronteira hoje está implícita.
4. **Quem enxerga a fonte de cotações** — hoje só admin. Diga o que dessa
   informação é útil ao usuário comum (transparência de dado, princípio #3 do
   CLAUDE.md) e o que é operação.

## As decisões que a proposta fecha

Decida cada uma e registre o trade-off em uma linha. São para resolver no
documento, não para devolver como pergunta aberta.

1. **Mapa de telas proposto** — quantas telas, com que nome e que conteúdo, e o
   caminho de migração de cada item de hoje para o novo lugar. Nomes que o
   usuário reconheça, sem jargão interno.
2. **Fronteira config × diagnóstico** — o critério que decide se algo é ajuste
   ou observabilidade, aplicado a todos os itens do inventário.
3. **Sessão "Fonte de cotações"** — o que ela mostra e o que ela deixa ajustar,
   por perfil de usuário. Inclui: provedor ativo e reserva, frescor/delay
   medido, consumo da cota, intervalo entre atualizações, e o efeito de mudar.
4. **A estatística que recomenda o uso da cota** — a conta exata (entradas,
   fórmula, saída), a recomendação que ela produz, e como a tela declara
   incerteza quando a amostra é curta. Reuse `projecao()` em vez de criar uma
   segunda fonte de verdade; se ela precisar evoluir, diga como.
5. **Escolha de outro provedor** — o que muda no registro de provedores para
   admitir um terceiro (o contrato `CandleProvider` já existe: diga o que falta),
   quem escolhe (env, admin, usuário), e o que acontece com o cache e com o
   acervo de histórico ao trocar.
6. **Modelo de planos** — o que o gratuito inclui, onde entra o cap, e quais
   features ficam no pago. Ancore nos ganchos de `plan.py` que já existem e na
   estratégia BYOK já declarada ali.
7. **Onde o cap incide e como se mede** — por conta, por dispositivo ou global;
   qual contador já existente serve (`metering.py`, `brapi_budget.py`) e qual
   precisaria nascer. O cap do gratuito conversa com a cota da brapi: diga como.
8. **Comportamento ao atingir o limite** — o que o usuário vê, o que continua
   funcionando, e como isso respeita os princípios do CLAUDE.md (nada de
   promessa, nada de dado inventado, estado correto sempre visível).
9. **Ordem de execução** — o que entra antes da submissão na App Store, o que
   espera, e o que depende de decisão comercial sua (preço, loja, IAP).

## Critério de aceite

- Inventário completo com `file:line` por item; nenhum "provavelmente".
- As nove decisões aparecem resolvidas, com trade-off em uma linha cada.
- A proposta de telas tem antes→depois item a item — nenhum ajuste de hoje
  desaparece sem destino.
- A estatística da cota tem fórmula escrita e exemplo numérico com os números
  reais de hoje (universo do scanner, cota, intervalo vigente).
- O ADR de planos separa o que é decisão técnica (mensurável no código) do que
  é decisão comercial sua — e marca a segunda como pendente, sem inventar preço.
- Toda proposta que dependa de contrato novo (endpoint, campo, env) descreve o
  contrato, sem implementar.
- Riscos abertos e o que a proposta deliberadamente não resolve, listados.

## Como trabalhar

Leia antes de propor: as telas de Perfil e as sub-telas em `web/src/App.jsx`,
`server/app/plan.py`, `server/app/brapi_budget.py`, `server/app/candle_provider.py`,
`server/app/metering.py`, `docs/adr/008`, `qa/42-finops.md` e `qa/43`.

Entregue no escopo pedido. Decida sozinho o rotineiro; se discordar de algo do
escopo, diga em uma frase e siga. No máximo dois subagentes (um varre a
superfície de configuração no front, outro os contadores e limites no backend);
o resto direto.

## Fora de escopo nesta rodada

- Alterar código de produção, prompts (`defaults.py` ↔ `catalog.js` seguem
  intocados), env de produção ou qualquer valor de orçamento.
- Definir preço, moeda, loja ou mecânica de cobrança — decisão comercial sua.
- Implementar provedor novo de cotações; a proposta descreve o que falta.
- Publicar, mergear ou bumpar carimbo.
