# Plano: fonte de cotações selecionável (Yahoo + brapi.dev), operando a dois

Prompt para Claude Code no repositório `b3-agente` (Boris+). Alvo desta rodada é
um **plano aprovável**, não código em produção.

## Premissas assumidas

1. O "material a seguir" citado no pedido original não chegou. O contrato da
   brapi vem da documentação viva (`https://brapi.dev/docs`, endpoints de quote e
   de lista, planos e limites), consultada nesta sessão e citada com URL e data.
2. "Operar a dois" significa os dois provedores **ativos ao mesmo tempo** —
   primário com reserva automática, cross-check ou divisão por timeframe —, não
   uma chave manual que alguém vira no deploy.
3. O ADR-001 fixou orçamento **US$ 0** para dado intraday, e é por isso que a
   brapi Pro ficou como plano B documentado e não implementado. Implementar a
   brapi agora revisa essa restrição: o plano declara o custo mensal e diz quem
   aprova.
4. A prioridade corrente do produto é a submissão na App Store. Nada deste plano
   entra na branch de lançamento sem aprovação explícita do Alex.

Se alguma premissa estiver errada, diga em uma frase e siga com a leitura mais
razoável.

## Entregável

Dois documentos, nenhuma mudança de comportamento em produção:

| Arquivo | Conteúdo |
|---|---|
| `docs/adr/0NN-fonte-de-cotacoes-selecionavel.md` | ADR novo (ou emenda datada ao ADR-001, se a decisão for só revisar a restrição de orçamento): contexto, decisão, alternativas descartadas com o porquê, gatilho de acionamento, consequências, custo mensal |
| `qa/NN-plano-fonte-de-cotacoes.md` | Plano em fases; cada fase lista arquivos tocados, teste que a prova e o comando exato que roda |

Código de produção: nenhum nesta rodada. Se uma fase precisar de código para ser
crível, entregue o diff **proposto dentro do plano**. Um spike descartável fora
da árvore de produção (`/tmp` ou o scratchpad) é bem-vindo para provar o payload
real da brapi — o resultado dele entra no plano como evidência, não como commit.

## Terreno já verificado (não re-descubra)

| Fato | Onde |
|---|---|
| A interface de provedor de candles **já existe**, com registry e injeção para teste | `server/app/candle_provider.py:110-186` (`CandleProvider`, `_PROVEDORES`, `get_provider`, `set_provider`) |
| `BrapiProvider` existe como stub que falha alto de propósito, citando o que falta | `server/app/candle_provider.py:136-157` |
| A seleção hoje é a env `B3_CANDLE_PROVIDER`, default `yahoo`, memoizada | `server/app/candle_provider.py:163-178` |
| A instrumentação (latência, taxa de falha, `alerta`) vive na fronteira e é **global**, não por provedor | `server/app/candle_provider.py:37-105`, exposta em `main.py:410` |
| Candles passam pelo ponto único; **cotação spot não** — `main.py` e `options_api.py` importam `yahoo` direto | `server/app/main.py:529, 568, 592, 908`; `server/app/options_api.py:40, 100-146` |
| O cache de candles indexa por `(symbol, interval)` e persiste em SQLite (L2) — o provedor não entra na chave | `server/app/candle_cache.py:117-119, 54-82` |
| A brapi **já é usada** para fundamentos, com `token` opcional no client HTTP | `server/app/fundamentals.py:46-48, 301-346` |
| `BRAPI_TOKEN` é citado em três lugares e não é lido em lugar nenhum ainda | `candle_provider.py:141,153`; `server/tests/test_candle_provider.py:75` |
| Os testes do provedor já travam o contrato, inclusive a mensagem do plano B e o gatilho numérico | `server/tests/test_candle_provider.py` |
| A decisão original, o gatilho e a medição que a sustenta | `docs/adr/001-fonte-de-dados-intraday.md` (Decisão 1 e § Consequências), `docs/MEDICAO-Yahoo-Intraday-2026-07-30.md` |

## Decisões que o plano fecha

Decida cada uma e registre a escolha com o trade-off em uma linha. Estas são
para resolver no documento, não para devolver ao Alex como pergunta aberta.

1. **Escopo de "cotações".** Candles (interface pronta), quote spot (`/api/quotes`,
   `/api/ativo/*`, sem interface), fundamentos (já brapi) e opções (Yahoo, com
   provider próprio) são quatro superfícies distintas. Diga quais entram na v1 e
   quais ficam fora.
2. **Onde mora a seleção.** Env por ambiente, config do servidor por conta, ou
   escolha do usuário na UI. Se for campo em `agent.*`, ele exige os três lugares
   de sempre (`agent_params`, `set_agent`, `SERVER_KEYS`) e sync explícito
   device→servidor no `deviceStore`.
3. **Identidade da fonte no cache.** Duas séries de origens diferentes sob a
   mesma chave se misturam, e o L2 sobrevive ao deploy. Diga como a chave, a
   invalidação e o `snapshotId` passam a distinguir a fonte.
4. **A forma de "operar a dois".** Failover automático (com qual gatilho —
   reusar `taxaFalha`/`alerta` ou um novo), cross-check de preço, ou divisão por
   intervalo. Se houver failover, diga como se volta ao primário.
5. **Divergência entre fontes.** Yahoo atrasa ~15 min medidos; a brapi Pro
   anuncia ~5 min. Qual fonte manda no número que a UI afirma, e como a camada
   didática declara a origem e a idade do dado — a regra vigente é que fonte
   indisponível se declara, não se estima.
6. **Instrumentação por provedor.** O `snapshot()` global perde sentido com dois
   provedores ativos: o gatilho do plano B mediria a média dos dois. Diga como
   fica.
7. **Cota e custo real.** Confirme na doc: requisições por mês, tickers por
   requisição, intervalos disponíveis, atraso, o que exige token. Cruze com o
   volume do Radar (universo × passadas por pregão) e diga a folga em % da cota.
8. **Segredo e ambiente.** `BRAPI_TOKEN` é variável de ambiente por ambiente no
   Railway, nunca no bundle do front. Diga o que acontece quando falta.
9. **Rollback.** Como voltar 100% ao Yahoo, e se isso exige deploy.

## Critério de aceite

- O ADR e o plano existem, com data e status, e o plano tem fase, arquivos,
  teste e comando por fase.
- Toda afirmação sobre a brapi tem URL e data de consulta ao lado, e diz o que
  foi confirmado. Onde a doc não responde, o plano diz "não confirmado" e propõe
  o spike que confirma.
- As nove decisões acima aparecem resolvidas, com o trade-off em uma linha cada.
- O plano cita a suíte canônica `bash scripts/executar.sh --testes` (são duas
  suítes: pytest e `web/tests/*.mjs`) como porta de saída de cada fase, e nomeia
  os testes novos que cada fase adiciona.
- Os guardrails de sempre aparecem onde tocam: paridade byte a byte
  `server/app/defaults.py` ↔ `web/src/catalog.js`, paridade `deviceStore` ↔
  `serverStore` em `web/src/persistence.js`, `scripts/bump.sh` antes de publicar,
  `npx vite build` depois de editar front.
- O custo mensal em reais aparece explícito, com a comparação contra o que o
  ADR-001 decidiu.

## Como trabalhar

Leia antes de propor: o ADR-001 inteiro, `candle_provider.py`, `candle_cache.py`,
as rotas de cotação e histórico em `main.py`, `fundamentals.py:290-350` e
`server/tests/test_candle_provider.py`. Consulte a documentação da brapi na
fonte. Entregue no escopo pedido — plano e ADR — e decida sozinho o rotineiro.

Delegue no máximo dois subagentes: um para varrer o repositório em busca de
acoplamentos ao Yahoo que a tabela acima não listou, outro para ler a
documentação externa. O resto faça direto.

## Fora de escopo nesta rodada

- Substituir a exceção do `BrapiProvider` por uma implementação que não foi
  exercitada contra a API real.
- Remover o gatilho do plano B ou a instrumentação da fronteira. Se a decisão
  mudar o gatilho, ele é atualizado com nota — guardião não se apaga.
- Trocar o bundle id, renomear `b3-agente`, `B3_*` ou as chaves `b3-*`.
- Commitar token, chave ou `.env`.
- Editar `server/web_dist` ou publicar.
- Declarar baseline verde tendo rodado só `scripts/test.sh`.
