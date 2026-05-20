from dataclasses import dataclass


@dataclass
class OptionsAnalysis:
    pcr: float
    max_pain: float
    smart_money_score: float
    trap_zone: bool
    put_writing_spike: bool
    call_writing_spike: bool

    def score(self) -> float:
        base = 50.0
        if self.pcr > 1.2:
            base += 15
        elif self.pcr < 0.8:
            base -= 10
        if self.smart_money_score > 60:
            base += 10
        if self.trap_zone:
            base -= 25
        return max(0, min(100, base))


def compute_pcr(chain: dict) -> float:
    records = chain.get("records", chain.get("data", []))
    if not records:
        return 1.0
    call_oi = sum(r.get("CE", {}).get("openInterest", 0) or 0 for r in records)
    put_oi = sum(r.get("PE", {}).get("openInterest", 0) or 0 for r in records)
    return put_oi / max(call_oi, 1)


def compute_max_pain(chain: dict) -> float:
    records = chain.get("records", chain.get("data", []))
    if not records:
        return 0.0
    strikes = []
    for r in records:
        strike = r.get("strikePrice") or r.get("strike")
        if strike:
            ce_oi = r.get("CE", {}).get("openInterest", 0) or 0
            pe_oi = r.get("PE", {}).get("openInterest", 0) or 0
            strikes.append((float(strike), ce_oi + pe_oi))
    if not strikes:
        return 0.0
    return max(strikes, key=lambda x: x[1])[0]


def analyze_options(current: dict, previous: dict | None = None) -> OptionsAnalysis:
    pcr = compute_pcr(current)
    max_pain = compute_max_pain(current)
    put_spike = call_spike = trap = False
    smart = 50.0

    if previous:
        prev_pcr = compute_pcr(previous)
        if pcr - prev_pcr > 0.15:
            put_spike = True
            smart += 15
        if prev_pcr - pcr > 0.15:
            call_spike = True
        if abs(pcr - prev_pcr) > 0.25:
            trap = True

    return OptionsAnalysis(
        pcr=pcr,
        max_pain=max_pain,
        smart_money_score=smart,
        trap_zone=trap,
        put_writing_spike=put_spike,
        call_writing_spike=call_spike,
    )
