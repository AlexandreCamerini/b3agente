---
quick_id: 260916-cod
slug: fecha-achados-pos-fase-32
date: 2026-09-16
status: complete
build_id: F10-20260916-02
tags: [opcoes, principio-4, code-review, verificacao-ao-vivo, publicacao]
---

# Quick 260916-cod — fecha os achados pós-Fase 32

Fecha os três achados do code review da Fase 32 (WR-01, IN-01, IN-02) e a
dívida de verificação do item 8 (ramo multi-candidato nunca visto rodando).
Em produção sob `F10-20260916-02`.

## Commits

| Commit | O quê |
|--------|-------|
| `5498253` | plano da quick |
| `fba6445` | WR-01 — linha de chamada e bloco B não afirmam vazio antes de medir |
| `8365799` | IN-01/IN-02 — higiene da extração (+ 6 asserções reconciliadas em `test_curadoria_ui.mjs`) |
| `5a35850` | bump + publicação (`F10-20260916-02`) |

## Task 1 — WR-01

O achado era mais largo do que o review descreveu: **os dois** call sites de
`ctx.curadoria` tinham o mesmo defeito, não só a linha em Posições.
`CuradoriaEstruturas.jsx` (Bloco B da aba Opções) caía no mesmo ramo
`top.length === 0 && !carregando && !erro` e dizia "nenhuma estrutura elegível"
antes de a flag `curadoriaAtiva` ligar.

Correção: `useCuradoria` expõe `concluido` (nasce `false`, vira `true` no
`.finally()` da primeira busca — cobre sucesso e falha). `LinhaChamadaOpcoes`
trata `carregando || !concluido` como "ainda não medi", antes do ramo de vazio;
`CuradoriaEstruturas` recebe `concluido` como prop e deriva `naoMedido`, usado
nos três ramos; `OpcoesScreen` repassa o campo.

`carregando` **não** foi reusado para isso de propósito: ele significa
"requisição em voo", e sobrecarregá-lo reintroduziria o "Verificando…" eterno
que o comentário original do hook previne. O comentário foi atualizado com a
nota e a referência a WR-01, não apagado.

O executor registrou honestamente que a correção **mascara** a janela de render
em vez de eliminá-la: a cadeia de dois saltos de efeito (flag liga por efeito,
busca dispara por outro efeito) continua existindo — o que muda é que a UI não
pinta mais uma afirmação falsa durante ela. Para o usuário, o comportamento
observável está correto; a latência de dois ticks permanece e não é defeito.

**Guardião** (`test_opcoes_consolidacao_ui.mjs`, regra 13) provado por injeção
real de defeito: removido o `|| !concluido`, o guardião acusa 2 falhas e sai 1;
revertido, passa e o `git diff` fica limpo.

**Prova ao vivo, caminho frio** (reload + ida direta a Posições, com
`MutationObserver` gravando cada texto que a linha exibe):

```
["Verificando oportunidades de opções…→", "⚡4 oportunidades de opções nas suas posições→"]
```

Nunca exibe vazio antes de medir.

## Task 2 — IN-01 / IN-02

- Imports órfãos `PayoffChart`/`estruturaParaPayoff` removidos de `App.jsx`
  (zero uso confirmado por grep).
- `.map((item) => …)` → `.map((cand) => …)` em `CuradoriaEstruturas.jsx`; o
  `item` de escopo do componente ficou intacto.
- **Deviation fora da lista `<files>`**: o rename quebrou 6 asserções de
  `test_curadoria_ui.mjs` (guardião pré-existente, não listado no plano) que
  hardcodavam `item.idCandidato`/`item.tipo`/`money(item.premioTotal)`.
  Corrigido em lockstep, com nota datada, sem enfraquecer a asserção semântica.
  Só apareceu ao rodar a suíte `.mjs` completa — rodar o teste-alvo isolado não
  teria pego.

## Task 3 — item 8 fechado: o ramo multi-candidato foi visto rodando

A fixture foi **escolher a posição certa**, não alterar código: a coexistência
put isolada + collar só ocorre quando `propor()` entra no ramo
`tipo == "put_protecao"`, que exige plano com `decisao == "VENDER"` ou
`lado == "baixa"` (`opcoes_lastreadas.py:247`) — aí o collar é tentado
incondicionalmente ao caixa. Com leitura de alta ou plano vazio a função devolve
`sem_setup` e nunca há dois candidatos. As sessões anteriores só tinham testado
posições de alta/lateral, por isso o ramo parecia inalcançável.

Consultando `/api/scan`, quatro ativos tinham plano de baixa (VIVT3, ABEV3,
LREN3, USIM5). Comprando **ABEV3 500 cotas** (lastro livre + caixa suficiente
para a put isolada):

- `/api/options/proposta/ABEV3?multiperna=1` → `motivo: "put_protecao"`,
  `candidatos: ["put_protecao", "collar"]`
- sub-aba Operar renderizou **dois cartões lado a lado**: "PUT DE PROTEÇÃO"
  (5× PUT ABEV3 strike 30,00) e "TRAVA PROTETORA" (5× TRAVA ABEV3 call 31,00 /
  put 30,00)
- geometria medida no DOM: mesma linha (`y=399` nos dois), **mesma largura**
  (210px cada), `x=165` e `x=385` — exatamente o que o item 8 exigia

Nenhum arquivo de `server/app/` ou `web/src/` foi alterado para produzir o
cenário.

## Task 4 — publicação

`origin/main` era ancestral do HEAD (fast-forward, sem merge). `bump.sh`
`F10-20260916-01` → `F10-20260916-02`; `publicar-web.sh` regenerou
`server/web_dist` (nenhum hunk manual); comentário do `SERVER_BUILD_ID`
reescrito à mão preservando o anterior como HISTORICO. Suíte pós-bump: **exit
0, 2923 passed + 152/152 `.mjs`**. Push nas DUAS branches, `HEAD ==
origin/main == 5a35850`. Carimbo confirmado por HTTP em
`boris.semente.dev/api/health`.

## Efeito na Fase 32

`32-VERIFICATION.md` estava `human_needed` por causa do item 8. Com o ramo
multi-candidato visto renderizando, a única razão daquele status deixou de
existir — a atualização do relatório está registrada junto deste fechamento.

## Nota de processo

O executor sinalizou (em vez de silenciar) que o harness dele pede HALT quando
o branch não está no namespace `worktree-agent-*`. Aqui é o comportamento
esperado: o projeto tem `workflow.use_worktrees=false`, então executores rodam
na árvore principal, na branch `v2/interacao-estrutural`. Confirmado pelo
orquestrador.

## Self-Check: PASSED
