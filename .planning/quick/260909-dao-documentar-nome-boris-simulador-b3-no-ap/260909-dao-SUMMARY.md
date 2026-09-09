---
quick_id: 260909-dao
status: complete
date: 2026-09-09
files_modified:
  - TESTFLIGHT.md
---

# Summary — 260909-dao

## O que foi entregue

`TESTFLIGHT.md`, item 7 corrigido: nome do App Store Connect atualizado de
"Boris+" para **"Boris+ Simulador B3"**, com nota explicando o campo e o
achado ao vivo — para a próxima pessoa não repetir o mesmo erro de digitar
"Boris+" sozinho e receber a mesma rejeição da Apple.

## O achado

Durante o upload do build 10 (TestFlight), a Apple recusou a criação do
registro no App Store Connect: "App Record Creation failed... The App Name
you entered is already being used." Busca confirmou apps "Boris" já
publicados hoje (ex. um app de dividir conta chamado simplesmente "Boris").

Isto não é defeito de código nem toca guardrail nenhum: são três campos
diferentes, e só um precisa ser único na App Store inteira.

| Campo | Onde vive | Único na loja? |
|---|---|---|
| Bundle id `com.alexandrecamerini.bolsia` | Xcode/Apple Developer | Não |
| `CFBundleDisplayName` ("Boris+" sob o ícone) | Embutido no app | Não |
| App Name (App Store Connect) | Ficha da loja | **Sim** |

O Alex escolheu "Boris+ Simulador B3" entre 4 variantes apresentadas
(recomendada, uma mais curta, uma mudança mínima, e a opção de digitar
outra). Decisão de marca dele, registrada aqui.

## Escopo — documentação apenas

Nenhum código tocado. `scripts/instalar-iphone.sh` continua setando
`CFBundleDisplayName=Boris+` — o nome sob o ícone do aparelho não muda.

## Validação

Documentação apenas. Sem suíte a rodar.

## Pendência (do Alex, fora do repo)

Cadastrar o app no App Store Connect com o nome novo e retomar o upload do
build 10 pelo Organizer do Xcode.
