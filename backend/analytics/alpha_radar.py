from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
import logging
from fastapi import HTTPException
import json
from enum import Enum

logger = logging.getLogger(__name__)

# Define alpha signal thresholds
ALPHA_THRESHOLDS = {
    'institutional': {
        'min_amount': 1000000,  # $1M
        'min_frequency': 0.1,   # 10% of volume
        'time_window': timedelta(days=1)
    },
    'whale': {
        'min_amount': 5000000,  # $5M
        'min_frequency': 0.05,  # 5% of volume
        'time_window': timedelta(days=1)
    },
    '13f': {
        'min_amount': 10000000, # $10M
        'min_frequency': 0.01,  # 1% of volume
        'time_window': timedelta(days=30)
    }
}

class AlphaSource(Enum):
    INSTITUTIONAL = "institutional"
    WHALE = "whale"
    THIRTEEN_F = "13f"

class AlphaSignal(BaseModel):
    timestamp: datetime
    symbol: str
    amount: float
    source: AlphaSource
    confidence: float
    metadata: Dict

class AlphaRadar:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.signal_cache = {}
        self.last_analysis = None
        
    async def analyze_alpha_signals(self, trades: List[Dict]) -> List[AlphaSignal]:
        """
        Analyze trades for alpha signals
        
        Args:
            trades: List of trade data containing:
                - symbol: str
                - amount: float
                - timestamp: datetime
                - source: str (institutional, whale, etc.)
                - metadata: Dict with additional info
            
        Returns:
            List of detected alpha signals
        """
        try:
            signals = []
            current_time = datetime.now()
            
            # Process each trade
            for trade in trades:
                symbol = trade['symbol']
                amount = trade['amount']
                source = trade['source']
                
                # Check if this could be an alpha signal
                if self._is_alpha_signal(trade):
                    # Create alpha signal
                    signal = AlphaSignal(
                        timestamp=current_time,
                        symbol=symbol,
                        amount=amount,
                        source=AlphaSource(source),
                        confidence=self._calculate_confidence(trade),
                        metadata=trade.get('metadata', {})
                    )
                    
                    # Store in Redis
                    await self._store_alpha_signal(signal)
                    
                    signals.append(signal)
                    
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing alpha signals: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing alpha signals: {str(e)}"
            )
            
    def _is_alpha_signal(self, trade: Dict) -> bool:
        """
        Check if trade meets alpha signal criteria
        """
        source = trade['source']
        amount = trade['amount']
        
        # Get thresholds for this source
        thresholds = ALPHA_THRESHOLDS.get(source)
        if not thresholds:
            return False
            
        # Check amount
        if amount < thresholds['min_amount']:
            return False
            
        # Check frequency
        if amount / trade['market_data']['volume'] < thresholds['min_frequency']:
            return False
            
        return True
        
    def _calculate_confidence(self, trade: Dict) -> float:
        """
        Calculate confidence score for alpha signal
        """
        source = trade['source']
        amount = trade['amount']
        volume = trade['market_data']['volume']
        
        # Get thresholds
        thresholds = ALPHA_THRESHOLDS[source]
        
        # Calculate factors
        amount_factor = amount / thresholds['min_amount']
        volume_factor = (amount / volume) / thresholds['min_frequency']
        
        # Combine factors
        confidence = (amount_factor * 0.6 + volume_factor * 0.4)
        
        return float(np.clip(confidence, 0.0, 1.0))
        
    async def _store_alpha_signal(self, signal: AlphaSignal) -> None:
        """
        Store alpha signal in Redis
        """
        try:
            await self.redis_pool.rpush(
                f"alpha_signals:{signal.symbol}:{signal.source.value}",
                json.dumps(signal.dict())
            )
            
            # Set expiration based on source
            time_window = ALPHA_THRESHOLDS[signal.source.value]['time_window']
            await self.redis_pool.expire(
                f"alpha_signals:{signal.symbol}:{signal.source.value}",
                time_window.total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Error storing alpha signal: {str(e)}")
            
    async def get_recent_signals(self, symbol: str, source: str, limit: int = 10) -> List[AlphaSignal]:
        """
        Get recent alpha signals for a symbol and source
        """
        try:
            signals = await self.redis_pool.lrange(
                f"alpha_signals:{symbol}:{source}",
                0,
                limit - 1
            )
            
            return [AlphaSignal.parse_raw(s) for s in signals]
            
        except Exception as e:
            logger.error(f"Error getting alpha signals: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting alpha signals: {str(e)}"
            )
            
    async def get_aggregated_signals(self, symbol: str, time_window: timedelta) -> Dict:
        """
        Get aggregated alpha signals for a symbol
        
        Returns:
            Dict containing:
            - total_amount: Total alpha amount
            - signal_count: Number of signals
            - confidence_score: Combined confidence
            - breakdown: Per-source breakdown
        """
        try:
            current_time = datetime.now()
            start_time = current_time - time_window
            
            # Get signals for each source
            breakdown = {}
            total_amount = 0.0
            total_confidence = 0.0
            
            for source in AlphaSource:
                signals = await self.get_recent_signals(symbol, source.value)
                source_amount = sum(s.amount for s in signals)
                source_confidence = sum(s.confidence for s in signals)
                
                breakdown[source.value] = {
                    'amount': source_amount,
                    'count': len(signals),
                    'confidence': source_confidence / len(signals) if signals else 0.0
                }
                
                total_amount += source_amount
                total_confidence += source_confidence
                
            # Calculate overall confidence
            confidence_score = total_confidence / len(breakdown) if breakdown else 0.0
            
            return {
                'total_amount': total_amount,
                'signal_count': sum(b['count'] for b in breakdown.values()),
                'confidence_score': float(confidence_score),
                'breakdown': breakdown,
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregated signals: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting aggregated signals: {str(e)}"
            )
