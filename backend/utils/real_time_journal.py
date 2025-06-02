from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi import HTTPException
import json
import plotly.graph_objects as go
from enum import Enum
from transformers import pipeline

logger = logging.getLogger(__name__)

# Initialize journaling pipeline
JOURNALING_PIPELINE = pipeline(
    "text-generation",
    model="gpt2"
)

class TradeAction(Enum):
    ENTER = "enter"
    EXIT = "exit"
    ADJUST = "adjust"

class TradeEntry(BaseModel):
    symbol: str
    action: TradeAction
    price: float
    size: float
    timestamp: datetime
    reason: str
    metadata: Dict

class TradeExit(BaseModel):
    symbol: str
    price: float
    pnl: float
    timestamp: datetime
    reason: str
    metadata: Dict

class TradeJournal:
    def __init__(self):
        self.entries = []
        self.exits = []
        self.active_trades = {}
        self.last_summary = None
        
    def log_trade_entry(self, entry: TradeEntry) -> Dict:
        """
        Log a trade entry
        
        Args:
            entry: TradeEntry object
            
        Returns:
            Dict containing trade summary
        """
        try:
            # Store entry
            self.entries.append(entry)
            self.active_trades[entry.symbol] = entry
            
            # Generate AI analysis
            analysis = self._generate_ai_analysis(entry)
            
            # Create summary
            summary = {
                'symbol': entry.symbol,
                'action': entry.action.value,
                'price': entry.price,
                'size': entry.size,
                'reason': entry.reason,
                'ai_analysis': analysis,
                'timestamp': entry.timestamp.isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error logging trade entry: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error logging trade entry: {str(e)}"
            )
            
    def log_trade_exit(self, exit_: TradeExit) -> Dict:
        """
        Log a trade exit
        
        Args:
            exit_: TradeExit object
            
        Returns:
            Dict containing trade summary
        """
        try:
            # Get entry data
            entry = self.active_trades.get(exit_.symbol)
            if not entry:
                raise HTTPException(
                    status_code=400,
                    detail="No active trade found for this symbol"
                )
            
            # Store exit
            self.exits.append(exit_)
            del self.active_trades[exit_.symbol]
            
            # Generate AI analysis
            analysis = self._generate_ai_analysis(exit_, entry)
            
            # Create summary
            summary = {
                'symbol': exit_.symbol,
                'entry_price': entry.price,
                'exit_price': exit_.price,
                'pnl': exit_.pnl,
                'duration': (exit_.timestamp - entry.timestamp).total_seconds(),
                'reason': exit_.reason,
                'ai_analysis': analysis,
                'timestamp': exit_.timestamp.isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error logging trade exit: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error logging trade exit: {str(e)}"
            )
            
    def _generate_ai_analysis(self, trade: TradeEntry, entry: Optional[TradeEntry] = None) -> str:
        """
        Generate AI analysis for trade
        """
        try:
            # Create context
            context = f"Trade for {trade.symbol} at {trade.price}"
            if entry:
                context += f"\nEntry price: {entry.price}\nP&L: {trade.pnl}"
            
            # Generate analysis
            prompt = f"""
            Analyze this trade:
            {context}
            
            Provide:
            1. Trade outcome assessment
            2. Key factors
            3. Lessons learned
            """
            
            analysis = JOURNALING_PIPELINE(prompt)[0]['generated_text']
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            return "Error generating AI analysis"
            
    def get_trade_summary(self, symbol: str) -> Dict:
        """
        Get summary of all trades for a symbol
        
        Returns:
            Dict containing:
            - total_trades: Number of trades
            - avg_pnl: Average P&L
            - win_rate: Win rate
            - max_drawdown: Maximum drawdown
            - ai_insights: AI-generated insights
        """
        try:
            # Get all trades for symbol
            trades = [
                (e, x) for e, x in zip(self.entries, self.exits)
                if e.symbol == symbol
            ]
            
            if not trades:
                return {
                    'total_trades': 0,
                    'avg_pnl': 0.0,
                    'win_rate': 0.0,
                    'max_drawdown': 0.0,
                    'ai_insights': "No trades found"
                }
            
            # Calculate statistics
            pnls = [x.pnl for _, x in trades]
            avg_pnl = np.mean(pnls)
            win_rate = sum(1 for pnl in pnls if pnl > 0) / len(pnls)
            max_drawdown = min(pnls)
            
            # Generate AI insights
            insights = self._generate_trade_insights(trades)
            
            return {
                'total_trades': len(trades),
                'avg_pnl': float(avg_pnl),
                'win_rate': float(win_rate),
                'max_drawdown': float(max_drawdown),
                'ai_insights': insights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trade summary: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting trade summary: {str(e)}"
            )
            
    def _generate_trade_insights(self, trades: List[tuple]) -> str:
        """
        Generate AI insights for trade history
        """
        try:
            # Create context
            context = "Trade history:\n"
            for entry, exit_ in trades:
                context += f"\nSymbol: {entry.symbol}\n"
                context += f"Entry: {entry.price} Exit: {exit_.price}\nP&L: {exit_.pnl}\n"
            
            # Generate insights
            prompt = f"""
            Analyze this trade history:
            {context}
            
            Provide:
            1. Pattern recognition
            2. Risk management insights
            3. Strategy recommendations
            """
            
            insights = JOURNALING_PIPELINE(prompt)[0]['generated_text']
            return insights
            
        except Exception as e:
            logger.error(f"Error generating trade insights: {str(e)}")
            return "Error generating trade insights"
            
    def generate_performance_chart(self, symbol: str) -> str:
        """
        Generate performance chart for a symbol
        
        Returns:
            HTML string of the chart
        """
        try:
            # Get trades
            trades = [
                (e, x) for e, x in zip(self.entries, self.exits)
                if e.symbol == symbol
            ]
            
            if not trades:
                return "No trades found"
                
            # Create data for chart
            timestamps = []
            pnls = []
            cumulative_pnl = 0
            
            for entry, exit_ in trades:
                timestamps.append(entry.timestamp)
                cumulative_pnl += exit_.pnl
                pnls.append(cumulative_pnl)
                
            # Create chart
            fig = go.Figure()
            
            # Add P&L line
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=pnls,
                mode='lines+markers',
                name='Cumulative P&L'
            ))
            
            # Add markers for trades
            for i, (entry, exit_) in enumerate(trades):
                fig.add_annotation(
                    x=entry.timestamp,
                    y=pnls[i],
                    text=f"Entry: {entry.price}<br>Exit: {exit_.price}",
                    showarrow=True,
                    arrowhead=1
                )
            
            fig.update_layout(
                title=f'{symbol} Trade Performance',
                xaxis_title='Time',
                yaxis_title='Cumulative P&L',
                width=800,
                height=600
            )
            
            return fig.to_html(full_html=False)
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating chart: {str(e)}"
            )
