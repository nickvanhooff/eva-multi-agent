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


def _get_llm(provider: str = None) -> ChatOpenAI:
    """Create a ChatOpenAI client for the given provider.

    Args:
        provider: Provider name (groq, openrouter, ollama).
                  Defaults to LLM_PROVIDER env var.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["ollama"])

    base_url = defaults["base_url"]
    model = os.getenv("LLM_MODEL", defaults["model"]) if provider == os.getenv("LLM_PROVIDER") else defaults["model"]

    # Resolve API key
    if provider == "ollama":
        api_key = "ollama"
    elif "api_key_env" in defaults:
        api_key = os.getenv(defaults["api_key_env"], "no-key")
    else:
        api_key = os.getenv("LLM_API_KEY", "no-key")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    provider: str = None,
) -> str:
    """Call an LLM via LangChain's ChatOpenAI.

    Args:
        system_prompt: The system instructions for the LLM.
        user_prompt: The user message / task for the LLM.
        temperature: Creativity control (0.0 = deterministic, 1.0 = creative).
        provider: Optional provider override (groq, openrouter, ollama).

    Returns:
        The LLM's response as a plain string.
    """
    llm = _get_llm(provider)
    llm = llm.with_config({"temperature": temperature})

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    return response.content or ""
