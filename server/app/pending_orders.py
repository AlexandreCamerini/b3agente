"""Motor determinístico de ordens pendentes (Fase 2, MERC-02..04).

POR QUE EXISTE: até aqui toda ordem (`store.buy`/`store.sell`) era síncrona —
pedida e executada na mesma requisição, ao preço da cotação do momento. D-01
(v1.1) muda isso: uma ordem colocada FORA do horário de pregão não pode
executar na hora (não há preço real de mercado) — ela fica "pendente" e
executa ao preço de ABERTURA do pregão seguinte. Este módulo é o primeiro
estado ASSÍNCRONO do motor de ordens do produto, por isso nasce isolado,
testável sem rede e sem HTTP, antes de qualquer rota ou UI existir (plano
02-02 conecta as rotas; 02-03 conecta o scheduler).

D-02/D-06: o caixa (compra) ou a posição (venda) é reservado no momento do
PEDIDO, não só na execução — evita que o usuário gaste o mesmo caixa ou venda
a mesma ação duas vezes em duas ordens pendentes simultâneas. D-05 decide a
MECÂNICA da reserva: reusar o caminho de débito que já existe (`cash -=
qty*preco`, o mesmo de `store.buy`) em vez de inventar um campo novo
"caixaDisponível" — é mais simples debitar na hora do pedido e devolver se
cancelar do que manter dois saldos sincronizados à mão.

Nenhuma função deste módulo escreve em `history`: uma ordem pendente ainda
não é uma operação. O histórico só ganha entrada quando a ordem EXECUTA, via
`store.buy`/`store.sell` (mesmo caminho da ordem imediata — D-05, CLAUDE.md
princípio 5: preço/débito vêm sempre do motor determinístico, nunca da IA).

Cada registro na lista `pendingOrders` estar presente JÁ significa "está
pendente" — não existe campo `status` gravado na lista (fonte única de
verdade). O texto "pendente" só é derivado na borda (rota/UI) que expõe a
lista ao cliente.
"""
import inspect
import secrets

from . import db, store

SECAO = "pendingOrders"

# ALIAS, não uma trava nova: a trava de verdade nasce em store.py (junto de
# SECTIONS) porque o dono de `cash`/`positions` é o store, e o caminho de
# ordem IMEDIATA (/api/buy, /api/sell — plano 02-02) precisa adquirir
# EXATAMENTE esta mesma trava. Duas travas distintas não excluiriam nada: a
# execução de pendentes roda na primeira passada do scheduler depois da
# abertura, exatamente a janela em que um usuário ao vivo pode mandar uma
# ordem imediata na MESMA conta, e os dois caminhos fazem read-modify-write
# sobre o mesmo cash/positions. Ver o comentário completo na definição, em
# store.py — nenhum outro módulo do backend cria uma segunda trava de
# processo para ordens.
ORDER_LOCK = store.ORDER_LOCK


class OrdemPendenteErro(Exception):
    """Base das exceções de domínio deste módulo (padrão `brapi.ForaDoPlano`)."""


class CaixaInsuficiente(OrdemPendenteErro):
    """Caixa livre não cobre o custo da compra pendente no momento do pedido."""


class PosicaoInsuficiente(OrdemPendenteErro):
    """Posição (líquida de reservas anteriores) não cobre a venda pendente
    pedida — é isto que impede vender a mesma ação duas vezes em duas
    pendentes simultâneas (D-06)."""


class OrdemNaoPendente(OrdemPendenteErro):
    """Id de ordem que não está (mais) na lista de pendentes — já foi
    executada, cancelada, ou nunca existiu."""


def _ler(conn, user_id=None) -> list:
    return db.kv_get(conn, SECAO, [], user_id=user_id) or []


def _gravar(conn, user_id, lista) -> None:
    db.kv_set(conn, SECAO, lista, user_id=user_id)


def listar(conn, user_id=None) -> list:
    """Cópia da lista, na ORDEM DE CRIAÇÃO (FIFO — D-07: múltiplas ordens no
    mesmo ticker coexistem, cada uma processada na ordem em que nasceu)."""
    return [dict(o) for o in _ler(conn, user_id=user_id)]


def caixa_reservado(conn, user_id=None) -> float:
    """Soma dos `caixaReservado` das ordens pendentes de COMPRA. Valor
    DERIVADO — não é um segundo saldo persistido, é recalculado na leitura."""
    total = sum((o.get("caixaReservado") or 0) for o in _ler(conn, user_id=user_id) if o.get("tipo") == "COMPRA")
    return round(total, 2)


def qty_reservada(conn, user_id=None, t: str = None) -> int:
    """Soma das quantidades das VENDAS pendentes de um ticker — a posição em
    `positions` já está líquida dessa reserva (ver `criar_venda`), então este
    helper serve para a UI mostrar "X ações com venda pendente", não para
    recalcular disponibilidade (que já vem correta de `positions`)."""
    return sum(o.get("qty") or 0 for o in _ler(conn, user_id=user_id) if o.get("tipo") == "VENDA" and o.get("t") == t)


def criar_compra(conn, user_id, t: str, qty: int, preco_ref: float, meta=None) -> dict:
    """Reserva o caixa NA HORA do pedido (D-02/D-05): debita `cash` como
    `store.buy` debitaria, mas NÃO grava posição nem history — a posição só
    nasce quando a ordem executar, via `executar_pendentes`."""
    with ORDER_LOCK:
        qty = max(100, round(qty / 100) * 100)  # mesma normalização de store.buy
        custo = round(qty * preco_ref, 2)
        cash = store.get(conn, "cash", user_id=user_id)
        if cash < custo:
            # mesma frase da rota /api/buy — o cliente não vê dois textos
            # diferentes pro mesmo motivo de recusa.
            raise CaixaInsuficiente("Caixa insuficiente.")
        registro = {
            "id": "po_" + secrets.token_hex(4),
            "criadaEm": store.now_str(),
            "tipo": "COMPRA",
            "t": t,
            "qty": qty,
            "precoReferencia": round(float(preco_ref), 2),
            "caixaReservado": custo,
            "avgReservado": None,
            "origem": "manual",
            "meta": store._sanitize_trade_meta(meta),
            "ultimaTentativaEm": None,
            "ultimoErro": None,
        }
        lista = _ler(conn, user_id=user_id)
        lista.append(registro)
        db.kv_set(conn, "cash", round(cash - custo, 2), user_id=user_id)
        _gravar(conn, user_id, lista)
        return dict(registro)


def criar_venda(conn, user_id, t: str, qty: int) -> dict:
    """Reserva a QUANTIDADE na hora do pedido (D-02/D-06): subtrai de
    `positions` (a mesma semântica de venda parcial de `store.sell` — `avg`
    preservado), sem gravar em history. A posição já fica líquida da reserva,
    então uma segunda `criar_venda` no mesmo ticker enxerga só o que sobrou —
    é isto que impede vender a mesma ação duas vezes em duas pendentes."""
    with ORDER_LOCK:
        positions = store.get(conn, "positions", user_id=user_id)
        pos = next((p for p in positions if p["t"] == t), None)
        if not pos:
            raise PosicaoInsuficiente("Sem posicao em " + t)
        qty = max(100, round(qty / 100) * 100)  # mesma normalização de store.sell
        disponivel = pos["qty"]
        if qty > disponivel:
            raise PosicaoInsuficiente(
                f"Posição insuficiente em {t}: disponível {disponivel}, pedido {qty}.")
        avg = pos["avg"]
        if qty >= pos["qty"]:
            positions = [p for p in positions if p["t"] != t]
        else:
            pos["qty"] = pos["qty"] - qty  # parcial: avg preservado, igual store.sell
        registro = {
            "id": "po_" + secrets.token_hex(4),
            "criadaEm": store.now_str(),
            "tipo": "VENDA",
            "t": t,
            "qty": qty,
            "precoReferencia": None,
            "caixaReservado": None,
            "avgReservado": avg,
            "origem": "manual",
            "meta": None,
            "ultimaTentativaEm": None,
            "ultimoErro": None,
        }
        lista = _ler(conn, user_id=user_id)
        lista.append(registro)
        db.kv_set(conn, "positions", positions, user_id=user_id)
        _gravar(conn, user_id, lista)
        return dict(registro)


def _restaurar_posicao(conn, user_id, t: str, qty: int, avg: float) -> None:
    """Inverso exato da reserva de `criar_venda`: devolve `qty` à posição em
    `t`, reponderando `avg` pela MESMA fórmula de `store.buy` se já existir
    posição no ticker (ex.: usuário recomprou enquanto a venda estava
    pendente). NÃO toca em `cash` nem `history` — quem chama decide isso."""
    positions = store.get(conn, "positions", user_id=user_id)
    existing = next((p for p in positions if p["t"] == t), None)
    if existing:
        total = existing["qty"] + qty
        existing["avg"] = round((existing["avg"] * existing["qty"] + avg * qty) / total, 2)
        existing["qty"] = total
    else:
        positions.append({"t": t, "qty": qty, "avg": round(avg, 2), "stop": None, "alvo": None,
                           "abertaEm": store.now_str()})
    db.kv_set(conn, "positions", positions, user_id=user_id)


def cancelar(conn, user_id, order_id: str) -> dict:
    """Devolução IMEDIATA (D-03: cancelável a qualquer momento antes da
    execução) — não espera o próximo tick do scheduler. COMPRA devolve o
    caixa reservado; VENDA devolve a posição via `_restaurar_posicao`."""
    with ORDER_LOCK:
        lista = _ler(conn, user_id=user_id)
        idx = next((i for i, o in enumerate(lista) if o.get("id") == order_id), None)
        if idx is None:
            raise OrdemNaoPendente(
                "Ordem pendente não encontrada — ela pode já ter sido executada ou cancelada.")
        registro = lista.pop(idx)
        if registro["tipo"] == "COMPRA":
            cash = store.get(conn, "cash", user_id=user_id)
            db.kv_set(conn, "cash", round(cash + (registro.get("caixaReservado") or 0), 2), user_id=user_id)
        else:
            _restaurar_posicao(conn, user_id, registro["t"], registro["qty"], registro["avgReservado"])
        _gravar(conn, user_id, lista)
        return dict(registro)


async def executar_pendentes(conn, user_id, price_getter, agora=None) -> list:
    """Aplica o preço do MOTOR (D-01) a cada ordem pendente, na ordem de
    criação (FIFO — D-07). `price_getter(ticker)` é injetável (sync ou async
    — resolvido com `inspect.isawaitable`), no contrato de
    `candle_provider.get_quote`/`yahoo.get_quote`: `{"price": float|None,
    "source": str}`. Padrão da casa para código testável sem rede (ver
    `brapi.get_history(..., fetch_json=fake)`).

    `agora` existe para permitir injeção de horário em teste/observabilidade
    futura; esta função não decide QUANDO rodar — quem chama (scheduler,
    02-03) decide isso pelo gate de pregão.

    A cotação é obtida FORA da trava — nunca segurar `ORDER_LOCK` durante um
    await de rede, isso bloquearia as threads HTTP do pool do FastAPI. Dentro
    da trava a lista é RELIDA e a ordem só é aplicada se o `id` ainda existir
    (T-02-04: ordem cancelada durante o await não ressuscita nem executa
    duas vezes).

    Nenhuma exceção de uma ordem derruba as outras: o corpo inteiro (cotação
    + aplicação) fica em try/except por ordem, registrando `ultimoErro` e
    seguindo para a próxima. Sem preço utilizável (`None`, não numérico,
    `<= 0`, ou o `price_getter` levanta), a ordem PERMANECE pendente — nunca
    fabricar preço (CLAUDE.md princípio 4).
    """
    del agora
    eventos = []
    with ORDER_LOCK:
        lista = _ler(conn, user_id=user_id)
    for registro in lista:
        order_id = registro["id"]
        t = registro["t"]
        try:
            resultado = price_getter(t)
            payload = await resultado if inspect.isawaitable(resultado) else resultado
            preco = payload.get("price") if isinstance(payload, dict) else None
            fonte = payload.get("source") if isinstance(payload, dict) else None
            if not isinstance(preco, (int, float)) or preco <= 0:
                erro = (isinstance(payload, dict) and payload.get("error")) or "Cotação indisponível."
                raise OrdemPendenteErro(erro)
            with ORDER_LOCK:
                atual = _ler(conn, user_id=user_id)
                alvo = next((o for o in atual if o.get("id") == order_id), None)
                if alvo is None:
                    continue  # cancelada durante a espera da cotação (T-02-04)
                if alvo["tipo"] == "COMPRA":
                    custo = round(alvo["qty"] * preco, 2)
                    cash_livre = store.get(conn, "cash", user_id=user_id)
                    if cash_livre + (alvo.get("caixaReservado") or 0) < custo:
                        # O preço de abertura subiu o suficiente para o caixa
                        # reservado (mais o livre) não cobrir mais o custo.
                        # Auto-cancela e devolve o caixa integralmente — a
                        # `tag` é o que permite scheduler (02-03)/app (02-06)
                        # avisarem o usuário sem varrer todo `warn` do agente
                        # (T-02-36: sem ela, o sumiço seria silencioso).
                        db.kv_set(conn, "cash",
                                  round(cash_livre + (alvo.get("caixaReservado") or 0), 2), user_id=user_id)
                        atual = [o for o in atual if o.get("id") != order_id]
                        _gravar(conn, user_id, atual)
                        eventos.append({
                            "time": store.now_str(), "kind": "warn", "tag": "pendente-cancelada",
                            "text": (f"Ordem pendente de compra ({alvo['qty']} {t}) cancelada na abertura: "
                                     f"o preço subiu de R$ {alvo['precoReferencia']:.2f} para "
                                     f"R$ {preco:.2f} e o caixa reservado não cobriu o custo. O caixa "
                                     "reservado voltou integralmente."),
                        })
                    else:
                        # devolve o reservado PRIMEIRO e deixa o débito real
                        # acontecer uma única vez, pelo caminho de sempre
                        # (D-05, princípio 5) — origem "pendente" distingue
                        # de manual/automatico no histórico.
                        db.kv_set(conn, "cash",
                                  round(cash_livre + (alvo.get("caixaReservado") or 0), 2), user_id=user_id)
                        atual = [o for o in atual if o.get("id") != order_id]
                        _gravar(conn, user_id, atual)
                        store.buy(conn, t, alvo["qty"], preco, user_id=user_id, meta=alvo.get("meta"),
                                  origem="pendente")
                        eventos.append({
                            "time": store.now_str(), "kind": "buy", "tag": "pendente-executada",
                            "text": (f"Ordem pendente de compra executada: {alvo['qty']} {t} a "
                                     f"R$ {preco:.2f} (fonte: {fonte or '?'})."),
                        })
                else:  # VENDA
                    atual = [o for o in atual if o.get("id") != order_id]
                    _gravar(conn, user_id, atual)
                    _restaurar_posicao(conn, user_id, t, alvo["qty"], alvo["avgReservado"])
                    store.sell(conn, t, preco, user_id=user_id, qty=alvo["qty"], origem="pendente")
                    eventos.append({
                        "time": store.now_str(), "kind": "buy", "tag": "pendente-executada",
                        "text": (f"Ordem pendente de venda executada: {alvo['qty']} {t} a "
                                 f"R$ {preco:.2f} (fonte: {fonte or '?'})."),
                    })
        except Exception as e:  # noqa: BLE001 — falha de UMA ordem não derruba as demais
            with ORDER_LOCK:
                atual = _ler(conn, user_id=user_id)
                alvo = next((o for o in atual if o.get("id") == order_id), None)
                if alvo is not None:
                    alvo["ultimaTentativaEm"] = store.now_str()
                    alvo["ultimoErro"] = str(e)
                    _gravar(conn, user_id, atual)
    if eventos:
        store.push_agent_log(conn, eventos, user_id=user_id)
    return eventos
