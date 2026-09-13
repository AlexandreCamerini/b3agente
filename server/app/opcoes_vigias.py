"""Fase 27 — "meus vigias": quem é o dono de cada setup no armazém do MCP.

**O problema.** O armazém de setups do `mcp.semente.dev` é ÚNICO, compartilhado
por todos os clientes do serviço e **não tem campo `owner`** (ADR-027, Decisão
7, comentada no próprio `options_mcp_api.py`). O `name` do setup vem do usuário
(`CAMPOS_OBRIGATORIOS_DO_SETUP`), e `list_setups` devolve nome, condições e
estado — nunca dono, nunca data de criação. Consequências, as duas reais:
dois usuários que escolham "IFR baixo" colidem no mesmo registro, e **o
conceito "meus setups" não existe em lugar nenhum do sistema** — nem no MCP,
nem no Boris. É este segundo fato que produziu a queixa que abriu a fase ("os
setups não estão sendo gravados"): eles estavam gravados, e não havia como
listá-los.

**A solução tem DUAS metades, e elas resolvem coisas diferentes.** Nenhuma
substitui a outra:

1. **O prefixo** (`prefixo`, `nome_no_servico`, `nome_do_usuario`, `e_meu`)
   isola no armazém COMPARTILHADO. É o que impede que A desative o setup de B,
   e é o que dá unicidade a um nome que o serviço aceita repetido. Vive no
   nome que viaja para fora.
2. **O índice local** (`registrar`, `remover`, `listar`) é o único lugar do
   sistema onde existe "meus vigias" com o nome que a PESSOA escreveu, o
   ticker e a data. O serviço não guarda nada disso, então sem o índice a
   listagem não teria o que mostrar além de uma string prefixada.

**Medido em 2026-09-13 (Task 0 da Fase 27, contra o serviço real):** o
`create_setup` aceita `[8 hexadecimais]-[texto]` como `name` e devolve o nome
EXATAMENTE como enviado — sem normalizar, truncar ou reescrever — tanto no
ensaio (`setup_as_interpreted.name`) quanto na gravação (`name`). É essa
fidelidade byte a byte que torna `nome_no_servico`/`nome_do_usuario`
confiáveis nos dois sentidos. Medido também: um nome SEM prefixo continua
aceito, ou seja, o serviço não impõe formato nenhum — a unicidade é
responsabilidade nossa, não dele.

Este módulo é PURO em relação à rede: recebe `conn`, nunca abre conexão, nunca
chama `mcp_client` e nunca importa `options_mcp_api` (seria ciclo).
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from typing import Optional

from . import db

# Seção PRÓPRIA de kv, escopada por `user_id` pelo `db._scoped` — o isolamento
# entre usuários é a CHAVE do registro, não um filtro em memória. Filtro se
# esquece de aplicar num call site novo; chave escapada, não.
SECAO = "opcoesVigias"

PREFIXO_TAM = 8
SEPARADOR = "-"

# Reconhece exatamente o formato que `prefixo()` produz. A estreiteza é o
# ponto, não descuido: `e_legado` decide "tem dono conhecido?" por ESTE regex,
# então qualquer folga aqui (aceitar maiúscula, tamanho variável, outro
# separador) faria um nome escrito por gente ser lido como prefixado. Por isso
# o alfabeto é hexadecimal minúsculo — ninguém batiza um setup de "a3f1c09e-" —
# e por isso a tela mostra sempre o nome da pessoa, nunca o do armazém.
_RE_PREFIXO = re.compile(r"^[0-9a-f]{8}-")


# --------------------------------------------------------------------------
# Metade 1 — o nome no armazém compartilhado. Tudo aqui é puro, sem I/O.
# --------------------------------------------------------------------------

def prefixo(uid) -> str:
    """Prefixo determinístico da conta: `sha256(uid)[:8] + "-"`.

    **sha256 truncado e não o uid** porque o nome VIAJA para um serviço de
    terceiro e fica visível a todos os clientes dele (ADR-027, Decisão 7):
    carimbar identificador de conta — ou e-mail — num nome público é
    vazamento, não organização. Oito hexadecimais dão colisão desprezível para
    a base do Boris e são curtos o bastante para não disputar espaço com o
    nome que a pessoa escreveu.
    """
    digest = hashlib.sha256(str(uid).encode("utf-8")).hexdigest()
    return digest[:PREFIXO_TAM] + SEPARADOR


def nome_do_usuario(uid, nome) -> str:
    """O nome que a PESSOA escreveu, a partir do nome no armazém.

    Tira o prefixo SÓ quando ele é o do próprio `uid`. Nome de outro dono volta
    intacto (o prefixo dele é informação sobre ele, e não vira meu por passar
    por aqui) e nome legado também — idempotente nos dois casos.
    """
    texto = "" if nome is None else str(nome)
    if not uid:
        return texto
    meu = prefixo(uid)
    return texto[len(meu):] if texto.startswith(meu) else texto


def nome_no_servico(uid, nome) -> str:
    """O nome que vai para o `create_setup`: `prefixo(uid) + nome da pessoa`.

    Começa desprefixando o que já for meu, e só então prefixa. Isso não é
    elegância: o ensaio (`/setups/compilar`) devolve o setup para a tela e a
    tela o manda de volta em `/setups/confirmar`. Sem a idempotência, um único
    ida-e-volta produziria `abcdef12-abcdef12-IFR baixo`.
    """
    return prefixo(uid) + nome_do_usuario(uid, nome)


def e_meu(uid, nome) -> bool:
    """`True` só para o prefixo DESTE uid. Nome de outro dono e nome sem
    prefixo nenhum são `False` — são as duas razões diferentes pelas quais um
    registro não entra numa listagem minha."""
    if not uid:
        return False
    return ("" if nome is None else str(nome)).startswith(prefixo(uid))


def e_legado(nome) -> bool:
    """`True` para o nome que não casa formato de prefixo nenhum: setup sem
    dono conhecido, anterior a esta fase ou criado por outro cliente do
    serviço.

    **Não é vestígio — é a única porta que remove um órfão.** Decisão do Alex,
    2026-09-13, literal: *"pode apagar os antigos"*. O que ela significa aqui,
    e as duas metades importam: legado sai de TODA listagem (ninguém precisa
    ver o setup de dono desconhecido), e continua **desativável** por quem tem
    `opcoes.criar_setup`. Sem a segunda metade, um setup antigo que sobre vira
    lixo permanente — ninguém o vê, ninguém o remove pelo produto, e o serviço
    continua avaliando-o todo pregão.

    O que esta função NÃO autoriza: varrer o armazém desativando tudo que ela
    marcar. O armazém "é visto por todos os clientes do serviço"
    (`rbac.py:29-34`), então um nome sem prefixo pode ser de OUTRO sistema —
    não do Boris+ e não do Alex. A limpeza é operacional, com lista na mão, um
    a um, com aprovação. Não há `undo`.
    """
    return _RE_PREFIXO.match("" if nome is None else str(nome)) is None


# --------------------------------------------------------------------------
# Metade 2 — o índice local. Único lugar com "meus vigias".
# --------------------------------------------------------------------------

def _itens(conn: sqlite3.Connection, uid) -> list:
    """A lista crua do kv, sempre uma lista de dicts. Valor corrompido (ou de
    forma antiga) degrada para vazio: o índice é contabilidade, e derrubar a
    aba por causa dele seria trocar um defeito pequeno por um grande."""
    bruto = db.kv_get(conn, SECAO, [], user_id=uid)
    if not isinstance(bruto, list):
        return []
    return [i for i in bruto if isinstance(i, dict)]


def registrar(conn: sqlite3.Connection, uid, *, nome_do_usuario: str,
              nome_no_servico: str, ticker=None, criado_em=None) -> dict:
    """Grava (ou substitui) um vigia no índice DESTE usuário e devolve o item.

    Substitui em vez de duplicar porque o armazém do serviço também não
    duplica: gravar duas vezes o mesmo `name` sobrescreve lá, e dois itens aqui
    para um registro lá seriam duas verdades sobre a mesma coisa.

    **Nenhum campo de estado** (`armed`, `streak`, `status`). Estado é MEDIÇÃO
    do serviço; guardá-lo aqui produziria um "armado" carimbado de ontem
    exibido como se fosse de hoje — princípio 4 do CLAUDE.md. Quem quer estado
    paga a consulta que o mede.
    """
    item = {
        "nome": str(nome_do_usuario or ""),
        "nomeNoServico": str(nome_no_servico or ""),
        "ticker": str(ticker) if ticker else None,
        "criadoEm": str(criado_em) if criado_em else None,
    }
    if not uid or not item["nomeNoServico"]:
        return item
    restantes = [i for i in _itens(conn, uid)
                 if i.get("nomeNoServico") != item["nomeNoServico"]]
    db.kv_set(conn, SECAO, [item] + restantes, user_id=uid)
    return item


def remover(conn: sqlite3.Connection, uid, nome_no_servico) -> bool:
    """Tira do índice. `False` quando não havia o que tirar — e isso é caminho
    NORMAL, não erro: desativar um setup legado (sem dono conhecido) é uma
    operação legítima que nunca teve entrada aqui."""
    if not uid:
        return False
    alvo = "" if nome_no_servico is None else str(nome_no_servico)
    antes = _itens(conn, uid)
    depois = [i for i in antes if i.get("nomeNoServico") != alvo]
    if len(depois) == len(antes):
        return False
    db.kv_set(conn, SECAO, depois, user_id=uid)
    return True


def listar(conn: sqlite3.Connection, uid: Optional[str]) -> list:
    """Os vigias DESTE usuário, mais recente primeiro (ordem de inserção).

    Escopo anônimo devolve `[]` sem levantar: as rotas que gravam exigem
    sessão, então quem não tem conta não tem vigia — e ler o balde anônimo
    aqui misturaria o kv legado de quem nunca logou com o índice de alguém.
    """
    if not uid:
        return []
    return list(_itens(conn, uid))
