# Diagnóstico — 9 tickers com 404 no bootstrap do ledger (LEDGER-01)

**Quando:** 2026-08-28, execução real registrada em `quando_utc` do JSON bruto
(`2026-08-28T09:01:01Z`) para a sonda primária/alias/contraprova, mais uma
verificação suplementar rodada minutos depois (mesma sessão de trabalho).
**Como:** `scripts/diagnostico-tickers-ledger.py`, script pontual descrito no
`00-01-PLAN.md` (Task 1) — não toca produção, não abre banco, não importa o
módulo do bootstrap. Reusa a camada de sessão real de `server/app/yahoo.py`.
**De onde:** rede do ambiente de execução do agente (não é o IP da Railway —
mesma ressalva já registrada em `docs/MEDICAO-Yahoo-Intraday-2026-07-30.md`).

Reproduzir:

```bash
server/.venv/bin/python scripts/diagnostico-tickers-ledger.py \
  --tickers ELET3,BRFS3,ELET6,JBSS3,CRFB3,NTCO3,CPLE6,MRFG3,EMBR3 \
  --rng 15y --tentativas 3 --espaco-s 2.0
```

Comando exato executado (via venv do clone principal, `server/.venv`, cuja
sessão de terminal foi a mesma usada para o restante da fase):

```
server/.venv/bin/python scripts/diagnostico-tickers-ledger.py --rng 15y --tentativas 3 --espaco-s 2.0
```

Parâmetros: `rng=15y`, `tentativas=3`, `espaco-s=2.0` (defaults do script).

---

## 1. Achado principal

Os 9 tickers devolvem **HTTP 404 em TODAS as 3 tentativas, em qualquer
`range`** (testado também com `2y`/`1mo` fora do laço principal, ver seção 3)
— não é ruído transitório do Yahoo (429/401/403 teriam aparecido como
`QuoteUnavailable`, nunca aconteceu). O 404 é uma resposta ESTÁVEL do Yahoo
para estes 9 códigos especificamente. Nenhum dos 9 caiu em `TRANSITORIO`.

A sonda de contraprova (`candle_provider.get_history`) não pôde confirmar
nem refutar nada de forma independente: no ambiente local, sem
`BRAPI_TOKEN`/`MYDATA_TOKEN`, a cadeia de fallback do `candle_provider`
acaba caindo de volta no próprio Yahoo (ver `server/app/candle_provider.py`,
`get_history`), então o erro reportado é o mesmo 404 — não é uma fonte
independente aqui. **Nenhuma env var foi criada ou alterada** para tentar
fazer essa sonda passar (guardrail do plano, verificado por `git status`
ao final).

A sonda de alias (busca pela raiz do ticker sem o dígito final) encontrou
candidatos plausíveis para 3 dos 9 (ELET3/ELET6 → INTB3, mas classe
incompatível — ver seção 3; JBSS3 → JBSS32, classe incompatível; CPLE6 →
CPLE3, classe incompatível), e nenhum candidato para os outros 6
(BRFS3, CRFB3, NTCO3, MRFG3, EMBR3). **Nenhum ticket fechou só com a sonda
de alias por raiz** — todos os 4 vereditos de alias/exclusão desta rodada
vieram de uma verificação suplementar (seção 3), não da busca automática
por raiz sozinha.

## 2. Tabela — um veredito por ticker

| Ticker | Tentativas (sonda 1) | Status observado | Candidato de alias | Veredito |
|---|---|---|---|---|
| ELET3 | 3/3 falharam | HTTP 404 em todas | nenhum encontrado (busca "ELET"/"Eletrobras" vazia) | `INDETERMINADO` |
| BRFS3 | 3/3 falharam | HTTP 404 em todas | nenhum encontrado sob nome próprio; absorvida em MBRF3 (ver seção 3) | `EXCLUIR` |
| ELET6 | 3/3 falharam | HTTP 404 em todas | nenhum encontrado (mesma busca de ELET3) | `INDETERMINADO` |
| JBSS3 | 3/3 falharam | HTTP 404 em todas | JBSS32.SA (JBS N.V., DR2 — classe diferente) | `EXCLUIR` |
| CRFB3 | 3/3 falharam | HTTP 404 em todas; quote Yahoo confirma `quoteType=NONE`/`tradeable=false` | nenhum | `EXCLUIR` |
| NTCO3 | 3/3 falharam | HTTP 404 em todas; quote Yahoo confirma `quoteType=NONE`/`tradeable=false` | nenhum | `EXCLUIR` |
| CPLE6 | 3/3 falharam | HTTP 404 em todas | CPLE3.SA (COPEL ON — classe diferente, PNB extinta) | `EXCLUIR` |
| MRFG3 | 3/3 falharam | HTTP 404 em todas | MBRF3.SA (mesma classe ON, série de 2 anos contínua) | `ALIAS:MBRF3` |
| EMBR3 | 3/3 falharam | HTTP 404 em todas | EMBJ3.SA (mesma classe ON, série de 2 anos contínua) | `ALIAS:EMBJ3` |

## 3. Evidência bruta

### 3.1 Sonda primária/alias/contraprova (`diagnostico-tickers-ledger.py`)

```json
{
  "comando": "scripts/diagnostico-tickers-ledger.py --rng 15y --tentativas 3 --espaco-s 2.0",
  "quando_utc": "2026-08-28T09:01:01Z",
  "rng": "15y",
  "tentativas": 3,
  "espaco_s": 2.0,
  "registros": [
    {
      "ticker": "ELET3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 740},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 447},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 448}
      ],
      "sonda_alias": {
        "raiz_buscada": "ELET",
        "candidatos": [{"symbol": "INTB3.SA", "shortname": "INTELBRAS   ON      NM", "exchange": "SAO"}],
        "candidatos_testados": [{"symbol": "INTB3.SA", "sucesso": true, "n_candles": 24, "ultima_data": "2026-08-27"}]
      },
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "BRFS3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 491},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 469},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 498}
      ],
      "sonda_alias": {"raiz_buscada": "BRFS", "candidatos": [], "candidatos_testados": []},
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "ELET6",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 532},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 422},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 435}
      ],
      "sonda_alias": {
        "raiz_buscada": "ELET",
        "candidatos": [{"symbol": "INTB3.SA", "shortname": "INTELBRAS   ON      NM", "exchange": "SAO"}],
        "candidatos_testados": []
      },
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "JBSS3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 425},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 434},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 461}
      ],
      "sonda_alias": {
        "raiz_buscada": "JBSS",
        "candidatos": [{"symbol": "JBSS32.SA", "shortname": "JBS N.V.    DR2", "longname": "JBS N.V.", "exchange": "SAO"}],
        "candidatos_testados": []
      },
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "CRFB3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 512},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 428},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 451}
      ],
      "sonda_alias": {"raiz_buscada": "CRFB", "candidatos": [], "candidatos_testados": []},
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "NTCO3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 427},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 519},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 459}
      ],
      "sonda_alias": {"raiz_buscada": "NTCO", "candidatos": [], "candidatos_testados": []},
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "CPLE6",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 521},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 452},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 505}
      ],
      "sonda_alias": {
        "raiz_buscada": "CPLE",
        "candidatos": [
          {"symbol": "CPLE3.SA", "shortname": "COPEL       ON      NM", "longname": "Companhia Paranaense de Energia - COPEL", "exchange": "SAO"},
          {"symbol": "CPLE3F.SA", "shortname": "COPEL       ON      NM", "exchange": "SAO"},
          {"symbol": "CPLE.SA", "shortname": "CESTA CPLE99", "exchange": "SAO"},
          {"symbol": "CPLE3Q.SA", "shortname": "COPEL       ON      NM", "exchange": "SAO"},
          {"symbol": "CPLE3M.SA", "exchange": "SAO"}
        ],
        "candidatos_testados": []
      },
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "MRFG3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 432},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 522},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 453}
      ],
      "sonda_alias": {"raiz_buscada": "MRFG", "candidatos": [], "candidatos_testados": []},
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    },
    {
      "ticker": "EMBR3",
      "sonda_primaria": [
        {"tentativa": 1, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 530},
        {"tentativa": 2, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 448},
        {"tentativa": 3, "sucesso": false, "excecao": "HTTPStatusError", "status_code": 404, "ms": 799}
      ],
      "sonda_alias": {"raiz_buscada": "EMBR", "candidatos": [], "candidatos_testados": []},
      "sonda_contraprova": {"sucesso": false, "nota": "contraprova indisponível: HTTPStatusError: 404 Not Found"}
    }
  ]
}
```

*(Erros HTTP truncados nas mensagens `erro` completas do JSON bruto do
script — todos são literalmente `Client error '404 Not Found' for url
'https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>.SA?range=15y&interval=1d&includePrePost=false&crumb=...'`,
a URL exata muda só no `crumb` de sessão por tentativa.)*

### 3.2 Verificação suplementar — por que 4 dos 9 fecharam além da sonda de raiz

A sonda de alias por raiz (ticker sem o último dígito) tem uma limitação
conhecida: quando a B3/empresa troca a RAIZ do código (não só o dígito de
classe — ex.: `EMBR` → `EMBJ`, ou quando o Yahoo apaga o registro antigo por
completo), a busca por raiz não encontra nada. Para não deixar um veredito
sem evidência, uma verificação suplementar rodou contra o Yahoo real:
`/v7/finance/quote` (metadado de listagem — `quoteType`/`tradeable`, que
distingue "código nunca existiu para o Yahoo" de "código existe mas está
INATIVO") e `/v1/finance/search` por NOME da empresa (não só raiz do
ticker), mais `yahoo.get_history` nos candidatos encontrados para confirmar
série de preço real.

```json
{
  "quotes": [
    {"symbol": "BRFS3.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "MRFG3.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "ELET3.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "ELET6.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "JBSS3.SA", "status": 200, "quoteType": "NONE", "tradeable": false, "price": null, "name": null},
    {"symbol": "NTCO3.SA", "status": 200, "quoteType": "NONE", "tradeable": false, "price": null, "name": null},
    {"symbol": "EMBR3.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "EMBJ3.SA", "status": 200, "quoteType": "EQUITY", "tradeable": false, "price": 97.61, "name": "Embraer S.A."},
    {"symbol": "JBSS32.SA", "status": 200, "quoteType": "EQUITY", "tradeable": false, "price": 70.45, "name": "JBS N.V."},
    {"symbol": "CRFB3.SA", "status": 200, "quoteType": "NONE", "tradeable": false, "price": null, "name": null},
    {"symbol": "CPLE6.SA", "status": 200, "quoteType": null, "vazio": true},
    {"symbol": "CPLE3.SA", "status": 200, "quoteType": "EQUITY", "tradeable": false, "price": 14.57, "name": "Companhia Paranaense de Energia - COPEL"},
    {"symbol": "MBRF3.SA", "status": 200, "quoteType": "EQUITY", "tradeable": false, "price": 18.76, "name": "MBRF Global Foods Company S.A."}
  ],
  "buscas": [
    {"query": "Embraer", "candidatos_sao": [{"symbol": "EMBJ3.SA", "exchange": "SAO", "shortname": "EMBRAER     ON      NM"}]},
    {"query": "EMB", "candidatos_sao": []},
    {"query": "Marfrig", "candidatos_sao": [{"symbol": "MBRF3.SA", "exchange": "SAO", "shortname": "MARFRIG     ON      NM"}]},
    {"query": "BRF", "candidatos_sao": [{"symbol": "BRFT11.SA", "exchange": "SAO", "shortname": "FIAGRO BRFT CI"}]},
    {"query": "Eletrobras", "candidatos_sao": []},
    {"query": "ELET", "candidatos_sao": [{"symbol": "INTB3.SA", "exchange": "SAO", "shortname": "INTELBRAS   ON      NM"}]},
    {"query": "Atacadao", "candidatos_sao": []},
    {"query": "Atacadão", "candidatos_sao": []},
    {"query": "CRFB", "candidatos_sao": []},
    {"query": "Natura", "candidatos_sao": []},
    {"query": "NTCO3", "candidatos_sao": []},
    {"query": "CPLE6", "candidatos_sao": []}
  ],
  "historicos": [
    {"ticker": "EMBJ3", "rng": "2y", "sucesso": true, "n": 500,
     "primeira": {"date": "2024-08-27", "close": 45.69},
     "ultima": {"date": "2026-08-27", "close": 97.61}},
    {"ticker": "MBRF3", "rng": "2y", "sucesso": true, "n": 500,
     "primeira": {"date": "2024-08-27", "close": 14.61},
     "ultima": {"date": "2026-08-27", "close": 18.76}}
  ]
}
```

*(Blocos de OHLC completos omitidos do resumo acima por brevidade — os
valores `close` de abertura/fechamento da janela de 2 anos são os
relevantes para julgar continuidade de série; execução completa
reproduzível com o mesmo script de sonda descrito nesta seção.)*

## 4. Veredito por ticker (evidência → conclusão)

### ELET3 — `INDETERMINADO: não resolvido em 2026-08-28: 404 em 3/3 tentativas, quote Yahoo vazio (sem stub, código nunca respondeu com metadado), busca por "ELET"/"Eletrobras" sem candidato plausível na B3`

Nenhuma evidência coletada hoje aponta para renomeação, fusão ou
deslistagem confirmada — apenas ausência total de registro. Não há
candidato de sucessora para testar. Marcado `INDETERMINADO` por A-04: a
evidência de hoje não fecha nenhum dos outros três vereditos.

### BRFS3 — `EXCLUIR: BRF S.A. sem série própria remanescente sob nenhum código; evidência aponta fusão com Marfrig no combinado "MBRF Global Foods Company S.A." (MBRF3.SA), mas a série de preço de MBRF3 (2024-08-27 a 2026-08-27) tem patamar de preço compatível com o histórico de Marfrig (MRFG3), não com BRF — sem candidato de sucessora exclusiva de BRF encontrado`

`BRFS3.SA` está VAZIO no quote do Yahoo (nem stub inativo). A busca por
"BRF" só devolve um FIAGRO sem relação. `MBRF3.SA` (nome "MBRF Global Foods
Company S.A.") confirma que existe uma entidade combinada Marfrig+BRF, mas
a série histórica de MBRF3 não é uma continuação plausível do preço de
BRFS3 — é o padrão de preço do Marfrig antigo (ver veredito de MRFG3).
Emendar a série de BRFS3 em MBRF3 corromperia a medição (A-02): trata-se de
incorporação/fusão com relação de troca de ações, não renomeação do mesmo
papel. `EXCLUIR`.

### ELET6 — `INDETERMINADO: não resolvido em 2026-08-28: mesma ausência total de ELET3 — 404 em 3/3 tentativas, quote Yahoo vazio, sem candidato de sucessora PNB/classe 6 encontrado`

Mesmo caso de ELET3, replicado para a classe 6 (PNB). `INDETERMINADO`.

### JBSS3 — `EXCLUIR: JBS S.A. reorganizada em JBS N.V.; sucessora listada na B3 é JBSS32.SA (JBS N.V., DR2), instrumento de classe DIFERENTE da ação ON original (dígito de classe 2 contra 3, tipo "DR2" e não ação comum) — não é o mesmo papel por A-02`

O quote de `JBSS3.SA` é um stub `quoteType=NONE`/`tradeable=false`
(registro inativo, não "nunca existiu"). O único candidato encontrado na
busca por raiz (`JBSS32.SA`) é explicitamente um instrumento DR2 (recibo
de depósito) da entidade holandesa JBS N.V., não uma continuação 1:1 da
ação ordinária brasileira original. Falha o teste de "mesmo papel" de
A-02. `EXCLUIR`.

### CRFB3 — `EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false (mesmo padrão de instrumento inativo já visto em JBSS3/NTCO3); sem candidato de sucessora em nenhuma busca (raiz "CRFB", nome "Atacadao"/"Atacadão"/"Carrefour Brasil")`

Deslistagem confirmada pelo próprio metadado do provedor (stub inativo, não
ausência total). Nenhuma sucessora encontrada. `EXCLUIR`.

### NTCO3 — `EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false; sem candidato de sucessora em nenhuma busca (raiz "NTCO", nome "Natura")`

Mesmo padrão de CRFB3 — stub inativo confirmado pelo provedor, zero
candidato plausível. `EXCLUIR`.

### CPLE6 — `EXCLUIR: classe PNB extinta — os únicos candidatos da busca por raiz "CPLE" são todos classe ON (CPLE3 e variantes), papel diferente do original por A-02; sem candidato de classe 6/PNB encontrado`

`CPLE6.SA` está VAZIO no quote (sem stub). `CPLE3.SA` está ativo (classe
ON). O filtro de classe do script corretamente rejeitou CPLE3 como
candidato automático (dígito final 3 ≠ 6). Sem candidato de mesma classe,
emendar a série em CPLE3 misturaria papéis diferentes. `EXCLUIR`.

### MRFG3 — `ALIAS:MBRF3`

`MBRF3.SA` é candidato de MESMA classe (ON, dígito 3), encontrado na busca
por nome "Marfrig"/"MBRF", com quote ativo (`quoteType=EQUITY`,
`price=18.76`, `name="MBRF Global Foods Company S.A."`) e série de preço
contínua de 2 anos (`2024-08-27` a `2026-08-27`, 500 candles), em patamar
compatível com o histórico conhecido de Marfrig (R$ 14–19). O nome
"MBRF Global Foods Company" confirma que Marfrig absorveu BRF e renomeou o
CÓDIGO já listado — mesma empresa/papel continuando sob código novo.
`ALIAS:MBRF3`.

### EMBR3 — `ALIAS:EMBJ3`

`EMBJ3.SA` é candidato de MESMA classe (ON, dígito 3), encontrado na busca
por nome "Embraer" (a busca por raiz "EMBR" não encontra, porque a raiz do
código mudou de letras, não só o dígito), com quote ativo
(`quoteType=EQUITY`, `price=97.61`, `name="Embraer S.A."`) e série de preço
contínua de 2 anos (`2024-08-27` a `2026-08-27`, 500 candles). `ALIAS:EMBJ3`.

## 5. Limitação declarada da sonda de alias por raiz

A sonda de alias do script (Task 1) busca só pela raiz do ticker sem o
dígito final. Ela funciona quando a mudança é só de dígito/classe (caso
CPLE6→CPLE3, rejeitado corretamente por classe incompatível), mas NÃO
encontra renomeações de raiz completa (EMBR→EMBJ). Os 2 vereditos `ALIAS`
desta rodada (MRFG3, EMBR3) só fecharam graças à verificação suplementar
por NOME da empresa (seção 3.2), não pela sonda de raiz sozinha. Registrado
aqui para quem for reexecutar o diagnóstico no futuro: se a raiz sozinha
não encontrar nada, buscar também pelo NOME da empresa antes de concluir
`INDETERMINADO`.

## 6. Verificação de fechamento

**Quando:** 2026-08-28T09:15:26Z. **Comando exato** (a partir de `server/`,
`--dry-run` garante zero escrita; `--db` aponta para um arquivo temporário
fora de `server/data/`; `--concorrencia 2` evita reintroduzir concorrência
alta, uma das hipóteses descartadas do 404 original):

```bash
cd server
.venv/bin/python -m app.signal_ledger_bootstrap \
  --dry-run --anos 1 --rng 2y --concorrencia 2 \
  --db /caminho/temporario/fora-de-server-data/ledger-verificacao.db
```

Linha de resumo final, copiada verbatim da saída real:

```
universo: 74 tickers · anos: 1.0 · rng: 2y · concorrência: 2 · DRY-RUN (nada será gravado)

tickers processados: 74 · sinais avaliados: 10929 · novas linhas gravadas: 0 · erros: 0
```

**`erros: 0`** — os 65 tickers que já funcionavam continuam funcionando, e
os 2 tickers resolvidos por alias (MRFG3→MBRF3, EMBR3→EMBJ3) buscaram com
sucesso pelo símbolo novo, SEM erro. 74 tickers do universo = 67
processados com sucesso + 7 excluídos (nunca tocaram a rede) — nenhum
ticker sumiu em silêncio.

Lista de exclusões impressa pela CLI, copiada verbatim:

```
tickers excluídos da carga: 7
  - ELET3: não resolvido em 2026-08-28: 404 em 3/3 tentativas, quote Yahoo vazio (sem stub), busca por raiz "ELET" e por nome "Eletrobras" sem candidato plausível na B3. Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito ELET3.
  - ELET6: não resolvido em 2026-08-28: mesma ausência total de ELET3 — 404 em 3/3 tentativas, quote Yahoo vazio, sem candidato de sucessora de classe 6/PNB encontrado. Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito ELET6.
  - JBSS3: EXCLUIR: JBS S.A. reorganizada em JBS N.V.; a única sucessora encontrada na B3 (JBSS32.SA) é um instrumento DR2 (recibo de depósito), classe diferente da ação ordinária original — falha o teste de "mesmo papel" de A-02. Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito JBSS3.
  - CPLE6: EXCLUIR: classe PNB extinta — os únicos candidatos encontrados (CPLE3 e variantes) são todos classe ON, papel diferente do original por A-02; sem candidato de classe 6/PNB. Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito CPLE6.
  - CRFB3: EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false (instrumento inativo, não ausência total) e nenhuma sucessora foi encontrada em nenhuma busca (raiz do ticker, nome "Atacadão"/"Carrefour Brasil"). Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito CRFB3.
  - NTCO3: EXCLUIR: registro Yahoo confirma quoteType=NONE/tradeable=false (mesmo padrão de CRFB3/JBSS3); nenhuma sucessora encontrada em nenhuma busca (raiz do ticker, nome "Natura"). Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito NTCO3.
  - BRFS3: EXCLUIR: BRF S.A. sem série própria remanescente sob nenhum código Yahoo (quote vazio); evidência aponta fusão com Marfrig no combinado "MBRF Global Foods Company S.A." (MBRF3.SA), mas a série de MBRF3 tem patamar de preço compatível com o histórico do Marfrig antigo, não com BRF — emendar corromperia a medição (A-02, incorporação/fusão com relação de troca de ações). Ver docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, veredito BRFS3.
```

Critério de fechamento da Task 3 (`erros: 0`, exclusões não contam como
erro) atingido na primeira varredura — não foi necessária uma segunda
rodada de confirmação nem novas entradas em `EXCLUIDOS`.
