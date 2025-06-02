from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi import HTTPException
import redis
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

# Define cooldown parameters
COOLDOWN_PARAMS = {
    'default': {
        'min_cooldown': timedelta(minutes=5),
        'max_cooldown': timedelta(hours=1),
        'adrenaline_threshold': 0.8,
        'emotion_decay': 0.95,
        'time_window': timedelta(hours=24)
    }
}

class TradeEvent(BaseModel):
    symbol: str
    timestamp: datetime
    pnl: float
    volatility: float
    emotion_score: float
    cooldown: Optional[timedelta] = None

class TradeCooldown:
    def __init__(self, config: Dict = COOLDOWN_PARAMS['default']):
        self.config = config
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.emotion_history = {}
        self.last_update = None
        
    async def process_trade(self, trade_data: Dict) -> Optional[timedelta]:
        """
        Process a trade and determine cooldown period
        
        Args:
            trade_data: Dict containing:
                - symbol: str
                - pnl: float (profit/loss)
                - volatility: float
                - timestamp: datetime
            
        Returns:
            Optional[timedelta]: Cooldown period or None if no cooldown needed
        """
        try:
            # Create trade event
            event = TradeEvent(
                symbol=trade_data['symbol'],
                timestamp=trade_data['timestamp'],
                pnl=trade_data['pnl'],
                volatility=trade_data['volatility'],
                emotion_score=self._calculate_emotion_score(trade_data)
            )
            
            # Store in Redis
            await self._store_trade_event(event)
            
            # Calculate cooldown
            cooldown = self._calculate_cooldown(event)
            
            if cooldown:
                event.cooldown = cooldown
                await self._store_cooldown(event)
                
            return cooldown
            
        except Exception as e:
            logger.error(f"Error processing trade: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing trade: {str(e)}"
            )
            
    def _calculate_emotion_score(self, trade_data: Dict) -> float:
        """
        Calculate emotion score based on trade characteristics
        """
        pnl = trade_data['pnl']
        volatility = trade_data['volatility']
        
        # Calculate emotional intensity
        intensity = abs(pnl) * volatility
        
        # Apply decay to historical emotion
        symbol = trade_data['symbol']
        if symbol in self.emotion_history:
            historical_intensity = self.emotion_history[symbol]
            intensity = (intensity + historical_intensity * self.config['emotion_decay']) / (1 + self.config['emotion_decay'])
            
        # Normalize to 0-1 range
        emotion_score = float(np.clip(intensity, 0, 1))
        
        # Update emotion history
        self.emotion_history[symbol] = emotion_score
        
        return emotion_score
        
    def _calculate_cooldown(self, event: TradeEvent) -> Optional[timedelta]:
        """
        Calculate appropriate cooldown period
        """
        # Check if adrenaline threshold is exceeded
        if event.emotion_score >= self.config['adrenaline_threshold']:
            # Calculate cooldown based on emotion and volatility
            base_cooldown = self.config['min_cooldown']
            
            # Increase cooldown with emotion and volatility
            emotion_factor = event.emotion_score
            volatility_factor = event.volatility
            
            # Calculate final cooldown
            cooldown = base_cooldown * (1 + emotion_factor) * (1 + volatility_factor)
            
            # Apply bounds
            cooldown = max(self.config['min_cooldown'],
                         min(self.config['max_cooldown'], cooldown))
            
            return cooldown
            
        return None
        
    async def _store_trade_event(self, event: TradeEvent) -> None:
        """
        Store trade event in Redis
        """
        try:
            await self.redis_pool.rpush(
                f"trade_events:{event.symbol}",
                json.dumps(event.dict())
            )
            
            # Set expiration
            await self.redis_pool.expire(
                f"trade_events:{event.symbol}",
                self.config['time_window'].total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Error storing trade event: {str(e)}")
            
    async def _store_cooldown(self, event: TradeEvent) -> None:
        """
        Store cooldown information in Redis
        """
        try:
            cooldown_data = {
                'symbol': event.symbol,
                'cooldown_until': (event.timestamp + event.cooldown).isoformat(),
                'reason': 'High emotional intensity' if event.emotion_score >= self.config['adrenaline_threshold'] else 'Regular cooldown'
            }
            
            await self.redis_pool.set(
                f"cooldown:{event.symbol}",
                json.dumps(cooldown_data)
            )
            
            # Set expiration
            await self.redis_pool.expire(
                f"cooldown:{event.symbol}",
                event.cooldown.total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Error storing cooldown: {str(e)}")
            
    async def check_cooldown(self, symbol: str) -> Optional[timedelta]:
        """
        Check if symbol is in cooldown
        
        Returns:
            Optional[timedelta]: Remaining cooldown time or None if not in cooldown
        """
        try:
            cooldown_data = await self.redis_pool.get(f"cooldown:{symbol}")
            if not cooldown_data:
                return None
                
            cooldown = json.loads(cooldown_data)
            cooldown_until = datetime.fromisoformat(cooldown['cooldown_until'])
            
            if datetime.now() < cooldown_until:
                return cooldown_until - datetime.now()
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error checking cooldown: {str(e)}"
            )
            
    async def get_emotion_history(self, symbol: str, limit: int = 10) -> List[float]:
        """
        Get emotion history for a symbol
        """
        try:
            events = await self.redis_pool.lrange(
                f"trade_events:{symbol}",
                0,
                limit - 1
            )
            
            return [json.loads(e)['emotion_score'] for e in events]
            
        except Exception as e:
            logger.error(f"Error getting emotion history: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting emotion history: {str(e)}"
            )
            
    async def get_cooldown_stats(self, symbol: str) -> Dict:
        """
        Get cooldown statistics for a symbol
        
        Returns:
            Dict containing:
            - total_cooldowns: Number of cooldowns
            - avg_duration: Average cooldown duration
            - max_duration: Maximum cooldown duration
            - current_status: Current cooldown status
        """
        try:
            # Get all cooldown events
            events = await self.redis_pool.lrange(
                f"trade_events:{symbol}",
                0,
                -1
            )
            
            cooldowns = []
            for event in events:
                data = json.loads(event)
                if data.get('cooldown'):
                    cooldowns.append(data['cooldown'])
            
            if not cooldowns:
                return {
                    'total_cooldowns': 0,
                    'avg_duration': 0,
                    'max_duration': 0,
                    'current_status': 'No cooldowns'
                }
            
            # Calculate statistics
            total_cooldowns = len(cooldowns)
            avg_duration = sum(cooldowns) / total_cooldowns
            max_duration = max(cooldowns)
            
            # Check current status
            current_status = 'In cooldown' if await self.check_cooldown(symbol) else 'Active'
            
            return {
                'total_cooldowns': total_cooldowns,
                'avg_duration': float(avg_duration),
                'max_duration': float(max_duration),
                'current_status': current_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cooldown stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting cooldown stats: {str(e)}"
            )
