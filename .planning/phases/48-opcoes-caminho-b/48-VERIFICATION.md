---
phase: 48-opcoes-caminho-b
verified: 2026-10-06T00:00:00Z
status: passed
score: 13/13 must-haves verified (automatizado); 1 item humano residual
overrides_applied: 0
re_verification:
  previous_status: gaps_found (48-14-GAPS.md, checkpoint humano)
  gaps_closed:
    - "G-01 (3 objetivos indisponiveis sem motivo real): motivo_sem_candidato distingue sem_vencimento_elegivel de sem_estrutura"
    - "G-02 (pernas abertas sem tela/acao de encerrar): PernasAbertas.jsx + 48-16"
  gaps_remaining: []
  regressions: []
gaps: []
deferred: []
approved_deviations:
  - "quick 261006-b1z (Alex, 2026-10-06): janela de prazo 15 a 60 dias REMOVIDA; piso = nao vencido (prazo_elegivel dias >= 1); frase de sem_vencimento_elegivel nao cita mais min/max"
  - "quick 261006-axi (Alex, 2026-10-06): universo do hub inclui ativos so com perna aberta (alem das posicoes de acoes); sem auto-selecao"
human_verification:
  - test: "Smoke visual no web/iPhone depois dos dois quicks posteriores ao 'aprovado' do 48-17 (b1z e axi)"
    expected: "Ativo so com perna aberta aparece no hub; vencimento curto (<15d) monta degraus; sem_vencimento_elegivel mostra datas lidas sem citar janela"
    why_human: "O aprovado do Alex (48-17) precede b1z/axi; so ha guardiao automatizado para essas duas mudancas, sem revisao visual"
---

# Phase 48: Opcoes caminho B - Verification Report

**Phase Goal:** redesenho da aba Opcoes (hub -> ativo + escada por objetivo; matriz de vencimentos atras de botao com custo 2N+1; grafico em R$ total; termos clicaveis; gap closure G-01/G-02).
**Status:** passed (nenhuma lacuna automatizada; smoke visual residual atendido — ver Resolução)
**Re-verification:** Sim, apos gap closure 48-15/16/17. Desvios aprovados anotados, nao tratados como falha.

## Evidencia executada (nao confiada do SUMMARY)

- `pytest` test_opcoes_escada, test_opcoes_escada_rotas, test_options_mcp_escada_matriz, test_conceitos_opcoes_escada, test_skill_ref: **146 passed**.
- `web/tests/test_opcoes_*.mjs` (31 arquivos) + test_tour_opcoes + test_vocabulario_opcoes: **todos ok**.
- `npx vite build` (web): gerou dist (ok).
- Nao rodei a suite canonica completa (`scripts/executar.sh --testes`); fica a cargo do orquestrador.
- Marcadores TBD/FIXME/XXX em `opcoes_escada.py` e `options_mcp_api.py`: nenhum.

## Requisitos

| ID | Status | Evidencia |
|----|--------|-----------|
| OPC-01 | VERIFICADO | `HubOpcoes.jsx`, `navOpcoes.js` (nivel unico hub/objetivo/escada/confirmar), test_opcoes_universo_carteira / nav_profundidade ok. Universo = posicoes + perna avulsa (desvio aprovado axi), nunca watchlist (OpcoesScreen.jsx l.314-329) |
| OPC-02 | VERIFICADO | `opcoes_escada.objetivos()` ordem fixa proteger/renda/collar; indisponivel com motivo/dica do motor (main.py 3943-3952); `ObjetivoAtivo.jsx` |
| OPC-03 | VERIFICADO | `opcoes_escada.py` (627 l., puro) + `GET /api/options/escada/{ticker}` (main.py 3859): ate 3 degraus via `_curadoria_scan_posicao` (mesma varredura da execucao), pares total/por acao, ausente = null+motivo; degradado = 200 sem numero (princ. 4) |
| OPC-04 | VERIFICADO | `EscadaObjetivo.jsx`; chips vem de `vencimentos` (custo zero); barras de `normalizar_barras` |
| OPC-05 | VERIFICADO | `GraficoResultado.jsx` (unidade total/porAcao), grade/linhas do backend (`_grafico`, MAX_PONTOS 241), tabela de numeros |
| OPC-06 | VERIFICADO | `escada-matriz` (`options_mcp_api.py` 2736): reserva 1 + `_cap_check(uid, 2N)`, `chamadasPrevistas = 2N+1` igual ao `comparar.chamadasPrevistas` da rota gratis; unico call site pago `verMatriz` em `useEscada.js`, disparado por clique (nunca useEffect); passa pelo cap |
| OPC-07 | VERIFICADO | `ConfirmarEstrutura.jsx`: `estudo_nao_executa` no Estudo, `ordem_rejeitada` "Ordem rejeitada: {motivo}" via skill_ref; executa pelo despacho existente tudo-ou-nada |
| OPC-08 | VERIFICADO | `TERMOS_OBJETIVO`, `_termos`, `TermoOpcoes.jsx`, test_conceitos_opcoes_escada ok |
| OPC-09 | VERIFICADO | put protetora/collar cobertos em `TERMOS_OBJETIVO` e conceitos (teste verde) |
| OPC-10 | VERIFICADO | `skill_ref.OPCOES_ESCADA` (l.1225) espelhado em `copy.js` (l.894/2180); test_opcoes_escada_espelho + test_skill_ref ok. Frase `sem_vencimento_elegivel` testada sem 15/60/janela |
| OPC-11 | VERIFICADO | `docs/AJUDA.md` secao Opcoes descreve fluxo sobre a Carteira, sem Watchlist; tour guardado por test_tour_opcoes ok. Watchlist remanescente em AJUDA.md l.26/39/41 e do Mercado/Home, fora da aba Opcoes |
| OPC-12 | VERIFICADO | Guardioes mantidos e reancorados com nota datada: test_opcoes_universo_carteira.mjs (reancoragem 2026-10-05 + reconciliacao 2026-10-06 axi), test_opcoes_escada_rotas.py (NOTA 2026-10-06 b1z), test_opcoes_escada_espelho.mjs (NOTA 2026-10-06). Nenhum teste apagado; invariantes (custo so em clique, universo, paridade) preservadas |
| OPC-13 | VERIFICADO (automatizado) | estados degradado/sem_posicao/sem_estrutura/sem_vencimento_elegivel/mercadoAberto/cota (`restamHoje`) na rota; guardioes de render/a11y verdes. Acessibilidade em dispositivo coberta pelo aprovado do Alex (48-17), anterior a b1z/axi |

Requisitos orfaos em REQUIREMENTS.md: nenhum (OPC-01..13 todos declarados nos PLANs; todos aparecem em ao menos um plano).

Nota de bookkeeping (nao e lacuna de codigo): REQUIREMENTS.md ainda marca OPC-01..13 como `[ ]` e "Pending" (linha 193); atualizar para Complete no fechamento da fase.

## Key links

- Hub -> escada: `useEscada.js` -> `store.opcoesEscada` (rota gratis) conectado; `store.mcpEscadaMatriz` presente nos DOIS stores (`persistence.js` 301 deviceStore e 1415 serverStore), paridade respeitada.
- Rota escada reusa `_curadoria_scan_posicao`, a mesma re-derivacao da execucao.
- Custo declarado: `comparar.rotulo` via `comparar_custo` (skill_ref) = mesmo numero do envelope da matriz.
- G-01: `motivo_sem_candidato` ligado em main.py 3941-3952 e 4000-4001.
- G-02: `PernasAbertas.jsx` presente (48-16); guardioes test_opcoes_abertas_e_motivos / fluxo_render verdes.

## Desvios aprovados (nao falhas)

1. b1z: sem janela 15-60 d; piso "nao vencido". Substitui o comportamento descrito no G-01; guardioes e comentarios (main.py 3937-3940, opcoes_escada.py 136-145) atualizados com data.
2. axi: universo do hub inclui ativo so com perna aberta; guardiao proibe auto-selecao por efeito.

## Observacoes (WARNING baixo, nao bloqueiam)

- Comentario em main.py l.3939-3940 ("Sem janela ... VENCIMENTOS_POR_POSICAO NAO muda aqui") esta com redacao truncada/quebrada; cosmetico.
- `VENCIMENTOS_POR_POSICAO=2` segue limitando a varredura; sem janela, o custo mydata por posicao nao aumentou, mas a cobertura de vencimentos longos continua limitada. Confirmar que e intencional.
- Decisoes de produto pendentes do 48-14 (selo de destaque sem call site; `liquido` do collar; `execucao.motivo`) seguem em STATE.md, fora do escopo dos OPC-xx.

## Human Verification Required

1. **Smoke pos-aprovacao (b1z + axi)** - Test: abrir a aba Opcoes (web publicado F10-20261006-01 ou iPhone) com (a) ativo so com perna aberta, (b) cadeia de vencimento curto. Expected: card no hub; degraus montam; motivo mostra datas lidas sem janela. Why human: o "aprovado" do Alex (48-17) e anterior a essas duas mudancas.

---

_Verified: 2026-10-06_
_Verifier: Claude (gsd-verifier)_

## Resolução do item humano (2026-10-06, orquestrador)

O smoke visual pendente (ativo só com perna no hub, vencimento curto montando degraus, motivo sem citar janela) estava na seção C (itens 14 a 16) da lista consolidada de checkpoint que o Alex respondeu com **"aprovado"** em 2026-10-06, depois de testar o web local com MyData e com a produção `boris.semente.dev` (carimbo F10-20261006-01) no ar. Limite do registro: a resposta foi só "aprovado", sem capturas nem as datas lidas; o verifier tinha assumido que o aprovado do 48-17 era anterior às quicks b1z e axi, o que não procede. Status elevado de `human_needed` para `passed` por essa base.
