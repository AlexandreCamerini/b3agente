# Itens diferidos — Fase 24

Achados fora do escopo do plano em execução, registrados em vez de corrigidos
(SCOPE BOUNDARY: só se auto-corrige o que a própria task causou).

---

## 2026-09-12 — frontmatter do `.planning/STATE.md` não parseia como YAML

**Achado durante:** execução do 24-16 (ao validar o STATE.md depois de editá-lo
à mão).

**Estado:** PRÉ-EXISTENTE. Reproduzido contra `git show HEAD:.planning/STATE.md`
— já estava quebrado antes desta execução, e não foi introduzido por ela.

**O defeito:** o valor de `stopped_at:` é uma string YAML delimitada por aspas
duplas e contém **4 aspas duplas não escapadas** no miolo, todas vindas do
texto do **24-15**:

```
... um `audit.record("mcp_cota")` POR CAMPO alterado ...     (2 aspas)
... dentro da aba "Fontes de dados" (nenhuma aba nova ...    (2 aspas)
```

`yaml.safe_load` aborta com `ParserError: while parsing a block mapping —
expected <block end>, but found '<scalar>'` na linha 6. Consequência: qualquer
leitor programático do frontmatter (incluindo os handlers `state.*` do
`gsd-sdk`) não consegue ler `progress`, `milestone`, `last_updated` etc.

**Por que não foi corrigido aqui:** (a) é pré-existente e sem relação com o
24-16; (b) a correção reescreve, por um caractere, o texto de registro de
outra execução — e o guardrail do `CLAUDE.md` sobre não reescrever histórico
pede que essa decisão seja do dono do repositório.

**Correção sugerida (1 linha, sem mudar o sentido do texto):** trocar as 4
aspas duplas por aspas simples no valor de `stopped_at`, ou escapá-las com
`\"`, como o restante do campo já faz.

**Verificação depois:**

```bash
server/.venv/bin/python -c "
import yaml
d = open('.planning/STATE.md').read().split('---')[1]
print(yaml.safe_load(d)['progress'])
"
```
