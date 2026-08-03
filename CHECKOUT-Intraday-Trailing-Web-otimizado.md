# CHECKOUT — Evolução: timing de entrada (intraday), trailing dinâmico, alvo dinâmico + web no Railway com admin

Documento de entrada para um **chat novo** (Claude Code, na raiz do repo
`b3-agente`). Contém o estado verificado do código, as decisões abertas e os
critérios de aceite. Objetivo: começar a trabalhar sem redescobrir o que já existe.

**Alvo: Claude Code.** Trabalho multi-fase no repositório, com deploy e verificação
em produção.

---

## 1. Missão

Cinco frentes, duas famílias:

**Produto (a análise ganha o eixo do tempo)**
| # | Frente | Em uma frase |
|---|---|---|
| F1 | **Timing de entrada** | Sair de "o setup existe" para "a condição de entrada ocorreu agora", com dado intraday |
| F2 | **Trailing dinâmico** | Trocar o trailing de % fixo por um que siga estrutura/volatilidade (ATR, mínimas, rompimento) |
| F3 | **Alvo dinâmico** | Reavaliar o alvo quando o ativo mostra indicação clara (extensão do movimento, nova resistência) |

**Plataforma**
| # | Frente | Em uma frase |
|---|---|---|
| F4 | **Web no Railway** | Servir o app web do próprio backend, com camada de segurança |
| F5 | **Módulo de administração** | Papéis, visão operacional e controles — hoje inexistente |

Restrição transversal: **custo** (contexto 2026-08-01: o Railway é o plano
pago de US$ 20/mês, não free tier — há franquia, mas o princípio de custo
O(1) em usuários continua valendo). Railway + IA + fetch de dados; toda decisão de
arquitetura declara o impacto de custo antes de ser adotada.

## 2. Lentes a acionar

- `engineering:system-design` — F1–F5 (fronteiras de serviço, modelo de dados intraday, admin).
- `anthropic-skills:analise-tecnica-b3` — F1–F3 (o que é gatilho de entrada legítimo, trailing dinâmico, extensão de alvo).
- `ai-firstify` — revisão das 7 dimensões quando a arquitetura estiver esboçada.
- `claude-api` — antes de afirmar qualquer fato de modelo/parâmetro/preço.
- `engineering:architecture` — registrar como ADR as escolhas irreversíveis (fonte de dados intraday, modelo de papéis).

---

## 3. Estado verificado do repositório

**As cinco frentes (F1–F5) são desenvolvimentos NOVOS.** Esta seção não lista
features prontas — lista a **infraestrutura existente sobre a qual o trabalho novo
se apoia** e os **andaimes que ele vai substituir ou ativar sem quebrar o que está
verde**. Conferido no código em 2026-07-30.

### Infraestrutura existente a reusar (não são as features)

| Componente | Onde | Fato verificado |
|---|---|---|
| Cliente Yahoo com crumb, fallback de host e retry | `server/app/yahoo.py` | Chama `/v8/finance/chart/` **sempre com `interval: "1d"`** — intraday nunca foi tentado, mas o endpoint aceita |
| Cache de candles em 2 níveis (memória + SQLite) | `server/app/candle_cache.py` | **A chave já é `símbolo + intervalo`** — a estrutura já segmenta por intervalo, o intraday encaixa |
| Snapshot técnico único (STU) | `server/app/technical_snapshot.py` | Fonte única de candles+indicadores por análise; `snapshotId` amarra N1/N2/N3 |
| Laço autônomo server-side | `server/app/agent.py` (`scheduler_loop`) | Gate `in_market_hours()`, intervalo por usuário, kill switch, heartbeat persistido, execução de stop/alvo |
| Cota, rate-limit e teto global | `server/app/metering.py` | `check(quota, rate_per_min, custo, cap_global)` — postura de custo reusável para orçamento de fetch |
| Autenticação (base, sem papéis) | `server/app/auth.py` | Sessões, throttle, senha com hash, Apple/Google. **Sem papéis, sem admin** — F5 é do zero |
| Famílias e confluência | `server/app/technical_models.py:139` | `families` + `confluenciaEntreFamilias` calculados |
| Fonte canônica da metodologia | `server/app/skill_ref.py` | Persona, princípios, contrato de dados, doutrina fundamental, didática |
| Harness de teste massivo | `scripts/masstest-agentes*.py` | Determinístico (grátis) e LLM (BYOK); gate pré-deploy |

### Dois andaimes a NÃO quebrar (existem no código, mas não são as features)

Não são entregas prontas — são pré-existências triviais que o desenvolvimento
novo vai **substituir/ativar**. Ignorá-las quebra teste verde ou duplica código.

1. **F2 (trailing dinâmico) — existe um trailing trivial de % fixo.**
   `server/app/agent.py:135` ajusta o stop a `trailingPct` (default 5%), de forma
   monotônica, com o guardião `test_trailing_sobe_o_stop_e_nunca_desce`. **Isso não
   é a feature** — a feature é o trailing **dinâmico** (ATR/estrutura). O trabalho
   novo o substitui/estende **preservando a monotonicidade e o guardião**, e sem
   descartar quem já tem `trailingPct` configurado.
2. **F4 (web no Railway) — o mount existe, mas está inerte.**
   `server/app/main.py:1213` monta `web/dist` em `/` *se existir*; mas `web/dist/`
   está no `.gitignore:15` e a raiz do deploy é `server/` (`server/railway.json`,
   `server/Procfile`), então o bundle nunca chega ao container e `/` dá **404**.
   **Servir a web em produção é desenvolvimento novo** — a parte a construir é o
   pipeline (como o bundle chega) + a camada de segurança, não o `app.mount`.

---

## 4. Frentes: o que decidir e como saber que terminou

### F1 — Timing de entrada (intraday)

**A investigar antes de projetar** (não assumir — medir):
- Quais intervalos e janelas o Yahoo devolve de fato para `.SA` (1m/5m/15m/60m e o `range` máximo de cada). O cliente atual já tem crumb/retry: dá para medir com um script pontual.
- Comportamento sob volume: latência, throttling e resposta a rajada — o Radar varre ~74 ativos.
- Alternativas gratuitas/baratas se o Yahoo não sustentar (a comparar por: cobertura B3, granularidade, limite de requisições, termos de uso, e **custo real** — inclusive "grátis com limite" que vira pago no volume do Radar).

**Decisões de arquitetura a fechar:** granularidade mínima que resolve o produto (1m é bem mais caro em armazenamento e fetch que 15m); quantos ativos são monitorados intraday (todos × só posições abertas × watchlist); onde o dado vive (o `candle_cache` já segmenta por intervalo — falta política de TTL/retenção).

**Aceite:** dado intraday chega ao STU com `snapshotId` próprio; o Radar diário continua com o mesmo custo de hoje; `scripts/masstest-agentes.py` segue com 0 violações.

### F2 — Trailing dinâmico

**Decisão:** qual critério (ATR × mínimas dos últimos N candles × abaixo do rompimento) e se substitui ou convive com o percentual atual (compatibilidade: usuários já têm `trailingPct` configurado).

**Aceite:** monotonicidade preservada (o guardião atual continua verde); trailing dinâmico nunca afrouxa o stop; teste com série real onde percentual e técnico divergem.

### F3 — Alvo dinâmico

**Decisão:** o que é "indicação clara" o suficiente para mover um alvo, e o que impede o alvo de correr indefinidamente atrás do preço. Precisa casar com o Princípio 5 da skill (R:R mínimo 1,5:1) e com o plano determinístico já existente (`setups.plano_operacional`).

**Aceite:** alvo só se move com critério declarado e auditável; o R:R recalculado permanece coerente; nenhuma contradição veredito↔plano (invariante que o masstest já cobre).

### F4 — Web no Railway com segurança, sob `acamerini.app` — ✅ FEITO (2026-08-02)

**Domínio: `acamerini.app` (ápice, sem subdomínio nem caminho)** — decisão já
registrada em `~/.claude/portas.md` antes mesmo deste checkout precisar
perguntar (quase-conflito com o MyData em 31/07, resolvido dando o ápice ao
BolsIA e `mydata.acamerini.app` ao MyData). Adicionado no Railway
(`railway domain acamerini.app`); **pendente (Alex)**: criar no provedor de
DNS o CNAME `@` → `7lawwovg.up.railway.app` + o TXT de verificação (até 72h
para propagar).

**Não houve ripple de URL-base**: `web/src/api.js` já resolve caminho
relativo (`/api/...`) fora do modo nativo — funciona em QUALQUER domínio que
sirva o mesmo `web_dist`, sem hardcode novo. O iOS continua apontando para a
Railway URL (`PROD_BASE`) de propósito — **decisão do Alex foi que o iOS não
entra no cadastro obrigatório**, então ele não deveria migrar para
`acamerini.app` mesmo.

**Hospedagem**: opção (a) do que este documento cogitava — mesmo serviço do
Railway, via `server/web_dist` (rootDirectory continua `/server`; ver F4
mínimo, já em produção desde 2026-08-01).

**Camada de segurança — decisão do Alex (2026-08-02): cadastro obrigatório SÓ
em `acamerini.app`**, não em todo o produto. Implementado como middleware
por HOST (`gate_cadastro_obrigatorio`, dormente via `B3_GATED_HOSTS` até o
Alex configurar a env). CORS **não mudou** — `allow_origins=["*"]` continua
necessário para o app iOS (origem `capacitor://`) chamar a API; como a web
serve front+API na MESMA origem, CORS não era o mecanismo certo para esta
decisão específica de qualquer forma. Cookie de sessão: **não existe** —
o app usa Bearer token desde sempre, então "Secure/SameSite" não se aplica
(não há cookie a endurecer). Cabeçalhos de segurança básicos (X-Content-Type-
Options, X-Frame-Options, HSTS) entraram, universais. **CSP ficou de fora**
— SPA React com estilo inline em toda parte; uma CSP errada quebraria a
renderização inteira. Rate-limit de borda: não entrou nesta rodada.

**Gap conhecido, não fechado**: o front NÃO tem tratamento visual dedicado
para o erro `cadastro_obrigatorio` (401) — hoje, se um visitante tentar
"Usar sem conta" em `acamerini.app`, vê o erro genérico da API em vez de uma
tela "crie sua conta para usar este domínio". Só dá para testar de verdade
depois que o DNS propagar.

**Aceite original revisado**: `/api/health` intacto ✓; carimbo do front bate
com `version.js` ✓; nenhuma rota de API perde controle de acesso ✓
(o gate é ADITIVO); TLS válido em `acamerini.app` — pendente do DNS.

### F5 — Módulo de administração — ✅ v1 FEITO (2026-08-02, SÓ VER)

**Decisão do Alex**: v1 só observa, sem ação nenhuma (kill switch/cota por
usuário/reprocessar Radar ficam para uma v2, se precisar). Sem tabela de
papéis nova — reaproveitou o portão que `/api/obs/logs` e `/api/obs/usage`
já tinham (`_is_obs_admin`: `B3_ADMIN_EMAILS` ou a 1ª conta criada).
`GET /api/admin/summary`: usuários cadastrados (sem pass_hash/provider_sub),
uso de IA, saúde do agente, estado do gate do F4. UI em Perfil → Logs & debug.

**Aceite**: nega acesso a não-admin (403, testado) ✓; nenhum dado sensível
vaza (guardião trava ausência de pass_hash) ✓; "ação administrativa fica
registrada" não se aplica — não existe ação nesta v1.

---

## 5. Decisões que dependem do Alex (bloqueiam implementação)

1. **Enquadramento regulatório de "momento perfeito de entrada".** Timing preciso aproxima o produto de sinal operacional. O modo Estudo hoje é educacional por decisão consciente (vocabulário sem verbo de ordem) e o Operador é a mesa. Definir em qual modo o timing aparece e com que vocabulário — **decisão de produto/jurídica, não técnica**.
2. **Orçamento mensal aceitável** para dado intraday + laço mais frequente. Isso escolhe granularidade e cobertura; sem número, a arquitetura fica no chute.
3. **Escopo do admin na v1** — observabilidade apenas, ou também ação (kill switch, cota)?
4. **Público da web em `acamerini.app`** — só você/beta fechado, ou aberto com cadastro? Muda a camada de segurança.
5. **Como o BolsIA se encaixa em `acamerini.app`** — subdomínio (`bolsia.acamerini.app`) ou caminho (`acamerini.app/bolsia`)? Como há **várias apps** planejadas, o subdomínio isola melhor (CORS, cookie, TLS por app); decidir agora evita retrabalho de DNS/segurança depois.

## 6. Restrições inegociáveis

- **Custo declarado por decisão.** Toda proposta de arquitetura vem com estimativa de custo (fetch, armazenamento, compute) e a alternativa mais barata considerada.
- **Railway dorme** por ausência de tráfego outbound (~10 min); o laço intraday precisa sobreviver a isso ou o comportamento se torna intermitente. Já há heartbeat persistido para observar.
- **SQLite (WAL) em volume único** — intraday multiplica escrita; medir antes de assumir que aguenta.
- **Não quebrar o que está verde:** 357 testes, invariantes do `masstest-agentes.py`, guardião de vocabulário (`test_guardrail_imperativo`), monotonicidade do trailing.
- **Fonte canônica** (`skill_ref.py`) continua sendo a única definição de metodologia; nada de reescrever persona em novos módulos.
- **Backend puro** → `atualizar.sh --somente-deploy`. Entrega com front → `entregar.sh` (ele re-sincroniza o carimbo).
- **URL-base da API vem de UMA fonte** — ao migrar para `acamerini.app`, nada de trocar a string em N arquivos; centralizar em env/config e derivar dela em `web/src/api.js`, `capacitor.config`, scripts e testes.
- Dados reais sempre; sem mock em caminho de produção.

## 7. Riscos conhecidos

| Risco | Sinal de que aconteceu |
|---|---|
| Yahoo limita/bloqueia intraday em volume | 429/vazio no fetch de N ativos; o cliente já tem retry e fallback de host — observar antes de escalar |
| Custo cresce em silêncio | `/api/obs/usage` e a cota existem; instrumentar o fetch intraday do mesmo jeito |
| Laço intraday × Railway dormindo | Heartbeat com buracos durante o pregão |
| Contradição entre camadas | Rodar `scripts/masstest-agentes.py` (grátis) antes e depois; 0 violações é o piso |

## 8. Sequência sugerida

Cada fase termina com evidência de execução, não com afirmação.

1. **Medir o Yahoo intraday** (script pontual, sem tocar produção) → tabela de intervalos/janelas/latência real + veredito sobre alternativas.
2. **ADR da fonte de dados** (`engineering:architecture`) → decisão registrada com custo.
3. **F2 (trailing dinâmico)** — menor risco, alto valor, não depende de dado novo se usar diário; entrega isolada com guardião.
4. **F1 + F3** — dependem do ADR; entram juntos porque compartilham o STU intraday.
5. **F4 → F5** — plataforma; F5 depois de F4 porque admin pressupõe superfície web servida.

## 9. Modelo e effort

- **Arquitetura, ADR e o módulo de admin:** `claude-opus-5`, effort `xhigh` — decisões irreversíveis e código multi-arquivo.
- **Implementação em volume, testes, scripts de medição:** `claude-sonnet-5`, effort `high` (varrer para `medium` onde a qualidade se mantiver).
- Não há carga de Batches nesta evolução (tudo é interativo ou agendado leve); streaming só importa acima de ~16K `max_tokens`, o que não é o caso aqui.

## 10. Primeiro comando sugerido no chat novo

> Leia `CHECKOUT-Intraday-Trailing-Web-otimizado.md`. Comece pela fase 1: meça o
> que o Yahoo entrega de intraday para tickers `.SA` (intervalos, janela máxima,
> latência, comportamento em rajada de ~74 ativos) com um script pontual que não
> toca produção, e traga a tabela + o veredito sobre alternativas gratuitas com o
> custo real no volume do Radar. Antes de propor arquitetura, responda as
> perguntas abertas da seção 5 que dependem de mim.
