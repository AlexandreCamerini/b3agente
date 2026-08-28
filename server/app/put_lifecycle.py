"""server/app/put_lifecycle.py — máquina de decisão PURA do ciclo de vida da
sugestão de put de proteção (Fase 11, Plano 01, Task 2).

A simulação inteira desta fase vive nas colunas novas de `put_suggestions`,
nunca na carteira real do usuário. As três seções que compõem a carteira
visível (posições de ação, caixa e histórico) fazem parte do conjunto de
seções exportado para o front — escrever ali é, por definição, superfície
visível ao usuário, o que contraria o objetivo do milestone ("sem mostrar
nada ao usuário neste milestone"). Além disso, a segunda passada do ciclo do
agente autônomo que avalia posições de opção reais começa lendo a coleção de
posições de opção da carteira e retorna imediatamente quando ela está vazia
— sem uma posição REAL lá dentro, pendurar o ciclo de vida literalmente
nesse caminho faria o monitoramento nunca rodar. A leitura literal não é só
arriscada: é tecnicamente inerte.

O valor de liquidação por vencimento (PUTLIFE-03) vem da mesma função pura
que a carteira real usa para calcular o intrínseco de uma posição de opção
— reusada por import local aqui, nunca copiada. Não existe fórmula de
expiração paralela neste arquivo: qualquer cálculo de `max(0, strike -
spot)` que apareça no resultado vem, literalmente, daquela função.

`put_suggestions` não tem (nem ganha) coluna de quantidade — uma das
garantias estruturais de long-only do ADR-021, Decisão 2 — então o
resultado da simulação é sempre por ação (`preco_fechamento -
preco_entrada`), nunca multiplicado por lote. Nenhum preço médio é
recalculado: uma sugestão é uma entrada única, nunca somada a outra.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import put_suggestions

MOTIVO_VENCIMENTO = "vencimento"  # vocabulário do ADR-005, reusado verbatim


def _numero_positivo(v) -> bool:
    # Copiado de put_bridge.py:46-47 (2 linhas) em vez de importado — put_bridge
    # carrega outros módulos por import local que não têm relação com ciclo de
    # vida, e o predicado é pequeno o bastante para não valer o acoplamento.
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def forma_adr003(linha: dict) -> dict:
    """Forma ADR-003 da posição de opção, a partir de uma linha camelCase de
    `put_suggestions.listar`. É deliberadamente INCOMPLETA: não contém a
    chave de quantidade, e é essa ausência que torna o dict estruturalmente
    incapaz de virar uma posição real — as funções de compra/venda de opção
    do motor dependem dessa chave para operar. `optionType` é forçado em
    código, sempre "put" — esta fase nunca produz a perna oposta."""
    return {
        "id": linha.get("contrato"),
        "underlying": linha.get("ticker"),
        "optionType": "put",
        "strike": linha.get("strike"),
        "expiration": linha.get("vencimento"),
        "avg": linha.get("precoEntrada"),
    }


def resolver_spots(candles: list, vencimento: str, hoje: str) -> dict:
    """PURA, sobre uma lista de candles (`{"date","close",...}`). Devolve o
    fechamento mais recente até `hoje` (`spotAtual`) e o primeiro fechamento
    a partir de `vencimento` (`spotLiquidacao` — cobre vencimento caindo em
    feriado/fim de semana, usando o primeiro pregão seguinte). Candle
    malformado (não-dict, sem `date`, `close` não numérico ou <= 0) é
    PULADO por item, nunca aborta a resolução. Ordem de entrada da lista é
    irrelevante — a busca é por extremos reais, não pelo primeiro/último
    item que casar."""
    spot_atual = None
    data_spot_atual = None
    spot_liquidacao = None
    data_spot_liquidacao = None

    for candle in candles or []:
        if not isinstance(candle, dict):
            continue
        data = candle.get("date")
        fechamento = candle.get("close")
        if not isinstance(data, str) or not data:
            continue
        if not isinstance(fechamento, (int, float)) or isinstance(fechamento, bool) or fechamento <= 0:
            continue

        if data <= hoje and (data_spot_atual is None or data > data_spot_atual):
            spot_atual = float(fechamento)
            data_spot_atual = data

        if data >= vencimento and (data_spot_liquidacao is None or data < data_spot_liquidacao):
            spot_liquidacao = float(fechamento)
            data_spot_liquidacao = data

    return {
        "spotAtual": spot_atual,
        "dataSpotAtual": data_spot_atual,
        "spotLiquidacao": spot_liquidacao,
        "dataSpotLiquidacao": data_spot_liquidacao,
    }


def intrinseco(linha: dict, spot: float) -> float | None:
    """Wrapper fino sobre a função de intrínseco já existente do motor —
    reusar esta função é PUTLIFE-03 no sentido literal: nenhuma fórmula de
    expiração paralela existe neste arquivo. Devolve `None` se `strike`/
    `spot` não forem números positivos (nunca inventa um valor sobre dado
    ausente ou degradado)."""
    strike = linha.get("strike")
    if not _numero_positivo(strike) or not _numero_positivo(spot):
        return None
    # Import local: evita ciclo (o módulo do agente autônomo importa este
    # arquivo pelo hook do Plano 02).
    from .agent import intrinseco_opcao
    return intrinseco_opcao({"strike": strike, "optionType": "put"}, spot)


def _vencida(vencimento, hoje) -> bool:
    if not isinstance(vencimento, str) or not vencimento:
        return False
    if not isinstance(hoje, str) or not hoje:
        return False
    return vencimento <= hoje


def decidir(linha: dict, hoje: str, spots: dict) -> tuple[str | None, dict, str]:
    """Máquina de decisão PURA: para cada linha (camelCase de `listar`/
    `listar_abertas`), devolve `(estado_novo | None, campos, motivo)`.
    `estado_novo` é sempre `None` ou um destino válido em
    `put_suggestions.TRANSICOES[linha["estado"]]`. Nunca levanta: dado
    malformado (`strike`/`premio`/`vencimento`) cai num `(None, {}, motivo)`
    explicado, nunca numa exceção. `campos` já vem no formato aceito por
    `put_suggestions.transicionar` (chaves snake_case de `COLUNAS_CICLO`)."""
    estado_atual = linha.get("estado")

    if estado_atual in put_suggestions.TERMINAIS:
        # Terminal é terminal — nenhuma transição do ROADMAP parte daqui.
        return None, {}, "terminal"

    vencimento = linha.get("vencimento")
    vencida = _vencida(vencimento, hoje)

    if estado_atual == "armada":
        if vencida:
            # ROADMAP: armada → expirada sem uso
            return "expirada_sem_uso", {}, "venceu sem execução"

        premio = linha.get("premio")
        if _numero_positivo(premio):
            # ROADMAP: armada → executada (simulada)
            campos = {"executada_em": hoje, "preco_entrada": premio}
            return "executada_simulada", campos, ""

        # Sem prêmio real de entrada — nunca inventa preço (princípio 4).
        return None, {}, "sem prêmio de entrada"

    # estado_atual está em ("executada_simulada", "monitorada") — os dois
    # únicos estados não-terminais além de "armada".
    if vencida:
        spot_liquidacao = spots.get("spotLiquidacao")
        valor_liquidacao = intrinseco(linha, spot_liquidacao) if spot_liquidacao is not None else None
        if valor_liquidacao is None:
            # Sem preço de liquidação confiável — o chamador registra
            # pendência (put_suggestions.registrar_pendencia), nunca fecha
            # sobre valor inventado.
            return None, {}, "sem preço de liquidação"

        preco_entrada = linha.get("precoEntrada")
        try:
            preco_entrada_num = float(preco_entrada)
        except (TypeError, ValueError):
            preco_entrada_num = 0.0

        campos = {
            "preco_fechamento": valor_liquidacao,
            "motivo_fechamento": MOTIVO_VENCIMENTO,
            "pnl_por_acao": round(valor_liquidacao - preco_entrada_num, 2),
            "spot_marcacao": float(spot_liquidacao),
            "intrinseco_marcacao": valor_liquidacao,
            "marcada_em": spots.get("dataSpotLiquidacao"),
            "fechada_em": hoje,
            "pendente_desde": None,
        }
        # ROADMAP: executada (simulada)/monitorada → fechada
        return "fechada", campos, ""

    spot_atual = spots.get("spotAtual")
    valor_atual = intrinseco(linha, spot_atual) if spot_atual is not None else None
    if valor_atual is None:
        return None, {}, "sem preço do ativo-objeto"

    campos = {
        "spot_marcacao": float(spot_atual),
        "intrinseco_marcacao": valor_atual,
        "marcada_em": spots.get("dataSpotAtual"),
    }
    # ROADMAP: executada (simulada)/monitorada → monitorada (remarcação diária)
    return "monitorada", campos, ""


# --------------------------------------------------------------------------- #
# Fase 11, Plano 02 — varredura diária. Molde estrutural: `put_bridge.py`
# linhas 147-366 (mesmo formato de gate/telemetria/`maybe_run` que nunca
# propaga), com chaves de env/kv PRÓPRIAS — os dois gates são independentes
# de propósito, desligar um não pode desligar o outro.
# --------------------------------------------------------------------------- #

HHMM_DEFAULT = "09:45"                     # depois da ponte (09:30, A-11-08)
K_LAST_RUN = "putLifecycleLastRun"         # chave kv global (user_id=None)
BRT = timezone(timedelta(hours=-3))

# Telemetria em memória (A-11-09): NUNCA entra em `agent.status_snapshot` —
# o portal admin é superfície proibida (PUT-03, D-10-L).
LAST_RUN = {"date": None, "atLabel": None, "duracaoS": None, "erro": None,
            "linhas": None, "avancos": None, "pendentes": None, "porEstado": None}


def _hhmm() -> str:
    raw = (os.environ.get("B3_PUT_LIFECYCLE_HHMM") or HHMM_DEFAULT).strip()
    try:
        h, m = raw.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        return f"{int(h):02d}:{int(m):02d}"
    except Exception:  # noqa: BLE001 — valor inválido cai no default
        return HHMM_DEFAULT


def enabled() -> bool:
    return not os.environ.get("B3_PUT_LIFECYCLE_OFF")


def should_run(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """Gating PURO (testável): dia útil, horário atingido, ainda não rodou hoje.

    Cópia estrutural de `put_bridge.should_run` — chave de env e telemetria
    próprias; NÃO importa `put_bridge` (gates independentes de propósito)."""
    now = now or datetime.now(BRT)
    if now.weekday() >= 5:
        return False
    hh, mm = _hhmm().split(":")
    alvo = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if now < alvo:
        return False
    return last_date != now.date().isoformat()


def last_run_date(conn) -> Optional[str]:
    from . import db  # import local: sem ciclo de import
    return db.kv_get(conn, K_LAST_RUN, user_id=None)


def run_diario(conn, now: Optional[datetime] = None) -> dict:
    """Varre `put_suggestions.listar_abertas` e aplica `decidir()`/
    `transicionar()` por linha. SÍNCRONA de propósito: ao contrário de
    `put_bridge.run_diario` (I/O de rede), esta rodada só lê o cache em
    memória/SQLite sobre dezenas de linhas — não vale o custo de uma thread
    (`asyncio.to_thread`) para um trabalho tão barato, e não há nenhum
    `await` real no corpo.

    Devolve {"linhas": int, "avancos": int, "pendentes": int,
    "porEstado": {estado: n}, "erros": list}."""
    from . import candle_cache  # import local: sem ciclo de import

    hoje = (now or datetime.now(BRT)).date().isoformat()
    linhas = put_suggestions.listar_abertas(conn)

    avancos = 0
    pendentes = 0
    por_estado: dict[str, int] = {}
    erros: list[str] = []

    for linha in linhas:
        try:
            candles = candle_cache.peek(linha.get("ticker"), "1d")
            spots = resolver_spots(candles, linha.get("vencimento"), hoje)
            estado_novo, campos, motivo = decidir(linha, hoje, spots)

            if estado_novo:
                if put_suggestions.transicionar(conn, linha["id"], estado_novo, campos):
                    avancos += 1
                    por_estado[estado_novo] = por_estado.get(estado_novo, 0) + 1
            elif motivo in ("sem preço de liquidação", "sem preço do ativo-objeto"):
                put_suggestions.registrar_pendencia(conn, linha["id"], hoje)
                pendentes += 1
        except Exception as e:  # noqa: BLE001 — isola erro por linha, nunca aborta as demais
            erros.append(f"{linha.get('id')}: {str(e)[:120]}")
            continue

    resumo = {"linhas": len(linhas), "avancos": avancos, "pendentes": pendentes,
              "porEstado": por_estado, "erros": erros}
    print(f"[put-lifecycle] {resumo}")
    return resumo


async def maybe_run(conn) -> Optional[dict]:
    """Hook do scheduler: roda no máximo 1x/dia útil no horário configurado.

    `async` por convenção (o hook do laço chama todos os `maybe_run` da
    mesma forma), mesmo sem nenhum `await` interno — `run_diario` é
    SÍNCRONA. Cópia estrutural de `put_bridge.maybe_run`: `putLifecycleLastRun`
    só é gravado no caminho de SUCESSO; NUNCA propaga exceção — este hook não
    pode derrubar o heartbeat, o kill-switch nem o ciclo de stop/alvo de
    nenhum usuário."""
    from . import db  # import local: sem ciclo de import

    if not enabled():
        return None
    if not should_run(last_date=last_run_date(conn)):
        return None
    try:
        t0 = time.monotonic()
        resumo = run_diario(conn)
        now = datetime.now(BRT)
        LAST_RUN.update(
            date=now.date().isoformat(),
            atLabel=now.strftime("%d/%m %H:%M"),
            duracaoS=round(time.monotonic() - t0, 1),
            linhas=resumo.get("linhas"),
            avancos=resumo.get("avancos"),
            pendentes=resumo.get("pendentes"),
            porEstado=resumo.get("porEstado"),
            erro=None,
        )
        db.kv_set(conn, K_LAST_RUN, now.date().isoformat(), user_id=None)
        return resumo
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_RUN["erro"] = str(e)[:200]
        print(f"[put-lifecycle] rodada diária falhou: {e}")
        return None
