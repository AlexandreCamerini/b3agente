# Sublinhado + toque, e o pet do assistente

Revisão da spec do toque longo, depois do teste no aparelho (2026-08-06).
Leia antes: `.claude/skills/didatica-bolsia/SKILL.md`.

## Por que o toque longo caiu

Testado ao vivo pelo Alex no mobile, o gesto falhou em três pontos que se
compõem:

1. **Sem indicação na tela** — nada dizia onde segurar.
2. **Sem saber onde, a pessoa segura em qualquer lugar** — e fora dos setores
   quem responde é a **seleção de texto** do sistema. O gesto certo no lugar
   errado produz o pior resultado possível.
3. Toque longo só funciona quando o alvo é óbvio (foto, mensagem, ícone).
   Num card cheio de texto, nunca vai ser.

Decisão: **trocar a ideia, não calibrá-la.** O que sobrevive (~90%): o
registro de setores no backend, a folha, o encadeamento, a allowlist
`tela:"setor:<id>"` do assistente, os contadores `gestoUso`, os guardiões.
Só o gesto e a indicação mudam.

## O desenho novo — referências de apps

**F1 — Duolingo: sublinhado pontilhado + toque simples.** Todo termo
explicável ganha sublinhado pontilhado discreto; **tocar** (tap) abre a folha
que já existe. A indicação mora no próprio termo, o gesto é universal, tap
não seleciona texto nem compete com rolagem. A dica de rodapé morre — o
sublinhado É a indicação, permanente e silenciosa.

**F2 — o pet (Codex/Duo): companion persistente do assistente.** Avatar
pequeno e fixo (canto inferior, acima da tab bar) nas telas de estudo. Tocar
abre a folha do assistente em dois estágios: primeiro **"o que esta tela
afirma"** — resumo determinístico montado dos conceitos do card visível,
grátis — e abaixo a pergunta livre (LLM, exige conta, teto existente,
`tela:"pet:<aba>"` na allowlist). Push do gatilho faz o pet ganhar badge, não
abrir folha sozinho. No Operador o pet some (isolamento estrutural, mesma
regra da via proativa).

**F3 — voz de SAÍDA.** Botão "ouvir esta explicação" na folha:
`speechSynthesis` com voz pt-BR; se o WKWebView falhar na medição, plugin
nativo de TTS do Capacitor como plano B. **Entrada** por voz fica fora: exige
SFSpeechRecognizer via plugin nativo — decisão separada, depois de o pet
provar uso.

## Decisões que não mudam

- Registro `conceitos.SETORES` no backend; região nova = build, reponteamento
  e texto = deploy.
- Tap entrega o determinístico; a LLM continua opt-in atrás dele (grátis
  responde antes do pago).
- Setor mais interno vence (stopPropagation no click).
- Caminho acessível: botão sr-only por setor continua (o tap já é acessível
  por si, mas o rótulo "O que é X?" dá o nome que o VoiceOver lê).
- `gestoUso` continua medindo: `gesto` = toques no sublinhado, `botao` =
  via sr-only; `aberturas` deixa de ser incrementado (a dica morreu).
- Campo ausente derruba parágrafo; vocabulário do backend; `/api/timing`
  intocado.

## Fases

**F1 — tap + sublinhado (executar agora).** `SetorAlvo` troca a máquina de
estados do toque longo por `onClick`; termos-chave ganham o pontilhado
(rótulo do badge, carimbo da barra, chips de confluência/fundamento, caption
da régua, "R:R"); `DicaGesto` e o incremento de aberturas saem; guardiões
reescritos para o contrato novo.

**F2 — pet (executada).** Avatar decidido pelo Alex: coruja animada no padrão
do PoC SwiftUI dele (🦉 + piscar 4s + boca ciclando 150ms + "respira" ao
falar), traduzida para React/emoji — a voz de saída veio junto porque o PoC é
inseparável dela: `speechSynthesis` pt-BR no WKWebView é o mesmo
AVSpeechSynthesizer do iOS. Entregue: `GET /api/pet/resumo` (determinístico,
frases canônicas de `timing.montar` + conectivas na rota), `PET_TELAS` na
allowlist do assistente, `PetFab`/`PetSheet`/`Coruja` no front, `petResumo`
nos dois stores, guardiões `test_pet.py` + `test_pet_ui.mjs`. Fica para o
aparelho: MEDIR a voz no WKWebView real (F3) e o badge do push no pet.

**F3 — voz de saída.** Medir `speechSynthesis` pt-BR no WKWebView no
aparelho; botão "ouvir" na folha; fallback plugin nativo.

## Critérios de aceite (F1)

- Tocar cada termo sublinhado abre a folha correta com os números do card;
  rolagem e toque fora dos sublinhados não abrem nada; **nenhuma seleção de
  texto** dispara nos setores.
- Zero resíduo do toque longo: `grep -n "GESTO_MS\|DicaGesto" web/src/App.jsx`
  vazio.
- Setor interno continua vencendo (carimbo→barra15m, chip→fundamento).
- `/api/timing` com as mesmas 20 chaves; suítes verdes com saída colada;
  guardião novo travando o contrato do tap; verificação ao vivo com
  screenshot (sublinhado visível + folha aberta por tap).
- Operador: sem via proativa (inalterado); sublinhado presente (a explicação
  não é exclusiva do Estudo).

## Deploy

Mesmo caminho da casa (BUILD_ID → publicar-web.sh → atualizar.sh → conferir
/api/health). O tap é código de app: o web pega no deploy; o iPhone só com
`instalar.sh --iphone`. O toque longo deployado ontem nunca chegou a build de
iPhone — o web troca de gesto no próximo deploy e nenhum aparelho fica com o
gesto morto.

## O que não fazer

- Não manter o toque longo "além do tap" — dois gestos para a mesma coisa é
  o dobro de coisas a aprender.
- Não sublinhar tudo: só o termo-âncora de cada setor, um por setor.
- Não fazer o pet abrir folha sozinho (o one-shot proativo do gatilho já
  existe e continua sendo o único caso).
- Não chamar LLM no tap nem no primeiro estágio do pet.
- Não implementar entrada por voz sem medição e sem decisão de escopo.
