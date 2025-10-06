"""Provider pool that handles failover and cooldown."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .providers.base import LLMProvider, LLMResponse


@dataclass
class ProviderEntry:
    """Configuration wrapper that tracks cooldown state for a provider."""
    name: str
    provider: LLMProvider
    cooldown_seconds: int = 60
    last_failure: float = field(default=0.0)
    retry_count: int = field(default=0)

    @property
    def is_available(self) -> bool:
        """Return True when the provider is outside its cooldown window."""
        return time.time() - self.last_failure >= self.cooldown_seconds


class LLMProviderPool:
    """Async-first registry that routes generation calls across providers."""
    def __init__(self) -> None:
        self._providers: List[ProviderEntry] = []
        self._index: Dict[str, ProviderEntry] = {}

    def register(self, entry: ProviderEntry) -> None:
        """Register a provider entry so it can participate in routing."""
        self._providers.append(entry)
        self._index[entry.name] = entry

    async def generate(self, **kwargs: Any) -> LLMResponse:
        """Try providers in registration order until one succeeds."""
        if not self._providers:
            raise RuntimeError("No LLM providers configured")

        errors: Dict[str, str] = {}
        for entry in self._providers:
            if not entry.is_available:
                continue
            try:
                response = await entry.provider.generate(**kwargs)
                entry.retry_count = 0
                return response
            except Exception as exc:  # pragma: no cover - network failure
                entry.last_failure = time.time()
                entry.retry_count += 1
                errors[entry.name] = str(exc)
                continue

        # If all providers fail, raise combined error
        raise RuntimeError(f"All providers failed: {errors}")

    async def generate_with(self, provider_name: str, **kwargs: Any) -> LLMResponse:
        """Invoke a specific provider by name, honoring cooldown state."""
        entry = self._index.get(provider_name)
        if not entry:
            raise RuntimeError(f"Provider '{provider_name}' is not registered")
        if not entry.is_available:
            raise RuntimeError(f"Provider '{provider_name}' is cooling down")
        try:
            response = await entry.provider.generate(**kwargs)
            entry.retry_count = 0
            return response
        except Exception as exc:  # pragma: no cover - network failure
            entry.last_failure = time.time()
            entry.retry_count += 1
            raise

    def get_provider(self, name: str) -> Optional[ProviderEntry]:
        """Retrieve a provider entry without issuing a request."""
        return self._index.get(name)

    async def close(self) -> None:
        """Cascade an async close call to each underlying provider if present."""
        for entry in self._providers:
            close = getattr(entry.provider, "close", None)
            if close:
                await close()
