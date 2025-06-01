import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Type
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from ..risk_management import RiskManager
from ..backtesting import Backtester

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, name: str, parameters: Dict = None):
        self.name = name
        self.parameters = parameters or {}
        self.metrics = {}
        self.correlation_matrix = None
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals"""
        raise NotImplementedError("Subclasses must implement generate_signals")
        
    def calculate_metrics(self, returns: pd.Series) -> Dict:
        """Calculate strategy metrics"""
        try:
            sharpe = returns.mean() / returns.std()
            sortino = returns.mean() / returns[returns < 0].std()
            max_drawdown = (returns + 1).cumprod().expanding().apply(lambda x: x.min() / x.max() - 1).min()
            
            return {
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'max_drawdown': max_drawdown,
                'win_rate': (returns > 0).mean(),
                'avg_return': returns.mean(),
                'std_dev': returns.std()
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {self.name}: {str(e)}")
            return {}

class StrategyFramework:
    def __init__(self,
                 strategies: List[Type[TradingStrategy]],
                 weights: Dict[str, float] = None,
                 risk_manager: RiskManager = None,
                 backtester: Backtester = None):
        """
        Initialize strategy framework with safety measures
        
        Args:
            strategies: List of strategy classes
            weights: Weights for each strategy
            risk_manager: Risk management instance
            backtester: Backtesting instance
        """
        self.strategies = strategies
        self.weights = weights or {s.__name__: 1/len(strategies) for s in strategies}
        self.risk_manager = risk_manager or RiskManager()
        self.backtester = backtester or Backtester()
        self.strategy_instances = {}
        self.last_update = None
        
        # Safety measures
        self.max_position_size = 0.1  # 10% of portfolio
        self.max_drawdown = 0.05      # 5% drawdown limit
        self.consecutive_losses = 0
        self.current_drawdown = 0
        self.active = True
        
        # Validate weights
        if not self._validate_weights():
            raise ValueError("Invalid strategy weights")
            
    def _validate_weights(self) -> bool:
        """Validate strategy weights"""
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            return False
            
        for weight in self.weights.values():
            if weight < 0 or weight > 0.5:  # No strategy can have more than 50% weight
                return False
                
        return True
        
    def _check_safety(self, trade_details: dict) -> bool:
        """Check if trade is within safety parameters"""
        try:
            if not self.active:
                logger.warning("AI trading is currently paused")
                return False
                
            if trade_details['position_size'] > self.max_position_size:
                logger.warning(f"Trade size {trade_details['position_size']} exceeds max position size {self.max_position_size}")
                return False
                
            if self.consecutive_losses >= 3:
                logger.warning(f"Maximum consecutive losses ({self.consecutive_losses}) reached")
                return False
                
            if self.current_drawdown >= self.max_drawdown:
                logger.warning(f"Maximum drawdown ({self.current_drawdown}) exceeded")
                return False
                
            # Check if trade is within risk parameters
            if not self.risk_manager.validate_trade(trade_details):
                logger.warning("Trade failed risk validation")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Safety check failed: {str(e)}")
            return False
        
    async def execute_trade(self, trade_details: dict) -> bool:
        """Execute trade with safety checks"""
        if not self._check_safety(trade_details):
            logger.warning("Trade rejected due to safety constraints")
            return False
            
        # Log the decision
        await log_ai_decision('trade_execution', trade_details)
        
        # Require user confirmation
        if not await require_user_confirmation(trade_details):
            logger.info("Trade execution requires user confirmation")
            return False
            
        # Execute trade through risk manager
        return await self.risk_manager.execute_trade(trade_details)

    async def initialize_strategies(self, data: pd.DataFrame) -> None:
        """Initialize all strategies with safety checks"""
        try:
            if not self.active:
                raise RuntimeError("AI trading is currently paused")
                
            for strategy in self.strategies:
                instance = strategy()
                signals = instance.generate_signals(data)
                
                # Validate signals
                if signals is None or signals.empty:
                    raise ValueError(f"No signals generated for strategy {strategy.__name__}")
                    
                self.strategy_instances[strategy.__name__] = instance
                
            # Log initialization
            await log_ai_decision('strategy_initialization', {
                'strategies': [s.__name__ for s in self.strategies],
                'weights': self.weights,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("Strategies initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing strategies: {str(e)}")
            # Log error
            await log_ai_decision('error', {
                'type': 'initialization_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise

    async def update_metrics(self, trade_result: dict) -> None:
        """Update safety metrics based on trade results"""
        try:
            if trade_result['profit'] < 0:
                self.consecutive_losses += 1
                self.current_drawdown = min(self.current_drawdown, trade_result['profit'])
            else:
                self.consecutive_losses = 0
                self.current_drawdown = 0
                
            # Log metrics update
            await log_ai_decision('metrics_update', {
                'consecutive_losses': self.consecutive_losses,
                'current_drawdown': self.current_drawdown,
                'trade_result': trade_result
            })
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
            raise

    def validate_weights(self) -> bool:
        """Validate that weights sum to 1"""
        total_weight = sum(self.weights.values())
        return abs(total_weight - 1.0) < 1e-6

    def optimize_weights(self) -> Dict[str, float]:
        """Optimize strategy weights based on correlations and performance"""
        try:
            if self.correlation_matrix is None:
                self.calculate_correlations()
                
            # Calculate performance metrics
            metrics = {}
            for name, instance in self.strategy_instances.items():
                metrics[name] = instance.calculate_metrics(
                    instance.generate_signals(data)
                )
                
            # Create optimization problem
            n = len(self.strategies)
            weights = np.ones(n) / n
            
            # Minimize correlation while maximizing performance
            for i in range(n):
                for j in range(i + 1, n):
                    corr = self.correlation_matrix.iloc[i, j]
                    if corr > self.correlation_threshold:
                        weights[i] *= (1 - corr)
                        weights[j] *= (1 - corr)
                        
            # Normalize weights
            weights /= weights.sum()
            
            # Update strategy weights
            self.weights = {
                name: weights[i]
                for i, name in enumerate(self.strategy_instances.keys())
            }
            
            return self.weights
            
        except Exception as e:
            logger.error(f"Error optimizing weights: {str(e)}")
            return self.weights

    def generate_combined_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate combined signals from all strategies"""
        try:
            # Get individual signals
            signals = pd.DataFrame({
                name: instance.generate_signals(data) * weight
                for name, instance in self.strategy_instances.items()
                for weight in [self.weights[name]]
            })
            
            # Combine signals
            combined = signals.sum(axis=1)
            
            # Apply risk management
            combined = combined * self.risk_manager.calculate_position_size(
                data['close'].iloc[-1],
                data['volatility'].iloc[-1],
                data['portfolio_value'].iloc[-1]
            )
            
            return combined
            
        except Exception as e:
            logger.error(f"Error generating combined signals: {str(e)}")
            return pd.Series()

    def rebalance(self, data: pd.DataFrame) -> None:
        """Rebalance strategy weights"""
        try:
            current_time = datetime.now()
            if self.last_rebalance is None or \
               (current_time - self.last_rebalance).days >= self.rebalance_period:
                
                self.optimize_weights()
                self.calculate_correlations()
                self.last_rebalance = current_time
                logger.info("Strategies rebalanced")
                
        except Exception as e:
            logger.error(f"Error rebalancing strategies: {str(e)}")
            raise

    def get_strategy_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all strategies"""
        try:
            return {
                name: instance.calculate_metrics(
                    instance.generate_signals(data)
                )
                for name, instance in self.strategy_instances.items()
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy metrics: {str(e)}")
            return {}

    def get_combined_metrics(self, data: pd.DataFrame) -> Dict:
        """Get combined strategy metrics"""
        try:
            combined_signals = self.generate_combined_signals(data)
            return self.calculate_metrics(combined_signals)
            
        except Exception as e:
            logger.error(f"Error getting combined metrics: {str(e)}")
            return {}

    def plot_strategy_performance(self) -> None:
        """Plot strategy performance"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create figure
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot individual strategy returns
            for name, instance in self.strategy_instances.items():
                returns = instance.generate_signals(data)
                axes[0, 0].plot(returns.cumsum(), label=name)
            axes[0, 0].set_title('Individual Strategy Returns')
            axes[0, 0].legend()
            
            # Plot correlation matrix
            sns.heatmap(self.correlation_matrix, annot=True, ax=axes[0, 1])
            axes[0, 1].set_title('Strategy Correlation Matrix')
            
            # Plot combined returns
            combined = self.generate_combined_signals(data)
            axes[1, 0].plot(combined.cumsum())
            axes[1, 0].set_title('Combined Strategy Returns')
            
            # Plot weights
            weights = pd.Series(self.weights)
            weights.plot(kind='bar', ax=axes[1, 1])
            axes[1, 1].set_title('Strategy Weights')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting strategy performance: {str(e)}")
            raise

# Example usage:
# strategies = [MomentumStrategy, MeanReversionStrategy, LSTMStrategy]
# framework = StrategyFramework(strategies)
# framework.initialize_strategies(data)
# signals = framework.generate_combined_signals(data)
