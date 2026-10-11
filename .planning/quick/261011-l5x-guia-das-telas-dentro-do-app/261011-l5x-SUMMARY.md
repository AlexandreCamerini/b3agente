---
phase: quick-261011-l5x
plan: 01
status: complete
completed: 2026-10-11
commits:
  - 51fa73bc  # Tarefa 1: fix do SW em abrirTreinamento
  - 17befcc2  # Tarefa 2: conteúdo 95 -> 57, shape novo, guardião de paridade
  - b2ad06cd  # Tarefa 3a: guiaNav.js + guiaTelas.js + vite fs.allow
  - 021843fa  # Tarefa 3b: GuiaTelas.jsx + fiação no Perfil > Ajuda
---

# Quick 261011-l5x: guia das telas dentro do app — Summary

Fix do service worker no `abrirTreinamento` web (about:blank síncrono, `update()` best-effort de 1,5 s, `?v=BUILD_ID`); guia reescrito de 95 para 57 pontos com fórmulas só do que o código confirma; folha de tela cheia in-app (`GuiaTelas.jsx`, `perfilView === "guia"`) lendo o mesmo `site/js/telas-data.js` do site.

## Contagem final por tela vs orçamento (total 57, guardião trava 50–60)

| id | antes | orçamento | final |
|----|------:|----------:|------:|
| boas | 4 | 2 | 2 |
| acomp | 8 | 4 | 4 |
| radar | 6 | 5 | 5 |
| watch | 6 | 3 | 3 |
| plano | 5 | 5 | 5 |
| ordem | 6 | 3 | 3 |
| pend | 2 | 2 | 2 |
| port | 5 | 3 | 3 |
| opc | 6 | 3 | 3 |
| opcobj | 5 | 3 | 3 |
| opcpiso | 4 | 3 | 3 |
| pior | 6 | 3 | 3 |
| payoff | 4 | 3 | 3 |
| confest | 5 | 4 | 4 |
| termo | 4 | 2 | 2 |
| opcaberta | 5 | 2 | 2 |
| boris | 4 | 3 | 3 |
| web1 | 4 | 1 | 1 |
| web2 | 3 | 2 | 2 |
| web3 | 3 | 1 | 1 |
| **total** | **95** | **57** | **57** |

Maior sobreposição Jaccard entre textos de ponto no resultado final: 0,29 (confest "Contratos e lastro" × opcaberta "Ações travadas"; abaixo do limiar 0,35). Maior texto: 231 caracteres (limite 240).

## Fontes: conferência (espelho da tabela do PLAN)

| Ponto / tema | Fonte | Status |
|---|---|---|
| opcpiso/pior/confest (perfil da estrutura) | `opcoes_payoff.py:166–286` (`perfil_da_estrutura`) | Conferido. perda_maxima = −pior resultado se negativo, senão 0; breakevens; ilimitado pela inclinação à direita. |
| idem | `opcoes_escada.py:264–297` (`_numeros`) | Conferido. `equilibrio` só com UM breakeven; `piso` = strike da PUT comprada; `teto` = strike da CALL vendida. |
| idem (pernas) | `opcoes_escada.py:224–242` | Conferido. |
| opcobj / payoff teto (proteger/renda/collar) | `opcoes_escada.py:49–63`, `:326–347` | Conferido (`TERMOS_OBJETIVO`: proteger, renda, collar; `_frase_risco` com/sem piso). |
| plano:Régua (alvo) | `setups.py:191–197`, `:209–216` (`_alvo_rr`) | Conferido: alvo = gatilho ± 2×\|gatilho − invalidação\|, fallback 2×ATR. `_alvo_rr` é usada em 9 pontos; IFR2 usa máxima dos 2 candles anteriores (`:295–302`). Texto diz "em vários setups", não "em todos". |
| plano:Régua (R:R mínimo) | `skill_ref.py:30–34` (1,5 / 2,0) | Valores conferidos. **Divergiu a citação** `agent.py:468–498`: ali `RR_MINIMO` só barra a EXTENSÃO do alvo dinâmico, não a entrada. A regra "plano abaixo de 1,5 não é montado" está em `setups.py:623` e `:699–701` (`plano_operacional` devolve plano vazio com motivo). Texto do guia: "Retorno abaixo de 1,5× o risco não vira plano", sem dizer que "o Operador recusa". |
| radar:Card do ativo (anel) | `setups.py:70–73`, `:485`; `sinal.js:53–60` | Conferido. `_confluencia` = round(100 × soma pesos ok ÷ soma pesos); `MIN_CONFLUENCIA = 50`. `sinal.js:53–60` é só o rótulo do anel (`rotuloAnel`). Texto antigo ("aderência em dados passados") substituído. |
| radar:Como o Radar analisa | `regime.py:219` (`_TIER`), `:256+` (`ranquear`); **`setups.py:569`** | **Divergiu a citação.** `setups.py:569` ordena os SETUPS de UM ativo por confluência (`sorted(... -confluencia)`), não o ranking do Radar. O ranking é `regime.py:313–320`: (tier do regime, momentum relativo, rank de elegibilidade, gatilho alinhado, confluência só como desempate final, ticker). O PLAN dizia "tier de regime e confluência"; o código vence: o texto diz regime → momentum relativo, confluência só desempata. |
| plano:Regime | `regime.py:56–66`, `:80–140` | Conferido. SMA200 (SMA50 não confiável com < 200 candles); ADX14 ≥ 25 tendência, < 20 lateral, 20–25 tratado como lateral. |
| radar:Período em uso | **`technical_models.py:231`**, `:283`; `regime.py:63`; `App.jsx` | `technical_models.py:231` e `:283` conferidos (`first_252`, `change252dPct`), mas medem a variação de 252 pregões do SNAPSHOT, não a janela da varredura. A janela da varredura é `candles.PERIOD_BARS` (`"1y": 252`, `candles.py:14–20`) via `resolve_keep` (`scanner.py:273`, `periodBars` em `:362`); o selo mostra "PERÍODO EM USO: 1A · N pregões" (`App.jsx:8240` na época, hoje ~`:8252` região). Linhas do App.jsx derivaram (+12): rótulo ~`:7954`, seletor ~`:8689`. Texto: "1 ano = 252 pregões, mostrados no selo", sem fórmula de variação. |
| plano:Amostra insuficiente | `signal_ledger.py:31–35` | Conferido (`MIN_N_JANELA = 40`). |
| radar:Cobertura | `App.jsx` (`{res.scanned}/{res.universeSize} ativos varridos · N sem dados`, hoje `:8252`); `scanner.py:350`, `:363–364` | Conferido (universeSize = len(uni), scanned = len(results)). Texto sem números de exemplo. |
| ordem:Quantidade | `finance.js:408–422` (`sizingPlano`) | Conferido. capital × pct% (padrão 1, teto 5) ÷ risco por ação, piso em lote de 100. |
| ordem:Custo estimado | grep em `store.py`/`finance.js` | Sem corretagem/emolumento/slippage no código de ordem. O ticket calcula `cost = q.price × qty` (`App.jsx:8893`) e avisa "Caixa insuficiente". Texto: "Preço × quantidade", sem afirmar nada sobre taxas. |
| ordem:Tudo ou nada | `store.py:719` (`buy`), `:755` (`sell`); CLAUDE.md C-14 | Conferido (linhas aproximadas; regra é a do CLAUDE.md). |
| pend:Ordem pendente / Caixa reservado | `pending_orders.py:12–20`, `:83–88` | Conferido (reserva caixa na compra, posição na venda; `caixa_reservado` delega a `store`). |
| acomp:Curva do patrimônio | `finance.js:279–329` | Conferido (curva, retAcum e drawdown da mesma janela). |

### Put protetora (conferência pedida)

`opcoes_escada._numeros([{"tipo":"PUT","lado":"compra","strike":28.0,"premio":1.2}], 100, 30.0)`:
- `total.perdaMaxima = 320.0` (esperado 320.0, bateu); `equilibrio = 31.2` (esperado 31.2, bateu); `piso = 28.0`.
- Contra-provas: piso 31 → perda 20,0 (= (30−31+1,2)×100); piso 32 (> pm + prêmio) → perda 0,0 e `equilibrio = None`. Por isso o texto usa a forma fechada com a condição explícita (piso acima de preço médio + prêmio: perda máxima zero, sem equilíbrio).

## Textos antigos corrigidos

- Radar "Card do ativo": "O anel mede aderência ao padrão em dados passados" (errado) → anel = confluência (peso dos critérios atendidos hoje ÷ peso total; < 50% o setup não conta; não mede a chance de dar certo).
- Radar "Como o Radar analisa": "ordena por confluência, quantos sinais independentes" (errado) → regime, depois momentum relativo; confluência só desempata.
- Cobertura: sem "62 de 65" nem fração de exemplo (guardião barra `N de M`).
- Régua: R:R 1,5 agora atribuído a `setups.py:699`, não ao Operador.
- Duplicatas removidas: "Operador IA" ficou só em acomp; "Card do ativo" só em radar; pior/opcpiso/confest/opcaberta sem repetição; `guard` das 20 telas removido; duplicata do aviso no `p.note` de `guia.html` removida (aviso fica só no `.appfoot` do site e no rodapé da folha do app).

## Guardiões

Novos: `web/tests/test_sw_update.mjs` (9 casos), `web/tests/test_guia_dados.mjs` (paridade site↔web via `node:vm`, `validarGuia`, sanidade da métrica, fonte única), `web/tests/test_guia_nav.mjs` (navegação, progresso v:2, layout 375×667/812 e 1024×768, câmera, swipe).

Atualizado com nota datada "2026-10-11 (quick 261011-l5x)": `web/tests/test_guia_treinamento_link.mjs`. A asserção "web: window.open noopener, sem await antes do clique" virou 4 (open síncrono antes do primeiro await, `opener = null`, `atualizarServiceWorker` no ramo web, `?v=` + BUILD_ID); "tile do guia abre guia.html" virou 2 (tile chama `onOpen("guia")` + App renderiza `<GuiaTelas` em `perfilView === "guia"`; `GuiaTelas.jsx` sem Browser.open/window.open/dangerouslySetInnerHTML e com DISCLAIMERS). Nenhuma asserção apagada sem substituta.

## Testes rodados (cwd `web/`, exceto indicado)

| Teste | Resultado |
|---|---|
| test_sw_update.mjs | ok (9/9) |
| test_guia_treinamento_link.mjs | ok |
| test_guia_dados.mjs | ok |
| test_guia_nav.mjs | ok |
| test_ui_onda_j.mjs | ok |
| test_pet_ui.mjs | ok |
| test_boris_intro.mjs | ok |
| test_conceito_ui.mjs | ok |
| test_pwa_navigate_denylist.mjs | ok |
| `server/.venv/bin/python -m pytest server/tests/test_site_dist.py` | 5 passed |
| `node --check site/js/guia.js`; sem `.guard`/`c[0]`/`c[6]` | ok |
| `npx vite build` (após cada tarefa e no fim) | ok; `dist/assets` com exatamente 20 capturas |
| build SSR de checagem do loader (`$TMPDIR`, apagado) | 20 telas, todas com URL de captura |
| renderToString de `GuiaTelas` (build SSR temporário, apagado) | renderiza ("Guia das telas", "PONTO 1 DE 2", "1/20") |
| `git diff` em `navStack.js` | vazio (intocado); `overlayLivre` intocado |

NÃO rodados (por instrução): suíte canônica `scripts/executar.sh --testes`, `cap copy ios`, bump/publicar, push.

## Desvios do plano

1. **[Rule 1 - citação errada no PLAN]** `setups.py:569` e `agent.py:468–498` citados na tabela Fontes não sustentavam o que o texto diria; corrigidos na conferência (ver tabela acima). `technical_models.py:231` estava certo como linha, mas descreve outra grandeza que a "janela da varredura"; o texto do guia usa `PERIOD_BARS`.
2. **Calibração, frase imprecisa do PLAN.** O PLAN dizia que 0,35 "barra todos eles" (os 5 duplicados nomeados). Correção: o limiar 0,35 barra acomp×port (0,74), ordem×opc (0,56), acomp×web1 (0,47), web1×web3 (0,46) e ordem×pend (0,38). O par port×web3 de 0,33 NÃO é barrado pelo limiar; ele deixou de existir pelo corte de conteúdo (web3 "Operador IA" e "Resultado aberto" cortados, "Patrimônio total" reescrito só com o que difere). Registrado também no comentário de `guiaDados.js`.
3. **Escopo da sobreposição da missão.** `validarGuia` compara a missão apenas com textos da MESMA tela (como o PLAN manda); pares de pontos são comparados entre todas as telas.
4. **`irParaTela(e, i, telas)`** recebeu o terceiro parâmetro `telas` para o clamp superior (o PLAN listava só `(e, i)`).
5. **Sem Rule 4.** Nenhuma mudança arquitetural.

## Limitações

- Progresso do guia não é compartilhado entre site e app no iOS (`capacitor://` tem localStorage próprio); mesma chave `boris-guia-v1`, payload `v:2`.
- Progresso antigo (sem `v:2`): missão descartada, teste mantido.
- +~2,4 MB de capturas no bundle (emitidas pelo Vite, fora do precache do Workbox).
- `site_dist`/`web_dist` NÃO republicados; `telas-data.js?v=9` e `guia.js?v=8` só valem após `publicar-site.sh` (decisão do Alex).
- Não validado em navegador real/aparelho: layout 375px e ≥900px foi validado por teste puro (`layoutGuia`) e render SSR, não visualmente.
- Tile "Conceitos de mercado" continua dependente de `/site/app/` e do fix do SW.

## Human-check (Alex, a 375px e em ≥900px)

- Perfil → Ajuda → Guia de treinamento abre a folha; captura inteira acima da dobra (44px de topo, captura ~55% da área útil).
- ‹ › e swipe horizontal trocam de ponto; o fim da tela mostra "Na prática" (missão + teste).
- Swipe de borda / voltar do sistema / Esc / ✕ fecham.
- Seletor "N/20 ▾" lista as telas por grupo, com ✓ nas concluídas.
- Em modo avião no iOS, as capturas continuam aparecendo.
- ≥900px: captura à esquerda, folha à direita, sem rolagem da página.
- Web com SW antigo: Perfil → Ajuda → Conceitos de mercado abre a página do treinamento, não a casca do app.

## Self-Check: PASSED

- Arquivos: `web/src/swUpdate.js`, `guiaDados.js`, `guiaNav.js`, `guiaTelas.js`, `GuiaTelas.jsx`, `web/tests/test_sw_update.mjs`, `test_guia_dados.mjs`, `test_guia_nav.mjs` existem; `site/js/telas-data.js`, `guia.js`, `app/guia.html` alterados.
- Commits 51fa73bc, 17befcc2, b2ad06cd, 021843fa presentes no `git log`.

## Verificação do orquestrador (2026-10-11)

- Suíte canônica (`bash scripts/executar.sh --testes`, após `npx cap copy ios`): rc=0, 3463 pytest + todos os `web/tests/*.mjs`.
- 1ª rodada acusou `test_carimbo_servidor_rodape.mjs` (3 falhas): falso positivo causado por comentário novo com `/site/app/*` — o `/*` literal abria bloco no strip de comentários do guardião. Corrigido só o texto do comentário (f43e0044); guardião intocado. `test_ios_assets.mjs` falhava só por falta de `cap copy ios` antes da suíte.
- Conferência visual em harness local (Vite dev, componente isolado com os tokens `.b3-theme-dark` do app): 390x844 — captura no topo, ponto embaixo, spotlight sobre o elemento, cartão "Na prática" com missão + teste; 1024x700 — lado a lado sem rolagem (scrollHeight = 700). Navegação ‹ › e seletor de tela funcionando.
- Observado: a captura `13-opcoes-pior-caso` já vem cortada à direita no próprio arquivo (não é o enquadramento); entra no item existente de refazer as capturas de Opções. Em ≥900px a captura de celular ocupa a coluna inteira (~594px), maior que o tamanho real — opcional limitar a largura.
- Pendente do Alex: conferência no iPhone (swipe entre pontos × gesto de borda) e publicar (`publicar-site.sh` + `bump.sh`/`publicar-web.sh`).
