# Toque longo → assistente do setor

Substituir a afordância do "?" por um gesto único de segurar a tela, e fazer o
assistente explicar o **setor** onde o dedo parou.

Leia antes de começar: `.claude/skills/didatica-bolsia/SKILL.md` (vocabulário
por modo, princípios de dado, guardiões, caminho de deploy). Esta spec não
repete o que está lá.

## Objetivo

Quem nunca operou precisa conseguir perguntar "o que é isto?" apontando para o
que está vendo, sem antes descobrir que existe um "?" de 18 pixels. O gesto é
o mesmo em qualquer lugar da tela: segurar por ~600 ms sobre um setor abre a
explicação daquele setor.

O app continua servindo dois mundos. O gesto não pode custar nada a quem já
sabe operar: no Operador ele existe, é silencioso e nunca abre sozinho.

## O problema, medido

| Fato | Onde |
|---|---|
| Um card pode exibir **6** "?" simultâneos (gatilho, barra 15m, confluência, fundamento, stop/alvo, R) | [App.jsx:2377](web/src/App.jsx:2377), [:2388](web/src/App.jsx:2388), [:2680](web/src/App.jsx:2680), [:2682](web/src/App.jsx:2682), [:2718](web/src/App.jsx:2718), [:2734](web/src/App.jsx:2734) |
| Numa watchlist de 6 ativos isso são até 36 alvos idênticos na mesma rolagem | mesma lista |
| O círculo visível tem 18 px dentro de um alvo de 44×44 com `margin: -13px` | [`ConceitoDot`](web/src/App.jsx:2117) |
| A explicação do setor só é alcançável por esse círculo (ou pela via proativa, que é one-shot por conceito, para sempre) | [App.jsx:2340‑2360](web/src/App.jsx:2340) |

O alvo de toque está correto pela HIG; o que falha é a **descoberta** — 18 px
de contorno fraco repetidos dezenas de vezes não são lidos como "toque aqui
para entender", são lidos como ruído tipográfico.

## Restrições que o código já decidiu

Confirme cada uma antes de contrariá-la; nenhuma é opinião.

1. **Gesto é código de app.** `web/capacitor.config.ts` usa `webDir: "dist"`
   sem `server.url` — o bundle web vai **dentro do binário**. Texto vindo da
   API muda com o deploy do Railway; JavaScript novo só chega ao iPhone com
   `bash instalar.sh --iphone`. Planeje a verificação nessa ordem: navegador
   primeiro, aparelho depois do build.
2. **O contrato do assistente já serve setor.** `POST /api/assistente` recebe
   `{tela, snapshot, pergunta}` e `tela` é string livre cortada em 40 chars
   ([assistente.py:180](server/app/assistente.py:180)). `tela: "setor:<id>"`
   não pede mudança de contrato.
3. **`campos` é allowlist no backend** ([conceitos.py:55](server/app/conceitos.py:55)).
   Setor novo escolhe conceitos existentes; não inventa chave de dado nova no
   cliente.
4. **O assistente exige conta e tem teto.** Anônimo recebe 401; o freio é
   `B3_ASSISTENTE_TETO_BRL` (padrão 1,00) contra `kv:assistenteGasto`. Um gesto
   mais fácil de disparar aumenta a chance de bater no teto — a camada
   determinística tem que responder primeiro.
5. **Gesto não é acessível sozinho.** VoiceOver e teclado não têm "segurar por
   600 ms". Um caminho equivalente por foco/toque precisa continuar existindo.

## Decisões desta spec

**O "?" sai da repetição, não da existência.** Cada card mantém **um** ponto de
entrada visível — um rótulo discreto no rodapé do card ("segure para
entender") que aparece nas primeiras N aberturas e some depois — e os seis
`ConceitoDot` por card saem do fluxo visual. Remover todos sem deixar nada
visível transformaria a camada didática em conhecimento oral.

**Setor é uma região declarada, não uma inferência.** Envolver cada bloco do
card num componente `SetorAlvo` que declara `{ setorId, dados }`. O gesto lê o
setor mais interno sob o dedo. Nada de `document.elementFromPoint` com
heurística de proximidade: a explicação precisa ser reprodutível.

**O registro de setores é servido pelo backend, não hardcoded no front.** O
mapeamento `setorId → conceito primário → "veja também"` entra na resposta de
`GET /api/conceitos` (chave `setores`), ao lado do catálogo. Motivo: a
restrição mais cara deste projeto é o build iOS — com o registro no servidor,
repontear um setor ou mudar o encadeamento é deploy do Railway; só **região
nova na tela** exige `instalar.sh --iphone`. O front declara regiões; o
backend decide o que cada uma explica. Isso também dá a F2 a allowlist de
graça: `setorId` fora do registro é 400.

**A folha abre no soltar do dedo, sempre.** O `ConceitoSheet` já abre primeiro
e busca depois ([App.jsx:2192](web/src/App.jsx:2192) — `setC(null)` e fetch em
seguida); o gesto herda esse orçamento. Segurar 600 ms e receber uma tela
travada esperando rede desfaz a confiança que o gesto acabou de pedir. O
título vem do catálogo já carregado em memória; os parágrafos ancorados
preenchem quando a API responder.

**Segurar entrega o determinístico; o assistente continua opt-in.** O toque
longo abre a folha com a explicação de `conceitos.py` (grátis, ancorada nos
números daquele card) e o botão do assistente por baixo, como hoje. Fazer o
gesto chamar a LLM direto inverte a relação de custo e quebra o Princípio 1.

**600 ms, não 2 000.** O iOS dispara o *callout* nativo perto de 500 ms; 2 s é
mais que o dobro do que qualquer app do sistema ensina e a maior parte das
pessoas solta antes. Suprima o callout no alvo e cancele o gesto se o dedo
andar mais que ~10 px (é rolagem) ou se um segundo dedo tocar a tela.

O gesto novo compete com handlers que já existem — resolva a matriz inteira,
não caso a caso:

| Gesto existente | Onde | Convivência exigida |
|---|---|---|
| Arrasto da folha (pointer) | [App.jsx:1359](web/src/App.jsx:1359) | Toque longo não dispara dentro de folha aberta |
| Swipe por touchstart | [App.jsx:6190](web/src/App.jsx:6190) | Movimento >10 px cancela o toque longo, nunca o contrário |
| Toque curto no card | `AtivoCard` | Soltar antes de 600 ms preserva o clique |
| Callout/seleção nativos do iOS | WKWebView | `-webkit-touch-callout: none` + `user-select: none` só nos setores |

**Descoberta se mede, não se supõe.** Um contador local (aberturas por gesto ×
aberturas pelo ponto de entrada visível) entra na config sincronizada — é ele
que decide o N da dica e valida os 600 ms com dado real, em vez de revisitar
os dois números por opinião.

**Voz entra medida, não presumida.** A saída falada (`speechSynthesis`) e a
entrada por voz (`SpeechRecognition`) têm disponibilidades diferentes dentro
do WKWebView do Capacitor. Meça as duas no aparelho antes de projetar
qualquer UI de voz — a resposta muda o custo da fase inteira.

## Fases

**F1 — o gesto e o setor determinístico.**
`SetorAlvo` envolvendo os blocos do `AtivoCard`; hook de toque longo com
cancelamento por movimento/multi-toque; folha abrindo com o conceito primário
do setor; os `ConceitoDot` repetidos saem; a dica única entra; caminho
acessível equivalente preservado. Um setor com mais de um conceito abre no
primeiro e oferece os outros pelo "veja também" que já existe.

**F2 — o assistente do setor.**
`tela: "setor:<id>"` e snapshot igual ao bundle que ancorou a explicação. A
lista de `setorId` válidos é allowlist no backend, junto do catálogo — id
desconhecido responde 400, não vira prompt.

**F3 — voz.**
Só depois da medição. Se a síntese funcionar no WKWebView, "ouvir esta
explicação" é um botão dentro da folha, sem servidor no meio. Entrada por voz
depende de plugin nativo e é decisão de escopo do Alex, não desta spec.

## Critérios de aceite

Cada item entrega evidência, não afirmação.

- No navegador: segurar 600 ms sobre cada setor do card abre a folha correta,
  com os números daquele ativo; rolar com o dedo iniciado sobre um setor não
  abre nada; toque curto mantém o comportamento anterior do card.
- Nenhum `ConceitoDot` remanescente no `AtivoCard` além do ponto de entrada
  único decidido em F1 — verificável por `grep -n ConceitoDot web/src/App.jsx`.
- `/api/assistente` com `tela: "setor:inexistente"` responde 400; com setor
  válido e sem conta, 401.
- Regressão do assistente vale para o caminho novo: "devo comprar PETR4
  agora?" via `tela: "setor:*"` recusa sem usar "sinal de compra" nem "hora de
  agir" — mesmo caso já medido manualmente no ESTADO-Didatica.md, agora pelo
  gesto.
- Verificação visual ao vivo, com screenshot na entrega: gesto em cada setor,
  dica única, folha abrindo no soltar, Operador sem abertura espontânea. Na
  entrega anterior, 3 defeitos só apareceram na verificação ao vivo — teste de
  comportamento não substitui olhar a tela.
- `/api/timing` continua com as mesmas 20 chaves e nenhum campo novo.
- Modo Operador: o gesto existe, nada abre sozinho, e o vocabulário na folha é
  o de `vocab["operador"]`.
- Suítes verdes e a saída colada na entrega:

```bash
cd server && ./.venv/bin/python -m pytest -q
```

```bash
cd web && for t in tests/*.mjs; do node "$t" >/dev/null || echo "FALHOU: $t"; done
```

- Guardião novo que trava o comportamento novo: cancelamento por movimento e
  resolução do setor mais interno. Comportamento sem guardião volta sozinho.
- Campo de config novo (dica vista, gesto desligado) entra nos **dois** stores
  de `web/src/persistence.js`; `web/tests/test_api_parity.mjs` cobre parte.

## Deploy

`web/src/version.js` (`BUILD_ID`, `F10-AAAAMMDD-NN`, data real) →
`bash scripts/publicar-web.sh` → `bash atualizar.sh --somente-deploy "msg"` →
conferir o carimbo em `/api/health`. Estando fora da `main`, o `atualizar.sh`
imprime "verificado" sem ter publicado nada; o carimbo é a única prova.

O iPhone só recebe o gesto com `bash instalar.sh --iphone`. Com o registro de
setores no backend, planeje o que vai em cada veículo: texto, encadeamento e
reponteamento de setor viajam no deploy; região nova e o hook do gesto viajam
no build.

**Pós-entrega:** atualizar `.claude/skills/didatica-bolsia/SKILL.md` com o
registro de setores (onde mora, como estender, o que exige build vs. deploy) —
é a skill que impede a próxima sessão de re-derivar tudo isto.

## O que não fazer

- Não deduzir o setor por coordenada e proximidade — a explicação tem que ser
  a mesma toda vez que o dedo cai no mesmo lugar.
- Não deixar o gesto ser o único caminho: sem alternativa acessível, a camada
  didática deixa de existir para quem usa VoiceOver.
- Não chamar a LLM no gesto. O determinístico é grátis, completo e imediato.
- Não montar vocabulário no front. A frase vem pronta do backend, de
  `skill_ref`.
- Não embutir conceito na resposta de `/api/timing` — o isolamento do Operador
  é estrutural.
- Não aumentar o teto do assistente para acomodar mais toques; o desenho é que
  segura o custo.
- Não usar 2 s. Meça o tempo real de decisão com o gesto em mãos antes de mexer
  no valor.

## Aberto para o Alex

- **Ponto de entrada visível:** dica no rodapé do card que some depois de N
  aberturas, ou um "?" único no cabeçalho do card, permanente. A primeira
  ensina e sai do caminho; a segunda nunca deixa ninguém preso.
- **Entrada por voz:** custa plugin nativo e um build. Decidir depois da
  medição de F3.
