import httpx
from fastapi import FastAPI

from app.clients.upstream_chat_client import UpstreamChatClient
from app.config import settings
from app.domain.response_store import InMemoryResponseStore
from app.routes.health import router as health_router
from app.routes.models import router as models_router
from app.routes.responses import router as responses_router
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="responses-completions-shim")
    app.state.response_store = InMemoryResponseStore()
    app.state.upstream_client = UpstreamChatClient(
        base_url=settings.upstream_base_url,
        api_key=settings.upstream_api_key,
        timeout=httpx.Timeout(settings.read_timeout_s, connect=settings.connect_timeout_s),
    )

    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(responses_router)
    return app


app = create_app()
