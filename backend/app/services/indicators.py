from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class IndicatorSnapshot:
    ema_fast: float
    ema_slow: float
    ema_bullish: bool
    rsi: float
    macd: float
    macd_signal: float
    macd_bullish: bool
    vwap: float
    adx: float
    price: float
    volume_ratio: float

    def to_dict(self) -> dict:
        return {
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "ema_bullish": self.ema_bullish,
            "rsi": self.rsi,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_bullish": self.macd_bullish,
            "vwap": self.vwap,
            "adx": self.adx,
            "price": self.price,
            "volume_ratio": self.volume_ratio,
        }


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = 100 - (100 / (1 + rs))
    return float(val.iloc[-1]) if not val.empty and not np.isnan(val.iloc[-1]) else 50.0


def _macd(series: pd.Series) -> tuple[float, float]:
    ema12 = _ema(series, 12)
    ema26 = _ema(series, 26)
    macd_line = ema12 - ema26
    signal = _ema(macd_line, 9)
    return float(macd_line.iloc[-1]), float(signal.iloc[-1])


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx = dx.rolling(period).mean()
    return float(adx.iloc[-1]) if not adx.empty and not np.isnan(adx.iloc[-1]) else 0.0


def compute_indicators(candles: list[dict]) -> IndicatorSnapshot | None:
    if len(candles) < 30:
        return None
    df = pd.DataFrame(candles)
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    ema_fast = float(_ema(close, 9).iloc[-1])
    ema_slow = float(_ema(close, 21).iloc[-1])
    macd, macd_sig = _macd(close)
    typical = (high + low + close) / 3
    vwap = float((typical * volume).sum() / max(volume.sum(), 1))
    vol_avg = float(volume.rolling(20).mean().iloc[-1] or 1)
    vol_ratio = float(volume.iloc[-1] / max(vol_avg, 1))

    return IndicatorSnapshot(
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        ema_bullish=ema_fast > ema_slow,
        rsi=_rsi(close),
        macd=macd,
        macd_signal=macd_sig,
        macd_bullish=macd > macd_sig,
        vwap=vwap,
        adx=_adx(high, low, close),
        price=float(close.iloc[-1]),
        volume_ratio=vol_ratio,
    )
