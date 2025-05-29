
def momentum_strategy(data):
    signals = []
    for ticker in data:
        if data[ticker]["price"] > data[ticker]["ma50"]:
            signals.append({"ticker": ticker, "action": "buy", "reason": "momentum breakout"})
    return signals
