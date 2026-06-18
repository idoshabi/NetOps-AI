"""Pluggable LLM provider abstraction.

The MVP ships a deterministic rule-based `MockProvider` that needs no API key
and never leaves the machine. The interface matches what an OpenAI / Azure
OpenAI / Anthropic / internal-enterprise adapter would implement, so the
assistant orchestration code does not change when a real model is wired in.
"""
from abc import ABC, abstractmethod

from app.config import settings


class LLMProvider(ABC):
    name = "base"

    @abstractmethod
    def complete(self, system: str, prompt: str, context: dict) -> str:
        """Return a natural-language completion. Context holds retrieved evidence."""
        raise NotImplementedError


class MockProvider(LLMProvider):
    """Rule-based 'LLM': formats answers from structured tool output.

    Deterministic and offline. The orchestrator does the retrieval + tool calls;
    this provider only renders the final natural-language phrasing.
    """
    name = "mock-rules-v1"

    def complete(self, system: str, prompt: str, context: dict) -> str:
        # The orchestrator pre-builds the answer text; the mock simply echoes it.
        return context.get("rendered_answer", prompt)


class OpenAICompatibleProvider(LLMProvider):
    """Placeholder adapter for OpenAI / Azure OpenAI / Anthropic / internal LLMs.

    Not exercised in the MVP (no network/keys required). Shows the wiring point:
    build messages from (system, prompt, context) and call the vendor SDK.
    """
    name = "openai-compatible"

    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def complete(self, system: str, prompt: str, context: dict) -> str:  # pragma: no cover
        raise NotImplementedError(
            "Real LLM provider not configured. Set LLM_PROVIDER=mock for the MVP, "
            "or implement the vendor SDK call here."
        )


def get_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "mock":
        return MockProvider()
    return OpenAICompatibleProvider(settings.LLM_PROVIDER, settings.LLM_MODEL, settings.LLM_API_KEY)
