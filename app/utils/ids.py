from uuid import uuid4


def new_response_id() -> str:
    return f"resp_{uuid4().hex[:24]}"


def new_message_id() -> str:
    return f"msg_{uuid4().hex[:24]}"


def new_function_call_item_id() -> str:
    return f"fc_{uuid4().hex[:24]}"


def new_request_id() -> str:
    return f"req_{uuid4().hex[:24]}"
