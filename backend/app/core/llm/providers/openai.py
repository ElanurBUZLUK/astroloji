"""OpenAI provider wrapper."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from .base import LLMProvider, LLMResponse

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": kwargs.get("messages", [{"role": "user", "content": prompt}]),
            "response_format": {"type": "json_object"} if kwargs.get("json_mode") else None,
        }
        if payload["response_format"] is None:
            payload.pop("response_format")
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        timeout_ms = kwargs.get("timeout_ms")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        request_timeout = None
        if timeout_ms is not None:
            request_timeout = timeout_ms / 1000.0
        response = await self._client.post(
            f"{OPENAI_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=request_timeout,
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        finish_reason = choice.get("finish_reason")
        return LLMResponse(content=content, tokens_used=tokens_used, raw=data, finish_reason=finish_reason)

    async def close(self) -> None:
        await self._client.aclose()
