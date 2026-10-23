---
phase: quick-261022-rht
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - resources/ios/versao.env
  - scripts/ios-aplicar-projeto.sh
  - web/tests/fixtures/ios-projeto/App/App.xcodeproj/project.pbxproj
  - web/tests/fixtures/ios-projeto/App/App/Info.plist
  - web/tests/test_ios_aplicar_projeto.mjs
  - scripts/instalar-iphone.sh
  - scripts/setup-ios.sh
  - scripts/ios-bump-build.sh
  - scripts/ios-testflight.sh
  - scripts/ios-restaurar-entitlements.sh
  - TESTFLIGHT.md
  - CLAUDE.md
autonomous: true
requirements: [QUICK-261022-RHT-1, QUICK-261022-RHT-2, QUICK-261022-RHT-3, QUICK-261022-RHT-4, QUICK-261022-RHT-5]

must_haves:
  truths:
    - "Num web/ios recém-criado por `npx cap add ios`, instalar-iphone.sh e setup-ios.sh deixam o pbxproj com DEVELOPMENT_TEAM=LC65399YC9, CODE_SIGN_ENTITLEMENTS=App/App.entitlements, MARKETING_VERSION e CURRENT_PROJECT_VERSION vindos de resources/ios/versao.env, nas DUAS configs do target (Debug+Release), e o PrivacyInfo.xcprivacy referenciado no grupo App + fase Resources, sem nenhum passo no Xcode"
    - "Rodar ios-aplicar-projeto.sh duas vezes deixa project.pbxproj e Info.plist byte-idênticos à primeira execução"
    - "Um pbxproj sem PBXNativeTarget (assinatura do incidente de 2026-10-22) faz o script sair != 0 com mensagem PT-BR apontando `bash scripts/instalar-iphone.sh --recriar-ios`, sem alterar o arquivo"
    - "ios-bump-build.sh incrementa o build em resources/ios/versao.env e aplica no projeto; se o pbxproj não tem CURRENT_PROJECT_VERSION ou não tem PBXNativeTarget, falha sem tocar versao.env (nunca mais calcula 0->1 em silêncio)"
    - "ios-testflight.sh referencia o PrivacyInfo sozinho (via ios-aplicar-projeto.sh) em vez de imprimir a instrução manual de arrastar no Xcode"
    - "O bundle id (PRODUCT_BUNDLE_IDENTIFIER) nunca é escrito por nenhum dos scripts"
  artifacts:
    - path: "resources/ios/versao.env"
      provides: "Fonte única versionada da versão pública iOS e do último build number"
      contains: "CURRENT_PROJECT_VERSION=35"
    - path: "scripts/ios-aplicar-projeto.sh"
      provides: "Reaplicação idempotente de time/entitlements/versões/PrivacyInfo/nome num web/ios qualquer"
      min_lines: 80
    - path: "web/tests/test_ios_aplicar_projeto.mjs"
      provides: "Guardião na suíte canônica (fixture -> aplica; 2x -> idêntico; sem target -> falha; bump)"
    - path: "web/tests/fixtures/ios-projeto/App/App.xcodeproj/project.pbxproj"
      provides: "pbxproj do template SPM do Capacitor (pristino, sem time/entitlements/PrivacyInfo)"
      contains: "isa = PBXNativeTarget;"
  key_links:
    - from: "scripts/instalar-iphone.sh"
      to: "scripts/ios-aplicar-projeto.sh"
      via: "chamada após cap sync + patch-appdelegate"
      pattern: "ios-aplicar-projeto\\.sh"
    - from: "scripts/setup-ios.sh"
      to: "scripts/ios-aplicar-projeto.sh"
      via: "chamada após cap add/sync + restaurar entitlements"
      pattern: "ios-aplicar-projeto\\.sh"
    - from: "scripts/ios-bump-build.sh"
      to: "resources/ios/versao.env"
      via: "lê/escreve CURRENT_PROJECT_VERSION e depois chama o aplicar"
      pattern: "versao\\.env"
    - from: "scripts/ios-testflight.sh"
      to: "scripts/ios-aplicar-projeto.sh"
      via: "substitui o bloco de instrução manual do PrivacyInfo"
      pattern: "ios-aplicar-projeto\\.sh"
---

<objective>
Fazer o projeto iOS (gitignored, recriável) voltar sozinho ao estado publicável depois de
`npx cap add ios`, eliminando o que foi feito à mão em 2026-10-22 (pbxproj sem target,
versões zeradas, sem time, sem entitlements, PrivacyInfo fora do bundle).

Purpose: hoje cada recriação de `web/ios` (clone novo, `--recriar-ios`, projeto corrompido)
exige editar pbxproj em python e lembrar build/versão de cabeça; `ios-bump-build.sh` fez
0->1 em silêncio no projeto quebrado. A versão pública e o build passam a ter fonte
versionada no repo e a reaplicação vira um script idempotente com guardião na suíte.

Output: `resources/ios/versao.env`, `scripts/ios-aplicar-projeto.sh`, fixture + guardião
`web/tests/test_ios_aplicar_projeto.mjs`, os 5 scripts iOS ligados ao novo fluxo,
TESTFLIGHT.md seções 1/5 atualizadas.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@scripts/instalar-iphone.sh
@scripts/setup-ios.sh
@scripts/ios-bump-build.sh
@scripts/ios-testflight.sh
@scripts/ios-restaurar-entitlements.sh
@TESTFLIGHT.md

NÃO ler `web/.env.local` (segredos), `.planning/STATE.md`, `.planning/PROJECT.md`.
Não usar `git stash`. Não chamar os mutadores `gsd-sdk state.*`.

<facts>
<!-- Medido pelo planner em 2026-10-22; o executor não precisa redescobrir. -->

Template que `npx cap add ios` usa: `web/node_modules/@capacitor/cli/assets/ios-spm-template.tar.gz`
(extrai em `App/App.xcodeproj/project.pbxproj`, 14491 bytes, e `App/App/Info.plist`).
No template PRISTINO:
- tem `/* Begin PBXNativeTarget section */` e `isa = PBXNativeTarget;`
- `CURRENT_PROJECT_VERSION = 1;` e `MARKETING_VERSION = 1.0;` nas 2 configs do target
- NÃO tem `DEVELOPMENT_TEAM`, NÃO tem `CODE_SIGN_ENTITLEMENTS` (o comentário de
  `ios-restaurar-entitlements.sh` que diz que o cap add já referencia o entitlements está
  errado para o Capacitor 8 atual — por isso o pbxproj ficou sem ele)
- `PRODUCT_BUNDLE_IDENTIFIER = com.getcapacitor.App;` (o cap sync troca pelo appId do
  capacitor.config.ts)
- Info.plist: `CFBundleDisplayName` = "My App", `CFBundleName` = `$(PRODUCT_NAME)`;
  `CFBundleShortVersionString` = `$(MARKETING_VERSION)`, `CFBundleVersion` = `$(CURRENT_PROJECT_VERSION)`
  (logo as versões vivem SÓ no pbxproj; não escrever versão no Info.plist).

Estado alvo (copiado do web/ios local consertado à mão hoje, que arquivou o build 35):
- Configs do target = os 2 blocos `XCBuildConfiguration` cujo `buildSettings` contém
  `INFOPLIST_FILE = App/Info.plist;` (IDs no template: `504EC3171FED79650016851F /* Debug */`,
  `504EC3181FED79650016851F /* Release */`). As 2 configs do PROJETO (sem INFOPLIST_FILE)
  não recebem as chaves. Indentação das chaves: 4 tabs; ordem alfabética do Xcode.
- Em cada config do target: `CODE_SIGN_ENTITLEMENTS = App/App.entitlements;`,
  `CURRENT_PROJECT_VERSION = 35;`, `DEVELOPMENT_TEAM = LC65399YC9;`, `MARKETING_VERSION = 2.0;`
- PrivacyInfo (IDs fixos, já usados no projeto local):
  - seção PBXBuildFile: `\t\t465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */ = {isa = PBXBuildFile; fileRef = 465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */; };`
  - seção PBXFileReference: `\t\t465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */ = {isa = PBXFileReference; lastKnownFileType = text.xml; path = PrivacyInfo.xcprivacy; sourceTree = "<group>"; };`
  - grupo `504EC3061FED79650016851F /* App */` (o PBXGroup com `path = App;`), em `children`:
    `\t\t\t\t465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */,`
  - `PBXResourcesBuildPhase` (bloco `504EC3021FED79650016851F /* Resources */`), em `files`:
    `\t\t\t\t465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */,`
- Info.plist local: `CFBundleName` e `CFBundleDisplayName` = `Boris+`.
- `/usr/bin/perl` existe (usar perl para editar o pbxproj — já é o padrão de setup-ios.sh;
  não depender do python3 do usuário). `/usr/libexec/PlistBuddy` para o Info.plist.
- A suíte web roda cada `web/tests/*.mjs` com cwd = `web/` (`scripts/executar.sh` linha ~33).
- Caminhos da fixture não são gitignored (conferido com `git check-ignore`).
</facts>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Fonte de versão + ios-aplicar-projeto.sh + fixture + guardião</name>
  <files>resources/ios/versao.env, scripts/ios-aplicar-projeto.sh, web/tests/fixtures/ios-projeto/App/App.xcodeproj/project.pbxproj, web/tests/fixtures/ios-projeto/App/App/Info.plist, web/tests/test_ios_aplicar_projeto.mjs</files>
  <behavior>
    - T1 fixture pristina -> exit 0; nas configs do target cada uma das 4 chaves aparece com o valor esperado (contagem == 2 para cada linha exata `DEVELOPMENT_TEAM = LC65399YC9;`, `CODE_SIGN_ENTITLEMENTS = App/App.entitlements;`, `CURRENT_PROJECT_VERSION = <versao.env>;`, `MARKETING_VERSION = <versao.env>;`); `CURRENT_PROJECT_VERSION = 1;` e `MARKETING_VERSION = 1.0;` somem; as 2 configs do PROJETO não ganham `DEVELOPMENT_TEAM`
    - T2 PrivacyInfo: `465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */` aparece 2x (definição + fase Resources), `465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */` aparece 3x (fileRef no buildfile + definição + filho do grupo); arquivo `App/App/PrivacyInfo.xcprivacy` existe e é idêntico a `resources/ios/PrivacyInfo.xcprivacy`
    - T3 Info.plist: CFBundleName e CFBundleDisplayName = `Boris+` (checar por regex `<key>CFBundleName</key>\s*<string>Boris\+</string>`)
    - T4 linha `PRODUCT_BUNDLE_IDENTIFIER = com.alexandrecamerini.bolsia;` idêntica antes/depois (bundle id intocado)
    - T5 segunda execução -> project.pbxproj e Info.plist byte-idênticos à primeira
    - T6 fixture com a seção PBXNativeTarget removida (o teste remove de `/* Begin PBXNativeTarget section */` a `/* End PBXNativeTarget section */` na cópia em tmp) -> exit != 0, saída contém `--recriar-ios`, pbxproj byte-idêntico ao de antes
    - T7 PrivacyInfo já referenciado com OUTROS IDs (o teste insere na cópia, nas 4 posições, IDs `AAAAAAAAAAAAAAAAAAAAAAAA`/`BBBBBBBBBBBBBBBBBBBBBBBB` simulando o arrasto no Xcode) -> exit 0 e nenhum `465BE8A` inserido (não duplica)
    - T8 versao.env inválido (via `--versao-file` apontando para tmp com `CURRENT_PROJECT_VERSION=abc`) -> exit != 0 e pbxproj intocado
    - T9 ios-dir inexistente -> exit != 0 com mensagem PT-BR
    - Skip: se `process.platform !== 'darwin'` ou `/usr/libexec/PlistBuddy` ausente, imprime `SKIP` e sai 0
  </behavior>
  <action>
    RED primeiro: criar a fixture e o teste, rodar e ver falhar (script ainda não existe); depois GREEN.

    Fixture: extrair `web/node_modules/@capacitor/cli/assets/ios-spm-template.tar.gz` em `$TMPDIR` e copiar `App/App.xcodeproj/project.pbxproj` e `App/App/Info.plist` para `web/tests/fixtures/ios-projeto/` mantendo o layout `App/...`. Única alteração na cópia: `PRODUCT_BUNDLE_IDENTIFIER = com.getcapacitor.App;` -> `com.alexandrecamerini.bolsia` (simula o pós-cap-sync). Nada mais (fixture representa o pristino: build 1, versão 1.0, sem time/entitlements/PrivacyInfo). Não copiar o resto do template.

    `resources/ios/versao.env`: formato KEY=VALUE com comentários `#`. Conteúdo: `MARKETING_VERSION=2.0` e `CURRENT_PROJECT_VERSION=35` (último build enviado ao App Store Connect, 2026-10-22). Cabeçalho (comentário) documentando, alinhado ao guardrail "três esquemas de versão" do CLAUDE.md: MARKETING_VERSION é a versão PÚBLICA (App Store) e sobe junto com o `version` dos package.json (raiz/web/web-admin) na cadência que o Alex decidir — edição manual, nenhum script altera package.json nem lê um do outro; CURRENT_PROJECT_VERSION é o último build enviado, só `ios-bump-build.sh` incrementa, e o valor commitado deve ser o do último upload (commit junto do archive); nenhum dos dois tem relação com BUILD_ID/SERVER_BUILD_ID nem com tag git. Arquivo é lido por parse (grep/sed), NUNCA por `source`.

    `scripts/ios-aplicar-projeto.sh` (bash 3.2, `set -euo pipefail`, mensagens ASCII-safe no estilo de setup-ios.sh; comentários podem ter acento como os outros scripts iOS, mas strings impressas sem acento evitam problema de locale — siga o setup-ios.sh). Opções: `--ios-dir DIR` (default `$REPO/web/ios`), `--versao-file FILE` (default `$REPO/resources/ios/versao.env`), `--sem-verificar` (pula xcodebuild), `-h|--help`. Constantes no script: `TEAM=LC65399YC9`, `ENTITLEMENTS=App/App.entitlements`, `NOME=Boris+`, IDs fixos do PrivacyInfo do bloco facts. Fluxo, nesta ordem, com toda validação ANTES de qualquer escrita:
    1. Validar entrada: ios-dir existe; pbxproj e Info.plist existem; versao.env existe e MARKETING_VERSION casa `^[0-9]+(\.[0-9]+){1,2}$` e CURRENT_PROJECT_VERSION casa `^[1-9][0-9]*$`; PlistBuddy e perl presentes. Qualquer falha -> `die` PT-BR, exit 1.
    2. Guard do incidente: se o pbxproj não contém `isa = PBXNativeTarget;`, die com mensagem PT-BR explícita: projeto iOS corrompido (sem target nativo, mesmo sintoma de 2026-10-22), nada foi alterado, rode `bash scripts/instalar-iphone.sh --recriar-ios`. Idem (mesma mensagem) se não houver nenhum bloco XCBuildConfiguration com `INFOPLIST_FILE = App/Info.plist;`.
    3. Editar o pbxproj com UM programa perl (`perl -0777`, valores passados por variável de ambiente, não interpolados no código) escrevendo num arquivo temporário ao lado; só substitui o original (mv) se o perl saiu 0, e só se o conteúdo mudou (cmp) — garante byte-identidade e mtime estável no 2º run. Dentro do perl: (a) para cada bloco XCBuildConfiguration cujo buildSettings contém `INFOPLIST_FILE = App/Info.plist;`, para cada uma das 4 chaves: se existe a linha, troca o valor; se não existe, insere `\t\t\t\tCHAVE = VALOR;` na posição alfabética entre as chaves de 4 tabs do bloco (ou, mais simples e aceitável, logo após `buildSettings = {` — o importante é ser determinístico e idempotente); contar configs alteráveis e falhar (exit != 0 do perl) se 0. (b) PrivacyInfo: se já existe uma entrada `PrivacyInfo.xcprivacy in Resources` dentro do bloco PBXResourcesBuildPhase E uma PBXFileReference com `path = PrivacyInfo.xcprivacy`, não toca (cobre o arrasto manual com outros IDs). Senão, se o pbxproj menciona `PrivacyInfo.xcprivacy` de forma parcial com IDs que não são os fixos, falhar com mensagem pedindo revisão manual (não adivinhar). Senão, inserir cada uma das 4 linhas do bloco facts que estiver faltando (checar cada uma pelo ID+comentário): buildfile antes de `/* End PBXBuildFile section */`, fileref antes de `/* End PBXFileReference section */`, filho no fim de `children = (` do PBXGroup com `path = App;`, e no fim de `files = (` do PBXResourcesBuildPhase; antes de inserir, garantir que os IDs fixos não estão em uso por outro objeto. Nunca escrever PRODUCT_BUNDLE_IDENTIFIER.
    4. Copiar `resources/ios/PrivacyInfo.xcprivacy` para `<ios-dir>/App/App/PrivacyInfo.xcprivacy` só se `cmp -s` disser que difere (referência sem arquivo quebra o build).
    5. Info.plist: para CFBundleName e CFBundleDisplayName, ler com `PlistBuddy -c Print`; só fazer Set (ou Add string se ausente) quando o valor difere de `Boris+` — evita reserialização no 2º run.
    6. Se `App.entitlements` não existe em `<ios-dir>/App/App/`, apenas avisar (warn) que o build vai falhar e apontar `bash scripts/ios-restaurar-entitlements.sh` — não criar aqui (é responsabilidade daquele script; os chamadores o rodam antes).
    7. Verificação: sem `--sem-verificar` e com `xcodebuild` no PATH, rodar `xcodebuild -project <ios-dir>/App/App.xcodeproj -target App -configuration Release -showBuildSettings -disableAutomaticPackageResolution` e conferir as 4 chaves; divergência -> die; se o próprio xcodebuild falhar (SPM/rede), só warn "nao consegui verificar" (degradação, não falso positivo). Imprimir resumo `[OK] time=... entitlements=... versao=... build=... PrivacyInfo=referenciado nome=Boris+`.

    Guardião `web/tests/test_ios_aplicar_projeto.mjs` no padrão dos outros `.mjs` (Node puro, `node:assert`, `node:child_process` spawnSync, `node:fs`, `node:os`): cada caso copia a fixture para um dir novo em `os.tmpdir()` (`fs.cpSync` recursivo) e roda `bash ../scripts/ios-aplicar-projeto.sh --ios-dir <tmp> --sem-verificar` (cwd = web/). Lê os valores esperados parseando `../resources/ios/versao.env` (não hardcodar 35). Cobre T1-T9 do `<behavior>`. Remove os tmp no final. Um bloco de comentário no topo explica o incidente de 2026-10-22 (por que o guardião existe — guardião não se apaga).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_ios_aplicar_projeto.mjs && bash -n ../scripts/ios-aplicar-projeto.sh && git -C .. diff --quiet -- web/tests/fixtures/ios-projeto || echo "fixture alterada pelo teste"</automated>
  </verify>
  <done>Teste passa com T1-T9; a fixture commitada não é alterada pela execução do teste; `bash -n` limpo; o script não contém `source` do versao.env nem escrita de PRODUCT_BUNDLE_IDENTIFIER (`grep -v '^\s*#' scripts/ios-aplicar-projeto.sh | grep -c PRODUCT_BUNDLE_IDENTIFIER` só em leitura/aviso, nunca em substituição).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Ligar o fluxo — instalar-iphone, setup-ios, ios-bump-build, ios-testflight, restaurar-entitlements</name>
  <files>scripts/instalar-iphone.sh, scripts/setup-ios.sh, scripts/ios-bump-build.sh, scripts/ios-testflight.sh, scripts/ios-restaurar-entitlements.sh, web/tests/test_ios_aplicar_projeto.mjs</files>
  <behavior>
    - B1 bump na fixture pós-aplicar com versao.env tmp (CURRENT_PROJECT_VERSION=35) -> exit 0, versao.env tmp passa a 36, pbxproj tmp tem `CURRENT_PROJECT_VERSION = 36;` 2x
    - B2 bump com argumento explícito menor/igual ao atual (ex. `35`) -> exit != 0, versao.env intocado
    - B3 bump numa cópia sem nenhuma linha CURRENT_PROJECT_VERSION -> exit != 0, versao.env intocado (nunca 0->1)
    - B4 bump numa cópia sem PBXNativeTarget -> exit != 0, saída contém `--recriar-ios`, versao.env intocado
    - S1 estático: instalar-iphone.sh, setup-ios.sh e ios-testflight.sh chamam `ios-aplicar-projeto.sh` (linhas não comentadas); ios-testflight.sh não contém mais "arraste"; ios-bump-build.sh referencia `versao.env` e não contém `|| echo 0`
    - S2 estático: em instalar-iphone.sh a chamada do aplicar vem DEPOIS de `cap sync ios` e de `ios-patch-appdelegate.sh`; em setup-ios.sh vem DEPOIS de `ios-restaurar-entitlements.sh` e do bloco de cap add/sync
  </behavior>
  <action>
    Adicionar os casos B1-B4 e S1-S2 ao mesmo `web/tests/test_ios_aplicar_projeto.mjs` (RED), depois implementar:

    `scripts/ios-bump-build.sh` (reescrever): aceitar `--ios-dir DIR` e `--versao-file FILE` (mesmos defaults do aplicar, para o teste) e o argumento posicional opcional N (como hoje). Ordem: (1) validar pbxproj existe; tem `isa = PBXNativeTarget;` senão die com a mesma mensagem do incidente apontando `bash scripts/instalar-iphone.sh --recriar-ios`; tem `CURRENT_PROJECT_VERSION = ` senão die PT-BR dizendo que o projeto está sem a chave e para rodar `bash scripts/ios-aplicar-projeto.sh` (remover o `|| echo 0`). (2) Ler CUR de versao.env (parse, validar inteiro); ler também o maior CURRENT_PROJECT_VERSION do pbxproj; base = max dos dois (avisar se divergem). (3) NEW = N ou base+1; NEW > base senão die. (4) Escrever um versao.env temporário (cópia com só a linha CURRENT_PROJECT_VERSION trocada, preservando comentários) e rodar `ios-aplicar-projeto.sh --ios-dir ... --versao-file <tmp>` repassando `--sem-verificar` se recebido; só se o aplicar sair 0, `mv` o tmp sobre o versao.env real (atômico: falha não deixa a fonte adiantada). (5) Imprimir `[OK] build: CUR -> NEW (versao publica MARKETING_VERSION=X)` + lembrete: commitar `resources/ios/versao.env` junto do upload, e que MARKETING_VERSION se edita à mão em versao.env (na cadência do Alex, junto com package.json). Manter o cabeçalho de uso atualizado.

    `scripts/instalar-iphone.sh`: substituir o passo 7 (que só setava CFBundleDisplayName via PlistBuddy) por "7) Projeto iOS: identidade, versao, time, entitlements, PrivacyInfo" chamando `bash "$ROOT/scripts/ios-aplicar-projeto.sh" || die "..."` (mensagem PT-BR: sem isso o archive falha ou sai com build/versão errados). Posição: depois do `ios-patch-appdelegate.sh` (o entitlements já foi garantido no passo 5). Comentário curto com o incidente de 2026-10-22. Atualizar a frase do bloco PASSOS FINAIS só se mencionar algo agora falso.

    `scripts/setup-ios.sh` (ASCII puro, bash 3.2, `${VAR:-}` — manter o estilo do arquivo): depois de `ok "iOS pronto."` e das chamadas allow-http/uiscene, garantir entitlements (se `ios/App/App/App.entitlements` não existe, `bash "$SCRIPT_DIR/ios-restaurar-entitlements.sh" || die ...` — necessário porque o aplicar passa a apontar CODE_SIGN_ENTITLEMENTS para esse arquivo e sem ele o build quebra), e então `bash "$SCRIPT_DIR/ios-aplicar-projeto.sh" --ios-dir "$WEB/ios" || die ...`. Atualizar a mensagem final ("selecione seu Time") para dizer que o time ja vem aplicado (LC65399YC9). Não mexer em `--app-id` nem no appId.

    `scripts/ios-testflight.sh`: trocar o bloco 1 (cp do PrivacyInfo + if/else com a instrução manual de arrastar) por `bash "$REPO/scripts/ios-aplicar-projeto.sh" || exit 1` com `[OK]` correspondente; manter checagem de `SRC_PRIVACY` e os passos 2 e 3 como estão.

    `scripts/ios-restaurar-entitlements.sh`: corrigir só o comentário do cabeçalho (o `cap add ios` do Capacitor 8 NÃO escreve CODE_SIGN_ENTITLEMENTS no pbxproj — medido em 2026-10-22 no template) e o warn final do pbxproj, que passa a apontar `bash scripts/ios-aplicar-projeto.sh` em vez do passo manual no Xcode. Lógica intocada.

    Rodar `bash -n` nos 5 scripts.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_ios_aplicar_projeto.mjs && for s in instalar-iphone setup-ios ios-bump-build ios-testflight ios-restaurar-entitlements ios-aplicar-projeto; do bash -n ../scripts/$s.sh || exit 1; done && LC_ALL=C grep -n '[^ -~	]' ../scripts/setup-ios.sh | grep -v '^[0-9]*:#' | head -5</automated>
  </verify>
  <done>Guardião passa com T1-T9 + B1-B4 + S1-S2; `bash -n` limpo nos 6 scripts; nenhuma linha nova não-ASCII fora de comentário em setup-ios.sh (comparar com `git diff` — linhas não-ASCII pré-existentes não contam); `git status` mostra resources/ios/versao.env ainda com 35 (o teste nunca escreve no real).</done>
</task>

<task type="auto">
  <name>Task 3: Docs + verificação real no web/ios local</name>
  <files>TESTFLIGHT.md, CLAUDE.md</files>
  <action>
    TESTFLIGHT.md seção 1: o item 3 (ação única de arrastar o PrivacyInfo no Xcode) deixa de existir — substituir por: `ios-testflight.sh`/`instalar-iphone.sh`/`setup-ios.sh` rodam `scripts/ios-aplicar-projeto.sh`, que reaplica time LC65399YC9, entitlements, MARKETING_VERSION/CURRENT_PROJECT_VERSION de `resources/ios/versao.env`, PrivacyInfo no grupo App + Resources e nome Boris+; idempotente; se acusar "sem target nativo", o projeto está corrompido -> `bash scripts/instalar-iphone.sh --recriar-ios`. Seção 5 item 11: `ios-bump-build.sh` incrementa em `resources/ios/versao.env` e aplica no projeto; commitar o versao.env junto do upload; falha (em vez de fazer 0->1) se o projeto estiver quebrado. Mencionar que a versão pública se muda editando MARKETING_VERSION em versao.env, na mesma cadência do package.json (decisão do Alex). Atualizar a tabela "Referência rápida dos scripts" com `ios-aplicar-projeto.sh` e `resources/ios/versao.env`; a frase final que diz que `instalar-iphone.sh` não tem relação com distribuição pode ficar, mas sem contradizer o novo fluxo.

    CLAUDE.md: no guardrail "Três esquemas de versão", item (3), acrescentar só a referência de onde a versão iOS vive agora: `MARKETING_VERSION` (e o build number) ficam em `resources/ios/versao.env`, aplicados por `scripts/ios-aplicar-projeto.sh`, porque `web/ios/` é gitignored. Uma frase; não reescrever o guardrail.

    Verificação real (não destrutiva): copiar `web/ios/App/App.xcodeproj/project.pbxproj` e `web/ios/App/App/Info.plist` para o scratchpad/`$TMPDIR` como backup; registrar `shasum` dos dois; rodar `bash scripts/ios-aplicar-projeto.sh` (SEM `--sem-verificar`, para exercitar o xcodebuild -showBuildSettings) no web/ios real — o projeto já está no estado alvo, então o pbxproj deve sair byte-idêntico; comparar shasum. Se o Info.plist mudou só por serialização, registrar no SUMMARY. Se xcodebuild só emitiu warn de não-verificação, registrar no SUMMARY. Se o sandbox bloquear o xcodebuild, registrar e seguir (não usar dangerouslyDisableSandbox para isso). Depois, `npx vite build` não é necessário (não tocou web/src). Rodar `node tests/test_ios_aplicar_projeto.mjs` uma última vez a partir de `web/`. A suíte canônica fica com o orquestrador.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && grep -q "ios-aplicar-projeto.sh" TESTFLIGHT.md && grep -q "versao.env" TESTFLIGHT.md && ! grep -qi "arraste" TESTFLIGHT.md && grep -q "resources/ios/versao.env" CLAUDE.md && (cd web && node tests/test_ios_aplicar_projeto.mjs)</automated>
  </verify>
  <done>TESTFLIGHT.md sem a instrução manual de arrastar, com o novo fluxo nas seções 1 e 5 e na tabela; CLAUDE.md com a referência de uma frase; execução no web/ios real deixou o pbxproj byte-idêntico (shasum antes = depois) e o resultado do xcodebuild está registrado no SUMMARY.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| repo -> web/ios (gitignored) | scripts escrevem num projeto local não versionado que vira o binário publicado |
| versao.env -> perl/pbxproj | valores de arquivo versionado entram num arquivo de projeto |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-rht-01 | Tampering | ios-aplicar-projeto.sh lendo versao.env | mitigate | parse por grep/sed com regex estrita (versão `^[0-9]+(\.[0-9]+){1,2}$`, build `^[1-9][0-9]*$`), nunca `source`; valores passados ao perl por env, não interpolados no código |
| T-rht-02 | Tampering | pbxproj real | mitigate | toda validação antes de escrever; escrita em tmp + mv só em sucesso e só se mudou; projeto sem PBXNativeTarget -> falha sem alterar |
| T-rht-03 | Tampering | bundle id | mitigate | nenhum script escreve PRODUCT_BUNDLE_IDENTIFIER; teste T4 trava |
| T-rht-04 | Denial of service | ios-bump-build.sh | mitigate | versao.env só é substituído após o aplicar sair 0 (tmp + mv); B2-B4 travam |
| T-rht-05 | Information disclosure | web/.env.local | accept | não é lido; DEVELOPMENT_TEAM é identificador público (já em TESTFLIGHT.md), não segredo |
</threat_model>

<verification>
- `cd web && node tests/test_ios_aplicar_projeto.mjs` verde (T1-T9, B1-B4, S1-S2)
- `bash -n` limpo nos 6 scripts iOS
- web/ios real: pbxproj byte-idêntico após aplicar; resultado do `xcodebuild -showBuildSettings` registrado
- `resources/ios/versao.env` commitado com MARKETING_VERSION=2.0 e CURRENT_PROJECT_VERSION=35
- Suíte canônica `bash scripts/executar.sh --testes`: orquestrador, fora do executor
</verification>

<success_criteria>
- Recriar web/ios (`instalar-iphone.sh --recriar-ios` ou `setup-ios.sh --reset`) resulta em projeto arquivável sem edição manual de pbxproj nem passo no Xcode para time/entitlements/versão/PrivacyInfo
- Projeto corrompido é detectado com mensagem acionável em vez de seguir silencioso
- O próximo `ios-bump-build.sh` produz build 36 a partir da fonte versionada
</success_criteria>

<output>
Create `.planning/quick/261022-rht-instalar-iphone-e-setup-ios-reaplicam-ve/261022-rht-SUMMARY.md` when done
</output>
