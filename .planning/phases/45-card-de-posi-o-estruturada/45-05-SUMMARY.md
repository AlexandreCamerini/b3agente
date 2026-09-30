# 45-05 — Verificação final e checkpoint humano

Plano de verificação (sem código novo). Task 1 executada pelo orquestrador (sem
subagente, por custo: era só rodar comandos); Task 2 (checkpoint humano)
respondida pelo Alex em 2026-09-29/30.

## Task 1 — verificação automatizada

- `cd web && npx vite build`: ok (exit 0) em cada onda.
- Suíte canônica (`bash scripts/executar.sh --testes`, fora do sandbox, após
  `cd web && npx cap copy ios`): verde (pytest 3136 passed, 5 skipped,
  3 xfailed; todos os `web/tests/*.mjs` [OK]) no fechamento das ondas 1, 2, 3,
  depois das correções pós-teste local e no estado final (HEAD `d68e5ff0`).
- Regressões achadas e corrigidas no caminho (não eram do plano):
  - onda 1: comentário de `copy.js` com a âncora proibida "trava protetora"
    (`test_opcoes_collar_vocab.py` varre comentários) — reescrito (`88c53923`).
  - onda 2: 3 guardiões web (`test_opcoes_consolidacao_ui`,
    `test_concentracao_carteira`, `test_carteira_opcoes_tira`) — hook/card
    movidos para fora da fatia, `BotaoAtualizarEstrutura` extraído, contagem
    de `store.optionsProposta(` atualizada com nota (`fd90d67d`, `5cd869b6`,
    `62d94b89`).
- Invariantes de escopo (`git diff 8242c016..HEAD`): `persistence.js` e
  `api.js` sem diff; `server/app` só `skill_ref.py` (ESTRUTURA_CARD) e o bump de
  `SERVER_BUILD_ID` em `main.py`; nenhuma rota nem store novos.

## Task 2 — checkpoint humano

Teste local (2026-09-29, banco temporário, UGPA3 1000 @ 39,50 + collar
call 42,00 vendida ×10 / put 33,25 comprada ×10; provedor sem rede e provedor
mock): ver "Correções pós-teste local" e "Investigação: ask × último negócio"
em `45-04-SUMMARY.md`. Screenshots em `/tmp/claude-501/t45/shots/` (não
versionados).

Decisões do Alex:

M1 (24px): aprovado
M7 (link histórico): aprovado
P4 follow-up AtivoCard: não
Encerrar: renomear (feito — "Ver encerramento em Opções…")
STOP: tirar duplicado (feito)
números (ask × último negócio): investigado, sem alteração de motor

## Estados observados

- vigente: observado ao vivo (provedor mock, strikes fictícios; não com o collar real)
- ate_5_dias: observado ao vivo (provedor mock, vencimento 02/10/2026)
- exercicio_provavel: observado ao vivo (provedor mock, collar real com spot 30,00)
- premio_indisponivel: observado ao vivo (provedor padrão sem rede)
- vencida: observado ao vivo (provedor mock, vencimento 20/09/2026)
- carregando: não reproduzido (gap) — rápido demais para capturar
- falha: observado ao vivo no iPhone do Alex (backend de produção sem a Fase 44:
  "Estrutura indisponível agora…", card atual preservado, sem aviso falso)

## Dívida conhecida

- `TravaPill` legado (`AtivoCard` e card atual): `negative` sobre
  `negativeTint10` mede 4,18 no tema claro (reprova AA). O contorno do card novo
  mede ≥ 4,79. P4: sem follow-up decidido.
- Card legado exibe percentual do capital com ponto decimal (`3.8%`); o card
  novo usa vírgula.
- Destino de "Ver encerramento em Opções…" só oferece recomprar a call; a put do
  collar e a put de proteção isolada não têm caminho de fechamento nesse fluxo
  (fechar as duas pernas fica fora do escopo — sem atomicidade).
- Card marca a call pelo ask; a proposta e a execução de fechamento usam o
  último negócio (R$ 0,70 × R$ 0,65 no teste). Deliberado nos dois lados.

## Pendências fora da fase

- Validação em aparelho com backend da Fase 44 em produção (status
  `human_needed` em `45-VERIFICATION.md`): a produção (`boris.semente.dev`,
  deploy manual a partir da `main`) ainda roda `F10-20260927-03`, sem a rota
  `estrutura`.
- Promoção `v2/interacao-estrutural` → `main` e deploy manual: decisão do Alex,
  não realizada.
