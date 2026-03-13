from __future__ import annotations

from time import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.auth.bearer import auth_error_response, require_bearer
from app.domain.canonical import CanonicalConversation, ResponseCreateRequest
from app.domain.mapper_canonical_to_chat import to_chat_payload
from app.domain.mapper_chat_to_responses import assistant_message_from_output, map_non_stream
from app.domain.mapper_responses_to_canonical import UnsupportedFeatureError, to_canonical
from app.domain.streaming_adapter import adapt_chat_stream
from app.utils.errors import error_response
from app.utils.ids import new_function_call_item_id, new_message_id, new_response_id

router = APIRouter()


@router.post("/v1/responses")
async def create_response(request: Request, body: ResponseCreateRequest):
    try:
        await require_bearer(request.headers.get("Authorization"))
    except PermissionError:
        return auth_error_response()

    try:
        current = to_canonical(body)
    except UnsupportedFeatureError as exc:
        return error_response(exc.message, exc.code, 400, param=exc.param, err_type="unsupported_feature")

    store = request.app.state.response_store
    if body.previous_response_id:
        previous = store.get(body.previous_response_id)
        if not previous:
            return error_response("previous_response_id not found.", "not_found", 404, "previous_response_id")
        prev_conv = CanonicalConversation.model_validate(previous["canonical_conversation_after_call"])
        merged_messages = prev_conv.messages + current.messages
        instructions = body.instructions
        if instructions:
            filtered = [m for m in merged_messages if m.role != "system"]
            merged_messages = filtered
        current = CanonicalConversation(
            model=current.model,
            instructions=instructions,
            messages=merged_messages,
            tools=current.tools,
            tool_choice=current.tool_choice,
            stream=current.stream,
            temperature=current.temperature,
            top_p=current.top_p,
            max_output_tokens=current.max_output_tokens,
        )

    payload = to_chat_payload(current)
    client = request.app.state.upstream_client
    response_id = new_response_id()
    created_at = int(time())

    if body.stream:
        item_id = new_message_id()
        fn_item_id = new_function_call_item_id()

        async def event_gen():
            try:
                async for event in adapt_chat_stream(
                    chunks=client.stream_chat_completion(payload),
                    response_id=response_id,
                    model=body.model,
                    item_id=item_id,
                    function_item_id=fn_item_id,
                ):
                    yield event
            except Exception as exc:  # noqa: BLE001
                yield f"event: error\ndata: {{\"message\": \"{str(exc)}\"}}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_gen(), media_type="text/event-stream")

    try:
        upstream_resp = await client.create_chat_completion(payload)
    except Exception as exc:  # noqa: BLE001
        return error_response(
            f"Upstream chat/completions rejected the request: {str(exc)}",
            "upstream_400",
            502,
            err_type="upstream_error",
        )

    wrapped = map_non_stream(upstream_resp, response_id=response_id, model=body.model)

    assistant_message = assistant_message_from_output(wrapped["output"])
    conv_after = current.model_copy(deep=True)
    conv_after.messages.append(assistant_message)

    store.put(
        response_id,
        {
            "response_id": response_id,
            "created_at": created_at,
            "model": body.model,
            "canonical_conversation_before_call": current.model_dump(),
            "canonical_conversation_after_call": conv_after.model_dump(),
            "assistant_output": wrapped["output"],
            "usage": wrapped.get("usage", {}),
        },
    )

    return JSONResponse(content=wrapped)
