# PROPOSTA-UX — Nova arquitetura de informação do BolsIA
**Status: ✋ GATE — aguarda aprovação do Alex antes de QUALQUER mudança de UI.**
Zero perda de funcionalidade: checklist item a item na §4.

---

## 1. Mapa atual (inventário por tela)

| Tela (aba) | O que exibe hoje |
|---|---|
| **Evolução** | saudação, curva de capital, streak, coach/insight, desafio da semana, KPIs (retorno acumulado etc.) |
| **Mercado** | watchlist com cotações, análise IA por ativo (N2 atual), modelos técnicos (TECH_MODELS), gráfico, compra |
| **Radar** | varredura do universo, setups + confluência + veredito, condições técnicas, disclaimer |
| **Opções** | cadeia/estudo de opções do ativo |
| **Carteira** | posições (cotação de novo), stop/alvo (+ IA stop/alvo), P&L por posição, histórico (sub-view), **Agente** (sub-view) |
| **Perfil** | conta, Config (IA/BYOK, candlePeriod, notificações, orçamento/risco), skill, prompts, disclaimer completo |

## 2. Duplicatas e atritos identificados

| # | Informação | Onde repete | Casa única proposta |
|---|---|---|---|
| D1 | **Cotação do ativo** | Mercado (watchlist), Carteira (posição), Radar (close), Opções | Componente único `TickerHeader` com preço/variação — cada tela o REUSA, nunca re-renderiza a informação de forma própria |
| D2 | **KPIs de resultado** (retorno, patrimônio) | Evolução (curva+KPIs), Topbar (patrimônio-hero), Carteira (P&L somado) | Topbar = patrimônio-hero (só); ACOMPANHAR = detalhe completo; Carteira mostra SÓ P&L por posição |
| D3 | **Disclaimers** longos repetidos por card na MESMA tela | Radar (por resultado), Mercado (por análise), Coach | 1 disclaimer por TELA (rodapé fixo curto + link "aviso completo" do Perfil); textos por card viram uma linha padrão |
| D4 | **Análise IA** em dois lugares distintos (Mercado: análise; Radar: veredito) sem ponte | Mercado × Radar | Jornada única: Radar DESCOBRE → "Análise completa" abre AVALIAR no ativo (mesmo motor N2) |
| D5 | **Stop/alvo** aparece na análise (stopSugerido/alvoSugerido) E na Carteira (IA stop/alvo) com fluxos separados | Mercado × Carteira | N3 é UM fluxo: sugerido na criação da posição e editável na posição (mesma tela, mesmo formato de cenários) |
| D6 | **Config de IA + endereço do servidor + BYOK** misturados com preferências de uso | Perfil/Config | Perfil dividido: "Conta" / "IA & chaves" / "Preferências (janela, notificações)" / "Sobre & avisos" |
| D7 | **Agente** escondido como sub-view da Carteira | Carteira | Vira casa própria (AUTOMATIZAR) — pré-requisito da Fase 3 (agente server-side com parâmetros) |

## 3. Nova arquitetura — jornada em 5 casas (wireframe textual)

Navegação inferior: **⊙ Descobrir · ◔ Avaliar · ▤ Operar · ⚙ Automatizar · ↗ Acompanhar** (Perfil no avatar da Topbar).

```
TOPBAR (todas as telas)
[logo]  Patrimônio simulado R$ 12.480 (+3,2%)          [avatar→Perfil]

1) DESCOBRIR  (Radar absorve Mercado/watchlist)
   [Varredura: universo IBOV · janela 6M · botão Varrer]  [custo IA estimado]
   ── Top oportunidades (determinístico, grátis) ──
   [PETR4  confluência 78%  Estudar alta   ▸]
     ↳ expandir: checklist do setup (presentes ✓ / ausentes ✗)
     ↳ ações: [Aprofundar com IA (N1)] [Análise completa → AVALIAR]
   ── Minha watchlist ── (cards compactos, TickerHeader único)
   rodapé: disclaimer curto fixo

2) AVALIAR  (análise do ativo — N2)
   [TickerHeader: PETR4 · R$ 38,29 · −1,2%]   [gráfico candlePeriod]
   [Síntese IA]  [por família: Tendência|Momentum|Volatilidade|PriceAction|Volume]
   [MODELOS UTILIZADOS ▾]  [Cenários de estudo ▾]
   CTA: [Simular compra] → modal pré-preenchido (qtd sugerida pelo orçamento)
   pós-compra: oferta N3 "Definir alvo e stop com IA"

3) OPERAR  (carteira)
   [posição PETR4 · qtd · PM · P&L]   [stop 36,28 | alvo 41,10  ✎ via N3]
   ações por posição: [Reanalisar (N2 com contexto da posição)] [Vender]
   [Histórico de análises da posição — o que a IA disse × o que aconteceu]
   sub-view: histórico de operações (como hoje)

4) AUTOMATIZAR  (agente — casa própria, pronta p/ server-side F3)
   [Agente: LIGADO ▣]  modo: [executar | apenas sinalizar]
   regras: [stop ▣] [alvo ▣] [trailing ▢]   tetos: [3 ops/dia] [R$ 500/op]
   [log do agente: "12:31 vendeu VALE3 (stop) — simulado"]
   aviso: "modo em segundo plano requer conta" (anônimo = foreground)

5) ACOMPANHAR  (Evolução enxuta)
   [curva de capital + KPIs completos (casa ÚNICA dos KPIs)]
   [streak] [coach] [desafio]  — cards atuais preservados

PERFIL (via avatar): Conta · IA & chaves · Preferências · Sobre & avisos
OPÇÕES: vira aba interna de AVALIAR (estudo de opções do ativo em foco)
```

## 4. Checklist de preservação (funcionalidade → novo lugar)

| Funcionalidade atual | Nova casa |
|---|---|
| Watchlist + catálogo de tickers | DESCOBRIR (seção watchlist) |
| Análise IA do ativo + TECH_MODELS | AVALIAR |
| Gráfico com candlePeriod | AVALIAR (header) |
| Compra/venda simulada | AVALIAR (CTA) + OPERAR (posição) |
| Stop/alvo manual e via IA | OPERAR (✎ na posição, fluxo N3) |
| Histórico de operações | OPERAR (sub-view, intacto) |
| Agente + ciclo | AUTOMATIZAR (promovido) |
| Radar v2 completo (setups/confluência/veredito) | DESCOBRIR (núcleo) |
| Opções | AVALIAR (aba interna) |
| Curva de capital, KPIs, streak, coach, desafio | ACOMPANHAR |
| Config (IA/BYOK/servidor/janela/notif/orçamento) | PERFIL (4 seções) |
| Welcome boot gate, login, disclaimer completo | Inalterados |

## 5. Plano de migração incremental (nunca big-bang)

Cada etapa = 1 entrega validável em device; rollback = 1 revert:
- **M1** Topbar/nav novas com telas ATUAIS mapeadas (rename das abas; Agente promovido a aba; zero mudança interna) ✋ device
- **M2** DESCOBRIR: Radar absorve watchlist + ações do card (Fase 2.1) ✋
- **M3** AVALIAR: análise por família + fluxo Simular compra (2.2) ✋
- **M4** OPERAR: N3 na posição + Reanalisar + histórico de análises (2.3–2.5) ✋
- **M5** ACOMPANHAR/PERFIL: consolidação de KPIs e Config em seções ✋
- **M6** Varredura de disclaimers (D3) — última, com revisão de texto

## 6. O que esta proposta NÃO muda
Identidade visual (Palette 1 aprovada), Topbar patrimônio-hero, dual-store,
guardrails, disclaimers (conteúdo), fluxo de login. Só REORGANIZA.

---
**✋ Aguardando aprovação. Alternativas em aberto se preferir:** (a) manter
Mercado e Radar separados e só criar as pontes (menor mudança); (b) Opções
como aba própria em vez de interna. A Fase 1 (backend) segue em paralelo
sem depender desta decisão.
