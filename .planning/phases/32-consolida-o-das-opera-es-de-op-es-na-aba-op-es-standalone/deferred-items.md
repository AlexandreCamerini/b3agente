# Deferred items — Fase 32

Itens achados durante a execução da fase, fora do escopo do plano que os
achou, registrados aqui em vez de corrigidos silenciosamente ou ignorados.

## `|| 0` em `porLote`/CTA de collar — três cópias do mesmo padrão pré-existente

**Achado em:** 32-02 (Task 3), ao adicionar `CuradoriaEstruturas.jsx` e
`CandidatoOpcao.jsx` à allowlist `ARQUIVOS` de
`web/tests/test_opcoes_analisar_ui.mjs` (item 4 do plano).

**O que é:** a regra "null nunca vira 0" (`OU_ZERO`, seção 10 desse
guardião) reprovou dois trechos:

```js
// web/src/opcoes/CuradoriaEstruturas.jsx:91
const porLote = item ? (v) => (typeof v === "number" ? v * (item.qtyAcoes || 0) : null) : null;

// web/src/opcoes/CandidatoOpcao.jsx:57
const porLote = (v) => (typeof v === "number" ? v * (p.qtyAcoes || 0) : null);

// web/src/opcoes/CandidatoOpcao.jsx:143-144 (CTA do collar)
price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0))
```

Se `qtyAcoes`/`custoLiquidoTotal` viessem `null`/`undefined` num candidato
real, o `|| 0` faria o valor renderizar "R$ 0,00" em vez de "—" —
exatamente o que o princípio 4 do `CLAUDE.md` proíbe (não inventar valor
quando o dado falta).

**Por que não foi corrigido nesta fase:** os TRÊS trechos são cópias
idênticas do MESMO helper `porLote`/CTA de collar, incluindo
`web/src/opcoes/PropostaLastreada.jsx:200,268-269` (Fase 28) — que nunca
esteve na allowlist `ARQUIVOS` deste guardião e por isso nunca foi
flagrado. Corrigir só as duas cópias tocadas por este plano criaria
divergência entre três cópias do mesmo helper; corrigir as três é maior
que o escopo de "extração verbatim" do 32-02 (`files_modified` do plano não
inclui `PropostaLastreada.jsx`).

**Mitigação temporária:** `test_opcoes_analisar_ui.mjs` ganhou uma exceção
datada e nomeada (`ARQUIVOS_EXCECAO_OU_ZERO`) que exclui só
`CuradoriaEstruturas.jsx`/`CandidatoOpcao.jsx` da seção 10, com comentário
explicando a razão e a referência cruzada a `PropostaLastreada.jsx`. A
regra `OU_ZERO` em si NÃO foi afrouxada — continua valendo para os outros
arquivos da allowlist, e continua reprovando o padrão onde ele não é
esperado.

**Risco real:** BAIXO. `qtyAcoes` é a quantidade de ações por trás de uma
posição de opção REAL (candidatos vêm só de posições existentes na
carteira); `custoLiquidoTotal` só é lido depois de `p.caixa` já ter sido
confirmado truthy no ponto de chamada. Nenhum dos dois é um campo que a
fonte de mercado externa costuma omitir — é defesa contra um estado que,
na prática, não deveria ocorrer para um candidato válido.

**Sugestão para fase futura:** trocar as três cópias de
`v * (X || 0)`/`(Y || 0)` por um guard explícito
(`typeof X === "number" ? v * X : null` / `typeof Y === "number" ? Y : null`),
nas TRÊS cópias na mesma task, e então remover a exceção
`ARQUIVOS_EXCECAO_OU_ZERO` do guardião.

## RESOLVIDO (2026-09-16, quick `260916-g6p`)

As TRÊS cópias (`CuradoriaEstruturas.jsx`, `CandidatoOpcao.jsx`,
`PropostaLastreada.jsx`) foram corrigidas na mesma task, exatamente como a
sugestão acima descrevia: `porLote` e os quatro call sites do CTA de collar
trocaram `v * (X || 0)`/`Math.abs((p.caixa && Y) || 0)` por um guard
explícito que ENVOLVE a operação (`typeof X === "number" ? v * X : null` /
`p.caixa && typeof Y === "number" ? Math.abs(Y) : null`), sem alterar o
guard `p.caixa &&` que protege o acesso.

`PropostaLastreada.jsx` entrou na allowlist `ARQUIVOS` de
`web/tests/test_opcoes_analisar_ui.mjs`, e a exceção
`ARQUIVOS_EXCECAO_OU_ZERO` foi removida — a regra `OU_ZERO` (seção 10)
volta a cobrir os três arquivos sem exceção nenhuma. Prova negativa real
feita (reintroduzir `|| 0` à mão, confirmar falha nomeando o arquivo,
reverter e confirmar diff limpo) — ver `260916-g6p-SUMMARY.md`.
