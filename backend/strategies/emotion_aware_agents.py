import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import ccxt
from pydantic import BaseModel
from fastapi import HTTPException
from enum import Enum
import yfinance as yf
from scipy.stats import norm

class MarketEmotion(Enum):
    FEAR = "fear"
    GREED = "greed"
    NEUTRAL = "neutral"

class EmotionState(Enum):
    CALM = 0
    CAUTIOUS = 1
    ALERT = 2
    PANIC = 3

class EmotionMetrics(BaseModel):
    market_emotion: MarketEmotion
    volatility: float
    sentiment_score: float
    risk_level: float
    emotion_state: EmotionState
    timestamp: datetime

class EmotionAwareAgent:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.volatility_thresholds = {
            'low': 0.01,
            'medium': 0.03,
            'high': 0.05
        }
        self.sentiment_thresholds = {
            'bearish': -0.3,
            'neutral': 0.3,
            'bullish': 0.6
        }
        
    def analyze_market_emotion(self, symbol: str) -> EmotionMetrics:
        """
        Analyze market emotion and volatility
        """
        try:
            # Get market data
            df = yf.download(symbol, period='1d', interval='1h')
            
            # Calculate volatility
            returns = df['Close'].pct_change()
            volatility = np.std(returns)
            
            # Calculate sentiment score
            sentiment = self._calculate_sentiment(symbol)
            
            # Determine market emotion
            market_emotion = self._determine_emotion(
                volatility,
                sentiment
            )
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(
                volatility,
                sentiment,
                market_emotion
            )
            
            # Determine emotion state
            emotion_state = self._determine_emotion_state(
                volatility,
                risk_level
            )
            
            return EmotionMetrics(
                market_emotion=market_emotion,
                volatility=volatility,
                sentiment_score=sentiment,
                risk_level=risk_level,
                emotion_state=emotion_state,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing market emotion: {str(e)}"
            )
    
    def _calculate_sentiment(self, symbol: str) -> float:
        """
        Calculate market sentiment using multiple indicators
        """
        try:
            # Get recent trades
            trades = self.exchange.fetch_trades(symbol)
            df = pd.DataFrame(trades)
            
            # Calculate volume-weighted sentiment
            df['volume_usd'] = df['amount'] * df['price']
            total_volume = df['volume_usd'].sum()
            
            # Calculate price momentum
            df['returns'] = df['price'].pct_change()
            momentum = df['returns'].mean()
            
            # Calculate volume sentiment
            volume_sentiment = (df['volume_usd'] * df['returns']).sum() / total_volume
            
            # Combine metrics
            sentiment = (momentum + volume_sentiment) / 2
            
            return float(np.clip(sentiment, -1, 1))
            
        except Exception as e:
            return 0.0  # Neutral sentiment if error occurs
    
    def _determine_emotion(self, 
                         volatility: float, 
                         sentiment: float) -> MarketEmotion:
        """
        Determine market emotion based on volatility and sentiment
        """
        if volatility > self.volatility_thresholds['high']:
            if sentiment < self.sentiment_thresholds['bearish']:
                return MarketEmotion.FEAR
            elif sentiment > self.sentiment_thresholds['bullish']:
                return MarketEmotion.GREED
            return MarketEmotion.NEUTRAL
            
        elif volatility > self.volatility_thresholds['medium']:
            if sentiment < self.sentiment_thresholds['neutral']:
                return MarketEmotion.FEAR
            elif sentiment > self.sentiment_thresholds['neutral']:
                return MarketEmotion.GREED
            return MarketEmotion.NEUTRAL
            
        return MarketEmotion.NEUTRAL
    
    def _calculate_risk_level(self, 
                             volatility: float, 
                             sentiment: float, 
                             emotion: MarketEmotion) -> float:
        """
        Calculate risk level based on market conditions
        """
        risk = volatility * abs(sentiment)
        
        if emotion == MarketEmotion.FEAR:
            risk *= 1.5
        elif emotion == MarketEmotion.GREED:
            risk *= 1.2
            
        return float(np.clip(risk, 0, 1))
    
    def _determine_emotion_state(self, 
                               volatility: float, 
                               risk_level: float) -> EmotionState:
        """
        Determine agent's emotion state
        """
        if risk_level > 0.8:
            return EmotionState.PANIC
        elif risk_level > 0.5:
            return EmotionState.ALERT
        elif volatility > self.volatility_thresholds['medium']:
            return EmotionState.CAUTION
        return EmotionState.CALM
    
    def adjust_strategy(self, 
                       emotion_metrics: EmotionMetrics, 
                       current_strategy: Dict) -> Dict:
        """
        Adjust trading strategy based on market emotion
        """
        adjusted_strategy = current_strategy.copy()
        
        # Adjust position size
        if emotion_metrics.emotion_state in [EmotionState.ALERT, EmotionState.PANIC]:
            adjusted_strategy['position_size'] *= 0.5
        elif emotion_metrics.emotion_state == EmotionState.CAUTION:
            adjusted_strategy['position_size'] *= 0.7
            
        # Adjust stop loss
        if emotion_metrics.emotion_state in [EmotionState.ALERT, EmotionState.PANIC]:
            adjusted_strategy['stop_loss'] *= 1.2
        elif emotion_metrics.emotion_state == EmotionState.CAUTION:
            adjusted_strategy['stop_loss'] *= 1.1
            
        # Adjust take profit
        if emotion_metrics.emotion_state == EmotionState.CALM:
            adjusted_strategy['take_profit'] *= 1.1
        elif emotion_metrics.emotion_state == EmotionState.PANIC:
            adjusted_strategy['take_profit'] *= 0.8
            
        return adjusted_strategy
