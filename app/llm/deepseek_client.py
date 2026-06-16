import os
from typing import Any

from app.llm.base import LLMConfigurationError, LLMProviderError


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


class DeepSeekLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        openai_client_cls: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv(
            "DEEPSEEK_BASE_URL",
            DEFAULT_DEEPSEEK_BASE_URL,
        )
        self.model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)

        if not self.api_key:
            raise LLMConfigurationError(
                "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek"
            )

        if openai_client_cls is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMConfigurationError(
                    "openai package is required for DeepSeekLLMClient"
                ) from exc
            openai_client_cls = OpenAI

        self.client = openai_client_cls(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
        except Exception as exc:
            raise LLMProviderError("DeepSeek request failed") from exc

        if not content:
            raise LLMProviderError("DeepSeek returned an empty response")

        return content.strip()
