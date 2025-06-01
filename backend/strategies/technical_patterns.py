import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from ta import trend, momentum, volatility
from scipy.signal import find_peaks
from pydantic import BaseModel
from fastapi import HTTPException

class PatternType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class PatternStrength(Enum):
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 1.0

class TechnicalPattern(BaseModel):
    pattern_type: PatternType
    strength: PatternStrength
    confidence: float
    timestamp: datetime
    indicators: Dict

class TechnicalPatternAI:
    def __init__(self):
        self.patterns = {
            'bullish': ['golden_cross', 'double_bottom', 'head_shoulders_bottom'],
            'bearish': ['death_cross', 'double_top', 'head_shoulders_top'],
            'neutral': ['triangle', 'rectangle', 'wedge']
        }
        self.confidence_threshold = 0.7
        
    def detect_patterns(self, symbol: str, data: pd.DataFrame) -> List[TechnicalPattern]:
        """
        Detect technical patterns in price data
        """
        try:
            patterns = []
            
            # Calculate technical indicators
            data['sma_20'] = trend.sma_indicator(data['Close'], window=20)
            data['sma_50'] = trend.sma_indicator(data['Close'], window=50)
            data['rsi'] = momentum.rsi(data['Close'])
            data['macd'] = trend.macd(data['Close'])
            data['bb_upper'] = volatility.bollinger_hband(data['Close'])
            data['bb_lower'] = volatility.bollinger_lband(data['Close'])
            
            # Detect bullish patterns
            if self._detect_golden_cross(data):
                patterns.append(self._create_pattern(
                    PatternType.BULLISH,
                    PatternStrength.STRONG,
                    self._calculate_confidence(data),
                    data
                ))
            
            if self._detect_double_bottom(data):
                patterns.append(self._create_pattern(
                    PatternType.BULLISH,
                    PatternStrength.MODERATE,
                    self._calculate_confidence(data),
                    data
                ))
            
            # Detect bearish patterns
            if self._detect_death_cross(data):
                patterns.append(self._create_pattern(
                    PatternType.BEARISH,
                    PatternStrength.STRONG,
                    self._calculate_confidence(data),
                    data
                ))
            
            if self._detect_double_top(data):
                patterns.append(self._create_pattern(
                    PatternType.BEARISH,
                    PatternStrength.MODERATE,
                    self._calculate_confidence(data),
                    data
                ))
            
            return patterns
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting technical patterns: {str(e)}"
            )
    
    def _detect_golden_cross(self, data: pd.DataFrame) -> bool:
        """
        Detect Golden Cross pattern
        """
        last_20 = data['sma_20'].iloc[-1]
        last_50 = data['sma_50'].iloc[-1]
        prev_20 = data['sma_20'].iloc[-2]
        prev_50 = data['sma_50'].iloc[-2]
        
        return (last_20 > last_50 and prev_20 <= prev_50)
    
    def _detect_death_cross(self, data: pd.DataFrame) -> bool:
        """
        Detect Death Cross pattern
        """
        last_20 = data['sma_20'].iloc[-1]
        last_50 = data['sma_50'].iloc[-1]
        prev_20 = data['sma_20'].iloc[-2]
        prev_50 = data['sma_50'].iloc[-2]
        
        return (last_20 < last_50 and prev_20 >= prev_50)
    
    def _detect_double_bottom(self, data: pd.DataFrame) -> bool:
        """
        Detect Double Bottom pattern
        """
        lows = find_peaks(-data['Low'], distance=20)[0]
        if len(lows) >= 2:
            bottom1 = data['Low'].iloc[lows[-1]]
            bottom2 = data['Low'].iloc[lows[-2]]
            return abs(bottom1 - bottom2) / bottom1 < 0.01
        return False
    
    def _detect_double_top(self, data: pd.DataFrame) -> bool:
        """
        Detect Double Top pattern
        """
        highs = find_peaks(data['High'], distance=20)[0]
        if len(highs) >= 2:
            top1 = data['High'].iloc[highs[-1]]
            top2 = data['High'].iloc[highs[-2]]
            return abs(top1 - top2) / top1 < 0.01
        return False
    
    def _calculate_confidence(self, data: pd.DataFrame) -> float:
        """
        Calculate pattern confidence based on multiple indicators
        """
        indicators = {
            'rsi': self._rsi_confidence(data['rsi'].iloc[-1]),
            'volume': self._volume_confidence(data),
            'macd': self._macd_confidence(data['macd'].iloc[-1]),
            'bollinger': self._bollinger_confidence(data)
        }
        
        return float(np.mean(list(indicators.values())))
    
    def _rsi_confidence(self, rsi: float) -> float:
        """
        Calculate confidence based on RSI value
        """
        if rsi < 30:
            return 0.9
        elif rsi > 70:
            return 0.1
        return 0.5
    
    def _volume_confidence(self, data: pd.DataFrame) -> float:
        """
        Calculate confidence based on volume patterns
        """
        last_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
        
        if last_volume > 1.5 * avg_volume:
            return 0.9
        elif last_volume < 0.5 * avg_volume:
            return 0.1
        return 0.5
    
    def _macd_confidence(self, macd: float) -> float:
        """
        Calculate confidence based on MACD value
        """
        if macd > 0:
            return 0.8
        elif macd < 0:
            return 0.2
        return 0.5
    
    def _bollinger_confidence(self, data: pd.DataFrame) -> float:
        """
        Calculate confidence based on Bollinger Bands
        """
        last_close = data['Close'].iloc[-1]
        upper = data['bb_upper'].iloc[-1]
        lower = data['bb_lower'].iloc[-1]
        
        if last_close > upper:
            return 0.2
        elif last_close < lower:
            return 0.8
        return 0.5
    
    def _create_pattern(self, 
                       pattern_type: PatternType, 
                       strength: PatternStrength, 
                       confidence: float, 
                       data: pd.DataFrame) -> TechnicalPattern:
        """
        Create a TechnicalPattern object
        """
        return TechnicalPattern(
            pattern_type=pattern_type,
            strength=strength,
            confidence=confidence,
            timestamp=datetime.now(),
            indicators={
                'rsi': data['rsi'].iloc[-1],
                'macd': data['macd'].iloc[-1],
                'volume': data['Volume'].iloc[-1],
                'sma_20': data['sma_20'].iloc[-1],
                'sma_50': data['sma_50'].iloc[-1]
            }
        )
