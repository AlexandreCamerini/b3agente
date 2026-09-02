# Phase 13: Uso real visível na interface + enforcement no iOS - Pattern Map

**Mapped:** 2026-08-29
**Files analyzed:** 6 (2 backend, 4 frontend — todos MODIFICADOS, nenhum arquivo novo além do endpoint dentro de `main.py`)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `server/app/main.py` (novo endpoint `GET /api/watchlist/quota`, próximo às linhas 1043-1110) | route (request-response) | request-response, read-only | `server/app/main.py:460-479` (`ai_quota`) | exact |
| `server/app/plan.py` (nenhuma mudança de lógica esperada — só é lido pelo endpoint novo) | service (regra de negócio pura) | CRUD (read) | já existente, `can_add_ticker`/`can_grow_watchlist_to` | exact (reuso direto, sem nova função) |
| `web/src/persistence.js` — `serverStore.putWatchlist`/`addWatchlistTicker` (linhas 157-158) e novo método `watchlistQuota()` | store/service (thin API wrapper) | request-response | `web/src/persistence.js:284` (`aiQuota: () => api.aiQuota()`) | exact |
| `web/src/persistence.js` — `deviceStore.putWatchlist`/`addWatchlistTicker` (linhas 791-838) + novo método `watchlistQuota()` | store (local-first com gate fail-closed) | request-response + file-I/O (localStorage) | `web/src/persistence.js:1148-1152` (`deviceStore.analisesNoMes`) para o método de leitura; `addWatchlistTicker` atual (mesma função, precisa ganhar o gate) | exact |
| `web/src/plan.js` — `canAddTicker` (correção de tom, remover CTA) | utility (pure function) | transform | `server/app/plan.py:75-82` (`can_add_ticker`, já corrigido na Fase 12) | exact (mirror cross-language) |
| `web/src/App.jsx` — subtítulo Watchlist (~3427), `CatalogModal` (~6618), `AtividadeIAScreen` bloco CUSTO ESTIMADO (~4984-4992) | component (React, texto only) | request-response (consome dado já carregado em `data`/estado local) | `web/src/App.jsx:5712-5723` (bloco "orçamento brapi: X/Y") para o fragmento numérico; `web/src/App.jsx:5566-5570` (`admin.usoIA.cotaPorUsuarioDia ?? "—"`) para o estado indisponível | exact |

## Pattern Assignments

### `server/app/main.py` — novo endpoint `GET /api/watchlist/quota` (route, request-response)

**Analog:** `server/app/main.py:460-479` (`ai_quota`)

**Padrão exato a espelhar** — mesmo formato de resposta (`count`/`limit` em vez de `monthUsed`/`monthLimit`, mas mesma filosofia: contagem real + limite do plano em nível raiz, nunca aninhado):
```python
@app.get("/api/ai/quota")
async def ai_quota(scope: Optional[str] = Depends(current_scope)):
    """... C-33 (fase 5): `monthUsed`/`monthLimit` em nível RAIZ ..."""
    avail = managed.is_available()
    if not scope:
        return {"managed": avail, "loggedIn": False, "byok": False, "quota": None,
                "monthUsed": None, "monthLimit": None}
    cfg = store.get(_conn, "config", user_id=scope)
    byok = bool(llm.resolve_key(cfg))
    snap = metering.snapshot(_conn, scope, managed.daily_quota()) if (avail and not byok) else None
    return {"managed": avail, "loggedIn": True, "byok": byok, "quota": snap,
            "monthUsed": metering.month_used(_conn, scope),
            "monthLimit": _plano_do_escopo(scope).get("max_analyses_per_month")}
```

**Adaptação recomendada para o endpoint novo** (contrato do `13-UI-SPEC.md`, `{ "count": N, "limit": N|null }`):
- numerador: `len(store.get(_conn, "watchlist", user_id=scope) or [])` — mesma leitura já usada em `watchlist_add`/`put_watchlist` (linhas 1102, 1150).
- denominador: `_plano_do_escopo(scope).get("max_watchlist")` — mesmo helper já usado pelos dois endpoints de watchlist existentes (linhas 1068, 1103).
- Não requer `scope` obrigatório: escopo anônimo já cai no `PLAN_FREE`/`ACTIVE_PLAN` via `_plano_do_escopo(None)` (ver `plan.py:44-47`, `ACTIVE_PLAN` é o fallback) — diferente de `ai_quota`, que faz early-return especial pra anônimo; aqui não é necessário, porque watchlist SEMPRE tem um plano resolvido (mesmo anônimo).
- Colocar fisicamente perto do bloco `# ---- Watchlist ----` (linha 1035), antes ou depois de `put_watchlist`/`watchlist_add` — não junto ao bloco de IA (linha 460), para manter a organização por domínio já existente no arquivo.

**Helper reutilizado (`_plano_do_escopo`)** — `server/app/main.py:122`, já usado nos dois endpoints de watchlist atuais (linhas 1068, 1103) e no `ai_quota` (linha 479). Não recriar.

**Regra de contagem (nunca hardcodar)** — `server/app/plan.py:31-42` (`PLAN_FREE["max_watchlist"] = 10`, `PLAN_PRO["max_watchlist"] = None`). O endpoint novo só LÊ, nunca reimplementa o número.

---

### `server/app/plan.py` (leitura, sem mudança de lógica esperada)

**Analog:** já é a fonte única — nenhuma extração necessária além de confirmar a assinatura:
```python
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)
```
Se o planner decidir expor `count`/`limit` calculados fora de `plan.py` (endpoint lê `plan.get("max_watchlist")` direto), não é necessária nova função aqui — `PLAN_FREE`/`PLAN_PRO` já são a fonte, `can_add_ticker`/`can_grow_watchlist_to` continuam servindo só o gate de escrita (`PUT`/`POST` existentes), não o novo `GET` de leitura.

---

### `web/src/persistence.js` — `serverStore` novo método `watchlistQuota()` (service, request-response)

**Analog:** `web/src/persistence.js:284`
```javascript
aiQuota: () => api.aiQuota(), // FASE 3: cota da IA gerenciada
```
**Padrão a copiar** — método de uma linha, delega 100% para `api.js`, sem otimismo/cache local (mesma classe de dado "server-authoritative", D-05 do CONTEXT):
```javascript
watchlistQuota: () => api.watchlistQuota(),
```

**`web/src/api.js` — adicionar entrada nova**, mesmo padrão de `aiQuota`/`validateTicker`:
```javascript
// web/src/api.js:203-204 (analog)
addWatchlistTicker: (ticker) => req("POST", "/api/watchlist/add", { ticker }),
validateTicker: (ticker) => req("GET", "/api/validate/" + encodeURIComponent(ticker)),
// web/src/api.js:303 (analog mais próximo — GET simples, sem parâmetro)
aiQuota: () => req("GET", "/api/ai/quota"),
```
Nova entrada recomendada: `watchlistQuota: () => req("GET", "/api/watchlist/quota"),` (ou a rota que o planner escolher — nome fica a critério, conforme CONTEXT.md).

---

### `web/src/persistence.js` — `deviceStore` (iOS): gate fail-closed antes do `write()` (store, request-response + file-I/O)

**Analog para o método de leitura:** `web/src/persistence.js:1148-1152` (`deviceStore.analisesNoMes`)
```javascript
// FIX-C33 (Fase 5): mesmo contrato de serverStore.analisesNoMes acima —
// o aparelho NÃO mantém contador próprio de análises; lê o MESMO
// `monthUsed` do ledger do servidor via aiQuota(). É por isso que o
// local-first do iPhone abre exceção aqui, igual já abre para aiQuota.
async analisesNoMes() {
  ensure();
  const q = await api.aiQuota();
  return (q && typeof q.monthUsed === "number") ? q.monthUsed : null;
},
```
**Adaptação:** `watchlistQuota()` no `deviceStore` segue o MESMO formato (`ensure()` + chamada de rede direta + parse defensivo), delegando para `api.watchlistQuota()`.

**Analog para o gate fail-closed a inserir em `addWatchlistTicker`/`putWatchlist`:** o próprio arquivo já tem o vocabulário de erro de rede a reaproveitar, `web/src/persistence.js:822-826`:
```javascript
if (!info) {
  const msg = e && e.message ? e.message : "";
  dlog("e-validacao", "rejeitado: " + msg);
  throw new Error(/404|not found|encontrado/i.test(msg) ? "Ticker " + t + " não encontrado na B3. Verifique o código." : (msg || "Não foi possível validar o ticker agora. Tente de novo."));
}
```
**Regra de composição (D-04, fail-closed — DIVERGE do padrão `analisesNoMes`/`aiQuota`, que é fail-open):**
```javascript
// PSEUDOCÓDIGO da extensão de addWatchlistTicker (web/src/persistence.js:799-838)
// ANTES do bloco que grava (`doc.watchlist = [...doc.watchlist, info.t]; write();`):
let quota;
try {
  quota = await api.watchlistQuota(); // mesma cadência de analisesNoMes: rede a cada tentativa, sem cache (D-05)
} catch (e) {
  throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo."); // D-04, fail-closed
}
if (quota && typeof quota.limit === "number" && typeof quota.count === "number" && quota.count >= quota.limit) {
  throw new Error(`Voce atingiu o limite de ${quota.limit} ativos do plano ${quota.id || "free"}.`); // MESMO texto do backend (plan.py), não reinventar
}
// só então: doc.watchlist = [...]; write();
```
O MESMO gate se aplica a `putWatchlist` (linha 791-798), comparando o tamanho FINAL do array recebido contra `quota.limit` (mesma semântica de `can_grow_watchlist_to` no backend, `server/app/plan.py:85-100`) — não reusar a checagem item-a-item de `addWatchlistTicker` para o `PUT` em massa.

**Por que NÃO copiar o padrão fail-open de `A.analyze`** (`web/src/App.jsx:7257-7272`):
```javascript
// ANTI-PATTERN para este caso — NÃO copiar aqui:
let usedThisMonth = 0;
try {
  const n = await store.analisesNoMes();
  if (typeof n === "number") usedThisMonth = n;
} catch { /* falha-aberta: gate do servidor continua ativo */ }
```
Justificativa (D-04, já travada em CONTEXT.md): para análises existe gate autoritativo server-side (`_gate_analise`) que barra mesmo se o pré-check do cliente falhar aberto; para watchlist no iOS NÃO existe gate autoritativo (`deviceStore` grava direto em `localStorage`, sem passar pelo servidor) — falha-aberta aqui reabre o CR-01.

---

### `web/src/plan.js` — `canAddTicker` (utility, transform) — correção de tom

**Analog:** `server/app/plan.py:75-82` (já corrigido na Fase 12/CAP-07, é a fonte da verdade de tom)
```python
def can_add_ticker(current_count: int, plan: Optional[dict] = None) -> tuple:
    plan = plan or ACTIVE_PLAN
    limit = plan.get("max_watchlist")
    if limit is not None and current_count >= limit:
        return (False, f"Voce atingiu o limite de {limit} ativos do plano {plan['id']}.")
    return (True, None)
```
**Estado atual do arquivo espelho (a corrigir)** — `web/src/plan.js:16-22`:
```javascript
export function canAddTicker(count, plan = ACTIVE_PLAN) {
  if (plan.maxWatchlist != null && count >= plan.maxWatchlist) {
    return { ok: false, reason: `O plano ${plan.id} permite até ${plan.maxWatchlist} ativos. Faça upgrade para adicionar mais.` };
  }
  return { ok: true };
}
```
**Correção:** remover `" Faça upgrade para adicionar mais."`, alinhar a frase ao fato+motivo do backend: `` `Você atingiu o limite de ${plan.maxWatchlist} ativos do plano ${plan.id}.` `` (mesmo texto do Python, plural/tom idêntico — UI-SPEC exige "mesmo fato+motivo já fechado no backend"). `canAnalyze` (linha 25-30) já está sem CTA — só conferir, não mexer.

Também trocar `maxWatchlist: null` por `10` e `maxAnalysesPerMonth: null` por `30` em `PLAN_FREE` (linha 10) se o planner decidir que este arquivo passa a refletir os limites reais (hoje está desatualizado — CONTEXT.md nota isso como CAP-07 do front pendente). Confirmar com o ROADMAP/REQUIREMENTS se isso é escopo desta fase antes de mudar os números.

---

### `web/src/App.jsx` — 3 pontos de exibição (component, texto)

**Analog para o fragmento "X/Y" com estado de alerta:** `web/src/App.jsx:5712-5723` (orçamento brapi)
```javascript
<div style={{ display: "flex", flexWrap: "wrap", gap: "5px 14px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO }}>
  <span>orçamento brapi: {orc.total}/{orc.tetoDia} hoje · cota {orc.cotaMes}/mês</span>
  ...
  <span style={orc.fatias && orc.fatias.spot && orc.fatias.spot.degradado ? { color: T.warn } : undefined}>
    estado do orçamento: {orc.fatias && orc.fatias.spot && orc.fatias.spot.degradado ? "degradado (TTL 3×)" : "normal"}
  </span>
  {proj && (
    <span style={proj.cabeNaCota === false ? { color: T.negative } : undefined}>
      projeção do mês: {proj.chamadasMes}/{proj.cotaMes} ({proj.percentualDaCota}%){proj.cabeNaCota === false ? " · NÃO CABE" : ""}
    </span>
  )}
</div>
```
Nota: este analog usa `T.negative` para "não cabe" — a UI-SPEC da Fase 13 é EXPLÍCITA que os 3 pontos novos usam `T.warn`, nunca `T.negative`/`T.positive` (P&L é reservado). Copiar a MECÂNICA (span condicional por `style`), não a cor.

**Analog para o estado "indisponível" (`—`):** `web/src/App.jsx:5566-5570`
```javascript
<div style={{ display: "flex", flexWrap: "wrap", gap: "5px 14px", color: T.textFaint, fontSize: "10.5px", fontFamily: MONO, marginBottom: "12px" }}>
  <span>cota/usuário/dia: {admin.usoIA.cotaPorUsuarioDia ?? "—"}</span>
  <span>teto global/dia: {admin.usoIA.tetoGlobalDia ?? "ilimitado"}</span>
```
Atenção: aqui `??  "ilimitado"` é usado para `tetoGlobalDia` (semântica "sem teto" = Pro/D-03), e `?? "—"` para `cotaPorUsuarioDia` (semântica "não sei agora"). A Fase 13 precisa dos DOIS estados distintos e não pode confundir — usar `??  "—"` só quando a chamada falhar/for indisponível, e OMITIR o segmento inteiro (não `?? "ilimitado"`) quando `limit === null` (D-03: "sem número fabricado", nem mesmo a palavra "ilimitado").

**Ponto 1 — Subtítulo Watchlist**, `web/src/App.jsx:3427-3429`:
```javascript
<p style={{ margin: "0 0 12px", color: T.textMuted, fontSize: "13px", maxWidth: "560px", lineHeight: 1.55 }}>
  {cp.subtituloWatchlist}{quotesAt ? "  ·  cotações " + quotesAt : ""}
</p>
```
Estende para incluir o segmento condicional `· ativos: <span>X/Y</span>` (ou `—`/omitido), seguindo a regra tipográfica do `13-UI-SPEC.md` (`<span>` só nos dígitos+barra, `fontFamily: MONO`, `fontWeight: 700`).

**Ponto 2 — `CatalogModal`**, `web/src/App.jsx:6618`:
```javascript
<div style={{ fontSize: "12.5px", color: T.textMuted, marginTop: "3px" }}>{catalogSel.length} de {data.catalog.length} selecionados</div>
```
Estende para `{catalogSel.length} de {data.catalog.length} selecionados · <span>X/Y</span> do plano free` — fonte do numerador é `catalogSel.length` (estado LOCAL em edição), fonte do limite é o MESMO `max_watchlist` do plano ativo (não reusar `data.watchlist.length`, ver contrato de dados do UI-SPEC).

**Ponto 3 — `AtividadeIAScreen`**, bloco CUSTO ESTIMADO, próximo a `web/src/App.jsx:4990-4992`:
```javascript
<div style={{ fontSize: "10px", color: T.textFaint, lineHeight: 1.5, marginTop: "9px" }}>
  Estimativa por preço de tabela dos modelos × câmbio (US$ 1 ≈ R$ {(ati.usdBrl || 5.4).toFixed(2).replace(".", ",")}). BYOK ou gerenciado. Não é fatura — é referência.
</div>
```
Adiciona nova linha `análises deste mês: <span>X/Y</span>` (fonte: `store.aiQuota()`, campos `monthUsed`/`monthLimit`, já carregados por esta tela — ver `App.jsx` uso de `store.aiQuota()` no restante do componente).

---

### Testing pattern (backend) — `server/tests/test_fase5_gate_mensal.py`

**Analog:** `server/tests/test_fase5_gate_mensal.py:188-207` (`test_ai_quota_conta_logada_devolve_month_used_inteiro`, `test_ai_quota_escopo_anonimo_devolve_month_used_none`)
```python
def test_ai_quota_conta_logada_devolve_month_used_inteiro(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "quota@teste.com")
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=3)

    r = c.get("/api/ai/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monthUsed"] == 3
    assert body["monthLimit"] == 30  # ATUALIZADO (Fase 12, v1.3): ADR-010 ativou o limite mensal do FREE


def test_ai_quota_escopo_anonimo_devolve_month_used_none(monkeypatch):
    c, main = _client(monkeypatch)
    r = c.get("/api/ai/quota")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monthUsed"] is None
    assert body["monthLimit"] is None
```
**Apply to:** teste novo do endpoint `GET /api/watchlist/quota` em `server/tests/` (arquivo sugerido: `test_fase13_watchlist_quota.py`, seguindo convenção `test_<feature>.py`). Usa os MESMOS helpers `_client`/`_registra`/`_auth` já definidos em `test_fase5_gate_mensal.py` (ou o equivalente local do arquivo novo) — casos mínimos: (a) conta logada com N itens na watchlist devolve `count=N`/`limit=10`; (b) escopo anônimo cai no `PLAN_FREE` também (watchlist não tem early-return especial para anônimo, diferente de `ai_quota`); (c) conta com `plan="pro"` devolve `limit=None`. Ver também `server/tests/test_fase12_cap_watchlist.py` para o padrão de teste de gate de escrita (`can_add_ticker`/`can_grow_watchlist_to`) já usado nesta mesma família de endpoints — reaproveitar fixtures/helpers de lá se existirem.

### Testing pattern (frontend) — inspeção estática de fonte, não execução real

**Analog:** `web/tests/test_fase5_gate_mensal_front.mjs` (guardião do gate de análises no front) e `web/tests/test_device_budget_sync.mjs` (guardião de sync device→servidor)

Achado importante de pesquisa: TODA a suíte `web/tests/*.mjs` roda como script Node puro (`scripts/executar.sh --testes`), SEM Vitest/Jest e SEM importar `App.jsx`/`persistence.js` como módulo executável (esses arquivos não rodam fora do build Vite). O padrão estabelecido é **inspeção estática de código-fonte**: `readFileSync` + regex/parsing de chaves balanceadas sobre o texto do arquivo, não invocação real das funções assíncronas com mocks de `fetch`.
```javascript
// web/tests/test_fase5_gate_mensal_front.mjs:19-30 (setup) + :62-70 (asserção de paridade)
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", p), "utf8");
const srcApp = read("src/App.jsx");
const srcPersistence = read("src/persistence.js");
const srcPlan = read("src/plan.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// paridade: MESMO nome de método definido nos dois stores
const defsAnalisesNoMes = (srcPersistence.match(/analisesNoMes\s*:\s*async\s*\(|async\s+analisesNoMes\s*\(/g) || []).length;
ok(`analisesNoMes tem exatamente 2 definições em persistence.js (uma por store, achado ${defsAnalisesNoMes})`,
   defsAnalisesNoMes === 2);
```
```javascript
// web/tests/test_device_budget_sync.mjs:44-57 — helper para extrair o corpo de um método por chaves balanceadas
function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}
const putConfigBody = bodyOf(src, "async putConfig(patch)");
```
**Apply to:** teste novo do gate fail-closed no `deviceStore` (arquivo sugerido: `test_fase13_watchlist_quota_ios.mjs` ou similar, convenção `test_<feature>.mjs`). Como o padrão da casa NÃO executa o `fetch` real, as asserções devem provar por INSPEÇÃO DE FONTE que:
- (a) `addWatchlistTicker`/`putWatchlist` no `deviceStore` chamam `api.watchlistQuota()` (ou equivalente) ANTES de qualquer `write()`/mutação de `doc.watchlist` — usar `bodyOf()` + comparação de índice, igual ao teste `initialBudget` (`putConfigBody.indexOf(...) < putConfigBody.indexOf(...)`);
- (b) o `catch` do `try` em volta dessa chamada lança erro (fail-closed) em vez de prosseguir com a escrita — provar que NÃO existe um padrão `catch { /* silencioso */ }` equivalente ao de `analisesNoMes`/`A.analyze` nesse trecho específico;
- (c) `watchlistQuota` está definido em AMBOS os stores (mesma asserção de paridade do exemplo acima, trocando o nome do método) — reaproveita a checagem que `test_fase3_paridade_stores_generica.mjs` já faz de forma genérica (todo método precisa aparecer nos dois `return {}`), então este teste pode ser mais estreito/focado só no comportamento fail-closed, deixando a paridade de NOMES para o guardião genérico existente.
- (d) `web/src/plan.js` — `canAddTicker` não contém mais a frase `"Faça upgrade para adicionar mais."` (mesmo padrão do assert (c) de `test_fase5_gate_mensal_front.mjs`, que verifica ausência de um comentário morto por `!srcApp.includes(...)`).

---

## Shared Patterns

### Padrão "X/Y" com 5 estados (normal/quase-limite/no-limite/sem-limite/indisponível)
**Source:** composição de `web/src/App.jsx:5712-5723` (fragmento + cor condicional) + `web/src/App.jsx:5566-5570` (fallback `"—"`)
**Apply to:** os 3 pontos de exibição em `App.jsx` (subtítulo Watchlist, CatalogModal, AtividadeIAScreen)
```javascript
// esqueleto reaproveitável (pseudocódigo, adaptar por local conforme 13-UI-SPEC.md)
const frag = (count, limit) => {
  if (limit == null) return null; // D-03: omite segmento inteiro, sem "ilimitado"
  if (count == null) return "—";  // indisponível/erro — nunca estimado
  const cor = count >= limit ? T.warn : (count / limit >= 0.9 ? T.warn : "inherit");
  return <span style={{ fontFamily: MONO, fontWeight: 700, color: cor }}>{count}/{limit}</span>;
};
```

### Leitura ao vivo server-authoritative, sem cache local (D-05)
**Source:** `web/src/persistence.js:284` (`serverStore.aiQuota`) e `:1140-1152` (`deviceStore.aiQuota`/`analisesNoMes`)
**Apply to:** `watchlistQuota()` nos dois stores — chamada de rede a cada leitura, sem persistir em `doc`/estado local.

### Fail-closed vs. fail-open — decisão por local de autoridade (D-04)
**Source:** `web/src/App.jsx:7257-7272` (`A.analyze`, fail-open — servidor é autoritativo) CONTRASTADO com o gate novo em `deviceStore.addWatchlistTicker`/`putWatchlist` (fail-closed — cliente é a única defesa)
**Apply to:** só o gate de watchlist no `deviceStore` usa fail-closed; não generalizar esse padrão para outros pré-checks do app onde o servidor já é a autoridade (ex.: não mudar `A.analyze`).

### Fonte única do número (`plan.py`), nunca hardcode
**Source:** `server/app/plan.py:31-42` (`PLAN_FREE`)
**Apply to:** endpoint novo (`main.py`), `deviceStore`/`serverStore` (leem do endpoint, não hardcodam `10`/`30`), `web/src/plan.js` (se atualizado, deve refletir os mesmos números, mas isso é fallback client-side, não fonte de verdade — a fonte de verdade do enforcement real é sempre o backend/endpoint).

### Paridade obrigatória entre stores
**Source:** `CLAUDE.md` (guardrail "Paridade obrigatória") + guardião `web/tests/test_fase3_paridade_stores_generica.mjs` (citado em `13-UI-SPEC.md`)
**Apply to:** qualquer método novo (`watchlistQuota`) precisa existir com o MESMO nome em `serverStore` E `deviceStore` — o teste de paridade compara os conjuntos de nomes dos dois `return {}`.

## No Analog Found

Nenhum arquivo desta fase ficou sem analog — é uma fase cirúrgica que estende endpoints/métodos/textos já existentes, todos com padrão-irmão direto no próprio repositório.

## Metadata

**Analog search scope:** `server/app/main.py`, `server/app/plan.py`, `web/src/persistence.js`, `web/src/api.js`, `web/src/plan.js`, `web/src/App.jsx`, `server/tests/test_fase5_gate_mensal.py`, `server/tests/test_fase12_cap_watchlist.py`
**Files scanned:** 8
**Pattern extraction date:** 2026-08-29
