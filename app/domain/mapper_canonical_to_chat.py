from __future__ import annotations

from typing import Any

from app.domain.canonical import CanonicalConversation


def _message_content_to_chat_string(content: list[dict]) -> str | None:
    text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
    if text_parts:
        return "\n".join(text_parts)
    return None


def to_chat_payload(conversation: CanonicalConversation) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []

    for message in conversation.messages:
        if message.role == "assistant" and any(item.get("type") == "tool_call" for item in message.content):
            arguments = ""
            for item in message.content:
                if item.get("type") == "tool_call":
                    arguments = item.get("arguments", "")
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": message.tool_call_id,
                            "type": "function",
                            "function": {
                                "name": message.tool_name,
                                "arguments": arguments,
                            },
                        }
                    ],
                }
            )
            continue

        chat_message: dict[str, Any] = {"role": message.role}
        if message.role == "tool":
            chat_message["tool_call_id"] = message.tool_call_id
            chat_message["content"] = _message_content_to_chat_string(message.content) or ""
        else:
            chat_message["content"] = _message_content_to_chat_string(message.content) or ""
        messages.append(chat_message)

    payload: dict[str, Any] = {
        "model": conversation.model,
        "messages": messages,
        "stream": conversation.stream,
    }

    if conversation.tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description"),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            }
            for t in conversation.tools
        ]
    if conversation.tool_choice is not None:
        if isinstance(conversation.tool_choice, dict):
            payload["tool_choice"] = {
                "type": "function",
                "function": {"name": conversation.tool_choice["name"]},
            }
        else:
            payload["tool_choice"] = conversation.tool_choice

    if conversation.temperature is not None:
        payload["temperature"] = conversation.temperature
    if conversation.top_p is not None:
        payload["top_p"] = conversation.top_p
    if conversation.max_output_tokens is not None:
        payload["max_completion_tokens"] = conversation.max_output_tokens

    return payload
