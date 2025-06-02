from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi import HTTPException
import json
from scipy.stats import norm

logger = logging.getLogger(__name__)

# Define market parameters
MARKET_PARAMS = {
    'default': {
        'volatility': 0.02,  # 2% daily volatility
        'trend': 0.0,  # No trend by default
        'mean_reversion': 0.5,  # 50% mean reversion
        'volume_profile': [0.1, 0.15, 0.2, 0.25, 0.3],  # Volume distribution
        'noise_level': 0.01  # 1% noise
    }
}

class MarketState(BaseModel):
    price: float
    volume: float
    timestamp: datetime
    volatility: float
    trend: float
    mean: float

class SyntheticMarket:
    def __init__(self, config: Dict = MARKET_PARAMS['default']):
        self.config = config
        self.current_state = None
        self.history = []
        self.last_update = None
        
    def generate_next_state(self, current_price: float) -> MarketState:
        """
        Generate next market state
        
        Args:
            current_price: Current market price
            
        Returns:
            MarketState with updated values
        """
        try:
            # Calculate time-based adjustments
            time_diff = (datetime.now() - self.last_update).total_seconds() / 3600
            
            # Generate price movement
            price_movement = self._generate_price_movement(time_diff)
            new_price = current_price * (1 + price_movement)
            
            # Generate volume
            volume = self._generate_volume()
            
            # Update state
            state = MarketState(
                price=new_price,
                volume=volume,
                timestamp=datetime.now(),
                volatility=self.config['volatility'],
                trend=self.config['trend'],
                mean=current_price
            )
            
            self.current_state = state
            self.history.append(state)
            self.last_update = datetime.now()
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating market state: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating market state: {str(e)}"
            )
            
    def _generate_price_movement(self, time_diff: float) -> float:
        """
        Generate price movement based on time and market conditions
        """
        # Calculate mean reversion force
        mean_reversion = self.config['mean_reversion']
        if self.current_state:
            mean_reversion_force = mean_reversion * (self.current_state.mean - self.current_state.price)
        else:
            mean_reversion_force = 0.0
            
        # Calculate trend component
        trend_component = self.config['trend'] * time_diff
        
        # Generate random noise
        volatility = self.config['volatility'] * np.sqrt(time_diff)
        noise = norm.rvs(scale=volatility)
        
        # Combine components
        total_movement = (
            mean_reversion_force +
            trend_component +
            noise
        )
        
        return float(total_movement)
        
    def _generate_volume(self) -> float:
        """
        Generate volume based on time of day and profile
        """
        # Get current time of day
        current_time = datetime.now().time()
        hour = current_time.hour + current_time.minute / 60
        
        # Normalize hour to 0-1 range
        normalized_hour = hour / 24
        
        # Get volume profile
        profile = self.config['volume_profile']
        
        # Interpolate volume based on time
        volume = np.interp(normalized_hour, np.linspace(0, 1, len(profile)), profile)
        
        # Add noise
        noise = self.config['noise_level'] * np.random.randn()
        
        return float(np.clip(volume + noise, 0, 1))
        
    def generate_market_series(self, n_periods: int, initial_price: float) -> List[MarketState]:
        """
        Generate a series of market states
        
        Args:
            n_periods: Number of periods to generate
            initial_price: Starting price
            
        Returns:
            List of MarketState objects
        """
        try:
            states = []
            current_price = initial_price
            
            for _ in range(n_periods):
                state = self.generate_next_state(current_price)
                states.append(state)
                current_price = state.price
                
            return states
            
        except Exception as e:
            logger.error(f"Error generating market series: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating market series: {str(e)}"
            )
            
    def get_market_statistics(self, window: int = 20) -> Dict:
        """
        Get market statistics for recent period
        
        Args:
            window: Number of periods to analyze
            
        Returns:
            Dict containing:
            - volatility: Recent volatility
            - trend: Recent trend
            - volume: Average volume
            - correlation: Price-volume correlation
        """
        try:
            if len(self.history) < window:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough history available"
                )
                
            recent_states = self.history[-window:]
            
            # Convert to DataFrame
            df = pd.DataFrame([s.dict() for s in recent_states])
            
            # Calculate statistics
            returns = df['price'].pct_change()
            volatility = returns.std()
            trend = returns.mean()
            avg_volume = df['volume'].mean()
            correlation = returns.corr(df['volume'])
            
            return {
                'volatility': float(volatility),
                'trend': float(trend),
                'avg_volume': float(avg_volume),
                'correlation': float(correlation),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating market stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating market stats: {str(e)}"
            )
            
    def save_market_data(self, filename: str) -> None:
        """
        Save market data to file
        """
        try:
            data = [s.dict() for s in self.history]
            with open(filename, 'w') as f:
                json.dump(data, f, default=str)
                
        except Exception as e:
            logger.error(f"Error saving market data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error saving market data: {str(e)}"
            )
            
    def load_market_data(self, filename: str) -> None:
        """
        Load market data from file
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.history = [MarketState(**d) for d in data]
                self.current_state = self.history[-1] if self.history else None
                
        except Exception as e:
            logger.error(f"Error loading market data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading market data: {str(e)}"
            )
