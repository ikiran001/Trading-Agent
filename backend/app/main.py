from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1 import market, options, sectors, sentiment, signals, webhooks
from app.api.ws.stream import router as ws_router
from app.config import get_settings
from app.di import bootstrap
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = bootstrap(get_settings())
    setup_logging(settings.log_level)
    app.state.settings = settings
    yield


app = FastAPI(title="Trading Agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(signals.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(options.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(ws_router)
