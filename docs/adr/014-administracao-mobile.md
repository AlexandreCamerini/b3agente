# ADR-014: Administração e observabilidade no app mobile

**Status:** Proposto — aguardando aprovação do Alex antes de qualquer
implementação (Fase 2 do prompt de execução).
**Data:** 2026-08-16 · **Origem:** pedido do Alex por acesso mobile à
superfície de administração/observabilidade do servidor, com reforço
explícito de escopo: "todos os controles de administração e observabilidade
que estão no servidor" — não um subconjunto.

---

## Contexto

`web-admin/` (ADR-011/012/013, em produção) tem hoje 10 abas com leitura +
escrita auditada, todas gated por permissão nomeada no backend
(`require_permission`, ADR-013). O app consumidor (`web/`, iOS/Capacitor) tem
**4 telas de observabilidade legadas** dentro de Perfil
(`EficienciaIAScreen`, `AtividadeIAScreen`, `FonteDadosScreen`,
`LogsDebugScreen`, `web/src/App.jsx:4519-5160`), nascidas do ADR-011 "até uma
decisão explícita" — nunca decidida.

O pedido: administradores acessarem a superfície inteira (as 10 abas +
reconciliação das 4 telas legadas) pelo app mobile.

## Fatos levantados (não redescubra)

| Fato | Onde | Por que importa |
|---|---|---|
| App nativo carrega bundle **local**, sem `server.url` | [web/capacitor.config.ts](web/capacitor.config.ts) — confirmado por leitura integral, chave `server` não existe | `/admin/*` do backend não é uma rota navegável dentro do WKWebView do app |
| `web-admin/` **já é fluido**, sem CSS desktop-only | [web-admin/src/App.jsx:886-899](web-admin/src/App.jsx#L886-L899) — nav em botões com `flexWrap`, container `maxWidth: 760px` (teto, não largura fixa), zero `<table>`, zero media query, viewport meta padrão em `web-admin/index.html:5` | Portar o bundle admin pra uma tela estreita não exige reescrita de layout — ele já encolhe |
| `web/src/api.js` já resolve **base URL nativa** (`nativeMode`, `runtimeBase`, `PROD_BASE`) | [web/src/api.js:6-96](web/src/api.js#L6-L96) | O app consumidor já sabe falar com o backend em produção a partir do nativo — mecanismo existe, mas é para chamadas JSON, não para servir o bundle HTML/JS do `web-admin/` |
| `web-admin/src/api.js` **não tem** esse suporte — é "só web", token próprio (`b3-admin-token`) | [web-admin/src/api.js:1-8](web-admin/src/api.js#L1-L8) | Sessão do admin é um mecanismo separado da sessão do app consumidor — reabrir `web-admin/` de dentro do app implica um handoff de auth, não reaproveita o login do app de graça |
| App consumidor **nunca lê `permissions`** de `/api/auth/me` | `grep -rn "permissions" web/src/` → zero ocorrências | O gate do ADR-013 chega pronto no payload e não é consumido em lugar nenhum do front consumidor — o botão novo desta rodada é o primeiro uso |
| `@capacitor/app-launcher` já é dependência; **não há** `@capacitor/browser` | [web/package.json:13-32](web/package.json#L13-L32) | App Launcher só abre a URL no Safari do sistema (sai do app, perde contexto); um browser *in-app* (SFSafariViewController) exige plugin novo |
| Tab "Auditoria" do `web-admin/` **não tem** gate de permissão no cliente | Explorado via agente — `VIEWS` em `web-admin/src/App.jsx:832-843`: todas as abas exceto `auditoria` têm `perm` cosmético | Cliente é só cosmético (o real é backend), mas confirme no backend qual permissão protege `GET /api/admin/audit` antes do mapeamento tela→permissão abaixo — não assumido neste ADR |

**Assimetria de publicação (Estado atual do prompt de execução, reafirmada
aqui por ser o fator decisivo):** mudar `web-admin/` é `publicar-admin.sh` —
sem review de loja, minutos. Mudar `web/` é `publicar-web.sh` **e** build
TestFlight — dias, sujeito a review da Apple. Superfície administrativa muda
com frequência (ADR-013 nasceu e foi implementado no mesmo dia). Qualquer
arquitetura que mova a UI admin para dentro do bundle `web/` converte toda
mudança futura de admin num ciclo de App Store.

## Alternativas consideradas

**A — Reimplementar as 10+4 telas como componentes nativos dentro de
`web/`.** Ganho: visual 100% integrado ao app, sem sair do container nativo.
Custo: duplica cada tela do `web-admin/` numa segunda base de código —
exatamente o padrão de dívida que este projeto já paga caro em
`deviceStore`↔`serverStore` e `defaults.py`↔`catalog.js` (paridade
obrigatória, testada, e ainda assim já vazou bug). Pior: por causa da
assimetria acima, toda mudança de admin passa a exigir TestFlight. Rejeitada
para a superfície inteira — custo recorrente permanente contra um ganho de
polish que a Opção C abaixo entrega em grande parte de graça (ver fatos:
`web-admin/` já é fluido).

**B — Abrir `web-admin/` no Safari do sistema via `@capacitor/app-launcher`
(zero dependência nova).** Ganho: nenhum código nativo novo, `web-admin/` já
renderiza bem em viewport estreito. Custo: sai do app (perde a moldura
nativa, notificação/estado do app fica em background), e login duplicado se
não houver handoff de token. Viável como fallback rápido, mas pior
experiência que C pelo mesmo custo de handoff de auth.

**C — Abrir `web-admin/` dentro de um browser in-app (`@capacitor/browser`,
SFSafariViewController no iOS) a partir de um ponto de entrada gated por
`permissions`, com handoff de sessão por token de curta duração.** Ganho:
zero duplicação de UI (o bundle admin responsivo já existe e já é mantido),
mudança de admin continua sendo só `publicar-admin.sh` (não regride a
assimetria de publicação), admin nunca sai da "moldura" do app. Custo: uma
dependência nativa nova (única vez — não por tela) e um endpoint de handoff
de sessão novo no backend.

## Decisão

**Opção C.** As 4 decisões que a Fase 1 precisava fechar:

### 1. Arquitetura de entrega

`web-admin/` inteiro (as 10 abas, sem port nem reescrita) abre dentro de um
browser in-app via `@capacitor/browser` (`Browser.open({ url, presentationStyle: "popover" })`
no iOS), disparado por um botão novo em Perfil, visível só quando
`permissions` (lido pela primeira vez no front consumidor) contém ao menos
uma das 7 permissões admin do ADR-013.

**Handoff de sessão:** o app chama uma rota nova
`POST /api/admin/mobile-handoff` (autenticada pela sessão já ativa do app),
que devolve um token de curta duração (minutos, uso único) trocável por
`b3-admin-token` na primeira carga do `web-admin/`. Evita duplo login e evita
o token de admin de longa duração transitar por um deep link. Rota nova,
`require_any_admin_permission`-gated — entra na tabela de rotas do ADR-013 e
no teste guardião `test_adr013_cobertura_rotas.py`.

**Onde quebra:** se o Alex preferir não adicionar `@capacitor/browser` agora,
a Opção B (App Launcher, já instalado) entrega o mesmo handoff de sessão sem
plugin novo — troque só o mecanismo de abertura (`Browser.open` →
`AppLauncher.openUrl`), o resto da decisão (handoff, gate por permissão) não
muda. Registrado aqui para não bloquear a aprovação por causa da dependência
nova.

### 2. Tratamento por superfície

**Uniforme para as 10 abas** — mesmo bundle responsivo, sem tela nativa
dedicada nem leitura simplificada por aba. `web-admin/` já é fluido (fato
acima); não há necessidade de diferenciar tratamento por superfície na v1.
Único ponto de atenção nomeado: a aba Prompts edita texto longo num
`<textarea>` HTML padrão — funciona (zoom nativo do browser, sem trava), mas
é o candidato mais provável a atrito real. Não é motivo para tratamento
especial agora; é o item a observar se o uso ao vivo reclamar.

### 3. Destino das 4 telas legadas em Perfil — CORRIGIDO na Fase 2

A v1 deste ADR assumiu, por semelhança de NOME com abas do `web-admin/`, que
as 4 telas eram superfície administrativa exposta sem gate. Fase 2 leu o que
cada tela busca de verdade e a premissa caiu:

| Tela | O que busca | Gate no backend | Veredito |
|---|---|---|---|
| `AtividadeIAScreen` | `GET /api/ai-activity` | `current_scope` — escopo por conta | **Pessoal**, não admin. Todo usuário vê o PRÓPRIO custo/histórico de IA — é o comportamento certo, não uma falha. |
| `EficienciaIAScreen` | `GET /api/analysis-outcomes/stats` | `current_scope` | **Pessoal** — "quanto MINHAS análises bateram alvo/stop". Comentário no código (`server/app/main.py:2106-2109`) já distingue explicitamente este painel pessoal do painel agregado "Eficiência da IA" do `web-admin/`. |
| `FonteDadosScreen` | endereço do servidor + teste de conexão (sem rede) **+** `GET /api/admin/summary` | rede: nenhum · `adminSummary`: `require_permission("observabilidade.ver")` | **Mista.** A parte pessoal (endereço/teste) é pra qualquer um. A parte admin **já se auto-esconde**: `web/src/App.jsx` captura o 403 (`/admin|restrito/i`) e liga `adminDenied`, some com a seção. Funciona hoje. |
| `LogsDebugScreen` | diagnóstico local + `GET /api/agent/*`, `POST /api/push/test` (`current_scope`) **+** `GET /api/obs/logs` (`observabilidade.ver`) **+** `GET /api/admin/summary` (`observabilidade.ver`) | mista | **Mista**, mesmo padrão de auto-esconder por 403 (`obsDenied`/`adminDenied`) já implementado. |

**Não há exposição a fechar.** As duas telas mistas já tratam a parte admin
corretamente (backend nega, front esconde a seção); gatear a tela INTEIRA
por permissão administrativa, como a v1 deste ADR propunha, seria uma
**regressão real** — tiraria de qualquer usuário pagante/free o acesso ao
próprio histórico de custo e eficiência de IA, que nunca foi admin.

**Decisão revisada:** nenhuma das 4 telas muda nesta rodada. Não há retirada
a marcar — nenhuma delas é substituível pelo `web-admin/` embutido (mostram
dado PESSOAL que o `web-admin/` nunca mostrou). Item cosmético, não
bloqueante, pra uma rodada futura: `FonteDadosScreen`/`LogsDebugScreen`
disparam a chamada admin e só escondem DEPOIS do 403 — poderiam checar
`ctx.authUser.permissions` antes de chamar, evitando a requisição fadada.
Fora de escopo aqui.

### 4. Risco de App Store

Mitigação: o ponto de entrada (botão em Perfil) só renderiza quando
`permissions` tem alguma permissão admin — um revisor logando com conta
comum nunca vê a superfície nem o botão. O conteúdo embutido é o mesmo
domínio do app (não third-party), servido por HTTPS, sem coleta nova de
dado. Risco residual: baixo, mesmo padrão de apps que embutem portal
avançado de configuração via browser in-app.

## Mapeamento tela → permissão (10 abas do `web-admin/`)

Reaproveita 1:1 o modelo do ADR-013 — nenhuma permissão nova, exceto a rota
de handoff (usa `require_any_admin_permission`, já existente como conceito
para o kill-switch).

| Aba | Permissão |
|---|---|
| Visão Geral, Custos, Comportamento do Usuário | `observabilidade.ver` |
| Eficiência da IA | `operador_ia.ver` |
| Automação (leitura / kill-switch) | `execucao_automatica.ver` / `.controlar` |
| Mudança de LLM | `llm.configurar` |
| Fontes de dados | `fontes_dados.configurar` |
| Prompts | `prompts.editar` |
| Usuários e papéis | `usuarios.gerenciar` |
| Auditoria | `require_any_admin_permission()` — confirmado em `server/app/main.py:740-742`; qualquer uma das 7 permissões admin libera, não uma específica |

## O que fica de fora desta rodada

- Tratamento diferenciado por superfície (decisão 2 — só entra se o uso ao
  vivo pedir).
- Checar `permissions` ANTES de chamar `adminSummary`/`obsLogs` em
  `FonteDadosScreen`/`LogsDebugScreen` pra evitar a requisição fadada ao 403
  (cosmético — decisão 3, item de polish, não bloqueante).
- Override manual de qualquer config a partir do handoff — o handoff só
  troca identidade, não adiciona capacidade que a permissão já não desse.

## Guardrails do CLAUDE.md — como cada um é respeitado

- **Gate real é sempre backend:** o botão em Perfil é cosmético — o handoff
  e cada rota atrás dele continuam validando `require_permission` como hoje.
- **Segredo só em env do servidor:** o token de handoff é de curta duração
  e uso único, nunca a `apiKey`/`baseUrl` da IA gerenciada — esses já são
  excluídos do payload pelo ADR-013 e este ADR não reabre isso.
- **Guardiões de teste não se apagam:** `test_adr013_cobertura_rotas.py`
  ganha a rota nova de handoff na allowlist/gate check, não é reescrito.
- **Publicação é passo manual separado:** decisão 1 preserva
  `publicar-admin.sh` como o único caminho de mudança de admin — é o motivo
  central de ter rejeitado a Opção A.
- **Paridade `deviceStore`↔`serverStore`:** não tocado — handoff não
  persiste nada em `web/src/persistence.js`.

## Pendente (decisão do Alex)

- Aprovar Opção C (com `@capacitor/browser`) ou a variante B (App Launcher,
  sem dependência nova) — arquitetura de handoff é igual nos dois.

**Pare aqui — Fase 2 (implementação) só começa após aceite explícito.**

## Referência cruzada

- `docs/adr/013-rbac-papeis-e-entitlements.md` — modelo de permissão
  reaproveitado 1:1; este ADR não redecide nenhuma permissão, só o
  transporte pro mobile.
- `docs/adr/011-modulo-observabilidade-governanca.md` — origem das 4 telas
  legadas ("até uma decisão explícita"); a decisão (Fase 2 deste ADR) é que
  3 das 4 são pessoais (nunca deveriam ter sido tratadas como observabilidade
  admin) e a parte administrativa das outras 2 já se auto-protege — nenhuma
  muda.
- `docs/prompts/admin-mobile-otimizado.md` — spec de execução que gerou este
  ADR (Fase 1).
