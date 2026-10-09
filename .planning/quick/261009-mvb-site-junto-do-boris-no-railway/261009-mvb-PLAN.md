---
quick_id: 261009-mvb
description: Servir o site estático (site/) junto do Boris no Railway, em /site/
---
# Quick 261009-mvb
Padrão admin_dist/ios_dist: `server/site_dist` (tracked) copiado de `site/` por `scripts/publicar-site.sh`; `app.mount("/site")` antes do catch-all; `/^\/site/` no navigateFallbackDenylist do PWA; guardiões `test_site_dist.py` + denylist. Privacy URL = rota `/privacidade` existente (fonte única `POLITICA-PRIVACIDADE.md`); site/privacidade.html vira só Termos. Fora de escopo: push, deploy, bump de SERVER_BUILD_ID, republicar web_dist.
