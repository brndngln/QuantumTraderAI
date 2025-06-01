import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from scipy.optimize import minimize
from backend.metrics import Metrics
from backend.cost_analysis import cost_analyzer

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    def __init__(self,
                 risk_free_rate: float = 0.02,
                 max_leverage: float = 2.0,
                 min_allocation: float = 0.01,
                 max_allocation: float = 0.3,
                 rebalance_period: int = 252,
                 optimization_method: str = 'risk_parity',
                 constraints: Dict = None):
        """
        Initialize portfolio optimizer
        
        Args:
            risk_free_rate: Annual risk-free rate
            max_leverage: Maximum leverage allowed
            min_allocation: Minimum allocation per asset
            max_allocation: Maximum allocation per asset
            rebalance_period: Period for rebalancing
            optimization_method: Portfolio optimization method
            constraints: Additional optimization constraints
        """
        self.risk_free_rate = risk_free_rate
        self.max_leverage = max_leverage
        self.min_allocation = min_allocation
        self.max_allocation = max_allocation
        self.rebalance_period = rebalance_period
        self.optimization_method = optimization_method
        self.constraints = constraints or {}
        self.metrics = Metrics(risk_free_rate)
        self.last_rebalance = None
        self.current_weights = {}
        
    def calculate_covariance_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate covariance matrix"""
        try:
            return returns.cov()
            
        except Exception as e:
            logger.error(f"Error calculating covariance matrix: {str(e)}")
            raise

    def calculate_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix"""
        try:
            return returns.corr()
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            raise

    def calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        try:
            return returns.std() * np.sqrt(252)
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0

    def calculate_risk_parity_weights(self, 
                                    volatilities: np.ndarray, 
                                    correlations: np.ndarray) -> np.ndarray:
        """Calculate risk parity weights"""
        try:
            # Calculate inverse volatilities
            inv_vols = 1 / volatilities
            
            # Calculate correlation matrix
            corr_matrix = np.diag(inv_vols) @ correlations @ np.diag(inv_vols)
            
            # Calculate eigenvalues and eigenvectors
            eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)
            
            # Calculate risk parity weights
            weights = eigenvectors[:, -1] * inv_vols
            weights = weights / np.sum(weights)
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculating risk parity weights: {str(e)}")
            return np.ones(len(volatilities)) / len(volatilities)

    def calculate_min_variance_weights(self, 
                                     cov_matrix: np.ndarray) -> np.ndarray:
        """Calculate minimum variance weights"""
        try:
            # Calculate inverse covariance matrix
            inv_cov = np.linalg.inv(cov_matrix)
            
            # Calculate weights
            weights = inv_cov @ np.ones(len(cov_matrix))
            weights = weights / np.sum(weights)
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculating min variance weights: {str(e)}")
            return np.ones(len(cov_matrix)) / len(cov_matrix)

    def calculate_max_diversification_weights(self, 
                                            volatilities: np.ndarray, 
                                            correlations: np.ndarray) -> np.ndarray:
        """Calculate maximum diversification weights"""
        try:
            # Calculate correlation matrix
            corr_matrix = np.diag(volatilities) @ correlations @ np.diag(volatilities)
            
            # Calculate diversification ratio
            diversification = np.sqrt(np.diag(corr_matrix)) / np.sqrt(np.diag(corr_matrix).sum())
            
            # Calculate weights
            weights = diversification / diversification.sum()
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculating max diversification weights: {str(e)}")
            return np.ones(len(volatilities)) / len(volatilities)

    def optimize_portfolio(self, returns: pd.DataFrame) -> Dict[str, float]:
        """Optimize portfolio weights"""
        try:
            # Calculate required matrices
            volatilities = returns.apply(self.calculate_volatility).values
            correlations = self.calculate_correlation_matrix(returns).values
            cov_matrix = self.calculate_covariance_matrix(returns).values
            
            # Choose optimization method
            if self.optimization_method == 'risk_parity':
                weights = self.calculate_risk_parity_weights(volatilities, correlations)
            elif self.optimization_method == 'min_variance':
                weights = self.calculate_min_variance_weights(cov_matrix)
            elif self.optimization_method == 'max_diversification':
                weights = self.calculate_max_diversification_weights(volatilities, correlations)
            
            # Apply constraints
            weights = np.clip(weights, self.min_allocation, self.max_allocation)
            weights = weights / weights.sum()
            
            # Create allocation dictionary
            allocations = {
                asset: float(weight)
                for asset, weight in zip(returns.columns, weights)
            }
            
            return allocations
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {str(e)}")
            raise

    def rebalance_portfolio(self, 
                          current_weights: Dict[str, float],
                          target_weights: Dict[str, float],
                          prices: Dict[str, float],
                          portfolio_value: float) -> Dict[str, float]:
        """Calculate rebalancing trades"""
        try:
            # Calculate target positions
            target_positions = {}
            for asset, weight in target_weights.items():
                target_positions[asset] = weight * portfolio_value / prices[asset]
                
            # Calculate current positions
            current_positions = {}
            for asset, weight in current_weights.items():
                current_positions[asset] = weight * portfolio_value / prices[asset]
                
            # Calculate trades needed
            trades = {}
            for asset in target_positions:
                if asset in current_positions:
                    trade_size = target_positions[asset] - current_positions[asset]
                    trades[asset] = trade_size
                else:
                    trades[asset] = target_positions[asset]
                    
            return trades
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {str(e)}")
            raise

    def calculate_portfolio_metrics(self, 
                                 returns: pd.DataFrame, 
                                 weights: Dict[str, float]) -> Dict:
        """Calculate portfolio metrics"""
        try:
            # Calculate weighted returns
            weighted_returns = returns.mul(pd.Series(weights))
            portfolio_returns = weighted_returns.sum(axis=1)
            
            # Calculate metrics
            metrics = self.metrics.calculate_basic_metrics(portfolio_returns)
            metrics.update({
                'volatility': self.calculate_volatility(portfolio_returns),
                'correlation': self.calculate_correlation_matrix(returns).mean().mean(),
                'diversification': len(returns.columns) / np.sum(weights ** 2)
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
            return {}

    def get_optimization_metrics(self) -> Dict:
        """Get optimization parameters and metrics"""
        try:
            return {
                'optimization_method': self.optimization_method,
                'risk_free_rate': self.risk_free_rate,
                'max_leverage': self.max_leverage,
                'min_allocation': self.min_allocation,
                'max_allocation': self.max_allocation,
                'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None,
                'current_weights': self.current_weights
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization metrics: {str(e)}")
            return {}

    def plot_allocation(self, weights: Dict[str, float]) -> None:
        """Plot portfolio allocation"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create DataFrame
            df = pd.DataFrame(list(weights.items()), columns=['Asset', 'Weight'])
            
            # Plot pie chart
            plt.figure(figsize=(10, 6))
            plt.pie(df['Weight'], labels=df['Asset'], autopct='%1.1f%%')
            plt.title('Portfolio Allocation')
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting allocation: {str(e)}")
            raise

# Initialize global instance
portfolio_optimizer = PortfolioOptimizer()
