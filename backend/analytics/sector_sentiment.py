import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
import json

class Sector(Enum):
    TECH = "tech"
    ENERGY = "energy"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    UTILITIES = "utilities"

class SentimentSource(Enum):
    ETF_FLOW = "etf_flow"
    NEWS = "news"
    EARNINGS = "earnings"
    SOCIAL = "social"
    VOLUME = "volume"

class SectorSentiment(BaseModel):
    sector: Sector
    sentiment_score: float
    etf_flow: float
    news_tone: float
    earnings_sentiment: float
    volume_anomaly: float
    last_update: datetime
    top_contributors: List[str]

class SectorSentimentIndex:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.sentiment_weights = {
            SentimentSource.ETF_FLOW: 0.3,
            SentimentSource.NEWS: 0.25,
            SentimentSource.EARNINGS: 0.2,
            SentimentSource.SOCIAL: 0.15,
            SentimentSource.VOLUME: 0.1
        }
        
    async def update_sector_sentiment(self, sector: Sector, new_data: Dict) -> SectorSentiment:
        """
        Update sentiment for a sector
        """
        try:
            # Get existing sentiment
            existing_sentiment = await self.get_sector_sentiment(sector)
            
            # Calculate new sentiment scores
            sentiment_scores = self.calculate_sentiment_scores(new_data)
            
            # Update Redis
            sentiment_data = SectorSentiment(
                sector=sector,
                sentiment_score=self.calculate_weighted_sentiment(sentiment_scores),
                etf_flow=sentiment_scores[SentimentSource.ETF_FLOW],
                news_tone=sentiment_scores[SentimentSource.NEWS],
                earnings_sentiment=sentiment_scores[SentimentSource.EARNINGS],
                volume_anomaly=sentiment_scores[SentimentSource.VOLUME],
                last_update=datetime.now(),
                top_contributors=self.get_top_contributors(new_data)
            )
            
            await self.redis_pool.set(
                f"sector_sentiment:{sector.value}",
                sentiment_data.json()
            )
            
            return sentiment_data
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating sector sentiment: {str(e)}"
            )
    
    async def get_sector_sentiment(self, sector: Sector) -> Optional[SectorSentiment]:
        """
        Get current sentiment for a sector
        """
        try:
            data = await self.redis_pool.get(f"sector_sentiment:{sector.value}")
            if data:
                return SectorSentiment.parse_raw(data)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting sector sentiment: {str(e)}"
            )
    
    def calculate_sentiment_scores(self, data: Dict) -> Dict[SentimentSource, float]:
        """
        Calculate sentiment scores from raw data
        """
        scores = {}
        
        # ETF Flow analysis
        scores[SentimentSource.ETF_FLOW] = self.analyze_etf_flow(data.get('etf_flow', {}))
        
        # News sentiment analysis
        scores[SentimentSource.NEWS] = self.analyze_news(data.get('news', []))
        
        # Earnings sentiment
        scores[SentimentSource.EARNINGS] = self.analyze_earnings(data.get('earnings', []))
        
        # Social media sentiment
        scores[SentimentSource.SOCIAL] = self.analyze_social(data.get('social', []))
        
        # Volume analysis
        scores[SentimentSource.VOLUME] = self.analyze_volume(data.get('volume', {}))
        
        return scores
    
    def calculate_weighted_sentiment(self, scores: Dict[SentimentSource, float]) -> float:
        """
        Calculate weighted sentiment score
        """
        total_weight = sum(self.sentiment_weights.values())
        weighted_sum = sum(
            scores[source] * self.sentiment_weights[source]
            for source in scores
        )
        
        return weighted_sum / total_weight
    
    def get_top_contributors(self, data: Dict) -> List[str]:
        """
        Get top contributing factors
        """
        contributors = []
        
        # Add ETF flow contributors
        contributors.extend(data.get('etf_flow', {}).get('top_contributors', []))
        
        # Add news contributors
        contributors.extend(data.get('news', []))
        
        return contributors[:5]  # Return top 5 contributors
    
    def analyze_etf_flow(self, flow_data: Dict) -> float:
        """
        Analyze ETF flow data
        """
        # Implementation depends on data source
        return 0.5
    
    def analyze_news(self, news_data: List[Dict]) -> float:
        """
        Analyze news sentiment
        """
        # Implementation depends on NLP service
        return 0.5
    
    def analyze_earnings(self, earnings_data: List[Dict]) -> float:
        """
        Analyze earnings sentiment
        """
        # Implementation depends on data source
        return 0.5
    
    def analyze_social(self, social_data: List[Dict]) -> float:
        """
        Analyze social media sentiment
        """
        # Implementation depends on social media API
        return 0.5
    
    def analyze_volume(self, volume_data: Dict) -> float:
        """
        Analyze volume anomalies
        """
        # Implementation depends on data source
        return 0.5
