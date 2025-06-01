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
                 volatility_adjustment: bool = True):
        """
        Initialize risk management system
        
        Args:
            max_position_size: Maximum position size as % of portfolio
            max_drawdown: Maximum allowed drawdown
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            risk_per_trade: Risk per trade as % of portfolio
            volatility_adjustment: Whether to adjust position size based on volatility
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.risk_per_trade = risk_per_trade
        self.volatility_adjustment = volatility_adjustment
        
        # Risk metrics
        self.current_drawdown = 0.0
        self.max_drawdown_reached = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        
    def calculate_position_size(self, 
                               current_price: float, 
                               portfolio_value: float, 
                               volatility: float) -> float:
        """Calculate optimal position size"""
        try:
            # Base position size based on risk per trade
            base_size = (portfolio_value * self.risk_per_trade) / (current_price * self.stop_loss_pct)
            
            # Apply volatility adjustment
            if self.volatility_adjustment:
                base_size *= (1 / (volatility + 1e-6))
            
            # Apply maximum position size limit
            max_size = portfolio_value * self.max_position_size
            position_size = min(base_size, max_size)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def calculate_stop_loss(self, 
                           entry_price: float, 
                           volatility: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        try:
            # Calculate stop loss
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            
            # Calculate take profit
            take_profit = entry_price * (1 + self.take_profit_pct)
            
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
                'total_profit': self.total_profit
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {str(e)}")
            return {}

    def check_risk_limits(self, 
                         portfolio_value: float, 
                         position_size: float) -> bool:
        """Check if risk limits are exceeded"""
        try:
            # Check position size limit
            if position_size > portfolio_value * self.max_position_size:
                return False
                
            # Check drawdown limit
            if self.current_drawdown > self.max_drawdown:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return False

    def calculate_hedging_position(self, 
                                  current_position: float, 
                                  market_trend: str, 
                                  volatility: float) -> float:
        """Calculate optimal hedging position"""
        try:
            # Calculate hedge ratio based on market conditions
            hedge_ratio = 0.0
            
            if market_trend == 'bullish':
                hedge_ratio = 0.5 * volatility
            elif market_trend == 'bearish':
                hedge_ratio = 1.0 * volatility
            else:  # sideways
                hedge_ratio = 0.3 * volatility
                
            # Calculate hedge position
            hedge_position = current_position * hedge_ratio
            return hedge_position
            
        except Exception as e:
            logger.error(f"Error calculating hedging position: {str(e)}")
            return 0.0

# Initialize global instance
risk_manager = RiskManager()
