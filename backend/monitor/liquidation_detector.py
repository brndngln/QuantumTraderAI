from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
from scipy.stats import zscore
import redis
from redis import asyncio as aioredis
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Define liquidation detection parameters
LIQUIDATION_THRESHOLDS = {
    'price_drop': 0.05,  # 5% price drop
    'volume_spike': 3.0,  # 3x normal volume
    'time_window': timedelta(minutes=5),  # 5 minute window
    'cluster_threshold': 3  # Minimum number of liquidations
}

class LiquidationEvent(BaseModel):
    timestamp: datetime
    price: float
    volume: float
    side: str  # 'long' or 'short'
    symbol: str
    confidence: float

class LiquidationDetector:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.liquidation_clusters = {}
        self.current_window = None
        
    async def process_trade(self, trade_data: Dict) -> Optional[LiquidationEvent]:
        """
        Process a trade and detect potential liquidations
        
        Args:
            trade_data: Dict containing:
                - symbol: str
                - price: float
                - volume: float
                - timestamp: datetime
                - side: str ('buy' or 'sell')
                - market_data: Dict with market conditions
            
        Returns:
            LiquidationEvent if a liquidation is detected
        """
        try:
            # Create trade event
            event = LiquidationEvent(
                timestamp=trade_data['timestamp'],
                price=trade_data['price'],
                volume=trade_data['volume'],
                side='long' if trade_data['side'] == 'sell' else 'short',
                symbol=trade_data['symbol'],
                confidence=0.0  # Will be calculated
            )
            
            # Check if this could be a liquidation
            if self._is_potential_liquidation(trade_data):
                # Update liquidation cluster
                self._update_liquidation_cluster(event)
                
                # Calculate confidence
                event.confidence = self._calculate_confidence(event)
                
                # Store in Redis
                await self._store_liquidation_event(event)
                
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing trade: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing trade: {str(e)}"
            )
            
    def _is_potential_liquidation(self, trade_data: Dict) -> bool:
        """
        Check if trade could be a liquidation
        """
        # Check price drop
        if trade_data['price'] < trade_data['market_data']['last_price'] * (1 - LIQUIDATION_THRESHOLDS['price_drop']):
            return True
            
        # Check volume spike
        if trade_data['volume'] > trade_data['market_data']['avg_volume'] * LIQUIDATION_THRESHOLDS['volume_spike']:
            return True
            
        return False
        
    def _update_liquidation_cluster(self, event: LiquidationEvent) -> None:
        """
        Update liquidation cluster tracking
        """
        symbol = event.symbol
        current_time = event.timestamp
        
        # Initialize cluster if needed
        if symbol not in self.liquidation_clusters:
            self.liquidation_clusters[symbol] = []
            
        # Remove old events
        self.liquidation_clusters[symbol] = [
            e for e in self.liquidation_clusters[symbol]
            if current_time - e.timestamp < LIQUIDATION_THRESHOLDS['time_window']
        ]
        
        # Add current event
        self.liquidation_clusters[symbol].append(event)
        
    def _calculate_confidence(self, event: LiquidationEvent) -> float:
        """
        Calculate confidence score for liquidation event
        """
        # Get cluster events
        cluster = self.liquidation_clusters.get(event.symbol, [])
        
        # Calculate factors
        price_drop_factor = self._calculate_price_drop_factor(event)
        volume_factor = self._calculate_volume_factor(event)
        cluster_factor = self._calculate_cluster_factor(cluster)
        
        # Combine factors
        confidence = (
            price_drop_factor * 0.4 +
            volume_factor * 0.4 +
            cluster_factor * 0.2
        )
        
        return float(np.clip(confidence, 0.0, 1.0))
        
    def _calculate_price_drop_factor(self, event: LiquidationEvent) -> float:
        """
        Calculate price drop factor
        """
        price_drop = (event.price - event.market_data['last_price']) / event.market_data['last_price']
        return float(np.clip(abs(price_drop) / LIQUIDATION_THRESHOLDS['price_drop'], 0, 1))
        
    def _calculate_volume_factor(self, event: LiquidationEvent) -> float:
        """
        Calculate volume spike factor
        """
        volume_spike = event.volume / event.market_data['avg_volume']
        return float(np.clip(volume_spike / LIQUIDATION_THRESHOLDS['volume_spike'], 0, 1))
        
    def _calculate_cluster_factor(self, cluster: List[LiquidationEvent]) -> float:
        """
        Calculate cluster factor based on number of events
        """
        if len(cluster) < LIQUIDATION_THRESHOLDS['cluster_threshold']:
            return 0.0
            
        # Calculate cluster strength
        strength = len(cluster) - LIQUIDATION_THRESHOLDS['cluster_threshold']
        max_strength = 10  # Maximum cluster size we consider
        return float(np.clip(strength / max_strength, 0, 1))
        
    async def _store_liquidation_event(self, event: LiquidationEvent) -> None:
        """
        Store liquidation event in Redis
        """
        try:
            await self.redis_pool.rpush(
                f"liquidations:{event.symbol}",
                json.dumps(event.dict())
            )
            
            # Set expiration
            await self.redis_pool.expire(
                f"liquidations:{event.symbol}",
                LIQUIDATION_THRESHOLDS['time_window'].total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Error storing liquidation event: {str(e)}")
            
    async def get_recent_liquidations(self, symbol: str, limit: int = 10) -> List[LiquidationEvent]:
        """
        Get recent liquidation events for a symbol
        """
        try:
            events = await self.redis_pool.lrange(
                f"liquidations:{symbol}",
                0,
                limit - 1
            )
            
            return [LiquidationEvent.parse_raw(e) for e in events]
            
        except Exception as e:
            logger.error(f"Error getting liquidations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting liquidations: {str(e)}"
            )
