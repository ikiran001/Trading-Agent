from datetime import datetime, time

import pytz

IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PREMARKET_CONNECT = time(8, 55)


def now_ist() -> datetime:
    return datetime.now(IST)


def is_market_hours(include_premarket: bool = True) -> bool:
    now = now_ist()
    if now.weekday() >= 5:
        return False
    t = now.time()
    start = PREMARKET_CONNECT if include_premarket else MARKET_OPEN
    return start <= t <= MARKET_CLOSE
