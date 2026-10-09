---
quick_id: 261009-s9s
status: complete
---
# Quick 261009-s9s — link no Perfil → Ajuda

Feito: `abrirGuiaTreinamento` + tile "Guia de treinamento" depois do Glossário (web/src/App.jsx); guardião test_guia_treinamento_link.mjs (9 asserções).

Verificação: `npx vite build` ok; web/tests/*.mjs 0 falhas; no app (porta 5181 com /site proxiado), o tile aparece em Ajuda no Modo Operador e o clique chama window.open("/site/app/", "_blank", "noopener"). Caminho nativo (Browser.open) verificado só por teste estático, não em aparelho.

Pendências do Alex: publicar-web.sh (o SW publicado precisa da denylist /site para não sequestrar a navegação), bump de SERVER_BUILD_ID, push; iOS só recebe no próximo build (cap copy ios); checar no iPhone o browser in-app e o "Voltar ao app" (aponta para "/", que no browser in-app abre o web app).
