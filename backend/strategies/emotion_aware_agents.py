import numpy as np
import pandas as pd
from typing import Dict
import ccxt
from enum import Enum

class MarketEmotion(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class EmotionAwareAgent:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.exchange = ccxt.binance()
        self.sentiment = 0.0
        self.emotion = MarketEmotion.NEUTRAL

    def analyze_market_sentiment(self) -> float:
        """
        Analyze market sentiment using multiple indicators
        """
        try:
            # Get recent price data
            data = self.get_price_data()
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(data)
            macd = self.calculate_macd(data)
            
            # Get news sentiment
            news_sentiment = self.get_news_sentiment()
            
            # Combine signals
            sentiment = (rsi + macd + news_sentiment) / 3
            
            return float(np.clip(sentiment, -1, 1))
        except Exception:
            return 0.0  # Neutral sentiment if error occurs

    def get_price_data(self) -> pd.DataFrame:
        """
        Get recent price data from exchange
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            raise Exception(f"Error fetching price data: {str(e)}")

    def calculate_rsi(self, data: pd.DataFrame) -> float:
        """
        Calculate RSI indicator
        """
        try:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Convert to sentiment score
            sentiment = (rsi.iloc[-1] - 50) / 50
            return float(np.clip(sentiment, -1, 1))
        except Exception as e:
            raise Exception(f"Error calculating RSI: {str(e)}")

    def calculate_macd(self, data: pd.DataFrame) -> float:
        """
        Calculate MACD indicator
        """
        try:
            exp1 = data['close'].ewm(span=12, adjust=False).mean()
            exp2 = data['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Convert to sentiment score
            sentiment = (macd.iloc[-1] - signal.iloc[-1]) / (macd.std() + 1e-8)
            return float(np.clip(sentiment, -1, 1))
        except Exception as e:
            raise Exception(f"Error calculating MACD: {str(e)}")

    def get_news_sentiment(self) -> float:
        """
        Get news sentiment analysis
        """
        try:
            # This would typically fetch news and analyze sentiment
            # For now, return random sentiment
            return float(np.random.normal(0, 0.3))
        except Exception:
            return 0.0  # Neutral sentiment if error occurs

    def update_emotion(self):
        """
        Update market emotion based on sentiment
        """
        self.sentiment = self.analyze_market_sentiment()
        
        if self.sentiment > 0.3:
            self.emotion = MarketEmotion.BULLISH
        elif self.sentiment < -0.3:
            self.emotion = MarketEmotion.BEARISH
        else:
            self.emotion = MarketEmotion.NEUTRAL

    def get_trading_signal(self) -> Dict:
        """
        Generate trading signal based on emotion
        """
        self.update_emotion()
        
        signal = {
            'symbol': self.symbol,
            'sentiment': self.sentiment,
            'emotion': self.emotion.value,
            'action': 'hold'
        }
        
        if self.emotion == MarketEmotion.BULLISH:
            signal['action'] = 'buy'
        elif self.emotion == MarketEmotion.BEARISH:
            signal['action'] = 'sell'
        
        return signal
