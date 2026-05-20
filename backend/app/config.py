from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"
    use_tick_simulator: bool = False

    database_url: str = "postgresql+asyncpg://trading:trading@localhost:5432/trading_agent"
    redis_url: str = "redis://localhost:6379/0"

    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_access_token: str = ""

    tradingview_webhook_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    openai_api_key: str = ""

    confidence_threshold: int = 70
    max_daily_loss_pct: float = 2.0
    max_consecutive_losses: int = 3
    min_rr_ratio: float = 1.5
    enable_live_trading: bool = False

    watchlist_symbols: str = "NIFTY,BANKNIFTY,FINNIFTY"
    news_rss_urls: str = ""

    @property
    def watchlist(self) -> list[str]:
        return [s.strip() for s in self.watchlist_symbols.split(",") if s.strip()]

    @property
    def news_urls(self) -> list[str]:
        return [u.strip() for u in self.news_rss_urls.split(",") if u.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
