# Quick Task 261011-l5x: Guia das telas dentro do app — Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Origem:** design critique da sessão de 2026-10-11 (guia publicado em `/site/app/guia.html`, medido a 375x812 e por script sobre `site/js/telas-data.js`). Opção A aprovada pelo Alex; também aprovou cortar pontos de navegação e o aviso por ponto.

<domain>
## Task Boundary

Três entregas, nesta ordem de dependência:
1. **Fix do service worker** — usuário web com SW instalado antes do denylist `/^\/site/` recebe a casca do app ao abrir `/site/app/*.html`.
2. **Reescrita do conteúdo** de `site/js/telas-data.js` (95 → ~55 pontos), com fórmulas conferidas no código.
3. **Componente React in-app** (folha de tela cheia) lendo os mesmos dados; o tile "Guia de treinamento" (Perfil → Ajuda) abre a folha em vez de `Browser.open`/`window.open`.

FORA de escopo: unificar `conceitos.html` com `server/app/kb.py` (fica para depois); refazer capturas; publicar/deploy (Alex decide depois).
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### SW (entrega 1)
- Evidência: em produção `sw.js` já tem `denylist:[/^\/admin/,/^\/ios/,/^\/site/]`, mas um navegador com SW antigo ativo serviu a casca do app em `/site/app/guia.html`; após `registration.update()` + navegação nova, o guia abriu. `fetch` direto devolve o HTML certo (o problema é só navegação interceptada).
- Com o guia in-app, o tile do guia não abre mais URL. Mas o tile "Conceitos de mercado" continua abrindo `/site/app/conceitos.html` → o fix ainda é necessário em `abrirTreinamento` (web): `await navigator.serviceWorker?.getRegistration()?.update()` best-effort (com timeout curto, nunca bloqueia a abertura) e URL com `?v=<BUILD_ID>` (query nova não muda a regra do denylist, mas o update garante o SW novo). Planner decide a combinação mínima eficaz; documentar o porquê em comentário (estilo do repo: comentário carrega a decisão).

### Conteúdo (entrega 2) — achados medidos
- 42 de 95 pontos: explicação reescreve a frase curta (sobreposição ≥60% de palavras). Frase vai no cartão, explicação na lista → mesma coisa duas vezes.
- "Operador IA" em 4 telas (acomp, port, web1, web3), até 100% igual. `ordem:Mercado fechado` ≈ `pend:Ordem pendente`. "Card do ativo" em radar e opcaberta. `ordem:Operação simulada` ≈ `opc:Aviso fixo`.
- Campo `guard` das 20 telas: ~8 variações de "educacional/virtual/não é recomendação" → vira UM rodapé fixo do guia.
- Missões copiam os pontos no imperativo (ex.: boas). Missão nova = resultado verificável (ex.: "monte um plano em que o risco fique abaixo de 1% do orçamento").
- Remover pontos de navegação pura (Voltar, Confirmar/cancelar, Editar e atualizar, Perfil e ajustes etc.).
- **Formato fixo** para ponto que fala de número/conceito: *o que é → como se calcula (1 linha) → como usar na decisão*. ≤ ~220 caracteres. Sem aviso legal dentro do ponto.
- **Nenhum número/fórmula sem fonte no código.** Conferir: pior caso / equilíbrio / piso / prêmio / collar (motor de opções em `server/app/`, `store.py`), régua do plano (invalidação/gatilho/alvo, R:R) em `setups.py`/`plan.js`, anel de confluência (`setups.py`/`technical_snapshot.py` — o que o % mede), regime (`regime.py`), período 252 pregões, cobertura da varredura (`scanner.py`). Se a fórmula do código diferir do rascunho da critique, o CÓDIGO vence. Se não der para confirmar, o ponto descreve sem fórmula — nunca inventa.
- Estrutura dos dados: hoje cada ponto é `[frase, x%, y%, w%, h%, título, explicação]`. Com a folha nova não há mais cartão de vidro com frase + lista com explicação: basta título + texto. Planner decide o novo shape (ex.: `[x,y,w,h,titulo,texto]` ou objeto), mantendo coordenadas existentes dos pontos que ficam.
- Rascunhos aprovados como direção (ajustar ao código):
  - Régua: "Invalidação é o preço em que a tese deixa de valer — é onde fica o stop. Gatilho confirma a entrada; alvo é a saída planejada. Compare (alvo − gatilho) com (gatilho − invalidação): abaixo de 1,5 para 1, o plano paga pouco pelo risco."
  - 252 pregões: "≈ 1 ano de negociação na B3. Janela longa capta a tendência principal e reage devagar; curta reage rápido e erra mais. Sinal vale para a janela em que foi medido."
  - Pior caso/equilíbrio (put protetora): pior caso = (preço médio − piso + prêmio) × quantidade; equilíbrio = preço médio + prêmio — CONFERIR.
  - Cobertura: "62 de 65 lidos: os 3 sem dado ficam fora do ranking, sem nota estimada. Cobertura baixa = ranking incompleto, não mercado sem oportunidade."
- Usar a skill do projeto `didatica-boris` (vocabulário por modo, princípios de dado).

### Componente in-app (entrega 3)
- Folha de tela cheia React, montada no bundle (offline no iOS — Capacitor carrega bundle local, sem `server.url`).
- Layout a 375px: topo 44px com seletor "3/20 ▾" (substitui faixa de miniaturas) + ✕; captura ~55% da altura com câmera/spotlight centralizando o ponto, SEM cartão de vidro por cima; folha inferior ~45% com título + texto e ‹ › (+ swipe horizontal) entre pontos; ao fim dos pontos de cada tela, cartão "Na prática" (1 missão + 1 teste). ≥900px: captura à esquerda, folha à direita, sem rolagem de página. Rodapé único com o aviso (dinheiro virtual, educacional).
- Fecha por swipe/voltar reaproveitando o mecanismo da Onda J (quick 261010-f50).
- Progresso: localStorage com try/catch (como o guia web faz hoje) — planner confere a chave usada em `site/js/guia.js` e decide se reaproveita.
- Acessibilidade: alvos ≥44px, `aria-label` nos botões de seta, foco preso na folha, `prefers-reduced-motion` desliga a animação da câmera.

### Claude's Discretion
- Como compartilhar a fonte única de dados entre `site/` (sem build, `window.TELAS`) e `web/src` (Vite). Opções: (a) dados num `.json` em `site/js/` + `telas-data.js` vira loader/gerado; (b) módulo em `web/src/` e `site/js/telas-data.js` gerado por script em `scripts/publicar-site.sh`; (c) outra. Requisito: um único arquivo editável + guardião de teste que trava a paridade. ATENÇÃO: o nome `TELAS` já existe em `web/src/telas.js` (navegação do app) — usar outro nome (ex.: `GUIA_TELAS`).
- Onde ficam as imagens no bundle (`site/img` = 2,9 MB). Copiar para `web/public/guia/` ou importar via Vite; pesar se convém comprimir. Não duplicar fonte editável.
- Manter a página web `/site/app/guia.html` funcionando com os dados novos (paridade); não precisa redesenhá-la além do necessário para o shape novo.
</decisions>

<specifics>
## Specific Ideas / Constraints

- `abrirTreinamento` em `web/src/App.jsx` ~linha 2981; tiles em ~3223/3228.
- `web/src/main.jsx:67-70` registra o SW (`virtual:pwa-register`, `immediate: true`).
- `App.jsx` tem ~7600 linhas / ~164k tokens: NUNCA ler inteiro (Grep + Read com offset/limit). Preferir componente em arquivo próprio (ex.: `web/src/GuiaTelas.jsx`) e função pura de navegação/estado testável (padrão `operadorIA.js`).
- Guardiões existentes que podem tocar: `server/tests/test_site_dist.py`, `web/tests/test_pwa_navigate_denylist.mjs`, testes de swipe da Onda J. Guardião não se apaga; reversão deliberada atualiza com nota datada.
- Asset cache bust em `site/app/guia.html` (`telas-data` v8, `guia.js` v7, `guia.css` v6): subir se mudar.
- Validação: guardiões tocados + teste novo da paridade de dados + teste puro da navegação + `npx vite build` (cwd `web/`). A suíte canônica roda UMA vez pelo orquestrador ao final (fora do sandbox). Não rodar `cap copy ios`.
- Disco do Mac está apertado (~1,7 GB livres): não instalar dependências novas; não criar worktree.
- Não publicar (sem `bump.sh`/`publicar-*`): publicação é decisão do Alex.
</specifics>

<canonical_refs>
## Canonical References
- `./CLAUDE.md` (princípios 1-10, guardrails, paridade, estratégia de execução)
- `.claude/skills/didatica-boris/SKILL.md`
- `.planning/quick/261010-f50-*` (Onda J: swipe/voltar fecha modais)
- `.planning/quick/261010-f51-*/261010-f51-SUMMARY.md` (cartão do Operador IA, `web/src/operadorIA.js`)
- `.planning/quick/261010-r6i-refazer-capturas-do-guia/` (capturas e `t.nh`)
- `site/js/guia.js`, `site/js/telas-data.js`, `site/css/guia.css`, `site/app/guia.html`
</canonical_refs>
</content>
</invoke>
