# 260911-pub — mesclar o 260911-k9g e publicar o front

**Pedido:** "mescla o 260911-k9g e publica o front" (Alex, 2026-09-11).

## Estado de partida (medido, não presumido)

- `v2/interacao-estrutural` em `1a91f0a`, **4 commits à frente do `main`
  (`e181f33`), 0 atrás** — fast-forward possível, sem merge de `origin/main`
  antes (memória `bump-colide-em-sessao-paralela` não se aplica aqui).
- `BUILD_ID` = `F10-20260910-02` (`web/src/version.js`)
- `SERVER_BUILD_ID` = `F10-20260911-02` (`server/app/main.py:1043`) — **maior
  que o do front**, resultado do último deploy só-backend.
- Conteúdo do k9g: rodapé do Perfil mostra o carimbo do app E do servidor.
  Toca `web/src/App.jsx`, `api.js`, `persistence.js`, mais o teste
  `web/tests/test_carimbo_servidor_rodape.mjs`. Plano/resumo em
  `.planning/quick/260911-k9g-carimbo-do-servidor-no-rodape/`.

## A armadilha (o motivo deste plano existir)

`bash scripts/bump.sh` **sem argumento** derivaria de `F10-20260910-02` e, por
ser outro dia, produziria `F10-20260911-01` — **abaixo** do `F10-20260911-02`
que já está no ar. O carimbo do front andaria para trás em relação ao servidor,
e o `publicar-web.sh` então REBAIXARIA o `SERVER_BUILD_ID` de `-02` para `-01`
ao sincronizar (ele iguala sem comparar ordem).

O próprio `server/app/main.py:1043` avisa: *"Ao publicar front, passe o carimbo
explícito a `bump.sh`"*. Então: **`bash scripts/bump.sh F10-20260911-03`**.

Segundo detalhe: o `publicar-web.sh` troca só a STRING do `SERVER_BUILD_ID` e
preserva o comentário da linha. O comentário atual diz "DEPLOY SÓ-BACKEND:
bumpado À MÃO, o front segue em F10-20260910-02" — verdadeiro hoje, mentira
depois desta publicação. Tem de ser reescrito à mão.

## Passos

1. Baseline: `bash scripts/executar.sh --testes` (as DUAS suítes) antes de
   qualquer mudança, para não atribuir a esta tarefa uma falha preexistente.
2. `bash scripts/bump.sh F10-20260911-03` — carimbo explícito.
3. `bash scripts/publicar-web.sh` — `npm ci` + `vite build`, copia para
   `server/web_dist`, sincroniza `SERVER_BUILD_ID`.
4. Reescrever o comentário do `SERVER_BUILD_ID` para descrever ESTA entrega.
5. Suíte inteira verde de novo, `test_ios_assets.mjs` incluso (ele pega
   bundle amputado e carimbo repetido com chunks diferentes).
6. Commit atômico: `version.js` + `server/app/main.py` + `server/web_dist`.
7. Mesclar em `main` (fast-forward) e `push`. Railway redeploya sozinho.
8. Verificar `/api/health` = `F10-20260911-03` e o bundle servido na raiz.

## Riscos

- `npm ci` precisa de rede; o sandbox pode barrar. Se barrar, reexecutar com
  sandbox desligado (é o caso previsto de "Operation not permitted").
- `server/web_dist` **se regenera, não se mescla** — se houver conflito nele,
  a resolução é rebuildar, nunca resolver hunk a hunk.
- `gh` está com falha de TLS neste ambiente (`x509: OSStatus -26276`); se o PR
  não subir, o fast-forward direto em `main` é o caminho, não insistir no `gh`.

## Critério de aceite

- `curl -s https://boris.semente.dev/api/health` → `F10-20260911-03`.
- O bundle servido em produção contém a string `F10-20260911-03`.
- Rodapé do Perfil em produção mostra os dois carimbos.
- `main` contém os 4 commits do k9g + o commit de publicação.
- Suíte canônica verde.
