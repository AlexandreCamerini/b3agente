"""server/tests/test_ledger_tickers.py — mapa de resolução de tickers do
bootstrap do ledger de sinais (LEDGER-01, Fase 0 v1.2, `00-01-PLAN.md`,
Task 2).

Todo offline: nenhum teste toca rede. Cobre o `<behavior>` do plano:
resolução direta, alias, exclusão, normalização de entrada, disjunção dos
dois mapas e formato das razões de exclusão.
"""
from app import ledger_tickers as lt


def test_resolver_ticker_sem_entrada_no_mapa_resolve_para_si_mesmo():
    assert lt.resolver("PETR4") == ("PETR4", None)


def test_resolver_ticker_com_alias_devolve_simbolo_do_alias():
    for original, alias_esperado in lt.ALIASES.items():
        assert lt.resolver(original) == (alias_esperado, None)


def test_resolver_ticker_excluido_devolve_none_e_razao():
    for original, razao_esperada in lt.EXCLUIDOS.items():
        simbolo, razao = lt.resolver(original)
        assert simbolo is None
        assert razao == razao_esperada


def test_resolver_normaliza_entrada_via_tickers_normalize_ticker():
    assert lt.resolver("petr4 ") == lt.resolver("PETR4")
    assert lt.resolver(" mrfg3") == lt.resolver("MRFG3")


def test_todo_valor_de_excluidos_e_string_nao_vazia_e_cita_a_data_do_diagnostico():
    for razao in lt.EXCLUIDOS.values():
        assert isinstance(razao, str) and razao.strip()
        assert "2026-08-28" in razao


def test_razoes_indeterminado_comecam_com_prefixo_datado():
    for ticker, razao in lt.EXCLUIDOS.items():
        if "INDETERMINADO" in razao or ticker in ("ELET3", "ELET6"):
            assert razao.startswith("não resolvido em 2026-08-28:")


def test_nenhum_simbolo_de_aliases_aparece_tambem_em_excluidos():
    assert set(lt.ALIASES) & set(lt.EXCLUIDOS) == set()


def test_todo_ticker_do_mapa_esta_documentado_no_diagnostico():
    import os

    doc_path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "docs", "DIAGNOSTICO-tickers-ledger-2026-08-28.md",
    )
    with open(doc_path, encoding="utf-8") as f:
        conteudo = f.read()
    for ticker in list(lt.ALIASES) + list(lt.EXCLUIDOS):
        assert ticker in conteudo, f"{ticker} não aparece no diagnóstico"
