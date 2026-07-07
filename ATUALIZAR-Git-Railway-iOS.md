# ATUALIZAR — Git · Railway · iOS
## Entrega FASE 4 "Fechamento" (parte 1): identidade + correções 1.1/1.3/1.4
*07/07/2026 · detalhes técnicos em `qa/15-fase4-correcoes.md`*

## O que mudou nesta entrega

1. **Identidade de produção (TRAVADA):** `appId com.alexandrecamerini.bolsia`
   · `appName BolsIA` — aplicada em config, PWA, disclaimers, scripts e
   backend por `scripts/atualizar-identidade.sh` (idempotente; `--verificar`
   só confere). Codinome interno `b3-agente` preservado.
2. **Venda corrigida (1.1):** `sellModal` faltava nas deps do `useMemo(A)` —
   "Confirmar venda" era no-op silencioso. Corrigido (+ `wlScanLoading`,
   `destaque`, `quotes`, mesma classe) e blindado por
   `web/tests/test_wiring_deps.mjs`.
3. **Radar 1x/dia (1.3):** varredura automática às 08:45 BRT em dia útil
   (novo `server/app/radar_daily.py`, dentro do scheduler existente),
   resultado do dia servido ao abrir a aba (chip com data/hora), botão
   "Varrer novamente" recomputa (`?force=1`), push opcional "Radar do dia
   pronto 📡". Ajustes: `B3_RADAR_DAILY_HHMM` (horário) e
   `B3_RADAR_DAILY_OFF=1` (desligar).
4. **Leitura da IA (1.4):** popup agora fecha (✕ no cabeçalho + rodapé fixo
   + tap fora) e rola de verdade sem travar a página; resumo aberto com
   "Leitura por setup"/"Cenários"/"Riscos" colapsáveis; prompt N1 com
   instrução de concisão (testada).

## 1) Git

```bash
# na raiz do repo local, com o zip extraído por cima:
bash scripts/subir-git.sh   # ou: git add -A && git commit -m "FASE 4: identidade BolsIA + venda + radar diário + leitura IA" && git push
```

## 2) Railway

```bash
bash scripts/atualizar-servidor.sh   # redeploy com o código novo
```

Variables (conferir):
- `APNS_TOPIC=com.alexandrecamerini.bolsia`  ← **novo valor (migração)**
- `APNS_TEAM_ID`, `APNS_KEY_ID`, `APNS_AUTH_KEY` (.p8 inteiro, com BEGIN/END)
- `APNS_SANDBOX=1` enquanto o build for pelo Xcode (remover em TestFlight)
- (opcionais) `B3_RADAR_DAILY_HHMM=08:45` · `B3_RADAR_DAILY_OFF` não setar

## 3) Migração de identidade — passos MANUAIS (uma vez)

1. **Portal Apple**: Certificates, Identifiers & Profiles → Identifiers →
   **+** → App IDs → App → Bundle ID *explícito*
   `com.alexandrecamerini.bolsia` → marcar **Push Notifications** e **Sign
   in with Apple** → Register.
2. **Railway**: `APNS_TOPIC=com.alexandrecamerini.bolsia` (acima).
3. **Nativo**: `bash scripts/setup-ios.sh` (regenera `web/ios/` com o novo
   appId via cap sync). No Xcode: Signing & Capabilities → Bundle Identifier
   `com.alexandrecamerini.bolsia` + Team + **+ Capability → Push
   Notifications**.
4. **Xcode**: Product → Clean Build Folder → instalar no iPhone.
5. **iPhone**: REMOVER o app antigo ("B3 Agente" — vira órfão com o bundle
   novo). Abrir o BolsIA e reativar o push (aba Operador IA → "Ativar push
   das ações") — tokens antigos são inválidos sob o novo bundle.
6. `bash scripts/atualizar-identidade.sh --verificar` → "IDENTIDADE OK ✅".

## 4) HARD STOP — roteiro de teste no aparelho

1. **Venda**: Portfólio → "Simular venda" → parcial (lote de 100) e depois
   total. Deve executar, atualizar posição/histórico/KPIs e mostrar o toast.
2. **Leitura da IA**: Radar → "Aprofundar com IA" → conferir resumo curto +
   seções colapsáveis → rolar até o fim → fechar por ✕, por "Fechar" e por
   tap fora (os três devem funcionar).
3. **Radar diário**: abrir a aba → resultado instantâneo com chip
   "Varredura automática de hoje · hh:mm" (na 1ª vez após o deploy, se ainda
   não houver passada do dia, a abertura computa e o chip mostra "manual") →
   "Varrer novamente" substitui o do dia. Na manhã seguinte (>08:45),
   conferir na Observabilidade o bloco `radarDiario` e o push "Radar do dia
   pronto 📡".
4. **Push**: Perfil → Observabilidade → "Testar push agora" — o Diário
   mostra sucesso ou o motivo EXATO (token/tópico/ambiente). Com a migração
   feita, `BadTopic` não deve mais ocorrer.

Qualquer item falhando: me traga o texto do Diário que eu sigo o diagnóstico.

## Próximo bloco (após o hard stop)
Bloco 2 — login Apple + Google (roteiro guiado) · Bloco 3 — auditoria QA +
checklist App Store (`qa/16`) · Bloco 4 — go-to-market.
