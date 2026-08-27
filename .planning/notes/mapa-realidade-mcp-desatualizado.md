---
title: Mapa de realidade do MCP está desatualizado em COTAHIST/Opções
date: 2026-08-27
context: Sessão /gsd-explore sobre deduplicação Boris×mydata — achado colateral,
  registrado aqui porque a correção do arquivo em si é noutro repositório.
---

# `~/dev/MCP/docs/boris-pp-00-mapa-de-realidade.md` precisa de correção

O documento comparou o Boris contra `~/dev/MCP/servers/mydata/`, tratando esse
repositório como "o mydata". Existe um segundo repositório também chamado
"mydata" — `~/dev/cvm-financas`, deployado em `mydata.acamerini.app` — que é o
hub de dados real. As linhas do "Achado 3" sobre **COTAHIST** e **Opções/
gregas/IV** estão comparando contra o repositório errado: o `fonte.py` (301 l.)
citado ali é só um cliente HTTP fino que chama o hub, não uma ingestão própria.

Ver [boris-pp-centralizacao-dados-mydata](boris-pp-centralizacao-dados-mydata.md)
para a tabela revisada com evidência (arquivo:linha) do repositório certo.

**Ação:** esta nota fica aqui como registro; a edição do arquivo em si é fora
do escopo desta sessão (repositório diferente, `~/dev/MCP`, não
`~/dev/bolsia/b3-agente`). Corrigir antes de usar aquele mapa como base de
qualquer outra decisão.
