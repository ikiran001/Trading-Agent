from app.services.detectors.breakout import detect_breakout


def test_breakout_up_with_volume():
    candles = []
    for i in range(22):
        candles.append({"high": 100, "low": 99, "close": 99.5, "volume": 100})
    candles.append({"high": 102, "low": 101, "close": 101.5, "volume": 500})
    result = detect_breakout(candles)
    assert result.detected
    assert result.direction == "up"
    assert result.volume_confirmed
