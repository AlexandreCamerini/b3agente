# QA 33 — Reorganização do Perfil em áreas dedicadas
*09/07/2026 · build alvo: F9-20260709-9*

Implementação da reorganização de UX proposta e validada no qa/32 (mockup
aprovado no chat, "vamos seguir"). Sem esta rodada, "Conta & preferências"
tinha virado um monólito de 7 seções empilhadas + 3 sub-componentes — o
próprio Alex identificou o sintoma: "a aplicação está ficando com muitas
funcionalidades... está na hora de revermos o UX".

## 1. O que mudou

O hub do Perfil (`PerfilHub`) tinha 3 linhas (Conta, Conta & preferências,
Observabilidade). Passa a ter 6:

1. **Conta** — inalterada (auth).
2. **Conta & preferências** — SLIM. Ficou só com o que é preferência pessoal
   de uso: Personalização (nome/tema), Período de candles, Orçamento,
   Perfil do operador.
3. **Configurações de IA** *(nova)* — Modelo/provedor do agente (BYOK),
   Skills por modo (Estudo/Operador), Prompts (stop/alvo por modo).
4. **Notificações** *(nova)* — a central de notificações (`NotifSection`),
   que já era autossuficiente, ganhou tela própria em vez de morar dentro de
   Conta & preferências.
5. **Eficiência da IA** *(nova)* — a autoavaliação da IA (qa/30/31), extraída
   da antiga Observabilidade.
6. **Logs & debug** *(renomeada de "Observabilidade")* — absorveu também
   "Servidor do app" e "Diagnóstico QA" (que antes viviam em Conta &
   preferências) junto com Status do servidor, Diário do operador e Logs
   detalhados que já estavam lá.

## 2. Como foi feito

`web/src/App.jsx`:
- `PerfilHub`: 6 `DrillRow`, cada um com ícone próprio (SVG inline, mesmo
  padrão stroke/currentColor do resto do app) e sub-texto dinâmico onde fazia
  sentido (notificações ativas/desativadas, operador ligado/desligado).
- 4 componentes de tela novos: `AiConfigScreen`, `NotificacoesScreen`,
  `EficienciaIAScreen`, `LogsDebugScreen`. Todo o JSX interno foi movido
  (copiado) das seções originais — sem reescrever a lógica/handlers, só
  realocando. `ObservabilidadeScreen` (monólito antigo) foi removida; seu
  conteúdo virou `EficienciaIAScreen` (card de eficiência) + `LogsDebugScreen`
  (o resto).
- `ConfigScreen`: perdeu `NotifSection`, `SkillSection`, `PromptsSection` e os
  blocos "Servidor do app"/"Diagnóstico QA"/"Modelo de IA" — junto com as
  variáveis/handlers que só existiam para eles (`srvTest`, `diagState`,
  `handleTestServer`, `runFullDiagnostic`, `copyDiag`, `srvColor`, `test`,
  `testColor`, `testBg`, `suggest`), que migraram para as telas novas.
- Roteamento (`perfilView`): de `hub | config | observabilidade` para
  `hub | config | ia | notificacoes | eficiencia | logs`, cada um com seu
  próprio `BackHeader`.
- `A.openNotifCentral` (atalho usado no card "Operador IA" e na tela
  Evolução) passou a navegar direto para `notificacoes` em vez de `config` —
  antes levava para dentro do monólito e a pessoa ainda tinha que rolar até
  achar a seção.
- 2 strings de ajuda que apontavam "Perfil → Observabilidade" foram
  atualizadas para "Perfil → Logs & debug" (Operador IA: texto de introdução
  e mensagem de erro de timeout).

## 3. Decisões de design tomadas nesta implementação (não estavam no mockup)

- **"Servidor do app" e "Diagnóstico QA" foram para Logs & debug, não para
  Configurações de IA** — apesar do diagnóstico testar também a config de IA,
  ele é uma ferramenta técnica geral (servidor + IA + notificações juntos);
  faz mais sentido ao lado dos outros logs técnicos do que dentro de uma tela
  de configuração de produto.
- **Disponibilidade sem login preservada**: "Servidor do app" e "Diagnóstico
  QA" continuam visíveis mesmo sem conta (como já eram em Conta &
  preferências) — só a parte "Status do servidor / Diário / Logs
  detalhados" (que sempre exigiu login) manteve o gate. Fundir as duas telas
  sem essa distinção teria tirado a ferramenta de diagnóstico de quem mais
  precisa dela (quem não consegue logar).
- **Ícones novos**: como o app usa SVG inline (não Tabler/webfont), desenhei
  4 ícones simples no mesmo estilo stroke/currentColor já usado no resto do
  Perfil (lâmpada para IA, sino para notificações, alvo para eficiência,
  barras — reaproveitado do antigo ícone de Observabilidade — para logs).

## 4. Testes

Novo guardião: `web/tests/test_perfil_reorg.mjs` (37 asserções) — tranca:
1. as 6 entradas do hub e suas rotas (`onOpen("ia")`, `"notificacoes"`,
   `"eficiencia"`, `"logs"`, `"config"`, mais Conta via `openAuth`);
2. que as 4 telas novas existem e a `ObservabilidadeScreen` antiga não existe
   mais;
3. que `ConfigScreen` (agora slim) NÃO contém mais as seções que migraram
   (sem duplicação de UI);
4. que as seções migradas realmente vivem nas telas novas;
5. que o roteamento (`perfilView`) cobre as 6 rotas;
6. que `openNotifCentral` aponta para `notificacoes`.

`web/tests/test_notif_central.mjs`: 1 asserção pré-existente ficou obsoleta
(esperava que o atalho navegasse para `"config"`) e foi atualizada para
`"notificacoes"` — mesma lição do qa/32 (mudança de design aprovada quebra
teste antigo; o teste antigo é quem estava errado, não o código novo).

```
Backend (offline, sandbox sem rede): 20/20 — 0 falhas, 1 pulada.
Web: 30/30 arquivos — 0 falhas (29 anteriores, 1 atualizado
[test_notif_central.mjs] + test_perfil_reorg.mjs novo).
```
Sintaxe verificada via `@babel/parser` (modo JSX) — sem erro.

## 5. Build

`web/src/version.js`: `BUILD_ID` `F9-20260709-8` → **`F9-20260709-9`**.

## 6. Roteiro de hard stop

1. `bash entregar.sh "qa/33: Perfil reorganizado em 6 áreas dedicadas"` (no Mac).
2. Xcode: ⇧⌘K + Run no iPhone físico.
3. Perfil → rodapé → confirmar **F9-20260709-9**.
4. Perfil → conferir as 6 linhas: Conta, Conta & preferências, Configurações
   de IA, Notificações, Eficiência da IA, Logs & debug.
5. Perfil → Conta & preferências → confirmar que NÃO tem mais notificações,
   skill, prompts, servidor do app, diagnóstico nem modelo de IA (só
   personalização, candles, orçamento, perfil do operador).
6. Perfil → Configurações de IA → confirmar modelo/provedor + skills +
   prompts, tudo funcionando (testar conexão, salvar skill, salvar prompt).
7. Perfil → Notificações → confirmar central completa (toggle, permissão,
   push, diagnóstico).
8. Perfil → Eficiência da IA → confirmar os números da autoavaliação (ou o
   estado vazio, se ainda não tiver análises avaliadas).
9. Perfil → Logs & debug → confirmar servidor do app + diagnóstico QA (sem
   login) e status/diário/logs detalhados (com login).
10. Operador IA → tocar no atalho de notificações → deve cair direto em
    Notificações (não mais em Conta & preferências).

## 7. Pendente

Fase B da eficiência (trades reais). Itens B(resto)/C/D/E da matriz qa/26.
Fraseologia (copy.js) contra os mocks. Radar sem "análise inicial rápida".
"Desenhar o prompt como especialista no Claude" (escopo ainda não
confirmado).
