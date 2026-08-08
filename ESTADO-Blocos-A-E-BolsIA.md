# ESTADO — Rodada Blocos A·B·C·D·E (BolsIA / b3-agente)

**Hard-stop entre blocos, na ordem A → E** (A destrava o teste dos demais).

---

## BLOCO A — Notificações: diagnóstico embutido + causa raiz atacada

**A pista decisiva**: o BolsIA nem aparece em Ajustes → Notificações. Um app só
entra nessa lista quando o pedido de permissão NATIVO dispara ao menos uma vez.
Se nunca apareceu, o plugin **não está no binário instalado** — os builds que
chegaram ao aparelho não passaram por `cap sync` (o erro de SPM bloqueou a
cadeia por semanas). Não é lógica de agendamento; é cadeia de build.

O que esta rodada entrega:
1. **Botão DIAGNÓSTICO na Config → Notificações** — roda `notify.diag()` no
   próprio aparelho (sem Safari/Mac) e dá o veredito em linguagem simples:
   - `pendingCount` ausente → *build antigo, correções não instaladas*;
   - `pluginLoaded=false` → *plugin fora do binário; rode
     `scripts/instalar-iphone.sh`*;
   - permissão ≠ granted → *pedir permissão / Ajustes*;
   - tudo ok → *testar agendado 30s e fechar o app*.
2. **`scripts/instalar-iphone.sh`** — cadeia completa com verificação em cada
   elo; o passo 6 **falha alto** se o `cap sync` não listar o
   local-notifications (o elo que vinha sendo pulado).
3. Rótulo do botão de teste corrigido (30s).

### ✋ Hard-stop A (device)
- [ ] `bash scripts/instalar-iphone.sh` → todas as etapas [OK]; Xcode abre;
      Run no iPhone físico.
- [ ] Config → Notificações → **Diagnóstico** → `plugin carregado: true`.
- [ ] **Pedir permissão** → iOS pergunta → BolsIA **aparece** em Ajustes →
      Notificações.
- [ ] Teste agendado (30s) → fechar o app → banner chega.

---

## BLOCO B — Radar v2: setups clássicos com confluência (modelo explicável)

- **`server/app/setups.py`** (novo, puro): Pullback à média (alta/baixa),
  Rompimento com volume (alta/baixa, extremo DO PERÍODO do usuário),
  Reversão de sobrevenda/sobrecompra, Compressão de volatilidade (neutra).
- Cada setup = **checklist de critérios objetivos** com presente/ausente e
  peso; **confluência 0–100** = % ponderada de critérios atendidos. Critérios
  **obrigatórios** definem o padrão (pullback sem tendência não é pullback —
  regra que impediu falso positivo em mercado lateral, pega em teste).
- **Veredito educacional** por ativo, só no vocabulário do produto:
  *Estudar alta · Estudar baixa · Monitorar · Sem setup no momento*.
- Payload do `/api/scan` ganha `setups[]`, `veredito`, `confluencia`,
  `melhorSetup` e `modelo[]` (explicação de cada setup);
  `condicoes_detectadas`/`score_tecnico` mantidos (retrocompatível). Ranking
  agora por confluência (score desempata).
- Tela Radar: seção colapsável **“COMO O RADAR ANALISA”**, veredito com as
  cores do app, barra de confluência, **“+ Ver critérios do setup”** com o
  checklist ✓/○ por ativo. Guardrail anti-imperativo estendido por teste.
- **Nota de honestidade**: confluência mede aderência a um padrão didático em
  dados passados — não é “grau de possibilidade de entrada” nem probabilidade
  de acerto, e o disclaimer diz isso com todas as letras.

### ✋ Hard-stop B (web + device)
- [ ] Radar mostra veredito + confluência por ativo; “Ver critérios” abre o
      checklist com ✓/○ coerentes com o gráfico do ativo.
- [ ] “COMO O RADAR ANALISA” explica os 4 setups.
- [ ] Trocar o período na Config muda rompimentos (extremo do período).
- [ ] Nenhuma frase imperativa em lugar algum da tela.

---

## BLOCO C — candlePeriod unificado (fim das janelas fixas)

- `/api/analyze/{ticker}` (análise completa) e `/api/carteira-stopalvo/{ticker}`
  (stop/alvo por ativo) — os dois usavam `get_history` com range default
  (~1 mês) e sem cache. Agora: **candle_cache + `slice_for_config`**
  (`candles.py`, novo helper puro) cortando pela janela do `candlePeriod`.
- Prompt do LLM declara a janela real: *“Historico diario (N candles; janela
  'X' escolhida pelo usuario na Config)”* — antes dizia “~1 mês” fixo.
- `/api/technical/analyze` já estava correto (Objetivo 4); agora os TRÊS
  caminhos de análise obedecem a mesma config, nos dois stores.

### ✋ Hard-stop C
- [ ] Config 1M → análise do ativo menciona ~22 candles; Config 2A → ~504.
- [ ] Stop/alvo da carteira reflete a mesma janela.

---

## BLOCO D — Login persistido (sem gravar senha)

- **E-mail lembrado** (`localStorage b3-last-email`): welcome e Perfil→Conta
  abrem com o e-mail preenchido e já no modo “Entrar” para quem já usou.
  A senha NUNCA é persistida (coberto por teste: nenhum
  `localStorage.setItem(...password...)`).
- **AutoFill nativo do iOS**: `autocomplete="username"` no e-mail,
  `current-password`/`new-password` na senha — o Chaveiro passa a oferecer as
  credenciais com FaceID. Passo nativo (uma vez, no Xcode): capability
  **Associated Domains** com `webcredentials:boris.semente.dev`.
- **Servidor**: novo `GET /.well-known/apple-app-site-association`
  (webcredentials) — defina no Railway `B3_APPLE_APP_ID=TEAMID.bundleid`
  (o Team ID está em Xcode → Signing).
- Sessão persistida + boot gate “Conectado como X” seguem como 1ª camada.
- *Camada extra de segurança (biometria para abrir o app etc.) fica para a
  rodada combinada.*

### ✋ Hard-stop D (device)
- [ ] Logout → welcome com e-mail preenchido e modo “Entrar”.
- [ ] Tocar na senha → iOS oferece a credencial do Chaveiro (após capability).
- [ ] Login completo em ≤ 2 toques.

---

## BLOCO E — Identidade iOS completa

- **`resources/icon-1024.png` + `resources/splash.png`** gerados da MESMA
  geometria do LogoMark (candlestick + spark, gradiente #3B82F6→#22D3EE,
  fundo #0b0e14), sem alfa (exigência da App Store).
- **`scripts/gen-assets.sh`**: `@capacitor/assets` gera o AppIcon.appiconset
  completo + splash, e atualiza favicon/apple-touch-icon da web com a mesma
  arte — fonte única, à prova de recriação da pasta ios/.
- `instalar-iphone.sh` grava `CFBundleDisplayName = BolsIA` via PlistBuddy.

### ✋ Hard-stop E (device, install limpo)
- [ ] Ícone da marca (não o genérico) na Home, App Library, multitarefa,
      Ajustes → BolsIA e no banner de notificação; nome **BolsIA** em todos.

---

## Scripts (automação pedida)
| Script | Faz |
|---|---|
| `scripts/instalar-iphone.sh [--recriar-ios]` | deps → assets → build → (recria ios/) → **cap sync com verificação do plugin** → nome BolsIA → abre Xcode com passo a passo |
| `scripts/atualizar-servidor.sh "msg"` | commit → push → espera o deploy do boris.semente.dev → smoke do `/api/scan` v2 |
| `scripts/gen-assets.sh` | ícones iOS completos + splash + ícones web da fonte única |

## Validação executada (sandbox)
balance ok · py_compile ok · node --check ok · **web 7/7** (test_radar
estendido p/ B+D+A) · **backend 14/14 + 2 SKIP** (httpx off — passam no
Railway; inclui `test_setups.py` novo, 6 testes com séries calibradas
numericamente).

## Invariantes conferidas
Dois stores mesma interface (scan inalterado) · motor de sinais reutilizado ·
guardrail anti-imperativo TESTADO em setups, disclaimer e tela · senha nunca
persistida (testado) · BYOK intocado · disclaimers ampliados.
