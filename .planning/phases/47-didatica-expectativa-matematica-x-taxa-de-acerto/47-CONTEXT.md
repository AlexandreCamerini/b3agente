# Phase 47: Didática — expectativa matemática × taxa de acerto - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning
**Source:** ROADMAP (Phase 47) + REQUIREMENTS DIDA-01..02 + CLAUDE.md (camada educacional); sem discuss-phase (escopo fechado, 2 requisitos).

<domain>
## Phase Boundary

O tema obrigatório do CLAUDE.md "diferença entre taxa de acerto e rentabilidade / expectativa matemática" ganha verbete determinístico na KB, e o microtexto de reconciliação da elegibilidade (HIER-03, Fase 43: "o padrão bateu os critérios × o histórico medido mostra X") passa a abrir esse verbete em vez de `confluencia`. Fora de escopo: qualquer cálculo novo de expectativa/estatística no motor, mudança dos números do microtexto, telas novas, IA gerando o texto.
</domain>

<decisions>
## Implementation Decisions (travadas)

- DIDA-01: verbete em `server/app/kb.py` e/ou `server/app/conceitos.py` (seguir o padrão das Fases 44-48: conceito com números do caso quando houver, e verbete KB com o MESMO texto, nos dois modos Estudo/Operador). Título/ID à escolha do planner seguindo o padrão de IDs existente. Conteúdo: o que é expectativa matemática (ganho médio × frequência − perda média × frequência), por que taxa de acerto sozinha não diz se há vantagem, que a expectativa depende do tamanho médio de ganhos e perdas e dos custos, e que amostra pequena não permite concluir. SEM promessa de rentabilidade, SEM "100%" nem garantia; quando faltar dado, a frase fixa "Não há dados suficientes para concluir.". Exemplo numérico, se houver, deve ser rotulado como ilustração e vir de constantes do código, nunca da IA.
- DIDA-02: a cláusula tocável do microtexto de reconciliação (hoje abre `setorId="analise"` → conceito `confluencia`; ver `server/app/skill_ref.py` ~524 e `reconciliacao_elegibilidade_txt` ~532, espelho `reconciliacaoTxt` em `web/src/copy.js`, uso no AtivoCard da Watchlist/Radar em `web/src/App.jsx`: Grep + offset/limit, nunca inteiro) passa a abrir o NOVO verbete. A frase do microtexto não muda de sentido; só o destino do toque. Registrar o setor novo na allowlist do "Perguntar ao Boris" se o padrão exigir (ver `server/tests/test_setores.py`).
- Texto novo nasce em `skill_ref.py` e é espelhado byte a byte em `web/src/copy.js` (nos dois modos) na mesma edição; guardião de paridade existente deve continuar verde.
- Guardiões que travam o destino atual (`confluencia`) são reconciliados com nota datada, sem apagar asserção de negócio válida.

### Claude's Discretion
- ID/nome do verbete e do setor; nº de tarefas e ondas; forma dos testes (pytest do conteúdo e do setor; .mjs de paridade e do destino do toque).
</decisions>

<canonical_refs>
## Canonical References

- `CLAUDE.md` (Camada educacional; princípios 5-8; guardiões de paridade)
- `.claude/skills/didatica-boris/SKILL.md` (vocabulário por modo, princípios de dado, guardiões)
- `server/app/skill_ref.py` (~520-560, `reconciliacao_elegibilidade_txt`), `web/src/copy.js` (`reconciliacaoTxt`)
- `server/app/kb.py`, `server/app/conceitos.py`, `server/tests/test_setores.py`, `server/tests/test_conceitos_opcoes_escada.py` (padrão de verbete + conceito + setor das Fases 44-48)
- `.planning/phases/48-opcoes-caminho-b/48-02-SUMMARY.md` (como foi feito o par conceito+KB+setor)
- `.planning/REQUIREMENTS.md` (DIDA-01..02)
</canonical_refs>

<specifics>
## Specific Ideas

Exemplo ilustrativo possível (a confirmar pelo planner contra o padrão de conceitos): 40 % de acerto com ganho médio 3 e perda média 1 tem expectativa positiva (0,4×3 − 0,6×1 = +0,6); 70 % de acerto com ganho médio 1 e perda média 4 tem expectativa negativa (0,7×1 − 0,3×4 = −0,5). Rotular como "ilustração, não resultado do seu histórico".
</specifics>

<deferred>
## Deferred Ideas

- Calcular a expectativa real do usuário a partir do histórico (cálculo de motor + tela): fase futura.
</deferred>

---
*Phase: 47-didatica-expectativa-matematica-x-taxa-de-acerto*
