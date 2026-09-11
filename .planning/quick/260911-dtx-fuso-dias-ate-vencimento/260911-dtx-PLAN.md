---
quick_id: 260911-dtx
phase: quick-260911-dtx
plan: 01
type: quick
wave: 1
depends_on: [260911-dcq]
files_modified: [server/app/options_api.py, server/app/main.py, server/app/mydata_client.py, server/tests/test_fuso_dias_ate_vencimento.py]
autonomous: true
---

<objective>
Achado D-2, **segunda parte** — a que tem consequência financeira, não
cosmética. O cálculo de DIAS ATÉ O VENCIMENTO usa `date.today()` sem fuso em
cinco pontos. Produção roda em UTC, então das 21:00 às 23:59 BRT o "hoje" já
virou e o prazo sai **um dia a menos**.
</objective>

<context>
A cadeia, verificada:

1. `server/app/options_api.py:35` — `_days_to()` faz
   `(d - dt.date.today()).days` e alimenta `daysToExpiration` (`:94`), que por
   sua vez decide um `riskFlag` em `:214` (`<= 21` dias).
2. `server/app/opcoes_lastreadas.py:22` — `_dias_ate(expiration, hoje)` recebe
   o dia **por parâmetro** (bom desenho, injetável e testável). Quem passa
   `dt.date.today()` naive são os chamadores: `main.py:2515, 2540, 2741`.
3. `server/app/mydata_client.py:202` — `date.today() - timedelta(...)` monta a
   janela de datas do histórico.

**Onde o dia a menos muda decisão:** `opcoes_lastreadas.py:261` recusa o
candidato fora da faixa `_PRAZO_MIN_DIAS (15) <= dias <= _PRAZO_MAX_DIAS (60)`.
Um contrato que vence em exatamente 15 dias é candidato às 20:59 BRT e deixa
de ser às 21:01 — a proposta some da tela sem nada ter mudado no mercado. O
mesmo vale na borda dos 60 e no `riskFlag` dos 21 dias.

Padrão já estabelecido (três quicks desta semana): `BRT = timezone(
timedelta(hours=-3))` local ao módulo, com comentário de decisão; guardião
cravando o relógio num instante em que UTC e BRT caem em DIAS diferentes.
</context>

<tasks>
<task type="auto">
  <name>Task 1: o "hoje" do prazo é o dia de Brasília</name>
  <files>server/app/options_api.py, server/app/main.py, server/app/mydata_client.py, server/tests/test_fuso_dias_ate_vencimento.py</files>
  <action>
  Corrigir os cinco pontos para o dia BRT:
  - `options_api._days_to`: internamente, `datetime.now(BRT).date()`;
  - `main.py:2515, 2540, 2741`: o `dt.date.today()` que viaja como argumento
    `hoje` para `opcoes_lastreadas`. **NÃO** mude a assinatura de
    `_dias_ate`/`propor`/`proposta_fechar` — receber o dia por parâmetro é o
    que os torna testáveis, e os módulos de opções são puros por guardião
    (`test_opcoes_fronteira.py`): não podem ganhar import de relógio. Um
    helper de data BRT em `main.py` (ou reuso do que já existir lá) é o
    caminho; **verifique se `main.py` já tem um** antes de criar outro.
  - `mydata_client.py:202`: idem, no mesmo padrão do módulo.

  **Cuidado com os módulos puros**: `opcoes_lastreadas.py`, `opcoes_motor.py`,
  `opcoes_payoff.py` e `opcoes_gatilho.py` são varridos pelo guardião de
  fronteira e não podem importar nada de rede/relógio. A correção é nos
  CHAMADORES. Se você se vir editando um desses quatro, parou no arquivo
  errado.

  Guardião `server/tests/test_fuso_dias_ate_vencimento.py`:
  (a) relógio cravado em 01:30 UTC (= 22:30 BRT do dia anterior) e
      `_days_to("<data>")` devolve o prazo contado do dia de Brasília;
  (b) **prova de impacto no gate, que é o ponto desta task**: um contrato que
      vence em exatamente `_PRAZO_MIN_DIAS` dias contados de BRT é aceito por
      `opcoes_lastreadas.propor` no mesmo instante em que o cálculo naive o
      recusaria. Monte pelo caminho real (a função recebe `hoje`; prove que o
      chamador passa o dia certo), não por mock da função de prazo.
  (c) o mesmo para a borda dos 60 dias e para o `riskFlag` de 21 dias.
  </action>
  <verify>
  RED/GREEN: rodar o guardião contra o código de ANTES (`git show HEAD:<arquivo>`
  para arquivos temporários FORA do repo — NUNCA `git stash`) e confirmar que
  o candidato na borda é RECUSADO antes e ACEITO depois. É essa a prova que
  vale; a do prazo isolado é só o degrau.
  Depois: `bash scripts/executar.sh --testes`.
  </verify>
  <done>Contrato na borda do prazo não muda de classificação por causa do relógio do servidor.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. Os quatro módulos puros de opções NÃO são tocados. Front
não é editado. Deploy só-backend — NÃO fazer.
</success_criteria>
