---
quick_id: 261022-rht
status: complete
commits: [8565273c, 2691c97c, task3-docs]
---

# Quick 261022-rht: instalar-iphone e setup-ios reaplicam versao/time/entitlements/PrivacyInfo

Criado `scripts/ios-aplicar-projeto.sh` (idempotente, perl + PlistBuddy, parse estrito de `resources/ios/versao.env`, falha acionavel em projeto sem PBXNativeTarget) e ligado a instalar-iphone, setup-ios, ios-testflight e ios-bump-build (que agora incrementa em versao.env e nunca faz 0->1).

## Testes
`node web/tests/test_ios_aplicar_projeto.mjs` OK (T1-T9, B1-B4, S1-S2). Guardioes que tocam os scripts: test_ios_open_target, test_qa20_appstore, test_radar, test_push_wiring OK. `bash -n` limpo nos 6 scripts.

## Verificacao no web/ios real
shasum antes = depois (pbxproj 6a3e1359..., Info.plist c0ab568e...), xcodebuild -showBuildSettings confirmou as 4 chaves (fora do sandbox).

## Deviations
- [Achado] web/ios real esta em CURRENT_PROJECT_VERSION=36, enquanto versao.env (conforme plano) diz 35. Rodar o aplicar com o versao.env real mudaria o pbxproj para 35 (aconteceu uma vez; restaurado do backup). A verificacao byte-identica usou `--versao-file` temporario com 36. Decisao pendente: ajustar versao.env para o ultimo build realmente enviado.
- [Rule 1] Primeira versao do perl usava s{}{}e com chaves nao escapadas (warnings); refatorado para sub `ajusta`.
- Task 1 commitada com o bloco B do guardiao desligado (bump antigo ainda existia); reativado no commit da Task 2.
