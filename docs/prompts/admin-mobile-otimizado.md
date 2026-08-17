# Observabilidade e administração no app mobile — spec de execução

## Objetivo

**Escopo é a superfície INTEIRA de administração e observabilidade que hoje
vive no servidor — não um subconjunto.** Isso cobre as duas superfícies que
já existem, somadas:

1. **Todo o portal `web-admin/`** (desktop, ADR-011/012/013) — as 10 abas:
   Visão Geral, Custos, Comportamento do Usuário, Eficiência da IA,
   Automação, Mudança de LLM, Fontes de dados, Prompts, Usuários e papéis,
   Auditoria.
2. **As 4 telas hoje dentro do app consumidor** em Perfil: Eficiência da IA,
   Atividade da IA, Fonte de dados, Diagnóstico.

Administradores passam a acessar essa superfície completa pelo app mobile
(iOS/Capacitor). A forma (UX/UI) sai de uma análise de design, não de um
porte direto das telas de desktop.

Duas fases: **Fase 1 termina num ADR e para para aprovação**; Fase 2 só começa
depois do aceite explícito do Alex.

## Estado atual — verificado no repositório, não redescubra

| Fato | Onde | Por que muda a decisão |
|---|---|---|
| O app consumidor **já tem 4 telas de observabilidade** em Perfil: `EficienciaIAScreen`, `AtividadeIAScreen`, `FonteDadosScreen`, `LogsDebugScreen` | `web/src/App.jsx` (componentes ~4600–5160; roteamento ~7453–7459) | A tarefa é em boa parte **reconciliação**, não greenfield |
| Os tiles "Fonte de dados" e "Diagnóstico" aparecem para **todo usuário**, sem gate de papel | `PerfilHub`, `web/src/App.jsx` ~2113–2131 | Hoje qualquer conta vê a porta; a tela é que falha/esvazia depois |
| O front consumidor **nunca lê `permissions`** | `grep -rn "permissions" web/src/` → vazio | O ADR-013 já entrega `permissions[]` em `/api/auth/me`; é o gancho que habilita gating de verdade |
| O app nativo carrega **bundle LOCAL**, não o servidor | `web/capacitor.config.ts`: `webDir: "dist"`, sem `server.url` | `/admin/*` **não existe** dentro do app nativo — "abrir /admin no app" não é uma opção trivial |
| O denylist de service worker para `/admin` **já existe** | `web/vite.config.js`: `navigateFallbackDenylist: [/^\/admin/]` | Resolve o caso PWA-no-navegador; **não** resolve o caso nativo |
| `@capacitor/app-launcher` já é dependência | `web/package.json` | Abrir URL externa não exige dependência nova |
| Backend está pronto | ADR-013: 9 rotas admin migradas + 5 novas, todas com `require_permission` | A tarefa é front + UX; backend novo só se a análise provar necessidade |

**Assimetria de publicação que deve pesar na decisão:** mudar `web/` exige
`publicar-web.sh` **e** um build TestFlight para chegar no iPhone; mudar
`web-admin/` exige só `publicar-admin.sh`. O que muda com frequência tende a
não pertencer ao bundle do iOS.

## Decisões que a Fase 1 fecha

1. **Arquitetura de entrega**: telas admin embutidas no app consumidor
   (`web/`), `web-admin/` responsivo aberto por webview/navegador, ou híbrido.
   Justifique contra o fato do bundle local e contra a assimetria de
   publicação.
2. **Tratamento por superfície**: escopo é todas — a decisão aqui é COMO cada
   uma aparece no mobile (tela nativa, leitura simplificada, ação bloqueada
   por complexidade de input), não SE ela entra. Editar prompt longo num
   celular é candidato óbvio a tratamento diferenciado — justifique o que
   escolher para cada superfície da lista do Objetivo.
3. **Destino das 4 telas que já existem** em Perfil: ganham gate por
   `permissions`, são absorvidas pela solução nova, ou continuam como estão.
   O ADR-011 disse que viveriam "até uma decisão explícita" — esta é a decisão.
4. **Risco de App Store**: funcionalidade administrativa dentro de um app de
   consumidor. Nomeie o risco e como a solução escolhida o trata.

## Fase 1 — auditoria + design (termina em ADR-014)

Use a skill `engineering:system-design` para a análise de UX/UI. O output dela
alimenta o ADR; não é entrega em si.

O ADR-014 precisa conter:

- a decisão arquitetural com o trade-off explícito (o que ganho, o que pago,
  onde quebra);
- as 4 decisões acima, fechadas;
- mapeamento tela → permissão do ADR-013 (`observabilidade.ver`,
  `operador_ia.ver`, `execucao_automatica.ver`, `llm.configurar`,
  `fontes_dados.configurar`, `prompts.editar`, `usuarios.gerenciar`);
- o que fica de fora desta rodada e por quê.

**Pare aqui e aguarde aprovação.**

## Fase 2 — implementação (só após aceite)

Segue o ADR aprovado. Nada além do escopo que ele fecha.

## Guardrails (do CLAUDE.md — valem nas duas fases)

- **Gate real é sempre backend.** A UI reflete o que `require_permission` já
  nega; esconder tile é cosmético.
- **Stop/alvo nunca é vetado** por papel ou plano — vale para qualquer gate
  novo.
- **Manchete vem só do motor determinístico.**
- **Segredo só em env do servidor** — `apiKey`/`baseUrl` da IA gerenciada não
  entram em tela nenhuma (o ADR-013 já os excluiu do override).
- **Guardiões de teste não se apagam**; `qa/`, `ESTADO-*`, `CHECKOUT-*` e
  RELEASES não se reescrevem.
- **Publicação é passo manual separado** do merge.
- **Paridade `deviceStore` ↔ `serverStore`** em `web/src/persistence.js`:
  método ou campo novo entra nos DOIS.

## Critério de aceite

Fase 1: ADR-014 existe, fecha as 4 decisões, e cada guardrail acima que a
proposta toca está nomeado com o tratamento dado.

Fase 2 (quando liberada):

- `bash scripts/executar.sh --testes` verde nas DUAS suítes;
- `npx vite build` limpo em cada front editado;
- teste ao vivo: um admin vê e usa as superfícies; um usuário comum não vê
  porta nenhuma e toma 403 se chamar a rota direto;
- evidência real de execução na entrega (saída de teste, screenshot),
  não afirmação de que passou.

Se a verificação no aparelho físico não for possível nesta sessão, diga isso
explicitamente em vez de declarar sucesso.
