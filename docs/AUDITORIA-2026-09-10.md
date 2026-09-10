# Auditoria completa — Boris+ (b3-agente) — 2026-09-10

**Escopo:** projeto inteiro, não diff. Branch `v2/interacao-estrutural` (Fase 2 da
aba Opções mesclada, PR #39 aberto; Fase 1 já em produção).
**Método:** 4 finders em paralelo + verificação adversarial dos achados
crítico/alto por agentes independentes, com instrução de refutar em caso de
dúvida. Nenhuma correção foi aplicada.
**Pedido de origem:** "a aba de Opções segue sem funcionar" + review geral.

---

## 1. Sumário executivo

A suíte roda verde (2239 pytest, 126 web, `vite build` ok), a segurança não tem
achado crítico e não há segredo versionado em todo o histórico. Ainda assim, o
achado mais grave é anterior a tudo que esta sessão construiu: **a rota
principal de compra aceita quantidade negativa e executa a ordem**, provado
chamando o endpoint real. A validação existe na venda e na compra de opção; só
a compra de ação ficou de fora, e nenhum teste cobria o caso.

Os três achados "críticos" de concorrência na carteira foram **refutados** por
reprodução: um processo, um event loop e seções críticas sem ponto de espera já
serializam tudo. Sobram dois defeitos no código MCP escrito nesta sessão, ambos
reproduzidos, que fazem o app afirmar o que não mediu — o que o princípio 4
proíbe. A falha da aba em produção continua sem causa provada; o teste decisivo
é uma linha de log que já existe e ninguém leu.

---

## 2. Achados confirmados

### A-00 · CRÍTICO · `server/app/main.py:2091` — compra aceita quantidade negativa
A rota principal de compra não rejeita `qty` negativo ou zero: o valor é
coagido silenciosamente e a ordem **executa**.
**Reproduzido com o endpoint real:**
```
POST /api/buy {"t":"PETR4","qty":-500}
→ 200 OK, positions:[{"t":"PETR4","qty":100,"avg":30.0}], caixa −R$ 3.000
```
A mesma validação **existe** em `/api/sell` (regressão F10-20260819, com
teste) e em `/api/options/buy:2298`. Só a compra de ação ficou de fora, e
nenhum teste da suíte envia quantidade negativa para ela.
**Impacto:** entrada inválida vira operação real na carteira, sem rejeição
registrada. Contraria o modelo de ordem do CLAUDE.md, onde uma ordem ou
executa inteira ou é rejeitada com motivo.
**Correção:** guarda `qty <= 0` antes de normalizar, espelhando
`/api/options/buy`, mais o teste equivalente ao que já existe para a venda.

### A-00b · ALTO · `server/app/main.py:2091` — quantidade não numérica vaza exceção
`POST /api/buy {"qty":"abc"}` devolve **500** com o texto cru da exceção
Python no corpo, em vez do 400 "Quantidade inválida." que a venda já garante
para a mesma entrada. **Reproduzido.**
**Correção:** capturar `TypeError`/`ValueError` no parse e levantar 400.

### A-01 · ALTO · `server/app/mcp_client.py:64` — código de teto colide com o do SDK
`CODIGO_TETO = -32000` é o mesmo valor de `CONNECTION_CLOSED` do SDK
(`mcp/shared/jsonrpc_dispatcher.py`). **Reproduzido:** `MCPError(-32000,
"Connection closed")` → `McpTetoAtingido` → HTTP 402 "atingiu o teto de
chamadas do dia".
**Impacto:** uma conexão caída faz o app afirmar um número de consumo que
ninguém mediu, e manda o usuário esperar até a meia-noite sem motivo. Viola o
princípio 4 (nunca inventar valor) e o 9 (estado correto).
**Correção:** só tratar como teto quando `data` for dict e trouxer
`teto`/`chamadas_hoje`; `"Connection closed"` cai em `McpIndisponivel`.

### A-02 · ALTO · `server/app/mcp_client.py:341-347` — ramo morto faz o log mentir
`if status in (401, 403)` nunca dispara no transporte streamable-HTTP: o SDK
converte qualquer não-2xx em `ErrorData(code=INTERNAL_ERROR)`
(`mcp/client/streamable_http.py:383-410`). **Reproduzido.**
**Impacto:** credencial recusada **pelo serviço** (audiência errada, client
fora da allowlist) é registrada como "serviço fora do ar". O diagnóstico da
falha atual foi travado por isso.
**Correção:** detectar por `codigo == INTERNAL_ERROR` e incluir a `mensagem`
em toda `McpIndisponivel` de protocolo.

### A-03 · ALTO · `server/app/options_mcp_api.py:428,496,586` — log sem a mensagem
As três rotas gravam `erro=type(e).__name__` e descartam `str(e)`. As
mensagens do módulo são livres de segredo por construção (docstring
`mcp_client.py:11-15`), então logá-las é seguro.
**Impacto:** perde o que separa "emissor recusou" de "erro de conexão" de
"status 502" de "erro de protocolo". Diagnóstico dedutivo em vez de imediato.
**Correção:** acrescentar `detalhe=str(e)` nas três chamadas.

### A-04 · ALTO · `server/requirements.txt:8` — pin flutuante do SDK
`mcp>=2.1,<3`, e `httpx2` sem pin nenhum (entra como transitivo). O build do
Railway resolve na data do deploy.
**Impacto:** produção pode estar com versão diferente da testada (2.2.0). Uma
mudança de API vira exceção genérica dentro do `try` e sai como "sem resposta"
— o desempacotamento de tupla em `mcp_client.py:319` é exatamente essa
armadilha.
**Correção:** pinar `mcp==2.2.0`, `mcp-types==2.2.0`, `httpx2==2.12.0` nos
dois manifestos.

### A-05 · ALTO · `server/app/mcp_client.py:209` — token recusado nunca é invalidado
`_TOKEN` só é limpo por `reset_cache()`, que nada chama em runtime.
**Impacto:** uma recusa momentânea vira falha permanente por até ~55 minutos.
Explica "falha sempre, sem intermitência".
**Correção:** ao classificar recusa do serviço, limpar `_TOKEN` e tentar uma
renovação.

### A-06 · ALTO · `web/src/api.js:321` — o tempo limite não fecha a conta
A rota de leitura faz até 3 chamadas MCP **seriais**, cada uma abrindo sessão
nova (token + `initialize` + tool). Medido: 8,2 s por chamada. O front desiste
em 30 s.
**Impacto:** a Fase 2 pode nunca completar em produção, mesmo com a credencial
resolvida.
**Correção:** subir o tempo limite dessa rota para 90 s, ou reusar uma sessão
para as três tools.

### A-07 · MÉDIO-ALTO · `server/app/metering.py:146-213` — cota de IA estoura sob concorrência
`check()` não reserva; `consume()` só roda após a resposta do modelo, que
espera até 60 s. **Reproduzido:**
```
estado inicial: used=4 quota=5
três requisições concorrentes passam na checagem
estado final: used=7 quota=5  ESTOUROU
```
**Impacto:** a cota gerenciada usa a chave paga do servidor — o excesso é
gasto real. O mesmo buraco existe no teto global.
**Correção:** reservar dentro de `check()` sob trava e devolver em caso de
falha, em vez de descontar só no sucesso.

### A-08 · MÉDIO · `server/app/agent.py:953-968` — o agente anuncia venda que não houve
O ciclo conta `executed += 1`, chama `_bump_ops` e emite evento `kind:"buy"`
mesmo quando `pnl is None` (posição já vendida por outro caminho).
**Reproduzido** com ciclo e venda manual concorrentes.
**Impacto:** o Diário registra uma venda que não aconteceu, o push dispara
"Proteção simulada: PETR4 vendido", e o teto diário de operações é consumido
por uma operação inexistente. Nenhum número de carteira é afetado. Viola o
princípio 9.
**Correção:** condicionar evento, `executed` e `_bump_ops` a `pnl is not None`.
**Nota:** `ORDER_LOCK` **não** é a correção — o ciclo teria de segurar a trava
atravessando espera de rede, o que o próprio repositório proíbe.

### A-09 · BAIXO · `server/app/main.py:2346` — venda de opção que falhou responde 200
`sell_option` devolvendo `None` (posição já vendida) vira HTTP 200 com
`priceUsed`. A rota de ação faz o oposto e levanta 400, com comentário
dizendo que era "a única exceção silenciosa". Opções ficou de fora.
**Correção:** levantar 400 quando o retorno for `None`, espelhando `/api/sell`.

### A-10 · BAIXO · `server/app/candle_provider.py:61` e `scan_deep.py:29` — fuso pendente
Usam o dia local (UTC em produção) como chave de "hoje". Ficaram fora da
correção de fuso de 2026-09-09. Entre 21:00 e 23:59 BRT o dia vira adiantado,
distorcendo a janela de observabilidade e o cache.

### A-11 · BAIXO · `server/app/brapi_budget.py:139-160` — orçamento sem trava (inerte)
Não tem trava, ao contrário do módulo irmão que resolveu essa classe de bug.
**Verificação derrubou a consequência:** 50 chamadas concorrentes, zero
corrupção, porque não há ponto de espera entre a checagem e o débito. Só
quebra com pausa artificial que o código não tem. Dívida de padrão, não
defeito.

### A-12 · MÉDIO · `server/app/rbac.py:124-126` — bootstrap do primeiro administrador
Sem `B3_ADMIN_EMAILS`, a primeira conta a se registrar num banco vazio vira
administradora. Em produção não é explorável (lista configurada, contas
existentes). O risco é um ambiente novo de preview subir sem ela.

### A-13 · MÉDIO · guardião de permissões cego a rotas de router
`test_adr013_cobertura_rotas.py` varre `app.routes` procurando `.path`, mas o
FastAPI 0.141 insere `_IncludedRouter` com `.path is None`. **7 rotas
invisíveis**: 4 em `/api/options/*` (sem guardião substituto) e 3 em
`/api/options/mcp/*` (cobertas por `test_mcp_guardioes.py`).

### A-14 · MÉDIA · `web/tests/test_fase3_paridade_stores_generica.mjs:4-5` — paridade só de nome
O guardião confere que os dois stores têm os mesmos métodos (70/70, zero
assimetria) e passa. O que ele **não** cobre é paridade de comportamento: 24
dos 70 métodos não têm nenhum teste pontual, entre eles os que **escrevem
estado** (`putSkill`, `putProfile`, `putSnapshot`, `putLlmPrompts`,
`optionsBuy`, `optionsSell`, `restoreSkill`). É a mesma classe de método que
causou os dois incidentes citados no próprio arquivo. O comentário ainda diz
"58 métodos", número de outra época.

### A-15 · MÉDIA · `docs/adr/008-fonte-de-cotacoes-selecionavel.md` — ADR sem nota de sucessão
O ADR-008 descreve a fonte de cotações master de um jeito que o ADR-020 depois
mudou. O ADR-020 documenta a mudança; o ADR-008 não aponta para frente. Quem
ler só o 008 tira conclusão errada sobre o sistema atual.
**Correção:** uma linha de Status no topo apontando para o ADR-020, sem tocar
o corpo — prática normal de ADR, não colide com o guardrail de histórico.

### A-16 · BAIXA · dois comentários que mentem sobre o código
`technical_snapshot.py:32` descreve a chave do cache como par quando ela é
tripla desde o ADR-001. `docs/adr/001` mantém marcado como pendente um item
que já está implementado no carimbo de barra da interface.

### A-17 · ALTA · `server/tests/test_adr013_cobertura_rotas.py:59` — provado cego por reintrodução
Confirmação forte do A-13. O auditor **removeu o `require_user` da rota de
status do MCP** e rodou o guardião: ele **passou**, sem detectar. O guardião
irmão da Fase 1 falhou corretamente no mesmo cenário, nomeando a rota. Ou
seja: hoje é possível publicar uma rota de opções sem exigir sessão e nenhum
teste do ADR-013 reclama.
**Correção:** trocar a varredura de `app.routes` pela versão recursiva que já
existe em `test_mcp_guardioes.py` e resolve o router aninhado.

### A-18 · MÉDIA · `server/tests/test_fase3_gate_plano.py:210` — filtro de comentário incompleto
O helper que "remove comentários" antes de contar ocorrências só descarta a
linha que **começa** com `#`. Comentário no fim da linha sobrevive.
**Provado:** o auditor removeu a única chamada real ao gate comercial de
análises e deixou no lugar uma linha de código com o nome da função num
comentário de cauda. A asserção de contagem continuou passando — um bypass do
gate que o próprio modelo de ameaças existe para impedir.
Mitigado hoje pelos testes de comportamento no mesmo arquivo, e o helper está
duplicado em três arquivos que podem divergir.
**Correção:** cortar a linha no primeiro `#` antes de contar, e extrair o
helper para um módulo único.

### A-19 · BAIXA · três guardiões de front contam sobre o fonte bruto
`test_status_mercado_ui.mjs:44`, `test_disclaimer_trade_modal.mjs:35` e
`test_fase21_dedup_consolidacao.mjs:56` contam ocorrências sem remover
comentários, então um comentário citando o mesmo texto infla a contagem. Todos
têm asserção companheira que pega a regressão real, e pelo menos oito outros
arquivos do repositório já implementam a remoção corretamente.

**Sem achado, verificado e não apenas não procurado:** nenhuma asserção
trivial (`assert True`, comparação de algo consigo mesmo) nas 286 suítes;
nenhum teste sem asserção depois de inspeção manual dos candidatos; nenhum
guardião cuja âncora tenha parado de casar hoje — os três acima são risco sob
regressão futura, não vacuidade atual.

**Sem achado:** zero `TODO`/`FIXME` reais no código; zero dependência
declarada e não usada nos dois lados; paridade de prompts entre servidor e
front confere byte a byte e cobre tudo que existe hoje; dois ganchos sem
chamador em `plan.py` são deliberados e documentados como tal.

---

## 3. Refutados / descartados (com evidência)

| Achado alegado | Veredito | Por quê |
|---|---|---|
| `/api/options/buy` sem trava → double-spend | **REFUTADO** | Rota `async def`, nenhum ponto de espera entre ler o caixa e escrever; 1 processo, nenhuma rota síncrona no caminho de ordem. Reproduzido: 3 compras concorrentes → 1 executa, caixa correto. |
| `/api/options/sell` sem trava → venda dupla | **REFUTADO** | Mesma defesa; reproduzido com 4 vendas concorrentes → 1 executa. |
| Ciclo do agente sem trava → escrita concorrente | **PARCIAL** | O fato é verdade, a consequência não: `store.sell` relê o estado e devolve `None`. O defeito real é outro (A-08). |
| Cabeçalho de autorização perdido com token em cache | **DESCARTADO** | `_HTTP` nunca volta a `None` e o SDK não fecha cliente fornecido. |
| Pacote MCP não instalado em produção | **DESCARTADO** | `httpx2` só existe como transitivo do `mcp`; ausência produziria "não configurado", e a tela diz "sem resposta". |
| Segredo versionado no repositório | **NÃO ENCONTRADO** | Histórico completo varrido; único achado é chave falsa de fixture. |

---

## 4. Cobertura declarada

**Rodou:** correção e concorrência do backend; segurança (segredos, injeção,
autorização, CORS, IDOR, dependências do front); cliente MCP e rota de opções
linha a linha com reprodução; suíte canônica e build executados de verdade.

**NÃO rodou, e por quê:**
- Vulnerabilidade de dependências **Python**: `pip-audit` não instalado e o
  cache local barrou `pip list --outdated`. Não foi possível confirmar nem
  descartar CVE nos pins.
- Front além do que os guardiões estáticos cobrem: não há automação de
  navegador no projeto, por decisão do ADR-018.
- **Ambiente de produção**: nenhum comando foi executado contra o Railway.
  Tudo sobre produção neste relatório é inferência a partir de respostas HTTP
  públicas.
- Dívida e guardiões vazios: parte ainda em execução quando este relatório foi
  fechado; será anexada.

**Premissa não verificável daqui:** se o Railway injetar `WEB_CONCURRENCY > 1`,
o uvicorn sobe múltiplos processos e a defesa do event loop cai **para as
quatro rotas de ordem**, não só as de opções. Conferir no painel.

---

## 5. Próximos passos (priorizados)

0. **Corrigir A-00 primeiro** — a compra aceitar quantidade negativa é o único
   achado que move dinheiro na carteira sem passar por rejeição, e a correção
   é uma guarda de duas linhas mais o teste que já existe na venda.
1. **Descobrir a causa da falha da aba** com o log que já existe:
   `railway logs | grep -F "[b3][mcp]"`. O campo `erro=` separa credencial
   recusada de indisponibilidade. Sem isso, qualquer correção é chute.
2. **Corrigir A-01 a A-06 num lote** — são todos do código MCP da Fase 1, e
   três deles (A-02, A-03, A-04) atacam justamente a cegueira que está
   travando o diagnóstico. A-06 é pré-requisito para a Fase 2 funcionar.
3. **Corrigir A-07 e A-08** — os dois únicos achados com consequência fora do
   MCP: dinheiro real da chave gerenciada, e o app afirmando uma venda que não
   aconteceu.
