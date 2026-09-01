---
title: Confirmar identidade do hub mydata (semente.dev × acamerini.app) e acesso server-to-server ao b-mcp antes de planejar Opções v2
date: 2026-09-01
priority: high
---

# Confirmar hub mydata e acesso ao b-mcp antes de planejar Opções v2

Levantado em `.planning/notes/opcoes-v2-b-mcp-exploracao.md` durante `/gsd-explore`
autônomo (usuário dormindo). Dois fatos que travam `/gsd-plan-phase` da ideia
"setups de opções propostos via b-mcp" e que não dá pra resolver por leitura de
código — dependem do Alex:

1. **`mydata.semente.dev`** (default de `~/dev/MCP/servers/mydata/fonte.py`) e
   **`mydata.acamerini.app`** (default de `server/app/mydata_client.py` deste
   repo) são o mesmo hub sob rename em andamento, ou dois serviços diferentes?
   Há evidência circunstancial de rename (portal do MCP virou
   `b-mcp.semente.dev`, auth `id.semente.dev`, admin `admin.semente.dev`,
   Boris tem `boris.semente.dev` em `operar.sh`) mas nenhuma confirmação
   direta de que é o mesmo Postgres/dado.

2. O servidor MCP `~/dev/MCP/servers/mydata/` (portal `b-mcp.semente.dev`,
   protegido por `PORTAL_SENHA` para uso humano) tem alguma via de acesso
   server-to-server — sem senha interativa — que o backend do Boris possa
   chamar para as tools `find_tradable_options`/`evaluate_option_structure`/
   `create_setup`/`evaluate_setups`? A documentação do MCP descreve esse
   server como "pessoal, local, servindo só você" — presumir uso
   multi-tenant em produção sem confirmação seria arquitetura inventada.

**Por que isso bloqueia planejamento:** sem saber se é o mesmo hub e como
acessá-lo em produção, não dá pra desenhar o transporte de "Opções v2"
(estender `mydata_client.py` com novos endpoints vs. algo genuinamente novo).

**Como resolver:** perguntar direto ao Alex, ou (se ele autorizar) testar em
produção — `curl -I https://mydata.semente.dev` vs. `https://mydata.acamerini.app`
e comparar payload/headers; verificar se existe rota de service-to-service no
`~/dev/MCP/servers/mydata/server.py` ou `portal/app.py` além do bearer
`id.semente.dev`.
