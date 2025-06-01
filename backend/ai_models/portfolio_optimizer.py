import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    def __init__(self,
                 max_assets: int = 10,
                 min_allocation: float = 0.01,
                 max_allocation: float = 0.3,
                 risk_free_rate: float = 0.02,
                 optimization_method: str = 'sharpe_ratio'):
        """
        Initialize portfolio optimizer
        
        Args:
            max_assets: Maximum number of assets in portfolio
            min_allocation: Minimum allocation per asset
            max_allocation: Maximum allocation per asset
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            optimization_method: Method for portfolio optimization
        """
        self.max_assets = max_assets
        self.min_allocation = min_allocation
        self.max_allocation = max_allocation
        self.risk_free_rate = risk_free_rate
        self.optimization_method = optimization_method
        
        # Optimization constraints
        self.constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Sum of weights = 1
            {'type': 'ineq', 'fun': lambda x: x - self.min_allocation},  # Min allocation
            {'type': 'ineq', 'fun': lambda x: self.max_allocation - x}  # Max allocation
        )
        
    def calculate_covariance_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate covariance matrix of returns"""
        try:
            return returns.cov()
            
        except Exception as e:
            logger.error(f"Error calculating covariance matrix: {str(e)}")
            raise

    def calculate_portfolio_return(self, 
                                 weights: np.ndarray, 
                                 returns: pd.DataFrame) -> float:
        """Calculate portfolio return"""
        try:
            return np.sum(returns.mean() * weights) * 252  # Annualize
            
        except Exception as e:
            logger.error(f"Error calculating portfolio return: {str(e)}")
            raise

    def calculate_portfolio_volatility(self, 
                                     weights: np.ndarray, 
                                     cov_matrix: pd.DataFrame) -> float:
        """Calculate portfolio volatility"""
        try:
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
            
        except Exception as e:
            logger.error(f"Error calculating portfolio volatility: {str(e)}")
            raise

    def calculate_sharpe_ratio(self, 
                             weights: np.ndarray, 
                             returns: pd.DataFrame, 
                             cov_matrix: pd.DataFrame) -> float:
        """Calculate Sharpe ratio"""
        try:
            portfolio_return = self.calculate_portfolio_return(weights, returns)
            portfolio_volatility = self.calculate_portfolio_volatility(weights, cov_matrix)
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
            return -sharpe_ratio  # Minimize negative Sharpe
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            raise

    def optimize_portfolio(self, 
                         returns: pd.DataFrame, 
                         cov_matrix: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """Optimize portfolio weights"""
        try:
            if cov_matrix is None:
                cov_matrix = self.calculate_covariance_matrix(returns)
                
            # Initial guess (equal weights)
            num_assets = len(returns.columns)
            initial_guess = np.array([1/num_assets] * num_assets)
            
            # Optimize based on selected method
            if self.optimization_method == 'sharpe_ratio':
                result = minimize(
                    self.calculate_sharpe_ratio,
                    initial_guess,
                    args=(returns, cov_matrix),
                    method='SLSQP',
                    constraints=self.constraints,
                    bounds=[(self.min_allocation, self.max_allocation)] * num_assets
                )
                
            elif self.optimization_method == 'min_variance':
                result = minimize(
                    lambda x: self.calculate_portfolio_volatility(x, cov_matrix),
                    initial_guess,
                    method='SLSQP',
                    constraints=self.constraints,
                    bounds=[(self.min_allocation, self.max_allocation)] * num_assets
                )
                
            # Create allocation dictionary
            allocations = {}
            for i, asset in enumerate(returns.columns):
                allocations[asset] = result.x[i]
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {str(e)}")
            raise

    def calculate_efficient_frontier(self, 
                                   returns: pd.DataFrame, 
                                   num_points: int = 20) -> pd.DataFrame:
        """Calculate efficient frontier"""
        try:
            cov_matrix = self.calculate_covariance_matrix(returns)
            
            # Generate target returns
            target_returns = np.linspace(
                returns.mean().min() * 252,
                returns.mean().max() * 252,
                num_points
            )
            
            # Calculate minimum variance portfolio for each target return
            frontier = []
            for target in target_returns:
                constraints = (
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: self.calculate_portfolio_return(x, returns) - target},
                    {'type': 'ineq', 'fun': lambda x: x - self.min_allocation},
                    {'type': 'ineq', 'fun': lambda x: self.max_allocation - x}
                )
                
                result = minimize(
                    lambda x: self.calculate_portfolio_volatility(x, cov_matrix),
                    np.array([1/len(returns.columns)] * len(returns.columns)),
                    method='SLSQP',
                    constraints=constraints,
                    bounds=[(self.min_allocation, self.max_allocation)] * len(returns.columns)
                )
                
                volatility = self.calculate_portfolio_volatility(result.x, cov_matrix)
                sharpe_ratio = self.calculate_sharpe_ratio(result.x, returns, cov_matrix)
                
                frontier.append({
                    'target_return': target,
                    'volatility': volatility,
                    'sharpe_ratio': -sharpe_ratio
                })
                
            return pd.DataFrame(frontier)
            
        except Exception as e:
            logger.error(f"Error calculating efficient frontier: {str(e)}")
            raise

    def rebalance_portfolio(self, 
                          current_weights: Dict[str, float],
                          target_weights: Dict[str, float],
                          transaction_cost: float = 0.001) -> Dict[str, float]:
        """Calculate portfolio rebalancing"""
        try:
            # Calculate adjustments needed
            adjustments = {}
            for asset in current_weights.keys():
                current = current_weights.get(asset, 0)
                target = target_weights.get(asset, 0)
                adjustment = target - current
                
                # Apply transaction cost
                if abs(adjustment) > transaction_cost:
                    adjustments[asset] = adjustment
                else:
                    adjustments[asset] = 0
                    
            return adjustments
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {str(e)}")
            raise

# Initialize global instance
portfolio_optimizer = PortfolioOptimizer()
