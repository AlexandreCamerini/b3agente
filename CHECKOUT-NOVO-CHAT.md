# CHECKOUT — retomada em novo chat (BolsIA)
*Gerado em 09/07/2026 · estado: build F9-20260709-4 pronto para instalar · pendências = qa/26*

## 1. Estado exato do projeto

- **Código/git:** tudo commitado e enviado (`main == origin/main`). Backend no
  Railway redeploya no push. Suítes: **219 pytest + 21 web — verdes**.
- **Entrega:** `bash entregar.sh "msg"` faz a cadeia inteira (testes → git →
  build → cap sync → patch do AppDelegate → espelho de chunks → verificação de
  carimbo) e abre o Xcode. `bash entregar.sh --so-verificar` só audita.
- **Carimbo de build (protocolo obrigatório):** `web/src/version.js` →
  aparece no rodapé do Perfil e no `/api/health`. NENHUMA avaliação funcional
  vale sem o carimbo conferido no aparelho. Atual: **F9-20260709-4**.
- **Último evento:** o bundle do iPhone foi AMPUTADO por um bug do entregar.sh
  (chunks de import dinâmico apagados → "plugin não instalado", app quebrado).
  Corrigido + guardião de paridade. O usuário estava prestes a rodar o
  `entregar.sh` do reparo e reinstalar.

## 2. PENDÊNCIAS — o que ainda NÃO foi validado (fonte: `qa/26-matriz-revalidacao.md`)

Todos os 26 itens da matriz aguardam validação no aparelho COM o carimbo
F9-20260709-4 (as falhas relatadas antes — notificações mortas, botão de
permissão sumido, identidade parcial — eram consistentes com o bundle
amputado e precisam ser RE-testadas no build íntegro):

- **A · Notificações (A1–A6):** permissão (inclusive pós-reinstalação — botão
  Pedir permissão agora aparece também em "denied"), toggle, banner em
  foreground (fix do "alert"→banner/list), agendada 30s com app fechado,
  push APNs (callbacks do AppDelegate reaplicados) e teste de push com reason
  traduzido. ⚠️ A5/A6 dependem das envs APNs no Railway (chave "Sandbox &
  Production", `APNS_SANDBOX=1` p/ build de Xcode).
- **B · Identidade/Modo Operador (B1–B7):** troca completa (tema verde
  #22c55e do mock, chip sólido, gráficos verdes, abas/filtros renomeados),
  persistência após reboot e após login/logout (fix local-first no iOS),
  volta ao Estudo restaurando tudo.
- **C · IA nas duas vozes (C1–C5):** N1 mesa × professor (cache por modo),
  stop/alvo por modo, skills selecionáveis pelo NOME (skill × skillOperador),
  prompts editáveis por modo.
- **D · Conta/Login (D1–D4):** form único Welcome=modal, logout com reset
  completo + welcome, Apple com nome/relay explicado, e-mail real após
  recompartilhar consentimento (servidor agora atualiza no relogin).
- **E · Plataforma (E1–E4):** ícone/splash do BolsIA, sem zoom ao focar
  campo, produção embutida no boot, logs na Observabilidade.

**Como reportar no novo chat:** só as falhas, formato `A5 FALHA — <o que viu>`.

## 3. Armadilhas conhecidas (não redescobrir)

1. `web/ios/` e `web/dist/` são GITIGNORADOS. A pasta ios/ é regenerável — o
   AppDelegate PERDE os callbacks do APNs quando isso acontece; o
   `scripts/ios-patch-appdelegate.sh` (idempotente) reaplica e o entregar.sh
   o chama sempre. Guardião: `test_push_wiring.mjs`.
2. O Vite gera VÁRIOS `index-*.js` (chunks de import dinâmico). NUNCA apagar
   por padrão de nome; órfão = o que não existe no `dist/` atual. Guardião:
   `test_ios_assets.mjs` (paridade só quando os carimbos coincidem).
3. A URL do Railway é SÓ API (deploy sobe apenas `server/`). Telas mudam
   APENAS via entregar.sh + Xcode (⇧⌘K + Run).
4. Detector de carimbo usa o formato `F<fase>-<AAAAMMDD>-<n>` (minificado
   contém strings tipo `F900-` que já causaram falso positivo).
5. iOS local-first: estado do servidor NUNCA sobrescreve o doc do aparelho
   (auth.me/login). Guardião: `test_copy_theme.mjs` (seção N2).
6. Regras do projeto: baseline verde antes de mexer, causa-raiz primeiro,
   patch cirúrgico + 1 guardião por bug, hard stop no aparelho, docs em qa/.

## 4. Histórico (1 linha por fase; detalhes nos qa/)

- **F5** (qa/18): watchlist via Radar, push callbacks, login hardening,
  observabilidade, cache candles em SQLite, scripts.
- **F6** (qa/19): servidor de produção embutido, formatação N1, toggle do
  Operador-servidor, central de notificações, reasons APNs.
- **F7.1** (qa/20): Modo Operador — plano determinístico (R:R≥1,5, decisões),
  termo, sizing.
- **F8A** (qa/21): "alert"→banner/list (causa real do banner mudo), aud em
  lista no login Apple, logout com reset de escopo.
- **F8B** (qa/22–25): dois-apps-em-um completo (copy.js 35+ chaves, tema por
  modo até nos gráficos, prompts/skills por modo, login unificado, paleta do
  mock, e-mail relay).
- **F9/9.1**: protocolo de entrega com carimbo (entregar.sh), patch
  automático do AppDelegate, reparo do bundle amputado + paridade de chunks.

## 5. Prompt pronto para o novo chat

```
Contexto: leia CHECKOUT-NOVO-CHAT.md e qa/26-matriz-revalidacao.md na raiz do
repo b3-agente. Regras do projeto valem (baseline verde, causa-raiz, guardião
por bug, carimbo de build antes de qualquer avaliação, docs em qa/).

Estado: build F9-20260709-4 instalado e confirmado no rodapé do Perfil.
[SE NÃO: rode 'bash entregar.sh "retomada"' + Xcode ⇧⌘K + Run primeiro.]

Resultado da matriz qa/26 no aparelho:
- <liste aqui APENAS as falhas, ex.: A5 FALHA — timeout aos 15s>
- <...>

Tarefa: para cada falha, diagnostique a causa-raiz (Logs do servidor,
Diagnóstico do app, console [b3]), corrija cirurgicamente com teste-guardião,
rode as suítes completas e feche com qa/27 + roteiro de hard stop. Ao final,
rode 'bash entregar.sh --so-verificar' e me passe o novo carimbo.
```
