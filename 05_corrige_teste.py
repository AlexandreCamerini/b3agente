#!/usr/bin/env python3
"""
05_corrige_teste.py — corrige a asserção desatualizada de test_copy_theme.mjs.

    python3 05_corrige_teste.py            # verifica e mostra o plano
    python3 05_corrige_teste.py --aplicar  # aplica + roda o teste
    python3 05_corrige_teste.py --reverter # desfaz pelo backup

O PROBLEMA
    O teste assere sobre TEXTO LITERAL do main.py e procura:
        {**mcfg, "appMode": (config or {}).get("appMode")}
    O código real termina em vírgula, não em chave, porque o dicionário
    continua nas linhas seguintes:
        {**mcfg, "appMode": (config or {}).get("appMode"),
                 "outraChave": ...}
    Ou seja: o comportamento está CERTO (o appMode é preservado). A asserção
    é que ficou presa a um formato antigo do código.

O GUARDA-CORPO (o mais importante deste script)
    Antes de mexer no teste, ele CONFIRMA que o main.py realmente remescla o
    appMode. Se não confirmar, ABORTA — porque aí o teste estaria vermelho
    com razão, e ajustar a asserção seria esconder um bug de verdade.

O QUE MUDA
    Uma única `}` no fim da string procurada. A asserção continua garantindo
    que o appMode é remesclado no mcfg — sem quebrar quando o dicionário
    ganhar mais chaves.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys

TESTE = "web/tests/test_copy_theme.mjs"
MAIN = "server/app/main.py"

# o que o main.py PRECISA conter para o comportamento estar correto
COMPORTAMENTO = '{**mcfg, "appMode": (config or {}).get("appMode")'
# a string exata que o teste procura hoje (com a chave a mais no fim)
DE = '(config or {}).get("appMode")}\''
PARA = '(config or {}).get("appMode")\''


def c(t, cod):
    return f"\033[{cod}m{t}\033[0m" if sys.stdout.isatty() else t


def ok(m):    print(c("  ✓ ", 32) + m)
def mal(m):   print(c("  ✗ ", 31) + m)
def aviso(m): print(c("  ! ", 33) + m)
def tit(m):   print("\n" + c(f"══ {m}", 1))
def morre(m):
    mal(m)
    sys.exit(1)


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "--check"

    if not os.path.isdir(".git"):
        morre("rode na raiz do b3-agente")

    if modo == "--reverter":
        tit("Revertendo")
        bak = TESTE + ".bak"
        if os.path.isfile(bak):
            shutil.move(bak, TESTE)
            ok(f"{TESTE} restaurado")
        else:
            aviso("sem backup — use: git checkout -- " + TESTE)
        return 0

    for f in (TESTE, MAIN):
        if not os.path.isfile(f):
            morre(f"não achei {f}")
    ok("arquivos encontrados")

    # ------------------------------------------------------------------
    tit("1. GUARDA-CORPO — o comportamento está correto no main.py?")
    src_main = open(MAIN, encoding="utf-8").read()

    if COMPORTAMENTO not in src_main:
        mal("o main.py NÃO remescla o appMode no mcfg.")
        print("""
    ABORTANDO. O teste está vermelho com razão — existe um bug real:
    a config gerenciada sobrescreve o appMode e o modo Operador vira Estudo.

    O conserto é no main.py (não no teste). Onde o mcfg vira a config
    efetiva, envolva assim:

        {**mcfg, "appMode": (config or {}).get("appMode"), ...}
""")
        return 1
    ok("main.py remescla o appMode — comportamento correto, teste desatualizado")

    linha = next((i for i, l in enumerate(src_main.splitlines(), 1)
                  if COMPORTAMENTO in l), None)
    if linha:
        print(f"      {MAIN}:{linha}")

    try:
        ast.parse(src_main)
        ok("main.py com sintaxe válida (dicionário bem formado)")
    except SyntaxError as e:
        morre(f"main.py tem erro de sintaxe ({e}) — resolva isso primeiro")

    # ------------------------------------------------------------------
    tit("2. A asserção desatualizada")
    src_teste = open(TESTE, encoding="utf-8").read()

    if DE not in src_teste:
        if PARA in src_teste:
            ok("a asserção JÁ está corrigida — nada a fazer")
            return 0
        morre(f"não achei a asserção esperada em {TESTE}. "
              "O arquivo mudou — não vou adivinhar; ajuste à mão.")

    n = src_teste.count(DE)
    if n != 1:
        morre(f"achei {n} ocorrências (esperava 1) — ambíguo, ajuste à mão.")

    for i, l in enumerate(src_teste.splitlines(), 1):
        if DE in l:
            print(f"      {TESTE}:{i}")
            print("      " + c("- ", 31) + l.strip()[:110])
            print("      " + c("+ ", 32) + l.replace(DE, PARA).strip()[:110])
            break

    # ------------------------------------------------------------------
    if modo == "--check":
        tit("PLANO")
        print("    Remove a `}` final da string procurada. A asserção segue")
        print("    garantindo que o appMode é remesclado no mcfg.")
        print(c("\n    Aplicar:  python3 05_corrige_teste.py --aplicar", 36))
        return 0

    if modo != "--aplicar":
        print("uso: 05_corrige_teste.py [--check|--aplicar|--reverter]")
        return 1

    # ------------------------------------------------------------------
    tit("3. Aplicando")
    shutil.copy2(TESTE, TESTE + ".bak")
    ok(f"backup: {TESTE}.bak")
    open(TESTE, "w", encoding="utf-8").write(src_teste.replace(DE, PARA, 1))
    ok("asserção corrigida")

    # ------------------------------------------------------------------
    tit("4. Rodando o teste")
    r = subprocess.run(["node", TESTE], capture_output=True, text=True)
    saida = (r.stdout or "") + (r.stderr or "")
    falhas = [l for l in saida.splitlines() if l.startswith("FALHOU")]

    for l in saida.splitlines():
        if "appMode" in l or l.startswith("FALHOU") or "falha(s)" in l:
            print("      " + l)

    if r.returncode == 0 and not falhas:
        ok("teste VERDE")
        tit("PRÓXIMOS PASSOS")
        print(f"""    1. Revise:  {c('git --no-pager diff ' + TESTE, 36)}
    2. Commit:  {c('git commit -am "fix(teste): asserção do appMode não depende do fim do dict"', 36)}
    3. Entregue: {c('./entregar.sh', 36)}

    Rollback: {c('python3 05_corrige_teste.py --reverter', 36)}""")
        return 0

    mal("ainda há falha(s) — a asserção não era a única causa")
    for l in falhas:
        print("      " + l)
    print(f"\n    Reverter: {c('python3 05_corrige_teste.py --reverter', 36)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
