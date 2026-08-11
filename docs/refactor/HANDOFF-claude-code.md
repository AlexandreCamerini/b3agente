# Handoff para o Claude Code — aplicar Refactor A (eixo de seleção do Radar)

Cole o bloco abaixo no Claude Code, **na raiz do repo `b3agente`**, com os 5
arquivos já copiados para dentro do repo (ver "Antes de colar").

## Antes de colar (colocar os arquivos no repo)

```bash
cd caminho/para/b3agente
mkdir -p docs/refactor
cp ~/Downloads/regime.py                 server/app/regime.py
cp ~/Downloads/test_regime.py            server/tests/test_regime.py
cp ~/Downloads/scanner.run_scan.patch    docs/refactor/
cp ~/Downloads/ESPEC-A-eixo-selecao.md   docs/refactor/
cp ~/Downloads/ESPEC-B-validacao-regime.md docs/refactor/
git checkout -b feat/eixo-selecao-regime
```

## Prompt para o Claude Code

> Contexto: estou trazendo um refactor do Radar (N1) especificado em
> `docs/refactor/ESPEC-A-eixo-selecao.md`. Os arquivos `server/app/regime.py` e
> `server/tests/test_regime.py` já estão no repo (módulo puro + testes, 10/10
> passando isolados). Falta integrar o `scanner.py`.
>
> Tarefa, nesta ordem, sem sair do escopo do N1:
> 1. Aplique o patch: `git apply docs/refactor/scanner.run_scan.patch`. Se
>    falhar por drift, faça os 3 hunks à mão a partir da ESPEC-A §4 (import de
>    `regime`; `snaps` dict + `snaps[symbol] = snap`; trocar o `results.sort`
>    por `regime.ranquear(results, snaps)`).
> 2. Rode a suíte canônica: `bash scripts/executar.sh --testes`. Quero as DUAS
>    suítes verdes (pytest backend + web/tests/*.mjs), não só `test.sh`.
> 3. Confirme que o contrato do Radar não regrediu: todo item de `results`
>    ainda tem `confluencia`, `veredito`, `plano`, `spark`. Os novos campos
>    (`regime`, `momentumRelPct`, `gatilhoAlinhado`, `radarScore`) devem existir.
> 4. Crie `docs/adr/009-eixo-de-selecao.md` registrando a decisão (resumo da
>    ESPEC-A §1–2: por que confluência deixa de ser chave de ordenação).
>
> NÃO faça agora (é a Fase A parte 2, decido depois):
> - O guardrail de família no prompt (ESPEC-A §6) — exige espelhar
>   `defaults.py` ↔ `web/src/catalog.js` byte-a-byte (invariante de paridade,
>   o teste trava). Deixe como TODO no ADR.
> - Qualquer coisa do B (validação por regime) — depende desta fase mergeada.
>
> Ao final: resumo do que mudou, arquivos tocados, resultado dos testes,
> limitações. Não commite sem eu revisar o diff.

## Depois (Fase B)

Quando A estiver mergeado e o Radar rodando com `regime`, abra outra sessão do
Claude Code apontando `docs/refactor/ESPEC-B-validacao-regime.md` — os deltas
já estão concretos (registrar+regime, compute_stats.porSetupRegime,
historico_do_par). Só comece o B depois que o campo `regime` estiver gravando
em `analysis_outcomes` por algumas semanas — B2 (rebaixamento no ranking) sem
amostra `n ≥ MIN_N` reordena com ruído.
