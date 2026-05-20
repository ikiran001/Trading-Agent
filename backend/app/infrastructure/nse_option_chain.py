import httpx

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

SYMBOL_MAP = {
    "NIFTY": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "FINNIFTY": "FINNIFTY",
}


class NSEOptionChainClient:
    BASE = "https://www.nseindia.com/api/option-chain-indices"

    def __init__(self):
        self._failures = 0
        self._paused_until = 0.0

    async def fetch(self, symbol: str) -> dict:
        import time

        if time.time() < self._paused_until:
            raise RuntimeError("NSE client circuit open")

        nse_symbol = SYMBOL_MAP.get(symbol, symbol)
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            await client.get("https://www.nseindia.com", headers=NSE_HEADERS)
            resp = await client.get(
                self.BASE,
                params={"symbol": nse_symbol},
                headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/option-chain"},
            )
            resp.raise_for_status()
            self._failures = 0
            return resp.json()

    def record_failure(self) -> None:
        import time

        self._failures += 1
        if self._failures >= 3:
            self._paused_until = time.time() + 60
            self._failures = 0
