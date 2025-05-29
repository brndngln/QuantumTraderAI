
import json
import os

def run_backtest(data, strategy_fn, strategy_name, output_path='data/backtest_results.json'):
    results = []
    for ticker, values in data.items():
        signal = strategy_fn({ticker: values})
        if signal:
            result = {"ticker": ticker, "strategy": strategy_name, "pnl": random.uniform(-5, 10)}
            results.append(result)
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    return results
