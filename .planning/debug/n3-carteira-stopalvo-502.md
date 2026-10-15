---
slug: n3-carteira-stopalvo-502
status: root-cause-narrowed
opened: 2026-10-14
---

# N3 `POST /api/carteira-stopalvo/{ticker}` → 502 em produção (4/4)

## Sintoma
14/10, 16:09–16:10 BRT: BRAP4, BPAC11, UGPA3, ITUB4, todas logo após `POST /api/buy`.
Config da conta: provider anthropic, model vazio (cai no fallback `claude-haiku-4-5`), keySource env.
O 502 vem do `except` em volta de `llm.analyze_carteira`; nada era registrado no servidor.

## Hipóteses
| # | Hipótese | Status | Evidência |
|---|---|---|---|
| H1 | ID `claude-haiku-4-5` aposentado ou inválido | REFUTADA | skill claude-api (models.md, cache de 2026-10-06): Haiku 4.5 **Active**, 64K de saída |
| H2 | Montagem pré-IA quebra (cotação/snapshot/prompt) | REFUTADA para dado normal | repro local com Yahoo real + transporte mockado: OK para ITUB4 e BRAP4, body com `claude-haiku-4-5` e max_tokens 4096 |
| H3 | `quote.change=None` → TypeError no `:+.2f` do `_build_user_prompt` | DEFEITO REAL e latente; improvável como causa de 4/4 | guardião RED → GREEN; o brapi só devolve None sem `regularMarketChangePercent` e sem prev |
| H4 | Falha do provedor ou da config (chave ausente no env → `missing_key`; 401/403/429/400 da Anthropic; saldo) | MAIS PROVÁVEL, não verificada | 4 falhas rápidas em ~1 min indicam erro determinístico de config/provedor. As rotas N2 têm fallback determinístico (FIX-C01) que MASCARA a mesma falha, então "o N2 funciona" não prova que a IA funciona |

## O que mudou
- `server/app/llm.py`: `resumo_falha_ia` e `log_falha_ia` (uma linha `[ia-falha] rota=… t=… tipo=… code=… provider=… model=… keySource=… msg=…`, com redação de `?key=`, `sk-…` e `AIza…`, truncada em 300 caracteres); `_build_user_prompt` omite o % quando `change` não é numérico.
- `server/app/main.py`: `log_falha_ia` no except do N3 (`carteira-stopalvo`) e nos dois excepts do N2 que caem no fallback FIX-C01 (`analyze`, `technical/analyze`). Contrato HTTP inalterado (502 / fallback).
- `server/tests/test_carteira_stopalvo_502.py`: 5 guardiões (log único sem segredo para LLMUserError e para exceção crua; redação; `change=None`; caminho feliz com modelo vazio indo ao provedor com haiku-4-5).

## Validação
`bash scripts/executar.sh --testes` (fora do sandbox): exit 0, 3604 passed / 5 skipped / 3 xfailed + todos os web/tests OK.
Atenção: a árvore tinha mudanças não commitadas de outra sessão (skill_ref.py, store.py, copy.js, main.py `meuModo`); a suíte rodou com elas.

## Próximo passo para fechar a causa raiz
1. Mais rápido, sem deploy: ler a mensagem do popup de stop/alvo no app (o corpo do 502 já traz `message`/`code`), ou ler os logs do Railway das 16:09 (precisa de autorização do Alex).
2. Ou: deploy só-backend (bump manual de SERVER_BUILD_ID), refazer um stop/alvo e procurar `[ia-falha] rota=carteira-stopalvo` no log.

## Achados laterais (fora do escopo, não corrigidos)
- O `public_error` devolve `str(exc)` cru no corpo do 502 para exceção que não é LLMUserError. No Google a URL leva `?key=`, então a chave pode vazar ao cliente (o T-04-01 já trata isso no N2; o N3 e outras 3 rotas 502 não tratam).
- Haiku 5.5 (`claude-haiku-5-5`) custa $0.10/$0.50 contra $1/$5 do 4.5, mas rejeita `temperature` diferente do default e liga adaptive thinking por padrão. Trocar o fallback exige entrada no `model_catalog` e decisão de custo do Alex.

## Evidência de produção (logs do Railway, lidos com autorização do Alex em 2026-10-14)
- 19:09–19:10 UTC: cada 502 vem logo depois de `[llm] modelo vazio p/ provider=anthropic → fallback claude-haiku-4-5`. A falha acontece DENTRO de `_call_llm`, depois do fallback, em 173–910 ms.
- Isso descarta o H3 (`change=None` quebraria antes de `_call_llm`, e o print do fallback não sairia) e o H2. Também não é timeout.
- De 01/10 a 14/10 nenhuma chamada de IA em produção durou o bastante para ser uma resposta real: `scan/deep` levou de 16 a 1369 ms, `technical/analyze` de 149 a 432 ms. O `scan/deep` engole o erro em `errors` (scan_deep.py:147) e o N2 cai no fallback FIX-C01. **A IA está fora há pelo menos 2 semanas, mascarada**, e só o N3 mostra (também deu 502 em 13/10: B3SA3, UGPA3, PETR4, BBAS3, BPAC11).
- Restam duas causas, e o log não as separa: (a) `missing_key`: com keySource env, nem `B3_AGENTE_API_KEY` nem `ANTHROPIC_API_KEY` existem no serviço de produção e a IA gerenciada está desligada; (b) a Anthropic recusa rápido (401 chave inválida/revogada, 403, 400 de saldo).
- Para separar: confirmar no dashboard do Railway (production → b3agente → Variables) se `ANTHROPIC_API_KEY`/`B3_AGENTE_API_KEY` existe, e no Console da Anthropic se a chave está ativa e com saldo. Ou fazer o deploy do log `[ia-falha]` e refazer um stop/alvo.
