# Site estático do Boris+

HTML/CSS/JS puro, sem build e sem CDN. Publique a pasta `site/` em qualquer hospedagem estática.

- `index.html` — home · `tour.html` — fluxo do produto com snapshots (mobile + web) · `app/` — treinamento aberto de dentro do app (tema próprio, sem navegação institucional): `app/guia.html` (guia das telas, 20 telas) e `app/conceitos.html` (10 módulos); progresso em localStorage · `suporte.html` (Support URL) · `privacidade.html` (só Termos de uso, em `#termos`; a Privacy URL é a rota `/privacidade` do servidor, fonte `server/POLITICA-PRIVACIDADE.md`).
- Visual: Brand Book v2 (`docs/brand/v2`). Fontes locais em `fonts/`.
- Snapshots em `img/` (capturados em 09/10/2026, app local, conta de teste, saldo virtual). Recapturar quando a UI mudar.
- Placeholders `[ ... ]` (classe `.ph`): razão social, CNPJ, e-mails, link da App Store, valores dos planos, texto jurídico. Substituir antes de publicar; privacidade/termos precisam de revisão jurídica.
- Testar local: `python3 -m http.server 8899 --directory site`.

## No Railway (junto do Boris)

`bash scripts/publicar-site.sh` copia `site/` para `server/site_dist`; o FastAPI serve em `/site/` (mesmo serviço). Links `/privacidade` são absolutos e só resolvem no servidor do Boris, não no `http.server` local.

Autoria: semente.dev (meta author e rodapés). Dois temas separados: site institucional (raiz, âmbar da marca) e treinamento no app (`app/`, acento do Modo Estudo).
