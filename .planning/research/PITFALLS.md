# Pesquisa de Pitfalls — Reorganização por Job-to-be-Done da aba Opções (v1.6)

**Domínio:** reorganização de UI densa e já publicada, fintech educacional
regulatório-adjacente (Boris+), com guardiões de teste que leem TEXTO-FONTE
(regex/`indexOf`/`includes`) em vez de comportamento em runtime.
**Pesquisado:** 2026-09-19
**Confiança:** HIGH — todos os achados vêm de leitura direta do código-fonte
e dos guardiões reais (`web/src/opcoes/OpcoesScreen.jsx`,
`web/tests/test_opcoes_subabas_ui.mjs`,
`web/tests/test_opcoes_consolidacao_ui.mjs`), não de treinamento genérico
sobre refactoring de React.

## Pitfalls Críticos

### Pitfall 1: Extrair componente muda quem decide e quem narra, sem ninguém pretender isso

**O que dá errado:**
`blocoCuradoria` (Bloco B, `OpcoesScreen.jsx:735-753`) hoje recebe NO MESMO
componente `top`/`meta` (saída determinística de `ctx.curadoria`) e
`narrativa`/`narrando`/`onNarrar`/`erroNarrativa` (texto gerado por IA sobre
esses mesmos 4 candidatos). A separação por job pode mover a "leitura da IA"
para uma seção própria (ex.: "O que o Boris acha" separado de "as 4
melhores estruturas"). Ao fazer isso, é fácil introduzir sem querer uma
segunda fonte de ordenação: a nova seção de narração decide sozinha em que
ordem mostrar os candidatos (ex.: prioriza o que já tem `narrativa` pronta,
ou reordena por "relevância" textual), o que faz a disponibilidade/conteúdo
da IA influenciar QUAL candidato o usuário vê primeiro — o motor deixou de
ser a única fonte de seleção/ranking mesmo que ninguém tenha tocado em
`avaliar()`/`rastrear()`.

**Por que acontece:**
Job-separation tende a agrupar por "o que a IA faz" (explicar) versus "o que
o motor faz" (escolher), o que parece limpo — mas os dois hoje convivem no
MESMO array (`ctx.curadoria.top`), e o desenvolvedor que faz a extração
precisa decidir onde esse array "mora" depois do split. Se a decisão for
implícita (cada seção busca seu próprio subconjunto de `top` por
conveniência de renderização), a garantia de fonte única se perde sem que
nenhuma linha de `avaliar()`/`rastrear()` tenha mudado.

**Como evitar:**
Trate `ctx.curadoria.top` como um valor imutável, computado uma única vez em
`OpcoesScreen.jsx` (ou no hook), e passe a MESMA referência de array, na
MESMA ordem, para qualquer seção nova que a reorganização criar — a seção de
"narração" nunca reordena, filtra ou pagina esse array por conta própria;
ela só decora item a item. Se a UI-SPEC da fase pedir uma seção "resumo da
IA" separada da "lista de candidatos", o contrato explícito deve ser
"renderiza `top[i].narrativa` ancorado no MESMO índice `i`", nunca "busca a
narrativa mais relevante".

**Sinais de alerta:**
Durante a implementação, se a nova seção de narração precisar de um
`useState`/`useMemo` próprio para decidir "qual candidato mostrar" (em vez
de simplesmente iterar o array que já veio pronto), é sinal de que a seleção
está migrando para o lado da IA. Também é sinal de alerta qualquer prop nova
chamada `ordenacaoNarrativa`, `prioridade`, ou lógica de `.sort()`/`.filter()`
tocando em algo vindo de `ctx.curadoria` fora de `useOpcoesPropostas.js`.

**Fase de tratamento:**
Antes de separar componentes — travar no UI-SPEC/CONTEXT da fase que
"top"/"meta" são um array só, com uma única fonte (`useOpcoesPropostas.js`/
`useCuradoria`), e que qualquer seção nova consome por índice, nunca
recomputa. Verificação: no code review pós-fase, grep por `.sort(` ou
`.filter(` em qualquer arquivo novo de `web/src/opcoes/` que também importe
`narrativa`/`erroNarrativa`.

---

### Pitfall 2: A frase-ponte (D-05) fica mais longe do bloco que ela desambigua, ou vira alvo de "isso já está repetido, corta"

**O que dá errado:**
`fraseDuasLeituras` (`OpcoesScreen.jsx:705-715`) existe especificamente para
impedir que "AS 4 MELHORES" do Bloco B seja lida como veredito geral do app
— é uma mitigação regulatória, comentada no código como "tornar esta frase
colapsável seria regressão regulatória, não ajuste visual". Duas formas
concretas de isso quebrar numa reorganização por job:
(1) a frase fica fisicamente distante do Bloco B se as duas coisas caem em
seções/abas diferentes, perdendo o efeito de desambiguação no exato ponto
onde o usuário lê "as 4 melhores";
(2) alguém decide, no espírito de "limpar a tela", que a frase é redundante
se aparecer em toda seção que mostra Bloco A ou B, e a torna condicional/
colapsável — violando D-05 diretamente, mesmo que o guardião de "sempre no
DOM" (ver Pitfall 3) não seja tecnicamente quebrado se a condição for escrita
de um jeito que o regex não pega.

**Por que acontece:**
Job-separation tem viés de "cada seção conta sua própria história completa",
o que empurra texto de enquadramento para perto de cabeçalhos de seção — mas
o D-05 não é copy de UX, é mitigação regulatória amarrada à ADJACÊNCIA
física com o Bloco B, não à existência da frase em algum lugar da tela.

**Como evitar:**
Tratar a frase-ponte como parte INDISSOCIÁVEL do Bloco B na reorganização —
se o Bloco B (curadoria/"as 4 melhores") vira uma seção própria, a frase
migra junto, sempre imediatamente acima dele, sem gate de coleção/scroll
entre os dois (mesma regra que já protege isso hoje, ver Pitfall 3). Se a
UI-SPEC da fase propuser mover Bloco A e Bloco B para seções DIFERENTES
(plausível, já que são jobs diferentes — "descobrir oportunidades" vs
"comparar as melhores estruturas"), isso precisa virar uma decisão explícita
registrada no CONTEXT.md da fase, não um efeito colateral da separação.

**Sinais de alerta:**
Qualquer PR/plano que mova `blocoCuradoria` para um arquivo/seção sem também
mover `fraseDuasLeituras` no mesmo commit. Qualquer proposta de "aria-expanded"
ou toggle novo tocando nesse texto.

**Fase de tratamento:**
Durante a separação de componentes — a task que extrai Bloco B deve
explicitamente decidir e documentar onde a frase-ponte mora depois; como
verificação pós-fase, reler o comentário de D-05 em `OpcoesScreen.jsx:705-710`
contra o resultado e confirmar que a leitura "as 4 melhores DESTE bloco,
não do app" continua garantida no layout novo.

---

### Pitfall 3: Guardiões regex escopados a um arquivo/variável ficam cegos quando o código migra de arquivo

**O que dá errado:**
Vários guardiões de `web/tests/test_opcoes_subabas_ui.mjs` e
`test_opcoes_consolidacao_ui.mjs` fazem contagem/posição sobre o TEXTO de
`OpcoesScreen.jsx` inteiro (variável `tela`), não sobre comportamento:
- `tela.match(/store\.optionsGate\(/g).length === 1` — exige exatamente 1
  ocorrência literal da chamada NESSE arquivo (`test_opcoes_subabas_ui.mjs:123-126`).
- `tela.indexOf("{fraseDuasLeituras}") < indexOf("{blocoOportunidades}") <
  indexOf("{blocoCuradoria}") < indexOf("{blocoVigias}")` — exige que os
  QUATRO identificadores apareçam nessa ordem textual
  (`test_opcoes_consolidacao_ui.mjs:78-85`).
- `for (const nome of ["cabecalho", "blocoVigias", "seletor",
  "LastroDoAtivo", "LeituraInterna", "blocoLeituraDoServico"]) tela.includes(nome)`
  (`test_opcoes_subabas_ui.mjs:190-193`).

Se a reorganização por job extrair, por exemplo, `blocoVigias` para um
componente `<SecaoVigias/>` num arquivo novo (`SecaoVigias.jsx`) — uma
mudança PURAMENTE estrutural, comportamento idêntico — o identificador
`blocoVigias` deixa de existir como const em `OpcoesScreen.jsx`, e os três
guardiões acima quebram, mesmo que nada tenha mudado de verdade para o
usuário. Isso é o cenário "bom" (falso positivo que pelo menos avisa). O
cenário ruim é o inverso: se o refactor move a chamada de
`store.optionsGate(` para um hook compartilhado (`useOpcoesGate.js`) para
reusar entre duas seções novas, `nGate` cai para 0 em `OpcoesScreen.jsx` — o
guardião falha, mas a mensagem de erro ("aparece exatamente 1×") não deixa
óbvio que a causa é "migrou de arquivo, não regrediu".

**Por que acontece:**
Esses guardiões foram escritos para pegar DUPLICAÇÃO (duas instâncias do
hook, dois `optionsGate` gerando resultados divergentes) — um problema real
já visto neste código (comentário da Fase 32: "nunca uma segunda instância
do hook"). Eles fazem isso da forma mais barata possível: contar substrings
num arquivo conhecido. Um refactor-only que reorganiza ONDE o código mora
(sem duplicar nada) ainda dispara o mesmo sintoma textual que duplicação
dispararia.

**Como evitar:**
Antes de mover qualquer bloco/chamada citado nos guardiões acima para um
arquivo novo, ler o guardião primeiro e decidir explicitamente: (a) atualizar
o guardião para escanear o NOVO arquivo também (mantendo a intenção —
"exatamente 1 chamada em TODA a pasta `opcoes/`", como já faz o guardião de
"nenhum arquivo importa App.jsx" em `test_opcoes_subabas_ui.mjs:100-116`,
que varre por diretório e não por arquivo fixo), ou (b) manter a chamada
física em `OpcoesScreen.jsx` e só passar o RESULTADO como prop para a seção
nova. Nunca "consertar" o guardião só trocando o número esperado sem
confirmar que a garantia original (uma única fonte de gate/proposta) segue
verdadeira.

**Sinais de alerta:**
`bash scripts/executar.sh --testes` falhando com mensagens tipo "`X`
continua referenciado em OpcoesScreen.jsx" ou "aparece exatamente 1×" logo
após um commit que só moveu código de lugar (nenhuma mudança de lógica no
diff). Isso é o guardião fazendo o trabalho dele — não silenciar/deletar o
teste, investigar se a garantia original ainda vale e reescrever o guardião
para a nova topologia de arquivos.

**Fase de tratamento:**
Antes de separar componentes — mapear, para CADA bloco que vai migrar de
lugar, quais guardiões de `web/tests/*.mjs` leem o arquivo de origem (repetir
o grep `grep -rln "OpcoesScreen.jsx" web/tests/*.mjs`, que hoje retorna 9
arquivos). Durante a separação — atualizar o guardião no MESMO commit que
move o código, nunca depois. Como verificação pós-fase — rodar a suíte
completa e ler CADA falha até entender se é regressão real ou só o guardião
desatualizado; nunca ajustar um guardião sem reler o comentário de contexto
que explica por que ele existe (a maioria tem um comentário "achado por
injeção de defeito real" ou "decisão do Alex" logo acima da asserção).

---

### Pitfall 4: Guardrail CVM (manchete) tem escopo fixo de arquivo/variável e não acompanha componente novo criado pela reorganização

**O que dá errado:**
O guardrail que impede a IA de substituir a manchete determinística
(`test_opcoes_subabas_ui.mjs:141-154`) testa APENAS a string `subAba`
(o texto-fonte da função `SubAbaOperar`): nega `\{[^}]*\bmanchete\b[^}]*\}`
e `.manchete` nesse texto, e exige que `<PropostaLastreada` ou
`<CandidatoOpcao` apareçam ali. Se a reorganização da sub-aba "Setups" criar
uma seção nova (ex.: um card-resumo de "oportunidade encontrada" na seção
de descoberta cross-carteira, plausível numa simplificação de UX — "mostra
a manchete inline pra não precisar abrir o card") que renderiza
`candidato.manchete` diretamente, esse guardião específico NÃO vê essa
seção nova (ela não está dentro de `subAba`), porque o escopo do teste é uma
variável extraída de um arquivo específico, não a pasta inteira.

**Por que acontece:**
Ao contrário do guardião de "ninguém importa App.jsx" (que varre
`readdirSync(dirOpcoes)` e por isso pega arquivos novos automaticamente),
este guardião foi escrito ANTES da reorganização por job existir, com escopo
deliberadamente estreito (só `SubAbaOperar`, porque era o único lugar novo
que renderizava propostas na época — Fase 27-32). Escopo estreito é uma
escolha correta quando só existe um lugar candidato; deixa de ser suficiente
quando a fase seguinte cria mais lugares candidatos.

**Como evitar:**
Ao planejar a fase de reorganização, tratar "toda seção nova que mostra
qualquer forma de card/resumo de candidato de opção" como sujeita ao mesmo
guardrail CVM, e ESTENDER o guardião (seguindo o padrão de varredura por
diretório do item 1, não o padrão de variável única do item 5) para cobrir
qualquer arquivo `.jsx` novo em `web/src/opcoes/` que renderize um candidato
— não confiar que "já existe um teste disso" sem checar o escopo real do
teste.

**Sinais de alerta:**
Qualquer seção nova que precise ler `candidato.manchete`,
`ctx.curadoria.top[i].manchete` ou equivalente para exibir texto — mesmo que
pareça só "um preview/chip", isso é literalmente o dado que o guardrail
protege. Se a suíte passa depois de introduzir esse código, isso NÃO prova
que o guardrail está respeitado — prova só que o guardião antigo não olha
para esse arquivo.

**Fase de tratamento:**
Antes de separar componentes — decidir explicitamente na UI-SPEC se alguma
seção nova vai exibir manchete/resumo textual de candidato; se sim, o plano
da fase precisa incluir a extensão do guardião (não só o componente).
Verificação pós-fase — grep manual por `\.manchete\b` em TODO
`web/src/opcoes/*.jsx` novo/alterado, comparando contra os testes que
efetivamente cobrem cada arquivo (não assumir cobertura por analogia).

---

### Pitfall 5: Estado de erro/dado degradado perde a garantia de "impossível não ver" ao virar seção não aberta por padrão

**O que dá errado:**
Hoje TUDO (Bloco A com `carregando`, Bloco B com `erro`/`concluido`/
`erroNarrativa`, `blocoVigias`) está numa rolagem só sob a sub-aba "Setups"
— um usuário que abre essa sub-aba necessariamente passa o olho por cima de
qualquer estado de erro/degradado, porque não há mais nada escondendo. Job-
separation em abas/acordeões troca isso por design: cada seção só é vista
quando o usuário a abre. Se o MCP externo estiver fora do ar (custo
declarado, cadeia vazia) e esse estado ficar isolado dentro da seção
"comparar vencimentos" ou "gerenciar setups salvos" — seções que um usuário
focado em "só quero ver oportunidades da minha carteira" nunca abre — o
aviso de dado degradado simplesmente não é visto. Isso não é invenção de
valor (Princípio 4 do CLAUDE.md não é tecnicamente violado — nenhum número
falso é mostrado), mas é a mesma falha PRÁTICA: o usuário toma decisão sem
saber que o dado está incompleto, porque o app deixou de garantir que esse
aviso apareça no caminho que ele efetivamente percorre.

**Por que acontece:**
A separação por job otimiza para "cada seção mostra só o que é relevante
para aquele job" — o que é exatamente o oposto do que um aviso de dado
degradado precisa (ele é relevante para TODOS os jobs que dependem daquela
fonte, não só o job onde o erro foi originado). O comentário de Fase 27 já
resolveu um problema análogo para `blocoVigias` ("SEMPRE renderizado, com ou
sem ativo escolhido — é o que faz a aba abrir com conteúdo") — a
reorganização de v1.6 precisa da mesma disciplina para estado de erro, não
só para "não abrir vazio".

**Como evitar:**
Antes de decidir onde cada job mora, mapear TODOS os estados de
erro/degradado hoje visíveis na rolagem única de "Setups"
(`opcoesPorTickerCarregando`, `ctx.curadoria.erro`/`naoMedido`,
`erroNarrativa`, os erros por vencimento em `item.erro` linha ~1198, e
qualquer banner de orçamento/budget) e decidir EXPLICITAMENTE, por estado,
se ele: (a) é local a um job só (ex.: erro de narrativa da IA só afeta quem
está lendo a curadoria) e pode viver dentro da seção correspondente, ou
(b) afeta múltiplos jobs (ex.: MCP fora do ar afeta descoberta E comparação
de vencimentos) e por isso precisa de um banner GLOBAL, visível
independente de qual seção está aberta — no topo da sub-aba "Setups", fora
de qualquer acordeão/tab interna. Não assumir que "cada seção cuida do
próprio erro" é suficiente só porque parece mais modular.

**Sinais de alerta:**
Se a UI-SPEC da fase descrever job-sections como abas/acordeões
mutuamente exclusivos (só uma visível por vez) e nenhuma task do plano
mencionar "onde vai o aviso de dado degradado/MCP fora do ar", isso é sinal
de que o mapeamento não foi feito. Em teste manual: abrir a sub-aba
"Setups" com o MCP propositalmente indisponível e confirmar que o aviso
aparece ANTES de abrir qualquer seção específica, não depois.

**Fase de tratamento:**
Antes de separar componentes — o CONTEXT.md da fase de reorganização deve
listar explicitamente cada estado de erro/degradado hoje visível e sua
classificação (local a um job vs. global). Como verificação pós-fase — teste
comportamental (não só guardião de texto) que simula falha de fonte de dado
e confirma visibilidade do aviso a partir do estado inicial da sub-aba,
sem interação do usuário.

---

### Pitfall 6: Estado de navegação (ticker/vencimento/filtro escolhido) não sobrevive à troca de seção — dívida já conhecida (B2) piora com mais divisões

**O que dá errado:**
O PROJECT.md já registra, como backlog aberto e NUNCA resolvido, o item
"B2 (preservar estado ao trocar de aba, sem decisão de abordagem)" da Fase
26 (v1.4) — ou seja, este produto JÁ TEM um problema conhecido e não
resolvido de estado se perdendo ao trocar de aba/seção. A reorganização de
v1.6 aumenta o número de "lugares" na mesma tela (de 2 sub-abas — Setups/
Operar — para N seções por job), o que multiplica as oportunidades desse
problema aparecer: hoje, com tudo numa rolagem só, o usuário escolhe um
ticker no `seletor` e o mesmo estado (`ticker`, `vencimento`, `painel`)
alimenta Bloco A, Bloco B, `LastroDoAtivo` e `LeituraInterna`
simultaneamente, porque são todos filhos do MESMO componente. Se a
reorganização isolar "analisar ticker manualmente" e "comparar vencimentos"
em seções que montam/desmontam (em vez de só ocultar via CSS), o estado
local (`useState` de `ticker`/`vencimento`/`painel` em `OpcoesScreen.jsx:368`
e vizinhos) pode resetar ao trocar de seção — quebrando o fluxo de "vi uma
oportunidade no Bloco A, quero conferir o vencimento dela" se isso virar uma
navegação entre duas seções que não compartilham estado.

**Por que acontece:**
Separar por job tenta ser "cada seção é independente e focada" — o que
empurra naturalmente para componentizar cada seção com seu próprio estado
local, em vez de manter um estado compartilhado no componente pai e só
mudar o que é RENDERIZADO. É a diferença entre "abas que trocam o que
aparece" (estado sobrevive) e "abas que trocam qual componente está montado"
(estado morre se não for hoisted).

**Como evitar:**
Manter `ticker`/`vencimento`/`painel`/outros estados hoje declarados em
`OpcoesScreen.jsx` NO COMPONENTE PAI da reorganização (não descer para
dentro de cada seção nova), e passar como props — igual ao padrão que já
existe para `seletor` (calculado uma vez, injetado em `SubAbaOperar`).
Qualquer seção nova que precise saber "qual ticker está selecionado" recebe
por prop, nunca reimplementa seu próprio `useState` local para isso. Se
alguma seção logicamente PRECISAR de estado próprio (ex.: qual vencimento
está expandido dentro da comparação), esse estado deve ser local só ao
que é puramente visual daquela seção — nunca dados que outra seção também
consome.

**Sinais de alerta:**
Qualquer componente novo de seção que declare `useState(ticker inicial)`
ou `useState(vencimento inicial)` — isso é reimplementação de estado que já
existe no pai, candidato certo a dessincronizar. Teste manual: escolher um
ticker/vencimento numa seção, trocar para outra seção e voltar — se a
seleção sumiu, é o Pitfall 6 acontecendo.

**Fase de tratamento:**
Antes de separar componentes — decidir e documentar no UI-SPEC que
`ticker`/`vencimento`/`painel` continuam vivendo em `OpcoesScreen.jsx` (ou
sobem para lá, se hoje vivessem mais embaixo), nunca descem. Como
verificação pós-fase — teste comportamental (não guardião de texto) que
simula a sequência "seleciona ticker → abre seção B → volta para seção A →
ticker ainda selecionado"; aproveitar para fechar o B2 do backlog nesta
mesma fase, já que a reorganização é o momento natural de resolver esse
padrão de vez, em vez de multiplicá-lo em N seções novas.

---

### Pitfall 7: "Simplificar para quem está aprendendo" remove um atalho que o usuário repetente já usa todo dia

**O que dá errado:**
Duas coisas concretas hoje na tela existem porque servem usuário repetente,
não porque são bonitas: (1) a rolagem única permite comparar visualmente um
candidato do Bloco A contra o gráfico/vencimento dele mais abaixo, na MESMA
tela, sem navegação — um usuário experiente pode ter esse fluxo de "scan
rápido, depois decido" internalizado; (2) o truncamento de vencimentos
(`N_MAX_VENCIMENTOS`, mensagem "os N primeiros de X") já é uma forma de
progressive disclosure que existe HOJE, então a reorganização não está
inventando isso — está decidindo o que fazer com o "resto". Simplificar
"para o iniciante" cortando esse acesso ao "resto" (em vez de só reorganizar
onde ele mora) tira algo que um usuário repetente comparando vencimentos
específicos pode precisar. O v1.6 já decidiu explicitamente NÃO fazer
progressive disclosure adaptativa nesta milestone (Fase 2, fora de escopo,
alvo futuro é a frase-ponte de `OpcoesScreen.jsx:711-714`) — o risco aqui é
alguém, no calor da reorganização, "simplificar" um pouco disso por conta
própria (ex.: esconder o link "ver todos os N vencimentos" atrás de mais um
clique que hoje não existe) achando que é só reorganização, quando na
prática é uma redução de informação disponível.

**Por que acontece:**
"Reorganizar por job" e "reduzir densidade de informação" parecem a mesma
coisa quando a motivação de origem foi "a tela confunde por misturar 5
jobs" — mas o PROJECT.md é explícito que a causa raiz identificada é
MISTURA DE JOBS, não excesso de informação por job; a milestone decidiu
"reorganizar primeiro, personalizar depois" exatamente para não confundir as
duas coisas. É fácil, durante a implementação, resolver ambiguidades de
layout removendo algo "que não parece caber em nenhum job claro" — perdendo
informação que não é redundante, só não tinha um lar óbvio na estrutura por
job.

**Como evitar:**
Tratar QUALQUER remoção de informação/controle hoje visível (não só
reposicionamento) como fora do escopo desta milestone, a menos que
explicitamente aprovada como decisão de produto separada — o PROJECT.md já
modela esse cuidado ("Nenhuma funcionalidade nova — só reorganização/
separação do que já existe"), o mesmo vale ao contrário: nenhuma
funcionalidade REMOVIDA. Se algo não tem job óbvio, a pergunta certa é "em
qual seção esse controle mora", nunca "esse controle ainda é necessário".

**Sinais de alerta:**
Qualquer decisão de design durante a fase que comece com "vamos simplificar
tirando X do fluxo principal e deixando em uma tela secundária/config" onde
X é algo hoje sempre visível sem clique extra (ex.: contagem de vencimentos
truncados, seletor de ticker, LastroDoAtivo). Se o motivo dado for "reduz
densidade" em vez de "pertence a outro job", é sinal de escopo se
expandindo de reorganização para redesign.

**Fase de tratamento:**
Antes de separar componentes — o UI-SPEC deve listar TODO controle/
informação hoje visível na rolagem única e mapear 1:1 para uma seção nova,
sem "descartados". Como verificação pós-fase — comparar a lista de controles
antes/depois (a mesma lista que os guardiões de `test_opcoes_subabas_ui.mjs`
item 11 já verificam por nome) e confirmar que todo item tem seção de
destino, não uma remoção disfarçada de reorganização.

## "Parece Pronto Mas Não Está" — Checklist

- [ ] **Split de Bloco B (curadoria):** verificar se a frase-ponte (D-05)
  migrou junto e continua imediatamente adjacente, sem toggle/colapso novo.
- [ ] **Qualquer bloco movido de arquivo:** rodar
  `grep -rln "OpcoesScreen.jsx" web/tests/*.mjs` de novo e confirmar que
  cada guardião listado foi revisado (não só que a suíte está verde — ler
  se o guardião ainda testa a garantia original ou só passou por acidente).
- [ ] **Seção nova que mostra candidato/proposta:** confirmar que o
  guardrail CVM de manchete (`test_opcoes_subabas_ui.mjs:141-154` ou
  extensão dele) cobre o arquivo novo, não só `SubAbaOperar`.
- [ ] **Estado de erro/degradado por seção:** simular MCP fora do ar e
  confirmar que o aviso aparece a partir do estado inicial da sub-aba
  "Setups", sem precisar abrir a seção onde o erro se origina.
- [ ] **Estado de navegação (ticker/vencimento):** testar manualmente
  trocar de seção e voltar — confirmar que a seleção sobrevive.
- [ ] **Lista de controles antes/depois:** todo controle hoje visível na
  rolagem única tem uma seção de destino identificada, nenhum "sumiu" na
  reorganização.

## Estratégias de Recuperação

| Pitfall | Custo de Recuperação | Passos |
|---------|----------------------|--------|
| Guardião regex quebrado por migração de arquivo (Pitfall 3) | BAIXO | Reescrever o guardião para escanear o novo arquivo/diretório em vez do antigo; nunca só ajustar o número esperado sem reler a garantia original |
| Guardrail CVM sem cobertura em seção nova (Pitfall 4) | MÉDIO | Estender o guardião para varredura por diretório (padrão do item 1 de `test_opcoes_subabas_ui.mjs`); auditoria manual de todo `.manchete` em `web/src/opcoes/*.jsx` alterado na fase |
| Frase-ponte separada fisicamente do Bloco B (Pitfall 2) | BAIXO | Mover o parágrafo de volta para adjacência imediata; não requer mudança de dado, só de layout |
| Estado de navegação resetando entre seções (Pitfall 6) | MÉDIO | Subir o `useState` para o componente pai comum mais próximo; se várias seções já foram publicadas com estado duplicado, precisa de uma fase de consolidação dedicada (mesmo padrão do B2 do backlog) |
| Informação/controle removido sem decisão de produto (Pitfall 7) | MÉDIO-ALTO | Se já publicado, requer nova fase para reintroduzir — pior que não remover, porque agora tem usuário acostumado com a ausência também |

## Mapeamento Pitfall → Fase

| Pitfall | Fase de Prevenção | Verificação |
|---------|--------------------|-------------|
| 1 — Split muda decisão vs. narração | Antes de separar (UI-SPEC/CONTEXT) | Code review: nenhum `.sort()`/`.filter()` em arquivo novo tocando `ctx.curadoria` |
| 2 — Frase-ponte perde adjacência | Durante a separação (mesma task que move Bloco B) | Reler comentário D-05 contra o layout final |
| 3 — Guardião regex cego a migração de arquivo | Antes de separar (mapear guardiões por arquivo-alvo) | `bash scripts/executar.sh --testes` verde E leitura manual de cada guardião tocado |
| 4 — Guardrail CVM sem cobertura em arquivo novo | Antes de separar (decidir no UI-SPEC se seção nova mostra manchete) | Grep manual `\.manchete\b` em todo `.jsx` novo/alterado |
| 5 — Erro/degradado escondido em seção fechada | Antes de separar (classificar cada estado local vs. global no CONTEXT.md) | Teste comportamental com MCP simulado indisponível, estado inicial da sub-aba |
| 6 — Estado de navegação não sobrevive à troca de seção | Antes de separar (decidir hoisting de estado no UI-SPEC) | Teste comportamental de troca de seção ida-e-volta; fechar B2 do backlog nesta fase |
| 7 — Simplificação remove informação de usuário repetente | Antes de separar (mapa 1:1 controle→seção no UI-SPEC) | Comparação de lista de controles antes/depois no code review pós-fase |

## Fontes

- `.planning/PROJECT.md` — Milestone v1.6 (goal, origem, fora de escopo) e
  Milestone v1.4 (histórico da consolidação anterior, D-02 a D-07, backlog
  B2 nunca resolvido)
- `web/src/opcoes/OpcoesScreen.jsx` (linhas 690-830, 360-370) — estrutura
  real de `fraseDuasLeituras`/`blocoOportunidades`/`blocoCuradoria`/
  `blocoVigias`, comentários de decisão D-02/D-04/D-05/D-07 (Fase 32)
- `web/tests/test_opcoes_subabas_ui.mjs` — guardiões de contagem exata
  (`nGate`/`nProposta`), guardrail CVM de manchete, checagem "nada
  desapareceu" por `includes`
- `web/tests/test_opcoes_consolidacao_ui.mjs` — guardião de ordem por
  `indexOf` entre frase-ponte/Bloco A/Bloco B/vigias, guardião "sem
  sticky/input de busca entre a frase-ponte e os vigias"
- CLAUDE.md do repositório (`/Users/acamerini/dev/borisv2/CLAUDE.md`) —
  princípios 4/5/regulatório citados como invariantes desta milestone

---
*Pesquisa de pitfalls para: reorganização por job-to-be-done, aba Opções
sub-aba Setups, Boris+ (b3-agente) — Milestone v1.6*
*Pesquisado: 2026-09-19*
