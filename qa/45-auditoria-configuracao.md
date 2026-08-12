# qa/45 — Auditoria da configuração, proposta de reorganização e sessão de fonte de cotações

**Data:** 2026-08-11 · **Status:** SUPERADO — ver nota abaixo · **Pedido por:**
Alex ("reorganizar toda a parte de configuração... log misturado com
configuração, duas configurações de conta, sessão de fonte de cotações com
estatística inteligente e escolha de outro provedor")

> **Nota de 2026-08-12 (revisão pós-auditoria do PR #13)**: a Decisão 1
> (mapa de telas) e o Bloco 1 + Bloco 2 da Decisão 3 (tela "Fonte de dados",
> leitura e ajuste de intervalo) descritos abaixo **já foram implementados**
> — PR #14, "qa/45 Decisão 1: Perfil reorganizado — 5 telas, Fonte de dados
> nova" e "Fonte de dados: intervalo do spot vira parametrizável", mergeados
> em `main` antes deste PR #13. Este documento fica registrado como está
> (histórico não se reescreve) para preservar o raciocínio original; para o
> estado atual da aplicação, ver `qa/46-auditoria-observabilidade-governanca.md`
> em `main` (esse arquivo não existe nesta branch — foi adicionado depois,
> direto em `main`, via PR #15).
> As citações `App.jsx:linha` da Parte 1 abaixo foram corrigidas para bater
> com o código desta PR (que antecede a reorganização), mas a estrutura que
> elas descrevem ("hoje") não é mais o estado de `main`.

---

## Parte 1 — Auditoria (inventário com evidência)

### 1.1 As sete entradas do Perfil hoje

| Tile | Abre | Conteúdo real | Quem vê |
|---|---|---|---|
| "Conta" / "Entrar ou criar conta" | `ctx.openAuth()` (modal, não é tela do `onOpen`) | Login/logout, nome, provedor OAuth | todos |
| "Conta & preferências" | `onOpen("config")` → `ConfigScreen` | Personalização, período de candles, orçamento simulado, perfil de risco | logado |
| "Configurações de IA" | `onOpen("ia")` → `IAScreen` | Modelo de IA do agente, skills por modo, prompts, Boris (voz/presença) | logado |
| "Eficiência da IA" | `onOpen("eficiencia")` | Estatística de acerto/expectância das análises | logado |
| "Atividade da IA" | `onOpen("atividade")` | Custo estimado, histórico de uso | logado |
| "Notificações" | `onOpen("notificacoes")` | Preferências de push | logado |
| "Logs & debug" | `onOpen("logs")` | 8 seções heterogêneas (ver 1.3) | todos (parte), admin (parte) |

`App.jsx:2064,2069,2075,2078,2081,2088,2091` (corrigido em 2026-08-12 — a
citação original tinha um deslocamento de +28 linhas, herdado de uma versão
do arquivo posterior à desta PR).

### 1.2 A duplicidade de "conta" (confirmada)

`App.jsx:2064` — tile "Conta" abre um **modal de auth** (`ctx.openAuth()`), não
uma tela do sistema de navegação por `onOpen`. `App.jsx:2069` — tile "Conta &
preferências" abre a tela `ConfigScreen` (`onOpen("config")`), cujo `<h1>`
interno diz **"Configurações"** (`App.jsx:5673`) — um terceiro nome para o
mesmo lugar. Resultado: três rótulos ("Conta", "Conta & preferências",
"Configurações") para duas superfícies distintas (modal de identidade vs. tela
de preferências), nenhuma delas chamada do que o outro rótulo sugere. Quem
procura "onde mudo minha senha" e quem procura "onde mudo o período de
candles" caem no mesmo tile de entrada ("Conta & preferências") mas em
sistemas diferentes — a senha está no modal atrás do OUTRO tile.

### 1.3 `ConfigScreen` — o que de fato é "conta & preferências"

`App.jsx:5666-5814`, 4 seções:

| Seção | Conteúdo | Persiste em |
|---|---|---|
| PERSONALIZAÇÃO | tema, modo claro/escuro/sistema | device (`localStorage`) |
| PERÍODO DE DADOS (CANDLES) | período do gráfico/indicadores | servidor, por conta (`config.candlePeriod`) |
| ORÇAMENTO DE INVESTIMENTO | saldo virtual inicial | servidor, por conta |
| PERFIL DO OPERADOR | risco por trade, tamanho de posição | servidor, por conta |

Coerente e enxuta — **isto não precisa mudar**. O problema não é aqui.

### 1.4 `AiConfigScreen` — "Configurações de IA"

`App.jsx:4279-4451` (corrigido em 2026-08-12 — nome do componente e range).
Quatro seções dentro desse range: INSTRUÇÕES DO AGENTE/SKILLS (`4136`, via
`<SkillSection`), CONFIG DE LLMs E PROMPTS (`~4175`, via `<PromptsSection`),
BÓRIS — VOZ/PRESENÇA/AVISOS (`4239`), MODELO DE IA DO AGENTE (`4321`).
Também coerente — tudo ali é, de fato, configuração de IA. **Não precisa
mudar.**

### 1.5 `LogsDebugScreen` ("Logs & debug") — onde a mistura está de verdade

`App.jsx:4896` em diante, na ordem em que aparecem na tela:

| # | Seção | É config ou é log? | Evidência |
|---|---|---|---|
| 1 | SNAPSHOTS DAS ANÁLISES | diagnóstico (rastreabilidade de QA) | `4916` |
| 2 | **SERVIDOR DO APP** (override de API base) | **CONFIGURAÇÃO** — campo de texto que a pessoa edita e persiste no aparelho | `4933` |
| 3 | DIAGNÓSTICO QA · iOS/IA/Notificações | diagnóstico | `4951` |
| 4 | (bloco condicional) status do Operador no servidor | diagnóstico/status | `4966+` |
| 5 | DIÁRIO DO OPERADOR (servidor) | log | `5007` |
| 6 | LOGS DETALHADOS DO SERVIDOR | log (admin) | `5039` |
| 7 | ADMINISTRAÇÃO → usuários, uso de IA, agente | painel admin (config + status misturados) | `5081+` |
| 8 | ADMINISTRAÇÃO → **FONTE DE COTAÇÕES** | metade config (provedor, intervalo), metade status (orçamento gasto, projeção) | (entrega de hoje) |

**O achado central**: a seção #2 (override do servidor da API) é uma
**configuração que a pessoa ajusta e que persiste** — indistinguível
estruturalmente de qualquer campo do `ConfigScreen` — só que vive dentro de
uma tela cujo `<h1>` diz "Logs & debug" e cuja descrição (`4898`) promete
"diagnóstico técnico". Isso é exatamente a queixa: **configuração
sobrevivendo dentro de log**. A seção #8 (fonte de cotações, entregue hoje)
repete o padrão por construção — nasceu dentro do painel de admin porque era
o lugar mais rápido de expor um dado que já estava sendo buscado, não porque
fosse o lugar certo.

### 1.6 Quem vê o quê hoje (fronteira de acesso)

| Nível | Vê | Não vê |
|---|---|---|
| Anônimo | tudo do `ConfigScreen`/`IAScreen` que não depende de conta | Logs & debug quase inteira (linha `4972`: "Entre na conta para ver...") |
| Logado comum | + Diário, status do servidor, override de API | Logs detalhados, painel de Administração (403 silencioso — `obsDenied`/`adminDenied`) |
| Admin (1º usuário cadastrado ou `B3_ADMIN_EMAILS`) | + logs detalhados, usuários cadastrados, uso de IA global, **fonte de cotações** | — |

A fonte de cotações — provedor ativo, se é brapi ou Yahoo, se o dado está
atrasado — é hoje **admin-only**. Isso contraria o princípio #3 do CLAUDE.md
("dados de mercado exibem fonte... para o usuário"), que não faz essa
distinção por papel. O badge no preço (entregue hoje, PR #12) já corrigiu a
parte "todo usuário vê a fonte do preço que está olhando"; o que continua
admin-only é o **detalhe operacional** (orçamento, cota, intervalo) — que
faz sentido continuar restrito, mas precisa de nome e lugar próprios, não
"um item dentro do painel de admin".

### 1.7 O que já existe no backend e não tem controle nenhum na UI

`GET/POST /api/obs/brapi/projecao` (`main.py`, ADR-008 desta sessão) simula e
aplica o intervalo de spot — **mas nenhuma linha em `web/src/api.js` ou
`persistence.js` chama essa rota**. Confirmado por busca: zero ocorrências de
"brapi" nos dois arquivos. A "estatística inteligente" e a "escolha de
intervalo" que o Alex pede **já têm motor pronto no servidor** e zero
superfície no app — hoje só é operável via `curl` direto.

### 1.8 Modelo de planos — o que já existe

`server/app/plan.py`: `PLAN_FREE`/`PLAN_PRO` com `max_watchlist`,
`max_analyses_per_month`, `byok_required`; hooks `can_add_ticker`,
`can_analyze`, `requires_subscription` — **todos implementados e todos hoje
retornam "permitido"/`False`** (ninguém é bloqueado). Estratégia declarada na
docstring do módulo: **BYOK viabiliza tier gratuito generoso** — o usuário
pluga a própria chave de LLM, o custo de inferência não recai sobre o app.

Contadores já existentes que um cap poderia reusar:
- `metering.py`: `check`/`consume`/`snapshot` — cota por usuário/dia, rate/min,
  teto global — já em produção pro uso de IA gerenciada.
- `brapi_budget.py`: fatias, teto diário, `pode_gastar`/`debita` — já em
  produção pro consumo da brapi.

`qa/42-finops.md` (com adendo de 01/08): único custo em dólar hoje é o
container Railway (~US$20/mês) + volume; LLM é BYOK (custo zero pro app,
exceto a IA *gerenciada* opcional, que tem cota por usuário e teto global
configuráveis por env, **hoje sem teto global definido** — ilimitado).

### 1.9 Registro de provedores de cotação

`candle_provider.py`: `_PROVEDORES = {"yahoo": YahooProvider, "brapi":
BrapiProvider}`, resolvido por env `B3_CANDLE_PROVIDER`. Contrato
`CandleProvider` é **um método**: `async def history(ticker, rng, interval) ->
dict`. Registrar um terceiro provedor é mecânico (nova classe + entrada no
dict) — a pergunta de produto é orçamento/contrato daquela API, não
arquitetura (ver decisão 5).

---

## Parte 2 — As nove decisões

### Decisão 1 — Mapa de telas proposto

Cinco telas no lugar das sete atuais, com a mesma quantidade de conteúdo —
nada some, tudo migra:

| Tela nova | Substitui | Contém |
|---|---|---|
| **Conta** | tile "Conta" (mantém) | Login, identidade, dados da conta — sem mudança |
| **Preferências** | "Conta & preferências" (renomeia; conteúdo idêntico) | Personalização, período de candles, orçamento simulado, perfil de risco — `ConfigScreen` como está |
| **IA & Boris** | "Configurações de IA" (renomeia; conteúdo idêntico) | Sem mudança de conteúdo |
| **Fonte de dados** *(nova)* | fatia de "Logs & debug" (SERVIDOR DO APP + FONTE DE COTAÇÕES) | Ver decisão 3 |
| **Diagnóstico** | resto de "Logs & debug" (snapshots, diagnóstico QA · iOS/IA/notificações, status do Operador no servidor, diário, logs detalhados, admin de usuários/IA) | Puro log/status, sem campo editável |

"Eficiência da IA" e "Atividade da IA" ficam onde estão — já são telas
coerentes de uma coisa só. **Trade-off**: 5 em vez de 7 tiles no Perfil reduz
ruído; o custo é uma migração de rota (`onOpen("fonteDados")` novo) que toca
navegação, não lógica de negócio.

### Decisão 2 — Fronteira config × diagnóstico

Regra única, aplicada a todo item do inventário: **se a pessoa pode editar e
o valor persiste, é configuração; se o valor só é produzido pelo sistema e
lido, é diagnóstico.** Aplicando:

- SERVIDOR DO APP (campo de texto, persiste) → configuração → migra pra "Fonte
  de dados".
- Provedor ativo/intervalo (SE a Fonte de dados ganhar um seletor — decisão 3)
  → configuração.
- Orçamento gasto, projeção, taxa de falha, diário, logs → diagnóstico, ficam
  em "Diagnóstico" (ou reaparecem como leitura dentro de "Fonte de dados" —
  ver decisão 3, que é a exceção deliberada à regra).

**Trade-off**: a regra é simples de aplicar e de lembrar; o preço é que
"Fonte de dados" quebra a separação estrita (mistura o intervalo, que é
config, com o orçamento gasto, que é diagnóstico) — aceito porque as duas
coisas são a mesma decisão vista de dois ângulos (decisão 3 justifica).

### Decisão 3 — Sessão "Fonte de dados"

Uma tela nova, visível a **todo usuário logado** (não só admin — ver decisão
1.6), com dois blocos:

**Bloco 1 — hoje (leitura, sempre visível):**
- Provedor ativo e reserva (brapi/Yahoo) — precisa de um rótulo de exibição
  novo (`FONTE_LABEL` não existe nesta PR; nasceu depois, no PR #12 — ao
  implementar esta decisão, criar ou reusar o que existir em `main` no
  momento).
- Frescor: **`docs/MEDICAO-Brapi-2026-08-11.md` marca o delay real do spot
  em pregão como "não confirmado"** — a medição de referência foi feita às
  01:31 BRT, fora de pregão, e o próprio documento lista "repetir a
  amostragem em pregão" como pendência aberta da Fase 0. *(Correção de
  2026-08-12: a versão original desta linha citava "brapi ~70s de atraso ·
  Yahoo ~15min" como "números reais" dessa fonte — o arquivo não contém
  esses números; era um dado não confirmado apresentado como medido,
  contra o princípio #4 do CLAUDE.md do repo.)* Até uma medição real em
  pregão existir, a tela não deve mostrar um valor de delay fixo — mostrar
  "frescor não medido ainda" ou equivalente, nunca um número inventado.
- Consumo da cota do mês (gasto/teto), com o disclaimer de que é um recurso
  compartilhado entre todos os usuários do app, não individual.

**Bloco 2 — ajuste (admin apenas, reusa o portão que já existe):**
- Intervalo de atualização do spot, com o "estatística inteligente" da
  decisão 4 embutida.
- Botão "aplicar" que chama o `POST /api/obs/brapi/projecao` já existente.

**Trade-off**: expor consumo agregado a todo usuário é transparência
(princípio #3) sem custo de segurança (é dado agregado, não por-usuário); o
controle de ajuste continua admin-only porque mexe em orçamento compartilhado
de todos — dar esse botão a qualquer usuário deixaria um usuário decidir a
frequência de atualização de todo mundo.

### Decisão 4 — A estatística que recomenda o uso da cota

**Reusa `brapi_budget.projecao()` — não cria segunda fonte de verdade.** A
conta, com os números reais de hoje (universo = 74 tickers, cota = 15.000/mês):

```
chamadasMes = spot_mes + delta_mes + fund_mes
  spot_mes  = universoN × (janela_pregao_s ÷ intervaloS) × 21 pregões
  delta_mes = universoN × 21
  fund_mes  = (universoN × 21) ÷ 7          # TTL de 7 dias

percentualDaCota = chamadasMes ÷ cotaMes × 100
intervaloMinimoSeguro = menor intervalo cujo total cabe na cota
```

Exemplo real (universo=74, intervalo=300s, cota=15.000):
`chamadasMes ≈ 136.974` → **913% da cota**, `intervaloMinimoSeguro ≈ 3068s
(~51min)`. A recomendação que a tela mostra: **"com o universo atual, o
intervalo mínimo que cabe na cota gratuita é ~51 min — abaixo disso a brapi
esgota antes do fim do pregão e o Yahoo assume o resto do dia."** Não é uma
sugestão da IA: é aritmética determinística já implementada, só sem UI.

**Declaração de incerteza**: a fórmula assume pior caso (universo inteiro
recalculado a cada intervalo); o consumo real tende a ser menor (cache
absorve parte da demanda). A tela diz isso explicitamente — "projeção de
pior caso, não previsão de uso real" — para não virar promessa que a
CLAUDE.md proíbe.

**Trade-off**: pior-caso superestima consumo (o número assusta mais do que a
realidade), mas é a única leitura segura sem telemetria de demanda real por
ticker — que não existe hoje e seria um projeto à parte.

### Decisão 5 — Escolha de outro provedor

O contrato `CandleProvider` já suporta um terceiro provedor sem mudança de
arquitetura — falta:
1. A implementação da classe (equivalente a `BrapiProvider`/`YahooProvider`).
2. Entrada no dict `_PROVEDORES`.
3. **Decisão de custo antes de qualquer código** — cada provedor novo é uma
   negociação de contrato/API própria (não existe "conector genérico").

**Quem escolhe**: env (`B3_CANDLE_PROVIDER`), como hoje — não usuário, pelo
mesmo motivo do intervalo (recurso compartilhado). Ao trocar, o cache (L2) e
o acervo de histórico **não se misturam entre fontes diferentes na mesma
troca de primário** — a regra "substituição, não merge" quando as fontes
divergem (já implementada no ADR-008) se aplica igual a um terceiro provedor.

**Trade-off**: manter a escolha em env (não em UI de usuário) preserva o
padrão já estabelecido, mas significa que "experimentar um provedor novo" só
o Alex faz, via Railway — aceitável, é decisão de custo, não de UX.

### Decisão 6 — Modelo de planos

Ancorado no que já existe em `plan.py`, sem reinventar:

| | Gratuito | Pago |
|---|---|---|
| Watchlist/análises | limite via `can_add_ticker`/`can_analyze` (hoje `None` = ilimitado) | ilimitado |
| Modelo de IA | BYOK obrigatório (chave própria) — estratégia já declarada | + opção de IA gerenciada pelo app (sem precisar de chave própria) — **candidata, PENDENTE de decisão do Alex** (ver `docs/adr/010`, seção "O que é comercial"; corrigido em 2026-08-12 — esta tabela apresentava como fechado algo que o próprio documento, linha 263, e o ADR-010 classificam como não decidido) |
| Fonte de cotações | brapi/Yahoo (o que está em produção) | mesmo — não é diferencial de plano, é infraestrutura do app |
| Features avançadas | — | candidatas: histórico de outcomes por regime (qa/44 B2), alvo dinâmico, IA gerenciada sem cota diária apertada |

**Trade-off**: a fonte de cotação **não deveria** ser o diferencial pago — é
custo de infraestrutura do app, não valor entregue ao usuário; o diferencial
natural é a **IA gerenciada** (que já tem custo em dólar mensurado em
`qa/42`) e features analíticas avançadas.

### Decisão 7 — Onde o cap incide e como se mede

**Por conta**, não por dispositivo (conta já é a unidade de identidade e
sync no app) nem global (global é o teto de proteção do app inteiro, não o
cap comercial do plano gratuito). Contador que já serve: `metering.py`
(mesmo padrão do uso de IA gerenciada — `check`/`consume`/`snapshot` por
`user_id`). Precisaria nascer: aplicar esse MESMO padrão a
`can_add_ticker`/`can_analyze` (hoje os hooks existem mas não chamam
nenhum contador real — comparam contra `None` sempre).

**Conversa com a cota da brapi**: são caps em camadas diferentes e não se
substituem — a cota da brapi é o **teto físico do app inteiro** (compartilhado
entre todos os usuários, protege contra estourar o plano gratuito da API); o
cap comercial é **por conta**, dentro daquele teto físico (protege o modelo
de negócio). Um usuário pago não aumenta a cota da brapi — aumenta a fatia
dele dentro do que o app já tem.

### Decisão 8 — Comportamento ao atingir o limite

Mesmo padrão que o app já usa pro orçamento da brapi (hard-stop com
degradação visível, nunca dado inventado): ao bater o cap do plano gratuito,
a ação específica é recusada com o motivo exato (`can_add_ticker` já retorna
essa mensagem pronta), o resto do app continua funcionando, e a tela mostra
o estado real ("análises deste mês: 30/30") — nunca um número estimado.
Nenhuma promessa de "assine e resolve na hora" — linguagem informativa,
consistente com a proibição de "enriquecimento rápido" do CLAUDE.md.

### Decisão 9 — Ordem de execução

**Antes da App Store** (baixo risco, sem decisão comercial pendente):
- Renomear/mover as 2 telas de conta (decisão 1) — cosmético, reduz confusão
  que já existe hoje.
- Sessão "Fonte de dados" com o Bloco 1 (leitura) — fecha o gap de
  transparência do princípio #3 pra todo usuário.

**Pode esperar**: Bloco 2 (ajuste de intervalo) — depende só de wiring, mas
sem urgência de produto. *(Nota de 2026-08-12: isto vale para o Bloco 2 como
descrito aqui — controle **admin-only**, sem gate comercial, que é o que de
fato foi implementado no PR #14. É diferente do que o `docs/adr/010` discute
sob "features avançadas do plano pago": uma hipotética versão FUTURA em que
o próprio usuário pagante ajustaria seu intervalo — essa sim depende de
repensar a arquitetura de orçamento por-usuário e continua pendente de
decisão do Alex, sem relação com o wiring admin-only já entregue.)*

**Depende de decisão comercial do Alex** (preço, loja, IAP, o que exatamente
é premium): tudo do modelo de planos (decisão 6) além do que já existe em
`plan.py`. Este documento não fixa preço nem mecânica de cobrança.

---

## Riscos abertos / o que esta proposta deliberadamente não resolve

1. **Terceiro provedor**: não há candidato concreto avaliado (custo, contrato,
   qualidade de dado) — a decisão 5 só prepara o terreno arquitetural.
2. **Cap por conta**: os hooks existem mas nunca foram exercitados com limite
   real — a primeira vez que `max_watchlist`/`max_analyses_per_month` saírem
   de `None` é also a primeira vez que esse caminho é testado em produção.
3. **IA gerenciada sem teto global** (`qa/42` adendo): continua ilimitado —
   risco de custo que já existia antes desta auditoria e que ela não amplia
   nem resolve; fica registrado aqui para não se perder.
4. **A estatística de projeção é pior-caso, não uso real** — se isso incomodar
   na prática, o próximo passo é medir demanda real por ticker (telemetria
   nova, fora do escopo de hoje).
