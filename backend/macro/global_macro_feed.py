import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum
import json

class MacroIndicator(Enum):
    CPI = "cpi"
    INTEREST_RATE = "interest_rate"
    INFLATION = "inflation"
    OIL_PRICE = "oil_price"
    CURRENCY_STRENGTH = "currency_strength"

class MacroData(BaseModel):
    indicator: MacroIndicator
    value: float
    change: float
    sentiment: float
    last_update: datetime

class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class StrategyFilter(BaseModel):
    risk_tier: RiskTier
    strategy_type: str
    market_condition: str
    weight: float

class GlobalMacroFeed:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.sentiment_weights = {
            MacroIndicator.CPI: 0.2,
            MacroIndicator.INTEREST_RATE: 0.3,
            MacroIndicator.INFLATION: 0.2,
            MacroIndicator.OIL_PRICE: 0.15,
            MacroIndicator.CURRENCY_STRENGTH: 0.15
        }
        
    async def update_macro_data(self, indicator: MacroIndicator, data: Dict) -> None:
        """
        Update macroeconomic data
        """
        try:
            # Create macro data object
            macro_data = MacroData(
                indicator=indicator,
                value=data['value'],
                change=data['change'],
                sentiment=self.calculate_sentiment(data['change']),
                last_update=datetime.now()
            )
            
            # Store in Redis
            await self.redis_pool.hset(
                f"macro_data:{indicator.value}",
                mapping=macro_data.dict()
            )
            
            # Update macro heatmap
            await self.update_macro_heatmap()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating macro data: {str(e)}"
            )
    
    def calculate_sentiment(self, change: float) -> float:
        """
        Calculate sentiment score from change
        """
        if change > 0:
            return min(1.0, change * 0.1)  # Max 1.0
        elif change < 0:
            return max(-1.0, change * 0.1)  # Min -1.0
        return 0.0
    
    async def update_macro_heatmap(self) -> None:
        """
        Update macroeconomic heatmap
        """
        try:
            # Get all macro data
            heatmap_data = []
            for indicator in MacroIndicator:
                data = await self.redis_pool.hgetall(f"macro_data:{indicator.value}")
                if data:
                    heatmap_data.append({
                        'indicator': indicator.value,
                        'value': float(data['value']),
                        'change': float(data['change']),
                        'sentiment': float(data['sentiment'])
                    })
            
            # Calculate overall sentiment
            overall_sentiment = self.calculate_overall_sentiment(heatmap_data)
            
            # Store heatmap
            heatmap = {
                'data': heatmap_data,
                'overall_sentiment': overall_sentiment,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.redis_pool.set(
                "macro_heatmap",
                json.dumps(heatmap)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating heatmap: {str(e)}"
            )
    
    def calculate_overall_sentiment(self, data: List[Dict]) -> float:
        """
        Calculate overall macroeconomic sentiment
        """
        total_sentiment = 0
        total_weight = 0
        
        for item in data:
            indicator = MacroIndicator(item['indicator'])
            weight = self.sentiment_weights[indicator]
            sentiment = item['sentiment']
            
            total_sentiment += sentiment * weight
            total_weight += weight
            
        return total_sentiment / total_weight if total_weight > 0 else 0
    
    async def get_macro_heatmap(self) -> Dict:
        """
        Get current macroeconomic heatmap
        """
        try:
            data = await self.redis_pool.get("macro_heatmap")
            if data:
                return json.loads(data)
            return {}
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting heatmap: {str(e)}"
            )
    
    async def get_strategy_filters(self) -> List[StrategyFilter]:
        """
        Get strategy filters based on macro conditions
        """
        try:
            # Get current heatmap
            heatmap = await self.get_macro_heatmap()
            
            # Determine risk tier based on sentiment
            overall_sentiment = heatmap.get('overall_sentiment', 0)
            risk_tier = self.determine_risk_tier(overall_sentiment)
            
            # Get relevant indicators
            relevant_indicators = self.get_relevant_indicators(heatmap)
            
            # Create strategy filters
            filters = []
            for indicator in relevant_indicators:
                filters.append(StrategyFilter(
                    risk_tier=risk_tier,
                    strategy_type=self.get_strategy_type(indicator),
                    market_condition=self.get_market_condition(indicator),
                    weight=self.sentiment_weights[indicator]
                ))
            
            return filters
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting strategy filters: {str(e)}"
            )
    
    def determine_risk_tier(self, sentiment: float) -> RiskTier:
        """
        Determine risk tier based on sentiment
        """
        if sentiment > 0.5:
            return RiskTier.LOW
        elif sentiment > -0.5:
            return RiskTier.MEDIUM
        else:
            return RiskTier.HIGH
    
    def get_relevant_indicators(self, heatmap: Dict) -> List[MacroIndicator]:
        """
        Get most relevant indicators
        """
        relevant = []
        for item in heatmap.get('data', []):
            if abs(item['sentiment']) > 0.3:  # Threshold for relevance
                relevant.append(MacroIndicator(item['indicator']))
        return relevant
    
    def get_strategy_type(self, indicator: MacroIndicator) -> str:
        """
        Get strategy type based on indicator
        """
        if indicator in [MacroIndicator.CPI, MacroIndicator.INFLATION]:
            return "inflation_protection"
        elif indicator == MacroIndicator.INTEREST_RATE:
            return "rate_sensitive"
        elif indicator == MacroIndicator.OIL_PRICE:
            return "commodity"
        else:
            return "currency"
    
    def get_market_condition(self, indicator: MacroIndicator) -> str:
        """
        Get market condition based on indicator
        """
        if indicator in [MacroIndicator.CPI, MacroIndicator.INFLATION]:
            return "inflationary"
        elif indicator == MacroIndicator.INTEREST_RATE:
            return "rate_hike"
        elif indicator == MacroIndicator.OIL_PRICE:
            return "commodity_rally"
        else:
            return "currency_strength"
