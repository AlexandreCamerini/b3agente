---
quick_id: 260911-dcq
phase: quick-260911-dcq
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [server/app/scanner.py, server/app/scan_deep.py, server/app/technical_snapshot.py, server/tests/test_fuso_carimbos_visiveis.py]
autonomous: true
---

<objective>
Achado D-2 (primeira parte), do executor da quick 260911-15a: os carimbos de
"quando isto foi apurado" que a interface EXIBE estão 3 h à frente em
produção, porque usam `time.strftime` sem fuso e o container roda em UTC.

São exatamente três, todos o mesmo padrão:
- `server/app/scanner.py:350` → `timestamp` — **o mais visível**: a tela mostra
  em `web/src/App.jsx:6980`, ao lado de "N/M ativos varridos";
- `server/app/scan_deep.py:155` → `timestamp`;
- `server/app/technical_snapshot.py:174` → `generatedAt`.

Isto contraria o princípio 3 do CLAUDE.md, que exige que o dado de mercado
exiba o horário da última atualização — um horário 3 h adiantado é pior que
nenhum, porque parece preciso.
</objective>

<context>
O padrão já está estabelecido no repositório por duas quicks desta semana:
- `260909-oyu` (`store.now_str`, `main.now_str`, `obslog`): `BRT =
  timezone(timedelta(hours=-3))` local ao módulo, com comentário de decisão;
- `260911-15a` (`candle_provider._hoje`, `scan_deep._day`): o mesmo, e o
  guardião cravando o relógio num instante em que UTC e BRT estão em DIAS
  diferentes. `scan_deep.py:40` já tem o comentário "A-10" desta rodada.

Ou seja: `scan_deep` já ganhou BRT para a chave de "hoje", mas o `timestamp`
da linha 155 do MESMO arquivo ficou de fora — é a pista de que a correção
anterior foi por sintoma, não por classe.
</context>

<tasks>
<task type="auto">
  <name>Task 1: os três carimbos de apuração em BRT</name>
  <files>server/app/scanner.py, server/app/scan_deep.py, server/app/technical_snapshot.py, server/tests/test_fuso_carimbos_visiveis.py</files>
  <action>
  Trocar os três `time.strftime("%Y-%m-%dT%H:%M:%S")` por carimbo em BRT, no
  padrão já estabelecido (`BRT` local ao módulo onde ainda não existir;
  `scan_deep` já tem, reuse).

  **Decisão a tomar e justificar no comentário**: manter o formato atual
  (`%Y-%m-%dT%H:%M:%S`, sem sufixo de fuso) ou acrescentar o offset
  (`-03:00`). Argumento para manter: a tela imprime a string crua
  (`App.jsx:6980`), então mudar o formato muda o que o usuário lê, e isso
  exigiria tocar o front. Argumento para acrescentar: sem sufixo, o carimbo
  continua ambíguo para quem consome a API. **LEIA como a tela renderiza antes
  de decidir** e, se escolher mudar o formato, PARE e reporte em vez de
  editar o front nesta task.

  Guardião novo `server/tests/test_fuso_carimbos_visiveis.py`, espelhando
  `test_store_now_str_brt.py` e `test_fuso_candle_provider_scan_deep_brt.py`:
  cravar o relógio num instante em que UTC e BRT caem em DIAS diferentes
  (ex.: 01:30 UTC = 22:30 BRT do dia anterior) e provar que os três carimbos
  trazem o dia E a hora de Brasília. Teste que só prova a hora não serve.

  Varra o resto de `server/app/` por outros `time.strftime` sem fuso que
  possam chegar à UI. Se achar um quarto, inclua; se achar algo que NÃO é
  carimbo de apuração (métrica interna, nome de arquivo), deixe e diga no
  SUMMARY por quê.
  </action>
  <verify>
  RED/GREEN: rodar o guardião novo contra o código de ANTES
  (`git show HEAD:<arquivo>` para arquivos temporários FORA do repo — NUNCA
  `git stash`) e confirmar a falha com o dia errado; depois com a correção.
  Depois: `bash scripts/executar.sh --testes`.
  </verify>
  <done>Os três carimbos mostram o horário de Brasília, provado num instante que cruza a meia-noite.</done>
</task>
</tasks>

<fora_de_escopo>
A SEGUNDA parte do D-2 **não** entra aqui: `date.today()` naive em
`options_api.py:36`, `main.py:2515,2540,2741` e `mydata_client.py:202`, que faz
aritmética de DIAS ATÉ O VENCIMENTO e alimenta o gate de liquidez. Tem
consequência financeira, não cosmética, e merece task própria com prova de
impacto no gate. Registre isso no SUMMARY como a pendência seguinte.
</fora_de_escopo>

<success_criteria>
Um commit atômico. Front NÃO é editado. Deploy só-backend — NÃO fazer.
</success_criteria>
