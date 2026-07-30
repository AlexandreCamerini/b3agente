"""qa/49 (pedido do Alex) — CATÁLOGO DE MODELOS por provedor + os parâmetros que
cada modelo aceita na API. Fonte ÚNICA no servidor: o frontend consome via
/api/ai/models (listbox pré-preenchida) e o llm.py APLICA os parâmetros. Assim o
usuário escolhe o modelo, vê os defaults corretos e não cai em erro de API
(ex.: modelo de raciocínio recusa `temperature` e precisa de teto de saída alto).

Campos por modelo:
  id          — nome exato do modelo na API do provedor
  label       — rótulo amigável na UI
  tier        — descrição curta (custo/velocidade) p/ a UI
  temperature — o modelo aceita `temperature` custom? (modelos que RACIOCINAM
                exigem o default e recusam o parâmetro → False = omitir do body)
  maxTokens   — teto de saída recomendado. Modelos que raciocinam precisam de
                folga (pensam DENTRO do teto): abaixo disso são cortados antes
                de escrever o texto. É teto, não alvo — só paga o que gera.
  thinking    — raciocina por padrão? (só informativo p/ a UI)

Modelo fora do catálogo (ou provedor 'local'/compatível): `spec()` devolve um
default permissivo — o guard de retry-sem-temperature no llm.py é a rede.
"""

# Teto de saída generoso p/ modelos que raciocinam (pensam dentro do max_tokens).
FOLGA_RACIOCINIO = 8000
# Teto padrão p/ modelos diretos (texto curto/estruturado): teto, não alvo.
TETO_PADRAO = 4096
# tempMax: a Anthropic aceita temperatura só até 1.0; OpenAI/Google até 2.0.
# maxTokensCap = teto de saída MÁXIMO aceito (valores conservadores/seguros p/
# evitar 400 "max_tokens too large"). Ambos clampados no _params_efetivos
# (autoridade) e refletidos como `max` nos campos da UI.

CATALOG = {
    "anthropic": [
        {"id": "claude-haiku-4-5", "label": "Claude Haiku 4.5", "tier": "Econômico · rápido (recomendado)",
         "temperature": True, "tempMax": 1.0, "maxTokens": TETO_PADRAO, "maxTokensCap": 8192, "thinking": False},
        {"id": "claude-sonnet-5", "label": "Claude Sonnet 5", "tier": "Avançado · raciocina (+caro)",
         "temperature": False, "tempMax": 1.0, "maxTokens": FOLGA_RACIOCINIO, "maxTokensCap": 16000, "thinking": True},
        {"id": "claude-opus-5", "label": "Claude Opus 5", "tier": "Máximo · raciocina (caro/lento)",
         "temperature": False, "tempMax": 1.0, "maxTokens": FOLGA_RACIOCINIO, "maxTokensCap": 16000, "thinking": True},
    ],
    "openai": [
        # ids verificados na doc da OpenAI (jul/2026): gpt-4o/o4-mini foram
        # aposentados; linha atual é GPT-5. gpt-4o-mini segue como o econômico.
        # GPT-5/o-series RACIOCINAM: temperatura omitida + usam max_completion_tokens
        # (o llm.py troca no retry). thinking=True aqui é o viés seguro (nunca erra).
        {"id": "gpt-4o-mini", "label": "GPT-4o mini", "tier": "Econômico · rápido (recomendado)",
         "temperature": True, "tempMax": 2.0, "maxTokens": TETO_PADRAO, "maxTokensCap": 16000, "thinking": False},
        {"id": "gpt-5.4-mini", "label": "GPT-5.4 mini", "tier": "Avançado · econômico",
         "temperature": False, "tempMax": 2.0, "maxTokens": FOLGA_RACIOCINIO, "maxTokensCap": 16000, "thinking": True},
        {"id": "gpt-5.6-terra", "label": "GPT-5.6 Terra", "tier": "Máximo · equilibra custo/qualidade",
         "temperature": False, "tempMax": 2.0, "maxTokens": FOLGA_RACIOCINIO, "maxTokensCap": 16000, "thinking": True},
    ],
    "google": [
        {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash", "tier": "Econômico · rápido (recomendado)",
         "temperature": True, "tempMax": 2.0, "maxTokens": TETO_PADRAO, "maxTokensCap": 8192, "thinking": False},
        {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro", "tier": "Avançado",
         "temperature": True, "tempMax": 2.0, "maxTokens": 8192, "maxTokensCap": 8192, "thinking": False},
    ],
    # Compatível/Local (openai-compatible): modelo é livre (texto), sem catálogo.
    "local": [],
}

_DEFAULT_SPEC = {"temperature": True, "tempMax": 2.0, "maxTokens": TETO_PADRAO, "maxTokensCap": 16000, "thinking": False}


def spec(provider: str, model: str) -> dict:
    """Especificação de parâmetros do (provider, model). Modelo desconhecido ou
    provedor sem catálogo → default permissivo (temperature aceita; teto padrão).
    O guard de retry no llm.py cobre um modelo desconhecido que recuse temp."""
    for m in CATALOG.get((provider or "").strip(), []):
        if m["id"] == model:
            return m
    return {**_DEFAULT_SPEC, "id": model, "label": model or "?", "tier": "Personalizado"}


def catalog_publico() -> dict:
    """Catálogo p/ a UI (o mesmo dict; sem segredos). `temperatureDefault` sai
    à parte no endpoint."""
    return CATALOG
