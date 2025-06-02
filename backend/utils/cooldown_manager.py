import json
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException
from pydantic import BaseModel
from redis import asyncio as aioredis
from datetime import datetime, timedelta
import logging
import numpy as np
from scipy.stats import norm
import json
import asyncio

logger = logging.getLogger(__name__)

class CooldownConfig(BaseModel):
    duration: int = 60  # Default cooldown duration in seconds
    last_triggered: datetime = None
    max_triggers: int = 3
    current_triggers: int = 0
    volatility_buffer: float = 0.1  # Buffer for volatility adjustments
    pattern_threshold: float = 0.8  # Threshold for pattern recognition
    retry_delay: int = 30  # Default retry delay in seconds
    max_retries: int = 3  # Maximum number of retries
    historical_data: List[float] = []  # Historical performance data
    pattern_history: List[str] = []  # Historical cooldown patterns

class CooldownManager:
    def __init__(self):
        self.redis_pool: Optional[aioredis.Redis] = None
        self.initialize_redis()
        self.pattern_recognizer = PatternRecognizer()
        self.performance_optimizer = PerformanceOptimizer()
        self.retry_manager = RetryManager()

    async def initialize_redis(self) -> None:
        """Initialize Redis connection with proper error handling"""
        try:
            self.redis_pool = aioredis.from_url(
                "redis://localhost:6379",
                decode_responses=True
            )
            await self.redis_pool.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to Redis"
            )

    async def get_config(self, strategy_id: str) -> CooldownConfig:
        """
        Get cooldown config for strategy with pattern recognition
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Returns:
            CooldownConfig: Configuration for the cooldown
            
        Raises:
            HTTPException: If there's an error retrieving the config
        """
        if not self.redis_pool:
            await self.initialize_redis()

        try:
            config_data = await self.redis_pool.get(f"cooldown_config:{strategy_id}")
            if config_data:
                config = CooldownConfig(**json.loads(config_data))
                
                # Update pattern recognition
                config.pattern_history = self.pattern_recognizer.update_patterns(
                    config.historical_data,
                    config.pattern_history
                )
                
                logger.debug(f"Retrieved cooldown config for {strategy_id}: {config.dict()}")
                return config
            logger.debug(f"No cooldown config found for {strategy_id}")
            return CooldownConfig()
        except aioredis.RedisError as e:
            logger.error(f"Redis error getting config for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Redis error: {str(e)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Invalid cooldown config data"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting config for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting cooldown config: {str(e)}"
            )

    async def set_config(self, strategy_id: str, config: CooldownConfig) -> None:
        """
        Set cooldown config for strategy with performance optimization
        
        Args:
            strategy_id: Unique identifier for the strategy
            config: Cooldown configuration to set
            
        Raises:
            HTTPException: If there's an error setting the config
        """
        if not self.redis_pool:
            await self.initialize_redis()

        try:
            # Optimize cooldown duration based on historical performance
            optimal_duration = self.performance_optimizer.get_optimal_duration(
                config.historical_data,
                config.duration
            )
            config.duration = optimal_duration
            
            config_data = json.dumps(config.dict())
            await self.redis_pool.set(
                f"cooldown_config:{strategy_id}",
                config_data
            )
            logger.debug(f"Set cooldown config for {strategy_id}: {config_data}")
        except aioredis.RedisError as e:
            logger.error(f"Redis error setting config for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Redis error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error setting config for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error setting cooldown config: {str(e)}"
            )

    async def reset_cooldown(self, strategy_id: str) -> None:
        """
        Reset cooldown for strategy
        
        Args:
            strategy_id: Unique identifier for the strategy
            
        Raises:
            HTTPException: If there's an error resetting the cooldown
        """
        if not self.redis_pool:
            await self.initialize_redis()

        try:
            await self.redis_pool.delete(f"cooldown_config:{strategy_id}")
            logger.debug(f"Cooldown reset for {strategy_id}")
        except aioredis.RedisError as e:
            logger.error(f"Redis error resetting cooldown for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Redis error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error resetting cooldown for {strategy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error resetting cooldown: {str(e)}"
            )
