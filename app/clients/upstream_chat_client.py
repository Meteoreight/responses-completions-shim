from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx


class UpstreamChatClient:
    def __init__(self, base_url: str, api_key: str, timeout: httpx.Timeout) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def create_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/v1/chat/completions", headers=self._headers(), json=payload)
            resp.raise_for_status()
            return resp.json()

    async def stream_chat_completion(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base_url}/v1/chat/completions", headers=self._headers(), json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    yield json.loads(data)
