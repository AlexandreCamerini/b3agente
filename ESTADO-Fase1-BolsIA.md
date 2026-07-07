# Estado — Fase 1: identidade BolsIA aplicada no app

## Aplicado no app (web/src/App.jsx) — cosmético, sem mexer em lógica
- **LogoMark** novo: candlestick + spark de IA, gradiente índigo→ciano.
- **Nome público "BolsIA"** (o "IA" no gradiente da marca) no Topbar, na tela de
  abertura e no onboarding; rodapé e textos de notificação renomeados.
- **Accent índigo** (#6E56F7 dark / #5B45E0 light) substituindo o dourado, nos
  dois temas, com `onAccent` branco. positive/negative (verde/rosa) mantidos.
- **Tela de boas-vindas** deixa claro: **"Dados reais da bolsa · capital simulado"**
  + "cotações reais e dinheiro simulado, com uma IA que explica cada decisão".
- `b3-agente` segue como **codinome interno** do repo (só a camada pública mudou).

## Identidade (pasta brand/)
- `bolsia-mark.svg` (logo), `bolsia-brand-board.html` (board visual),
  `BolsIA-Brand-Kit.md` (tokens: paleta, tipografia, voz).
- Subtítulo App Store: **"Dados reais, capital simulado"** (29 car.; "IA" já no nome).

## Pendências da Fase 1 (gates)
1. **Busca formal** do nome: INPI (classes 9·41·42·36) + disponibilidade no
   App Store Connect — antes de registrar de fato.
2. **Nome de exibição no iOS**: trocar `CFBundleDisplayName`/appName do Capacitor
   para "BolsIA" (pra bater com os textos de notificação "Ajustes → … → BolsIA").
   Hoje o código já diz BolsIA; o nativo precisa acompanhar no rebuild.
3. **Device (gate do plano):** build renomeado abre sem regressão; conferir
   visual do accent índigo em telas claras/escuras, o novo logo, e a tela de
   abertura. Patrimônio/cores de mercado seguem legíveis.
