from fastapi.responses import JSONResponse


def error_response(message: str, code: str, status_code: int, param: str | None = None, err_type: str = "invalid_request_error") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": err_type,
                "param": param,
                "code": code,
            }
        },
    )
