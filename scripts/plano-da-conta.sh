#!/usr/bin/env bash
# Lê e (com confirmação) altera o PLANO de uma conta em produção.
#
# `pro` é, nas palavras do próprio `server/app/plan.py`, "estado alcançável só
# por atribuição manual": não existe rota administrativa para isso, então a
# única porta é o SQLite do container. Este script é essa porta, com leitura
# antes da escrita e confirmação explícita.
#
#   bash scripts/plano-da-conta.sh                      # só LISTA (não escreve)
#   bash scripts/plano-da-conta.sh <e-mail> pro         # promove, perguntando antes
#   bash scripts/plano-da-conta.sh <e-mail> free        # rebaixa
#
# Planos (server/app/plan.py): free = 30 análises/mês · pro = ilimitado.
set -euo pipefail
cd "$(dirname "$0")/.."
EMAIL="${1:-}"
PLANO="${2:-}"
SVC="b3agente"
ENV="production"

if [ -n "$PLANO" ] && [ "$PLANO" != "pro" ] && [ "$PLANO" != "free" ]; then
  echo "plano inválido: use 'pro' ou 'free'" >&2; exit 1
fi

command -v railway >/dev/null 2>&1 || { echo "railway CLI não encontrada" >&2; exit 1; }

echo "== Contas em $ENV (e-mail mascarado) =="
railway ssh --environment "$ENV" --service "$SVC" -- /opt/venv/bin/python3 -c '
import os, sqlite3
p = os.environ.get("B3_DB_PATH", "server/data/b3_agente.db")
if not os.path.exists(p):
    import glob
    cand = glob.glob("/app/**/*.db", recursive=True) + glob.glob("**/*.db", recursive=True)
    print("  banco não encontrado em", p, "| candidatos:", cand[:5]); raise SystemExit(1)
c = sqlite3.connect(p)
for uid, em, pl in c.execute("SELECT id, email, plan FROM users ORDER BY created_at"):
    m = ((em or "")[:3] + "***@" + (em or "").split("@")[-1]) if em and "@" in em else "(sem e-mail)"
    print(f"  {uid[:8]}... | {m:26} | plano={pl}")
'

[ -z "$EMAIL" ] && { echo; echo "  (só leitura — passe <e-mail> e <plano> para alterar)"; exit 0; }

echo
printf "  Alterar %s para plano '%s' em PRODUÇÃO? [y/N] " "$EMAIL" "$PLANO"
read -r r || true
[[ "$r" =~ ^[Yy] ]] || { echo "  cancelado"; exit 0; }

railway ssh --environment "$ENV" --service "$SVC" -- /opt/venv/bin/python3 -c "
import os, sqlite3
p = os.environ.get('B3_DB_PATH', 'server/data/b3_agente.db')
c = sqlite3.connect(p)
row = c.execute('SELECT id, plan FROM users WHERE lower(email) = lower(?)', ('$EMAIL',)).fetchone()
if not row:
    print('  nenhuma conta com esse e-mail'); raise SystemExit(1)
uid, antes = row
c.execute('UPDATE users SET plan = ? WHERE id = ?', ('$PLANO', uid))
c.commit()
depois = c.execute('SELECT plan FROM users WHERE id = ?', (uid,)).fetchone()[0]
print(f'  {uid[:8]}...: {antes} -> {depois}')
print('  ATENÇÃO: o banco fica em disco EFÊMERO do Railway. Um redeploy que')
print('  recrie o volume leva esta alteração junto — reaplique se sumir.')
"
