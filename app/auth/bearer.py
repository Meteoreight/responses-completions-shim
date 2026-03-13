from fastapi import Header

from app.config import settings
from app.utils.errors import error_response


async def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not settings.shim_api_key:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionError("missing bearer")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.shim_api_key:
        raise PermissionError("invalid bearer")


def auth_error_response():
    return error_response("Invalid or missing bearer token.", "unauthorized", 401, err_type="authentication_error")
