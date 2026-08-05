# CHECKOUT — Camada de entendimento do BolsIA (didática + assistente)

Documento de trabalho para sessões novas do Claude Code neste repositório.
Objetivo, fatos verificados, decisões fechadas, fases com critério de aceite,
e o que fica fora.

> Substitui a versão anterior deste arquivo (escopo só-Estudo, só primeira
> vez). O que mudou: explicação passa a ser acessível em qualquer tela e a
> qualquer momento, ancorada nos dados reais em exibição, e ganha um assistente
> de IA que lê o contexto da tela.

---

## Objetivo

Que uma pessoa sem experiência entenda o mercado **através do uso do app**, e
não em paralelo a ele: cada número que a tela afirma tem uma explicação
alcançável ali mesmo, feita com aquele dado, e há um assistente que responde
"por que isso está assim?" olhando a mesma tela que ela.

O produto atende dois mundos ao mesmo tempo — ensina quem está chegando e
opera para quem já sabe. A camada de entendimento é o que faz o primeiro mundo
existir sem estorvar o segundo.

**Segurança e fluidez são requisitos, não adornos.** Segurança: nada que a
camada diga vira recomendação de investimento, e nenhum número é inventado.
Fluidez: a explicação chega sem tirar a pessoa do fluxo, e sem custo de LLM por
padrão.

O caso que originou isto: o card diz "◔ PLANO ARMADO · a 0,9R do gatilho".
Quem nunca operou não sabe o que é gatilho, o que acontece quando é atingido,
nem o que "0,9R" significa.

---

## Fatos verificados no código (2026-08-05)

Levantados nesta base. Confira antes de contrariar; não precisa redescobrir.

| Fato | Onde |
|---|---|
| Modo é `config.appMode` ∈ `estudo` \| `operador` | `defaults.py`, uso amplo em `App.jsx` |
| Já existe flag de primeira vez persistida em config (`tourSeen`) | [App.jsx:5342](web/src/App.jsx:5342) |
| Já existe nível declarado do usuário: `profile.experiencia` ∈ `iniciante` \| `intermediario` \| `avancado` | [defaults.py:234](server/app/defaults.py:234) |
| Vocabulário por modo (Estudo sem verbo de ordem) é canônico no backend | `skill_ref.vocab` [skill_ref.py:217](server/app/skill_ref.py:217) |
| Frases de estado do timing já vêm prontas do servidor | `skill_ref.TIMING` + `timing.montar` |
| Princípio 1 ("o backend calcula; a LLM interpreta") e a variante sem pacote | [skill_ref.py:38](server/app/skill_ref.py:38), [skill_ref.py:121](server/app/skill_ref.py:121) |
| Camada LLM pronta: chamada multi-provedor, erro público, uso/custo | `llm._call_llm`, `llm.public_error`, `llm.collect_usage` |
| Montagem **cache-aware** do system já existe, com mínimo por modelo | `llm._system_cacheavel` + `_CACHE_MIN` [llm.py:315](server/app/llm.py:315) |
| Parâmetros por modelo saem do catálogo (evita `temperature` em modelo que raciocina) | `llm._params_efetivos` + `model_catalog` |
| Custo por chamada é registrado e tem snapshot por escopo | `ai_activity.registrar`, `ai_activity.snapshot` |
| Snapshot técnico tem identidade rastreável (`snapshotId`) | `technical_snapshot`, exposto em `/api/technicals` |
| Guia por área existe, mas em tela separada | `ajudaSecoes()` [App.jsx:1881](web/src/App.jsx:1881) |
| Paridade obrigatória entre `deviceStore` e `serverStore` | `web/src/persistence.js` |
| Front do iOS só muda com build; backend vale no deploy | `TESTFLIGHT.md`, `scripts/publicar-web.sh` |

**A lacuna real:** há didática para o que a LLM escreve e nenhuma para o que o
app afirma sozinho. Timing, confluência, R, fundamento e vencimento são
determinísticos — nenhuma LLM os produziu, então nenhuma LLM os explica.

---

## Decisões fechadas

Implemente sobre elas. Se discordar de alguma, diga em uma frase e siga.

1. **Público de referência: iniciante absoluto.** O texto assume que a pessoa
   não sabe o que é uma vela de 15 minutos. `profile.experiencia` gradua a
   profundidade; não cria conteúdo separado.
2. **Duas vias de acesso, sempre.** (a) *Proativa*: a explicação de um conceito
   aparece sozinha na primeira vez que ele surge na tela. (b) *Permanente*:
   depois disso continua alcançável em um toque, no mesmo lugar. A primeira
   vez é um empurrão, não a única porta.
3. **Ancorada no dado em exibição.** A explicação usa os números daquele card
   naquele instante. "Gatilho" explica o gatilho daquele ativo, naquele preço.
4. **Duas camadas com custos diferentes:**
   - **Determinística (padrão, sem custo):** catálogo de conceitos servido pelo
     backend, como `skill_ref.TIMING` já faz. Cobre o "o que é isto".
   - **Assistente de IA (sob demanda, com custo):** responde pergunta livre
     sobre a tela atual. Cobre o "por que isto está assim, no meu caso".
5. **O assistente recebe um snapshot estruturado, não a tela.** O front envia o
   view-model que já usou para renderizar (com `snapshotId` quando houver);
   nada de raspar DOM nem de reenviar texto livre como instrução.
6. **Mesma lei de vocabulário.** O assistente obedece `skill_ref.vocab` e os
   princípios: no Estudo descreve condição, sem verbo de ordem; nunca inventa
   número; sem pacote técnico, não cita indicador que exigiria fonte ausente.
7. **Modo Operador intacto.** Sem camada didática proativa e sem mudança de
   payload. O assistente pode existir no Operador, com o vocabulário de mesa.
8. **Desligável em produção sem deploy de app** (ver Guardrails).

---

## Guardrails

O que impede esta camada de virar um problema.

**Isolamento do Operador.** Guardião automatizado prova que a resposta em
`modo=operador` é idêntica à de hoje. Inspeção visual não conta.

**Chave de desligamento.** Um flag no backend desliga (a) a camada didática e
(b) o assistente, de forma independente, sem rebuild do app. Se algo sair
errado em produção, o caminho de volta é uma variável, não um deploy de iOS.

**Teto de custo.** O assistente respeita um limite por escopo e por dia,
usando o registro que `ai_activity` já mantém. Ao atingir o teto, a resposta é
uma mensagem clara — a camada determinística continua funcionando.

**Conteúdo de tela é dado, não instrução.** O snapshot entra no lugar de dados
da mensagem. Texto vindo de análise anterior da LLM, nome de ativo ou campo
editável pelo usuário não altera as regras do assistente. Instrução de operador
que precise chegar no meio da conversa vai como mensagem `{"role": "system"}`
dentro de `messages[]` — canal não falsificável, e preserva o prefixo cacheado
(disponível em `claude-opus-5` e `claude-opus-4-8`; no `claude-sonnet-5` use
`system` de topo).

**Sem promessa de resultado.** Os disclaimers de `web/src/disclaimers.js` valem
para a camada nova; o assistente não escapa deles por ser conversa.

---

## Desenho do assistente (seção de API)

Aplica-se à Fase 4. Reusa a camada LLM existente em vez de criar uma paralela.

**Montagem cache-aware.** O prefixo estável — princípios, vocabulário do modo,
catálogo de conceitos — vai primeiro e passa por `llm._system_cacheavel`, que
já respeita o mínimo por modelo (512 tokens no `claude-opus-5`, 1024 no
`claude-sonnet-5`). O volátil — snapshot da tela, pergunta do usuário — vem
depois. Sinal de que funcionou: `cache_read_input_tokens` > 0 em perguntas
seguidas na mesma tela; zero significa invalidador silencioso no prefixo.

**Parâmetros.** Saem de `model_catalog` via `llm._params_efetivos`. Modelos que
raciocinam recusam `temperature` e precisam de teto de saída alto — isto já
está resolvido no código; use o caminho existente.

**Custo por resposta.** `llm.collect_usage()` + `ai_activity.registrar` já dão
tokens e custo. O assistente registra com `tipo` próprio, para o painel de IA
separar o que é análise do que é ensino.

**Escolha de modelo.** A pergunta típica ("o que é gatilho, no meu caso?") é
curta e ancorada em dado já calculado — não é raciocínio difícil. Comece no
modelo econômico do catálogo e suba só se a qualidade pedir; a alavanca de
custo aqui é o modelo e o `effort`, não cortar o snapshot.

---

## Fases

Cada fase entrega valor sozinha. Ao fim de cada uma, mostre a evidência.

### Fase 1 — Fundação: contrato do conceito, isolamento e chave de desligar

- Catálogo de conceitos no backend: `id`, `titulo`, `corpo` para iniciante
  absoluto, e os campos numéricos que o chamador injeta.
- As respostas que carregam conceito passam a incluí-lo conforme o modo.
- Estado "já vi" persistido em `config` (padrão `tourSeen`), nos dois stores.
- Flags de desligamento (didática, assistente) no backend.

**Aceite:** teste provando payload de `operador` idêntico ao atual e conceito
presente em `estudo`; teste provando que a flag desligada remove a camada.
Evidência: saída do pytest com os testes nomeados.

### Fase 2 — Um conceito ponta a ponta: `gatilho`

Calibra o formato antes de escalar.

- Cobre as três perguntas do iniciante: o que é, o que acontece quando é
  atingido, e o que **não** acontece (o app não compra nada; decisão e execução
  são da pessoa).
- Aparece sozinho na primeira vez; permanece acessível em um toque depois.
- Dispensável em um toque, e a dispensa persiste.

**Aceite:** verificação ao vivo em Estudo mostrando a explicação na primeira
carga, o acesso permanente na segunda, e a mesma tela em Operador sem
alteração. Evidência: prints dos dois modos.

### Fase 3 — Cobertura das telas relevantes

Na ordem em que o card apresenta: `stop`, `alvo`, `R`, `confluência`,
`fundamento A/B/C`, `barra de 15m`. Depois, um inventário das demais telas
(Radar, Portfólio, Operador IA) listando o que cada uma afirma sem explicar.

**Aceite:** inventário escrito + cada conceito com guardião de modo.

### Fase 4 — Assistente de IA com contexto de tela

- Endpoint que recebe `{modo, tela, snapshot, pergunta}` e responde no
  vocabulário do modo.
- Acesso a partir das telas cobertas na Fase 3, levando o snapshot daquela tela.
- Teto de custo, flag de desligamento e registro em `ai_activity` ativos desde
  a primeira versão.

**Aceite:** conversa real em produção com `cache_read_input_tokens` > 0 na
segunda pergunta da mesma tela; teste provando que o assistente recusa inventar
número ausente do snapshot; teste provando o teto de custo. Evidência: saída
das chamadas e dos testes.

### Fase 5 — ADR

Registra por que a didática é backend-first e determinística, por que o
assistente recebe snapshot em vez de tela, e por que o Operador é imune.
Formato de `docs/adr/001..005`.

---

## Fora de escopo

- Camada didática **proativa** no Operador (o assistente sob demanda pode
  existir lá, com vocabulário de mesa).
- Substituir a `AjudaScreen` ou o tour — ambos permanecem.
- Explicação gerada por LLM na camada determinística.
- Opções: escondidas por falta de fonte; voltam quando o MyData entregar cadeia.

---

## Critério de pronto

- Suítes verdes: backend e web, sem redução de cobertura.
- Operador provado inalterado por teste, não por inspeção.
- Verificação ao vivo nos dois modos, com evidência anexada.
- Flags de desligamento exercitadas (liga/desliga) antes do deploy.
- ADR escrito, `RELEASES.md` atualizado, carimbo de build novo.

---

## Autonomia e continuidade

**Decida sozinho** o rotineiro: nome de arquivo, formato de teste, ordem dentro
da fase, redação do texto didático. Rode as suítes e a verificação ao vivo sem
pedir permissão.

**Pare e pergunte** só no que tem efeito externo ou é irreversível: deploy,
push, mudança de preço/limite que gaste dinheiro do Alex, e a redação final de
conteúdo que será lido por usuário iniciante (uma revisão por fase basta).

**Bloqueio externo** (chave ausente, fonte fora do ar, decisão do Alex
pendente): registre no arquivo de estado, siga para o próximo item que não
dependa disso, e diga em uma frase o que ficou parado e por quê.

**Continuidade entre sessões:** mantenha `ESTADO-Didatica.md` na raiz com fase
atual, o que foi provado, e o que está bloqueado. Uma sessão nova começa lendo
esse arquivo e este documento.

**Conhecimento reusável** desta área mora em `.claude/skills/didatica-bolsia/`
— vocabulário por modo, princípios, guardiões e caminho de deploy. Consulte
antes de reintroduzir regra que já está lá.

**Permissões do harness:** autonomia real depende de `.claude/settings.json`
liberar o rotineiro (pytest, build do web, suítes `node`, `git status/diff`,
health de produção, masstest) e manter em `ask` o que tem efeito externo
(`atualizar.sh`, `entregar.sh`, `publicar-web.sh`, `git push/commit`,
`railway`). O bloco proposto está na entrega desta spec; criá-lo é ação do
Alex — escrita nesse arquivo é barrada por classificador, e com razão.
