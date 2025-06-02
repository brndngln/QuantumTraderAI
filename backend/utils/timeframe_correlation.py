from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np
from fastapi import HTTPException
from pydantic import BaseModel
import logging
from scipy.stats import pearsonr

logger = logging.getLogger(__name__)

class Timeframe(Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"

class SignalStrength(Enum):
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8

class TimeframeSignal(BaseModel):
    timeframe: Timeframe
    signal: float
    strength: SignalStrength
    confidence: float

class TimeframeCorrelation:
    def __init__(self):
        self.timeframes = [
            Timeframe.ONE_MINUTE,
            Timeframe.FIVE_MINUTE,
            Timeframe.FIFTEEN_MINUTE,
            Timeframe.ONE_HOUR,
            Timeframe.FOUR_HOUR,
            Timeframe.ONE_DAY
        ]
        self.min_correlation = 0.7
        self.window_size = 24  # hours
        
    async def analyze_correlation(self, symbol: str, signals: List[TimeframeSignal]) -> Dict:
        """
        Analyze signal correlation across multiple timeframes
        
        Args:
            symbol: Trading symbol
            signals: List of signals from different timeframes
            
        Returns:
            Dict containing:
            - correlation_matrix: Correlation between timeframes
            - overall_confidence: Combined confidence score
            - dominant_signal: Most consistent signal
        """
        try:
            # Validate signals
            if not signals:
                raise HTTPException(
                    status_code=400,
                    detail="No signals provided for analysis"
                )
                
            # Create correlation matrix
            correlation_matrix = {}
            for i, signal1 in enumerate(signals):
                for j, signal2 in enumerate(signals):
                    if i != j:
                        corr, _ = pearsonr([signal1.signal], [signal2.signal])
                        correlation_matrix[f"{signal1.timeframe.value}_{signal2.timeframe.value}"] = corr
            
            # Calculate overall confidence
            avg_confidence = np.mean([s.confidence for s in signals])
            
            # Find dominant signal
            dominant_signal = max(
                signals,
                key=lambda x: x.confidence * x.strength.value
            )
            
            # Check for signal agreement
            agreement = sum(
                1 for s in signals
                if abs(s.signal - dominant_signal.signal) < 0.2
            ) / len(signals)
            
            return {
                "correlation_matrix": correlation_matrix,
                "overall_confidence": avg_confidence,
                "dominant_signal": dominant_signal.dict(),
                "signal_agreement": agreement,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timeframe correlation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing timeframe correlation: {str(e)}"
            )
