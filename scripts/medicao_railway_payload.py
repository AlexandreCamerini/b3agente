"""Payload que roda DENTRO do container da Railway (via `railway ssh`).

Responde UMA pergunta: o Yahoo trata o IP de datacenter da Railway diferente do
IP residencial onde a Fase 1 foi medida? É o pré-requisito do ADR da fonte de
dados, porque o orçamento aprovado é US$ 0 (fonte única, sem fallback pago).

POSTURA DE RISCO — este script roda no MESMO IP que serve o app ao vivo, então:
  • ESCALONADO: 1 requisição → 5 → 1 rodada → concorrências → sustentado. Cada
    degrau só começa se o anterior passou limpo.
  • PARA NO PRIMEIRO 429/401/403. O objetivo é detectar bloqueio, não achar o
    teto. Um erro já é a resposta; insistir só machuca o app que está no ar.
  • TETO DURO de requisições (MAX_REQ). Nem que tudo passe, ele ultrapassa.
  • SOMENTE LEITURA: não importa `main`, não abre o banco, não escreve em /data,
    não toca o candle_cache. Só GETs no Yahoo e print no stdout.

Autossuficiente de propósito: tenta reusar a sessão do cliente real
(`app.yahoo`) e, se o import falhar, constrói cookie+crumb sozinho — assim não
depende do layout do container.

Modos:
  bloqueio (padrão) — o teste de IP. Rodar com o pregão FECHADO: se o Yahoo
                      bloquear, ninguém está usando o app.
  atraso            — 15 requisições, só para medir a distância entre o último
                      candle e o relógio. Exige pregão ABERTO (10h–17h BRT).
"""
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx

MAX_REQ = 300               # teto duro de requisições ao Yahoo nesta execução
INTERVALO = "15m"           # granularidade candidata para o Radar intraday
RANGE = "1d"                # janela do delta (a que o laço buscaria a cada rodada)
PAUSA_ENTRE_DEGRAUS = 3.0   # respiro entre degraus, para não parecer rajada única

# Os 65 do universo do Radar que o Yahoo serve (os 9 restantes dão 404 em
# QUALQUER intervalo, inclusive 1d — buraco pré-existente, medido em 30/07/2026).
UNIVERSO_FALLBACK = [
    "PETR4", "PETR3", "VALE3", "ITUB4", "BBDC4", "BBDC3", "BBAS3", "B3SA3",
    "ABEV3", "WEGE3", "RENT3", "PRIO3", "SUZB3", "EQTL3", "RADL3", "VIVT3",
    "ITSA4", "BPAC11", "RDOR3", "HAPV3", "LREN3", "MGLU3", "RAIL3", "CSAN3",
    "UGPA3", "VBBR3", "GGBR4", "CSNA3", "USIM5", "CMIN3", "BRAP4", "CYRE3",
    "MRVE3", "ENGI11", "ENEV3", "EGIE3", "CMIG4", "TAEE11", "CPFE3", "AURE3",
    "SBSP3", "TIMS3", "TOTS3", "BBSE3", "CXSE3", "PSSA3", "SANB11", "MULT3",
    "IGTI11", "ALOS3", "HYPE3", "ASAI3", "BEEF3", "SLCE3", "SMTO3", "RAIZ4",
    "RECV3", "VAMO3", "FLRY3", "KLBN11", "DXCO3", "BRKM5", "GOAU4", "COGN3",
    "YDUQ3",
]
SEM_DADO_NO_YAHOO = ["ELET3", "ELET6", "JBSS3", "EMBR3", "CPLE6", "CRFB3",
                     "NTCO3", "MRFG3", "BRFS3"]

HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
BASE_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

_estado = {"req": 0, "abortado": None, "sessao": None}


# --------------------------------------------------------------------------
# Sessão: reusa o cliente real se der; senão constrói cookie+crumb igual a ele
# --------------------------------------------------------------------------
async def _sessao(client):
    if _estado["sessao"] is not None:
        return _estado["sessao"]
    try:
        sys.path.insert(0, "/app")
        from app import yahoo as ycli  # noqa: PLC0415
        s = await ycli._ensure_session(client)
        _estado["sessao"] = {"cookie": s["cookie"], "crumb": s["crumb"], "via": "app.yahoo"}
        return _estado["sessao"]
    except Exception as e:  # noqa: BLE001 — container sem o pacote: segue autônomo
        print(f"  (app.yahoo indisponível: {type(e).__name__} — construindo sessão própria)")
    cookie = ""
    for url in ("https://fc.yahoo.com/", "https://finance.yahoo.com/"):
        try:
            r = await client.get(url, headers={**BASE_HEADERS, "Accept": "text/html,*/*"})
            c = "; ".join(f"{k}={v}" for k, v in r.cookies.items())
            if c:
                cookie = c
                break
        except httpx.HTTPError:
            continue
    crumb = ""
    try:
        r = await client.get("https://query1.finance.yahoo.com/v1/test/getcrumb",
                             headers={**BASE_HEADERS, "Accept": "text/plain,*/*",
                                      **({"Cookie": cookie} if cookie else {})})
        txt = (r.text or "").strip()
        if r.status_code == 200 and txt and len(txt) <= 64 and "Too Many" not in txt:
            crumb = txt
    except httpx.HTTPError:
        pass
    _estado["sessao"] = {"cookie": cookie, "crumb": crumb, "via": "própria"}
    return _estado["sessao"]


class Abortar(RuntimeError):
    """Bloqueio detectado: o teste para aqui, por contrato."""


async def _get(client, ticker, interval=INTERVALO, rng=RANGE):
    """UM GET. Conta no teto, e 429/401/403 aborta a execução inteira."""
    if _estado["abortado"]:
        raise Abortar(_estado["abortado"])
    if _estado["req"] >= MAX_REQ:
        _estado["abortado"] = f"teto de {MAX_REQ} requisições atingido"
        raise Abortar(_estado["abortado"])
    _estado["req"] += 1
    s = await _sessao(client)
    q = {"range": rng, "interval": interval, "includePrePost": "false"}
    if s["crumb"]:
        q["crumb"] = s["crumb"]
    h = {**BASE_HEADERS, "Accept": "application/json,*/*"}
    if s["cookie"]:
        h["Cookie"] = s["cookie"]
    t0 = time.perf_counter()
    try:
        r = await client.get(HOSTS[0] + "/v8/finance/chart/" + ticker + ".SA",
                             params=q, headers=h)
    except httpx.HTTPError as e:
        return {"status": 0, "ms": (time.perf_counter() - t0) * 1000,
                "erro": type(e).__name__, "n": 0, "ultimo": None}
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code in (429, 401, 403):
        _estado["abortado"] = (f"Yahoo HTTP {r.status_code} em {ticker} "
                               f"na requisição nº {_estado['req']}")
        raise Abortar(_estado["abortado"])
    out = {"status": r.status_code, "ms": ms, "bytes": len(r.content), "n": 0, "ultimo": None}
    if r.status_code == 200:
        try:
            res = ((r.json().get("chart") or {}).get("result") or [None])[0] or {}
            ts = res.get("timestamp") or []
            out["n"] = len(ts)
            out["ultimo"] = ts[-1] if ts else None
        except Exception:  # noqa: BLE001
            pass
    return out


async def _rodada(client, universo, conc):
    sem = asyncio.Semaphore(conc)

    async def um(tk):
        async with sem:
            return await _get(client, tk)

    t0 = time.perf_counter()
    res = await asyncio.gather(*[um(t) for t in universo])
    wall = time.perf_counter() - t0
    lat = sorted(x["ms"] for x in res)
    st = {}
    for x in res:
        st[x["status"]] = st.get(x["status"], 0) + 1
    return {"wall_s": round(wall, 2), "status": st,
            "p50_ms": round(statistics.median(lat)) if lat else None,
            "p95_ms": round(lat[int(len(lat) * 0.95)]) if lat else None,
            "bytes": sum(x.get("bytes", 0) for x in res),
            "ok": sum(1 for x in res if x["status"] == 200 and x["n"] > 0)}


async def _ip_de_saida(client):
    """Qual IP o Yahoo enxerga. Decide se um serviço separado isolaria o risco
    (se o IP for o mesmo, um segundo serviço na mesma região não protege nada)."""
    for url in ("https://api.ipify.org", "https://checkip.amazonaws.com"):
        try:
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                return (r.text or "").strip()
        except Exception:  # noqa: BLE001
            continue
    return "desconhecido"


# --------------------------------------------------------------------------
# Modo BLOQUEIO — escalonado, para no primeiro erro
# --------------------------------------------------------------------------
async def modo_bloqueio(client, universo):
    rel = {}
    print(f"\n[0] Identidade de saída")
    rel["ip"] = await _ip_de_saida(client)
    rel["regiao"] = os.environ.get("RAILWAY_REPLICA_REGION") or os.environ.get("RAILWAY_REGION") or "?"
    s = await _sessao(client)
    print(f"    IP visto de fora: {rel['ip']} · região: {rel['regiao']}")
    print(f"    sessão: cookie={'sim' if s['cookie'] else 'NÃO'} "
          f"crumb={'sim' if s['crumb'] else 'NÃO'} (via {s['via']})")
    if not s["crumb"]:
        print("    ATENÇÃO: sem crumb. Em IP de datacenter isso é o primeiro sintoma "
              "de aperto — o /v1/test/getcrumb já costuma vir bloqueado antes do chart.")

    print(f"\n[1] Uma requisição ({INTERVALO} × {RANGE}, PETR4)")
    r = await _get(client, "PETR4")
    rel["degrau1"] = r
    print(f"    status={r['status']} velas={r['n']} {r['ms']:.0f}ms {r.get('bytes', 0)/1024:.1f}KB")
    if r["status"] != 200 or not r["n"]:
        print("    → o intraday NÃO sai deste IP. Resposta obtida; nada mais a testar.")
        return rel
    await asyncio.sleep(PAUSA_ENTRE_DEGRAUS)

    print(f"\n[2] Cinco requisições sequenciais (linha de base de latência)")
    seq = []
    for tk in universo[:5]:
        x = await _get(client, tk)
        seq.append(x["ms"])
        await asyncio.sleep(0.3)
    rel["degrau2"] = {"p50_ms": round(statistics.median(seq)), "max_ms": round(max(seq))}
    print(f"    p50={rel['degrau2']['p50_ms']}ms max={rel['degrau2']['max_ms']}ms "
          f"(residencial em 30/07: p50 173ms)")
    await asyncio.sleep(PAUSA_ENTRE_DEGRAUS)

    print(f"\n[3] Uma rodada do universo ({len(universo)} ativos) na concorrência de HOJE (4)")
    rel["degrau3"] = await _rodada(client, universo, 4)
    print(f"    {rel['degrau3']['ok']}/{len(universo)} ok em {rel['degrau3']['wall_s']}s "
          f"p50={rel['degrau3']['p50_ms']}ms p95={rel['degrau3']['p95_ms']}ms "
          f"status={rel['degrau3']['status']}")
    await asyncio.sleep(PAUSA_ENTRE_DEGRAUS)

    print(f"\n[4] Mesma rodada a conc=8 e conc=16 (o que o laço intraday usaria)")
    rel["degrau4"] = {}
    for conc in (8, 16):
        rel["degrau4"][conc] = await _rodada(client, universo, conc)
        d = rel["degrau4"][conc]
        print(f"    conc={conc:<3} {d['ok']}/{len(universo)} ok em {d['wall_s']}s "
              f"p50={d['p50_ms']}ms p95={d['p95_ms']}ms status={d['status']}")
        await asyncio.sleep(PAUSA_ENTRE_DEGRAUS)

    restante = MAX_REQ - _estado["req"]
    rodadas = max(0, restante // len(universo))
    print(f"\n[5] Sustentado: {rodadas} rodada(s) seguida(s) a conc=8 "
          f"(simula {rodadas * 5} min do laço de 5 min)")
    rel["degrau5"] = []
    for i in range(rodadas):
        d = await _rodada(client, universo, 8)
        rel["degrau5"].append(d)
        print(f"    rodada {i+1}: {d['ok']}/{len(universo)} ok em {d['wall_s']}s "
              f"p50={d['p50_ms']}ms status={d['status']}")
    return rel


# --------------------------------------------------------------------------
# Modo ATRASO — 15 requisições, exige pregão aberto
# --------------------------------------------------------------------------
async def modo_atraso(client, universo):
    agora = time.time()
    brt = datetime.now(timezone.utc) - timedelta(hours=3)
    aberto = brt.weekday() < 5 and 10 <= brt.hour < 17
    print(f"\nRelógio BRT: {brt:%d/%m %H:%M} · pregão {'ABERTO' if aberto else 'FECHADO'}")
    if not aberto:
        print("AVISO: com o pregão fechado este número mede a distância até o "
              "fechamento, NÃO o atraso do feed. Rode entre 10h e 17h BRT.")
    rel = []
    for iv in ("1m", "5m", "15m"):
        for tk in universo[:5]:
            r = await _get(client, tk, interval=iv, rng="1d")
            if not r.get("ultimo"):
                continue
            atraso = (agora - r["ultimo"]) / 60
            rel.append({"ticker": tk, "intervalo": iv, "atraso_min": round(atraso, 1),
                        "ultimo_utc": datetime.fromtimestamp(r["ultimo"], tz=timezone.utc)
                        .strftime("%H:%M:%SZ")})
            print(f"  {tk:<7} {iv:>3} → último candle {rel[-1]['ultimo_utc']} "
                  f"({rel[-1]['atraso_min']} min atrás)")
            await asyncio.sleep(0.3)
    if rel:
        piores = [x["atraso_min"] for x in rel if x["intervalo"] == "1m"]
        if piores:
            print(f"\n  Atraso em 1m: mediana {statistics.median(piores):.1f} min. "
                  f"Acima de ~5 min, 'a condição ocorreu agora' não se sustenta em 5m.")
    return rel


async def main():
    modo = (sys.argv[1] if len(sys.argv) > 1 else "bloqueio").strip()
    try:
        sys.path.insert(0, "/app")
        from app.scanner import DEFAULT_UNIVERSE  # noqa: PLC0415
        universo = [t for t in DEFAULT_UNIVERSE if t not in SEM_DADO_NO_YAHOO]
        fonte = "app.scanner"
    except Exception:  # noqa: BLE001
        universo, fonte = list(UNIVERSO_FALLBACK), "lista embutida"
    print("=" * 70)
    print(f"MEDIÇÃO YAHOO — DE DENTRO DA RAILWAY · modo={modo}")
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%SZ} · universo: {len(universo)} "
          f"ativos ({fonte}) · teto: {MAX_REQ} requisições · aborta no 1º 429/401/403")
    print("=" * 70)
    rel = {"modo": modo, "quando_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            rel["dados"] = await (modo_atraso(client, universo) if modo == "atraso"
                                  else modo_bloqueio(client, universo))
            rel["veredito"] = "sem bloqueio nos degraus executados"
        except Abortar as e:
            rel["veredito"] = f"ABORTADO: {e}"
            print(f"\n!!! ABORTADO: {e}")
            print("    O teste parou de propósito. Um erro já é a resposta — "
                  "insistir só prejudica o app que está no ar.")
    rel["requisicoes"] = _estado["req"]
    rel["parede_s"] = round(time.perf_counter() - t0, 1)
    print(f"\n{'=' * 70}")
    print(f"TOTAL: {rel['requisicoes']} requisições em {rel['parede_s']}s · {rel['veredito']}")
    print("JSON>>> " + json.dumps(rel, default=str))


if __name__ == "__main__":
    asyncio.run(main())
