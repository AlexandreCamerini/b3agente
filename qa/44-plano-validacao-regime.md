# qa/44 — Análise da ESPEC-B e plano: fechar o loop de validação por regime

**Data:** 2026-08-11 · **Origem da proposta:** chat "Análise técnica B3 setups"
(projeto Bolsa, claude.ai), exportada em 11/08 no mesmo lote do Refactor A —
versionada em [`docs/refactor/ESPEC-B-validacao-regime.md`](../docs/refactor/ESPEC-B-validacao-regime.md)
· **Depende de:** Refactor A em produção (feito em 11/08 — ADR-009, PR #8)
· **Status:** plano aprovado para implementação em fases; B2 atrás de flag

## 1. Análise da proposta (verificada contra o código real em 11/08)

**O que a spec acerta — premissas conferidas linha a linha:**

- A camada de validação existe e é boa, como a spec afirma:
  `analysis_outcomes.py` tem `registrar`, `_celula` com guarda `MIN_N=10` (sem
  porcentagem abaixo disso), `compute_stats` com `porSetup`, `porConfianca`,
  `porDecisao`, expectância (R médio), calibração e drawdown. Não é greenfield.
- O gap é real e cirúrgico: nenhum campo `regime` no registro; a confiança é
  declarada e comparada, nunca derivada do resultado medido.
- O desenho dos 3 deltas é minimalista e reusa `_celula` — certo.
- O guardrail CVM está explícito e no vocabulário certo (descritivo, nunca
  promessa; `< MIN_N` nunca vira porcentagem).

**Os 4 furos que o plano corrige:**

1. **`regime=snap["regime"]["regime"]` não existe nos call-sites.** O A anexa
   o regime ao **resultado do scan** (`regime.ranquear`), não ao snapshot dos
   fluxos N1/N2. Nos call-sites reais (`main.py:898` N1, `main.py:1002` N2) o
   que está em escopo é `snap`. Correção: chamar `regime.classificar(snap)`
   direto no momento do registro — é função pura e barata, e grava o regime
   DO MOMENTO DA ANÁLISE, que é exatamente a semântica pedida pelo Delta 1.
2. **N2 registra `setup=None`** → a chave `"None @ regime"` do
   `porSetupRegime` seria célula-lixo. Correção: normalizar para `"—"` (a
   spec já usa esse fallback) e restringir o B2 (rebaixamento) a registros
   COM setup — na prática, o recorte setup×regime é do N1.
3. **O teto do B2 no `radarScore` não reordena nada.** Mesma armadilha pega no
   Refactor A: `radarScore` é derivado para exibição; a ordenação real é a
   TUPLA (tier, momentum, gatilho, confluência, ticker). Um teto no score
   mudaria o número mostrado sem mover o ativo. Correção: o rebaixamento age
   na tupla — remove o bônus de `gatilhoAlinhado` e marca
   `rebaixadoPorHistorico=true` no resultado (a UI explica o porquê). O
   guardião do ranking é atualizado COM NOTA de novo (regra do repo).
4. **A amostra por par demora.** Só entram na estatística leituras N1 com
   decisão COMPRAR/VENDER e stop+alvo, maturadas em 10 pregões; um par
   (setup × regime) atingir `n ≥ 10` leva semanas. Ativar o B2 cedo
   reordenaria com ruído — o oposto do objetivo, como a própria spec admite.
   Correção: B2 nasce atrás de `B3_OUTCOMES_FEEDBACK` (default OFF) e só se
   liga quando o painel mostrar pares com `n ≥ MIN_N`.

**Fora de escopo desta entrega** (mantém a paridade de prompts intocada): nada
de citar histórico medido no PROMPT do N2 — B1 anota payload e UI apenas.
Levar `historicoRegime` para o texto da IA exigiria paridade byte a byte
`defaults.py` ↔ `catalog.js` e vocabulário CVM revisado; fica como fase C, se
o Alex quiser.

## 2. Plano de implementação

Porta de saída de TODA fase: `bash scripts/executar.sh --testes` (as DUAS
suítes) com **verificação de `[X]`**, não só contagem de `[OK]`. Front tocado
→ `npx vite build`. Deploy só-backend → bump de `SERVER_BUILD_ID`.

### Fase B1a — Gravar e segmentar (começa a acumular amostra JÁ)

**Arquivos:** `server/app/analysis_outcomes.py` (param `regime` no
`registrar`, `porRegime` + `porSetupRegime` no `compute_stats`),
`server/app/main.py` (2 call-sites passam
`regime=regime.classificar(snap)["regime"]`).

**Testes** (`test_analysis_outcomes.py`, ampliação): registro grava regime;
registro antigo sem regime cai em `"—"` sem quebrar; células respeitam
`MIN_N`; chave `setup=None` normalizada para `"—"`.
**Comando:** `server/.venv/bin/python -m pytest tests/test_analysis_outcomes.py -q`

### Fase B1b — `historico_do_par` (função pura)

**Arquivos:** `server/app/analysis_outcomes.py` (como na spec, com os 4
status: favoravel/desfavoravel/neutro/sem_dados).
**Testes:** os 4 status + amostra insuficiente nunca vira status direcional.
**Comando:** idem B1a.

### Fase B1c — Anotação (transparência, sem reordenar)

**Arquivos:** `server/app/scan_deep.py` ou `main.py` (anexa `historicoRegime`
ao payload do N1), `web/src/App.jsx` (tela Eficiência da IA ganha o recorte
por regime e por setup×regime; card do ativo mostra a anotação com o
vocabulário fixo: "resultado medido em N leituras passadas neste regime —
passado não é garantia futura").

**Guardrails:** disclaimer obrigatório em toda superfície; `npx vite build`;
`bump.sh` + `entregar.sh` para publicar (é entrega com front).
**Testes:** teste de UI (`web/tests/`) cobrindo a seção nova e a ausência de
porcentagem quando `insuficiente`; guardião do vocabulário (sem "vai dar",
sem promessa).

### Fase B2 — Rebaixamento por histórico (flag, só com amostra)

**Arquivos:** `server/app/regime.py` (`ranquear` recebe `stats` opcional; par
desfavorável com `n ≥ MIN_N` perde o bônus de gatilho na TUPLA e ganha
`rebaixadoPorHistorico=true`), `server/app/scanner.py` (injeta stats quando
`B3_OUTCOMES_FEEDBACK=1`), guardião do ranking atualizado com nota (2ª nota —
histórico medido passa a rebaixar).

**Critério de ativação (não é data, é dado):** painel mostrando ≥3 pares
setup×regime com `n ≥ MIN_N`. Até lá a flag fica OFF e o comportamento é
idêntico ao ADR-009.
**Testes:** rebaixamento só com flag + amostra; `sem_dados` nunca rebaixa;
tupla reordenada de fato (não só o score); marca visível no payload.

### Verificação final

Suíte canônica; masstest determinístico (`scripts/masstest-agentes.py`) para
o contrato do N1; validação ao vivo: uma leitura N1 real grava outcome com
regime (conferir no SQLite), painel Eficiência mostra células por regime com
`n` pequeno e SEM porcentagem.

## 3. Critérios de aceite (da spec + correções)

- `compute_stats` retorna `porRegime`/`porSetupRegime`; `< MIN_N` sem
  porcentagem; registro antigo não quebra (`"—"`).
- `historico_do_par` puro e coberto (4 status).
- B1 anota sem reordenar; N2 sem setup nunca gera célula-lixo.
- B2: OFF por default; ligado, rebaixa NA TUPLA com `n ≥ MIN_N`, sempre com
  disclaimer e marca explícita; guardião com nota.
- Interlock A→B respeitado: o campo gravado vem de `regime.classificar` no
  momento da análise.
- Nenhuma mudança em prompts (paridade intocada nesta entrega).
