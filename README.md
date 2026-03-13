# responses-completions-shim

FastAPI shim that exposes a minimal OpenAI Responses-compatible API for Codex and forwards inference to an internal `/v1/chat/completions` endpoint.

## Endpoints

- `POST /v1/responses`
- `GET /v1/models`
- `GET /healthz`
- `GET /readyz`

## Docker Composeで起動

```bash
docker compose up --build
```

起動後:

- shim: `http://localhost:8080`
- mock upstream: `http://localhost:8001` (compose内部向け)

### 動作確認（non-stream）

```bash
curl -sS http://localhost:8080/v1/responses \
  -H "Authorization: Bearer local-shim-token" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "input": "say hello",
    "stream": false
  }'
```

### 動作確認（stream）

```bash
curl -N http://localhost:8080/v1/responses \
  -H "Authorization: Bearer local-shim-token" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "input": "say hello",
    "stream": true
  }'
```

## ローカル実行

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Environment variables:

- `UPSTREAM_BASE_URL`
- `UPSTREAM_API_KEY`
- `SHIM_API_KEY` (optional)
