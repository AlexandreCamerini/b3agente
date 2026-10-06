---
phase: 49-anatomia-da-perna
reviewed: 2026-10-06T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - server/app/anatomia_perna.py
  - server/app/main.py
  - server/app/skill_ref.py
  - web/src/api.js
  - web/src/persistence.js
  - web/src/copy.js
  - web/src/opcoes/AnatomiaPerna.jsx
  - web/src/opcoes/GraficoAnatomia.jsx
  - web/src/opcoes/PosicaoTotal.jsx
  - web/src/opcoes/PernasAbertas.jsx
  - web/src/opcoes/ObjetivoAtivo.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/useAnatomia.js
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 49: Code Review Report

**Reviewed:** 2026-10-06
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

O motor `anatomia_perna.py` é puro, delega o payoff a `opcoes_payoff` e trata dado ausente como None. A paridade de chaves `anat_*` entre `skill_ref.py` e `copy.js` fecha (64 chaves, mesmo conjunto; todas as chaves usadas nos componentes existem nos dois lados). A rota isola por escopo, valida `excluir` por allowlist e limita a 20 itens. Os problemas reais estão na camada de estado do front (resposta velha exibida como atual), na afirmação "custo MCP zero" e no veto do Encerrar.

## Critical Issues

### CR-01: Falha na releitura mantém a anatomia antiga na tela, com chips dessincronizados do gráfico

**File:** `web/src/opcoes/useAnatomia.js:40` e `web/src/opcoes/PernasAbertas.jsx:164,214`
**Issue:** No `catch`, o hook preserva `dados: a.dados` e só seta `erro`. Em `PernasAbertas`, `comAnatomia` depende só de `dados.estado === "ok" && dados.anatomia`. Quando já havia dados, o ramo de anatomia renderiza e `lido.erro` nunca é consultado (só o ramo de fallback usa `falhou`).
Cenário: o usuário desliga o chip da PUT (`alternar` altera `excluidas` na hora), a releitura estoura timeout (30 s) ou volta 400/502, e o `PosicaoTotal` continua mostrando `total.pontos`, a leitura "com/sem" e a tabela do total com a perna ainda somada. O chip aparece desligado e o número é de outra hipótese. Não há mensagem de erro nem botão de nova tentativa. Pelo princípio 5 e pela regra de dado inválido, isso é número exibido que não corresponde ao estado mostrado.
**Fix:**
```jsx
// PernasAbertas.jsx
const comAnatomia = !!(dados && dados.estado === "ok" && dados.anatomia);
const releituraFalhou = comAnatomia && !!lido.erro && !anatomiaInjetada;
// no ramo comAnatomia, antes de <PosicaoTotal>: se releituraFalhou, renderizar a frase
// tx("anat_erro") + botão tx("tentar_de_novo") -> lido.recarregar(), e NÃO renderizar
// o total (ou passar recalculando/obsoleto para o PosicaoTotal esconder pontos/leitura).
```
Alternativa no hook: zerar `dados` quando a falha vem de uma releitura com `excluir` diferente da última resposta bem-sucedida.

## Warnings

### WR-01: `custoMcp: 0` é fixo, mas a cadeia pode vir do provedor pago (mydata)

**File:** `server/app/main.py:4048` (`custoMcp: 0`), `:3179` (`options_provider.get_options`), `server/app/options_provider.py:36-40`
**Issue:** A rota diz "custo MCP ZERO", mas `_estrutura_do_ativo` chama `options_provider.get_options(t, venc)` uma vez por vencimento. Esse seletor despacha por `B3_OPTIONS_PROVIDER`, e `mydata` é provedor válido (gate de orçamento dentro do adaptador). Com `mydata` ativo, cada abertura da tela e cada toggle de chip (nova leitura) consome orçamento pago, e o `0` informado ao cliente é falso. A rota também não tem cap por usuário. Se a produção roda em `yahoo`, o risco é latente, mas o invariante não está garantido pelo código.
**Fix:** Forçar leitura só de cache/provedor grátis na anatomia (por exemplo, um parâmetro `somente_gratis` que recusa `mydata`). Alternativamente, derivar `custoMcp` do provedor efetivo (`0 if provider_name() != "mydata" else None`) e cobrir com teste que fixa `B3_OPTIONS_PROVIDER=mydata` e verifica que a rota não chama o provedor.

### WR-02: Veto do Encerrar por "prêmio indisponível" depende de frescor/cotação

**File:** `web/src/opcoes/AnatomiaPerna.jsx:77,158-166` (consome `server/app/estrutura_posicao.py:268-272, 440-447`)
**Issue:** `encerrar.permitido === false` também ocorre quando `premioAtual is None or not lastOk`, isto é, sem cotação ou com último negócio inválido. Nesse caso o botão vira `aria-disabled` justamente quando a cadeia falha ou a perna é ilíquida, e o usuário não consegue sair da posição. Isso contradiz o invariante "Encerrar nunca desabilitado por frescor/liquidez". Há ainda assimetria: se `_estrutura_do_ativo` falha por inteiro (devolve `None`), `enc` é `None`, `vetado` fica false e o Encerrar fica habilitado. A mesma perna é vetada com cadeia parcial e liberada com cadeia totalmente fora.
**Fix:** Limitar o veto da UI aos motivos estruturais (`vencida`, `dados_invalidos`) e deixar `premio_indisponivel` sem desabilitar. O texto de confirmação já tem a variante `anat_confirmar_sem_cotacao`. Se o `store.sell_option` realmente exige prêmio, o veto deve vir da regra do store, com mensagem própria, e não de leitura de cotação.
```jsx
const vetado = !!(perna.encerrar && perna.encerrar.permitido === false
  && perna.encerrar.motivo !== "premio_indisponivel");
```

### WR-03: `excluir` obsoleto vira HTTP 400 e derruba toda a anatomia

**File:** `server/app/main.py:4046-4047`, `web/src/opcoes/PernasAbertas.jsx:41-45,136`
**Issue:** O filtro `excluirParaRota` usa os ids de `optionPositions` do cliente. Se o cliente estiver defasado em relação ao escopo do servidor (outro aparelho encerrou a perna; deviceStore antes de sincronizar), a rota devolve 400 "Perna inválida". O hook trata como erro, e o usuário perde a anatomia inteira (cai no fallback 48-16) por causa de um chip. A rota deveria descartar ids desconhecidos (e já devolve `excluidas` filtrado em `ler_anatomia`) em vez de falhar. Isso também fere "erro vira 200 com estado".
**Fix:** Na rota, manter a validação de formato e do limite (tamanho e regex de cada id) e filtrar com `lista = [x for x in lista if x in permitidos]`, devolvendo `excluidas` já saneado. Só 400 para lista grande ou id fora do formato.

### WR-04: Total mistura perna sem data de vencimento em total de "um só vencimento"

**File:** `server/app/anatomia_perna.py:324-333`
**Issue:** `vencs` ignora pernas com `_venc is None`. Com uma perna datada e outra sem data (`expiration` ausente ou inválida), `len(vencs) == 1` e o total soma as duas como se vencessem juntas. O título "Resultado no vencimento (dd/mm)" fica enganoso e o número pode estar errado. Essa perna nunca é cotada nem tem prazo (`anat_prazo_sem_data`), então o motor sabe que o dado está incompleto.
**Fix:** Tratar `None` como vencimento distinto: `vencs = {p["_venc"] for p in incl}` e, se houver `None` junto com data (ou mais de um valor), cair no ramo `anat_total_vencimentos_diferentes` ou num motivo próprio "sem data".

### WR-05: Linha do total perde a identidade quando uma perna está selecionada

**File:** `web/src/opcoes/PosicaoTotal.jsx:92` e `web/src/opcoes/GraficoAnatomia.jsx:115-120`
**Issue:** `total = s.destaque && s.traco === undefined`. Com `selecionada`, a série "total" entra com `destaque: !selecionada = false`, então `total` vira false. Ela é desenhada com `T.accent`, tracejado vazio (sólido), largura 2. A perna de índice 0 (`traco: 0`, sólida, accent) fica igual a ela, só mais grossa (3.5) quando selecionada. Duas linhas indistinguíveis por cor e por traço, com diferença só na espessura. Isso fere "não depender só de cor" e confunde o "com/sem esta perna".
**Fix:** Marcar o total por propriedade explícita (`tipo: "total"`) em vez de inferir de `destaque`/`traco`, e manter sempre traço e cor próprios (por exemplo `T.textPrimary` sólido), mudando só a opacidade quando houver perna selecionada.

## Info

### IN-01: Valores `inf`/`nan` passam por `_num` e `_n`

**File:** `server/app/anatomia_perna.py:41-46,179-180`
**Issue:** `_num` aceita `inf` (`v == v and v > 0`). `strike` infinito derruba `_grade` (`math.floor(inf)` levanta `OverflowError`) fora do `try` por perna, e a rota devolve `estado: "erro"` para o ativo inteiro. `_n` em `_hoje` repassa `nan`/`inf` do payload da estrutura, e o JSON sai inválido (`NaN`). Improvável, mas as posições são gravadas pelo cliente.
**Fix:** Usar `math.isfinite(v)` em `_num`, `_num_nn` e `_n`.

### IN-02: Reinício do ticker dispara releitura desnecessária com "ACOES"

**File:** `web/src/opcoes/PernasAbertas.jsx:41-45,141-143`
**Issue:** `excluirParaRota` mantém "ACOES" para qualquer ticker. Ao trocar de ativo, a primeira leitura sai com `excluir=ACOES` (estado do ativo anterior) e logo depois o efeito zera `excluidas` e dispara outra. O contador do hook descarta a resposta velha, então não há corrida, só uma chamada à cadeia a mais (ver WR-01).
**Fix:** Derivar `excluidas` por ticker (`useState` chaveado) ou resetar em render, em vez de `useEffect` após o render.

### IN-03: Aria do pior caso pode sair "−R$ 0,00"

**File:** `server/app/anatomia_perna.py:294`
**Issue:** O prefixo `"−R$ "` é fixo. Com prêmio de entrada 0 (`_num_nn` permite), `perda_maxima` é 0 e o texto lido por leitor de tela fica "−R$ 0,00". Dado real, mas com sinal de perda indevido.
**Fix:** Omitir o sinal quando `piorCaso == 0`.

---

_Reviewed: 2026-10-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Resolução

Aplicada em 2026-10-06 (gsd-code-fixer). Um commit por achado, exceto CR-01 + IN-02 (mesmo bloco de estado).

| Achado | Status | Commit | Nota |
|--------|--------|--------|------|
| CR-01 | fixed: requires human verification | 795b6864 | `releituraFalhou` no ramo da anatomia: alerta `anat_erro` + "Tentar de novo"; `PosicaoTotal obsoleto` oculta gráfico/slider/tabela e mostra `anat_desatualizado` (chave nova, paridade skill_ref↔copy.js) |
| WR-01 | no_change_needed (docstring) | cc6a32d1 | `yahoo` e `mydata` cacheiam por (ticker, vencimento) 300 s e consultam o cache antes do gate (`options_provider_yahoo.py:93`, `options_provider_mydata.py:270`); toggle de chip dentro do TTL não toca a fonte. Só a 1ª leitura após o TTL passa pelo gate do adaptador |
| WR-02 | fixed: requires human verification | 9d70cac1 | `premio_indisponivel` vira aviso com botão habilitado (anatomia e fallback 48-16); `vencida`/`dados_invalidos` seguem vetando. Motor intocado. A rota `/api/options/sell` já recusa sem prêmio (502 com mensagem). Fixtures de veto antigos preservados |
| WR-03 | fixed | 9e77e489 | id de formato válido e desconhecido é filtrado (200); 400 só para formato inválido ou >20 itens |
| WR-04 | fixed | 3b563901 | perna sem data junto de outra perna: total sem número + `anat_total_sem_data` (chave nova) |
| WR-05 | fixed | b8fe3828 | série marcada por `tipo: "total"`; cor de texto, peso 3 e halo de fundo; opacidade reduzida quando há seleção |
| IN-01 | fixed | c60a637d | `math.isfinite` em `_num`, `_num_nn`, `_hoje._n` |
| IN-02 | fixed | 795b6864 | reset de escolhas no render (estado chaveado por ticker), sem `useEffect` |
| IN-03 | fixed | 0f38809c | sem sinal "−" quando o pior caso é 0 |

Verificação: pytest (anatomia, rota, estrutura, skill_ref, mcp_guardioes) 182 passed; `web/tests/test_opcoes_*.mjs` e correlatos verdes; `npx vite build` ok.
