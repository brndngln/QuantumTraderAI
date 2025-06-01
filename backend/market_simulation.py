import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from backend.cost_analysis import cost_analyzer
from backend.metrics import Metrics

logger = logging.getLogger(__name__)

class MarketSimulator:
    def __init__(self,
                 market_data: pd.DataFrame,
                 order_book_depth: int = 10,
                 liquidity_threshold: float = 0.05,
                 market_impact_exponent: float = 0.6,
                 slippage_base: float = 0.0005):
        """
        Initialize market simulator
        
        Args:
            market_data: Market data DataFrame
            order_book_depth: Depth of order book to simulate
            liquidity_threshold: Threshold for liquidity impact
            market_impact_exponent: Exponent for market impact calculation
            slippage_base: Base slippage percentage
        """
        self.market_data = market_data
        self.order_book_depth = order_book_depth
        self.liquidity_threshold = liquidity_threshold
        self.market_impact_exponent = market_impact_exponent
        self.slippage_base = slippage_base
        self.metrics = Metrics()
        self.cost_analyzer = cost_analyzer
        
    def simulate_order_book(self, 
                          price: float, 
                          volume: float, 
                          side: str) -> Dict:
        """Simulate order book execution"""
        try:
            # Create simulated order book levels
            levels = []
            current_price = price
            remaining_volume = volume
            
            for i in range(self.order_book_depth):
                if side == 'buy':
                    level_price = current_price * (1 + self.slippage_base * (i + 1))
                else:
                    level_price = current_price * (1 - self.slippage_base * (i + 1))
                    
                level_volume = volume * (1 - i/self.order_book_depth)
                levels.append({
                    'price': level_price,
                    'volume': level_volume,
                    'remaining_volume': remaining_volume
                })
                remaining_volume -= level_volume
                
                if remaining_volume <= 0:
                    break
                    
            return {
                'levels': levels,
                'total_volume': volume,
                'average_price': np.mean([l['price'] for l in levels])
            }
            
        except Exception as e:
            logger.error(f"Error simulating order book: {str(e)}")
            return {}

    def calculate_market_impact(self, 
                              trade_size: float, 
                              market_volume: float) -> float:
        """Calculate market impact"""
        try:
            impact = trade_size / market_volume
            return impact ** self.market_impact_exponent
            
        except Exception as e:
            logger.error(f"Error calculating market impact: {str(e)}")
            return 0.0

    def simulate_trade(self, 
                      price: float, 
                      volume: float, 
                      side: str, 
                      market_volume: float) -> Dict:
        """Simulate trade execution"""
        try:
            # Calculate base slippage
            base_slippage = self.cost_analyzer.calculate_slippage(
                volume, price, market_volume
            )
            
            # Calculate market impact
            market_impact = self.calculate_market_impact(volume, market_volume)
            
            # Simulate order book execution
            order_book = self.simulate_order_book(price, volume, side)
            
            # Calculate execution price
            if side == 'buy':
                execution_price = price * (1 + base_slippage + market_impact)
            else:
                execution_price = price * (1 - base_slippage - market_impact)
                
            return {
                'execution_price': execution_price,
                'base_slippage': base_slippage,
                'market_impact': market_impact,
                'order_book': order_book,
                'total_cost': self.cost_analyzer.calculate_total_transaction_cost(
                    volume, execution_price, market_volume
                )
            }
            
        except Exception as e:
            logger.error(f"Error simulating trade: {str(e)}")
            return {}

    def simulate_market_impact(self, 
                             trades: List[Dict], 
                             market_volume: float) -> Dict:
        """Simulate market impact of multiple trades"""
        try:
            total_volume = sum(t['volume'] for t in trades)
            impact = self.calculate_market_impact(total_volume, market_volume)
            
            return {
                'total_volume': total_volume,
                'market_volume': market_volume,
                'market_impact': impact,
                'impact_percentage': impact * 100
            }
            
        except Exception as e:
            logger.error(f"Error simulating market impact: {str(e)}")
            return {}

    def simulate_liquidity(self, 
                         trades: List[Dict], 
                         market_volume: float) -> Dict:
        """Simulate liquidity impact"""
        try:
            total_volume = sum(t['volume'] for t in trades)
            liquidity_ratio = total_volume / market_volume
            
            if liquidity_ratio > self.liquidity_threshold:
                impact = (liquidity_ratio - self.liquidity_threshold) * 100
            else:
                impact = 0
                
            return {
                'total_volume': total_volume,
                'market_volume': market_volume,
                'liquidity_ratio': liquidity_ratio,
                'impact_percentage': impact
            }
            
        except Exception as e:
            logger.error(f"Error simulating liquidity: {str(e)}")
            return {}

    def simulate_trading_day(self, 
                           trades: List[Dict], 
                           market_volume: float) -> Dict:
        """Simulate a full trading day"""
        try:
            # Calculate market impact
            market_impact = self.simulate_market_impact(trades, market_volume)
            
            # Calculate liquidity impact
            liquidity_impact = self.simulate_liquidity(trades, market_volume)
            
            # Calculate total costs
            total_costs = sum(
                self.cost_analyzer.calculate_total_transaction_cost(
                    t['volume'], t['price'], market_volume
                )
                for t in trades
            )
            
            return {
                'market_impact': market_impact,
                'liquidity_impact': liquidity_impact,
                'total_costs': total_costs,
                'total_volume': sum(t['volume'] for t in trades)
            }
            
        except Exception as e:
            logger.error(f"Error simulating trading day: {str(e)}")
            return {}

    def plot_market_simulation(self, 
                             trades: List[Dict], 
                             market_volume: float) -> None:
        """Plot market simulation results"""
        try:
            import matplotlib.pyplot as plt
            
            # Create DataFrame
            df = pd.DataFrame(trades)
            
            # Plot volume distribution
            plt.figure(figsize=(15, 10))
            plt.subplot(2, 2, 1)
            df['volume'].plot(kind='bar')
            plt.title('Trade Volumes')
            
            # Plot price distribution
            plt.subplot(2, 2, 2)
            df['price'].plot()
            plt.title('Trade Prices')
            
            # Plot market impact
            plt.subplot(2, 2, 3)
            market_impact = self.simulate_market_impact(trades, market_volume)
            plt.bar(['Market Impact'], [market_impact['market_impact']])
            plt.title('Market Impact')
            
            # Plot liquidity impact
            plt.subplot(2, 2, 4)
            liquidity_impact = self.simulate_liquidity(trades, market_volume)
            plt.bar(['Liquidity Impact'], [liquidity_impact['impact_percentage']])
            plt.title('Liquidity Impact')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting market simulation: {str(e)}")
            raise

    def get_simulation_metrics(self) -> Dict:
        """Get simulation parameters"""
        return {
            'order_book_depth': self.order_book_depth,
            'liquidity_threshold': self.liquidity_threshold,
            'market_impact_exponent': self.market_impact_exponent,
            'slippage_base': self.slippage_base
        }

# Initialize global instance
market_simulator = MarketSimulator()
