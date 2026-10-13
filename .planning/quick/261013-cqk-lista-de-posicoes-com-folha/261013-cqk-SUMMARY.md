---
phase: quick-261013-cqk
plan: 01
status: complete
---

# Quick 261013-cqk: Lista de posições + folha (opção B) — SUMMARY

Status: completo. Leva 1 (Tarefas 1 e 2) e Leva 2 (Tarefas 3 e 4) feitas.

## Leva 1

### Commits
- 8eba50a5 `feat(quick-261013-cqk)`: proximidade do plano no backend (Tarefa 1)
- 2c87ed07 `feat(quick-261013-cqk)`: proximidade no estado principal, helpers puros e copy (Tarefa 2)

### Verifies
- `cd server && .venv/bin/python -m pytest tests/test_cartao_proximidade.py tests/test_cartao_posicao.py tests/test_carteira_leitura_rota.py -q` -> 59 passed.
- Cada um separado, `node`: test_lista_posicoes_logica.mjs, test_cartao_posicao_espelho.mjs, test_cartao_v6_logica.mjs, test_fase461_logica.mjs, test_copy_theme.mjs -> todos ok.
- `server/.venv/bin/python -m pytest tests/test_skill_ref.py -q` -> 49 passed.
- `grep -cE "[-+*/] *(a|b)\.(resultado|dias)" web/src/listaPosicoes.js` -> 0.
- NÃO rodados (por instrução): suíte canônica, vite build, cap copy ios, guardiões de App.jsx.

### Backend
- `LIMIAR_PROXIMIDADE = 0.75` e `_proximidade(avg, stop, alvo, preco, pos_plano)` em `server/app/cartao_posicao.py`; `leitura_plano` grava `r["proximidade"]` ("perto_stop" | "perto_alvo" | None) logo após `posicaoNoPlano`. Rota e main.py sem diff.
- persistence.js NÃO tocado: serverStore e deviceStore só delegam `carteiraLeitura` à mesma rota; paridade por construção.
- Testes: `server/tests/test_cartao_proximidade.py` (25 casos da tabela, limiar monkeypatch 0.9, chaves antigas, inf/nan) + `test_leitura_proximidade_perto_stop` em test_carteira_leitura_rota.py.

### Desvios
- Tarefa 1/2 TDD: testes e implementação foram escritos na mesma passada, sem rodar o RED isolado e sem commit `test(...)` separado (um commit por tarefa, como pedido). Os testes cobrem todos os casos da spec.
- Nenhum guardião existente precisou de substituta nesta leva (as fixtures `lp()` não têm `proximidade`). As extensões em test_cartao_posicao_espelho.mjs (NEUTRAS +10, ESPECIFICAS +2) e test_cartao_v6_logica.mjs levam a nota `2026-10-13 (quick 261013-cqk)`.
- Mudança intencional: com estrutura de opções e dentro do plano, `estadoPrincipalV6` agora devolve `estado_perto_stop`/`estado_perto_alvo` (antes null). Guardiões de App.jsx não rodados nesta leva; a leva 2 deve conferir se algum trava essa mudança.

### Interfaces para a Leva 2

`web/src/listaPosicoes.js` (puro; importa `estadoPrincipalV6`):
- `export const NIVEIS_ATENCAO = Object.freeze({ RISCO:0, PERTO_STOP:1, VENCE_5_DIAS:2, SEM_PLANO:3, PERTO_ALVO:4, LEITURA_INDISPONIVEL:5, DEMAIS:6 })`
- `export const CRITERIOS_ORDEM = Object.freeze(["atencao","resultado","vencimento"])`
- `prioridadeAtencao({ p, estrutura, leituraPlano, situacaoPlano } = {}) -> { nivel: 0..6, chip }`; `chip` = `{ tipo:"estado", chave, vals, tom, glifo }` | `{ tipo:"vencimento" }` | `null`. `p` pode ser null (avulsa). `situacaoPlano` in "ok"|"carregando"|"desatualizada"|"falha".
- `ordenarLinhas(linhas, criterio) -> novo array`; linha = `{ t, nivel, resultado, dias }` (resultado/dias number|null; qualquer outro campo da linha é preservado). Critério desconhecido/ausente = "atencao". "resultado" = pior (menor) no topo, null no fim; "vencimento" = dias crescentes (negativo primeiro), null no fim; empate por `t`.

`estadoPrincipalV6({ p, estrutura, leituraPlano })` (estruturaCard.js), ramos novos no plano completo, depois de abaixo_stop/acima_alvo e antes de estado_dentro, só com `posicaoNoPlano === "dentro"` e leitura não desatualizada, com ou sem estrutura:
- `leituraPlano.proximidade === "perto_stop"` -> `{ chave:"estado_perto_stop", vals:{}, tom:"atencao", glifo:"⚠" }`
- `leituraPlano.proximidade === "perto_alvo"` -> `{ chave:"estado_perto_alvo", vals:{}, tom:"info", glifo:"◎" }`
Texto via `cartaoPosicaoTxt(modo, chave)` (ChipEstadoV6 já resolve; `corTom` já cobre atencao/info).

Chaves de copy novas em `COPY[modo].cartaoPosicao` (espelho em `skill_ref.CARTAO_POSICAO`):
- Neutras: `estado_perto_stop`, `estado_perto_alvo`, `ordenar_aria`, `ordenar_atencao`, `ordenar_resultado`, `ordenar_vencimento`, `selo_estrutura` ("+ {nome}"), `selo_so_opcoes`, `linha_faixa` ("Piso {piso} · Teto {teto}"), `folha_aria` ("Detalhe da posição {ticker}").
- Específicas por modo (vals `{ticker, resultado, estado}` / `{ticker, resultado}`): `linha_aria`, `linha_aria_sem_estado`.

### Não verificado em runtime (a registrar na Leva 2)
Esc, foco devolvido, voltar/swipe, arrastar a alça, z-index sobre compra/venda/stop-alvo: só guardião estático.

## Leva 2

### Commits
- 5209c11c `feat(quick-261013-cqk)`: lista compacta de posições, folha de detalhe e camada posicao (Tarefa 3: App.jsx, navStack.js)
- 00eebf69 `test(quick-261013-cqk)`: guardiões substitutos da lista/folha e guardião novo test_lista_posicoes_ui (Tarefa 4)

### O que mudou
- navStack.js: `"posicao"` é o primeiro item de `ORDEM_CAMADAS` (z 45, a mais baixa); comentário de z-index atualizado.
- `BottomSheet` ganhou prop `zIndex` (default 1000; Indicadores técnicos não mudou).
- `CartaoPosicao`: props `naFolha`/`onFecharFolha`; `useState(!!naFolha)`; rodapé fecha a folha quando `naFolha`; espaçador do FAB só `aberto && !naFolha`.
- Componentes novos entre `CartaoPosicao` e o bloco da Fase 46-06 (dentro da fatia do guardião transversal): `textoChipAtencao`, `ChipsOrdenacaoPosicoes`, `ChipAtencaoLista`, `MiniReguaLista`, `textoFaixaLista`, `CorpoLinhaLista`, `LinhaPosicao`, `LinhaPernaAvulsa`.
- `CarteiraScreen`: hooks novos (`ordem`, `abertaT`, `abertaExiste` + 3 efeitos) todos antes do `return (`; modelo `linhas = data.positions.map((p) => {...})` e `modeloAvulsa(t)`; lista ordenada por `ordenarLinhas`, avulsas depois; `folha` com `<BottomSheet zIndex={45}>` + scroller (`CONTENT_MAX_WIDTH`) + `CartaoPosicao naFolha` (ou `CartaoPernaAvulsa`). Hero, aviso de opções, concentração, `LinhaChamadaOpcoes` e estado vazio intactos; `id={"posicao-" + p.t}` preservado.
- App: `posicaoNav`/`posicaoFecharRef`, `"posicao"` em `estadoNav.modais` (só tab carteira + carteiraView main), `fecharCamada.posicao`, ctx `reportarNavPosicao`/`registrarFecharPosicao`, `overlayLivre ... && !posicaoNav`.
- Nenhuma conta financeira nos componentes novos: ordem/chip vêm de `listaPosicoes.js`, mini-régua só por `dominioRegua`/`posRegua`.

### Guardiões alterados (asserção antiga -> substituta; todos com nota `2026-10-13 (quick 261013-cqk)`)
| Arquivo | Antiga | Substituta |
|---|---|---|
| test_ui_onda_j.mjs | `ORDEM_CAMADAS === ["catalog",...,"tech"]` | mesma lista com `"posicao"` na frente; + 3 casos (prof 1, posicao abaixo de sell, subirNivel fecharModal); + `"posicao: () =>"` na lista do `fecharCamada`; + P2 `reportarNavPosicao:`/`registrarFecharPosicao:` e `posicaoNav && "posicao"` |
| test_boris_intro.mjs | regex `overlayLivre: ... && !borisIntroOpen,` | mesma regex terminando em `&& !borisIntroOpen && !posicaoNav,` |
| test_carteira_perna_avulsa.mjs | `<CartaoPernaAvulsa` nos 900 chars após `avulsas.map((t) =>` | `<LinhaPernaAvulsa` nesses 900 chars + `<CartaoPernaAvulsa` presente no corpo de `CarteiraScreen` (folha) |
| test_ritmo_sp.mjs | `componentesV6` sem a lista | + `ChipsOrdenacaoPosicoes`, `ChipAtencaoLista`, `MiniReguaLista`, `LinhaPosicao`, `LinhaPernaAvulsa`, `CorpoLinhaLista` |
| test_ui_onda_g.mjs | `maxWidth: CONTENT_MAX_WIDTH` 2x | 3x (scroller da folha) |
| test_lista_posicoes_ui.mjs | (novo) | forma da lista/folha/camada, anti-loop (strings e índice dos hooks < primeiro `return (`), sem lógica de proximidade nos componentes, paridade `carteiraLeitura` nos dois stores |

Nenhum outro guardião do loop travou o card grande (test_cartao_v6_*, estrutura_card_ui, fase461_ui, concentracao, fase21, curadoria, lastro, pet_ui, conceito_ui, opcoes_consolidacao_ui passaram sem mudança, inclusive test_cartao_posicao_enxuto com o espaçador condicional). Nada foi apagado.

### Verifies
- `npx vite build` (cwd web/) -> ok, antes e depois da Tarefa 4.
- Tarefa 3: 9 guardiões (transversal, fechado, aberto, enxuto, opcoes_tira, estrutura_card_ui, fase461_ui, hero_reconciliado, posicao_stop_alvo) -> todos ok, cada um separado.
- Tarefa 4: loop dos 28 arquivos, cada um separado -> f=0 (todos ok) na rodada final. Primeira rodada: falharam só os 4 esperados (onda_j, boris_intro, perna_avulsa, onda_g) + o guardião novo ainda inexistente; ritmo_sp falhou após a extensão por `marginLeft: "auto"` em `CorpoLinhaLista`, corrigido (desvio abaixo).
- NÃO rodados (por instrução): suíte canônica, `cap copy ios`, publicação, push. pytest do backend não foi tocado nesta leva.

### Desvios
- `CorpoLinhaLista` (componente extra, não previsto) concentra o botão de 2 andares; `LinhaPosicao`/`LinhaPernaAvulsa` o alimentam. `LinhaPernaAvulsa` recebe `{ t, e, modoLeitura, ... }` e calcula `linhasResultadoV6({ estrutura: e })` por dentro (o PLAN listava `res` como prop). Avulsa sem estrutura mostra o texto de leitura (`lendo`/`indisponivel`) ou "—" no lugar do valor.
- Ajuste de ritmo (variação % alinhada à direita via `flex: 1 1 auto; textAlign: right` em vez de `marginLeft: auto`) entrou no commit da Tarefa 4, não no da Tarefa 3, porque só o test_ritmo_sp estendido o acusou.
- Mini-régua usa `dominioRegua([stop, alvo, avg, preco])` (inclui PM e preço para não sair do trilho); largura mínima 64px.
- Vencimento: o chip de vencimento da linha usa o texto `cp.chipVence*` do card (mesma fórmula), em estilo âmbar.

### Não verificado em runtime
Só coberto por guardião estático; conferir no iPhone/PWA com conta com posições:
- Esc fecha a folha; foco volta para a linha tocada.
- Voltar do sistema e swipe de borda fecham a folha (fiação `fecharCamada.posicao`).
- Arrastar a alça fecha; tocar fora fecha.
- z-index das camadas abertas de dentro da folha (compra/venda 50, stop/alvo 55, conceito 86) por cima da folha (45); PetFab e folha proativa de conceito somem sob a folha.
- Cabeçalho sticky do card dentro do scroller da folha; rolagem do scroller em tela pequena e em tela grande (maxWidth 720).
- Layout das duas linhas em telas estreitas (quebra de chips), ordenação ao tocar nos chips.

### Follow-ups
- Se o Alex preferir "Resultado" com melhor no topo (hoje pior no topo, decisão I1), é troca de um comparador e de um caso de teste.
- Persistir `ordem` em localStorage é opcional e ficou fora.
- Rodar a suíte canônica (`bash scripts/executar.sh --testes`) e `cap copy ios` no orquestrador antes de publicar.

## Verificação do orquestrador (2026-10-13)
- Gate entre levas: verifies da leva 1 re-rodados pelo orquestrador (108 pytest + guardiões do card) antes de disparar a leva 2.
- Suíte canônica após a leva 2: pytest 3493 passed; 2 .mjs fora do loop do executor falharam — test_estrutura_card_contraste (linhas da lista usavam `varsCartaoV6(themeKey, modo)`; voltou à forma literal travada) e test_fase20_fundacao_visual (CONTENT_MAX_WIDTH 2→3, substituta datada).
- App local (preview `api-qa-opcoes`, mercado forçado aberto, banco local de dev; conta de teste local criada para isso), 390x844, Modo Estudo: lista com BBAS3 "⚠ Perto do stop do plano" no topo (stop = PM → régua stop→alvo) e PETR4 "✓ Dentro do plano"; folha abre o card enxuto; Esc fecha e devolve o foco à linha; voltar do sistema fecha a folha (em ritmo humano — sequência scriptada < 1 s entre Esc, reabrir e voltar dessincroniza a reconciliação de histórico da Onda J; comportamento pré-existente, não desta task); "Simular venda" abre a venda (z 50) por cima da folha (z 45).
- Regressão achada e corrigida (): o guia do 1º uso (261012-09v, z 1100) abria por cima da tela de login — o efeito do 1º uso rodava antes do efeito do portão no mesmo ciclo. Guarda `welcomeShownRef` + guardião em test_ajuda_help. Conferido no app: sem sessão → só o login; conta nova logada → guia abre.
- Depois das correções: 218/218 .mjs ok, vite build ok (pytest não re-rodado: backend sem mudança após a suíte verde).
- Não conferido: swipe de borda e arrasto da alça no aparelho; Modo Operador e posição com opções na lista (a conta de teste não tinha estrutura).
- Contas de teste locais ficam no banco local de dev (server/data), não em produção.
