from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    stream: bool = False
    tools: list[dict[str, Any]] | None = None


app = FastAPI(title="mock-upstream")


def _check_auth(authorization: str | None) -> None:
    required = os.getenv("MOCK_UPSTREAM_API_KEY", "")
    if not required:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.removeprefix("Bearer ").strip()
    if token != required:
        raise HTTPException(status_code=401, detail="invalid bearer")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, authorization: str | None = Header(default=None)):
    _check_auth(authorization)

    if body.stream:
        async def gen():
            if body.tools:
                chunks = [
                    {"choices": [{"delta": {"tool_calls": [{"id": "call_mock_1", "function": {"name": "read_file", "arguments": '{\"path\":\"m'}}]}}]},
                    {"choices": [{"delta": {"tool_calls": [{"function": {"arguments": 'ain.py\"}'}}]}}]},
                ]
            else:
                chunks = [
                    {"choices": [{"delta": {"content": "Hel"}}]},
                    {"choices": [{"delta": {"content": "lo from mock upstream"}}]},
                ]

            for chunk in chunks:
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    if body.tools:
        return {
            "id": "chatcmpl_mock_tool",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_mock_1",
                                "type": "function",
                                "function": {"name": "read_file", "arguments": '{"path":"main.py"}'},
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    last_content = body.messages[-1].get("content", "") if body.messages else ""
    return {
        "id": "chatcmpl_mock_text",
        "choices": [{"message": {"role": "assistant", "content": f"echo: {last_content}"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17},
    }
