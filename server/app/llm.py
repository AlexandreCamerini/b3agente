"""Integracao com a LLM (httpx async). Monta o prompt (skill + dados + formato
JSON dos KPIs), chama o provedor e devolve (texto, kpis). Tambem testa conexao.
As chaves ficam no servidor (web) ou sao enviadas pelo handset (iOS)."""
import os
import json

import httpx


class LLMUserError(RuntimeError):
    def __init__(self, message: str, *, provider=None, model=None, key_source=None, action=None, hint=None, code=None):
        super().__init__(message)
        self.payload = {
            "message": message,
            "provider": provider,
            "model": model,
            "keySource": key_source,
            "action": action,
            "hint": hint,
            "code": code,
        }
        self.payload = {k: v for k, v in self.payload.items() if v not in (None, "")}


def _cfg_payload(config: dict, message: str, *, action=None, hint=None, code=None) -> LLMUserError:
    return LLMUserError(
        message,
        provider=(config or {}).get("provider"),
        model=(config or {}).get("model"),
        key_source=(config or {}).get("keySource"),
        action=action,
        hint=hint,
        code=code,
    )


def public_error(exc: Exception) -> dict:
    if isinstance(exc, LLMUserError):
        return exc.payload
    return {"message": str(exc) or exc.__class__.__name__, "action": "Revise provedor, modelo, chave e conectividade em Configurações → Modelo de IA."}

from .catalog import name_of
from .kpi import parse_rich

GUARDRAILS = "\n".join([
    "",
    "- REGRAS DO SISTEMA (invioláveis) -",
    "Este e um simulador EDUCACIONAL com dados de mercado REAIS e dinheiro SIMULADO.",
    "Voce e uma FERRAMENTA DE ENSINO, nao um robo de investimento.",
    "EXPLIQUE e ENSINE o raciocinio por tras de cada conclusao (ex.: 'num perfil",
    "conservador o stop costuma ficar mais proximo porque limita a perda...').",
    "Nao de ordens de operacao prontas; mostre o porque, os trade-offs e o risco.",
    "Nunca prometa lucro nem use linguagem de ganho garantido.",
    "Sempre destaque gerenciamento de risco e o uso de stop.",
    "Dimensione posicao, stop e alvo de forma coerente com o CAPITAL simulado",
    "disponivel e com o PERFIL de risco informado.",
    "Baseie-se em dados PASSADOS; nao ha garantia de repeticao.",
    "Se o cenario for indefinido, diga que o melhor e nao operar.",
    "Nada do que voce escrever e recomendacao de investimento.",
])

FORMAT = "\n".join([
    "",
    "- FORMATO OBRIGATORIO DA RESPOSTA -",
    "Responda com APENAS UM objeto JSON valido (sem texto fora dele, sem cercas ```).",
    "Use exatamente estas chaves e apenas os valores permitidos:",
    "{",
    '  "direcao": "Alta|Baixa|Lateral",',
    '  "conviccao": "Muito Alto|Alto|Médio|Baixo",',
    '  "qualidade": "Excelente|Boa|Regular|Ruim",',
    '  "recomendacao": "Estudar alta|Estudar baixa|Monitorar|Aguardar|Não operar|Reduzir risco",',
    '  "resumo": "1 a 2 frases objetivas",',
    '  "confirmacoes": ["sinais a favor da tese (curtos)"],',
    '  "invalidacoes": ["o que invalidaria a tese (curtos)"],',
    '  "cuidados": ["riscos e observacoes (curtos)"],',
    '  "fatosRelevantes": ["somente fatos fornecidos ou contexto explicitamente marcado como geral"],',
    '  "corpo": "análise em MARKDOWN: use ## títulos, **negrito**, listas com - e quebras de linha",',
    '  "stopSugerido": 0.0,',
    '  "alvoSugerido": 0.0',
    "}",
    "O campo `recomendacao` NAO e recomendacao de investimento; e um PLANO EDUCACIONAL",
    "para estudo no simulador. Nao use 'comprar' ou 'vender'.",
    "O campo `corpo` e a analise em MARKDOWN (titulos, negrito, listas) — sera",
    "renderizado no app; nao use HTML, apenas markdown simples.",
    "stopSugerido e alvoSugerido sao referencias TECNICAS em reais para estudo",
    "e gestao de risco simulada, coerentes com ATR, suportes e resistencias.",
    "Cada lista deve ter de 1 a 4 itens curtos. Nao escreva absolutamente nada fora",
    "do objeto JSON.",
    # FASE 8B (revisão de eficiência dos defaults): leitura é no celular — o
    # corpo enxuto vale nos DOIS modos; clareza > exaustividade.
    "SEJA CONCISO: `corpo` em ate 12 linhas de markdown; corte redundancia,",
    "nao corte o raciocinio.",
])


def _profile_line(profile: dict) -> str:
    if not isinstance(profile, dict) or not profile:
        return ""
    return (
        "Perfil do operador (ajuste recomendacao, stop e alvo a ELE): "
        f"risco {profile.get('risco', 'moderado')}, "
        f"horizonte {profile.get('horizonte', 'swing')}, "
        f"tolerancia de perda por operacao {profile.get('toleranciaPerdaPct', 2)}%, "
        f"objetivo {profile.get('objetivo', 'crescimento')}, "
        f"experiencia {profile.get('experiencia', 'intermediario')}."
    )

ENV_NAMES = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY",
    "local": "B3_AGENTE_API_KEY",
}


def provider_env_name(provider: str) -> str:
    return ENV_NAMES.get(provider, "B3_AGENTE_API_KEY")


def resolve_key(config: dict) -> str:
    if config.get("keySource") == "env":
        return os.environ.get("B3_AGENTE_API_KEY") or os.environ.get(provider_env_name(config.get("provider", "")), "") or ""
    return config.get("apiKey") or ""


def _build_user_prompt(ticker: str, quote: dict, history: dict, profile: dict = None, account: dict = None) -> str:
    lines = [f"Ativo: {ticker} ({name_of(ticker)}) - B3"]
    pl = _profile_line(profile)
    if pl:
        lines.append(pl)
    if isinstance(account, dict):
        cash = account.get("cash")
        budget = account.get("budget")
        if isinstance(cash, (int, float)):
            extra = f" (orcamento inicial R$ {budget:.2f})" if isinstance(budget, (int, float)) else ""
            lines.append(f"Capital SIMULADO disponivel: R$ {cash:.2f}{extra}. Dimensione posicao, stop e alvo de forma coerente com este capital e o perfil.")
    if quote and quote.get("price") is not None:
        lines.append(f"Cotacao atual (referencia para stop/alvo): R$ {quote['price']:.2f} ({quote.get('change', 0):+.2f}% no dia)")
    lines.append("")
    n_candles = len(history.get("candles") or [])
    plabel = history.get("periodLabel") or "?"
    lines.append(f"Historico diario ({n_candles} candles; janela '{plabel}' escolhida pelo usuario na Config) - data, abertura, maxima, minima, fechamento, volume:")
    for c in history.get("candles", []):
        lines.append("\t".join(str(c.get(k)) for k in ("date", "open", "high", "low", "close", "volume")))
    lines.append("")
    lines.append(f"Com base nas instrucoes, no PERFIL e nestes dados reais, produza a leitura tecnica educacional de {ticker} no JSON exigido.")
    return "\n".join(lines)


def _provider_error(config: dict, status: int, msg=None) -> LLMUserError:
    actions = {
        400: "Verifique se o nome do modelo está correto para o provedor escolhido.",
        401: "Verifique a chave de API. No iPhone, se usar 'Digitar aqui', a chave precisa estar salva no próprio aparelho.",
        403: "A chave não tem permissão para este modelo ou endpoint.",
        404: "Modelo ou endpoint não encontrado. Troque o modelo na configuração da IA.",
        429: "Limite de requisições atingido. Aguarde ou use outra chave/modelo.",
    }
    label = {401: "chave inválida", 403: "sem permissão", 404: "modelo/endpoint não encontrado", 429: "limite de requisições"}.get(status, "erro do provedor")
    message = f"IA indisponível: HTTP {status} ({label})" + (f" - {msg}" if msg else "")
    return _cfg_payload(config, message, action=actions.get(status, "Revise a configuração da IA e tente novamente."), code=f"provider_http_{status}")


def _safe_json_response(resp: httpx.Response):
    try:
        return resp.json()
    except ValueError:
        txt = (resp.text or "").strip()[:300]
        return {"error": {"message": txt or "Resposta não-JSON do provedor."}}


# FASE 1 (consistência): temperatura baixa em TODOS os níveis — mesmos dados
# do snapshot devem gerar leituras estáveis (N1 e N2 nunca "sorteiam" direção).
LLM_TEMPERATURE = 0.2


async def _call_anthropic(config, key, system, user, max_tokens):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.anthropic.com/v1/messages",
            headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
            json={"model": config["model"], "max_tokens": max_tokens, "temperature": LLM_TEMPERATURE, "system": system, "messages": [{"role": "user", "content": user}]},
        )
    data = _safe_json_response(r)
    if r.status_code != 200:
        raise _provider_error(config, r.status_code, (data.get("error") or {}).get("message"))
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


async def _call_openai_compatible(base_url, config, key, system, user, max_tokens):
    url = base_url.rstrip("/") + "/chat/completions"
    body = {"model": config["model"], "max_tokens": max_tokens, "temperature": LLM_TEMPERATURE,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, headers={"content-type": "application/json", "authorization": "Bearer " + key}, json=body)
        data = _safe_json_response(r)
        # Guarda de compatibilidade: modelos de raciocínio da OpenAI (o1/gpt-5…)
        # rejeitam `temperature` ≠ 1 — repete UMA vez sem o parâmetro (BYOK é
        # livre; a consistência fica por conta do prompt/snapshot nesses modelos).
        if r.status_code == 400 and "temperature" in str((data.get("error") or {}).get("message") or "").lower():
            body.pop("temperature", None)
            r = await c.post(url, headers={"content-type": "application/json", "authorization": "Bearer " + key}, json=body)
            data = _safe_json_response(r)
    if r.status_code != 200:
        raise _provider_error(config, r.status_code, (data.get("error") or {}).get("message"))
    return (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


async def _call_google(config, key, system, user, max_tokens):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={key}"
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            url,
            headers={"content-type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": LLM_TEMPERATURE},
            },
        )
    data = _safe_json_response(r)
    if r.status_code != 200:
        raise _provider_error(config, r.status_code, (data.get("error") or {}).get("message"))
    cand = (data.get("candidates") or [{}])[0]
    return "".join(p.get("text", "") for p in ((cand.get("content") or {}).get("parts") or [])).strip()


async def _call_llm(config, key, system, user, max_tokens):
    if not (config.get("model") or "").strip():
        raise _cfg_payload(config, "Nenhum modelo de IA configurado.", action="Informe um modelo em Configurações → Modelo de IA.", code="missing_model")
    if not key:
        raise _cfg_payload(config, "Nenhuma chave de API disponível para a IA.", action="Escolha 'Variável de ambiente' no Railway/servidor ou 'Digitar aqui' e salve a chave no iPhone.", hint="No iPhone a chave manual não é herdada da web; ela fica no armazenamento local do app.", code="missing_key")
    provider = config.get("provider")
    if provider == "anthropic":
        return await _call_anthropic(config, key, system, user, max_tokens)
    if provider == "openai":
        return await _call_openai_compatible("https://api.openai.com/v1", config, key, system, user, max_tokens)
    if provider == "google":
        return await _call_google(config, key, system, user, max_tokens)
    if provider == "local":
        if not (config.get("baseUrl") or "").strip():
            raise _cfg_payload(config, "Base URL é obrigatória para o provedor Compatível/Local.", action="Informe a Base URL completa, por exemplo http://SEU_IP:11434/v1.", code="missing_base_url")
        return await _call_openai_compatible(config["baseUrl"], config, key, system, user, max_tokens)
    raise _cfg_payload(config, "Provedor de IA desconhecido: " + str(provider), action="Selecione Anthropic, OpenAI, Google ou Compatível/Local.", code="unknown_provider")




def _build_structured_prompt(ticker: str, context: dict, profile: dict = None, account: dict = None) -> str:
    lines = [
        f"Ativo: {ticker} ({name_of(ticker)}) - B3",
        f"Modelo tecnico solicitado: {context.get('modelLabel')} ({context.get('model')})",
        "",
        "Voce recebera abaixo um pacote tecnico JA CALCULADO pelo sistema, mais os candles diarios historicos.",
        "Use os candles para validar a leitura. Nao invente indicador, preco, volume, fato ou noticia ausente.",
        (f"Snapshot tecnico #{context.get('snapshotId')} ({context.get('snapshotAt')}): TODOS os numeros citados vem DELE — e o mesmo snapshot que o Radar (N1) leu; a direcao de estudo deve ser COERENTE com `setupsRadar` (divergencia so com justificativa explicita nos dados)." if context.get("snapshotId") else ""),
        "Atue como um operador senior explicando o racional tecnico para estudo, mas respeite os guardrails educacionais.",
    ]
    pl = _profile_line(profile)
    if pl:
        lines.append(pl)
    if isinstance(account, dict):
        cash = account.get("cash")
        budget = account.get("budget")
        if isinstance(cash, (int, float)):
            extra = f" (orcamento inicial R$ {budget:.2f})" if isinstance(budget, (int, float)) else ""
            lines.append(f"Capital SIMULADO disponivel: R$ {cash:.2f}{extra}.")
    lines.extend([
        "",
        "PACOTE TECNICO E CANDLES EM JSON:",
        json.dumps(context, ensure_ascii=False, separators=(",", ":")),
        "",
        "Tarefa:",
        "1. Analise o ativo pelo modelo solicitado, usando os candles e os blocos calculados.",
        "2. Explique tendencia, momentum, volume, volatilidade, suportes/resistencias e risco conforme o modelo pedir.",
        "3. Se o modelo for opcoes e options.available=false, explique que a fonte yfinance nao retornou cadeia de opcoes e foque no ativo objeto.",
        "4. Se o cenario for indefinido, use recomendacao='Não operar' ou 'Aguardar'.",
        "5. Use o bloco `families` (leitura por familia + confluenciaEntreFamilias) como espinha da analise: explique cada familia e a sintese.",
        "6. Respeite `dataQuality` (serie curta/volume/multi-timeframe limitam o teto de confianca — declare as limitacoes).",
        "7. Termine o campo `corpo` com a secao '## Modelos utilizados' explicando CADA metodologia aplicada (o que e, o que mede, limitacoes) — o app ensina, nao opina.",
        "8. Saia somente no JSON obrigatorio.",
    ])
    return "\n".join(lines)


async def analyze_structured(config: dict, skill: dict, profile: dict, account: dict, ticker: str, context: dict, modo: str = None):
    key = resolve_key(config)
    pl = _profile_line(profile)
    # FASE 8B (B3): N2 por modo — professor (educacional, intacto) × mesa de
    # operações (decisão direta). Mesmas chaves de saída; muda persona/tom.
    operador = (modo == "operador") or (modo is None and is_operador(config))
    if operador:
        mesa = "\n".join([
            "# Persona",
            "Voce e a MESA DE OPERACOES do cliente na B3: analise tecnica, leitura de",
            "candles, risco e disciplina. Oriente direto: decisao, plano e onde a tese",
            "morre — sem aula; uma linha de racional por decisao basta.",
            "Diferencie fato calculado, inferencia tecnica e incerteza. Nao-operacao e",
            "resultado de primeira classe quando os sinais conflitam.",
        ])
        system = (skill.get("text") or "") + "\n" + mesa + "\n" + GUARDRAILS_PRO + ("\n" + pl if pl else "") + "\n" + FORMAT_PRO
    else:
        super_operator = "\n".join([
            "# Persona",
            "Voce e um super operador educacional da B3 especializado em analise tecnica, leitura de candles, risco e psicologia de mercado.",
            "Sua funcao e ENSINAR o raciocinio de uma mesa profissional, nao emitir ordem operacional real.",
            "Diferencie fato calculado, inferencia tecnica e incerteza. Seja direto e didatico para leitura em celular.",
            "Priorize contexto, risco, invalidacao, stop tecnico e nao-operacao quando os sinais forem conflitantes.",
        ])
        system = (skill.get("text") or "") + "\n" + super_operator + "\n" + GUARDRAILS + ("\n" + pl if pl else "") + "\n" + FORMAT
    user = _build_structured_prompt(ticker, context, profile, account)
    raw = await _call_llm(config, key, system, user, 1800)
    if not raw:
        raise RuntimeError("A LLM nao retornou texto.")
    return parse_rich(raw)

async def analyze(config: dict, skill: dict, profile: dict, account: dict, ticker: str, quote: dict, history: dict):
    key = resolve_key(config)
    pl = _profile_line(profile)
    system = (skill.get("text") or "") + "\n" + GUARDRAILS + ("\n" + pl if pl else "") + "\n" + FORMAT
    user = _build_user_prompt(ticker, quote, history, profile, account)
    raw = await _call_llm(config, key, system, user, 1300)
    if not raw:
        raise RuntimeError("A LLM nao retornou texto.")
    r = parse_rich(raw)
    # {kpis, detail, proposal, markdown, text}
    return r


# ===========================================================================
# FASE 1 — Pipeline de análise IA em 3 níveis.
# Metodologia da skill `analise-tecnica-b3` (operador sênior de AT da B3)
# ADAPTADA ao guardrail educacional: a skill decide comprar/vender; aqui o
# mesmo rigor (dados só do pacote, confluência, invalidação, teto de
# confiança, cenários) produz LEITURA DE ESTUDO no vocabulário fixo.
# ===========================================================================

OPERADOR_EDUCACIONAL = "\n".join([
    "# Persona (metodologia: operador sênior de AT da B3, em função de PROFESSOR)",
    "Disciplina, objetividade e rigor estatístico. Explique primeiro em linguagem",
    "simples, depois o termo técnico. Nunca confunda convicção com certeza.",
    "",
    "# Regras metodológicas invioláveis",
    "1. NUNCA invente preço, indicador, volume, fato ou notícia: use SOMENTE o",
    "   pacote técnico pré-calculado fornecido. Todo número citado vem dele.",
    "2. Nunca prometa lucro nem percentual de acerto; probabilidades apenas",
    "   relativas (baixa/moderada/alta), nunca % sem base estatística.",
    "3. Nunca fundamente a leitura em UM indicador isolado: peso maior em",
    "   estrutura de preço + volume + confluência entre famílias.",
    "4. Sinais conflitantes => a leitura é 'Aguardar' ou 'Não operar'.",
    "5. SEMPRE informe o que INVALIDA a tese de estudo (nível ou condição).",
    "6. Diferencie: cenário confirmado, em formação e especulativo.",
    "7. Movimento excessivamente esticado: diga explicitamente.",
    "8. Sem oportunidade de estudo => frase fixa: 'Sem setup no momento — não",
    "   há leitura com vantagem estatística clara.'",
    "9. Respeite dataQuality do pacote: serieCurta/volumeAusente/multiTimeframe",
    "   limitam o teto de confiança (hoje, sem 2º timeframe, teto = moderada);",
    "   DECLARE as limitações em vez de compensá-las com inferência.",
    "10. PROIBIDO verbo de ordem (compre/venda/entre agora) e a palavra",
    "    'recomendação' de investimento. Vocabulário fixo do plano de estudo:",
    "    'Estudar alta' | 'Estudar baixa' | 'Monitorar' | 'Aguardar' | 'Não operar'.",
])

DEEP_FORMAT = "\n".join([
    "",
    "- FORMATO OBRIGATÓRIO (N1 · aprofundamento do Radar) -",
    "Responda com APENAS UM objeto JSON válido (sem texto fora, sem cercas ```):",
    "{",
    '  "resumo": "2 a 3 frases da leitura geral",',
    '  "leituraSetups": [{"setup": "nome do setup detectado", "leitura": "o que o padrão significa AQUI",',
    '     "criteriosPresentes": ["..."], "criteriosAusentes": ["o que falta e por que importa"]}],',
    '  "cenarios": {"alta": "condição + o que confirmaria", "baixa": "condição + o que confirmaria", "neutro": "quando a leitura é ficar de fora"},',
    '  "riscos": ["riscos objetivos da leitura"],',
    '  "invalidacao": "nível/condição que invalida a tese de estudo",',
    '  "confianca": "baixa|moderada",',
    '  "planoEstudo": "Estudar alta|Estudar baixa|Monitorar|Aguardar|Não operar",',
    '  "modelosUtilizados": [{"nome": "...", "oQueE": "...", "oQueMede": "...", "limitacoes": "..."}]',
    "}",
    "modelosUtilizados cobre CADA metodologia usada (setups, ADX, MACD, Bollinger...):",
    "o app ensina, não opina. `confianca` respeita o teto do dataQuality.",
    "SEJA CONCISO (leitura no celular): 'resumo' em até 3 frases; cada 'leitura'",
    "de setup em até 2 frases; cada cenário em 1 frase; até 3 'riscos' de 1 frase",
    "cada; 'invalidacao' em 1 frase. Clareza didática vale mais que exaustividade —",
    "corte redundância, não corte o raciocínio.",
])


# ============================================================================
# FASE 8B (B3) — CÉREBRO DO MODO OPERADOR. A MESMA metodologia do operador
# sênior (regras 1–9 idênticas às do educacional), mas em função de MESA DE
# OPERAÇÕES que orienta o cliente: decisão direta, plano e gestão de risco.
# O que muda é o vocabulário (item 10) e o tom; os limites regulatórios NÃO
# mudam: proibido prometer resultado/taxa de acerto sem base e proibido
# "recomendação personalizada" (o perfil só dimensiona o risco). O aviso
# obrigatório da persona é acrescentado pela UI (DISCLAIMERS.operador).
# ============================================================================
CONCLUSOES_PRO = [
    "A operação está tecnicamente validada, desde que a condição de entrada seja confirmada.",
    "O cenário é promissor, mas ainda exige confirmação.",
    "Os sinais são conflitantes. A melhor decisão é aguardar.",
    "Não há uma operação com vantagem estatística clara neste momento.",
]

OPERADOR_PRO = "\n".join([
    "# Persona (metodologia: operador sênior de AT da B3, em função de MESA DE OPERAÇÕES)",
    "Disciplina, objetividade e rigor estatístico. Fale como uma mesa orienta o",
    "cliente: direto, curto e acionável — o quê, quando, quanto e onde a tese",
    "morre. Sem rodeios didáticos; o cliente já sabe os conceitos.",
    "",
    "# Regras metodológicas invioláveis",
    "1. NUNCA invente preço, indicador, volume, fato ou notícia: use SOMENTE o",
    "   pacote técnico pré-calculado fornecido. Todo número citado vem dele.",
    "2. Nunca prometa lucro, retorno ou percentual de acerto; probabilidades",
    "   apenas relativas (baixa/moderada/alta), nunca % sem base estatística.",
    "3. Nunca fundamente a decisão em UM indicador isolado: peso maior em",
    "   estrutura de preço + volume + confluência entre famílias.",
    "4. Sinais conflitantes => decisão 'AGUARDAR CONFIRMAÇÃO' ou 'NÃO OPERAR'.",
    "5. SEMPRE informe o nível/condição que INVALIDA a tese (o stop é técnico,",
    "   nunca arbitrário).",
    "6. Diferencie: cenário confirmado, em formação e especulativo.",
    "7. Movimento excessivamente esticado: não perseguir preço — diga.",
    "8. Sem vantagem estatística => frase fixa: 'Não há uma operação com",
    "   vantagem estatística clara neste momento.'",
    "9. Respeite dataQuality do pacote: serieCurta/volumeAusente/multiTimeframe",
    "   limitam o teto de confiança (sem 2º timeframe, teto = moderada);",
    "   DECLARE as limitações em vez de compensá-las com inferência.",
    "10. Vocabulário de DECISÃO obrigatório: 'COMPRAR' | 'VENDER' |",
    "    'AGUARDAR CONFIRMAÇÃO' | 'NÃO OPERAR' — sempre COERENTE com o plano",
    "    determinístico fornecido no pacote (entrada/stop/alvos/R:R); nunca o",
    "    contradiga nem crie níveis que não estejam nele.",
    "11. O plano é técnico e a execução é do usuário na corretora dele; isto",
    "    não é aconselhamento personalizado — o perfil informado só dimensiona",
    "    o risco (% por operação), nunca muda a leitura técnica.",
])

GUARDRAILS_PRO = "\n".join([
    "",
    "- REGRAS DO SISTEMA (invioláveis) -",
    "Modo OPERADOR: ferramenta de decisão e disciplina para o PRÓPRIO usuário.",
    "Seja direto: decisão, plano (entrada, stop na invalidação, alvos, R:R),",
    "gestão de risco em R e condição de cancelamento. Nada de aula — uma linha",
    "de racional por decisão basta.",
    "Nunca prometa lucro nem use linguagem de ganho garantido.",
    "Risco primeiro: toda posição tem stop e tamanho definido ANTES da entrada;",
    "parcial no alvo 1; 'NÃO OPERAR' é resultado de primeira classe.",
    "Baseie-se em dados PASSADOS; não há garantia de repetição.",
    "Termine SEMPRE com UMA conclusão canônica, textualmente:",
    "'" + "' | '".join(CONCLUSOES_PRO) + "'",
])

# N2 no modo operador: mesmas CHAVES do FORMAT educacional (o app já parseia e
# renderiza), mudando apenas vocabulário e tom — zero mudança de contrato.
FORMAT_PRO = FORMAT.replace(
    '"recomendacao": "Estudar alta|Estudar baixa|Monitorar|Aguardar|Não operar|Reduzir risco",',
    '"recomendacao": "COMPRAR|VENDER|AGUARDAR CONFIRMAÇÃO|NÃO OPERAR|Reduzir risco",',
).replace(
    "O campo `recomendacao` NAO e recomendacao de investimento; e um PLANO EDUCACIONAL\npara estudo no simulador. Nao use 'comprar' ou 'vender'.",
    "O campo `recomendacao` e a DECISAO da mesa, coerente com o plano deterministico\nfornecido; a execucao e sempre do usuario, na corretora dele.",
) + "\nSEJA CONCISO (mesa, leitura no celular): `corpo` em ate 10 linhas de markdown,\nabrindo com 'Resumo executivo' (2 frases) e fechando com a conclusao canonica."

# N1 (deep) no modo operador: mesmas CHAVES do DEEP_FORMAT (o DeepModal já
# renderiza), com semântica de mesa — planoEstudo vira a DECISÃO.
PRO_DEEP_FORMAT = "\n".join([
    "",
    "- FORMATO OBRIGATÓRIO (N1 · plano da mesa) -",
    "Responda com APENAS UM objeto JSON válido (sem texto fora, sem cercas ```):",
    "{",
    '  "resumo": "resumo EXECUTIVO (2 a 3 frases: decisão, racional em 1 linha, risco principal), terminando com a conclusão canônica",',
    '  "leituraSetups": [{"setup": "nome do setup", "leitura": "o que o padrão manda fazer AQUI (1 frase)",',
    '     "criteriosPresentes": ["..."], "criteriosAusentes": ["o que falta e o que isso muda no plano"]}],',
    '  "cenarios": {"alta": "gatilho + plano se confirmar", "baixa": "onde a tese morre + ação", "neutro": "quando ficar de fora"},',
    '  "riscos": ["riscos objetivos do plano (curtos)"],',
    '  "invalidacao": "nível/condição EXATA que cancela o plano",',
    '  "confianca": "baixa|moderada",',
    '  "planoEstudo": "COMPRAR|VENDER|AGUARDAR CONFIRMAÇÃO|NÃO OPERAR",',
    '  "modelosUtilizados": [{"nome": "...", "oQueE": "...", "oQueMede": "...", "limitacoes": "..."}]',
    "}",
    "`planoEstudo` é a DECISÃO da mesa e deve ser COERENTE com o plano",
    "determinístico do pacote (entrada/stop/alvos/R:R) — nunca o contradiga.",
    "SEJA CONCISO (mesa): 'resumo' em até 3 frases; cada 'leitura' em até 2;",
    "cada cenário em 1 frase; até 3 'riscos' de 1 frase; 'invalidacao' em 1.",
])

_DECISOES_PRO = ("COMPRAR", "VENDER", "AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR")


def is_operador(config) -> bool:
    """Modo do escopo/aparelho: o cliente manda appMode dentro da config (iOS)
    ou ele vem da config persistida do escopo (web)."""
    return isinstance(config, dict) and config.get("appMode") == "operador"


def _parse_json_loose(raw: str):
    """Extrai o primeiro objeto/array JSON de uma resposta, tolerante a cercas."""
    import json as _json
    import re as _re2
    txt = (raw or "").strip()
    txt = _re2.sub(r"^```(?:json)?", "", txt).strip()
    txt = _re2.sub(r"```$", "", txt).strip()
    try:
        return _json.loads(txt)
    except (ValueError, TypeError):
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        s = txt.find(opener)
        e = txt.rfind(closer)
        if s != -1 and e > s:
            try:
                return _json.loads(txt[s:e + 1])
            except (ValueError, TypeError):
                continue
    return None


def _deep_fallback(raw: str) -> dict:
    """FASE 6 (fix 2): a resposta do N1 não veio no JSON obrigatório (causa
    típica: truncamento). NUNCA devolver o blob cru para a UI — era isso que
    aparecia "todo mal formatado" no modal do Radar. Ordem de recuperação:
      1. salvar o campo "resumo" do JSON parcial (regex tolerante);
      2. senão, remover a sintaxe JSON (chaves/aspas/nomes de campo) e devolver
         texto legível;
      3. marcar parseFalhou=True para a UI oferecer "rodar de novo".
    """
    import re as _re3
    txt = (raw or "").strip()
    txt = _re3.sub(r"^```(?:json)?", "", txt).strip()
    txt = _re3.sub(r"```$", "", txt).strip()
    m = _re3.search(r'"resumo"\s*:\s*"((?:[^"\\]|\\.)*)', txt)
    if m and m.group(1).strip():
        resumo = m.group(1).replace('\\"', '"').replace("\\n", " ").strip()
    else:
        campos = ("resumo|leituraSetups|cenarios|riscos|invalidacao|confianca|planoEstudo|"
                  "modelosUtilizados|setup|leitura|criteriosPresentes|criteriosAusentes|"
                  "alta|baixa|neutro|nome|oQueE|oQueMede|limitacoes")
        t = _re3.sub(r'"(?:' + campos + r')"\s*:', "", txt)
        t = _re3.sub(r'[{}\[\]"`]', " ", t)
        t = _re3.sub(r"\s*,\s*", " · ", t)
        t = _re3.sub(r"\s+", " ", t).strip(" ·:")
        resumo = t[:600]
    return {
        "resumo": resumo or "A leitura veio incompleta do modelo — toque em 'Aprofundar com IA' novamente.",
        "leituraSetups": [], "cenarios": {}, "riscos": [], "invalidacao": "",
        "confianca": "baixa", "planoEstudo": "Monitorar", "modelosUtilizados": [],
        "parseFalhou": True,
    }


async def analyze_deep(config: dict, profile: dict, ticker: str, context: dict, setups_payload: dict, modo: str = None):
    """N1: UMA chamada de IA para UM ativo do top-N do Radar. Recebe o contexto
    técnico completo (janela do usuário) + os setups detectados com checklist;
    devolve leitura estruturada. Nenhum cálculo novo acontece aqui.
    FASE 8B (B3): `modo` ('operador') troca persona/guardrails/formato — mesmas
    CHAVES de saída, semântica de mesa. Padrão/qualquer outro valor = estudo."""
    key = resolve_key(config)
    pl = _profile_line(profile)
    operador = (modo == "operador") or (modo is None and is_operador(config))
    if operador:
        system = OPERADOR_PRO + "\n" + GUARDRAILS_PRO + (("\n" + pl) if pl else "") + "\n" + PRO_DEEP_FORMAT
    else:
        system = OPERADOR_EDUCACIONAL + "\n" + GUARDRAILS + (("\n" + pl) if pl else "") + "\n" + DEEP_FORMAT
    user = "\n".join([
        f"Ativo: {ticker} ({name_of(ticker)}) - B3 · Aprofundamento do Radar (nível 1).",
        (f"Snapshot técnico #{context.get('snapshotId')} ({context.get('snapshotAt')}): todos os números vêm DELE — mesma fonte do Radar; `planoEstudo` deve ser coerente com o veredito dos setups abaixo." if isinstance(context, dict) and context.get("snapshotId") else ""),
        "",
        "SETUPS DETECTADOS (determinístico, com checklist e confluência %):",
        json.dumps(setups_payload, ensure_ascii=False, separators=(",", ":")),
        "",
        "PACOTE TÉCNICO PRÉ-CALCULADO (janela escolhida pelo usuário) + candles:",
        json.dumps(context, ensure_ascii=False, separators=(",", ":")),
        "",
        "Tarefa: para CADA setup detectado, explique a leitura, os critérios",
        "presentes e os AUSENTES (e por que a ausência importa); descreva os",
        "cenários de ESTUDO alta/baixa/neutro e os riscos. Sem verbo de ordem.",
        "Saia somente no JSON obrigatório.",
    ])
    # FASE 6 (fix 2): 1600 tokens truncava leituras com muitos setups — JSON
    # inválido caía no fallback e o modal mostrava texto quebrado. 2200 dá
    # folga mantendo a instrução de concisão como controle principal.
    raw = await _call_llm(config, key, system, user, 2200)
    if not raw:
        raise RuntimeError("A LLM nao retornou texto.")
    data = _parse_json_loose(raw)
    if not isinstance(data, dict):
        return _deep_fallback(raw)
    data.setdefault("modelosUtilizados", [])
    # FASE 8B (B3): validação do rótulo por MODO — mesa usa decisões diretas;
    # estudo mantém o vocabulário educacional. Valor fora do conjunto vira o
    # neutro do modo (nunca vaza vocabulário de um modo no outro).
    if operador:
        if str(data.get("planoEstudo") or "").upper() not in _DECISOES_PRO:
            data["planoEstudo"] = "AGUARDAR CONFIRMAÇÃO"
        else:
            data["planoEstudo"] = str(data["planoEstudo"]).upper()
    else:
        if data.get("planoEstudo") not in ("Estudar alta", "Estudar baixa", "Monitorar", "Aguardar", "Não operar"):
            data["planoEstudo"] = "Monitorar"
    conf = str(data.get("confianca") or "").lower()
    data["confianca"] = conf if conf in ("baixa", "moderada") else "moderada"  # teto sem 2º timeframe
    return data


def parse_carteira(raw: str, ticker: str) -> dict:
    """FASE 3: interpreta a resposta do prompt de stop/alvo da carteira, que sai
    como um ARRAY JSON (um objeto por ativo). Extrai o objeto do `ticker` pedido
    (a análise é individual; o array normalmente traz 1 item). Tolerante a cercas
    e a texto ao redor."""
    import json as _json
    import re as _re2
    txt = (raw or "").strip()
    txt = _re2.sub(r"^```(?:json)?", "", txt).strip()
    txt = _re2.sub(r"```$", "", txt).strip()
    data = None
    try:
        data = _json.loads(txt)
    except (ValueError, TypeError):
        for opener, closer in (("[", "]"), ("{", "}")):
            s = txt.find(opener)
            e = txt.rfind(closer)
            if s != -1 and e > s:
                try:
                    data = _json.loads(txt[s:e + 1])
                    break
                except (ValueError, TypeError):
                    data = None
    items = []
    if isinstance(data, list):
        items = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict):
        items = [data]
    tnorm = (ticker or "").upper().replace(".SA", "")
    chosen = None
    for it in items:
        a = str(it.get("ativo") or it.get("ticker") or "").upper().replace(".SA", "")
        if a == tnorm:
            chosen = it
            break
    if chosen is None and items:
        chosen = items[0]
    if not chosen:
        return {"proposal": None, "explicacao": "", "operar": None, "precoAtual": None, "raw": txt[:400]}

    def _num(v):
        try:
            return None if v is None else round(float(v), 2)
        except (TypeError, ValueError):
            return None

    operar = chosen.get("operar")
    operar = None if operar is None else bool(operar)
    stop = _num(chosen.get("stop"))
    alvo = _num(chosen.get("alvo"))
    if operar is False:
        stop = None
        alvo = None
    proposal = {"stop": stop, "alvo": alvo} if (stop is not None or alvo is not None) else None
    # FASE 1 (N3): cenários estruturados conservador/moderado/agressivo com
    # memória de cálculo — a UI pré-preenche com 1 toque; usuário SEMPRE confirma.
    cenarios = []
    for c in (chosen.get("cenarios") or []):
        if not isinstance(c, dict):
            continue
        perfil = str(c.get("perfil") or "").strip().lower()
        if perfil not in ("conservador", "moderado", "agressivo"):
            continue
        cs, ca = _num(c.get("stop")), _num(c.get("alvo"))
        if cs is None and ca is None:
            continue
        cenarios.append({
            "perfil": perfil, "stop": cs, "alvo": ca,
            "riscoRetorno": _num(c.get("riscoRetorno")),
            "memoriaCalculo": str(c.get("memoriaCalculo") or ""),
            "rrDesfavoravel": bool(c.get("rrDesfavoravel")) or (
                c.get("riscoRetorno") is not None and _num(c.get("riscoRetorno")) is not None and _num(c.get("riscoRetorno")) < 1.5
            ),
        })
    modelos = [m for m in (chosen.get("modelosUtilizados") or []) if isinstance(m, dict)]
    return {
        "proposal": proposal,
        "explicacao": str(chosen.get("explicacao") or ""),
        "operar": operar,
        "precoAtual": _num(chosen.get("precoAtual")),
        "cenarios": cenarios,
        "modelosUtilizados": modelos,
    }


async def analyze_carteira(config: dict, profile: dict, account: dict, ticker: str, quote: dict, history: dict, prompt: str, tech_context: dict = None):
    """FASE 3: análise INDIVIDUAL de stop/alvo de UM ativo da carteira, guiada
    pelo prompt configurável (prompts.carteiraStopAlvo) + BYOK. Usa o formato do
    próprio prompt (array por ativo) — NÃO usa o FORMAT do Mercado.
    FASE 1 (N3): quando tech_context vem, o payload ganha ATR(14), suportes/
    resistências da janela, bandas e viés — e a resposta passa a incluir
    `cenarios` (conservador/moderado/agressivo) com memória de cálculo."""
    key = resolve_key(config)
    pl = _profile_line(profile)
    instruction = (prompt or "").strip()
    cenarios_ext = ""
    if tech_context:
        cenarios_ext = "\n".join([
            "",
            "EXTENSÃO OBRIGATÓRIA DO FORMATO: além dos campos do array, cada objeto",
            "inclui:",
            '  "cenarios": [',
            '    {"perfil": "conservador", "stop": 0.0, "alvo": 0.0, "riscoRetorno": 0.0,',
            '     "memoriaCalculo": "ex.: stop didático = mínima local 36,80 − 1×ATR 0,52 = 36,28"},',
            '    {"perfil": "moderado", ...}, {"perfil": "agressivo", ...}',
            "  ],",
            '  "modelosUtilizados": [{"nome":"...","oQueE":"...","oQueMede":"...","limitacoes":"..."}]',
            "Regras dos cenários (metodologia de mesa, uso EDUCACIONAL):",
            "- stop TÉCNICO ligado à invalidação (suporte/mínima local e/ou k×ATR do",
            "  CONTEXTO TÉCNICO fornecido) — nunca arbitrário; alvo em resistência ou",
            "  múltiplos de ATR. Todo número citado VEM do contexto (não invente).",
            "- riscoRetorno = (alvo−preço)/(preço−stop); se < 1,5 marque",
            '  "rrDesfavoravel": true (cenário fica rotulado como estudo).',
            "- Ajuste as distâncias ao PERFIL (tolerância de perda) e ao capital.",
            "- Sem verbo de ordem; são sugestões PARA ESTUDO que o usuário confirma.",
        ])
    # FASE 8B (B4/N3): no modo OPERADOR o prompt configurável do usuário ganha
    # a camada de MESA por cima (tom direto + conclusões canônicas + limites) —
    # o formato do array por ativo NÃO muda (o popup já parseia).
    voz = ("\n\n" + GUARDRAILS_PRO + "\nFale como mesa de operações: stop na invalidação técnica, "
           "alvos com R:R explícito e uma linha de racional por número.") if is_operador(config) else ""
    system = instruction + voz + ((("\n\n" + pl)) if pl else "") + cenarios_ext + (
        "\n\nResponda SOMENTE com o array JSON especificado, sem texto fora dele e sem cercas ```."
    )
    user = _build_user_prompt(ticker, quote, history, profile, account)
    if tech_context:
        user += "\n\nCONTEXTO TÉCNICO PRÉ-CALCULADO (ATR, suportes/resistências da janela, bandas, viés) — use ESTES números:\n" + json.dumps(tech_context, ensure_ascii=False, separators=(",", ":"))
    raw = await _call_llm(config, key, system, user, 1300 if tech_context else 900)
    if not raw:
        raise RuntimeError("A LLM nao retornou texto.")
    res = parse_carteira(raw, ticker)
    # Robustez: se a resposta veio no formato antigo (objeto único com
    # stopSugerido/alvoSugerido), aproveita via parse_rich — evita "sem proposta"
    # quando o prompt salvo ainda é o default anterior.
    if res.get("proposal") is None and not res.get("explicacao"):
        try:
            rich = parse_rich(raw)
            prop = rich.get("proposal")
            if prop and (prop.get("stop") is not None or prop.get("alvo") is not None):
                res = {
                    "proposal": prop,
                    "explicacao": (rich.get("detail") or {}).get("resumo") or "",
                    "operar": True,
                    "precoAtual": None,
                }
        except Exception:  # noqa: BLE001
            pass
    return res


async def test_connection(config: dict) -> dict:
    key = resolve_key(config)
    try:
        await _call_llm(config, key, "Responda apenas: OK.", "ping", 16)
        return {
            "ok": True,
            "message": f"Conexão com IA estabelecida ({config.get('provider')} · {config.get('model')}).",
            "provider": config.get("provider"),
            "model": config.get("model"),
            "keySource": config.get("keySource"),
        }
    except httpx.TimeoutException as e:  # noqa: BLE001
        err = _cfg_payload(config, "Tempo esgotado ao chamar a IA.", action="Teste a internet do servidor/iPhone e reduza o tamanho do modelo se necessário.", code="llm_timeout")
        return {"ok": False, **err.payload}
    except httpx.RequestError as e:  # noqa: BLE001
        err = _cfg_payload(config, "Falha de rede ao chamar a IA: " + str(e), action="Verifique conexão, proxy, firewall e se o endpoint do provedor está acessível.", code="llm_network")
        return {"ok": False, **err.payload}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, **public_error(e)}
