# Quick Task 260830-eqm: Fase 4 do ADR-23 — Boris+ relying party do semente.id

**Fonte canônica:** `~/dev/cvm-financas/prompt-boris-fase4-relying-party-otimizado.md` (lido na íntegra em 2026-08-30). Este arquivo transcreve o bloco `<contexto>/<objetivo>/<restricoes>/<tarefa>/<criterio_de_aceite>` para uso do planner/executor desta quick task — não resuma nem infira além do que está aqui.

<contexto>
Este repositório é o Boris+ (codinome interno `b3-agente`, mantido de
propósito). Produto multi-usuário em https://boris.semente.dev.

Autenticação hoje:
- Clientes finais: email+senha PBKDF2 e social Apple/Google com validação
  OIDC própria — server/app/auth.py (verify_oauth_token:263,
  upsert_oauth_user:317, unificação por email verificado).
- Painel do dono: web-admin/src/App.jsx, `function Login` (~linha 962),
  autentica com api.login(email, password) e recusa conta sem
  `permissions` (ADR-013 deste repo).
- Rotas: POST /api/auth/login, /api/auth/oauth, /api/auth/me,
  /api/auth/logout (server/app/main.py:235-330).

Existe um portal de identidade do portfólio em produção:
https://id.semente.dev — emissor OIDC próprio (Authorization Code + PKCE
S256), federando Apple e Google, contas do dono por convite, unificação por
email VERIFICADO pelo provedor. É a Fase 1 do ADR-23, cuja fonte de verdade
é ~/dev/cvm-financas/docs/arquitetura.md (seção ADR-23) — leia antes de
desenhar.

A Fase 2 (MyData como relying party do mesmo portal) está em produção e é a
implementação de referência para copiar o padrão:
- ~/dev/cvm-financas/app/api/semente_id.py — cliente OIDC: PKCE, troca do
  code, validação do id_token (issuer, audience, nonce) contra o JWKS em
  https://id.semente.dev/jwks, e a trava SEMENTE_ID_EMAIL_DONO.
- ~/dev/cvm-financas/app/api/admin.py:713-728 — GET
  /admin/api/observabilidade, o formato do contrato mínimo.
- ~/dev/cvm-financas/tests/test_semente_id.py e
  tests/test_entrar_semente_id_http.py — o padrão de teste: id_token
  assinado com chave RSA gerada em memória, sem tocar rede real.

Sobre o nome: o produto se chama Boris+ desde 10/08/2026 e o rename já foi
executado por scripts/atualizar-identidade.sh (idempotente). O que ainda
carrega "BolsIA" é registro histórico em .planning/, qa/, ESTADO-* e
RELEASES.md — preservado de propósito, porque reescrever o nome da época
falsificaria o que foi decidido nela.

Cada repositório é editado na sessão dele: o que precisar do MyData ou do
portal vira pergunta para o Alex, não edição direta.

**Isolamento já garantido:** esta quick task roda em worktree própria
(`.claude/worktrees/fase4-relying-party-adr23`, branch
`worktree-fase4-relying-party-adr23`), separada da pasta principal onde a
Fase 13 do milestone v1.3 executa ao vivo. Não editar a pasta principal.
Este trabalho é fora da sequência do ROADMAP.md do v1.3 por decisão
explícita do Alex (rodar como GSD quick task, não como fase do milestone).
</contexto>

<objetivo>
Três alvos, nesta ordem de dependência:

1. IDENTIDADE — o painel administrativo do Boris+ ganha um segundo caminho
   de entrada pelo portal semente.id, ao lado do login por email+senha que
   já existe.
2. OBSERVABILIDADE — o backend publica GET /observabilidade no contrato
   mínimo do ADR-23, para o console admin.semente.dev agregar depois.
3. CAUDA DO RENAME — as superfícies que ainda dizem "BolsIA" e são vistas
   por alguém hoje (interface, documentação operacional viva, mensagens de
   erro, README) passam a dizer Boris+. Registro histórico permanece como
   está.
</objetivo>

<restricoes>
- O bundle id `com.alexandrecamerini.bolsia` permanece exatamente como
  está, e com ele APNS_TOPIC e o `aud` do Sign in with Apple. O raciocínio
  está em scripts/atualizar-identidade.sh:7-11: ele é a identidade do app
  na Apple, o usuário nunca o vê, e trocá-lo publicaria outro app. O mesmo
  vale para o codinome interno `b3-agente` (pastas, package.json, env vars
  B3_*, chaves de armazenamento b3-* que são dado de usuário).
- O login email+senha do painel continua funcionando idêntico ao de hoje —
  o portal soma um caminho. Se o portal cair, o dono entra pelo caminho de
  sempre (mesmo princípio do ADR-19 do MyData).
- O login dos clientes finais permanece como está. Este trabalho é só a
  superfície administrativa.
- redirect_uri do client OIDC usa https://boris.semente.dev — o portal
  compara por igualdade exata, sem prefixo nem wildcard.
- id_token validado por issuer (https://id.semente.dev), audience
  (client_id deste app) e nonce, contra o JWKS do portal.
- O portal é multiusuário (outros sistemas do portfólio o compartilham).
  Para o painel continuar sendo só do dono, replique a trava
  SEMENTE_ID_EMAIL_DONO do MyData — ou documente por que o RBAC deste repo
  já cobre o caso.
- GET /observabilidade segue o formato de app/api/admin.py:713-728 do
  MyData: {situacao: "ok"|"atencao"|"critico", alertas: [...],
  ultimas_execucoes: [...], proximas: [...]}, derivado de dado que já
  existe aqui.
- Credenciais do portal entram por variável de ambiente.
- Registrar o client no portal roda contra produção de outro repositório:
  `railway ssh --service semente-id "python -m app.cli client boris-web-admin
  --redirect https://boris.semente.dev/<caminho-do-callback>"`, projeto
  `mydata` no Railway. **Não rodar este comando** sem confirmação explícita
  do Alex — o client_secret devolvido aparece uma única vez e é segredo.
  Se o client_id/secret de produção ainda não existir, deixe a integração
  pronta com credenciais lidas de env (placeholder documentado) e pare para
  pedir ao Alex que rode o comando/forneça as credenciais.
</restricoes>

<tarefa>
Leia o ADR-23 (`~/dev/cvm-financas/docs/arquitetura.md`, seção ADR-23) e os
três arquivos de referência do MyData antes de desenhar.

Entregue os três alvos do objetivo. Para o alvo 3, generalize
scripts/atualizar-identidade.sh em vez de criar um script paralelo — duas
fontes de verdade para a mesma migração é o problema que ele já resolve — e
comece medindo o que ainda diz "BolsIA" fora dos registros históricos, para
o alvo ter tamanho conhecido antes de começar.

Se a implementação esbarrar no login dos clientes finais ou no bundle id,
pare e traga para decisão em vez de contornar.
</tarefa>

<criterio_de_aceite>
- Login por email+senha do painel continua idêntico ao de hoje.
- Login pelo portal abre o painel administrativo de ponta a ponta, com
  teste automatizado usando id_token assinado por chave gerada em memória
  (o portal de produção fica fora da suíte).
- GET /observabilidade responde as quatro chaves do contrato, com teste.
- `bash scripts/atualizar-identidade.sh --verificar` roda limpo, e o bundle
  id continua com.alexandrecamerini.bolsia.
- A suíte deste repositório passa inteira via
  `bash scripts/executar.sh --testes` (as duas suítes: pytest + web/tests/*.mjs),
  sem regressão no login dos clientes finais.
- Nenhum client_secret em commit ou log.
</criterio_de_aceite>

Decida sozinho o rotineiro e entregue no escopo acima. Se discordar de
alguma restrição, diga em uma frase e siga.
