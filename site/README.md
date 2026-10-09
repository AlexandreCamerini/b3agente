# Site estático do Boris+

HTML/CSS/JS puro, sem build e sem CDN. Publique a pasta `site/` em qualquer hospedagem estática.

- `index.html` — home · `tour.html` — fluxo do produto com snapshots (mobile + web) · `treinamento.html` — material interativo (10 módulos, laboratórios e quizzes; progresso em localStorage) · `suporte.html` (Support URL) · `privacidade.html` (Privacy URL; `#termos`).
- Visual: Brand Book v2 (`docs/brand/v2`). Fontes locais em `fonts/`.
- Snapshots em `img/` (capturados em 09/10/2026, app local, conta de teste, saldo virtual). Recapturar quando a UI mudar.
- Placeholders `[ ... ]` (classe `.ph`): razão social, CNPJ, e-mails, link da App Store, valores dos planos, texto jurídico. Substituir antes de publicar; privacidade/termos precisam de revisão jurídica.
- Testar local: `python3 -m http.server 8899 --directory site`.
