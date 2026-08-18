# Achados — Dimensão UX/UI

Data: 2026-08-18

## Método de verificação

**Nível alcançado: 3 (API real + código/docs).** Os níveis 1 (`mcp__claude-in-chrome__*`)
e 2 (`mcp__computer-use__*`) foram checados no início da execução e **não estão
disponíveis no conjunto de ferramentas deste subagente** — nenhuma ferramenta
`mcp__*` aparece na lista de ferramentas atribuídas a este executor (consistente com
o bug conhecido upstream, anthropics/claude-code#13898, que remove ferramentas MCP de
agentes com `tools:` restrito no frontmatter). Não houve insistência: a escada caiu
direto para o Nível 3, conforme instruído.

**Como o stack subiu (real, não mockado):**
- Backend `uvicorn app.main:app` na porta 8787, processo real, mesmo código de
  `server/app/`, contra as fontes de dado reais (Yahoo Finance / brapi em produção,
  sem stub). `B3_ADMIN_EMAILS=auditoria-admin@local.test`.
- Vite dev server do front nesta mesma árvore de trabalho na porta 5176 (não 5174,
  reservada ao plano 01-01 paralelo). O worktree deste plano não tinha `.venv`/
  `node_modules` próprios (base do worktree antecede a criação de `.planning/`);
  usado o Python do venv da árvore principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv`,
  só interpretador+pacotes, código servido é o do worktree) e um **symlink**
  `web/node_modules -> .../b3-agente/web/node_modules` (nenhum pacote novo instalado,
  gitignored, satisfaz T-01-SC). Confirmado por diff que `App.jsx`/`copy.js`/
  `CLAUDE.md` são byte-idênticos entre este worktree e a árvore principal antes de
  reusar os pacotes já instalados.
- Conta isolada `auditoria-ux@local.test` via `POST /api/auth/register` (escopo
  `user_id` próprio, separado do plano de STORY que roda no mesmo backend
  compartilhado).
- Chamadas HTTP reais contra o backend (registro, login, `/api/quotes`,
  `/api/buy`, `/api/sell`, `/api/timing/{t}`, `/api/technicals/{t}`) exercitando o
  motor determinístico de verdade — não simulação de payload.

**O que NÃO pôde ser verificado ao vivo (limitação explícita):** renderização visual
real (screenshot/DOM), pois os Níveis 1/2 estavam indisponíveis nesta sessão.
Vereditos de layout, responsividade visual e contraste de cor são inferidos por
leitura de código (JSX + tabela de tema) e, no caso de contraste, por cálculo real
da razão WCAG a partir dos hex do tema (função de luminância relativa padrão),
não por medição em tela renderizada. Onde a limitação afeta o veredito, isso está
marcado explicitamente na linha correspondente.

## Auditoria dos 10 princípios

| # | Princípio (CLAUDE.md) | Veredito | Onde foi verificado | Evidência |
|---|---|---|---|---|
| 1 | Saldo fictício visível | conforme | ao vivo (API) + código | `POST /api/auth/register`/`/api/state` retornam `cash`/`positions` sempre; `Topbar` (`web/src/App.jsx:707-746`) renderiza `caixa {money(caixa)}` e patrimônio em toda tela principal (componente compartilhado, não condicional) |
| 2 | Nenhuma ação envia ordens reais | conforme | código | Não existe integração de corretora/banco em `server/app/*.py` (grep por `corretora`/`broker`/`ordem real` não encontra rota externa); `disclaimers.js:26,34,38` afirma isso explicitamente em 3 pontos |
| 3 | Fonte + horário + natureza do dado exibidos | **violado** | ao vivo (API) + código | Ver F-UX-01: `TechnicalModal` (`App.jsx:1512`) exibe rótulo fixo "Fonte: Yahoo Finance" independente da fonte real; `GET /api/technicals/PETR4` (testado ao vivo) não devolve nenhum campo `source`/`provedor` no payload — o rótulo não pode nem estar certo por acidente |
| 4 | Fonte falha → não inventa valor | parcial | ao vivo (API) | `GET /api/quotes?symbols=INVALIDO` devolve `{"price":null,"error":"sem cotacao"}` (não inventa) e a UI mostra `"—"`/`"sem cotação"` (`App.jsx:2915,2923`) — correto; mas `POST /api/buy` com ticker inexistente devolveu **HTTP 500 com stack de exceção crua** (URL da Yahoo, parâmetro `crumb`) em vez do 502 limpo esperado — ver F-UX-03 |
| 5 | Cálculo determinístico (nunca pela IA) | conforme | código | `store.buy`/`store.sell` (`server/app/store.py:530-590`) são aritmética pura; stop/alvo sugeridos pela IA aparecem como *sugestão* aplicável só por ação explícita do usuário (`App.jsx:6863-6869`, botão "Aplicar em {t}") |
| 6 | IA não promete rentabilidade/certeza | conforme | código (grep dirigido) | Nenhuma ocorrência de linguagem de garantia/certeza fora de negações (`grep -rniE "garant\|promet\|100%\|infalível..."` em `copy.js`, `disclaimers.js`, `catalog.js`, `App.jsx`, `skill_ref.py`, `conceitos.py`, `kb.py`, `mercado_ref.py`, `defaults.py` — todas as ocorrências são "não garante"/"nunca prometa" ou falsos positivos de CSS `width:100%`) |
| 7 | Toda análise de IA informa uso de dado histórico/atrasado/insuficiente | conforme | código | `skill_ref.py:54` regra 11 ("dados insuficientes ⇒ declare a lacuna"); UI usa "n insuficiente"/"aguardando o prazo" em vez de número (`App.jsx:4671-4746`) — variação do padrão canônico, não a frase literal do CLAUDE.md (ver achado UX-04 na seção de achados) |
| 8 | Sem linguagem de enriquecimento rápido/garantia de lucro | conforme | código (grep dirigido) | Mesmo grep do item 6 — zero ocorrência de "enriquec", "dinheiro rápido", "lucro certo", "sempre ganha/acerta" em qualquer arquivo varrido |
| 9 | Estados completos (carregamento, vazio, erro, mercado fechado, atrasado, rejeitada, parcial, concluída) | parcial | ao vivo (API+UI) + código | Ver matriz completa na seção `## Achados` (UX-01); 7 de 8 estados têm cobertura real, "ordem parcialmente executada" (fill parcial, não escolha de venda parcial) está estruturalmente ausente do motor |
| 10 | Acessibilidade, linguagem clara, responsividade, transparência de risco | parcial | código + cálculo de contraste | 74 `aria-`/9 `role=`/2 `tabIndex` em `App.jsx`; contraste de `textFaint` falha WCAG AA para texto pequeno nos dois temas (4.24:1 escuro, 3.68:1 claro, mínimo 4.5:1) — ver F-UX-05 |

## Achados

### UX-01 — Estados completos e transparência de dado

**Matriz de estados** (princípio 9 do CLAUDE.md) nas 4 telas principais.
Método: `vazio` e `erro/fonte indisponível` e `ordem rejeitada` foram provocados via
API real na conta `auditoria-ux@local.test`; os demais foram inferidos do código com
a chamada de API real que os alimenta (`/api/timing`, `/api/technicals`) quando
disponível.

| Estado (princípio 9) | Ativo | Carteira | Operador IA | Perfil |
|---|---|---|---|---|
| Carregamento | OK (`App.jsx:2908-2912` skeleton `.sk` na cotação; `4595,4698` "carregando…") | OK (skeleton implícito no mesmo componente de cotação reusado) | OK (`App.jsx:5567` `SweepGauge` com passos nomeados durante scan) | OK (`App.jsx:5077,5131` "carregando o diário…"/"carregando logs…") |
| Vazio | OK (`App.jsx:3268` `vazioWatchlist`; testado ao vivo — conta nova sem watchlist customizada mostra catálogo padrão, nunca tela em branco) | OK (`App.jsx:3474` "Portfólio vazio" + CTA "Ir à watchlist →", testado ao vivo: `positions:[]` na conta recém-criada) | OK (`App.jsx:2464` estado vazio da conversa com chips de sugestão) | N/A — Perfil não tem conceito de "vazio" (é configuração, sempre populado) |
| Erro / fonte indisponível | PARCIAL — cotação individual OK (`q.error` → "—"/"sem cotação", `App.jsx:2915,2923`, testado ao vivo com `symbols=INVALIDO`); ação de compra com ticker inexistente **não é limpa** — ver F-UX-03 | OK (mesmo padrão `q.error` reusado via `markPrice`) | OK (`App.jsx:3420` "IA indisponível ({r.error}) — exibindo a estimativa automática pelo seu perfil": degrada para o determinístico em vez de travar) | AUSENTE de erro de fonte de mercado (não se aplica); erros de rede em logs de observabilidade são engolidos silenciosamente por design (`App.jsx:6707,6946`: "silencioso — stale/erro não derruba a tela") — aceitável para telemetria, mas não generalizar o padrão para dado financeiro |
| Mercado fechado | OK — testado ao vivo às 09:19 (antes da abertura): `GET /api/timing/PETR4` devolveu `"foraDoPregao":true,"motivo":"Fora do pregão — sem barra nova..."`; UI mapeia para rótulo dedicado "◌ FORA DO PREGÃO" (`App.jsx:2202,2643`), distinto do genérico "sem dado" | N/A direto (carteira não tem timing por ativo na tela principal) | Indireto — mesmo dado de timing alimenta o card usado no Operador | N/A |
| Dado atrasado | PARCIAL — `barraDeOutroDia` tem rótulo dedicado "◌ AGUARDANDO 1ª BARRA" com data explícita (`App.jsx:2206,2669`, "a hora sozinha esconde que o dado é do pregão anterior"); mas a cotação (`/api/quotes`) não expõe idade da última atualização por ticker na UI do card, só a data agregada `at` da resposta — ver F-UX-01 (fonte) para o problema irmão de rotulagem | N/A | N/A | N/A |
| Ordem rejeitada | OK — testado ao vivo: `POST /api/buy` com `qty` que estoura o caixa devolve 400 "Caixa insuficiente." e `BuyModal` mostra inline "Caixa insuficiente. Disponível: {cash}" (`App.jsx:6179`) antes mesmo de enviar, pelo cálculo local `ok = cost <= data.cash` | N/A direto (rejeição acontece no fluxo de compra, que abre a partir de qualquer tela) | N/A | N/A |
| Ordem parcialmente executada | **AUSENTE** — o motor não tem conceito de fill parcial: `store.buy` sempre executa 100% da quantidade arredondada ao lote (`store.py:530-531`) ou a operação inteira é rejeitada (400 caixa insuficiente). "Venda parcial" (`App.jsx:6190-6204`, `cp.vazioHistorico`) é o usuário ESCOLHENDO vender uma fração da posição — não é o mercado preenchendo parcialmente uma ordem. O princípio 9 pede o estado; ele não existe estruturalmente. | mesmo | N/A | N/A |
| Operação concluída | OK — testado ao vivo: compra 100 PETR4 a R$42,47 seguida de venda registrou `history` com `type:"COMPRA"`/`type:"VENDA"` e `pnl` calculado (`0.0` na venda no mesmo preço); `store.public_state` devolve o estado atualizado imediatamente, sem tela intermediária de "processando" | OK (mesmo endpoint/estado alimenta a tela) | N/A direto | N/A |

**Achado consolidado desta seção:**

### F-UX-01 — Rótulo de fonte de dado fixo e incorreto no painel técnico (candlestick/indicadores)
- **Requisito:** UX-01
- **Severidade:** Crítico — viola o princípio 3 do CLAUDE.md do repo (D-02): a fonte exibida não é "a fonte", é uma string fixa que pode estar objetivamente errada.
- **Evidência:** `web/src/App.jsx:1511-1513` — `TechnicalModal` renderiza `"Fonte: Yahoo Finance" + (data.at ...)` como texto literal, sem ler nenhum campo de proveniência. | `GET /api/technicals/PETR4?period=1y` (chamada real, testada) — o payload devolvido (`t, currency, candles, indicators, summary, periodChangePct, snapshotId, snapshotAt, at`) **não contém nenhum campo `source`/`provedor`**; o backend nem tem como o front acertar por acaso. Desde a ADR-008 (11/08/2026), brapi é a fonte MASTER de candles diários e Yahoo é o backup — ou seja, o rótulo fixo está provavelmente errado para boa parte das consultas diárias, não é só "impreciso".
- **Verificação:** API real (`curl` autenticado) + leitura do caminho de render.
- **Impacto:** o usuário lê "Fonte: Yahoo Finance" no gráfico de velas/indicadores de qualquer ativo, mesmo quando o dado veio da brapi — informação de proveniência ativamente falsa, não apenas ausente. Isso é o oposto do que o princípio 3 exige.
- **Recomendação:** propagar `source`/`provedor` do `candle_provider` até o payload de `/api/technicals` (o `candle_cache`/`technical_snapshot` já carregam essa informação para o Radar, ver `App.jsx:5315` que já usa `FONTE_LABEL(candles.provedor)` em outra tela) e trocar a string fixa em `TechnicalModal` por `FONTE_LABEL(data.source)`, com fallback explícito ("fonte não registrada") se o campo faltar — nunca reafirmar "Yahoo Finance" por padrão.

### F-UX-02 — Disclaimer de operação simulada definido mas nunca renderizado no momento da decisão
- **Requisito:** UX-01
- **Severidade:** Médio — o princípio está formalmente cumprido em outros pontos da tela (banner global, rótulo "COMPRA SIMULADA"/"VENDA SIMULADA"), mas o texto específico que afirma "Nenhuma ordem real é enviada a uma corretora" não aparece no modal onde a decisão é tomada (D-04, régua explícita do 01-CONTEXT.md para este exato padrão).
- **Evidência:** `web/src/disclaimers.js:24-26` define `DISCLAIMERS.trade` ("Operação SIMULADA (paper trading). Nenhuma ordem real é enviada a uma corretora.") e `disclaimers.js:16-18` define `DISCLAIMERS.proposal` — nenhuma das duas chaves é referenciada em `web/src/App.jsx` (`grep -n "DISCLAIMERS\." App.jsx` lista 7 usos, nenhum é `.trade` nem `.proposal`) | `BuyModal` (`App.jsx:6144-6188`) mostra "COMPRA SIMULADA" como rótulo curto e uma nota sobre preço final (`App.jsx:6180`), mas nunca a frase de responsabilidade/execução.
- **Verificação:** código (grep dirigido + leitura do componente do modal de compra).
- **Impacto:** no instante de maior atenção do usuário (confirmar uma ordem), a garantia explícita "não vai para uma corretora real" não está na tela — só o rótulo "SIMULADA", que um usuário apressado pode não processar como a mesma afirmação.
- **Recomendação:** renderizar `DISCLAIMERS.trade` no `BuyModal`/`SellModal`, próximo ao botão de confirmação (uma linha, `fontSize` pequeno, mesmo padrão visual dos outros disclaimers já usados no arquivo).

### F-UX-03 — Erro de fonte de dado vaza detalhe técnico interno e sai como 500, não 502 limpo
- **Requisito:** UX-01
- **Severidade:** Alto — não inventa valor (o princípio 4 em sentido estrito não é violado), mas quebra a convenção do próprio projeto de nunca expor erro opaco/cru ao usuário e expõe detalhe de infraestrutura (D-03: já é comportamento real em produção, não hipotético — testado ao vivo).
- **Evidência:** `POST /api/buy {"t":"XXXXX9","qty":10}` (chamada real, testada) devolveu **HTTP 500** com `{"detail":"HTTPStatusError: Client error '404 Not Found' for url 'https://query1.finance.yahoo.com/v8/finance/chart/XXXXX9.SA?range=1d&interval=1d&crumb=rZaCr5Q9WJs'\n..."}` — URL do provedor e parâmetro `crumb` (efêmero, mas ainda assim detalhe interno) vazam para o cliente. | `server/app/candle_provider.py:365-379` (`get_quote`, singular, usado por `/api/buy`/`/api/sell`) chama `yahoo.get_quote` sem `try/except` — diferente de `get_quotes` (plural, usado por `/api/quotes`, linhas 382-404), que captura falha por ticker e devolve `{"price":null,"error":"sem cotacao"}`. As duas funções deveriam ter paridade de tratamento de erro e não têm.
- **Verificação:** API real (`curl` autenticado, reproduzido).
- **Impacto:** um usuário comprando um ticker mal digitado ou fora de catálogo recebe uma mensagem técnica ilegível em vez do 502 "Sem cotacao para ..." já implementado no código logo abaixo (`main.py:1508-1510`) — esse caminho de erro correto nunca é alcançado porque a exceção interrompe antes.
- **Recomendação:** envolver a chamada em `candle_provider.get_quote` (ou o `yahoo.get_quote` que ela chama) num tratamento que devolva `None`/preço nulo em vez de propagar a exceção crua, replicando o padrão já usado em `get_quotes`; isso faz o 502 limpo de `main.py:1510` ser alcançado como já era a intenção do código.

### F-UX-04 — "Ordem parcialmente executada" não existe no modelo de dados
- **Requisito:** UX-01
- **Severidade:** Médio — o princípio 9 lista o estado como obrigatório; a ausência é estrutural, não um bug pontual (D-04: risco real de o relatório de auditoria futura assumir cobertura que não existe, ainda sem incidente registrado).
- **Evidência:** `server/app/store.py:530-531` (`buy`) e `:578` (`sell`) — toda ordem é executada 100% na quantidade arredondada ao lote de 100 ou rejeitada inteira (`main.py:1512-1513`, `400 Caixa insuficiente`); não há fila, book de ofertas nem qualquer mecanismo de fill parcial. "Venda parcial" na UI (`App.jsx:6190-6236`) é a escolha do usuário de vender uma fração da posição já aberta — semanticamente diferente do estado que o CLAUDE.md pede (execução de uma ordem única que só se preenche em parte).
- **Verificação:** código (leitura de `store.py`/`main.py`) — não há caminho de API para provocar esse estado porque ele não existe.
- **Impacto:** nenhum usuário jamais verá esse estado, porque o motor não o produz; qualquer suposição de cobertura completa do princípio 9 no relatório consolidado (REPORT-01) precisa registrar esta lacuna explicitamente, não assumir "conforme" por analogia com a venda parcial.
- **Recomendação:** decisão de produto, não código — declarar explicitamente (em copy ou documentação) que a simulação é sempre "tudo ou nada" por desenho (execução instantânea ao preço de mercado, sem book), o que é defensável dado o princípio 5 (determinismo), e não fingir cobertura do estado nesta fase de diagnóstico.

### UX-02 — Consistência visual e hierarquia Estudo × Operador

**O usuário sabe em qual modo está?** Sim, de forma persistente. `Topbar`
(`App.jsx:707-753`) renderiza um "chip de modo" (ponto colorido + rótulo) **sob o
wordmark, em toda tela onde `Topbar` é montado** — não é um indicador que aparece só
no momento da troca. Comentário do próprio código confirma que essa é uma correção
deliberada de um problema anterior ("o badge de modo SAIU de ao lado do wordmark...
e virou uma LINHA de modo própria... simétrico nos dois modos").

**A troca muda tema/vocabulário de forma coerente?** Sim. `appMode` decide uma
classe CSS global (`b3-mode-operador` em `<html>`, `App.jsx:6329-6341`) que
troca a paleta de acento (`MODE_*`, comentário linha 45-48: "Brand Book v2...
DOIS EIXOS INDEPENDENTES" — tema claro/escuro × modo Estudo/Operador), o
`BottomNav` troca rótulos de aba pela fraseologia do modo (`App.jsx:774-778`,
"Watchlist/Portfólio" × "Monitoramento/Posições"), e a troca de modo dispara
`A.flash("Modo Operador ativado — reiniciando…")` seguido de reload completo
(`App.jsx:1849`) — garante que nenhuma tela fique com mistura de vocabulário dos
dois modos, ao custo de uma interrupção total da navegação a cada troca (decisão
deliberada, documentada no comentário, não um bug).

**Há tela onde os dois modos são indistinguíveis?** Não identificada nesta
verificação — o gate "Executar" do Operador Autônomo (`App.jsx:3780-3799`)
mostra "Disponível no Modo Operador — em Modo Estudo o agente só orienta, nunca
vende sozinho" com link direto para trocar, então mesmo a tela que só faz sentido
num modo comunica o modo atual.

### F-UX-05 — Troca de modo força reload completo do app
- **Requisito:** UX-02
- **Severidade:** Baixo — polimento/consistência de fluxo, sem risco de produto nem violação de princípio (D-05); a própria implementação documenta que o reload é deliberado para evitar mistura de vocabulário entre modos, então o trade-off é consciente, não um descuido.
- **Evidência:** `web/src/App.jsx:1849` — `A.flash(m === "operador" ? "Modo Operador ativado — reiniciando…" : "Modo Estudo ativado — reiniciando…")` seguido de reload completo da aplicação a cada troca de `appMode`.
- **Verificação:** código/docs (comentário do próprio arquivo confirma a intenção).
- **Impacto:** o usuário perde o contexto de navegação (tela atual, scroll, modais abertos) toda vez que alterna Estudo ↔ Operador — um custo de fricção real, mesmo sendo a opção mais segura contra estado misto.
- **Recomendação:** se a fricção incomodar em uso real, considerar re-render local do `appMode` (o mecanismo de paleta via classe CSS já é reativo, `App.jsx:6329-6341`) preservando a tela atual, em vez de reload de página inteira; baixa prioridade.

**UX-02 — Verificado e conforme:** chip de modo textual persistente ("MODO ESTUDO"/
"MODO OPERADOR", `web/src/copy.js:22,90`, não só cor) em toda tela via `Topbar`
compartilhado; paleta e vocabulário por modo consistentes; o gate crítico do
agente autônomo (vender de verdade vs. apenas sinalizar) comunica o modo atual com
link de saída — cobertura completa dentro do que este nível de verificação
permite avaliar (código + payload real, sem captura visual).

### UX-03 — Responsivo e acessibilidade básica (Ativo, Operador IA, Carteira, Perfil)

**Método:** sem Nível 1/2 (nenhum redimensionamento de viewport real nesta sessão —
limitação já declarada em `## Método de verificação`). Responsivo e alvo de toque
auditados por leitura das regras de layout no código; contraste calculado com a
fórmula de luminância relativa do WCAG 2.x a partir dos hex do `Theme` do app
(`web/src/App.jsx:60-153`), não medido em tela renderizada.

**Responsivo:** os contêineres principais usam `width:"100%"` com `maxWidth`
fixo (420-560px) e `padding` lateral consistente (`App.jsx` em dezenas de pontos,
ex.: `355,379,545,624,1909,2062,2359,3365,5842,6086,6153,6207`) — o padrão de
modal/tela é "encolhe até o `maxWidth`", que é o comportamento correto para telas
estreitas de iPhone; não foi encontrado nenhum bloco com largura fixa em `px`
maior que uma tela pequena (busca por `width: "[3-9]\d\d px"` não teve ocorrência
de bloco de conteúdo, só SVGs internos com `viewBox` proporcional). Não é possível
confirmar ausência de overflow horizontal sem renderização real — declarado como
limitação, não como "conforme".

**Alvo de toque:** botões de ação primária declaram `minHeight` explícito de
40-48px (`App.jsx:6152-6188` BuyModal `minHeight:"44px"` no botão comprar;
`3974` "Executar ciclo agora" `padding:"12px"`; `6170-6172` +/- do lote
`width/height:"42px"`) — consistente com o alvo mínimo de ~44×44pt recomendado
para WKWebView sem hover. Contraexemplo pontual: os toggles de accordion em
`App.jsx:2706,2773` (`role="button"`, ver F-UX-06) não declaram `minHeight`,
só `padding:"9px 0"` — a altura efetiva do alvo de toque depende só do texto
interno, sem piso mínimo garantido.

**Leitura de tela / semântica:** 74 ocorrências de `aria-` e 9 de `role=` em
`App.jsx` — cobertura real, não decorativa: modais usam `role="dialog"
aria-label="..."` (`2356,2487`), o switch de configuração usa `role="switch"
aria-checked aria-label"` (`313`), ícones puramente decorativos usam
`aria-hidden` (`195,2712,7488`), estados de progresso usam `role="status"
aria-live="polite"` (`5783`). Zero `<img>` no arquivo — não há caso de imagem
sem `alt` (não é um "achado ausente", é `N/A` genuíno).

**Contraste** (calculado, luminância relativa WCAG, ver F-UX-07 abaixo).

### F-UX-06 — Toggle "acordeão" com `role="button"` não responde a teclado
- **Requisito:** UX-03
- **Severidade:** Médio — risco real de exclusão de usuário que navega só por teclado/leitor de tela; ainda não materializado em incidente registrado (D-04).
- **Evidência:** `web/src/App.jsx:2706` e `:2773` — `<div onClick={onToggle} role="button" tabIndex={0}>` (toggle de contrato de opção e de seção expansível). Busca por `onKeyDown|onKeyPress` no arquivo inteiro (`grep -n`) encontra **uma única ocorrência em 7599 linhas** (`App.jsx:6098`, e é para um `<input>` de busca, não relacionada). Um `<div>` com `role="button"` e `tabIndex={0}` fica focável por Tab e é anunciado como botão por leitor de tela, mas — diferente de um `<button>` nativo — o navegador não dispara `onClick` ao pressionar Enter/Espaço nele; sem `onKeyDown` explícito, a tecla não faz nada.
- **Verificação:** código (grep dirigido + leitura dos dois pontos de uso).
- **Impacto:** um usuário operando por teclado (ou testando com leitor de tela, que também costuma ativar via Enter) consegue *focar* o toggle mas não consegue *ativá-lo* — a seção nunca abre por teclado, só por toque/clique de mouse.
- **Recomendação:** trocar o `<div role="button">` por um `<button>` nativo (herda ativação por teclado de graça, só precisa reset de estilo) ou adicionar `onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onToggle()}` nos dois pontos.

### F-UX-07 — `textFaint` abaixo do mínimo de contraste WCAG AA para texto pequeno, nos dois temas
- **Requisito:** UX-03
- **Severidade:** Médio — risco real de legibilidade para usuário com baixa visão, ainda não incidente documentado (D-04).
- **Evidência:** `web/src/App.jsx:70,87` — `textFaint: "#6f7797"` (tema escuro) sobre `bgBase: "#10121a"` calcula **4.24:1**; `textFaint: "#7a8099"` (tema claro) sobre `bgBase: "#f7f8fc"` calcula **3.68:1** (fórmula de luminância relativa WCAG 2.x, razão de contraste padrão). O mínimo AA para texto normal é 4,5:1 (3:1 só vale para texto grande ≥18pt/24px ou negrito ≥14pt/18.66px). `textFaint` é usado extensivamente em fonte pequena (10-11.5px) para conteúdo que não é decorativo: rótulos de fonte de dado (`2927,2936`), timestamps, disclaimers auxiliares e mensagens de erro secundárias (`2367,4595,4698,5077,5131`) — nenhum desses contextos qualifica como "texto grande".
- **Verificação:** cálculo real a partir dos hex do tema (não medição em tela renderizada — ver limitação do método).
- **Impacto:** usuários com baixa visão ou em ambientes de luz forte (uso mobile ao ar livre é o caso de uso típico do produto) podem não conseguir ler informação de proveniência do dado e mensagens de erro secundárias — que são justamente o conteúdo mais ligado à transparência exigida pelo princípio 3/10.
- **Recomendação:** escurecer/clarear `textFaint` até atingir ≥4.5:1 nos dois temas, ou reservar a cor atual só para texto ≥14px que já cruze o limiar de "texto grande em negrito", auditando os usos atuais um a um.

### F-UX-08 — Gate "Executar" desabilitado: aviso visível existe, mas sem vínculo semântico (`aria-describedby`)
- **Requisito:** UX-03
- **Severidade:** Baixo — o defeito original documentado em `docs/auditoria-controle-ordens-parametros.md` (depender só de `title`, invisível em toque) **já foi corrigido** no código atual; o que resta é um refinamento de acessibilidade, não uma falha funcional (D-05).
- **Evidência:** `web/src/App.jsx:3780-3799` — o botão "Executar (vende no stop/alvo)" fica `disabled` fora do Modo Operador (`desabilitado = m === "executar" && !operador"`) e, quando desabilitado, um parágrafo logo abaixo explica o motivo com link direto ("Disponível no Modo Operador — em Modo Estudo o agente só orienta, nunca vende sozinho. Trocar para Modo Operador →", `3795-3799`) — isso já resolve a lacuna visual original (comentário do próprio código, `3784-3787`, confirma que foi uma correção deliberada de qa/audit-2026-08-07). Falta apenas a ligação semântica: o botão não tem `aria-describedby` apontando para o parágrafo de explicação, então um leitor de tela que navegue direto ao botão (sem ler o texto acima) não ouve o motivo.
- **Verificação:** código (leitura direta do JSX, comparado com o achado histórico do CONCERNS.md).
- **Impacto:** menor que o originalmente documentado — o motivo é visível e alcançável na mesma tela, só não está semanticamente amarrado ao controle para quem navega por leitor de tela em ordem não-linear.
- **Possível duplicata:** CODE-03 (a faceta de dívida técnica/blast radius do mesmo gate pertence ao plano 01-03; este achado registra só a faceta de acessibilidade, já parcialmente corrigida).
- **Recomendação:** adicionar `aria-describedby` no botão apontando para o `id` do parágrafo explicativo — mudança pequena, sem risco.

### UX-04 — Copy contra as proibições do CLAUDE.md

**Varredura executada** (grep dirigido, ver comando no plano) sobre
`web/src/copy.js`, `disclaimers.js`, `catalog.js`, `App.jsx` e
`server/app/skill_ref.py`, `conceitos.py`, `kb.py`, `mercado_ref.py`,
`defaults.py`. Resultado: **zero violação real encontrada.**

**Julgamento das ocorrências (nenhuma é violação):**
- Todas as ocorrências de `garant`/`promet` são negações explícitas — "sem
  garantia de resultado", "não representa garantia", "nunca prometa lucro",
  "não garante resultado futuro" (`disclaimers.js:14,18,30,34,38`;
  `catalog.js:47,66,98,145`; `skill_ref.py:42,105,167`; `kb.py:34,412,504,1193`)
  — são o guardrail funcionando, não o problema.
- Todas as ocorrências de `100%` são falsos positivos descartados: CSS
  (`width:"100%"`, `height:"100%"`, `viewBox`), ou uso técnico correto
  ("cálculo 100% no servidor", `App.jsx:4738,4788`; "persistência 100% no
  aparelho", `catalog.js:2`; anel de confluência "0–100% = quanto o ativo bate
  com um setup", `App.jsx:1968` — mede aderência a um padrão de estudo, não
  probabilidade de acerto, e o próprio `conceitos.py:214-215` explica essa
  distinção de propósito para o usuário: "Confluência NÃO é probabilidade de
  dar certo").
- Nenhuma ocorrência de "enriquec", "dinheiro rápido", "lucro certo", "sempre
  ganha/acerta", "infalível", "nunca perde/erra" em qualquer dos 9 arquivos.

**Frase canônica "Não há dados suficientes para concluir":** não existe
verbatim em nenhum arquivo do repositório (busca direta por essa string e por
"dados suficientes" não encontra o texto exato do CLAUDE.md). A **intenção**
está implementada de forma consistente, em palavras equivalentes, em pelo
menos 3 camadas independentes:
- `server/app/skill_ref.py:54` (regra 11 do prompt de IA): "Dados
  insuficientes ⇒ não produza uma leitura definitiva; declare a lacuna."
- `server/app/assistente.py:103-105,126-132` (system prompt do assistente
  conversacional): "Se a resposta exigir um número que não está lá, diga que
  essa informação não aparece nesta tela — nunca estime..." e "Fonte
  indisponível se DECLARA, nunca se estima: sem dado fresco, diga a idade do
  que existe e pare aí."
- `web/src/App.jsx:4671-4746` (UI de eficácia/expectância): "n insuficiente"
  em vez de número, com o motivo explicado ao lado.

Isto é PARCIAL, não uma violação: o comportamento exigido pelo princípio (não
forçar conclusão sem dado) está implementado e verificado em 3 pontos
independentes do sistema; só a string literal do CLAUDE.md nunca aparece
verbatim em nenhuma tela.

### F-UX-09 — Frase canônica de dado insuficiente nunca aparece verbatim
- **Requisito:** UX-04
- **Severidade:** Baixo — a substância do princípio está implementada em 3 camadas independentes (ver acima); é uma lacuna de padronização textual, não de comportamento (D-05).
- **Evidência:** busca por "Não há dados suficientes para concluir" e por "dados suficientes" em `web/src/*.js`, `web/src/*.jsx` e `server/app/*.py` não encontra a string exata; os equivalentes funcionais estão em `skill_ref.py:54`, `assistente.py:103-105,126-132`, `App.jsx:4671-4746` (citados acima).
- **Verificação:** código/docs (grep direto).
- **Impacto:** nenhum no comportamento (o usuário sempre vê alguma declaração de insuficiência de dado quando aplicável); risco é só de inconsistência textual entre telas/vozes diferentes do produto, o que pode confundir alguém comparando o app ao texto do CLAUDE.md literalmente.
- **Recomendação:** se o CLAUDE.md pretende a frase como um padrão textual literal (não só um comportamento), padronizar as ocorrências equivalentes para usar exatamente essa string onde fizer sentido gramatical; baixa prioridade, sem risco de produto.

## Verificado e conforme

- Saldo/caixa/patrimônio sempre visíveis no `Topbar` global, testado ao vivo (princípio 1).
- `POST /api/buy` com quantidade que estoura o caixa: rejeição limpa 400 "Caixa insuficiente.", testada ao vivo, com espelho no cálculo local do `BuyModal` antes mesmo do request.
- Ciclo compra→venda completo testado ao vivo: histórico registra `COMPRA`/`VENDA` com `pnl`, sem invenção de número.
- `GET /api/timing/PETR4` fora do pregão devolve estado, motivo e ressalva explícitos; front mapeia para rótulo dedicado "FORA DO PREGÃO" distinto do genérico "sem dado" — implementação já resolveu o bug histórico documentado no próprio comentário do código (`App.jsx:2199-2206`).
- Grep dirigido por linguagem de enriquecimento/garantia/certeza em 9 arquivos (front+backend): zero violação real encontrada; todas as ocorrências de "garant"/"promet" são negações ("não garante", "nunca prometa") ou o guardrail explícito nos prompts de IA (`skill_ref.py`).
- Degradação graciosa quando a IA está indisponível: `App.jsx:3420` mostra a estimativa determinística automática em vez de bloquear o usuário — reforça o princípio 6 na prática, não só na teoria.
- Chip de modo textual persistente ("MODO ESTUDO"/"MODO OPERADOR") em toda tela, paleta/vocabulário coerentes por modo, gate do agente autônomo comunica o modo atual com link de saída (princípio implícito de clareza/UX-02).
- Modais usam `role="dialog"`+`aria-label`; switch de configuração usa `role="switch"`+`aria-checked`+`aria-label`; ícones decorativos usam `aria-hidden`; estados de progresso usam `role="status"`+`aria-live="polite"` — cobertura de semântica real, não perfunctória, em 74 pontos de `aria-`/9 de `role=`.
- Zero uso de `<img>` sem `alt` (não há `<img>` no arquivo — N/A genuíno, não uma lacuna).
- Botões de ação primária (comprar, vender, executar ciclo, +/- de lote) declaram `minHeight`/dimensão explícita ≥40px, consistente com alvo de toque em WKWebView sem hover.
- Frase canônica de dado insuficiente do CLAUDE.md: comportamento implementado em 3 camadas independentes (prompt de IA, assistente conversacional, UI de eficácia), mesmo sem a string literal em nenhuma delas (ver F-UX-09).

## Cobertura de requisitos

| Requisito | Achados | Status |
|---|---|---|
| UX-01 | F-UX-01 (Crítico), F-UX-02 (Médio), F-UX-03 (Alto), F-UX-04 (Médio) | com achados |
| UX-02 | F-UX-05 (Baixo) | com achados |
| UX-03 | F-UX-06 (Médio), F-UX-07 (Médio), F-UX-08 (Baixo) | com achados |
| UX-04 | F-UX-09 (Baixo) | com achados |
