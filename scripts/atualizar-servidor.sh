#!/usr/bin/env bash
# atualizar-servidor.sh — commit + push + verificação do deploy no Railway.
# Uso (na raiz do repo):  bash scripts/atualizar-servidor.sh "mensagem do commit"
set -euo pipefail
cd "$(dirname "$0")/.."
MSG="${1:-atualizacao}"
RAILWAY_URL="https://boris.semente.dev"
REPO_URL="https://github.com/AlexandreCamerini/b3agente.git"

# ---------------------------------------------------------------------------
# Blindagem (erro recorrente: "'origin' does not appear to be a git repository")
# 1. a pasta precisa SER um repo git — extrair o b3-agente.zip como pasta nova
#    (sem .git) e rodar o deploy dali é o erro clássico;
# 2. o repo enxergado pelo git precisa ser ESTA pasta (não um pai por acidente);
# 3. sem remote origin → reanexa sozinho a URL canônica do projeto.
# ---------------------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "✗ esta pasta não é um repositório git."
  echo "  Você provavelmente extraiu o b3-agente.zip como pasta NOVA (ele vem sem .git)."
  echo "  Caminho certo: no seu CLONE, rode  bash atualizar.sh ~/Downloads/files.zip \"msg\""
  echo "  (ou, para criar o repo do zero:  bash scripts/git-do-zero.sh)"
  exit 1
fi
TOP="$(git rev-parse --show-toplevel)"
if [ "$TOP" != "$(pwd)" ]; then
  echo "✗ o git está enxergando OUTRO repositório: $TOP"
  echo "  (esta pasta não tem .git próprio e caiu num repo pai por acidente)"
  echo "  Aplique a entrega no seu clone:  cd SEU_CLONE && bash atualizar.sh files.zip \"msg\""
  exit 1
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "remote 'origin' ausente — reanexando $REPO_URL"
  git remote add origin "$REPO_URL"
fi

git add -A
git diff --cached --quiet && echo "nada novo para commitar" || git commit -m "$MSG"

# ---------------------------------------------------------------------------
# Blindagem 2 (erro recorrente: "! [rejected] main -> main (fetch first)"):
# o GitHub pode ter commits que o local não tem (ex.: repo local recriado por
# um git-do-zero antigo → linhagens divergentes). Diagnóstico automático:
#   • remoto contido no local → push normal (fast-forward);
#   • remoto à frente com ancestral comum → traz com rebase e segue;
#   • históricos SEM ancestral comum → para com instrução clara (neste projeto
#     o LOCAL é a fonte da verdade; sobrescrever o GitHub é decisão SUA).
# ---------------------------------------------------------------------------
git fetch origin
if git rev-parse --verify -q origin/main >/dev/null && \
   ! git merge-base --is-ancestor origin/main main 2>/dev/null; then
  if git merge-base main origin/main >/dev/null 2>&1; then
    echo "remoto à frente do local — integrando com rebase…"
    if ! git pull --rebase origin main; then
      git rebase --abort 2>/dev/null || true
      echo "✗ rebase com conflito — o GitHub tem mudanças que colidem com as locais."
      echo "  Veja o que só existe lá:   git log --oneline main..origin/main"
      echo "  Se o LOCAL é a fonte da verdade (fluxo padrão deste projeto):"
      echo "     git push --force-with-lease origin main"
      exit 1
    fi
  else
    echo "✗ históricos SEM ancestral comum (repo local recriado em algum momento)."
    echo "  Veja o que só existe no GitHub:  git log --oneline origin/main | head"
    echo "  Neste projeto o LOCAL é a fonte da verdade (entregas via zip + suítes verdes)."
    echo "  Confirmando isso, sobrescreva o GitHub com:"
    echo "     git push --force-with-lease origin main"
    echo "  e rode de novo:  bash atualizar.sh --somente-deploy \"$MSG\""
    exit 1
  fi
fi

git push -u origin main
echo "push feito — aguardando o deploy do Railway…"

for i in $(seq 1 20); do
  code=$(curl -s -o /tmp/health.json -w "%{http_code}" \
    "$RAILWAY_URL/api/scan?period=1mo&tickers=PETR4,VALE3" || echo 000)
  [ "$code" = "200" ] && { echo "✓ /api/scan no ar (tentativa $i)"; break; }
  echo "tentativa $i/20 → HTTP $code"
  [ "$i" = "20" ] && { echo "✗ sem 200 após ~5 min — veja Deployments no painel do Railway"; exit 1; }
  sleep 15
done
python3 -c "import json; d=json.load(open('/tmp/health.json')); r=d['results'][0]; print('✓ radar v2:', r['ticker'], '->', r.get('veredito'), str(r.get('confluencia'))+'%', '· snapshot #'+str(r.get('snapshotId')))"
echo "✓ servidor atualizado e verificado"
