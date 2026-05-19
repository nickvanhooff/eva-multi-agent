"""Runtime LLM and pipeline settings (editable via API / Config UI)."""

import copy
import json
from pathlib import Path
from typing import Any

# Defaults mirror src/llm.py — single source for API + fallbacks
DEFAULT_AGENT_LLM_CONFIG: dict[str, dict] = {
    "researcher": {"provider": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct", "temperature": 0.4},
    "strateeg": {"provider": "groq", "model": "llama-3.1-8b-instant", "temperature": 0.5},
    "copywriter": {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.9},
    "social_specialist": {"provider": "groq", "model": "llama-3.1-8b-instant", "temperature": 0.8},
    "campaign_manager": {"provider": "openrouter", "model": "openai/gpt-oss-120b:free", "temperature": 0.3},
    "website_generator": {"provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.2},
}

DEFAULT_MAX_ITERATIONS = 3
VALID_PROVIDERS = frozenset({"groq", "openrouter", "ollama"})
CONFIG_PATH = Path("data/runtime_config.json")

# Full pickable catalog per provider (UI); saved/custom models are merged in at runtime
MODEL_OPTIONS: dict[str, list[str]] = {
    "groq": [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "gemma2-2b-it",
        "llama-guard-3-8b",
    ],
    "openrouter": [
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "qwen/qwen3-coder:free",
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "google/gemma-3-27b-it:free",
        "google/gemma-3-12b-it:free",
        "deepseek/deepseek-r1:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "microsoft/phi-4-reasoning:free",
    ],
    "ollama": [
        "llama3.2",
        "llama3.1",
        "llama3",
        "mistral",
        "mixtral",
        "qwen2.5",
        "qwen2.5-coder",
        "gemma2",
        "phi3",
    ],
}

_runtime: dict[str, Any] = {
    "max_iterations": DEFAULT_MAX_ITERATIONS,
    "agents": copy.deepcopy(DEFAULT_AGENT_LLM_CONFIG),
}


def _clamp_temperature(value: float) -> float:
    return max(0.0, min(2.0, float(value)))


def _validate_agent_entry(name: str, entry: dict) -> dict:
    if not isinstance(entry, dict):
        raise ValueError(f"Agent '{name}' config must be an object")
    provider = str(entry.get("provider", "")).strip().lower()
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Agent '{name}': invalid provider '{provider}'")
    model = str(entry.get("model", "")).strip()
    if not model:
        raise ValueError(f"Agent '{name}': model is required")
    return {
        "provider": provider,
        "model": model,
        "temperature": _clamp_temperature(entry.get("temperature", 0.7)),
    }


def get_max_iterations() -> int:
    return int(_runtime.get("max_iterations", DEFAULT_MAX_ITERATIONS))


def get_agent_llm_config(agent_name: str) -> dict:
    """LLM kwargs for call_llm (provider, model, temperature, agent_name)."""
    agents = _runtime.get("agents", DEFAULT_AGENT_LLM_CONFIG)
    base = copy.deepcopy(
        agents.get(
            agent_name,
            {"provider": "openrouter", "model": "nvidia/nemotron-3-nano-30b-a3b:free", "temperature": 0.7},
        )
    )
    return {**base, "agent_name": agent_name}


def _models_for_provider(provider: str) -> list[str]:
    """Catalog + defaults + currently saved models for this provider."""
    seen: set[str] = set()
    ordered: list[str] = []
    for source in (
        MODEL_OPTIONS.get(provider, []),
        [e["model"] for e in DEFAULT_AGENT_LLM_CONFIG.values() if e["provider"] == provider],
        [
            e["model"]
            for e in _runtime.get("agents", DEFAULT_AGENT_LLM_CONFIG).values()
            if e.get("provider") == provider
        ],
    ):
        for model in source:
            if model and model not in seen:
                seen.add(model)
                ordered.append(model)
    return ordered


def get_model_options() -> dict[str, list[str]]:
    return {p: _models_for_provider(p) for p in sorted(VALID_PROVIDERS)}


def get_recommended_models_by_agent() -> dict[str, dict[str, list[str]]]:
    """Per agent + provider: saved and default models (shown first in UI)."""
    agents = _runtime.get("agents", DEFAULT_AGENT_LLM_CONFIG)
    result: dict[str, dict[str, list[str]]] = {}
    for name in DEFAULT_AGENT_LLM_CONFIG:
        by_provider: dict[str, list[str]] = {p: [] for p in VALID_PROVIDERS}
        for provider in VALID_PROVIDERS:
            seen: set[str] = set()
            ordered: list[str] = []
            for cfg in (agents.get(name), DEFAULT_AGENT_LLM_CONFIG.get(name)):
                if not cfg or cfg.get("provider") != provider:
                    continue
                model = cfg.get("model")
                if model and model not in seen:
                    seen.add(model)
                    ordered.append(model)
            by_provider[provider] = ordered
        result[name] = by_provider
    return result


def get_public_config() -> dict:
    """Full config for GET /config (no secrets)."""
    agents = copy.deepcopy(_runtime.get("agents", DEFAULT_AGENT_LLM_CONFIG))
    return {
        "max_iterations": get_max_iterations(),
        "agents": agents,
        "saved": {
            "max_iterations": get_max_iterations(),
            "agents": agents,
        },
        "valid_providers": sorted(VALID_PROVIDERS),
        "agent_keys": list(DEFAULT_AGENT_LLM_CONFIG.keys()),
        "model_options": get_model_options(),
        "recommended_models": get_recommended_models_by_agent(),
    }


def apply_config(payload: dict, persist: bool = True) -> dict:
    """Merge validated payload into runtime config. Returns public config."""
    global _runtime

    if "max_iterations" in payload:
        n = int(payload["max_iterations"])
        if n < 1 or n > 10:
            raise ValueError("max_iterations must be between 1 and 10")
        _runtime["max_iterations"] = n

    if "agents" in payload:
        incoming = payload["agents"]
        if not isinstance(incoming, dict):
            raise ValueError("agents must be an object")
        current = copy.deepcopy(_runtime.get("agents", DEFAULT_AGENT_LLM_CONFIG))
        for name, entry in incoming.items():
            if name not in DEFAULT_AGENT_LLM_CONFIG:
                raise ValueError(f"Unknown agent '{name}'")
            current[name] = _validate_agent_entry(name, entry)
        _runtime["agents"] = current

    if persist:
        save_to_disk()
    return get_public_config()


def reset_to_defaults(persist: bool = True) -> dict:
    global _runtime
    _runtime = {
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "agents": copy.deepcopy(DEFAULT_AGENT_LLM_CONFIG),
    }
    if persist:
        save_to_disk()
    return get_public_config()


def save_to_disk() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "max_iterations": _runtime["max_iterations"],
                "agents": _runtime["agents"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_from_disk() -> None:
    if not CONFIG_PATH.exists():
        return
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        apply_config(data, persist=False)
    except Exception as e:
        print(f"[CONFIG] Could not load {CONFIG_PATH}: {e}")


# Apply saved config on import
load_from_disk()
