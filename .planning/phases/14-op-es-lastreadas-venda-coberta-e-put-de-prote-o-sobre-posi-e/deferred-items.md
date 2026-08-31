# Deferred Items — Phase 14

Out-of-scope discoveries logged during execution, not fixed (per SCOPE BOUNDARY:
only auto-fix issues directly caused by the current task's changes).

## Plano 07

- **`server/tests/test_reuso_analise_n2.py::test_rota_reaproveita_e_so_chama_a_ia_quando_a_pergunta_muda`**
  e **`server/tests/test_rotas_fase4.py::test_ia_sem_chave_gera_fallback_deterministico_technical`**
  falham quando a suíte pytest inteira roda (`bash scripts/executar.sh --testes`),
  mas passam limpos quando rodados isoladamente (`pytest tests/test_reuso_analise_n2.py
  tests/test_rotas_fase4.py` → 44 passed). Indica poluição de estado entre arquivos
  de teste (provável módulo global não resetado entre suites, ex.: cache de
  `technical_snapshot`), não relacionada a opções lastreadas — o plano 14-07 não
  tocou nenhum arquivo em `server/`. Não corrigido (fora do escopo desta task);
  registrado para investigação futura.
