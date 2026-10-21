---
quick_id: 261021-spd
status: complete
commits: [e202814c, 131b50d8, 95d33b1e]
---
# Quick 261021-spd: ciclo do Operador no iPhone delega ao servidor

- Servidor: `_run_cycle_inner` pré-checa `store.qty_livre`; 100% travada não vende, não grava rejeição, não consome teto, 1 warn/posição/dia (`avisoLastroTravado`). Parcial cita quantidade vendida.
- iPhone: `deviceStore.cycle` com sessão faz POST /api/cycle e adota o estado (sem fallback local); sem conta, lastro vira aviso e erro de venda vira warn.
- Desvio: `SERVER_KEYS` içada ao módulo; guardião `test_agent_server_toggle.mjs` ajustado para ler a lista no const do módulo.
- Testes: pytest 73 + 64 verdes; .mjs novo 19 ok; vite build ok.

## Revisão independente (orquestrador, 2026-10-21)

- B1 (toggle "Modo autônomo" sem efeito logado) rebaixado: o toggle é o "Modo local (com o app aberto)", timer do ciclo; a autoridade de execução é o `mode` executar/sinalizar do servidor. Efeito real: o iPhone logado deixa de vender pela flag local fora do `mode`/Modo Operador (fecha furo da trava de Estudo).
- W2 corrigido em `95d33b1e`: `/api/cycle` devolve `cicloEmAndamento` + `mensagem` quando `run_cycle_for` pulou; iPhone repassa; App mostra a frase. Guardião S3 de `test_execucao_fora_pregao.mjs` reconciliado com nota. Teste novo `server/tests/test_api_cycle_em_andamento.py`.
- Suíte canônica (antes do W2): 3627 passed, 5 skipped, 3 xfailed + todos os `.mjs`, rc=0. Depois do W2: testes tocados (21 pytest + 4 `.mjs`) e `npx vite build` ok.

## Limitações conhecidas

- W1: eventos locais anteriores ao login são substituídos pelos do servidor no 1º ciclo logado.
- I1: notificação local do agente (`evs.length > beforeN`) não dispara com a lista no teto de 50.
- I2: logado sem rede/token expirado → ciclo dá erro, sem fallback local (por desenho).
- Texto do toggle "Modo local" ainda diz que o ciclo local protege stop/alvo — com conta ele dispara o ciclo do servidor.
- Item 3 (PUT de proteção órfã quando o stop vende as ações) fora do escopo.
