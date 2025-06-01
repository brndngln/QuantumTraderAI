import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import HTTPException
import redis
from redis import asyncio as aioredis
import json
from enum import Enum

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    STRATEGIC = "strategic"
    REFLEX = "reflex"

class TradeMemory(BaseModel):
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    entry_time: datetime
    exit_time: Optional[datetime]
    profit_loss: float
    strategy_used: str
    market_conditions: Dict
    emotion_state: str
    confidence: float
    tags: List[str]

class TradeMemoryEngine:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.memory_types = {
            MemoryType.SHORT_TERM: 24 * 3600,  # 24 hours
            MemoryType.LONG_TERM: 30 * 24 * 3600,  # 30 days
            MemoryType.STRATEGIC: 90 * 24 * 3600,  # 90 days
            MemoryType.REFLEX: 1 * 3600  # 1 hour
        }
        
    async def store_trade_memory(self, trade_memory: TradeMemory) -> None:
        """
        Store trade memory in appropriate memory type
        """
        try:
            # Convert to JSON
            memory_data = trade_memory.json()
            
            # Store in appropriate memory types
            for memory_type, ttl in self.memory_types.items():
                key = f"trade_memory:{memory_type}:{trade_memory.entry_time.timestamp()}"
                
                # Store with TTL
                await self.redis_pool.setex(
                    key,
                    ttl,
                    memory_data
                )
                
                # Store in index for quick retrieval
                index_key = f"trade_memory_index:{memory_type}"
                await self.redis_pool.zadd(
                    index_key,
                    {
                        key: trade_memory.entry_time.timestamp()
                    }
                )
                
            # Store in strategic memory with additional analysis
            await self._store_strategic_memory(trade_memory)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error storing trade memory: {str(e)}"
            )
    
    async def retrieve_memory(self, 
                            symbol: str, 
                            memory_type: MemoryType, 
                            limit: int = 100) -> List[TradeMemory]:
        """
        Retrieve trade memories for a specific symbol
        """
        try:
            index_key = f"trade_memory_index:{memory_type}"
            
            # Get latest memory keys
            keys = await self.redis_pool.zrevrange(
                index_key,
                0,
                limit - 1
            )
            
            memories = []
            for key in keys:
                memory_data = await self.redis_pool.get(key)
                if memory_data:
                    memory = TradeMemory.parse_raw(memory_data)
                    if memory.symbol == symbol:
                        memories.append(memory)
            
            return memories
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving trade memory: {str(e)}"
            )
    
    async def analyze_memory_patterns(self, 
                                    symbol: str, 
                                    memory_type: MemoryType) -> Dict:
        """
        Analyze patterns in trade memories
        """
        try:
            memories = await self.retrieve_memory(symbol, memory_type)
            
            if not memories:
                return {
                    'pattern_strength': 0,
                    'confidence': 0,
                    'recommendation': 'neutral',
                    'patterns': {}
                }
            
            # Calculate pattern metrics
            metrics = self._calculate_pattern_metrics(memories)
            
            # Generate pattern analysis
            analysis = {
                'pattern_strength': metrics['pattern_strength'],
                'confidence': metrics['confidence'],
                'recommendation': self._generate_recommendation(metrics),
                'patterns': {
                    'success_rate': metrics['success_rate'],
                    'average_profit': metrics['average_profit'],
                    'emotion_patterns': metrics['emotion_patterns'],
                    'market_condition_patterns': metrics['market_condition_patterns']
                }
            }
            
            return analysis
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing memory patterns: {str(e)}"
            )
    
    def _calculate_pattern_metrics(self, memories: List[TradeMemory]) -> Dict:
        """
        Calculate metrics from trade memories
        """
        profits = [m.profit_loss for m in memories if m.profit_loss > 0]
        losses = [m.profit_loss for m in memories if m.profit_loss < 0]
        
        success_rate = len(profits) / len(memories) if memories else 0
        average_profit = np.mean(profits) if profits else 0
        average_loss = np.mean(losses) if losses else 0
        
        # Calculate emotion patterns
        emotion_patterns = {}
        for memory in memories:
            emotion = memory.emotion_state
            if emotion not in emotion_patterns:
                emotion_patterns[emotion] = {
                    'count': 0,
                    'success_rate': 0,
                    'average_profit': 0
                }
            
            emotion_patterns[emotion]['count'] += 1
            if memory.profit_loss > 0:
                emotion_patterns[emotion]['success_rate'] += 1
            emotion_patterns[emotion]['average_profit'] += memory.profit_loss
            
        # Normalize emotion patterns
        for emotion in emotion_patterns:
            count = emotion_patterns[emotion]['count']
            emotion_patterns[emotion]['success_rate'] /= count
            emotion_patterns[emotion]['average_profit'] /= count
            
        # Calculate market condition patterns
        market_condition_patterns = {}
        for memory in memories:
            conditions = memory.market_conditions
            for condition in conditions:
                if condition not in market_condition_patterns:
                    market_condition_patterns[condition] = {
                        'count': 0,
                        'success_rate': 0,
                        'average_profit': 0
                    }
                
                market_condition_patterns[condition]['count'] += 1
                if memory.profit_loss > 0:
                    market_condition_patterns[condition]['success_rate'] += 1
                market_condition_patterns[condition]['average_profit'] += memory.profit_loss
                
        # Normalize market condition patterns
        for condition in market_condition_patterns:
            count = market_condition_patterns[condition]['count']
            market_condition_patterns[condition]['success_rate'] /= count
            market_condition_patterns[condition]['average_profit'] /= count
            
        return {
            'pattern_strength': success_rate * (average_profit - average_loss),
            'confidence': success_rate,
            'success_rate': success_rate,
            'average_profit': average_profit,
            'emotion_patterns': emotion_patterns,
            'market_condition_patterns': market_condition_patterns
        }
    
    def _generate_recommendation(self, metrics: Dict) -> str:
        """
        Generate trading recommendation based on memory analysis
        """
        if metrics['pattern_strength'] > 0.5 and metrics['confidence'] > 0.7:
            return 'strong_buy'
        elif metrics['pattern_strength'] > 0.3 and metrics['confidence'] > 0.5:
            return 'buy'
        elif metrics['pattern_strength'] < -0.5 and metrics['confidence'] > 0.7:
            return 'strong_sell'
        elif metrics['pattern_strength'] < -0.3 and metrics['confidence'] > 0.5:
            return 'sell'
        return 'neutral'
    
    async def _store_strategic_memory(self, trade_memory: TradeMemory) -> None:
        """
        Store additional strategic analysis in memory
        """
        try:
            # Get similar memories
            similar_memories = await self.retrieve_memory(
                trade_memory.symbol,
                MemoryType.LONG_TERM,
                limit=100
            )
            
            # Analyze patterns
            analysis = self._calculate_pattern_metrics(similar_memories)
            
            # Store strategic insights
            strategic_key = f"strategic_memory:{trade_memory.symbol}:{trade_memory.entry_time.timestamp()}"
            strategic_data = {
                'trade_memory': trade_memory.dict(),
                'pattern_analysis': analysis,
                'strategic_insights': self._generate_strategic_insights(analysis)
            }
            
            await self.redis_pool.setex(
                strategic_key,
                self.memory_types[MemoryType.STRATEGIC],
                json.dumps(strategic_data)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error storing strategic memory: {str(e)}"
            )
    
    def _generate_strategic_insights(self, analysis: Dict) -> Dict:
        """
        Generate strategic insights from pattern analysis
        """
        insights = {
            'market_trend': self._determine_market_trend(analysis),
            'risk_level': self._calculate_risk_level(analysis),
            'confidence_score': self._calculate_confidence_score(analysis),
            'recommended_position_size': self._calculate_position_size(analysis),
            'emotion_based_adjustments': self._get_emotion_adjustments(analysis)
        }
        
        return insights
    
    def _determine_market_trend(self, analysis: Dict) -> str:
        """
        Determine market trend based on pattern analysis
        """
        if analysis['pattern_strength'] > 0.5:
            return 'bullish'
        elif analysis['pattern_strength'] < -0.5:
            return 'bearish'
        return 'neutral'
    
    def _calculate_risk_level(self, analysis: Dict) -> float:
        """
        Calculate risk level based on analysis
        """
        return 1 - analysis['confidence']
    
    def _calculate_confidence_score(self, analysis: Dict) -> float:
        """
        Calculate overall confidence score
        """
        return analysis['confidence'] * analysis['pattern_strength']
    
    def _calculate_position_size(self, analysis: Dict) -> float:
        """
        Calculate recommended position size
        """
        base_size = 0.01  # 1% of portfolio
        adjustment = analysis['confidence'] * analysis['pattern_strength']
        return base_size * (1 + adjustment)
    
    def _get_emotion_adjustments(self, analysis: Dict) -> Dict:
        """
        Get emotion-based adjustments
        """
        adjustments = {}
        for emotion, metrics in analysis['emotion_patterns'].items():
            if metrics['count'] > 10:  # Only consider significant samples
                adjustments[emotion] = {
                    'position_size': metrics['success_rate'] * 0.1,
                    'stop_loss': 1 - metrics['success_rate'] * 0.2,
                    'take_profit': metrics['success_rate'] * 0.3
                }
        
        return adjustments
