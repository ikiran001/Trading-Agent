from app.services.sentiment import SentimentClassifier


def test_bullish_headline():
    c = SentimentClassifier()
    assert c.classify("Markets rally on strong GDP surge") == "bullish"


def test_bearish_headline():
    c = SentimentClassifier()
    assert c.classify("Stocks crash amid selloff fears") == "bearish"
