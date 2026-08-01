# Auditoria dos prompts e instruções da LLM — handoff para execução

> **Data da auditoria:** 2026-07-31 · **Base:** `main` @ `39f2910` (release F9-20260731-01)
> **Escopo:** todas as instruções enviadas à LLM para análise de ativos — persona,
> princípios, indicadores, regras, contratos de saída — em `server/app/skill_ref.py`,
> `server/app/llm.py` e `server/app/defaults.py`.
> **Objetivo deste documento:** permitir que um NOVO chat execute as correções sem
> perder nenhum detalhe. Cada achado traz onde está, a evidência textual, por que é
> problema, a correção proposta e o critério de aceite.

---

## 1. Contexto mínimo (para quem chega agora)

BolsIA: simulador educacional da B3 (backend FastAPI no Railway + app Capacitor
iOS). A análise de ativos por LLM tem **quatro superfícies**:

| Superfície | Função no produto | Onde monta o prompt |
|---|---|---|
| **N2** `analyze_structured` | Análise estruturada da aba Mercado (pacote técnico + candles) | `llm.py:533` (user prompt em `llm.py:496`) |
| **N1** `analyze_deep` | "Aprofundar com IA" do Radar (setups + pacote completo) | `llm.py:823` |
| **Legado** `analyze` | Caminho antigo (só candles crus em TSV) | `llm.py:580` (user prompt em `llm.py:244`) |
| **N3** `analyze_carteira` | Stop/alvo por ativo da carteira (prompt editável pelo usuário + piso do servidor) | `llm.py:1001` |

Dois **modos** de app: `estudo` (educacional — sem verbo de ordem; enum
"Estudar alta|Estudar baixa|Monitorar|Aguardar|Não operar") e `operador` (mesa —
"COMPRAR|VENDER|AGUARDAR CONFIRMAÇÃO|NÃO OPERAR"). A fonte canônica da
metodologia é **`skill_ref.py`** (persona, 11 princípios, processo em 9 passos,
contrato de dados, conclusões canônicas, vocabulário por modo) — `llm.py` e
`defaults.py` **compõem** a partir dela em vez de reescrever.

Padrão do projeto: **"prompt pede + código impõe"** — todo guardrail crítico tem
enforcement pós-resposta em código (remap de enum PRO, teto de convicção,
fallback de `planoEstudo`, default de `confianca`), além do pedido no prompt.

---

## 2. Invariantes — o que NÃO pode quebrar

1. **Contratos de saída parseados pela UI**: chaves do FORMAT
   (`direcao/conviccao/qualidade/recomendacao/resumo/confirmacoes/invalidacoes/cuidados/fatosRelevantes/corpo/stopSugerido/alvoSugerido`),
   do DEEP_FORMAT (`resumo/leituraSetups/cenarios/riscos/invalidacao/confianca/planoEstudo/modelosUtilizados`)
   e do N3 (array por ativo `{ativo, precoAtual, stop, alvo, explicacao, operar}` +
   extensão `cenarios`). **Nenhuma correção pode mudar chave ou enum consumido pela UI**
   (a UI estiliza os valores via REC_STYLE; `kpi.py` normaliza).
2. **Enforcement em código** (não remover ao mexer nos prompts):
   remap PRO + teto de convicção no N2 (`llm.py:568-577`), teto sempre-Médio no
   legado (`llm.py:604-605`), validação de `planoEstudo` por modo + default
   `confianca="baixa"` no N1 (`llm.py:871-882`), piso de guardrails do servidor no
   N3 mesmo com prompt editado (`llm.py:1038-1039`, qa/39 P1-4).
3. **Testes guardiões existentes** (rodar após qualquer mudança):
   `server/tests/test_llm_errors.py` (em ~l.58 garante a derivação do FORMAT_PRO:
   enum COMPRAR presente, "Estudar alta" ausente, "PLANO EDUCACIONAL" ausente),
   `test_guardrail_imperativo.py`, `test_llm_prompt_concisao.py`, `test_skill_ref.py`.
   Suíte: `./operar.sh testes` (funciona de qualquer worktree).
4. **Cache de prompt**: o system é montado para ser cacheável
   (`_system_cacheavel`, `llm.py:~315`, mínimos por modelo em `_CACHE_MIN`).
   Mudanças no system invalidam o cache uma vez (ok), mas **não** introduzir
   conteúdo variável por chamada no system (perfil já é exceção deliberada — ver A7).
5. **Não é este documento que decide commit/push** — quem executa decide junto
   com o Alex; há sessões paralelas trabalhando no repo (cuidado com divergência).

---

## 3. Achados (por severidade)

### 🔴 A1 — `_profile_line` manda "ajustar a recomendação ao perfil" (contradição regulatória)

- **Onde:** `llm.py:218` (função `_profile_line`, usada por TODAS as superfícies —
  system e/ou user prompt).
- **Evidência:** `"Perfil do operador (ajuste recomendacao, stop e alvo a ELE): ..."`.
- **Contradiz:**
  - `OPERADOR_PRO` (`llm.py:699-701`): "isto não é aconselhamento personalizado —
    o perfil informado só dimensiona o risco (% por operação), **nunca muda a
    leitura técnica**";
  - `defaults.py:121-122` (carteiraStopAlvoOperador): "O PERFIL do cliente
    dimensiona o risco...; ele NÃO muda a leitura técnica";
  - `skill_ref.DISCLAIMER` ("não representa... recomendação personalizada").
- **Problema:** "ajuste a recomendação ao perfil dele" é a definição literal de
  recomendação personalizada — exatamente o que o produto declara não fazer. O
  modelo recebe as duas ordens e escolhe uma. Risco regulatório + inconsistência.
- **Correção proposta:** trocar o cabeçalho da linha por algo como:
  `"Perfil do operador (dimensione stop, alvo e tamanho de posicao ao perfil; a leitura tecnica e a decisao NAO mudam com o perfil): risco ..., horizonte ..., tolerancia ..., objetivo ..., experiencia ..."`
  Manter os cinco campos (risco/horizonte/toleranciaPerdaPct/objetivo/experiencia).
- **Aceite:** grep sem ocorrência de "ajuste recomendacao" no repo; suíte verde;
  novo teste guardião afirmando que `_profile_line(...)` contém "NAO mudam" (ou
  equivalente) e não contém "ajuste recomendacao".

### 🔴 A2 — Caminho legado exige um "pacote técnico pré-calculado" que ele não envia

- **Onde:** `analyze` (`llm.py:580-607`) + `_build_user_prompt` (`llm.py:244-265`).
- **Evidência:** o system compõe `skill.text`, que contém o Princípio 1
  (`skill_ref.py:29-30`): "use SOMENTE o pacote técnico pré-calculado fornecido.
  Todo número citado vem dele." Mas o user prompt do legado envia **apenas
  candles crus em TSV** (`llm.py:260-262`) — não existe pacote nessa rota.
- **Problema:** a instrução referencia um artefato ausente. Para citar RSI/médias
  o modelo precisa **calcular por conta própria** (violando o princípio) ou se
  recusar. É a superfície com maior risco de número inventado.
- **Correção proposta (escolher uma, com o Alex):**
  - (a) **Aposentar a rota** — verificar chamadores de `analyze()` em `main.py`;
    se o N2 cobre todos os casos, redirecionar e deprecar; ou
  - (b) dar à rota uma variante do princípio: "use APENAS os candles fornecidos;
    indicadores só os que você derivar aritmeticamente deles, mostrando o cálculo
    no corpo; na dúvida, declare a ausência".
- **Aceite:** (a) nenhum endpoint ativo chega a `analyze()` OU (b) o system do
  legado não contém mais a frase "pacote técnico pré-calculado" sem o pacote
  existir; teste guardião cobrindo a variante.

### 🟡 A3 — `CONTRATO_DADOS` só entra no N1; N2 e N3 recebem os mesmos dados com menos rigor

- **Onde:** `skill_ref.CONTRATO_DADOS` (`skill_ref.py:70-81`) é anexado **apenas**
  em `analyze_deep` (`llm.py:834`).
- **Evidência:** o N2 recebe o MESMO pacote com `dataQuality` mas só ganha a
  regra do multi-timeframe (`llm.py:197-198`) e um "Respeite dataQuality"
  genérico (`llm.py:526`). O N3 — que propõe **stop/alvo**, o número mais
  sensível — não recebe nenhuma regra de qualidade de dados (só o que o prompt
  handwritten disser).
- **Problema:** mesmos dados, três níveis de rigor. As regras valiosas
  (defasagem >15min, série <20/<50 candles, volume ausente, **2+ falhas ⇒
  aguardar**) não protegem N2/N3.
- **Correção proposta:** incluir `"\n" + skill_ref.CONTRATO_DADOS` na montagem do
  system do N2 (`llm.py:548` e `llm.py:557`) e do N3 (`llm.py:1040`, dentro da
  camada `voz` do servidor, para valer também sobre prompt editado).
- **Aceite:** teste guardião: system do N2 e do N3 contém "Qualidade dos dados";
  suíte verde; conferir tamanho do system vs. mínimo de cache (`_CACHE_MIN`) —
  só cresce, então cache continua elegível.

### 🟡 A4 — Conclusão canônica obrigatória sem lugar no contrato JSON (modo estudo; e no N3 sem lugar nenhum)

- **Onde:** `GUARDRAILS` (`llm.py:172-173`): "Termine SEMPRE com UMA conclusao de
  estudo, textualmente: ..." (as 4 `CONCLUSOES_EDU` de `skill_ref.py:96-101`).
- **Evidência da assimetria:** no modo operador o endereço existe — FORMAT_PRO
  fecha com "…fechando com a conclusao canonica" no `corpo` (`llm.py:727`) e
  PRO_DEEP_FORMAT põe no `resumo` (`llm.py:736`). No modo **estudo**, FORMAT
  (`llm.py:176-211`) e DEEP_FORMAT (`llm.py:642-664`) **não dizem onde** a
  conclusão cabe — e o FORMAT ainda ordena "Nao escreva absolutamente nada fora
  do objeto JSON" (`llm.py:205-206`). No **N3**, o `voz` do modo estudo anexa o
  GUARDRAILS inteiro (`llm.py:1039`) — inclusive o "Termine SEMPRE…" — mas o
  contrato é um array com `explicacao` de 2-4 frases e "Responda SOMENTE com o
  array JSON" (`llm.py:1040-1042`): a ordem não tem onde ser cumprida.
- **Problema:** instruções em conflito → o modelo decide sozinho (conclusão some,
  ou vai para fora do JSON e arrisca o parse).
- **Correção proposta:**
  1. FORMAT (edu): adicionar linha "O `corpo` FECHA com uma das conclusões de
     estudo canônicas, textualmente."
  2. DEEP_FORMAT (edu): idem para o `resumo` (espelhando o PRO_DEEP_FORMAT).
  3. N3 estudo: ou instruir "a `explicacao` de cada ativo fecha com a conclusão
     de estudo aplicável", ou cortar o "Termine SEMPRE…" da camada anexada ao N3
    (usar um GUARDRAILS sem a exigência de fecho — avaliar extrair
    `GUARDRAILS_BASE` + fecho como peças separadas).
- **Aceite:** teste guardião de simetria: se GUARDRAILS exige fecho canônico,
  o FORMAT do mesmo modo declara o campo onde ele vai; suíte verde.

### 🟡 A5 — N2 exige "CADA metodologia" com corpo de 12 linhas (mesmo squeeze que já quebrou o N1)

- **Onde:** `_build_structured_prompt` item 7 (`llm.py:527`): "Termine o campo
  `corpo` com a secao '## Modelos utilizados' explicando **CADA** metodologia
  aplicada" × FORMAT (`llm.py:209-210`): "`corpo` em ate 12 linhas".
- **Histórico:** essa aritmética já estourou no N1 — 100% dos estudos caíam no
  `_deep_fallback` por truncamento (comentário em `llm.py:854-857`) até o corte
  para "ATÉ 4 modelos MAIS RELEVANTES" (`llm.py:657-658`). O N2 não recebeu o
  mesmo remédio.
- **Correção proposta:** no item 7, trocar "CADA metodologia aplicada" por
  "os ATÉ 4 modelos MAIS RELEVANTES para esta leitura (priorize os que sustentam
  a tese)" — mesma redação do DEEP_FORMAT para consistência.
- **Aceite:** medir com o masstest LLM (`scripts/masstest-agentes-llm.py`, BYOK)
  antes/depois: taxa de truncamento/fallback do N2 não piora e o corpo respeita
  o limite com mais frequência.

### 🟡 A6 — Três escalas de confiança convivendo (e "alta" impossível no N1 por enum)

- **Onde/evidência:**
  - N2/legado: `conviccao` = "Muito Alto|Alto|Médio|Baixo" (`llm.py:183`);
  - N1: `confianca` = **"baixa|moderada"** apenas (`llm.py:653` e `llm.py:742`) —
    "alta" é impossível **mesmo com `multiTimeframe=true`**, e o código valida
    só esses dois valores (`llm.py:879-882`);
  - Referência canônica: PROCESSO §9 (`skill_ref.py:63-64`) define exatamente
    quando "alta" é legítima (confluência + multi-timeframe); CONTRATO_DADOS
    fala em teto "moderada" apenas **sem** 2º timeframe.
- **Problema:** ou o teto permanente do N1 é decisão de produto (conservadorismo
  no aprofundamento) — e então está **não documentada** e contradiz o processo
  canônico incluído no mesmo prompt — ou o enum está comendo um nível que os
  dados multi-timeframe permitiriam.
- **Correção proposta:** decisão do Alex. (a) Se teto intencional: adicionar uma
  linha no DEEP_FORMAT/PRO_DEEP_FORMAT ("por desenho, o N1 nunca declara
  confiança 'alta'") e comentário no código. (b) Se não: incluir `"alta"` no enum
  dos dois formatos + na validação (`llm.py:882`), gated por
  `dataQuality.multiTimeframe` (enforcement em código, como o N2 faz).
- **Aceite:** decisão registrada em comentário no código; se (b), teste de que
  `confianca="alta"` só sobrevive com `multiTimeframe=true`.

### 🟢 A7 — Redundâncias na composição (custo de tokens + risco de divergência)

- **Persona 2× no N2:** o `skill.text` default já traz `PERSONA_BASE`+`PRINCIPIOS`
  (`defaults.py:23-27`), e `analyze_structured` re-declara persona em outras
  palavras — `super_operator` (`llm.py:550-556`) no edu, `mesa` (`llm.py:540-547`)
  no operador. Duas personas em vozes ligeiramente diferentes no mesmo system.
- **Perfil 2×:** no system (`llm.py:548/557/590/592`) **e** no user prompt
  (`_build_structured_prompt` `llm.py:506-508`; `_build_user_prompt`
  `llm.py:246-248`). Obs.: perfil no system também **fragmenta o cache** entre
  usuários com perfis diferentes — mover o perfil SÓ para o user prompt melhora
  o hit rate de cache além de deduplicar.
- **Contrato de saída 2×:** `_CONTRATO_SAIDA` no skill.text (`defaults.py:10-16`)
  + FORMAT completo no system.
- **"Nunca prometa lucro" 3-4×** na composição final (PRINCIPIOS #2, GUARDRAILS,
  prompts N3).
- **Correção proposta:** (i) mover `_profile_line` só para o user prompt em todas
  as superfícies; (ii) reduzir `super_operator`/`mesa` a APENAS o que
  PERSONA_BASE não cobre (a função/tom), 2-3 linhas; (iii) avaliar remover
  `_CONTRATO_SAIDA` do skill default (o FORMAT já cobre — mas cuidado: skill é
  editável pelo usuário; o _CONTRATO_SAIDA protege quando o usuário troca o
  texto. Se mantiver, documentar que é redundância deliberada).
- **Aceite:** suíte verde; smoke manual de uma análise N2 nos dois modos;
  nenhum enum/chave mudou.

### 🟢 A8 — N3 não compõe da fonte canônica; R:R 1,5 vive como literal em 4 lugares

- **Onde:** `default_llm_prompts()` (`defaults.py:62-151`) — os dois prompts de
  carteira são **reescritos à mão**, apesar de o cabeçalho do módulo prometer
  composição do canônico. O R:R mínimo aparece como literal em:
  `skill_ref.py:34` (PRINCIPIOS #5), `defaults.py:89` (carteiraStopAlvo),
  `defaults.py:126` (carteiraStopAlvoOperador), `llm.py:1027` (cenarios_ext).
- **Problema:** é a mesma classe de drift ("tríplice divergência") que o
  skill_ref nasceu para eliminar. Se o produto um dia mudar o R:R mínimo, três
  lugares esquecem.
- **Correção proposta:** (i) extrair `RR_MIN = 1.5` (e `RR_IDEAL = 2.0`) para
  `skill_ref.py` e interpolar nos 4 pontos; (ii) recompor os blocos invioláveis
  dos prompts de carteira a partir de `skill_ref` (PRINCIPIOS resumidos +
  DISCLAIMER), mantendo o formato de saída intacto (o popup parseia o array).
  **Atenção:** prompts de carteira são persistidos por usuário
  (`llmPrompts` no estado) — usuários existentes mantêm o texto antigo; a
  recomposição vale para defaults novos. Não migrar estado sem decisão do Alex.
- **Aceite:** `grep -rn "1,5" server/app/` mostra o valor vindo de constante nos
  prompts default; teste em `test_skill_ref.py` para as novas constantes.

### 🟢 A9 — Custo: todos os candles da janela viajam em toda chamada

- **Onde:** `_build_structured_prompt` (`llm.py:518`, JSON completo do contexto,
  candles inclusos), `analyze_deep` (`llm.py:847`), `_build_user_prompt`
  (`llm.py:261-262`, TSV) — janela default 1y ≈ 250 candles; 2y ≈ 500.
- **Problema:** maior driver de input tokens; o cache não ajuda (user prompt
  varia por ticker/hora). Pelo Princípio 1, todo número citado vem do PACOTE —
  os candles servem de validação, não de fonte.
- **Correção proposta:** **medir antes de mudar.** Rodar o masstest LLM com
  variante enviando só os últimos ~90 candles no N2 (pacote técnico continua
  calculado sobre a janela completa) e comparar qualidade (taxa de fallback,
  coerência com setupsRadar) e custo. Só adotar se a qualidade não regredir.
- **Aceite:** números do masstest antes/depois documentados; decisão registrada.

### Menores (registrar ao passar)

- **M1 — FORMAT_PRO com dois limites de linhas:** o `.replace()` não remove o
  "SEJA CONCISO: `corpo` em ate 12 linhas" herdado do FORMAT (`llm.py:209-210`)
  e o sufixo acrescenta "corpo em ate 10 linhas" (`llm.py:727`) — o FORMAT_PRO
  final pede 12 E 10. Corrigir com um terceiro `.replace()` do bloco de concisão
  (e o guardião de `test_llm_errors.py` ganha um assert de que "12 linhas" não
  aparece no FORMAT_PRO).
- **M2 — "Reduzir risco" assimétrico:** existe no enum do N2 (`llm.py:185` e
  FORMAT_PRO) e no vocab como extensão (`skill_ref.py:170/176`), mas não no
  `planoEstudo` do N1 (`llm.py:654/743`) nem na validação (`llm.py:871-878`).
  Decidir: ou entra no N1 (UI já estiliza) ou documentar por que N1 não reduz.
- **M3 — `stopSugerido: 0.0` sem regra de null:** o exemplo do FORMAT
  (`llm.py:192-193`) mostra `0.0` e não diz o que mandar quando não há plano
  (o N3 diz explicitamente `null` — `defaults.py:108-109`). Adicionar ao FORMAT:
  "sem referência técnica, use null (nunca 0.0)". Conferir o que `kpi.py` faz
  com 0.0 hoje antes de mudar.
- **M4 — user prompt do N3 com voz de estudo no modo operador:** `analyze_carteira`
  reusa `_build_user_prompt`, que fecha com "produza a leitura tecnica
  **educacional** de {ticker} no JSON exigido" (`llm.py:264`) mesmo na mesa —
  e pede "o JSON exigido" (singular) quando o N3 espera um ARRAY. Parametrizar a
  frase final por modo/superfície.
- **M5 — Coerência decisão ↔ conclusão canônica não é exigida:** nada impede
  `recomendacao="COMPRAR"` fechando com "Os sinais são conflitantes...". Uma
  linha no FORMAT/_PRO ("a conclusão canônica deve ser COERENTE com a
  recomendação") custa pouco; enforcement em código é possível (mapear conclusão
  → conjunto de decisões compatíveis) mas avaliar custo/benefício.
- **M6 — Acentuação mista:** GUARDRAILS/FORMAT em ASCII ("invioláveis" sem
  acento etc.) × skill_ref acentuado. Cosmético; não prioritário (mudar strings
  invalida cache e testes de igualdade textual à toa — fazer só se encostar nos
  blocos por outro motivo).

---

## 4. Ordem de ataque sugerida

| # | Item | Esforço | Risco se não fizer |
|---|---|---|---|
| 1 | **A1** perfil "ajusta recomendação" | 1 linha + teste | Regulatório |
| 2 | **A2** rota legada sem pacote | Decisão + pequena | Números inventados |
| 3 | **A4** endereço da conclusão canônica (edu + N3) | 3 linhas | Parse quebrado / conclusão sumida |
| 4 | **A3** CONTRATO_DADOS no N2 e N3 | 2 linhas | Stop/alvo sobre dado ruim |
| 5 | **A5** top-4 modelos no N2 | 1 linha + masstest | Truncamento (repete o bug do N1) |
| 6 | **M1** 12×10 linhas no FORMAT_PRO | 1 replace + assert | Instrução ambígua |
| 7 | **A6** escala de confiança | Decisão do Alex | Inconsistência declarada |
| 8 | **A7** dedup persona/perfil/contrato | Médio | Custo + drift de tom |
| 9 | **A8** N3 compor do canônico + RR_MIN | Médio | Drift futuro |
| 10 | **A9** janela de candles | Medir primeiro | Custo por chamada |
| — | M2-M6 | Ao passar | Baixo |

## 5. Validação (obrigatória após cada lote)

```bash
./operar.sh testes
```

- Guardiões relevantes: `test_llm_errors.py` (FORMAT_PRO), `test_guardrail_imperativo.py`,
  `test_llm_prompt_concisao.py`, `test_skill_ref.py`. Ampliar guardiões conforme
  os aceites acima (cada correção de prompt ganha seu assert).
- Para A5/A9 (mudanças com efeito na QUALIDADE da resposta): medir com
  `scripts/masstest-agentes.py` (determinístico, grátis) e
  `scripts/masstest-agentes-llm.py` (LLM real, BYOK) antes/depois.
- Smoke manual: uma análise N2 + um "Aprofundar" N1 + um stop/alvo N3, nos dois
  modos (estudo/operador), conferindo enum na UI e fecho canônico.

## 6. O que está SÓLIDO e deve ser preservado (não "consertar")

- Fonte única `skill_ref` com composição (não cópia) — estender, nunca contornar.
- Enforcement pós-resposta em código para enum/teto/defaults (padrão do projeto).
- Contrato de dados honesto ("declare a lacuna, não compense com inferência").
- Piso de guardrails do servidor no N3 mesmo sobre prompt editado (qa/39 P1-4).
- Cache condicional por modelo (`_system_cacheavel`/`_CACHE_MIN`) e parâmetros
  por catálogo (`_params_efetivos` — temperature omitida em modelos que
  raciocinam; LLM_TEMPERATURE=0.2).
- FORMAT_PRO derivado por `.replace()` é frágil **mas guardado por teste**
  (`test_llm_errors.py:~58`) — pode manter, só somar o assert do M1.
