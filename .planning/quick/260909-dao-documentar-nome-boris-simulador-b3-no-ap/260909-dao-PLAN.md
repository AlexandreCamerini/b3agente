---
quick_id: 260909-dao
description: documentar nome "Boris+ Simulador B3" no App Store Connect (colisão de nome resolvida)
date: 2026-09-09
status: executing
---

# Quick 260909-dao — App Name da loja ≠ nome do app

## Achado (ao vivo, durante o TestFlight do build 10)

Apple recusou a criação do registro no App Store Connect: "App Record
Creation failed... The App Name you entered is already being used." Busca
na App Store confirmou o motivo plausível — existem múltiplos apps "Boris"
publicados hoje (ex. o app de dividir conta "Boris",
`apps.apple.com/ca/app/boris/id6755980288`), e a checagem de unicidade da
Apple é ampla, não string exata.

Isto NÃO é um problema de código nem viola guardrail nenhum do CLAUDE.md:
são TRÊS campos diferentes, e só um precisa ser único na loja inteira:

| Campo | Onde vive | Único na loja? | Afetado |
|---|---|---|---|
| Bundle id `com.alexandrecamerini.bolsia` | Xcode/Apple Developer | Não | Não |
| `CFBundleDisplayName` ("Boris+" sob o ícone) | Embutido no app | Não | Não |
| **App Name** (App Store Connect) | Ficha da loja | **Sim** | **Sim** |

O Alex escolheu, entre 4 opções apresentadas, **"Boris+ Simulador B3"** para
o App Name. Decisão de marca dele, registrada aqui — não decidida pelo
agente.

## Escopo — DOCUMENTAÇÃO APENAS

Corrigir `TESTFLIGHT.md` item 7, que hoje instrui "nome **Boris+**" sem
mencionar a possibilidade de colisão nem o nome que de fato vai ser usado.
Sem isso, a próxima pessoa (ou eu, numa sessão futura) repete o erro.

Nenhum código tocado. `scripts/instalar-iphone.sh` (que seta
`CFBundleDisplayName=Boris+`) permanece INALTERADO — o nome sob o ícone
continua "Boris+", só a ficha da loja muda.

## Task

`TESTFLIGHT.md`, item 7: trocar "nome **Boris+**" por "nome **Boris+
Simulador B3**" e acrescentar uma nota curta explicando o porquê (App Name é
único na loja inteira; `CFBundleDisplayName` sob o ícone continua "Boris+")
e o achado ao vivo, para o histórico do checklist.

## Validação

Documentação apenas — sem suíte a rodar, sem `vite build`. Critério de
aceite: quem seguir o item 7 de agora em diante digita o nome certo de
primeira.
