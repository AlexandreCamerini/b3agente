# QA iOS — IA, erros acionáveis e notificações

## Correções aplicadas

1. **Erros de IA agora são diagnósticos acionáveis**
   - Backend retorna `detail` estruturado com `message`, `provider`, `model`, `keySource`, `action`, `hint` e `code`.
   - Frontend preserva essas informações e mostra ao usuário o que corrigir.
   - Coberto por teste unitário backend e teste de paridade do cliente HTTP.

2. **Configurações recebeu Diagnóstico QA completo**
   - Novo botão: `Rodar diagnóstico completo`.
   - Testa `/api/health`, `/api/config/test` e plugin/permissão de notificações.
   - Gera relatório copiável para debug.

3. **Notificações locais iOS revisadas**
   - Botão explícito `Pedir permissão`.
   - Teste de notificação agenda o disparo e instrui colocar o app em segundo plano.
   - `capacitor.config.ts` inclui `LocalNotifications.presentationOptions = ["alert", "sound", "badge"]`.

4. **Cliente HTTP mais robusto**
   - Erro HTTP com objeto JSON é formatado com detalhes humanos.
   - Evita erro genérico de `JSON.parse`/HTML no WebView.
   - Mantém exigência de URL absoluta no iPhone.

## Validação executada

- Backend: `46 passed`
- Cliente HTTP/iOS: `6 testes de paridade: TODOS PASSARAM`

## Observações para teste no iPhone

- API base precisa ser absoluta, exemplo: `https://b3-production-8fc0.up.railway.app`.
- Se `keySource=manual`, a chave deve ser salva no próprio iPhone.
- Se permissão iOS estiver `denied`, só o usuário consegue reativar em Ajustes → Notificações → B3 Agente.
- Após alterar plugin de notificação, rodar `npm install && npx cap sync ios` e reinstalar pelo Xcode.
