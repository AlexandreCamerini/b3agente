#!/usr/bin/env python3
"""
03_gateway_cache.py — implementa o GATEWAY dentro do llm.py do Boris+.

    python3 03_gateway_cache.py            # mostra o diff (não altera)
    python3 03_gateway_cache.py --aplicar  # aplica com backup + validação
    python3 03_gateway_cache.py --reverter # desfaz pelo backup

O QUE ADICIONA (aditivo — nada é removido ou substituído)
    1. prompt caching no _call_anthropic, CONDICIONAL ao mínimo do modelo
    2. telemetria honesta: conta os tokens lidos/escritos no cache

O QUE PRESERVA
    multi-provedor, record_usage, cota, rate limit, BYOK vs managed,
    erros acionáveis. O gateway aqui é a peça que FALTAVA, não um substituto.

POR QUE CONDICIONAL
    Abaixo do mínimo do modelo a API aceita o cache_control e IGNORA em
    silêncio: você paga a escrita e nunca lê. Aplicar sempre seria pior que
    não aplicar. Haiku 4.5 exige 4.096 tokens; os prompts do Boris+ têm
    ~1.100-1.200. Só Opus/Sonnet/Fable se beneficiam.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys

ALVO = "server/app/llm.py"

HELPER = '''
# --- prompt caching (gateway) -----------------------------------------------
# Mínimo cacheável por modelo. Abaixo disso a API IGNORA o cache_control em
# SILÊNCIO: paga-se a escrita e nunca se lê. Por isso é condicional.
_CACHE_MIN = {
    "claude-fable-5": 512,
    "claude-opus-4-8": 1024,
    "claude-opus-4-7": 2048,
    "claude-opus-4-6": 4096,
    "claude-opus-4-5": 4096,
    "claude-sonnet-5": 1024,
    "claude-sonnet-4-6": 1024,
    "claude-sonnet-4-5": 1024,
    "claude-haiku-4-5": 4096,
}
# ~3.2 chars/token em português (conservador: subestimar evita write inútil).
_CHARS_POR_TOKEN = 3.2


def _system_cacheavel(model: str, system: str):
    """Devolve o `system` como bloco com cache_control se o prefixo atingir o
    mínimo do modelo; caso contrário devolve a string original (sem cache).

    Ganho: nas chamadas seguintes com o MESMO system, o prefixo é lido a 10%
    do preço de entrada. Cenário ideal: Radar N1, que faz N chamadas em
    sequência com system idêntico."""
    minimo = None
    for prefixo, valor in _CACHE_MIN.items():
        if (model or "").startswith(prefixo):
            minimo = valor
            break
    if minimo is None:
        return system  # modelo desconhecido: não arrisca write inútil
    if len(system) / _CHARS_POR_TOKEN < minimo:
        return system  # abaixo do mínimo: cachear seria pagar sem receber
    return [{"type": "text", "text": system,
             "cache_control": {"type": "ephemeral"}}]

'''

ANCORA_HELPER = "async def _call_anthropic(config, key, system, user, max_tokens):"

DE_SYSTEM = '"system": system, "messages": [{"role": "user", "content": user}]}'
PARA_SYSTEM = ('"system": _system_cacheavel(config["model"], system), '
               '"messages": [{"role": "user", "content": user}]}')

DE_USAGE = '''    u = data.get("usage")
    if isinstance(u, dict):
        return (u.get("input_tokens", u.get("prompt_tokens")),
                u.get("output_tokens", u.get("completion_tokens")))'''

PARA_USAGE = '''    u = data.get("usage")
    if isinstance(u, dict):
        entrada = u.get("input_tokens", u.get("prompt_tokens"))
        # Com prompt caching, input_tokens traz SÓ os tokens novos. Os lidos e
        # escritos no cache vêm em campos separados — somá-los mantém a
        # telemetria (e a cota) honesta em vez de subestimar o consumo.
        if entrada is not None:
            entrada = (int(entrada)
                       + int(u.get("cache_read_input_tokens") or 0)
                       + int(u.get("cache_creation_input_tokens") or 0))
        return (entrada, u.get("output_tokens", u.get("completion_tokens")))'''


def cor(t, c):
    return f"\033[{c}m{t}\033[0m" if sys.stdout.isatty() else t


def falha(msg):
    print(cor(f"✗ {msg}", 31))
    sys.exit(1)


def transformar(src: str) -> str:
    if "_system_cacheavel" in src:
        falha("o patch já foi aplicado (encontrei _system_cacheavel).")
    for nome, alvo, n_esperado in [
        ("âncora do helper", ANCORA_HELPER, 1),
        ("linha do system", DE_SYSTEM, 1),
        ("bloco do _norm_usage", DE_USAGE, 1),
    ]:
        n = src.count(alvo)
        if n != n_esperado:
            falha(f"{nome}: esperava {n_esperado} ocorrência, achei {n}. "
                  "O arquivo mudou — não vou adivinhar. Aplique à mão.")
    src = src.replace(ANCORA_HELPER, HELPER + ANCORA_HELPER, 1)
    src = src.replace(DE_SYSTEM, PARA_SYSTEM, 1)
    src = src.replace(DE_USAGE, PARA_USAGE, 1)
    return src


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "--check"

    if not os.path.isfile(ALVO):
        falha(f"não achei {ALVO} — rode na raiz do b3-agente")

    if modo == "--reverter":
        bak = ALVO + ".bak"
        if not os.path.isfile(bak):
            print(cor("! sem backup — use: git checkout -- " + ALVO, 33))
            return 1
        shutil.move(bak, ALVO)
        print(cor(f"✓ {ALVO} restaurado do backup", 32))
        return 0

    original = open(ALVO, encoding="utf-8").read()
    novo = transformar(original)

    try:
        ast.parse(novo)
    except SyntaxError as e:
        falha(f"o resultado seria inválido ({e}). Nada foi alterado.")
    print(cor("✓ resultado tem sintaxe válida", 32))

    if modo == "--check":
        print(cor("\nMODO CHECK — nada alterado. Mudanças previstas:\n", 1))
        print("  1. helper _system_cacheavel() antes de _call_anthropic")
        print("  2. _call_anthropic passa o system por esse helper")
        print("  3. _norm_usage soma os tokens de cache na contagem de entrada")
        print(cor("\n  Aplicar:  python3 03_gateway_cache.py --aplicar", 36))
        return 0

    if modo != "--aplicar":
        print("uso: 03_gateway_cache.py [--check|--aplicar|--reverter]")
        return 1

    shutil.copy2(ALVO, ALVO + ".bak")
    print(cor(f"✓ backup: {ALVO}.bak", 32))
    open(ALVO, "w", encoding="utf-8").write(novo)

    try:
        ast.parse(open(ALVO, encoding="utf-8").read())
        print(cor("✓ arquivo gravado e validado", 32))
    except SyntaxError:
        shutil.move(ALVO + ".bak", ALVO)
        falha("sintaxe inválida após gravar — revertido automaticamente")

    print(cor("\nDiff:", 1))
    subprocess.run(["git", "diff", "--", ALVO], check=False)

    print(cor("""
Próximos passos
  1. Revise o diff acima.
  2. Teste: rode uma análise 2x seguidas no MESMO modo em até 5 minutos.
     A 2a deve mostrar cache_read_input_tokens > 0 na resposta da API.
  3. Commit:
       git checkout -b gateway-cache
       git commit -am "gateway: prompt caching condicional + telemetria de cache"

Rollback
  python3 03_gateway_cache.py --reverter    (desfaz o arquivo)
  git checkout -- server/app/llm.py         (desfaz pelo git)

Limites conhecidos
  - Só Opus/Sonnet/Fable atingem o mínimo com os prompts atuais (~1.100-1.200
    tokens). Em Haiku 4.5 (mínimo 4.096) o helper devolve o system sem cache,
    de propósito.
  - analyze_structured fica ABAIXO de 1.024 no piso medido: para cachear ali,
    é preciso reordenar (estático primeiro, variável por último) e engordar o
    prefixo. Isso mexe na composição dos prompts — é decisão sua, não faço aqui.
  - Ganho esperado no Boris+: 4-9%. O prefixo é pequeno perto do contexto e o
    output domina o custo. No orc o mesmo mecanismo rende 35-60%.
""", 36))
    return 0


if __name__ == "__main__":
    sys.exit(main())
