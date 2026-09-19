# Phase 33: Extração dos 5 jobs em componentes próprios - Pattern Map

**Mapped:** 2026-09-19
**Files analyzed:** 11 (5 novos componentes + `OpcoesScreen.jsx` + 5 guardiões)
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/opcoes/SecaoVigias.jsx` (novo) | component | request-response (props-in, callback-out) | `web/src/opcoes/OportunidadesOpcoes.jsx` | exact (mesmo padrão de extração Fase 32, mesmo "nunca desaparece" NAV-03) |
| `web/src/opcoes/SecaoDescobrir.jsx` (novo) | component | request-response, cross-source aggregation | `web/src/opcoes/OportunidadesOpcoes.jsx` + `web/src/opcoes/CuradoriaEstruturas.jsx` (compor os dois, não reescrever) | exact (é literalmente mover `fraseDuasLeituras`+`blocoOportunidades`+`blocoCuradoria` para dentro) |
| `web/src/opcoes/SecaoSetups.jsx` (novo) | component | CRUD (listar/criar/desativar setup) | `web/src/opcoes/CriarSetup.jsx` (já é módulo próprio) + trecho "SETUPS GRAVADOS" hoje inline em `OpcoesScreen.jsx:1224-1352` | role-match (CriarSetup é só a metade "criar"; a listagem precisa de extração nova a partir do inline) |
| `web/src/opcoes/SecaoComparar.jsx` (novo) | component | request-response (form → possibilidades) | trecho "COMPARAR OS VENCIMENTOS" hoje inline em `OpcoesScreen.jsx:1133-1220` | partial (sem módulo irmão já extraído; usar `CuradoriaEstruturas.jsx` como referência de como um bloco vira componente com cascata própria) |
| `web/src/opcoes/SecaoAnalisar.jsx` (novo) | component | request-response, com fold-in D-04a (props em vez de fetch local) | `SubAbaOperar` (função interna de `OpcoesScreen.jsx:1406-1558`) | exact (SubAbaOperar já resolve exatamente esse padrão: recebe dado pronto por prop, delega o card, nunca chama `store.*` direto — ver D-04a) |
| `web/src/opcoes/OpcoesScreen.jsx` (modificado) | orchestrator/screen (não se enquadra bem em "controller" — é o componente-pai que só chama hooks e distribui props) | request-response | (o próprio arquivo, versão anterior à extração) | n/a — é o arquivo que perde JSX, não que ganha analog externo |
| `web/tests/test_opcoes_subabas_ui.mjs` (modificado) | test (guardian) | static-analysis / file-scan | `web/tests/test_opcoes_subabas_ui.mjs:100-116` (o próprio arquivo — trecho já por diretório) | exact — é o PRECEDENTE citado no CONTEXT.md, não um analog externo |
| `web/tests/test_opcoes_consolidacao_ui.mjs` (modificado) | test (guardian) | static-analysis / cross-file indexOf | `test_opcoes_subabas_ui.mjs:100-116` (varredura por diretório) + `test_opcoes_analisar_ui.mjs:534-537` (segundo precedente de varredura por diretório) | role-match — precisa migrar de `indexOf` em UM arquivo para varredura de diretório/JSX-tag |
| `web/tests/test_opcoes_analisar_ui.mjs` (modificado) | test (guardian) | static-analysis / indexOf de ordem | mesmo arquivo, linhas 534-537 (padrão de varredura já presente NO PRÓPRIO arquivo, para outra regra) | exact — o arquivo já convive com os dois estilos (indexOf fixo E varredura de diretório); só extrapolar o segundo estilo para a regra de ordem 141-146 |
| `web/tests/test_opcoes_vigias_ui.mjs` (modificado) | test (guardian) | static-analysis / indexOf | `test_opcoes_subabas_ui.mjs:100-116` | role-match |
| `web/tests/test_opcoes_mcp_aba_ui.mjs` (modificado) | test (guardian) | static-analysis / indexOf | `test_opcoes_subabas_ui.mjs:100-116` | role-match |

Nota: este é um refactor de UI dentro de um domínio React sem roteador — não há
"controller/service/model" no sentido clássico. O mapeamento de papel real é
**componente-filho recebendo dados prontos por prop** (todos os 5 novos) vs.
**componente-pai que só orquestra hooks e distribui props** (`OpcoesScreen.jsx`
depois da extração) vs. **guardião de teste que lê texto-fonte** (os 5 `.mjs`).

## Pattern Assignments

### `web/src/opcoes/SecaoVigias.jsx` (component, request-response)

**Analog:** `web/src/opcoes/OportunidadesOpcoes.jsx` (padrão de extração Fase 32, 32-02) + bloco fonte real em `OpcoesScreen.jsx:587-640` (`blocoVigias`)

**Header de proveniência a replicar** (mesmo tom de `OportunidadesOpcoes.jsx:1-22`):
```javascript
/**
 * SecaoVigias.jsx — Fase 33 (33-0X), extração de OpcoesScreen.jsx.
 *
 * Job 2 do PROJECT.md ("gerenciar vigias") — hoje inline em OpcoesScreen.jsx
 * (`blocoVigias`, `CartaoDeVigia`). Comportamento idêntico, zero funcionalidade
 * nova (D-03 do 33-CONTEXT.md). Recebe TUDO por prop; não chama
 * `useOpcoesMcp`/`store.*` diretamente — só o orquestrador (OpcoesScreen)
 * chama o hook (padrão Emenda 3 do ADR-027, já replicado por
 * OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx na Fase 32).
 */
```

**Props a receber** (do mapa de integração, ARCHITECTURE.md linha 169 — não inventar novas):
`vigias`, `vigiasVivos`, `atualizarVigias`, `carteira` (para `tickersEmCarteira`), `ticker` (para `selecionado`), `onIr` (=`irParaVigia`), `cp`.

**Core pattern a mover verbatim** (`OpcoesScreen.jsx:587-640`, `CartaoDeVigia` em `OpcoesScreen.jsx:1805-1871`):
```javascript
{vigias.carregando ? (
  <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
) : vigias.erro ? (
  <ErroDoMcp erro={vigias.erro} cp={cp} />
) : listaDeVigias.length === 0 ? (
  <Aviso>{cp.opcoesVigiasVazio || "Nenhum vigia gravado nesta conta ainda."}</Aviso>
) : (
  <div style={{ display: "grid", gap: "10px" }}>
    {listaDeVigias.map((v, i) => (
      <CartaoDeVigia key={...} vigia={v} temEstado={temEstadoDosVigias}
        selecionado={!!(v && v.ticker) && v.ticker === ticker}
        naCarteira={!!(v && v.ticker) && tickersEmCarteira.includes(v.ticker)}
        onIr={irParaVigia} cp={cp} />
    ))}
  </div>
)}
```
`Aviso`, `ErroDoMcp`, `Kicker`, `CartaoDeVigia`, `BOTAO`/`CUSTO_NO_BOTAO`/`desabilitado`/`CUSTO_DA_ACAO` são helpers hoje privados a `OpcoesScreen.jsx` (linhas 95-300 aprox., `CartaoDeVigia` em 1805-1871). Decisão de extração (Claude's Discretion, CONTEXT.md): mover `CartaoDeVigia` junto para dentro de `SecaoVigias.jsx` (uso exclusivo dele) ou deixar como export nomeado de um módulo de helpers compartilhado — mas NUNCA duplicar a função em dois arquivos.

**Erro/estado a preservar:** cascata carregando→erro→vazio→dados idêntica (ver Pitfall 5 do PITFALLS.md — vigias é estado global-ish, sempre visível independente de ticker, não pode virar "escondido atrás de clique").

---

### `web/src/opcoes/SecaoDescobrir.jsx` (component, cross-source aggregation)

**Analog:** `web/src/opcoes/OportunidadesOpcoes.jsx` (Bloco A) + `web/src/opcoes/CuradoriaEstruturas.jsx` (Bloco B) — este componente novo é um WRAPPER fino que compõe os dois, não reimplementa nenhum.

**Fonte real a mover** (`OpcoesScreen.jsx:705-753`, `fraseDuasLeituras`+`blocoOportunidades`+`blocoCuradoria`):
```javascript
const fraseDuasLeituras = (
  <p style={{ fontSize: "12px", color: T.textMuted, lineHeight: 1.5, margin: "10px 0 14px" }}>
    {cp.duasLeiturasIntro}
  </p>
);
const blocoOportunidades = (
  <OportunidadesOpcoes propostas={opcoesPorTicker} carregando={opcoesPorTickerCarregando}
    positions={carteira} cp={cp} onAbrir={irParaOperar} />
);
const blocoCuradoria = (
  <CuradoriaEstruturas top={...} meta={...} carregando={...} erro={...} concluido={...}
    narrativa={...} narrando={...} erroNarrativa={...} onNarrar={...} onRecarregar={...}
    cp={cp} onAbrir={irParaOperar} onExecutar={...} operador={...} palette={palette} />
);
```

**CRÍTICO — Pitfall 2 do PITFALLS.md (frase-ponte D-05):** `fraseDuasLeituras` DEVE migrar para dentro de `SecaoDescobrir.jsx` JUNTO com `blocoCuradoria`, imediatamente acima dele, sem toggle/colapso novo — é mitigação regulatória amarrada à adjacência física, não copy reposicionável. Não separar Bloco A e Bloco B em componentes/seções diferentes sem decisão explícita registrada (a fase já decidiu: os dois entram juntos em `SecaoDescobrir`, D-03 passo 2).

**Fold-in D-04b (carimbo de frescor, exceção a REORG-02):** ao construir este componente, adicionar o carimbo de frescor nos Blocos A/B — pesquisar primeiro se o dado já existe na resposta de `OportunidadesOpcoes`/`CuradoriaEstruturas` (o bloco "LEITURA DO ATIVO" já expõe frescor — ver `escolherFrescor`/`OpcoesScreen.jsx:409-432` como fonte de vocabulário/padrão a reusar via `copy.js`, não inventar rótulo novo).

**Props a receber:** `opcoesPorTicker`, `opcoesPorTickerCarregando`, `ctx.curadoria` (ou os campos individuais dele), `carteira`, `onAbrir` (=`irParaOperar`), `cp`, `palette`, `operador`. NÃO instanciar `useCuradoria`/`useOpcoesPropostas` própria (ARCHITECTURE.md, tabela "Integration Points" linha 168).

**Guardrail CVM (Pitfall 4):** este é o candidato MAIS provável a precisar de cobertura nova do guardrail de manchete — ele renderiza candidatos via `OportunidadesOpcoes`/`CuradoriaEstruturas`, que já leem `pr.manchete`/`cand.manchete` verbatim. Se a extensão do guardião (ver seção guardiões abaixo) varrer por diretório, este arquivo entra automaticamente.

---

### `web/src/opcoes/SecaoSetups.jsx` (component, CRUD)

**Analog primário:** `web/src/opcoes/CriarSetup.jsx` (já é módulo próprio, D-01 do CONTEXT — não renomear, só envolver) — ler a assinatura de props dele como referência de "componente sem fonte de dado própria" (comentário em `OpcoesScreen.jsx:1362-1366`: "`CriarSetup` é deliberadamente um componente sem fonte de dado própria").

**Trecho fonte a extrair** (listagem "SETUPS GRAVADOS", hoje inline, `OpcoesScreen.jsx:1224-1376`):
```javascript
<Kicker>{cp.opcoesSetupsTitulo || "SETUPS GRAVADOS"}</Kicker>
{naoAvaliado ? <Aviso>{...}</Aviso> : null}
{setups.length === 0 ? (
  <Aviso>{cp.opcoesSemSetups || "Nenhum setup gravado para este ativo."}</Aviso>
) : (
  <div style={{ display: "grid", gap: "10px" }}>
    {setups.map((s) => { /* card com avaliacao, conditions, backtest, botão de gráfico, BotaoDesativar */ })}
  </div>
)}
{podeCriarSetup ? (
  <>
    <Kicker>{cp.opcoesCriarTitulo || "CRIAR UM SETUP"}</Kicker>
    <CriarSetup ticker={ticker} estado={setupNovo} onCompilar={compilarSetup}
      onConfirmar={confirmarSetup} custos={CUSTO_DA_ACAO} cp={cp} />
  </>
) : null}
```

**Props a receber** (ARCHITECTURE.md linha 172): `ticker`, `leitura` (para `l.setups`/`l.setupsNaoAvaliados` — OU já desestruturado como `setups`/`naoAvaliado` pelo orquestrador, à discrição de quem planeja), `grafico`/`abrirGrafico`/`fecharGrafico`, `setupNovo`/`compilarSetup`/`confirmarSetup`/`desativarSetup`, `podeCriarSetup`.

**Erro/degradado a preservar:** `naoAvaliado` NÃO é erro — é estado "sem avaliação hoje" com semântica própria (comentário `OpcoesScreen.jsx:1264-1266`: "Sem avaliação NÃO vira 'não armado'"). Não fundir com a cascata de erro do fetch principal.

**Fetch pago compartilhado (Achado crítico da ARCHITECTURE.md):** `setups`/`setupsNaoAvaliados` vêm do MESMO `leitura.dados` caro que jobs 3 e 4 usam. Nesta Fase (extração, não redesenho de navegação), os 3 componentes continuam recebendo o resultado já pronto e decidindo internamente o que mostrar — não resolver a bifurcação de UX aqui (Build Order Fase A da ARCHITECTURE.md).

---

### `web/src/opcoes/SecaoComparar.jsx` (component, request-response)

**Analog:** sem módulo irmão já extraído — usar `web/src/opcoes/CuradoriaEstruturas.jsx` como referência de "bloco com cascata carregando→erro→vazio→dados dentro de componente próprio, alimentado por prop" e o próprio trecho fonte como base literal.

**Trecho fonte a extrair** ("COMPARAR OS VENCIMENTOS", `OpcoesScreen.jsx:1133-1220`):
```javascript
<Kicker>{cp.opcoesPossibilidadesTitulo || "COMPARAR OS VENCIMENTOS"}</Kicker>
<div style={CAIXA}>
  {N === 0 ? (
    <Aviso>{cp.opcoesSemVencimento || "..."}</Aviso>
  ) : (
    <>
      {/* custo declarado, inputs alvo/stop, botão verPossibilidades */}
    </>
  )}
  <div style={{ marginTop: "10px" }}>
    {possibilidades.carregando ? <Aviso>...</Aviso>
      : possibilidades.erro ? <ErroDoMcp erro={possibilidades.erro} cp={cp} />
      : possibilidades.dados && !(possibilidades.dados.possibilidades||[]).length ? <Aviso>{possibilidades.dados.motivo}</Aviso>
      : possibilidades.dados ? (/* map com PayoffChart/RazaoGanhoPerda/Cenarios por vencimento */)
      : null}
  </div>
</div>
```

**Props a receber** (ARCHITECTURE.md linha 171): `ticker`, `tese`, `lote`, `alvo`/`setAlvo`, `stop`/`setStop`, `leitura` (para `l.expirations`), `possibilidades`, `verPossibilidades`, `cp`, `palette`. **Não recalcular** `chamadasPrevistas`/`N_MAX_VENCIMENTOS`/`consultados`/`vencimentos` localmente — essas constantes/derivações continuam no orquestrador e descem prontas por prop (ver comentário "Não deve fazer" da tabela de integração).

**Estado compartilhado com job 3 (Pitfall 6 / achado ARCHITECTURE.md):** `tese`/`lote` são o MESMO formulário do job 3 (Analisar) — ficam no `OpcoesScreen.jsx`, nunca descem para `SecaoComparar` como `useState` local. `alvo`/`stop` são exclusivos deste job, mas também ficam no orquestrador por serem consumidos entre re-renders da mesma sessão de navegação (não resetar ao trocar de seção).

---

### `web/src/opcoes/SecaoAnalisar.jsx` (component, request-response + fold-in D-04a)

**Analog:** `SubAbaOperar` (`OpcoesScreen.jsx:1406-1558`) — é o precedente mais próximo de "nunca chama `store.mcp*` (pago) direto, delega o card, guarda de gate/liquidez explícita" e É o objeto do fold-in D-04a. Ressalva: `SubAbaOperar` HOJE busca `gate`/`prop` localmente via dois `useEffect` chamando `store.optionsGate`/`store.optionsProposta` (rotas internas de custo ZERO, permitidas pela regra 2 do guardião — `test_opcoes_subabas_ui.mjs:119-120`, que só proíbe `store.mcp*`) — não recebe esses dois campos por prop. É exatamente essa parte do padrão que NÃO deve ser copiada para `SecaoAnalisar` (ver "o que NÃO copiar" abaixo); o que se copia de `SubAbaOperar` é a disciplina de delegar o card e nunca tocar `store.mcp*`.

**Trecho fonte a extrair** ("LEITURA DO ATIVO" + "O QUE DÁ PARA MONTAR", `OpcoesScreen.jsx:911-1131`): tabela de `behavior` (Linha × Linha), `LacunasDaLeitura`, seletor de tese, vencimento, lote, botão "Montar estrutura", cascata de `proposta`, botões "Ver a cadeia"/"Ver as operáveis" com `painel` local.

**Fold-in D-04a — o que copiar e o que NÃO copiar de `SubAbaOperar`:**
```javascript
// SubAbaOperar (OpcoesScreen.jsx:1432-1446) — o padrão de DOIS useEffect a
// EVITAR reproduzir em SecaoAnalisar; ele existe em SubAbaOperar porque é
// gate/proposta INTERNOS de custo zero (rotas diferentes de leitura.dados).
useEffect(() => {
  let vivo = true;
  setGate(null);
  if (!store || !ticker) return () => { vivo = false; };
  store.optionsGate(ticker).then((r) => { if (vivo) setGate(r); }).catch(() => {});
  return () => { vivo = false; };
}, [store, ticker]);
```
O que D-04a pede é o OPOSTO deste padrão: `opcoesPorTicker`/`opcoesPorTickerCarregando` (saída de `useOpcoesPropostas`, já calculada no topo de `OpcoesScreen`) sobem por PROP para `SecaoAnalisar`, substituindo os `useEffect` locais equivalentes que hoje existem em `SubAbaOperar` — não em `OpcoesScreen.jsx` diretamente, mas o princípio de "usar o fan-out do topo em vez de refazer o fetch" é o mesmo. Cair no fetch local só quando o ticker não tiver sido varrido no fan-out do topo.

**`painel` (cadeia/operáveis) é estado LOCAL a esta seção** (ARCHITECTURE.md linha 158-160: "não há razão estrutural para não ficar local a esse job-section específico, diferente de `ticker`/`tese`") — este é o ÚNICO `useState` que pode nascer dentro do componente novo sem violar Pitfall 6.

**Props a receber:** `ticker`, `escolherTicker`, `status`, `leitura`, `abrirLeitura`, `tecnico`, `posicaoSelecionada`, `tese`/`setTese`, `vencimento`/`setVencimento`, `lote`/`setLote`, `opcoesPorTicker`/`opcoesPorTickerCarregando` (fold-in D-04a), `cp`, `palette`.

**Ao atualizar `test_opcoes_subabas_ui.mjs` regra 3:** quando a contagem de `store.optionsGate(`/`store.optionsProposta(` local a este componente cair de 1 para 0, atualizar a regra com nota datada (ver seção Guardiões abaixo) — não silenciar.

---

## Guardiões — padrão a mirrorar (D-02)

**Analog canônico, já implementado e testado:** `web/tests/test_opcoes_subabas_ui.mjs:100-116`

```javascript
// Fase 32 (32-03, 2026-09-15): estende o invariante acima a TODOS os arquivos de
// web/src/opcoes/ ... Varredura por DIRETÓRIO, não lista fixa: um arquivo novo
// entra automaticamente na checagem, sem precisar lembrar de atualizar este guardião.
const arquivosOpcoesDir = readdirSync(dirOpcoes).filter((f) => f.endsWith(".jsx") || f.endsWith(".js"));
ok("achou pelo menos 10 arquivos em web/src/opcoes/ (sanidade da varredura por diretório)",
   arquivosOpcoesDir.length >= 10);
const comImportDeApp = arquivosOpcoesDir.filter((f) => {
  const src = readFileSync(join(dirOpcoes, f), "utf8");
  return /from\s+["'][^"']*App\.jsx["']/.test(src);
});
ok("nenhum arquivo de web/src/opcoes/ importa App.jsx" + ...,
   comImportDeApp.length === 0);
```

**Segundo precedente, já em produção, para regra de RECÁLCULO (não CVM):** `web/tests/test_opcoes_analisar_ui.mjs:534-537` — mesmo padrão `for (const arq of readdirSync(dirOpcoes)...)`, mostrando que este arquivo JÁ convive com varredura de diretório e indexOf fixo lado a lado — extrapolar o estilo de diretório para as regras de ORDEM é uma mudança de grau, não de espécie, neste arquivo específico.

### Mapeamento guardião → regra afetada → reescrita necessária

| Guardião | Regra afetada (linha) | O que quebra com a extração | Reescrita (Build Order Fase A, ARCHITECTURE.md) |
|---|---|---|---|
| `test_opcoes_consolidacao_ui.mjs` | regra 1 (78-85): `indexOf("{fraseDuasLeituras}") < indexOf("{blocoOportunidades}") < indexOf("{blocoCuradoria}") < indexOf("{blocoVigias}")` | os 4 identificadores somem de `OpcoesScreen.jsx` (viram JSX tags em arquivo novo) | trocar por `indexOf("<SecaoDescobrir")` / `indexOf("<SecaoVigias")` no MESMO arquivo — mantém a relação de ordem, só troca o marcador textual (mecânico, conforme ARCHITECTURE.md "Fase A") |
| `test_opcoes_consolidacao_ui.mjs` | regra 8 (144-150): ausência de `<input>`/`sticky`/`fixed` entre frase-ponte e vigias | continua válido se `SecaoDescobrir`/`SecaoVigias` ficam como tags adjacentes na mesma ordem — só migrar os marcadores de busca | mesma técnica da regra 1, sem mudança de intenção |
| `test_opcoes_subabas_ui.mjs` | regra 3 (123-126): `nGate === 1`/`nProposta === 1` em `OpcoesScreen.jsx` | se o fold-in D-04a mover a chamada para dentro de `SecaoAnalisar.jsx`/hook compartilhado, a contagem em `OpcoesScreen.jsx` cai para 0 | migrar a contagem para SOMA sobre `readdirSync(dirOpcoes)` (mesmo padrão do trecho 100-116), preservando a garantia "exatamente 1 em toda a pasta opcoes/", com nota datada explicando a migração de arquivo |
| `test_opcoes_subabas_ui.mjs` | regra 11 (190-193): `tela.includes("blocoVigias")` etc. (case-sensitive, camelCase) | `blocoVigias` (const) vira `<SecaoVigias` (tag Pascal) — substring desaparece por nomenclatura, não por regressão | trocar a lista de nomes para os NOMES DE COMPONENTE/TAG novos (`SecaoVigias`, `SecaoAnalisar` etc.), preservando a intenção "nada da Fase 27 desapareceu" — nota datada citando a Fase 33 |
| `test_opcoes_vigias_ui.mjs` | linhas 60-98 (`indexOf("cp.opcoesVigiasTitulo")`, fatia de bloco por `onClick={atualizarVigias}`) | os marcadores continuam existindo, mas agora DENTRO de `SecaoVigias.jsx`, não em `OpcoesScreen.jsx` — ler o arquivo errado faz o guardião nunca achar o marcador (índice -1 passa despercebido se a asserção não checar `>= 0` primeiro) | trocar a fonte lida (`readFileSync`) de `OpcoesScreen.jsx` para `SecaoVigias.jsx`; manter a asserção de "achou >= 0" ANTES de qualquer fatiamento (mesmo cuidado do "parse mudo" em `test_opcoes_subabas_ui.mjs:89-92`) |
| `test_opcoes_vigias_ui.mjs` | linhas 120-122 (`function CartaoDeVigia`, fatia por `\n}`) | se `CartaoDeVigia` migrar para dentro de `SecaoVigias.jsx`, o marcador `"function CartaoDeVigia"` deve ser buscado no arquivo novo | mesma troca de fonte lida |
| `test_opcoes_mcp_aba_ui.mjs` | linhas 128-133 (`indexOf("{cabecalho}")`, ordem carregando/erro/vazio/dados) | a cascata carregando→erro→vazio→dados pode passar a viver dentro de um `<CascataDoServico>` (recomendação da ARCHITECTURE.md) ou ficar fatiada entre `SecaoAnalisar`/`SecaoComparar`/`SecaoSetups` — os marcadores de string continuam existindo, mas talvez em arquivo diferente de `OpcoesScreen.jsx` | mapear PRIMEIRO onde cada ramo (carregando/erro/vazio/dados) efetivamente fica após a extração, então apontar `readFileSync` para o(s) arquivo(s) corretos — não assumir que continuam em `OpcoesScreen.jsx` só porque a suíte passa |
| `test_opcoes_analisar_ui.mjs` | linhas 141-146 (`iAnalisar < iPossib < iSetups`, ordem textual jobs 3→4→5) | os três kickers (`cp.opcoesAnalisarTitulo`/`opcoesPossibilidadesTitulo`/`opcoesSetupsTitulo`) migram para 3 arquivos DIFERENTES — a comparação `indexOf` num único `tela` deixa de fazer sentido (todos os três podem retornar -1 ou índices de outro contexto) | Fase A (extração, ordem preservada) do CONTEXT.md/ARCHITECTURE.md: como os 3 componentes ainda são renderizados na MESMA ordem dentro de `OpcoesScreen.jsx` (`<SecaoAnalisar/><SecaoComparar/><SecaoSetups/>`), trocar os marcadores de `cp.opcoesXTitulo` para `<SecaoAnalisar`/`<SecaoComparar`/`<SecaoSetups` no `OpcoesScreen.jsx` — a garantia de ORDEM sobrevive; só o texto buscado muda |
| `test_opcoes_analisar_ui.mjs` | linhas 154-157 (fatia de bloco por trio `.carregando`/`.erro`/vazio/dados) | mesmo cuidado de `test_opcoes_mcp_aba_ui.mjs` acima — mapear se a cascata migrou de arquivo | idem — apontar para o arquivo novo antes de reescrever a asserção |
| `test_opcoes_analisar_ui.mjs` | linha 534 (varredura por diretório de recálculo) | NENHUMA mudança necessária — este já varre o diretório inteiro, arquivos novos entram de graça | nenhuma ação — é o segundo precedente que já cobre `Secao*.jsx` automaticamente |

**Regra geral de reescrita (Pitfall 3):** para CADA guardião acima, antes de editar, `grep -rln "OpcoesScreen.jsx" web/tests/*.mjs` (a pesquisa já confirma 9 arquivos hoje) e reler o comentário de contexto acima da asserção — a maioria cita "achado por injeção de defeito real" ou "decisão do Alex". Reescrever no MESMO commit que move o código, nunca depois. Nunca só ajustar o número/nome esperado sem confirmar que a garantia original (fonte única, ordem, sem recálculo) ainda vale.

## Shared Patterns

### Isolamento de duas vias (ADR-027, Emenda 3) — aplica a TODOS os 5 componentes novos
**Fonte:** `web/src/opcoes/OportunidadesOpcoes.jsx:1-22`, `web/src/opcoes/CuradoriaEstruturas.jsx:1-27`
```javascript
/**
 * (a) Por que este módulo existe: `OpcoesScreen.jsx` não pode importar
 * `App.jsx` (ADR-027, Decisão 3) e `App.jsx` não pode importar
 * `OpcoesScreen.jsx` (seria ciclo)...
 */
```
Nenhum `Secao*.jsx` importa `App.jsx`. Tokens de tema (`T`), fontes (`MONO`), formatadores (`price`/`money`) e o padrão de carrossel (`carouselTrackStyle`/`carouselItemStyle`) são "espelho declarado" localmente — nunca importados de `App.jsx`. Coberto automaticamente pela varredura de diretório de `test_opcoes_subabas_ui.mjs:100-116`.

### Dado por prop, ação por callback — nunca `store.*`/`api.*` dentro de componente de seção
**Fonte:** ARCHITECTURE.md, seção "Convenção a replicar", e `test_opcoes_subabas_ui.mjs` regra 2 (linha 119-120: `!/store\.mcp/.test(subAba)`)
Todo `Secao*.jsx` recebe dado pronto (`propostas`, `leitura`, `vigias` etc.) e ações prontas (`onAbrir`, `onExecutar`, `onNarrar`) por prop — nunca chama `useOpcoesMcp`/`useOpcoesPropostas`/`store.mcp*`/`store.options*` diretamente. Verificação pós-fase: grep `store\.` em cada `Secao*.jsx` novo, deve dar zero.

### Guardrail CVM de manchete — verbatim, sem composição
**Fonte:** comentários repetidos em `OportunidadesOpcoes.jsx:111-113`, `CuradoriaEstruturas.jsx:190-193`, guardião `test_opcoes_subabas_ui.mjs:141-154`
```javascript
{/* manchete do motor, verbatim — guardrail CVM (CLAUDE.md);
    nunca truncada/concatenada: cortar reescreveria a afirmação do motor. */}
<div ...>{cand.manchete}</div>
```
`SecaoDescobrir.jsx` (que embute `OportunidadesOpcoes`/`CuradoriaEstruturas`) herda esta obrigação. Se qualquer `Secao*.jsx` novo vier a renderizar `candidato.manchete`/`ctx.curadoria.top[i].manchete` diretamente (não via componente já coberto), a extensão do guardião precisa alcançá-lo — ver Pitfall 4.

### Cascata carregando → erro → vazio com motivo → dados
**Fonte:** repetida em `OpcoesScreen.jsx` (836-908, 1013-1038, 1068-1128, 1183-1215) e em `CuradoriaEstruturas.jsx:298-328`
```javascript
{trio.carregando ? (
  <Aviso>{cp.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
) : trio.erro ? (
  <ErroDoMcp erro={trio.erro} cp={cp} />
) : trio.dados && /* vazio com motivo */ ? (
  <Aviso>{trio.dados.motivo || "..."}</Aviso>
) : trio.dados ? (
  /* render dos dados */
) : null}
```
Recomendação da ARCHITECTURE.md ("Um helper vale a pena"): extrair `<CascataDoServico status={...} erro={...} carregando={...}>{children}</CascataDoServico>` reusado por `SecaoAnalisar`/`SecaoComparar`/`SecaoSetups`, em vez de reescrever o if/else em cada um — decisão de quem planeja/executa (Claude's Discretion), mas se optar por não extrair, replicar a MESMA ordem de ramos (carregando antes de vazio, sempre) em cada seção — nunca inventar uma ordem nova.

### Estado compartilhado por 2+ jobs fica no orquestrador (`OpcoesScreen.jsx`)
**Fonte:** ARCHITECTURE.md, seção "Estado local que atravessa jobs" + Pitfall 6 do PITFALLS.md
`ticker`/`escolherTicker`, `tese`, `vencimento`, `lote` NÃO descem para nenhum `Secao*.jsx` — continuam declarados em `OpcoesScreen.jsx` e chegam por prop. Único `useState` que pode nascer dentro de uma seção nova: `painel` (`"" | "cadeia" | "operaveis"`), exclusivo de `SecaoAnalisar`.

## No Analog Found

Nenhum arquivo desta fase ficou sem analog — os 5 componentes novos têm precedente direto de extração (Fase 32) ou trecho-fonte identificável linha a linha dentro de `OpcoesScreen.jsx`, e os 5 guardiões têm o padrão de varredura por diretório já implementado duas vezes no próprio diretório de testes.

## Metadata

**Analog search scope:** `web/src/opcoes/` (14 arquivos), `web/tests/test_opcoes_*.mjs` (5 arquivos relevantes), leitura completa de `web/src/opcoes/OpcoesScreen.jsx` (2010 linhas, lido em blocos não sobrepostos: 1-95, 303-432, 587-836, 836-965, 965-1100, 1100-1410, 1406-1495), `web/src/opcoes/OportunidadesOpcoes.jsx` (135 linhas, completo), `web/src/opcoes/CuradoriaEstruturas.jsx` (359 linhas, completo).
**Files scanned:** 11 arquivos de código + 5 guardiões (leitura direta) + 3 documentos de pesquisa (33-CONTEXT.md, ARCHITECTURE.md, PITFALLS.md)
**Pattern extraction date:** 2026-09-19
