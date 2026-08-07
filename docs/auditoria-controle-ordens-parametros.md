# Auditoria — módulos de controle de ordens e parâmetros

Pedido do Alex, 2026-08-07: "não me deixa mais selecionar o modo executar" +
auditoria geral pra organizar o app e não repetir este tipo de erro.

## O bug relatado agora — causa raiz, achada ao vivo

Não é regressão de nenhuma entrega desta sessão. Consultei o banco de
produção (read-only): `config.appMode` continua `"estudo"` — nunca mudou,
a sessão inteira. É exatamente por isso que o botão "Executar" está
desabilitado: essa é a trava da Fase A, que o próprio Alex confirmou como
comportamento correto ("No Modo Estudo só estará disponível o modo
sinalizar").

**O que está errado não é a trava — é que ela é presencialmente muda.**

```jsx
// App.jsx:3596-3601
const desabilitado = m === "executar" && !operador;
<button onClick={() => !desabilitado && putAg({ mode: m })} disabled={desabilitado}
  title={desabilitado ? "Disponível no Modo Operador — ..." : undefined}
  ...>
```

`title` é a ÚNICA explicação imediata — e `title` não existe em toque
(WKWebView/iOS não tem hover). Tocar no botão desabilitado não faz
NADA: sem toast, sem navegação, sem pista. Existe um parágrafo abaixo
explicando o motivo (`App.jsx:3606-3610`), mas ele não diz ONDE trocar de
modo — porque o toggle de verdade (`appMode`) não mora nesta tela, mora em
**Perfil → Modo de trabalho** (`ModoTrabalhoCard`, `App.jsx:1779`), uma tela
totalmente diferente, sem link nenhum daqui pra lá.

**Desbloqueio imediato**: Perfil → Modo de trabalho → Operador → aceitar o
termo. Isso resolve o "não me deixa selecionar" hoje. O resto desta
auditoria é sobre por que isso não devia precisar de mim pra descobrir.

## Achado estrutural: dois "Operador" que não são a mesma coisa

| Nome que o usuário vê | O que é de fato | Onde mora | Efeito |
|---|---|---|---|
| Aba **"Operador IA"** | Tela de configuração do agente (mode, rules, trailing, entrada automática, intervalo) | Nav inferior, sempre visível em qualquer modo | Painel de controle — mas metade dos controles fica muda sem o outro toggle |
| **"Modo Operador"** (dentro de "Modo de trabalho") | `config.appMode` — identidade do app inteiro (Estudo × Operador): vocabulário, disclaimers, e o PORTÃO que libera "Executar" em toda a tela acima | Perfil → Modo de trabalho, com termo de aceite | É o interruptor mestre — mas fica escondido numa tela que nada na "Operador IA" aponta |

Mesma palavra, dois lugares, um deles secretamente comanda o outro. Um
usuário que abre "Operador IA" (nome convidativo, é a aba que promete
controlar o agente) e tenta ligar "Executar" não tem como adivinhar que
precisa ir a OUTRO lugar primeiro — e quando o app não reage ao toque, a
leitura mais natural é "quebrou", não "falta um passo em outro menu".

`appMode === "operador"` é recalculado de forma independente em pelo menos
11 lugares do arquivo (`App.jsx:1581,1779,1954,3044,3529,4029,5155,5855,
6271,6412...`) — cada tela deriva sozinha a mesma pergunta. Não é bug (dá
o mesmo resultado em todos), mas é sintoma: não existe UM lugar canônico
que represente "o modo atual e como mudá-lo", existe uma pergunta repetida
by grep.

O mesmo padrão de "explica mas não linka" se repete em pelo menos DOIS
pontos da mesma tela:
- `App.jsx:3606-3610` (Executar/sinalizar)
- `App.jsx:3745-3749` (Entrada automática)

Ambos dizem "Disponível no Modo Operador" e nenhum dos dois tem um botão
que leve pra lá.

## Outros achados nos módulos de ordens/parâmetros (contexto desta sessão)

Três bugs REAIS de dado (não de UX) já foram corrigidos hoje — listados
aqui porque fazem parte do mesmo território e a causa raiz de todos era a
mesma categoria de erro: **um estado importante mudava num lugar que outro
lugar não enxergava**.

1. **Stop/alvo apagava sozinho** (`App.jsx`, painel de editar posição) — sair
   do campo vazio salvava `null` sem confirmação. Corrigido: F10-20260807-04.
2. **Carteira nativa (iPhone) não sincronizava com o servidor** — `buy`/
   `sell`/`putPosition` no `deviceStore` eram 100% locais; o Operador no
   servidor nunca via o que o usuário configurava no aparelho. Este é o
   MESMO formato de erro do item acima, em escala maior: estado partido em
   dois lugares (aparelho × servidor) sem sincronização. Corrigido:
   F10-20260807-05.
3. **Ciclo só rodava no intervalo agendado** (até 60min) — um gatilho
   recém-armado ficava invisível até o próximo tick. Corrigido:
   F10-20260807-06.

O fio comum dos 3 + o achado de hoje: **o app tem vários "estados que
decidem se uma ordem dispara" guardados em lugares diferentes
(appMode, agent.mode, agent.serverEnabled, agent.rules.*, position.stop/
alvo — no aparelho OU no servidor) e nenhuma tela mostra os quatro juntos
com clareza sobre qual depende de qual.**

## Prioridade de ação

1. **(Alto, mecânico) Linkar o portão.** Nos dois pontos que já explicam
   "Disponível no Modo Operador" (`App.jsx:3606`, `3745`), trocar o
   parágrafo mudo por um botão que navega direto pra Perfil → Modo de
   trabalho. Elimina o "não deixa selecionar" sem mexer em nenhuma regra.
2. **(Alto, mecânico) `title` nunca sozinho.** Trocar `title={...}` nos
   controles desabilitados por texto sempre visível (já existe o parágrafo
   — só falta o link do item 1) ou um toast ao tocar num controle
   desabilitado, pra WKWebView nunca depender de hover.
3. **(Médio, estrutural) Um card de status único.** No topo de "Operador
   IA", ANTES de qualquer controle, um resumo dos 3-4 interruptores que
   decidem se uma ordem dispara (Modo do app · Operador no servidor ·
   Executar/sinalizar) com estado atual de cada um e link direto pra
   trocar — hoje isso está espalhado pela tela e um deles nem está na tela.
4. **(Médio, nomenclatura) Resolver a colisão "Operador".** Não
   necessariamente renomear (mexe em cópia estabelecida) — mas pelo menos
   a aba "Operador IA" precisa deixar claro, no topo, que ela CONTROLA os
   parâmetros mas não É o interruptor mestre — esse mora em Perfil.
5. **(Baixo, código) `operador` como valor derivado único.** Os 11+ lugares
   que recalculam `appMode === "operador"` poderiam ler de um único lugar
   (contexto/memo) — não é bug hoje, mas cada novo local que esquecer de
   checar via a mesma lógica é um bug potencial amanhã.

## O que NÃO é bug (evitar retrabalho)

- Trailing desligado (`rules.trailing: false`) — nunca foi ligado, é
  default, não é erro.
- `entradaAuto`/`alvoDinamico` nunca configurados — mesma coisa, opt-in que
  ninguém ligou ainda, UI já existe e funciona (conferido nesta sessão).
- `agent.mode: "executar"` salvo mas inerte — é o valor antigo do campo,
  correto ele existir e ficar sem efeito enquanto `appMode !== "operador"`
  (é exatamente a trava da Fase A funcionando).

## Próximo passo

Itens 1 e 2 são pequenos, mecânicos, e resolvem o sintoma relatado agora —
proponho fazer os dois já. Itens 3-5 são maiores (tela nova, decisão de
nomenclatura, refactor) e merecem aprovação separada antes de eu montar
código. Confirma o escopo?
