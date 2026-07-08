# QA 25 — FASE 8B: rodada de garantia (R1–R5) · build F8B-20260709-3
*09/07/2026 · 19 suítes backend + 21 web, 0 falhas*

## R1 — Notificações "regrediram" (deadlock pós-reinstalação)
- **Mecânica do problema:** ao REINSTALAR o app, o iOS pode reportar permissão
  "denied" herdada e o BolsIA some de Ajustes → Notificações até um NOVO
  requestPermissions. Nossa central só mostrava "Pedir permissão" no estado
  `default` — com "denied" restava "Abrir Ajustes", onde o app nem aparecia:
  beco sem saída (a regressão percebida).
- **Fix:** "Pedir permissão" disponível SEMPRE que não concedida (default E
  denied — pedir com denied é inofensivo e re-registra o app em Ajustes);
  diagnóstico orienta "toque em Pedir permissão PRIMEIRO após reinstalar".
- Conferido: `capacitor.config.json` sincronizado está correto (banner/list);
  guardião novo tranca a PARIDADE entre o config-fonte e o sincronizado.
- **No aparelho:** central → Pedir permissão → conceder → o BolsIA volta a
  aparecer em Ajustes → Notificações e o toggle liga.

## R2 — Instrução do agente POR skill, selecionável pelo nome (pedido)
- Nova seção `skillOperador` ("Mesa B3 - Operador v1", texto de mesa) ao lado
  da `skill` educacional — defaults nos dois lados, backfill automático.
- A tela INSTRUÇÕES DO AGENTE ganhou seletor PELO NOME (dropdown com as duas
  skills + badge "EM USO no modo atual"); salvar/restaurar agem na selecionada.
- As análises usam automaticamente a skill do modo ativo (iOS envia a certa no
  corpo; web escolhe pela config do escopo; rota N2 seleciona por modo).

## R3 — Paleta fiel ao mock + modo inconfundível
- Override do Operador agora bate 1:1 com o mock aprovado: cards #10161a,
  negativo #ef4444, positivo = acento #22c55e, textos frios (#93a5ad/#5b6d75),
  tints recalculados; versão light coerente (#15803d).
- Chip "MODO OPERADOR" virou SÓLIDO (fundo verde, texto escuro, 10px) — não há
  como não saber onde se está.

## R4 — Fraseologia: vazamentos finais fechados
- REC_STYLE não tinha as decisões da mesa — o chip do N2 caía no cinza
  (COMPRAR/VENDER/AGUARDAR/NÃO OPERAR agora coloridos).
- Filtros da Watchlist ("Estudar alta/baixa" → "Compra/Venda" na mesa), nota
  do popup de stop/alvo, vazio do histórico e rodapés do Acompanhar/destaque —
  todos no copy.js (35 chaves espelhadas).

## R5 — E-mail real no login Apple (seu último ponto)
- **O que dá para fazer:** o relay é escolha de privacidade do usuário na
  Apple — nenhum app consegue LER o e-mail real por trás dele. O caminho é o
  usuário refazer o consentimento: iPhone → Ajustes → [seu nome] → Início de
  Sessão e Segurança → Iniciar Sessão com a Apple → BolsIA → "Parar de Usar o
  ID Apple" → entrar de novo no app escolhendo **"Compartilhar Meu E-mail"**.
- **Bug nosso corrigido para esse fluxo funcionar:** o servidor NÃO atualizava
  o e-mail de conta existente no relogin — mesmo compartilhando o real, o app
  seguiria mostrando o relay. `upsert_oauth_user` agora atualiza o e-mail
  quando o novo login traz um diferente (respeitando o UNIQUE — colisão mantém
  o atual). Teste `test_oauth_atualiza_email_ao_recompartilhar` cobre os dois
  ramos. Lembrete: o modal da conta já explica esse caminho para o usuário.

## Instalação (a causa provável do relato) — checklist obrigatório
```bash
bash operar.sh deploy "F8B-3 rodada de garantia"
cd web && npm install && npm run ios     # npm install ANTES (dependências novas)
# Xcode: Product → Clean Build Folder → Run
```
**Confirme `build F8B-20260709-3` no rodapé do Perfil ANTES de testar.**
Se o carimbo for outro, o aparelho está com build antigo — nada desta (ou da
anterior) entrega estará visível.

## Hard stop
1. Carimbo `F8B-20260709-3` no Perfil.
2. Notificações: Pedir permissão → app reaparece em Ajustes → toggle liga →
   teste agendado 30s com app fechado entrega banner.
3. Operador: paleta idêntica ao mock, chip sólido, gráficos verdes, filtros
   "Compra/Venda", chip do N2 colorido com a decisão.
4. Skills: seletor pelo nome mostra as duas; editar/salvar/restaurar cada uma;
   análise no modo operador responde com a voz da skill de mesa.
5. Apple e-mail real: refazer consentimento (caminho acima) → relogar → o
   perfil passa a mostrar o e-mail verdadeiro.
