#!/usr/bin/env python3
"""PreToolUse guard — bloqueia comandos Bash catastroficos antes de executar.
Contrato Claude Code: le JSON do stdin; exit 2 = bloqueia (stderr vai pro Claude);
exit 0 = libera. Em input ilegivel, NAO bloqueia (fail-open p/ nao travar sessao)."""
import json
import re
import sys

try:z
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = (data.get("tool_input") or {}).get("command", "") or ""

# (regex, motivo) — casa contra o comando completo, case-insensitive
BLOQUEIOS = [
    (r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+(/|~|\$HOME|\*)", "rm recursivo forcado em raiz/home/glob"),
    (r"\brm\s+-[a-z]*f[a-z]*r[a-z]*\s+(/|~|\$HOME|\*)", "rm recursivo forcado em raiz/home/glob"),
    (r":\(\)\s*\{.*\|.*&\s*\}\s*;", "fork bomb"),
    (r"\bdd\b.*\bof=/dev/(sd|nvme|disk|hd)", "dd sobre disco fisico"),
    (r"\bmkfs\.", "formatacao de filesystem"),
    (r">\s*/dev/(sd|nvme|disk|hd)", "escrita direta em disco"),
    (r"\bchmod\s+-R\s+0*777\s+/", "chmod 777 recursivo em raiz"),
    (r"\bgit\s+push\b.*\b(--force|-f)\b.*\b(main|master)\b", "git push forcado em branch principal"),
    (r"\bgit\s+push\s+.*\b(main|master)\b.*\b(--force|-f)\b", "git push forcado em branch principal"),
]

for pattern, motivo in BLOQUEIOS:
    if re.search(pattern, cmd, re.IGNORECASE):
        print(f"[guard-destrutivo] BLOQUEADO: {motivo}\nComando: {cmd}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
