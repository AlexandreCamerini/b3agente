---
phase: quick-261010-r6i
plan: 01
status: complete
commits: []
---

# Quick 261010-r6i: capturas do guia refeitas (cartão do Operador IA)

## O que mudou
- `site/img/08-portfolio.jpg` refeita: 780x1775 (era 780x1688). Viewport 390x915 só nesta tela, para caber cartão + métricas + estado vazio + "Ver histórico de operações" (a missão do guia pede para abri-lo); faixa vazia de 55px cortada.
- `site/img/web-portfolio.jpg` (800x500) e `site/img/web-acompanhar.jpg` (800x500) refeitas.
- `site/js/guia.js`: altura natural da captura passa a vir de `t.nh` (fallback 1688/500 como antes). `site/js/telas-data.js`: tela `port` declara `nh: 1775`. Sem isso a câmera do guia distorceria a imagem nova.
- `telas-data.js`: pontos reancorados nas telas `port` (5), `web3` (3: patrimônio total e resultado aberto, a segunda linha de métricas fica abaixo da dobra a 800x500) e `web1` (+1 ponto "Operador IA"); missões de `web1`/`web3` ajustadas.
- `site/index.html` e `site/tour.html`: `height="1688"` → `1775` na `08-portfolio.jpg`.
- `site/app/guia.html`: `?v=5` → `?v=7` (telas-data e guia.js; guia.css ficou em `?v=6`).
- `server/site_dist` republicado por `scripts/publicar-site.sh`.

## Verificação
- Pontos conferidos no guia servido localmente: spotlight de cada ponto cai sobre o elemento medido na captura (port 5/5, web1 4/4, web3 3/3).
- `server/tests/test_site_dist.py`: 5 passed. `web/tests/test_pwa_navigate_denylist.mjs`: ok. `diff -rq site server/site_dist`: sem diferença.

## Lacunas conhecidas
- `site/img/02-acompanhar.jpg` (mobile) NÃO foi refeita: com o cartão novo, "Resumo do dia" e "Curva do patrimônio + vazio explicado" não cabem juntos em 390x844 (nem em viewport mais alto, que o painel escala fora do padrão 2x). A imagem atual não mostra o cartão mas segue correta no que mostra. Decisão do Alex: manter assim, ou aceitar recortar/re-pontuar essa tela.
- A tela `web-portfolio` mostra só a primeira linha de métricas; caixa disponível e em posições ficam abaixo da dobra a 800x500 (o caixa segue visível no cabeçalho).
- As demais capturas (01–17, web-plano-setup) seguem de 09/10/2026 e mostram o cabeçalho sem mudança; não foram conferidas uma a uma.
- Valores: conta de teste nova, R$ 10.000 virtuais, mercado fechado (sábado), cotações de Yahoo/brapi do momento.

## Não feito (decisão do Alex)
- Sem push e sem publicar. `site_dist` está republicado no working tree; ir ao ar exige bump de `SERVER_BUILD_ID` e push (deploy só-backend).

## Incidente durante a captura
- O painel do navegador embutido mudou de estado sozinho duas vezes (Modo Operador ativado com "Termo aceito", e navegação para `/site/app/guia.html`). O usuário compartilha esse painel; não foi uma ação desta sessão. A conta era descartável e o banco temporário foi apagado.
