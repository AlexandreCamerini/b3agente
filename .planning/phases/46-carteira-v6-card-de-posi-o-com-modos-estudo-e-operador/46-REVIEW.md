---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
reviewed: 2026-10-02T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - server/app/cartao_posicao.py
  - server/app/estrutura_posicao.py
  - server/app/main.py (POST /api/carteira/leitura, 4335-4381)
  - server/app/skill_ref.py (CARTAO_POSICAO / CARTAO_DIDATICA, 866-1186)
  - web/src/estruturaCard.js
  - web/src/cartaoV6Cores.js
  - web/src/copy.js (cartaoPosicaoTxt / espelho)
  - web/src/persistence.js (carteiraLeitura nos dois stores)
  - web/src/App.jsx (useLeiturasPlano, CartaoPosicao, LinhasResultadoV6, ChipsMetaV6, LinhaEstadoV6, FaixaVencimento, FaceAcao, BlocoBorisIA, SimuladorEstudo, TermosTocaveis, PayoffOperador, GradeConta)
findings:
  critical: 0
  high: 2
  medium: 6
  low: 7
  total: 15
status: issues_found
---

# Fase 46: Code Review (Carteira v6)

Escopo: planos 46-01..46-12. Excluídos por instrução: G-07/G-08 do 46-UAT, ReguaFaixa sem uso, imports sem uso mostraAvisoSemStop/mostraRR/valorRR.
Verificado: paridade skill_ref<->copy.js passa (`node web/tests/test_cartao_posicao_espelho.mjs`), guardião de contraste passa, paridade serverStore/deviceStore de `carteiraLeitura` presente (persistence.js:278 e :1347), sem hex literal no trecho do card (cores só por `cartaoV6Cores.js` / `T.*` / `--cv-*`), sem vocabulário proibido ("trava protetora", "abate o custo") nem promessa de lucro. Sem crítico.

## Alto

### AL-01: Estudo mostra equação do equilíbrio FALSA para collar
**Arquivo:** `server/app/cartao_posicao.py:466-487` (usa `caso_equilibrio` de `skill_ref.py:1142`)
**Cenário:** `didatica_estrutura` monta `casos["equilibrio"]` com `premio` = prêmio da ÚNICA call vendida. Para `collar`, o equilíbrio do payoff é `PM − prêmio da call + prêmio da put`, mas o texto afirma "R$ be = preço médio R$ pm menos o prêmio R$ premio". Reproduzido: collar PETR4, PM 35,00, call vendida a 1,00, put comprada a 0,60 → `be` = 34,60 e o card diz "R$ 34,60 = preço médio R$ 35,00 menos o prêmio R$ 1,00" (35 − 1 = 34). É um número de explicação educacional aritmeticamente errado, exibido em "No seu caso" ao tocar em "equilíbrio" (viola princípio 5/6: nada que o motor não sustente). O Operador está protegido (`_conta_call_coberta` só atende `nome == "call_coberta"`), o Estudo não.
**Correção:** gerar `casos["equilibrio"]` com a frase "menos o prêmio" só quando `nome == "call_coberta"`; para collar usar frase própria que cite os dois prêmios (put pago e call recebida, ambos vindos do payload) ou cair em `caso_aguardando`. Adicionar teste de collar com prêmios diferentes de zero.

### AL-02: Falha da leitura em lote é invisível e deixa leituras velhas na tela como se fossem atuais
**Arquivo:** `web/src/App.jsx:4484-4530` (consumo em `:5647`); `plano.status` nunca é lido (grep: só `plano.leituras[...]`)
**Cenário:** `useLeiturasPlano` marca `status: "falha"` e mantém as leituras anteriores, mas nenhuma tela usa `status`. (1) Se `POST /api/carteira/leitura` falha (timeout 15 s, 5xx, offline), o card segue exibindo `resultado`, `rr`, "agora R$ X" e `posicaoNoPlano` calculados com o preço ANTIGO enquanto `quotes` já avançou, sem aviso (princípios 3/4/9: dado atrasado e estado de erro sem estado correspondente). (2) Na primeira carga com falha, `leituraPlano` fica `undefined` e a linha "Ações" mostra "cotação indisponível" (`motivo_cotacao_indisponivel`), diagnóstico errado: a cotação existe, o que falhou foi a leitura. (3) `ultimaRef.current = assinatura` é gravado antes da chamada: sem mudança de preço/posição não há nova tentativa, e não há botão de reatualizar para o plano (o `BotaoAtualizarEstrutura` só cobre estrutura). (4) Após buy/sell, até a resposta chegar, o card mistura `p.qty/p.avg` novos com `resultado` da quantidade antiga.
**Correção:** expor `plano.status`; em `falha`/`carregando` com `leituras[t].assinatura` diferente da vigente, descartar ou marcar a leitura como desatualizada (chave de copy própria, ex. `leitura_indisponivel`), distinguir "leitura indisponível" de "cotação indisponível" e permitir nova tentativa (limpar `ultimaRef` no erro + botão). Guardar a assinatura usada em cada resposta e só exibir se igual à atual.

## Médio

### MD-01: "Sem stop e alvo" falso para posição protegida por put (regressão de CARD-05)
**Arquivo:** `web/src/estruturaCard.js:206` (`estadoPrincipalV6`)
**Cenário:** o ramo `p.stop == null && p.alvo == null → estado_sem_plano` ("Sem stop e alvo — defina o plano", tom atenção ⚠) ignora `estrutura.stopTexto` (proteção declarada pelo motor quando `qtdPut >= quantidade`). Antes, `mostraAvisoSemStop` suprimia o aviso nesse caso; agora um collar/put de proteção totalmente coberto exibe alerta de risco falso. Não é a dívida do import sem uso: é a regra que ele implementava que deixou de valer.
**Correção:** em `estadoPrincipalV6`, quando `estrutura && estrutura.stopTexto != null` e `p.stop == null`, não emitir `estado_sem_plano` (ou usar um estado neutro com o `stopTexto`).

### MD-02: aria/rótulo "sem teto" afirmado quando existe teto com cobertura parcial
**Arquivo:** `server/app/cartao_posicao.py:376`; frases `payoff_aria_sem_teto` (`skill_ref.py:968` e `:1087`)
**Cenário:** `chave_aria = "payoff_aria" if k is not None and ganho is not None else "payoff_aria_sem_teto"`. Com call vendida cobrindo só parte da base (`faixa_teto_parcial`, `ganhoMaximo = None` mas `teto` definido), o leitor de tela recebe "sem teto, o resultado acompanha a ação" (Estudo), afirmação falsa que contradiz o `teto` desenhado no payoff.
**Correção:** terceiro caso (`payoff_aria_teto_parcial`: teto R$ X cobre só parte das ações; ganho máximo não calculado) ou decidir só por `k is None`.

### MD-03: nota de PM afirma "PM = total ÷ qtd" sem conferir que as compras reconciliam com o PM; truncamento pega as compras mais antigas
**Arquivo:** `server/app/cartao_posicao.py:120-140` (`_nota_pm`); `server/app/main.py:4375` (`compras_brutas[:_LEITURA_MAX_COMPRAS]`)
**Cenário:** (a) o texto asserta "PM R$ {avg} = R$ {total} ÷ {q} ações" com `avg` vindo da posição e `total/q` do histórico; se divergirem (posição importada, ajuste de PM por exercício/atribuição, histórico truncado, compras inválidas descartadas por `_num`), a equação exibida é falsa. (b) com >200 compras o corte `[:200]` mantém as MAIS antigas (o front envia antiga→recente), então `total`/`q` ficam sem as compras recentes e a nota ainda complementa com "Vendas parciais reduzem a quantidade" por engano (`abs(q - qty) > 1e-9`).
**Correção:** só emitir a nota se `abs(total/q - avg) <= 0.005` (e `n` não truncado); cortar com `[-_LEITURA_MAX_COMPRAS:]` ou rejeitar acima do limite; não anexar `nota_pm_vendas` quando houve descarte/truncamento.

### MD-04: preço do card fechado sem fonte, horário nem estado de atraso/mercado fechado
**Arquivo:** `web/src/App.jsx:4491-4500` (envio), `:4739-4741` ("agora X"), `:4764` (hoje na faixa), `:4914`
**Cenário:** o hook envia `quotes[t].price` sem `source`/`asOf`/flag de atraso e a rota ecoa `preco` como se fosse "agora". Resultado, % e posição no plano (abaixo do stop / dentro / acima do alvo) aparecem com cotação defasada ou de fechamento anterior sem rótulo (princípios 3, 7 e 9: fonte, horário e "mercado fechado/atrasado"). A face Opções mostra fonte/horário; o card fechado e a face Ação não.
**Correção:** propagar origem e horário da cotação (já existentes no quote) para a linha do card ("agora R$ X · fonte · hh:mm · atrasada 15 min") e suprimir `posicaoNoPlano`/estado de risco quando o dado estiver marcado como atrasado/histórico.

### MD-05: cabeçalho do card mostra só o resultado das ações rotulado "resultado" enquanto a estrutura carrega ou falha
**Arquivo:** `web/src/App.jsx:4885-4892` (`e = modoLeitura === "estruturada" ? ... : null`) + `web/src/estruturaCard.js:394-406`
**Cenário:** posição com opções em `carregando`/`falha`: `e` é `null`, então `linhasResultadoV6` cai no ramo "ação" e o cabeçalho exibe o P&L só das ações com legenda "resultado · +x%", sem sinal de que as pernas de opção ficaram de fora (call vendida em perda, por exemplo). O usuário lê o número como resultado da posição inteira; só a linha "lendo/indisponível" abaixo avisa.
**Correção:** quando `comPernas` e `modoLeitura !== "estruturada"`, tratar o cabeçalho como suspenso (`—` + "total suspenso") ou usar `legenda_resultado` com "só ações".

### MD-06: Simulador do Estudo não reconcilia o índice quando a grade muda
**Arquivo:** `web/src/App.jsx:5226-5232`
**Cenário:** `idx` é inicializado uma vez em `useState` (ponto "hoje"). Ao atualizar a estrutura (botão Atualizar, spot novo, troca de assinatura), `sim.pontos` é recalculada (outro `lo/hi`, outros preços), mas `idx` continua apontando o mesmo ÍNDICE, que agora é outro preço/zona: o slider deixa de estar em "hoje" e o chip "hoje" fica desmarcado sem o usuário ter mexido. Também, ao alternar faces (AreaFlip desmonta a face), a posição escolhida se perde. Não há erro numérico (preço e resultado do mesmo índice são coerentes), mas o estado é enganoso.
**Correção:** guardar o PREÇO escolhido (ou o nome do ponto) e remapear para o índice na nova grade; ou `key={assinatura da grade}` no componente para reiniciar em "hoje".

## Baixo

### BX-01: preço exatamente no stop ou no alvo é classificado como "dentro"
**Arquivo:** `server/app/cartao_posicao.py:201-202`
**Cenário:** `preco < stop` / `preco > alvo` estritos: com preço = stop ou = alvo o card diz "Dentro do plano" quando o gatilho já foi tocado.
**Correção:** usar `<=` / `>=` (e alinhar o teste guardião).

### BX-02: exceção do cálculo de cenários engolida sem log
**Arquivo:** `server/app/estrutura_posicao.py:391-392`
**Cenário:** `except Exception: cenarios = didatica = None` esconde bugs do motor (a rota de leitura loga, esta não); o usuário só vê "Cenários não calculados".
**Correção:** `obslog.log("err", ..., level="warn")` como em `main.py:4380`.

### BX-03: didática de call coberta/collar degrada para texto de "combinação composta" quando `cenarios` falha
**Arquivo:** `server/app/cartao_posicao.py:438-452`
**Cenário:** as três ramificações exigem `cen`; se `cenarios_da_estrutura` devolve None (ex.: mais de um breakeven), uma call coberta conhecida passa a ser descrita como "combinação envolve lastro, piso e teto: aguardando o cálculo". Honesto, mas o nome da estrutura já é conhecido.
**Correção:** não depender de `cen` para o parágrafo-base, só para o caso de equilíbrio.

### BX-04: vocabulário fora de skill_ref/copy no card
**Arquivo:** `web/src/App.jsx:5245-5248` ("◆ equilíbrio", "teto", "hoje"), `:5078-5080` ("Stop", "Alvo", "hoje", " dia/dias"), `:5172`
**Cenário:** o front compõe frases que a lei do vocabulário reserva ao backend/copy; não há espelho em `skill_ref.py`, então Estudo/Operador não variam e o guardião de paridade não os cobre.
**Correção:** mover para chaves de `CARTAO_POSICAO` (já existem `faixa_rot_be`/`faixa_rot_teto`/`leg_hoje`).

### BX-05: `pctDoCapital` calcula no cliente com bases inconsistentes
**Arquivo:** `web/src/App.jsx:1129-1132`, usado em `:4891` e `:5060`
**Cenário:** `qty * preço_cru_da_cotação / total`, onde `total` marca outras posições sem cotação a PM (patrimônio de `portfolioMetrics`); aritmética financeira no cliente contraria D-01/princípio 5 e o formato difere entre `toFixed(1)` (FaceAcao) e `pctCapitalTexto` (linhas).
**Correção:** mover para `leitura_plano` (o backend já recebe `preco`/`qty`; faltaria o patrimônio) ou documentar a exceção e unificar a formatação.

### BX-06: helpers de formatação com bordas visuais
**Arquivo:** `web/src/estruturaCard.js:339-344`, `:419`
**Cenário:** `rsSinalNbsp` com valor negativo minúsculo (|v| < 0,005) imprime "−R$ 0,00" (sinal sem arredondar); `chip_vence` com `dias` nulo imprime "vence 20/11 · —d".
**Correção:** classificar o sinal sobre `Math.round(v*100)`; omitir o sufixo de dias quando nulo.

### BX-07: limite de 60 posições do backend sem tratamento no front e uma chamada por tick de preço
**Arquivo:** `server/app/main.py:4354` x `web/src/App.jsx:4491-4527`
**Cenário:** o front envia todas as posições; acima de 60 o servidor devolve 400 e TODOS os cards caem em falha (AL-02). Além disso a assinatura inclui o preço a 2 casas, então cada variação de cotação dispara um POST em lote (sem custo de provedor, mas tráfego e flicker de "carregando").
**Correção:** fatiar em lotes de 60 e debouncer a assinatura por preço (ou re-ler só em mudança de posição/plano).

---

_Reviewed: 2026-10-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
