# Correção — LLM no iPhone / URL do backend Railway

## Problema
Na instalação iOS, o usuário executou:

```bash
bash scripts/setup-ios.sh --api-base b3-production-8fc0.up.railway.app --app-id com.acamerini.b3agente
```

Sem protocolo, a URL podia ser embutida no build como string ambígua. Em WebView/iOS isso pode gerar chamadas relativas ao próprio app ou HTTP incorreto, fazendo chamadas de LLM falharem no iPhone mesmo funcionando na web.

## Correção aplicada

### `web/src/api.js`
- `VITE_API_BASE` agora é normalizado no carregamento do app.
- `setApiBase()` também normaliza qualquer valor salvo nas preferências locais do iPhone.
- Regra:
  - `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`, `127.x.x.x` e `localhost` => `http://`
  - domínios públicos como `b3-production-8fc0.up.railway.app` => `https://`
- Remove barra final e `/api` duplicado.

### `scripts/setup-ios.sh`
- `--api-base` agora é normalizado antes do `npm run build`.
- Exemplo sem protocolo agora vira automaticamente:

```text
https://b3-production-8fc0.up.railway.app
```

## Testes

```bash
node web/tests/test_api_parity.mjs
# 5 testes de paridade do cliente HTTP: TODOS PASSARAM

cd server && python -m pytest -q
# 45 passed
```

## Comando recomendado

```bash
bash scripts/setup-ios.sh \
  --api-base https://b3-production-8fc0.up.railway.app \
  --app-id com.acamerini.b3agente \
  --reset
```

Depois, no app iPhone, valide em Perfil / Conta & preferências:

```text
Servidor/API = https://b3-production-8fc0.up.railway.app
```

E toque em **Testar conexão**.
