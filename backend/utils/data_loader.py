
def load_realtime_data():
    # This would normally hit an API, for now we simulate
    return {
        "AAPL": {"price": 160, "ma50": 150, "lower_band": 145},
        "TSLA": {"price": 190, "ma50": 200, "lower_band": 185}
    }
