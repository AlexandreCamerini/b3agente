# ATUALIZAR — Git · Railway · iOS
## Entrega FASE 6 + FASE 7.1: correções finais + Modo Operador (fundação)
*08/07/2026 · detalhes em `qa/19-fase6-correcoes.md` e `qa/20-fase7-1-modo-operador.md`*

> **FASE 7.1 (aprovada por você) incluída nesta entrega:** seletor Estudo ↔
> Operador no Perfil com Termo de Responsabilidade; Radar no modo operador com
> decisão direta (COMPRAR/VENDER/AGUARDAR/NÃO OPERAR), plano completo
> (entrada · stop na invalidação · alvo 1/alvo final · R:R com corte em 1,5:1)
> e posição sugerida por % de risco. Tudo determinístico (setups.py), Estudo
> intocado, sem IA nova. Hard stop adicional no item 6 do roteiro.

## O que mudou nesta entrega

1. **Servidor FIXO (fix 1):** o app nativo agora nasce apontado para a
   produção do Railway — login, cotações e IA funcionam de fábrica, sem
   digitar servidor. O campo da Config virou "override de desenvolvimento"
   (vazio = produção) e vale para o aparelho inteiro (não se perde mais ao
   entrar/sair da conta).
2. **"Aprofundar com IA" legível (fix 2):** leitura truncada do modelo não
   vira mais texto quebrado — o app recupera o resumo, avisa que veio
   incompleta e oferece rodar de novo; resumo agora renderiza títulos, listas
   e parágrafos.
3. **"Ativar no servidor" funcionando (fix 3):** no iPhone o toggle do
   Operador nunca chegava ao backend (parâmetro descartado no store local) e a
   UI fingia sucesso. Agora é chamada confirmada: liga de verdade ou mostra o
   motivo exato.
4. **Central única de notificações (fix 4):** tudo em Perfil → Conta &
   preferências: permissão do sistema (com **Abrir Ajustes** quando o iOS já
   negou — ele só pergunta uma vez), avisos locais, push do servidor (ativar
   aparelho + testar) e diagnóstico. O Operador IA ganhou um atalho para lá.
   *Dependência nova: `@capacitor/app-launcher`.*
5. **Push — BadEnvironmentKeyInToken (fix 5):** o servidor agora traduz cada
   rejeição da Apple em instrução exata (esse reason = chave .p8 restrita a um
   ambiente ≠ do host em uso) e só descarta token quando o problema é do
   token. **Tem passo manual seu — item 3 abaixo.**
6. **Modo Operador (item 6 — GATE):** proposta em `PROPOSTA-MODO-OPERADOR.md`
   + mock em `qa/mocks/modo-operador.html`. Nada implementado — aguarda seu OK.

## 1) Validação local

```bash
cd web && npm install && cd ..     # dependência nova (app-launcher)
bash operar.sh testes              # 17 suítes backend + 17 web
```

## 2) Git + Railway

```bash
bash operar.sh deploy "FASE 6: servidor fixo + leitura IA + operador servidor + central de notificações + reasons APNs"
```

Variables (Railway): sem mudanças obrigatórias nesta entrega. Confira
`B3_ADMIN_EMAILS` (logs) e as APNs do item 3.

## 3) APNs — passo MANUAL (resolve o BadEnvironmentKeyInToken)

1. Portal Apple → Certificates, Identifiers & Profiles → **Keys** → sua chave
   APNs → confira o **Environment**. Se estiver restrita (só Development ou só
   Production), crie uma nova com **"Sandbox & Production"**, baixe o `.p8` e
   atualize `APNS_AUTH_KEY` + `APNS_KEY_ID` no Railway.
2. Regra do ambiente: build instalado pelo **Xcode** → `APNS_SANDBOX=1`;
   **TestFlight/App Store** → REMOVER a variável.
3. Depois do ajuste: app → central de notificações → "Testar push" — se ainda
   falhar, a mensagem agora diz exatamente o quê corrigir.

## 4) iOS — recompilar (exigido pelos fixes 1 e 4)

```bash
cd web && npm run ios     # build + cap sync (pega o app-launcher) + Xcode
```

Xcode: Product → Clean Build Folder → instalar no iPhone.

## 5) HARD STOP — roteiro de teste no aparelho

1. **Servidor/login:** apague o app, instale o build novo, abra SEM configurar
   nada → a Config deve mostrar "em uso agora: https://b3agente-production…" e
   o login por e-mail deve funcionar direto. Feche e reabra o app 2×: nada de
   recadastrar servidor.
2. **Leitura IA:** Radar → "Aprofundar com IA" em 2–3 ativos → texto com
   parágrafos/listas legíveis; se aparecer o aviso de leitura incompleta,
   rodar de novo deve completar.
3. **Operador no servidor:** aba Operador IA → "Ativar no servidor" → deve
   confirmar "ATIVADO ✓" e o status refletir; desligue e ligue de novo. Sem
   conta, deve pedir login com mensagem clara (não fingir sucesso).
4. **Central de notificações:** Perfil → Conta & preferências → central única.
   (a) permissão: se negada, botão "Abrir Ajustes →" leva direto ao app nos
   Ajustes; (b) "Testar agendada (30s)" com app fechado → banner chega;
   (c) "Ativar push neste aparelho" → "push ativo ✓"; (d) "Testar push" com o
   app em segundo plano → banner chega.
5. **APNs reason:** se o teste de push falhar, o Diário/central deve mostrar o
   reason + instrução exata (não mais o erro seco).
6. **Modo Operador (F7.1):** Perfil → "Modo de trabalho" → Operador → o termo
   deve exigir rolagem até o fim antes do aceite; ativado, o Radar mostra
   decisões diretas com plano (entrada/stop/alvos/R:R) e posição sugerida;
   ativos sem vantagem mostram "NÃO OPERAR" com o motivo. Voltar ao Estudo
   restaura tudo. Fechar e reabrir o app: o modo persiste e o termo não
   reaparece. F7.2 (IA no formato PRO) começa após este hard stop.

Qualquer item falhando: copie a linha dos "Logs do servidor" (Observabilidade)
ou do Diário que eu sigo o diagnóstico.
