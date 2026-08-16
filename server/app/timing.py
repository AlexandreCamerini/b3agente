"""F1 — timing de entrada: de "o setup existe" para "a condição ocorreu AGORA".

O que este módulo é — e o que ele deliberadamente NÃO é:

  • DETERMINÍSTICO. Nenhuma LLM decide timing. O gatilho é a condição objetiva
    do plano operacional DIÁRIO (setups.plano_operacional: entrada/stop/lado)
    verificada contra o fechamento da última barra de 15m FECHADA da passada
    intraday global (ADR-001 item 7). Custo por consulta: zero fetch — só kv.
  • CALIBRAGEM-SEGURO. O ADR-002 (Decisão 4) prova que as famílias de
    volatilidade e volume MENTEM em 15m com os limiares do diário. Por isso o
    timing NÃO usa o veredito/confluência 15m como gate: usa apenas preço ×
    nível — a única leitura timeframe-agnóstica disponível hoje. O resumo 15m
    viaja como CONTEXTO (com essa ressalva), nunca como critério.
  • HONESTO SOBRE O ATRASO. O feed intraday tem ~15 min de atraso medido
    (ADR-001, Decisão 2): toda resposta carrega o carimbo `asOf` da barra
    fechada e a ressalva do atraso. Sem carimbo, a frase insinua tempo real.
  • NÃO PERSEGUIR (Princípio 8): gatilho rompido além de 0,5R vira `esticado`
    — o mesmo ZONA_PERSEGUICAO do plano diário, uma fonte só.

Estados (skill_ref.TIMING dá a frase por modo):
  sem_plano  — o Radar diário não tem plano operável para o ativo;
  sem_dado   — sem passada intraday fresca/confiável (lacuna severa conta);
               fora do pregão o estado é o mesmo, mas vem com `foraDoPregao`
               e frase própria: mercado fechado é o normal, não avaria;
  armado     — plano existe, gatilho ainda não atingido na barra fechada;
  gatilho    — barra de 15m FECHADA cruzou a entrada no lado do plano;
  esticado   — cruzou além da zona de perseguição: não entrar.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from . import intraday
from .setups import DECISAO_COMPRAR, DECISAO_VENDER, ZONA_PERSEGUICAO
from . import skill_ref

# Lacuna severa: abaixo desta cobertura a série 15m do dia não é confiável o
# suficiente para afirmar "a condição ocorreu" (ADR-001 item 1d: série furada
# mente com cara de certa).
COBERTURA_MIN = 0.7

RESSALVA_ATRASO = ("Condição verificada na última barra de 15m FECHADA — o feed "
                   "tem ~15 min de atraso medido; não é tempo real.")
RESSALVA_CALIBRAGEM = ("O veredito/confluência 15m é contexto, não critério: os "
                       "limiares de volatilidade/volume são calibrados no diário, "
                       "não no intraday.")


def _agora_brt() -> datetime:
    """Relógio do pregão (BRT) — mesma referência da passada intraday."""
    return datetime.now(intraday.BRT)


def _hora_de(as_of: Optional[str]) -> str:
    """'2026-07-31 15:15' -> '15:15' (rótulo humano da barra fechada)."""
    if not isinstance(as_of, str) or " " not in as_of:
        return ""
    return as_of.split(" ", 1)[1][:5]


def avaliar(plano: Optional[dict], resumo15m: Optional[dict],
            passada_ok: bool = True, pregao_aberto: bool = True,
            data_sessao: Optional[str] = None) -> dict:
    """Núcleo PURO do timing: plano diário × barra 15m fechada => estado.

    `plano` é o dict de setups.plano_operacional/plano_do_resultado (diário);
    `resumo15m` é o resumo por ativo da passada intraday (intraday._resumo);
    `passada_ok` diz se a passada é fresca (intraday.passada_fresca).
    Retorna {estado, ...números que sustentam o estado}; a frase por modo é
    responsabilidade do chamador (montar), para o núcleo ficar sem vocabulário.
    """
    decisao = (plano or {}).get("decisao")
    entrada = (plano or {}).get("entrada")
    risco = (plano or {}).get("riscoPorAcao")
    if decisao not in (DECISAO_COMPRAR, DECISAO_VENDER) or entrada is None or not risco:
        return {"estado": "sem_plano",
                "motivo": (plano or {}).get("motivo") or "Radar diário sem plano operável para o ativo."}

    base = {"lado": plano.get("lado"), "decisaoDiaria": decisao,
            "entrada": entrada, "stop": plano.get("stop"), "riscoPorAcao": risco,
            "setup": plano.get("setup")}
    close = (resumo15m or {}).get("close")
    if not passada_ok or close is None:
        # Fora do pregão a passada VELHA é o esperado, não uma avaria: não há
        # barra nova para verificar a condição enquanto o mercado está fechado.
        # O estado continua `sem_dado` (não há leitura de timing mesmo), mas o
        # motivo/frase deixam de acusar dado ruim — a mensagem antiga fazia o
        # card noturno parecer quebrado todo dia, das 18h às 10h.
        if not pregao_aberto:
            return {**base, "estado": "sem_dado", "foraDoPregao": True,
                    "asOf": (resumo15m or {}).get("asOf"),
                    "motivo": "Fora do pregão — sem barra nova para verificar a condição."}
        return {**base, "estado": "sem_dado",
                "motivo": "Sem passada intraday fresca para o ativo."}
    # A passada ser fresca NÃO garante que a barra seja de hoje: nos primeiros
    # minutos do pregão (e enquanto o atraso do feed corre) a última barra
    # FECHADA ainda é a do pregão anterior. Sem esta checagem o timing afirmaria
    # estado do dia com evidência de ontem — no limite, "GATILHO ATINGIDO" para
    # um cruzamento que aconteceu no fechamento anterior.
    data_barra = str((resumo15m or {}).get("asOf") or "")[:10]
    if data_sessao and data_barra and data_barra != data_sessao:
        return {**base, "estado": "sem_dado", "barraDeOutroDia": True,
                "asOf": (resumo15m or {}).get("asOf"),
                "motivo": ("Última barra de 15m fechada ainda é do pregão anterior "
                           "(%s) — nada de hoje para verificar." % data_barra)}
    cobertura = (resumo15m or {}).get("cobertura")
    if (resumo15m or {}).get("lacuna") and isinstance(cobertura, (int, float)) \
            and cobertura < COBERTURA_MIN:
        return {**base, "estado": "sem_dado", "cobertura": cobertura,
                "motivo": ("Série 15m com lacuna severa (cobertura %.0f%% < %.0f%%) — "
                           "não dá para afirmar que a condição ocorreu."
                           % (cobertura * 100, COBERTURA_MIN * 100))}

    alta = decisao == DECISAO_COMPRAR
    base.update({"fechamento15m": close, "asOf": (resumo15m or {}).get("asOf"),
                 "barraEmFormacao": (resumo15m or {}).get("barraEmFormacao"),
                 "lacuna": bool((resumo15m or {}).get("lacuna")),
                 "cobertura": cobertura})
    cruzou = close >= entrada if alta else close <= entrada
    if not cruzou:
        dist = abs(entrada - close)
        return {**base, "estado": "armado",
                "distancia": round(dist, 2), "distanciaEmR": round(dist / risco, 2)}
    excedente = abs(close - entrada)
    if excedente > ZONA_PERSEGUICAO * risco:
        return {**base, "estado": "esticado",
                "excedente": round(excedente, 2),
                "excedenteEmR": round(excedente / risco, 2)}
    return {**base, "estado": "gatilho",
            "excedente": round(excedente, 2),
            "excedenteEmR": round(excedente / risco, 2)}


def enriquecer_contexto(contexto: dict, resumo15m: Optional[dict],
                        passada_ok: bool) -> dict:
    """F1/A6b: anexa o bloco `intraday15m` ao contexto do N1 e promove
    dataQuality.multiTimeframe quando o 2º timeframe é REAL e confiável.

    PURA e não-mutante: devolve CÓPIA quando enriquece (o contexto original
    vem do cache de snapshot, compartilhado entre superfícies). Sem resumo
    fresco => devolve o contexto original intacto. Lacuna severa anexa o bloco
    (contexto honesto) mas NÃO promove multiTimeframe: série furada não é
    confirmação."""
    if not passada_ok or not resumo15m or resumo15m.get("close") is None:
        return contexto
    novo = dict(contexto)
    dq = dict(novo.get("dataQuality") or {})
    cob = resumo15m.get("cobertura")
    severa = bool(resumo15m.get("lacuna")) and isinstance(cob, (int, float)) \
        and cob < COBERTURA_MIN
    dq["multiTimeframe"] = not severa
    novo["dataQuality"] = dq
    novo["intraday15m"] = {
        **{k: resumo15m.get(k) for k in ("asOf", "barraEmFormacao", "close",
                                         "veredito", "confluencia", "melhorSetup",
                                         "lacuna", "cobertura")},
        # ADR-002 Decisão 4: em 15m, volatilidade/volume têm limiar do diário —
        # o bloco é confirmação de estrutura/momentum, não gate.
        "aviso": RESSALVA_CALIBRAGEM,
    }
    return novo


def montar(radar_stored: Optional[dict], intra_stored: Optional[dict],
           ticker: str, modo: str, agora=None) -> dict:
    """Timing completo de UM ativo a partir dos DOIS armazenados globais
    (Radar diário + passada intraday) — zero fetch, custo O(1) por consulta.
    `modo` ∈ {estudo, operador} escolhe o vocabulário canônico (skill_ref)."""
    item = None
    for r in (radar_stored or {}).get("results") or []:
        if isinstance(r, dict) and r.get("ticker") == ticker:
            item = r
            break
    plano = (item or {}).get("plano")
    resumo = intraday.resumo_do_ticker(intra_stored, ticker)
    fresca = intraday.passada_fresca(intra_stored, agora=agora)
    aberto = intraday.in_market_hours(agora) if agora is not None else intraday.in_market_hours()
    hoje = (agora or _agora_brt()).date().isoformat()
    aval = avaliar(plano, resumo, passada_ok=fresca, pregao_aberto=aberto, data_sessao=hoje)
    if item is None:
        aval = {"estado": "sem_plano",
                "motivo": "Ativo fora do Radar diário armazenado (ou Radar ainda não rodou hoje)."}

    vocabulario = "operador" if modo == "operador" else "educacional"
    estado = aval["estado"]
    # Fora do pregão o estado segue `sem_dado` (não há timing a ler), mas a
    # FRASE e a ressalva mudam: falar de "atraso de 15 min" com o mercado
    # fechado insinua que existiria barra nova se o feed fosse melhor.
    fora = bool(aval.get("foraDoPregao"))
    ontem = bool(aval.get("barraDeOutroDia"))
    chave_frase = estado
    hora_barra = _hora_de(aval.get("asOf"))
    if fora:
        chave_frase = "fora_pregao" if hora_barra else "fora_pregao_sem_hora"
        ressalvas = [("Mercado fechado — a última barra de 15m é de %s." % hora_barra)
                     if hora_barra else "Mercado fechado — sem barra de 15m nova desde o fechamento."]
    elif ontem:
        # Pregão aberto, mas a evidência ainda é do dia anterior: dizer "~15 min
        # de atraso" aqui erraria a idade do dado por horas.
        chave_frase = "aguardando_barra"
        ressalvas = ["Última barra de 15m FECHADA: %s (pregão anterior). A leitura "
                     "de hoje começa quando a primeira barra do dia fechar."
                     % (aval.get("asOf") or "—")]
    else:
        ressalvas = [RESSALVA_ATRASO]
    if aval.get("lacuna"):
        cobertura_pct = aval.get("cobertura")
        if isinstance(cobertura_pct, (int, float)):
            ressalvas.append("Série 15m do dia está incompleta (%.0f%% das barras "
                             "esperadas) — a leitura pode não refletir o pregão inteiro."
                             % (cobertura_pct * 100))
        else:
            ressalvas.append("Série 15m do dia está incompleta — a leitura pode não "
                             "refletir o pregão inteiro.")
    contexto15m = None
    if resumo is not None:
        contexto15m = {"veredito": resumo.get("veredito"),
                       "confluencia": resumo.get("confluencia"),
                       "melhorSetup": resumo.get("melhorSetup"),
                       "aviso": RESSALVA_CALIBRAGEM}
    return {
        "ticker": ticker,
        "modo": vocabulario,
        **aval,
        "frase": skill_ref.timing_txt(vocabulario, chave_frase, hora_barra),
        "ressalvas": ressalvas,
        "contexto15m": contexto15m,
        "vereditoDiario": (item or {}).get("veredito"),
    }
