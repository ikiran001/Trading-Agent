from app.domain.signal import SignalAction
from app.services.nifty50_options import atm_strike, suggest_instrument


def test_atm_strike():
    chain = {
        "records": [
            {"strikePrice": 24000, "CE": {}, "PE": {}},
            {"strikePrice": 24100, "CE": {}, "PE": {}},
            {"strikePrice": 24200, "CE": {}, "PE": {}},
        ]
    }
    assert atm_strike(chain, 24180) == 24200


def test_suggest_ce_on_buy():
    chain = {"records": [{"strikePrice": 24000, "CE": {}, "PE": {}}]}
    assert suggest_instrument(chain, 24010, SignalAction.BUY) == "24000 CE"


def test_suggest_pe_on_sell():
    chain = {"records": [{"strikePrice": 24000, "CE": {}, "PE": {}}]}
    assert suggest_instrument(chain, 24010, SignalAction.SELL) == "24000 PE"
