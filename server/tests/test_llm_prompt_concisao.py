# FASE 4 (1.4b light) — a instrução de CONCISÃO precisa estar no formato N1.
# Teste de wiring por texto (llm.py importa httpx; ler o fonte mantém a suíte
# verde em qualquer ambiente — padrão "grep de wiring" do projeto).
import os

LLM_PY = os.path.join(os.path.dirname(__file__), "..", "app", "llm.py")


def _src():
    with open(LLM_PY, encoding="utf-8") as f:
        return f.read()


def test_deep_format_tem_instrucao_de_concisao():
    src = _src()
    assert "SEJA CONCISO" in src
    assert "até 3 frases" in src          # resumo
    assert "até 2 frases" in src          # leitura por setup
    assert "1 frase" in src               # cenários/riscos/invalidação


def test_concisao_nao_corta_o_raciocinio():
    # a diretriz didática acompanha o corte — ensina, não amputa
    assert "corte redundância, não corte o raciocínio" in _src()


def test_vocabulario_educacional_permanece_no_formato():
    src = _src()
    for termo in ("Estudar alta", "Estudar baixa", "Monitorar", "Aguardar"):
        assert termo in src
