from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ResponseCreateRequest(BaseModel):
    model: str
    input: Any
    instructions: str | None = None
    tools: list[dict] | None = None
    tool_choice: Any | None = None
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_output_tokens: int | None = None
    previous_response_id: str | None = None
    metadata: dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None
    store: bool | None = None
    text: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None


class CanonicalMessage(BaseModel):
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: list[dict]
    tool_call_id: str | None = None
    tool_name: str | None = None


class CanonicalConversation(BaseModel):
    model: str
    instructions: str | None = None
    messages: list[CanonicalMessage] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    tool_choice: Any | None = None
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_output_tokens: int | None = None
