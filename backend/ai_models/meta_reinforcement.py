
import random
from collections import defaultdict

class MetaReinforcementLearner:
    def __init__(self):
        self.rewards = defaultdict(list)
        self.q_scores = defaultdict(float)

    def record_trade_result(self, strategy, reward):
        self.rewards[strategy].append(reward)
        self.q_scores[strategy] = sum(self.rewards[strategy]) / len(self.rewards[strategy])

    def choose_strategy(self):
        if not self.q_scores:
            return random.choice(["momentum", "mean_reversion", "lstm", "transformer"])
        return max(self.q_scores.items(), key=lambda x: x[1])[0]
