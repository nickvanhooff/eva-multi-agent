"""Provider-agnostic LLM wrapper using the OpenAI SDK.

Supports Ollama, OpenRouter, and Groq via base_url switching.
No LangChain dependency — pure openai SDK.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Provider configurations
PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",  # Ollama doesn't need a real key
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


def _get_client() -> tuple[OpenAI, str]:
    """Create an OpenAI client based on environment configuration.

    Returns:
        Tuple of (client, model_name)
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["ollama"])

    base_url = os.getenv("LLM_BASE_URL", defaults["base_url"])
    api_key = os.getenv("LLM_API_KEY", defaults.get("api_key", "no-key"))
    model = os.getenv("LLM_MODEL", defaults["model"])

    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Call an LLM via the OpenAI-compatible API.

    Args:
        system_prompt: The system instructions for the LLM.
        user_prompt: The user message / task for the LLM.
        temperature: Creativity control (0.0 = deterministic, 1.0 = creative).

    Returns:
        The LLM's response as a plain string.
    """
    client, model = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content or ""
