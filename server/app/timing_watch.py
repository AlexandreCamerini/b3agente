"""Aviso de CONDIÇÃO ATINGIDA (push) — o vigia do gatilho.

Roda dentro do `agent.scheduler_loop`, logo depois da passada intraday: mesmo
laço, sem segundo scheduler (mesmo padrão de radar_daily e analysis_outcomes).
Custo por ativo: zero fetch — `timing.montar` lê os dois armazenados globais.

Este módulo existe sob uma revisão de risco explícita. Um push é a única coisa
do app que interrompe a pessoa FORA do app, sem o contexto da tela, e num
produto de mercado isso é a superfície mais perigosa que existe. As regras
abaixo não são preferências:

  • CONSENTIMENTO VEM DO SERVIDOR, NUNCA DA `config`. No aparelho a config é
    LOCAL (`deviceStore.putConfig` grava em localStorage e não chama a API), e
    a audiência do APNs é exatamente essa. Ler `config.notif` aqui avisaria
    sobre ativos que a pessoa removeu, no vocabulário do modo errado, e
    ignoraria o interruptor desligado. A fonte é `push.prefs_for` — alimentada
    pelo registro do token, o único caminho que sempre chega ao servidor.
  • OPT-IN. Classe nova de alerta nasce desligada (`push.PREFS_PADRAO`).
  • O CARIMBO VAI NO TÍTULO. ADR-001: toda afirmação de timing carrega a hora
    da barra, senão insinua tempo real. No iOS o título é a única parte
    garantida na tela de bloqueio — o corpo trunca. Carimbo no corpo é carimbo
    que some.
  • VOCABULÁRIO DE ESTUDO SEMPRE, nos dois modos. Canal interruptivo, fora do
    app, sem o contexto da tela, não é lugar para a linguagem mais assertiva.
    Quem está no Operador tem o app; o push é o menor denominador comum.
  • A FRASE VEM DE `skill_ref.timing_txt`. Redação nova aqui faria a pessoa ler
    um texto na notificação e outro no card — e ela é justamente quem não sabe
    se são a mesma coisa.
  • `esticado` CANCELA em vez de avisar. Entre a barra fechar e o push chegar
    correm ~15 min de atraso do feed mais o intervalo do laço; se nesse tempo o
    preço esticou, avisar seria convocar a pessoa para uma entrada que o
    próprio app desaconselha (Princípio 8).
  • TETO DUPLO e AGREGAÇÃO. Um ativo oscilando em torno da entrada faz
    armado → gatilho → armado → gatilho em barras consecutivas, e cada uma tem
    `asOf` diferente: passaria pelo dedupe legitimamente. Daí o teto por
    (usuário, ticker, DIA). E na primeira barra do dia vários ativos abrem já
    além da entrada — isso vira UMA mensagem, não N banners.

Chave de desligamento: `B3_TIMING_PUSH_KILL=1` (env) OU override em runtime
pelo portal admin (`PUT /api/admin/timing-watch/kill-switch`), persistido em
`admin_config` — mesmo padrão memória→DB→env de `agent.kill_switch_on`
(REPORT-01 C-35: antes deste ponto, o único jeito de reverter o interruptor
do push era redeploy — o mesmo risco que já produziu o incidente do
kill-switch do agente, ligado sem querer por 2,5 dias).
"""
from __future__ import annotations

import asyncio
import os
from typing import Optional

from . import db, intraday, push, skill_ref, timing

# Teto por usuário por dia. Acima disto o aviso vira ruído e a pessoa desliga a
# classe inteira — perder o canal por excesso é pior que perder um evento.
MAX_POR_DIA = 6
# A partir de quantos ativos simultâneos a mensagem agrega em vez de listar.
AGREGA_A_PARTIR_DE = 2
# Estados que interessam ao vigia (os demais não são evento).
ESTADO_ALVO = "gatilho"


# C-35 (REPORT-01): o kill-switch do push de gatilho ganha o MESMO padrão
# memória→DB→env que `agent.kill_switch_on` (ADR-013) já usa, generalizado
# aqui em vez de inventado de novo. Nenhum call site muda de assinatura
# (`kill_switch_on()` continua sem args) — só passa a checar mais uma fonte,
# na ordem memória → DB → env, antes de cair no default (desligado).
_DB_CONN = None
_DB_ENABLED = False
_KILL_MEM = None          # None = sem override explícito ainda; True/False = override achado (DB ou set_kill_switch)
_KILL_DB_CHECKED = False  # já confirmamos que o DB NÃO tem override neste processo? evita reconsultar a cada chamada


def configure_db(conn) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = True


def reset_kill_switch_cache() -> None:
    """Só para testes — mesmo padrão de `agent.reset_kill_switch_cache`: a
    memória NÃO é limpa por `configure_db` de propósito (produção nunca
    deveria perder o cache num reconnect); testes que trocam de banco entre
    casos chamam isto explicitamente para não vazar estado de um teste pro
    outro."""
    global _KILL_MEM, _KILL_DB_CHECKED
    _KILL_MEM = None
    _KILL_DB_CHECKED = False


def set_kill_switch(on: bool, actor: str = None) -> bool:
    """Chamado pela rota admin (`PUT /api/admin/timing-watch/kill-switch`).
    Persiste e atualiza a memória imediatamente — sem esperar o próximo
    boot. `actor` é o user_id de quem mudou (mesmo campo que
    `admin_audit_log` já registra para a transição via `audit.record`).
    A escrita no banco é best-effort (try/except): falhar aqui não pode
    impedir o kill-switch de valer NA MEMÓRIA — é o controle de emergência,
    tem que responder mesmo com o SQLite indisponível."""
    global _KILL_MEM
    _KILL_MEM = bool(on)
    if _DB_ENABLED:
        try:
            db.admin_config_set(_DB_CONN, "timingWatchKillSwitch", bool(on), updated_by=actor)
        except Exception:  # noqa: BLE001 — mesmo padrão de agent.set_kill_switch
            pass
    return _KILL_MEM


def kill_switch_on() -> bool:
    """Memória → DB (best-effort, só até confirmar se existe override) →
    env (SEMPRE lido ao vivo) → default (desligado).

    Mesmos achados de revisão corrigidos em `agent.kill_switch_on`, copiados
    aqui de propósito: (a) a leitura do DB tem try/except — uma falha do
    SQLite não pode propagar pro `scheduler_loop` e pular o ciclo INTEIRO por
    causa só desta checagem; (b) quando ninguém nunca mexeu no toggle
    (override ausente, o caso mais comum), a função bateria no SQLite em TODO
    tick do scheduler sem o `_KILL_DB_CHECKED` — ele faz essa consulta correr
    NO MÁXIMO uma vez por processo quando não há override.

    IMPORTANTE: o resultado do ENV nunca é cacheado em `_KILL_MEM` — só um
    override explícito (do DB ou de `set_kill_switch`) é. `B3_TIMING_PUSH_
    KILL` continua sendo lido AO VIVO em toda chamada sem override.

    Achado de revisão (C-35): a versão anterior aceitava só `== "1"`, mais
    estrita que `agent.kill_switch_on`, que aceita `("1", "true", "TRUE",
    "yes")` após `.strip()`. Ampliação deliberada aqui para os dois
    interruptores terem o MESMO contrato — não é comportamento acidental."""
    global _KILL_MEM, _KILL_DB_CHECKED
    if _KILL_MEM is not None:
        return _KILL_MEM
    if _DB_ENABLED and not _KILL_DB_CHECKED:
        try:
            override = db.admin_config_get(_DB_CONN, "timingWatchKillSwitch")
            if isinstance(override, bool):
                _KILL_MEM = override
                return _KILL_MEM
        except Exception:  # noqa: BLE001
            pass
        _KILL_DB_CHECKED = True
    return (os.environ.get("B3_TIMING_PUSH_KILL") or "").strip() in ("1", "true", "TRUE", "yes")


# ---------------------------------------------------------------- estado por usuário
# `{"dia": "2026-08-05", "ultimo": {TICKER: estado}, "avisados": [TICKER, ...]}`
# `avisados` é o teto por (usuário, ticker, dia); `ultimo` detecta a TRANSIÇÃO.
# Persistido em kv: sobrevive a deploy, que é o que impede o reinício do
# processo de reemitir tudo de novo.
def _estado(conn, uid: str) -> dict:
    e = db.kv_get(conn, "timingWatch", None, user_id=uid)
    return e if isinstance(e, dict) else {"dia": "", "ultimo": {}, "avisados": []}


def _zera_se_virou_o_dia(e: dict, hoje: str) -> dict:
    if e.get("dia") != hoje:
        return {"dia": hoje, "ultimo": {}, "avisados": []}
    return e


def avaliar_usuario(radar_stored, intra_stored, universo, estado: dict,
                    hoje: str, agora=None) -> tuple:
    """NÚCLEO PURO: decide o que notificar. Devolve `(tickers, estado_novo)`.

    Sem I/O, sem rede, sem kv — dá para testar a regra inteira sem servidor.
    """
    e = _zera_se_virou_o_dia(dict(estado or {}), hoje)
    ultimo = dict(e.get("ultimo") or {})
    avisados = list(e.get("avisados") or [])
    novos = []
    for t in universo or []:
        r = timing.montar(radar_stored, intra_stored, t, "estudo", agora=agora)
        atual = r.get("estado")
        # Fora do pregão e barra do dia anterior não são evento de hoje: o
        # `sem_dado` deles carrega evidência velha ou nenhuma.
        if r.get("foraDoPregao") or r.get("barraDeOutroDia"):
            continue
        anterior = ultimo.get(t)
        ultimo[t] = atual
        if atual != ESTADO_ALVO:
            continue
        if anterior == ESTADO_ALVO:
            continue                      # mesma condição, ainda de pé
        if t in avisados:
            continue                      # teto por (usuário, ticker, dia)
        if len(avisados) + len(novos) >= MAX_POR_DIA:
            continue                      # teto por usuário/dia
        novos.append((t, r))
    return novos, {"dia": hoje, "ultimo": ultimo,
                   "avisados": avisados + [t for t, _ in novos]}


def mensagem(novos: list) -> tuple:
    """`(titulo, corpo)` no vocabulário de ESTUDO, com o carimbo no título.

    Um ativo: título com ticker + hora da barra; corpo com a frase canônica.
    Vários (abertura, tipicamente): uma mensagem agregada — N banners
    simultâneos sobre cruzamentos que aconteceram antes de a pessoa acordar
    para o pregão é assédio, não serviço.
    """
    if not novos:
        return None, None
    hora = timing._hora_de((novos[0][1] or {}).get("asOf")) or "—"
    if len(novos) >= AGREGA_A_PARTIR_DE:
        tickers = ", ".join(t for t, _ in novos)
        return (f"{len(novos)} ativos · condição atingida na barra de {hora}",
                f"{tickers}. Leitura da barra de 15m fechada às {hora} — pode ter "
                "mudado desde então. Abra o app para ver o plano de cada um. "
                "Nada foi comprado: a decisão continua sendo sua.")
    t, r = novos[0]
    return (f"{t} · condição atingida na barra de {hora}",
            skill_ref.timing_txt("educacional", ESTADO_ALVO, hora)
            + f" Leitura da barra de 15m fechada às {hora}; pode ter mudado desde "
              "então — confira no app. Nada foi comprado.")


async def rodar(conn, radar_stored, intra_stored, notificar, agora=None) -> int:
    """Varre todos os usuários com consentimento e envia. Devolve quantos avisos.

    `notificar(uid, titulo, corpo, tickers)` é injetado (o laço passa o envio
    real; o teste passa um espião). A varredura é SÍNCRONA e barata (O(1) por
    ativo, zero fetch); só o envio é concorrente — o laço não pode ficar preso
    em N × 10 s de timeout de APNs em série.
    """
    if kill_switch_on():
        return 0
    hoje = (agora or timing._agora_brt()).date().isoformat()
    trabalho = []
    for uid in _usuarios_com_consentimento(conn):
        prefs = push.prefs_for(conn, uid)
        universo = push.universo_valido(prefs, agora=None)
        if not universo:
            continue
        antes = _estado(conn, uid)
        novos, depois = avaliar_usuario(radar_stored, intra_stored, universo,
                                        antes, hoje, agora=agora)
        # Grava SÓ quando muda: um kv_set por usuário por tick seria um commit
        # por usuário na conexão SQLite compartilhada com a API inteira.
        if depois != antes:
            db.kv_set(conn, "timingWatch", depois, user_id=uid)
        if novos:
            titulo, corpo = mensagem(novos)
            trabalho.append((uid, titulo, corpo, [t for t, _ in novos]))
    if not trabalho:
        return 0
    await asyncio.gather(*[notificar(*w) for w in trabalho], return_exceptions=True)
    return len(trabalho)


def _usuarios_com_consentimento(conn) -> list:
    """Só quem LIGOU a classe e tem aparelho registrado.

    A audiência sai das PRÓPRIAS chaves de preferência (`u:<uid>:pushPrefs`),
    não de um `SELECT * FROM users`: quem nunca tocou no interruptor não tem a
    chave, então o conjunto já nasce do tamanho certo em vez de varrer a base
    inteira a cada barra. Contraste deliberado com `radar_daily._push_audience`
    ("todo mundo com token"), que não serve aqui — esta classe é muito mais
    frequente e é a única disparada por evento de mercado.
    """
    try:
        rows = conn.execute(
            "SELECT key FROM kv WHERE key LIKE 'u:%:pushPrefs'").fetchall()
    except Exception:  # noqa: BLE001 — sem kv = sem audiência
        return []
    out = []
    for (chave,) in rows:
        uid = chave[2:-len(":pushPrefs")]
        if not uid or not push.tokens_for(conn, uid):
            continue
        if not push.prefs_for(conn, uid).get("gatilho"):
            continue
        out.append(uid)
    return out


# Última barra já varrida (por processo). A passada intraday roda a cada ~4 min
# (`intraday.GAP_MIN_S`), mas a barra de 15m só muda de 15 em 15: sem este
# gate o vigia varria ~3× por barra. Inofensivo (a transição absorve), mas é
# trabalho jogado fora — e o comentário que dizia o contrário era falso.
_ULTIMA_BARRA = {"asOf": None}


async def maybe_run(conn, radar_stored, intra_stored, notificar, agora=None) -> int:
    """Hook do scheduler. Só dentro do pregão — fora dele não há barra nova."""
    aberto = intraday.in_market_hours(agora) if agora is not None else intraday.in_market_hours()
    if not aberto:
        return 0
    barra = (intra_stored or {}).get("asOf")
    if barra and barra == _ULTIMA_BARRA["asOf"]:
        return 0            # mesma barra já varrida nesta instância
    try:
        n = await rodar(conn, radar_stored, intra_stored, notificar, agora=agora)
    except Exception as e:  # noqa: BLE001 — o vigia nunca derruba o laço
        # A barra NÃO é marcada aqui de propósito: marcar antes de varrer faria
        # uma falha transitória (kv, radar malformado) apagar os gatilhos
        # daquela barra em silêncio, sem nova tentativa no próximo tick.
        print(f"[timing_watch] varredura falhou: {e}")
        return 0
    _ULTIMA_BARRA["asOf"] = barra
    return n
