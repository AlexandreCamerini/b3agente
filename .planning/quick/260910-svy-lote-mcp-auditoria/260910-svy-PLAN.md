---
quick_id: 260910-svy
phase: quick-260910-svy
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [server/app/mcp_client.py, server/app/options_mcp_api.py, server/requirements.txt, server/requirements-prod.txt, server/tests/test_mcp_client.py]
autonomous: true
---

<objective>
Lote de cinco achados da auditoria de 2026-09-10 (`docs/AUDITORIA-2026-09-10.md`),
todos no código MCP da Fase 1. Dois deles fazem o app afirmar o que não mediu,
violando o princípio 4 do CLAUDE.md. Backend-only.
</objective>

<context>
Verificado no SDK instalado (`mcp` 2.2.0), e é o centro de dois achados:
```
INTERNAL_ERROR    = -32603
CONNECTION_CLOSED = -32000   <-- mesmo valor que CODIGO_TETO
REQUEST_TIMEOUT   = -32001
```
</context>

<tasks>
<task type="auto">
  <name>Task 1 (A-01 + A-02 + A-03): classificar erro pelo que ele é, e logar o motivo</name>
  <files>server/app/mcp_client.py, server/app/options_mcp_api.py, server/tests/test_mcp_client.py</files>
  <action>
  **A-01** (`mcp_client.py:64,330`) — `CODIGO_TETO = -32000` colide com
  `CONNECTION_CLOSED` do SDK. Hoje uma conexão caída vira HTTP 402 "atingiu o
  teto de chamadas do dia": número afirmado sem medição. Só tratar como teto
  quando o `-32000` vier ACOMPANHADO da prova: `data` é dict E traz
  `teto`/`chamadas_hoje` (o serviço sempre manda, ver contrato do MCP, seção
  "Erro JSON-RPC -32000"). Sem essa prova, `-32000` é conexão fechada e cai em
  `McpIndisponivel`. Importar os códigos de `mcp.types` em vez de cravar
  número — se o SDK mudar, o import quebra alto em vez de classificar errado.

  **A-02** (`mcp_client.py:341-347`) — o ramo `if status in (401,403)` é código
  morto no transporte streamable-HTTP: o SDK converte qualquer não-2xx em
  `ErrorData(code=INTERNAL_ERROR)`. Credencial recusada PELO SERVIÇO aparece
  hoje como "serviço fora do ar". Classificar por `codigo == INTERNAL_ERROR`
  somado ao texto da `mensagem`, e **incluir a `mensagem` em toda
  `McpIndisponivel` de protocolo** (hoje só o `code=` sobrevive). Manter o ramo
  de status HTTP com comentário dizendo que serve a outro transporte, ou
  removê-lo com nota — decida lendo, e justifique.

  **A-03** (`options_mcp_api.py:428,496,586`) — as três rotas logam
  `erro=type(e).__name__` e descartam `str(e)`. Acrescentar `detalhe=str(e)`.
  As mensagens do módulo são livres de segredo por construção (docstring
  `mcp_client.py:11-15`) — confirme isso lendo antes de logar.

  Testes em `test_mcp_client.py`: `-32000` COM `data` completo → `McpTetoAtingido`;
  `-32000` com `"Connection closed"` e sem `data` → `McpIndisponivel` (é o caso
  que hoje mente); `INTERNAL_ERROR` com mensagem de credencial → classificação
  correta; e que a mensagem do serviço chega na exceção.
  </action>
  <verify>pytest dos testes novos; `bash scripts/executar.sh --testes`</verify>
  <done>Nenhum caminho afirma teto sem a prova numérica; o log diz o motivo.</done>
</task>

<task type="auto">
  <name>Task 2 (A-04): pinar o SDK e o cliente HTTP</name>
  <files>server/requirements.txt, server/requirements-prod.txt</files>
  <action>
  `mcp>=2.1,<3` flutua e `httpx2` não tem pin (entra como transitivo). O build
  do Railway resolve na data do deploy, então produção pode rodar versão
  diferente da testada. Pinar `mcp==2.2.0`, `mcp-types==2.2.0`,
  `httpx2==2.12.0` nos DOIS manifestos, com comentário explicando o motivo
  (API diferente vira exceção genérica e sai como "sem resposta").
  ATENÇÃO: o guardião `test_opcoes_fronteira.py` confere que a linha do `mcp` é
  IGUAL nos dois arquivos — ele tem de continuar verde. Se o pin exato quebrar
  a resolução, PARE e reporte; não relaxe por conta própria.
  </action>
  <verify>`pip download --python-version 3.12 --only-binary=:all: -r server/requirements-prod.txt` resolve (produção roda 3.12); suíte verde</verify>
  <done>Versão de produção deixa de ser decidida pela data do deploy.</done>
</task>

<task type="auto">
  <name>Task 3 (A-05): token recusado é invalidado</name>
  <files>server/app/mcp_client.py, server/tests/test_mcp_client.py</files>
  <action>
  `_TOKEN` só é limpo por `reset_cache()`, que nada chama em runtime. Uma
  recusa momentânea vira falha permanente por até ~55 min. Ao classificar
  recusa pelo SERVIÇO (o caminho do A-02), limpar `_TOKEN` e tentar UMA
  renovação antes de desistir. Uma só: laço de retry contra 401 é o que o
  contrato do MCP proíbe ("nenhuma repetição transforma 401 em 200").
  Teste: primeira chamada recusa, segunda passa → o resultado chega ao
  chamador e o token foi renovado uma vez, não duas.
  </action>
  <verify>pytest dos testes novos; suíte inteira</verify>
  <done>Recusa pontual não vira indisponibilidade de uma hora.</done>
</task>
</tasks>

<success_criteria>
Commits atômicos por task, PT-BR, referenciando `auditoria A-0x`. Front NÃO é
editado (sem `vite build`). Backend-only: o SUMMARY deve lembrar que o deploy
disto é só-backend, com bump manual do `SERVER_BUILD_ID` — e que A-06
(timeout) ficou FORA do lote de propósito, porque a medição em produção
(1 a 6 s, não os 8,2 s locais) tirou a urgência.
</success_criteria>
