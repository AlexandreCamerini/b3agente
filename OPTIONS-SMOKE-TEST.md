# Smoke Test — B3 Agente Opções

1. Abrir o app web.
2. Acessar a aba `Opções`.
3. Buscar `AAPL` para validar provider Yahoo com cadeia de opções mais provável.
4. Confirmar que aparecem vencimentos, calls e puts.
5. Selecionar uma call com open interest.
6. Validar exibição de strike, bid/ask, IV, liquidez, score e gregos.
7. Confirmar que a análise educacional aparece sem recomendação direta.
8. Buscar `PETR4` ou outro ativo B3.
9. Se Yahoo não retornar opções, validar mensagem clara de indisponibilidade.
10. No iPhone, validar que a aba abre, usa o backend configurado e não quebra em resposta não JSON.
