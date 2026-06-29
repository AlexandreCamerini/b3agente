# Testes

## Backend

Comando:

```bash
cd server && pytest -q
```

Resultado:

```text
45 passed
```

Cobertura adicionada:

- `technical_models.build_context`
- envio de 120 candles para a LLM
- fallback de modelo inválido para `completo`
- compactação sem carregar candles para a UI
- normalização de plano educacional no parser de KPIs

## Frontend

Comando:

```bash
cd web && npm run build
```

Resultado:

```text
✓ built
```

## Cliente HTTP / iOS WebView

Comando:

```bash
cd web && node tests/test_api_parity.mjs
```

Resultado:

```text
5 testes de paridade do cliente HTTP: TODOS PASSARAM
```
