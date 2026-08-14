"""ADR-011/qa/47 — portal de observabilidade em /admin/* (mesmo container do
backend, sem infra nova). O bundle é PÚBLICO (como o do app consumidor); o
gate de verdade é `_is_obs_admin` nas rotas /api/obs/*, /api/agent/status,
/api/analytics/summary — já cobertos pelos testes dessas rotas. Este arquivo
só cobre o MOUNT: existe, vem antes do catch-all "/", e não intercepta /api.
"""
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_admin_mount_vem_antes_do_mount_raiz():
    """Starlette resolve mounts na ORDEM de registro — se '/' vier antes de
    '/admin', o catch-all engoliria /admin/* inteiro (mesmo bug de classe que
    /ios/manifest.plist já teve que evitar registrando antes de app.mount('/'))."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    i_admin = src.find('app.mount("/admin"')
    i_raiz = src.find('app.mount("/"')
    assert i_admin > 0, "mount de /admin não encontrado"
    assert i_raiz > 0, "mount de '/' não encontrado"
    assert i_admin < i_raiz, "/admin precisa ser registrado ANTES do mount catch-all '/'"


def test_admin_dist_existe_no_repo():
    """server/admin_dist é TRACKED (publicado via scripts/publicar-admin.sh),
    mesma árvore que o Railway serve — se sumir do repo, o portal cai."""
    d = pathlib.Path(__file__).resolve().parents[1] / "admin_dist"
    assert d.exists() and (d / "index.html").exists()


def test_admin_serve_o_bundle():
    c = TestClient(app)
    r = c.get("/admin/")
    assert r.status_code == 200
    assert "Observabilidade" in r.text or "root" in r.text


def test_admin_nao_intercepta_rotas_de_api():
    """Prova que o mount não é um catch-all cego: /api/health continua
    respondendo depois de /admin ser montado."""
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200


def test_admin_assets_sao_servidos():
    c = TestClient(app)
    r = c.get("/admin/")
    # extrai o primeiro <script src="/admin/assets/...js"> do index gerado pelo vite
    import re
    m = re.search(r'src="(/admin/assets/[^"]+\.js)"', r.text)
    assert m, "index.html do portal não referencia nenhum asset JS"
    r2 = c.get(m.group(1))
    assert r2.status_code == 200


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
