---
quick_id: 261009-mvb
status: complete
---
# Quick 261009-mvb — site junto do Boris

Feito: mount `/site` em `server/app/main.py`; `scripts/publicar-site.sh`; `server/site_dist` (25 arquivos, 1,5 MB); denylist `/^\/site/` em `web/vite.config.js` + guardião `test_pwa_navigate_denylist.mjs`; `server/tests/test_site_dist.py` (5 testes); site/ aponta Privacy para `/privacidade`.

Verificação: test_site_dist + test_politica_privacidade 12 passed; `npx vite build` ok; suíte pytest 3462 passed, 1 failed (`test_fuso_dias_ate_vencimento::test_proposta_de_fechamento_tambem_recebe_o_dia_de_brasilia`, reproduzido idêntico com minhas mudanças em stash: pré-existente, sensível a horário, ~00h BRT); 100% dos web/tests/*.mjs ok.

Pendências do Alex: bump manual de SERVER_BUILD_ID + push (deploy só-backend); `publicar-web.sh` para o SW novo com a denylist (sem isso, quem já tem o PWA instalado abre o shell do app em /site/); definir Marketing/Support URL = `<domínio>/site/` e `/site/suporte.html`, Privacy URL = `/privacidade`; placeholders e termos.
