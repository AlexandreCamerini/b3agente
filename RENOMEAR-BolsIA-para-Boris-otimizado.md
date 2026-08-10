# Aposentar o nome BolsIA em favor de Boris

## Objetivo

O produto se chama **Boris+**. O nome **BolsIA** ainda aparece em 87 arquivos
(223 linhas), em diretórios e na identidade das plataformas. Automatize a troca
onde ela é segura e reversível; leve as decisões irreversíveis para o Alex com
o custo declarado, em vez de executá-las.

## O que já existe — parta daqui, não do zero

**`scripts/atualizar-identidade.sh`** já faz este trabalho, é idempotente e tem
o escopo pensado. Ele está travado em `APP_ID="com.alexandrecamerini.bolsia"` /
`APP_NAME="BolsIA"` e já cobre: `capacitor.config.ts`, `index.html` (título +
metas iOS/PWA), `vite.config.js` (manifest PWA), `disclaimers.js`,
`configurar-apns.sh`, `setup-ios.sh`, `ios-allow-http.sh`, `main.py`
(docstring + title do FastAPI) e `test_fase3_operador.py`.

O cabeçalho dele também **declara o que deliberadamente não muda**: pastas
`b3-agente/`, `package.json` `"b3-agente-web"`, env vars `B3_*` e os registros
em `qa/`. Essa decisão continua válida — `b3-agente` é codinome interno, não a
marca; trocá-lo é custo sem retorno.

Generalizar esse script é a espinha do trabalho. Um script novo em paralelo
criaria duas fontes de verdade para a mesma migração.

## Zonas de risco — o que a automação faz e o que ela não faz

### Zona 1 — troca automática (o script executa)

Texto visível e comentários: `.md` de documentação viva, strings de UI,
comentários de código, mensagens de script. `BolsIA` → `Boris+` quando é nome
de produto exibido; `Boris` quando é sujeito de frase ("o Boris calcula").

Regra de caixa: preserve a do original (`BOLSIA` → `BORIS`, `bolsia` →
`boris`), e nunca gere `Boris+ +` ao passar sobre texto já migrado.

### Zona 2 — troca automática com contrato acoplado (mesma execução, atômica)

- `window.__bolsiaSocial` → `window.__borisSocial`. O contrato tem **três**
  pontas: `web/src/social.js` (define), `web/src/App.jsx` (consome) e
  `web/tests/test_social_login.mjs` (trava). As três mudam juntas ou nenhuma —
  meia migração aqui é login social morto no aparelho.
- `.claude/skills/didatica-bolsia/` → `didatica-boris/`. Renomeie o diretório
  **com `git mv`** e atualize quem cita o nome (a `description` da skill e
  qualquer referência em docs).

### Zona 3 — histórico: não tocar

`qa/*.md`, `ESTADO-*.md`, `CHECKOUT-*.md` e `RELEASES.md` são registros
datados. Reescrever "BolsIA" ali falsifica o que foi decidido na época. Se
quiser contexto para quem ler depois, acrescente **uma linha** no topo dos
índices (`RELEASES.md`, `qa/00-sumario.md`): "BolsIA foi renomeado para Boris+
em 10/08/2026; documentos anteriores preservam o nome da época."

### Zona 4 — identidade de plataforma: decisão do Alex, não do script

`com.alexandrecamerini.bolsia` é o **bundle id**. Trocá-lo não é renomear: é
publicar um app diferente. Consequências, para constar na decisão:

| O que acontece | Por quê |
|---|---|
| App novo na App Store | O bundle id é a identidade do app; o antigo não "vira" o novo |
| Todo login Sign in with Apple quebra | O `sub` que identifica o usuário é emitido **por bundle id** — ninguém reentra na própria conta |
| Certificado/topic APNs refeitos | `APNS_TOPIC` no Railway, chave `.p8`, App ID no portal |
| Instalações existentes ficam órfãs | Quem tem o app instalado não recebe atualização |

O usuário **não vê** o bundle id. Recomendação: manter, e migrar só o que
aparece — `CFBundleDisplayName`, nome na loja, ficha. Se o Alex decidir trocar
mesmo assim, isso vira um plano à parte com o portal da Apple, não uma linha de
`sed`.

Trate igual o diretório-raiz do repositório (`/Users/acamerini/dev/bolsia/`):
renomeá-lo quebra o `server/.venv` (caminho absoluto em `pyvenv.cfg` e nos
`activate`) e os **5 worktrees registrados**, cujos ponteiros são absolutos.
Se ele quiser mesmo, é procedimento com recriação de venv e
`git worktree repair` — descreva o custo e deixe a decisão com ele.

## Como o script deve se comportar

- **Idempotente**: rodar duas vezes não muda nada na segunda.
- **`--verificar`**: mesma varredura, zero escrita, relatório do que mudaria.
  É o modo padrão de quem está com medo — e deve ser barato de rodar.
- **`git mv`** para diretórios e arquivos, preservando histórico.
- **Recusa-se a rodar com a árvore suja**, para o diff da migração ficar
  isolado e reversível com um `git checkout`.
- **Relatório final** por zona: quantos arquivos, quantas ocorrências, e a
  lista explícita do que foi deixado de lado e por quê.

## Critério de aceite

Com evidência real colada na resposta — saída de comando, não afirmação:

1. `bash scripts/executar.sh --testes` verde (baseline atual: **753 backend +
   67 suítes web**). O `test_social_login.mjs` é o que prova a Zona 2.
2. `npx vite build` limpo — o `App.jsx` é grande e um rename cego quebra
   sintaxe com facilidade.
3. `git grep -i bolsia` devolve **apenas** Zona 3 (histórico) e Zona 4
   (identidade de plataforma). Qualquer outra sobra é migração incompleta.
4. Rodar o script uma segunda vez não produz diff.
5. `bash scripts/atualizar-identidade.sh --verificar` passa com a identidade
   nova.
6. O app sobe e a tela de login mostra a marca certa — captura de tela.

## Fora de escopo

Trocar o bundle id, renomear `b3-agente`/`B3_*`/`b3-agente-web`, reescrever
histórico em `qa/`, e mexer no domínio `boris.semente.dev` (já correto).

## Nota de execução

Entregue no escopo acima. Decida sozinho o rotineiro — nomes de variável,
formato do relatório, onde cortar Zona 1 × Zona 3 num arquivo ambíguo. Se
discordar de alguma zona, diga em uma frase e siga com a sua escolha, deixando
a divergência registrada no relatório final.
