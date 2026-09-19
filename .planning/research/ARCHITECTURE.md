# Architecture Research — Reorganização da aba Opções por job-to-be-done

**Domain:** reorganização de UI existente (React 18, sem router), zero capability nova
**Researched:** 2026-09-19
**Confidence:** HIGH (leitura direta do código-fonte e dos guardiões — nenhuma hipótese de treino)

Esta pesquisa NÃO propõe arquitetura genérica de mercado — o milestone v1.6 é
reorganização de UI existente. Tudo abaixo vem de leitura direta de
`web/src/opcoes/OpcoesScreen.jsx` (2010 linhas), `web/src/opcoes/useOpcoesMcp.js`
(466 linhas), `web/src/App.jsx` (trecho de `useCuradoria`/`curadoriaAtiva`,
linhas 4142-4223 e 7734-7747) e 6 guardiões de teste (`web/tests/test_opcoes_*.mjs`).

## Estado Atual (linha de base para a reorganização)

### A sub-aba "Setups" hoje é UMA função (`OpcoesScreen`) com rolagem única

Ordem de renderização atual dentro de `subaba === "setups"` (OpcoesScreen.jsx:800-1384):

```
cabecalho (pregão/fonte/frescor)
  ↓
fraseDuasLeituras (frase-ponte, SEMPRE no DOM, Fase 32 D-05)
  ↓
blocoOportunidades  (<OportunidadesOpcoes/> — Bloco A, motor COM gate)
  ↓
blocoCuradoria      (<CuradoriaEstruturas/> — Bloco B, motor SEM gate)
  ↓
blocoVigias         ("SEUS VIGIAS" — índice + estado do dia)
  ↓
seletor             (chips de ticker da carteira)
  ↓
LastroDoAtivo / LeituraInterna / blocoLeituraDoServico  (dependem de `ticker`)
  ↓
cascata carregando→erro→vazio→dados (compartilhada por leitura+setups+proposta)
  ↓
  dentro de "dados": LEITURA DO ATIVO → O QUE DÁ PARA MONTAR (tese/proposta)
                    → COMPARAR OS VENCIMENTOS (possibilidades) → SETUPS GRAVADOS
                    → CRIAR UM SETUP
```

Os 5 jobs que o `PROJECT.md` nomeia mapeiam para blocos de código já
identificáveis, mas NÃO igualmente independentes entre si (ver "Achado
crítico" abaixo):

| Job (PROJECT.md) | Bloco(s) hoje | Componente(s) já extraído(s)? |
|---|---|---|
| 1. Descobrir oportunidades cross-carteira | `fraseDuasLeituras` + `blocoOportunidades` + `blocoCuradoria` | SIM — `OportunidadesOpcoes.jsx`, `CuradoriaEstruturas.jsx` (módulos de terceiro, Fase 32) |
| 2. Gerenciar vigias | `blocoVigias`, `CartaoDeVigia` (função interna) | NÃO — inline em `OpcoesScreen.jsx` |
| 3. Analisar um ticker manualmente | `cabecalho`, `seletor`, `LastroDoAtivo`, `LeituraInterna`, `blocoLeituraDoServico`, bloco "LEITURA DO ATIVO", "O QUE DÁ PARA MONTAR" | Parcial — `LeituraInterna`/`LastroDoAtivo` são funções internas ao arquivo, não módulos próprios |
| 4. Comparar vencimentos | "COMPARAR OS VENCIMENTOS" (possibilidades) | NÃO — inline, mesmo `<div style={CAIXA}>` do job 3 |
| 5. Gerenciar/criar setups salvos | "SETUPS GRAVADOS" + `<CriarSetup/>` | Parcial — `CriarSetup.jsx` já é módulo próprio; a listagem de setups gravados é inline |

## Integração com os hooks de dados (`useOpcoesMcp.js`) — o que NÃO muda

`useOpcoesMcp(store, ticker)` é chamado **uma única vez**, no topo de
`OpcoesScreen`, e devolve um objeto plano com todos os trios
`dados/carregando/erro` + as funções de disparo. Nenhum job-section deve
chamar este hook de novo — cada seção recebe o(s) trio(s) relevantes **por
prop**, exatamente como `SubAbaOperar` já recebe `tecnico` hoje (linha 1406)
e como `OportunidadesOpcoes`/`CuradoriaEstruturas` já recebem seus dados por
prop (linhas 721-753). Isto é o padrão estabelecido no próprio arquivo — a
reorganização por job deve REPLICAR esse padrão, não inventar um novo.

**Mapa de qual job precisa de qual pedaço do hook:**

| Job | Campos de `useOpcoesMcp` | Estado local de `OpcoesScreen` |
|---|---|---|
| 1. Descobrir | nenhum (usa `useOpcoesPropostas` + `ctx.curadoria`, hooks IRMÃOS, não filhos de `useOpcoesMcp`) | `carteira` |
| 2. Vigias | `vigias`, `vigiasVivos`, `atualizarVigias` | `carteira` (para `tickersEmCarteira`), callback `irParaVigia` |
| 3. Analisar ticker | `status`, `leitura`, `abrirLeitura`, `tecnico` | `ticker`, `escolherTicker`, `tese`/`vencimento`/`lote` (para o formulário de proposta), `posicaoSelecionada` |
| 4. Comparar vencimentos | `leitura` (só para ler `l.expirations`), `possibilidades`, `verPossibilidades` | `ticker`, `tese`, `lote`, `alvo`, `stop` — **mesmo estado do job 3** |
| 5. Setups salvos | `leitura` (só para ler `l.setups`/`l.setupsNaoAvaliados`), `grafico`, `abrirGrafico`, `fecharGrafico`, `setupNovo`, `compilarSetup`, `confirmarSetup`, `desativarSetup` | `ticker`, `podeCriarSetup` |

### Achado crítico: Jobs 3, 4 e 5 NÃO são independentes — compartilham um único fetch pago

`setups` (job 5) e `expirations`/`behavior` (jobs 3 e 4) são todos **campos do
mesmo objeto** `leitura.dados` (`l = leitura.dados`, OpcoesScreen.jsx:404).
Esse objeto só existe depois de `abrirLeitura()` — um clique explícito que
custa **3 chamadas** do cap MCP (`CUSTO_DA_ACAO.leitura = 3`,
`_cap_check(uid, 3)` no backend). Não existe endpoint mais barato para "só
listar os setups gravados" ou "só ver os vencimentos" — a mesma resposta cara
alimenta os três jobs.

Isto é uma bifurcação de produto genuína, não um detalhe de implementação, e
não deve ser resolvida silenciosamente nesta pesquisa — fica registrada como
pergunta em aberto para o `CONTEXT.md`/`UI-SPEC.md` do milestone:

- **(a)** os três jobs compartilham UM ÚNICO ponto de entrada ("ler este
  ativo no serviço", que já existe hoje) e, depois de pago, os três painéis
  ficam disponíveis; ou
- **(b)** cada job pede sua própria leitura com uma explicação própria de
  custo — o que multiplicaria a exposição a "the same 3-call fetch,
  requested 3 times from 3 different screens" se a pessoa navegar entre eles
  sem lembrar que já pagou.

Dado o guardrail do ADR-027 §3.3 ("custo de MCP só em clique explícito, nunca
ao abrir tela") e o histórico do próprio arquivo de reduzir chamadas
duplicadas (Fase 27-05 matou a duplicação entre o efeito de troca de ticker e
`recarregarLeitura`), a opção (a) é a que preserva a disciplina já
estabelecida — mas a decisão é do Alex, não desta pesquisa.

**Vigias (job 2) e Descobrir (job 1) são os únicos dois jobs genuinamente
independentes** — não dependem de ticker escolhido nem de `leitura` paga:
`vigias`/`vigiasVivos` são rotas internas de custo zero (27-01/27-02);
`ctx.curadoria`/`useOpcoesPropostas` vêm de hooks que vivem fora de
`useOpcoesMcp` inteiramente (ver seção seguinte).

## Integração com o estado lifted em `App()` — `curadoriaAtiva`

`curadoriaAtiva` (App.jsx:7739) é uma flag monotônica **fora de
`OpcoesScreen.jsx` inteiramente** — vive em `App()`, liga quando
`tab === "opcoes"` OU `(tab === "carteira" && carteiraView === "main")`,
nunca desliga, nunca dispara em boot puro (Fase 32, 32-02, decisão A). O
hook `useCuradoria(curadoriaAtiva)` roda uma única vez em `App()` e o
resultado (`ctx.curadoria`) é passado por prop tanto para `CarteiraScreen`
(linha de chamada) quanto para `OpcoesScreen` (Bloco B).

**Conclusão direta para a reorganização:** a reorganização por job-to-be-done
da sub-aba "Setups" **não pode, por construção, quebrar esse gate**, porque
o gate está uma camada acima — ele é acionado por `tab`, não por qual job-
section está visível dentro da aba Opções. Enquanto a Fase de reorganização:

1. mantiver a leitura de `ctx.curadoria` chegando a `OpcoesScreen` do mesmo
   jeito (via `ctx`, sem instanciar `useCuradoria` de novo dentro de nenhum
   job-section), e
2. NÃO promover a checagem `tab === "opcoes"` para uma checagem por job
   específico (ex.: `job === "descobrir"`) — o que reintroduziria o próprio
   problema que a Fase 32 corrigiu (custo de rede pago só por abrir uma tela)

...o `curadoriaAtiva` fica intocado. O único jeito de QUEBRAR essa garantia
seria decidir, no design de navegação, que o job "Descobrir oportunidades"
só deve buscar dados quando a pessoa clicar nele — isso exigiria mover o
gate de `tab` para `job`, que é uma regressão ao padrão pré-Fase-32 (fetch
amarrado à visita de uma tela específica, não da aba como um todo). Não
recomendado; deixar `ctx.curadoria` como está e simplesmente **renderizar**
seu conteúdo dentro do job "Descobrir" quando ele estiver ativo é
suficiente — o dado já estará pronto (ou em `carregando`) porque foi buscado
no nível da aba, não do job.

`useOpcoesPropostas(store, carteira.map(...))` (linha 401-402) segue o MESMO
princípio: hook chamado uma vez em `OpcoesScreen`, resultado repassado por
prop ao job "Descobrir" (hoje, `OportunidadesOpcoes`). Nenhuma mudança
necessária além de continuar chamando-o no componente orquestrador, nunca
dentro de um job-section que pode montar/desmontar.

## Estado local que atravessa jobs (não pode ser fatiado por componente)

Estes `useState` de `OpcoesScreen` são consumidos por MAIS de um job e
precisam continuar vivendo no componente orquestrador (ou subir mais, se o
orquestrador deixar de ser `OpcoesScreen`):

- `ticker`/`escolherTicker` — jobs 2 (navega para ele), 3, 4, 5 (todos leem o
  mesmo ticker escolhido)
- `tese`, `vencimento`, `lote`, `alvo`, `stop` — jobs 3 e 4 compartilham o
  MESMO formulário de tese/lote; `alvo`/`stop` são usados só pelo job 4, mas
  `tese`/`lote` são usados pelos dois
- `painel` (`"" | "cadeia" | "operaveis"`) — hoje é acionado de dentro da
  seção "O QUE DÁ PARA MONTAR" (job 3), mas não há razão estrutural para não
  ficar local a esse job-section específico, diferente de `ticker`/`tese`

Regra prática: **estado usado por 1 job → desce para o componente daquele
job. Estado usado por 2+ jobs → fica no orquestrador.**

## Integration Points (resumo objetivo)

| Job-section (novo) | Recebe do orquestrador | Não deve fazer |
|---|---|---|
| SecaoDescobrir | `opcoesPorTicker`, `opcoesPorTickerCarregando`, `ctx.curadoria`, `carteira`, `onAbrir` (=`irParaOperar`) | instanciar `useCuradoria`/`useOpcoesPropostas` própria |
| SecaoVigias | `vigias`, `vigiasVivos`, `atualizarVigias`, `carteira`, `ticker`, `onIr` (=`irParaVigia`) | chamar `store.mcp*` direto (deve passar pelo trio do hook) |
| SecaoAnalisar (job 3) | `ticker`, `escolherTicker`, `status`, `leitura`, `abrirLeitura`, `tecnico`, `posicaoSelecionada`, `tese`/`setTese`, `vencimento`/`setVencimento`, `lote`/`setLote` | disparar `abrirLeitura` fora de clique explícito |
| SecaoComparar (job 4) | `ticker`, `tese`, `lote`, `alvo`/`setAlvo`, `stop`/`setStop`, `leitura` (para `expirations`), `possibilidades`, `verPossibilidades` | recalcular `chamadasPrevistas`/`N_MAX_VENCIMENTOS` localmente (mantém constantes do orquestrador) |
| SecaoSetups (job 5) | `ticker`, `leitura` (para `setups`/`setupsNaoAvaliados`), `grafico`/`abrirGrafico`/`fecharGrafico`, `setupNovo`/`compilarSetup`/`confirmarSetup`/`desativarSetup`, `podeCriarSetup` | reimplementar a cascata carregando→erro→vazio (extrair como helper compartilhado, ver abaixo) |

### Um helper vale a pena: a cascata de estado do serviço

Hoje existe UMA cascata `carregando → erro → vazio com motivo → dados`
(OpcoesScreen.jsx:832-908) que cobre leitura+setups+proposta ao mesmo tempo,
porque tudo mora na mesma árvore JSX. Se os jobs 3/4/5 viram
componentes/seções separados, cada um vai precisar da MESMA lógica de estado
(porque todos dependem de `leitura`/`status`/`erro`). Duplicar essa cascata 3
vezes é o tipo exato de duplicação que os comentários do próprio arquivo já
identificam como fonte de divergência silenciosa ("duas cópias do mesmo
pedido divergem na primeira manutenção feita só numa delas" —
`useOpcoesMcp.js:291-295`). Recomendação: extrair um componente
`<CascataDoServico status={...} erro={...} carregando={...}>{children}</CascataDoServico>`
usado pelos três, em vez de reescrever o `if/else` em cada job-section.

## Guardiões existentes que codificam a ORDEM da rolagem única — risco concreto

Vários guardiões não testam comportamento — testam a **posição literal de
substrings** dentro do arquivo `OpcoesScreen.jsx` inteiro (a variável `tela`
lida por `readFileSync`). Isso significa que a garantia que eles fornecem
hoje é "estas coisas aparecem NESTA ORDEM NO MESMO ARQUIVO", uma asserção que
deixa de fazer sentido conceitual assim que os blocos viram
componentes/painéis navegáveis separados — não é que o teste vai "quebrar
por acidente", é que o INVARIANTE que ele defende deixa de existir por
desenho da própria reorganização pedida.

Confirmado por leitura direta (não é hipótese):

1. **`test_opcoes_consolidacao_ui.mjs`, regra 1** (linhas 77-85): exige
   `indexOf("{fraseDuasLeituras}") < indexOf("{blocoOportunidades}") <
   indexOf("{blocoCuradoria}") < indexOf("{blocoVigias}")` dentro do MESMO
   arquivo. Se "Descobrir" (jobs 1) e "Vigias" (job 2) viram duas seções
   navegáveis distintas, a frase-ponte pode deixar de preceder o bloco de
   vigias na mesma árvore — o teste vai reprovar mesmo que o comportamento
   esteja correto.
2. **`test_opcoes_consolidacao_ui.mjs`, regra 8** (linhas 144-150): exige
   ausência de `<input>`/`position: sticky|fixed` **entre** a frase-ponte e
   os vigias — pressupõe que os dois continuam na mesma faixa contígua de
   texto-fonte. Uma navegação por job (abas/menu) provavelmente introduz
   algum controle de navegação exatamente nessa posição textual.
3. **`test_opcoes_analisar_ui.mjs`, linhas 141-146**: exige
   `iAnalisar < iPossib < iSetups` e `opcoesLeituraTitulo` antes de
   `opcoesAnalisarTitulo` — isto é literalmente a ordem hoje dos jobs 3→4→5
   dentro do MESMO arquivo. Vira obsoleto no dia em que esses três viram
   componentes irmãos, não mais texto sequencial.
4. **`test_opcoes_subabas_ui.mjs`, regra 11** (linhas 190-193): exige que os
   literais `cabecalho`, `blocoVigias`, `seletor`, `LastroDoAtivo`,
   `LeituraInterna`, `blocoLeituraDoServico` continuem aparecendo como
   substring em `OpcoesScreen.jsx`. É sensível a maiúscula/minúscula — se o
   bloco de vigias virar um componente `<BlocoVigias/>` (Pascal), a
   substring `"blocoVigias"` (camel, minúsculo) some do arquivo e o
   guardião reprova por um motivo puramente de nomenclatura, não de
   regressão real.
5. **`test_opcoes_vigias_ui.mjs`** (linhas 60-98) e
   **`test_opcoes_mcp_aba_ui.mjs`** (linhas 128-133, 209, 320): fazem o
   mesmo tipo de fatiamento por `indexOf`/`.match` sobre `tela` inteira —
   qualquer um que dependa de `blocoVigias`/`cabecalho`/`chip` continuarem
   como `const` nomeadas dentro do MESMO arquivo-fonte quebra se essas
   viram componentes-arquivo próprios sem deixar rastro textual equivalente.

**Isto não é motivo para não reorganizar** — é motivo para orçar
explicitamente, na(s) fase(s) que tocam `OpcoesScreen.jsx`, a tarefa de
**reescrever estes guardiões com uma nota datada**, no mesmo padrão que o
próprio arquivo já usa em dezenas de comentários ("Fase 32 (32-04): ...
SUPERADA ... texto histórico abaixo segue válido — só o 'aqui' mudou de
resposta"). Não é aceitável apagá-los silenciosamente, nem é aceitável
tentar preservar a ordem-em-um-arquivo-só como requisito de design só para
não mexer no teste — isso inverteria a causalidade (o teste ditando a
arquitetura, em vez de documentar a decisão de produto).

## Convenção a replicar ao extrair componentes

Os módulos que a Fase 32 já extraiu (`OportunidadesOpcoes.jsx`,
`CuradoriaEstruturas.jsx`, `CandidatoOpcao.jsx`) seguem uma disciplina clara
que os guardiões já verificam e que os novos job-sections devem seguir:

- **Nenhum import de `App.jsx`** — invariante de duas vias do ADR-027,
  verificado por varredura de DIRETÓRIO em `test_opcoes_subabas_ui.mjs`
  (linhas 100-116): "acha pelo menos 10 arquivos... nenhum arquivo importa
  App.jsx" — um job-section novo entra automaticamente nessa checagem sem
  precisar editar o guardião.
- **Sem `store.<metodo>(` nem `api.<metodo>(` dentro do componente** — dado
  chega por prop, ação sobe por callback (`onAbrir`, `onExecutar`, `onIr`).
- **Toda `cp.X` referenciada existe nos dois ramos de `COPY`** (`estudo` e
  `operador`) — checado automaticamente por varredura de regex em pelo
  menos dois guardiões (`test_opcoes_subabas_ui.mjs` regra 9,
  `test_opcoes_analisar_ui.mjs`).

## Build Order Recomendado

A pesquisa aponta uma ordem de execução com risco crescente de quebra dos
guardiões de ordem, do mais seguro para o mais arriscado:

### Fase A — Extrair componentes, preservando a ordem/comportamento atual (baixo risco)

Mover cada job-section para seu próprio arquivo em `web/src/opcoes/`,
recebendo exatamente os mesmos dados que recebe hoje via `const blocoX = (...)`,
**sem mudar a navegação** — a sub-aba "Setups" continua renderizando os 5
componentes em sequência, na MESMA ordem de hoje. Isso:

- não quebra `curadoriaAtiva` (nada muda na cadeia de fetch);
- não quebra os guardiões de ORDEM (a ordem textual em `OpcoesScreen.jsx`
  pode ser preservada usando `<SecaoDescobrir .../>` no lugar exato onde
  `{blocoOportunidades}{blocoCuradoria}` estava — os guardiões que checam
  substrings viram apenas os NOMES dos JSX tags, então **atualizar os
  guardiões nesta fase é mecânico**: trocar `"{blocoOportunidades}"` por
  `"<SecaoDescobrir"` no `indexOf`, mantendo a MESMA relação de ordem);
- é o momento certo para introduzir o `<CascataDoServico>` compartilhado,
  já que a extração vai forçar a decisão de "quem trata carregando/erro"
  de qualquer forma;
- resolve a bifurcação job3/4/5-compartilham-fetch-pago **sem decidir nada
  de UX ainda** — os três componentes continuam recebendo `leitura` inteiro
  e decidindo internamente o que mostrar, exatamente como hoje.

### Fase B — Redesenhar a navegação (risco médio, depende da decisão do Alex sobre a bifurcação acima)

Só depois da Fase A (componentes já isolados e testáveis independentemente),
trocar a rolagem única por navegação por job (abas, acordeão, ou menu +
detalhe — decisão de UI-SPEC, fora do escopo desta pesquisa). Esta fase:

- **exige reescrever, não apenas ajustar, os guardiões de ordem** listados
  acima (`test_opcoes_consolidacao_ui.mjs` regras 1/8,
  `test_opcoes_analisar_ui.mjs` linhas 141-146, `test_opcoes_subabas_ui.mjs`
  regra 11) — eles devem passar a verificar "todo job é alcançável a partir
  do menu/abas" e "a frase-ponte aparece incondicionalmente dentro do job
  Descobrir", em vez de ordem textual cross-job;
- é o momento de decidir a bifurcação job3/4/5: se a decisão for "um único
  ponto de entrada paga a leitura para os três", a navegação precisa deixar
  isso explícito (ex.: os jobs 4 e 5 mostram um estado "leia o ativo
  primeiro" com CTA que leva ao job 3, em vez de botão de leitura duplicado
  em cada um);
- deve rodar a suíte canônica (`bash scripts/executar.sh --testes`) a cada
  guardião reescrito, não só no final — o volume de guardiões que fazem
  fatiamento por `indexOf` neste diretório (pelo menos 6 arquivos
  confirmados) torna plausível quebrar um sem perceber por edição
  colateral em outro arquivo lido pelo mesmo guardião (ex.:
  `test_opcoes_consolidacao_ui.mjs` lê `App.jsx` E `OpcoesScreen.jsx` E
  `CuradoriaEstruturas.jsx` no mesmo arquivo de teste).

### Por que não fazer os dois juntos

Fundir extração de componente com redesenho de navegação numa única fase
significa reescrever os guardiões de ordem SEM ter ainda a garantia de que
os dados corretos chegam a cada componente — dois eixos de risco (estrutura
de arquivo + fluxo de navegação) mudando ao mesmo tempo, sem um checkpoint
intermediário em que a suíte ainda esteja verde. A Fase A entrega esse
checkpoint: componentes extraídos, suíte verde, MESMO comportamento visível,
guardiões atualizados só na sintaxe (nome do marcador), não na lógica.

## Pergunta em aberto para o CONTEXT.md/UI-SPEC do milestone (não resolvida aqui)

Como os jobs 3 ("analisar ticker"), 4 ("comparar vencimentos") e 5
("gerenciar setups salvos") compartilham a MESMA resposta paga de 3 chamadas
(`leitura.dados`), a navegação por job precisa decidir explicitamente: um
único ponto de entrada paga uma vez e libera os três painéis, ou cada painel
pede sua própria leitura (mais fiel à ideia de "cada job é independente",
mas arrisca cobrar 3× de quem navega entre os três sem lembrar que já pagou
uma vez). Esta é uma decisão de produto/UX, não uma escolha de arquitetura
de dados — o hook já suporta as duas opções sem mudança de contrato.

## Sources

- `web/src/opcoes/OpcoesScreen.jsx` (leitura completa, 2010 linhas)
- `web/src/opcoes/useOpcoesMcp.js` (leitura completa, 466 linhas)
- `web/src/App.jsx`, trechos `useCuradoria`/`curadoriaAtiva`/`LinhaChamadaOpcoes`
  (linhas 4112-4260, 7724-7747)
- `web/tests/test_opcoes_consolidacao_ui.mjs`,
  `web/tests/test_opcoes_subabas_ui.mjs`,
  `web/tests/test_opcoes_analisar_ui.mjs`,
  `web/tests/test_opcoes_vigias_ui.mjs`,
  `web/tests/test_opcoes_mcp_aba_ui.mjs`,
  `web/tests/test_opcoes_custo_declarado.mjs`,
  `web/tests/test_opcoes_universo_carteira.mjs` (leitura direta dos asserts)
- `.planning/PROJECT.md` (seções Milestone v1.6 e v1.4)

---
*Architecture research for: reorganização por job-to-be-done, aba Opções (Boris+)*
*Researched: 2026-09-19*
