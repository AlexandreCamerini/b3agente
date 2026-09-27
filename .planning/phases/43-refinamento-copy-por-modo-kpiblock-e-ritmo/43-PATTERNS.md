# Phase 43: Refinamento — copy por modo, KpiBlock e ritmo - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 5 (nenhum arquivo novo de produção — mesmo perfil da Fase 42: edição/remoção dentro de arquivos existentes + guardiões novos/atualizados)
**Analogs found:** 5 / 5

Nota de escopo: como na Fase 42, esta fase não cria nenhum arquivo de produção
novo (só o guardião `web/tests/test_ritmo_sp.mjs` é 100% novo). O trabalho é
edição em `server/app/skill_ref.py`, `web/src/copy.js`, `web/src/App.jsx` e
seus guardiões em `web/tests/`. Os "analogs" abaixo são, em sua maioria, o
próprio par que a fase está espelhando (`HISTORICO`/`historico_txt` para o
dict novo `RECONCILIACAO_ELEGIBILIDADE`) e os componentes que já existem e
serão editados no lugar (`SinalChip`, `HistoricoPill`, `AnalysisView`,
`FundamentoTabela`, `LinhaContexto`) — não há componente de outro domínio a
copiar.

---

## File Classification

| Arquivo | Papel | Fluxo de dado | Ação nesta fase |
|---|---|---|---|
| `server/app/skill_ref.py` | provider (vocabulário/dict de texto) | CRUD (leitura por modo/estado) | Adiciona `RECONCILIACAO_ELEGIBILIDADE`, `RECONCILIACAO_POR_QUE_IMPORTA`, `reconciliacao_elegibilidade_txt()` — ao lado de `HISTORICO`/`HISTORICO_ROTULO`/`historico_txt` |
| `web/src/copy.js` | provider (espelho JS do vocabulário) | CRUD (leitura por modo/estado) | Adiciona `COPY.estudo/operador.reconciliacaoElegibilidade`, `reconciliacaoTxt()`, `reconciliacaoPorQueImporta`, rótulo `"LEITURA DA IA"` — ao lado de `historicoRotulo`/`historicoTxt` |
| `web/src/App.jsx` | component (React, UI) | request-response (render puro) | Remove `KpiBlock`/`KpiCell`/`DIR_STYLE`/`SCALE_STYLE`; adiciona bloco de 3 `SinalChip contexto` em `AnalysisView`; adiciona prop `microtexto`/`A`/`didatica`/`dados` em `HistoricoPill`; introduz constante `SP`; aplica `SP[N]` em `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill`/gaps entre blocos do `AtivoCard`; remove `label` do chip em `FundamentoTabela` (D-17); amplia área de toque do `SetorAlvo setorId="fundamento"` (D-18) |
| `web/tests/test_vocabulario_espelho.mjs` | test (guardião cruzado skill_ref↔copy.js) | transform (parse+diff de texto) | Estende `DICTS`/`CHAVE_JS`/`CHAVES_ESPERADAS` com `RECONCILIACAO_ELEGIBILIDADE` (chaves: `elegivel`,`inelegivel`,`insuficiente`,`nunca_medido`,`aposentado`) |
| `web/tests/test_decisao_modo.mjs` | test (guardião grep-estático) | transform | Reconciliar (nunca apagar) as linhas ~38-58 que testam `KpiBlock`/rec mapeado — nota datada "REVERSÃO DELIBERADA" |
| (novo) `web/tests/test_ritmo_sp.mjs` | test (guardião grep-estático, ban-list de px solto) | transform | Guardião NOVO — mesma receita de `test_sinal_chip_ui.mjs` (Parte A/D), varre `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill`/trecho do `AtivoCard` por `margin`/`padding`/`gap` em px literal fora de `SP[N]`/`SP_OPTICO_*` |
| `web/tests/test_sinal_chip_ui.mjs` | test (guardião grep-estático) | transform | Atualizar asserções que hoje fixam valores px literais (linhas 63-64 e outras) para `SP[N]`, e a contagem de `<SinalChip peso="contexto"` call sites (hoje 4 — sobe para 7 com os 3 chips novos da IA) |

---

## Pattern Assignments

### `server/app/skill_ref.py` — `RECONCILIACAO_ELEGIBILIDADE` / `reconciliacao_elegibilidade_txt` (provider, CRUD)

**Analog exato:** `HISTORICO`/`HISTORICO_ROTULO`/`historico_txt` (`server/app/skill_ref.py:355-432`).

**Padrão de dict a copiar** (lines 366-383, 428-432):
```python
HISTORICO = {
    "operador": {
        "elegivel": "✓ ELEGÍVEL — vantagem estatística medida na janela {janela}.",
        "inelegivel": "✗ NÃO ELEGÍVEL — sem vantagem estatística medida na janela {janela}.",
        "insuficiente": "Amostra insuficiente (n<40) — ausência de evidência não é prova de mau desempenho.",
        "nunca_medido": "Sem histórico medido ainda.",
        "aposentado": "Padrão gráfico identificado, sem vantagem estatística medida (ADR-016).",
        "desatualizado": "Medido até {medidoAte} — dado pode estar desatualizado.",
    },
    "educacional": { ... mesmas chaves ... },
}

def historico_txt(modo: str, estado: str, janela: str = "", medido_ate: str = "") -> str:
    """Frase canônica de um estado do histórico medido, no vocabulário do modo."""
    h = HISTORICO.get(modo if modo in HISTORICO else "educacional", HISTORICO["educacional"])
    frase = h.get(estado) or h["nunca_medido"]
    return frase.replace("{janela}", janela or "?").replace("{medidoAte}", medido_ate or "?")
```

**Regra de fallback a preservar:** `modo` desconhecido cai em `"educacional"` (nunca `KeyError`); `estado` desconhecido cai em `d["nunca_medido"]` (`.get(estado) or d["nunca_medido"]`) — mesma dupla trava que o texto novo `reconciliacao_elegibilidade_txt` (já desenhado no `43-UI-SPEC.md`) replica.

**Placeholder nunca vira `0`/vazio silencioso (regra da casa):** `.replace("{janela}", janela or "?")` — string `"?"` explícita, nunca omissão. `reconciliacao_elegibilidade_txt` precisa do mesmo tratamento para `{n}`/`{expR}` (ver `43-UI-SPEC.md`, já com o código completo pronto — este PATTERNS aponta só o analog, a implementação exata já está travada no UI-SPEC).

**Comentário de decisão obrigatório no topo do bloco novo** — padrão do comentário de `HISTORICO` (`skill_ref.py:355-365`): explica de onde vem o dado, por que existe o vocabulário, e cita a regra de `didatica-boris` (resultado negativo com o mesmo peso do positivo). Replicar esse estilo de comentário para `RECONCILIACAO_ELEGIBILIDADE` (o `43-UI-SPEC.md` já traz o comentário pronto, linhas 252-258).

---

### `web/src/copy.js` — `reconciliacaoTxt` / `reconciliacaoElegibilidade` (provider, espelho)

**Analog exato:** `historicoRotulo`/`historicoTxt` (`web/src/copy.js:585-599`, `:1351`, `:1600`).

```js
// web/src/copy.js:1600 (historicoTxt, padrão de função espelhada)
export function historicoTxt(mode, estado, vals) {
  const d = copyFor(mode).historico;
  const frase = d[estado] || d.nunca_medido;
  ...
  return frase.replace("{janela}", ...).replace("{medidoAte}", ...);
}
```

`reconciliacaoTxt(mode, estado, vals)` segue o MESMO shape: `copyFor(mode).reconciliacaoElegibilidade`, fallback para `.nunca_medido`, `.replace()` em cadeia. Código exato já travado no `43-UI-SPEC.md` (linhas 307-317) — usar aquele, este PATTERNS só confirma que é a mesma receita de `historicoTxt`.

`reconciliacaoPorQueImporta` é export solto (fora de `COPY.estudo`/`COPY.operador`) porque é string fixa sem variação por modo/estado — **não há analog direto de export solto de string fixa no arquivo**; o padrão mais próximo é `glossarioSub`/`concentracaoLink` do 42-PATTERNS (chaves idênticas nos dois modos, dentro de `COPY`), mas como esta string não varia NUNCA (nem por modo), fica fora de `COPY` — decisão já travada em D-13/UI-SPEC, não uma escolha do planner.

---

### `web/src/App.jsx` — remoção de `KpiBlock`/`KpiCell`/`DIR_STYLE`/`SCALE_STYLE`

**Localização atual (lida nesta sessão):**
- `DIR_STYLE` — `App.jsx:1072-1076`
- `SCALE_STYLE` — `App.jsx:1077-1080`
- `KpiCell` — `App.jsx:1327-1336`
- `KpiBlock` — `App.jsx:1338-1367`

Nenhum call site de `KpiBlock`/`KpiCell` sobrevive em produção (confirmado pelo comentário `App.jsx:3925`: "qa/49 (v11): KpiBlock removido"). Apagar as 4 declarações por inteiro.

**Guardião a reconciliar (nunca apagar):** `web/tests/test_decisao_modo.mjs:38-58` testa hoje:
```js
// linha 40-41
ok("KpiBlock é mode-aware (rótulo por modo)",
  /operador \? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"/.test(app));
// linha 58-59
ok("KpiBlock exibe rec mapeado (não kpis.recomendacao cru)",
  /const rec = recDoModo\(kpis\.recomendacao, operador\)/.test(app) && /fontSize: "14px", color: recColor \}\}>\{rec\}</.test(app));
```
A primeira asserção (linha 40-41) sobrevive sem edição — o regex `/operador \? "DECISÃO DA MESA" : "PLANO EDUCACIONAL"/` casa também com o `SinalChip peso="primario"` (`App.jsx:1392` e outros call sites), então continua batendo mesmo após `KpiBlock` sumir. A segunda (linha 58-59) referencia `recDoModo`/`recColor` especificamente dentro do corpo apagado — precisa de nota datada `REVERSÃO DELIBERADA (2026-XX-XX, Fase 43, ID-CHIP-03)` explicando que o mapa rec→cor de direção/convicção/qualidade não tem substituto (D-03: recomendação da IA não vira chip), seguindo o MESMO estilo já usado na linha 44-48 do próprio arquivo:
```js
// web/tests/test_decisao_modo.mjs:44-48 (estilo exato a replicar)
// REVERSÃO DELIBERADA (2026-08-09): o fallback para `recDoModo(kp.recomendacao)`
// saiu. Ele existia para a manchete nunca ficar vazia, mas criava uma SEGUNDA
// fonte para o mesmo espaço visual — e só na Watchlist, porque o Radar sempre
// usou o motor. Dava para ler uma recomendação numa aba e outra na outra.
// Agora: o motor decide, a IA explica; sem plano, a ausência é declarada.
```

**`test_hero_reconciliado.mjs` (linha ~57):** não editar — a asserção já checa AUSÊNCIA de `KpiBlock`, permanece verdadeira.

---

### `web/src/App.jsx` — os 3 `SinalChip contexto` em `AnalysisView` (CHIP-03)

**Analog exato:** `AnalysisView` já existe (`App.jsx:1616-1675`, lido nesta sessão) — o novo bloco entra como um `{an.kpis && (...)}` adicional, na MESMA posição estrutural dos outros blocos condicionais do componente (`an.iaIndisponivel`, `d.fatos`, `an.fundamento`, `an.rebaixadoPorFundamento`), todos seguindo o padrão `{condição && (<div style={{marginTop: "Npx"}}>...</div>)}`.

**Ponto de inserção exato:** entre a linha 1652 (fim do bloco `semDados`/`body`/`Markdown`) e a linha 1653 (`{Array.isArray(d.fatos)...}`) — conforme UI-SPEC linha 190-192.

**Padrão de `SinalChip peso="contexto"` a reusar** (já editado pela Fase 42, `App.jsx:1427` região, chamado hoje em `LinhaContexto`/`FundamentoTabela`/`HistoricoPill`):
```jsx
<SinalChip peso="contexto" label="FUNDAMENTO" value={score} explicavel ariaLabel={ariaFundamento(score, modo)} />
```
Os 3 chips novos usam a mesma forma, sem `estado` (ramo neutro padrão — sem cor). Código completo já travado no `43-UI-SPEC.md` (linhas 196-222) — usar aquele verbatim.

**Contagem de call sites a atualizar:** `test_sinal_chip_ui.mjs:176-180` afirma hoje "exatamente 4 call sites" de `<SinalChip peso="contexto"`. Após esta fase: 4 (existentes) + 3 (novos em `AnalysisView`) = 7. Atualizar o número E o comentário que lista onde cada um está.

---

### `web/src/App.jsx` — `HistoricoPill` com prop `microtexto` (HIER-03)

**Analog exato:** o próprio `HistoricoPill` atual (`App.jsx:6750-6797`, lido nesta sessão) — a fase estende a assinatura (`microtexto`, `A`, `didatica`, `dados`) sem quebrar os 2 call sites que NÃO passam essas props (cauda do Radar, lista do Operador IA — continuam com números crus, D-09).

**Assinatura atual:**
```jsx
function HistoricoPill({ historico, elegivel, aposentado, operador, hojeYmd, compacto }) {
```
**Nova (D-09, três formas mutuamente exclusivas — já especificado, código completo no UI-SPEC linhas 351-390):** adiciona `microtexto, A, didatica, dados` à lista de parâmetros.

**Call site do `AtivoCard` a editar** (`App.jsx:3771-3775`, lido nesta sessão):
```jsx
{sc && sc.melhorSetup && (
  <div style={{ marginTop: "8px" }}>
    <HistoricoPill historico={sc.setupHistorico} elegivel={sc.setupElegivel} operador={operador} />
  </div>
)}
```
Vira (D-07/D-09, UI-SPEC linha 339-341): adiciona `microtexto A={A} didatica={didatica} dados={dadosDoCard}`; o `marginTop: "8px"` do wrapper vira `SP[2]` (tabela RITMO-01, linha "Elegibilidade, gap plano/contexto→elegibilidade" — já conforme, só troca a string por `SP[2]`).

**Cláusula tocável — analog de `SetorAlvo`:** `web/src/entendimento.jsx:87`, `export function SetorAlvo({ setorId, dados, rotulo, A, didatica, ativo = true, style, children })`. Uso já existente idêntico ao que a fase pede em `LinhaContexto` (`App.jsx:1473`):
```jsx
<SetorAlvo setorId="fundamento" rotulo="o fundamento" A={A} didatica={didatica} dados={dados} style={{ display: "inline-flex" }}>
  <SinalChip peso="contexto" label="FUNDAMENTO" value={score} explicavel ariaLabel={ariaFundamento(score, modo)} />
</SetorAlvo>
```
`HistoricoPill` reusa exatamente esse padrão para `setorId="analise"` envolvendo a cláusula "por que importa" — código completo já no UI-SPEC (linhas 419-424).

---

### `web/src/App.jsx` — fold-ins D-17/D-18

**D-17 — `FundamentoTabela` (`App.jsx:1558-1593`, lido nesta sessão):** linha 1576 hoje:
```jsx
{f.score && <SinalChip peso="contexto" label="FUNDAMENTO" value={f.score} ariaLabel={ariaFundamento(f.score, "estudo")} />}
```
Remove só a prop `label="FUNDAMENTO"` — o cabeçalho `<span>FUNDAMENTO</span>` da linha 1572 continua intocado.

**D-18 — `LinhaContexto` (`App.jsx:1473-1476`, lido nesta sessão):**
```jsx
<SetorAlvo setorId="fundamento" rotulo="o fundamento" A={A} didatica={didatica} dados={dados} style={{ display: "inline-flex" }}>
  <SinalChip peso="contexto" label="FUNDAMENTO" value={score} explicavel ariaLabel={ariaFundamento(score, modo)} />
</SetorAlvo>
```
`style` do `SetorAlvo` ganha `padding: "10px 6px", margin: "-10px -6px"` (código completo já no UI-SPEC linhas 464-467) — técnica de cancelamento de margem, sem analog direto no código atual (é padrão CSS genérico, não específico do repo).

---

### RITMO-01 — constante `SP` e migração de valores px literais

**Não há analog no código atual** (nenhuma constante de escala 4/8pt existe hoje em `App.jsx`) — a fonte é o próprio `qa/AUDITORIA-Design-System-v1.md §3.2`, já citada no UI-SPEC com a constante pronta:
```js
const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };
```
Colocar ao lado de `DIR_STYLE`/`REC_STYLE` (mesmo bloco de constantes de apresentação, região `App.jsx:1070-1110` antes da remoção do KpiBlock, ou onde `REC_STYLE` estiver após a remoção).

**Padrão de comentário de constante de apresentação a copiar** (`App.jsx:1085-1090`, comentário de `tierOf`):
```js
// 2.3: tier de oportunidade pela confluência do STU. Verde/vermelho seguem
// reservados a sinal de mercado ... o tier é OUTRO eixo semântico e por isso
// tem paleta própria.
```
`SP` replica esse estilo (decisão + razão), já escrito no UI-SPEC linhas 47-52.

**Tabela de substituição valor→degrau:** já integralmente especificada no `43-UI-SPEC.md` seção "Mapeamento valor herdado → degrau (D-15)" com citação de linha exata para cada ponto (`SinalChip:1393`, `LinhaContexto:1458`, `PlanoOperacionalBloco:1508/1515/1520/1525/1529/1532`, `HistoricoPill:6777`, `TimingBadge:3358`, elegibilidade `:3772`) — usar aquela tabela verbatim, não há necessidade de re-derivar.

---

## Shared Patterns

### Guardião cruzado skill_ref.py ↔ copy.js (paridade byte-a-byte)
**Source:** `web/tests/test_vocabulario_espelho.mjs` (lido integralmente nesta sessão, 213 linhas).
**Apply to:** `RECONCILIACAO_ELEGIBILIDADE`.

Padrão de extensão exato — adicionar aos arrays já existentes no topo do bloco (linhas 120-128):
```js
const DICTS = ["HISTORICO", "HISTORICO_ROTULO", "ENTRADA_AUTO"]; // → acrescentar "RECONCILIACAO_ELEGIBILIDADE"
const MODO_JS = { educacional: "estudo", operador: "operador" }; // sem mudança
const CHAVE_JS = { HISTORICO: "historico", HISTORICO_ROTULO: "historicoRotulo", ENTRADA_AUTO: "entradaAuto" };
// → acrescentar RECONCILIACAO_ELEGIBILIDADE: "reconciliacaoElegibilidade"
const CHAVES_ESPERADAS = {
  HISTORICO: [...], HISTORICO_ROTULO: [...], ENTRADA_AUTO: [...],
  // → acrescentar RECONCILIACAO_ELEGIBILIDADE: ["elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado"],
};
```
O laço principal (linhas 132-167) já itera sobre `DICTS` genericamente — nenhuma outra edição estrutural necessária além dos 3 arrays acima. O parser `blocoDoDict`/`blocoDoModo`/`paresDoModo` (linhas 101-118) funciona por regex genérico sobre `NOME = { ... }` — compatível sem alteração com o novo dict, desde que `RECONCILIACAO_ELEGIBILIDADE` siga o MESMO shape textual (`"modo": { "chave": "valor", ... },`).

**Cuidado (ítem 5 do guardião, linhas 181-190):** o guardião varre se `App.jsx` NÃO hardcoda nenhum valor de texto do dict novo — como o front usa `reconciliacaoTxt()` (nunca string literal), isso já é satisfeito por construção, mas o item roda automaticamente sobre `DICTS` também para o novo nome.

### Guardião ban-list de token dentro do corpo de função (grep sem falso-positivo de comentário)
**Source:** `web/tests/test_sinal_chip_ui.mjs` (lido integralmente nesta sessão, 193 linhas) — é O modelo direto para o novo `test_ritmo_sp.mjs` que o UI-SPEC pede.
**Apply to:** guardião RITMO-01 (varredura de px solto fora de `SP[N]`).

Padrão de infraestrutura a copiar literalmente (linhas 18-35):
```js
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}
```
Usar `functionBody("SinalChip")`, `functionBody("LinhaContexto")`, `functionBody("PlanoOperacionalBloco")`, `functionBody("HistoricoPill")` + um recorte manual do trecho do `AtivoCard` entre a manchete e a linha de elegibilidade (mesma técnica de `test_decisao_modo.mjs:33-34`, `app.slice(app.indexOf(...), app.indexOf(...))`), depois `semComentarios()` em cada, depois regex de ban-list:
```js
// modelo de asserção (adaptar path/valor):
ok("corpo de X não usa px literal solto em margin/padding/gap fora de SP[N]/SP_OPTICO_*",
  !/(?:margin|padding|gap)(?:Top|Bottom|Left|Right)?:\s*"(?!0")\d+(?:\.\d+)?px/.test(semComentarios(functionBody("X"))));
```
(regex exata a ajustar pelo planner/executor conforme os casos reais — inclusive strings compostas tipo `"9px 11px"` — mas a INFRAESTRUTURA `functionBody`/`semComentarios` e o estilo `ok(name, cond)` devem vir literalmente deste arquivo.)

**Descoberta automática de teste novo:** `scripts/executar.sh:33` (`for t in web/tests/*.mjs`) — `test_ritmo_sp.mjs` é pego sem registro manual (confirmado no 42-PATTERNS, mesma linha).

### Guardião de reconciliação datada ("REVERSÃO DELIBERADA")
**Source:** `web/tests/test_decisao_modo.mjs:44-48`, `web/tests/test_fundamento_ui.mjs:16/24/49`, `web/tests/test_fase22_componentes_compartilhados.mjs:354/412/435` (todas lidas por grep nesta sessão, formato idêntico).
**Apply to:** qualquer guardião que perca a asserção original por remoção de código (KpiBlock, DIR_STYLE/SCALE_STYLE).

Formato canônico (extraído de `test_decisao_modo.mjs:44-48`):
```js
// REVERSÃO DELIBERADA (AAAA-MM-DD, Fase N, ID): o que existia, por que
// existia, por que sai agora — sem apagar o comentário nem a asserção
// morta silenciosamente; se a asserção não tem mais o que testar, o
// comentário sozinho é a prova de que a mudança foi deliberada.
```
Nunca deletar o bloco de teste nem o comentário anterior — acrescentar, nunca substituir (regra do repositório, confirmada em CLAUDE.md "Histórico não se reescreve" e replicada nos guardiões de teste).

### Componente `SetorAlvo` (âncora didática tocável)
**Source:** `web/src/entendimento.jsx:87`, uso em `App.jsx:1473-1476` (`LinhaContexto`, fundamento).
**Apply to:** cláusula tocável do Estudo em `HistoricoPill` (D-11) e área de toque ampliada do chip de fundamento (D-18) — mesmo componente, duas props diferentes (`children` vs `style` de padding/margem).

---

## No Analog Found

| Arquivo/trecho | Papel | Fluxo de dado | Razão |
|---|---|---|---|
| `const SP = {...}` | config (constante de apresentação) | n/a | Primeira escala de espaçamento nomeada do projeto — fonte é a auditoria de design system (`qa/AUDITORIA-Design-System-v1.md`), não código existente. Padrão de COMENTÁRIO copiado de `tierOf`/`DIR_STYLE`, mas o valor/estrutura é novo. |
| `web/tests/test_ritmo_sp.mjs` | test (guardião novo) | transform | Nenhum guardião hoje varre `margin`/`padding`/`gap` px solto — é o primeiro do tipo. Infraestrutura (`functionBody`/`semComentarios`) 100% copiada de `test_sinal_chip_ui.mjs`; a REGRA de ban-list (px fora de `SP[N]`) é nova. |
| `SP_OPTICO_CHIP_PRIMARIO`/`SP_OPTICO_ANEL` | config (exceção nomeada) | n/a | Já registradas como decisão fechada no `42-UI-SPEC.md` — não há código ainda, só a decisão; o planner só precisa declarar as duas constantes com o valor já aprovado. |

---

## Metadata

**Analog search scope:** `server/app/skill_ref.py` (seção "Vocabulário do histórico medido por setup", linhas 355-440), `web/src/copy.js` (`historicoRotulo`/`historicoTxt`, linhas 585-599/1351/1600), `web/src/App.jsx` (`DIR_STYLE`/`SCALE_STYLE`/`KpiCell`/`KpiBlock` 1072-1367, `SinalChip` 1383-1454, `LinhaContexto`/`PlanoOperacionalBloco`/`FundamentoTabela` 1455-1593, `AnalysisView` 1616-1675, `AtivoCard` call site 3760-3775, `HistoricoPill` 6750-6797), `web/src/entendimento.jsx` (`SetorAlvo` linha 87), `web/tests/test_vocabulario_espelho.mjs` (integral, 213 linhas), `web/tests/test_sinal_chip_ui.mjs` (integral, 193 linhas), `web/tests/test_decisao_modo.mjs` (integral, 63 linhas), grep de "REVERSÃO DELIBERADA" em todo `web/tests/*.mjs`.
**Files scanned:** 9 leituras diretas (nenhuma sobreposta) + 4 greps direcionados. `App.jsx` (~7600 linhas) lido só por trechos não sobrepostos.
**Pattern extraction date:** 2026-09-27
