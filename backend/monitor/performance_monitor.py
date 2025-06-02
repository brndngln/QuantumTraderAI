from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from datetime import datetime
import json

class PerformanceMetrics(BaseModel):
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = PerformanceMetrics(
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=0.0
        )
        self.rolling_window = 252  # Default rolling window (1 year of trading days)
        self.trade_history = []
        
    def calculate_annualized_return(self, returns: List[float], period: int = 252) -> float:
        """
        Calculate annualized return
        """
        returns = np.array(returns)
        total_return = np.prod(1 + returns) - 1
        return (1 + total_return) ** (period / len(returns)) - 1
    
    def calculate_sortino_ratio(self, returns: List[float], target_return: float = 0.0) -> float:
        """
        Calculate Sortino Ratio
        """
        returns = np.array(returns)
        downside_returns = returns[returns < target_return]
        downside_std = np.std(downside_returns)
        excess_returns = returns - target_return
        return np.mean(excess_returns) / downside_std if downside_std != 0 else 0
    
    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """
        Calculate win rate
        """
        wins = sum(1 for trade in trades if trade['profit'] > 0)
        return wins / len(trades) if len(trades) > 0 else 0
    
    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """
        Calculate profit factor
        """
        total_profit = sum(trade['profit'] for trade in trades if trade['profit'] > 0)
        total_loss = abs(sum(trade['profit'] for trade in trades if trade['profit'] < 0))
        return total_profit / total_loss if total_loss != 0 else 0
    
    def update_metrics(self, trades: List[Dict]) -> PerformanceMetrics:
        """
        Update performance metrics based on trade history
        """
        try:
            returns = [trade['profit'] / trade['entry_price'] for trade in trades]
            
            self.metrics.total_return = np.prod(1 + np.array(returns)) - 1
            self.metrics.annualized_return = self.calculate_annualized_return(returns)
            self.metrics.sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
            self.metrics.sortino_ratio = self.calculate_sortino_ratio(returns)
            self.metrics.max_drawdown = self._calculate_max_drawdown(trades)
            self.metrics.win_rate = self.calculate_win_rate(trades)
            self.metrics.average_win = np.mean([trade['profit'] for trade in trades if trade['profit'] > 0])
            self.metrics.average_loss = np.mean([trade['profit'] for trade in trades if trade['profit'] < 0])
            self.metrics.profit_factor = self.calculate_profit_factor(trades)
            
            return self.metrics
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")
            return self.metrics
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """
        Calculate maximum drawdown from trade history
        """
        equity = []
        current_equity = 0
        
        for trade in trades:
            current_equity += trade['profit']
            equity.append(current_equity)
            
        if not equity:
            return 0
            
        max_drawdown = 0
        peak = equity[0]
        
        for value in equity:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown
    
    def get_rolling_metrics(self, trades: List[Dict], window: int = 252) -> Dict:
        """
        Calculate rolling performance metrics
        """
        metrics = []
        
        for i in range(len(trades) - window + 1):
            window_trades = trades[i:i + window]
            metrics.append(self.update_metrics(window_trades).dict())
            
        return {
            'dates': [trade['entry_time'] for trade in trades[:window]],
            'metrics': metrics
        }
