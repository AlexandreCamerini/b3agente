---
quick_id: 260910-mqs
phase: quick-260910-mqs
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py]
autonomous: true
---

<objective>
Achado A-00 (CRÍTICO) da auditoria de 2026-09-10: `POST /api/buy` aceita `qty`
negativo ou zero e EXECUTA a ordem. Reproduzido com TestClient real:
`{"t":"PETR4","qty":-500}` → 200 OK, grava posição de 100 ações e debita
R$ 3.000. Junto, A-00b: `qty` não numérico devolve 500 com o texto cru da
exceção Python em vez de 400.

**Não é defeito da aba de Opções.** É bug pré-existente da rota principal de
compra, achado pela auditoria. Entra na mesma branch por conveniência; o
SUMMARY deve deixar isso explícito para quem revisar o PR #39.
</objective>

<context>
Causa: `server/app/main.py:2091` — `qty = int(body.get("qty") or 0)`.
Negativo passa direto; zero vira falsy e escapa; string não numérica levanta
`ValueError` sem tratamento.

A guarda EXISTE nos dois irmãos, e é deles que se copia o padrão:
- `POST /api/sell` (`main.py:2190-2210`): distingue AUSENTE (`None`) de
  ZERO/NEGATIVO explícito, converte sob `try/except (TypeError, ValueError)`,
  grava `store.registrar_rejeicao(...)` antes de levantar (só quando
  `scope is not None` — o balde anônimo é compartilhado, T-04-12/T-02-07), e
  levanta `HTTPException(400, "Quantidade inválida.")`.
- `POST /api/options/buy` (`main.py:2298`): `qty <= 0` rejeita.

A compra ficou de fora porque a venda ganhou a sua guarda na regressão
F10-20260819, que era específica de venda total silenciosa.
</context>

<tasks>
<task type="auto">
  <name>Task 1: guarda de qty na compra + testes de regressão</name>
  <files>server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py</files>
  <action>
  1. LEIA `/api/buy` inteira antes de mudar. Descubra o comportamento atual
     para `qty` AUSENTE e PRESERVE-O — a compra pode ter default de lote.
     Não invente mudança de contrato.
  2. Validar `qty` cobrindo três casos: não numérico → 400; `<= 0` → 400;
     ausente → comportamento atual, intacto.
  3. Posição da guarda: decida lendo o código e explique no comentário. O
     ticker inválido já rejeita antes (`main.py:2094-2100`); `qty` inválido
     com ticker VÁLIDO também tem de rejeitar, e a rejeição precisa do
     ticker já normalizado para gravar no histórico.
  4. Rejeição de conta logada grava no histórico:
     `store.registrar_rejeicao(_conn, "COMPRA", t, qty_cru, None, motivo,
     user_id=scope, origem="manual")`, mesmo padrão do FIX-C02 na própria
     rota. Anônimo não grava.
  5. Mensagem ao usuário: exatamente `"Quantidade inválida."` — mesma string
     da venda, para a UI não ganhar variante nova. Motivo do histórico no
     padrão da venda.
  6. Comentário de decisão citando A-00, a data, e por que a guarda não
     existia.
  7. Testes em `server/tests/test_fase5_rejeicao_rotas.py`, espelhando
     `test_sell_qty_zero_400_regressao_f10_20260819` (linhas 173-193):
     negativo → 400 + posição inalterada + entrada `rejeitada`/`COMPRA`;
     zero → idem; `"abc"` → 400 com a mensagem, NUNCA 500.
  8. Atualizar a tabela do docstring do arquivo de teste (linhas ~20-25) com
     os casos novos e nota da auditoria.
  </action>
  <verify>
  RED/GREEN obrigatório: rodar os testes novos contra o código ANTES da
  correção (`git show HEAD:server/app/main.py` para arquivo temporário FORA
  do repo — nunca `git stash`) e confirmar a falha; depois com a correção e
  confirmar que passam. Registrar as duas saídas no SUMMARY.
  Depois: `bash scripts/executar.sh --testes` inteira.
  </verify>
  <done>Suíte verde e os três testes novos provados RED antes, GREEN depois.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. Front não é editado (sem `vite build`). Sem deploy, sem
bump, sem Railway, sem publicação.
</success_criteria>
