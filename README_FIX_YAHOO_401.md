# Correção — erro 401 no Yahoo Finance em Opções

## Causa
O módulo de opções chamava diretamente `/v7/finance/options` sem reutilizar a sessão/cookie/crumb já implementada no provider de cotações. Em alguns ambientes o Yahoo responde 401/403/429 para esse endpoint não oficial.

## Correção
- `server/app/options_provider_yahoo.py` passou a reutilizar `_yfetch`, com sessão, crumb, retry e rotação query1/query2.
- Quando o Yahoo continuar bloqueando/indisponível, o backend retorna HTTP 200 com `providerStatus: "degraded"`, `calls: []`, `puts: []` e `warning` clara, em vez de vazar erro 401 para o app.
- `server/app/options_api.py` agora tolera falha temporária no contexto técnico do ativo objeto sem derrubar a cadeia de opções.
- Adicionado teste cobrindo o caso `Yahoo HTTP 401`.

## Validação
- Backend: `42 passed`
- Frontend build: `vite build` OK

## Observação de produto
Mesmo corrigido, Yahoo/yfinance continua sendo fonte não oficial para opções. Para produção em B3, manter o `OptionsProvider` plugável e evoluir para API especializada.
