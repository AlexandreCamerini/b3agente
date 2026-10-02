---
status: closed_with_caveats
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
source: [teste do Alex no iPhone, 2026-10-01 (print UGPA3/CXSE3, Modo Operador)]
started: 2026-10-01
updated: 2026-10-02
---

# 46 — UAT (lacunas do card fechado v6 com texto longo)

Origem: o Alex testou o app no iPhone (build apontando para o backend local) e
reprovou a hierarquia do card FECHADO quando há texto longo e valores
monetários. Houve proposta visual aprovada no chat (protótipo interativo
"rótulo/valor" + "valor em uma linha"), cujas regras estão abaixo. Isto NÃO é
um VERIFICATION.md — o verifier da fase ainda não rodou; o checkpoint humano do
46-08 segue pendente e deve ser repetido após estas correções.

Escopo: SÓ o card fechado (`CartaoPosicao`, `LinhaEstadoV6`, `ReguaPlano`,
`FaixaVencimento` em `web/src/App.jsx`), os textos por modo
(`server/app/skill_ref.py` ↔ `web/src/copy.js`, byte a byte) e os guardiões
afetados. Sem tocar motor (`cartao_posicao.py`) além de expor dados que já
existam; cálculo financeiro continua 100 % determinístico no backend (nada de
número novo inventado no front). Cores: usar apenas `cartaoV6Cores.js`
(`varsCartaoV6`), nada de neutro global. Razões de contraste em comentário
com ponto e duas casas ("4.56:1"), nunca "4,5:1".

## Gaps

### G-01 — Palavra "Parcial" no lugar do número principal
status: failed
truth: O slot do resultado (canto superior direito do cabeçalho) mostra SEMPRE um número ou "—"; nunca uma palavra grande centralizada.
observed: UGPA3 exibe "Parcial" grande, mono, centralizado; a informação útil vira linha mono pequena.
decisão do Alex (aprovada): quando o total estiver suspenso mostrar "—" + chip "total suspenso" (tom pendente: bg #2D2618 / texto #FFE3A0 no escuro). NÃO mostrar o parcial no cabeçalho.

### G-02 — Linhas rótulo/valor logo abaixo do resultado
status: failed
truth: Logo abaixo do cabeçalho, linhas "rótulo (sans, secundário) à esquerda / valor (mono tabular) à direita", separadas por hairline:
  - `Ações` → resultado das ações (verde/vermelho conforme sinal, "+" explícito para positivo);
  - `Opções · <contrato>` → resultado da opção, OU o motivo em âmbar ("prêmio indisponível") — nunca zero/estimativa;
  - quando a ESTRUTURA existe (call coberta, collar, put de proteção, composta): linha de total `Estrutura` (borda superior mais forte, fonte 14) com o resultado da estrutura; se o prêmio faltar, mostrar "aguardando prêmio" em âmbar e o cabeçalho fica "—".
  - Cabeçalho com estrutura completa: número do resultado da estrutura + legenda "resultado da estrutura" (11 px); sem estrutura: legenda "resultado".
  - Ação simples (sem opções): linhas `Ações` e `Do capital` (sem linha de total).
  - O número do cabeçalho e o da linha `Estrutura` são o MESMO valor (mesma fonte do backend).
observed: hoje há uma linha mono "Ações −R$ 1.150,00 · Opções indisp." sem estrutura de coluna.
open: rótulo da linha de total é "Estrutura" (alternativas "Resultado"/"Total da estrutura"); usar "Estrutura" e registrar a chave em skill_ref/copy para troca fácil.

### G-03 — Três faixas de aviso empilhadas (viola D-13 "um estado")
status: failed
truth: No card fechado aparece UMA linha de estado (a de maior prioridade, regra D-13 / `estadoPrincipalV6`). Os avisos redundantes "Resultado parcial: um prêmio atual indisponível" e "Prêmio indisponível: <contrato>. Resultado total suspenso." deixam de ser faixas: a informação passa a viver na linha `Opções · <contrato>` (G-02). Para UGPA3 o único aviso é o cadeado: "Ações travadas pela call · saída após encerrar" (ícone de cadeado 16 px, bg #16233A, borda #465D7B, texto #D6DEEB no escuro).
observed: 3 caixas "ⓘ" seguidas no card fechado.
nota: investigar se as faixas duplicadas vêm de `LinhaEstadoV6` + avisos legados da Fase 45 (`TravaPill`/callouts) e remover a duplicidade na origem, ajustando guardiões com nota datada (asserção equivalente, nunca apagar).

### G-04 — Linha de meta corrida
status: failed
truth: A meta vira chips que quebram linha sozinhos (pill 999 px, 11.5 px, fundo #1B2A3D, texto #C1CDE0 no escuro): `1000 ações · PM 39,50`, `Call coberta` (nome da estratégia), `vence 19/11 · 49d`; para ação simples: `300 ações · PM 66,40`, `stop 62,00 · alvo 74,00`. Sem frase corrida com "·" que quebre no meio.
observed: "1000 ações · PM R$ 39,50 · call coberta · vence 19/11 (49d)" quebra de forma imprevisível a 130 % / 320 px.

### G-05 — Valor principal quebra em duas linhas
status: failed
truth: O valor do cabeçalho NUNCA quebra: "R$ 120,00" (ou "−R$ 123.456,78") em uma linha em 320/340/390 px e com texto a 130 %.
regras: coluna do resultado `flex: 0 0 auto` + `white-space: nowrap`; coluna do ticker/nome `min-width: 0` + `flex: 1 1 auto` e é ela que cede (nome da empresa quebra com `overflow-wrap: anywhere`); espaço entre "R$" e o número é NBSP (U+00A0) em TODA formatação monetária do card (cabeçalho e linhas rótulo/valor), valores das linhas também `nowrap`; fonte do valor 21 px, `letter-spacing: -0.3px`, mono tabular; se ainda não couber no pior caso (320 px × 130 %, valor de 7 dígitos) reduzir a fonte do valor (nunca quebrar linha).
observed: print do protótipo (CXSE3) mostrava "+R$" numa linha e "120,00" na outra; o mesmo risco existe no app.
acceptance: guardião estático trava `nowrap`/NBSP no componente; teste de pior caso (string longa) em `test_cartao_v6_fechado.mjs` ou guardião novo.

### G-06 — Régua: rótulos desconectados dos marcadores
status: failed
truth: Rótulos da régua ficam ancorados sob o respectivo marcador (equilíbrio ◆ valor; teto valor), usando a anti-colisão já existente (`ancoraRotulo` em `estruturaCard.js`, 46-02), em vez de 3 colunas fixas; o ponto "hoje" ganha legenda ("● hoje") e "sem piso" vira nota discreta na legenda. Valores vêm de `leitura_plano`/`estrutura`; "hoje" usa `quotes[t].price` (nunca `markPrice`).
observed: losango do equilíbrio a ~13 % da barra com o texto no meio; ponto "hoje" sem rótulo.

### G-07 — Nome da empresa não aparece nos cards da aba Posições
status: open (aberto em 2026-10-02, ressalva do checkpoint do 46-12; fora do fechamento da 46)
truth: O card de posição sempre mostra o nome da empresa sob o ticker quando ele é conhecido; sem nome conhecido, mostra só o ticker (nunca texto inventado).
observed: `CartaoPosicao` recebe `nomeEmpresa={q.name}` (App.jsx ~5647) e o nome some quando a cotação não traz `name`; não há fallback.
hipotese: fallback por catálogo de tickers (`CATALOG_TICKERS`/nome local) ou último nome conhecido; confirmar a causa no aparelho antes de implementar (cotação sem `name` por fonte vs. dado ausente no catálogo).
acceptance: teste com cotação sem `name` mostra o nome do catálogo; sem catálogo, só o ticker; nenhum nome inventado.

### G-08 — "Total suspenso" sem explicar a causa
status: open (aberto em 2026-10-02, ressalva do checkpoint do 46-12; fora do fechamento da 46)
truth: Quando o total da estrutura fica suspenso por prêmio de opção sem cotação (regra D-05, `estrutura_posicao.py`), o card diz a causa em linguagem do modo ("sem cotação da opção <contrato> nesta fonte") e continua mostrando "—" no cabeçalho. Nunca estima prêmio nem total.
observed: UGPA3 com UGPAK42 sem prêmio → "total suspenso" sem motivo. No teste do iPhone o servidor local rodava com provedor Yahoo (default do código), que devolve cadeia vazia para B3; produção usa `B3_OPTIONS_PROVIDER=mydata` (ADR-020). O sintoma provavelmente é artefato do setup de teste, mas a mensagem deve explicar a causa de qualquer forma.
acceptance: texto novo por modo em `skill_ref.py` ↔ `copy.js` (byte a byte); guardião da frase; sem vocabulário proibido; default de `B3_OPTIONS_PROVIDER` no código NÃO muda.

## Verificação esperada (para o plan-checker/verifier)
- `npx vite build`; guardiões do card v6 + os listados na SUMMARY do 46-08 verdes; `test_estrutura_card_contraste.mjs` com os novos pares (chip âmbar #FFE3A0/#2D2618, vermelho/verde sobre #111B29, 4 combinações tema × modo, ≥ 4.5:1 texto).
- Paridade `skill_ref.py` ↔ `copy.js` para qualquer chave nova; nenhum vocabulário proibido.
- Reexecutar o checkpoint humano do 46-08 no iPhone (build com `--api-base http://<IP-do-Mac>:8787`) após as correções.
