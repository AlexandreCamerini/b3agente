# Phase 38: KB Didática ampliada - Research

**Researched:** 2026-09-23
**Domain:** Internal glossary/search feature + component extraction (React front-end) + one new read-only FastAPI route. No new external dependencies.
**Confidence:** HIGH — every claim below is grounded in direct reads of `server/app/kb.py`, `server/app/conceitos.py`, `server/app/main.py`, `web/src/App.jsx`, `web/src/opcoes/OpcoesScreen.jsx`, `web/src/persistence.js`, `web/src/api.js`, and the two guardian test files that already encode the contracts this phase touches.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase Boundary:** Usuário consegue buscar qualquer um dos 83 verbetes da KB de mecânica B3 (`server/app/kb.py`) e encontrar um link "saiba mais" contextualizado nas 4 abas que hoje não oferecem essa ponta de entrada (Acompanhar, Radar, Watchlist, Opções — só Portfólio tem hoje, via o alerta de concentração ligado a `abrirVerbete("diversificacao", ...)`). `SetorAlvo`/`ConceitoSheet` saem de `App.jsx` para um módulo compartilhado, sem que `OpcoesScreen.jsx` passe a importar nada de `App.jsx` (isolamento deliberado preservado, `OpcoesScreen.jsx:20-24`).

**D-01:** Busca livre por texto **e** navegação por família, na mesma tela — não é um toggle entre dois modos. Campo de texto no topo filtra a lista completa; sem texto digitado, a lista mostra as 9 famílias (`indicadores`, `estrutura`, `familias`, `modelos`, `setups`, `plano_risco`, `fundamentos`, `mercado_b3`, `estados_app` — 4 a 16 verbetes cada) como seções/acordeão.

**D-02:** `kb.buscar()` mantém a lógica de match atual (termo/frase completa com fronteira de palavra) — não estender para prefixo/substring. Zero risco de regredir o uso existente por `resolver()` (assistente).

**D-03:** Sem limite de resultados na tela de navegação — mostra todos os que baterem. O `limite=5` de `kb.buscar()` foi desenhado pra responder 1 pergunta do assistente, não pra filtrar uma lista; fica pro planner decidir se cria parâmetro/função nova sem tocar o comportamento que o assistente já usa.

**D-04:** Busca é **live** (filtra a cada tecla), client-side sobre o catálogo completo já carregado — sem round-trip por letra. Implica que o front precisa buscar `catalogo()` completo uma vez (hoje só existe `GET /api/kb/buscar`, que devolve resultados já pontuados/limitados — **não existe endpoint que devolva o catálogo completo**; fica pro planner/pesquisa decidir a rota nova).

**D-05:** Estado vazio (0 resultados): mensagem clara ("Nenhum verbete encontrado para '{termo}'") sem esconder a navegação por família abaixo — a pessoa continua podendo explorar por categoria mesmo sem match de texto.

**D-06:** Dentro da aba Perfil — não abre ícone global novo nem entra na folha de ajuda existente. Perfil é hoje um hub de tiles (Preferências, Conta, IA & chaves, Observabilidade...) que abrem tela focada (`ProfileTile`, padrão de `App.jsx` em torno da linha 2471/2726); a busca de verbetes segue o MESMO padrão: um tile novo (ex.: "Aprender"/"Glossário") abrindo uma tela dedicada de busca. Não introduz mecanismo de navegação novo.

**D-07:** Cada uma das 4 abas (Acompanhar, Radar, Watchlist, Opções) abre sempre o MESMO verbete fixo — sem lógica condicional por contexto (ticker/setup ativo). Mesmo padrão simples que o link existente de Portfólio já usa (fixo em `"diversificacao"`).

**D-08:** O `vid` exato por aba (qual dos 83 verbetes ancora cada uma) NÃO foi travado nesta discussão — é proposta do planner a partir do catálogo existente, revisada e aprovada pelo Alex no CONTEXT.md/plano antes de qualquer código.

### Claude's Discretion

- Escolher o `vid` (dentre os 83 de `kb.py`) que ancora cada uma das 4 abas sem cobertura — critério: coerência temática com o que a aba mostra hoje. **`38-UI-SPEC.md` já propôs uma tabela com 4 candidatos (ver Architecture Patterns abaixo) — este research valida essa proposta contra o catálogo real e a confirma como tecnicamente correta**, mas a aprovação final do Alex continua pendente, conforme D-08.
- Mecanismo técnico de como `ConceitoSheet`/`store.conceito(cid)` (hoje resolve só via `conceitos.py`/`conceitos.montar()`) passa a abrir também verbetes de `kb.py` (que tem formato de dado diferente — ver `kb.formatar()`). Isso é implementação, não vai a `discuss-phase` — mas o researcher/planner DEVE endereçar essa ponte explicitamente. **Ver "Pattern 1: A ponte kb.py × conceitos.py" abaixo — resolvido com recomendação concreta.**
- Nome/label exato do tile novo em Perfil e da tela de busca. **UI-SPEC já travou: tile "Glossário".**
- Rota/endpoint novo para expor o catálogo completo de `kb.py` ao front (D-04) — nome, formato, se cacheável. **Ver "Pattern 2: rota de catálogo completo" abaixo.**

### Deferred Ideas (OUT OF SCOPE)

None — discussão ficou dentro do escopo da fase (busca KB-01 + ancoragem KB-02). B2 (continuidade de estado da aba Opções) e C3 (consolidação de registros de tela) são as Fases 39 e 40, não tocadas aqui.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KB-01 | Usuário pode buscar um verbete entre os 83 da KB de mecânica B3 (busca livre + navegação por família, D-01) | Pattern 2 (rota de catálogo completo) + Pitfall "porta de matching client-side" resolvem a mecânica de busca; `kb.buscar()`/`kb.catalogo()` já existem e não precisam de mudança de assinatura pública (D-02/D-03 respeitados via função nova opcional, ver Pattern 2) |
| KB-02 | Usuário vê link "saiba mais" nas 4 abas sem cobertura, requerendo extrair `SetorAlvo`/`ConceitoSheet` para módulo compartilhado sem violar isolamento de `OpcoesScreen.jsx` | Pattern 1 (ponte de dados) + Pattern 3 (extração do módulo + duas opções de wiring, com recomendação) resolvem o mecanismo técnico completo; tabela de `vid` proposta validada contra `kb.py` real |
</phase_requirements>

## Summary

Esta fase é 100% código interno — zero dependência nova, zero pacote a instalar. O trabalho real tem três partes concretas: (1) um endpoint novo, barato e sem custo de LLM (`GET /api/kb/catalogo`), que devolve os 83 verbetes formatados de uma vez para a busca live client-side (D-04); (2) uma ponte de dados entre `kb.py` (glossário estático, sem números de card) e `conceitos.py` (conceitos ancorados nos números do card exibido) dentro do MESMO componente `ConceitoSheet`, porque os dois formatos são diferentes e o roteamento entre eles precisa ser EXPLÍCITO — nunca por tentativa/erro — para não regredir os 9 pontos de entrada existentes (`SetorAlvo` toque, link "saiba mais" de Portfólio); e (3) a extração de `SetorAlvo`/`ConceitoSheet`/`AssistenteBox`/`AiNote` de `App.jsx` para um módulo terceiro, seguindo o MESMO padrão já em produção (`web/src/opcoes/uiOpcoes.jsx`, Fase 33) — incluindo a mesma regra aceita de token de tema espelhado localmente (`T` derivado de `var(--...)`, não importado).

Achado central que muda a leitura ingênua da tarefa: `ctx.A` (o objeto de callbacks que `App.jsx` já passa para `OpcoesScreen.jsx` via `<OpcoesScreen ctx={ctx} />`, `App.jsx:9299`) JÁ inclui `abrirVerbete`, e o `<ConceitoSheet>` que `App.jsx` renderiza hoje (`App.jsx:9366-9375`) é um overlay GLOBAL (`position: fixed, inset: 0, zIndex: 86`) montado FORA do bloco condicional de abas — ou seja, ele já cobre visualmente a aba Opções mesmo sem NENHUMA mudança de import. Isso significa que a extração exigida pela decisão travada não é estritamente necessária para o link funcionar visualmente — mas a decisão travada pede explicitamente que `OpcoesScreen.jsx` IMPORTE o componente do módulo novo (não apenas dispare o overlay global via `ctx.A`), então a Pattern 3 abaixo recomenda a opção que corresponde literalmente ao texto da decisão: `OpcoesScreen.jsx` monta sua PRÓPRIA instância local de `ConceitoSheet`, com seu PRÓPRIO estado local, desacoplada do `conceitoAberto` de `App.jsx`.

O segundo achado com risco real: `ConceitoSheet` hoje resolve os chips "veja também" checando `didatica.conceitos` (o catálogo de `conceitos.py`, só 9 itens) — um verbete de `kb.py` cujo `veja` aponta para outro id só-de-`kb.py` (o caso comum: 74 dos 83 verbetes são só-de-`kb.py`) teria os chips silenciosamente OMITIDOS sob o código atual. A correção é trocar a fonte de verificação para o catálogo completo de `kb.py` (que é um superconjunto estrito de `conceitos.py` — os 9 ids mapeados aparecem nos dois), sem tocar o texto principal do conceito.

**Primary recommendation:** extrair para um módulo novo (`web/src/didatica.jsx`, nome sugerido) `SUBLINHADO`, `SR_ONLY`, `SetorAlvo`, `AiNote`, `AssistenteBox`, `ConceitoSheet` e `CONCEITO_BLOCOS`, com um `T` local espelhado (padrão `uiOpcoes.jsx`); adicionar `GET /api/kb/catalogo` no backend; adicionar `titulo` (dict `{educacional, operador}`, mesma forma de `texto`) ao formato de verbete de `kb.py` para os ~74 verbetes sem `conceitos.py` equivalente; e dar a `ConceitoSheet` um parâmetro explícito de fonte (`fonte: "conceito" | "kb"`, default `"conceito"` para não regredir nenhum call-site existente) que decide se ela busca via `POST /api/conceito/{cid}` (comportamento atual, intocado) ou via o catálogo `kb` já em memória (novo).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Catálogo determinístico de verbetes (83 itens, 9 famílias) | API / Backend | — | `kb.py` já é a fonte única, zero custo, zero LLM (`server/app/kb.py:1-24`) — esta fase só expõe mais um jeito de ler o que já existe, nunca recalcula nada |
| Busca live (filtro por tecla) | Browser / Client | API / Backend | D-04 exige filtragem client-side sem round-trip; o backend só entrega o catálogo cru uma vez (barato, ~83 itens curtos) |
| Renderização da folha de explicação (`ConceitoSheet`) | Browser / Client | — | Puro componente de apresentação, já parametrizado por props — vive no client, consome dado já formatado pelo backend (`texto`/`veja`/`titulo`) |
| Ponte kb.py↔conceitos.py (roteamento de fonte) | Browser / Client | API / Backend | O DISCRIMINADOR de fonte (qual endpoint chamar) é decisão de UI (quem abriu o quê); a FORMATAÇÃO de cada fonte continua no backend (`kb.formatar`/`conceitos.montar`) — nenhum cálculo migra para o client |
| "Saiba mais" fixo por aba (KB-02) | Browser / Client | — | Vid fixo, sem lógica condicional (D-07) — é só um botão que chama `A.abrirVerbete(vid, dados)`/equivalente local, sem estado servidor novo |
| Isolamento estrutural `OpcoesScreen.jsx` × `App.jsx` | Browser / Client (módulo terceiro) | — | Já é o padrão estabelecido (`web/src/opcoes/uiOpcoes.jsx`, `finance.js`, `executarCandidato.js`) — módulo terceiro importado pelos dois lados, nenhum importa o outro |

## Standard Stack

Nenhuma dependência nova. Esta fase usa exclusivamente:
- Backend: FastAPI (rota nova), `server/app/kb.py` (sem mudança de assinatura pública — só aditivo)
- Frontend: React 18 (já em uso), sem biblioteca de busca/fuzzy-match nova — o filtro client-side é uma função pura sem dependência externa (ver Pitfall "porta de matching")

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Filtro client-side por substring simples | Portar `_bate_como_palavra`/`_pontuar` de `kb.py` para JS (fronteira de palavra idêntica ao backend) | Fidelidade 100% com `kb.buscar()`, mas duplica lógica de matching em duas linguagens — risco de divergência silenciosa na próxima correção. Recomendado: substring simples, ver Open Questions #1 |
| `titulo` novo em `kb.py` | Derivar título client-side de `termos[0]` | `termos` das entradas `_de_conceito()` são `tuple(sorted(...))` — ORDEM ALFABÉTICA, não canônica (`server/app/kb.py:103-106`); `termos[0]` produziria título arbitrário/ruim para os 9 conceito-derivados. Para os 74 nativos, `termos` é ordem autoral (ex. `"ind-rsi"` → `("rsi", "ifr", ...)`, `server/app/kb.py:170-171`) mas ainda assim é abreviação minúscula, não um título de tela. `titulo` explícito é a opção honesta, como o próprio UI-SPEC nomeou |

## Package Legitimacy Audit

**Não aplicável — esta fase não instala nenhum pacote novo** (backend: só código Python adicionado a `kb.py`/`main.py`; frontend: só módulos `.jsx`/`.js` novos dentro do repositório, zero `npm install`). Gate do protocolo pulado por ausência de gatilho.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────── Browser (React) ───────────────────────────┐
│                                                                          │
│  App.jsx (root)                          OpcoesScreen.jsx (isolado)    │
│  ├─ boot: fetch /api/conceitos ──┐       ├─ recebe ctx={...} via prop  │
│  ├─ boot: fetch /api/kb/catalogo─┤       ├─ estado local próprio:      │
│  │        (NOVO, D-04)           │       │   verbeteAberto             │
│  │                               │       └─ <ConceitoSheet fonte="kb"  │
│  ├─ PerfilHub → tile "Glossário" │            cid={vidFixo} .../>      │
│  │   └─ TelaGlossario (NOVA)     │            (import do módulo novo)  │
│  │       ├─ busca live (client)  │                    ▲                │
│  │       └─ acordeão por família │                    │                │
│  │            ambos usam catálogo│                    │                │
│  │            já em memória──────┘                    │                │
│  │                                                     │                │
│  ├─ EvolucaoScreen/RadarScreen/MercadoScreen           │                │
│  │   (definidas DENTRO de App.jsx)                     │                │
│  │   └─ botão "saiba mais" → A.abrirVerbete(vid, dados)│                │
│  │                                                      │                │
│  └─ <ConceitoSheet> global (App.jsx:9366, overlay)      │                │
│         zIndex 86, cobre TODAS as abas ────────────────┘                │
│                    │ import de "./didatica.jsx" (módulo NOVO, terceiro) │
│                    ▼                                                    │
│         web/src/didatica.jsx (NOVO — SetorAlvo, ConceitoSheet,          │
│         AssistenteBox, AiNote) — importado por App.jsx E OpcoesScreen.jsx│
│         nenhum dos dois importa o outro                                 │
└──────────────────────────────────┬───────────────────────────────────┘
                                    │ fonte="conceito" (intocado)         │ fonte="kb" (novo)
                                    ▼                                      ▼
                     POST /api/conceito/{cid}              catálogo já em memória
                     conceitos.montar(cid, modo, dados)     (lookup local, sem fetch)
                     — SÓ para os 9 call-sites existentes   fetched 1x via
                       (SetorAlvo toque, link Portfólio)    GET /api/kb/catalogo (NOVO)
                                                             kb.catalogo() + kb.formatar()
```

### Recommended Project Structure

```
web/src/
├── didatica.jsx          # NOVO — módulo terceiro: SetorAlvo, ConceitoSheet,
│                          #   AssistenteBox, AiNote, CONCEITO_BLOCOS, SUBLINHADO,
│                          #   SR_ONLY. T local espelhado (padrão uiOpcoes.jsx).
│                          #   Importado por App.jsx E web/src/opcoes/OpcoesScreen.jsx.
├── App.jsx                # perde as ~170 linhas de SetorAlvo/ConceitoSheet/
│                          #   AssistenteBox/AiNote (passam a vir de didatica.jsx);
│                          #   ganha TelaGlossario (nova, dentro de App.jsx, mesmo
│                          #   padrão de ConfigScreen/AjudaScreen) e o fetch de
│                          #   /api/kb/catalogo no boot.
└── opcoes/
    └── OpcoesScreen.jsx   # ganha 1 novo import de "../didatica.jsx" + estado
                           #   local (verbeteAberto) + botão "saiba mais" fixo
                           #   (mkt-opcao, D-07)

server/app/
├── kb.py                  # ADITIVO: campo "titulo" no dict de cada verbete
│                          #   (~74 nativos; os 9 _de_conceito() já herdam de
│                          #   conceitos.CONCEITOS[cid]["titulo"]); formatar()
│                          #   passa a incluir "titulo" resolvido por modo.
└── main.py                # ADITIVO: GET /api/kb/catalogo (novo, ao lado da
                           #   GET /api/kb/buscar existente, main.py:4595)
```

### Pattern 1: A ponte kb.py × conceitos.py — discriminador explícito, não fallback

**O problema, com evidência concreta.** `ConceitoSheet` hoje (`App.jsx:2941-2951`) sempre chama `store.conceito(cid, { dados })` → `POST /api/conceito/{cid}` → `conceitos.montar(cid, modo, dados, resumido)` (`server/app/main.py:4203-4224`). Essa função só reconhece os 9 ids de `conceitos.CONCEITOS` (`gatilho`, `stop`, `alvo`, `r`, `diversificacao`, `confluencia`, `fundamento`, `barra15m`, `liquidez-opcao` — confirmado por leitura direta de `server/app/conceitos.py:73-339`). Dos 4 `vid` propostos pelo UI-SPEC para KB-02, **3 (`mkt-carteira-simulada`, `ind-rsi`, `mkt-opcao`) NÃO estão nessa lista** — chamar `POST /api/conceito/ind-rsi` hoje devolve `404 "Conceito não existe no catálogo."` (`main.py:4222-4223`). Só `confluencia` (o vid do Radar) resolveria pelo caminho atual, por coincidência de estar nos dois catálogos.

**Por que fallback/tentativa automática é arriscado.** Uma primeira ideia óbvia seria: "se `POST /api/conceito/{cid}` der 404, tenta `kb`". Isso teria um efeito colateral sério para os 9 ids que EXISTEM nos dois catálogos: os 9 verbetes `_de_conceito()`-derivados em `kb.py` são construídos com `conceitos.montar(cid, modo, None, resumido=False)` — **`dados=None` explícito** (`server/app/kb.py:94-98`, comentário confirma: "produz a versão GENÉRICA (sem números de nenhum ativo)"). O fluxo ATUAL de `SetorAlvo`/Portfólio passa `dados` REAIS (números do card, ex. `{ticker, entrada, stop, ...}`). Se o roteamento fosse "tenta conceito, se falhar tenta kb" e algum dia alguém invertesse a ordem, ou se um cliente futuro chamasse `A.abrirVerbete("gatilho", dadosReais)` esperando o texto ANCORADO mas a lógica decidisse usar o caminho `kb` por engano, o usuário veria texto GENÉRICO onde esperava números do próprio card — uma regressão silenciosa exatamente do tipo que o CLAUDE.md princípio 1 proíbe (a explicação deixaria de citar o dado real sem avisar).

**Recomendação: discriminador explícito, thread through `conceitoAberto`/estado equivalente.** `ConceitoSheet` ganha uma prop nova, `fonte` (`"conceito" | "kb"`), **default `"conceito"`** — isso preserva 100% do comportamento atual para TODOS os 9 call-sites existentes (nenhuma chamada existente precisa mudar). Os call-sites NOVOS desta fase (as 4 âncoras fixas de KB-02, e cada item clicado na tela de busca de KB-01) passam `fonte: "kb"` explicitamente, porque eles SEMPRE se originam do catálogo `kb.py` (mesmo quando o vid escolhido coincide com um id espelhado de `conceitos.py`, como `confluencia` — usar o caminho `kb` ali é seguro porque D-07 exige vid FIXO, sem `dados` de card específico, i.e. o comportamento "genérico" do kb É o comportamento correto para esses 4 links, não um efeito colateral indesejado).

```jsx
// dentro de ConceitoSheet (proposta) — App.jsx:2941 hoje, migra para didatica.jsx
useEffect(() => {
  let alive = true;
  setC(null); setErro(false);
  const fetch = fonte === "kb"
    ? Promise.resolve(kbCatalogo.find((v) => v.id === cid) || null).then((v) => {
        if (!v) throw new Error("kb: id não encontrado");
        return { titulo: v.titulo, oQueE: [v.texto], naoAcontece: [], oQueAcontece: [], veja: v.veja };
      })
    : store.conceito(cid, { dados });
  fetch.then((r) => { if (alive) setC(r); }).catch(() => { if (alive) setErro(true); });
  return () => { alive = false; };
}, [cid, dados, fonte]);
```

**Formato do adaptador (shape-normalizing, não force-fit).** Por instrução explícita do UI-SPEC (seção 4), o texto único de `kb.formatar()` NÃO deve ser forçado nos três blocos (`naoAcontece`/`oQueE`/`oQueAcontece`) — ele é UM parágrafo. A proposta acima coloca o texto inteiro em `oQueE` (rótulo "O QUE É", o mais neutro dos três) e deixa os outros dois vazios — `CONCEITO_BLOCOS.map(...)` já pula blocos vazios (`(c[chave] || []).length > 0`, `App.jsx:2975`), então nenhuma seção fantasma aparece. Alternativa equivalente: um 4º valor de `chave` só para kb (`"texto"`) com rótulo neutro — decisão estética de baixo risco, deixada para o plano.

**`titulo` — a peça que falta.** `kb.formatar()` hoje NÃO devolve `titulo` (`server/app/kb.py:1618-1628`, confirmado por leitura: retorna só `id`, `familia`, `texto`, `veja`). Sem isso, `<h2>{c.titulo}</h2>` (`App.jsx:2972`) renderizaria vazio para qualquer verbete kb-nativo. Recomendação (mais honesta, citada pelo próprio UI-SPEC como opção A): adicionar `"titulo": {"educacional": "...", "operador": "..."}` ao dict de cada verbete nativo (~74 entradas em `_INDICADORES`/`_ESTRUTURA`/`_FAMILIAS`/`_MODELOS`(`_modelo_verbete`)/`_SETUPS`/`_PLANO_RISCO_EXTRA`/`_FUNDAMENTOS_EXTRA`/`_MERCADO_B3`/`_KPIS`), e fazer `_de_conceito()` (`server/app/kb.py:94-112`) copiar `c["titulo"]` (já existe em `conceitos.CONCEITOS[cid]`) para as 9 entradas espelhadas — sem trabalho extra ali. `formatar()` passa a incluir `"titulo": v["titulo"].get(voc)` — resolvido pelo mesmo padrão de `texto` (mode-collapse no backend, não no client). Este é o único ponto onde o `test_kb.py` guardião (verifica `id`/`termos`/`texto` não-vazios nos dois modos) provavelmente precisa de uma assertiva nova equivalente para `titulo` — mencionar explicitamente no plano.

**"Veja também" — o lookup precisa trocar de fonte.** `ConceitoSheet` hoje resolve os chips de navegação checando `didatica.conceitos.find(x => x.id === vid)` (`App.jsx:2991`) — ou seja, só contra o catálogo de `conceitos.py` (9 itens). Um verbete kb-nativo com `veja: ["familia-momentum", "setup-ifr2"]` (exemplo real, `ind-rsi`, `server/app/kb.py:188`) teria AMBOS os alvos ausentes de `didatica.conceitos` — os chips desapareceriam silenciosamente, sem erro visível, violando a garantia que o próprio `kb.py` declara ("todo id citado aqui EXISTE no catálogo — sem link morto", docstring `kb.py:35-37`, e reforçada pelo guardião `test_kb.py`). Confirmado por leitura: `kb.catalogo()` é um SUPERCONJUNTO ESTRITO de `conceitos.CONCEITOS` (os mesmos 9 ids aparecem nos dois, via `_conceitos_verbetes()`, `kb.py:115-116`) — então trocar a fonte da checagem de `didatica.conceitos` para o catálogo `kb` (já em memória, do fetch de D-04) resolve os dois casos com uma mudança única, sem regressão para os 9 ids antigos (mesmos ids, mesmo `veja`, resultado idêntico).

### Pattern 2: rota de catálogo completo (D-04)

**Rota nova, ao lado de `GET /api/kb/buscar` (`main.py:4595`):**

```python
# server/app/main.py — proposta, mesma vizinhança de GET /api/kb/buscar
@app.get("/api/kb/catalogo")
async def get_kb_catalogo(modo: Optional[str] = None,
                          scope: Optional[str] = Depends(current_scope)):
    """Catálogo completo da KB (83 verbetes), formatado no modo do escopo.
    Público, sem custo, sem conta — mesma filosofia de GET /api/kb/buscar.
    O front busca UMA vez (D-04) e filtra client-side a cada tecla."""
    from . import kb
    cfg = store.get(_conn, "config", user_id=scope) or {}
    voc = "operador" if (modo or cfg.get("appMode")) == "operador" else "educacional"
    return {"modo": voc, "verbetes": [kb.formatar(v, voc) for v in kb.catalogo()]}
```

Custo: zero LLM, zero I/O externo — `kb.catalogo()` já é descrito como "custo desprezível" mesmo reconstruindo a cada chamada (`kb.py:1556-1561`). Payload estimado: 83 itens × texto curto ≈ dezenas de KB, nenhuma paginação necessária. Cache: **nenhum cache de servidor necessário** — o front busca uma vez por sessão (mesmo padrão já em produção de `store.conceitos(modoApp)` no boot, `App.jsx:8048-8049`, sem refetch depois). Se o modo (`appMode`) mudar em runtime, o catálogo NÃO se realinha automaticamente sob esse padrão — mesma limitação já aceita hoje para `didatica.conceitos` (não é regressão nova, é precedente existente).

**Client — `api.js`/`persistence.js` (novo método, nos DOIS stores, paridade obrigatória):**

```javascript
// web/src/api.js — ao lado de kbBuscar (api.js:285)
kbCatalogo: (modo) => req("GET", "/api/kb/catalogo" + (modo ? "?modo=" + encodeURIComponent(modo) : ""), undefined, 15000),

// web/src/persistence.js — serverStore() (~persistence.js:245) E deviceStore() (~persistence.js:1188)
// serverStore:
kbCatalogo: (modo) => api.kbCatalogo(modo),
// deviceStore:
async kbCatalogo(modo) { ensure(); return api.kbCatalogo(modo || doc.config.appMode || "estudo"); },
```

O guardião genérico `web/tests/test_fase3_paridade_stores_generica.mjs` já falha automaticamente se o método existir só de um lado (varre os DOIS blocos de `persistence.js` por nome) — não precisa de teste pontual novo SÓ para paridade de nome, mas um teste de conteúdo (mesmo padrão de `test_didatica_parity.mjs`) é recomendado para travar a assinatura exata.

**D-03 (sem limite na tela de navegação) e D-02 (não estender `kb.buscar()`).** Como a tela de busca filtra CLIENT-SIDE sobre o array completo já em memória, ela nunca chama `kb.buscar(pergunta, limite=5)` — logo D-02/D-03 são automaticamente respeitadas: `kb.buscar()` continua com `limite=5` inalterado, usado só por `resolver()`/`/api/kb/buscar` (assistente), e a tela nova não precisa de "parâmetro/função nova" no backend — o filtro (com ou sem limite) é 100% lógica de front. Isso simplifica a decisão que D-03 deixava em aberto para o planner: **não é necessário criar nova função em `kb.py`.**

### Pattern 3: extração do módulo compartilhado — duas opções de wiring, recomendação

**Confirmado por leitura de `App.jsx:8970` e `App.jsx:8976`:** o objeto `ctx` passado para TODAS as telas (incluindo `<OpcoesScreen ctx={ctx} />`, `App.jsx:9299`) já inclui `A` (com `A.abrirVerbete`) e `didatica`/`conceitoAberto`. E o `<ConceitoSheet>` que `App.jsx` renderiza hoje (`App.jsx:9366-9375`) é um overlay `position: fixed, inset: 0, zIndex: 86` montado como IRMÃO do bloco condicional de abas — não dentro dele — logo já cobre visualmente qualquer aba, inclusive Opções, sem qualquer import novo.

**Opção A — reusar o overlay global via `ctx.A.abrirVerbete`.** `OpcoesScreen.jsx` só precisaria de um botão chamando `ctx.A.abrirVerbete(vid, dados)` — zero import novo, zero módulo compartilhado. Funciona hoje, sem qualquer mudança estrutural. **Mas isso NÃO corresponde ao texto literal da decisão travada** ("`SetorAlvo`/`ConceitoSheet` saem de `App.jsx` para um módulo compartilhado... `OpcoesScreen.jsx` deve ser importável... ambos importam do módulo novo, nenhum importa do outro" — `38-CONTEXT.md`, seção `canonical_refs`/"Isolamento estrutural"). Reportado aqui por honestidade (Honest Reporting) — não é uma alternativa proposta para substituir a decisão, é o motivo pelo qual a decisão B abaixo precisa ser seguida deliberadamente, não "descoberta" como se fosse a única opção viável.

**Opção B — recomendada — `OpcoesScreen.jsx` importa o módulo novo e mantém estado próprio.** `OpcoesScreen.jsx` ganha `import { ConceitoSheet } from "../didatica.jsx"` e um `useState` LOCAL (ex. `verbeteAberto`), espelhando exatamente o padrão que `App.jsx` já usa para `conceitoAberto`/`A.abrirVerbete`/`A.closeConceito` (`App.jsx:7783`, `8624`, `8636-8639`) — mas como uma cópia independente, não compartilhada. `ConceitoSheet` já é hoje um componente de props puro (`cid`, `dados`, `setor`, `onClose`, `onTrocar`, `didatica`, `voltar` — `App.jsx:2941`), então a extração não exige NENHUMA mudança na lógica interna do componente — só troca de arquivo e (Pattern 1) a prop `fonte` nova. Isso corresponde literalmente ao texto da decisão travada, dá a `OpcoesScreen.jsx` autonomia total (nenhuma dependência de timing/z-index do overlay raiz), e é consistente com o padrão já em produção onde `OpcoesScreen.jsx` gerencia seu PRÓPRIO estado de UI local (`useState` em `useOpcoesMcp.js`/seções `Secao*.jsx`) em vez de emprestar estado de `App.jsx`.

```jsx
// web/src/opcoes/OpcoesScreen.jsx — proposta, mesmo padrão de import de uiOpcoes.jsx
import { ConceitoSheet } from "../didatica.jsx";
// ...
const [verbeteAberto, setVerbeteAberto] = useState(null); // {cid, dados}
// botão fixo (D-07), vid = "mkt-opcao" (ver tabela de vid validada abaixo)
<button onClick={() => setVerbeteAberto({ cid: "mkt-opcao", dados: null })}
  style={{ /* mesmo tratamento visual do link de Portfólio, App.jsx:4358 */ }}>
  saiba mais
</button>
{verbeteAberto && (
  <ConceitoSheet cid={verbeteAberto.cid} dados={verbeteAberto.dados} fonte="kb"
    kbCatalogo={ctx.kbCatalogo /* fetch 1x em App.jsx, repassado via ctx — dado, não import */}
    onClose={() => setVerbeteAberto(null)}
    onTrocar={(vid) => setVerbeteAberto((v) => ({ ...v, cid: vid }))}
    didatica={ctx.didatica} voltar={null} />
)}
```

**`kbCatalogo` passa por `ctx`, não por import.** `ctx` já é o canal estabelecido de dados através do limite de isolamento (App.jsx importa e monta `OpcoesScreen`, `OpcoesScreen` nunca importa `App.jsx` — a assimetria é só de IMPORT, não de dados). Buscar o catálogo `kb` uma vez em `App.jsx` (junto do boot que já busca `didatica`) e repassar via `ctx.kbCatalogo` evita um segundo fetch duplicado quando `OpcoesScreen` abre seu link fixo — e mantém D-04 ("uma vez") literal mesmo com dois pontos de consumo (Perfil e Opções).

### Anti-Patterns to Avoid

- **Tentativa automática conceito→kb com fallback silencioso em caso de 404:** ver Pattern 1 — risco real de regredir os 9 call-sites existentes para texto genérico sem aviso.
- **Reescrever `_bate_como_palavra`/`_pontuar` no client "para ficar igual ao backend" sem necessidade:** a tela de busca não precisa da MESMA fórmula de pontuação do assistente (propósitos diferentes — glossário navegável vs. resposta de 1 pergunta) — ver Open Questions #1.
- **Normalizar `T` (tokens de tema) importando de um módulo central novo:** o padrão do repositório é replicar localmente (`uiOpcoes.jsx:29-31`) — introduzir um import central agora seria uma mudança de arquitetura não pedida por esta fase.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Matching de termo/fronteira de palavra idêntico ao backend | Reimplementação completa de `_bate_como_palavra`/`_pontuar` em JS | Filtro client-side simples (substring case/acento-insensitive) — ver Open Questions #1 | `kb.buscar()` já existe e é usado por `resolver()`; duplicar a fórmula exata em duas linguagens cria uma segunda fonte de verdade que diverge na próxima correção, para um caso de uso (busca navegável) que não precisa de paridade perfeita |
| Normalização de acento/caixa no client | Nova função de normalização Unicode em JS | `String.normalize("NFD")` + replace de diacríticos (mesma técnica de `kb._normalizar`, `kb.py:60-65`) — já é API nativa do browser, sem lib nova | Evita dependência nova (`normalize-diacritics` ou similar) para um problema resolvido por 3 linhas de JS nativo |

**Key insight:** esta fase não tem nenhum problema "deceptively complex" que justifique biblioteca nova — é composição de padrões já em produção no mesmo repositório (extração de componente para módulo terceiro, endpoint de catálogo completo, ponte de formato entre duas fontes de dado determinísticas).

## Runtime State Inventory

> Fase de extração/refatoração (código move de arquivo) — inventário abaixo por precaução, mesmo sem rename de identificador de negócio.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nenhum — `kb.py`/`conceitos.py` não persistem nada; a extração de componentes React não toca nenhuma tabela SQLite/KV | Nenhuma |
| Live service config | Nenhum — nenhuma configuração de serviço externo referencia `SetorAlvo`/`ConceitoSheet` por nome | Nenhuma |
| OS-registered state | Nenhum | Nenhuma |
| Secrets/env vars | Nenhum — `B3_DIDATICA_OFF`/`B3_ASSISTENTE_OFF` continuam lidos do mesmo jeito, sem mudança de nome | Nenhuma |
| Build artifacts | Nenhum — módulo novo `.jsx` entra no bundle Vite normalmente, sem artefato pré-compilado a invalidar | Nenhuma |

## Common Pitfalls

### Pitfall 1: guardião estático `test_conceito_ui.mjs` quebra silenciosamente após a extração

**What goes wrong:** `web/tests/test_conceito_ui.mjs` lê `web/src/App.jsx` via `readFileSync` e testa com REGEX literal sobre o texto-fonte (ex. `/function ConceitoSheet\(/.test(app)`, `/function SetorAlvo\(\{ setorId, dados, rotulo, A, didatica/.test(app)` — `test_conceito_ui.mjs:36-56`). Depois que `SetorAlvo`/`ConceitoSheet` saírem de `App.jsx`, TODAS essas asserções passam a `FALHOU` (não erro de execução — o script imprime "FALHOU" e incrementa `fails`, terminando com exit code não-zero).
**Why it happens:** é o MESMO padrão de risco já documentado 3× no `STATE.md` deste projeto (Fases 32/33/34 — "guardiões reapontados", cada uma achou guardiões regex ancorados no arquivo errado após uma extração de componente).
**How to avoid:** reapontar as asserções de `test_conceito_ui.mjs` para ler `web/src/didatica.jsx` (o módulo novo) em vez de (ou além de) `App.jsx`, mantendo o mesmo espírito de "asserção sobre o CONTRATO, não a assinatura literal" que o próprio arquivo já declara em comentário (`test_conceito_ui.mjs:33-35`).
**Warning signs:** suíte canônica (`bash scripts/executar.sh --testes`) reportando falha em `test_conceito_ui.mjs` logo após mover os componentes, mesmo com o app funcionando visualmente.

### Pitfall 2: chips "veja também" desaparecem silenciosamente para verbetes kb-nativos

Já detalhado em Pattern 1 — `didatica.conceitos.find(...)` (`App.jsx:2991`) só resolve contra os 9 ids de `conceitos.py`. Sem trocar a fonte de checagem para o catálogo `kb` completo, `veja` de qualquer um dos 74 verbetes kb-nativos renderiza ZERO chips, sem erro, sem log — um "link morto" silencioso que o próprio `kb.py` promete nunca ter (docstring `kb.py:35-37`, guardião `test_kb.py`).

### Pitfall 3: `POST /api/conceito/{cid}` com um `vid` kb-nativo devolve 404, não texto vazio

Se algum call-site novo (por engano) chamar o caminho ANTIGO (`fonte` default/ausente) com um dos 74 vids que só existem em `kb.py`, o usuário veria a mensagem de erro genérica "Não consegui carregar a explicação agora" (`App.jsx:2968`/`2947`) em vez do texto real — funcionalmente inofensivo (não quebra o app, respeita princípio 4 de nunca inventar dado), mas indica que o discriminador `fonte` não foi setado corretamente no call-site. Guardião recomendado: teste que os 4 `vid` fixos de KB-02 (e uma amostra dos verbetes navegáveis por família) sempre abrem com `fonte="kb"` nos novos call-sites.

### Pitfall 4: catálogo `kb.py` reflete `B3_DIDATICA_OFF` — comportamento herdado, não bug novo

`_de_conceito()` deriva texto via `conceitos.montar(...)`, que respeita a flag de desligamento (`B3_DIDATICA_OFF`) — se a camada didática estiver desligada em produção, os 9 verbetes espelhados de `conceitos.py` dentro do catálogo `kb` podem vir com texto reduzido/vazio. Isso é comportamento EXISTENTE (não introduzido por esta fase) e já é a mesma limitação de `/api/kb/buscar` hoje — não é uma regressão, mas vale documentar no plano para não ser "descoberto" como bug durante a verificação ao vivo.

### Pitfall 5: guardião `test_kb.py` precisa de assertiva nova para o campo `titulo`

Ao adicionar `titulo` ao formato do verbete, o guardião `server/tests/test_kb.py` (que hoje valida `id`/`termos`/`texto` não-vazios nos dois modos para TODO verbete, `test_kb.py:8-12`) deve ganhar a MESMA verificação para `titulo` — senão um verbete novo (ou um esquecido na migração dos ~74) pode ficar com título vazio sem que nenhum teste acuse.

### Pitfall 6: `titulo` novo não é uma migração de schema — é autoria de conteúdo em escala

**What goes wrong:** ler a recomendação do Pattern 1 ("adicionar `titulo` ao dict de cada verbete nativo") como uma tarefa mecânica de estrutura de dado subestima o esforço real: são ~74 verbetes nativos × 2 modos (`educacional`/`operador`) ≈ 148 strings de título NOVAS a escrever, cada uma sujeita às mesmas regras de vocabulário do resto da camada didática (`.claude/skills/didatica-boris/SKILL.md` — sem verbo de ordem, sem prometer resultado) e ao guardião `test_kb.py`, que varre `EXPRESSOES_PROIBIDAS` (`"sinal de compra"`, `"sinal de entrada"`, `"hora de agir"`, `"chegou o momento"`, fora de negação) em QUALQUER texto do catálogo — inclusive um `titulo` novo, se o guardião for estendido para cobri-lo (Pitfall 5).
**Why it happens:** a proposta técnica (Pattern 1) descreve a FORMA do dado (`{educacional, operador}`, espelhando `texto`), não o VOLUME de autoria — os dois são fáceis de confundir numa leitura rápida.
**How to avoid:** o plano deve dimensionar esta parte como uma task de conteúdo (redigir + revisar ~148 strings curtas), não uma task de refactor de estrutura — possivelmente separada da task que adiciona o campo `titulo` ao código (`kb.formatar()`/`_de_conceito()`), para permitir revisão de texto isolada da revisão de código.
**Warning signs:** um plano que trata "adicionar `titulo`" como 1 task de poucas linhas, sem menção a quantidade de verbetes ou a revisão de vocabulário.

## Code Examples

### Ponto de mount atual do overlay global (referência para Pattern 3)
```jsx
// web/src/App.jsx:9366-9375 — hoje, permanece assim para os call-sites que ficam em App.jsx
{conceitoAberto && (
  <ConceitoSheet cid={conceitoAberto.cid} dados={conceitoAberto.dados}
    setor={conceitoAberto.setor || null}
    didatica={didatica} onClose={A.closeConceito}
    onTrocar={A.trocarConceito}
    voltar={(conceitoAberto.trilha || []).length ? A.voltarConceito : null} />
)}
```

### Padrão de "saiba mais" existente, a replicar nas 4 abas novas
```jsx
// web/src/App.jsx:4358 — precedente único hoje (Portfólio, vid fixo "diversificacao")
<button type="button" onClick={() => A.abrirVerbete("diversificacao", { ticker: conc.t, pct: pctArred })}
  style={{ background: "transparent", border: "none", padding: 0, marginTop: "6px",
           color: T.accent, fontWeight: 700, fontSize: "12px", textDecoration: "none" }}>
  {cp.concentracaoLink}
</button>
```

### Token de tema espelhado localmente — padrão já em produção (a seguir no módulo novo)
```javascript
// web/src/opcoes/uiOpcoes.jsx:29-31 — replicar em web/src/didatica.jsx com as chaves
// realmente usadas por SetorAlvo/ConceitoSheet/AssistenteBox (textFaint, borderSubtle,
// scrim, bgPanel, textPrimary, textSecondary, accent, accentTint10, negative, textMuted, bgBase)
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "borderSubtle", "negative", "bgPanel", "textSecondary", "textPrimary", "borderFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));
```

## State of the Art

Não aplicável — este é um repositório único, sem padrão de indústria externo relevante além dos já documentados (React 18 sem router, tokens CSS-variable). Nenhuma mudança de "old approach → new approach" nesta fase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `titulo` deve ter forma `{educacional, operador}` (espelhando `texto`), não string única | Pattern 1 | Baixo — decisão reversível de formato de dict, sem impacto em dado armazenado; só reescreve `formatar()`/`_de_conceito()` |
| A2 | Filtro client-side de busca (KB-01) deve usar substring simples, não portar `_bate_como_palavra`/`_pontuar` para JS | Don't Hand-Roll, Open Questions #1 | Médio — se Alex preferir paridade exata com `kb.buscar()`, a UX da busca muda ligeiramente (substring pode achar mais/menos resultados que "fronteira de palavra"); reversível, é só lógica de filtro, sem migração de dado |
| A3 | Nome do módulo novo (`web/src/didatica.jsx`) é sugestão, não travado por CONTEXT.md/UI-SPEC | Recommended Project Structure | Nenhum — puramente cosmético, o plano pode escolher outro nome sem impacto funcional |

**Nenhum destes bloqueia o planejamento** — todos são detalhes de implementação de baixo risco, reversíveis sem migração de dado.

## Open Questions

1. **Fórmula de matching da busca live (KB-01): replicar `kb.buscar()` em JS ou usar substring simples?**
   - What we know: D-01 exige filtro a cada tecla, client-side, sobre o catálogo completo (83 itens). D-02 proíbe estender `kb.buscar()` no backend, mas NÃO especifica a fórmula do filtro novo no front.
   - What's unclear: se a UX esperada é "encontra só quando bate como palavra/frase inteira" (igual ao assistente) ou "encontra por qualquer substring" (mais permissivo, mais fácil de implementar, mais familiar como campo de busca comum).
   - Recommendation: usar substring simples (case/acento-insensitive) no front — ver Don't Hand-Roll. Se Alex quiser paridade exata, é uma troca de função pura, sem impacto em endpoint/dado.

2. **`kb.formatar()` ganha `titulo` para TODOS os modos de consumo, ou só quando chamado pela rota de catálogo/busca nova?**
   - What we know: `resolver()` (usado por `/api/assistente`) e `/api/kb/buscar` já chamam `formatar()` hoje e não usam `titulo` em lugar nenhum do fluxo do assistente.
   - What's unclear: se adicionar um campo a mais no payload de `/api/kb/buscar`/`resolver()` tem algum consumidor que trata payload por posição/chave estrita (risco baixo, mas não verificado).
   - Recommendation: adicionar `titulo` universalmente em `formatar()` (é aditivo, JSON não quebra por campo extra) — mais simples que ramificar por chamador.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | Não | Rota nova (`GET /api/kb/catalogo`) é pública, mesma política de `GET /api/kb/buscar` — conteúdo estático de glossário, sem dado de usuário |
| V3 Session Management | Não | `scope` é opcional (`Depends(current_scope)`), só usado para ler `appMode` da config — mesmo padrão da rota irmã |
| V4 Access Control | Não | Conteúdo idêntico para todo usuário (autenticado ou anônimo); nenhuma escrita |
| V5 Input Validation | Sim | Query param `modo` já tratado por allowlist implícita (`"operador"` vs. qualquer outro valor → `"educacional"`, mesmo padrão de `GET /api/kb/buscar`); campo de busca no front nunca é enviado ao backend (filtro é local) — zero superfície de injeção |
| V6 Cryptography | Não | Nenhum dado sensível envolvido |

### Known Threat Patterns for este stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Regex/`.find()` sobre string do usuário no filtro client-side | Denial of Service (local, não-servidor) | Baixo risco real (83 itens, strings curtas) — nenhuma mitigação especial necessária além de não usar regex construída dinamicamente a partir do input sem escapar caracteres especiais |

## Sources

### Primary (HIGH confidence — leitura direta do código)
- `server/app/kb.py` (linhas 1-65, 94-165, 1520-1669) — formato de verbete, `_de_conceito`, `catalogo()`, `buscar()`, `formatar()`, `resolver()`
- `server/app/conceitos.py` (linhas 1-80) — formato de `CONCEITOS`, 9 chaves confirmadas
- `server/app/main.py` (linhas 4186-4225, 4580-4610) — rotas `/api/conceitos`, `/api/conceito/{cid}`, `/api/kb/buscar`
- `web/src/App.jsx` (linhas 1-50, 2810-3013, 2460-2483, 8600-8650, 8960-9010, 9270-9380) — `SetorAlvo`, `ConceitoSheet`, `AssistenteBox`, `AiNote`, `ProfileTile`, objeto `A`, objeto `ctx`, render global de `ConceitoSheet`, imports/comentários de isolamento
- `web/src/opcoes/OpcoesScreen.jsx` (linhas 1-60) — comentário de isolamento, imports de módulos terceiros já em produção
- `web/src/opcoes/uiOpcoes.jsx` (linhas 1-35) — padrão de token de tema espelhado localmente
- `web/src/api.js` (linhas 281-289), `web/src/persistence.js` (linhas 225-253, 1186-1188) — `conceito`/`conceitos`/`kbBuscar` nos dois stores
- `web/tests/test_conceito_ui.mjs` (linhas 1-70) — guardião regex sobre `App.jsx`, risco de quebra pós-extração
- `web/tests/test_fase3_paridade_stores_generica.mjs` (linhas 1-40) — guardião genérico exaustivo de paridade de nome
- `web/tests/test_didatica_parity.mjs` (linhas 1-45) — guardião pontual de paridade de conteúdo
- `server/tests/test_kb.py` (linhas 1-20) — contrato de `id`/`termos`/`texto`/`veja` sem link morto
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário por modo, princípios de dado, caminho de deploy
- `.planning/config.json` — `nyquist_validation: false`, `security_enforcement` ausente (padrão: habilitado)

### Secondary (MEDIUM confidence)
- Nenhuma — toda a pesquisa desta fase foi resolvida por leitura direta do código-fonte do próprio repositório, sem necessidade de fonte externa (esta é uma fase 100% interna, sem biblioteca nova).

### Tertiary (LOW confidence)
- Nenhuma.

## Metadata

**Confidence breakdown:**
- Standard stack: N/A — nenhuma dependência nova
- Architecture (ponte kb×conceitos, extração de módulo, rota de catálogo): HIGH — toda a análise vem de leitura direta de código, com citação de linha, incluindo o achado de que `ctx.A`/overlay global já alcançam `OpcoesScreen.jsx` funcionalmente (não impede seguir a decisão travada, só documenta o porquê da Opção B ser uma escolha deliberada, não a única tecnicamente possível)
- Pitfalls: HIGH — os 5 pitfalls listados são todos verificados por leitura direta (regex de guardião, shape de dado, flag de ambiente), não especulação

**Research date:** 2026-09-23
**Valid until:** válido enquanto `kb.py`/`conceitos.py`/`App.jsx`/`OpcoesScreen.jsx` não sofrerem refactor concorrente — recomendado revalidar se `/gsd:plan-phase 38` rodar mais de ~7 dias após esta pesquisa (repositório com alta cadência de mudança nestes arquivos, ver `STATE.md`)
