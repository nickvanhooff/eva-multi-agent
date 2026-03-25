"""Provider-agnostic LLM wrapper using LangChain's ChatOpenAI.

Supports Ollama, OpenRouter, and Groq via base_url switching.
Uses LangChain for automatic LangSmith tracing integration.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Provider configurations
PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "llama3.2",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
}


def _get_llm() -> ChatOpenAI:
    """Create a ChatOpenAI client based on environment configuration.

    Automatically integrates with LangSmith for tracing when configured.

    Returns:
        ChatOpenAI instance configured for the current provider.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["ollama"])

    base_url = os.getenv("LLM_BASE_URL", defaults["base_url"])
    api_key = os.getenv("LLM_API_KEY", defaults.get("api_key", "no-key"))
    model = os.getenv("LLM_MODEL", defaults["model"])

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Call an LLM via LangChain's ChatOpenAI.

    Args:
        system_prompt: The system instructions for the LLM.
        user_prompt: The user message / task for the LLM.
        temperature: Creativity control (0.0 = deterministic, 1.0 = creative).

    Returns:
        The LLM's response as a plain string.
    """
    llm = _get_llm()
    llm = llm.with_config({"temperature": temperature})

    from langchain.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    return response.content or ""
