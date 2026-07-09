# QA 29 — Cores do Modo Operador nos gráficos + "Plano da mesa" não achava o modelo
*09/07/2026 · build alvo: F9-20260709-6*

Dois bugs distintos reportados juntos pelo Alex (junto com os mocks
`dois-apps-em-um.html` e `modo-operador.html` como referência de design),
ambos com causa-raiz encontrada e corrigidos nesta rodada.

## 1. Gráficos com cor errada no Modo Operador (qa/26 B2)

### Sintoma
Sparkline de operações e a curva de patrimônio simulado ("Patrimônio
Simulado") continuavam azuis (paleta base "Estudo") mesmo com o Modo
Operador ativo — deveriam usar verde/grafite conforme o mock aprovado
(`dois-apps-em-um.html`: cards `#10161a`, negativo `#ef4444`, positivo/acento
`#22c55e`, textos frios `#93a5ad`/`#5b6d75`).

### Causa-raiz
Mesma classe de bug já documentada no comentário perto de `PALETTE`/
`MODE_OPERADOR` em `App.jsx`: atributos de apresentação SVG (`fill=`,
`stroke=` como STRING crua, fora de `style=`) não resolvem `var(--x)` de
forma confiável neste WebKit — renderizam com a cor da paleta BASE, ignorando
o override do Modo Operador. O fix original (`usePalette()`, hex já
resolvido) só cobria `PriceChart`. `OpsSparkline` (marcações de compra/venda)
e `CapitalCurve` (Patrimônio Simulado) ficaram de fora e reproduziam o bug.

### Fix
`web/src/App.jsx`:
- `OpsSparkline({ candles, ops })`: adicionado `const P = usePalette();`;
  trocado `stroke={T.textFaint}` → `stroke={P.textFaint}`,
  `fill={T.positive}` → `fill={P.positive}`, `fill={T.negative}` →
  `fill={P.negative}`.
- `CapitalCurve({ ctx })`: adicionado `const P = usePalette();`; trocado
  `stroke={T.chartGrid}` → `stroke={P.chartGrid}`,
  `stroke={up ? T.positive : T.negative}` → `stroke={up ? P.positive :
  P.negative}`, `stroke={T.textFaint}` → `stroke={P.textFaint}` (path do
  placeholder "sem série").

Deixado de fora DE PROPÓSITO (patch cirúrgico): outros usos de `T.x` nesses
mesmos componentes via `style={{color: T.positive}}` (texto normal, resolve
`var()` sem problema via CSS/DOM) e o ícone decorativo de ajuda em
`AnalysisView` (~linha 965), que é chrome neutro sem relação com identidade
de modo.

### Guardião
`web/tests/test_chart_colors_theme_aware.mjs` — tranca que
`OpsSparkline`, `CapitalCurve` e `PriceChart` usem `usePalette()` e NUNCA
`fill={T.` / `stroke={T.` cru.

## 2. "Plano da mesa (IA)" não achava o modelo LLM (novo item, fora da matriz)

### Sintoma
Clicar em "Plano da mesa (IA)" no card do Radar falhava com erro do tipo
"modelo de IA não encontrado" mesmo com o aparelho configurado com um modelo
(BYOK) — enquanto a análise individual (N2, stop/alvo) funcionava normalmente
com a mesma configuração.

### Causa-raiz
`web/src/persistence.js` — `deviceStore.scanDeep(body)` era a ÚNICA chamada
de IA do aparelho que **não mandava `config` no corpo da requisição**, ao
contrário de `analyze()` e `analyzeStopAlvo()` (que sempre mandam
`config: doc.config`). Só repassava `appMode`:

```js
// ANTES (bug)
async scanDeep(body) {
  ensure();
  return api.scanDeep({ ...(body || {}), appMode: doc.config.appMode || "estudo" });
},
```

No servidor, `scan_deep_run` (`server/app/main.py`) monta
`config = (body or {}).get("config") or store.get(_conn, "config", user_id=scope) or {}`
e passa por `_ai_apply_managed(scope, config)`. Sem `config` no corpo e sem
sessão logada (`scope=None` — o app é local-first, nem sempre manda
`Authorization: Bearer`), essa função não tem BYOK nem gerenciada disponível
e devolve a config recebida (vazia). `llm.py` então levanta
`"Nenhum modelo de IA configurado."` (`code="missing_model"`) — o app tinha
um modelo configurado no aparelho, mas ele nunca chegava ao servidor NESSA
chamada especificamente.

### Fix
`web/src/persistence.js`, `scanDeep(body)`:
```js
async scanDeep(body) {
  ensure();
  return api.scanDeep({ config: doc.config, ...(body || {}), appMode: doc.config.appMode || "estudo" });
},
```
`config` entra ANTES do spread do `body` — mesma ordem/padrão de
`analyze()`/`analyzeStopAlvo()`.

### Guardião
`web/tests/test_scandeep_config.mjs` (novo) — checagem estática no fonte:
localiza o método `scanDeep` em `persistence.js`, garante que ele contém
`config: doc.config` e que essa chave aparece ANTES do `...(body ...)`
(senão um `body.config` vindo de fora poderia sobrescrever silenciosamente).

## 3. Testes

```
Backend (offline, sandbox sem rede): 19/20 — 0 falhas, 1 pulada (test_llm_errors.py,
dependência ausente no sandbox — rodar pytest completo no Mac antes do deploy).
Web: 25/25 — 0 falhas (24 anteriores + test_scandeep_config.mjs novo).
```

## 4. Build

`web/src/version.js`: `BUILD_ID` `F9-20260709-5` → **`F9-20260709-6`**.

## 5. Roteiro de hard stop (confirmar no aparelho antes de seguir)

1. `bash entregar.sh "qa/29: cores modo operador + config no scanDeep"` (no
   Mac — sandbox não builda Vite/Xcode).
2. Xcode: ⇧⌘K (clean) + Run no iPhone físico.
3. Perfil → rodapé → confirmar **F9-20260709-6**. Sem isso, NENHUM resultado
   abaixo vale.
4. Ativar Modo Operador → Radar → conferir sparkline das operações e o
   gráfico "Patrimônio Simulado" em verde/grafite (não azul).
5. Radar → clicar "Plano da mesa (IA)" num ativo → confirmar que a análise
   roda (sem erro de "modelo não configurado"), usando o modelo já
   configurado em Perfil → Configurações → Modelo de IA.

## 6. Itens ainda pendentes do pedido original do Alex (não cobertos aqui)

- "Desenhar o prompt como especialista no Claude" — precisa confirmação de
  escopo (redesenhar `skill`/`skillOperador`? outro prompt?).
- Radar "sem análise inicial rápida" — não investigado ainda.
- Fraseologia não acompanha a mudança de identidade — só grep preliminar em
  `copy.js`, auditoria completa contra os mocks ainda não feita.
- Nova funcionalidade: guardar resultado de TODAS as análises pra medir
  eficiência depois — precisa de decisões de escopo com o Alex antes de
  implementar (quais campos guardar, horizonte de tempo pra medir
  "eficiência", como correlacionar previsão × comportamento real do ativo).
- Itens B (restante)/C/D/E da matriz qa/26 — ainda sem relato detalhado do
  aparelho.
