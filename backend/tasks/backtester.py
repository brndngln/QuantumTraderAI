import random
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from fastapi import HTTPException

class Backtester:
    def __init__(self):
        self.results = []

    def run_backtest(self, strategy_fn, tickers: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Run backtest for given strategy
        """
        try:
            for ticker in tickers:
                # Simulate data fetching
                values = pd.DataFrame({
                    'date': pd.date_range(start=start_date, end=end_date),
                    'close': [random.uniform(100, 200) for _ in range(20)]
                })
                
                signal = strategy_fn({ticker: values})
                if signal:
                    result = {
                        "ticker": ticker,
                        "strategy": strategy_fn.__name__,
                        "pnl": random.uniform(-5, 10),
                        "date": datetime.now().isoformat()
                    }
                    self.results.append(result)
            
            # Save results
            results_path = Path("data/backtest_results.json")
            results_path.parent.mkdir(exist_ok=True)
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            return self.results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error running backtest: {str(e)}"
            )
