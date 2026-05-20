# Deployment Guide

## Docker Compose (development / small prod)

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

## Kubernetes (production-ready skeleton)

1. Create secrets: `trading-agent-secrets` with DB URL, Redis URL, Kite keys, Telegram token
2. Apply manifests:

```bash
kubectl apply -f deploy/k8s/
```

3. Scale workers independently:

```bash
kubectl scale deployment worker-market --replicas=1
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL async URL |
| REDIS_URL | Yes | Redis connection |
| KITE_* | For live | Zerodha credentials |
| USE_TICK_SIMULATOR | Dev | `true` = synthetic ticks |
| TRADINGVIEW_WEBHOOK_SECRET | Prod | HMAC secret |
| TELEGRAM_* | Optional | Alert delivery |

## Health checks

- Liveness: `GET /health`
- Workers: process heartbeat via logs (add Prometheus in phase 2)

## Performance notes

- Run Redis and Postgres on same AZ as workers
- Target &lt;500ms signal-to-dashboard on LAN
- NSE option chain: respect rate limits; circuit breaker pauses 60s after 3 failures
