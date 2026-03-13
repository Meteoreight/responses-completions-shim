# responses-completions-shim

FastAPI shim that exposes a minimal OpenAI Responses-compatible API for Codex and forwards inference to an internal `/v1/chat/completions` endpoint.

## Endpoints

- `POST /v1/responses`
- `GET /v1/models`
- `GET /healthz`
- `GET /readyz`

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Environment variables:

- `UPSTREAM_BASE_URL`
- `UPSTREAM_API_KEY`
- `SHIM_API_KEY` (optional)

## Run with Docker Compose

Use Docker Compose if you want to run the shim and a mock upstream service together.

```bash
docker compose up --build
```

After startup:

- shim: `http://localhost:8080`
- upstream-mock: `http://upstream-mock:8001` (internal compose network)

For smoke-test examples (stream/non-stream), see `docs/docker-compose.md`.
