from typing import Protocol


class LLMClientError(Exception):
    """Base exception for LLM client failures."""


class LLMConfigurationError(LLMClientError):
    """Raised when the LLM client is missing required configuration."""


class LLMProviderError(LLMClientError):
    """Raised when the remote LLM provider returns an error."""


class BaseLLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        ...
