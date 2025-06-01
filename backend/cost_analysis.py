import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
import numba
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Cache for cost calculations
cost_cache = {}
last_cache_update = datetime.min
CACHE_TTL = 300  # 5 minutes

@numba.jit(nopython=True)
def _fast_commission_cost(trade_size: float, price: float, base_commission: float) -> float:
    """Fast commission cost calculation using Numba"""
    return trade_size * price * base_commission

@numba.jit(nopython=True)
def _fast_slippage(trade_size: float, price: float, 
                  market_volume: float, slippage_base: float, 
                  liquidity_threshold: float) -> float:
    """Fast slippage calculation using Numba"""
    base_slippage = price * slippage_base
    liquidity_impact = trade_size / market_volume
    if liquidity_impact > liquidity_threshold:
        base_slippage *= (1 + liquidity_impact)
    return base_slippage

@numba.jit(nopython=True)
def _fast_market_impact(trade_size: float, price: float, 
                       market_volume: float, market_impact_exponent: float) -> float:
    """Fast market impact calculation using Numba"""
    impact = trade_size / market_volume
    return price * impact ** market_impact_exponent

@numba.jit(nopython=True)
def _fast_total_transaction_cost(trade_size: float, price: float, market_volume: float,
                               base_commission: float, slippage_base: float,
                               liquidity_threshold: float, market_impact_exponent: float) -> float:
    """Fast total transaction cost calculation using Numba"""
    commission = _fast_commission_cost(trade_size, price, base_commission)
    slippage = _fast_slippage(trade_size, price, market_volume, slippage_base, liquidity_threshold)
    market_impact = _fast_market_impact(trade_size, price, market_volume, market_impact_exponent)
    return commission + slippage + market_impact

class TransactionCostAnalyzer:
    def __init__(self,
                 base_commission: float = 0.001,
                 slippage_base: float = 0.0005,
                 liquidity_threshold: float = 0.05,
                 market_impact_exponent: float = 0.6,
                 cache_enabled: bool = True):
        """
        Initialize transaction cost analyzer
        
        Args:
            base_commission: Base commission rate
            slippage_base: Base slippage percentage
            liquidity_threshold: Threshold for liquidity impact
            market_impact_exponent: Exponent for market impact calculation
            cache_enabled: Enable caching of calculations
        """
        self.base_commission = base_commission
        self.slippage_base = slippage_base
        self.liquidity_threshold = liquidity_threshold
        self.market_impact_exponent = market_impact_exponent
        self.cache_enabled = cache_enabled
        self.cost_cache = {}
        
    def _get_cache_key(self, trade_size: float, price: float, market_volume: float) -> str:
        """Generate cache key based on trade parameters"""
        return f"cost_{hash((trade_size, price, market_volume))}"
        
    def _cache_result(self, key: str, result: Any) -> None:
        """Cache result with TTL"""
        if self.cache_enabled:
            self.cost_cache[key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
    def _get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result if valid"""
        if not self.cache_enabled:
            return None
            
        if key not in self.cost_cache:
            return None
            
        cached = self.cost_cache[key]
        if (datetime.now() - cached['timestamp']).total_seconds() > CACHE_TTL:
            return None
            
        return cached['result']
    
    def calculate_commission_cost(self, 
                                trade_size: float, 
                                price: float) -> float:
        """Calculate commission cost with caching and optimization"""
        try:
            key = self._get_cache_key(trade_size, price, 0)  # Use 0 as market_volume placeholder
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_commission_cost(trade_size, price, self.base_commission)
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating commission cost: {str(e)}")
            return 0.0

    def calculate_slippage(self, 
                         trade_size: float, 
                         price: float, 
                         market_volume: float) -> float:
        """Calculate slippage with caching and optimization"""
        try:
            key = self._get_cache_key(trade_size, price, market_volume)
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_slippage(
                trade_size, price, market_volume,
                self.slippage_base, self.liquidity_threshold
            )
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating slippage: {str(e)}")
            return 0.0

    def calculate_market_impact(self, 
                              trade_size: float, 
                              price: float, 
                              market_volume: float) -> float:
        """Calculate market impact with caching and optimization"""
        try:
            key = self._get_cache_key(trade_size, price, market_volume)
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_market_impact(
                trade_size, price, market_volume,
                self.market_impact_exponent
            )
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating market impact: {str(e)}")
            return 0.0

    def calculate_total_transaction_cost(self, 
                                       trade_size: float, 
                                       price: float, 
                                       market_volume: float) -> float:
        """Calculate total transaction cost with caching and optimization"""
        try:
            key = self._get_cache_key(trade_size, price, market_volume)
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_total_transaction_cost(
                trade_size, price, market_volume,
                self.base_commission, self.slippage_base,
                self.liquidity_threshold, self.market_impact_exponent
            )
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating total transaction cost: {str(e)}")
            return 0.0

    def analyze_trade_costs(self, 
                           trade_data: pd.DataFrame) -> pd.DataFrame:
        """Analyze transaction costs for a series of trades"""
        try:
            # Calculate costs for each trade
            trade_data['commission'] = trade_data.apply(
                lambda x: self.calculate_commission_cost(x['size'], x['price']),
                axis=1
            )
            trade_data['slippage'] = trade_data.apply(
                lambda x: self.calculate_slippage(x['size'], x['price'], x['volume']),
                axis=1
            )
            trade_data['market_impact'] = trade_data.apply(
                lambda x: self.calculate_market_impact(x['size'], x['price'], x['volume']),
                axis=1
            )
            trade_data['total_cost'] = trade_data['commission'] + \
                                     trade_data['slippage'] + \
                                     trade_data['market_impact']
            
            # Calculate cost metrics
            metrics = {
                'avg_commission': trade_data['commission'].mean(),
                'avg_slippage': trade_data['slippage'].mean(),
                'avg_market_impact': trade_data['market_impact'].mean(),
                'total_cost': trade_data['total_cost'].sum(),
                'cost_ratio': trade_data['total_cost'].sum() / trade_data['price'].sum()
            }
            
            return trade_data, metrics
            
        except Exception as e:
            logger.error(f"Error analyzing trade costs: {str(e)}")
            return pd.DataFrame(), {}

    def optimize_trade_size(self, 
                          target_size: float, 
                          price: float, 
                          market_volume: float,
                          max_cost_ratio: float = 0.01) -> float:
        """Optimize trade size to minimize transaction costs"""
        try:
            # Start with target size
            current_size = target_size
            
            # Calculate initial costs
            initial_cost = self.calculate_total_transaction_cost(
                current_size, price, market_volume
            )
            initial_cost_ratio = initial_cost / (current_size * price)
            
            # Reduce size if costs are too high
            while initial_cost_ratio > max_cost_ratio and current_size > 0:
                current_size *= 0.9  # Reduce by 10%
                current_cost = self.calculate_total_transaction_cost(
                    current_size, price, market_volume
                )
                current_cost_ratio = current_cost / (current_size * price)
                
            return current_size
            
        except Exception as e:
            logger.error(f"Error optimizing trade size: {str(e)}")
            return target_size

    def get_cost_metrics(self) -> Dict[str, float]:
        """Get current cost parameters"""
        return {
            'base_commission': self.base_commission,
            'slippage_base': self.slippage_base,
            'liquidity_threshold': self.liquidity_threshold,
            'market_impact_exponent': self.market_impact_exponent
        }

    def plot_cost_analysis(self, trade_data: pd.DataFrame) -> None:
        """Plot cost analysis results"""
        try:
            import matplotlib.pyplot as plt
            
            # Create figure
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot individual cost components
            trade_data[['commission', 'slippage', 'market_impact']].plot(ax=axes[0, 0])
            axes[0, 0].set_title('Transaction Cost Components')
            
            # Plot total costs
            trade_data['total_cost'].plot(ax=axes[0, 1])
            axes[0, 1].set_title('Total Transaction Costs')
            
            # Plot cost ratios
            trade_data['cost_ratio'] = trade_data['total_cost'] / (trade_data['size'] * trade_data['price'])
            trade_data['cost_ratio'].plot(ax=axes[1, 0])
            axes[1, 0].set_title('Cost Ratio')
            
            # Plot trade sizes
            trade_data['size'].plot(ax=axes[1, 1])
            axes[1, 1].set_title('Trade Sizes')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting cost analysis: {str(e)}")
            raise

# Initialize global instance
cost_analyzer = TransactionCostAnalyzer()
