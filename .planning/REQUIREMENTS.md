# Requirements: Boris+ (b3-agente) — Milestone v2.0

**Defined:** 2026-09-29
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como
o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só
então tem acesso a automações do Modo Operador.

## v2.0 Requirements

Fonte: print do Alex (UGPA3, 1000 cotas, PM R$ 39,50) — card de Posições
mostra "1000 travada(s) · lastro de CALL", P&L só das ações, aviso falso
"Posição sem stop definido" e `R:R —`, enquanto a aba Opções mostrou uma put
de proteção para o mesmo ativo (hipótese: collar, cada tela mostra metade).
Causa em código: `server/app/main.py:~3181` pega só a PRIMEIRA opção aberta do
ativo; `badgeTravada` só existe para call coberta (`web/src/copy.js:~1547`);
`proposta_fechar` (`opcoes_lastreadas.py`) não consulta a leitura técnica.
Mock aprovado: https://claude.ai/artifact/JEpy5VmkoddNTHyVYnYWZc (decisões
2026-09-29: régua mantida, pernas sempre visíveis, texto do Estudo completo).
Todo cálculo é do motor determinístico (princípio 5); nada estimado.

### Motor — estrutura por ativo (Fase 44)

- [x] **ESTR-01**: O motor devolve, por ativo, TODAS as pernas de opção
  abertas (tipo, strike, vencimento, quantidade, lado), não só a primeira;
  a estrutura é classificada (call coberta / put de proteção / collar).
- [x] **ESTR-02**: O resultado da estrutura (P&L das ações + prêmio das pernas
  marcado a mercado) é calculado pelo motor; prêmio sem cotação →
  `null` (nunca 0, nunca estimado) e o resultado sinaliza "incompleto".
- [x] **ESTR-03**: O motor calcula a faixa no vencimento (piso/teto e
  perda/ganho máximos pelos strikes); `null` quando não determinável.
- [x] **ESTR-04**: O motor classifica o estado da estrutura: vigente / ≤5 dias
  / exercício provável / prêmio indisponível / vencida.
- [x] **ESTR-05**: O gate de liquidez barra só propostas NOVAS; estrutura já
  aberta reprovada no gate vira `aberta_sem_proposta`; encerramento com prêmio
  indisponível fica bloqueado com motivo.
- [x] **ESTR-06**: As frases de motivo (cada motivo distinto, sem colapsar
  `sem_contrato_liquido`/`sem_vencimento_elegivel` em `sem_setup`) e de
  piso/teto/stop vêm de `skill_ref.py`, espelhadas em `copy.js` com paridade
  travada por teste.

### Card de posição estruturada (Fase 45)

- [ ] **CARD-01**: O card de Posições mostra a estrutura (nome + resultado
  total ações+prêmio), não só o P&L das ações.
- [ ] **CARD-02**: O card mostra a régua "faixa no vencimento" (piso, teto,
  preço atual, PM).
- [ ] **CARD-03**: O card lista todas as pernas do ativo, sempre visível.
- [ ] **CARD-04**: Os 5 estados de ESTR-04 têm tratamento visual próprio;
  "Encerrar" fica bloqueado com o motivo quando o prêmio está indisponível.
- [ ] **CARD-05**: Estrutura com proteção não exibe o aviso falso "Posição sem
  stop definido" nem `R:R —`; piso/teto aparecem no lugar, em texto do motor.
- [ ] **CARD-06**: `badgeTravada` cobre collar e put de proteção; textos por
  modo (Estudo completo, Operador direto); verde/vermelho só em
  manchete/preço/P&L (COR-01), escala `SP`, contraste AA nas 4 combinações
  tema×modo, `aria-label` nos elementos novos; âncora proibida "trava
  protetora"/"abate o custo" ausente (usar "collar").

### Didática (Fase 46)

- [ ] **DIDA-01**: A KB ganha verbete "expectativa matemática × taxa de acerto
  (vantagem estatística)" em `kb.py`/`conceitos.py`, sem promessa de
  rentabilidade.
- [ ] **DIDA-02**: A cláusula tocável do microtexto de reconciliação (hoje abre
  `confluencia`) passa a abrir esse verbete, com paridade `skill_ref`↔`copy.js`.

## Future Requirements

- Quick task avulsa (fora da milestone): remover
  `tiraOpcoesSemCobertura/SemSetup/SemMercado` (`copy.js`) e citar janela e n
  total na frase do Operador em "amostra insuficiente" (`historico.n`).
- Backlog anterior em `PROJECT.md` §Active (ConfluenceRing motion, tokens
  `--sp-*` globais, decisão contra o regime, B3 execução).

## Out of Scope

- Executar/enviar ordem real de opção (Princípio 2) e fill parcial (C-14).
- Estruturas novas além das 3 da biblioteca (call coberta, put de proteção,
  collar).
- Mudar a manchete determinística ou a lógica de decisão/elegibilidade.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ESTR-01..06 | 44 | Complete |
| CARD-01..06 | 45 | Pending |
| DIDA-01..02 | 46 | Pending |
