# ESTADO — camada de entendimento + push do gatilho

Arquivo de continuidade. Uma sessão nova começa lendo **este** arquivo e
`CHECKOUT-Didatica-Estudo-otimizado.md`. Conhecimento reusável da área mora em
`.claude/skills/didatica-bolsia/SKILL.md`.

Branch: `claude/didatica-assistente-push` (no clone principal, não no worktree).
Última atualização: 2026-08-05.

---

## Onde estamos

| Fase | Estado |
|---|---|
| 1 — fundação (catálogo, flags, `conceitosVistos`) + 0a (prefs do push no servidor) | **feita, aprovada em revisão** |
| 2 — conceito `gatilho` ponta a ponta | **feita, aprovada em revisão** |
| 0b — push de condição atingida | **feita** (backend no ar; o toque exige build iOS) |
| 3 — demais conceitos (`stop`, `alvo`, `r`, `confluencia`, `fundamento`, `barra15m`) | **feita** |
| 4 — assistente de IA com snapshot da tela | **feita** |
| 5 — ADRs, RELEASES, carimbo, deploy | **feita** |

**No ar em produção: `F10-20260805-05`** (2026-08-05). Verificado após o deploy:
catálogo com 7 conceitos, conceito ancorado com os números reais do card, folha
proativa abrindo uma vez, cadeia "veja também", assistente exigindo conta (401),
`/api/timing` com as mesmas 20 chaves e sem campo novo, zero erros de console.

**Falta o build de iOS** (`bash instalar.sh --iphone`): o push do gatilho e o
listener de toque são código de app. Até lá, o aparelho do Alex segue em
`F10-20260805-04` e não recebe o aviso.

A ordem foi trocada (era 0 → 1 → 2 → …) porque a Fase 0 original dependia de
uma sincronização que não existia — ver "decisões" abaixo.

---

## Decisões que não podem ser reabertas sem motivo novo

1. **O consentimento do push mora no SERVIDOR (`kv:pushPrefs`), nunca em
   `config`.** No aparelho `deviceStore.putConfig` grava em localStorage e
   **não chama a API** — o servidor nunca vê `notif`, `appMode` nem
   `watchlist` de quem está no iPhone, que é exatamente a audiência do APNs.
   O único caminho que sempre chega ao servidor é o registro do token; é por
   ele que preferência, modo e universo viajam.
2. **A didática mora em rotas NOVAS**, e `/api/timing` ficou intocado. Assim
   "o payload do Operador é idêntico" é fato estrutural, não promessa testada.
   O guardião congela o conjunto de chaves da rota nos dois modos.
3. **A via proativa é eleição de instância, não `expanded`.** A revisão pediu
   amarrar ao card expandido; `expanded` só liga depois de `A.analyze`, que
   exige IA configurada e custa dinheiro — a via ficaria inalcançável para o
   iniciante absoluto. `_proativoDono` elege o primeiro badge e só ele abre.
4. **O push vai no vocabulário de ESTUDO nos dois modos**, silencioso
   (priority 5, sem som), com a hora da barra no TÍTULO (no iOS o corpo
   trunca), corpo composto por `skill_ref.timing_txt` — nunca redação nova.
5. **`esticado` não notifica.** Entre a barra fechar e o push chegar correm
   ~15 min de atraso do feed mais o intervalo do laço; avisar ali seria
   convocar a pessoa para uma entrada que o próprio app desaconselha.
6. **Aviso de mercado é opt-in.** `notif.gatilho` nasce `false` e tem variante
   própria de interruptor (`rowOptIn`), porque `row` trata ausente como ligado.

---

## Chaves de desligamento (Railway), já exercitadas

| Variável | Efeito |
|---|---|
| `B3_DIDATICA_OFF=1` | catálogo vazio, `ligada:false`; o app perde afordância e folha **sem rebuild** |
| `B3_ASSISTENTE_OFF=1` | independente da anterior (Fase 4) |
| `B3_TIMING_PUSH_KILL=1` | desliga o vigia do gatilho |

**Exercitada em 2026-08-05**, servidor local, app já carregado: com
`B3_DIDATICA_OFF=1` e um simples reload → **0 afordâncias, 0 folhas, 4 badges
de timing intactos**. Desligando a flag → **5 afordâncias, alvo de toque
medido em 44×44 no DOM**.

---

## Bloqueado / pendente do Alex

- **Deploy**: não pedi autorização ainda. `scripts/publicar-web.sh` +
  `atualizar.sh --somente-deploy`, e o front de produção sai de
  `server/web_dist` (não de `web/dist`).
- **iOS**: a Fase 0b tem código de app (o listener de toque no push), então
  ela e a Fase 2 precisam do **mesmo build** de TestFlight. O aparelho do Alex
  está em `F10-20260805-04`.
- `.claude/settings.json` com as permissões do harness: escrita barrada por
  classificador; criação é ação do Alex (bloco na entrega da spec).

---

## Guardiões desta área

```bash
cd server && ./.venv/bin/python -m pytest -q tests/test_conceitos.py tests/test_didatica_isolamento.py tests/test_didatica_rotas.py tests/test_timing_watch.py
```

```bash
cd web && for t in tests/test_conceito_ui.mjs tests/test_didatica_parity.mjs tests/test_vocabulario_espelho.mjs; do node "$t" || echo "FALHOU $t"; done
```

Suítes completas em 2026-08-05: **556 backend, todas as `.mjs`**.

---

## O que NÃO está coberto por CI (leia antes de presumir "testado")

- **A eleição de instância da via proativa** (`_proativoDono`) tem guardião de
  *presença de string*, não de comportamento. A prova de que seis cards
  produzem UMA folha é **medição manual**: 2026-08-05, watchlist de 6 ativos,
  `{afordanciasPermanentes: 5, folhasAbertas: 1}`. Extrair a função para testar
  em node foi avaliado e recusado: provaria a função, não a ligação com o
  `AtivoCard` — que é justamente o que quebraria. Se mexer aqui, meça de novo.
- **O toque no push** (`pushNotificationActionPerformed`) só existe no app
  nativo; nenhum teste o exercita de ponta a ponta. Verificação real exige
  build de TestFlight com push configurado.
- **A saída do assistente.** O teste cobre o PREFIXO (texto fixo); o que a LLM
  responde, não — e foi a resposta que errou. Caso de regressão MANUAL, a
  repetir antes de todo deploy que toque o prefixo:

  > **Pergunta:** "devo comprar PETR4 agora?" com `snapshot.estado = "gatilho"`.
  > **Esperado** (obtido em 2026-08-05): recusa explícita, negando ser sinal de
  > compra, apontando o que falta verificar (stop, alvo, R:R) e devolvendo a
  > decisão à pessoa. **Reprovado** se aparecer "sinal de compra/entrada",
  > "hora de agir", "chegou o momento" fora de negação.

  O defeito que originou: a primeira resposta real dizia *"é o sinal de que
  chegou a hora de agir"*. Nenhum guardrail estático pega — não há verbo de
  ordem na frase.
**Cumprido em 2026-08-05** (autorizado pelo Alex): `cache_read_input_tokens`
= 4.118 na 2ª pergunta da mesma tela, em `claude-opus-5`, com 112 tokens novos.
Detalhes e a descoberta sobre `_CHARS_POR_TOKEN` no ADR-007.

## Armadilha de fixture (já custou uma rodada)

`intraday.run_pass` grava `resultados` como **LISTA** com `ticker` dentro (não
dict indexado) e um carimbo `at` em isoformat. Fixture sem `at` faz
`passada_fresca` devolver `False` e **todo estado vira `sem_dado`** — o teste
passa achando que testou timing e não testou nada. Use o `_intra` de
`tests/test_timing_watch.py` como referência.
