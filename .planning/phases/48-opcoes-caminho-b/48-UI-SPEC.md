---
phase: 48
slug: opcoes-caminho-b
status: draft
shadcn_initialized: false
preset: none
created: 2026-10-05
---

# Phase 48 — UI Design Contract (Opções, caminho B)

> Contrato visual e de interação. Gerado por gsd-ui-researcher, verificado por gsd-ui-checker.
> Escopo: hub (carteira) → ativo (A) como estrutura; escada por objetivo (B) como entrada em "Estruturas". C (payoff com alças) fora de escopo.
> Fonte das decisões: ROADMAP Phase 48 + memória `opcoes-caminho-b-aprovado` (fechadas pelo Alex, 2026-10-05) + protótipo aprovado (artifact 27e91b8c). Não há CONTEXT.md nem RESEARCH.md.

## Premissas declaradas (assumidas sem perguntar)

1. Stack e design system existentes; nada de shadcn. Tokens do Brand Book v2, dark-first, com tema claro. Os valores abaixo vêm do protótipo, que declara "os mesmos do app". **Pré-condição do plano:** o executor confere cada hex contra `T` em `web/src/entendimento.jsx` / `cartaoV6Cores.js` e usa o token do app, nunca o hex literal. Valor divergente = o app vence, e o contraste é rechecado.
2. Os 3 objetivos funcionam na v1: Proteger (put protetora), Gerar renda (call coberta), Proteger com custo baixo (collar). Outras estruturas ficam fora da escada e vão para "Montar do zero".
3. Lote de referência e quantidade vêm da posição em carteira (o protótipo usa 300 ações, lote 100). Preço de referência = preço médio da posição (protótipo usa R$ 38,00 só como exemplo).
4. Modo (Estudo × Operador) troca só texto, e o texto vem do backend. Layout e componentes são idênticos nos dois modos. No Operador, a folha de conceito e a grade com conta ("conta" por célula, `grade` de `cenarios_da_estrutura`) aparecem como hoje.
5. O dado de opções é leitura de fim de pregão (ver Estados). Nunca se apresenta como "agora".
6. Nenhum token novo, exceto o delta da seção Color (zero tokens de cor novos; 1 papel de tipografia nova não é criado).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (React single-file + módulos em `web/src/opcoes/`, estilos inline com tokens `T`) |
| Preset | not applicable |
| Component library | none (primitivos próprios; reaproveita `SetorAlvo`, `ConceitoSheet`, `PayoffChart`, `SecaoComparar`, `LastroDoAtivo`, `ExecutarProposta`) |
| Icon library | nenhuma nova. Chevron `›` e `‹` em texto, como o protótipo e o app |
| Font | Corpo: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`. Display (títulos de tela e de objetivo): Fredoka. Números: `ui-monospace, "SF Mono", Menlo, Consolas, monospace` com `font-variant-numeric: tabular-nums` |

Reaproveitar o que o app já carrega; se Fredoka já é a fonte display do app, não adicionar `@font-face` novo (checar no `index.html`/CSS).

---

## Spacing Scale

Múltiplos de 4. Escala declarada: 4, 8, 16, 24, 32, 48, 64.

| Token | Value | Usage nesta fase |
|-------|-------|------------------|
| xs | 4px | gap entre rótulo e valor, gap entre segmentos da régua |
| sm | 8px | gap entre chips, entre barras da escada, entre itens de legenda |
| md | 16px | padding horizontal de tela, padding interno de card, gap entre cards |
| lg | 24px | respiro entre seções de uma tela |
| xl | 32px | respiro antes do CTA principal |
| 2xl | 48px | altura mínima de célula da matriz e dos chips de vencimento |
| 3xl | 64px | altura mínima de card de objetivo e de degrau |

Exceções:
- 12px de padding interno em card compacto e em sheet (múltiplo de 4, herdado do app e do protótipo). Não usar 6, 9, 10, 13, 14, que aparecem no protótipo.
- Alvo mínimo de toque 44px em todo controle (CTA 48px, ver Acessibilidade). Controle abaixo de 44px visual ganha área de toque estendida (padding ou `::after`), nunca é encolhido.
- Raios: 12 em cards, 16 no topo da sheet, 999 em chips e pills (herdados).

---

## Typography

Contrato desta fase: 4 tamanhos, 2 pesos.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Label (rótulos mono em caixa alta, chips, eixos do gráfico, rodapés) | 12px | 700 | 1.4 |
| Body (frases, legendas, descrições de objetivo e degrau) | 14px | 400 | 1.5 |
| Heading (título de objetivo, ticker, título da sheet) | 16px | 700 | 1.2 |
| Display (título de tela: "Opções", ticker do ativo) | 24px | 700 | 1.2 |

- Pesos: 400 e 700 apenas. O protótipo usa 500/600/800; ao implementar, mapear 500→400 e 600/800→700. Na face Fredoka, o 700 renderiza com o corte mais próximo carregado (600 no protótipo): aceito, sem carregar peso novo.
- Números em R$, strikes, prêmios e eixos: mono + tabular-nums, no mesmo tamanho do texto vizinho.
- Rótulo mono em caixa alta (`opc-*`, "PIOR CASO") usa letter-spacing .08em. Não criar tamanho 10/10.5/11/11.5/13 novo: o protótipo os usa, o contrato os absorve em 12 (label) ou 14 (body). Eixos do SVG ficam em 12.
- Não há texto de produto abaixo de 12px. Texto de ajuda/estado do app que já usa 11px não é tocado nesta fase.

---

## Color

Tokens existentes (hex do protótipo, a validar contra `T`; ver Premissa 1). Zero cor nova.

| Role | Dark | Light | Usage |
|------|------|-------|-------|
| Dominant (60%) | `#10121a` (bg) | `#f7f8fc` | fundo de tela |
| Secondary (30%) | `#1b1f2e` (card), `#161927` (panel/sheet) | `#ffffff` (card), `#eef0f7` (panel) | cards de ativo, objetivo, degrau, matriz, sheet, chips |
| Accent (10%) | `#2fa8a0`; texto/ênfase `#5cc4bd` | `#1f7d76`; texto `#166861` | lista fechada abaixo |
| Destructive | n/a nesta fase | n/a | Não há ação destrutiva. `--neg` (`#f26d6d` / `#c6464c`) é cor semântica de PERDA, não de ação |
| Semântica de resultado | pos `#34d399`, neg `#f26d6d`, warn `#fbbf24` | pos `#1c825d`, neg `#c6464c`, warn `#a16207` | pos = ganho, neg = perda, warn = marcador do "E se…?" |
| Texto | fg `#eef1f8`, fg2 `#c9d1e6`, muted `#9aa3bd`, dim `#8890a8` | `#10121a`, `#2d3444`, `#5b6178`, `#646b7f` | hierarquia de texto |

Accent reservado para (lista fechada):
1. CTA primário da tela (Escolher este / Executar simulado), preenchido, texto `--on-accent`.
2. Estado selecionado: degrau (`aria-checked`), chip de vencimento e célula da matriz (`aria-pressed`): borda accent + fundo accent-tint.
3. Linha "com a estrutura" no gráfico e os 5 marcadores numerados.
4. Botão `‹ voltar` e rótulo de bloco "O QUE É / O QUE ACONTECE" na folha de conceito.
5. Foco visível (`outline 2px accent-soft`, offset 2).
6. Faixa lateral do vigia armado e o texto "atualizar ›".
Nunca em: termos clicáveis (usam sublinhado pontilhado em `--dim`), links de texto comuns, ícones decorativos.

Regras de não-manipulação (princípio do produto):
- Ganho e perda recebem o MESMO peso visual: mesma espessura de barra, mesma opacidade de preenchimento (~.2). Perda não é escondida nem suavizada.
- Verde/vermelho nunca são a única pista: toda barra, linha e marcador tem rótulo textual e valor em R$; perda no gráfico também ganha rótulo "perde"/sinal "−".
- Régua de regime: alta = verde cheio, baixa = listrado vermelho (padrão 135°), lateral = cinza. O formato carrega o significado além da cor.
- Contraste AA verificado no protótipo: dim sobre card escuro 5,15:1; accent 5,6:1; claro 5,3:1. O executor recalcula qualquer par que usar fora dessa lista (texto ≥4,5:1; elementos gráficos e bordas de controle ≥3:1). Em claro, `--warn` `#a16207` sobre card branco deve passar 4,5:1 se for texto.

---

## Mapa de telas e fluxo

Navegação: a aba Opções deixa de ter 3 sub-abas (`oportunidades`, `recomendadas`, `montar`) e o sheet de Vigias como superfícies de mesmo nível. Passa a ser um fluxo em profundidade, com `‹ voltar` em cada nível. Estado de navegação único (um só `ativo` selecionado, absorvendo `ticker` e `oportunidadeAberta`).

| # | Tela | Conteúdo | Custo |
|---|------|----------|-------|
| 1 | Hub "Opções" | topo (título + frescor + aviso virtual); seção "Atenção" (vigias armados, link ao estado do dia); seção "Sua carteira" (cards de ativo); aviso "abrir não gasta consultas" | 0 |
| 2 | Objetivo (por ativo) | "O que você quer fazer com as N ações?"; 3 cards de objetivo; atalho secundário "Montar do zero" (leva ao Montar atual) | 0 |
| 3 | Escada + gráfico | chips de vencimento; 3 degraus; botão "Comparar vencimentos"; gráfico "Resultado no vencimento"; legenda numerada 1-5; "E se…?"; "Ver os números"; frase de risco; CTA "Escolher este" | 0 (vencimento mais próximo); comparar = 2N+1 declarado |
| 4 | Confirmar | frase de risco; resumo de pernas, lote e lastro; CTA "Executar (simulado)"; CTA secundário opcional "Criar vigia" | 0 |
| Folha | ConceitoSheet | termos clicáveis (ver Termos) | 0; "Perguntar ao Boris" tem custo visível |

Fluxo: 1 → toque no card do ativo → 2 → toque no objetivo → 3 → "Escolher este" → 4 → "Executar (simulado)" → retorno ao hub com toast e posição atualizada. `‹` volta um nível e preserva a escolha (objetivo, degrau, vencimento) enquanto o usuário não trocar de ativo.

### Tela 1: Hub
- Card de ativo (`min-height` 64, toda a área clicável, `role="button"`, Enter/Espaço): ticker (mono 16/700), subtítulo "N ações · M livres para lastro" (lastro é termo clicável), régua de regime dos 7 pregões com legenda textual, chips (HV21, suporte/resistência), rodapé "K estruturas · J vigias" + `›`.
- Lista de cards vem da CARTEIRA (decisão da Fase 39, `OpcoesScreen.jsx:295`), nunca da watchlist.
- Seção "Atenção" só aparece se houver vigia armado. O botão "atualizar" declara "o estado do dia custa 2 consultas" antes do clique (ADR-027).
- Substitui: sub-abas Oportunidades/Destacadas, entrada do sheet de Vigias (vigias viram a seção Atenção + rodapé do card).

### Tela 2: Objetivo
- 3 cards (`min-height` 64): título 16/700 (Fredoka), 1 frase de descrição com termos clicáveis, linha "Perde: …" em muted. Ordem fixa: Proteger de queda, Gerar renda, Proteger com custo baixo.
- Cards desabilitados (não ocultos) quando o objetivo é inviável, com o MOTIVO escrito no próprio card (ver Estados, lastro).
- "Montar do zero" é link secundário abaixo dos cards (alvo 44px), leva ao fluxo Montar existente. Nada se perde (mapa de funções abaixo).

### Tela 3: Escada e gráfico
- Cabeçalho da seção: "Escolha o piso | teto | piso e teto" conforme o objetivo, com "ação a R$ X" à direita.
- Chips de vencimento: grid de 3 colunas, `min-height` 48, `aria-pressed`, mostra data e "N dias". Abre no vencimento mais próximo da carteira, sem consulta paga.
- Degraus: `role="radiogroup"` de 3 `role="radio"` (`aria-checked`), `min-height` 64, cada um com nome ("Mais protegido", "Equilibrado", "Mais barato" etc.), strikes em mono e 2 barras (pior caso/ganho máximo/prêmio ou custo conforme o objetivo, ver tabela). Selecionado: sobe 3px (transform) e borda accent. Teclado: setas movem o radio, Enter/Espaço seleciona.
- Colunas por objetivo: Proteger = perda máxima + custo da proteção. Gerar renda = ganho máximo + prêmio recebido + nota "sem piso: a queda não é limitada". Collar = perda máxima + ganho máximo (+ líquido "custa/recebe" na matriz).
- "Comparar vencimentos": botão secundário, largura total, com custo no rótulo ("N consultas (2×K+1) · restam X hoje"). Some ao clicar e abre a matriz. Matriz: linhas = vencimentos, colunas = degraus; célula (`min-height` 52, `aria-pressed`) mostra pior caso (ou ganho) e custo/prêmio; toque seleciona vencimento e degrau juntos. Linha com vencimento sem dado: células "—" com motivo.
- Gráfico "Resultado no vencimento": SVG responsivo (viewBox 340×214, `role="img"` + `aria-label` completo gerado do backend, ver Copy). Eixo x = preço da ação no vencimento; eixo y = R$ total nas N ações (padrão) com alternância "Total | Por ação" (segmented de 2 botões, 44px, `aria-pressed`). Duas linhas: "só as ações" (tracejada, `--dim`) e "com a estrutura" (cheia, accent-soft). Preenchimento pos acima de zero, neg abaixo. Linha vertical pontilhada no preço médio. 5 marcadores numerados (r=9 de raio visual, área de toque não é necessária pois a interação está na legenda): 1 piso, 2 equilíbrio, 3 teto, 4 perda máxima, 5 ganho máximo. Marcador sem sentido na estrutura (sem piso/teto) não é desenhado, e a legenda explica a ausência.
- Legenda numerada (mesma numeração 1-5): valor em mono + 1 frase; cada nome é termo clicável.
- "E se a PETR4 fechar a R$ X no vencimento?": `<input type="range">` nativo (`min-height` 44, `accent-color` accent), mostra "Só as ações" × "Com a estrutura" e 1 frase de diferença. Valor lido da grade do backend (lookup, sem conta no front).
- "Ver os números": `<details>` com tabela preço × só as ações × com a estrutura (alternativa textual ao gráfico, obrigatória para leitor de tela).
- Frase de risco (`aria-live="polite"`): "Pior caso … Melhor caso … Equilíbrio …", vinda pronta do backend.
- CTA "Escolher este" + "sem custo".

### Tela 4: Confirmar
- Frase de risco repetida; card com Estrutura, Vencimento, pernas (put comprada: strike e quanto paga; call vendida: strike e quanto recebe), lote e frase de lastro (travado ou "sem lastro: ações livres").
- CTA primário "Executar (simulado)" + "sem custo". `ExecutarProposta` existente faz a execução (todo-ou-nada; "ordem parcialmente executada" não existe no modelo).
- Linha "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco." fixa no topo de TODAS as telas (princípio 1).
- Stop/alvo nunca vetados: se a tela 4 oferecer proteção, "Aplicar proteção" fica sempre disponível. `operar: false` do parecer é aviso, nunca bloqueio.
- Pós-execução: toast "Ordem simulada registrada. Nenhuma ordem real foi enviada." + retorno ao hub.

---

## Interações, movimento e responsividade

- Transição de tela: `opacity` + `translateY(6px)`, 200ms ease-out. Folha: `translateY(24px)` + opacity, 220ms. Só transform e opacity.
- Degrau selecionado: `translateY(-3px)`, 180ms. Gráfico redesenha SEM animação.
- `prefers-reduced-motion: reduce`: todas as transições e animações desligadas (`transition: none`, `animation: none`), sem deslocamento de tela. Obrigatório e testável por guardião estático.
- Mobile-first: coluna única até 900px; desktop/PWA mantém a mesma coluna, `max-width` ~480px centralizada para as telas 2-4 (sem reflow de layout novo). Gráfico `width:100%; height:auto`. Matriz sem scroll horizontal em 375px (3 colunas × células flexíveis).
- Área segura iOS: `env(safe-area-inset-*)` no topo sticky e no rodapé (CTA).
- Foco: `outline 2px accent-soft`, offset 2, em todos os controles. Ordem de tab segue a ordem visual. Ao entrar numa tela, foco no título (`tabIndex=-1`); ao voltar, foco no controle que abriu.
- Tema: segue o app (escuro padrão, claro por `prefers-color-scheme`/preferência). Nenhum valor hardcoded fora de `T`.

---

## Estados (contrato completo; princípio 9)

Cada tela precisa dos estados abaixo. Texto vem do backend ou de `copy.js` (ver Copy). O front não inventa valor: campo ausente = "—" com causa, nunca 0.

| Estado | Tela(s) | Comportamento visual |
|--------|---------|----------------------|
| Carregando | hub, 3 | Skeleton de card (mesmas alturas, 64px) sem shimmer em reduced-motion. Texto sr-only "Carregando". Gráfico: placeholder do mesmo tamanho (sem layout shift). Consulta paga em curso: botão desabilitado com "consultando…" |
| Vazio: sem posição em carteira | hub | Heading + corpo (ver Copy) + CTA "Ver Carteira". Opções não funcionam sobre watchlist |
| Vazio: sem vencimento/estrutura montável | 3 | Linha "—" nos degraus + motivo do backend; CTA desabilitado |
| Erro de fonte (opções fora do ar) | todas | Faixa warn no topo com problema + próximo passo + "Tentar de novo" (44px). Não mostra número calculado. Impede Executar |
| Sem cotação/prêmio | 3, matriz | Célula/linha "—" + causa curta via `motivoSemCotacao` ("sem prêmio" etc.). Degrau afetado fica `aria-disabled` e não selecionável; Executar bloqueado |
| Cota esgotada (consultas ou IA) | botão Comparar, "Perguntar ao Boris", "atualizar" | Botão desabilitado, rótulo mostra "cota do dia esgotada" + quando renova. A explicação determinística continua visível (a IA é só complemento) |
| Mercado fechado | hub, 3, 4 | Selo "Pregão fechado" ao lado do frescor. Execução simulada permanece permitida só se a regra do motor a permitir; se o motor rejeitar, mostrar o motivo ("ordem rejeitada: …") |
| Dado atrasado / fim de pregão | hub, 3, 4 | Frescor SEMPRE visível no topo: "fonte · pregão DD/MM · em dia | atrasado | fim de pregão". Dado atrasado ganha selo warn e a frase "não é o preço de agora". Se o dado ultrapassa a janela do motor, Executar é bloqueado com motivo |
| Lastro indisponível | 2, 3, 4 | Objetivo Gerar renda e collar (que vende call) ficam desabilitados no card, com o motivo escrito (ex.: "só 100 ações livres; precisa de 300" ou "ações travadas em outra call"). Nunca ocultar. Link "ver lastro" abre o termo. Proteger (put) segue habilitado |
| Ordem rejeitada | 4 | Faixa neg com motivo do motor, nenhuma posição criada, CTA volta ao estado inicial |
| Operação concluída | 4 → hub | Toast + linha nova no rodapé do card ("K estruturas"). Sem animação de comemoração; sem linguagem de ganho |
| Ordem parcial | n/a | Não existe (execução tudo-ou-nada; achado C-14). Não criar estado nem copy para isso |

---

## Termos clicáveis (SUBLINHADO + ConceitoSheet)

Técnica exata do app (`web/src/entendimento.jsx`): `SetorAlvo` + `SUBLINHADO` (pontilhado, `T.textFaint`, offset 3, espessura 1) + toque simples + `ConceitoSheet`. O termo mais interno vence. Cada termo tem botão `sr-only` "O que é X?" (acessível por teclado, Enter/Espaço). A folha é `role="dialog"`, `aria-modal`, devolve o foco ao fechar, fecha com Esc e toque no fundo. Botão "Entendi" (44px) fecha. "‹ Voltar" quando há histórico; chips "veja também".

Alvo de toque: o termo inline pode ser menor que 44px visualmente; a área é coberta pelo botão sr-only/padding do `SetorAlvo` conforme o padrão do app. Termos em texto corrido só ganham sublinhado na PRIMEIRA ocorrência por bloco (evita parede de pontilhado).

| Termo | id | Tipo | Onda |
|-------|----|------|------|
| opção, strike, vencimento, call, put | `mkt-opcao` | KB existente (glossário) | já existe |
| piso | `opc-piso` | KB existente | já existe |
| teto | `opc-teto` | KB existente | já existe |
| equilíbrio | `opc-equilibrio` | KB existente | já existe |
| lastro | `opc-lastro` | KB existente | já existe |
| venda coberta | `opc-call-coberta` | KB existente | já existe |
| prêmio | `opc-premio` | NOVO: conceito (números do caso) + verbete KB | Onda 1 |
| perda máxima / pior caso | `opc-perda-maxima` | NOVO | Onda 1 |
| put protetora | `opc-put-protetora` | NOVO | Onda 2 |
| collar | `opc-collar` | NOVO | Onda 2 |

- Onda 1 (piso, teto, equilíbrio já existem; entram prêmio e perda máxima) destrava gráfico, legenda e frase de risco. Onda 2 (objetivos: put protetora e collar) destrava a tela 2. Se a Onda 2 não entrar junto, a tela 2 mostra o objetivo SEM o termo técnico (sem sublinhado órfão).
- Folha de conceito: 3 blocos na ordem do app: "O QUE O APP NÃO FAZ" (rótulo em neg), "O QUE É", "O QUE ACONTECE" (com os números do caso: strike, prêmio, perda, lote, vencimento, vindos do backend). Verbete KB puro (glossário) mostra só "O QUE É" com a nota "explicação geral, sem números de nenhum ativo".
- Mesmo texto em dois modos: o conceito e o verbete KB compartilham a fonte; educacional e operador têm versões separadas (`e`/`o`, `nao`/`nao_o`).
- "Perguntar ao Boris": dentro da folha, atrás de toque, com custo visível ("usa IA · restam N hoje"); se a IA falha ou a cota acaba, a explicação determinística permanece.
- Guardiões a adicionar/estender: `test_kb_ancoras.py`, `test_setores.py`, `test_setor_toque.mjs` (ids novos e rótulo sr-only), e paridade `skill_ref.py` ↔ `copy.js`.

---

## Copywriting Contract

Regra de ouro: o front NÃO compõe vocabulário. Frases de modo, rótulos de coluna, frase de risco, `faixaAria`/`payoff.aria`, motivos e verbetes vêm do backend (`skill_ref.py`, `conceitos.py`, `kb.py`, `cartao_posicao._txt`), com espelho em `web/src/copy.js` onde o app já espelha (paridade travada por teste). Os textos abaixo são o contrato de conteúdo; o texto literal final é revisado nas duas versões (Estudo e Operador) antes de entrar.

| Element | Copy |
|---------|------|
| Primary CTA (tela 3) | "Escolher este" + microlinha "sem custo" |
| Primary CTA (tela 4) | "Executar (simulado)" + microlinha "sem custo" |
| CTA secundário | "Comparar vencimentos" + "N consultas (2×K+1) · restam X hoje"; "Montar do zero"; "Criar vigia" (opcional) |
| Aviso fixo de saldo | "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco." |
| Frescor | "{fonte} · pregão {DD/MM} · {em dia / atrasado / fim de pregão}" |
| Pergunta da tela 2 | "O que você quer fazer com as {N} ações?" + "Você vê o pior caso e o gráfico antes de decidir. Termos sublinhados abrem uma explicação." |
| Objetivo: Proteger de queda | "Você paga um prêmio. Se a ação cair abaixo do piso, a perda para ali. Em termos técnicos, uma put protetora." / "Perde: o prêmio, se a ação não cair" |
| Objetivo: Gerar renda | "Você recebe um prêmio. Em troca, limita o ganho acima de um teto. Em termos técnicos, uma venda coberta, que trava as ações como lastro." / "Perde: ganho acima do teto" |
| Objetivo: Proteger com custo baixo | "O prêmio recebido paga (quase) o da proteção. Perda e ganho ficam entre o piso e o teto. Em termos técnicos, um collar." / "Perde: ganho acima do teto" |
| Frase de risco | "Pior caso: perde até R$ {X} nas {N} ações (R$ {x} por ação), por mais que a ação caia abaixo do piso de R$ {K}. Melhor caso: ganha até R$ {Y} … Equilíbrio: a ação precisa fechar a R$ {BE} no vencimento {DD/MM}." Sem piso: "sem piso, se a ação for a zero você perde R$ {X}; a queda segue a da ação, amortecida só pelo prêmio de R$ {p}". Sem teto: "sem teto: você ganha o que a ação subir, menos o prêmio pago" |
| Título do gráfico / subtítulo | "Resultado no vencimento" / "linha cheia = com a estrutura · tracejada = só as ações" |
| Alternância de unidade | "Total ({N} ações)" / "Por ação" |
| "E se…?" | "E se a {TICKER} fechar a R$ {X} no vencimento?" + "Só as ações" / "Com a estrutura" + diferença "Neste preço, a estrutura melhora/reduz o resultado em R$ {D}" |
| Empty state heading (hub sem posição) | "Você ainda não tem ações em carteira" |
| Empty state body | "As opções aqui são estudadas sobre as ações que você já tem na carteira virtual. Compre uma posição simulada e volte." + CTA "Ver Carteira" |
| Empty state (sem estrutura montável) | "Sem estrutura disponível para {TICKER} neste vencimento" + motivo do backend + "Tente outro vencimento ou monte do zero." |
| Error state (fonte) | "Não foi possível ler as opções agora. Nenhum valor foi estimado. Tente de novo; se persistir, os dados de opções estão fora do ar." + "Tentar de novo" |
| Sem cotação/prêmio | "—" na célula + causa curta de `motivoSemCotacao` |
| Cota esgotada | "Cota de consultas do dia esgotada. Renova {quando}. A explicação acima continua valendo." |
| Lastro indisponível | "Gerar renda indisponível: {motivo, ex.: só 100 ações livres; esta estrutura trava 300}." (card desabilitado, `aria-disabled`, motivo lido por leitor de tela) |
| Mercado fechado / atrasado | "Pregão fechado: estes valores são de {DD/MM}, não de agora." |
| Confirmação (destrutivo) | Nenhuma ação destrutiva nesta fase. "Executar (simulado)" não exige confirmação extra: a tela 4 já é a confirmação, com custo, pernas, lastro e frase de risco visíveis. Encerrar estrutura/call, se exposto no card, reaproveita o diálogo existente do app |
| Toast pós-execução | "Ordem simulada registrada. Nenhuma ordem real foi enviada." |
| Dado insuficiente (IA/explicação) | "Não há dados suficientes para concluir." (literal do produto) |

Proibido em qualquer texto: promessa de rentabilidade, "lucro garantido", "ganhe", "proteção total", "sem risco", linguagem de enriquecimento. "Proteger" descreve limite de perda, nunca eliminação do risco ("limita a perda, não a queda"). Toda frase de risco usa as palavras "pior caso" e "melhor caso" como pares, com o mesmo destaque.

### Reancoragem de rótulos e correção "Watchlist"
- Ajuda e tour dizem "escolhido na sua {Watchlist}" (`App.jsx:2704`, `2769`; o `grep` atual mostra `tWl` na linha 2704 e a frase "um ativo da sua lista" em 2769). O universo da aba é a CARTEIRA: reescrever ambos para "Carteira" (usar `cp.tituloPortfolio`, não `tWl`), e remover "quais estruturas do catálogo fazem sentido, os vencimentos disponíveis e os setups já armados" em favor da descrição do novo fluxo (objetivo, escada, vencimentos, gráfico). Manter a ressalva "leitura de fim de pregão" e "travessão, nunca zero".
- Sub-abas deixam de existir; os rótulos `opcoesAbaOportunidades/Recomendadas/Montar` em `copy.js` são mantidos enquanto o guardião os travar e removidos só com a reancoragem (nota datada).
- Tour: o passo 4 do funil continua sobre a aba Opções, com o texto novo (por modo, vindo de `copy.js`).

---

## Mapa "nada se perde: onde cada função vive"

| Função atual | Onde vive depois |
|--------------|------------------|
| Oportunidades (lista por ativo) | Hub, seção "Sua carteira" (cards) |
| Destacadas / Recomendadas | Escada da tela 3 (degraus por objetivo), mais o selo no card quando houver destaque |
| Montar | "Montar do zero" (link na tela 2), fluxo atual intacto |
| Vigias (sheet) | Seção "Atenção" no hub + rodapé do card + "Criar vigia" na tela 4; o `VigiasSheet` segue como destino do "ver todos" |
| Comparar (`SecaoComparar`) | Botão "Comparar vencimentos" e matriz na tela 3 (custo 2N+1) |
| Setups (`SecaoSetups`) | Rodapé do card ("K estruturas") e lista no ativo; sem perda de dado |
| Lastro (`LastroDoAtivo`) | Subtítulo do card, estado desabilitado do objetivo e linha da tela 4 |
| Payoff (`PayoffChart`, `ExplicacaoPayoff`) | Gráfico e legenda da tela 3 (base de desenho reaproveitada) |
| Executar (`ExecutarProposta`) | Tela 4, sem mudança de contrato |
| Controle fino de lote/contrato | "Montar do zero" (perda declarada na v1) |

---

## Pré-condições do código (A confirmar no código; verificado em 2026-10-05, sem implementar)

| Item | Veredito | Evidência e consequência para o plano |
|------|----------|---------------------------------------|
| 1. `cenarios_da_estrutura` cobre intervalo e passo do "E se…?" | CONFIRMADO COM RESSALVAS | `cartao_posicao.py:326`. Grade de `floor(0.8·min(hoje, BE, piso))` a `ceil(1.14·max(hoje, BE, teto))` em passos de `TICK=0.05` (até `MAX_PONTOS_GRADE`, passo cresce se exceder). Estudo devolve `simulador{min,max,passo,pontos[{preco,resultado,zona}],nomeados,zonas}`; Operador devolve `payoff{pontos,xMin,xMax,yMin,yMax}` + `grade`. Ressalvas: (a) exige exatamente 1 breakeven, senão devolve `None` (OK para put protetora, call coberta e collar; plano deve tratar `None` como estado "sem simulador"); (b) a faixa é derivada por estrutura, NÃO é fixa em ±21% como o protótipo (30–46 sobre 38): o eixo x do gráfico deve ler `min/max` (ou `xMin/xMax`) do backend; (c) é uma chamada por estrutura, então a escada de 3 degraus precisa de 3 cenários (1 por degrau) ou lazy só para o degrau selecionado |
| 2. `/mcp/possibilidades` devolve valores por vencimento equivalentes aos degraus | NÃO CONFIRMADO (provável campo aditivo) | `options_mcp_api.py:2535`. Devolve lista por vencimento com UMA `estrutura` (+ `emReais`, `razaoGanhoPerda`, `dominio`, `segmentos`) segundo a tese (`direcao`,`tipo`), não 3 degraus por vencimento por objetivo. Matriz vencimento × degrau exige ou 3 chamadas por tese, ou campo aditivo `degraus[]` por vencimento e objetivo. Custo 2×N+1 (D-24.1) hoje cobre N vencimentos para UMA estrutura; a matriz do protótipo (3 vencimentos × 3 degraus) não cabe no custo declarado se virar 3 chamadas. Decisão do plano: campo aditivo no backend ou reduzir a matriz à linha da tese. O rótulo de custo é o número que o backend informa, nunca calculado no front |
| 3. `opcoes_payoff` expõe pior caso, melhor caso e equilíbrio por degrau | CONFIRMADO POR ESTRUTURA | `opcoes_payoff.perfil_da_estrutura` devolve `ganho_maximo`, `perda_maxima`, `ganho_ilimitado`, `perda_ilimitada`, `breakevens[]`, `custo_liquido`, `curva[]`; `_em_reais` multiplica por lote (`ganhoMaximo`, `perdaMaxima`, `custoLiquido`). "Por degrau" = uma chamada por estrutura candidata (um degrau = uma estrutura). Estados a tratar: `perda_ilimitada`/`ganho_ilimitado` (sem piso/teto), `vencimentos.divergentes` (sem curva única), `ganho_maximo=None` com teto parcial (`payoff_aria_teto_parcial`) |
| Corolário | | Custo de `cenarios_da_estrutura` e `perfil_da_estrutura` é determinístico e sem chamada externa; o único custo pago é a consulta ao serviço de opções (`/possibilidades`, `proposta`). A tela 3 deve ser montável sem nova consulta paga depois da primeira (ADR-027) |

Se o item 2 exigir backend novo, o campo é ADITIVO (não altera contrato existente) e entra com guardião Python e paridade `defaults.py`↔`catalog.js` se tocar prompts.

---

## Guardiões a reancorar (nota datada; não apagar)

Princípio: reversão deliberada atualiza o guardião com nota datada; o histórico não se reescreve. Cada guardião troca a âncora, nunca a invariante.

| Guardião | O que trava hoje (a reancorar) | Nova âncora |
|----------|--------------------------------|-------------|
| `web/tests/test_opcoes_nav_tres_abas_ui.mjs` | 3 abas (`ABAS_OPCOES = oportunidades, recomendadas, montar`, `OpcoesScreen.jsx:288`) | Hub → ativo → objetivo → escada → confirmar; "Montar do zero" alcançável |
| `test_opcoes_subabas_ui.mjs` | sub-abas e rótulos `cp.opcoesAba*` | Nível de navegação em profundidade; rótulo do link "Montar do zero" |
| `test_opcoes_jornada_ui.mjs` | jornada atual entre as abas | Jornada nova (objetivo primeiro); mantém invariantes: lastro, custo declarado, "—" sem zero |
| `test_opcoes_continuidade_ui.mjs` | continuidade da seleção entre abas | Estado único de ativo/objetivo/degrau/vencimento preservado ao voltar |
| `test_opcoes_hub_workspace_ui.mjs` | hub/workspace atual | Novo hub (cards da carteira, seção Atenção) |
| `test_telas_registro.mjs` | registro de telas e rótulos em `telas.js` | Ajustar registro se rótulo/ordem mudar; ícone/título da aba "Opções" ficam |
| `test_tour_opcoes.mjs` | passo do tour da aba | Texto novo (sem "Watchlist", fala em Carteira); âncora do passo preservada |
| a adicionar | n/a | Reduced-motion (sem `transition` fora do bloco `@media`), alvos ≥44, `aria-checked` nos degraus, alternativa textual do gráfico, `role="dialog"` da folha, termos com `sr-only`, ausência de "Watchlist" na aba, ausência de `0` como substituto de ausente |

Invariantes que NENHUM guardião reancorado pode afrouxar: custo só em clique (`test_opcoes_custo_declarado.mjs`), universo = carteira (`test_opcoes_universo_carteira.mjs`), travessão em vez de zero, paridade `deviceStore` ↔ `serverStore`, manchete só do motor.

---

## Acessibilidade (checklist verificável)

- Contraste AA: texto ≥4,5:1; texto grande e elementos gráficos ≥3:1; claro e escuro verificados.
- Alvos ≥44px (CTA 48, chip de vencimento 48, célula da matriz 52, degrau/objetivo 64, slider 44).
- Gráfico: `role="img"` + `aria-label` do backend (`payoff.aria`/`faixaAria`) + tabela "Ver os números" equivalente; marcadores `aria-hidden` (a legenda carrega a informação).
- Radiogroup de degraus com setas; termos e cards operáveis por Enter e Espaço; Esc fecha a folha; foco devolvido.
- Cor nunca é única pista (rótulo, sinal, número e padrão listrado).
- `aria-live="polite"` na frase de risco ao trocar degrau/vencimento; estados de erro com `role="alert"`.
- Reduced-motion respeitado em todas as transições e animações.
- VoiceOver iOS: ordem de leitura = ordem visual; estados desabilitados leem o motivo.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none (shadcn não adotado) | not applicable |
| third-party | none | not applicable |

---

## Fora de escopo (para o executor não derivar)

- Caminho C (payoff com alças arrastáveis).
- Estruturas além de put protetora, call coberta e collar na escada.
- Fill parcial; recomendação personalizada; qualquer cálculo no front ou na IA; token de cor novo; ícones novos; mudança de bundle id.
- Reescrever `App.jsx` além das âncoras da aba, da Ajuda e do tour.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
