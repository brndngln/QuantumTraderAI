
import json
import numpy as np

class MetaLearner:
    def __init__(self, history_file='data/trade_history.json'):
        self.history_file = history_file
        self.strategy_scores = {}

    def load_history(self):
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def evaluate_strategies(self, history):
        scores = {}
        for trade in history:
            strategy = trade.get("strategy")
            pnl = trade.get("pnl", 0)
            if strategy not in scores:
                scores[strategy] = []
            scores[strategy].append(pnl)
        return {s: np.mean(pnls) for s, pnls in scores.items() if pnls}

    def recommend_strategies(self):
        history = self.load_history()
        self.strategy_scores = self.evaluate_strategies(history)
        return sorted(self.strategy_scores.items(), key=lambda x: -x[1])

    def confidence_weight(self, strategy):
        return max(0, self.strategy_scores.get(strategy, 0) / 100)

meta = MetaLearner()
