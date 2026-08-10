"""qa/20 (B3) — política de privacidade em URL PÚBLICA.

O App Store Connect exige uma Privacy Policy URL; o texto existia só como
arquivo no repo. A rota serve o PRÓPRIO .md versionado (fonte única) com um
render mínimo — e estes guardiões também impedem o texto de regredir para o
mundo pré-login-obrigatório ("com conta (opcional)", "sem conta").
"""
from fastapi.testclient import TestClient

from app import main
from app.main import _politica_html


def test_rota_publica_serve_html_legivel():
    with TestClient(main.app) as c:
        r = c.get("/privacidade")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Política de Privacidade" in r.text
    assert "Excluir" in r.text or "excluir a" in r.text, "a política tem que citar a exclusão in-app (5.1.1(v))"
    assert "**" not in r.text, "negrito de markdown vazou cru para o HTML"


def test_alias_em_ingles_para_o_revisor():
    with TestClient(main.app) as c:
        assert c.get("/privacy").status_code == 200


def test_politica_nao_promete_mais_o_modo_sem_conta():
    """Login virou obrigatório (F10-20260810-01): publicar uma política dizendo
    'com conta (opcional)' seria metadata falsa — pior que não ter URL."""
    md = main._POLITICA_MD.read_text(encoding="utf-8")
    assert "opcional" not in md.lower()
    assert "Sem conta" not in md
    assert "requer uma conta" in md


def test_render_minimo_cobre_o_dialeto_do_documento():
    html = _politica_html("# Titulo\n\n*Última atualização: X*\n\nPar **forte** aqui.\n\n- item um\n- item dois\n\n## Secao")
    assert "<h1>Titulo</h1>" in html
    assert "<strong>forte</strong>" in html
    assert "<li>item um</li>" in html and "<li>item dois</li>" in html
    assert "<h2>Secao</h2>" in html
    assert "<em>Última atualização: X</em>" in html


def test_render_escapa_html_do_documento():
    html = _politica_html("linha <script>alert(1)</script> perigosa")
    assert "<script>alert" not in html


def test_continuacao_de_item_fica_dentro_do_li():
    """No .md a prosa de um bullet continua nas linhas seguintes, indentada —
    quebrava para fora do <li> e virava parágrafo solto no meio da lista."""
    html = _politica_html("- **E-mail** — para criar\n  sua conta com a Apple.\n- outro item")
    assert "<li><strong>E-mail</strong> — para criar sua conta com a Apple.</li>" in html
    assert html.count("<li>") == 2 and "<p>sua conta" not in html
