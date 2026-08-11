# ESPEC-B — Fechar o loop de validação por regime

**Premissa honesta:** a camada de validação **já existe e é boa**. `analysis_outcomes.py` já grava cada leitura com stop/alvo, avalia num horizonte fixo de 10 pregões e o `compute_stats` já entrega **taxa de acerto, expectância (R médio), profit factor, calibração (confiança declarada × acerto real), curva de R acumulado + drawdown máximo e recorte por setup**, tudo com guarda `MIN_N=10`. Isso NÃO é greenfield.

**O gap real é cirúrgico:** o outcome não é segmentado por **regime de mercado** (tendência × lateral) — a própria `ESPEC-Analises-Tecnicas §6` e a skill pedem esse recorte — e a expectância medida **não realimenta** a confiança nem o ranking. Hoje a confiança é **declarada** (confluência/timeframe) e só *comparada* com o real na calibração; ela não *deriva* do resultado medido.

**Arquivos:** `~ server/app/analysis_outcomes.py` (3 deltas), `~ server/app/main.py` (2 call-sites), `~ server/app/scanner.py`/`regime.py` (consumo do feedback — opcional, fase B2). **Depende de A** (o campo `regime` vem de `regime.classificar`).

---

## Delta 1 — Persistir o regime na análise (`registrar`)

O regime tem que ser gravado **no momento da análise** (o regime de hoje, não o de quando o outcome é avaliado 10 pregões depois).

```python
def registrar(conn, *, ticker, modo, tipo, modelo, setup, recomendacao,
              stop, alvo, preco, snapshot_id, confianca=None, user_id=None,
              regime=None):                      # + NOVO (str: saída de regime.classificar()["regime"])
    ...
    entry = {
        ...,
        "confianca": normalizar_confianca(confianca),
        "regime": regime,                        # + NOVO — None em registros antigos (retrocompatível)
        ...
    }
```

Call-sites (`main.py:865` scanDeep/N1 e `main.py:969` analyze/N2): passar `regime=snap["regime"]["regime"]` (o campo que o A anexa a cada resultado). Registros pré-B ficam com `regime=None` → caem numa célula `"—"`, sem quebrar nada.

## Delta 2 — Segmentar `compute_stats` por regime e por setup×regime

`_celula` já faz o trabalho pesado (métricas + guarda `MIN_N`). Reusar:

```python
# dentro de compute_stats, junto de por_setup:
por_regime, por_setup_regime = {}, {}
for o in resolvidos:
    rg = o.get("regime") or "—"
    por_regime.setdefault(rg, []).append(o)
    chave = f"{o.get('setup') or '—'} @ {rg}"
    por_setup_regime.setdefault(chave, []).append(o)

# no return, junto das chaves existentes:
"porRegime":      {k: _celula(v) for k, v in por_regime.items()},
"porSetupRegime": {k: _celula(v) for k, v in por_setup_regime.items()},
```

Isso responde a pergunta que o CLAUDE.md/skill exigem e que hoje o painel "Eficiência da IA" não responde: **"este setup tem expectância positiva em tendência mas negativa em lateral?"** — o recorte que separa um setup útil de um que só funciona num regime.

## Delta 3 — O feedback loop (a parte que realmente "fecha")

Função pura nova em `analysis_outcomes.py`: dada a expectância **medida** por (setup × regime), devolve um veredito de histórico — **com guarda de amostra e degradação graciosa**.

```python
def historico_do_par(stats: dict, setup: str, regime: str) -> dict:
    """Veredito do par (setup, regime) a partir do que JÁ foi medido.
    Puro. Nunca vira promessa — é descritivo e educacional (guardrail CVM).
    Retorna:
      {"status": "favoravel|desfavoravel|neutro|sem_dados",
       "expectanciaR": float|None, "n": int}
    """
    cel = (stats.get("porSetupRegime") or {}).get(f"{setup} @ {regime}")
    if not cel or cel.get("insuficiente"):
        return {"status": "sem_dados", "expectanciaR": None, "n": (cel or {}).get("n", 0)}
    r = cel.get("rMedio")
    if r is None:
        return {"status": "neutro", "expectanciaR": None, "n": cel["n"]}
    status = "favoravel" if r > 0 else "desfavoravel" if r < 0 else "neutro"
    return {"status": status, "expectanciaR": r, "n": cel["n"]}
```

Dois consumidores (ambos **não-destrutivos** — anotar antes de reordenar):

**B1 — Anotação (entra já).** O N1/N2 anexa `historicoRegime` ao resultado. A UI mostra *"neste regime, este setup teve expectância medida de +0,4R em 23 leituras"* — ou *"sem histórico suficiente neste regime"*. Puro ganho de transparência, zero risco de reordenar com base em ruído.

**B2 — Rebaixamento (entra depois de acumular amostra).** No `regime.ranquear`, quando `historico_do_par` for `desfavoravel` com `n ≥ MIN_N`, aplicar um **teto** no `radarScore` e/ou rebaixar a confiança declarada para o par — o setup com expectância medida negativa **naquele regime** para de ser promovido. Enquanto `sem_dados`, mantém o eixo estrutural do A (neutro). É assim que a confiança passa a **derivar de resultado medido**, não de aderência.

## Guardrail inegociável (CVM)

Expectância medida é **descritiva e educacional**, jamais previsão. Toda superfície que exibir `expectanciaR`/`historicoRegime` carrega o disclaimer do app e usa o vocabulário fixo ("resultado medido em leituras passadas", nunca "vai dar X%"). Amostra `< MIN_N` **nunca** vira porcentagem (regra já vigente no `_celula`). Passado favorável **não** é garantia futura — texto obrigatório.

## Interlock A ↔ B

```
A (regime.classificar)  ──emite──►  r["regime"]["regime"]
                                         │
                    ┌────────────────────┴─────────────────────┐
          registrar(regime=...)                        ranquear consome
          (grava no outcome)                           historico_do_par (B2)
                    │                                          ▲
          compute_stats.porSetupRegime ──historico_do_par──────┘
```

A ordem **A→B é obrigatória**: sem o campo `regime` que o A emite, o B não tem o que segmentar.

## Critérios de aceite

- `compute_stats` retorna `porRegime` e `porSetupRegime`; células `< MIN_N` sem porcentagem.
- Registro antigo (`regime=None`) não quebra agregação (cai em `"—"`).
- `historico_do_par` puro, coberto por teste (favorável/desfavorável/neutro/sem_dados).
- B1 anota sem reordenar; B2 só rebaixa com `n ≥ MIN_N` e sempre com disclaimer.
- Suíte `bash scripts/executar.sh --testes` verde.

## Sequência sugerida

1. Delta 1 + 2 + call-sites (grava e segmenta — começa a **acumular** amostra por regime).
2. `historico_do_par` + testes.
3. B1 (anotação na UI) — transparência imediata.
4. B2 (rebaixamento no ranking) **só quando** houver `n ≥ MIN_N` em pares relevantes — senão você reordena com ruído, o oposto do objetivo.
