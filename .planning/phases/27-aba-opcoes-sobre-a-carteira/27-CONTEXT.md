# Fase 27 — Aba Opções sobre a carteira · CONTEXT

> Decisões do Alex de 2026-09-13, com o diagnóstico que as motivou. Tudo aqui
> foi **reconfirmado por leitura do código no dia**, com arquivo:linha. O que
> não foi decidido está na seção "Em aberto" — não presumir.

## O defeito que originou a fase (diagnosticado 2026-09-13)

Queixa do Alex: *"os setups criados na aba de opções não estão sendo
gravados"*.

**Não há falha de escrita.** `POST /api/options/mcp/setups/confirmar`
(`options_mcp_api.py:2825`) chama `create_setup` no serviço MCP com
`confirm: True` e trata erro — se falhasse, a tela mostraria. A paridade
`deviceStore`/`serverStore` está correta nos três métodos de escrita
(`persistence.js:292-294` e `:1308-1318`), então o iPhone também grava.

O que existe são **três fatos que somados são indistinguíveis de "não
gravou"**:

1. **Não existe rota de listar setups.** `list_setups` é chamado num lugar
   só — dentro de `/leitura/{ticker}` (`options_mcp_api.py:1599`) — e
   imediatamente filtrado por ticker por `_registros_do_ticker`
   (`options_mcp_api.py:1477`). Um setup só é visível com o ticker dele
   aberto.
2. **O ticker nasce vazio toda vez.** `useState("")` em
   `OpcoesScreen.jsx:203`; a escolha é um toggle de chips
   (`OpcoesScreen.jsx:240`). Sair da aba e voltar = tela sem ativo
   selecionado = nenhum setup à vista.
3. **O armazém do MCP é compartilhado e sem dono** (ADR-027 Decisão 7,
   comentado no próprio código em `options_mcp_api.py:2868`). Setup não tem
   `user_id`. **O conceito "meus setups" não existe em lugar nenhum do
   sistema** — nem no MCP, nem no Boris+.

Corolário que a fase precisa tratar: como o armazém é compartilhado e o nome
do setup vem do usuário (`CAMPOS_OBRIGATORIOS_DO_SETUP`,
`options_mcp_api.py:311`), **dois usuários podem colidir no mesmo nome**.

## Decisões do Alex (2026-09-13)

### D1 — Motor da análise técnica: HÍBRIDO

Perguntado de onde deve sair a análise técnica da evolução dos ativos.
Resposta: **híbrido — técnico interno + estrutura no MCP**.

- O **motor interno determinístico** calcula a evolução técnica do ativo
  (tendência, volatilidade, suporte/resistência): `technical_snapshot.py`,
  `indicators.py`, `setups.py` — os mesmos que já alimentam Radar e
  Watchlist. Custo zero, sem LLM, sem rede externa.
  `technical_snapshot.build(ticker, raw_candles, period, interval)` já
  recebe a série de candles, então "evolução no tempo" é factível sem motor
  novo.
- O **serviço MCP** segue responsável só pelo que é específico de opção:
  cadeia, vencimentos, estruturas operáveis, payoff.

**Consequência que a fase precisa assumir:** isto cruza a fronteira que o
ADR-027 fechou deliberadamente (a aba é isolada do núcleo; `OpcoesScreen.jsx`
não importa nada de `App.jsx`). **Exige emenda ao ADR-027** — registrada, não
silenciosa. O isolamento de *front* (`OpcoesScreen.jsx` sem import de
`App.jsx`) permanece; o que muda é o backend passar a servir leitura técnica
interna para a aba.

### D2 — Carteira vazia: estado vazio com caminho

Perguntado o que a aba mostra para quem não tem posição. Resposta: **estado
vazio com caminho para a carteira** — explica que a aba opera sobre o que a
pessoa tem e leva para escolher um ativo. **Não** cai para a watchlist, e
**não** mostra watchlist ao lado do portfólio.

### D3 — Universo da aba = carteira

Pedido literal: *"a aba de opções só apresentasse os ativos que estão no
portfolio e que os setups fossem armados sob os mesmos"*. O universo passa de
`ctx.data.watchlist` (`OpcoesScreen.jsx:202`) para `ctx.data.positions` — que
já está no ctx, sem chamada nova (`App.jsx:3997` já usa o mesmo dado para
marcar "em carteira").

### D4 — Protótipo de UX aprovado

Protótipo em <https://claude.ai/code/artifact/97e3ba12-10d3-4ffc-9ec8-fdd989654f3a>,
**aprovado sem ressalvas** em 2026-09-13. Ele fixa:

- **Vigias antes da carteira.** A lista de setups fica no topo, fora de
  qualquer ticker — é a correção do defeito, não decoração. Ordenada por
  quem disparou.
- **Régua de regime**: 7 segmentos, um por pregão, cor do estado medido,
  hoje destacado. É a "evolução no tempo" pedida — o número de hoje sozinho
  não diz se a volatilidade subiu ou desabou na semana.
- **Custo declarado no controle**: cada botão que consome cota diz "1
  consulta"; o que é interno diz "grátis". Sem isso, o híbrido não se
  sustenta — a pessoa evita a tela inteira por medo de gastar.
- **Lastro livre no cartão** ("300 livres para lastro", "100 já travadas
  numa call coberta"): hoje esse número só aparece na mensagem de recusa,
  depois da tentativa (`store.py:938`).
- Tokens do Brand Book v2, 375 px, tema escuro do Modo Estudo.

### D5 — Skill de UX: não se aplica

O Alex pediu `/bencium-innovative-ux-designer`. Ela cria identidade visual do
zero (dez direções tipográficas, paleta nova). **Não foi usada, com
concordância dele**: o Boris+ tem sistema comprometido e travado por
`web/tests/test_brand_book_v2_tokens.mjs`, e o ADR-011 já teve uma decisão de
paleta própria **revertida** para o Brand Book v2. A própria skill manda
pular a criação conceitual quando existe sistema comprometido. O problema era
arquitetura de informação, não identidade visual.

## Fora de escopo (explícito)

- **Ligar a aba à execução de ordens** — é o B3 da Fase 26, que tem decisão
  registrada do Alex (lastro obrigatório por padrão; operar a descoberto
  exige flag opt-in em Configurações) mas **ainda sem plano**, e depende de
  investigar se o sistema de lastro da Fase 14/17 se estende às estruturas
  que a aba monta via MCP. Esta fase é a fundação dele, não ele.
- **Abrir posição de opção automaticamente pelo Operador IA** — a pesquisa do
  26-CONTEXT já provou que não existe e seria construção do zero.
- **B2** (preservar estado ao trocar de aba) — sem decisão de abordagem.

## Em aberto (NÃO presumir)

1. **Ordenação dos vigias** — o protótipo ordena por quem disparou. Sinalizado
   ao Alex como suposição; ele aprovou o conjunto sem comentar o ponto
   especificamente. Manter "disparou primeiro" e registrar como decisão do
   executor se nada mudar.
2. **Carteira grande** — a aba não tem busca. Sinalizado que acima de ~8
   posições isso vira rolagem longa. Sem decisão; não inventar busca nesta
   fase, mas não desenhar nada que a impeça depois.
3. **Namespacing do nome do setup** no armazém compartilhado — o risco de
   colisão é real (ver corolário acima). A abordagem é decisão de
   implementação do plano 27-01; o que não pode acontecer é dois usuários
   enxergarem ou desativarem o setup um do outro.

## Guardrails (herdados, não re-litigar)

- **Brand Book v2** travado por `web/tests/test_brand_book_v2_tokens.mjs` —
  nenhuma cor, escala de tipo ou token novo fora do sistema.
- **Paridade obrigatória** `deviceStore` ↔ `serverStore` em
  `web/src/persistence.js`: método novo entra nos DOIS.
- **Princípio 5 do CLAUDE.md**: cotação, posição, saldo, lucro/prejuízo e
  agora a leitura técnica são determinísticos — a IA explica, nunca calcula.
  Este é o argumento a favor do híbrido, e ele só vale se o número vier do
  motor, não do LLM.
- **Princípio 4**: dado ausente vira travessão **com motivo**, nunca 0.
- **ADR-027 §3.3**: custo de MCP só em clique explícito — nunca ao abrir
  tela. A emenda do D1 não afrouxa isto; ao contrário, a leitura interna
  existe justamente para a tela abrir sem gastar.
- **Guardiões de teste não se apagam** — reversão deliberada atualiza o
  guardião com nota datada.
- **Suíte canônica**: `bash scripts/executar.sh --testes`, **fora do
  sandbox** (dentro dele ~26 testes falham falsamente por bloqueio de CA).
  Front editado → `npx vite build` antes de declarar ok.
