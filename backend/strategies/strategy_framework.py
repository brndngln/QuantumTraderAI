import pandas as pd
from typing import Dict
from fastapi import HTTPException
import matplotlib.pyplot as plt

class StrategyFramework:
    def __init__(self):
        self.strategies = {}
        self.data = None

    def register_strategy(self, name: str, strategy_fn):
        """
        Register a trading strategy
        """
        self.strategies[name] = strategy_fn

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Generate signals for all registered strategies
        """
        self.data = data
        signals = {}
        for name, strategy in self.strategies.items():
            try:
                signals[name] = strategy(data)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in strategy {name}: {str(e)}"
                )
        return signals

    def generate_combined_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate combined signals from all strategies
        """
        signals = self.generate_signals(data)
        combined = pd.Series(0, index=data.index)
        
        for name, signal in signals.items():
            combined += signal
        
        return combined

    def plot_signals(self, data: pd.DataFrame):
        """
        Plot signals from all strategies
        """
        signals = self.generate_signals(data)
        combined = self.generate_combined_signals(data)
        
        fig, axes = plt.subplots(2, 2, figsize=(20, 10))
        
        # Plot individual signals
        for name, signal in signals.items():
            axes[0, 0].plot(signal, label=name)
        axes[0, 0].set_title('Individual Strategy Signals')
        axes[0, 0].legend()
        
        # Plot combined signals
        axes[1, 0].plot(combined, label='Combined')
        axes[1, 0].set_title('Combined Strategy Signals')
        axes[1, 0].legend()
        
        # Plot returns
        returns = pd.Series(0, index=data.index)
        for name, signal in signals.items():
            returns += signal * data['Close'].pct_change()
        
        axes[0, 1].plot(returns.cumsum(), label='Total')
        axes[0, 1].set_title('Strategy Returns')
        axes[0, 1].legend()
        
        # Plot combined returns
        combined_returns = combined * data['Close'].pct_change()
        axes[1, 1].plot(combined_returns.cumsum())
        axes[1, 1].set_title('Combined Strategy Returns')
        
        plt.tight_layout()
        plt.show()
