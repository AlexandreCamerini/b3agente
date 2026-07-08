# QA 23 — FASE 8B: "Dois apps em um" completo (B1+B2+B4) + revisão de UX
*08/07/2026 · baseline verde antes de mexer (19 backend + 20 web)*

## B2 — Identidade visual por modo
- Como TODA a UI lê `var(--x)`, o Modo Operador virou um OVERRIDE de variáveis
  (`.b3-mode-operador` por cima de `.b3-theme-dark/light`): acento
  **verde-mercado #22c55e** (light: #15803d), fundos grafite mais frios, tints
  e knobs coerentes — nenhum uso de `T.x` mudou.
- Chip permanente **"MODO OPERADOR"** ao lado da marca no Topbar (some no
  Estudo); `<meta theme-color>` acompanha o modo (status bar/PWA).
- **Transição suave só na troca**: classe temporária `b3-mode-switch` (~450ms)
  anima cores na mudança de identidade sem pesar nas interações normais.

## B1 — Fraseologia por modo (copy.js em produção)
- `ctx.cp = copyFor(appMode)` no root; migrado para o dicionário: saudação e
  resumo do dia do Acompanhar (professor convida a estudar × mesa conta planos
  válidos/gatilhos), títulos e subtítulos (Radar → "Mesa de oportunidades";
  Watchlist → "Monitoramento"; Portfólio → "Posições"), rótulos da NAVEGAÇÃO,
  botões (Simular compra/venda × Registrar entrada/saída; Aprofundar com IA ×
  Plano da mesa), empty states, toasts de compra/venda e rodapé do Perfil.
  Disclaimer do Radar já trocava por modo (F7.1).
- copy.js agora com **25 chaves espelhadas** (novas: toastVenda, notifAlvo*,
  notifVar*). Validação executável: chaves idênticas, vocabulário de ordem
  proibido no ramo Estudo, fallback seguro.

## B4 — Tratamento e notificações por modo + N3 PRO
- Notificações locais de stop/alvo/variação com título e corpo na voz do modo
  (professor: "bom momento para estudar o que mudou" × mesa: "Execute a saída
  na corretora — o plano manda" / "Realize a parcial e suba o stop").
- **Bug real corrigido:** `_ai_apply_managed` recriava a config gerenciada e
  DESCARTAVA o `appMode` — para usuários da IA gerenciada, a mesa falava como
  professor. O modo agora viaja junto (vale para N1/N2/N3).
- **N3 (stop/alvo da carteira):** no modo operador, o prompt configurável do
  usuário ganha a camada de mesa por cima (GUARDRAILS_PRO + tom direto, R:R
  explícito, conclusões canônicas) sem mudar o formato do array (o popup já
  parseia).

## Revisão de UX (dois modos)
Implementado nesta rodada (plataforma):
- **Zoom automático do Safari eliminado**: inputs/select/textarea a 16px — o
  clássico "pulo de tela" ao focar um campo no iPhone.
- **Flash cinza de toque do iOS removido** (`-webkit-tap-highlight-color`).
- Botões sem seleção acidental de texto (`user-select:none`).
- Transição de identidade na troca de modo (acima).
Já auditado e mantido (bom): focus-visible ring, reduced-motion, skeletons,
pull-to-refresh com engate, safe-areas, alvos ≥42px nos botões primários,
scroll contido nos modais.
Backlog de UX sugerido (não bloqueia): haptics nativos na troca de modo e nos
toasts (Capacitor Haptics), tabela de posições com colunas fixas no landscape,
e revisão de contraste dos textos 10.5px no tema claro.

## Guardião novo
`web/tests/test_copy_theme.mjs` — 24 asserções cobrindo B1 (telas sem texto
sensível hardcodado), B2 (override de tema/chip/theme-color/transição), B4
(notificações por modo, managed preserva appMode, N3 mesa) e as prevenções de
UX (16px, tap-highlight).

## Evidência
- Backend: 19 suítes offline verdes · py_compile OK.
- Web: **21/21 suítes** · JSX OK.
- Pendente (hard stop): troca Estudo↔Operador no aparelho — paleta, chip,
  nav, saudação, botões e notificações mudam juntos; voltar restaura tudo.
