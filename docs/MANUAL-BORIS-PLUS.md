# Manual de utilização — Boris+

> Origem: mapeamento da experiência completa do app, feito em 12/09/2026 a
> partir de leitura direta de `web/src/App.jsx`, `web/src/copy.js`,
> `web/src/opcoes/OpcoesScreen.jsx`, `server/app/conceitos.py`,
> `server/app/kb.py`, `server/app/skill_ref.py` e `server/app/assistente.py`
> na branch `v2/interacao-estrutural`. Documento vivo — atualize quando a UI
> ou o vocabulário por modo mudar.

## Antes de começar

O Boris+ é um simulador educacional da B3. Os dados de mercado são reais; o
dinheiro é inteiramente fictício. Nenhuma ação do app envia ordem para
corretora, bolsa ou conta bancária — não existe caminho no produto que faça
isso.

O login é obrigatório, porque a conta sustenta a sincronização entre
aparelhos, o Operador do lado do servidor e as notificações. Conta nova
nasce limpa, sem posição de demonstração.

## Os dois modos

| | Modo Estudo | Modo Operador |
|---|---|---|
| Papel da IA | Ensina o raciocínio: indicador, correlação, decisão. Nunca executa. | Interpreta o plano e opera dentro das regras que você definiu. |
| Vocabulário | Professor. Radar, Watchlist, Portfólio. | Mesa de operações. Mesa, Monitoramento, Posições. |
| Execução | Compra e venda simuladas, feitas por você. | O mesmo, mais o ciclo automático do Operador IA. |
| Cor de acento | Azul-esverdeado | Dourado |
| Onde se troca | Perfil, pelo avatar no topo. A troca recarrega o app inteiro — é mudança de registro, não de tema. | |

Verde e vermelho nunca são cor de modo. Nos dois modos eles significam uma
coisa só: compra e venda, ganho e perda.

## Sua primeira sessão, minuto a minuto

Se você nunca usou o app, faça nesta ordem. Leva cerca de vinte minutos e
você sai com uma posição simulada aberta e entendendo por que ela está
aberta.

**0 a 2 min — Entre e veja o tour.** O login é obrigatório. Sua conta nasce
limpa, sem posição nenhuma, com saldo fictício. O tour está no rodapé de
Acompanhar. A tela de Acompanhar estará quase vazia — é o estado correto,
não um erro.

**2 a 4 min — Escolha o modo, e comece no Estudo.** Vá no avatar, no topo,
e abra o Perfil. Confirme que está em Modo Estudo. O Modo Operador faz
sentido depois que você já consegue explicar uma decisão com suas
palavras.

**4 a 8 min — Varra o Radar e leia uma manchete.** Abra o Radar e dispare a
varredura. Escolha um ativo cuja manchete diga para estudar a alta e abra o
card dele. A manchete nunca é escrita pela IA — ela vem do motor de
cálculo. Se não houver plano para aquele ativo, o app diz que não há, em
vez de preencher com opinião.

**8 a 12 min — Toque em um termo sublinhado antes de tocar em qualquer
botão.** No card, palavras como gatilho, confluência e risco aparecem com
sublinhado pontilhado. Toque em uma: a explicação abre ali mesmo, sem sair
da tela, é escrita (não gerada por IA), não custa nada e não gasta cota.
Este é o gesto que mais distingue o Boris+ de qualquer corretora — em todos
os apps pesquisados essa explicação vive num curso separado; aqui ela está
dentro do card, no instante da dúvida.

**12 a 15 min — Agora sim, peça a análise da IA.** No mesmo card, use
Estudar este ativo. A IA lê o pacote técnico que o motor já calculou e
explica em quatro passos: o que cada indicador marca agora, quais
confirmam e quais divergem, como a combinação produz a leitura, e o que
mudaria essa leitura. Isso consome uma análise da sua cota — trinta por mês
e vinte por dia no plano gratuito. Se acabar, o app mostra a explicação
automática, sem IA, e diz claramente que é ela.

**15 a 18 min — Simule a compra e ponha a proteção na mesma visita.**
Informe a quantidade e confirme; em seguida aplique stop e alvo. Não deixe
para depois. Se você digitar zero ou um número inválido, a ordem é recusada
inteira e a recusa entra no histórico com o motivo — não existe ordem pela
metade neste app, por desenho.

**18 a 20 min — Pergunte ao Boris por que você fez isso.** Toque na coruja,
no canto inferior direito. Ele já sabe em que tela você está e o que ela
mostra. Pergunte algo concreto, como o que invalidaria esta entrada. O
Boris lê a resposta em voz alta por padrão; para desligar, vá em
Perfil → IA & Boris.

## O percurso completo, em oito passos

A numeração importa: cada passo depende do anterior.

1. **Escolher o ativo.** Abra o Radar e dispare a varredura. Ela devolve os
   ativos com setup válido, ordenados por confluência, com a manchete vinda
   do motor de cálculo. *Aba Radar (Mesa no Operador).*
2. **Conferir o dado antes de confiar nele.** Todo card carrega a fonte, o
   horário da última atualização e se o dado é tempo real, atrasado ou
   histórico. Se o app não conseguiu medir o frescor, ele diz isso — e não
   é o mesmo que estar em dia. *Selo de frescor, em qualquer card.*
3. **Analisar contexto e risco.** Abra o card completo. A manchete resume,
   os chips destrincham a análise e a régua de posição mostra onde o preço
   está entre suporte e resistência. Toque em qualquer termo sublinhado
   para abrir o verbete. *Watchlist (Monitoramento).*
4. **Enviar a ordem virtual.** Informe a quantidade e confirme. A ordem é
   aceita inteira ou rejeitada inteira — execução parcial não existe no
   modelo, por desenho. *Card do ativo, ou Portfólio.*
5. **Definir stop e alvo.** Sempre disponível. Quando o parecer do motor
   diz para não operar, isso é opinião, não veto: a proteção nunca é
   bloqueada. *Card do ativo, ou Portfólio.*
6. **Acompanhar a execução simulada.** No Modo Operador, o ciclo automático
   cuida de trailing stop, alvo dinâmico e avisos de gatilho, com
   kill-switch para interromper tudo. Em qualquer modo, o histórico
   registra cada decisão, inclusive as recusadas e o motivo. *Portfólio →
   Operador IA e Histórico.*
7. **Ver o resultado sem maquiagem.** Patrimônio, caixa, exposição,
   resultado aberto e realizado, drawdown — ganho e perda com o mesmo peso
   visual. *Acompanhar, Portfólio.*
8. **Entender o porquê e comparar.** Peça a explicação à IA e compare sua
   evolução com o benchmark. Quando não houver evidência suficiente, a
   resposta correta é dizer isso. *Assistente, em qualquer tela;
   Acompanhar.*

## Como usar a IA sem desperdiçar cota

O app tem duas camadas de explicação, e elas custam coisas diferentes. A
primeira é escrita à mão e não passa por modelo nenhum: os verbetes do card
e o resumo do Boris. Custam zero, respondem na hora e funcionam com a cota
esgotada. A segunda chama o modelo: análise do ativo, aprofundamento do
Radar, sugestão de stop e alvo, e as perguntas livres.

A regra prática: tente sempre a camada de graça primeiro. Se a dúvida é o
que significa este número, ela é de graça. Se a dúvida é o que este
conjunto de números diz sobre este ativo hoje, aí vale gastar.

### Como perguntar, e como não perguntar

| Pergunta | Por quê |
|---|---|
| ✓ O que invalidaria esta entrada? | Boa. A resposta sai dos números da tela e ensina a reconhecer a saída. |
| ✓ Por que a confluência caiu de quatro para três sinais? | Boa. Compara estados que o app mediu e mostra o raciocínio. |
| ✓ Meu drawdown de 4,1% é alto para o risco que escolhi? | Boa. A IA vê seu patrimônio, seu resultado e seu perfil de risco no pacote da tela. |
| ✗ PETR4 vai subir amanhã? | Não responde, e está certo em não responder — o app não promete resultado. |
| ✗ Quanto rendeu o CDI no ano passado? | A IA só cita número que está no pacote da tela; se não está lá, ela diz que a informação não aparece. |
| ✗ Devo comprar agora? | No Modo Estudo o verbo de ordem é proibido. Ela descreve a condição e devolve a decisão para você. |

### Como ler a resposta

Toda resposta de IA vem com um rótulo dizendo que é conteúdo educacional e
não recomendação. Esse rótulo também distingue quando o texto veio do
modelo e quando veio da explicação automática do app — o que acontece
quando a cota acaba.

Se a IA disser que não há dados suficientes, isso é recurso, não defeito:
ela foi instruída a declarar a lacuna em vez de preencher. O mesmo vale
para a frase sobre não haver operação com vantagem estatística clara — é
uma frase fixa, vinda do motor.

Uma separação que vale decorar: **a manchete do card é do motor, a
explicação abaixo é da IA.** Se as duas parecerem discordar, a manchete é a
que manda. A IA explica; ela não decide.

## A rotina de um dia

- **Antes da abertura — Olhe o Radar e não toque em nada.** A varredura do
  dia e o plano de cada candidato já estão montados. Decidir antes da
  abertura é metade do treino.
- **Durante o pregão — Responda ao gatilho, não ao preço.** O app avisa
  quando a condição é atingida, com o carimbo da barra em que isso
  aconteceu. Agir antes do gatilho é o erro mais comum; o estado esticado
  existe justamente para dizer que você chegou tarde.
- **Depois do fechamento — Confira o histórico, inclusive as recusas.** As
  ordens rejeitadas ficam registradas com o motivo, e ensinam mais que as
  aceitas.
- **Uma vez por semana — Abra Eficiência da IA e compare com o
  benchmark.** Mostra taxa de acerto, expectância e curva de risco em R.
  Precisa de pelo menos dez operações para dizer algo, e avisa quando a
  amostra é pequena em vez de exibir um número bonito e sem base. Acerto
  alto com expectância baixa significa ganhar muitas vezes pouco e perder
  poucas vezes muito — é a lição que mais dói e a mais útil.

## Onde fazer cada coisa

| Quero… | Vá para | Observação |
|---|---|---|
| Descobrir um ativo | Radar | A varredura se perde ao trocar de aba nesta versão. Decida antes de sair. |
| Seguir um ativo de perto | Watchlist | Análise completa no Estudo, plano no Operador. |
| Comprar ou vender simulado | Watchlist ou Portfólio | Ordem é tudo ou nada. |
| Pôr stop e alvo | Card do ativo | Nunca bloqueado, mesmo com parecer contrário. |
| Ver o que já fiz | Portfólio → Histórico | Inclui ordens rejeitadas, com o motivo. |
| Ligar a automação | Portfólio → Operador IA | Só no Modo Operador. |
| Ler opções da B3 | Opções | Leitura. Esta versão não executa ordem de opção por aqui. |
| Trocar de modo | Perfil → Modos | Recarrega o app inteiro. |
| Rever o tour | Perfil → Ajuda | Não cobre Acompanhar nem Opções nesta versão. |
| Entender um número do card | Toque no sublinhado | De graça. Não gasta cota e funciona sempre. |
| Pedir a leitura da IA | Card → Estudar este ativo | Gasta uma análise da cota. |
| Perguntar qualquer coisa | Coruja, canto inferior | Já sabe em que tela você está. Não funciona na aba Opções nesta versão. |
| Ver quanto gastei de IA | Perfil → Atividade da IA | Mostra o mês; o limite diário de 20 não aparece nesta versão. |
| Usar minha própria chave | Perfil → IA & Boris | Sai de todos os limites do app; o gasto passa a ser seu no provedor. |
| Desligar a voz do Boris | Perfil → IA & Boris | Vem ligada por padrão. |

## Estados que você vai encontrar

- **"Mercado fechado"** — Fora do pregão. Os preços exibidos são do último
  fechamento e o app diz isso.
- **"Dado atrasado"** — A cotação chegou, mas não é do instante; o app
  mostra o horário real da leitura.
- **"Frescor não medido"** — Diferente de atrasado: o app não conseguiu
  saber. Ele não afirma que está em dia.
- **"Quantidade inválida."** — Zero, negativo ou não numérico. A ordem é
  recusada inteira e a recusa entra no histórico com o motivo.
- **"Serviço de opções não configurado"** — A credencial do serviço de
  dados de opções não chegou ao servidor. É configuração, não falha de
  rede.
- **"Serviço de opções sem resposta agora"** — A credencial existe, mas o
  serviço não respondeu ou recusou. Nada foi consumido da sua cota.
- **"Cota do dia esgotada"** — O teto diário de chamadas foi atingido. Zera
  no dia seguinte, no horário de Brasília.
- **"Não há dados suficientes para concluir."** — A resposta correta da IA
  quando a evidência não sustenta uma conclusão. É recurso, não erro.

## Vocabulário do app

| Termo | Significado |
|---|---|
| Setup | Configuração técnica nomeada que o motor reconhece no gráfico. Quem decide se existe é regra determinística, nunca a IA. |
| Confluência | Quantos sinais independentes apontam para a mesma direção. É o critério de ordenação do Radar. |
| Armado · Gatilho · Esticado | Os três estados de timing: condição montada e não disparada; o momento do disparo; preço já corrido demais para a entrada original. |
| Risco em R | A distância entre entrada e stop, usada como unidade. Um alvo "2R" mira o dobro do que se arrisca. |
| Trailing stop | Stop que acompanha o preço a favor e nunca contra, protegendo ganho já conquistado. |
| Alvo dinâmico | Alvo que se estende quando o movimento continua, com freio por extensão e por relação risco-retorno. |
| Kill-switch | Interrupção geral do ciclo automático. Deixa o Operador IA parado até ser religado. |
| Faixa de liquidez | Três classificações para opções: negociável, difícil e sem mercado. Difícil pede consentimento explícito. |
| Frescor | Há quanto tempo o dado foi medido. "Não medido" é um dos três estados possíveis. |
| Drawdown | A maior queda do topo até o fundo no período. Mede o pior momento, não o resultado final. |
| Carimbo de versão | O par no rodapé: versão do aplicativo e versão do servidor. Confira aqui quando uma correção não aparecer. |
| Pacote técnico | O conjunto de números que o motor calcula e entrega pronto para a IA. Ela só pode citar número que esteja nele. |
| Verbete | Explicação escrita à mão, sem IA. Custo zero, resposta instantânea, texto diferente por modo. |
| Cota | Quanto de IA você pode usar: 30 análises por mês, 20 por dia, R$ 1,00 por dia de perguntas livres, no plano gratuito. |
| Chave própria | Usar sua própria credencial de modelo em vez da cota do app. Remove todo limite; o gasto passa a ser seu no provedor. |
| Expectância | Quanto você ganha por operação, em média, somando acertos e erros. Pode ser negativa com taxa de acerto alta. |

## O que o Boris+ nunca faz

- Enviar ordem para corretora, bolsa ou conta bancária. Não existe esse
  caminho.
- Deixar a IA calcular saldo, preço médio, resultado, custo ou drawdown.
  Todo número vem de regra determinística.
- Inventar valor quando a fonte falha. Mostra o estado real e impede a
  operação que dependeria do dado inválido.
- Prometer rentabilidade, garantir acerto ou usar linguagem de
  enriquecimento rápido.
- Esconder perda ou apresentar resultado com distorção visual.
- Apresentar simulação como recomendação de investimento.
- Deixar a IA escrever a manchete do card — ela vem do motor; a IA explica
  o que está abaixo dela.
- Usar as expressões "sinal de compra", "sinal de entrada", "hora de agir"
  ou "chegou o momento" — são proibidas no texto do assistente.
- Citar um número que não esteja no pacote da tela. Se faltar, a resposta
  correta é dizer que a informação não aparece.
- Mandar notificação com verbo imperativo de operação.

---

*Documento gerado a partir da análise de UX e da camada de IA de
12/09/2026. Referências completas com arquivo:linha estão no artefato de
análise correspondente e no prompt de execução das melhorias propostas.*
