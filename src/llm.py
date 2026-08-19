"""Provider-agnostic LLM wrapper using LangChain's ChatOpenAI.

Supports Ollama, OpenRouter, and Groq via base_url switching.
Uses LangChain for automatic LangSmith tracing integration.

Per-agent provider override via env vars:
  RESEARCHER_LLM_PROVIDER, STRATEEG_LLM_PROVIDER, COPYWRITER_LLM_PROVIDER,
  SOCIAL_LLM_PROVIDER, CM_LLM_PROVIDER
"""

# Expected environment variables (loaded via .env or deployment secrets):
#   OLLAMA_API_KEY – API key for the local Ollama server (if authentication is enabled).
#   OPENROUTER_API_KEY – API key for OpenRouter.
#   LLM_API_KEY – Generic API key for Groq (or fallback for providers without a specific env var).

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage

load_dotenv()

# Groq model with 500K TPD — used when primary model hits rate limits (429)
GROQ_RATE_LIMIT_FALLBACK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Defaults for code/docs; live values come from runtime_config (API / data/runtime_config.json)
from src.runtime_config import DEFAULT_AGENT_LLM_CONFIG as AGENT_LLM_CONFIG


def get_agent_config(agent_name: str) -> dict:
    """Return LLM config (provider, model, temperature, agent_name) for the given agent."""
    from src.runtime_config import get_agent_llm_config

    return get_agent_llm_config(agent_name)


PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        # Use an environment variable for the Ollama API key instead of a hard‑coded value.
        "api_key_env": "OLLAMA_API_KEY",
        "model": "llama3.2",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "LLM_API_KEY",
        "model": "llama-3.3-70b-versatile",
    },
}


def _get_llm(provider: str = None, model: str = None) -> ChatOpenAI:
    """Create a ChatOpenAI client for the given provider.

    Args:
        provider: Provider name (groq, openrouter, ollama).
                  Defaults to LLM_PROVIDER env var.
        model: Model name override. Defaults to provider default.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["ollama"])

    base_url = defaults["base_url"]

    # Model: explicit > env var (only for default provider) > provider default
    if model:
        resolved_model = model
    elif provider == os.getenv("LLM_PROVIDER"):
        resolved_model = os.getenv("LLM_MODEL", defaults["model"])
    else:
        resolved_model = defaults["model"]

    # Resolve API key – prefer the env var defined in defaults, fallback to generic LLM_API_KEY.
    if "api_key_env" in defaults:
        api_key = os.getenv(defaults["api_key_env"], "no-key")
    else:
        api_key = os.getenv("LLM_API_KEY", "no-key")

    return ChatOpenAI(
        model=resolved_model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )


def _is_rate_limit_error(exc: BaseException) -> bool:
    """True for HTTP 429 / rate-limit errors from OpenAI-compatible APIs."""
    visited: set[int] = set()
    current: BaseException | None = exc
    status_codes: set[int] = set()

    while current is not None:
        oid = id(current)
        if oid in visited:
            break
        visited.add(oid)
        code = getattr(current, "status_code", None)
        if isinstance(code, int):
            status_codes.add(code)
        if type(current).__name__ == "RateLimitError":
            return True
        current = current.__cause__ or current.__context__

    if 429 in status_codes:
        return True

    message = str(exc).lower()
    return any(
        token in message
        for token in ("429", "rate limit", "rate_limit", "too many requests", "tokens per day")
    )


def _invoke_messages(
    provider: str | None,
    model: str | None,
    temperature: float,
    messages: list,
):
    llm = _get_llm(provider, model).with_config({"temperature": temperature})
    return llm.invoke(messages)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    provider: str = None,
    model: str = None,
    agent_name: str = "unknown",
    **_,
) -> str:
    """Call an LLM via LangChain's ChatOpenAI.

    Automatically pushes llm_call and llm_response events to the event bus
    so the API can stream them to the frontend in real-time.

    Args:
        system_prompt: The system instructions for the LLM.
        user_prompt:   The user message / task for the LLM.
        temperature:   Creativity control (0.0 = deterministic, 1.0 = creative).
        provider:      Optional provider override (groq, openrouter, ollama).
        model:         Optional model override.
        agent_name:    Agent name for event logging (injected via get_agent_config).

    Returns:
        The LLM's response as a plain string.
    """
    from src.event_bus import push  # late import — avoids circular on startup

    resolved_model = model or PROVIDER_DEFAULTS.get(
        provider or os.getenv("LLM_PROVIDER", "ollama"), {}
    ).get("model", "unknown")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    def _log_call(target_model: str, target_provider: str | None, note: str = ""):
        prefix = f"→ Calling {target_model}"
        if note:
            prefix = f"→ {note}: {target_model}"
        push(agent_name, "llm_call", prefix, {
            "system_prompt": system_prompt[:500],
            "user_prompt": user_prompt[:500],
            "model": target_model,
            "provider": target_provider,
        })

    _log_call(resolved_model, provider)

    model_used = resolved_model
    provider_used = provider

    try:
        response = _invoke_messages(provider, model, temperature, messages)
    except Exception as exc:
        if (
            _is_rate_limit_error(exc)
            and resolved_model != GROQ_RATE_LIMIT_FALLBACK_MODEL
        ):
            print(
                f"[LLM] Rate limit on {resolved_model} ({provider}) — "
                f"fallback to groq/{GROQ_RATE_LIMIT_FALLBACK_MODEL}"
            )
            _log_call(
                GROQ_RATE_LIMIT_FALLBACK_MODEL,
                "groq",
                "Fallback after rate limit",
            )
            model_used = GROQ_RATE_LIMIT_FALLBACK_MODEL
            provider_used = "groq"
            response = _invoke_messages(
                "groq", GROQ_RATE_LIMIT_FALLBACK_MODEL, temperature, messages
            )
        else:
            raise

    content = response.content or ""

    push(agent_name, "llm_response", f"← Response from {model_used}", {
        "preview": content[:800],
        "length": len(content),
        "model": model_used,
        "provider": provider_used,
        "fallback": model_used != resolved_model,
    })

    return content