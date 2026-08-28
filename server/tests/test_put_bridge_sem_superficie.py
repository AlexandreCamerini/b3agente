"""server/tests/test_put_bridge_sem_superficie.py — guardião de PUT-03
(Fase 10, Plano 03, Task 1).

Este arquivo NÃO testa comportamento de código — testa AUSÊNCIA de
acoplamento entre a ponte gatilho→put (`put_bridge.py`/`put_suggestions.py`)
e qualquer superfície visível ao usuário: rotas HTTP, vocabulário do
assistente, front do app, portal admin, `defaults.py`/`catalog.js` (paridade
de prompts) e as duas agregações do `signal_ledger` que alimentam o ranking
VISÍVEL do Radar (ADR-017).

Por que um teste que lê o FONTE, e não um teste de diff (D-10-M): um diff é
relativo a um ponto no tempo e some no merge seguinte; um teste que abre
`server/app/main.py`/`skill_ref.py` e conta ocorrências continua valendo
amanhã, na Fase 11 e depois dela — é o mesmo raciocínio dos "guardiões de
teste" que o CLAUDE.md do repositório já protege ("guardiões de teste não se
apagam"). Apagar ou afrouxar este arquivo é reverter uma decisão de produto
(PUT-03), não "limpar teste morto" — se algum dia a exposição da sugestão de
put for aprovada (PUTUI-01, fora do escopo de v1.2), o jeito correto de
mexer aqui é ATUALIZAR o teste com uma nota de decisão, nunca apagá-lo.

Duas frentes de prova, deliberadamente redundantes:
  1. Leitura de fonte com contagem de ocorrências (comentários FILTRADOS —
     D-10-N: sem isso, o próprio comentário que explica a regra faz o teste
     passar/falhar sozinho, tornando a documentação auto-invalidante).
  2. Comportamento real: `agent.status_snapshot()` não ganha nenhuma chave
     com "put"; nenhuma rota de `app.main.app.routes` tem "put" no path;
     as agregações do ADR-017 (`signal_ledger.agregar_cumulativo`/
     `agregar_janela`) continuam vendo `porSetup == {}` mesmo depois de
     `put_suggestions` receber linhas — a via de vazamento que nenhum grep
     de front-end pegaria (D-10-A do Plano 01).

Nenhum destes testes toca a rede.
"""
from __future__ import annotations

import os
import pathlib
import re
import sqlite3
import tempfile

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[2]  # raiz do repositório

TOKENS = (
    "put_bridge",
    "put_suggestions",
    "putSuggestion",
    "putBridge",
    "sugestão de put",
    "sugestao_de_put",
)


def _sem_comentarios(texto: str, linguagem: str) -> str:
    """Remove comentários antes de contar ocorrências — sem isso o próprio
    comentário que explica a regra faz o teste passar/falhar sozinho
    (D-10-N). Heurística de linha (não um parser completo): '#'/'//'
    precedidos de espaço ou início de linha são tratados como início de
    comentário; blocos `/* ... */` são removidos, inclusive multi-linha.
    Suficiente para os arquivos-alvo deste guardião (nenhum deles usa '#'
    ou '//' dentro de uma string de forma que colidiria com a heurística)."""
    linhas_saida: list[str] = []
    dentro_bloco = False
    for linha in texto.splitlines():
        if linguagem == "python":
            if dentro_bloco:
                # Python não tem bloco /* */, mas mantém o ramo simétrico
                # para reaproveitar a mesma função sem `if` externo.
                pass
            m = re.search(r"(^|\s)#", linha)
            if m:
                linha = linha[: m.start()]
        elif linguagem == "js":
            if dentro_bloco:
                fim = linha.find("*/")
                if fim == -1:
                    linhas_saida.append("")
                    continue
                linha = linha[fim + 2 :]
                dentro_bloco = False
            m = re.search(r"(^|\s)//", linha)
            if m:
                linha = linha[: m.start()]
            linha = re.sub(r"/\*.*?\*/", "", linha)
            if "/*" in linha:
                idx = linha.find("/*")
                linha = linha[:idx]
                dentro_bloco = True
        linhas_saida.append(linha)
    return "\n".join(linhas_saida)


def _contagens(texto_filtrado: str) -> dict[str, int]:
    return {token: texto_filtrado.count(token) for token in TOKENS}


def _assert_sem_tokens(caminho: pathlib.Path, linguagem: str, contexto: str) -> None:
    texto = caminho.read_text(encoding="utf-8")
    filtrado = _sem_comentarios(texto, linguagem)
    contagens = _contagens(filtrado)
    achados = {tok: n for tok, n in contagens.items() if n > 0}
    assert not achados, (
        f"PUT-03: {contexto} não pode expor a sugestão de put nesta fase — "
        f"token(s) encontrado(s) em {caminho.relative_to(RAIZ)}: {achados}"
    )


def test_main_py_nao_referencia_a_ponte():
    caminho = RAIZ / "server" / "app" / "main.py"
    if not caminho.exists():
        pytest.skip(f"{caminho} não existe neste checkout")
    _assert_sem_tokens(caminho, "python", "nenhuma rota HTTP")


def test_skill_ref_nao_menciona_put_de_protecao():
    caminho = RAIZ / "server" / "app" / "skill_ref.py"
    if not caminho.exists():
        pytest.skip(f"{caminho} não existe neste checkout")
    _assert_sem_tokens(caminho, "python", "o vocabulário visível ao usuário")


def test_front_do_app_nao_referencia_a_ponte():
    base = RAIZ / "web" / "src"
    if not base.exists():
        pytest.skip(f"{base} não existe neste checkout")
    arquivos = sorted(base.rglob("*.js")) + sorted(base.rglob("*.jsx"))
    assert arquivos, f"nenhum .js/.jsx encontrado em {base} — checkout suspeito"
    for caminho in arquivos:
        _assert_sem_tokens(caminho, "js", "o front do app consumidor")


def test_portal_admin_nao_referencia_a_ponte():
    base = RAIZ / "web-admin" / "src"
    if not base.exists():
        pytest.skip(f"{base} não existe neste checkout")
    arquivos = sorted(base.rglob("*.js")) + sorted(base.rglob("*.jsx"))
    if not arquivos:
        pytest.skip(f"nenhum .js/.jsx encontrado em {base}")
    for caminho in arquivos:
        _assert_sem_tokens(caminho, "js", "o portal admin")


def test_defaults_e_catalog_intactos_quanto_a_put():
    defaults_py = RAIZ / "server" / "app" / "defaults.py"
    catalog_js = RAIZ / "web" / "src" / "catalog.js"
    if not defaults_py.exists():
        pytest.skip(f"{defaults_py} não existe neste checkout")
    if not catalog_js.exists():
        pytest.skip(f"{catalog_js} não existe neste checkout")
    _assert_sem_tokens(defaults_py, "python", "a paridade byte-a-byte de prompts (defaults.py)")
    _assert_sem_tokens(catalog_js, "js", "a paridade byte-a-byte de prompts (catalog.js)")


def _chaves_recursivas(obj) -> set[str]:
    """Coleta todas as chaves de dict em qualquer nível (dict aninhado ou
    dentro de lista de dicts) — prova por COMPORTAMENTO real, não por grep,
    que `status_snapshot` nunca ganha uma chave sobre a ponte (D-10-L)."""
    chaves: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            chaves.add(str(k))
            chaves |= _chaves_recursivas(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            chaves |= _chaves_recursivas(item)
    return chaves


def test_status_snapshot_nao_expoe_a_ponte():
    from app import agent, db

    d = tempfile.mkdtemp()
    conn = db.connect(os.path.join(d, "b3.db"))
    try:
        snapshot = agent.status_snapshot(conn)
    finally:
        conn.close()

    chaves = _chaves_recursivas(snapshot)
    achadas = {k for k in chaves if "put" in k.lower()}
    assert not achadas, (
        f"PUT-03: status_snapshot não pode expor a ponte — chave(s) suspeita(s): {achadas}"
    )


def test_nenhuma_rota_serve_a_tabela():
    from app import main

    paths_suspeitos = [
        r.path for r in main.app.routes if "put" in getattr(r, "path", "").lower()
    ]
    assert not paths_suspeitos, (
        f"PUT-03: nenhuma rota pode servir a tabela put_suggestions — path(s) suspeito(s): {paths_suspeitos}"
    )


def test_agregacoes_do_adr017_nao_enxergam_sugestao_de_put():
    from app import db, put_suggestions, signal_ledger

    d = tempfile.mkdtemp()
    conn = db.connect(os.path.join(d, "b3.db"))
    try:
        for i in range(3):
            put_suggestions.registrar(
                conn,
                {
                    "user_id": f"u{i}",
                    "ticker": "PETR4",
                    "data_pregao": "2026-08-28",
                    "setup": "rompimento",
                    "lado": "baixa",
                    "contrato": f"PETRP{i}",
                    "strike": 30.0,
                    "vencimento": "2026-09-19",
                    "estilo_exercicio": "americana",
                    "iv": 0.30,
                    "premio": 1.2,
                    "volume": 500,
                    "spot": 32.0,
                    "fonte": "mydata",
                },
            )
        assert put_suggestions.contar(conn) == 3  # sanity: as linhas gravaram de fato

        cumulativo = signal_ledger.agregar_cumulativo(conn)
        janela = signal_ledger.agregar_janela(conn, 2026)

        assert cumulativo.get("porSetup") == {}, (
            "PUT-03/D-10-A: agregar_cumulativo não pode enxergar linha de put — "
            f"porSetup={cumulativo.get('porSetup')}"
        )
        assert janela.get("porSetup") == {}, (
            "PUT-03/D-10-A: agregar_janela não pode enxergar linha de put — "
            f"porSetup={janela.get('porSetup')}"
        )
    finally:
        conn.close()
