from app.domain.signal import SignalAction, SignalCategory, SignalCreate
from app.services.detectors.breakout import detect_breakout
from app.services.detectors.fake_breakout import detect_fake_breakout
from app.services.detectors.reversal import detect_reversal
from app.services.mtf_analyzer import MTFAnalysis


class DecisionEngine:
    WEIGHTS = {
        "mtf": 0.25,
        "volume": 0.15,
        "options": 0.20,
        "sector": 0.15,
        "sentiment": 0.15,
        "tradingview": 0.10,
    }

    def fuse(
        self,
        symbol: str,
        indicators: dict | None,
        mtf: MTFAnalysis | None,
        options_score: float = 50.0,
        sector_score: float = 50.0,
        sentiment_score: float = 50.0,
        tv_confirm: bool = False,
        candles_1m: list[dict] | None = None,
        data_stale: bool = False,
    ) -> SignalCreate | None:
        if data_stale:
            return None

        reasons: list[str] = []
        sub_scores: dict[str, float] = {}

        mtf_score = 50.0 + (mtf.trend_alignment_score / 2 if mtf else 0)
        sub_scores["mtf"] = max(0, min(100, mtf_score))
        if mtf and mtf.trend_alignment_score > 30:
            reasons.append("Multi-timeframe bullish alignment")
        elif mtf and mtf.trend_alignment_score < -30:
            reasons.append("Multi-timeframe bearish alignment")

        vol_score = 50.0
        if indicators:
            vol_score = min(100, 50 + (indicators.get("volume_ratio", 1) - 1) * 40)
            if indicators.get("ema_bullish"):
                reasons.append("EMA bullish crossover")
            if indicators.get("price", 0) > indicators.get("vwap", 0):
                reasons.append("Price above VWAP")
        sub_scores["volume"] = vol_score

        sub_scores["options"] = options_score
        sub_scores["sector"] = sector_score
        sub_scores["sentiment"] = sentiment_score
        sub_scores["tradingview"] = 80.0 if tv_confirm else 50.0

        confidence = int(sum(sub_scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS))

        trap = detect_fake_breakout(candles_1m or [])
        if trap.trap_zone:
            confidence -= 20
            reasons.append(trap.reason or "Fake breakout trap zone")

        action = SignalAction.HOLD
        market_condition = "NEUTRAL"

        if candles_1m:
            breakout = detect_breakout(candles_1m)
            reversal = detect_reversal(candles_1m)
            if breakout.detected and breakout.direction == "up" and breakout.volume_confirmed:
                action = SignalAction.BUY
                market_condition = "BULLISH"
                reasons.append("Volume breakout above resistance")
            elif breakout.detected and breakout.direction == "down" and breakout.volume_confirmed:
                action = SignalAction.SELL
                market_condition = "BEARISH"
                reasons.append("Breakdown below support")
            elif reversal.detected and reversal.direction == "bullish":
                action = SignalAction.BUY
                reasons.append("Bullish reversal pattern")
            elif reversal.detected and reversal.direction == "bearish":
                action = SignalAction.SELL
                reasons.append("Bearish reversal pattern")

        if confidence < 50:
            action = SignalAction.HOLD

        category = SignalCategory.INTRADAY
        adx = indicators.get("adx", 25) if indicators else 25
        if abs(mtf.trend_alignment_score if mtf else 0) > 60 and adx > 25:
            category = SignalCategory.SCALP if adx > 30 else SignalCategory.INTRADAY
        elif adx > 25:
            category = SignalCategory.SWING

        price = indicators.get("price", 0) if indicators else 0
        entry = price if price else None
        sl = round(price * 0.995, 2) if price and action == SignalAction.BUY else round(price * 1.005, 2) if price else None
        t1 = round(price * 1.008, 2) if price and action == SignalAction.BUY else round(price * 0.992, 2) if price else None
        t2 = round(price * 1.015, 2) if price and action == SignalAction.BUY else round(price * 0.985, 2) if price else None

        if sector_score > 65:
            reasons.append("Leading sector strength")
        if options_score > 65:
            reasons.append("Options flow supports direction")
        if sentiment_score > 60:
            reasons.append("Positive market sentiment")

        return SignalCreate(
            signal=action,
            category=category,
            symbol=symbol,
            entry=entry,
            stop_loss=sl,
            target_1=t1,
            target_2=t2,
            confidence=max(0, min(100, confidence)),
            market_condition=market_condition,
            holding_time="15-30 mins" if category == SignalCategory.INTRADAY else "1-5 mins",
            reasons=reasons[:8],
            data_stale=data_stale,
        )
