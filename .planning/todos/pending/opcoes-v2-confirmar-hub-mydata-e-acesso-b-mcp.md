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

## Ação decorrente do item 1 (resolvido) — pendente de confirmação

`server/app/mydata_client.py:21` tem `BASE_DEFAULT =
"https://mydata.acamerini.app"` — funciona hoje (mesmo serviço, alias),
mas está desatualizado frente ao domínio canônico confirmado. Railway
production não tem `MYDATA_URL` setada (só `MYDATA_TOKEN` e
`B3_OPTIONS_PROVIDER=mydata`), então o processo em produção depende
inteiramente desse default. Trocar o default do código pra
`https://mydata.semente.dev` é mudança de baixo risco (mesmo serviço,
confirmado por headers idênticos) mas é config de produção — perguntei ao
Alex antes de aplicar em vez de trocar sozinho.
