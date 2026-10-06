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

- [x] **CARD-01**: O card de Posições mostra a estrutura (nome + resultado
  total ações+prêmio), não só o P&L das ações.
- [x] **CARD-02**: O card mostra a régua "faixa no vencimento" (piso, teto,
  preço atual, PM).
- [x] **CARD-03**: O card lista todas as pernas do ativo, sempre visível.
- [x] **CARD-04**: Os 5 estados de ESTR-04 têm tratamento visual próprio;
  "Encerrar" fica bloqueado com o motivo quando o prêmio está indisponível.
- [x] **CARD-05**: Estrutura com proteção não exibe o aviso falso "Posição sem
  stop definido" nem `R:R —`; piso/teto aparecem no lugar, em texto do motor.
- [x] **CARD-06**: `badgeTravada` cobre collar e put de proteção; textos por
  modo (Estudo completo, Operador direto); verde/vermelho só em
  manchete/preço/P&L (COR-01), escala `SP`, contraste AA nas 4 combinações
  tema×modo, `aria-label` nos elementos novos; âncora proibida "trava
  protetora"/"abate o custo" ausente (usar "collar").
  > Reversão deliberada (Fase 45, D-11, 2026-09-29): put de proteção NÃO trava ações (put comprada não soma em qtyTravada), então a pill vermelha `badgeTravada` aparece só onde há call vendida; no collar usa `badge_travada_collar`. A put de proteção é coberta pelo chip neutro de estrutura.

### Carteira v6 (Fase 46)

IDs propostos na 46-UI-SPEC (Pergunta 6) e fixados no plan-phase de 2026-09-30.

- [x] **CART6-01**: O card de posição fechado tem um visual e um estado, igual
  nos dois modos: régua stop←agora→alvo (ação com plano) ou faixa piso·◆BE·teto
  (composta com BE do backend), estado principal por prioridade (D-13/D-14).
- [x] **CART6-02**: O card aberto tem seletor Ação | Opções (n) e flip 3D só
  nessa área (170+170 ms; `prefers-reduced-motion` troca sem animação).
- [x] **CART6-03**: Estudo mostra o simulador "e se?" (grade de preços do
  backend, zona por ponto) e termos tocáveis (definição da KB + "No seu caso"
  do backend) e "Bóris explica" determinístico.
- [x] **CART6-04**: Operador mostra o payoff no vencimento (curva do backend,
  sem texto no desenho) e a grade 3×2 com a conta de cada célula.
- [x] **CART6-05**: O backend entrega, de forma aditiva, cenários/simulador/
  grade/leitura do plano/didática; UGPA3 e CXSE3 viram pytest do backend
  (sem `optionsCalc` no cliente).
- [x] **CART6-06**: A KB ganha os verbetes lastro, call coberta, teto, piso,
  equilíbrio e preço médio, sem promessa de rentabilidade.
- [x] **CART6-07**: Todo texto novo nasce em `skill_ref.py` com espelho byte a
  byte em `copy.js`; guardiões da Fase 45 contraditos são atualizados com nota.

### Didática (Fase 47)

- [ ] **DIDA-01**: A KB ganha verbete "expectativa matemática × taxa de acerto
  (vantagem estatística)" em `kb.py`/`conceitos.py`, sem promessa de
  rentabilidade.
- [ ] **DIDA-02**: A cláusula tocável do microtexto de reconciliação (hoje abre
  `confluencia`) passa a abrir esse verbete, com paridade `skill_ref`↔`copy.js`.

### Opções, caminho B (Fase 48)

Fonte: UI-SPEC aprovado (`48-UI-SPEC.md`) + decisões fechadas do ROADMAP
(2026-10-05): hub → ativo como estrutura; escada por objetivo; matriz atrás de
botão com custo 2N+1 (ADR-027); gráfico em R$ total com alternância por ação;
termos novos em duas ondas. Todo cálculo no backend (princípio 5).

- [x] **OPC-01**: A aba Opções abre num hub com um card por ação da CARTEIRA
  (nunca watchlist), seção "Atenção" de vigias com custo declarado antes do
  clique, frescor e a linha fixa de dinheiro virtual; navegação em profundidade
  (hub → objetivo → escada → confirmar, `‹ voltar`) com estado único que absorve
  `ticker` e `oportunidadeAberta`; deep-links existentes seguem válidos.
- [x] **OPC-02**: A tela de objetivo mostra Proteger de queda, Gerar renda e
  Proteger com custo baixo em ordem fixa; objetivo inviável fica desabilitado
  com o motivo do motor escrito; "Montar do zero" leva ao Montar atual intacto.
- [x] **OPC-03**: O backend (motor puro `opcoes_escada` + rota grátis) entrega,
  por objetivo e vencimento, até 3 degraus derivados do mesmo motor que a
  execução re-deriva, com pior caso, melhor caso, equilíbrio, piso/teto e
  prêmio pago/recebido em R$ total e por ação; ausente é null com motivo.
- [x] **OPC-04**: A escada mostra chips de vencimento (custo zero), 3 degraus
  como radiogroup acessível com barras do backend e o CTA "Escolher este".
- [x] **OPC-05**: O gráfico "Resultado no vencimento" abre em R$ total nas N
  ações com alternância "Por ação", duas linhas, 5 marcadores com legenda,
  "E se…?" por lookup da grade do backend e tabela "Ver os números".
- [x] **OPC-06**: "Comparar vencimentos" fica atrás de botão, mostra o custo
  2N+1 informado pelo backend antes do clique e abre a matriz vencimento ×
  degrau; a chamada paga só sai de clique e passa pelo cap.
- [x] **OPC-07**: A confirmação mostra frase de risco, pernas, lote e lastro;
  executa pelo despacho existente (tudo-ou-nada), não executa no Estudo, mostra
  "Ordem rejeitada: motivo" verbatim e o toast sem linguagem de ganho.
- [x] **OPC-08**: prêmio e perda máxima viram conceito com números do caso e
  verbete KB, mesmo texto, dois modos (onda 1); piso, teto e equilíbrio abrem
  os verbetes existentes.
- [x] **OPC-09**: put protetora e collar idem (onda 2).
- [x] **OPC-10**: Todo texto novo nasce em `skill_ref.OPCOES_ESCADA` com
  espelho byte a byte em `copy.js`, sem linguagem proibida.
- [x] **OPC-11**: Ajuda, tour e `docs/AJUDA.md` deixam de citar "Watchlist" na
  aba Opções e descrevem o fluxo sobre a Carteira.
- [x] **OPC-12**: Os guardiões afetados são reancorados com nota datada, sem
  apagar teste nem afrouxar invariante (custo só em clique, universo = carteira,
  travessão nunca zero, paridade de stores, manchete só do motor).
- [x] **OPC-13**: Estados completos (carregando, vazio, erro de fonte, sem
  prêmio, cota esgotada, mercado fechado/atrasado, lastro indisponível, ordem
  rejeitada, concluída) e acessibilidade (alvos ≥44, radiogroup, gráfico com
  alternativa textual, aria-live, reduced-motion, folha com Esc e foco) travados
  por guardião.

### Anatomia da perna (Fase 49)

Fonte: crítica do screenshot do checkpoint 48-17 (2026-10-06) + protótipo
`49-anatomia-da-perna/prototipo-anatomia-perna.html` + decisões do Alex
(2026-10-06): ordem posição → pernas → objetivos; Encerrar no card com
confirmação informada; protótipo como contrato visual (sem UI-SPEC formal);
ações no gráfico total só com preço médio vindo do motor. Todo cálculo no
backend (princípio 5).

- [ ] **ANAT-01**: Cada perna aberta mostra uma frase de template determinístico
  (`skill_ref` ↔ `copy.js`, por modo) com o que foi pago, o direito
  (comprar/vender, quantidade, strike) e o prazo em dias; sem número no motor,
  travessão + motivo, nunca zero.
- [ ] **ANAT-02**: Pior caso, equilíbrio e resultado no vencimento por perna vêm do
  motor, batem com a conta por strike/prêmio em teste unitário e independem de
  cotação; só "Hoje" depende dela e mostra "Sem cotação" com o motivo do motor.
- [ ] **ANAT-03**: Curva de payoff por perna e total por ativo (pontos) calculadas no
  backend, grátis (custo MCP 0), com paridade `deviceStore` ↔ `serverStore`; a
  tela não refaz a conta.
- [ ] **ANAT-04**: Gráfico total no topo (posição → pernas → objetivos), com chips para
  ligar/desligar pernas e hipótese de preço do usuário rotulada como não
  previsão; ações só entram com preço médio do motor (nunca estimado).
- [ ] **ANAT-05**: "Ver o que muda sem esta perna": resultado com e sem a perna e a
  contribuição dela, no preço escolhido.
- [ ] **ANAT-06**: Encerrar permanece no card; a confirmação informa o que se sabe e o
  que não se sabe (ex.: sem cotação não dá para calcular o caixa) e nenhuma
  ordem real; nunca desabilitado por frescor/liquidez (invariante do 48-16).
- [ ] **ANAT-07**: Acessibilidade: curva com alternativa textual e tabela, perda por
  hachura (não só cor), alvos ≥44, contraste AA nos 4 temas,
  `prefers-reduced-motion`, foco e leitor de tela no card e na confirmação.
- [ ] **ANAT-08**: Estudo e Operador com vocabulário próprio; sem promessa de ganho;
  "Não há dados suficientes para concluir." quando faltar dado; guardiões
  existentes reconciliados com nota datada, sem apagar teste.

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
| CARD-01..06 | 45 | Complete (código verificado; validação em aparelho com backend da Fase 44 em produção pendente — ver 45-VERIFICATION.md) |
| CART6-01..07 | 46 | Pending |
| DIDA-01..02 | 47 | Pending |
| OPC-01..13 | 48 | Pending |
| ANAT-01..08 | 49 | Pending |
