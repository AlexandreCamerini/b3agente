"""Leitura de fonte Python SEM comentários — insumo COMPARTILHADO dos guardiões
estáticos que contam ocorrências em `server/app/main.py`. Não é arquivo de
teste: nenhuma asserção mora aqui.

2026-09-10 (auditoria A-18) — por que este módulo existe. O helper
`_main_source_sem_comentarios()` estava copiado em três arquivos
(`test_fase3_gate_plano.py`, `test_fase12_cap_watchlist.py`,
`test_fase5_gate_mensal.py`) e os três só descartavam a linha que COMEÇA com
`#`. Comentário de CAUDA sobrevivia. Provado pelo auditor: ele removeu a única
chamada real ao gate comercial de análises e deixou no lugar uma linha de
código com o nome da função num comentário de cauda — a asserção de contagem
continuou passando. Ou seja, um bypass do gate que o modelo de ameaças existe
para impedir passava pelo guardião que existe para pegá-lo.

Decisão de desenho: NÃO cortar a linha no primeiro `#` com busca textual.
`#` dentro de string literal é comum (`"#ff0000"`, `"/api/x#frag"`, f-string
com `#`), e cortar ali apagaria CÓDIGO REAL depois da string na mesma linha —
trocaria um jeito de ficar cego por outro, pior, porque a contagem cairia e o
guardião passaria a reprovar/aprovar por motivo errado. O corte usa
`tokenize` (stdlib): só o que o próprio Python classifica como `COMMENT` é
descartado, e a linha é cortada exatamente na coluna desse token. `#` em
string literal não é `COMMENT` e fica intacto.

Diferença de forma em relação às três cópias: antes a linha de comentário
inteira DESAPARECIA (mudando a contagem de linhas); aqui ela vira linha vazia.
Nenhum guardião depende de número de linha — todos usam `.count()` e
`.index()` sobre o texto — e manter a linha preserva a correspondência de
numeração com o arquivo real, o que ajuda a depurar uma falha.
"""
import io
import pathlib
import tokenize


def sem_comentarios(src: str) -> str:
    """`src` sem comentários, preservando todo o resto (inclusive `#` dentro
    de string). Propaga erro de tokenização de propósito: fonte que não
    tokeniza é problema a mostrar, não a contornar — cair num filtro mais
    fraco em silêncio é exatamente como um guardião fica cego (A-18)."""
    cortes: dict = {}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            linha, coluna = tok.start
            if linha not in cortes or coluna < cortes[linha]:
                cortes[linha] = coluna
    fora = []
    for n, linha in enumerate(src.splitlines(), start=1):
        fora.append(linha[:cortes[n]] if n in cortes else linha)
    return "\n".join(fora)


def main_source_sem_comentarios() -> str:
    """`server/app/main.py` sem comentários — o alvo dos guardiões estáticos de
    gate único (C-32, Fase 5, Fase 12)."""
    alvo = pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py"
    return sem_comentarios(alvo.read_text(encoding="utf-8"))
