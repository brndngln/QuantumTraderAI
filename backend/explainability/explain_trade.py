import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum
import json

class StrategyType(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    MACHINE_LEARNING = "machine_learning"

class TradeExplanation(BaseModel):
    strategy: StrategyType
    signal_type: str
    confidence: float
    checklist: List[Dict]
    criteria_met: List[str]
    market_context: Dict[str, Any]
    timestamp: datetime

class ExplainabilityEngine:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.checklists = {
            StrategyType.TECHNICAL: [
                {'name': 'trend', 'weight': 0.3},
                {'name': 'momentum', 'weight': 0.2},
                {'name': 'volatility', 'weight': 0.2},
                {'name': 'support_resistance', 'weight': 0.1},
                {'name': 'volume', 'weight': 0.1}
            ],
            StrategyType.FUNDAMENTAL: [
                {'name': 'earnings', 'weight': 0.3},
                {'name': 'valuation', 'weight': 0.2},
                {'name': 'growth', 'weight': 0.2},
                {'name': 'financial_health', 'weight': 0.1},
                {'name': 'industry_position', 'weight': 0.1}
            ],
            StrategyType.SENTIMENT: [
                {'name': 'news', 'weight': 0.3},
                {'name': 'social_media', 'weight': 0.2},
                {'name': 'analyst', 'weight': 0.2},
                {'name': 'volume_anomaly', 'weight': 0.1},
                {'name': 'price_action', 'weight': 0.1}
            ],
            StrategyType.MACRO: [
                {'name': 'economic_data', 'weight': 0.3},
                {'name': 'interest_rates', 'weight': 0.2},
                {'name': 'inflation', 'weight': 0.2},
                {'name': 'currency', 'weight': 0.1},
                {'name': 'commodities', 'weight': 0.1}
            ],
            StrategyType.MACHINE_LEARNING: [
                {'name': 'model_confidence', 'weight': 0.4},
                {'name': 'feature_importance', 'weight': 0.3},
                {'name': 'backtest_performance', 'weight': 0.2},
                {'name': 'risk_metrics', 'weight': 0.1}
            ]
        }
        
    async def explain_trade(self, trade: Dict) -> TradeExplanation:
        """
        Generate explanation for trade
        """
        try:
            # Get strategy type
            strategy_type = self.determine_strategy_type(trade)
            
            # Get relevant checklist
            checklist = self.checklists[strategy_type]
            
            # Evaluate criteria
            criteria = self.evaluate_criteria(trade, checklist)
            
            # Generate explanation
            explanation = TradeExplanation(
                strategy=strategy_type,
                signal_type=self.determine_signal_type(trade),
                confidence=self.calculate_confidence(criteria),
                checklist=checklist,
                criteria_met=[c['name'] for c in criteria if c['met']],
                market_context=self.get_market_context(trade),
                timestamp=datetime.now()
            )
            
            # Store explanation
            await self.redis_pool.hset(
                f"trade_explanation:{trade['id']}",
                mapping=explanation.dict()
            )
            
            return explanation
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error explaining trade: {str(e)}"
            )
    
    def determine_strategy_type(self, trade: Dict) -> StrategyType:
        """
        Determine strategy type based on trade data
        """
        if trade.get('technical_indicators'):
            return StrategyType.TECHNICAL
        elif trade.get('fundamental_data'):
            return StrategyType.FUNDAMENTAL
        elif trade.get('sentiment_data'):
            return StrategyType.SENTIMENT
        elif trade.get('macro_data'):
            return StrategyType.MACRO
        else:
            return StrategyType.MACHINE_LEARNING
    
    def determine_signal_type(self, trade: Dict) -> str:
        """
        Determine signal type
        """
        if trade['side'] == 'buy':
            return 'bullish'
        else:
            return 'bearish'
    
    def evaluate_criteria(self, trade: Dict, checklist: List[Dict]) -> List[Dict]:
        """
        Evaluate criteria against checklist
        """
        results = []
        
        for item in checklist:
            result = {
                'name': item['name'],
                'weight': item['weight'],
                'met': False,
                'value': None
            }
            
            # Evaluate based on strategy type
            if trade['strategy'] == StrategyType.TECHNICAL:
                result['met'] = self.evaluate_technical_criteria(trade, item['name'])
            elif trade['strategy'] == StrategyType.FUNDAMENTAL:
                result['met'] = self.evaluate_fundamental_criteria(trade, item['name'])
            elif trade['strategy'] == StrategyType.SENTIMENT:
                result['met'] = self.evaluate_sentiment_criteria(trade, item['name'])
            elif trade['strategy'] == StrategyType.MACRO:
                result['met'] = self.evaluate_macro_criteria(trade, item['name'])
            else:
                result['met'] = self.evaluate_ml_criteria(trade, item['name'])
            
            results.append(result)
            
        return results
    
    def calculate_confidence(self, criteria: List[Dict]) -> float:
        """
        Calculate overall confidence score
        """
        total_weight = sum(item['weight'] for item in criteria)
        met_weight = sum(item['weight'] for item in criteria if item['met'])
        
        return met_weight / total_weight if total_weight > 0 else 0
    
    def get_market_context(self, trade: Dict) -> Dict:
        """
        Get market context for trade
        """
        return {
            'volatility': trade.get('volatility', 0.0),
            'trend': trade.get('trend', 'neutral'),
            'support_resistance': trade.get('support_resistance', []),
            'volume': trade.get('volume', 0),
            'news_sentiment': trade.get('news_sentiment', 0.0),
            'macro_conditions': trade.get('macro_conditions', {})
        }
    
    def evaluate_technical_criteria(self, trade: Dict, criterion: str) -> bool:
        """
        Evaluate technical criteria
        """
        indicators = trade.get('technical_indicators', {})
        
        if criterion == 'trend':
            return indicators.get('trend', 'neutral') != 'neutral'
        elif criterion == 'momentum':
            return abs(indicators.get('momentum', 0.0)) > 0.5
        elif criterion == 'volatility':
            return indicators.get('volatility', 0.0) > 0.01
        elif criterion == 'support_resistance':
            return bool(indicators.get('support_resistance'))
        elif criterion == 'volume':
            return indicators.get('volume', 0.0) > 0.0
        
        return False
    
    def evaluate_fundamental_criteria(self, trade: Dict, criterion: str) -> bool:
        """
        Evaluate fundamental criteria
        """
        data = trade.get('fundamental_data', {})
        
        if criterion == 'earnings':
            return data.get('earnings_growth', 0.0) > 0.0
        elif criterion == 'valuation':
            return data.get('pe_ratio', 0.0) > 0.0
        elif criterion == 'growth':
            return data.get('revenue_growth', 0.0) > 0.0
        elif criterion == 'financial_health':
            return data.get('debt_ratio', 0.0) < 0.5
        elif criterion == 'industry_position':
            return data.get('market_share', 0.0) > 0.0
        
        return False
    
    def evaluate_sentiment_criteria(self, trade: Dict, criterion: str) -> bool:
        """
        Evaluate sentiment criteria
        """
        data = trade.get('sentiment_data', {})
        
        if criterion == 'news':
            return data.get('news_sentiment', 0.0) > 0.0
        elif criterion == 'social_media':
            return data.get('social_sentiment', 0.0) > 0.0
        elif criterion == 'analyst':
            return data.get('analyst_sentiment', 0.0) > 0.0
        elif criterion == 'volume_anomaly':
            return data.get('volume_anomaly', False)
        elif criterion == 'price_action':
            return data.get('price_action', False)
        
        return False
    
    def evaluate_macro_criteria(self, trade: Dict, criterion: str) -> bool:
        """
        Evaluate macro criteria
        """
        data = trade.get('macro_data', {})
        
        if criterion == 'economic_data':
            return data.get('economic_sentiment', 0.0) > 0.0
        elif criterion == 'interest_rates':
            return data.get('rate_trend', 'neutral') != 'neutral'
        elif criterion == 'inflation':
            return data.get('inflation_rate', 0.0) > 0.0
        elif criterion == 'currency':
            return data.get('currency_strength', 0.0) > 0.0
        elif criterion == 'commodities':
            return data.get('commodity_trend', 'neutral') != 'neutral'
        
        return False
    
    def evaluate_ml_criteria(self, trade: Dict, criterion: str) -> bool:
        """
        Evaluate machine learning criteria
        """
        data = trade.get('ml_data', {})
        
        if criterion == 'model_confidence':
            return data.get('confidence', 0.0) > 0.7
        elif criterion == 'feature_importance':
            return bool(data.get('important_features'))
        elif criterion == 'backtest_performance':
            return data.get('backtest_sharpe', 0.0) > 1.0
        elif criterion == 'risk_metrics':
            return data.get('max_drawdown', 0.0) < 0.2
        
        return False
    
    async def get_trade_explanation(self, trade_id: str) -> Optional[TradeExplanation]:
        """
        Get explanation for trade
        """
        try:
            data = await self.redis_pool.hgetall(f"trade_explanation:{trade_id}")
            if data:
                return TradeExplanation.parse_obj(data)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting explanation: {str(e)}"
            )
    
    async def get_all_explanations(self) -> List[TradeExplanation]:
        """
        Get all stored explanations
        """
        try:
            keys = await self.redis_pool.keys("trade_explanation:*")
            explanations = []
            
            for key in keys:
                data = await self.redis_pool.hgetall(key)
                if data:
                    explanations.append(TradeExplanation.parse_obj(data))
            
            return explanations
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting explanations: {str(e)}"
            )
    
    async def clear_old_explanations(self, days: int = 30) -> None:
        """
        Clear explanations older than X days
        """
        try:
            explanations = await self.get_all_explanations()
            current_time = datetime.now()
            
            for explanation in explanations:
                if (current_time - explanation.timestamp).days > days:
                    await self.redis_pool.delete(
                        f"trade_explanation:{explanation.timestamp.strftime('%Y%m%d_%H%M%S')}")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error clearing explanations: {str(e)}"
            )
