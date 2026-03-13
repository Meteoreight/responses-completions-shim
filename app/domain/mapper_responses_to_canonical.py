from __future__ import annotations

from typing import Any

from app.domain.canonical import CanonicalConversation, CanonicalMessage, ResponseCreateRequest


class UnsupportedFeatureError(Exception):
    def __init__(self, message: str, code: str, param: str = "input") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.param = param


def _normalize_content_item(item: dict[str, Any]) -> dict[str, Any]:
    item_type = item.get("type")
    if item_type in {"input_text", "output_text", "text"}:
        return {"type": "text", "text": item.get("text", "")}
    if item_type == "tool_call":
        return {"type": "tool_call", "arguments": item.get("arguments", "")}
    if item_type == "input_image":
        raise UnsupportedFeatureError(
            "This shim currently supports text + function tools only. input_image is not supported.",
            "unsupported_input_image",
        )
    if item_type == "input_file":
        raise UnsupportedFeatureError(
            "This shim currently supports text + function tools only. input_file is not supported.",
            "unsupported_input_file",
        )
    raise UnsupportedFeatureError(f"Unsupported content item type: {item_type}", "unsupported_content_item")


def _normalize_message(message: dict[str, Any]) -> CanonicalMessage:
    role = message.get("role", "user")
    content = message.get("content", "")
    if isinstance(content, str):
        norm_content = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        norm_content = [_normalize_content_item(item) for item in content]
    else:
        raise UnsupportedFeatureError("Invalid message content type.", "invalid_message_content")

    return CanonicalMessage(
        role=role,
        content=norm_content,
        tool_call_id=message.get("tool_call_id") or message.get("call_id"),
        tool_name=message.get("tool_name") or message.get("name"),
    )


def _normalize_input(raw_input: Any) -> list[CanonicalMessage]:
    if isinstance(raw_input, str):
        return [CanonicalMessage(role="user", content=[{"type": "text", "text": raw_input}])]

    if isinstance(raw_input, list):
        if not raw_input:
            return []
        if isinstance(raw_input[0], dict) and "role" in raw_input[0]:
            return [_normalize_message(m) for m in raw_input]
        if isinstance(raw_input[0], dict) and "type" in raw_input[0]:
            return [CanonicalMessage(role="user", content=[_normalize_content_item(i) for i in raw_input])]

    raise UnsupportedFeatureError("Unsupported input format.", "unsupported_input")


def _normalize_tools(raw_tools: list[dict] | None) -> list[dict]:
    tools = raw_tools or []
    normalized: list[dict] = []
    for tool in tools:
        if tool.get("type") != "function":
            raise UnsupportedFeatureError(
                "This shim currently supports function tools only.",
                "unsupported_tool_type",
                "tools",
            )
        if "name" not in tool:
            raise UnsupportedFeatureError("Function tool must include name.", "invalid_tool", "tools")
        normalized.append(tool)
    return normalized


def _normalize_tool_choice(tool_choice: Any) -> Any:
    if tool_choice is None:
        return None
    if tool_choice in {"auto", "none", "required"}:
        return tool_choice
    if isinstance(tool_choice, dict) and tool_choice.get("type") == "function" and tool_choice.get("name"):
        return tool_choice
    raise UnsupportedFeatureError("Unsupported tool_choice.", "unsupported_tool_choice", "tool_choice")


def to_canonical(req: ResponseCreateRequest) -> CanonicalConversation:
    messages = _normalize_input(req.input)
    tools = _normalize_tools(req.tools)
    tool_choice = _normalize_tool_choice(req.tool_choice)

    if req.instructions:
        insert_at = 0
        for i, message in enumerate(messages):
            if message.role == "developer":
                insert_at = i + 1
        messages.insert(insert_at, CanonicalMessage(role="system", content=[{"type": "text", "text": req.instructions}]))

    return CanonicalConversation(
        model=req.model,
        instructions=req.instructions,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        stream=req.stream,
        temperature=req.temperature,
        top_p=req.top_p,
        max_output_tokens=req.max_output_tokens,
    )
