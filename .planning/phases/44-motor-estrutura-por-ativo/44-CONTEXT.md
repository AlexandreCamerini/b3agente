# Phase 44: Motor — estrutura por ativo - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

O backend entrega, por ativo, todas as pernas de opção abertas e a leitura determinística da estrutura (nome, resultado, faixa no vencimento, estado, motivos) sem estimar nada. Só motor + frases de `skill_ref.py` com paridade em `copy.js`. O card (Fase 45) e o verbete (Fase 46) ficam fora. Sem ordem real, sem fill parcial (C-14), sem estruturas além de call coberta / put de proteção / collar, sem mudar manchete/decisão/elegibilidade.

</domain>

<decisions>
## Implementation Decisions

### Contrato da API
- **D-01:** Módulo novo puro `server/app/estrutura_posicao.py` que reusa `opcoes_payoff.perfil_da_estrutura` (nada de reimplementar payoff). A rota `GET /api/options/proposta/{ticker}` ganha chave ADITIVA `estrutura` (mesmo padrão de `candidatos`, `.get()` com default; cliente antigo ignora). Sem rota nova.
- **D-02:** Cálculo só no servidor, inclusive para iOS (o front envia/lê as pernas, o servidor calcula). NÃO espelhar payoff/estrutura em JS — evita nova paridade `deviceStore`↔`serverStore`. Pesquisador confirma como o iOS já alimenta a rota de proposta (optionPositions vive no device) e segue o mesmo caminho.
- **D-03:** Todas as opções abertas do `underlying` entram (fim do `next(...)` de `main.py:~3188`, que pega só a primeira); classificação call coberta / put de proteção / collar sai do conjunto de pernas.

### Marcação do prêmio e "incompleto"
- **D-04:** Perna marcada pelo lado que FECHA a posição: vendida = ask (custo de recompra), comprada = bid (o que se receberia). Lado ausente → cai no `last` com carimbo explícito de origem (`last`); sem nenhum → `null`. Nunca mid, nunca estimado.
- **D-05:** Perna sem cotação → `resultado_total = null`, `incompleto: true`, e o payload expõe as partes conhecidas separadas (P&L das ações, prêmio das pernas cotadas) e QUAIS pernas faltam. Nunca soma parcial apresentada como total (princípios 4 e 5).

### Motivos, gate e estados
- **D-06:** `sem_contrato_liquido` e `sem_vencimento_elegivel` ganham chave e frase próprias em `skill_ref.OPCOES_LASTREADAS` (Estudo + Operador), distintas de `sem_setup`; `tendencia_de_alta` continua alias. Espelho em `copy.js` e teste de paridade atualizado (guardião de reversão deliberada: atualizar com nota, não apagar).
- **D-07:** Gate de liquidez barra só proposta NOVA. Estrutura já aberta reprovada → estado `aberta_sem_proposta` com o motivo do gate, nunca some. `encerrar` devolve `{permitido: false, motivo}` quando o prêmio da perna a recomprar não tem cotação. `proposta_fechar` continua sem consultar leitura técnica; "degradado" deixa de ser o único motivo distinguível no fechamento.

### Casos de borda
- **D-08:** Vencimentos divergentes entre pernas → faixa/piso/teto `null` com frase "vencimentos diferentes" (reusa `vencimentos.divergentes` de `opcoes_payoff`, D-03 Fase 36); todas as pernas listadas; estado usa o vencimento mais próximo.
- **D-09:** Quantidade de opção ≠ lotes de ações → faixa calculada só na parte coberta (`min(qtd opção, ações)`); excedente vira flag `descoberta` com frase do motor; faixa `null` se houver perna vendida sem lastro (perda ilimitada).

### Claude's Discretion
- Limiar de "exercício provável" (ITM por quanto), janela "≤5 dias" (corridos vs pregões) e precedência entre estados simultâneos — não foram discutidos. O planner/pesquisador decide e documenta, mantendo determinismo, teste unitário por estado e a ordem sugerida: vencida > prêmio indisponível > exercício provável > ≤5 dias > vigente (`aberta_sem_proposta` é eixo separado, ligado ao gate).
- Nomes de campos do payload `estrutura` e formato exato das frases de piso/teto/stop (Estudo completo, Operador direto).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — ESTR-01..06 e Out of Scope da v2.0
- `.planning/ROADMAP.md` §Phase 44 — goal e 4 critérios de sucesso
- Mock aprovado: https://claude.ai/artifact/JEpy5VmkoddNTHyVYnYWZc (régua mantida, pernas sempre visíveis, texto do Estudo completo)

### Código a estender/reusar
- `server/app/main.py:~3188` — `options_proposta`, onde `pos_op_aberta` pega só a 1ª opção
- `server/app/opcoes_payoff.py` — `perfil_da_estrutura`, `vencimentos.divergentes`, `custo_liquido`
- `server/app/opcoes_lastreadas.py` — `propor`, `proposta_fechar` (405), `put_sem_lastro`
- `server/app/skill_ref.py` — `OPCOES_LASTREADAS` (~592-707), `opcoes_lastreadas_txt`, alias `_OPCOES_LASTREADAS_ALIASES_SEM_SETUP`
- `server/app/store.py:795+` — shape de `optionPositions`
- `web/src/copy.js` (~718-792, ~1547) — espelho de frases; `badgeTravada`
- `web/src/api.js:327` — `optionsProposta`

### Guardrails
- `CLAUDE.md` — princípios 4/5, paridade `skill_ref.py`↔`copy.js`, guardiões não se apagam, âncora proibida "trava protetora"/"abate o custo" (usar "collar")
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário por modo

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `opcoes_payoff.perfil_da_estrutura`: faixa/máx/mín/breakevens já com estado de vencimentos divergentes — base de ESTR-03.
- `opcoes_lastreadas_txt(modo, chave, **dados)`: interpolação de frases por modo; degrada para `educacional`.

### Established Patterns
- Chave aditiva na resposta com `.get()` default; `null` explícito, nunca `0.0` (guardião `test_m3_format_pede_null_nunca_zero`).
- Motor puro separado de I/O; exceção do provedor vira `providerStatus: "degraded"`, nunca 500.
- Frase só em `skill_ref.py`, front recebe pronta/espelha em `copy.js`.

### Integration Points
- `options_proposta` (montagem do payload) e o ramo `pos_op_aberta`; `put_sem_lastro` para a flag `descoberta`.

</code_context>

<specifics>
## Specific Ideas

Caso de referência: UGPA3, 1000 ações, PM R$ 39,50 + put de proteção + call (collar) — hoje o card mostra só "1000 travada(s) · lastro de CALL", P&L só das ações e aviso falso de "sem stop".

</specifics>

<deferred>
## Deferred Ideas

- Quick task avulsa: remover `tiraOpcoesSemCobertura/SemSetup/SemMercado` (`copy.js`) e citar janela e n em "amostra insuficiente" — já registrada em REQUIREMENTS §Future.
- Espelho do cálculo em JS para uso offline no iPhone — descartado nesta fase (D-02); reavaliar só se surgir requisito offline.

</deferred>

---

*Phase: 44-Motor — estrutura por ativo*
*Context gathered: 2026-09-29*
