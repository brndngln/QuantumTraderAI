import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from backend.metrics import Metrics
from backend.risk_management import risk_manager
from backend.cost_analysis import cost_analyzer
from backend.portfolio_optimizer import portfolio_optimizer

logger = logging.getLogger(__name__)

class RealTimeAnalyzer:
    def __init__(self,
                 window_size: int = 252,
                 update_frequency: int = 60,
                 risk_threshold: float = 0.02,
                 rebalance_threshold: float = 0.05,
                 max_position_size: float = 0.05):
        """
        Initialize real-time analyzer
        
        Args:
            window_size: Rolling window size
            update_frequency: Frequency of updates (seconds)
            risk_threshold: Risk threshold for alerts
            rebalance_threshold: Threshold for rebalancing
            max_position_size: Maximum position size
        """
        self.window_size = window_size
        self.update_frequency = update_frequency
        self.risk_threshold = risk_threshold
        self.rebalance_threshold = rebalance_threshold
        self.max_position_size = max_position_size
        self.metrics = Metrics()
        self.last_update = None
        self.current_positions = {}
        self.risk_metrics = {}
        
    def update_positions(self, positions: Dict[str, float]) -> None:
        """Update current positions"""
        try:
            self.current_positions = positions
            self._calculate_risk_metrics()
            
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
            raise

    def _calculate_risk_metrics(self) -> None:
        """Calculate risk metrics"""
        try:
            # Calculate portfolio metrics
            metrics = {
                'total_exposure': sum(abs(p) for p in self.current_positions.values()),
                'max_position': max(abs(p) for p in self.current_positions.values()),
                'position_count': len(self.current_positions),
                'concentration': max(self.current_positions.values()) / sum(self.current_positions.values())
            }
            
            # Calculate risk metrics
            risk_metrics = risk_manager.get_risk_metrics()
            metrics.update(risk_metrics)
            
            self.risk_metrics = metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            raise

    def check_risk_limits(self) -> Dict[str, bool]:
        """Check if risk limits are exceeded"""
        try:
            alerts = {
                'max_position': self.risk_metrics['max_position'] > self.max_position_size,
                'position_count': self.risk_metrics['position_count'] > 10,
                'concentration': self.risk_metrics['concentration'] > 0.2,
                'drawdown': self.risk_metrics['current_drawdown'] > self.risk_threshold,
                'volatility': self.risk_metrics.get('volatility', 0) > 0.05
            }
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return {}

    def calculate_position_sizing(self, 
                                price: float, 
                                volatility: float, 
                                portfolio_value: float) -> float:
        """Calculate optimal position size"""
        try:
            # Get risk-adjusted position size
            position_size = risk_manager.calculate_position_size(
                price,
                portfolio_value,
                volatility
            )
            
            # Apply rebalance threshold
            if position_size > self.rebalance_threshold * portfolio_value:
                position_size = self.rebalance_threshold * portfolio_value
                
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position sizing: {str(e)}")
            return 0.0

    def optimize_positions(self, 
                         current_positions: Dict[str, float],
                         target_positions: Dict[str, float],
                         portfolio_value: float) -> Dict[str, float]:
        """Optimize positions based on risk and cost"""
        try:
            # Calculate optimal weights
            optimized_weights = portfolio_optimizer.optimize_portfolio(
                pd.DataFrame.from_dict(current_positions, orient='index', columns=['weights'])
            )
            
            # Calculate rebalancing trades
            trades = portfolio_optimizer.rebalance_portfolio(
                current_positions,
                optimized_weights,
                {asset: price for asset, price in current_positions.items()},
                portfolio_value
            )
            
            # Adjust for transaction costs
            for asset, trade in trades.items():
                cost = cost_analyzer.calculate_total_transaction_cost(
                    abs(trade),
                    current_positions[asset],
                    portfolio_value
                )
                if cost > self.risk_threshold * portfolio_value:
                    trades[asset] = 0
                    
            return trades
            
        except Exception as e:
            logger.error(f"Error optimizing positions: {str(e)}")
            return {}

    def get_real_time_metrics(self) -> Dict:
        """Get current real-time metrics"""
        try:
            return {
                'risk_metrics': self.risk_metrics,
                'current_positions': self.current_positions,
                'risk_alerts': self.check_risk_limits(),
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {str(e)}")
            return {}

    def plot_real_time_analysis(self) -> None:
        """Plot real-time analysis results"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create DataFrame
            df = pd.DataFrame.from_dict(self.current_positions, orient='index', columns=['Position'])
            
            # Plot position sizes
            plt.figure(figsize=(15, 10))
            plt.subplot(2, 2, 1)
            df['Position'].plot(kind='bar')
            plt.title('Current Positions')
            
            # Plot risk metrics
            plt.subplot(2, 2, 2)
            pd.Series(self.risk_metrics).plot(kind='bar')
            plt.title('Risk Metrics')
            
            # Plot alerts
            plt.subplot(2, 2, 3)
            pd.Series(self.check_risk_limits()).plot(kind='bar')
            plt.title('Risk Alerts')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting real-time analysis: {str(e)}")
            raise

    def get_position_adjustments(self, 
                               current_positions: Dict[str, float],
                               price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate position adjustments"""
        try:
            # Calculate volatility
            volatilities = price_data.apply(self.metrics.calculate_volatility)
            
            # Calculate optimal sizes
            adjusted_positions = {}
            for asset, position in current_positions.items():
                if asset in price_data.columns:
                    price = price_data[asset].iloc[-1]
                    volatility = volatilities[asset]
                    
                    # Calculate optimal size
                    optimal_size = self.calculate_position_sizing(
                        price,
                        volatility,
                        sum(current_positions.values())
                    )
                    
                    # Calculate adjustment
                    adjustment = optimal_size - abs(position)
                    adjusted_positions[asset] = adjustment
                    
            return adjusted_positions
            
        except Exception as e:
            logger.error(f"Error calculating position adjustments: {str(e)}")
            return {}

# Initialize global instance
real_time_analyzer = RealTimeAnalyzer()
