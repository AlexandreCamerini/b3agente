"""quick 261009-mvb — site de marketing estático servido em /site/ (mesmo
serviço do Boris). Guardiões: o mount existe ANTES do catch-all "/", a árvore
mora dentro de server/ (rootDirectory=/server do Railway) e o site é
autocontido (sem CDN), e a Privacy URL continua sendo /privacidade."""
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)
SITE = Path(main.__file__).resolve().parent.parent / "site_dist"


def test_site_dist_mora_dentro_de_server():
    assert SITE.is_dir(), "rode scripts/publicar-site.sh (server/site_dist ausente)"
    assert main._SITE_DIST == SITE
    assert (SITE / "index.html").is_file()


def test_paginas_do_site_respondem_em_site():
    for path, marca in [
        ("/site/", "Boris"),
        ("/site/tour.html", "O app por dentro"),
        ("/site/app/", "Treinamento"),
        ("/site/app/guia.html", "Guia das telas"),
        ("/site/app/conceitos.html", "Conceitos de mercado"),
        ("/site/css/inapp.css", "appbar"),
        ("/site/js/telas-data.js", "window.TELAS"),
        ("/site/js/guia.js", "boris-guia-v1"),
                ("/site/suporte.html", "Suporte"),
        ("/site/privacidade.html", "Termos de uso"),
        ("/site/css/site.css", "--brand-amber"),
        ("/site/js/treinamento.js", "boris-treino-v1"),
    ]:
        r = client.get(path)
        assert r.status_code == 200, path
        assert marca in r.text, path


def test_site_nao_sequestrado_pelo_catch_all_e_api_segue_404():
    # se o mount /site viesse depois do "/", cairia no shell do app
    assert "Treine com o mercado real" in client.get("/site/").text
    r = client.post("/api/rota/que/nao/existe")
    assert r.status_code == 404


def test_privacy_url_continua_sendo_a_rota_do_servidor():
    assert client.get("/privacidade").status_code == 200
    html = (SITE / "suporte.html").read_text(encoding="utf-8")
    assert 'href="/privacidade"' in html
    assert 'name="author" content="semente.dev"' in html


def test_site_autocontido_sem_url_externa_e_sem_prometer_lucro():
    for f in SITE.rglob("*"):
        if f.suffix in {".html", ".css", ".js"}:
            txt = f.read_text(encoding="utf-8")
            achados = [u for u in re.findall(r"https?://[^\s\"')]+", txt) if "w3.org" not in u and not u.startswith("https://semente.dev")]
            assert not achados, f"{f.name} referencia URL externa: {achados}"
    home = (SITE / "index.html").read_text(encoding="utf-8").lower()
    for proibido in ("lucro garantido", "retorno garantido", "enriqueça", "fique rico"):
        assert proibido not in home
