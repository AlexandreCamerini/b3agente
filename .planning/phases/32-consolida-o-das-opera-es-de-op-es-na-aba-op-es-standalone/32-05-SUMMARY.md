---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
plan: 05
subsystem: release
tags: [verificacao-ao-vivo, checkpoint, publicacao, railway, opcoes]

# Dependency graph
requires:
  - phase: 32-03
    provides: "blocos cross-carteira na aba Opções + LinhaChamadaOpcoes em Posições"
  - phase: 32-04
    provides: "SubAbaOperar multi-candidato; App.jsx sem PropostaDaPosicao"
provides:
  - "Evidência de que a cadeia de execução do collar curado não foi tocada (auditoria 32-05-AUDITORIA.md)"
  - "Verificação ao vivo dos 10 itens do roteiro, com execução REAL nos dois ramos (venda coberta por clique, collar pelo mesmo executarCandidato+store)"
  - "Consolidação publicada em produção sob o carimbo F10-20260916-01, com push nas DUAS branches"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ramo inalcançável por clique no ambiente mock é exercitado pelo MÓDULO real servido pelo Vite (import('/src/opcoes/executarCandidato.js') + store real), nunca por reimplementação do caminho no teste — o que se prova é o código de produção, não uma cópia dele"

key-files:
  created:
    - .planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/32-05-AUDITORIA.md
  modified:
    - web/src/version.js
    - server/app/main.py
    - server/web_dist
---

# Plano 32-05 — Auditoria, verificação ao vivo e publicação

## Task 1 — Auditoria de não-regressão

Evidência completa em `32-05-AUDITORIA.md` (commits `a8ea8be`, `7c24de2`).
Veredito: **LIMPA**.

Um ponto foi reaberto pelo executor como achado-condicional e **resolvido pelo
orquestrador**: o item 1 manda conferir que o diff da fase não toca
`executarCandidato.js`, `persistence.js`, `api.js` nem `server/app/`. Pelo
range literal do plano (`main...HEAD`) ele listava esses arquivos — mas a
branch LOCAL `main` estava parada em `54ff538` (rascunho da Fase 31). A
referência correta é `origin/main` (`df34cb6`), que é **ancestral direto** do
HEAD (0 atrás, 28 à frente). Pelo range correto:

```
git diff --name-only origin/main...HEAD | grep -E "executarCandidato|persistence|web/src/api|^server/app/"
→ (vazio)
```

Consequência prática: a Task 3 não precisou do merge que o plano previa — foi
fast-forward. Os demais itens da auditoria (2 a 7) passaram sem ressalva:
suíte 2923 passed + 152 `.mjs` exit 0, `vite build` verde, 11/11 guardiões
nominais, nenhuma contagem de `ok(` reduzida contra o baseline `bd459f1`.

## Task 2 — Verificação ao vivo (checkpoint bloqueante)

Ambiente: `api-qa-opcoes` (mercado aberto + `B3_OPTIONS_PROVIDER=mock`) + `web`
dev. Conta de dev com PETR4/VALE3 travadas; ITUB4, BBDC4 e BBAS3 comprados
durante a sessão para produzir lastro livre (sem lastro livre o motor marca a
posição como `ignorada` e não há candidato algum — foi a primeira leitura
enganosa da sessão, e é comportamento CORRETO do motor, não defeito).

| # | Item | Resultado |
|---|------|-----------|
| 1 | Posições sem os blocos | OK — uma linha discreta com seta; nenhuma tira, nenhuma lista das 4, nenhum acordeão dentro dos cards de posição |
| 2 | Contagem bate (D-03) | OK — linha "4 oportunidades de opções nas suas posições"; a lista curada mostrou exatamente 4 cartões; a aba abriu sem ativo pré-selecionado |
| 3 | Frase-ponte (D-05) | OK — visível acima dos dois blocos, sem controle de recolher |
| 4 | Rótulos (D-05) | OK — "CONFIRMADAS PELA LEITURA TÉCNICA" × "AS 4 MELHORES… inclusive as que a leitura técnica ainda não confirma" |
| 5 | Execução real | OK nos dois ramos — detalhe abaixo |
| 6 | "Ver posição" no painel inline | OK — abriu a sub-aba Operar com BBAS3 já selecionado (não ficou inerte nem só rolou) |
| 7 | Erro de busca | OK — bloco: "a busca falhou" + CTA "Tentar de novo"; linha em Posições: "Não foi possível verificar agora", SEM número zero |
| 8 | Multi-candidato | **NÃO EXERCITADO** — ver limitação abaixo |
| 9 | Modo Estudo | OK — cards viram "ESTUDO · …", linguagem condicional, cartões da lista nem são `button`, zero "Executar estrutura" em qualquer bloco |
| 10 | Rolagem (D-06) | OK — desktop e 375px; `scrollWidth == clientWidth` (sem overflow horizontal), nada fixo cobrindo conteúdo |

### Item 5 — execução real, ramo venda coberta (clique de verdade)

Card "1. ITUB4 · venda coberta, strike 32" → confirmação inline → "Executar
estrutura".

- posição aberta: `ITUB4MOCK06C`, call **vendida**, strike 32, qty 300,
  lastro `{t: ITUB4, qty: 300}`, `ivEntrada 0.35`
- caixa: R$ 62.539,00 → R$ 62.734,00 (**+R$ 195,00**, exatamente o prêmio
  anunciado no card)
- ITUB4 passou a `qtyTravada: 300`

### Item 5 — execução real, ramo collar

No provedor mock a razão prêmio÷perda das vendas cobertas é sempre maior, então
**nenhum collar entra no top-4** — o ramo era inalcançável por clique. Em vez de
declarar cobertura que não existia, o elo foi exercitado com o MESMO código de
produção servido pelo Vite (`import('/src/opcoes/executarCandidato.js')` +
`store` real de `persistence.js`), usando um candidato de collar gerado pelo
motor de verdade (`_curadoria_scan_posicao` para BBDC4):

- despacho resolvido: **`optionsCuradoriaAbrirCollar`** (correto)
- corpo: `{underlying, idCandidato, pernasContratos: [{contractSymbol, lado} ×2],
  contratos}` — sem `expiration`, conforme a quick `260915-ndt`
- resultado: **duas pernas abertas de verdade** — `BBDC4MOCK06C` call vendida
  strike 31 qty 400 + `BBDC4MOCK04P` put comprada strike 29 qty 400
- caixa inalterado (R$ 55.454,00), correto: prêmios iguais no mock → collar de
  custo líquido zero

O que ficou fora desse caminho é apenas o clique/confirmação do card, que o
ramo de venda coberta exercitou no mesmo componente.

### Limitação registrada — item 8

O ramo multi-candidato só renderiza quando a leitura técnica endossa put
isolada E collar na MESMA posição (MULTI-01, Fase 19). As 5 posições testadas
voltaram `candidatos: []` com proposta única — o mock não produz essa
coexistência. Cobertura hoje é o guardião estático
`test_opcoes_multi_candidato_ui.mjs`, cuja sanidade o Plano 32-04 comprovou por
injeção real de defeito. **Fica como dívida de verificação**: o ramo
multi-candidato nunca foi visto rodando.

### Aprovação

Alex aprovou explicitamente no checkpoint, com ciência da limitação do item 8 e
do `deferred-items.md`, e liberou a publicação.

## Task 3 — Bump, publicação e push

1. `origin/main` já era ancestral do HEAD → **nenhum merge necessário**
   (fast-forward), ao contrário do que o plano previa.
2. `bash scripts/bump.sh` → `F10-20260915-02` → **`F10-20260916-01`**.
3. `bash scripts/publicar-web.sh` → build + `server/web_dist` regenerado
   (1.7M) + `SERVER_BUILD_ID` sincronizado. **Nenhum hunk manual no dist.**
   O script precisou rodar fora do sandbox: `npm ci` exige o registry e o
   sandbox derruba o TLS ("failed to copy trust settings of system
   certificate"), o mesmo falso-negativo que os executores dos planos
   anteriores já tinham documentado.
4. Comentário do `SERVER_BUILD_ID` reescrito à mão para descrever ESTA entrega
   — o script sincroniza só o valor. O texto da entrega anterior (quick
   `260915-ndt`) foi preservado como HISTORICO na mesma linha, conforme o
   guardrail de não reescrever histórico.
5. `bash scripts/executar.sh --testes` depois do bump: **exit 0**, 2923 passed,
   5 skipped, 3 xfailed + `web/tests/*.mjs` todos OK.
6. Commit `6c74b94` (`chore(32-05): publica a consolidacao das opcoes`).
7. Push nas DUAS branches: `v2/interacao-estrutural` e `HEAD:main`.
   `git rev-parse HEAD` == `git rev-parse origin/main` == `6c74b94`.
8. Carimbo em produção confirmado por HTTP — ver seção abaixo.

## Verificação do deploy

`https://boris.semente.dev/api/health` respondia `F10-20260915-02` no momento
do push (deploy do Railway em andamento) e passou a responder
**`F10-20260916-01`** depois do redeploy, confirmando que a consolidação está
no ar.

## Issues Encountered

- **Item 1 da auditoria** reaberto pelo executor por usar a branch local `main`
  (atrasada) como referência em vez de `origin/main`. Resolvido pelo
  orquestrador; nenhuma correção de código foi necessária.
- **Estado de teste deixado no banco local de dev**: 5 posições (PETR4, VALE3,
  ITUB4, BBDC4, BBAS3) e 4 pernas de opção, incluindo o collar de BBDC4.
  Dinheiro virtual, banco local — não toca produção nem a conta do Alex em
  produção.
- **Sandbox derruba `npm ci` e `curl` para localhost**: os passos de build e as
  consultas ao backend local precisaram sair do sandbox ou passar pelo browser.

## Self-Check: PASSED
