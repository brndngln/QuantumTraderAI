import numpy as np
from typing import Dict, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum

class StrategyPerformanceTier(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class LeverageConfig(BaseModel):
    win_rate: float
    confidence_score: float
    vault_buffer: float
    strategy_tier: StrategyPerformanceTier
    max_leverage: float
    min_leverage: float

class LeverageScaler:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.default_config = {
            StrategyPerformanceTier.HIGH: LeverageConfig(
                win_rate=0.7,
                confidence_score=0.9,
                vault_buffer=0.2,
                strategy_tier=StrategyPerformanceTier.HIGH,
                max_leverage=5.0,
                min_leverage=2.0
            ),
            StrategyPerformanceTier.MEDIUM: LeverageConfig(
                win_rate=0.5,
                confidence_score=0.7,
                vault_buffer=0.3,
                strategy_tier=StrategyPerformanceTier.MEDIUM,
                max_leverage=3.0,
                min_leverage=1.5
            ),
            StrategyPerformanceTier.LOW: LeverageConfig(
                win_rate=0.3,
                confidence_score=0.5,
                vault_buffer=0.4,
                strategy_tier=StrategyPerformanceTier.LOW,
                max_leverage=2.0,
                min_leverage=1.0
            )
        }
        
    async def calculate_leverage(self, strategy_id: str, vault_balance: float, trade_size: float) -> float:
        """
        Calculate optimal leverage for trade
        """
        try:
            # Get current performance
            performance = await self.get_strategy_performance(strategy_id)
            
            # Get current risk metrics
            risk_metrics = await self.get_risk_metrics(strategy_id)
            
            # Calculate leverage based on factors
            leverage = self.calculate_dynamic_leverage(
                performance.win_rate,
                risk_metrics.confidence_score,
                vault_balance,
                trade_size
            )
            
            # Store leverage decision
            await self.redis_pool.hset(
                f"leverage_history:{strategy_id}",
                mapping={
                    'timestamp': datetime.now().isoformat(),
                    'leverage': str(leverage),
                    'win_rate': str(performance.win_rate),
                    'confidence': str(risk_metrics.confidence_score)
                }
            )
            
            return leverage
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating leverage: {str(e)}"
            )
    
    def calculate_dynamic_leverage(self, win_rate: float, confidence: float, vault_balance: float, trade_size: float) -> float:
        """
        Calculate dynamic leverage based on multiple factors
        """
        # Calculate base leverage based on win rate
        base_leverage = self.calculate_base_leverage(win_rate)
        
        # Adjust for confidence
        confidence_adj = self.calculate_confidence_adjustment(confidence)
        
        # Calculate vault buffer
        vault_buffer = self.calculate_vault_buffer(vault_balance, trade_size)
        
        # Combine factors
        leverage = base_leverage * confidence_adj * vault_buffer
        
        # Ensure within bounds
        config = self.get_leverage_config(win_rate)
        leverage = max(config.min_leverage, min(config.max_leverage, leverage))
        
        return leverage
    
    def calculate_base_leverage(self, win_rate: float) -> float:
        """
        Calculate base leverage based on win rate
        """
        if win_rate >= 0.7:
            return 4.0
        elif win_rate >= 0.5:
            return 3.0
        else:
            return 2.0
    
    def calculate_confidence_adjustment(self, confidence: float) -> float:
        """
        Calculate confidence adjustment factor
        """
        return confidence * 1.5  # Max 1.5x multiplier
    
    def calculate_vault_buffer(self, vault_balance: float, trade_size: float) -> float:
        """
        Calculate vault buffer adjustment
        """
        buffer = vault_balance / trade_size
        return min(1.0, max(0.5, buffer))
    
    def get_leverage_config(self, win_rate: float) -> LeverageConfig:
        """
        Get appropriate leverage config based on win rate
        """
        if win_rate >= 0.7:
            return self.default_config[StrategyPerformanceTier.HIGH]
        elif win_rate >= 0.5:
            return self.default_config[StrategyPerformanceTier.MEDIUM]
        else:
            return self.default_config[StrategyPerformanceTier.LOW]
    
    async def get_strategy_performance(self, strategy_id: str) -> Dict:
        """
        Get strategy performance metrics
        """
        try:
            data = await self.redis_pool.hgetall(f"strategy_performance:{strategy_id}")
            return {
                'win_rate': float(data.get('win_rate', '0.5')),
                'total_trades': int(data.get('total_trades', '0')),
                'profit_factor': float(data.get('profit_factor', '1.0'))
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting strategy performance: {str(e)}"
            )
    
    async def get_risk_metrics(self, strategy_id: str) -> Dict:
        """
        Get risk metrics for strategy
        """
        try:
            data = await self.redis_pool.hgetall(f"risk_metrics:{strategy_id}")
            return {
                'confidence_score': float(data.get('confidence_score', '0.5')),
                'volatility': float(data.get('volatility', '0.0')),
                'max_drawdown': float(data.get('max_drawdown', '0.0'))
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting risk metrics: {str(e)}"
            )
    
    async def update_performance(self, strategy_id: str, performance: Dict) -> None:
        """
        Update strategy performance metrics
        """
        try:
            await self.redis_pool.hset(
                f"strategy_performance:{strategy_id}",
                mapping=performance
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating performance: {str(e)}"
            )
    
    async def update_risk_metrics(self, strategy_id: str, metrics: Dict) -> None:
        """
        Update risk metrics
        """
        try:
            await self.redis_pool.hset(
                f"risk_metrics:{strategy_id}",
                mapping=metrics
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating risk metrics: {str(e)}"
            )
