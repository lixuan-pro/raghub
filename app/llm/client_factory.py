import os

from app.llm.base import BaseLLMClient, LLMConfigurationError
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.mock_client import MockLLMClient


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()

    if selected_provider == "mock":
        return MockLLMClient()

    if selected_provider == "deepseek":
        return DeepSeekLLMClient()

    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER: {selected_provider}"
    )
