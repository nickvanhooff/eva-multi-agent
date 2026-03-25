"""LangSmith integration for debugging and monitoring the multi-agent system.

LangSmith (https://smith.langchain.com) provides:
- Real-time tracing of all LLM calls and agent steps
- Performance monitoring (latency, token usage, cost)
- Debugging interface to inspect state transitions
- Comparison of different runs

Configuration via environment variables:
- LANGSMITH_ENABLED: Enable/disable tracing (default: false)
- LANGSMITH_API_KEY: Your LangSmith API key (from https://smith.langchain.com)
- LANGSMITH_PROJECT: Project name (default: 'eva-multi-agent')
- LANGSMITH_ENDPOINT: API endpoint (usually default)
"""

import os


def setup_tracing() -> bool:
    """Configure LangSmith tracing for the LangGraph application.

    Returns:
        True if LangSmith is enabled, False otherwise.
    """
    enabled = os.getenv("LANGSMITH_ENABLED", "false").lower() == "true"

    if not enabled:
        return False

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print(
            "[WARNING] LANGSMITH_ENABLED=true but LANGSMITH_API_KEY not set. "
            "Tracing disabled."
        )
        return False

    # Set environment variables for LangSmith SDK
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = os.getenv(
        "LANGSMITH_PROJECT", "eva-multi-agent"
    )

    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ["LANGSMITH_ENDPOINT"] = endpoint

    print(
        f"\n[TRACING] LangSmith enabled for project: {os.environ['LANGSMITH_PROJECT']}"
    )
    print(f"[TRACING] Dashboard: https://smith.langchain.com/")
    print(
        "[TRACING] All agent steps, LLM calls, and state transitions will be traced.\n"
    )

    return True


def get_tracing_config() -> dict:
    """Get current tracing configuration.

    Returns:
        Dictionary with tracing status and project name.
    """
    enabled = os.getenv("LANGSMITH_ENABLED", "false").lower() == "true"
    return {
        "enabled": enabled,
        "project": os.getenv("LANGSMITH_PROJECT", "eva-multi-agent"),
        "endpoint": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
    }
