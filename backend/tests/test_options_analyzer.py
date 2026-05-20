from app.services.options_analyzer import analyze_options, compute_pcr


def test_pcr_calculation():
    chain = {
        "records": [
            {"strikePrice": 22000, "CE": {"openInterest": 1000}, "PE": {"openInterest": 1500}},
            {"strikePrice": 22100, "CE": {"openInterest": 2000}, "PE": {"openInterest": 1000}},
        ]
    }
    pcr = compute_pcr(chain)
    assert pcr == 2500 / 3000


def test_trap_on_pcr_shift():
    current = {"records": [{"strikePrice": 22000, "CE": {"openInterest": 100}, "PE": {"openInterest": 500}}]}
    previous = {"records": [{"strikePrice": 22000, "CE": {"openInterest": 100}, "PE": {"openInterest": 100}}]}
    a = analyze_options(current, previous)
    assert a.put_writing_spike or a.trap_zone or a.smart_money_score >= 50
