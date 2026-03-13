# Docker Compose Setup

```bash
docker compose up --build
```

Services:

- shim: `http://localhost:8080`
- upstream-mock: internal compose service on `http://upstream-mock:8001`

## Smoke test (non-stream)

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

## Smoke test (stream)

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
