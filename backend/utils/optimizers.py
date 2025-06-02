from typing import List, Optional, Dict, Any
import numpy as np
from scipy.stats import norm
import logging
from enum import Enum

class PatternType(Enum):
    REBOUND = "rebound"
    STREAK = "streak"
    VOLATILITY_SPIKE = "volatility_spike"
    PERFORMANCE_DROPOFF = "performance_dropoff"

class PatternRecognizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_thresholds = {
            PatternType.REBOUND: 0.8,
            PatternType.STREAK: 3,
            PatternType.VOLATILITY_SPIKE: 2.0,
            PatternType.PERFORMANCE_DROPOFF: 0.1
        }
    
    def update_patterns(self, performance_data: List[float], pattern_history: List[str]) -> List[str]:
        """
        Update pattern history based on new performance data
        """
        try:
            if len(performance_data) < 3:
                return pattern_history
                
            # Check for patterns
            patterns = []
            
            # Check for rebound pattern
            if self._detect_rebound(performance_data):
                patterns.append(PatternType.REBOUND.value)
                
            # Check for streak pattern
            if self._detect_streak(performance_data):
                patterns.append(PatternType.STREAK.value)
                
            # Check for volatility spike
            if self._detect_volatility_spike(performance_data):
                patterns.append(PatternType.VOLATILITY_SPIKE.value)
                
            # Check for performance dropoff
            if self._detect_performance_dropoff(performance_data):
                patterns.append(PatternType.PERFORMANCE_DROPOFF.value)
                
            # Update pattern history
            pattern_history.extend(patterns)
            pattern_history = pattern_history[-10:]  # Keep last 10 patterns
            
            return pattern_history
            
        except Exception as e:
            self.logger.error(f"Error updating patterns: {str(e)}")
            return pattern_history
    
    def _detect_rebound(self, data: List[float]) -> bool:
        """
        Detect rebound pattern (alternating gains and losses)
        """
        if len(data) < 3:
            return False
            
        changes = [data[i] - data[i-1] for i in range(1, len(data))]
        signs = [np.sign(change) for change in changes]
        
        # Check for alternating signs
        return any(signs[i] != signs[i+1] for i in range(len(signs)-1))
    
    def _detect_streak(self, data: List[float]) -> bool:
        """
        Detect streak pattern (consecutive gains or losses)
        """
        if len(data) < 3:
            return False
            
        changes = [data[i] - data[i-1] for i in range(1, len(data))]
        signs = [np.sign(change) for change in changes]
        
        # Check for streak
        return any(signs[i] == signs[i+1] for i in range(len(signs)-1))
    
    def _detect_volatility_spike(self, data: List[float]) -> bool:
        """
        Detect volatility spike
        """
        if len(data) < 3:
            return False
            
        returns = [data[i] / data[i-1] - 1 for i in range(1, len(data))]
        std = np.std(returns)
        
        return std > self.pattern_thresholds[PatternType.VOLATILITY_SPIKE]
    
    def _detect_performance_dropoff(self, data: List[float]) -> bool:
        """
        Detect performance dropoff
        """
        if len(data) < 3:
            return False
            
        recent_performance = np.mean(data[-3:])
        overall_performance = np.mean(data)
        
        return (overall_performance - recent_performance) / overall_performance > \
               self.pattern_thresholds[PatternType.PERFORMANCE_DROPOFF]

class PerformanceOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimization_factors = {
            'volatility': 0.3,
            'performance': 0.4,
            'pattern': 0.3
        }
    
    def get_optimal_duration(self, performance_data: List[float], current_duration: int) -> int:
        """
        Calculate optimal cooldown duration based on performance metrics
        """
        try:
            if len(performance_data) < 3:
                return current_duration
                
            # Calculate performance metrics
            volatility = self._calculate_volatility(performance_data)
            performance_score = self._calculate_performance_score(performance_data)
            pattern_score = self._calculate_pattern_score(performance_data)
            
            # Calculate weighted score
            score = (
                self.optimization_factors['volatility'] * volatility +
                self.optimization_factors['performance'] * performance_score +
                self.optimization_factors['pattern'] * pattern_score
            )
            
            # Adjust duration based on score
            adjustment_factor = 1 + (score - 0.5) * 0.5  # Scale between 0.75 and 1.25
            optimal_duration = int(current_duration * adjustment_factor)
            
            return max(1, min(3600, optimal_duration))  # Clamp between 1s and 1h
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal duration: {str(e)}")
            return current_duration
    
    def _calculate_volatility(self, data: List[float]) -> float:
        """
        Calculate normalized volatility score
        """
        returns = [data[i] / data[i-1] - 1 for i in range(1, len(data))]
        std = np.std(returns)
        return norm.cdf(std)  # Normalize using standard normal CDF
    
    def _calculate_performance_score(self, data: List[float]) -> float:
        """
        Calculate normalized performance score
        """
        returns = [data[i] / data[i-1] - 1 for i in range(1, len(data))]
        mean_return = np.mean(returns)
        return norm.cdf(mean_return)  # Normalize using standard normal CDF
    
    def _calculate_pattern_score(self, data: List[float]) -> float:
        """
        Calculate pattern-based score
        """
        changes = [data[i] - data[i-1] for i in range(1, len(data))]
        signs = [np.sign(change) for change in changes]
        
        # Score based on pattern consistency
        score = 1 - sum(1 for i in range(len(signs)-1) if signs[i] != signs[i+1]) / (len(signs)-1)
        return score

class RetryManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.retry_delays = [30, 60, 120]  # Default retry delays in seconds
        self.max_retries = 3
    
    def get_retry_delay(self, attempt: int) -> int:
        """
        Get delay for retry attempt
        """
        if attempt >= len(self.retry_delays):
            return self.retry_delays[-1]
        return self.retry_delays[attempt]
    
    def should_retry(self, attempt: int) -> bool:
        """
        Determine if retry should be attempted
        """
        return attempt < self.max_retries
    
    async def retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """
        Retry operation with exponential backoff
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                result = await operation(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"Operation failed on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.get_retry_delay(attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                attempt += 1
        raise Exception("Max retries exceeded")
