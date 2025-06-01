import numpy as np
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum

class VotingStrategy(Enum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    PRIORITY = "priority"

class AgentVote(BaseModel):
    agent_id: str
    signal: float  # -1 to 1
    confidence: float  # 0 to 1
    priority: int  # 1 to 10
    timestamp: datetime

class VotingConfig(BaseModel):
    strategy: VotingStrategy
    threshold: float
    minimum_agents: int
    decay_factor: float

class AgentVotingEngine:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.default_config = VotingConfig(
            strategy=VotingStrategy.WEIGHTED,
            threshold=0.6,
            minimum_agents=3,
            decay_factor=0.95
        )
        
    async def process_votes(self, votes: List[AgentVote], symbol: str) -> Optional[float]:
        """
        Process votes from multiple agents
        """
        try:
            # Get current config
            config = await self.get_voting_config(symbol)
            
            # Validate votes
            if len(votes) < config.minimum_agents:
                return None
                
            # Process votes based on strategy
            if config.strategy == VotingStrategy.MAJORITY:
                return self.process_majority_vote(votes)
            elif config.strategy == VotingStrategy.WEIGHTED:
                return self.process_weighted_vote(votes)
            else:
                return self.process_priority_vote(votes)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing votes: {str(e)}"
            )
    
    def process_majority_vote(self, votes: List[AgentVote]) -> float:
        """
        Process votes using majority rule
        """
        bullish_votes = sum(1 for v in votes if v.signal > 0)
        bearish_votes = sum(1 for v in votes if v.signal < 0)
        
        if bullish_votes > bearish_votes:
            return 1.0
        elif bearish_votes > bullish_votes:
            return -1.0
        return 0.0
    
    def process_weighted_vote(self, votes: List[AgentVote]) -> float:
        """
        Process votes using weighted scoring
        """
        total_weight = 0
        weighted_sum = 0
        
        for vote in votes:
            weight = vote.confidence * vote.priority
            weighted_sum += vote.signal * weight
            total_weight += weight
            
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def process_priority_vote(self, votes: List[AgentVote]) -> float:
        """
        Process votes using priority override
        """
        # Sort by priority
        votes.sort(key=lambda v: v.priority, reverse=True)
        
        # Return signal from highest priority agent
        return votes[0].signal
    
    async def get_voting_config(self, symbol: str) -> VotingConfig:
        """
        Get voting configuration for symbol
        """
        try:
            data = await self.redis_pool.hgetall(f"voting_config:{symbol}")
            if data:
                return VotingConfig.parse_obj(data)
            return self.default_config
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting voting config: {str(e)}"
            )
    
    async def update_voting_config(self, symbol: str, config: VotingConfig) -> None:
        """
        Update voting configuration
        """
        try:
            await self.redis_pool.hset(
                f"voting_config:{symbol}",
                mapping=config.dict()
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating voting config: {str(e)}"
            )
    
    async def record_vote(self, vote: AgentVote, symbol: str) -> None:
        """
        Record agent vote
        """
        try:
            # Store vote
            await self.redis_pool.lpush(
                f"votes:{symbol}:{vote.agent_id}",
                vote.json()
            )
            
            # Trim old votes
            await self.redis_pool.ltrim(
                f"votes:{symbol}:{vote.agent_id}",
                0,
                99  # Keep last 100 votes
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error recording vote: {str(e)}"
            )
    
    async def get_agent_performance(self, agent_id: str, symbol: str) -> Dict:
        """
        Get agent performance metrics
        """
        try:
            # Get votes
            votes = await self.redis_pool.lrange(
                f"votes:{symbol}:{agent_id}",
                0,
                100
            )
            
            # Calculate metrics
            if votes:
                data = [AgentVote.parse_raw(v) for v in votes]
                return {
                    'accuracy': self.calculate_accuracy(data),
                    'avg_confidence': self.calculate_avg_confidence(data),
                    'win_rate': self.calculate_win_rate(data)
                }
            
            return {
                'accuracy': 0.5,
                'avg_confidence': 0.5,
                'win_rate': 0.5
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting agent performance: {str(e)}"
            )
    
    def calculate_accuracy(self, votes: List[AgentVote]) -> float:
        """
        Calculate agent accuracy
        """
        correct = sum(1 for v in votes if v.signal * self.get_market_direction(v.timestamp) > 0)
        return correct / len(votes) if votes else 0
    
    def calculate_avg_confidence(self, votes: List[AgentVote]) -> float:
        """
        Calculate average confidence
        """
        return sum(v.confidence for v in votes) / len(votes) if votes else 0
    
    def calculate_win_rate(self, votes: List[AgentVote]) -> float:
        """
        Calculate win rate
        """
        wins = sum(1 for v in votes if v.signal * self.get_market_direction(v.timestamp) > 0)
        return wins / len(votes) if votes else 0
    
    def get_market_direction(self, timestamp: datetime) -> float:
        """
        Get market direction at time
        """
        # Implementation depends on data source
        return 0.0
