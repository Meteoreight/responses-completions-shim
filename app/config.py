from pydantic import BaseModel
import os


class Settings(BaseModel):
    upstream_base_url: str = os.getenv("UPSTREAM_BASE_URL", "http://localhost:8001")
    upstream_api_key: str = os.getenv("UPSTREAM_API_KEY", "")
    shim_api_key: str = os.getenv("SHIM_API_KEY", "")
    connect_timeout_s: float = float(os.getenv("CONNECT_TIMEOUT_S", "5"))
    read_timeout_s: float = float(os.getenv("READ_TIMEOUT_S", "120"))


settings = Settings()
