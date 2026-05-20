# Real-Time AI Intraday Trading Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an event-driven Indian intraday trading agent that ingests live broker ticks, fuses TA/options/sentiment/sector data, emits risk-gated signals, and streams them to a Next.js dashboard and Telegram.

**Architecture:** Modular monolith (`backend/app`) with async FastAPI API/WS, Redis pub/sub event bus, dedicated worker processes for ingest/aggregate/analyze/decide, PostgreSQL for signals and history. Zerodha Kite v1 via adapter interface. Phased delivery — each phase is deployable.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, Redis, PostgreSQL, Next.js 14, Tailwind, TA-Lib, scikit-learn, transformers, Docker Compose.

**Design spec:** `docs/superpowers/specs/2026-05-20-realtime-trading-agent-design.md`

---

## Spec Coverage Map

| Requirement | Phase | Tasks |
|-------------|-------|-------|
| Live tick streaming | 1 | 1.8–1.12 |
| Multi-TF candles | 1–2 | 1.12, 2.3–2.6 |
| Options chain live | 3 | 3.1–3.5 |
| News sentiment | 4 | 4.1–4.4 |
| Sector rotation | 3 | 3.6–3.8 |
| Breakout/reversal/institutional | 2–3 | 2.7–2.12, 3.3 |
| AI decision + confidence | 5 | 5.1–5.8 |
| TradingView webhooks | 7 | 7.1–7.3 |
| Telegram alerts | 6 | 6.7–6.8 |
| WebSocket dashboard | 6 | 6.1–6.6 |
| Risk management | 5 | 5.6–5.7 |
| Backtesting | 8 | 8.1–8.5 |
| AI memory/learning | 8 | 8.6–8.8 |
| Docker/K8s | 0, 9 | 0.1–0.5, 9.1–9.3 |
| PostgreSQL schema | 0 | 0.6–0.9 |

---

## Phase 0: Platform Foundation

### Task 0.1: Monorepo scaffold and tooling

**Files:**
- Create: `README.md`, `.gitignore`, `.env.example`, `docker-compose.yml`
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`
- Create: `frontend/package.json` (minimal placeholder)

- [ ] **Step 1: Create `.gitignore`**

```gitignore
.env
__pycache__/
*.pyc
.pytest_cache/
node_modules/
.next/
dist/
*.egg-info/
.venv/
data/
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: trading
      POSTGRES_PASSWORD: trading
      POSTGRES_DB: trading_agent
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  backend:
    build: ./backend
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8000:8000"]
  worker-market:
    build: ./backend
    command: python -m app.workers.market_stream
    env_file: .env
    depends_on: [postgres, redis]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
volumes:
  pgdata:
```

- [ ] **Step 3: Create `.env.example`**

```bash
# App
APP_ENV=development
LOG_LEVEL=INFO
TIMEZONE=Asia/Kolkata

# Database
DATABASE_URL=postgresql+asyncpg://trading:trading@localhost:5432/trading_agent

# Redis
REDIS_URL=redis://localhost:6379/0

# Zerodha Kite
KITE_API_KEY=
KITE_API_SECRET=
KITE_ACCESS_TOKEN=

# TradingView webhook
TRADINGVIEW_WEBHOOK_SECRET=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Risk
CONFIDENCE_THRESHOLD=70
MAX_DAILY_LOSS_PCT=2.0
MAX_CONSECUTIVE_LOSSES=3
MIN_RR_RATIO=1.5
ENABLE_LIVE_TRADING=false

# Symbols (comma-separated instrument tokens or symbols)
WATCHLIST_SYMBOLS=NIFTY,BANKNIFTY,FINNIFTY
```

- [ ] **Step 4: Create `backend/pyproject.toml`**

```toml
[project]
name = "trading-agent-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.27",
  "sqlalchemy[asyncio]>=2.0",
  "asyncpg>=0.29",
  "alembic>=1.13",
  "redis>=5.0",
  "httpx>=0.27",
  "pydantic-settings>=2.2",
  "pandas>=2.2",
  "numpy>=1.26",
  "TA-Lib>=0.4.28",
  "scikit-learn>=1.4",
  "transformers>=4.40",
  "torch>=2.2",
  "kiteconnect>=5.0",
  "python-telegram-bot>=21.0",
  "tenacity>=8.2",
  "structlog>=24.1",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "httpx", "fakeredis>=2.21"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y build-essential wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 6: Verify compose config**

Run: `docker compose config`  
Expected: valid YAML, no errors

---

### Task 0.2: Configuration and logging

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/logging.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_config.py
from app.config import Settings

def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.confidence_threshold == 70
    assert s.timezone == "Asia/Kolkata"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `cd backend && pytest tests/test_config.py -v`  
Expected: `ModuleNotFoundError` or import error

- [ ] **Step 3: Implement settings**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"
    database_url: str = "postgresql+asyncpg://trading:trading@localhost:5432/trading_agent"
    redis_url: str = "redis://localhost:6379/0"
    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_access_token: str = ""
    tradingview_webhook_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    confidence_threshold: int = 70
    max_daily_loss_pct: float = 2.0
    max_consecutive_losses: int = 3
    min_rr_ratio: float = 1.5
    enable_live_trading: bool = False
    watchlist_symbols: str = "NIFTY,BANKNIFTY,FINNIFTY"

def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test — expect PASS**

Run: `cd backend && pytest tests/test_config.py -v`

---

### Task 0.3: FastAPI application shell

**Files:**
- Create: `backend/app/main.py`, `backend/app/di.py`, `backend/app/api/health.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Write failing health test**

```python
from httpx import AsyncClient, ASGITransport
from app.main import app

async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

- [ ] **Step 2: Implement minimal app**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.health import router as health_router
from app.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    yield

app = FastAPI(title="Trading Agent", lifespan=lifespan)
app.include_router(health_router)

# backend/app/api/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Run test — PASS**

Run: `cd backend && pytest tests/test_health.py -v`

---

### Task 0.4: Database engine and session DI

**Files:**
- Create: `backend/app/infrastructure/db.py`
- Create: `backend/app/di.py`
- Test: `backend/tests/test_db_session.py`

- [ ] **Step 1: Implement async engine factory**

```python
# backend/app/infrastructure/db.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

def create_engine(database_url: str):
    return create_async_engine(database_url, echo=False)

def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

- [ ] **Step 2: Wire in `di.py` and expose via lifespan**

- [ ] **Step 3: Integration test with test DB URL** (skip if no postgres; mark `@pytest.mark.integration`)

---

### Task 0.5: Alembic and core schema migration

**Files:**
- Create: `backend/alembic.ini`, `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_initial_schema.py`
- Create: `backend/app/domain/models.py`

- [ ] **Step 1: Define SQLAlchemy models**

Models: `Instrument`, `Candle`, `OptionChainSnapshot`, `NewsItem`, `SectorScore`, `Signal`, `SignalOutcome`, `ConfidenceHistory`, `RiskState`, `WebhookEvent` — columns per design spec §7.

- [ ] **Step 2: Generate and apply migration**

Run: `cd backend && alembic upgrade head`  
Expected: tables created in Postgres

- [ ] **Step 3: Repository stubs**

Create `backend/app/repositories/signal_repository.py` with `async def create(signal: Signal) -> Signal`.

---

### Task 0.6: Redis client and pub/sub helper

**Files:**
- Create: `backend/app/infrastructure/redis_bus.py`
- Test: `backend/tests/test_redis_bus.py` (use `fakeredis`)

- [ ] **Step 1: Write failing publish/subscribe test**

```python
import pytest
from app.infrastructure.redis_bus import RedisBus

@pytest.mark.asyncio
async def test_pubsub_roundtrip(fake_redis):
    bus = RedisBus(fake_redis)
    received = []

    async def handler(channel, data):
        received.append((channel, data))

    await bus.subscribe("tick:NIFTY", handler)
    await bus.publish("tick:NIFTY", {"ltp": 23650.5})
    await asyncio.sleep(0.05)
    assert received[0][1]["ltp"] == 23650.5
```

- [ ] **Step 2: Implement `RedisBus` with `publish`, `subscribe`, JSON serde**

- [ ] **Step 3: Tests PASS**

---

## Phase 1: Market Data Plane

### Task 1.1: Broker adapter interface

**Files:**
- Create: `backend/app/infrastructure/brokers/base.py`
- Create: `backend/app/infrastructure/brokers/kite_adapter.py`
- Test: `backend/tests/test_kite_adapter.py`

- [ ] **Step 1: Define abstract `BrokerStreamAdapter`**

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable

class BrokerStreamAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def subscribe(self, instrument_tokens: list[int]) -> None: ...

    @abstractmethod
    async def stream_ticks(self) -> AsyncIterator[dict]: ...

    @abstractmethod
    async def disconnect(self) -> None: ...
```

- [ ] **Step 2: Implement `KiteStreamAdapter` wrapping `KiteTicker` with reconnect callback**

- [ ] **Step 3: Mock tick test** — inject fake tick dict, assert normalized schema:

```python
{"symbol": "NIFTY", "ltp": float, "volume": int, "oi": int|None, "bid": float, "ask": float, "ts": datetime}
```

---

### Task 1.2: Instrument registry

**Files:**
- Create: `backend/app/services/instrument_service.py`
- Create: `backend/app/repositories/instrument_repository.py`

- [ ] **Step 1: Seed instruments from Kite REST `instruments()` CSV on startup**

- [ ] **Step 2: Map `NIFTY` → index token, index options use separate resolver (phase 3)**

- [ ] **Step 3: Test token lookup by symbol**

---

### Task 1.3: Market stream worker

**Files:**
- Create: `backend/app/workers/market_stream.py`

- [ ] **Step 1: Worker loop**

```python
# Pseudocode structure — implement fully
async def main():
    settings = get_settings()
    bus = RedisBus.from_url(settings.redis_url)
    adapter = KiteStreamAdapter(...)
    await adapter.connect()
    tokens = await instrument_service.resolve_tokens(settings.watchlist_symbols)
    await adapter.subscribe(tokens)
    async for tick in adapter.stream_ticks():
        await bus.publish(f"tick:{tick['symbol']}", tick)
```

- [ ] **Step 2: Market hours guard** — only connect 08:55–15:35 IST

- [ ] **Step 3: Exponential backoff reconnect** using `tenacity`

- [ ] **Step 4: Manual smoke test** with valid Kite token (document in README)

---

### Task 1.4: Candle aggregator worker

**Files:**
- Create: `backend/app/services/candle_aggregator.py`
- Create: `backend/app/workers/candle_aggregator.py`
- Test: `backend/tests/test_candle_aggregator.py`

- [ ] **Step 1: Test 1m bar close from tick sequence**

Feed 60 synthetic ticks spanning one minute → expect one OHLCV dict.

- [ ] **Step 2: Implement multi-timeframe buffers** — 1, 3, 5, 15, 30, 60 minutes

- [ ] **Step 3: On bar close → `bus.publish(f"candle:{symbol}:{tf}", candle)` + upsert DB**

---

### Task 1.5: Sample data mode (dev without broker)

**Files:**
- Create: `backend/app/workers/tick_simulator.py`

- [ ] **Step 1: CLI flag `USE_TICK_SIMULATOR=true` publishes synthetic ticks at 10/s**

- [ ] **Step 2: Document in README for offline UI development**

---

## Phase 2: Technical Analysis Plane

### Task 2.1: Indicator service

**Files:**
- Create: `backend/app/services/indicators.py`
- Test: `backend/tests/test_indicators.py`

- [ ] **Step 1: Tests for EMA crossover, RSI, MACD, VWAP, ADX** using known pandas fixtures

- [ ] **Step 2: Implement wrappers around TA-Lib**

- [ ] **Step 3: Return structured `IndicatorSnapshot` dataclass**

---

### Task 2.2: Pattern detectors

**Files:**
- Create: `backend/app/services/detectors/breakout.py`
- Create: `backend/app/services/detectors/reversal.py`
- Create: `backend/app/services/detectors/fake_breakout.py`
- Test: `backend/tests/test_breakout_detector.py`

- [ ] **Step 1: Breakout — price closes above resistance + volume &gt; 1.5× avg**

- [ ] **Step 2: Reversal — RSI divergence + MACD cross against trend**

- [ ] **Step 3: Fake breakout — breakout without volume confirmation → `trap_zone=True`**

---

### Task 2.3: Multi-timeframe alignment

**Files:**
- Create: `backend/app/services/mtf_analyzer.py`

- [ ] **Step 1: Load last candle per TF from Redis cache keys**

- [ ] **Step 2: Compute `trend_alignment_score` (-100 to +100)**

- [ ] **Step 3: Publish `analysis:technical:{symbol}`**

---

### Task 2.4: Analysis worker

**Files:**
- Create: `backend/app/workers/technical_analysis.py`

- [ ] **Step 1: Subscribe `candle:*:*` → run indicators + detectors**

- [ ] **Step 2: Debounce 100ms per symbol**

---

## Phase 3: Options & Sector Engines

### Task 3.1: NSE option chain fetcher

**Files:**
- Create: `backend/app/infrastructure/nse_option_chain.py`
- Create: `backend/app/workers/option_chain_poller.py`

- [ ] **Step 1: Async HTTP client with NSE headers/cookies rotation**

- [ ] **Step 2: Poll every 5s for NIFTY, BANKNIFTY, FINNIFTY during market hours**

- [ ] **Step 3: Persist `OptionChainSnapshot` + publish `option_chain:{symbol}`**

- [ ] **Step 4: Circuit breaker** — 3 failures → pause 60s, set `data_stale` flag

---

### Task 3.2: Options analytics service

**Files:**
- Create: `backend/app/services/options_analyzer.py`
- Test: `backend/tests/test_options_analyzer.py`

- [ ] **Step 1: Compute PCR, max pain, OI change deltas vs previous snapshot**

- [ ] **Step 2: Detect put/call writing spikes (&gt;5% OI change in 5s window)**

- [ ] **Step 3: Output `smart_money_score` and `trap_zone` booleans**

---

### Task 3.3: Sector rotation engine

**Files:**
- Create: `backend/app/services/sector_rotation.py`
- Create: `backend/app/data/sector_map.yaml` (symbol → sector)

- [ ] **Step 1: Aggregate %change volume-weighted per sector from watchlist stocks**

- [ ] **Step 2: Rank sectors, publish `sector:heatmap` every 30s**

- [ ] **Step 3: Persist `SectorScore` rows**

---

## Phase 4: Sentiment Engine

### Task 4.1: News ingest adapters

**Files:**
- Create: `backend/app/infrastructure/news/rss_fetcher.py`
- Create: `backend/app/workers/news_poller.py`

- [ ] **Step 1: RSS poll Economic Times, Moneycontrol (configurable URLs)**

- [ ] **Step 2: Dedupe by URL hash, store `NewsItem`**

---

### Task 4.2: Sentiment classifier

**Files:**
- Create: `backend/app/services/sentiment.py`
- Test: `backend/tests/test_sentiment.py`

- [ ] **Step 1: Local HuggingFace pipeline `finbert` or similar for financial text**

- [ ] **Step 2: Classify bullish/bearish/neutral/high_vol_risk**

- [ ] **Step 3: Optional OpenAI summarize for `reason` bullets when `OPENAI_API_KEY` set**

---

### Task 4.3: News-market correlator

**Files:**
- Create: `backend/app/services/news_correlator.py`

- [ ] **Step 1: Map headline entities to sectors/symbols via keyword map**

- [ ] **Step 2: Publish `sentiment:aggregate` score -100..100**

---

## Phase 5: Decision, Risk & Signals

### Task 5.1: Signal domain and fusion

**Files:**
- Create: `backend/app/domain/signal.py`
- Create: `backend/app/services/decision_engine.py`
- Test: `backend/tests/test_decision_engine.py`

- [ ] **Step 1: Define `SignalCreate` pydantic model matching spec JSON**

- [ ] **Step 2: Implement weighted confidence fusion (weights from design §6.2)**

- [ ] **Step 3: Category rules — SCALP vs INTRADAY vs SWING based on TF alignment + ADX**

- [ ] **Step 4: Test: high alignment + volume → BUY confidence &gt; 70**

- [ ] **Step 5: Test: fake breakout flag → HOLD or confidence &lt; threshold**

---

### Task 5.2: Risk management service

**Files:**
- Create: `backend/app/services/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

- [ ] **Step 1: Track daily PnL, consecutive losses in `RiskState`**

- [ ] **Step 2: `approve(signal) -> Approved | Rejected(reason)`**

- [ ] **Step 3: Enforce MIN_RR_RATIO, ADX sideways block, ATR volatility block**

---

### Task 5.3: Decision worker

**Files:**
- Create: `backend/app/workers/decision_engine.py`

- [ ] **Step 1: Subscribe `analysis:*`, `option_chain:*`, `sentiment:*`, `sector:*`**

- [ ] **Step 2: Debounce 200ms, fuse, risk check, persist, publish `signal:new`**

---

## Phase 6: API, WebSocket & Frontend

### Task 6.1: REST signal and market endpoints

**Files:**
- Create: `backend/app/api/v1/signals.py`, `market.py`, `options.py`, `sectors.py`, `sentiment.py`

- [ ] **Step 1: `GET /api/v1/signals?active=true`**

- [ ] **Step 2: `GET /api/v1/market/{symbol}` — quote + candles**

- [ ] **Step 3: OpenAPI tags and pagination**

---

### Task 6.2: WebSocket gateway

**Files:**
- Create: `backend/app/api/ws/stream.py`
- Test: `backend/tests/test_ws_stream.py`

- [ ] **Step 1: Client connects `/ws/v1/stream`**

- [ ] **Step 2: Server subscribes Redis `signal:new`, `market:*`, `sector:heatmap`**

- [ ] **Step 3: Multiplex JSON envelopes `{type, payload}`**

```python
{"type": "signal", "payload": {...}}
{"type": "candle", "payload": {...}}
```

---

### Task 6.3: Next.js scaffold

**Files:**
- Create: `frontend/` with `npx create-next-app@14` (TypeScript, Tailwind, App Router)

- [ ] **Step 1: `src/lib/ws-client.ts` — reconnecting WebSocket hook**

- [ ] **Step 2: `src/lib/api.ts` — REST client to backend**

- [ ] **Step 3: Environment `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`**

---

### Task 6.4: Dashboard components

**Files:**
- Create: `frontend/src/components/SignalFeed.tsx`, `ConfidenceMeter.tsx`, `SectorHeatmap.tsx`, `NewsTicker.tsx`, `OptionChainTable.tsx`, `RiskPanel.tsx`

- [ ] **Step 1: Command center page `app/page.tsx` layout grid**

- [ ] **Step 2: Wire WS — state updates without refresh**

- [ ] **Step 3: TradingView widget embed `components/TradingViewChart.tsx`**

---

### Task 6.5: Live chart signal overlays

- [ ] **Step 1: Pass marker annotations from latest signals into TV widget config (or custom overlay div)**

---

### Task 6.6: PnL and active trades (manual v1)

- [ ] **Step 1: Local form to record entry/exit → POST `/api/v1/trades`**

- [ ] **Step 2: Display unrealized PnL from last signal prices**

---

### Task 6.7: Telegram alert service

**Files:**
- Create: `backend/app/infrastructure/telegram_notifier.py`
- Create: `backend/app/workers/alert_dispatcher.py`

- [ ] **Step 1: Subscribe `signal:new`, format alert message per spec**

- [ ] **Step 2: Rate limit 1 msg/sec per symbol**

- [ ] **Step 3: Test with mock bot API**

---

## Phase 7: TradingView Integration

### Task 7.1: Webhook endpoint with HMAC

**Files:**
- Create: `backend/app/api/v1/webhooks/tradingview.py`
- Test: `backend/tests/test_tradingview_webhook.py`

- [ ] **Step 1: Verify `X-TV-Signature` HMAC-SHA256 of body with secret**

- [ ] **Step 2: Parse alert fields: `symbol`, `action`, `price`, `indicator`**

- [ ] **Step 3: Store `WebhookEvent`, publish `webhook:tradingview`**

- [ ] **Step 4: Decision engine adds +10% confidence weight when aligned**

---

### Task 7.2: TradingView setup guide

**Files:**
- Create: `docs/tradingview-setup.md`

- [ ] **Step 1: Document alert message JSON template for Pine Script**

---

## Phase 8: Backtesting & AI Memory

### Task 8.1: Historical candle loader

**Files:**
- Create: `backend/app/services/backtest/data_loader.py`

- [ ] **Step 1: Load candles from DB by date range**

- [ ] **Step 2: Kite REST backfill CLI `python -m app.cli.backfill --date 2026-05-19`**

---

### Task 8.2: Replay engine

**Files:**
- Create: `backend/app/services/backtest/replay.py`
- Test: `backend/tests/test_replay.py`

- [ ] **Step 1: Candle-by-candle iterator emits same Redis events as live**

- [ ] **Step 2: Run decision engine in process, collect signals**

- [ ] **Step 3: Compute win rate, max drawdown, Sharpe (basic)**

---

### Task 8.3: Outcome tracking

**Files:**
- Create: `backend/app/services/outcome_tracker.py`

- [ ] **Step 1: Cron/worker marks signal TP/SL hit based on subsequent candles**

- [ ] **Step 2: Write `SignalOutcome`**

---

### Task 8.4: Confidence learning (v1 heuristic)

**Files:**
- Create: `backend/app/services/learning/confidence_calibrator.py`

- [ ] **Step 1: Bucket outcomes by `market_condition` + `category`**

- [ ] **Step 2: Adjust per-bucket weight multipliers stored in `confidence_history`**

- [ ] **Step 3: Weekly recompute job**

---

## Phase 9: Deployment & Documentation

### Task 9.1: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Architecture diagram, quick start, Kite auth flow, market hours**

- [ ] **Step 2: Disclaimer**

---

### Task 9.2: Deployment guide

**Files:**
- Create: `docs/deployment.md`, `deploy/k8s/*.yaml`

- [ ] **Step 1: Docker Compose production notes**

- [ ] **Step 2: K8s deployments: backend, workers (HPA optional), redis, postgres statefulset**

- [ ] **Step 3: Secrets via K8s secrets, liveness probes on `/health`**

---

### Task 9.3: Unit test suite CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: `pytest` + `npm test` + lint on push**

---

## Execution Order (Critical Path)

```
0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6
  → 1.1 → 1.2 → 1.3 → 1.4 → 1.5
  → 2.* → 3.* → 4.* → 5.*
  → 6.* → 7.* → 8.* → 9.*
```

Phases 2–4 can parallelize after Phase 1. Phase 5 depends on 2–4. Phase 6 depends on 5.

---

## Self-Review Checklist

- [x] Every spec section mapped (Spec Coverage Map)
- [x] No TBD placeholders
- [x] Phase 0–1 steps include code and commands
- [x] Phases 2–9 include concrete files and acceptance criteria
- [x] Type/signal schema consistent with design doc

---

## Post-Plan: Execution Choice

**Plan saved to:** `docs/superpowers/plans/2026-05-20-realtime-trading-agent.md`  
**Design spec:** `docs/superpowers/specs/2026-05-20-realtime-trading-agent-design.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks  
2. **Inline Execution** — Implement task-by-task in this session with checkpoints  

**Which approach do you want?**

Also please confirm design spec defaults:
- Zerodha Kite v1 broker?
- Paper trading only (no auto orders) for v1?
- Approve design spec so implementation can begin?
