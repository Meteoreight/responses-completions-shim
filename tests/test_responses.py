import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class FakeUpstreamClient:
    def __init__(self):
        self.last_payload = None

    async def create_chat_completion(self, payload):
        self.last_payload = payload
        user_text = payload["messages"][-1].get("content", "")
        if payload.get("tools"):
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call_abc123",
                                    "type": "function",
                                    "function": {"name": "read_file", "arguments": '{"path":"main.py"}'},
                                }
                            ]
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

        if "what is my name" in user_text.lower():
            history = "\n".join([m.get("content", "") for m in payload["messages"]])
            if "Ten" in history:
                reply = "Your name is Ten"
            else:
                reply = "I do not know"
        else:
            reply = "hello"

        return {
            "choices": [{"message": {"content": reply}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    async def stream_chat_completion(self, payload):
        self.last_payload = payload
        for part in [
            {"choices": [{"delta": {"content": "Hel"}}]},
            {"choices": [{"delta": {"content": "lo"}}]},
        ]:
            yield part


@pytest.fixture
async def client():
    app = create_app()
    app.state.upstream_client = FakeUpstreamClient()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_non_stream_text(client):
    resp = await client.post("/v1/responses", json={"model": "gpt-5.2", "input": "say hello", "stream": False})
    data = resp.json()
    assert resp.status_code == 200
    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["output"][0]["type"] == "message"
    assert data["output"][0]["content"][0]["type"] == "output_text"


@pytest.mark.asyncio
async def test_stream_text(client):
    resp = await client.post("/v1/responses", json={"model": "gpt-5.2", "input": "say hello", "stream": True})
    body = resp.text
    assert resp.status_code == 200
    assert "event: response.created" in body
    assert "event: response.output_text.delta" in body
    assert "event: response.completed" in body
    assert "data: [DONE]" in body


@pytest.mark.asyncio
async def test_function_call_non_stream(client):
    req = {
        "model": "gpt-5.2",
        "input": "read_file を使って",
        "tools": [
            {
                "type": "function",
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            }
        ],
        "stream": False,
    }
    resp = await client.post("/v1/responses", json=req)
    data = resp.json()
    assert resp.status_code == 200
    assert data["output"][0]["type"] == "function_call"
    assert data["output"][0]["name"] == "read_file"
    json.loads(data["output"][0]["arguments"])


@pytest.mark.asyncio
async def test_previous_response_id(client):
    first = await client.post("/v1/responses", json={"model": "gpt-5.2", "input": "my name is Ten"})
    rid = first.json()["id"]
    second = await client.post(
        "/v1/responses",
        json={"model": "gpt-5.2", "previous_response_id": rid, "input": "what is my name?"},
    )
    text = second.json()["output"][0]["content"][0]["text"]
    assert "Ten" in text


@pytest.mark.asyncio
async def test_unsupported_input_image(client):
    resp = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-5.2",
            "input": [{"type": "input_image", "image_url": "https://example.com/img.png"}],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "unsupported_input_image"
