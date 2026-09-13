---
name: didatica-boris
description: Regras da camada de entendimento do Boris+ — vocabulário por modo, princípios de dado, guardiões e caminho de deploy. Use ao escrever ou revisar texto didático, explicação de conceito no card, ou qualquer resposta do assistente de IA que leia dados da tela.
---

# Camada de entendimento do Boris+

O que uma sessão precisa saber para escrever explicação, conceito ou resposta
de assistente sem reintroduzir erro já resolvido.

## Vocabulário por modo (não negociável)

A fonte é `server/app/skill_ref.py`:

- `vocab["educacional"]` — Modo **Estudo**. Descreve condição, nunca ordem.
  Vereditos: `Estudar alta | Estudar baixa | Monitorar | Aguardar | Não operar`.
- `vocab["operador"]` — Modo **Operador**. Fala como mesa.
  Decisões: `COMPRAR | VENDER | AGUARDAR CONFIRMAÇÃO | NÃO OPERAR`.
- `TIMING[modo][estado]` — frase canônica de cada estado de timing, incluindo
  as variantes `fora_pregao` e `aguardando_barra`.

Texto novo entra **nessas estruturas**, não solto no front. O front recebe a
frase pronta; ele não compõe vocabulário.

## Princípios de dado

- **Princípio 1** (`skill_ref.PRINCIPIOS`): o backend calcula, a LLM
  interpreta. Nenhum número é inventado.
- **Sem pacote técnico** (`skill_ref.PRINCIPIO_DADOS_SEM_PACOTE`): em rota que
  não recebe o pacote, cite apenas o que é derivável dos dados fornecidos.
- Para o assistente: o que não estiver no snapshot recebido, ele diz que não
  tem — não estima, não completa.

## Sublinhado + toque e o registro de setores

A afordância da camada é o padrão do Duolingo: termo explicável carrega
SUBLINHADO PONTILHADO (`SUBLINHADO` em `web/src/App.jsx`) e abre a folha com
TOQUE simples. O toque longo (v1) caiu no teste ao vivo: sem indicação, a
pessoa segurava em qualquer lugar e a seleção de texto do sistema respondia.

O front declara regiões (`SetorAlvo`); **o que cada região explica** vem de
`conceitos.SETORES` (`server/app/conceitos.py`), servido em `GET
/api/conceitos` como `setores`.

- Repontear um setor, mudar texto ou encadeamento = **deploy** do Railway.
- Região nova na tela ou mudança no gesto = **build** (`instalar.sh --iphone`).
- `tela: "setor:<id>"` no `/api/assistente` é allowlist contra `SETORES` —
  id desconhecido é 400, nunca prompt.
- O setor mais interno sob o dedo vence (stopPropagation no click); um
  sublinhado por setor, só no termo-âncora.
- Acessibilidade: cada setor carrega botão sr-only "O que é X?".
- Medição: `config.gestoUso` — `gesto` = toques no sublinhado, `botao` =
  sr-only; monotônico (max) nos dois stores.

Guardiões: `server/tests/test_setores.py`, `web/tests/test_setor_toque.mjs`.

## O pet (Boris) e a voz

Mascote do assistente: o componente é `Boris` (a coruja desenhada em
`web/src/pet/Boris.jsx`), montado por `PetFab`/`PetSheet` em
`web/src/App.jsx`. Aparece em QUALQUER aba e nos DOIS modos de trabalho — a
restrição por modo foi revertida na Fase 1 da auditoria de UX (2026-08-08,
reversão registrada no comentário do render em `App.jsx`, ~`:9590`). O que
ainda condiciona o FAB não é aba nem modo: didática ligada, tela livre de
overlay (some sob folha aberta, para não competir) e o interruptor
`config.fabVisivel` (F10-20260809, default LIGADO nos dois modos — é opção
de esconder, não reversão da Fase 1). E NUNCA abre sozinho (o único one-shot
proativo segue sendo o do gatilho). O resumo vem de `GET /api/pet/resumo`
(determinístico: frases canônicas de `timing.montar` + conectivas NA ROTA —
o front exibe e fala a MESMA lista `fala`). A pergunta LLM usa
`tela: "pet:<id>"`, allowlist `conceitos.PET_TELAS`. Voz de saída: roteada
por plataforma em `web/src/pet/vozBoris.js` (`falarTexto`/`calarVoz`) — Web
Speech API pt-BR no PWA, plugin TTS nativo
(`@capacitor-community/text-to-speech`) no app Capacitor, porque o WKWebView
não confia no `speechSynthesis`; fechar a folha CALA a voz; sem voz, o texto
continua inteiro. Guardiões: `server/tests/test_pet.py`,
`server/tests/test_pet_todas_telas.py`, `web/tests/test_pet_ui.mjs`,
`web/tests/test_boris_voz_nativa.mjs`.

## Explicação boa, nesta base

- Ancorada no número daquele card, naquele instante.
- Responde três perguntas: o que é, o que acontece quando ocorre, e o que
  **não** acontece (o app não executa ordem; a decisão é da pessoa).
- Escrita para quem não sabe o que é uma vela de 15 minutos.
- `profile.experiencia` gradua a profundidade; não cria texto paralelo.

## Guardiões antes de entregar

```bash
cd server && ./.venv/bin/python -m pytest -q
```

```bash
cd web && for t in tests/*.mjs; do node "$t" >/dev/null || echo "FALHOU: $t"; done
```

Os que travam esta área: `server/tests/test_timing.py` (estados e variantes de
frase), `web/tests/test_timing_ui.mjs` (badge e rótulos). Regra da casa:
mudança de comportamento vem com guardião que a trava.

## Caminho de deploy

O front em produção **não** vem de `web/dist` — o Railway só enxerga
`server/`, então o web mora em `server/web_dist`, versionado.

```bash
bash scripts/publicar-web.sh
```

```bash
bash atualizar.sh --somente-deploy "mensagem"
```

Bumpe `web/src/version.js` (`BUILD_ID`, padrão `F10-AAAAMMDD-NN`, data real do
dia) antes de publicar; `publicar-web.sh` sincroniza o `SERVER_BUILD_ID`.
Confirme em `/api/health` que o carimbo novo subiu.

O app iOS só muda com build novo (`bash instalar.sh --iphone`); conteúdo servido
pelo backend vale assim que o Railway sobe.

## Paridade dos dois stores

`web/src/persistence.js` tem `deviceStore` (iOS, local-first) e `serverStore`
(web). Campo ou método novo entra nos **dois** — o guardião
`web/tests/test_api_parity.mjs` cobre parte disso.
