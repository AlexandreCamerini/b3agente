# Phase 41: Consolidação de registros de tela - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** ~6 (1 novo módulo registro provável + 4 consumidores editados no `App.jsx` + `PET_TELAS`/teste de paridade)
**Analogs found:** 5 / 5 (nenhum "no analog" — o próprio par que a fase consolida já é o analog de si mesmo)

Nenhum RESEARCH.md/UI-SPEC nesta fase (research desligada, `--skip-ui`, D-04
trava zero mudança visível). Este mapa é só leitura do código-fonte existente
citado em CONTEXT.md/CLAUDE.md.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| Novo módulo de registro (ex. `web/src/telas.js`, nome a critério do planner — D-Discretion) | model/config (registro estático) | transform (id → metadata estático) | `web/src/opcoes/memoriaOpcoes.js` (módulo puro sem React/store) | role-match |
| `web/src/App.jsx` — `BottomNav`/`defs` (~1024-1050) | component | request-response (render) | ele mesmo (edição in-place) | exact |
| `web/src/App.jsx` — `ajudaSecoes(cp, operador)` (~2492) | utility (gerador de conteúdo) | transform | ele mesmo | exact |
| `web/src/App.jsx` — `tourPassos(cp)` (~2550-2582) | utility (gerador de conteúdo) | transform | ele mesmo | exact |
| `web/src/App.jsx` — `petTela`/`petSnapshot` (~9125-9200) | hook (useMemo) | event-driven (deriva de `tab`/`carteiraView`/dados runtime) | ele mesmo | exact |
| Novo teste de paridade registro↔`PET_TELAS` | test (guardian estático) | batch/transform (leitura de fonte, sem build/servidor) | `web/tests/test_pet_opcoes.mjs` (já deriva `BottomNav.defs` e cruza com `PET_TELAS` + `case` do switch) | exact |
| `server/app/conceitos.py:565` `PET_TELAS` | config (allowlist) | CRUD (leitura estática) | inalterado — só é LIDO pelo novo teste | n/a (não é editado nesta fase, CONTEXT.md: "nenhuma mudança de comportamento no servidor esperada") |

## Pattern Assignments

### Novo módulo de registro de telas

**Analog:** `web/src/opcoes/memoriaOpcoes.js` (Fase 40, ESTADO-01)

**Por que este e não outro:** é o exemplo mais recente de módulo `web/src/*`
puro (sem import de React, sem store, sem I/O), com funções pequenas e
comentário de cabeçalho que declara o CONTRATO e por que ele não importa
nada de fora — exatamente a forma que D-02 pede para o registro (só
estrutura: id, rótulo/ícone de barra, flag+ordem, posição no tour).

**Cabeçalho / contrato pattern** (`web/src/opcoes/memoriaOpcoes.js:1-9`):
```javascript
// Fase 40 (ESTADO-01) — módulo puro de memória em sessão do ticker + aba
// ativa da tela Opções. Sem React, sem I/O, sem store: só as três regras de
// precedência/validação que a fiação (App.jsx/OpcoesScreen.jsx) consome.
// A ausência de import de React/store aqui é o próprio contrato de D-01
// (a memória nunca passa por deviceStore/serverStore/localStorage).
```

**Função pura pequena, guard clause primeiro** (`memoriaOpcoes.js:11-16`):
```javascript
export function abaInicialOpcoes(abas, abaInicial, memoria) {
  if (!Array.isArray(abas)) return "oportunidades";
  if (abas.includes(abaInicial)) return abaInicial;
  if (memoria && abas.includes(memoria.aba)) return memoria.aba;
  return "oportunidades";
}
```
Aplicar ao registro: cada "consumidor" (ordem na barra, id do tour, id da
allowlist) deve ser uma função pura de leitura sobre o array estático —
sem side effect, sem hook.

**Alternativa considerada e descartada:** `web/src/glossario.js` (`ANCORAS_KB`,
124 linhas) é outro registro estático candidato, mas é um dicionário
id→texto (conteúdo), não id→estrutura de navegação — mais distante do que
D-02 pede. `memoriaOpcoes.js` é o match melhor por ser estrutura, não texto.

---

### `BottomNav`/`defs`, `ajudaSecoes`, `tourPassos`, `petTela`/`petSnapshot` — edição in-place

Estes 4 são o PRÓPRIO objeto da consolidação — não há "analog externo"
melhor que o código atual deles. O padrão a preservar ao editar cada um:

**`defs` — rótulo por modo com fallback literal** (`web/src/App.jsx:1030-1033`):
```javascript
const defs = [["evolucao", "Acompanhar"], ["radar", (cp && cp.tabRadar) || "Radar"],
  ["mercado", (cp && cp.tituloWatchlist) || "Watchlist"],
  ["carteira", (cp && cp.tituloPortfolio) || "Portfólio"],
  ["opcoes", (cp && cp.tabOpcoes) || "Opções"]];
```
Regra a manter: o TEXTO do rótulo continua vindo de `cp.*` (copy.js) — o
registro deve carregar só o `id`, a CHAVE do `cp.*` (ou nada, se
`ajudaSecoes`/`defs` já resolvem por si) e a ordem/flag "na barra", nunca a
string. D-02 é explícito sobre isso.

**`ajudaSecoes` — chaveada por TÍTULO, não por id** (`web/src/App.jsx:2492-2497`):
```javascript
function ajudaSecoes(cp, operador) {
  const tRadar = cp.tituloRadar, tWl = cp.tituloWatchlist, tPort = cp.tituloPortfolio;
  const tOpc = cp.tituloOpcoes || "Opções";
  ...
  return [
    ["O que é o Boris+", [...]],
    ["Os dois modos", [...]],
    ["Acompanhar (início)", [...]],
    [tRadar, [...]], [tWl, [...]], [tPort, [...]], [tOpc, [...]],
    ["Operador IA", [...]], ["Fundamento (A/B/C)", [...]],
    ["Eficiência da IA", [...]], ["Avisos importantes", [...]],
  ];
}
```
ACHADO (registrar, não corrigir — D-04): `ajudaSecoes` tem 11 seções; só 6
delas correspondem a uma "tela" (`evolucao` via "Acompanhar (início)",
`radar`, `mercado`, `carteira`, `opcoes`, `agente` via "Operador IA"). As
outras 5 ("O que é o Boris+", "Os dois modos", "Fundamento", "Eficiência da
IA", "Avisos importantes") não são tela nenhuma — são conteúdo institucional
intercalado. `historico` e `perfil` NÃO têm seção própria em `ajudaSecoes`.
Se o planner mapear ids do registro → seções por match de título, este
descasamento (nem toda seção é tela, nem toda tela tem seção) precisa virar
teste que tolera a lacuna, não que force paridade 8-com-8 aqui (D-01 só
exige paridade 8-com-8 entre registro e `PET_TELAS`, não entre registro e
`ajudaSecoes`).

**`tourPassos` — cobre só 4 das 8 telas + 2 passos não-tela** (`web/src/App.jsx:2569-2578`):
```javascript
function tourPassos(cp) {
  return [
    ["Bem-vindo · você está em Acompanhar", "..."],
    ["O que o Boris+ é — e o que não é", "..."],
    ["1 · Descubra no " + cp.tituloRadar, "..."],
    ["2 · Acompanhe na " + cp.tituloWatchlist, "..."],
    ["3 · Simule no " + cp.tituloPortfolio, "..."],
    ["4 · Estude estruturas em " + (cp.tituloOpcoes || "Opções"), "..."],
  ];
}
```
D-02 já resolve isso: os 2 primeiros passos (boas-vindas, "o que o app é")
ficam FORA do registro por decisão explícita — não são tela. Os 4 restantes
mapeiam 1:1 com `evolucao`/`radar`/`mercado`/`opcoes` (falta `carteira`? não
— reler: passo "3 · Simule" é `carteira`). `agente`, `historico`, `perfil`
não têm passo de tour — coerente com D-01 (registro cobre as 8, mas nem toda
tela precisa aparecer no tour; campo "posição no tour" fica `null`/ausente
para essas 3).

**`petTela`/`petSnapshot` — switch já indexado por id, `default: return {}`**
(`web/src/App.jsx:9138-9139` e comentário em 9124-9129):
```javascript
const petTela = tab === "carteira" ? (carteiraView === "historico" ? "historico" : carteiraView === "agente" ? "agente" : "carteira") : tab;
const petSnapshot = useMemo(() => {
  if (!data) return {};
  switch (petTela) {
    case "carteira": { ... }
    case "evolucao": { ... }
    case "radar": { ... }
    case "agente": { ... }
    case "historico": { ... }
    case "opcoes": { ... }
    case "perfil": { ... }
    default:
      return {};
  }
}, [petTela, data, quotes, wlScan]);
```
D-03 já decide: este switch continua existindo tal qual (dados de runtime
não vão para o registro estático). O que muda, a critério do planner: um
teste estático que cruza os `case "<id>"` deste switch com os ids do
registro (mesma técnica de `test_pet_opcoes.mjs`, ver abaixo) — note que
`"mercado"` PROPOSITALMENTE não tem `case` (comentário no próprio código:
snapshot dele vem do resumo dentro do `PetSheet`, não deste switch) — o
teste de paridade precisa esse escape hatch para não quebrar em falso
positivo.

---

### Teste de paridade registro ↔ `PET_TELAS`

**Analog primário:** `web/tests/test_pet_opcoes.mjs` (linhas 42-93) — já faz
EXATAMENTE o formato de "dois pontos testados, leitura de fonte, sem import
cross-language" que CLAUDE.md manda para `defaults.py`↔`catalog.js`, mas
aplicado a telas em vez de prompts. Hoje deriva de `BottomNav.defs`; com o
registro novo, passa a derivar do registro.

**Técnica de extração por regex + matchAll** (`test_pet_opcoes.mjs:42-49`):
```javascript
const defsBloco = app.match(/const defs = \[\[([\s\S]*?)\]\];/);
ok("BottomNav.defs foi encontrado em App.jsx (a fonte derivada deste guardião)", !!defsBloco);
const abasDaBarra = defsBloco
  ? [...("[[" + defsBloco[1] + "]]").matchAll(/\["([a-z]+)",/g)].map((m) => m[1])
  : [];
```

**Leitura da allowlist Python sem import** (`test_pet_opcoes.mjs:56-58`):
```javascript
const PET_TELAS = (conceitos.match(/PET_TELAS = \(([^)]*)\)/) || [, ""])[1]
  .split(",").map((s) => s.trim().replace(/^"|"$/g, "")).filter(Boolean);
ok("conceitos.PET_TELAS foi lido do backend", PET_TELAS.length >= 7, "achou: " + PET_TELAS.join(", "));
```

**Loop de cruzamento id-a-id com mensagem de causa-raiz na falha** (`test_pet_opcoes.mjs:60-71`):
```javascript
for (const aba of abasDaBarra) {
  if (aba !== "mercado") {
    ok(`a aba "${aba}" da barra tem ramo próprio no switch do petSnapshot`,
       new RegExp(`case "${aba}": \\{`).test(app),
       "sem `case`, o snapshot cai no `default: return {}` e o Boris fala da tela sem dado nenhum");
  }
  ok(`a aba "${aba}" da barra está na allowlist conceitos.PET_TELAS`,
     PET_TELAS.includes(aba),
     "fora da allowlist, /api/assistente responde 400 'Tela desconhecida.'");
}
```

**Analog secundário (mesmo padrão "dois pontos testados", cross-language, Python):**
`server/tests/test_auditoria_prompts.py:255-268` (`test_a8ii_paridade_defaults_carteira_com_catalog_js`):
```python
def test_a8ii_paridade_defaults_carteira_com_catalog_js():
    """web/src/catalog.js espelha o TEXTO dos defaults do servidor (o aparelho
    monta o estado sem servidor). Byte a byte: divergiu, este teste acusa."""
    import os, re
    caminho = os.path.join(os.path.dirname(__file__), "..", "..", "web", "src", "catalog.js")
    with open(caminho, encoding="utf-8") as f:
        src = f.read()
    prompts = defaults.default_llm_prompts()
    for chave in ("carteiraStopAlvo", "carteiraStopAlvoOperador"):
        m = re.search(chave + r":\s*`([^`]*)`", src)
        assert m, f"literal de {chave} não encontrado no catalog.js"
        assert m.group(1) == prompts[chave], f"{chave} divergiu do servidor"
```
Diferença chave a preservar: nenhum dos dois testes faz import
cross-language (JS não importa Python nem vice-versa) — ambos leem o
arquivo do outro lado como TEXTO e casam regex. O novo teste de paridade
registro↔`PET_TELAS` deve seguir o mesmo desenho: `web/tests/*.mjs` lendo
`server/app/conceitos.py` como string (nunca subprocess Python, nunca
import). CONTEXT.md confirma: "não há 'um' ponto cruzando JS/Python, só
dois pontos testados".

**Técnica de extração de função pura via `extrair()`/`eval` (para testar
`tourPassos`/`ajudaSecoes`/o registro sem build)** (`web/tests/test_tour_opcoes.mjs:26-65`):
```javascript
function extrair(nome, fonte) {
  const i = fonte.indexOf("function " + nome + "(");
  if (i < 0) return null;
  let nivel = 0, dentro = false;
  for (let k = i; k < fonte.length; k++) {
    if (fonte[k] === "{") { nivel++; dentro = true; }
    else if (fonte[k] === "}") { nivel--; if (dentro && nivel === 0) return fonte.slice(i, k + 1); }
  }
  return null;
}
const fonteTour = extrair("tourPassos", app);
const tourPassos = fonteTour ? eval("(" + fonteTour + ")") : null;   // eslint-disable-line no-eval
```
Usar esta técnica (não regex de contagem) para qualquer novo teste que
precise EXECUTAR `ajudaSecoes`/`tourPassos`/o registro com um `cp` fake —
o próprio comentário do arquivo explica por quê: "contar passos por regex
daria falso verde na primeira reorganização do array."

## Shared Patterns

### Paridade cross-file sem import cross-language
**Fonte:** `server/tests/test_auditoria_prompts.py` (Python lê `.js` como
texto) + `web/tests/test_pet_opcoes.mjs` (JS lê `.py` como texto)
**Aplicar a:** o novo teste de paridade registro↔`PET_TELAS` — nunca criar
um "único ponto" que importe Python de JS ou rode subprocess; sempre leitura
de fonte + regex, como os dois exemplos acima.

### Módulo puro sob `web/src/`, sem React/store
**Fonte:** `web/src/opcoes/memoriaOpcoes.js:1-9`
**Aplicar a:** o novo arquivo de registro (D-Discretion sobre nome/local) —
zero import de React, zero import de `persistence.js`, funções pequenas
exportadas, comentário de cabeçalho justificando a ausência de I/O.

### Guardião como rede de segurança até a consolidação
**Fonte:** `web/tests/test_pet_opcoes.mjs:1-24` (comentário de cabeçalho)
**Aplicar a:** o novo teste deve citar explicitamente que substitui/absorve
este guardião (ele mesmo se autodeclara "rede de segurança até lá,
referindo-se ao C3/Fase 41") — ao editar `test_pet_opcoes.mjs` para ler do
registro em vez de `BottomNav.defs`, manter o comentário histórico e somar
uma nota datada (guardrail do repo: "guardiões de teste não se apagam —
reversão deliberada atualiza o guardião com nota").

## Achados registrados (D-04: não corrigir agora)

1. `ajudaSecoes` tem 11 seções, só 6 mapeiam 1:1 com uma tela do registro;
   `historico` e `perfil` não têm seção própria. Não é bug a corrigir nesta
   fase — é descasamento estrutural a documentar no registro (campo
   "seção de ajuda" pode ficar ausente/null para essas duas).
2. `tourPassos` cobre 4 das 8 telas (`evolucao`, `radar`, `mercado`,
   `opcoes` — falta explicitamente `carteira` no id mas está coberta pelo
   passo "3 · Simule no <Portfólio>"; confirmar ao escrever o plano se o
   id certo do passo 3 é `carteira`); `agente`, `historico`, `perfil` não
   têm passo.
3. `BottomNav.defs` só cobre 5 telas (as da barra); `agente`, `historico`,
   `perfil` chegam por `carteiraView`/navegação, não pela barra — D-01 já
   antecipa isso (flag "na barra" no registro, não presença obrigatória).

## Guardiões existentes que fixam a FORMA atual (reconciliação datada exigida, nunca deleção)

| Guardião | O que pina hoje | Por que quebra com a consolidação |
|---|---|---|
| `web/tests/test_pet_opcoes.mjs:42-93` | Deriva `abasDaBarra` de `const defs = [[...]]` via regex; cruza contra `PET_TELAS` e `case "<aba>":` do switch | Se o registro passar a ser a fonte de `defs` (D-Discretion permite reescrever `BottomNav` para ler do registro), a regex `const defs = \[\[...\]\];` pode deixar de casar — precisa apontar para o registro novo, com nota datada explicando a migração |
| `web/tests/test_tour_opcoes.mjs:71-73` | `passos.length === 6` (contagem literal), extrai `tourPassos`/`ajudaSecoes` via `extrair()`+`eval` e roda de verdade | Continua válido inalterado SE `tourPassos`/`ajudaSecoes` continuarem como funções que recebem `cp` e devolvem array (D-02 mantém isso) — só quebra se o planner mover os textos para dentro do registro (D-02 proíbe) |
| `web/tests/test_ajuda_help.mjs:18-43` | Existência de `ajudaSecoes`/`tourPassos` como `function ...(`, rotas de UI (`perfilView === "ajuda"`), persistência de `tourSeen` nos dois stores | Não deve quebrar (D-04); é o guardião mais amplo de "a Ajuda/Tour ainda funcionam" — útil como smoke test pós-refactor |
| `web/tests/test_operador_ia_subtela.mjs` | Nenhum `tab === "agente"` órfão fora de comentários/COPY | Continua válido; não toca telas do registro diretamente, mas é o padrão de "higiene de comentário antes de contar" a reaproveitar se o novo teste também fizer contagem sobre `App.jsx` bruto |
| `server/tests/test_pet_todas_telas.py` | 8 telas em `PET_TELAS`; para cada uma, `/api/pet/resumo?tela=<aba>` responde 200 com `fala` não vazia | Backend não muda nesta fase (CONTEXT.md) — continua passando sem edição; serve de referência para o formato "para cada id, uma asserção" que o novo teste JS deve espelhar do lado front |

## Metadata

**Analog search scope:** `web/src/App.jsx`, `web/src/opcoes/`,
`web/tests/*.mjs`, `server/app/conceitos.py`, `server/app/main.py`,
`server/tests/test_auditoria_prompts.py`, `server/tests/test_pet_todas_telas.py`
**Files scanned:** ~12
**Pattern extraction date:** 2026-09-25
