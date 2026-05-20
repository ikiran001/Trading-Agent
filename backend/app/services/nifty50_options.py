"""NIFTY 50 (NSE:NIFTY) index options helpers."""

from app.domain.signal import SignalAction


def _records(chain_payload: dict) -> list[dict]:
    chain = chain_payload.get("chain") or chain_payload
    data = chain.get("data") or chain
    if isinstance(data, list):
        return data
    return data.get("records") or []


def atm_strike(chain_payload: dict, spot: float) -> int | None:
    records = _records(chain_payload)
    strikes: list[float] = []
    for row in records:
        s = row.get("strikePrice") or row.get("strike")
        if s is not None:
            strikes.append(float(s))
    if not strikes:
        return None
    return int(min(strikes, key=lambda x: abs(x - spot)))


def suggest_instrument(
    chain_payload: dict | None,
    spot: float,
    action: SignalAction,
) -> str | None:
    """
    NIFTY 50 options convention:
    - Bullish (BUY) -> ATM or near-ATM Call (CE)
    - Bearish (SELL) -> ATM or near-ATM Put (PE)
    """
    if not chain_payload or spot <= 0:
        return None
    strike = atm_strike(chain_payload, spot)
    if strike is None:
        return None
    if action == SignalAction.BUY:
        return f"{strike} CE"
    if action == SignalAction.SELL:
        return f"{strike} PE"
    return None
