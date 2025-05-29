
def mean_reversion_strategy(data):
    signals = []
    for ticker in data:
        if data[ticker]["price"] < data[ticker]["lower_band"]:
            signals.append({"ticker": ticker, "action": "buy", "reason": "mean reversion opportunity"})
    return signals
