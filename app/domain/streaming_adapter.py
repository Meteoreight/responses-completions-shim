from __future__ import annotations

import json
from time import time
from typing import Any, AsyncIterator


def sse(event: str, data: dict[str, Any] | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def adapt_chat_stream(
    chunks: AsyncIterator[dict[str, Any]],
    response_id: str,
    model: str,
    item_id: str,
    function_item_id: str,
) -> AsyncIterator[str]:
    created = int(time())
    yield sse("response.created", {"id": response_id, "object": "response", "created_at": created, "model": model, "status": "in_progress"})
    yield sse("response.in_progress", {"id": response_id, "status": "in_progress"})

    text_acc = ""
    args_acc = ""
    call_id = None
    function_name = None
    saw_text = False
    saw_function = False

    async for chunk in chunks:
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        content_delta = delta.get("content")
        if content_delta:
            saw_text = True
            text_acc += content_delta
            yield sse("response.output_text.delta", {"response_id": response_id, "item_id": item_id, "delta": content_delta})

        tool_calls = delta.get("tool_calls") or []
        if tool_calls:
            saw_function = True
            call = tool_calls[0]
            call_id = call.get("id") or call_id
            fn = call.get("function", {})
            function_name = fn.get("name") or function_name
            arg_delta = fn.get("arguments")
            if arg_delta:
                args_acc += arg_delta
                yield sse("response.function_call_arguments.delta", {"response_id": response_id, "item_id": function_item_id, "delta": arg_delta})

    final_output = []
    if saw_function:
        yield sse(
            "response.function_call_arguments.done",
            {"response_id": response_id, "item_id": function_item_id, "arguments": args_acc},
        )
        final_output.append({"id": function_item_id, "type": "function_call", "call_id": call_id, "name": function_name, "arguments": args_acc})
    else:
        if saw_text:
            yield sse("response.output_text.done", {"response_id": response_id, "item_id": item_id, "text": text_acc})
        final_output.append(
            {
                "id": item_id,
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": text_acc}],
            }
        )

    yield sse("response.completed", {"id": response_id, "object": "response", "created_at": created, "status": "completed", "model": model, "output": final_output})
    yield "data: [DONE]\n\n"
