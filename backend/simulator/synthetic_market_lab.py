import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime, timedelta
from enum import Enum
import random

class MarketCondition(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    VOLATILE = "volatile"
    RANGE_BOUND = "range_bound"

class MarketScenario(BaseModel):
    condition: MarketCondition
    volatility: float
    trend_strength: float
    duration: int  # in days
    news_events: List[Dict]
    economic_data: List[Dict]

class SyntheticMarketGenerator:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.default_params = {
            'volatility_range': (0.005, 0.02),  # 0.5% to 2% daily
            'trend_strength_range': (0.001, 0.005),  # 0.1% to 0.5% daily
            'news_impact_range': (-0.02, 0.02),  # 2% impact
            'economic_data_range': (-0.01, 0.01)  # 1% impact
        }
        
    async def generate_market_scenario(self, symbol: str, days: int) -> MarketScenario:
        """
        Generate a synthetic market scenario
        """
        try:
            # Get historical data
            historical_data = await self.get_historical_data(symbol)
            
            # Analyze market conditions
            condition = self.analyze_market_condition(historical_data)
            
            # Generate scenario
            scenario = MarketScenario(
                condition=condition,
                volatility=self.generate_volatility(historical_data),
                trend_strength=self.generate_trend_strength(condition),
                duration=days,
                news_events=self.generate_news_events(days),
                economic_data=self.generate_economic_data(days)
            )
            
            # Store scenario
            await self.redis_pool.hset(
                f"market_scenario:{symbol}",
                mapping=scenario.dict()
            )
            
            return scenario
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating market scenario: {str(e)}"
            )
    
    def analyze_market_condition(self, data: pd.DataFrame) -> MarketCondition:
        """
        Analyze market condition based on historical data
        """
        volatility = data['close'].pct_change().std()
        trend = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0]
        
        if volatility > 0.02:
            return MarketCondition.VOLATILE
        elif trend > 0.01:
            return MarketCondition.BULLISH
        elif trend < -0.01:
            return MarketCondition.BEARISH
        else:
            return MarketCondition.RANGE_BOUND
    
    def generate_volatility(self, data: pd.DataFrame) -> float:
        """
        Generate volatility based on historical data
        """
        historical_vol = data['close'].pct_change().std()
        return max(
            min(historical_vol * 1.5, self.default_params['volatility_range'][1]),
            self.default_params['volatility_range'][0]
        )
    
    def generate_trend_strength(self, condition: MarketCondition) -> float:
        """
        Generate trend strength based on market condition
        """
        if condition == MarketCondition.BULLISH:
            return random.uniform(
                self.default_params['trend_strength_range'][0],
                self.default_params['trend_strength_range'][1]
            )
        elif condition == MarketCondition.BEARISH:
            return random.uniform(
                -self.default_params['trend_strength_range'][1],
                -self.default_params['trend_strength_range'][0]
            )
        else:
            return 0.0
    
    def generate_news_events(self, days: int) -> List[Dict]:
        """
        Generate synthetic news events
        """
        events = []
        event_days = random.sample(range(1, days), random.randint(1, 3))
        
        for day in event_days:
            impact = random.uniform(
                self.default_params['news_impact_range'][0],
                self.default_params['news_impact_range'][1]
            )
            events.append({
                'day': day,
                'impact': impact,
                'type': random.choice(['positive', 'negative']),
                'description': f"Synthetic news event {day}"
            })
        
        return events
    
    def generate_economic_data(self, days: int) -> List[Dict]:
        """
        Generate synthetic economic data
        """
        data = []
        data_days = random.sample(range(1, days), random.randint(2, 4))
        
        for day in data_days:
            impact = random.uniform(
                self.default_params['economic_data_range'][0],
                self.default_params['economic_data_range'][1]
            )
            data.append({
                'day': day,
                'impact': impact,
                'type': random.choice(['economic', 'political']),
                'description': f"Synthetic economic data {day}"
            })
        
        return data
    
    async def generate_market_data(self, scenario: MarketScenario, days: int) -> pd.DataFrame:
        """
        Generate synthetic market data
        """
        try:
            # Initialize data
            data = []
            current_price = 100.0  # Base price
            
            for day in range(days):
                # Base price movement
                price_change = scenario.trend_strength
                
                # Add volatility
                price_change += random.gauss(0, scenario.volatility)
                
                # Add news impact
                for event in scenario.news_events:
                    if event['day'] == day:
                        price_change += event['impact']
                
                # Add economic data impact
                for event in scenario.economic_data:
                    if event['day'] == day:
                        price_change += event['impact']
                
                # Update price
                current_price *= (1 + price_change)
                
                # Add to data
                data.append({
                    'date': datetime.now() + timedelta(days=day),
                    'open': current_price * (1 + random.uniform(-0.001, 0.001)),
                    'high': current_price * (1 + random.uniform(0, 0.002)),
                    'low': current_price * (1 - random.uniform(0, 0.002)),
                    'close': current_price,
                    'volume': random.randint(100000, 1000000)
                })
            
            # Create DataFrame
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating market data: {str(e)}"
            )
    
    async def get_historical_data(self, symbol: str) -> pd.DataFrame:
        """
        Get historical price data
        """
        # Implementation depends on data source
        return pd.DataFrame()
    
    async def store_market_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Store synthetic market data
        """
        try:
            # Convert to JSON
            data_json = data.to_json(orient='records')
            
            # Store in Redis
            await self.redis_pool.hset(
                f"synthetic_data:{symbol}",
                mapping={
                    'data': data_json,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error storing market data: {str(e)}"
            )
    
    async def get_stored_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get stored synthetic market data
        """
        try:
            data = await self.redis_pool.hgetall(f"synthetic_data:{symbol}")
            if data:
                return pd.read_json(data['data'])
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting market data: {str(e)}"
            )
