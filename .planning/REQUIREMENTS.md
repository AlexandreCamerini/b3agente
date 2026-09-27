# Requirements: Boris+ (b3-agente) — Milestone v1.9

**Defined:** 2026-09-26
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como
o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só
então tem acesso a automações do Modo Operador.

## v1 Requirements

Fonte: `qa/AUDITORIA-Jornada-Decisao-v1.md` (Fases 1 e 2 da auditoria),
disparada pelo achado ao vivo do Alex no card de UGPA3 em TestFlight ("não
sei se é pra vender ou comprar"). Escopo = camada visual do card único de
ativo (`AtivoCard`, `App.jsx:3368`, e o cabeçalho do Radar que o
reaproveita, `App.jsx:~6869-6950`). Linhas citadas medidas em 2026-09-26;
a auditoria cita linhas ~25 menores (drift).

### Cor semântica

- [ ] **COR-01**: Usuário vê o estado "sem vantagem estatística medida"
  (`HISTORICO_PILL_STYLE.inelegivel`, `App.jsx:6577`) num canal de cor que
  não é o de VENDER/Baixa/prejuízo — `HISTORICO_PILL_STYLE` deixa de
  referenciar `T.negative`/`T.positive` diretamente. Candidato de token:
  `T.warn` já existente (mesmo racional em `App.jsx:522`) ou token dedicado
  de "confiabilidade" — decidido em discuss-phase. Qualquer que seja, existe
  nas 8 combinações tema×modo e passa contraste AA (texto sobre o tint) em
  todas.

### Hierarquia do card

- [ ] **HIER-01**: Usuário vê o tier de confluência uma única vez por card,
  como `ConfluenceRing` posicionado junto da manchete de decisão; o pill
  solto "confiança X" (`App.jsx:6896`) e a repetição do rodapé
  (`App.jsx:6944-6947`) deixam de existir. Decisão do Alex, 2026-09-26.
- [ ] **HIER-02**: Usuário lê o card na ordem manchete → plano operacional
  (entrada/stop/alvo, quando existir) → uma linha de contexto agrupado
  (regime + fundamento, peso "contexto") → elegibilidade estatística. Vale
  nos 4 contextos do `AtivoCard` (watchlist/Acompanhar, radar/Mesa,
  posições, home) e no cabeçalho do Radar.
- [ ] **HIER-03**: Usuário vê, junto à elegibilidade, um microtexto de
  reconciliação entre "o padrão bateu os critérios" e "o histórico de {n}
  ocorrências mostra {vantagem medida | sem vantagem medida | nunca
  medido}", em vez de dois pills soltos para conciliar sozinho. Texto com
  versão por modo (Estudo explicativo, Operador direto), vindo do par
  `server/app/skill_ref.py` ↔ `web/src/copy.js` — nenhuma string solta no
  componente; números vêm do `signal_ledger`, nunca da IA.

### Componente de sinal

- [ ] **CHIP-01**: Existe um único componente `SinalChip` com dois pesos
  fixos por contrato — `primario` (só a decisão) e `contexto` (todo o
  resto) — cujo visual não é escolhido por chamada; substitui o `chip()`
  interno do `AtivoCard`, `FundamentoChip`, `RegimeChip`
  (`App.jsx:1373-1399`) e o pill de confiança. Zero receita nova de pill
  fora dele (verificável por grep/guardião).
- [ ] **CHIP-02**: Todo `SinalChip` expõe `aria-label` descritivo, no padrão
  já usado por `HistoricoPill` (hoje `chip()`/`FundamentoChip`/`RegimeChip`
  só têm texto visual).
- [ ] **CHIP-03**: A tela de detalhe técnico (`KpiBlock`/`KpiCell`,
  `App.jsx:1321-1356`, aberta via gráfico de velas) passa a mostrar
  direção/convicção/qualidade com o mesmo `SinalChip` peso `contexto`, em
  vez da grade de caixas cinzas.

### Ritmo visual

- [ ] **RITMO-01**: Os blocos do card (manchete → plano → contexto →
  elegibilidade) usam espaçamento da escala 4/8pt
  (`qa/AUDITORIA-Design-System-v1.md §3.2`) via constantes nomeadas, sem
  valores soltos tipo `"11px"`/`"9px"` entre blocos.

### Invariantes (critério transversal, não fase)

- Manchete COMPRAR/VENDER/AGUARDAR/NÃO OPERAR segue vindo só do motor
  (`setups.py`/`kpi.py`) — nenhum teste de `setups.py`/`kpi.py`/
  `signal_ledger.py` muda.
- Separação decisão × elegibilidade (ADR-017) fica mais legível, nunca
  fundida numa síntese.
- Guardião de teste novo para cada invariante visual acima (COR-01 grep,
  CHIP-01 receita única); guardiões existentes não se apagam.
- Verificação humana ao vivo em cada fase: Alex olha o card de UGPA3 (ou
  equivalente) e diz em < 3 s qual é o veredito e o que é contexto.

## Future Requirements

- Motion no `ConfluenceRing` ao trocar de tier (Fase 3 da auditoria —
  Polish), deferido por decisão de escopo 2026-09-26.
- Formalizar a escala 4/8pt como tokens `--sp-*` globais no app inteiro
  (RITMO-01 cobre só o card).

## Out of Scope

- Qualquer mudança na lógica de decisão, elegibilidade ou regime (motor
  determinístico) — o problema é só de apresentação.
- Fundir decisão e elegibilidade num indicador-síntese — contraria ADR-017.
- Composição própria de indicadores em Monitoramento/Posições fora do
  `AtivoCard` — se aparecer, vira achado registrado na fase, não escopo.
- B3 (execução a descoberto na aba Opções) e demais itens do backlog Active
  do PROJECT.md.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COR-01 | — | Pending |
| HIER-01 | — | Pending |
| HIER-02 | — | Pending |
| HIER-03 | — | Pending |
| CHIP-01 | — | Pending |
| CHIP-02 | — | Pending |
| CHIP-03 | — | Pending |
| RITMO-01 | — | Pending |

---
*Requirements defined: 2026-09-26*
