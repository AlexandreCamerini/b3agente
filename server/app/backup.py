"""Backup do banco SQLite — implementação única, dois pontos de entrada.

POR QUE ESTE MÓDULO EXISTE DENTRO DE `server/app/` (e não em `scripts/`):
o `rootDirectory` do Railway é `/server` (ver `server/railway.json` e o
cabeçalho de `scripts/publicar-web.sh`), então `scripts/` NÃO existe dentro
do container. Um `preDeployCommand` apontando para `scripts/backup-db.sh`
falharia com "arquivo não encontrado" — e, pior, falharia justamente no
deploy em que o backup mais importava. Aqui dentro, o mesmo código serve o
pre-deploy do Railway e o uso local (`scripts/backup-db.sh` delega para cá).

NUNCA usa `db.connect()`: aquele caminho chama `init_db()`, que roda as
migrações (`ALTER TABLE ... ADD COLUMN`, `_migrate_identities_from_users`).
Um backup tirado depois da migração é um backup do estado NOVO — inútil como
rede de segurança para voltar à versão anterior. Aqui a conexão é crua
(`sqlite3.connect`), somente leitura na prática, sem tocar schema.

Uso:
    python -m app.backup                 # backup para <dir do banco>/backups
    python -m app.backup --pre-deploy    # idem, com semântica de deploy (ver abaixo)
    python -m app.backup --out /outro/dir --keep 30

Semântica de saída no modo `--pre-deploy` (é o que o Railway lê):
  • banco INEXISTENTE  -> código 0. Primeiro deploy de um environment novo não
    tem o que proteger; travar o deploy aqui seria impedir o ambiente de
    nascer.
  • backup OK          -> código 0.
  • banco existe e o backup FALHOU -> código 1, deploy travado. É exatamente o
    caso em que subir a versão nova sem rede é a decisão errada.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

KEEP_PADRAO = 14


def _keep_do_ambiente() -> int:
    try:
        return max(1, int(os.environ.get("B3_BACKUP_KEEP", KEEP_PADRAO)))
    except ValueError:
        return KEEP_PADRAO


def diretorio_padrao(db_path: str) -> str:
    """`<pasta do banco>/backups`.

    Derivar do PRÓPRIO banco (em vez de um caminho fixo) garante que o backup
    caia no MESMO volume — no Railway o banco vive no volume via `B3_DB_PATH`,
    e um backup salvo fora dele morreria junto com o container, que é o
    oposto do objetivo.
    """
    return str(Path(db_path).resolve().parent / "backups")


def _podar(out_dir: Path, keep: int) -> int:
    """Mantém os `keep` backups mais recentes. Devolve quantos removeu."""
    arquivos = sorted(out_dir.glob("b3_agente-*.db"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    removidos = 0
    for velho in arquivos[keep:]:
        try:
            velho.unlink()
            removidos += 1
        except OSError:
            pass  # poda é higiene, nunca motivo para falhar um backup bom
    return removidos


def fazer_backup(db_path: Optional[str] = None, out_dir: Optional[str] = None,
                 keep: Optional[int] = None) -> Optional[str]:
    """Backup online consistente. Devolve o caminho gerado, ou `None` quando
    o banco ainda não existe (situação legítima: environment recém-criado).

    Consistência com o servidor no ar: `wal_checkpoint(TRUNCATE)` consolida o
    WAL e a API `.backup()` do SQLite copia sob lock — mesma técnica do
    `scripts/backup-db.sh` original, preservada por ser a correta.
    """
    from . import db as db_mod  # import local: `default_db_path` é puro, sem I/O

    origem = Path(db_path or db_mod.default_db_path())
    if not origem.is_file():
        return None

    destino_dir = Path(out_dir or diretorio_padrao(str(origem)))
    destino_dir.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = destino_dir / f"b3_agente-{carimbo}.db"

    src = sqlite3.connect(str(origem))
    try:
        try:
            src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:
            # Banco sem WAL (ou já consolidado) não impede o backup — a API
            # `.backup()` abaixo é consistente por si só.
            pass
        dst = sqlite3.connect(str(destino))
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()

    _podar(destino_dir, keep if keep is not None else _keep_do_ambiente())
    return str(destino)


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Backup do banco SQLite do Boris+.")
    p.add_argument("--pre-deploy", action="store_true",
                   help="modo Railway: banco ausente não é erro (ver docstring)")
    p.add_argument("--db", default=None, help="caminho do banco (default: B3_DB_PATH)")
    p.add_argument("--out", default=None, help="pasta de destino (default: <dir do banco>/backups)")
    p.add_argument("--keep", type=int, default=None, help=f"quantos manter (default: {KEEP_PADRAO})")
    a = p.parse_args(argv)

    try:
        destino = fazer_backup(a.db, a.out, a.keep)
    except Exception as e:  # noqa: BLE001 — a mensagem É o produto aqui
        print(f"[backup] FALHOU: {type(e).__name__}: {e}", file=sys.stderr)
        if a.pre_deploy:
            print("[backup] deploy TRAVADO de propósito: o banco existe mas não foi "
                  "possível protegê-lo. Suba sem rede só se essa for uma decisão "
                  "consciente (remova o preDeployCommand em server/railway.json).",
                  file=sys.stderr)
        return 1

    if destino is None:
        alvo = a.db or os.environ.get("B3_DB_PATH") or "(default)"
        print(f"[backup] banco ainda não existe em {alvo} — nada a fazer.")
        return 0  # environment novo: seguir é o certo, nos dois modos

    tamanho = Path(destino).stat().st_size
    print(f"[backup] ok -> {destino} ({tamanho / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
