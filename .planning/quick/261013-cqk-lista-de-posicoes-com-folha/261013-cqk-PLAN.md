---
phase: quick-261013-cqk
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/cartao_posicao.py
  - server/tests/test_cartao_proximidade.py
  - server/tests/test_carteira_leitura_rota.py
  - server/app/skill_ref.py
  - web/src/copy.js
  - web/src/estruturaCard.js
  - web/tests/test_cartao_v6_logica.mjs
  - web/src/listaPosicoes.js
  - web/tests/test_lista_posicoes_logica.mjs
  - web/src/navStack.js
  - web/src/App.jsx
  - web/tests/test_lista_posicoes_ui.mjs
  - web/tests/test_cartao_posicao_espelho.mjs
  - web/tests/test_ui_onda_j.mjs
  - web/tests/test_boris_intro.mjs
  - web/tests/test_carteira_perna_avulsa.mjs
  - web/tests/test_ritmo_sp.mjs
  - web/tests/test_ui_onda_g.mjs
autonomous: true
requirements: [D1, D2, D3, D4]

must_haves:
  truths:
    - "A aba Posições mostra uma linha compacta de 2 andares por posição (ticker, selo de estrutura, resultado do cabeçalho; mini-régua ou faixa piso/teto, UM chip de estado, variação %), e as pernas avulsas depois, como linhas 'só opções'"
    - "Tocar uma linha abre uma folha com o CartaoPosicao inteiro já aberto (ou o CartaoPernaAvulsa); voltar do sistema, swipe de borda, arrastar a alça, tocar fora e Esc fecham a folha e o foco volta para a linha"
    - "Chips 'Atenção primeiro' (padrão), 'Resultado' e 'Vencimento' reordenam a lista; empate estável por ticker; sem opção vai ao fim em Vencimento"
    - "O estado perto do stop / perto do alvo vem SÓ do backend (leitura_plano.proximidade); o front só lê o enum"
    - "Lista e card mostram o MESMO estado: estadoPrincipalV6 devolve estado_perto_stop/estado_perto_alvo e a lista deriva o chip dele"
    - "Na folha o card não reserva a folga do FAB (o FAB não aparece sob a folha)"
    - "MUDANÇA INTENCIONAL: estado_perto_stop / estado_perto_alvo passa a aparecer também em posições COM estrutura de opções (antes, com estrutura e dentro do plano, o estado principal era null); vale para o card e para a lista"
    - "O hero (PATRIMÔNIO TOTAL, RESULTADO ABERTO, CAIXA DISPONÍVEL, EM POSIÇÕES) fica igual"
    - "Sem cotação, leitura falhada ou plano incompleto: nenhuma proximidade é exibida (nunca estado inventado)"
  artifacts:
    - path: "server/app/cartao_posicao.py"
      provides: "LIMIAR_PROXIMIDADE e _proximidade(); campo proximidade em leitura_plano"
      contains: "LIMIAR_PROXIMIDADE = 0.75"
    - path: "web/src/listaPosicoes.js"
      provides: "NIVEIS_ATENCAO, CRITERIOS_ORDEM, prioridadeAtencao, ordenarLinhas (puros)"
      exports: ["NIVEIS_ATENCAO", "CRITERIOS_ORDEM", "prioridadeAtencao", "ordenarLinhas"]
    - path: "web/src/navStack.js"
      provides: "camada 'posicao' em ORDEM_CAMADAS (a mais baixa)"
      contains: "\"posicao\""
    - path: "web/src/App.jsx"
      provides: "LinhaPosicao, LinhaPernaAvulsa, MiniReguaLista, ChipAtencaoLista, ChipsOrdenacaoPosicoes; folha em CarteiraScreen; CartaoPosicao com naFolha"
    - path: "web/tests/test_lista_posicoes_logica.mjs"
      provides: "tabela de prioridade e ordenação"
    - path: "web/tests/test_lista_posicoes_ui.mjs"
      provides: "guardião estático da lista + folha + camada"
    - path: "server/tests/test_cartao_proximidade.py"
      provides: "tabela de casos da regra de proximidade"
  key_links:
    - from: "web/src/estruturaCard.js:estadoPrincipalV6"
      to: "leituraPlano.proximidade"
      via: "ramo pos === \"dentro\" lê o enum do backend"
      pattern: "estado_perto_stop"
    - from: "server/app/cartao_posicao.py:leitura_plano"
      to: "_proximidade"
      via: "r[\"proximidade\"] = _proximidade(avg, stop, alvo, preco, pos_plano)"
      pattern: "r\\[\"proximidade\"\\]"
    - from: "web/src/App.jsx:CarteiraScreen"
      to: "web/src/listaPosicoes.js"
      via: "prioridadeAtencao + ordenarLinhas"
      pattern: "ordenarLinhas\\("
    - from: "web/src/App.jsx:CarteiraScreen"
      to: "App (estadoNav.modais / fecharCamada)"
      via: "ctx.reportarNavPosicao + ctx.registrarFecharPosicao"
      pattern: "reportarNavPosicao"
    - from: "web/src/App.jsx:aplicarSubidaRef"
      to: "posicaoFecharRef.current"
      via: "fecharCamada.posicao"
      pattern: "posicao: \\(\\) =>"
---

<objective>
Opção B da aba Posições: a pilha de cards grandes vira LISTA COMPACTA (uma linha de 2 andares por posição, chip de atenção, ordenação Atenção/Resultado/Vencimento) e tocar uma linha abre uma FOLHA (camada nova da Onda J) com o CartaoPosicao reutilizado já aberto. Inclui a regra nova de proximidade (75% do caminho PM→stop / PM→alvo), calculada só no backend.

Purpose: a opção A enxugou o corpo do card, mas com várias posições a tela continua um scroll longo de cards. Com a lista, o usuário vê todas as posições de uma vez, com o que pede atenção no topo, e abre o detalhe de uma de cada vez.
Output: regra `proximidade` em `leitura_plano` + pytest; módulo puro `listaPosicoes.js` + teste; lista + folha + camada `posicao` no App/navStack; guardiões substitutos com nota datada.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/261013-cqk-lista-de-posicoes-com-folha/261013-cqk-CONTEXT.md
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md
@.planning/quick/261013-29f-card-de-posicao-enxuto/261013-29f-SUMMARY.md

Regras de leitura: `web/src/App.jsx` NUNCA inteiro (Grep + Read com offset/limit). Não ler STATE.md/PROJECT.md.

<interfaces>
<!-- Conferido no código em 2026-10-13. Use direto; não refaça o inventário. -->

server/app/cartao_posicao.py (188-237) `leitura_plano(posicao, preco, compras, modo) -> dict`:
- já calcula `avg, qty, stop, alvo, preco` via `_num`; `plano` in {"completo","so_stop","so_alvo","sem_plano"};
- `pos_plano` = "abaixo_stop" (preco < stop) | "acima_alvo" (preco > alvo) | "dentro" | None (só com plano completo E preco não None); grava `r["posicaoNoPlano"] = pos_plano`.
- Helpers do módulo: `_num`, `_r1`, `_r2`; `import math` já existe.
- Rota única: `POST /api/carteira/leitura` (server/app/main.py:4695) chama `cartao_posicao.leitura_plano` e devolve `{"modo", "leituras": {t: r}}`. O payload é repassado inteiro: campo novo chega ao front sem mexer na rota.

Paridade de stores: `web/src/persistence.js:292` (serverStore) `carteiraLeitura: (body) => api.carteiraLeitura(body)` e `:1372` (deviceStore) `async carteiraLeitura(body) { ... return api.carteiraLeitura(body); }`. Os DOIS só delegam à MESMA rota do backend — nenhum dos dois recalcula `leitura_plano`. Logo, o campo `proximidade` não exige mudança em persistence.js (paridade preservada por construção). NÃO tocar persistence.js.

web/src/estruturaCard.js:
- `estadoPrincipalV6({ p, estrutura, leituraPlano }) -> { principal: { chave, vals, tom, glifo } | null, extras: [] }`; chaves: "motor" (vencida/exercicio_provavel, vals.texto = estrutura.estadoTexto), "estado_travadas_todas", "estado_travadas_parcial", "estado_sem_plano", "estado_falta_alvo", "estado_falta_stop", "estado_abaixo_stop", "estado_acima_alvo", "estado_dentro" (só sem estrutura), "extra_cotacao_indisponivel". Ignora `posicaoNoPlano` quando `leituraPlano.desatualizada`.
- `chipVencimento(estrutura) -> { tipo: "vencida"|"hoje"|"vence", ddmm, dias, ambar } | null`.
- `linhasResultadoV6({ estrutura, leituraPlano, pctCapital, situacaoPlano, estruturaPendente }) -> { cabecalho: { valor, legenda, vals, suspenso }, linhas, chipCabecalho, notas }`. legendas: "legenda_resultado_estrutura" | "legenda_resultado_so_acoes" | "legenda_resultado_variacao" | null; chipCabecalho: "chip_total_suspenso" | "chip_desatualizado" | null.
- `situacaoLeituraPlano({ status, leitura, sigAtual }) -> { situacao: "ok"|"carregando"|"desatualizada"|"falha", leitura }`.
- `estadoLeitura(temPernas, entrada)` -> modoLeitura ("estruturada" | "carregando" | "falha" | ...); `dominioRegua(valores)`, `posRegua(v, dominio)` (layout, liberados no guardião transversal); `rsSinalNbsp(v)`, `tomDoEstado(estado)`, `nomeEmpresaCard(...)`.
- Estrutura (payload do motor, estrutura_posicao.py:451+): `nomeTexto`, `estado` in {"vencida","premio_indisponivel","exercicio_provavel","ate_5_dias","vigente"} (precedência nessa ordem, dias CORRIDOS), `estadoTexto`, `diasParaVencimento` (number|null, negativo = vencida), `faixa: { piso, teto } | null`.

web/src/App.jsx (linhas aproximadas):
- 357 `price(n)` ("—" se nulo), 360 `pct(n)`; 1779 `REDUCE_MOTION`; 3150 `FOLGA_FAB_PET`.
- 1962-1984 `function BottomSheet({ onClose, label, children })`: `useDialogA11y(true, onClose)` (foco, Esc com pilha, devolve foco), role="dialog" aria-modal, overlay `zIndex: 1000` fixo, alça arrastável (dy > 110 fecha), `className={REDUCE_MOTION ? undefined : "sheet-enter"}`, transição desligada com REDUCE_MOTION. Único uso hoje: 2024 (Indicadores técnicos).
- 4852 `ChipEstadoV6({ p, leitura, modo })` (estilo de chip a copiar: `corTom` por tom, TIPO_CARD.chip, glifo/IconeCadeado).
- 4911 `CartaoPernaAvulsa({ t, nomeEmpresa, leitura, cp, operador, ctx, data, onAtualizar })`.
- 4937 `CartaoPosicao({ p, nomeEmpresa, modoLeitura, leituraEstrutura, leituraPlano, situacaoPlano, onTentarPlano, cp, operador, ctx, data, total, onAtualizar, histAberto, onHist, editAberto, onEditar })`; `const [aberto, setAberto] = useState(false)`; rodapé único (~5045) com onClick que alterna `aberto` e faz `scrollIntoView` ao fechar; `{aberto && <div aria-hidden style={{ height: FOLGA_FAB_PET }} />}`; termina ~5063.
- 5661 `function LinhaChamadaOpcoes(` — o guardião transversal (test_cartao_v6_transversal) varre a fatia `function ReguaPlano(` → `function LinhaChamadaOpcoes(`: zero hex, `<button>` com minHeight >= 44, fontSize só `TIPO_CARD.*`, pesos 400/700, nenhum `+ - * /` adjacente a preco|resultado|be|k|stop|alvo|avg|valor|distStopPct|ateBePct (exceto posRegua/dominioRegua).
- 5728-5880 `CarteiraScreen({ ctx })`: estados `histFor`, `editFor`; hooks `useEstruturasPosicao` (-> `leituras`, `atualizar`) e `useLeiturasPlano` (-> `plano.status/leituras/sigs/tentarDeNovo`); `nomesRef`; `comPernas`; `avulsas = tickersSoComPernas(...)`; hero intacto; loop `data.positions.map((p) => {...})` (5854) com wrapper `<div key={p.t} id={"posicao-" + p.t} style={{ ...card, ...varsCartaoV6(themeKey, operador ? "operador" : "estudo"), padding: `${SP[4]}px` }}>`; depois `avulsas.map((t) => {...})` com `<CartaoPernaAvulsa`.
- 9020 `const [carteiraView, setCarteiraView] = useState("main")`; 9029-9030 `radarNav` + `radarFecharRef` (padrão a copiar).
- 10318-10326 `estadoNav = { ..., modais: [catalogOpen && "catalog", ..., techFor && "tech"].filter(Boolean), cardExpandido }`.
- 10334-10358 `aplicarSubidaRef.current` com `fecharCamada = { catalog: A.closeCatalog, ..., tech: A.closeTech }`.
- 10455-10458 ctx: `reportarNavRadar: (card, deep) => setRadarNav(...)`, `registrarFecharRadar: (fn) => { radarFecharRef.current = typeof fn === "function" ? fn : null; }`.
- 10490 `overlayLivre: !tourOpen && !aboutOpen && !welcomeOpen && !welcomeAuthOpen && !conceitoAberto && !petOpen && !borisIntroOpen,` (PetFab z 60 e a folha proativa de conceito só aparecem com overlayLivre).
- 10851 `<CarteiraScreen ctx={ctx} />` só é montado com `carteiraView === "main"` na aba carteira.
- z-index das camadas: catalog/buy/sell 50, stopAlvo 55, PetFab/toast 60, about 70, ..., conceito 86, BottomSheet 1000. BottomNav NÃO é fixed (flex none) — qualquer overlay fixed com z > 0 cobre a barra.

web/src/navStack.js:38 `ORDEM_CAMADAS = Object.freeze(["catalog","buy","sell","stopAlvo","radarDeep","about","tour","auth","pet","conceito","borisIntro","tech"])` (ordem crescente de z-index; `modalDoTopo` usa a ordem).

server/app/skill_ref.py:936 `CARTAO_POSICAO = { "operador": {...}, "educacional": {...} }` ↔ web/src/copy.js:1133 (estudo) e :2447 (operador) `cartaoPosicao: {...}` — espelho byte a byte, `cartaoPosicaoTxt(mode, chave, vals)` (copy.js:2700). Guardião `web/tests/test_cartao_posicao_espelho.mjs` (NEUTRAS = idênticas nos dois modos; ESPECIFICAS = diferem; PROIBIDO no Estudo: comprar|vender|trava protetora|abate o custo|garante|certo|sempre). Python: `server/tests/test_skill_ref.py`.
</interfaces>
</context>

## Regra de proximidade (D1) — especificação fechada

Constante única em `server/app/cartao_posicao.py`: `LIMIAR_PROXIMIDADE = 0.75` (comentário: quick 261013-cqk, 2026-10-13, decisão D1 do Alex).

Função pura `_proximidade(avg, stop, alvo, preco, pos_plano) -> Optional[str]`, chamada no fim de `leitura_plano` com os mesmos valores já normalizados (`_num`): `r["proximidade"] = _proximidade(avg, stop, alvo, preco, pos_plano)`. Nenhum campo existente muda.

Pré-condições (qualquer uma falsa → `None`, nunca estado inventado):
1. `pos_plano == "dentro"` (isso já implica plano completo e preço presente; abaixo_stop/acima_alvo têm estado próprio e mais forte);
2. `avg is not None`;
3. `stop < alvo` (plano invertido ou stop == alvo não tem régua);
4. todos os valores finitos (`math.isfinite`).

Fração percorrida rumo ao STOP (`f_stop`):
- `avg > stop` (caminho normal PM→stop existe): `f_stop = (avg - preco) / (avg - stop)` — fórmula locked de D1.
- `avg <= stop` (stop movido para proteger lucro; inclui `pm == stop`): o caminho PM→stop não existe; usa a régua stop→alvo: `f_stop = (alvo - preco) / (alvo - stop)` (≥ 0,75 ⇔ preço no quarto da faixa mais próximo do stop).

Fração percorrida rumo ao ALVO (`f_alvo`):
- `alvo > avg`: `f_alvo = (preco - avg) / (alvo - avg)` — fórmula locked de D1.
- `alvo <= avg` (alvo abaixo do PM, plano de redução de perda): régua stop→alvo: `f_alvo = (preco - stop) / (alvo - stop)`.

Os denominadores são sempre > 0 nos ramos escolhidos (ramo 1 exige `avg > stop` / `alvo > avg`; ramo 2 usa `alvo - stop > 0` pela pré-condição 3) — divisão por zero impossível. Fração não finita → `None`.

Decisão: `f_stop >= LIMIAR_PROXIMIDADE` → `"perto_stop"`; senão `f_alvo >= LIMIAR_PROXIMIDADE` → `"perto_alvo"`; senão `None`. Empate (as duas ≥ limiar, possível nos ramos de fallback com faixa estreita): `"perto_stop"` vence (risco primeiro). Sem arredondamento da fração.

Tabela de casos (vira `server/tests/test_cartao_proximidade.py`, parametrizado; `qty=100`):

| # | avg | stop | alvo | preço | esperado | por quê |
|---|-----|------|------|-------|----------|---------|
| 1 | 20 | 16 | 30 | 17 | perto_stop | (20−17)/(20−16) = 0,75, borda inclusiva |
| 2 | 20 | 16 | 30 | 17.05 | None | 0,7375 < 0,75; f_alvo negativa |
| 3 | 20 | 16 | 30 | 16 | perto_stop | preço == stop é "dentro"; f_stop = 1 |
| 4 | 20 | 16 | 30 | 27.5 | perto_alvo | (27,5−20)/(30−20) = 0,75 |
| 5 | 20 | 16 | 30 | 27.4 | None | 0,74 |
| 6 | 20 | 16 | 30 | 30 | perto_alvo | preço == alvo é "dentro"; f_alvo = 1 |
| 7 | 20 | 16 | 30 | 20 | None | preço == PM: f_stop 0 e f_alvo 0 |
| 8 | 20 | 22 | 30 | 23 | perto_stop | stop ≥ PM: (30−23)/(30−22) = 0,875 |
| 9 | 20 | 22 | 30 | 25 | None | f_stop 0,625; f_alvo 0,5 |
| 10 | 20 | 22 | 30 | 28 | perto_alvo | f_stop 0,25; f_alvo (28−20)/10 = 0,8 |
| 11 | 20 | 20 | 30 | 22.5 | perto_stop | pm == stop: (30−22,5)/(30−20) = 0,75 |
| 12 | 20 | 20 | 30 | 23 | None | f_stop 0,7; f_alvo 0,3 |
| 13 | 30 | 20 | 28 | 27 | perto_alvo | alvo ≤ PM: f_stop 0,3; f_alvo (27−20)/(28−20) = 0,875 |
| 14 | 40 | 20 | 24 | 24 | perto_stop | empate: f_stop 0,8 e f_alvo 1 → stop vence |
| 15 | 20 | 16 | 30 | None | None | preço ausente (posicaoNoPlano None) |
| 16 | 20 | 16 | None | 17 | None | plano so_stop |
| 17 | 20 | None | 30 | 28 | None | plano so_alvo |
| 18 | 20 | None | None | 17 | None | sem_plano |
| 19 | 20 | 16 | 30 | 15 | None | abaixo_stop tem estado próprio |
| 20 | 20 | 16 | 30 | 31 | None | acima_alvo tem estado próprio |
| 21 | 20 | 25 | 25 | 25 | None | stop == alvo (sem régua) |
| 22 | None | 16 | 30 | 17 | None | PM ausente |
| 23 | "abc" | 16 | 30 | 17 | None | PM inválido vira None em `_num` |
| 24 | 30 | 20 | 30 | 29 | perto_alvo | alvo == PM: o caminho PM→alvo tem comprimento zero (denominador 0), então cai no ramo `alvo <= avg` (régua stop→alvo): f_alvo = (29−20)/(30−20) = 0,9; f_stop = (30−29)/(30−20) = 0,1. Justificativa: com alvo no PM, o preço a 1 real do alvo está de fato perto dele; a régua stop→alvo é a única medida definida |
| 25 | 30 | 20 | 30 | 30 | perto_alvo | preço == alvo == PM: f_stop = 0; f_alvo na régua = (30−20)/(30−20) = 1. Coerente com o caso 6 (preço no alvo → perto_alvo); o "preço == PM → None" do caso 7 só vale quando PM não coincide com o alvo |

Testes extras no mesmo arquivo: `LIMIAR_PROXIMIDADE == 0.75`; monkeypatch do limiar para 0.9 faz o caso 1 virar None (prova fonte única); `leitura_plano` mantém todas as chaves anteriores (`posicaoNoPlano`, `distStopPct`, `distAlvoPct`, `rr`, `resultado`, ...) e ganha `proximidade`.

## estadoPrincipalV6 passa a ler a proximidade (ajuste do orquestrador, 2026-10-13)

Para lista e card mostrarem o mesmo estado, `estadoPrincipalV6` (web/src/estruturaCard.js:220-256) ganha dois ramos, no `else` do plano completo, DEPOIS de abaixo_stop/acima_alvo e ANTES de `estado_dentro`, usando o mesmo `pos` já guardado contra `desatualizada`:
- `pos === "dentro" && leituraPlano.proximidade === "perto_stop"` → `linha("estado_perto_stop", {}, "atencao", "⚠")` (com ou sem estrutura);
- `pos === "dentro" && leituraPlano.proximidade === "perto_alvo"` → `linha("estado_perto_alvo", {}, "info", "◎")` (com ou sem estrutura);
- senão o ramo atual (`pos === "dentro" && !estrutura` → `estado_dentro`).
Precedências inalteradas: motor (vencida/exercício provável) > travadas > protegida pela put > sem plano/falta stop/falta alvo > abaixo/acima > perto_stop > perto_alvo > dentro. Leitura desatualizada ou ausente → `pos` nulo → sem proximidade (nunca estado inventado). O helper só lê o enum; nenhuma conta. ChipEstadoV6, LinhaEstadoV6 e o resumo do card passam a mostrar a proximidade sozinhos, porque já resolvem `cartaoPosicaoTxt(modo, principal.chave)` e o mapa `corTom` já cobre "atencao"/"info".

Casos novos em `web/tests/test_cartao_v6_logica.mjs` (extensão com nota `// 2026-10-13 (quick 261013-cqk): proximidade no estado principal.`; as fixtures `lp()` atuais não têm `proximidade`, então as asserções existentes não mudam — se alguma comparação exata quebrar, substituta datada mantendo a intenção):
- `lp({ proximidade: "perto_stop" })` sem estrutura → chave `estado_perto_stop`, tom atencao, glifo ⚠;
- idem com `est()` (vigente) → `estado_perto_stop` (antes: principal null);
- `lp({ proximidade: "perto_alvo" })` → `estado_perto_alvo`, tom info, glifo ◎;
- `lp({ proximidade: "perto_stop", desatualizada: true })` → NÃO é perto_stop;
- `lp({ posicaoNoPlano: "abaixo_stop", proximidade: "perto_stop" })` → `estado_abaixo_stop`;
- exercício provável + perto_stop → `motor`; travadas todas + perto_stop → `estado_travadas_todas`;
- `lp({ proximidade: null })` → `estado_dentro` (comportamento atual).

Divergência residual aceita e documentada: quando o nível 2 (vence em até 5 dias) supera o estado principal na LISTA (ex.: sem plano + vence em 3 dias, ou perto do alvo + vence em 3 dias), o chip da linha é o de vencimento; no card esse mesmo chip de vencimento já aparece em `ChipsMetaV6` ao lado do estado principal — os dois estados estão visíveis no card, nenhum contraditório.

## Prioridade de atenção e ordenação (D1/D2) — especificação fechada

Módulo puro novo `web/src/listaPosicoes.js` (sem React, sem I/O, sem `+ - * /` sobre valores financeiros — só comparação `<`/`>`/`===`; importa `estadoPrincipalV6` de `./estruturaCard.js`).

`NIVEIS_ATENCAO` (congelado, menor = mais atenção):

| nível | condição (avaliada em todas; vale o MENOR nível aplicável) | chip retornado |
|-------|------------------------------------------------------------|----------------|
| 0 | `principal.chave` in {"motor" (vencida / exercício provável), "estado_abaixo_stop", "estado_acima_alvo"} | `{ tipo: "estado", ...principal }` |
| 1 | `principal.chave === "estado_perto_stop"` (estadoPrincipalV6 já aplicou validade da leitura e precedências) | `{ tipo: "estado", ...principal }` |
| 2 | `estrutura.estado === "ate_5_dias"` (dias corridos, do motor) | `{ tipo: "vencimento" }` |
| 3 | `principal.chave` in {"estado_sem_plano", "estado_falta_stop", "estado_falta_alvo"} | `{ tipo: "estado", ...principal }` |
| 4 | `principal.chave === "estado_perto_alvo"` | `{ tipo: "estado", ...principal }` |
| 5 | leitura indisponível: `situacaoPlano` in {"carregando","falha","desatualizada"} ou `principal.chave === "extra_cotacao_indisponivel"` | `principal` se houver, senão `null` |
| 6 | demais (dentro do plano, travadas, protegida pela put, vigente, prêmio indisponível) | `principal` se houver, senão `null` |

`principal` = `estadoPrincipalV6({ p, estrutura, leituraPlano }).principal` (com os ramos de proximidade da seção anterior) — a lista não lê `proximidade` direto: deriva tudo do mesmo estado principal do card, então lista e card nunca divergem no estado. `situacaoPlano` só entra no nível 5. Chip `tipo` passa a ser só `"estado"` | `"vencimento"` | `null`.

`prioridadeAtencao({ p, estrutura, leituraPlano, situacaoPlano }) -> { nivel, chip }`. Aceita `p` nulo (perna avulsa: só níveis 0, 2, 5, 6 via estrutura).

`CRITERIOS_ORDEM = Object.freeze(["atencao", "resultado", "vencimento"])`; `ordenarLinhas(linhas, criterio) -> novo array` (não muta). Cada linha: `{ t, nivel, resultado, dias }`.
- "atencao" (padrão; critério desconhecido cai aqui): `nivel` crescente, depois `t` crescente.
- "resultado": `resultado` crescente; `null` (suspenso) no fim; empate por `t`. DECISÃO (I1, registrada): "Resultado" = PIOR no topo (maior prejuízo primeiro), coerente com a lógica de "atenção" da tela; não há ordem decrescente nem alternância nesta entrega. Se o Alex preferir melhor-no-topo, é troca de um comparador e de um caso de teste.
- "vencimento": `dias` crescente (vencida, com dias negativos, primeiro); `null` (sem opção) no fim; empate por `t`.
Comparador só com `<`/`>`; nunca subtração de valores.

Casos de teste obrigatórios (`web/tests/test_lista_posicoes_logica.mjs`): um caso por nível 0..6; nível 1 suprimido quando `leituraPlano.desatualizada` (vira nível 5 com `situacaoPlano: "desatualizada"`); nível 1 suprimido com travadas (principal travadas → nível 6); nível 1 com estrutura vigente; perto_stop + ate_5_dias → nível 1 com chip `estado_perto_stop`; perto_alvo + ate_5_dias → nível 2 com chip de vencimento; sem_plano + ate_5_dias → nível 2; exercício provável + perto_stop → nível 0; avulsa (p nulo) com ate_5_dias → 2; cada critério de ordenação com empate por ticker, nulls no fim, critério inválido == atencao, array de entrada intacto.

## Corte de execução (bloqueante do checker, 2026-10-13)

PLAN único, executado em DUAS levas de executor, cada uma com o próprio verify:
- **Leva 1 = Tarefas 1 e 2** (backend da proximidade; `estadoPrincipalV6` + `listaPosicoes.js` + copy). Fecha com o verify da Tarefa 1 E o da Tarefa 2 verdes, commits próprios e um SUMMARY parcial (seção "Leva 1") no mesmo arquivo de SUMMARY.
- **Leva 2 = Tarefas 3 e 4** (lista, folha e camada em App.jsx/navStack.js; guardiões). SÓ começa depois que os testes da leva 1 passarem (o orquestrador confere os dois verifies antes de disparar a leva 2). Executor novo, contexto novo: lê este PLAN, o SUMMARY da leva 1 e só as interfaces da leva 1 que consome (`prioridadeAtencao`, `ordenarLinhas`, chaves de copy, ramos novos de `estadoPrincipalV6`). Fecha com o verify da Tarefa 3 E o da Tarefa 4 verdes e completa o SUMMARY (seção "Leva 2").
- Falha no verify da leva 1 → leva 2 não dispara; corrige-se na leva 1.

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend — proximidade em leitura_plano (D1)</name>
  <files>server/app/cartao_posicao.py, server/tests/test_cartao_proximidade.py, server/tests/test_carteira_leitura_rota.py</files>
  <behavior>
    - Os 25 casos da tabela "Regra de proximidade" acima, parametrizados, chamando `cartao_posicao.leitura_plano({"t": "PETR4", "qty": 100, "avg": avg, "stop": stop, "alvo": alvo}, preco, [], "educacional")["proximidade"]`.
    - `LIMIAR_PROXIMIDADE == 0.75`; monkeypatch para 0.9 muda o caso 1 para None.
    - Chaves antigas de `leitura_plano` continuam presentes.
    - Rota: `POST /api/carteira/leitura` com item dentro do plano e preço a 75% do caminho do stop devolve `leituras[t]["proximidade"] == "perto_stop"` (reaproveitar o `_item()`/fixture `cli` já existentes em test_carteira_leitura_rota.py).
  </behavior>
  <action>
RED primeiro: criar `server/tests/test_cartao_proximidade.py` com a tabela e os testes extras; acrescentar UM teste de rota em `test_carteira_leitura_rota.py` (padrão dos testes existentes no arquivo). Rodar e ver falhar (KeyError/None).
GREEN: em `cartao_posicao.py`, perto das constantes do topo (linha ~28-31), declarar `LIMIAR_PROXIMIDADE = 0.75` com comentário de decisão (quick 261013-cqk, D1, Alex 2026-10-13: fração do caminho PM→stop/PM→alvo; fallback na régua stop→alvo quando o caminho não existe). Criar `_proximidade(avg, stop, alvo, preco, pos_plano)` exatamente como a seção "Regra de proximidade" (pré-condições, dois ramos por lado, empate → perto_stop, `math.isfinite` na fração). Em `leitura_plano`, gravar `r["proximidade"]` logo depois de `r["posicaoNoPlano"]`. Não mudar nenhum cálculo existente nem a rota em main.py (ela repassa o dict inteiro). Não tocar persistence.js: os dois stores delegam `carteiraLeitura` à mesma rota (ver interfaces), então a paridade deviceStore↔serverStore se mantém por construção — registrar isso no SUMMARY.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest tests/test_cartao_proximidade.py tests/test_cartao_posicao.py tests/test_carteira_leitura_rota.py -q</automated>
  </verify>
  <done>25 casos + extras verdes; test_cartao_posicao.py e test_carteira_leitura_rota.py sem regressão; `grep -n "LIMIAR_PROXIMIDADE = 0.75" server/app/cartao_posicao.py` acha 1 linha; main.py e persistence.js sem diff.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: estadoPrincipalV6 com proximidade + helpers puros de prioridade/ordenação + copy nova nos dois modos (D1/D2/D3)</name>
  <files>web/src/estruturaCard.js, web/tests/test_cartao_v6_logica.mjs, web/src/listaPosicoes.js, web/tests/test_lista_posicoes_logica.mjs, server/app/skill_ref.py, web/src/copy.js, web/tests/test_cartao_posicao_espelho.mjs</files>
  <behavior>
    - Os casos novos de `estadoPrincipalV6` listados em "estadoPrincipalV6 passa a ler a proximidade".
    - Todos os casos listados em "Casos de teste obrigatórios" da seção de prioridade/ordenação.
    - `cartaoPosicaoTxt("estudo"|"operador", chave)` resolve cada chave nova; o espelho Python↔JS é byte a byte.
  </behavior>
  <action>
(a0) RED: acrescentar em `web/tests/test_cartao_v6_logica.mjs` os casos de proximidade (nota datada) e ver falhar. GREEN: em `web/src/estruturaCard.js`, os dois ramos novos de `estadoPrincipalV6` exatamente como a seção "estadoPrincipalV6 passa a ler a proximidade", com comentário `// quick 261013-cqk (2026-10-13): proximidade do backend (leitura_plano.proximidade) entra no estado principal; lista e card leem o mesmo estado.` Rodar test_cartao_v6_logica e test_fase461_logica (este último usa estadoPrincipalV6 com desatualizada).
(a) RED: criar `web/tests/test_lista_posicoes_logica.mjs` (padrão node puro dos outros `.mjs`: `ok(nome, cond)`, contador de falhas, `process.exit`) importando de `../src/listaPosicoes.js`. Rodar e ver falhar (módulo ausente).
(b) GREEN: criar `web/src/listaPosicoes.js` com `NIVEIS_ATENCAO`, `CRITERIOS_ORDEM`, `prioridadeAtencao`, `ordenarLinhas` exatamente como a seção "Prioridade de atenção e ordenação". Cabeçalho do módulo explica: só decide ordem/chip a partir de enums do backend; nenhum número calculado aqui.
(c) Copy (skill `didatica-boris`: texto novo entra na estrutura canônica, nunca solto no front). Acrescentar em `skill_ref.CARTAO_POSICAO` nos DOIS modos e espelhar byte a byte em `copy.js` (`cartaoPosicao` de estudo ~1133 e de operador ~2447), com comentário `# quick 261013-cqk (2026-10-13): lista de posições + folha (opção B).`:
  NEUTRAS (texto idêntico nos dois modos): `estado_perto_stop` = "Perto do stop do plano"; `estado_perto_alvo` = "Perto do alvo do plano"; `ordenar_aria` = "Ordenar posições"; `ordenar_atencao` = "Atenção primeiro"; `ordenar_resultado` = "Resultado"; `ordenar_vencimento` = "Vencimento"; `selo_estrutura` = "+ {nome}"; `selo_so_opcoes` = "só opções"; `linha_faixa` = "Piso {piso} · Teto {teto}"; `folha_aria` = "Detalhe da posição {ticker}".
  ESPECÍFICAS (diferem por modo): `linha_aria` — operador "{ticker}: {resultado}. {estado}. Abrir detalhe." / educacional "{ticker}: {resultado}. {estado}. Toque para ver o detalhe e aprender."; `linha_aria_sem_estado` — operador "{ticker}: {resultado}. Abrir detalhe." / educacional "{ticker}: {resultado}. Toque para ver o detalhe e aprender.".
  Conferir que nenhuma frase do Estudo bate o regex PROIBIDO do guardião (comprar/vender/garante/certo/sempre…).
(d) Guardião de espelho (extensão, nada apagado): em `test_cartao_posicao_espelho.mjs`, acrescentar as 10 neutras à lista NEUTRAS e as 2 específicas à ESPECIFICAS, com comentário `// 2026-10-13 (quick 261013-cqk): + chaves da lista/folha (opção B).`
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && f=0; for t in web/tests/test_lista_posicoes_logica.mjs web/tests/test_cartao_posicao_espelho.mjs web/tests/test_cartao_v6_logica.mjs web/tests/test_fase461_logica.mjs web/tests/test_copy_theme.mjs; do node "$t" >/dev/null 2>&1 || { echo "FALHOU $t"; f=1; }; done; (cd server && .venv/bin/python -m pytest tests/test_skill_ref.py -q) || f=1; exit $f</automated>
  </verify>
  <done>estadoPrincipalV6 devolve estado_perto_stop/estado_perto_alvo nos casos novos e as asserções antigas seguem verdes; listaPosicoes.js exporta os 4 símbolos; teste lógico verde com todos os casos; espelho verde com as 12 chaves novas; test_skill_ref.py verde; `grep -cE "[-+*/] *(a|b)\.(resultado|dias)" web/src/listaPosicoes.js` retorna 0.</done>
</task>

<task type="auto">
  <name>Task 3: Lista compacta + folha + camada "posicao" (D2/D3/D4)</name>
  <files>web/src/App.jsx, web/src/navStack.js</files>
  <action>
App.jsx só por Grep + Read com offset/limit. Todo componente NOVO fica entre o fim de `CartaoPosicao` e `function LinhaChamadaOpcoes(` (assim cai na fatia do guardião transversal: TIPO_CARD.* para fontSize, pesos 400/700, `<button>` com `minHeight: 44`, sem hex, sem aritmética financeira; espaçamento só `SP[n]`/template `${SP[n]}px` por test_ritmo_sp). Nunca usar `CARD_PAD_X` nem `maxWidth: CONTENT_MAX_WIDTH` nos componentes novos (test_ui_onda_g conta os usos), exceto o caso explícito do item (f).

(a) navStack.js (D4): `ORDEM_CAMADAS` ganha `"posicao"` como PRIMEIRO item (z-index 45, a camada mais baixa: buy/sell 50, stopAlvo 55 e conceito 86 abertos de dentro do card ficam por cima da folha). Atualizar o comentário de z-index acima da constante (`posicao 45` + nota `quick 261013-cqk, 2026-10-13`).

(b) BottomSheet (reuso, discretion): acrescentar prop opcional `zIndex` com default 1000 (`function BottomSheet({ onClose, label, children, zIndex = 1000 })`, overlay usa `zIndex`). O uso existente (Indicadores técnicos) não muda.

(c) CartaoPosicao: props novas `naFolha` e `onFecharFolha`. `useState(!!naFolha)` para `aberto`. No rodapé único: `onClick` chama `onFecharFolha()` quando `naFolha`, senão o comportamento atual (alternar + scrollIntoView). Espaçador da folga do FAB: `{aberto && !naFolha && <div aria-hidden style={{ height: FOLGA_FAB_PET }} />}` (sob a folha o FAB some via `overlayLivre`, então a folga seria espaço vazio — ajuste do orquestrador). Os literais `FOLGA_FAB_PET`, `FAB_PET_BOTTOM`, `FAB_PET_ALTURA` e a constante ficam intactos; o guardião test_cartao_posicao_enxuto:123-124 só exige `/FOLGA_FAB_PET/` no corpo do card e as constantes, então passa sem mudança (se falhar, substituta datada aceitando o condicional). Manter literais `aria-expanded={aberto}`, `aria-controls={idCorpo}`, `rodape_fechar`/`rodape_abrir`. Nada mais muda no card (faces, Bóris IA, Compras, editor, recortes `functionBody(...)` dos guardiões).

(d) Componentes novos (props só com dados já lidos; NENHUMA conta):
- `ChipsOrdenacaoPosicoes({ ordem, onOrdem, modo })`: `role="group"` com `aria-label` = `ordenar_aria`; três `<button type="button" aria-pressed={ordem === c}>` (`ordenar_atencao`/`ordenar_resultado`/`ordenar_vencimento`), `minHeight: 44`, pill, peso 700 quando ativo e 400 quando não.
- `ChipAtencaoLista({ chip, modo, textoVence })`: `chip.tipo === "estado"` renderiza como `ChipEstadoV6` (motor → `vals.texto`; senão `cartaoPosicaoTxt(modo, chave, vals)`); `"vencimento"` → `textoVence`; `null` → nada. Mesmo mapa `corTom` do ChipEstadoV6; glifo `aria-hidden`.
- `MiniReguaLista({ leitura })`: só quando sem estrutura, plano completo e `leitura.preco` presente; trilho fino com marcadores stop/PM/agora/alvo posicionados SÓ com `dominioRegua([...])` + `posRegua(v, dom)` (liberados no transversal); `aria-hidden` (o aria-label da linha descreve). Sem texto numérico.
- `LinhaPosicao({ p, e, res, leitura, atencao, textoVence, modo, onAbrir })`: um único `<button type="button" onClick={onAbrir} aria-haspopup="dialog" aria-label=...>` largura 100%, `minHeight: 44`, fundo/borda de card via `varsCartaoV6`. Andar 1: ticker (MONO, 700) + selo `selo_estrutura` com `{ nome: e.nomeTexto }` quando há estrutura | `rsSinalNbsp(res.cabecalho.valor)` com a mesma cor do cabeçalho do card; abaixo, `res.chipCabecalho` (chip existente) OU legenda só quando `legenda_resultado_so_acoes`/`legenda_resultado_estrutura` (a variação vai para o andar 2, não duplicar). Andar 2: `MiniReguaLista` OU, com estrutura, `linha_faixa` com `price(e.faixa.piso)`/`price(e.faixa.teto)` (`sem_piso`/`sem_teto` se nulo; nada se `e.faixa` nulo) | `ChipAtencaoLista` | `pct(leitura.variacaoPct)` quando não nulo. `aria-label`: `linha_aria` com `{ ticker, resultado, estado }` (resultado = valor formatado ou texto do chip de cabeçalho; estado = texto do chip) ou `linha_aria_sem_estado` sem chip.
- `LinhaPernaAvulsa({ t, e, res, atencao, textoVence, modo, onAbrir })`: mesmo botão; selo `selo_so_opcoes`; sem régua; faixa curta se houver; resultado de `linhasResultadoV6({ estrutura: e })` quando estruturada, senão chip do estado de leitura existente.

(e) CarteiraScreen (D2/D3): hero, aviso de opções, concentração, LinhaChamadaOpcoes e vazio ficam INTACTOS. Estado local `const [ordem, setOrdem] = useState("atencao")` (sem persistência — discretion) e `const [abertaT, setAbertaT] = useState(null)`. Montar o modelo por posição mantendo o literal `data.positions.map((p) => {` (guardião de perna avulsa): calcula `q`, `leitura`, `modoLeitura`, `nomeEmpresa`, `vig` exatamente como hoje, `e` (como no card), `res = linhasResultadoV6({ estrutura: e, leituraPlano: vig.leitura, pctCapital: null, situacaoPlano: vig.situacao, estruturaPendente: modoLeitura === "carregando" || modoLeitura === "falha" })`, `atencao = prioridadeAtencao({ p, estrutura: e, leituraPlano: vig.leitura, situacaoPlano: vig.situacao })`, `textoVence` (mesma fórmula com `chipVencimento` e `cp.chipVence/chipVenceHoje/chipVencida` do card), e devolve `{ p, t: p.t, nivel: atencao.nivel, resultado: res.cabecalho.valor, dias: e ? e.diasParaVencimento : null, ... }`. Render: `ChipsOrdenacaoPosicoes` acima da lista (só se houver ≥ 2 itens no total); depois `ordenarLinhas(linhas, ordem).map(({ p, ... }) => <div key={p.t} id={"posicao-" + p.t}><LinhaPosicao ... onAbrir={() => setAbertaT(p.t)} /></div>)` — o literal `id={"posicao-" + p.t}` fica em CarteiraScreen (âncora de deep link). Em seguida `avulsas.map((t) => ...)` com `<LinhaPernaAvulsa` (ordem alfabética atual, sempre DEPOIS das posições, D3) e wrapper `id={"posicao-" + t}`.
Folha: quando `abertaT` resolve para uma posição (`const p = data.positions.find(...)`, variável chamada `p` de propósito) renderizar `<BottomSheet zIndex={45} onClose={() => setAbertaT(null)} label={cartaoPosicaoTxt(modo, "folha_aria", { ticker: p.t })}>` contendo um scroller `overflowY: "auto"`, `overscrollBehavior: "contain"`, `background: T.bgCard`, `padding: `${SP[4]}px``, `...varsCartaoV6(themeKey, modo)`, com o MESMO `<CartaoPosicao ... histAberto={histFor === p.t} onHist=... editAberto={editFor === p.t} onEditar=... naFolha onFecharFolha={() => setAbertaT(null)} />` de hoje (mesmas props). Quando `abertaT` é avulsa: mesma folha com `<CartaoPernaAvulsa ... />`. Se `abertaT` não existe mais (posição vendida de dentro da folha), um efeito zera `abertaT` — nunca folha vazia. Forma exata, sem loop: `const abertaExiste = !!abertaT && (data.positions.some((x) => x.t === abertaT) || avulsas.includes(abertaT));` e `useEffect(() => { if (abertaT && !abertaExiste) setAbertaT(null); }, [abertaT, abertaExiste]);` — guarda `abertaT && !abertaExiste` faz o efeito parar depois de um único `setAbertaT(null)` (com `abertaT` nulo a condição é falsa); deps são primitivos (string/boolean), nunca arrays/objetos recriados a cada render. "Tentar de novo" e "Atualizar" continuam dentro do card na folha (estados de leitura já existentes).
Canal com o App (padrão Radar/Onda J): `useEffect(() => { if (ctx.reportarNavPosicao) ctx.reportarNavPosicao(!!abertaT); }, [abertaT])` — dep única `abertaT` (string|null); o setter do App (`setPosicaoNav((v) => (v === !!aberta ? v : !!aberta))`) devolve o MESMO valor quando nada mudou, então o re-render do App não re-dispara o efeito (abertaT não muda) e não há loop. Registro do fechamento num efeito separado com deps `[]`: `ctx.registrarFecharPosicao(() => setAbertaT(null))`, cleanup registra `null` e reporta `false`. HOOKS: todos os `useState`/`useEffect` novos da CarteiraScreen ficam no topo do corpo, junto de `histFor`/`editFor` e dos hooks existentes, ANTES de qualquer `return` (hoje a tela tem um único `return`; nenhum `return` condicional pode ser introduzido antes deles).

(f) Largura em tela grande (responsivo, princípio 10): o scroller da folha recebe `width: "100%", maxWidth: CONTENT_MAX_WIDTH, margin: "0 auto"` — o guardião test_ui_onda_g conta 2 usos e passa a 3 (substituta na Task 4).

(g) App (camada): `const [posicaoNav, setPosicaoNav] = useState(false);` e `const posicaoFecharRef = useRef(null);` junto de `radarNav`. `estadoNav.modais` ganha `tab === "carteira" && carteiraView === "main" && posicaoNav && "posicao"` (no início da lista). `fecharCamada` ganha `posicao: () => { if (posicaoFecharRef.current) posicaoFecharRef.current(); },`. ctx ganha `reportarNavPosicao: (aberta) => setPosicaoNav((v) => (v === !!aberta ? v : !!aberta)),` e `registrarFecharPosicao: (fn) => { posicaoFecharRef.current = typeof fn === "function" ? fn : null; },`. `overlayLivre` ganha `&& !posicaoNav` no FIM da expressão (PetFab z 60 e a folha proativa de conceito somem sob a folha, como em toda folha — skill didatica-boris). Animação: a do BottomSheet (`sheet-enter`, desligada com `REDUCE_MOTION`); NÃO criar bloco `@media (prefers-reduced-motion` novo (test_ui_onda_j trava em 2).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && npx vite build >/dev/null && f=0; for t in tests/test_cartao_v6_transversal.mjs tests/test_cartao_v6_fechado.mjs tests/test_cartao_v6_aberto.mjs tests/test_cartao_posicao_enxuto.mjs tests/test_carteira_opcoes_tira.mjs tests/test_estrutura_card_ui.mjs tests/test_fase461_ui.mjs tests/test_hero_reconciliado.mjs tests/test_posicao_stop_alvo.mjs; do node "$t" >/dev/null 2>&1 || { echo "FALHOU $t"; f=1; }; done; exit $f</automated>
  </verify>
  <done>vite build ok; os 9 guardiões acima verdes (falhas esperadas de ORDEM_CAMADAS/overlayLivre/perna avulsa/ritmo/onda_g ficam para a Task 4); `grep -n 'id={"posicao-" + p.t}' web/src/App.jsx` acha a linha dentro de CarteiraScreen; `grep -n "posicao: () =>" web/src/App.jsx` acha o fecharCamada.</done>
</task>

<task type="auto">
  <name>Task 4: Guardiões substitutos com nota datada + guardião novo da lista/folha</name>
  <files>web/tests/test_ui_onda_j.mjs, web/tests/test_boris_intro.mjs, web/tests/test_carteira_perna_avulsa.mjs, web/tests/test_ritmo_sp.mjs, web/tests/test_ui_onda_g.mjs, web/tests/test_lista_posicoes_ui.mjs</files>
  <action>
Regra do repo: guardião não se apaga; cada asserção alterada mantém a intenção e ganha comentário `// 2026-10-13 (quick 261013-cqk): <motivo>` logo acima. Substituições conhecidas (asserção atual → substituta):

1. test_ui_onda_j.mjs:19 `ORDEM_CAMADAS === ["catalog", ..., "tech"]` → `["posicao", "catalog", "buy", "sell", "stopAlvo", "radarDeep", "about", "tour", "auth", "pet", "conceito", "borisIntro", "tech"]`. Acrescentar (extensão): `profundidade(E({ tab: "carteira", modais: ["posicao"] })) === 1`; `modalDoTopo(E({ modais: ["posicao", "sell"] })) === "sell"`; `subirNivel(E({ tab: "carteira", modais: ["posicao"] })) === "fecharModal"`. Na lista estática de `fecharCamada` (linha ~46 da P2) acrescentar `"posicao: () =>"`; nova P2: `app.includes("reportarNavPosicao:") && app.includes("registrarFecharPosicao:")` e `app.includes('posicaoNav && "posicao"')`.
2. test_boris_intro.mjs:111-112 regex `overlayLivre: ... && !borisIntroOpen,` → mesma regex terminando em `&& !borisIntroOpen && !posicaoNav,` (intenção preservada: borisIntro segue no portão).
3. test_carteira_perna_avulsa.mjs:29 `<CartaoPernaAvulsa` nos 900 chars depois de `avulsas.map((t) =>` → `<LinhaPernaAvulsa` nesses 900 chars E `<CartaoPernaAvulsa` presente no corpo de CarteiraScreen (dentro da folha). Linhas 26/28 (ordem posições → avulsas) seguem iguais.
4. test_ritmo_sp.mjs:149-150 `componentesV6` (extensão): + "ChipsOrdenacaoPosicoes", "ChipAtencaoLista", "MiniReguaLista", "LinhaPosicao", "LinhaPernaAvulsa".
5. test_ui_onda_g.mjs `maxWidth: CONTENT_MAX_WIDTH 2x` → `3x` (o terceiro é o scroller da folha de posição).

Guardião novo `web/tests/test_lista_posicoes_ui.mjs` (texto de App.jsx, `functionBody`/`semComentarios` no padrão de test_ritmo_sp): CarteiraScreen contém `ordenarLinhas(`, `prioridadeAtencao(`, `<LinhaPosicao`, `<LinhaPernaAvulsa`, `<BottomSheet zIndex={45}`, `naFolha`, `<CartaoPosicao`, `id={"posicao-" + p.t}`, `histFor === p.t`, `editFor === p.t`, `ctx.reportarNavPosicao`, `ctx.registrarFecharPosicao`; hero intacto (`PATRIMÔNIO TOTAL`, `RESULTADO ABERTO`, `CAIXA DISPONÍVEL`, `EM POSIÇÕES`); `ChipsOrdenacaoPosicoes` tem `aria-pressed` e `minHeight: 44`; `LinhaPosicao` é `<button` com `aria-label` e `minHeight: 44`; nenhum componente novo contém `distStopPct`, `posicaoNoPlano ===` ou `.avg -`/`- p.avg` (proximidade só do backend); `BottomSheet` tem default `zIndex = 1000`; `CartaoPosicao` usa `useState(!!naFolha)` e `onFecharFolha`, e o espaçador é `aberto && !naFolha &&` com `FOLGA_FAB_PET`; anti-loop (W4): CarteiraScreen contém `if (abertaT && !abertaExiste) setAbertaT(null)` e `}, [abertaT, abertaExiste]);`, contém `ctx.reportarNavPosicao(!!abertaT); }, [abertaT]);`, o App contém `setPosicaoNav((v) => (v === !!aberta ? v : !!aberta))`, e no corpo de CarteiraScreen o índice de `useState("atencao")`, `useState(null)` de `abertaT` e dos dois `useEffect` novos é MENOR que o índice do primeiro `return (`; `web/src/persistence.js` continua com `carteiraLeitura` nos dois stores (paridade por delegação).

Depois rodar a lista ampla abaixo (cada arquivo separado). Qualquer OUTRO guardião que falhe por travar o loop antigo de cards grandes (candidatos: test_concentracao_carteira, test_fase21_dedup_consolidacao, test_curadoria_ui, test_carteira_lastro_ui, test_cartao_v6_camadas, test_pet_ui, test_conceito_ui, test_opcoes_consolidacao_ui) recebe substituta com a mesma nota datada, mantendo a intenção — nunca apagar sem substituta; registrar cada uma no SUMMARY (asserção antiga → nova). Falha que indique regressão real (não trava de forma) volta para o App.jsx, não para o guardião.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && f=0; for t in tests/test_lista_posicoes_ui.mjs tests/test_lista_posicoes_logica.mjs tests/test_ui_onda_j.mjs tests/test_boris_intro.mjs tests/test_carteira_perna_avulsa.mjs tests/test_ritmo_sp.mjs tests/test_ui_onda_g.mjs tests/test_cartao_v6_transversal.mjs tests/test_cartao_v6_fechado.mjs tests/test_cartao_v6_aberto.mjs tests/test_cartao_v6_camadas.mjs tests/test_cartao_v6_logica.mjs tests/test_fase461_logica.mjs tests/test_cartao_posicao_enxuto.mjs tests/test_cartao_posicao_espelho.mjs tests/test_carteira_opcoes_tira.mjs tests/test_estrutura_card_ui.mjs tests/test_fase461_ui.mjs tests/test_hero_reconciliado.mjs tests/test_concentracao_carteira.mjs tests/test_fase21_dedup_consolidacao.mjs tests/test_curadoria_ui.mjs tests/test_carteira_lastro_ui.mjs tests/test_posicao_stop_alvo.mjs tests/test_pet_ui.mjs tests/test_conceito_ui.mjs tests/test_opcoes_consolidacao_ui.mjs tests/test_copy_theme.mjs; do node "$t" >/dev/null 2>&1 || { echo "FALHOU $t"; f=1; }; done; npx vite build >/dev/null || f=1; exit $f</automated>
  </verify>
  <done>Os 28 arquivos verdes, cada um rodado separado; vite build ok; cada substituição com nota `2026-10-13 (quick 261013-cqk)`; nenhuma asserção removida sem substituta (conferir com `git diff --stat web/tests` + leitura do diff).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → POST /api/carteira/leitura | posições (avg/stop/alvo/preço) vêm do cliente; rota pura, sem efeito, sem mercado |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-cqk-01 | Tampering | `_proximidade` com valores não numéricos/infinito | mitigate | `_num` + pré-condições + `math.isfinite`; denominadores > 0 por construção; casos 21-25 na tabela |
| T-cqk-02 | Information disclosure | regra financeira no front | mitigate | front só lê o enum `proximidade`; guardião novo proíbe `distStopPct`/aritmética sobre avg nos componentes; transversal cobre a fatia |
| T-cqk-03 | Denial of service | rota com muitas posições | accept | limites `_LEITURA_MAX_POSICOES`/`_LEITURA_MAX_COMPRAS` já existentes; função O(1) por posição |
| T-cqk-04 | Repudiation/Integridade de UX | chip de proximidade com leitura velha | mitigate | proximidade só entra no estado principal com `posicaoNoPlano` válido (estadoPrincipalV6 já ignora leitura desatualizada); testado nos dois arquivos de lógica |
</threat_model>

<verification>
- `cd server && .venv/bin/python -m pytest tests/test_cartao_proximidade.py tests/test_cartao_posicao.py tests/test_carteira_leitura_rota.py tests/test_skill_ref.py -q`
- Loop da Task 4 (cada guardião separado) + `npx vite build`.
- NÃO rodar: suíte canônica, `cap copy ios`, bump/publicar/push (ficam com o orquestrador).
</verification>

<success_criteria>
- Regra de proximidade com constante única, 25 casos de borda verdes, sem divisão por zero, sem estado inventado.
- Lista compacta com 3 critérios de ordenação, chip único por prioridade, perna avulsa no fim; folha com o CartaoPosicao reutilizado aberto, fechando por voltar/swipe/Esc/alça/fora, foco devolvido.
- Lista e card mostram o mesmo estado principal (inclui perto do stop/alvo); sem folga de FAB dentro da folha.
- Hero intacto; deep link `posicao-<ticker>` preservado; paridade skill_ref↔copy e deviceStore↔serverStore preservadas.
- Guardiões substitutos documentados no SUMMARY.
</success_criteria>

<output>
Criar `.planning/quick/261013-cqk-lista-de-posicoes-com-folha/261013-cqk-SUMMARY.md` (padrão do 261013-29f: o que mudou, testes rodados um a um, guardiões substituídos antigo → novo, desvios, follow-ups). O SUMMARY registra EXPLICITAMENTE como "não verificado em runtime": Esc fecha a folha, foco devolvido à linha, voltar do sistema/swipe de borda fecha a folha, arrastar a alça fecha, z-index sobre compra/venda/stop-alvo — só cobertos por guardião estático; conferir no iPhone/PWA com conta com posições. Editar STATE.md só à mão (proibido `gsd-sdk state.*`), se o orquestrador pedir.
</output>
