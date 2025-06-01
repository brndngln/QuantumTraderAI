import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self,
                 initial_capital: float = 100000.0,
                 commission: float = 0.001,
                 slippage: float = 0.0005,
                 max_positions: int = 10,
                 risk_per_trade: float = 0.01,
                 data_frequency: str = 'daily'):
        """
        Initialize backtesting framework
        
        Args:
            initial_capital: Starting capital
            commission: Trading commission
            slippage: Slippage percentage
            max_positions: Maximum concurrent positions
            risk_per_trade: Risk per trade
            data_frequency: Data frequency
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.data_frequency = data_frequency
        
        self.portfolio = None
        self.trades = []
        self.metrics = {}
        self.current_position = 0
        
    def initialize_portfolio(self, start_date: datetime) -> None:
        """Initialize portfolio"""
        try:
            self.portfolio = {
                'cash': self.initial_capital,
                'positions': {},
                'start_date': start_date,
                'end_date': None,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0.0,
                'max_drawdown': 0.0,
                'current_drawdown': 0.0,
                'peak_value': self.initial_capital
            }
            logger.info(f"Portfolio initialized with {self.initial_capital} capital")
            
        except Exception as e:
            logger.error(f"Error initializing portfolio: {str(e)}")
            raise

    def calculate_position_size(self, 
                              current_price: float, 
                              volatility: float) -> float:
        """Calculate position size based on risk"""
        try:
            # Base position size based on risk per trade
            position_size = (self.portfolio['cash'] * self.risk_per_trade) / (current_price * self.slippage)
            
            # Adjust for volatility
            position_size *= (1 / (volatility + 1e-6))
            
            return min(position_size, self.portfolio['cash'])
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def execute_trade(self, 
                     symbol: str, 
                     price: float, 
                     position_size: float, 
                     direction: str) -> Dict:
        """Execute a trade"""
        try:
            # Calculate costs
            commission = position_size * price * self.commission
            slippage_cost = position_size * price * self.slippage
            total_cost = commission + slippage_cost
            
            # Update portfolio
            self.portfolio['cash'] -= position_size * price + total_cost
            
            # Create trade record
            trade = {
                'symbol': symbol,
                'entry_price': price,
                'position_size': position_size,
                'direction': direction,
                'commission': commission,
                'slippage': slippage_cost,
                'entry_time': datetime.now(),
                'exit_price': None,
                'exit_time': None,
                'profit': None,
                'status': 'open'
            }
            
            # Add to trades list
            self.trades.append(trade)
            self.portfolio['total_trades'] += 1
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {}

    def close_trade(self, trade: Dict, exit_price: float) -> None:
        """Close a trade position"""
        try:
            # Calculate profit/loss
            if trade['direction'] == 'long':
                profit = (exit_price - trade['entry_price']) * trade['position_size']
            else:
                profit = (trade['entry_price'] - exit_price) * trade['position_size']
            
            # Update trade record
            trade['exit_price'] = exit_price
            trade['exit_time'] = datetime.now()
            trade['profit'] = profit
            trade['status'] = 'closed'
            
            # Update portfolio
            self.portfolio['cash'] += trade['position_size'] * exit_price + profit
            self.portfolio['total_profit'] += profit
            
            # Update trade statistics
            if profit > 0:
                self.portfolio['winning_trades'] += 1
            else:
                self.portfolio['losing_trades'] += 1
            
        except Exception as e:
            logger.error(f"Error closing trade: {str(e)}")
            raise

    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate backtesting metrics"""
        try:
            # Calculate basic metrics
            total_trades = len(self.trades)
            winning_trades = sum(1 for t in self.trades if t.get('profit', 0) > 0)
            losing_trades = total_trades - winning_trades
            
            # Calculate win rate
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate average profit/loss
            profits = [t['profit'] for t in self.trades if 'profit' in t]
            avg_profit = np.mean(profits) if profits else 0
            
            # Calculate Sharpe ratio
            returns = [(t['profit'] / t['position_size']) for t in self.trades if 'profit' in t]
            sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-6) if returns else 0
            
            # Calculate drawdown
            peak_value = max(self.portfolio['cash'], self.portfolio['peak_value'])
            current_drawdown = (peak_value - self.portfolio['cash']) / peak_value
            max_drawdown = max(current_drawdown, self.portfolio['max_drawdown'])
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'final_value': self.portfolio['cash'],
                'total_profit': self.portfolio['total_profit']
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}

    def run_backtest(self, 
                    strategy: callable, 
                    data: pd.DataFrame, 
                    start_date: datetime, 
                    end_date: datetime) -> Dict:
        """Run backtesting"""
        try:
            # Initialize portfolio
            self.initialize_portfolio(start_date)
            
            # Filter data by date range
            data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            # Run strategy on each time step
            for timestamp, row in data.iterrows():
                # Get strategy signals
                signals = strategy(row)
                
                # Execute trades based on signals
                for symbol, signal in signals.items():
                    if self.current_position < self.max_positions:
                        position_size = self.calculate_position_size(
                            row['close'],
                            row['volatility']
                        )
                        
                        if signal > 0:
                            self.execute_trade(symbol, row['close'], position_size, 'long')
                        elif signal < 0:
                            self.execute_trade(symbol, row['close'], position_size, 'short')
                
                # Update metrics
                self.metrics = self.calculate_metrics()
                
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            raise

    def plot_results(self) -> None:
        """Plot backtest results"""
        try:
            import matplotlib.pyplot as plt
            
            # Create equity curve
            equity_curve = pd.DataFrame({
                'date': [t['entry_time'] for t in self.trades],
                'value': [self.portfolio['cash']]
            })
            
            plt.figure(figsize=(12, 6))
            plt.plot(equity_curve['date'], equity_curve['value'])
            plt.title('Backtest Equity Curve')
            plt.xlabel('Date')
            plt.ylabel('Portfolio Value')
            plt.grid(True)
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting results: {str(e)}")
            raise

# Initialize global instance
backtester = Backtester()
