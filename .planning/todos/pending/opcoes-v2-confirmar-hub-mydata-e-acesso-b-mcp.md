---
title: Definir acesso server-to-server ao b-mcp antes de planejar Opções v2
date: 2026-09-01
priority: high
---

# Definir acesso server-to-server ao b-mcp antes de planejar Opções v2

Levantado em `.planning/notes/opcoes-v2-b-mcp-exploracao.md` durante `/gsd-explore`
autônomo (usuário dormindo). Dois fatos travavam `/gsd-plan-phase` da ideia
"setups de opções propostos via b-mcp" — o primeiro já foi resolvido pelo Alex,
o segundo segue aberto:

1. ~~`mydata.semente.dev` × `mydata.acamerini.app` são o mesmo hub?~~
   **RESOLVIDO 2026-09-01** — o Alex confirmou: `mydata.semente.dev` é o
   domínio canônico. Verificado tecnicamente também: os dois domínios
   respondem no mesmo Railway edge (`jfk1`) com `x-hikari-trace` IDÊNTICO
   (`jfk1.57w5`) e `content-length` idêntico — é o mesmo serviço reachable
   por dois nomes DNS, não dois hubs separados. `acamerini.app` segue vivo e
   funcional (não há incidente em produção), mas `semente.dev` é o nome a
   usar daqui pra frente. Ver "Ação decorrente" abaixo.

2. O servidor MCP `~/dev/MCP/servers/mydata/` (portal `b-mcp.semente.dev`,
   protegido por `PORTAL_SENHA` para uso humano) tem alguma via de acesso
   server-to-server — sem senha interativa — que o backend do Boris possa
   chamar para as tools `find_tradable_options`/`evaluate_option_structure`/
   `create_setup`/`evaluate_setups`? A documentação do MCP descreve esse
   server como "pessoal, local, servindo só você" — presumir uso
   multi-tenant em produção sem confirmação seria arquitetura inventada.

**Por que isso bloqueia planejamento:** sem saber como acessar o `b-mcp` em
produção (item 2), não dá pra desenhar o transporte de "Opções v2" (estender
`mydata_client.py` com novos endpoints vs. algo genuinamente novo).

**Como resolver o item 2:** perguntar direto ao Alex, ou (se ele autorizar)
verificar se existe rota de service-to-service no
`~/dev/MCP/servers/mydata/server.py` ou `portal/app.py` além do bearer
`id.semente.dev`.

## Ação decorrente do item 1 (resolvido) — CONCLUÍDA 2026-09-01

O Alex confirmou o domínio canônico. O `BASE_DEFAULT` de
`server/app/mydata_client.py` foi trocado de `https://mydata.acamerini.app`
para `https://mydata.semente.dev`; a docstring do módulo e o guardião
`test_base_url_sem_env_usa_default` foram atualizados junto (ver commit
desta quick task, `.planning/quick/260901-2da-*`). Risco nulo porque os
dois nomes DNS respondem no mesmo serviço Railway (mesmo edge `jfk1`,
`x-hikari-trace` `jfk1.57w5` idêntico). Nenhuma variável de ambiente do
Railway foi alterada — produção não seta `MYDATA_URL` e continua não
setando; o default do código é a fonte.
