# Phase 49: Anatomia da perna - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning
**Source:** Crítica do screenshot do checkpoint 48-17 + protótipo + decisões do Alex (AskUserQuestion)

<domain>
## Phase Boundary

O usuário entende o que cada perna aberta faz — o direito comprado, o pior caso, o equilíbrio, o prazo — e o que muda no conjunto se ela sair, ANTES de decidir ou encerrar. Evolui `PernasAbertas.jsx` (Fase 48, plano 48-16), que hoje lista id/tipo/lado/strike/venc/qtd/prêmio/resultado e encerra, mas não ensina. Escopo: aba Opções, nível "objetivo do ativo" (e Montar, onde `PernasAbertas` já é montada). Fora de escopo: nova escada, matriz paga, execução de estrutura, mudança de motor financeiro existente.
</domain>

<decisions>
## Implementation Decisions (travadas)

### Ordem da tela
- Posição (gráfico total) → pernas (cards de anatomia) → objetivos (escada, inalterada). O título deixa de ser a pergunta "Objetivo para as 100 ações?" acima das pernas.

### Card de perna (ver protótipo)
- Frase determinística por modo (Estudo/Operador) em `skill_ref.OPCOES_ESCADA` espelhada byte a byte em `web/src/copy.js`: "Você pagou R$ X (R$ prêmio × qtd) pelo direito de comprar/vender N ITUB4 a R$ K cada, até DD/MM." + condição de ganho com equilíbrio.
- Três números: Pior caso, Equilíbrio (termo clicável `opc-equilibrio`), Hoje (chip "Sem cotação" + motivo do motor `motivoSemCotacao`).
- Prazo em dias como dado de primeira classe ("vence em 3 dias"), calculado por regra determinística.
- Curva de payoff da perna no vencimento (strike e equilíbrio marcados), tabela alternativa ("Ver em tabela"), hachura para perda.
- Resultado no vencimento NÃO depende de cotação; só "Hoje" depende.

### Gráfico total
- Chips ligam/desligam pernas; slider de preço no vencimento rotulado "hipótese sua, não previsão".
- Interação-assinatura: "Ver o que muda sem esta perna" → com/sem e contribuição no preço escolhido.
- Ações entram no total SOMENTE com preço médio vindo do motor; sem ele, ficam fora com aviso. Nunca estimado.

### Encerrar
- Permanece no card. Confirmação em 2 passos informa o que se sabe e o que não se sabe (sem cotação: não dá para calcular o caixa) e "nenhuma ordem real". Chama `A.sellOption(id)` como hoje. Nunca desabilitado por frescor, `executavel`, gate de liquidez ou erro da escada (invariante 48-16); só `encerrar.permitido === false` do motor veta, com o texto do motor.
- Perna com lastro aponta para o painel da estrutura (`fecharLastreada`); perna vendida sem lastro não ganha `sellOption` (inalterado).

### Contrato visual
- O protótipo HTML é o contrato (sem UI-SPEC formal; planejar com `--skip-ui`). Tokens do app existentes; reduced-motion, alvos ≥44, AA nos 4 temas.

### Claude's Discretion
- Forma dos pontos de payoff no contrato da rota (array de {preco, resultado}) e granularidade; nome dos módulos/rotas novos; divisão em ondas; estrutura interna dos componentes (`AnatomiaPerna.jsx`, gráfico SVG puro).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fase 48 (base a evoluir)
- `.planning/phases/48-opcoes-caminho-b/48-16-SUMMARY.md` — `PernasAbertas.jsx`, invariantes de Encerrar, fiação no `OpcoesScreen.jsx`
- `.planning/phases/48-opcoes-caminho-b/48-15-SUMMARY.md` — vocabulário `OPCOES_ESCADA`, rota `/api/options/escada`
- `.planning/phases/48-opcoes-caminho-b/48-UI-SPEC.md` — tokens, estados, termos clicáveis
- `.planning/phases/48-opcoes-caminho-b/48-14-GAPS.md` — causa-raiz G-01/G-02
- `.planning/phases/49-anatomia-da-perna/prototipo-anatomia-perna.html` — contrato visual e de interação

### Motor e dados
- `server/app/opcoes_escada.py`, `server/app/opcoes_payoff*` / `cartao_posicao.py` (`cenarios_da_estrutura`, ~l.326) — payoff existente; confirmar shape antes de criar
- `server/app/skill_ref.py` (`OPCOES_ESCADA`), `web/src/copy.js` — paridade byte a byte
- `server/app/conceitos.py`, `server/app/kb.py` — verbete `opc-equilibrio`, `opc-piso`, `opc-teto`
- `web/src/persistence.js` — `deviceStore` ↔ `serverStore`
- `web/src/opcoes/PernasAbertas.jsx`, `ObjetivoAtivo.jsx`, `OpcoesScreen.jsx`, `fluxoEstilo.js`, `TermoOpcoes.jsx`

### Projeto
- `CLAUDE.md` (princípios 4, 5, 6, 8, 9; guardiões de paridade; execução em 2 suítes)
- `docs/adr/025-collar-e-estrutura-multiperna.md`, `docs/adr/027-consumo-do-servico-mcp-autenticado.md`
- `.claude/skills/didatica-boris/SKILL.md`
</canonical_refs>

<specifics>
## Specific Ideas

- Cenário real de teste: ITUB4 100 ações + CALL 49,26 (prêmio 0,21) + CALL 49,76 (0,16) + PUT 46,51 (2,40), venc 09/10; PETR4 1000 ações + 2 CALLs. Pior caso por perna = −prêmio × qtd; equilíbrio CALL = K+prêmio, PUT = K−prêmio.
- Hoje de ITUB4 total (S=48, sem ações) = −R$ 277,00 (conferência do protótipo).
</specifics>

<deferred>
## Deferred Ideas

- Estado "com cotação" da linha Hoje com variação diária; comparação multi-vencimento; payoff da posição lastreada com ações sem preço médio no motor (se o motor não o expõe, ações ficam fora nesta fase).
</deferred>

---

*Phase: 49-anatomia-da-perna*
*Context gathered: 2026-10-06*
