---
phase: 49-anatomia-da-perna
verified: 2026-10-06T00:00:00Z
status: passed
score: 8/8 must-haves verified (automatizado); 1 item humano residual
overrides_applied: 0
human_verification:
  - test: "Passo 4 do checkpoint 49-08: conferir à mão 1 perna real (pior caso, equilíbrio, resultado no vencimento) contra a conta strike/prêmio"
    expected: "Números da tela batem com a conta manual"
    why_human: "Alex aprovou o 49-08 em 2026-10-06 sem informar os números do passo 4; o teste unitário cobre a conta, mas a conferência com dado real do app não ficou registrada"
---

# Phase 49: Anatomia da perna — Verification Report

**Goal:** o usuário entende o que cada perna aberta faz (direito, pior caso, equilíbrio, prazo) e o que muda no conjunto se ela sair, antes de decidir/encerrar; tudo pelo motor determinístico.
**Status:** human_needed (nenhum gap de código)
**Re-verification:** Não (inicial)

## Evidência executada neste verificador

- pytest dirigido (anatomia_perna, rota anatomia, skill_ref): 84 passed.
- pytest `-k "opcoes or anat or perna or escada or mcp_guard"`: 889 passed, 1 skipped.
- `web/tests/test_opcoes_anatomia_{render,stores}.mjs`, `test_carteira_perna_avulsa.mjs`, `test_opcoes_abertas_e_motivos.mjs`, `test_api_parity.mjs`: todos ok.
- `npx vite build`: ok.
- Suíte completa: pytest 27 failed / 3370 passed; web 1 falha (`test_ios_assets.mjs`). Nenhuma falha toca anatomia/opções: `test_benchmark_ibov`, `test_fase3_kill_switch_duracao`, `test_options_provider_yahoo`, `test_owner`, `test_push_registro_evento`, `test_rotas_fase4`, `test_texto_vazio`, `test_yahoo_granularidade`, `test_yahoo_intraday`. A falha do iOS é falta de `cap copy ios` (chunks ausentes no bundle iOS), fora do escopo. As falhas de pytest parecem rede/sandbox/ambiente, mas não foram checadas contra um baseline anterior à fase; vale uma rodada fora do sandbox pelo orquestrador.

## Observable Truths

| # | Req | Truth | Status | Evidência |
|---|-----|-------|--------|-----------|
| 1 | ANAT-01 | Frase de template por perna, por modo, `skill_ref` ↔ `copy.js` | VERIFIED | `_txt(modo, chave)` em `anatomia_perna.py` via `skill_ref`; `AnatomiaPerna.jsx` renderiza o texto do motor. Chaves `anat_*`: 66 em `skill_ref.py`, mesmo conjunto em `copy.js` (diff vazio, salvo o prefixo literal `anat_` em comentário/regex). |
| 2 | ANAT-02 | Pior caso/equilíbrio/vencimento do motor, independem de cotação; "Hoje" com motivo | VERIFIED | `ler_anatomia`, `_hoje` retorna `(valor, motivo)`; testes unitários verdes. |
| 3 | ANAT-03 | Curvas por perna e total no backend, custo MCP 0, paridade de stores | VERIFIED | Rota `/api/options/anatomia/{ticker}` em `main.py:4028`, `custoMcp: 0`; `opcoesAnatomia` em `api.js:418`, `persistence.js:328` (deviceStore) e `:1471` (serverStore); `test_opcoes_anatomia_stores.mjs` e `test_api_parity.mjs` ok. |
| 4 | ANAT-04 | Gráfico total no topo, chips, hipótese rotulada, ações só com PM do store | VERIFIED | `PosicaoTotal.jsx` + `GraficoAnatomia.jsx` + `useAnatomia.js`; rota lê `positions` do escopo e usa o preço médio do store (nunca do cliente); `ACOES_ID` entra só com `pm` não nulo (`anatomia_perna.py:228`). |
| 5 | ANAT-05 | "Sem esta perna": com/sem e contribuição | VERIFIED | `excluir` na rota → `ler_anatomia(excluir=...)`; leitura com/sem em `PosicaoTotal`; testes de render verdes. |
| 6 | ANAT-06 | Encerrar no card, confirmação informada, nunca vetado por frescor/liquidez | VERIFIED | `AnatomiaPerna.jsx`/`PernasAbertas.jsx`: `premio_indisponivel` vira aviso (`MOTIVO_SO_AVISO`); só `vencida`/`dados_invalidos` desabilitam. A rota não passa pelo gate de liquidez. Fallback 48-16 preservado. |
| 7 | ANAT-07 | Acessibilidade | VERIFIED (código) | SVG `role=img` com `aria-labelledby`, `<table>` alternativa em `PosicaoTotal` e `AnatomiaPerna`, `<pattern>` de hachura para perda, `minHeight: 44px`, `role=group`/`aria-labelledby` na confirmação. Contraste AA nos 4 temas e reduced-motion foram validados visualmente no checkpoint 49-08 (aprovado pelo Alex), não por este verificador. |
| 8 | ANAT-08 | Vocabulário por modo, sem promessa, "Não há dados suficientes", guardiões reconciliados | VERIFIED | Textos por modo em `skill_ref.OPCOES_ESCADA`; estados `sem_pernas`/`erro`/`anat_desatualizado`/`anat_total_sem_data` cobertos; guardiões verdes. |

**Score:** 8/8

## Plano × REQUIREMENTS

Os IDs ANAT-01..08 aparecem nos `requirements:` dos planos 49-01..08. Todos têm definição em REQUIREMENTS.md (linhas 145-166). Sem requisito órfão. A tabela de rastreio em REQUIREMENTS.md (linha 194) e os checkboxes ainda dizem `Pending`/`[ ]`. É pendência de bookkeeping, não de código.

## Regressão pelos quicks pós-fase

Nenhum dos 3 quicks alterou `anatomia_perna.py`, `AnatomiaPerna.jsx`, `PosicaoTotal.jsx`, `PernasAbertas.jsx`, `GraficoAnatomia.jsx` nem `useAnatomia.js` (último commit nesses arquivos é o dos fixes do REVIEW).

| Quick | Toque na área | Resultado |
|-------|---------------|-----------|
| 261006-axi (perna sem ações) | `estruturaCard.js`, hub, `App.jsx`, e **um teste novo em `test_opcoes_anatomia_rota.py`** provando a anatomia sem ações | Testes verdes; a rota já suporta `posicao=None` (ACOES só entra com PM). |
| 261006-b1z (janela de prazo) | `opcoes_escada/curadoria/lastreadas`, `main.py`, `skill_ref`, `copy.js` | Paridade `skill_ref` ↔ `copy.js` mantida; 889 testes de opções verdes. |
| 261006-bwv (patrimônio) | `store.valor_opcoes`, `finance.js`, `App.jsx` | Não toca o motor da anatomia; `test_patrimonio_opcao_avulsa` verde. |

## Anti-patterns

TBD/FIXME/XXX nos arquivos da fase: nenhum. Stubs: nenhum (`anatomia_perna.py` 373 linhas, componentes 46-253 linhas, dados fluem do motor pela rota).

## Gaps

Nenhum.

## Human Verification Required

1. **Conferência numérica real (passo 4 do 49-08).** Abrir uma perna aberta real e comparar pior caso, equilíbrio e resultado no vencimento com a conta manual por strike/prêmio. Esperado: os números batem. Por que humano: a aprovação do checkpoint veio sem os números registrados. Severidade baixa, porque o motor tem teste unitário contra a conta.

Opcional, vindo do 49-REVIEW: CR-01 e WR-02 estão marcados "fixed: requires human verification" (releitura falhando mostra alerta com nova tentativa; `premio_indisponivel` mantém o botão habilitado). Os testes automatizados passam, mas o comportamento visual na tela real não foi reconferido por este verificador.

---

_Verified: 2026-10-06_
_Verifier: Claude (gsd-verifier)_

## Resolução (2026-10-06, orquestrador)

- **Item humano (passo 4 do 49-08):** o Alex respondeu "aprovado" à lista consolidada sem informar os números; o registro não os inventa. A conta (−277,00 total / −37,00 sem a PUT / −240,00 de contribuição em R$ 48,00) está provada por `server/tests/test_anatomia_perna.py`. CR-01 e WR-02 do REVIEW: cobertos pelo aprovado consolidado e por guardiões novos.
- **Falhas da suíte citadas pelo verifier (27 pytest + `test_ios_assets`):** vieram de execução dentro do sandbox (sem rede; sem `cap copy ios`). A suíte canônica `bash scripts/executar.sh --testes` rodada fora do sandbox pelo orquestrador em 2026-10-06, após as quicks axi/b1z/bwv: 3397 pytest passed, 5 skipped, 3 xfailed, todos os `.mjs` OK, saída 0.
- **Contraste AA e reduced-motion:** validados pelo checkpoint humano; sem medição automatizada nova.
Status elevado de `human_needed` para `passed` por essa base.
