from __future__ import annotations

from time import time
from typing import Any

from app.utils.ids import new_function_call_item_id, new_message_id


def map_non_stream(chat_response: dict[str, Any], response_id: str, model: str) -> dict[str, Any]:
    choice = chat_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    output: list[dict[str, Any]] = []

    if message.get("tool_calls"):
        for tool_call in message["tool_calls"]:
            output.append(
                {
                    "id": new_function_call_item_id(),
                    "type": "function_call",
                    "call_id": tool_call.get("id"),
                    "name": tool_call.get("function", {}).get("name"),
                    "arguments": tool_call.get("function", {}).get("arguments", ""),
                }
            )
    else:
        output.append(
            {
                "id": new_message_id(),
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": message.get("content", ""),
                    }
                ],
            }
        )

    usage = chat_response.get("usage", {})
    return {
        "id": response_id,
        "object": "response",
        "created_at": int(time()),
        "status": "completed",
        "model": model,
        "output": output,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }


def assistant_message_from_output(output_items: list[dict[str, Any]]) -> dict[str, Any]:
    first = output_items[0]
    if first["type"] == "function_call":
        return {
            "role": "assistant",
            "tool_call_id": first["call_id"],
            "tool_name": first["name"],
            "content": [{"type": "tool_call", "arguments": first.get("arguments", "")}],
        }
    return {
        "role": "assistant",
        "content": [{"type": "text", "text": first["content"][0]["text"]}],
    }
