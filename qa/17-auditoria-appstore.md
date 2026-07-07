# QA 17 — FASE 4 · Bloco 3: auditoria final + checklist App Store
*07/07/2026 · status: ✅ pronto · 🔧 corrigido nesta fase · ✋ ação do Alex*

## A) Auditoria de código e robustez

| Item | Status | Evidência |
|---|---|---|
| Suítes completas | ✅ | 24 backend + 12 web verdes; 4 ⏭️ conhecidas (httpx) passam no pytest do Alex |
| Timeouts de rede | ✅ | `api.js`: AbortController, 15s padrão / 90s IA |
| Tela branca | ✅ | ErrorBoundary global no `main.jsx` (C1) com recarregar + detalhe técnico |
| Falha de rede degrada | ✅ | `loadErr` com tela acionável; Radar/watchlist com stale fallback silencioso |
| Offline | ✅ | `sync.js`: cache otimista + outbox; para no 1º erro transitório, descarta 4xx |
| Estados vazios | ✅ | fluxo `novato`, "Sua watchlist está vazia", welcome testado (`test_welcome`) |
| KPIs fonte única | ✅ | tudo via `finance.js` (portfolioMetrics/equityCurve); snapshot escreve de `m.patr` |
| Venda / closures | 🔧 | bug 1.1 corrigido; classe blindada por `test_wiring_deps.mjs` |
| Popup Leitura IA | 🔧 | 1.4: fecha (✕/rodapé/tap fora), rola contido, colapsáveis, prompt conciso |
| Preço defasado no log de análise | 🔧 | `quotes` nas deps do A (mesma correção 1.1) |

## B) Checklist de submissão App Store

### Conta, identidade e conformidade
- ✋ **App ID** `com.alexandrecamerini.bolsia` registrado com Push + Sign in
  with Apple (migração de identidade — Parte A do LOGIN-SOCIAL.md confere).
- ✅ Sign in with Apple presente e ACIMA do Google (4.8); e-mail relay tratado.
- ✅ Exclusão de conta in-app (5.1.1(v)) **com revoke SIWA** no servidor.
- ✅ Disclaimers educacionais centralizados (`disclaimers.js`) no banner do
  app, em todo output de IA, em stop/alvo, operação simulada e Radar.
- ✋ **Política de privacidade**: texto pronto em `POLITICA-PRIVACIDADE.md` —
  publique (GitHub Pages do repo resolve: Settings → Pages) e cole a URL no
  App Store Connect → App Privacy → Privacy Policy URL.

### App Privacy ("nutrition labels") — declarar EXATAMENTE isto
- **Dados coletados, vinculados ao usuário, SEM tracking:**
  - Contact Info → Email Address (conta; Apple relay possível) — App Functionality
  - Identifiers → User ID (escopo dos dados) e Device ID (token de push) — App Functionality
  - User Content → "Other User Content" (carteira SIMULADA, watchlist,
    histórico de estudo) — App Functionality
- **Não coletados:** localização, contatos, financeiro REAL, saúde, fotos,
  histórico de navegação, dados de terceiros para anúncios.
- **Tracking:** NÃO (sem ads, sem compartilhamento) → "Data Not Used to
  Track You". Sem ATT prompt (não usar).
- Nota BYOK: a chave OpenAI do usuário fica na configuração dele e é usada
  só para as chamadas dele; já coberto no texto da política.

### Build e assets
- ✋ Ícone iOS: rodar `bash scripts/gen-assets.sh` e conferir o 1024×1024
  (App Store) sem alpha; launch screen já vem do template Capacitor com o
  fundo `#0b0e14`.
- ✋ Screenshots: mínimo 6,7" (iPhone Pro Max) e 6,1"; sugestão de sequência:
  Radar com chip da varredura do dia → Leitura da IA (resumo+colapsáveis) →
  Portfólio com PlanRuler → Operador IA → Perfil/Observabilidade. Capture no
  simulador com dados de demonstração.
- ✋ Versão/build: sugerido `1.0.0 (1)` no Xcode (General → Identity).
- ✋ **`APNS_SANDBOX`**: REMOVER do Railway ao subir para TestFlight (builds
  TestFlight usam APNs de produção) — testar o push de novo por lá.
- ✅ Permissões: o app só pede NOTIFICAÇÕES (sem string de Info.plist
  exigida) — nada de câmera/localização/tracking para justificar.

### Ficha da loja (proposta pronta — colar no App Store Connect)
- **Nome:** `BolsIA`
- **Subtítulo (≤30):** `Simule a bolsa e aprenda com IA`  *(29 caracteres)*
- **Categoria:** primária **Educação**, secundária **Finanças** — o produto é
  um simulador educacional sem dinheiro real; a categoria certa reduz
  fricção da revisão de apps financeiros e casa com a postura CVM.
- **Classificação etária:** 4+ (sem apostas simuladas — paper trading
  educacional não pontua no questionário; sem conteúdo sensível).
- **Palavras-chave (≤100):**
  `bolsa,acoes,simulador,paper trading,investir,analise tecnica,educacao financeira,ia`
- **Descrição (rascunho):**

> Estude a bolsa brasileira sem arriscar um centavo. O BolsIA é um simulador
> educacional de paper trading: cotações reais, dinheiro 100% simulado e uma
> IA que explica o raciocínio por trás de cada leitura técnica.
>
> • RADAR DIÁRIO — uma varredura automática por dia útil encontra condições
> técnicas no mercado e a IA traduz em linguagem didática.
> • APRENDA O PORQUÊ — indicadores, setups e cenários explicados passo a
> passo, com os critérios presentes e ausentes de cada padrão.
> • OPERE SEM RISCO — monte carteira simulada, defina stop e alvo de estudo
> e acompanhe a evolução do seu patrimônio virtual.
> • OPERADOR IA — deixe o simulador aplicar suas regras de proteção sozinho
> e receba notificações do que aconteceu, com o motivo.
> • SUA CONTA, SEUS DADOS — entre com Apple ou Google e continue de onde
> parou em qualquer aparelho; ou use sem conta nenhuma.
>
> O BolsIA é uma ferramenta EDUCACIONAL: não faz recomendações de
> investimento, não envia ordens reais e não garante resultados. Conteúdo
> gerado por IA com base em dados passados serve para ensinar o raciocínio —
> decisões com dinheiro real são suas e merecem um profissional habilitado.

### Revisão Apple — respostas prontas (App Review notes)
- ✋ Conta de demonstração: crie um usuário e-mail (`review@` + senha) com
  carteira simulada populada e cole em App Review Information.
- Nota sugerida ao revisor: "Educational paper-trading simulator. No real
  money, no brokerage connection, no investment advice (fixed educational
  vocabulary enforced server-side). AI features interpret pre-computed
  technical data only."

## C) Pendências que NÃO bloqueiam a submissão
- Plugins de login sob Capacitor 8: validar `npm install` (LOGIN-SOCIAL C2).
- Push em produção via TestFlight (após remover `APNS_SANDBOX`).
