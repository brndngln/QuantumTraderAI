from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import os
import pandas as pd
from fastapi import HTTPException
from redis import asyncio as aioredis
from pydantic import BaseModel
from enum import Enum
import matplotlib.pyplot as plt
import mplfinance as mpf

class TradeReason(Enum):
    STRATEGY = "strategy"
    SENTIMENT = "sentiment"
    VOLATILITY = "volatility"
    NEWS = "news"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"

class TradeEntry(BaseModel):
    timestamp: datetime
    symbol: str
    price: float
    size: float
    reason: TradeReason
    market_context: Dict[str, Any]
    optional: Optional[str] = None
    screenshot_path: Optional[str] = None

class TradeExit(BaseModel):
    timestamp: datetime
    price: float
    profit: float
    duration: float
    reason: str

class TradeSummary(BaseModel):
    date: datetime
    trades: List[Dict]
    total_profit: float
    win_rate: float
    avg_profit: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float

class TradeJournal:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.logs_dir = "logs"
        os.makedirs(self.logs_dir, exist_ok=True)
    
    async def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:
        """
        Log a complete trade with entry and exit
        """
        try:
            # Create trade record
            trade_record = {
                'entry': entry.dict(),
                'exit': exit.dict(),
                'profit': exit.profit,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in Redis
            await self.redis_pool.rpush(
                'trade_journal',
                json.dumps(trade_record)
            )
            
            # Save to daily file
            date_str = datetime.now().strftime('%Y-%m-%d')
            daily_file = os.path.join(self.logs_dir, f'trade_journal_{date_str}.json')
            
            if not os.path.exists(daily_file):
                with open(daily_file, 'w') as f:
                    json.dump([], f)
            
            with open(daily_file, 'r+') as f:
                data = json.load(f)
                data.append(trade_record)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            
            # Generate summary if end of day
            if datetime.now().hour == 23 and datetime.now().minute >= 55:
                await self.generate_daily_summary(date_str)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error logging trade: {str(e)}"
            )
    
    async def generate_daily_summary(self, date_str: str) -> None:
        """
        Generate daily trade summary
        """
        try:
            # Load trades for day
            daily_file = os.path.join(self.logs_dir, f'trade_journal_{date_str}.json')
            with open(daily_file, 'r') as f:
                trades = json.load(f)
            
            # Calculate metrics
            total_profit = sum(t['exit']['profit'] for t in trades)
            winning_trades = [t for t in trades if t['exit']['profit'] > 0]
            losing_trades = [t for t in trades if t['exit']['profit'] <= 0]
            
            summary = TradeSummary(
                date=datetime.strptime(date_str, '%Y-%m-%d'),
                trades=[t for t in trades],
                total_profit=total_profit,
                win_rate=len(winning_trades) / len(trades) if trades else 0,
                avg_profit=sum(t['exit']['profit'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                avg_loss=sum(t['exit']['profit'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                max_drawdown=min(t['exit']['profit'] for t in losing_trades) if losing_trades else 0,
                sharpe_ratio=self.calculate_sharpe_ratio(trades)
            )
            
            # Save summary
            summary_file = os.path.join(self.logs_dir, f'trade_summary_{date_str}.json')
            with open(summary_file, 'w') as f:
                json.dump(summary.dict(), f, indent=2)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating summary: {str(e)}"
            )
    
    def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """
        Calculate Sharpe ratio for trades
        """
        returns = [t['exit']['profit'] for t in trades]
        if not returns:
            return 0.0
            
        mean_return = sum(returns) / len(returns)
        std_dev = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
        
        return mean_return / std_dev if std_dev > 0 else 0.0
    
    async def generate_screenshot(self, symbol: str, timeframe: str = '1d') -> str:
        """
        Generate chart screenshot for trade analysis
        """
        try:
            # Get historical data (implementation depends on data source)
            data = await self.get_historical_data(symbol, timeframe)
            
            # Create chart
            plt.figure(figsize=(10, 6))
            mpf.plot(data, type='candle', style='yahoo', title=f'{symbol} {timeframe} Chart')
            
            # Save screenshot
            screenshot_path = os.path.join(
                self.logs_dir,
                f'chart_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            )
            plt.savefig(screenshot_path)
            plt.close()
            
            return screenshot_path
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating screenshot: {str(e)}"
            )
    
    async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Get historical price data
        """
        # Implementation depends on data source
        return pd.DataFrame()
