# ADR-018: Cobertura E2E/browser automation — avaliação (FIX-C27)

**Status:** Aceito.
**Data:** 2026-08-23.
**Origem:** REPORT-01 (achado C-27, Médio) → ROADMAP v1.1, Fase 5 (05-CONTEXT.md): "avaliar E2E
leve (Playwright/similar) para o roteiro dos 8 passos da Experiência Principal — não implementar
uma suíte E2E completa nesta fase". Este documento é a avaliação exigida pelo Success Criteria
do ROADMAP ("cobertura E2E mínima... é avaliada") — decisão, não obrigatoriamente código novo.

---

## Contexto

Inventário real da suíte, medido no momento desta escrita (2026-08-23):

- `server/tests/*.py`: **105 arquivos** com `def test_*` (mais `__init__.py`, sem teste).
- `web/tests/*.mjs`: **95 arquivos**, dos quais:
  - **24** importam diretamente de `../src/*` (`web/src/finance.js`, `persistence.js` etc.) —
    exercitam código real, exigem `web/node_modules` (ver FIX-C24, mesmo plano).
  - **83** usam `readFileSync` para inspeção estática de fonte (regex sobre o texto do arquivo,
    sem importar nem executar o módulo) — é a categoria "contract/parity test" já documentada em
    `TESTING.md` ("Test Types"), específica da arquitetura dual-client deste projeto.
  - (a soma passa de 95 porque alguns arquivos fazem as duas coisas.)

`TESTING.md` já registra, antes deste ADR: *"E2E tests: not present. There is no browser
automation (Playwright/Cypress) or device-level test harness in the repo."* Este ADR não
contesta o fato — avalia se e quando isso deveria mudar.

**Evidência histórica de defeito que só a verificação ao vivo pegou.** O projeto tem precedente
registrado, não hipotético: `08-05-PLAN.md` (Fase 8) cita explicitamente "três defeitos (sync
device→servidor, orçamento sem flush, link do Operador) que passaram por toda a suíte e só
apareceram na verificação ao vivo". Rastreando cada um:

1. **Sync nativo era só ida** (stop/alvo apagado no blur vazio) — `stop-alvo-bug-e-automacoes`
   (memória do projeto), corrigido só depois de teste ao vivo no iPhone.
2. **Orçamento sem sync device→servidor** (`initialBudget`) + **debounce sem flush** —
   `orcamento-bug-e-config-boris` (memória), DUAS causas distintas, ambas só-iOS
   (F10-20260809-03 e F10-20260809-05).
3. **Link "Operador IA" × "Modo Operador" sem ligação** — `auditoria-modo-operador-ux` (memória),
   pego em auditoria manual da UI, não por teste automatizado.

Os três são **defeitos do lado nativo** (Capacitor/WKWebView no iPhone, `deviceStore`,
persistência local) — nenhum é reprodutível rodando só a PWA num navegador desktop. `07-06-PLAN.md`
generaliza o padrão: "o repositório tem três precedentes de defeito que passaram na suíte e só
apareceram ao vivo", e por isso as Fases 7 e 8 já passaram a exigir checkpoint humano bloqueante
com passos numerados antes de qualquer deploy que toque o ciclo automático — um controle de
processo que este ADR não substitui, só contextualiza.

## O que E2E cobriria e o que NÃO cobriria

Mapeando os 8 passos da Experiência Principal (CLAUDE.md) contra o que a suíte atual já trava:

| Passo | O que a suíte atual já trava | Cobertura real |
|---|---|---|
| 1. Escolher ativo | `test_radar.mjs`, `test_radar_watchlist.mjs` (wiring estático) | Parcial — não navega a UI de verdade |
| 2. Visualizar dados e horário | `test_fonte_cotacoes_visivel.mjs`, `test_fonte_explicacao.mjs` | Parcial — checa presença de texto/prop, não renderização |
| 3. Analisar contexto/risco | `test_timing_ui.mjs`, `test_hero_reconciliado.mjs` | Parcial |
| 4. Enviar ordem virtual | `test_disclaimer_trade_modal.mjs`, testes de rota `TestClient` no backend | Boa no backend (integração real); front é estático |
| 5. Acompanhar execução simulada | `test_ordens_pendentes_ui.mjs` | Parcial |
| 6. Visualizar resultado | `test_historico_ui.mjs`, `test_posicao_stop_alvo.mjs` | Parcial |
| 7. Explicação educacional | `test_conceito_ui.mjs`, `test_didatica_parity.mjs` | Boa (paridade de texto é o risco real aqui, já coberta) |
| 8. Registrar aprendizado / benchmark | `test_benchmark_curva.mjs` | Parcial |

Nenhum destes é um teste de **navegação real de UI** — são inspeção estática de fonte (regex
sobre JSX/JS) ou testes unitários de função pura. Um E2E de verdade (Playwright) cobriria a
**renderização e interação reais** nos 8 passos, na PWA: cliques, navegação entre telas, estado
visual pós-ação.

**A assimetria que decide o caso**: o app roda em DUAS superfícies — PWA no navegador e shell
Capacitor/WKWebView no iPhone (`web/capacitor.config.ts`, `appId: com.alexandrecamerini.bolsia`,
sem `server.url`, bundle embutido no binário). Playwright/Cypress testam a **PWA no Chromium**,
não o WKWebView nativo nem os plugins Capacitor (`@capgo/capacitor-social-login`,
`@capacitor/push-notifications`, `text-to-speech`) que são exatamente onde os três defeitos
históricos acima aconteceram. Ou seja: **o E2E mais barato de implementar (Playwright na PWA) não
teria pego nenhum dos três defeitos caros já registrados neste projeto** — eles vivem na
superfície que Playwright não alcança.

## Opções avaliadas

**(i) Playwright sobre a PWA (`web/`, `localhost:5173` via Vite).**
- Custo: médio — instalação de pacote novo (`@playwright/test`), browsers headless, CI/execução
  local adicional (~1-2min por rodada), manutenção de seletores conforme `App.jsx` muda (arquivo
  único de ~8000 linhas, alta taxa de mudança nas Fases 2-8).
- Cobertura real: só a PWA desktop/mobile-web. **Não cobre o lado nativo**, onde os três
  defeitos históricos custosos ocorreram (ver seção anterior).

**(ii) Harness de device (XCUITest ou Maestro) sobre o build do TestFlight.**
- Custo: alto — infraestrutura de simulador/device iOS, possivelmente CI com runner macOS
  (GitHub Actions macOS é pago por minuto, mais caro que Linux), curva de aprendizado de um
  framework novo (nenhum precedente no repo), manutenção contínua de um segundo conjunto de
  testes de UI para o mesmo produto.
- Cobertura real: **essa é a superfície onde os defeitos caros de fato aconteceram** — sync
  nativo, orçamento, plugins Capacitor. Cobertura alta do que mais importa, mas ao maior custo
  das três opções.

**(iii) Não adotar agora; reforçar o que já existe (guardiões estáticos + checklist manual do
`TESTFLIGHT.md`).**
- Custo: zero infraestrutura nova. Custo de oportunidade: nenhum ganho de cobertura automatizada
  imediato.
- Cobertura real: mantém o padrão atual — guardiões de paridade (estáticos, rápidos, já
  numerosos: 24 arquivos importam `web/src` de verdade) + checkpoint humano bloqueante antes de
  deploys que tocam execução automática (padrão já em uso desde Fase 7/8) + checklist manual do
  `TESTFLIGHT.md` para o lado nativo.

## Decisão

**Não adotar E2E/browser automation agora — opção (iii).** Justificativa em uma linha: o E2E
mais barato (Playwright/PWA) não cobre a superfície onde os defeitos caros historicamente
aconteceram (nativo/Capacitor), e o E2E que cobriria essa superfície (device harness) tem custo
de infraestrutura desproporcional ao estágio atual do produto (um desenvolvedor, pré-receita,
`05-CONTEXT.md`: "manter MUITO restrito... não abrir escopo de infraestrutura de teste nova sem
necessidade clara").

**O que NÃO está sendo decidido**: isto não é um veredito permanente de "nunca fazer E2E". Não
está sendo decidido que Playwright é inútil em geral — está sendo decidido que, HOJE, com os
defeitos reais deste projeto concentrados no lado nativo, ele não é o próximo investimento de
teste com melhor retorno. Também não está sendo decidido enfraquecer o checkpoint humano
bloqueante já em uso nas Fases 7/8 — esse controle continua sendo a mitigação real para o defeito
"passou na suíte, só apareceu ao vivo" enquanto não houver harness de device.

## Gatilhos de reavaliação

Condições objetivas que reabrem esta decisão:

1. **Terceiro defeito de regressão em fluxo financeiro crítico** (compra/venda, cálculo de
   posição/PnL, gate comercial) escapando para produção depois de passar pela suíte canônica
   completa — os dois primeiros (sync stop/alvo, orçamento) já aconteceram; um terceiro no mesmo
   padrão é sinal de que o guardião estático não é suficiente para essa classe de defeito.
2. **Entrada de um segundo desenvolvedor no projeto** — o custo de manutenção de um harness de
   device deixa de ser pago só pelo Alex; revisão de PR por outra pessoa também se beneficia de
   um smoke E2E automatizado que não depende de verificação manual ao vivo.
3. **Cobrança real ligada (ADR-010, números comerciais definidos)** — o custo de um bug de
   carteira/gate chegando a produção sobe de "prejuízo educacional" para "prejuízo financeiro
   percebido pelo usuário pagante"; o cálculo de custo-benefício desta decisão muda.
4. **Frequência de deploy que torna o checklist manual do `TESTFLIGHT.md` o gargalo** — se o
   tempo de verificação manual antes de cada deploy nativo passar a dominar o ciclo de entrega
   (hoje é esporádico, ligado a mudanças de execução automática).

## Consequências

**O que fica descoberto conscientemente:**
- Regressões de UI/interação na PWA que nenhum guardião estático detecta (ex.: um clique que
  para de disparar a ação certa por causa de um handler quebrado) seguem dependendo de
  verificação manual ou do usuário reportar.
- O lado nativo (Capacitor/WKWebView) segue sem qualquer automação — só checklist manual
  (`TESTFLIGHT.md`) e checkpoint humano bloqueante nos deploys que tocam execução automática.

**Controle compensatório para cada lacuna:**
- PWA: guardiões estáticos de paridade/wiring (95 arquivos `web/tests/*.mjs`, 24 exercitando
  código real) + `npx vite build` obrigatório em toda edição de front (CLAUDE.md, "Validação
  obrigatória") pega erro de sintaxe que nem grep nem os testes estáticos pegam.
- Nativo: checklist do `TESTFLIGHT.md` + o padrão de checkpoint humano bloqueante antes de
  deploy de mudança de execução automática, já em uso desde Fase 7 (`07-06-PLAN.md`) e Fase 8
  (`08-05-PLAN.md`) — mitigação de processo para exatamente a classe de defeito que este ADR
  documentou como "não seria pega por Playwright-na-PWA de qualquer forma".
- Nenhuma dependência nova instalada neste plano (`package.json`/`package-lock.json`
  inalterados em `web/`, `web-admin/` e raiz) — confirma que esta é avaliação, não implementação.
