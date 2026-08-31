"""Seletor de provedor de opções por env (Fase 9, Plano 03 — qa/09).

Espelho em miniatura de `candle_provider.provider_name()`/`get_provider()`:
o nome do provedor ativo vem de `B3_OPTIONS_PROVIDER` (default `"yahoo"`), e
todo consumidor chama `get_options()` daqui, nunca direto de um dos módulos
por trás.

Isto é ALAVANCA DE ROLLBACK OPERACIONAL, não fallback automático. D-04
(`options_provider_mydata.py`) proíbe explicitamente o Yahoo como fallback
ativo de opções — reintroduzi-lo em tempo de execução anularia o ganho da
migração, porque o endpoint de opções do Yahoo é exatamente a fonte instável
(401/403/429) que a migração elimina. Trocar de provedor aqui é sempre uma
decisão humana registrada (mudança de env em deploy), nunca um desvio
silencioso decidido pelo código em runtime.

O default de produção continua `"yahoo"` nesta fase: o Folded Todo do
09-CONTEXT.md exige medir o rate-limit real do mydata (Plano 09-04) antes de
desligar Yahoo/brapi nas fatias migradas — a virada para `mydata` é o
checkpoint humano do Plano 09-06.

Fase 14 (Plano 01) acrescenta `"mock"`: existe SÓ para desenvolvimento e
teste da mecânica lastreada (venda coberta / put de proteção) enquanto a
virada de produção do mydata não acontece — nunca é default, e só entra por
variável de ambiente do servidor (`B3_OPTIONS_PROVIDER=mock`), nunca por
escolha do cliente.

Fase 0/Plano 02 (OPTGATE-01, achado WR-01 do `09-REVIEW.md`): o gate de
orçamento do mydata vive NO ADAPTADOR (`options_provider_mydata._gate`),
não neste seletor — este arquivo continua sendo despacho puro por env, sem
nenhuma lógica de cota. O comportamento é coberto de ponta a ponta pelo
teste deste seletor com `B3_OPTIONS_PROVIDER=mydata` (monkeypatch de
escopo de teste, nunca do ambiente real).
"""
from __future__ import annotations

import os
from typing import Optional

from . import options_provider_mock
from . import options_provider_mydata
from . import options_provider_yahoo

_PROVEDORES = {
    "yahoo": options_provider_yahoo.get_options,
    "mydata": options_provider_mydata.get_options,
    "mock": options_provider_mock.get_options,
}


def provider_name() -> str:
    return (os.environ.get("B3_OPTIONS_PROVIDER") or "yahoo").strip().lower()


async def get_options(ticker: str, expiration: Optional[str] = None) -> dict:
    nome = provider_name()
    fn = _PROVEDORES.get(nome)
    if fn is None:
        raise ValueError(
            f"B3_OPTIONS_PROVIDER='{nome}' desconhecido. Opções: "
            f"{', '.join(sorted(_PROVEDORES))}.")
    return await fn(ticker, expiration)
