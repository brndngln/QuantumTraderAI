import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from enum import Enum

class PnLThreshold(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CooldownConfig(BaseModel):
    pnl_threshold: PnLThreshold
    cooldown_minutes: int
    emotional_intensity: float
    last_trigger: Optional[datetime] = None

class CooldownManager:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.default_config = {
            PnLThreshold.LOW: CooldownConfig(
                pnl_threshold=PnLThreshold.LOW,
                cooldown_minutes=15,
                emotional_intensity=0.5
            ),
            PnLThreshold.MEDIUM: CooldownConfig(
                pnl_threshold=PnLThreshold.MEDIUM,
                cooldown_minutes=30,
                emotional_intensity=0.7
            ),
            PnLThreshold.HIGH: CooldownConfig(
                pnl_threshold=PnLThreshold.HIGH,
                cooldown_minutes=60,
                emotional_intensity=0.9
            )
        }
        
    async def check_cooldown(self, pnl: float, strategy_id: str) -> bool:
        """
        Check if strategy is in cooldown period
        """
        try:
            # Get current config
            config = await self.get_config(strategy_id)
            
            # Calculate emotional intensity
            emotional_intensity = self.calculate_emotional_intensity(pnl)
            
            # Update config if intensity is high
            if emotional_intensity > config.emotional_intensity:
                config = self.get_cooldown_config(emotional_intensity)
                await self.set_config(strategy_id, config)
            
            # Check cooldown period
            if config.last_trigger:
                cooldown_end = config.last_trigger + timedelta(minutes=config.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    return True
            
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking cooldown: {str(e)}"
            )
    
    async def trigger_cooldown(self, strategy_id: str, pnl: float) -> None:
        """
        Trigger cooldown period for strategy
        """
        try:
            # Get current config
            config = await self.get_config(strategy_id)
            
            # Calculate emotional intensity
            emotional_intensity = self.calculate_emotional_intensity(pnl)
            
            # Update config if intensity is high
            if emotional_intensity > config.emotional_intensity:
                config = self.get_cooldown_config(emotional_intensity)
            
            # Update last trigger time
            config.last_trigger = datetime.now()
            
            # Store in Redis
            await self.set_config(strategy_id, config)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error triggering cooldown: {str(e)}"
            )
    
    def calculate_emotional_intensity(self, pnl: float) -> float:
        """
        Calculate emotional intensity based on PnL
        """
        abs_pnl = abs(pnl)
        
        # Simple intensity calculation
        if abs_pnl < 1000:
            return 0.3
        elif abs_pnl < 5000:
            return 0.6
        else:
            return 0.9
    
    def get_cooldown_config(self, emotional_intensity: float) -> CooldownConfig:
        """
        Get appropriate cooldown config based on intensity
        """
        if emotional_intensity < 0.5:
            return self.default_config[PnLThreshold.LOW]
        elif emotional_intensity < 0.8:
            return self.default_config[PnLThreshold.MEDIUM]
        else:
            return self.default_config[PnLThreshold.HIGH]
    
    async def get_config(self, strategy_id: str) -> CooldownConfig:
        """
        Get cooldown config for strategy
        """
        try:
            data = await self.redis_pool.get(f"cooldown_config:{strategy_id}")
            if data:
                return CooldownConfig.parse_raw(data)
            return self.default_config[PnLThreshold.LOW]
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting cooldown config: {str(e)}"
            )
    
    async def set_config(self, strategy_id: str, config: CooldownConfig) -> None:
        """
        Set cooldown config for strategy
        """
        try:
            await self.redis_pool.set(
                f"cooldown_config:{strategy_id}",
                config.json()
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error setting cooldown config: {str(e)}"
            )
    
    async def reset_cooldown(self, strategy_id: str) -> None:
        """
        Reset cooldown for strategy
        """
        try:
            await self.redis_pool.delete(f"cooldown_config:{strategy_id}")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error resetting cooldown: {str(e)}"
            )
