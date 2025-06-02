import pandas as pd
from typing import Dict
from enum import Enum

class PatternType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class TechnicalPatterns:
    def __init__(self):
        self.patterns = {
            'rsi': self.detect_rsi_divergence,
            'macd': self.detect_macd_cross,
            'bb': self.detect_bollinger_breakout
        }

    def detect_patterns(self, data: pd.DataFrame) -> Dict[str, PatternType]:
        """
        Detect multiple technical patterns
        """
        signals = {}
        for name, detector in self.patterns.items():
            signals[name] = detector(data)
        return signals

    def detect_rsi_divergence(self, data: pd.DataFrame) -> PatternType:
        """
        Detect RSI divergence
        """
        rsi = self.calculate_rsi(data)
        if rsi.iloc[-1] > 70:
            return PatternType.BEARISH
        elif rsi.iloc[-1] < 30:
            return PatternType.BULLISH
        return PatternType.NEUTRAL

    def detect_macd_cross(self, data: pd.DataFrame) -> PatternType:
        """
        Detect MACD crossover
        """
        macd = self.calculate_macd(data)
        if macd['macd'].iloc[-1] > macd['signal'].iloc[-1]:
            return PatternType.BULLISH
        elif macd['macd'].iloc[-1] < macd['signal'].iloc[-1]:
            return PatternType.BEARISH
        return PatternType.NEUTRAL

    def detect_bollinger_breakout(self, data: pd.DataFrame) -> PatternType:
        """
        Detect Bollinger Bands breakout
        """
        bb = self.calculate_bollinger_bands(data)
        if data['Close'].iloc[-1] > bb['upper'].iloc[-1]:
            return PatternType.BEARISH
        elif data['Close'].iloc[-1] < bb['lower'].iloc[-1]:
            return PatternType.BULLISH
        return PatternType.NEUTRAL

    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI
        """
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD
        """
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return pd.DataFrame({
            'macd': macd,
            'signal': signal
        })

    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands
        """
        rolling_mean = data['Close'].rolling(window=20).mean()
        rolling_std = data['Close'].rolling(window=20).std()
        upper_band = rolling_mean + (rolling_std * 2)
        lower_band = rolling_mean - (rolling_std * 2)
        return pd.DataFrame({
            'upper': upper_band,
            'lower': lower_band
        })
