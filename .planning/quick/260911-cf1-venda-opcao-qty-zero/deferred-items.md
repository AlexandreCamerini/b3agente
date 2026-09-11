# Deferred — quick 260911-cf1

## D-2 (candidato): `/api/options/lastreada/fechar` fecha tudo com `contratos: 0`

Descoberto ao mapear os chamadores de `store.sell_option` durante o D-1.
**Não corrigido** — rota da Fase 14, fora do escopo do plano desta quick.

`server/app/main.py`, rota `POST /api/options/lastreada/fechar`:

```python
contratos_n = int(contratos_body) if isinstance(contratos_body, (int, float)) and contratos_body > 0 else None
```

`contratos: 0`, `contratos: -3` e `contratos: "abc"` caem todos em `None`, e
`None` nessa rota significa **fechar a operação lastreada INTEIRA** (o `None`
é repassado como `contratos=` para `store.fechar_call_coberta` e como
`qty=None` para `store.sell_option`). Mesmo efeito do D-1: liquidação total
silenciosa a partir de uma entrada que o usuário poderia crer que fecha zero.
Diferenças em relação ao D-1:

- não vaza 500: o `isinstance` já engole o não numérico, então `"abc"` não
  levanta `ValueError` — vira fechamento total, que é pior que o 500;
- a rota tem trava de Modo Operador (403 em Modo Estudo), o que reduz a
  superfície mas não elimina;
- `contratos` ausente também significa "fechar tudo", igual à venda de opção —
  então a correção tem o mesmo formato do D-1: distinguir AUSENTE de ZERO/
  NEGATIVO/não numérico explícito.

Seria a QUINTA ocorrência da família de `qty` falsy. Merece quick própria.
