---
quick_id: 261014-upj
slug: rebaixamento-operador-visivel
status: complete
date: 2026-10-14
commits: [3c30823f]
---

# Quick 261014-upj — SUMMARY

## O que mudou

- `server/app/store.py` — `set_config`: a migração de saída do Operador grava
  `agent.rebaixadoOperador = {em, execucao, entradaAuto}` (OR com o anterior) e
  um `warn` no Diário (`tag: "rebaixamento-operador"`, frase educacional), só
  quando algo mudou. `set_agent`: em Operador, `mode` limpa `execucao`,
  `entradaAuto` limpa `entradaAuto`; marcador some quando os dois zeram.
- `server/app/skill_ref.py` — `REBAIXAMENTO_OPERADOR` (9 chaves × 2 modos) +
  `rebaixamento_operador_txt`.
- `server/app/main.py` — `/api/agent/status` expõe `meuModo`,
  `minhaEntradaAuto`, `meuRebaixamento`.
- `web/src/copy.js` — espelho byte a byte (`rebaixamentoOperador`).
- `web/src/App.jsx` (AgenteScreen) — aviso `role="status"` com "Religar
  Executar" / "Manter apenas sinalizar" (ou ciência só da entrada); botões de
  modo passam por `escolherModo` (grava + relê o servidor); `modoEfetivo`
  prefere `srv.meuModo` com conta.

## Desvio do brief (declarado)

`modoEfetivo` passou a ler o modo do servidor. Motivo: no iPhone,
`deviceStore` nunca relê `agent.mode` do servidor — depois da migração a tela
mostrava "Executar" com o servidor em "sinalizar", o que torna o aviso
contraditório com o card-herói e é muito provavelmente o que o Alex viu.
Guardião `test_agente_modo_estudo_ui.mjs` atualizado com nota (garantia
"fora do Operador = sinalizar" intacta). `persistence.js` não foi tocado.

## Testes

- Novos: `server/tests/test_rebaixamento_operador.py` (11 casos: 3 combinações,
  nada armado, não duplica, volta mantém, limpeza por campo, manter limpa,
  fora do Operador não limpa, copy, rota de status);
  `web/tests/test_rebaixamento_operador_ui.mjs`.
- Guardiões atualizados com nota: `test_agente_modo_estudo_ui.mjs` (2
  asserções), `test_vocabulario_espelho.mjs` (dict novo).
- `test_entrar_no_operador_nao_mexe_no_mode_sinalizar` intacto e verde.
- `npx vite build` ok; `npx cap copy ios` ok; `bash scripts/executar.sh
  --testes` rc=0 — 3604 passed, 5 skipped, 3 xfailed + todos `.mjs` OK.

## Limitações

- Contas migradas antes do deploy (a do Alex, 14/10) não têm marcador: sem
  aviso retroativo. O card-herói, porém, já mostra "Apenas sinalizar" de
  verdade (modo do servidor) — religar é um toque em Executar.
- Em offline, `escolherModo` relê o status antigo até o próximo poll (20 s).
- `doc.agent.entradaAuto` do iPhone segue local (o toggle da Entrada
  automática lê dele); não alterado.

## Validar localmente

Entrar no Operador, ligar Executar, trocar para Estudo, voltar ao Operador:
Diário (Perfil → Logs & debug) tem o warn; tela Operador IA mostra o aviso; "Religar
Executar" some com ele e o card-herói vira "Executar".

NÃO publicado (aguarda o Alex): exige `scripts/bump.sh` + `publicar-web.sh` e
build iOS.
