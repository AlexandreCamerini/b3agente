---
quick_id: 261009-rso
status: complete
---
# Quick 261009-rso — Guia das telas + página institucional

Entregue em `site/`: `guia-telas.html` + `js/guia.js` + `js/telas-data.js` (20 telas, cada uma com marcadores, "o que dá para fazer", missão prática e teste rápido) + `css/guia.css`; `tour.html` reescrito como "O app por dentro" (`css/app.css`) com os 11 passos com capturas e novas seções; canvas (`tour.js`/`tour.css`) removido; subnav Conceitos × Guia em treinamento.html; nav/rodapés atualizados; `server/site_dist` republicado; `test_site_dist.py` cobre as páginas novas.

Verificação: sem overflow horizontal a 390px nas 6 páginas; guia percorrido por script (20/20 telas, quiz errado→certo, missões, 0 erros de console); links/âncoras/imagens sem quebra; 0 URLs externas.

Pendências: marcadores estimados à mão (conferir); cotas e planos como placeholder; capturas de opções vêm de provedor mock; deploy (bump SERVER_BUILD_ID, push, publicar-web) com o Alex.
