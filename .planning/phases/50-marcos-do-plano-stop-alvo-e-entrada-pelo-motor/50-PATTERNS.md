# Fase 50: Marcos do plano (stop, alvo e entrada pelo motor) - Mapa de padrões

**Mapeado:** 2026-10-21
**Arquivos analisados:** 17 (9 a modificar, 3 novos prováveis, 5 de teste/paridade)
**Analogs encontrados:** 14 / 17

Escopo: CONTEXT.md (D-01..D-16). Não há RESEARCH.md. Trechos com linha foram lidos diretamente; onde a linha é só apontada pelo CONTEXT e não foi lida nesta passada, está marcado como **não lido**.

---

## Divergências entre CONTEXT.md e o código (ler antes de planejar)

1. **Rota de posição:** o CONTEXT cita `PUT /api/position`. A rota real é `PUT /api/position/{ticker}` (`server/app/main.py:3010`), que já chama `_disparar_ciclo_imediato(scope)` ao final.
2. **`pending_orders.py:196` não é o caminho de compra.** A linha 196 está dentro de `_restaurar_posicao` (l.184-199), que RECRIA posição ao cancelar uma venda pendente. O caminho de compra de ordem pendente (`executar_pendentes`, l.221) não foi lido; o planner deve localizar onde ele grava a posição nova antes de cravar D-09.
3. **Arredondamento de lote conflita com D-07.** `store.buy` faz `max(100, round(qty/100)*100)` (l.841, arredonda para o mais próximo, mínimo 100). `agent._avaliar_entradas` faz `int(orcamento // price // 100) * 100` (agent.py l.776, arredonda para BAIXO). D-07 pede "arredonda para baixo" e "não compra se não couber 1 lote". Ou seja: `store.buy` arredonda para cima quando a qty bruta é, por exemplo, 150 (vira 200). Já existe um fix (F10-20260819) que normaliza no `main.py:2846` antes de checar caixa; o sizing novo precisa ser a fonte única e o `store.buy` não pode mais "corrigir" a qty.
4. **Entrada automática não carrega marcos.** `agent.py:788` chama `store.buy(..., meta={"setup": r.get("setup")}, origem="automatico")`: só o nome do setup, sem gatilho/invalidação. O preço usado é `fechamento15m` (l.764), não o gatilho (D-06 exige distinguir os dois).
5. **Compra em posição existente.** `store.buy` (l.855-858) recalcula o preço médio e NÃO toca em stop/alvo. Com D-08/D-09, o planner precisa decidir o que acontece com os marcos ao somar lote (recalcular a partir do novo preço médio ou manter os do plano original).
6. **ADR-015 / série medida.** D-01 (folga de ATR) e D-02 (alvo em resistência) mudam a taxa stop/alvo do `signal_ledger`. O CONTEXT pede nota de quebra de série; nenhum analog de "nota de quebra" foi localizado.

---

## File Classification

| Arquivo (novo ou modificado) | Papel | Fluxo de dados | Analog mais próximo | Qualidade |
|---|---|---|---|---|
| `server/app/setups.py` (função pura de marcos, ou `server/app/marcos.py` novo) | service (puro) | transform | `setups.plano_operacional` l.639-718 + `_alvo_rr` l.209 | exact |
| `server/app/store.py` (`set_position` l.602, `buy` l.840) | service (CRUD) | CRUD | próprio `store.buy`/`set_position`; rejeição: `store.registrar_rejeicao` | exact |
| `server/app/main.py` (`PUT /api/position/{ticker}` l.3010; `POST /api/buy` l.2838-2862) | controller | request-response | `/api/buy` (rejeição com `HTTPException(400)`) | exact |
| `server/app/agent.py` (`_avaliar_entradas` l.702-790; laço de saída l.1030-1090; `nivel_trailing` l.428; `avaliar_alvo_dinamico` l.489) | service (ciclo) | event-driven / batch | próprio laço; aviso: `_avisar_lastro_travado` l.961 | exact |
| `server/app/pending_orders.py` (compra executada, l.221+) | service | CRUD | `store.buy` | role-match |
| `server/app/technical_models.py` (`riskPlanReference` l.254-267, `piv` l.333-337) | utility (puro) | transform | **não lido** | - |
| `server/app/skill_ref.py` (`RR_MIN`=1.5 l.32) | config | - | fonte única já existente | exact |
| `server/app/cartao_posicao.py` (`leitura_plano` l.221-262) | service (puro) | transform | próprio (rótulo do R:R) | exact |
| `server/app/opcoes_lastreadas.py` (`propor` l.195-275), `server/app/put_bridge.py` (`COLCHAO_PCT` l.40,70) | service | transform | **não lido** | - |
| `server/app/llm.py` (FORMAT N2 l.236-266, `parse_carteira` l.1071, `analyze_carteira` l.1170), `server/app/kpi.py` (`parse_rich` l.265-310) | service (IA) | request-response | próprio (parser atual) | exact |
| `server/app/defaults.py` ↔ `web/src/catalog.js` (`carteiraStopAlvo`, `carteiraStopAlvoOperador`, l.165-225) | config (prompt) | - | par existente, paridade byte a byte | exact |
| `web/src/finance.js` (`sizingPlano` l.415; `setupOperavel`/`metaDeEntrada` l.517-547) | utility (puro) | transform | `sizingPlano` | exact |
| `web/src/persistence.js` (`deviceStore.putPosition` l.1952) | store (cliente) | CRUD | `serverStore`/`deviceStore` par | exact |
| `web/src/App.jsx` (`localProposal` l.396, `rrPos` l.4142, `StopAlvoModal` l.4173, `applyProposal` l.10335, `applyStopAlvoFor` l.10430) | component | request-response | próprio | exact |
| Testes novos (ex.: `server/tests/test_marcos_plano.py`, `web/tests/test_marcos_geometria.mjs`) | test | - | ver seção Testes | role-match |

Total com analog exato ou de papel: 14. Sem analog: geometria de posição em `set_position` (ver "No Analog Found").

---

## Pattern Assignments

### A. Função pura de marcos (D-01..D-04) — `server/app/setups.py`

**Analog:** `setups.plano_operacional` (`server/app/setups.py:639-718`) e `_alvo_rr` (l.209-216).

**Imports / constantes** (l.623-624):
```python
RR_MINIMO = skill_ref.RR_MIN  # fonte única em skill_ref (ADR15-05)
ZONA_PERSEGUICAO = 0.5        # até 0,5× o risco além do gatilho ainda dá entrada a mercado
```
Reusar `RR_MINIMO`; NÃO criar literal 1.5 novo (guardião `test_rr_min_fonte_unica.mjs`).

**Assinatura e forma de retorno** (l.632-640): toda decisão retorna um dict com `decisao`, campos numéricos arredondados por `_rr2` e `motivo` em PT-BR:
```python
def _plano_vazio(motivo):
    return {"decisao": DECISAO_NAO_OPERAR, "motivo": motivo, "setup": None,
            "lado": None, "tipo": None, "entrada": None, "stop": None,
            "alvo1": None, "alvo2": None, "rr1": None, "rr2": None,
            "riscoPorAcao": None}

def plano_operacional(setup, close=None):
```
Padrão a copiar: a função nova deve devolver `{"valido": bool, "motivo": str, "entrada", "stop", "alvo", "rr", ...}` com `null` (nunca `0.0`) nos campos não calculados.

**Guard clauses e recusa com motivo** (l.646-656):
```python
gatilho = setup.get("gatilho")
stop = setup.get("invalidacao")
if gatilho is None or stop is None or gatilho == stop:
    return _plano_vazio("Setup sem gatilho/invalidação numéricos — sem plano executável, não operar.")
alta = lado == "alta"
risco = abs(gatilho - stop)
if (alta and stop >= gatilho) or ((not alta) and stop <= gatilho):
    return _plano_vazio("Gatilho e invalidação incoerentes para o lado do setup — não operar.")
```

**Zona de perseguição (D-03)** (l.660-673): copiar literalmente a lógica, que já é a regra do D-03:
```python
if close is not None:
    rompido = close >= gatilho if alta else close <= gatilho
    if rompido:
        excedente = abs(close - gatilho)
        if excedente > ZONA_PERSEGUICAO * risco:
            return {**_plano_vazio(""), "setup": setup.get("nome"), "lado": lado,
                    "motivo": "Gatilho já rompido e preço esticado (>0,5R além) — não persiga; espere novo setup ou reteste."}
        entrada = float(close)
```

**Recusa por R:R mínimo (D-02, D-06)** (l.686-692):
```python
rr2 = abs(alvo2 - entrada) / risco_real
if rr2 < RR_MINIMO:
    return {**_plano_vazio(""), "setup": setup.get("nome"), "lado": lado,
            "motivo": "R:R de %.1f:1 abaixo do mínimo de %.1f:1 — não há operação com vantagem estatística clara neste momento." % (rr2, RR_MINIMO)}
```
Alvo no lado do lucro (l.678-683): `alvo_lado_certo = (alvo2 > entrada) if alta else (alvo2 < entrada)`. Esta é a checagem que a nova função deve generalizar (D-11) e que o caso PM 23,01 / alvo 21,58 teria reprovado.

**Alvo projetado (fallback D-02 "entrada + 2R")** (l.209-216 e l.674-676):
```python
def _alvo_rr(gatilho, invalidacao, atr=None, alta=True):
    if gatilho is not None and invalidacao is not None and gatilho != invalidacao:
        risco = abs(gatilho - invalidacao)
        return _rr2(gatilho + 2 * risco if alta else gatilho - 2 * risco)
    if gatilho is not None and atr:
        return _rr2(gatilho + 2 * atr if alta else gatilho - 2 * atr)
    return None
```
Nota: `_alvo_rr` já tem fallback por ATR; a regra D-02 ("resistência relevante, senão entrada+2R") é nova. O `alvo2 = gatilho + 2*risco` de `plano_operacional` l.675 é a mesma ideia com a régua antiga, a ser substituída.

**Stop com folga de ATR (D-01):** NÃO existe no motor hoje. O stop vem direto de `setup["invalidacao"]` (l.647). A folga `invalidação − 0,1×ATR(14)` e o ajuste para `entrada − 1×ATR` são novos. ATR já é calculado em `agent.py` (`ctxs[...]["atr"]`, l.1030-1035) — ver padrão em "Gestão".

**Resistência relevante (D-02):** **não lido** — `technical_models.py` l.333-337 (`piv`) é a fonte. O planner decide o critério (CONTEXT Discretion).

---

### B. Validação de geometria na gravação (D-11, D-12) — `store.set_position` + `PUT /api/position/{ticker}`

**Analog de rejeição:** `server/app/main.py:2838-2862` (compra) — checa, registra rejeição no Diário e só então levanta `HTTPException`:
```python
if qty * price > cash_disp:
    if scope is not None:
        store.registrar_rejeicao(
            _conn, "COMPRA", t, qty, price,
            f"Caixa insuficiente para {qty} {t} a R$ {price} — disponível: R$ {cash_disp}.",
            user_id=scope, origem="manual")
    raise HTTPException(400, "Caixa insuficiente.")
```
Ponto de extensão: a validação de geometria de posição deve seguir o MESMO molde (motivo PT-BR, `HTTPException(400, ...)`), mas o `set_position` hoje não valida nada (`store.py:602-620` só faz `float(stop)`).

**Estado atual de `set_position`** (`server/app/store.py:602-619`):
```python
def set_position(conn, t: str, stop=None, alvo=None, has_stop=False, has_alvo=False,
                  alvo_extensoes=None, user_id=None) -> None:
    positions = get(conn, "positions", user_id=user_id)
    for p in positions:
        if p["t"] == t:
            if has_stop:
                p["stop"] = None if stop in (None, "") else float(stop)
            if has_alvo:
                p["alvo"] = None if alvo in (None, "") else float(alvo)
    db.kv_set(conn, "positions", positions, user_id=user_id)
```
Padrão de recusa de domínio em `store.py` (já existe, copiar): `raise ValueError(MOTIVO_...)` (l.943, l.998, l.1143, l.1159). Ex.: `raise ValueError(MOTIVO_DESCOBERTO_DESLIGADO)`.

**Rota atual, sem tratamento** (`server/app/main.py:3010-3016`):
```python
@app.put("/api/position/{ticker}")
async def position(ticker: str, body: dict = Body(default={}), scope: Optional[str] = Depends(current_scope)):
    store.set_position(_conn, ticker.upper(), stop=body.get("stop"), alvo=body.get("alvo"), has_stop=("stop" in body), has_alvo=("alvo" in body), user_id=scope)
    _disparar_ciclo_imediato(scope)
    return store.public_state(_conn, user_id=scope)
```
Para D-11: capturar `ValueError` do `set_position` na rota e converter em `HTTPException(400, msg)`. Hoje a rota não tem try/except — erro de validação vira 500.

**Espelho no cliente (paridade, D-11 "inclusive no deviceStore")** — `web/src/persistence.js:1952-1966`:
```js
async putPosition(t, b) {
  ensure();
  if (sync.hasSession()) {
    const r = await api.putPosition(t, b);
    _adotarCarteiraDoServidor(r);
    write();
    return pub();
  }
  const pos = doc.positions.find((p) => p.t === t);
  if (pos) {
    if ("stop" in b) pos.stop = b.stop === "" || b.stop == null ? null : Number(b.stop);
    if ("alvo" in b) pos.alvo = b.alvo === "" || b.alvo == null ? null : Number(b.alvo);
  }
  write();
  return pub();
}
```
Hoje o ramo local grava SEM validação. A validação D-11 entra aqui antes de `write()` (e o ramo com sessão depende do 400 do servidor). Paridade: a mesma função pura de geometria deve ser espelhada em `web/src/finance.js` (padrão "função pura exportada", ex. `sizingPlano`).

---

### C. Compra com marcos e sizing (D-06, D-07, D-08, D-09)

**Analog de sizing (front, fonte a espelhar):** `web/src/finance.js:415-431`:
```js
export function sizingPlano(plano, capital, pctPorTrade) {
  const p = plano || {};
  if (p.decisao !== "COMPRAR" && p.decisao !== "VENDER") return null;
  const risco = typeof p.riscoPorAcao === "number" ? p.riscoPorAcao : null;
  const entrada = typeof p.entrada === "number" ? p.entrada : null;
  const cap = typeof capital === "number" && capital > 0 ? capital : null;
  const pct = typeof pctPorTrade === "number" && pctPorTrade > 0 ? Math.min(5, pctPorTrade) : 1.0;
  if (!risco || risco <= 0 || !entrada || !cap) return null;
  const riscoFinanceiro = +(cap * (pct / 100)).toFixed(2);
  const qtd = Math.floor(riscoFinanceiro / risco / 100) * 100;
  if (qtd < 100) {
    return { qtd: 0, valorAprox: 0, riscoFinanceiro, pct, aviso: "Capital insuficiente para 1 lote de 100 com risco de " + pct + "% — aumente o capital operacional ou o % de risco." };
  }
  return { qtd, valorAprox: +(qtd * entrada).toFixed(2), riscoFinanceiro, pct, aviso: null };
}
```
Mapeamento para D-07: `riscoPorAcao` passa a ser `entrada − stop` do motor; `pct` = risco por operação com teto 5 (já existe); lote de 100 floor (já existe); `aviso` vira o texto do "não cabe 1 lote". FALTA no `sizingPlano` o teto por `allocPct` do caixa (D-07 "limitado pelo allocPct") — o planner adiciona `qtd = min(qtd_risco, floor(caixa*allocPct/entrada/100)*100)`.

**Analog de sizing (backend, a ser substituído):** `server/app/agent.py:774-786`:
```python
cash = store.get(conn, "cash", user_id=scope) or 0.0
orcamento = cash * (par["allocPct"] / 100.0)
qty = int(orcamento // price // 100) * 100
if qty < 100:
    events.append({"time": _now_str(), "kind": "warn",
                   "text": f"Entrada automática: orçamento de {par['allocPct']:.0f}% do caixa "
                           f"(R$ {orcamento:.2f}) não cobre 1 lote de {ticker} a R$ {price:.2f} — "
                           f"sem execução, aviso mantido."})
    continue
```
Hoje o sizing usa só `allocPct` (não risco). D-07 troca a conta por `min(risco, allocPct)`; o aviso "não cobre 1 lote" já existe e é o padrão a manter.

**Gravação de marcos na compra (D-08):** `server/app/store.py:840-870`. Hoje:
```python
def buy(conn, t: str, qty: int, price: float, user_id=None, meta=None, origem: str = "manual") -> None:
    qty = max(100, round(qty / 100) * 100)
    ...
    m = _sanitize_trade_meta(meta)
    ...
    pos = {"t": t, "qty": qty, "avg": round(price, 2), "stop": None, "alvo": None,
           "abertaEm": now_str()}
```
Ponto de extensão: `stop`/`alvo` deixam de ser `None` quando o motor fornece marcos. `_sanitize_trade_meta` (l.821-837) já é o canal de metadados de entrada; ele só aceita `("setup", "lado", "veredito", "snapshotId")` e `("gatilho", "invalidacao", "confluencia")`. Os marcos novos (`stop`, `alvo`, `entrada` do motor) precisam entrar nesta whitelist OU ser passados como argumentos explícitos de `buy` (decisão do planner). Recomendação: argumentos explícitos para os marcos validados, `meta` só para telemetria.

**Arredondamento:** `store.buy` l.841 (`qty = max(100, round(qty / 100) * 100)`) conflita com D-07 (floor). Ver divergência 3.

**Aviso de caixa existente:** `main.py:2846-2860` (ver seção B) — o planner deve reusar `store.registrar_rejeicao` para "não compra: R:R < 1,5" (D-06) em vez de criar novo canal.

**Compra manual sem plano (D-09):** o card precisa pedir para definir marcos. Analog de UI: `StopAlvoModal` (`web/src/App.jsx:4173`) já aplica via `A.applyStopAlvoFor(t, stop, alvo)` (l.4202).

---

### D. Gestão: breakeven + trailing + alvo dinâmico (D-14, D-15)

**Analog de trailing ATR:** `server/app/agent.py:428-454` (`nivel_trailing`, PURO). Padrão de retorno `(nivel|None, descricao)` e descrição para o Diário:
```python
def nivel_trailing(mode: str, price: float, par: dict, ctx: dict = None):
    ctx = ctx or {}
    pct = par.get("trailingPct") or 5.0
    ...
    if mode == "atr":
        atr = ctx.get("atr")
        if not atr or atr <= 0:
            return _percentual(" (sem ATR disponível — critério técnico indisponível)")
        k = par.get("trailingAtrMult") or ATR_MULT_DEFAULT
        return round(price - k * atr, 2), f"{k:.1f}× o ATR(14) de R$ {atr:.2f} abaixo do preço"
```
D-14 pede trailing de **2×ATR** (default de `ATR_MULT_DEFAULT`, verificar valor) e breakeven "a 1R". Breakeven NÃO existe: adicionar como regra nova ao lado de `nivel_trailing`, mantendo o mesmo retorno `(nivel, descricao)`.

**Monotonicidade (regra que o D-14 reafirma):** `agent.py:1041-1050`:
```python
if par["rules"]["trailing"] and pos.get("stop") is not None:
    novo, criterio = nivel_trailing(par["trailingMode"], price, par, ctxs.get(pos["t"]))
    if novo is not None and novo > pos["stop"]:
        store.set_position(conn, pos["t"], stop=novo, alvo=None, has_stop=True, has_alvo=False, user_id=scope)
        events.append({"time": _now_str(), "kind": "info",
                       "text": f"Trailing: stop de {pos['t']} ajustado para R$ {novo:.2f} ({criterio})."})
        pos = {**pos, "stop": novo}
```
Ponto de extensão: breakeven e trailing passam por ESTE mesmo `if novo > pos["stop"]` (só sobe). Ligado por padrão para posição com plano (D-14), desligável: nova flag em `par` no padrão de `par["rules"]["trailing"]`.

**Alvo dinâmico (D-15, opt-in):** `agent.py:489-520` `avaliar_alvo_dinamico(price, pos, ctx)` é PURA e devolve `(None, None)` quando não estende; o chamador (l.1052-1065) grava com `set_position(..., alvo_extensoes=usadas)`. Regra atual já cumpre D-15 (`ALVO_ATR_MULT=1.5`, `MAX_ALVO_EXTENSOES=2`, `RR_MINIMO`), basta medir com o stop já em breakeven/trailing. Nota no código l.466-470: "Nenhuma das duas muda o stop" — manter.

**R:R a partir do preço (D-05):** `agent._rr(avg, stop, alvo)` (l.474-484) — a fórmula canônica a reusar: `(alvo - avg) / (avg - stop)`. Front: `rrPos` (`web/src/App.jsx:4142`):
```js
const rrPos = pos && pos.stop != null && pos.alvo != null && cur != null && cur > pos.stop ? (pos.alvo - cur) / (cur - pos.stop) : null;
```
Este é o R:R "a partir do preço atual" (acompanhamento). D-05 pede rótulo distinto do R:R de decisão (a partir da entrada). Análogo no backend: `cartao_posicao.leitura_plano` (l.221-262, **lido só pelo CONTEXT**).

---

### E. Aviso deduplicado do Diário (D-13) — posição com marco inválido

**Analog direto:** `server/app/agent.py:961-980` `_avisar_lastro_travado`:
```python
def _avisar_lastro_travado(conn, scope, ticker: str, texto: str) -> list:
    """Aviso de Diário (kind "warn", SEM `tag`: o push só olha "buy") de posição
    100% travada como lastro com stop/alvo atingido — 1x por (ticker, dia BRT),
    kv `avisoLastroTravado` no mesmo formato de `avisoForaPregao`. ..."""
    hoje = _today()
    chave = "lastro:" + ticker
    try:
        estado = db.kv_get(conn, "avisoLastroTravado", None, user_id=scope)
    except Exception:  # noqa: BLE001
        estado = None
    chaves = list(estado.get("chaves") or []) if isinstance(estado, dict) and estado.get("data") == hoje else []
    if chave in chaves:
        return []
    chaves.append(chave)
    try:
        db.kv_set(conn, "avisoLastroTravado", {"data": hoje, "chaves": chaves}, user_id=scope)
    except Exception:  # noqa: BLE001
        pass
    return [{"time": _now_str(), "kind": "warn", "t": ticker, "text": texto}]
```
Uso (l.1082-1088): o laço faz `events.extend(_avisar_lastro_travado(...))` e `continue` — sem rejeição, sem consumir `maxOpsDia`.
Para D-13: copiar o molde com kv nova (ex. `avisoPlanoInvalido`) e chave `"invalido:"+ticker`. Trocar o `kind`/`text` (texto: "plano inválido — redefina", com marcos do motor como sugestão). Ponto de inserção: ANTES de `breach_stop/hit_alvo` (l.1063) — se geometria inválida, `continue` e não vende. Vale também para o caminho sem conta do iPhone (`persistence.js` ciclo local) — **não lido**.

**Invariante a preservar:** `pos` com marco inválido NÃO pode disparar `store.sell`. O gate é o `continue` antes de `_gatilho_saida`.

---

### F. Parecer de IA só explica (D-10)

**Analog de parser:** `server/app/kpi.py:265-310` `parse_rich` (validação stop×alvo sem preço) e `server/app/llm.py:1071` `parse_carteira`. Não lidos nesta passada além da referência do CONTEXT. Padrão a copiar do guardião existente: `test_m3_format_pede_null_nunca_zero` (nulos como `null`).

**Prompts (paridade byte a byte):** `server/tests/test_auditoria_prompts.py` itera as chaves `("carteiraStopAlvo", "carteiraStopAlvoOperador")` (l.171, l.237, l.265) e usa `monkeypatch.setitem(defaults.LEGACY_PROMPT_SHA256, "carteiraStopAlvo", ...)` (l.322) para testar prompts legados. Padrão para os testes novos: estender estas mesmas listas de chave e atualizar o hash legado com nota (guardião, não apagar).
**Não confirmado:** o teste que compara `defaults.py` com `catalog.js` byte a byte não foi localizado com certeza. `grep -ln catalog` achou `test_auditoria_prompts.py`, `test_catalogo_planos.py`, `test_telas_paridade.py`. O planner deve verificar qual deles faz a comparação de arquivo antes de mexer nos prompts.

**Mudança de semântica:** `applyStopAlvoFor` (`web/src/App.jsx:10430`) e `applyProposal` (l.10335) hoje aplicam os números da IA. Pelo D-10 passam a aplicar os marcos do motor. Ler só com offset (App.jsx é grande).

---

### G. Opções ancoradas nos marcos (D-16)

**Não lido.** Arquivos: `server/app/opcoes_lastreadas.py:195-275` (`propor`), `server/app/put_bridge.py:40,70` (`COLCHAO_PCT`), `server/app/opcoes_motor.py` (`rastrear`), `server/app/opcoes_gatilho.py`. Referência de regra "sem marcos cai no spot e DIZ que caiu": padrão de `nivel_trailing` (ver D): `_percentual(" (sem ATR disponível — critério técnico indisponível)")`. Esse padrão de "cair no fallback e nomear o fallback no texto" é o que D-16 pede.

---

### H. Testes (padrões a copiar)

**Servidor (pytest):** convenção `server/tests/test_<feature>.py`, `def test_<descricao>():` (CLAUDE.md). Testes a estender (com nota): `test_plano_operacional.py`, `test_agent.py`, `test_entrada_automatica.py`, `test_cartao_posicao.py`, `test_kpi.py`, `test_pipeline_n2_n3.py`. Novo: caso de regressão obrigatório PM 23,01 / cotação 23,51 / stop 23,36 / alvo 21,58 → `PUT` recusado (400).

**Front (node, sem framework):** `web/tests/test_api_parity.mjs` — padrão `ok(name)` + `assert` + bloco `await (async () => {...})()`:
```js
import assert from "node:assert";
import { api, setNativeMode, setApiBase, getApiBase, testServer } from "../src/api.js";
let passed = 0;
const ok = (name) => { console.log("ok", name); passed++; };
await (async () => {
  setNativeMode(true);
  ...
  ok("nativo sem base usa a produção embutida (app funciona de fábrica)");
})();
```
Guardiões a atualizar com nota: `web/tests/test_rr_min_fonte_unica.mjs` (fonte única de RR_MIN, não lido), `test_posicao_stop_alvo.mjs` e `test_finance.mjs` (`sizingPlano`, não lidos), `test_trailing_dinamico_ui.mjs`, `test_alvo_dinamico_ui.mjs`, `test_plano_ui.mjs`.

Comando: `node web/tests/<arquivo>.mjs`. Canônica do repo: `bash scripts/executar.sh --testes` (uma vez por onda, pelo orquestrador).

---

## Shared Patterns

### Rejeição com motivo PT-BR (aplicar a D-06, D-07, D-11, D-13)
**Fonte:** `server/app/main.py:2854-2860` + `server/app/store.py` (`ValueError` de domínio, l.943, 998, 1143).
**Aplicar a:** `set_position`/`PUT /api/position/{ticker}`, compra automática, compra manual.
```python
# store: recusa de domínio
raise ValueError("Geometria inválida: ...")
# rota: converter em 400 com motivo
except ValueError as e:
    raise HTTPException(400, str(e))
```
Recusa de compra gera rejeição no histórico via `store.registrar_rejeicao(conn, "COMPRA", t, qty, price, motivo, user_id=scope, origem=...)` (só com `scope is not None`).

### Aviso de Diário deduplicado por dia (D-13)
**Fonte:** `server/app/agent.py:961-980` (`_avisar_lastro_travado`) e `avisoForaPregao` (agent.py ~l.950).
**Aplicar a:** plano inválido, stop largo demais (D-01), R:R < 1,5 na compra (D-06), não cabe 1 lote (D-07).

### Função pura + espelho front com paridade
**Fonte:** `setups.plano_operacional` (server) ↔ `finance.js:sizingPlano` (front), `_rr` (agent.py l.474) ↔ `rrPos` (App.jsx l.4142).
**Aplicar a:** função de marcos (D-04), geometria (D-11). Espelho no front só se necessário; se espelhado, testar com `web/tests/*.mjs`.

### Nulo é `null`, nunca `0`
**Fonte:** `nivel_trailing` (`_percentual` devolve `None` quando ausente), `_rr2` (setups.py l.205-206: `round(float(x),2) if isinstance(x,(int,float)) else None`), guardião `test_m3_format_pede_null_nunca_zero`.

### Campos de posição e whitelist de metadados
**Fonte:** `store.buy` (l.856-858: `stop: None, alvo: None`), `_sanitize_trade_meta` (store.py l.821-837).
**Aplicar a:** qualquer campo novo de posição (marcos do motor, flag de breakeven) precisa entrar em `store.py` E em `deviceStore` (`persistence.js`) — regra de paridade do CLAUDE.md.

---

## No Analog Found

| Arquivo / função | Papel | Fluxo | Motivo |
|---|---|---|---|
| Validação de geometria em `set_position` | service | CRUD | Não existe validação de stop/alvo hoje; o padrão mais próximo é a checagem de coerência de `plano_operacional` (l.650-692), que é de setup, não de posição. |
| Breakeven a 1R (D-14) | service | event-driven | Nenhuma regra de breakeven no código; trailing (`nivel_trailing`) é o único ajuste de stop. |
| Resistência relevante como alvo (D-02) | utility | transform | `piv` existe em `technical_models.py` (l.333-337), mas não há função que escolha "primeira resistência acima da entrada com distância mínima". |
| Nota de quebra de série do `signal_ledger` (CONTEXT specifics) | - | - | Nenhum exemplo de nota de quebra de métrica localizado. |

---

## Metadata

**Escopo da busca:** `server/app/` (setups, store, agent, main, pending_orders, skill_ref), `web/src/` (finance.js, persistence.js, App.jsx por offset), `web/tests/`, `server/tests/`.
**Arquivos lidos integralmente ou por trecho nesta passada:** setups.py (l.35-70, 205-225, 623-725), agent.py (l.428-500, 702-790, 955-1090), store.py (l.600-620, 821-870), main.py (l.2838-2862, 3008-3016), pending_orders.py (l.184-215), persistence.js (l.1950-1966), finance.js (l.415-431), App.jsx (grep de nomes + l.4142, 4173-4202 via CONTEXT), test_api_parity.mjs (l.1-40).
**Não lidos (planner/executor devem ler com offset/limit):** technical_models.py, cartao_posicao.py, opcoes_lastreadas.py, put_bridge.py, llm.py, kpi.py, defaults.py, catalog.js, pending_orders.py (`executar_pendentes`), persistence.js (ciclo local sem conta), App.jsx (`localProposal`, `applyProposal`, `applyStopAlvoFor` — declarados como funções/arrow dentro do componente; grep por declaração exata não retornou, usar `grep -n "localProposal\|applyStopAlvoFor"`).
**Data de extração:** 2026-10-21
