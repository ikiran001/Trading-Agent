import re

BULLISH_WORDS = {"surge", "rally", "gain", "bullish", "record high", "upgrade", "beat"}
BEARISH_WORDS = {"fall", "crash", "drop", "bearish", "downgrade", "miss", "selloff", "volatility"}
HIGH_VOL_WORDS = {"rbi", "fed", "inflation", "war", "crisis", "default", "halt"}


class SentimentClassifier:
    def classify(self, text: str) -> str:
        lower = text.lower()
        bull = sum(1 for w in BULLISH_WORDS if w in lower)
        bear = sum(1 for w in BEARISH_WORDS if w in lower)
        if any(w in lower for w in HIGH_VOL_WORDS):
            return "high_vol_risk"
        if bull > bear:
            return "bullish"
        if bear > bull:
            return "bearish"
        return "neutral"

    def score(self, sentiments: list[str]) -> float:
        if not sentiments:
            return 50.0
        mapping = {"bullish": 75, "bearish": 25, "neutral": 50, "high_vol_risk": 40}
        return sum(mapping.get(s, 50) for s in sentiments) / len(sentiments)
