---
quick_id: 260910-svy
phase: quick-260910-svy
plan: 01
status: complete
achados: [A-01, A-02, A-03, A-04, A-05]
commits: [ebc963f, 460aa50, 3fed1d5]
files_modified:
  - server/app/mcp_client.py
  - server/app/options_mcp_api.py
  - server/requirements.txt
  - server/requirements-prod.txt
  - server/tests/test_mcp_client.py
  - server/tests/test_opcoes_fronteira.py
deploy: somente-backend (bump manual do SERVER_BUILD_ID)
suite: 2256 passed / 4 skipped (backend) + 126 OK / 0 falhas (web)
completed: 2026-09-10
---

# Quick 260910-svy: lote MCP da auditoria (A-01 a A-05) — Summary

Cinco achados da auditoria de 2026-09-10 no código MCP da Fase 1. Os dois
primeiros faziam o app afirmar o que não mediu (princípio 4 do CLAUDE.md):
conexão caída saía como "você atingiu o teto de 2.000 chamadas do dia", e
credencial recusada pelo serviço saía como "serviço fora do ar". Backend-only.

## Commits

| Commit | Achados | Assunto |
| --- | --- | --- |
| `ebc963f` | A-01, A-02, A-03 | classificar erro pelo que ele é, e logar o motivo |
| `460aa50` | A-04 | pin exato do SDK e do cliente HTTP |
| `3fed1d5` | A-05 | token recusado é invalidado e renovado UMA vez |

## Prova RED/GREEN do A-01

O caso que mentia: `MCPError(-32000, "Connection closed")` **sem `data`**.
O `-32000` do contrato (teto diário) é o MESMO valor do `CONNECTION_CLOSED` do
SDK (`mcp_types`, mcp 2.2.0) — conferido no SDK instalado, e agora fixado por
assert no teste.

Script único (`prova_a01.py`) rodado contra duas cópias do módulo **fora do
repo** (`$TMPDIR/red-a01/{antes,depois}/`, cada uma um pacote com `obslog.py`;
a cópia `antes` foi conferida por `git hash-object` = `306f93e1`, o blob de
`HEAD:server/app/mcp_client.py` no início — nenhum `git stash` envolvido):

```
[antes]  FALHA: -32000 sem `data` virou McpTetoAtingido (HTTP 402 'teto do dia'). data={} msg='Connection closed'
         log: ERROR [b3][mcp] teto do serviço atingido ... escopo=None chamadas_hoje=None
[depois] OK: virou McpIndisponivel — serviço de opções devolveu erro de protocolo
         (code=-32000, status=None): conexão fechada (CONNECTION_CLOSED — o MESMO
         -32000 do teto, mas sem `chamadas_hoje`/`teto` em `data`, então NÃO é
         teto): Connection closed
         log: WARNING [b3][mcp] serviço de opções falhou ... motivo=Connection closed
```

O log do "antes" é o resumo do defeito: afirmava teto e, na mesma linha,
`chamadas_hoje=None` — a contagem que ninguém mediu.

Régua nova: só é teto quando `data` é dict e traz `chamadas_hoje` **e** `teto`
numéricos (`bool` rejeitado de propósito). Falso-negativo é o lado seguro — teto
real sem os números vira 503 "tente em alguns minutos", não 402 com contagem
inventada. Coberto por `test_conexao_fechada_nao_vira_teto_mesmo_tendo_o_mesmo_32000`
e por um parametrizado de 7 formas de `data` sem prova.

## Descoberta: a correção proposta para o A-02 não era implementável

O **fato** do A-02 está certo (o ramo `if status in (401,403)` é código morto no
transporte streamable-HTTP, e por isso o log mentia). A **correção proposta** —
"classificar por `INTERNAL_ERROR` somado ao texto da `mensagem`" — não funciona:
lido `mcp/client/streamable_http.py:383-411` (mcp 2.2.0), o SDK colapsa todo
não-2xx que não seja 404 numa mensagem **constante**, `"Server returned an error
response"`. Então 401, 403, 500 e 502 chegam byte a byte idênticos. Nenhum texto
recupera informação que o texto não tem, e chamar 502 de "credencial recusada"
seria cometer o erro do A-01 em outro lugar.

O que dá para fazer é **medir**: o `AsyncClient` do `httpx2` é nosso, então um
`event_hooks={"response": [...]}` anota o status não-2xx antes de o SDK traduzir.
Conferido contra um servidor HTTP local devolvendo 401 — o hook vê o status
inclusive em resposta **streaming**, que é o modo do transporte:

```
post bufferizado: 401 hook viu: [401]
stream, dentro do ctx: 401 hook viu: [401]
```

O balde é uma `ContextVar` criada por `_chamar` antes de abrir a sessão (as
tasks-filhas do task group do SDK herdam a mesma lista). Não é slot de módulo
porque são até 4 chamadas concorrentes — seria o mesmo racy que a docstring de
`ResultadoTool` já descreve. **Status não medido fica `None` e a classificação
cai em indisponível**; um teste (`..._sem_status_medido_nao_afirma_recusa...`)
exige literalmente `status=None` na mensagem, para que ninguém volte a chutar.

## Decisão: o ramo de status HTTP FICOU

O plano deixava a escolha. Mantido, com nota no código, por três razões:

1. Ele ainda classifica a exceção levantada pelo **nosso** cliente `httpx2`
   antes de o SDK traduzir (p.ex. redirect não seguido) — caso que o hook não
   cobre porque nem chega a haver `MCPError`.
2. O teste `test_nenhuma_mensagem_de_erro_ecoa_o_segredo_nem_o_token` exercita
   esse caminho (caso "c"): removê-lo apagaria cobertura de um guardião T-waw-01.
3. O defeito do A-02 não era a existência do ramo, era ele ser a **única** porta
   para o 401. Agora não é: quem pega o 401 deste transporte é o ramo `MCPError`,
   e o ramo HTTP virou o caminho secundário (também alimentado pelo hook).

Custo de manter: três linhas e um comentário. Custo de remover: perder a
classificação certa nos dois casos acima.

## Segurança: a mensagem do serviço é entrada externa

Desde o A-02 a `message` do erro JSON-RPC viaja para a exceção e para o log.
Ela é escolhida pelo **outro lado**, então um serviço mal-comportado que ecoasse
o header `Authorization` arrastaria o nosso access token para o nosso log
(T-waw-01). `_trecho()` redige o access token e o `MCP_CLIENT_SECRET` antes de
cortar (cortar primeiro deixaria um pedaço do segredo sobrevivendo) e limita a
200 caracteres. O guardião de segredo ganhou o caso "d", com uma mensagem de
serviço que ecoa token e segredo: ele exige `[redigido]` e a ausência dos dois.

O A-03 (`detalhe=str(e)` nas três rotas) foi aplicado **depois** de ler as
mensagens de cada exceção do módulo e confirmar que nenhuma carrega segredo.

## A-04: pin, e o guardião que precisou ser apertado

`mcp==2.2.0` e `httpx2==2.12.0` (linha nova — o SDK só pede `httpx2>=2.5.0`,
então o stack que de fato fala com o serviço entrava flutuante) nos DOIS
manifestos, idênticos.

**`mcp-types` NÃO ganhou linha**, divergindo da letra do plano: os metadados do
próprio `mcp==2.2.0` exigem `mcp-types==2.2.0` com `==` (conferido na venv e na
resolução). A linha extra não prenderia nada que já não esteja preso, e
colidiria com o filtro do guardião, que conta linhas começando por `"mcp"`.
Não é afrouxamento — `mcp-types` segue travado em 2.2.0 exato.

Resolução conferida para **3.12** (o que produção roda; a venv local é 3.14):
`pip download --python-version 3.12 --only-binary=:all: -r requirements-prod.txt`
baixou 42 wheels, entre elas `mcp-2.2.0`, `mcp_types-2.2.0`, `httpx2-2.12.0`.
O pin exato **não** quebrou a resolução, então não houve o motivo previsto para
parar.

O guardião `test_guardiao_b_mcp_esta_nos_requirements_e_igual_nos_dois` media a
faixa por texto (`">=2.1" in linha`) e por isso **reprovava o pin exato** —
conferido: `assert ('>=2.1' in 'mcp==2.2.0')`. Foi **apertado, não apagado**
(guardrail do CLAUDE.md), com nota datada no docstring: a propriedade protegida
é a mesma (uma linha só, idêntica nos dois arquivos, versão dentro da faixa que
o contrato nomeia), só que agora verificada sobre a VERSÃO e exigindo `==` —
faixa é justamente o defeito do A-04. Vale para `mcp` e `httpx2`, com nome de
pacote casado exatamente (`mcp` não casa `mcp-types`). Contra-prova rodada:
revertendo os dois arquivos para `mcp>=2.1,<3` o guardião reprova com
"`mcp` voltou a ser faixa em vez de pin exato"; os arquivos foram restaurados
com `git checkout --` dos caminhos.

Fora de escopo, registrado: o resto da árvore transitiva (`anyio`, `httpcore2`,
`jsonschema`, `pydantic_core`...) segue flutuante. Reprodutibilidade total pede
lockfile, que o repo não tem por decisão anterior — este lote fecha só os dois
nomes do achado.

## A-05: uma renovação, não um laço

`_recusa_do_servico` limpa `_TOKEN` e tenta **uma** renovação quando o 401/403
do serviço foi medido. Uma só, porque o contrato é explícito ("nenhuma repetição
transforma 401 em 200"): a renovação cobre o token velho/errado em mãos; se o
novo também é recusado, a causa é configuração e repetir queima chamada do teto
compartilhado. Os testes medem o limite pelos POSTs ao emissor: recusa
persistente para em 2 (emissão + 1 renovação) e 2 tentativas ao serviço.

## Desvio de processo

A-05 foi implementado junto com A-02 na primeira passada (o gatilho do A-05 é a
classificação do A-02). Para cumprir "um commit por task", os commits locais —
ainda não publicados — foram re-divididos: `git reset` misto para a base e três
commits refeitos, com o estado intermediário (sem A-05) exercitado pela suíte
antes do commit 1. O estado final dos arquivos foi conferido idêntico ao que
havia sido testado (`diff` contra cópia salva). Nenhum commit publicado foi
reescrito; nenhuma deleção de arquivo nos três commits.

## Validação

- `bash scripts/executar.sh --testes` (suíte canônica, as DUAS metades):
  **2256 passed, 4 skipped** (backend, pytest) + **126 OK / 0 falhas** (web).
  Rodado após cada task.
- `tests/test_mcp_client.py`: 28 testes (eram 13), todos verdes.
- Guardiões `test_mcp_guardioes.py` e `test_opcoes_fronteira.py`: verdes.
- Front **não** foi editado — sem `vite build`, como o plano manda.
- A suíte precisa rodar fora do sandbox (o `mktemp -d` dos logs do web e o
  `load_verify_locations` do pip tomam `PermissionError` dentro dele).

## Limitações conhecidas

- Nada aqui foi exercitado **contra o serviço real**. O 401 do serviço é
  reproduzido por duble que chama o hook de verdade; o caminho ao vivo é o
  `test_mcp_vivo.py` (opt-in, exige `MCP_CLIENT_SECRET`) e não foi rodado.
- A falha de produção que motivou a auditoria não foi diagnosticada — este lote
  tira a cegueira (log com status e motivo) para que a próxima ocorrência diga
  qual é a causa.
- A-06 (timeout do front, `web/src/api.js`) ficou **fora do lote de propósito**:
  a medição em produção (1 a 6 s, não os 8,2 s locais) tirou a urgência.

## Deploy

**SÓ-BACKEND.** Nada em `web/` ou `web-admin/` mudou, então não há
`bump.sh`/`publicar-web.sh` envolvido. Deploy só-backend exige **bump manual do
`SERVER_BUILD_ID`** (memória `deploy-backend-carimbo`), senão o carimbo de build
não muda e não há como distinguir no ar o que está rodando.

Depois do deploy, o que observar no obslog (`cat=mcp`): linhas
`serviço de opções falhou` passam a trazer `status=` e `motivo=`, e
`credencial recusada pelo serviço` aparece quando o 401 é do serviço — antes
qualquer um dos dois era "serviço fora do ar" ou, pior, "teto atingido".

## Self-Check: PASSED

Os 6 arquivos modificados existem em disco; os 3 commits (`ebc963f`, `460aa50`,
`3fed1d5`) existem em `git log`; nenhuma deleção de arquivo entre a base
`0139a52` e `HEAD`; árvore limpa a menos deste SUMMARY, que por instrução fica
para o commit de docs do orquestrador (SUMMARY/STATE/PLAN não entram aqui).
