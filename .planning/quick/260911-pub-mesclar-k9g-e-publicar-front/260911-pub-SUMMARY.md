---
quick_id: 260911-pub
status: done
commit: 54d97b1
merge: a8b0a6b (PR #45)
files_modified: [web/src/version.js, server/app/main.py, server/web_dist/**]
carimbo: F10-20260910-02 -> F10-20260911-03
---

# 260911-pub — Mesclar o 260911-k9g e publicar o front

## O que mudou

Publicação do front que entrega o quick `260911-k9g` (rodapé do Perfil com o
carimbo do app **e** do servidor). Sem esta publicação o k9g estava mesclado,
testado e invisível: `server/web_dist` é a única árvore que o Railway serve, e
merge de PR não publica front.

Também mesclou em `main` os 4 commits do k9g que estavam parados em
`v2/interacao-estrutural`.

## A armadilha que o plano existiu para evitar

`bash scripts/bump.sh` **sem argumento** derivaria `F10-20260911-01` a partir do
`F10-20260910-02` do front (dia novo → sequencial reinicia em 01). O
`publicar-web.sh` então **rebaixaria** o `SERVER_BUILD_ID` de `F10-20260911-02`
— já no ar pelo deploy só-backend anterior — para `-01`, porque ele iguala os
dois carimbos sem comparar ordem:

```bash
if [ "$SRV_ATUAL" != "$BUILD_LOCAL" ]; then   # != , não <
```

O aviso já estava escrito no comentário do próprio `server/app/main.py:1043`
("Ao publicar front, passe o carimbo explícito a `bump.sh`"), deixado lá pelo
deploy anterior. Foi lido e obedecido: `bash scripts/bump.sh F10-20260911-03`.

`-01` e `-02` ficam **pulados de propósito**. O comentário da linha do
`SERVER_BUILD_ID` foi reescrito para descrever esta entrega — o
`publicar-web.sh` troca só a string e preservaria o texto antigo, que dizia
"DEPLOY SÓ-BACKEND ... o front segue em F10-20260910-02" e viraria mentira.

## Descoberta de ambiente: 26 falhas falsas no sandbox

O baseline dentro do sandbox acusou 26 falhas em 8 arquivos
(`test_yahoo_*`, `test_texto_vazio`, `test_benchmark_ibov`,
`test_push_registro_evento`, `test_fase3_kill_switch_duracao`,
`test_options_provider_yahoo`, `test_rotas_fase4`). Causa reproduzida num teste
isolado:

```
PermissionError: [Errno 1] Operation not permitted
  ssl.py:717  context.load_verify_locations(cafile, capath, cadata)
```

Artefato do sandbox barrando a leitura dos certificados, **não regressão**. Fora
do sandbox: 2342 passed, 4 skipped. A mesma causa explicava o
`x509: OSStatus -26276` do `gh`, que também voltou a funcionar fora do sandbox.

**Como aplicar:** suíte do backend deste repo precisa de sandbox desligado, senão
o resultado é ruído. Conferir a assinatura `load_verify_locations` antes de
caçar regressão inexistente.

## Verificação

- `bash scripts/executar.sh --testes` → **exit 0**, antes e depois da mudança.
- Carimbo conferido nos quatro elos: `version.js`, `web/dist`,
  `server/web_dist`, `main.py` — todos `F10-20260911-03`, mesmo arquivo de
  bundle (`index-Ci9stJwG.js`, 827.722 bytes) nos dois dists. Ordenar por
  tamanho (`ls -laS`) é o que impede confundir um chunk pequeno com o bundle.
- `git add` com escopo fechado nos 4 caminhos; as 4 skills não rastreadas em
  `.claude/skills/` ficaram fora, conferido.

## Limitação conhecida

O bundle do **iOS** continua em `F10-20260910-02`: o app do TestFlight (2.0/12)
foi arquivado antes desta publicação. Quem abrir pelo TestFlight verá
`app F10-20260910-02 · servidor F10-20260911-03` — que é exatamente a
informação que o k9g existe para mostrar, e está correta.
