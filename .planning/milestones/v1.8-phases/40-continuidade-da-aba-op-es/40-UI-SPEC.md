---
phase: 40
slug: continuidade-da-aba-op-es
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-25
reviewed_at: 2026-09-25
---

# Phase 40 — UI Design Contract

> Contrato de interação para ESTADO-01. Esta fase **não desenha UI nova**: o
> contrato aqui fixa a AUSÊNCIA de elemento visual novo (D-05, restauração
> silenciosa) e define o comportamento observável do estado lembrado
> (ticker + aba ativa) nos 6 cenários de navegação/escopo. Tokens, tipografia,
> espaçamento, cor e copy são herdados integralmente de `39-UI-SPEC.md`
> (status `approved`), mesma aba, mesmos arquivos. Gerado por
> gsd-ui-researcher, verificado por gsd-ui-checker.

Premissas declaradas (não perguntadas ao Alex — derivadas do código e de
`40-CONTEXT.md`, flag no fim para o planner confirmar):

- P-1: o deep-link `opcoesAbaInicial` (D-03) sobrescreve só a ABA; o ticker
  lembrado permanece (as duas coisas não competem — Destacadas não é
  ticker-scoped; ver cenário B).
- P-2: "ticker válido" = presente em `ctx.data.positions` no momento do mount
  (é a mesma lista que alimenta o `seletor`, `OpcoesScreen.jsx:303,597`).
- P-3: restaurar o ticker NÃO dispara nenhuma chamada paga do cap ADR-027
  (ver "Contrato de custo" abaixo) — verificado em `useOpcoesMcp.js:203-279`.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — React 18 hand-rolled, sem shadcn, sem `components.json` (mesma decisão deliberada de `32/34/38/39-UI-SPEC.md`) |
| Preset | não aplicável |
| Component library | nenhuma — estilos inline, tokens `T.*` via `var(--*)` |
| Icon library | nenhuma nova — esta fase não adiciona ícone |
| Font | herdada do shell do app (`App.jsx`), não tocada |

Gate de shadcn não roda: `components.json` ausente repo-wide e esta fase não
introduz componente algum.

---

## Inventário do que esta fase introduz na UI

| Dimensão | Novo nesta fase | Fonte do que já existe |
|---|---|---|
| Componente | **nenhum** | `OpcoesScreen.jsx` (abaBar, seletor, abas) — Fase 39 |
| Token de cor | **nenhum** | `39-UI-SPEC.md` §Color |
| Tamanho/peso de fonte | **nenhum** | `39-UI-SPEC.md` §Typography |
| Valor de espaçamento/raio | **nenhum** | `39-UI-SPEC.md` §Spacing Scale |
| Chave de copy (`copy.js`) | **nenhuma** | — |
| Toast, banner, microtexto, ícone, animação, skeleton | **nenhum** (D-05) | — |
| Estado de UI novo (loading/vazio/erro) | **nenhum** | estados de `39-UI-SPEC.md` §"Estados completos" |

Critério de aceite verificável: o diff da fase em `web/src/copy.js` é vazio;
o diff em `web/src/opcoes/*.jsx` não adiciona nenhum literal de `style={{...}}`
novo, nenhuma string visível nova e nenhum elemento JSX novo além da leitura/
escrita do estado lembrado.

---

## Interaction & State Contract

### Modelo de estado

```
App.jsx (nunca desmonta — vive a sessão inteira do app/página)
  opcoesAbaInicial        ... já existe (Fase 39-02), one-shot, deep-link
  opcoesMemoria           ... NOVO (D-01): { ticker: string, aba: string } | null
                              em memória; NÃO entra em deviceStore/serverStore
                              limpo em _resetScopeState() (D-04 / SC#4)

OpcoesScreen (desmonta ao sair da aba — App.jsx:9279, comportamento mantido)
  abaOpcoes  ← inicial resolvido UMA vez no useState(() => ...) do mount
  ticker     ← inicial resolvido UMA vez no useState(() => ...) do mount
  tudo o mais (vigiasAberto, compararAberto, oportunidadeAberta, tese,
  vencimento, alvo, stop, verbeteAberto, resultados de chamadas) ← default
```

Nome `opcoesMemoria` é sugestão; o planner pode renomear. Forma de escrita
(sincronizar a cada mudança de `ticker`/`abaOpcoes` via callback de `ctx`,
no mesmo desenho de `setOpcoesAbaInicial`/`limparOpcoesAbaInicial`) fica a
critério do planner, com uma restrição: a escrita NÃO pode depender só do
cleanup de unmount (troca de escopo com a aba aberta precisa zerar e não ser
reescrita pelo cleanup logo depois — ver cenário C).

### Ordem de precedência do estado inicial (resolvida no mount)

Aba ativa:

1. `ctx.opcoesAbaInicial` válido em `ABAS_OPCOES` → usa (D-03, vence sempre)
2. `opcoesMemoria.aba` válido em `ABAS_OPCOES` → usa
3. `"oportunidades"` (default da Fase 39)

Ticker:

1. `opcoesMemoria.ticker` presente em `ctx.data.positions` (P-2) → usa
2. `""` (default — "nasce vazio", `OpcoesScreen.jsx:304-311`)

Valor fora da allowlist ou ticker ausente da carteira NUNCA é aceito — cai
para o default. Mesma disciplina de T-39-14 (allowlist de `ABAS_OPCOES`) e
do princípio 4 do CLAUDE.md (não inventar estado).

### Cenários observáveis (critérios de aceite)

| # | Cenário | Pré-condição | Ação | Resultado observável exigido |
|---|---|---|---|---|
| A | Sair e voltar | Opções em "Montar" com PETR4 selecionado; sheet de Vigias aberto; "Ver outros vencimentos" expandido | Tocar outra aba principal (ex. Carteira), depois voltar a Opções | Abre em "Montar", chip PETR4 com `aria-pressed="true"`, conteúdo de Montar do ticker. Sheet de Vigias FECHADO, Comparar RECOLHIDO, tese/vencimento/alvo/stop vazios, lote no default (D-02 / SC#3) |
| A2 | Sair e voltar sem ticker | Opções em "Destacadas", nenhum ticker | Sair e voltar | Abre em "Destacadas" (rótulo visível "Destacadas"; id interno `recomendadas`) |
| B | Deep-link com memória | Memória = { aba: "montar", ticker: "PETR4" } | Em Posições, tocar o atalho que chama `goOpcoes("recomendadas")` | Abre em "Destacadas" (D-03). Memória passa a ser { aba: "recomendadas", ticker: "PETR4" }; ao ir para "Montar" em seguida, PETR4 continua selecionado (P-1). `opcoesAbaInicial` é limpo após o mount (one-shot, comportamento da 39-02 intacto) |
| B2 | Voltar depois do deep-link | Após B, sair de Opções por outra aba e voltar | — | Abre em "Destacadas" (a memória reflete a última aba efetivamente vista, não a de antes do deep-link) |
| C | Logout / troca de conta | Conta X com memória { aba: "montar", ticker: "VALE3" } | Logout (ou excluir conta) e login como conta Y (e-mail, OAuth Apple/Google ou cadastro); abrir Opções | Abre em "Oportunidades", nenhum ticker selecionado. Nenhum chip, cabeçalho ou texto referente a VALE3 aparece para Y, nem por um frame (SC#4). Vale para os 5 call-sites de `_resetScopeState()` (login, register, oauth, logout, deleteAccount — `App.jsx:9032/9041/9052/9068/9079`) |
| C2 | Troca de escopo com Opções aberta | Opções montado com ticker | Ação que chama `_resetScopeState()` sem desmontar Opções (login/register/oauth em `App.jsx:9032/9041/9052` NÃO trocam a aba) | Memória termina `null` depois do fluxo — o cleanup de unmount de `OpcoesScreen` não pode regravar o estado da conta anterior. **E a tela montada também volta ao default** (ticker `""`, aba `"oportunidades"`): nenhum ticker/leitura da conta anterior fica visível para a nova. Mecanismo a fixar pelo planner — ex.: `key` de escopo no `<OpcoesScreen>` (força remount) ou revalidação do ticker contra `positions` fora do mount; alternativamente, provar que nenhum caminho autentica com Opções montada e registrar a prova aqui. *(Adicionado após recomendação #1 do gsd-ui-checker, 2026-09-25 — o texto anterior deixava a questão em aberto com "se existir tal caminho".)* |
| D | Reload / reinício | Qualquer memória | Recarregar a página (web) ou matar e reabrir o app (iOS); também a troca Estudo↔Operador, que faz reload total | Abre em "Oportunidades", sem ticker (D-01: sem persistência entre sessões — comportamento esperado, não bug) |
| E | Ticker lembrado não está mais na carteira | Memória { aba: "montar", ticker: "PETR4" }; usuário vende toda a posição de PETR4 na Carteira | Voltar a Opções | Abre em "Montar" (a aba segue válida), SEM ticker: estado vazio de Montar com o `Aviso` já existente `cp.opcoesEscolherAtivo` ("Escolha um ativo da sua carteira para ver a leitura dele." no Estudo / "Escolha um ativo da carteira para ver a leitura." no Operador). Nunca um cabeçalho/leitura de ativo fora da carteira, nunca um chip "fantasma". A memória é regravada com `ticker: ""` |
| E2 | Carteira vazia | Memória com ticker; usuário zerou a carteira | Voltar a Opções | Mesmo que E; se Montar mostra o estado de carteira vazia da Fase 27 (D2), ele aparece normalmente — nenhum estado novo |
| F | Aba ativa trocada dentro de Opções | Em "Oportunidades", tocar "Montar" | Sair e voltar | Abre em "Montar" (memória acompanha cada troca de aba, não só a primeira) |
| G | Desselecionar ticker | Tocar de novo o chip ativo (`escolherTicker` é toggle) | Sair e voltar | Sem ticker — a memória lembra a desseleção, não o último ticker "bom" |

### "Sem salto perceptível" — critério verificável (D-05)

- O primeiro render de `OpcoesScreen` após voltar JÁ mostra a aba e o ticker
  lembrados: ambos resolvidos no inicializador de `useState(() => ...)`, nunca
  por `useEffect` que troca o valor depois do primeiro paint. Proibido o
  padrão "renderiza Oportunidades → efeito → setAbaOpcoes(memória)".
- Não há flash do estado default: nenhum frame com a pill "Oportunidades"
  ativa quando a memória diz outra aba; nenhum frame com o `Aviso` de "Escolha
  um ativo…" quando a memória tem ticker válido.
- Restaurar o ticker NÃO passa por `escolherTicker` (que é toggle e zera
  tese/Comparar) — é valor inicial direto.
- Sem toast, sem microtexto ("Voltamos para onde você estava" etc.), sem
  animação de entrada, sem scroll programático. Posição de scroll volta ao
  topo como hoje (scroll não é lembrado — D-02).
- Verificação: teste em `web/tests/` que (1) confirma a leitura da memória
  dentro do inicializador lazy de `useState` e (2) ausência de
  `setAbaOpcoes`/`setTicker` alimentado pela memória dentro de `useEffect`;
  mais checagem manual no aparelho (sair/voltar 3× em 375px sem piscar).

### Contrato de custo (ADR-027 §3.3) — consequência visível da restauração

Restaurar o ticker dispara exatamente os efeitos que a seleção de ticker já
dispara hoje, e nenhum outro:

- `opcoesTecnico` (leitura técnica interna, `custoMcp: 0`) — dispara de novo
  no remount; é grátis. O bloco de leitura interna mostra o carregando já
  existente e depois o dado.
- A leitura paga (`mcpLeitura`, custo 3) e as chamadas sob demanda
  (cadeia/operáveis/proposta/possibilidades) **não disparam** e **não são
  lembradas** (D-02: só ticker + aba). Ao voltar, o botão que declara
  "3 consultas" aparece de novo, no estado pré-clique — igual a quando o
  usuário escolhe o ticker pela primeira vez.

Isto é a consequência intencional de D-02, não regressão, e é a única
diferença visível entre "antes de sair" e "depois de voltar" com ticker
selecionado. Aceite: nenhuma chamada a `store.mcpLeitura` ou às rotas
`/api/options/mcp/*` ocorre no remount sem clique (o guardião
`test_opcoes_analisar_ui.mjs` continua passando sem edição).

---

## Spacing Scale

Nenhum valor novo. Herda integralmente `39-UI-SPEC.md` §Spacing Scale
(alvo de toque 44px; pill 8px 14px; caixa 12px 14px; gap 8px; exceção de
grade herdada, `developer-approved — matches existing pattern`, não
reaberta).

| Token | Value | Usage |
|-------|-------|-------|
| — | — | nenhum elemento novo a espaçar |

Exceptions: nenhuma nova.

---

## Typography

Nenhum tamanho/peso novo. Herda `39-UI-SPEC.md` §Typography (4 papéis:
heading 22px/800, eyebrow 9–10.5px/800, body 12.5–13px, body pequeno
10.5–12px; exceção de 3 pesos herdada de `32-UI-SPEC.md`, não reaberta).
Pill ativa restaurada usa exatamente o mesmo estilo da pill ativa por clique
(13px/700).

---

## Color

Nenhuma cor/token novo. Herda `39-UI-SPEC.md` §Color.

| Role | Token | Usage |
|------|-------|-------|
| Dominante (60%) | `T.bgBase` | inalterado |
| Secundária (30%) | `T.bgPanel` / `T.bgCard` | inalterado |
| Acento (10%) | `T.accent` / `T.accentTint10` | inalterado |
| Destrutiva | não aplicável | nenhuma ação destrutiva nesta fase |

Accent reserved for: exatamente a lista de `39-UI-SPEC.md` (pill ativa da
abaBar, chip de ticker ativo, contador do VigiasBadge > 0, ⓘ, link "Ver
outros vencimentos", botões de execução). A pill/chip restaurados recebem o
acento pela mesma regra `aria-pressed`/ativo de hoje — nenhum realce extra
("destaque de restauração") é permitido.

---

## Copywriting Contract

Nenhuma chave nova em `copy.js`; nenhuma string visível nova.

| Element | Copy |
|---------|------|
| Primary CTA | inalterado — nenhum CTA novo |
| Restauração | **nenhuma copy** (D-05): sem toast, sem aviso, sem rótulo "restaurado" |
| Empty state (ticker lembrado inválido, cenário E) | reusa `cp.opcoesEscolherAtivo` existente — sem texto explicando que o ticker "sumiu" |
| Rótulo da 2ª aba | "Destacadas" (`cp.opcoesAbaRecomendadas`, renomeado na Fase 39; id interno `recomendadas` — não renomear o id) |
| Error state | inalterado — erros das chamadas seguem os de `39-UI-SPEC.md` §"Estados completos" |
| Destructive confirmation | não aplicável — logout/exclusão de conta já têm fluxo próprio; esta fase só adiciona a limpeza silenciosa da memória a eles |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | não aplicável — projeto não usa shadcn | não aplicável |
| terceiros | nenhum | não aplicável |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

## Open Questions (flags para o planner)

1. **P-1 — deep-link preserva o ticker lembrado?** Este contrato lê D-03 como
   "a aba do deep-link vence"; o ticker fica. Se o Alex quiser que o
   deep-link zere também o ticker, muda uma linha do inicializador, nenhuma
   outra parte do contrato.
2. **Carteira ainda carregando no mount (cenário E).** Dentro da mesma
   sessão `ctx.data.positions` já está em memória no `App.jsx`, então a
   validação P-2 é confiável. Se o planner achar um caminho em que Opções
   monta antes de `positions` chegar, o comportamento exigido é o default
   (sem ticker) — nunca exibir ticker não validado. Não pedir "esperar e
   restaurar depois" (isso reintroduziria o salto que D-05 proíbe).
3. **Custo zero é premissa, confira.** P-3 foi verificada lendo
   `useOpcoesMcp.js` (só `opcoesTecnico`, custo 0, dispara por ticker). Se
   algum efeito dependente de `ticker` gastar cota depois da Fase 39, a
   restauração do ticker vira gasto sem clique — bloqueante (ADR-027 §3.3).

---

*Phase: 40-Continuidade da aba Opções*
*UI-SPEC gerado: 2026-09-25*
