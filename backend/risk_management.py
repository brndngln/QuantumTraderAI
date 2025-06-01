import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self,
                 max_position_size: float = 0.05,
                 max_drawdown: float = 0.02,
                 stop_loss_pct: float = 0.02,
                 take_profit_pct: float = 0.03,
                 risk_per_trade: float = 0.01,
                 volatility_adjustment: bool = True,
                 correlation_threshold: float = 0.8,
                 max_leverage: float = 2.0):
        """
        Initialize risk management system
        
        Args:
            max_position_size: Maximum position size as % of portfolio
            max_drawdown: Maximum allowed drawdown
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            risk_per_trade: Risk per trade as % of portfolio
            volatility_adjustment: Whether to adjust position size based on volatility
            correlation_threshold: Maximum allowed correlation between positions
            max_leverage: Maximum leverage allowed
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.risk_per_trade = risk_per_trade
        self.volatility_adjustment = volatility_adjustment
        self.correlation_threshold = correlation_threshold
        self.max_leverage = max_leverage
        
        self.current_drawdown = 0.0
        self.max_drawdown_reached = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.current_positions = {}
        self.correlation_matrix = None
        
    def calculate_position_size(self, 
                               current_price: float, 
                               portfolio_value: float, 
                               volatility: float,
                               leverage: float = 1.0) -> float:
        """Calculate optimal position size"""
        try:
            # Base position size based on risk per trade
            base_size = (portfolio_value * self.risk_per_trade) / (current_price * self.stop_loss_pct)
            
            # Apply volatility adjustment
            if self.volatility_adjustment:
                base_size *= (1 / (volatility + 1e-6))
            
            # Apply leverage
            base_size *= min(leverage, self.max_leverage)
            
            # Apply maximum position size limit
            max_size = portfolio_value * self.max_position_size
            position_size = min(base_size, max_size)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def calculate_stop_loss(self, 
                           entry_price: float, 
                           volatility: float,
                           position_size: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        try:
            # Calculate stop loss
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            
            # Calculate take profit
            take_profit = entry_price * (1 + self.take_profit_pct)
            
            # Adjust based on volatility
            adjustment = volatility * position_size
            stop_loss -= adjustment
            take_profit += adjustment
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {str(e)}")
            return 0.0, 0.0

    def calculate_risk_reward_ratio(self, 
                                  stop_loss: float, 
                                  take_profit: float, 
                                  entry_price: float) -> float:
        """Calculate risk/reward ratio"""
        try:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            return reward / risk
            
        except Exception as e:
            logger.error(f"Error calculating risk/reward ratio: {str(e)}")
            return 0.0

    def update_metrics(self, 
                      trade_pnl: float, 
                      portfolio_value: float) -> None:
        """Update risk metrics"""
        try:
            self.total_trades += 1
            self.total_profit += trade_pnl
            
            if trade_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
                
            # Calculate current drawdown
            peak_value = max(portfolio_value, self.max_drawdown_reached)
            self.current_drawdown = (peak_value - portfolio_value) / peak_value
            self.max_drawdown_reached = max(peak_value, self.max_drawdown_reached)
            
        except Exception as e:
            logger.error(f"Error updating risk metrics: {str(e)}")

    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics"""
        try:
            win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
            avg_profit = self.total_profit / self.total_trades if self.total_trades > 0 else 0
            
            return {
                'current_drawdown': self.current_drawdown,
                'max_drawdown': self.max_drawdown_reached,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'total_profit': self.total_profit,
                'correlation_threshold': self.correlation_threshold,
                'max_leverage': self.max_leverage
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {str(e)}")
            return {}

    def check_position_correlation(self, new_position: str) -> bool:
        """Check correlation with existing positions"""
        try:
            if not self.correlation_matrix or not self.current_positions:
                return True
                
            # Get correlations with existing positions
            correlations = self.correlation_matrix.loc[new_position, list(self.current_positions.keys())]
            
            # Check if any correlation exceeds threshold
            return not (correlations > self.correlation_threshold).any()
            
        except Exception as e:
            logger.error(f"Error checking position correlation: {str(e)}")
            return True

    def update_correlation_matrix(self, price_data: pd.DataFrame) -> None:
        """Update correlation matrix"""
        try:
            self.correlation_matrix = price_data.pct_change().corr()
            logger.info("Correlation matrix updated")
            
        except Exception as e:
            logger.error(f"Error updating correlation matrix: {str(e)}")

    def get_position_limits(self, portfolio_value: float) -> Dict[str, float]:
        """Get position limits based on current portfolio"""
        try:
            return {
                'max_position_size': portfolio_value * self.max_position_size,
                'max_leverage': self.max_leverage,
                'current_drawdown': self.current_drawdown,
                'max_drawdown': self.max_drawdown
            }
            
        except Exception as e:
            logger.error(f"Error getting position limits: {str(e)}")
            return {}

# Initialize global instance
risk_manager = RiskManager()
