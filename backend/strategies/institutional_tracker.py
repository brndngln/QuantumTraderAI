from typing import Dict
import numpy as np
from fastapi import HTTPException
import pandas as pd

class InstitutionalTracker:
    def __init__(self):
        self.patterns = {
            'block_trade': self.detect_block_trade,
            'institutional_flow': self.detect_institutional_flow,
            'dark_pool': self.detect_dark_pool_activity
        }
        self.weights = {
            'block_trade': 0.4,
            'institutional_flow': 0.3,
            'dark_pool': 0.3
        }

    def detect_block_trade(self, data: pd.DataFrame) -> float:
        """
        Detect block trades (large institutional trades)
        """
        try:
            # Calculate volume thresholds
            avg_volume = data['Volume'].mean()
            threshold = avg_volume * 5  # 5x average volume
            
            # Find potential block trades
            block_trades = data[data['Volume'] > threshold]
            
            # Calculate score based on volume and price impact
            score = 0
            for _, trade in block_trades.iterrows():
                price_impact = abs(trade['Close'] - trade['Open']) / trade['Open']
                score += trade['Volume'] * price_impact
            
            return float(score / len(data)) if len(data) > 0 else 0
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting block trades: {str(e)}"
            )

    def detect_institutional_flow(self, data: pd.DataFrame) -> float:
        """
        Detect institutional flow patterns
        """
        try:
            # Calculate volume profile
            volume_profile = data['Volume'].rolling(window=20).mean()
            
            # Calculate price momentum
            price_momentum = data['Close'].pct_change().rolling(window=20).mean()
            
            # Calculate correlation between volume and price
            correlation = volume_profile.corr(price_momentum)
            
            # Calculate score based on correlation strength
            score = abs(correlation) * 100
            
            return float(score)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting institutional flow: {str(e)}"
            )

    def detect_dark_pool_activity(self, data: pd.DataFrame) -> float:
        """
        Detect dark pool activity patterns
        """
        try:
            # Calculate volume anomalies
            avg_volume = data['Volume'].mean()
            std_volume = data['Volume'].std()
            
            # Detect large volume spikes
            spikes = data[data['Volume'] > (avg_volume + 3 * std_volume)]
            
            # Calculate price impact of spikes
            price_impact = spikes['Close'].pct_change().abs().mean()
            
            # Calculate score based on frequency and impact
            score = len(spikes) * price_impact * 100
            
            return float(score)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting dark pool activity: {str(e)}"
            )

    def analyze_institutional_trends(self, symbol: str, timeframe: str = '1h') -> Dict:
        """
        Analyze institutional trading trends over time
        """
        try:
            # Get data for the specified timeframe
            data = self.get_data(symbol, timeframe)
            
            # Analyze each pattern
            patterns = {}
            for name, detector in self.patterns.items():
                patterns[name] = detector(data)
            
            # Calculate weighted confidence score
            total = sum(self.weights.values())
            confidence = sum((patterns[k] * self.weights[k] for k in patterns.keys())) / total
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'confidence': float(np.clip(confidence, 0, 1)),
                'patterns': patterns
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing institutional trends: {str(e)}"
            )

    def get_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Get historical data for analysis
        """
        try:
            # This would typically fetch data from an API
            # For now, return a mock DataFrame
            return pd.DataFrame({
                'Open': np.random.random(100) * 100,
                'Close': np.random.random(100) * 100,
                'Volume': np.random.random(100) * 100000
            })
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching data: {str(e)}"
            )
