import numpy as np
from fastapi import HTTPException
from datetime import datetime
from typing import Dict

class MarketGenerator:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.current_price = 100.0  # Starting price
        self.volatility = 0.01  # 1% daily volatility
        self.trend = 0.0  # No trend initially
        self.last_update = datetime.now()

    def generate_price(self) -> float:
        """
        Generate next price based on market conditions
        """
        try:
            # Calculate time since last update
            time_diff = (datetime.now() - self.last_update).total_seconds() / 3600  # Convert to hours
            
            # Generate random noise
            noise = np.random.normal(0, self.volatility * np.sqrt(time_diff))
            
            # Update price with trend and noise
            self.current_price += self.trend * time_diff + noise
            
            # Apply bounds to prevent extreme values
            self.current_price = max(0.01, min(10000.0, self.current_price))
            
            # Update last update time
            self.last_update = datetime.now()
            
            return float(self.current_price)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating price: {str(e)}"
            )

    def set_volatility(self, volatility: float):
        """
        Set market volatility
        """
        try:
            self.volatility = max(0.0, min(1.0, volatility))  # Clamp between 0 and 1
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error setting volatility: {str(e)}"
            )

    def set_trend(self, trend: float):
        """
        Set market trend
        """
        try:
            self.trend = trend
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error setting trend: {str(e)}"
            )

class SyntheticMarketLab:
    def __init__(self):
        self.markets = {}
        self.data_store = {}

    def create_market(self, symbol: str) -> Dict:
        """
        Create a new synthetic market
        """
        try:
            if symbol in self.markets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Market {symbol} already exists"
                )
            
            self.markets[symbol] = MarketGenerator(symbol)
            return {
                'symbol': symbol,
                'status': 'created'
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating market: {str(e)}"
            )

    def get_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict:
        """
        Get historical market data
        """
        try:
            if symbol not in self.markets:
                raise HTTPException(
                    status_code=404,
                    detail=f"Market {symbol} not found"
                )
            
            market = self.markets[symbol]
            
            # Generate historical data
            timestamps = []
            prices = []
            
            for _ in range(limit):
                price = market.generate_price()
                timestamps.append(datetime.now().isoformat())
                prices.append(price)
            
            # Store data
            if symbol not in self.data_store:
                self.data_store[symbol] = []
            
            self.data_store[symbol].append({
                'timestamp': timestamps[-1],
                'price': prices[-1]
            })
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'data': [
                    {
                        'timestamp': ts,
                        'price': price
                    }
                    for ts, price in zip(timestamps, prices)
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting market data: {str(e)}"
            )

    def set_market_conditions(self, symbol: str, volatility: float, trend: float) -> Dict:
        """
        Set market conditions (volatility and trend)
        """
        try:
            if symbol not in self.markets:
                raise HTTPException(
                    status_code=404,
                    detail=f"Market {symbol} not found"
                )
            
            market = self.markets[symbol]
            market.set_volatility(volatility)
            market.set_trend(trend)
            
            return {
                'symbol': symbol,
                'volatility': volatility,
                'trend': trend,
                'status': 'updated'
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error setting market conditions: {str(e)}"
            )

    def get_market_state(self, symbol: str) -> Dict:
        """
        Get current market state
        """
        try:
            if symbol not in self.markets:
                raise HTTPException(
                    status_code=404,
                    detail=f"Market {symbol} not found"
                )
            
            market = self.markets[symbol]
            
            return {
                'symbol': symbol,
                'current_price': market.current_price,
                'volatility': market.volatility,
                'trend': market.trend,
                'last_update': market.last_update.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting market state: {str(e)}"
            )
