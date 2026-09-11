---
status: completed
quick_id: 260911-dcq
commit: 5d2117ab10e03a4dd17e5da6edb3e403314ceeaa
files_modified:
  - server/app/scanner.py
  - server/app/scan_deep.py
  - server/app/technical_snapshot.py
files_created:
  - server/tests/test_fuso_carimbos_visiveis.py
---

# Quick 260911-dcq: os três carimbos de apuração em horário de Brasília

## O que foi feito

`scanner.timestamp` (App.jsx:6980, "N/M ativos varridos"), `scan_deep.timestamp`
e `technical_snapshot.generatedAt` usavam `time.strftime("%Y-%m-%dT%H:%M:%S")`
sem fuso. Em produção (Railway, container em UTC) o carimbo saía 3h à frente
do horário real de Brasília e, na janela das 21:00 às 23:59 BRT, saía com o
DIA seguinte. Contraria o princípio 3 do CLAUDE.md: dado de mercado exibe o
horário real da última atualização; um horário adiantado é pior que nenhum
porque parece preciso.

Correção: extraída uma `_now_iso()` por módulo (`datetime.now(BRT).strftime(...)`,
mesmo padrão de `_day()`/`_hoje()` já estabelecido em `scan_deep.py`/
`candle_provider.py`), substituindo o `time.strftime` inline nos três locais.
`BRT = timezone(timedelta(hours=-3))` local ao módulo onde ainda não existia
(`scanner.py`, `technical_snapshot.py`); `scan_deep.py` já tinha o BRT de
260911-15a (A-10) — reaproveitado.

Commit: `5d2117ab10e03a4dd17e5da6edb3e403314ceeaa` —
`fix(fuso): carimbos de apuracao visiveis em horario de Brasilia (D-2)`.

## Decisão de formato

Mantido `%Y-%m-%dT%H:%M:%S`, sem sufixo de fuso (`-03:00`). A tela imprime
`res.timestamp` como string crua (`web/src/App.jsx:6980`) — acrescentar o
sufixo mudaria o que o usuário lê e exigiria tocar o front. Só a FONTE do
relógio mudou (de `time.strftime()` naive para `datetime.now(BRT)`), a string
resultante tem o mesmo shape de antes; só o valor de hora/dia agora está
correto. Front NÃO foi editado, conforme escopo.

## Prova RED/GREEN (instante que cruza a meia-noite)

Instante usado: **01:30 UTC do dia 10/09/2026 = 22:30 BRT do dia 09/09/2026**
— UTC e BRT em DIAS diferentes, para provar dia E hora (um teste que só prova
a hora foi exatamente o que deixou os três carimbos passarem despercebidos na
correção anterior de 260911-15a).

Script standalone fora do repo (`$TMPDIR/dcq_red_green.py`, não commitado),
usando a linha EXATA extraída de `git show HEAD:server/app/scanner.py` (idêntica
em `scan_deep.py:155` e `technical_snapshot.py:174` antes desta correção):

```
RED  (código de ANTES, container em UTC): '2026-09-10T01:30:00'
     esperado em BRT:                      '2026-09-09T22:30:00'
     RED confirma o defeito (dia/hora errados)? True

GREEN (código corrigido, mesmo instante):
  scanner._now_iso() = '2026-09-09T22:30:00'            OK=True
  scan_deep._now_iso() = '2026-09-09T22:30:00'           OK=True
  technical_snapshot._now_iso() = '2026-09-09T22:30:00'  OK=True
```

Nota metodológica: `time.strftime(fmt)` sem argumentos chama `time.localtime()`
— uma função C que lê o relógio/fuso reais do processo; não é possível
monkeypatchar via atributo Python (`time.localtime = ...`, testado, sem
efeito). O valor RED foi calculado como `time.strftime(fmt, time.gmtime(instante))`,
matematicamente idêntico ao que a linha antiga devolveria num container com
fuso UTC (a produção real, documentado em `260909-oyu`/`A-10`: local == UTC).

Guardião novo `server/tests/test_fuso_carimbos_visiveis.py` (5 testes, todos
verdes), espelhando `test_store_now_str_brt.py` e
`test_fuso_candle_provider_scan_deep_brt.py`: monkeypatch de `datetime` em
cada módulo com o mesmo instante-fronteira, provando `_now_iso()` dos três
módulos e um guardião de CLASSE (`scan_deep._day()` e `scan_deep._now_iso()`
concordam no mesmo dia para o mesmo instante — a lição do A-10 de que um
arquivo com o defeito corrigido pela metade é pior que nenhuma correção,
porque esconde a inconsistência).

```
tests/test_fuso_carimbos_visiveis.py::test_scanner_now_iso_e_hora_e_dia_de_brasilia PASSED
tests/test_fuso_carimbos_visiveis.py::test_scan_deep_now_iso_e_hora_e_dia_de_brasilia PASSED
tests/test_fuso_carimbos_visiveis.py::test_technical_snapshot_now_iso_e_hora_e_dia_de_brasilia PASSED
tests/test_fuso_carimbos_visiveis.py::test_scan_deep_day_e_timestamp_concordam_no_mesmo_instante PASSED
tests/test_fuso_carimbos_visiveis.py::test_formato_das_strings_nao_mudou PASSED
5 passed in 0.04s
```

## Varredura por um quarto carimbo naive

`grep -rn "time.strftime\|strftime(" server/app/` cobriu todo o módulo.
Achados que NÃO entraram:

- **`push.py:146`** — `p["at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())`.
  Usa `time.gmtime()` explícito (UTC deliberado, não naive-local), é
  bookkeeping interno de `pushPrefs` (última escrita das preferências de
  push) lido só por `timing_watch.py` (seleção de audiência do scheduler) —
  nunca chega ao front (`grep` em `web/src/App.jsx`/`persistence.js` não achou
  consumo do campo `at`). Não é "carimbo de apuração" visível ao usuário.
- **`backup.py:92`** — `carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")`.
  Naive local, mas é o NOME do arquivo de backup (`b3_agente-{carimbo}.db`),
  não um dado de mercado/apuração exibido na UI. Fora de escopo do D-2.
- **`metering.py:106,115`** e **`llm.py:23`** — `datetime.now(timezone.utc)`
  explícito, âncora deliberada de dia/mês de FATURAMENTO/COTA (comentário em
  `metering.py`: "None = comportamento histórico (UTC)"), não um carimbo de
  apuração de mercado. Fora de escopo.

Nenhum quarto carimbo de apuração naive foi encontrado além dos três do plano.

## Pendência seguinte (fora de escopo aqui)

A segunda parte do achado D-2 — `date.today()` naive em `options_api.py:36`,
`main.py:2515,2540,2741` e `mydata_client.py:202`, fazendo aritmética de DIAS
ATÉ O VENCIMENTO que alimenta o gate de liquidez de opções — **não foi
tocada**. Tem consequência financeira (não cosmética) e merece task própria
com prova de impacto no gate antes de mexer.

## Suíte

`bash scripts/executar.sh --testes` (com `dangerouslyDisableSandbox: true` —
a suíte falha por sandbox, `PermissionError`/`Operation not permitted` em
`/test_*.log`, mesmo sintoma documentado nas environment_notes):

- pytest: **2326 passed, 4 skipped**, 485 warnings.
- `web/tests/*.mjs`: **126/126 OK** (contagem de arquivos = contagem de `[OK]`).

Nenhuma falha. Front não foi editado (`web/src/` fora do diff do commit).

## Limitações conhecidas

- Nenhuma. Os três carimbos do escopo estão corrigidos e testados; a
  varredura por um quarto não encontrou candidato adicional.

## Instruções para validar localmente

```bash
cd server && /Users/acamerini/dev/borisv2/server/.venv/bin/python -m pytest \
  tests/test_fuso_carimbos_visiveis.py -v
cd .. && bash scripts/executar.sh --testes   # se falhar por sandbox, repetir
                                              # com permissão de bypass
```
