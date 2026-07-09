# BolsIA — Auditoria de design + Design System (v1)

> Sessão: Racionalização de design e atração de mercado.
> Estágio: **mapeamento do código real + proposta**. Nada aqui foi aplicado ao código —
> o mock (`qa/mocks/racionalizacao-design-v1.html`) é o artefato de aprovação. Patches só depois do OK.

---

## 1. Reconciliação: diagnóstico herdado (§2 do prompt) × código real

O diagnóstico herdado está **parcialmente desatualizado** — várias frentes já avançaram no código.
Isto muda o escopo real: menos "construir do zero", mais "fechar lacunas e dar acabamento".

| Item do §2 | Realidade no código (`web/src/App.jsx`) | Status |
|---|---|---|
| "Nenhum token de cor por modo — tudo azul" | Existe token system completo: `PALETTE{dark,light}` + `T.x → var(--x)` + override `MODE_OPERADOR` aplicado por classe `.b3-mode-operador` (l.29–97). **Operador já é verde** `#22c55e`. **Estudo ainda é azul genérico** `#3B82F6`/`#2563EB`. | **Parcial** — o "azul" é só do **Estudo** |
| "Badge de modo assimétrico (só Operador)" | `copy.js`: `estudo.chipModo = null`, `operador.chipModo = "MODO OPERADOR"`. Topbar (l.585) só renderiza o chip quando existe. | **Confirmado** |
| "Zero visualização de dado" | Já existem: `OpsSparkline` (l.705, preço + marcas compra/venda), `PlanRuler` (l.741, régua de plano/risco). Mas **watchlist/radar não têm sparkline por linha**, e a curva de patrimônio é só traço. | **Parcial** |
| "Confluência = barra plana repetida" | `RadarScreen` l.3397–3401: `<div width={conf%}>` barra plana. | **Confirmado** → vira anel |
| "Disclaimer duplicado em quase todo card" | Centralizado em `disclaimers.js` (bom). Renderizado em ~6 pontos (l.254–255 dobrado no welcome, 3467 por-tela no Radar, 3709 budget, 3776 rodapé). **Não** é "por card" — já está quase consolidado. | **Amplamente resolvido**; falta 1 affordance única/tela |
| "Ícones de tab genéricos, sem relação com a marca" | `NavIcon` (l.603) tem SVGs próprios (linha), limpos, mas **não carregam o motivo do logo** (candle + spark de IA). | **Parcial** |
| "Home despeja lista sem hero" | `EvolucaoScreen` (home): saudação + resumo do dia + card "OPORTUNIDADE ADICIONAL" (destaque único já existe) + curva + streak + coach. **Não há carrossel/hero swipeable**; é pilha vertical. | **Parcial** (já há 1 destaque, falta o formato hero) |
| "Gráfico vazio sem copy" | `CapitalCurve` l.1383–1387 **já tem copy** ("Sua curva começa amanhã…") + traço tracejado placeholder. | **Resolvido** (ajustar copy p/ "2º dia") |

**Leitura:** a espinha (tokens por modo, fraseologia por modo, sparkline base, régua de plano, estado vazio com copy)
**já existe**. O gap de "parece MVP" concentra-se em: (a) **Estudo ainda usa azul genérico**; (b) **falta de gradiente/área** nas
curvas; (c) **confluência como barra**; (d) **home sem formato hero**; (e) **sinalização de modo assimétrica**; (f) **ícones sem
o motivo da marca**.

---

## 2. Inventário de cor fora do token system (grep)

49 ocorrências de hex em `App.jsx`. Classificação:

**Legítimas (manter):**
- l.29–92 — definição do `PALETTE` + `MODE_OPERADOR` (é a fonte dos tokens).
- l.124–136, 148 — `LogoMark` + `IA_GRAD` (marca fixa azul→ciano; identidade de ícone, correta nos dois modos).
- l.314–317 — cores de marca do Google (botão "Sign in with Google").

**Violações a tokenizar (hardcoded fora do PALETTE):**
- l.649–650 — `const TEAL = "#2dd4bf"`, `const ORANGE = "#fb923c"` → mover para tokens semânticos (`--kpi-teal`, `--kpi-orange`) ou usar `accentSoft/positive`.
- l.1093–1095 — `#22c55e`/`#f43f5e` inline (barras) → `T.positive`/`T.negative`.
- l.3100, 3153 — `#fbbf24` (âmbar solto) → `--warn`/`accent` do modo.
- l.4170 — `#0a0d10`/`#f3f4f7`/`#0b0e14` inline → `T.bgBase`.
- l.4967 — `#fff` inline → `T.onAccent`.

**Critério de aceite §6 ("zero hex azul fixo fora do token system"):** já quase satisfeito — o azul só vive no `PALETTE`
(Estudo) e na marca (`LogoMark`/`IA_GRAD`). O grep final deve confirmar 0 azul **inline** fora dessas duas origens.

---

## 3. Design System proposto

### 3.1 Tokens de cor por modo (decisão #1 — precisa de OK)

Preserva o mecanismo atual (CSS vars + override por classe). **Muda o acento do Estudo de azul → âmbar**,
para matar o "parece um painel genérico" e tornar os dois modos inconfundíveis. A **marca** (logo + wordmark "IA")
permanece azul→ciano fixa nos dois modos (identidade de ícone).

| Papel | Estudo (proposto) | Operador (atual, mantém) |
|---|---|---|
| Identidade | Professor / mesa de estudo — **âmbar** | Mesa ao vivo — **verde-mercado** |
| `accent` (dark) | `#f0b429` | `#22c55e` |
| `accentSoft` | `#ffd873` | `#86efac` |
| `onAccent` | `#20160a` | `#04170b` |
| `positive` / `negative` | `#34d399` / `#fb7185` | `#22c55e` / `#ef4444` |
| `bgBase` / `bgCard` | `#0b0e14` / `#11151c` | `#0a0d10` / `#10161a` |

> Alternativa se âmbar não agradar: manter o Estudo azul, porém um **índigo mais rico** (`#6366f1`) — ainda distinto do `#3B82F6` "flat". Decidir no mock.

### 3.2 Escala de espaçamento (4/8pt)
`--sp-1:4px · --sp-2:8px · --sp-3:12px · --sp-4:16px · --sp-5:20px · --sp-6:24px · --sp-8:32px`.
Hoje há valores avulsos (5px, 7px, 9px, 11px, 13px, 18px…). Normalizar para a escala; exceções só em micro-ajuste óptico.

### 3.3 Raio, elevação, tipografia
- Raio: `--r-card:14px · --r-pill:999px · --r-inner:10px` (hoje mistura 10/12/13).
- Elevação: 1 sombra padrão de card `0 1px 0 rgba(255,255,255,.03), 0 8px 24px -12px rgba(0,0,0,.5)` + borda `borderSubtle`. Sem elevações ad-hoc.
- Tipografia (**preservar** — acerto atual): `MONO` (ui-monospace/SF Mono) para **todo número**; `SANS` (-apple-system) para texto. Escala: display 27 / h1 22–23 / título 15–18 / corpo 13 / label 10.5–11 (kicker, uppercase, `letter-spacing .05em`).

---

## 4. Camada de visualização de dado (componentes reutilizáveis)

1. **`Sparkline`** (inline, watchlist/radar): 1 linha de fechamentos, ~64×22px, cor = sinal (positive/negative) ou neutra. Reaproveita a lógica de `OpsSparkline` (`linePath`, `extentOf`), sem marcadores. Uma por linha de ativo.
2. **`EquityArea`** (patrimônio): evolui `CapitalCurve` — troca `<path fill=none>` por **área preenchida com gradiente** na cor do modo (`accent → transparente`), linha por cima. Estado vazio: copy "O gráfico aparece a partir do **2º dia** de histórico." (ajuste do texto atual).
3. **`ConfluenceRing`** (confluência do setup): anel circular SVG (ø ~44px, `stroke-dasharray`) substitui a barra plana l.3399. Centro = `NN%`, cor por tier (`tierOf`: forte/moderada/neutra). Reutilizável em radar, watchlist e destaque da home.
4. **`EmptyState`** (genérico): ícone com motivo da marca (candle/spark shimmer `sc-placeholder` já existente no runtime) + título + copy + 1 CTA. Um por tela.

---

## 5. Hierarquia por tela (1 métrica dominante + 1 CTA primário)

| Aba | Métrica/insight dominante | CTA primário único | Secundário/colapsado |
|---|---|---|---|
| **Acompanhar (home)** | Hero: **melhor oportunidade do dia** (ticker + anel de confluência) em card swipeable | "Estudar / Ver plano" do hero | Resumo do dia, curva, streak, coach, lista completa de setups (abaixo) |
| **Radar** | Card do topo com **anel de confluência** grande | `Aprofundar com IA` (Estudo) / `Plano da mesa` (Operador) | `+ Watchlist`, critérios do setup (colapsado) |
| **Watchlist** | Linha por ativo com **sparkline + confluência** | `Estudar ativo` / `Plano completo` | Filtros, ordenação |
| **Portfólio** | **Patrimônio (curva com área)** + P&L do dia | `Simular compra` / `Registrar entrada` | Posições com régua de plano, histórico |
| **Operador IA** | **Estado do operador autônomo (ON/OFF + modo)** num card único dominante | Toggle "Operador no servidor" | Regras (stop/alvo/trailing), tetos, link p/ notificações |

**Home como carrossel (§5.5):** 1 hero (melhor oportunidade) swipeable no topo; a lista completa de setups vira seção
secundária "Mais oportunidades" abaixo, não despejada.

**Disclaimer consolidado (§6):** 1 affordance por tela — ícone `ⓘ` no header → abre sheet com o texto do modo
(`DISCLAIMERS.radar`/`.operador`). Remove o parágrafo fixo por seção.

---

## 6. Sinalização de modo redundante (4 sinais, simétricos nos 2 modos)

1. **Cor** — token `accent` do modo (âmbar × verde).
2. **Badge simétrico** — `estudo.chipModo = "MODO ESTUDO"` (hoje `null`) + `operador.chipModo = "MODO OPERADOR"`.
3. **Friso superior** — barra de 3px na cor do modo no topo da tela (novo).
4. **Ícone distinto** — livro/lupa (Estudo) × mira/pregão (Operador) ao lado do badge.

---

## 7. Aba Operador IA (§7) — decisão #2

O prompt fixa: **mantém os controles de execução plenos em Modo Estudo**, mas a aba deve ser revista.
Proposta de revisão (sem remover função): promover **um estado dominante** ("Operador no servidor: ATIVO/INATIVO · modo
Executar/Sinalizar") como card-herói no topo; **agrupar** as regras (stop/alvo/trailing) e os tetos em uma seção
"Regras & limites" logo abaixo; e mover o link de notificações para o rodapé. Um único CTA de peso (o toggle). Isto
mantém tudo acessível no Estudo, mas para de "parecer um painel de execução plena" solto.

---

## 8. Iconografia de marca (§7 do escopo)

Estender o motivo do `LogoMark` (candle + spark de IA) aos ícones **ativos** da tab bar e aos estados vazios.
Reaproveitar o shimmer `sc-placeholder` (já no runtime) para loading — não recriar.

---

## 9. Critérios de aceite (§6) — rastreio

- [ ] 1 só CTA de peso por tela — endereçado na tabela §5.
- [ ] Todo card de setup = 1 componente parametrizado — consolidar radar/watchlist/destaque no mesmo `SetupCard`.
- [ ] Disclaimer 1×/tela — affordance `ⓘ` + sheet.
- [ ] Watchlist/Radar com sparkline; patrimônio com área — componentes §4.
- [ ] Confluência = anel — `ConfluenceRing`.
- [ ] Badge + cor simétricos nos 2 modos — §6.
- [ ] Estado vazio do gráfico com copy — já ok, ajustar p/ "2º dia".
- [ ] 0 hex azul inline fora do PALETTE/marca — grep final.

---

## 10. v2 — ajustes do feedback (mock `racionalizacao-design-v2.html`)

1. **Badge reposicionado.** Saiu de ao lado do wordmark (apertado contra o patrimônio) para **linha própria sob "BolsIA"**: `● MODO ESTUDO · Alex` — dot na cor do modo + rótulo + saudação. Fica persistente, legível e integrado, sem competir com o número do patrimônio. O `ⓘ` do disclaimer saiu do topbar global e virou **1 por tela**, ao lado do título (mais contextual). O avatar (canto sup. direito) abre o Perfil.
2. **Nada removido — só reorganizado, com pontos de acesso visuais.**
   - Portfólio: card **"Histórico de operações"** com ícone/entrada dedicada (abre a lista completa) + botão **"Leitura da IA"** em cada posição.
   - Operador IA: controles plenos mantidos (Executar/Sinalizar, regras stop/alvo/trailing, tetos) + **"Diário do operador"** (histórico de decisões) preservado como quick-link.
   - Radar/Watchlist/Home: análise da IA acessível pelos CTAs de sempre.
3. **Menu de Perfil/Config reorganizado.** Hoje é um monólito de 6 `DrillRow` de mesmo peso. Proposta: cabeçalho de perfil → card **Modo de trabalho** (troca Estudo/Operador clara) → **tiles agrupados** por bloco: **Conta** · **Personalização & simulação** (Preferências / Orçamento & risco) · **IA & desempenho** (Config de IA / Eficiência) · **Notificações & avançado** (Notificações / Logs & debug). Cada tile abre a **mesma sub-tela focada de hoje** — conteúdo idêntico, só hierarquia e entrada visual novas.
