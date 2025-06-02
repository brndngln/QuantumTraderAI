from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from scipy.stats import norm
from datetime import datetime
import json

class RiskMetrics(BaseModel):
    volatility: float
    sharpe_ratio: float
    value_at_risk: float
    conditional_var: float
    max_drawdown: float
    exposure: float
    correlation_matrix: Dict

class DynamicRiskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_risk_metrics = RiskMetrics(
            volatility=0.0,
            sharpe_ratio=0.0,
            value_at_risk=0.0,
            conditional_var=0.0,
            max_drawdown=0.0,
            exposure=0.0,
            correlation_matrix={}
        )
        self.risk_tolerance = 0.05  # Default risk tolerance
        self.volatility_buffer = 0.1  # Buffer for volatility adjustments
        
    def calculate_value_at_risk(self, returns: List[float], confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk using historical method
        """
        returns = np.array(returns)
        return -np.percentile(returns, 100 * (1 - confidence))
    
    def calculate_conditional_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall)
        """
        returns = np.array(returns)
        var = self.calculate_value_at_risk(returns, confidence)
        return -np.mean(returns[returns <= -var])
    
    def calculate_max_drawdown(self, prices: List[float]) -> float:
        """
        Calculate maximum drawdown
        """
        prices = np.array(prices)
        max_drawdown = 0
        peak = prices[0]
        
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        """
        returns = np.array(returns)
        excess_returns = returns - risk_free_rate
        return np.mean(excess_returns) / np.std(excess_returns)
    
    def calculate_position_size(self, volatility: float, exposure_limit: float = 0.1) -> float:
        """
        Calculate optimal position size based on volatility and risk tolerance
        """
        return exposure_limit / (volatility + self.volatility_buffer)
    
    def update_risk_metrics(self, returns: List[float], prices: List[float]) -> RiskMetrics:
        """
        Update risk metrics based on new data
        """
        try:
            self.current_risk_metrics.volatility = np.std(returns)
            self.current_risk_metrics.sharpe_ratio = self.calculate_sharpe_ratio(returns)
            self.current_risk_metrics.value_at_risk = self.calculate_value_at_risk(returns)
            self.current_risk_metrics.conditional_var = self.calculate_conditional_var(returns)
            self.current_risk_metrics.max_drawdown = self.calculate_max_drawdown(prices)
            self.current_risk_metrics.exposure = self.calculate_position_size(self.current_risk_metrics.volatility)
            
            # Update correlation matrix
            if len(returns) > 1:
                returns_df = pd.DataFrame(returns)
                self.current_risk_metrics.correlation_matrix = returns_df.corr().to_dict()
            
            return self.current_risk_metrics
            
        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {str(e)}")
            return self.current_risk_metrics
    
    def adjust_risk_tolerance(self, market_volatility: float) -> None:
        """
        Adjust risk tolerance based on market conditions
        """
        # Increase risk tolerance in low volatility environments
        if market_volatility < 0.1:
            self.risk_tolerance = min(0.1, self.risk_tolerance + 0.01)
        # Decrease risk tolerance in high volatility environments
        elif market_volatility > 0.3:
            self.risk_tolerance = max(0.01, self.risk_tolerance - 0.01)
    
    def get_risk_exposure(self) -> float:
        """
        Get current risk exposure
        """
        return self.current_risk_metrics.exposure
