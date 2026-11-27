"""FASE 3.3b — Push (APNs) para as ações do agente. Sub-fase condicionada à
conta Apple Developer PAGA (confirmada pelo Alex). No-op se não configurado.

Env necessárias (Railway → Variables):
  APNS_TEAM_ID    — Team ID da conta Apple Developer
  APNS_KEY_ID     — Key ID da chave de push (.p8)
  APNS_AUTH_KEY   — conteúdo do .p8 (colar o PEM inteiro) OU caminho do arquivo
  APNS_TOPIC      — bundle id do app (ex.: com.alexandrecamerini.bolsia)
  APNS_SANDBOX    — "1" para o ambiente de desenvolvimento (TestFlight usa produção)

Tokens de aparelho ficam na seção kv `pushTokens` por usuário (cap 5,
registrados via POST /api/push/register-token). Ver APNS-PUSH.md para o
passo a passo (chave no portal, capability no Xcode, plugin no app).
"""
import json
import os
import time
from typing import Optional

from . import db

_JWT_CACHE = {"token": None, "at": 0.0}


def is_configured() -> bool:
    return all(os.environ.get(k) for k in ("APNS_TEAM_ID", "APNS_KEY_ID", "APNS_AUTH_KEY", "APNS_TOPIC"))


def _auth_key() -> str:
    raw = os.environ.get("APNS_AUTH_KEY") or ""
    if raw.strip().startswith("-----BEGIN"):
        return raw
    try:
        with open(raw, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return raw


def _jwt() -> str:
    """JWT ES256 do APNs, cacheado por ~45min (Apple aceita até 60)."""
    now = time.time()
    if _JWT_CACHE["token"] and now - _JWT_CACHE["at"] < 45 * 60:
        return _JWT_CACHE["token"]
    import jwt  # PyJWT[crypto] — já nas requirements
    token = jwt.encode(
        {"iss": os.environ["APNS_TEAM_ID"], "iat": int(now)},
        _auth_key(),
        algorithm="ES256",
        headers={"kid": os.environ["APNS_KEY_ID"]},
    )
    _JWT_CACHE.update(token=token, at=now)
    return token


def _host() -> str:
    return "https://api.sandbox.push.apple.com" if os.environ.get("APNS_SANDBOX") == "1" else "https://api.push.apple.com"


# ------------------------- tokens por usuário (kv) -------------------------
def register_token(conn, user_id: str, token: str) -> list:
    toks = db.kv_get(conn, "pushTokens", [], user_id=user_id) or []
    token = (token or "").strip()
    if token and token not in toks:
        toks = (toks + [token])[-5:]
        db.kv_set(conn, "pushTokens", toks, user_id=user_id)
    return toks


def tokens_for(conn, user_id: str) -> list:
    return db.kv_get(conn, "pushTokens", [], user_id=user_id) or []


# ------------------- preferências e universo do push (kv) -------------------
# Por que isto existe (revisão do supervisor, 2026-08-05): no aparelho a
# `config` é LOCAL — `deviceStore.putConfig` grava em localStorage e NUNCA
# chama a API (persistence.js). Ou seja: a audiência do APNs é exatamente
# aquela cuja preferência, watchlist e modo o servidor não consegue ler. Um
# push server-side decidido por `config` avisaria sobre ativos que a pessoa
# removeu, no vocabulário do modo errado, e ignoraria o interruptor desligado.
#
# O único caminho que SEMPRE chega ao servidor é o registro do token
# (`registerPushToken`, nos dois stores). Então é por ele que a preferência, o
# modo e o universo viajam. Opt-in por decisão de produto: classe nova de
# alerta nasce DESLIGADA — o padrão `False` aqui é deliberado.
#
# NOTA (quick task 260824-kc2, 2026-08-24) — por que `radar`, `execucao` e
# `protecao` nascem LIGADAS sem violar a regra do opt-in logo acima. Elas não
# são alertas NOVOS: já existiam e já chegavam a todo mundo com token
# registrado, porque os três call sites (Radar diário, ordem pendente e ciclo
# do Operador) não consultavam preferência nenhuma. O que nasce agora é o
# CONTROLE, não o alerta — fazê-las nascer `False` TIRARIA notificação de quem
# a recebe hoje, que é o oposto exato da decisão do Alex. A regra do opt-in
# continua valendo para uma classe de alerta genuinamente nova no futuro, e
# `gatilho` continua sendo o exemplo vivo dela (nasce `False`).
#
# A migração de quem já existe sai DE GRAÇA: `prefs_for` faz
# `{**PREFS_PADRAO, **p}`, então preferência gravada antes desta mudança herda
# as três chaves novas com o default certo. Nenhuma migração de dado escrita —
# o default É a migração.
#
# Fase 51 (D-13) — `fechamento` (push "Seu dia na bolsa") é opt-in GENUÍNO e
# nasce `False` aqui. O contrário do que `radar`/`execucao`/`protecao` fazem:
# o merge `{**PREFS_PADRAO, **p}` ligaria o push para TODA conta antiga sem a
# chave gravada, sem ninguém ter consentido. Conta nova recebe True por
# gravação explícita (`auth.py` -> `decidir_fechamento`). `fechamento` e
# `fechamentoDecidido` ficam FORA de PREFS_BOOLS de propósito: o consentimento
# só é gravado por `decidir_fechamento` (convite / criação de conta); o
# `register-token` repassa `body.prefs` inteiro a `set_prefs`, e com a chave na
# allowlist qualquer sync do aparelho sobrescreveria a decisão do usuário.
PREFS_PADRAO = {"gatilho": False, "radar": True, "execucao": True,
                "protecao": True, "fechamento": False,
                "fechamentoDecidido": False,
                "modo": "estudo", "universo": [], "at": None}
# Chaves booleanas da preferência (allowlist do `set_prefs`), na ordem em que
# nasceram. `gatilho` primeiro por ser a original; as três classes de conta
# depois.
PREFS_BOOLS = ("gatilho", "radar", "execucao", "protecao")
UNIVERSO_MAX = 60
VALIDADE_DIAS = 7   # universo mais velho que isto não vale (aparelho sumiu)


def prefs_for(conn, user_id: str) -> dict:
    p = db.kv_get(conn, "pushPrefs", None, user_id=user_id)
    if not isinstance(p, dict):
        return dict(PREFS_PADRAO)
    return {**PREFS_PADRAO, **p}


def set_prefs(conn, user_id: str, patch: dict) -> dict:
    """Aplica um patch de preferências do push. Allowlist explícita: chave
    desconhecida é descartada (mesma disciplina do store.set_config).

    O patch é PARCIAL por CONTRATO, não por acidente (260824-kc2): chave
    ausente fica exatamente como estava. É esse contrato que permite ao web
    escrever só as três classes de conta (`radar`/`execucao`/`protecao`) sem
    encostar em `gatilho`, `modo` e `universo` — que continuam sendo autoridade
    do APARELHO, porque só ele registra token APNs (`web/src/notify.js`
    devolve `{ok:false}` fora do nativo antes de qualquer chamada). Sem a
    parcialidade, o primeiro acesso pelo navegador apagaria em silêncio o
    gatilho que o iPhone tinha ligado.
    """
    p = prefs_for(conn, user_id)
    patch = patch if isinstance(patch, dict) else {}
    # Consentimento do fechamento nunca entra por aqui (ver PREFS_PADRAO): só
    # `decidir_fechamento` grava. Descarta antes da allowlist, por defesa.
    patch = {k: v for k, v in patch.items()
             if k not in ("fechamento", "fechamentoDecidido")}
    for k in PREFS_BOOLS:
        if k in patch:
            p[k] = bool(patch[k])
    if patch.get("modo") in ("estudo", "operador"):
        p["modo"] = patch["modo"]
    if isinstance(patch.get("universo"), list):
        vistos, uni = set(), []
        for t in patch["universo"]:
            t = str(t or "").strip().upper()[:12]
            if t and t not in vistos:
                vistos.add(t)
                uni.append(t)
        p["universo"] = uni[:UNIVERSO_MAX]
    p["at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    db.kv_set(conn, "pushPrefs", p, user_id=user_id)
    return p


# -------------------- fechamento: consentimento e teto de engajamento -------
TETO_ENGAJAMENTO_DIA = 2


def quer_fechamento(conn, user_id: str) -> bool:
    """FAIL-CLOSED: opt-in genuíno, na dúvida NÃO envia. É o oposto do gate do
    Radar (`radar_daily._quer_radar`, fail-open): lá a falha tiraria um aviso
    que o usuário já recebia; aqui enviaria sem consentimento."""
    try:
        return prefs_for(conn, user_id).get("fechamento") is True
    except Exception:  # noqa: BLE001
        return False


def estado_fechamento(conn, user_id: str) -> dict:
    p = prefs_for(conn, user_id)
    return {"ligado": p.get("fechamento") is True,
            "decidido": p.get("fechamentoDecidido") is True}


def decidir_fechamento(conn, user_id: str, ligado: bool) -> dict:
    """Única porta de gravação do consentimento do fechamento (convite e
    criação de conta). Grava direto no kv, sem passar por `set_prefs`."""
    p = prefs_for(conn, user_id)
    p["fechamento"] = bool(ligado)
    p["fechamentoDecidido"] = True
    p["at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    db.kv_set(conn, "pushPrefs", p, user_id=user_id)
    return p


def reservar_engajamento(conn, user_id: str, hoje: str, tipo: str) -> bool:
    """Teto de TETO_ENGAJAMENTO_DIA pushes de engajamento por conta/dia,
    compartilhado entre o Radar 08:45 e o fechamento. True = reservou (pode
    enviar); False = tipo já enviado hoje ou teto atingido."""
    est = db.kv_get(conn, "pushEngajamento", None, user_id=user_id)
    if not isinstance(est, dict) or est.get("dia") != hoje:
        est = {"dia": hoje, "tipos": []}
    tipos = [t for t in (est.get("tipos") or []) if isinstance(t, str)]
    if tipo in tipos or len(tipos) >= TETO_ENGAJAMENTO_DIA:
        return False
    tipos.append(tipo)
    db.kv_set(conn, "pushEngajamento", {"dia": hoje, "tipos": tipos},
              user_id=user_id)
    return True


# -------------------- tag do evento → classe de consentimento ----------------
# Tabela ÚNICA (260824-kc2), e mora aqui — não em `agent.py` — por duas razões:
# consentimento é assunto DESTE módulo, e os dois funis de push do scheduler
# (ordem pendente e ciclo do Operador) precisam da MESMA tabela; duas cópias
# divergiriam no primeiro evento novo.
CLASSE_POR_TAG = {
    "stop": "protecao",
    "alvo": "protecao",
    "protecao-opcao": "protecao",
    "entrada-auto": "execucao",
    "pendente-executada": "execucao",
    "pendente-cancelada": "execucao",
}


def classe_do_evento(tag) -> Optional[str]:
    """Classe de consentimento de um evento, derivada da `tag` que ele carrega.

    Degradação DEFINIDA, no mesmo idioma de `skill_ref.push_titulo`: tag
    ausente ou desconhecida devolve `None` — e `None` significa **FAIL-OPEN**,
    ou seja, o push SAI. Uma tag que ninguém mapeou não é uma classe que o
    usuário desligou; silenciar por omissão de tabela seria tirar aviso SEM
    consentimento, que é o mais caro dos dois erros possíveis aqui.

    O PREÇO desse desenho, escrito para o próximo leitor: **todo evento que
    vira push precisa de `tag`**, senão escapa do controle. Foi exatamente o
    caso do evento de venda de opção (`agent.py`, `_avaliar_opcoes`), que saía
    sem `tag` e por isso ignorava o interruptor "Proteção" do usuário —
    corrigido com `tag: protecao-opcao` no mesmo quick task que criou esta
    tabela. A classe do Radar (`radar`) não entra aqui: o push da prévia não
    passa por funil de evento, é gate direto em `radar_daily.run_daily`.
    """
    return CLASSE_POR_TAG.get(str(tag or "").strip())


def universo_valido(prefs: dict, agora: Optional[float] = None) -> list:
    """Universo só vale se foi renovado recentemente — aparelho que parou de
    abrir o app não deve continuar gerando push sobre uma lista congelada."""
    at = (prefs or {}).get("at")
    if not at:
        return []
    try:
        import calendar  # `at` é gravado em UTC (gmtime): timegm, não mktime
        t = calendar.timegm(time.strptime(at, "%Y-%m-%dT%H:%M:%S"))
    except (ValueError, TypeError):
        return []
    if ((agora if agora is not None else time.time()) - t) > VALIDADE_DIAS * 86400:
        return []
    return list((prefs or {}).get("universo") or [])


# --------------------------------- envio -----------------------------------
# FASE 6 (fix 5): tradutor dos `reason` do APNs em instrução EXATA (pt-BR).
# O caso que motivou: BadEnvironmentKeyInToken — a chave .p8 foi criada no
# portal Apple RESTRITA a um ambiente (Development ou Production) e o servidor
# está falando com o host do outro ambiente. Não é problema do token do
# aparelho: trocar APNS_SANDBOX ou gerar chave sem restrição resolve.
_REASON_HELP = {
    "BadEnvironmentKeyInToken": (
        "a chave .p8 (APNS_AUTH_KEY) é RESTRITA a um ambiente e não bate com o host em uso. "
        "Corrija no portal Apple (Keys → sua chave APNs → Environment: 'Sandbox & Production') "
        "OU alinhe APNS_SANDBOX no Railway: 1 = build do Xcode (sandbox); remova a variável = TestFlight/App Store (produção)."
    ),
    "BadDeviceToken": (
        "a Apple recusou o token deste aparelho nos DOIS ambientes (o servidor já tenta produção e sandbox, "
        "independente de APNS_SANDBOX) — token velho, de outro app ou de outra conta. "
        "Toque de novo em 'Ativar push neste aparelho' — o token inválido foi descartado."
    ),
    "Unregistered": "o aparelho removeu o app ou o token expirou — token descartado; reative o push no aparelho.",
    "DeviceTokenNotForTopic": "o token não pertence a este app (APNS_TOPIC) — token descartado; confira o bundle id e reative o push.",
    "BadTopic": "APNS_TOPIC inválido — deve ser exatamente o bundle id do app (com.alexandrecamerini.bolsia).",
    "TopicDisallowed": "a chave APNs não tem direito sobre este APNS_TOPIC — confira o App ID no portal Apple.",
    "InvalidProviderToken": "APNS_TEAM_ID / APNS_KEY_ID / APNS_AUTH_KEY não batem entre si — confira os três no Railway com os valores do portal Apple.",
    "ExpiredProviderToken": "JWT do provedor expirado — transitório; se persistir, confira o relógio do servidor.",
    "MissingTopic": "faltou APNS_TOPIC no Railway.",
}
# reasons que INVALIDAM o token do aparelho (aí sim descartamos):
_DROP_TOKEN_REASONS = ("BadDeviceToken", "Unregistered", "DeviceTokenNotForTopic")


def explain_reason(reason: str) -> str:
    """Instrução acionável para um reason do APNs ('' se desconhecido)."""
    return _REASON_HELP.get((reason or "").strip(), "")


def env_label() -> str:
    return "sandbox (APNS_SANDBOX=1)" if os.environ.get("APNS_SANDBOX") == "1" else "produção"


def _outro_host() -> str:
    """Host do ambiente que NÃO é o principal — alvo do fallback de BadDeviceToken."""
    return "https://api.push.apple.com" if os.environ.get("APNS_SANDBOX") == "1" else "https://api.sandbox.push.apple.com"


def _outro_label() -> str:
    return "produção" if os.environ.get("APNS_SANDBOX") == "1" else "sandbox"


# Entrega por `kind` do evento (quick 261127 — legibilidade do push no iPhone).
# `interruption-level`: "passive" entra na lista sem acender a tela nem tocar —
# é o que cabe a leitura informativa (timing, prévia do Radar, resumo do
# fechamento); "active" é o padrão do iOS e fica para operação JÁ executada.
# NUNCA "time-sensitive": exige entitlement próprio e furaria o Foco — simulador
# educacional não tem urgência que justifique isso. `expira_s` só no timing:
# "condição atingida às 11:15" entregue às 12:00 afirma o que já não vale.
# `kind` fora da tabela (teste, admin) → sem campo: o iOS aplica o padrão.
ENTREGA_POR_KIND = {
    "ordem": {"nivel": "active"},
    "operador": {"nivel": "active"},
    "timing": {"nivel": "passive", "expira_s": 1800},
    "radar": {"nivel": "passive"},
    "fechamento": {"nivel": "passive"},
}


def entrega_do_kind(kind) -> dict:
    """`{"nivel": ..., "expira_s": ...}` do kind; `{}` se desconhecido."""
    return dict(ENTREGA_POR_KIND.get(str(kind or ""), {}))


def subtitulo_do_ticker(ticker) -> Optional[str]:
    """Subtítulo "PETR4 · Petrobras PN" a partir da tabela FIXA do catálogo.
    Ticker fora do catálogo → None (omite o campo; nunca inventa nome)."""
    from . import catalog
    t = str(ticker or "").strip().upper()
    if not t or not catalog.is_catalog_ticker(t):
        return None
    return f"{t} · {catalog.name_of(t)}"


async def send_to_user(conn, user_id: str, title: str, body: str,
                       som: bool = True, prioridade: str = "10",
                       client=None, extra: Optional[dict] = None,
                       thread_id: Optional[str] = None,
                       subtitle: Optional[str] = None) -> dict:
    """Envia o push a todos os aparelhos do usuário.

    FASE 3 (observabilidade do push): devolve um DIAGNÓSTICO completo, não
    mais um int — quem chama (main.py) precisa distinguir "não configurado"
    de "sem token" de "token(s) rejeitado(s)" para logar (e mostrar) o motivo
    certo, em vez da mensagem genérica que escondia qual dos três era.
    {"sent": int, "total": int, "detalhes": [str, ...]}

    `som`/`prioridade` são parâmetros porque nem toda classe de aviso merece o
    mesmo peso: uma execução do Operador é priority 10 com som; um aviso de
    condição de estudo atingida entra silencioso (priority 5), que é o que a
    Apple recomenda para conteúdo informativo — e o que uma mesa aprovaria
    para um simulador. `client` permite reusar UM cliente HTTP no fan-out do
    laço, em vez de abrir uma conexão nova por usuário.
    """
    if not is_configured():
        return {"sent": 0, "total": 0, "detalhes": ["APNs não configurado no servidor (variáveis do Railway ausentes)"]}
    toks = tokens_for(conn, user_id)
    if not toks:
        return {"sent": 0, "total": 0, "detalhes": []}
    import httpx
    extra = extra or {}
    # `thread-id` = ticker quando o push tem destino único: 3 avisos do mesmo
    # ativo viram UM grupo na tela de bloqueio. Sem ticker, sem agrupamento.
    tk_extra = str(extra.get("t") or "").strip().upper()
    thread_id = thread_id or tk_extra or None
    subtitle = subtitle or subtitulo_do_ticker(tk_extra)
    alert = {"title": title, "body": body}
    if subtitle:
        alert["subtitle"] = subtitle
    aps = {"alert": alert}
    if som:
        aps["sound"] = "default"
    if thread_id:
        aps["thread-id"] = thread_id
    entrega = entrega_do_kind(extra.get("kind"))
    if entrega.get("nivel"):
        aps["interruption-level"] = entrega["nivel"]
    payload = {"aps": aps}
    # `extra` viaja FORA do `aps` (convenção da Apple para dados do app) e é o
    # que dá DESTINO ao toque: sem o ticker aqui, o app abre na aba inicial e
    # não há nada sobre o ativo em lugar nenhum da tela — interrupção sem
    # destino é a pior categoria de push que existe.
    for k, v in (extra or {}).items():
        if v is not None and k != "aps":
            payload[k] = v
    sent = 0
    keep = list(toks)
    detalhes = []

    headers_extra = {}
    if entrega.get("expira_s"):
        # epoch absoluto (UTC), como a Apple exige; 0 significaria "não guardar".
        headers_extra["apns-expiration"] = str(int(time.time()) + int(entrega["expira_s"]))

    async def _post(cli, host, tk):
        r = await cli.post(
            host + "/3/device/" + tk,
            headers={
                "authorization": "bearer " + _jwt(),
                "apns-topic": os.environ["APNS_TOPIC"],
                "apns-push-type": "alert",
                "apns-priority": str(prioridade),
                **headers_extra,
            },
            content=json.dumps(payload),
        )
        if r.status_code == 200:
            return 200, ""
        try:
            reason = (r.json() or {}).get("reason", "")
        except Exception:  # noqa: BLE001
            reason = ""
        return r.status_code, reason

    async def _enviar(cli):
        nonlocal sent
        for tk in toks:
            try:
                status, reason = await _post(cli, _host(), tk)
                rotulo = env_label()
                # Fallback de ambiente (2026-11-18): o servidor fala com UM host
                # (APNS_SANDBOX), mas build do Xcode gera token de sandbox e
                # TestFlight/App Store de produção. BadDeviceToken no host
                # principal → tenta o outro antes de descartar o token. Só
                # funciona com chave .p8 sem restrição de ambiente (a 42D5CDUT49
                # é); chave restrita devolve BadEnvironmentKeyInToken no outro
                # host e o token cai no descarte normal.
                if reason == "BadDeviceToken":
                    status2, reason2 = await _post(cli, _outro_host(), tk)
                    if status2 == 200:
                        status, reason = 200, ""
                    else:
                        rotulo = f"{env_label()} e {_outro_label()}"
                        if reason2 not in ("BadDeviceToken", ""):
                            status, reason = status2, reason2
                if status == 200:
                    sent += 1
                else:
                    # FASE 6 (fix 5): reason cru + ambiente em uso + instrução exata
                    ajuda = explain_reason(reason)
                    detalhes.append(
                        (f"{tk[:10]}…: HTTP {status} {reason} [ambiente: {rotulo}]"
                         + (f" → {ajuda}" if ajuda else "")).strip()
                    )
                    if reason in _DROP_TOKEN_REASONS and tk in keep:
                        keep.remove(tk)
            except Exception as e:  # noqa: BLE001 — push é best-effort
                detalhes.append(f"{tk[:10]}…: erro de rede ({e})")

    if client is not None:
        await _enviar(client)
    else:
        async with httpx.AsyncClient(http2=True, timeout=10) as cli:
            await _enviar(cli)
    if keep != toks:
        db.kv_set(conn, "pushTokens", keep, user_id=user_id)
    _registrar_envio(conn, user_id, title, body, sent, len(toks), detalhes)
    return {"sent": sent, "total": len(toks), "detalhes": detalhes}


# ------------------- histórico de envios (widget de info) -------------------
HISTORICO_MAX = 15


def _registrar_envio(conn, user_id: str, title: str, body: str, sent: int,
                     total: int, detalhes: list) -> None:
    """Guarda os últimos envios por usuário para o widget de informações do
    push. Best-effort: falha de gravação nunca derruba o envio. Só metadados
    do que o servidor JÁ enviou — nada de valor calculado pela IA."""
    try:
        h = db.kv_get(conn, "pushHistorico", [], user_id=user_id) or []
        h.append({"at": time.time(), "titulo": (title or "")[:80],
                  "corpo": (body or "")[:140], "enviados": int(sent),
                  "total": int(total),
                  "erro": ("; ".join(detalhes)[:200] if sent == 0 and detalhes else None)})
        db.kv_set(conn, "pushHistorico", h[-HISTORICO_MAX:], user_id=user_id)
    except Exception:  # noqa: BLE001
        pass


def info_for(conn, user_id: str) -> dict:
    """Estado do push desta conta para o widget: configuração do servidor,
    aparelhos, preferências e os últimos envios (mais recente primeiro).
    Nunca expõe token inteiro nem chave."""
    h = db.kv_get(conn, "pushHistorico", [], user_id=user_id) or []
    toks = tokens_for(conn, user_id)
    prefs = prefs_for(conn, user_id)
    return {
        "configurado": is_configured(),
        "ambiente": env_label(),
        "aparelhos": len(toks),
        "prefs": {k: bool(prefs.get(k)) for k in PREFS_BOOLS + ("fechamento",)},
        "ultimos": list(reversed(h[-HISTORICO_MAX:])),
        "ultimoOk": next((e["at"] for e in reversed(h) if e.get("enviados", 0) > 0), None),
    }
