# Real-Time AI Intraday Trading Agent (India)

Event-driven intraday trading desk focused on **NIFTY 50** (NSE:NIFTY) index and options. Streams live ticks, analyzes multi-timeframe charts, option chain, news sentiment, and sector rotation — then emits risk-gated BUY/SELL/HOLD signals with live dashboard and Telegram alerts.

> **Disclaimer:** This software is for research and education. It is not SEBI-registered investment advice. You are responsible for all trading decisions.

## Architecture

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy, Redis pub/sub
- **Workers:** Market stream, candles, technical analysis, decision engine, options, news, alerts
- **Frontend:** Next.js 14 dashboard with WebSocket live updates
- **Data:** Zerodha Kite WebSocket (or tick simulator for dev)

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.12+ (local dev)
- Node.js 20+ (frontend)

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set USE_TICK_SIMULATOR=true for offline dev
```

### 3. Run with Docker

```bash
docker compose up --build
```

- API: http://localhost:8000
- Dashboard: http://localhost:3001 (port 3001 avoids conflict with other apps on 3000)
- Health: http://localhost:8000/health

### 4. Local backend dev

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker compose up postgres redis -d
alembic upgrade head
uvicorn app.main:app --reload
```

Run workers in separate terminals:

```bash
python -m app.workers.market_stream
python -m app.workers.candle_aggregator
python -m app.workers.technical_analysis
python -m app.workers.decision_engine
```

### 5. Zerodha Kite setup

1. Create Kite Connect app at https://developers.kite.trade/
2. Add redirect URL: `http://127.0.0.1:8765/` (required for token script)
3. Set `KITE_API_KEY` and `KITE_API_SECRET` in `.env` (no quotes around values)
4. Generate today's access token:

```bash
python3 scripts/generate_kite_token.py
```

This opens Kite login in your browser, updates `KITE_ACCESS_TOKEN` in `.env`, and sets `USE_TICK_SIMULATOR=false`.

5. Restart workers: `docker compose up -d --force-recreate worker-market backend`

### 6. TradingView webhooks

See [docs/tradingview-setup.md](docs/tradingview-setup.md). POST alerts to:

`POST http://localhost:8000/api/v1/webhooks/tradingview`

Header: `X-TV-Signature` = HMAC-SHA256(body, `TRADINGVIEW_WEBHOOK_SECRET`)

### 7. Tests

```bash
cd backend && pytest -v
```

## Trading NIFTY 50

**NIFTY** on NSE is the **Nifty 50** index. This project is configured for:

| What | Config |
|------|--------|
| Index stream | `WATCHLIST_SYMBOLS=NIFTY` (Kite token `256265`) |
| Option chain | NSE NIFTY weekly/monthly CE/PE |
| Chart | TradingView `NSE:NIFTY` |
| Signals | `symbol: NIFTY`, `instrument: e.g. 24100 CE` |

**Signal convention**

- **BUY** + bullish setup → suggested **ATM Call (CE)**
- **SELL** + bearish setup → suggested **ATM Put (PE)**

You place orders in Zerodha Kite (options on NIFTY). The agent does **not** auto-place trades by default.

## Signal JSON

```json
{
  "signal": "BUY",
  "symbol": "NIFTY",
  "instrument": "24100 CE",
  "confidence": 84,
  "entry": 22100,
  "stop_loss": 21990,
  "target_1": 22276,
  "reasons": ["Price above VWAP", "EMA bullish crossover"]
}
```

## Project layout

```
backend/app/     # API, services, workers, domain
frontend/        # Next.js dashboard
docs/            # Design, plans, deployment
deploy/k8s/      # Kubernetes manifests
```

## Deployment

See [docs/deployment.md](docs/deployment.md).
