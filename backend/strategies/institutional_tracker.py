import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import ccxt
import yfinance as yf
from pydantic import BaseModel
from fastapi import HTTPException

class InstitutionalFlow(BaseModel):
    symbol: str
    volume: float
    direction: str
    timestamp: datetime
    confidence: float

class SmartMoneyTracker:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.volume_threshold = 1000000  # $1M threshold for institutional activity
        self.time_window = timedelta(hours=1)
        self.dark_pool_threshold = 0.05  # 5% of volume considered dark pool
        
    def detect_institutional_activity(self, symbol: str) -> List[InstitutionalFlow]:
        """
        Detect institutional trading activity using volume analysis
        """
        try:
            # Get recent trades
            trades = self.exchange.fetch_trades(symbol)
            
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['volume_usd'] = df['amount'] * df['price']
            
            # Detect large volume spikes
            volume_peaks = find_peaks(df['volume_usd'], height=self.volume_threshold)
            
            # Analyze each peak
            flows = []
            for peak_idx in volume_peaks[0]:
                peak_volume = df['volume_usd'].iloc[peak_idx]
                peak_time = df['timestamp'].iloc[peak_idx]
                
                # Check if dark pool activity
                is_dark_pool = False
                if peak_volume > self.dark_pool_threshold * df['volume_usd'].sum():
                    is_dark_pool = True
                
                # Determine direction based on price movement
                price_change = (df['price'].iloc[peak_idx] - 
                              df['price'].iloc[peak_idx-1]) / 
                              df['price'].iloc[peak_idx-1]
                
                direction = 'buy' if price_change > 0 else 'sell'
                confidence = abs(price_change) * 100
                
                flows.append(InstitutionalFlow(
                    symbol=symbol,
                    volume=peak_volume,
                    direction=direction,
                    timestamp=peak_time,
                    confidence=confidence
                ))
            
            return flows
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting institutional activity: {str(e)}"
            )
    
    def analyze_institutional_trends(self, symbol: str, timeframe: str = '1h') -> Dict:
        """
        Analyze institutional trading trends over time
        """
        try:
            # Get historical data
            df = yf.download(symbol, period='1d', interval=timeframe)
            
            # Calculate volume indicators
            df['volume_ma'] = df['Volume'].rolling(window=20).mean()
            df['volume_std'] = df['Volume'].rolling(window=20).std()
            
            # Detect volume anomalies
            df['volume_zscore'] = (df['Volume'] - df['volume_ma']) / df['volume_std']
            
            # Identify institutional patterns
            patterns = {
                'accumulation': (df['volume_zscore'] > 2).sum(),
                'distribution': (df['volume_zscore'] < -2).sum(),
                'consolidation': ((df['volume_zscore'].abs() < 1).sum() / len(df)) * 100
            }
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'patterns': patterns,
                'last_update': datetime.now().isoformat(),
                'confidence': self._calculate_confidence(patterns)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing institutional trends: {str(e)}"
            )
    
    def _calculate_confidence(self, patterns: Dict) -> float:
        """
        Calculate confidence score based on institutional patterns
        """
        total = sum(patterns.values())
        if total == 0:
            return 0.0
            
        # Weighted confidence calculation
        weights = {
            'accumulation': 0.4,
            'distribution': 0.3,
            'consolidation': 0.3
        }
        
        confidence = sum((patterns[k] * weights[k] for k in patterns.keys())) / total
        return float(np.clip(confidence, 0, 1))
