"""Provider-agnostic LLM wrapper using LangChain's ChatOpenAI.

Supports Ollama, OpenRouter, and Groq via base_url switching.
Uses LangChain for automatic LangSmith tracing integration.

Per-agent provider override via env vars:
  RESEARCHER_LLM_PROVIDER, STRATEEG_LLM_PROVIDER, COPYWRITER_LLM_PROVIDER,
  SOCIAL_LLM_PROVIDER, CM_LLM_PROVIDER
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage

load_dotenv()

# Per-agent LLM config — change model/provider/temperature here, not in agent files
#
# Best split (use when OpenRouter is available):
#   researcher        → groq       llama-3.1-8b-instant               (500k tokens/day, fast)
#   strateeg          → groq       llama-3.1-8b-instant               (500k tokens/day, fast)
#   copywriter        → openrouter meta-llama/llama-3.3-70b-instruct:free  (70B quality for creative writing)
#   social_specialist → openrouter meta-llama/llama-3.3-70b-instruct:free  (70B quality for platform content)
#   campaign_manager  → groq       llama-3.3-70b-versatile            (100k tokens/day, deterministic)
#
# Current: all on Groq — OpenRouter free tier (50 req/day global) is exhausted
AGENT_LLM_CONFIG: dict[str, dict] = {
    "researcher":          {"provider": "groq", "model": "llama-3.1-8b-instant",    "temperature": 0.4},
    "strateeg":            {"provider": "groq", "model": "llama-3.1-8b-instant",    "temperature": 0.5},
    "copywriter":          {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.9},
    "social_specialist":   {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.8},
    "campaign_manager":    {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.3},
    "website_generator":   {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.7},
}


def get_agent_config(agent_name: str) -> dict:
    """Return LLM config (provider, model, temperature, agent_name) for the given agent.

    Falls back to openrouter defaults if agent_name is not found.
    """
    base = AGENT_LLM_CONFIG.get(
        agent_name,
        {"provider": "openrouter", "model": "nvidia/nemotron-3-nano-30b-a3b:free", "temperature": 0.7},
    )
    return {**base, "agent_name": agent_name}


PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
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

    # Resolve API key
    if provider == "ollama":
        api_key = "ollama"
    elif "api_key_env" in defaults:
        api_key = os.getenv(defaults["api_key_env"], "no-key")
    else:
        api_key = os.getenv("LLM_API_KEY", "no-key")

    return ChatOpenAI(
        model=resolved_model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )


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

    push(agent_name, "llm_call", f"→ Calling {resolved_model}", {
        "system_prompt": system_prompt[:500],
        "user_prompt": user_prompt[:500],
        "model": resolved_model,
        "provider": provider,
    })

    llm = _get_llm(provider, model)
    llm = llm.with_config({"temperature": temperature})

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    content = response.content or ""

    push(agent_name, "llm_response", f"← Response from {resolved_model}", {
        "preview": content[:800],
        "length": len(content),
    })

    return content
