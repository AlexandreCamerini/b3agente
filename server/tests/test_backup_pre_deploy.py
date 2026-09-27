"""Guardião do backup automático de deploy (2026-09-07).

O que estes testes protegem, e por que cada um existe:

1. O backup NÃO pode migrar o banco antes de copiá-lo. `db.connect()` chama
   `init_db()`, que roda `ALTER TABLE ... ADD COLUMN` e
   `_migrate_identities_from_users`. Um backup tirado DEPOIS disso guarda o
   estado NOVO — inútil para voltar à versão anterior, que é o único motivo
   de o backup existir. Este é o teste central do arquivo.

2. Banco ausente não pode travar o deploy. O primeiro deploy de um
   environment novo (ex.: staging recém-criado) não tem banco; se o comando
   de backup falhasse aí, o ambiente nunca nasceria.

3. Banco presente + backup falho TEM que travar o deploy. É exatamente o caso
   em que subir sem rede de segurança é a decisão errada.

4. A FIAÇÃO em `server/railway.json` e `.railway/railway.ts` — sem ela o
   módulo é código morto e ninguém percebe até precisar de um backup que
   nunca foi feito.

CORREÇÃO DELIBERADA (o pré-deploy nunca funcionou) (2026-09-27): o backup era ligado como `preDeployCommand`
(modo `--pre-deploy`). A doc oficial do Railway
(docs.railway.com/deployments/pre-deploy-command) diz que o pré-deploy roda
"in a separate container from your application" e que "volumes are not
mounted" — `/data` só existe no container da aplicação. Medido em produção e
staging desde 2026-09-13: todo `preDeployCommand` imprimia "banco ainda não
existe" e saía 0, ou seja, NENHUM backup real rodou. O backup migrou para o
INÍCIO do `startCommand` (modo `--pre-start`, mesma semântica de saída);
`--pre-deploy` sobrevive só como alias de compatibilidade da flag.
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app import backup as backup_mod

SERVER_DIR = Path(__file__).resolve().parent.parent


def _banco_velho(caminho: Path) -> None:
    """Banco com schema ANTIGO: só `kv`, sem nenhuma das tabelas/colunas que
    `init_db()` acrescentaria."""
    conn = sqlite3.connect(str(caminho))
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO kv VALUES ('marcador', 'estado-anterior')")
    conn.commit()
    conn.close()


def _tabelas(caminho: Path) -> set:
    conn = sqlite3.connect(str(caminho))
    try:
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_backup_nao_migra_o_banco_antes_de_copiar(tmp_path):
    """O CORAÇÃO deste guardião: o backup precisa registrar o estado ANTERIOR.

    Se algum dia alguém trocar o `sqlite3.connect` cru de `fazer_backup` por
    `db.connect()` (parece inofensivo — "reusar o helper do projeto"), este
    teste falha: o backup passaria a conter as tabelas que `init_db()` cria.
    """
    origem = tmp_path / "velho.db"
    _banco_velho(origem)

    destino = backup_mod.fazer_backup(str(origem), str(tmp_path / "bk"))

    assert destino is not None
    assert _tabelas(Path(destino)) == {"kv"}, (
        "o backup contém tabelas que o banco de origem não tinha — alguém fez "
        "o backup migrar o banco antes de copiar, e isso destrói o propósito "
        "de poder voltar à versão anterior")

    conn = sqlite3.connect(destino)
    try:
        valor = conn.execute("SELECT value FROM kv WHERE key='marcador'").fetchone()[0]
    finally:
        conn.close()
    assert valor == "estado-anterior"


def test_backup_nao_altera_o_banco_de_origem(tmp_path):
    origem = tmp_path / "velho.db"
    _banco_velho(origem)
    antes = origem.read_bytes()

    backup_mod.fazer_backup(str(origem), str(tmp_path / "bk"))

    # `wal_checkpoint` pode consolidar o WAL, mas o CONTEÚDO lógico não muda.
    assert _tabelas(origem) == {"kv"}
    conn = sqlite3.connect(str(origem))
    try:
        assert conn.execute("SELECT value FROM kv WHERE key='marcador'").fetchone()[0] == "estado-anterior"
    finally:
        conn.close()
    assert len(antes) > 0


def test_banco_ausente_devolve_none_sem_levantar(tmp_path):
    assert backup_mod.fazer_backup(str(tmp_path / "nao-existe.db"), str(tmp_path / "bk")) is None


def test_pre_start_com_banco_ausente_sai_zero(tmp_path):
    """Environment novo (staging recém-criado) precisa conseguir nascer."""
    rc = backup_mod.main(["--pre-start", "--db", str(tmp_path / "nao-existe.db"),
                          "--out", str(tmp_path / "bk")])
    assert rc == 0


def test_pre_start_com_banco_presente_e_backup_falho_trava_o_deploy(tmp_path):
    """Destino não-gravável com banco real presente => código 1."""
    origem = tmp_path / "velho.db"
    _banco_velho(origem)
    somente_leitura = tmp_path / "ro"
    somente_leitura.mkdir()
    somente_leitura.chmod(0o500)
    try:
        rc = backup_mod.main(["--pre-start", "--db", str(origem),
                              "--out", str(somente_leitura / "sub")])
        assert rc == 1, ("banco existe e o backup falhou — o deploy TEM que "
                         "travar, senão a versão nova sobe sem rede")
    finally:
        somente_leitura.chmod(0o700)


def test_pre_deploy_continua_aceito_como_alias_de_pre_start(tmp_path):
    """Compatibilidade: quem ainda invoca `--pre-deploy` não pode quebrar."""
    rc = backup_mod.main(["--pre-deploy", "--db", str(tmp_path / "nao-existe.db"),
                          "--out", str(tmp_path / "bk")])
    assert rc == 0


def test_retencao_mantem_apenas_os_mais_recentes(tmp_path):
    origem = tmp_path / "velho.db"
    _banco_velho(origem)
    destino_dir = tmp_path / "bk"
    for _ in range(5):
        backup_mod.fazer_backup(str(origem), str(destino_dir), keep=3)
        # carimbo tem resolução de 1s; forçar nomes distintos sem dormir 5s
        for i, p in enumerate(sorted(destino_dir.glob("b3_agente-*.db"))):
            import os
            os.utime(p, (p.stat().st_atime, p.stat().st_mtime - i))
    assert len(list(destino_dir.glob("b3_agente-*.db"))) <= 3


def test_destino_padrao_fica_no_mesmo_volume_do_banco():
    """No Railway o banco vive no volume via `B3_DB_PATH`; um backup fora dele
    morreria com o container. Derivar do próprio banco garante o mesmo volume."""
    assert backup_mod.diretorio_padrao("/data/b3_agente.db") == "/data/backups"


def test_railway_json_liga_o_backup_no_start():
    """Guardião de FIAÇÃO: sem isto o módulo vira código morto e o backup
    nunca roda em produção — falha que só aparece quando já é tarde.

    Reversão deliberada (2026-09-27): não pode mais estar em
    `preDeployCommand` — o pré-deploy do Railway roda em container separado e
    não monta volume (doc oficial), então nunca protegeria o banco real."""
    cfg = json.loads((SERVER_DIR / "railway.json").read_text())
    cmd = cfg["deploy"]["startCommand"]
    assert cmd.startswith("(python -m app.backup --pre-start || python3 -m app.backup --pre-start) &&"), (
        "o backup precisa rodar ANTES do uvicorn, no início do startCommand")
    assert "uvicorn app.main:app" in cmd
    assert "preDeployCommand" not in cfg["deploy"], (
        "o pré-deploy do Railway não monta volume — backup ligado ali é "
        "código morto que nunca protege o banco real")


def test_railway_ts_liga_o_backup_no_start():
    """Guardião de FIAÇÃO equivalente para o IaC (`.railway/railway.ts`),
    que substitui `server/railway.json` — mesma nota da reversão de
    2026-09-27 acima."""
    texto = (SERVER_DIR.parent / ".railway" / "railway.ts").read_text()
    assert 'start: "(python -m app.backup --pre-start || python3 -m app.backup --pre-start) && uvicorn app.main:app' in texto, (
        "o backup precisa rodar ANTES do uvicorn, no início do `start`")
    assert "preDeploy:" not in texto, (
        "o pré-deploy do Railway não monta volume — backup ligado ali é "
        "código morto que nunca protege o banco real")


def test_modulo_roda_como_entrypoint_de_linha_de_comando(tmp_path):
    """`python -m app.backup` é literalmente o que o Railway invoca."""
    origem = tmp_path / "velho.db"
    _banco_velho(origem)
    r = subprocess.run(
        [sys.executable, "-m", "app.backup", "--pre-start",
         "--db", str(origem), "--out", str(tmp_path / "bk")],
        cwd=str(SERVER_DIR), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "[backup] ok ->" in r.stdout
