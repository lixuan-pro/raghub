import pytest

from app.llm.base import LLMConfigurationError, LLMProviderError
from app.llm.client_factory import get_llm_client
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.mock_client import MockLLMClient


class FakeMessage:
    content = "DeepSeek fake answer"


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]


class FakeCompletions:
    def __init__(self) -> None:
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return FakeResponse()


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeOpenAI:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.chat = FakeChat()


class FailingCompletions:
    def create(self, **kwargs):
        raise RuntimeError("network error")


class FailingChat:
    completions = FailingCompletions()


class FailingOpenAI:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.chat = FailingChat()


def test_get_llm_client_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_get_llm_client_uses_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_get_llm_client_builds_deepseek_client(monkeypatch):
    fake_client = object()
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(
        "app.llm.client_factory.DeepSeekLLMClient",
        lambda: fake_client,
    )

    client = get_llm_client()

    assert client is fake_client


def test_deepseek_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError):
        DeepSeekLLMClient(openai_client_cls=FakeOpenAI)


def test_deepseek_client_generate_uses_openai_compatible_client():
    client = DeepSeekLLMClient(
        api_key="test-key",
        base_url="https://example.test",
        model="deepseek-v4-flash",
        openai_client_cls=FakeOpenAI,
    )

    answer = client.generate("hello")

    assert answer == "DeepSeek fake answer"
    request = client.client.chat.completions.last_request
    assert request["model"] == "deepseek-v4-flash"
    assert request["messages"][0]["content"] == "hello"


def test_deepseek_client_wraps_provider_errors():
    client = DeepSeekLLMClient(
        api_key="test-key",
        openai_client_cls=FailingOpenAI,
    )

    with pytest.raises(LLMProviderError):
        client.generate("hello")
