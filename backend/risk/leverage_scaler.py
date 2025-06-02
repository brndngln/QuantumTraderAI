from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from fastapi import HTTPException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define leverage tiers based on performance and risk
LEVERAGE_TIERS = {
    'conservative': (1.0, 2.0),
    'moderate': (2.0, 3.0),
    'aggressive': (3.0, 5.0)
}

# Define buffer thresholds
BUFFER_THRESHOLDS = {
    'low': 0.1,  # 10% buffer
    'medium': 0.2,  # 20% buffer
    'high': 0.3   # 30% buffer
}

class LeverageScaler:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'performance': [],
            'risk': [],
            'leverage': []
        }

    def calculate_leverage(self, volatility: float, performance: float, vault_buffer: float) -> Tuple[float, Dict]:
        """
        Calculate optimal leverage based on multiple factors
        
        Args:
            volatility: Current market volatility
            performance: Strategy performance score
            vault_buffer: Available vault buffer percentage
            
        Returns:
            Tuple containing:
            - float: Calculated leverage
            - Dict: Leverage breakdown and factors
        """
        try:
            # Base leverage is inverse of volatility
            base_leverage = 1 / volatility
            
            # Adjust based on performance
            performance_factor = min(1.0, max(0.5, performance))
            
            # Adjust based on vault buffer
            buffer_factor = self._calculate_buffer_factor(vault_buffer)
            
            # Combine factors
            adjusted_leverage = base_leverage * performance_factor * buffer_factor
            
            # Apply tier-based limits
            leverage_tier = self._determine_leverage_tier(performance)
            min_leverage, max_leverage = LEVERAGE_TIERS[leverage_tier]
            
            # Apply final bounds
            leverage = max(min_leverage, min(max_leverage, adjusted_leverage))
            
            # Log and return breakdown
            breakdown = {
                'base_leverage': base_leverage,
                'performance_factor': performance_factor,
                'buffer_factor': buffer_factor,
                'leverage_tier': leverage_tier,
                'final_leverage': leverage
            }
            
            logger.info(f"Leverage calculation: {breakdown}")
            
            return float(leverage), breakdown
            
        except Exception as e:
            logger.error(f"Error calculating leverage: {str(e)}")
            return 1.0, {"error": str(e)}  # Default to 1x leverage if error occurs

    def update_performance_metrics(self, performance_data: List[Dict]) -> Dict:
        """
        Update performance metrics and calculate current performance score
        
        Args:
            performance_data: List of performance metrics
            
        Returns:
            Dict containing:
            - performance_score: Current performance score
            - metrics_updated: Boolean flag
            - trend: Performance trend
        """
        try:
            # Add new data to metrics
            self.metrics['performance'].extend(performance_data)
            
            # Calculate performance score
            scores = []
            for data in self.metrics['performance'][-10:]:  # Last 10 periods
                score = data.get('returns', 0.0) * data.get('sharpe', 1.0)
                scores.append(score)
            
            # Calculate weighted average
            weights = np.linspace(0.1, 1.0, len(scores))
            performance_score = float(np.average(scores, weights=weights))
            
            # Calculate trend
            if len(self.metrics['performance']) > 20:
                df = pd.DataFrame(self.metrics['performance'][-20:])
                trend = np.polyfit(range(len(df)), df['returns'], 1)[0]
            else:
                trend = 0.0
            
            return {
                'performance_score': performance_score,
                'metrics_updated': True,
                'trend': float(trend)
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating performance: {str(e)}"
            )
        """
        Update performance metrics and calculate current performance score
        """
        try:
            # Add new data to metrics
            self.metrics['performance'].extend(performance_data)
            
            # Calculate performance score
            scores = []
            for data in self.metrics['performance'][-10:]:  # Last 10 periods
                score = data.get('returns', 0.0) * data.get('sharpe', 1.0)
                scores.append(score)
            
            # Calculate weighted average
            weights = np.linspace(0.1, 1.0, len(scores))
            performance_score = float(np.average(scores, weights=weights))
            
            return {
                'performance_score': performance_score,
                'metrics_updated': True
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating performance: {str(e)}"
            )

    def update_risk_metrics(self, risk_data: List[Dict]) -> Dict:
        """
        Update risk metrics and calculate current risk score
        """
        try:
            # Add new data to metrics
            self.metrics['risk'].extend(risk_data)
            
            # Calculate risk score
            scores = []
            for data in self.metrics['risk'][-10:]:  # Last 10 periods
                score = data.get('volatility', 0.0) * data.get('drawdown', 1.0)
                scores.append(score)
            
            # Calculate weighted average
            weights = np.linspace(0.1, 1.0, len(scores))
            risk_score = float(np.average(scores, weights=weights))
            
            return {
                'risk_score': risk_score,
                'metrics_updated': True
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating risk metrics: {str(e)}"
            )

    def get_current_metrics(self) -> Dict:
        """
        Get current performance and risk metrics
        """
        try:
            # Calculate averages for recent periods
            metrics = {
                'performance': {
                    'avg_returns': float(np.mean([
                        d.get('returns', 0.0)
                        for d in self.metrics['performance'][-10:]
                    ])),
                    'avg_sharpe': float(np.mean([
                        d.get('sharpe', 0.0)
                        for d in self.metrics['performance'][-10:]
                    ]))
                },
                'risk': {
                    'avg_volatility': float(np.mean([
                        d.get('volatility', 0.0)
                        for d in self.metrics['risk'][-10:]
                    ])),
                    'avg_drawdown': float(np.mean([
                        d.get('drawdown', 0.0)
                        for d in self.metrics['risk'][-10:]
                    ]))
                },
                'leverage': {
                    'current': float(np.mean([
                        d.get('leverage', 1.0)
                        for d in self.metrics['leverage'][-10:]
                    ]))
                }
            }
            
            return metrics
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting risk metrics: {str(e)}"
            )

    def optimize_leverage(self, current_leverage: float) -> Dict:
        """
        Optimize leverage based on current metrics
        """
        try:
            # Get current metrics
            metrics = self.get_current_metrics()
            
            # Calculate optimal leverage
            optimal_leverage = self.calculate_leverage(
                metrics['risk']['avg_volatility'],
                metrics['performance']['avg_sharpe']
            )
            
            # Calculate adjustment
            adjustment = optimal_leverage / current_leverage
            
            return {
                'optimal_leverage': optimal_leverage,
                'adjustment': adjustment,
                'metrics': metrics
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error optimizing leverage: {str(e)}"
            )
