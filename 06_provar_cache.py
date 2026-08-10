#!/usr/bin/env python3
"""
06_provar_cache.py — PROVA se o prompt caching está funcionando de verdade.

    export ANTHROPIC_API_KEY=sk-ant-...
    python3 06_provar_cache.py

Por que este script existe
--------------------------
A telemetria do Boris+ não consegue mostrar o cache: o _norm_usage SOMA
cache_read + cache_creation + input para manter a cota honesta, então o total
de tokens fica igual com ou sem cache. O ganho do caching é no PREÇO (leitura
custa 10% do input), não na contagem. A prova tem que vir da API.

O que ele faz
-------------
1. Lê os prompts reais do server/app/llm.py (sem importar o módulo)
2. Faz DUAS chamadas idênticas à API, com cache_control, poucos tokens
3. Mostra os campos crus de usage das duas
4. Calcula a economia real em USD

Custo do teste: frações de centavo (2 chamadas, saída de 16 tokens).
Não toca em nenhum arquivo do projeto. Só faz requisição HTTP.
"""
from __future__ import annotations

import ast
import json
import os
import sys
import time
import urllib.error
import urllib.request

ARQ = "server/app/llm.py"

# USD por MTok: (entrada, saida, leitura_cache, escrita_cache, minimo)
PRECOS = {
    "claude-haiku-4-5":  (1.0,  5.0, 0.10, 1.25, 4096),
    "claude-sonnet-5":   (2.0, 10.0, 0.20, 2.50, 1024),
    "claude-sonnet-4-6": (3.0, 15.0, 0.30, 3.75, 1024),
    "claude-opus-4-8":   (5.0, 25.0, 0.50, 6.25, 1024),
    "claude-fable-5":   (10.0, 50.0, 1.00,12.50,  512),
}


def c(t, cod):
    return f"\033[{cod}m{t}\033[0m" if sys.stdout.isatty() else t


def ok(m):    print(c("  ✓ ", 32) + m)
def mal(m):   print(c("  ✗ ", 31) + m)
def aviso(m): print(c("  ! ", 33) + m)
def tit(m):   print("\n" + c(f"══ {m}", 1))


def constantes(caminho: str) -> dict:
    """Extrai as constantes de texto sem IMPORTAR o módulo (ele tem imports
    relativos que quebrariam fora do pacote)."""
    src = open(caminho, encoding="utf-8").read()
    ns: dict = {}
    for node in ast.parse(src).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        alvo = node.targets[0]
        if not isinstance(alvo, ast.Name) or not alvo.id.isupper():
            continue
        trecho = ast.get_source_segment(src, node.value)
        if not trecho:
            continue
        try:
            ns[alvo.id] = eval(trecho, {"__builtins__": {}}, dict(ns))  # noqa: S307
        except Exception:
            pass
    return {k: v for k, v in ns.items() if isinstance(v, str)}


def modelo_configurado() -> str:
    """Lê o modelo default do defaults.py; cai no sonnet-5 se não achar."""
    try:
        src = open("server/app/defaults.py", encoding="utf-8").read()
        for linha in src.splitlines():
            if '"model":' in linha and "claude" in linha:
                return linha.split('"model":')[1].split('"')[1]
    except Exception:
        pass
    return "claude-sonnet-5"


def chamar(chave: str, modelo: str, system_blocks, rotulo: str) -> dict | None:
    corpo = json.dumps({
        "model": modelo,
        "max_tokens": 16,
        "system": system_blocks,
        "messages": [{"role": "user", "content": "Responda apenas: OK."}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=corpo, method="POST",
        headers={"content-type": "application/json", "x-api-key": chave,
                 "anthropic-version": "2023-06-01"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        u = data.get("usage", {})
        u["_ms"] = int((time.time() - t0) * 1000)
        print(f"  {rotulo}: {u.get('_ms')} ms")
        return u
    except urllib.error.HTTPError as e:
        mal(f"{rotulo}: HTTP {e.code} — {e.read()[:200].decode(errors='replace')}")
    except Exception as e:  # noqa: BLE001
        mal(f"{rotulo}: {e}")
    return None


def main() -> int:
    if not os.path.isfile(ARQ):
        mal(f"não achei {ARQ} — rode na raiz do b3-agente")
        return 1
    chave = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not chave:
        mal("defina ANTHROPIC_API_KEY (a mesma que o Boris+ usa)")
        return 1

    tit("1. Preparando")
    k = constantes(ARQ)
    ok(f"{len(k)} constantes lidas de {ARQ}")

    # o system do analyze_deep é o que atinge o mínimo de cache
    partes = [k.get("OPERADOR_PRO"), k.get("GUARDRAILS_PRO"), k.get("PRO_DEEP_FORMAT")]
    if not all(partes):
        partes = [k.get("OPERADOR_EDUCACIONAL"), k.get("GUARDRAILS"), k.get("DEEP_FORMAT")]
    if not all(partes):
        mal("não consegui montar o system do analyze_deep — nomes mudaram?")
        return 1
    system = "\n".join(partes)

    modelo = modelo_configurado()
    p = PRECOS.get(modelo)
    est = int(len(system) / 3.2)
    ok(f"modelo: {modelo}")
    ok(f"system: {len(system):,} chars (~{est:,} tokens estimados)")
    if p and est < p[4]:
        aviso(f"ABAIXO do mínimo do modelo ({p[4]:,}) — o cache deve ficar em 0.")
        aviso("se der 0 nas duas chamadas, é isso, e é o comportamento correto.")

    tit("2. Duas chamadas idênticas (a 2ª deve ler do cache)")
    blocos = [{"type": "text", "text": system,
               "cache_control": {"type": "ephemeral"}}]
    u1 = chamar(chave, modelo, blocos, "1ª chamada")
    if not u1:
        return 1
    time.sleep(2)  # a entrada só existe depois que a 1ª resposta começa
    u2 = chamar(chave, modelo, blocos, "2ª chamada")
    if not u2:
        return 1

    tit("3. Usage cru da API")
    print(f"  {'campo':<32}{'1ª':>10}{'2ª':>10}")
    for campo in ("input_tokens", "cache_creation_input_tokens",
                  "cache_read_input_tokens", "output_tokens"):
        print(f"  {campo:<32}{u1.get(campo, 0):>10,}{u2.get(campo, 0):>10,}")

    tit("VEREDITO")
    escrita = u1.get("cache_creation_input_tokens", 0) or 0
    leitura = u2.get("cache_read_input_tokens", 0) or 0

    if leitura > 0:
        ok(f"CACHE FUNCIONANDO — a 2ª chamada leu {leitura:,} tokens do cache")
        if p:
            sem = (escrita + (u1.get("input_tokens", 0) or 0)) * p[0] / 1e6
            com = leitura * p[2] / 1e6 + (u2.get("input_tokens", 0) or 0) * p[0] / 1e6
            if sem > 0:
                print(f"\n    input da 2ª chamada sem cache: ${sem:.6f}")
                print(f"    input da 2ª chamada com cache: ${com:.6f}")
                print(f"    economia no input: {(1 - com/sem) * 100:.0f}%")
        print("""
    Lembre: no Boris+ o input é pequeno perto do contexto técnico e o output
    domina o custo. A economia no TOTAL da chamada fica em 4-9%, não nesse
    percentual do input isolado.""")
        return 0

    if escrita > 0 and leitura == 0:
        aviso("escreveu o cache mas não leu na 2ª — prefixo divergiu entre as chamadas")
        aviso("ou passaram-se mais de 5 minutos (TTL).")
        return 1

    mal("SEM CACHE — nenhum token escrito nem lido")
    print("""
    Causas possíveis, em ordem:
      1. o prefixo está abaixo do mínimo do modelo (veja o aviso no passo 1)
      2. o modelo configurado não é Claude
      3. o patch não está no código em execução

    Confirme o patch:  grep -n "_system_cacheavel" server/app/llm.py
    Deve aparecer 2x: a definição e a chamada dentro do _call_anthropic.""")
    return 1


if __name__ == "__main__":
    sys.exit(main())
