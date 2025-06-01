import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
import numba
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Cache for metrics calculations
metrics_cache = {}
last_cache_update = datetime.min
CACHE_TTL = 300  # 5 minutes

@numba.jit(nopython=True)
def _fast_sharpe_ratio(returns: np.ndarray, risk_free_rate: float) -> float:
    """Fast Sharpe ratio calculation using Numba"""
    excess_returns = returns - (risk_free_rate / 252)
    mean = np.mean(excess_returns)
    std = np.std(excess_returns)
    return mean / std if std != 0 else 0.0

@numba.jit(nopython=True)
def _fast_max_drawdown(cumulative: np.ndarray) -> float:
    """Fast maximum drawdown calculation using Numba"""
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return np.min(drawdown)

@numba.jit(nopython=True)
def _fast_basic_metrics(returns: np.ndarray, risk_free_rate: float) -> Dict:
    """Fast basic metrics calculation using Numba"""
    excess_returns = returns - (risk_free_rate / 252)
    return {
        'sharpe_ratio': _fast_sharpe_ratio(returns, risk_free_rate),
        'max_drawdown': _fast_max_drawdown(np.cumprod(1 + returns)),
        'avg_return': np.mean(returns),
        'std_dev': np.std(returns),
        'total_return': np.prod(1 + returns) - 1
    }

class Metrics:
    def __init__(self,
                 risk_free_rate: float = 0.02,
                 benchmark_returns: Optional[pd.Series] = None,
                 window_size: int = 252,
                 cache_enabled: bool = True):
        """
        Initialize metrics calculator
        
        Args:
            risk_free_rate: Annual risk-free rate
            benchmark_returns: Benchmark returns series
            window_size: Rolling window size
            cache_enabled: Enable caching of calculations
        """
        self.risk_free_rate = risk_free_rate
        self.benchmark_returns = benchmark_returns
        self.window_size = window_size
        self.cache_enabled = cache_enabled
        self.metrics_cache = {}
        
    def _get_cache_key(self, returns: pd.Series, method_name: str) -> str:
        """Generate cache key based on returns and method"""
        return f"{method_name}_{hash(returns.to_string())}"
        
    def _cache_result(self, key: str, result: Any) -> None:
        """Cache result with TTL"""
        if self.cache_enabled:
            self.metrics_cache[key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
    def _get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result if valid"""
        if not self.cache_enabled:
            return None
            
        if key not in self.metrics_cache:
            return None
            
        cached = self.metrics_cache[key]
        if (datetime.now() - cached['timestamp']).total_seconds() > CACHE_TTL:
            return None
            
        return cached['result']
    
    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio with caching and optimization"""
        try:
            key = self._get_cache_key(returns, 'sharpe_ratio')
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_sharpe_ratio(returns.values, self.risk_free_rate)
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return 0.0

    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown with caching and optimization"""
        try:
            key = self._get_cache_key(returns, 'max_drawdown')
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_max_drawdown((1 + returns).cumprod().values)
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Max Drawdown: {str(e)}")
            return 0.0

    def calculate_basic_metrics(self, returns: pd.Series) -> Dict:
        """Calculate basic performance metrics with caching and optimization"""
        try:
            key = self._get_cache_key(returns, 'basic_metrics')
            cached = self._get_cached_result(key)
            if cached is not None:
                return cached
                
            result = _fast_basic_metrics(returns.values, self.risk_free_rate)
            self._cache_result(key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating basic metrics: {str(e)}")
            return {}
