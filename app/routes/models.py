from fastapi import APIRouter

router = APIRouter()


@router.get("/v1/models")
async def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-5.2",
                "object": "model",
                "owned_by": "APIM",
            }
        ],
    }
