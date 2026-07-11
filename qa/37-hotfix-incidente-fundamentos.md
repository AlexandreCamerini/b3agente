# qa/37 — HOTFIX do incidente da F10.2 (fundamentos derrubaram o servidor)

> Build: **F9-20260710-6**. Incidente relatado pelo Alex: "o Operador IA
> perdeu a conexão com o Railway, a área de config da base sumiu, mais coisas
> desapareceram". Revisão adversarial (agente) achou **DOIS bugs ortogonais**,
> ambos introduzidos na F10.2 (qa/36). Nenhum dado do usuário foi perdido
> (boot é local-first e protegido por try/catch).

## Bug 1 (CRÍTICO) — `fundamentals` usado sem `import` em `main.py`
`main.py` referenciava `fundamentals` em `_enrich_fundamentos` (scan) e no N2
sem nunca ter `from . import fundamentals`. Como o uso é em corpo de função,
o `import app.main` passava — mas **em runtime `/api/scan` estourava
`NameError` → HTTP 500** em toda varredura com resultados (inclusive o
resultado-do-dia em cache). Efeito: **Radar/Mesa não carregava** — "áreas
desaparecendo", determinístico e independente do event loop.
- Fix: adicionado `from . import fundamentals`.
- Defesa em profundidade: `_enrich_fundamentos` agora é **best-effort total**
  (try/except) — o fundamento é overlay e NUNCA pode derrubar o scan.
- Por que passou batido: a suíte testava `scanner.run_scan` direto, nunca o
  endpoint. Meu check de "boot OK" só importava o módulo (não roda o corpo).

## Bug 2 (CRÍTICO) — warm job bloqueava o event loop
`agent.scheduler_loop` chamava `fundamentals.maybe_warm`, que rodava
`warm_universe` **síncrono dentro da corrotina** → `httpx.get` bloqueante em
loop por ~74 tickers (timeout 12s cada, brapi rate-limited). Congela o
FastAPI inteiro por dezenas de segundos a minutos → healthcheck do Railway
falha → restart → roda de novo → **crash loop**. Efeito: **perda de conexão
sistêmica** (agente, config do servidor, tudo que depende do backend).
- Fix (já parcialmente no working tree, agora completo e commitado):
  1. `maybe_warm` **só roda com `BOLSAI_API_KEY`** (produção está sem a chave
     → **no-op**: incidente para no deploy). A bolsai é a fonte do universo;
     sem chave, aquecer via brapi seria inútil (4 tickers) e rate-limited.
  2. Quando há chave, roda **fora do event loop** via `asyncio.to_thread`,
     com throttle 0,4s e teto de 60/passada, e só bolsai (não martela brapi).
  3. Busca inline do N2 também via `asyncio.to_thread`.
  - Seguro porque o `db.py` usa conexões **thread-local**
    (`_ThreadLocalConnection`) → I/O em thread não quebra o SQLite.

## Frontend — limpo (confirmado)
A revisão varreu o App.jsx: todos os símbolos novos resolvem, todas as chaves
de copy existem nos 2 modos, a reorg de Perfil/Agente não removeu destino, e a
seção "SNAPSHOTS DAS ANÁLISES" (qa/35) tem guardas `|| {}` — não derruba o
`LogsDebugScreen`. **Nenhum bug de frontend.** O "config sumiu" era efeito do
backend fora do ar, não perda de tela nem de dado.

## Guardiões novos (test_fundamentals.py)
- `test_main_importa_fundamentals_e_scan_enrich_nao_quebra` — chama
  `_enrich_fundamentos` DE VERDADE (o ponto do NameError); teria pego o bug 1.
- `test_maybe_warm_pula_sem_chave_bolsai` — sem chave, warm é no-op (bug 2).
- `test_maybe_warm_roda_em_thread_com_chave` — com chave, delega ao thread.
- `test_warm_universe_respeita_limit`, `test_fetch_merged_pula_brapi_no_warm`.
- `test_integracao_esta_ligada_no_backend` reforçado: exige `asyncio.to_thread`
  e o gate `not _bolsai_key()` no fundamentals.

## Validação
**258 pytest** + web de código verdes; `import app.main` + `_enrich_fundamentos`
executam sem erro; servidor sobe limpo. Build **F9-20260710-6**.

## Hard stop (aparelho)
1. **Radar/Mesa volta a carregar** (era o 500 do bug 1).
2. **Operador IA reconecta ao servidor**; config do servidor responde.
3. Sem `BOLSAI_API_KEY`: chip de fundamento só nos ativos abertos no N2 (que
   busca inline via brapi para os 4 tickers) — resto "sem dado". Normal.

## Lição / processo
Faltou exercitar o **endpoint** (não só `run_scan`) e rodar o app de verdade
antes de entregar. Para as próximas: um smoke test de `/api/scan` via
TestClient pegaria import faltante; e nenhuma chamada de rede síncrona pode
entrar no event loop (só via `asyncio.to_thread` ou httpx async).
