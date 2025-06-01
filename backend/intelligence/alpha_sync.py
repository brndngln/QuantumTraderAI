import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum
import json

class AlphaSource(Enum):
    THIRTEF = "13f"
    WHALE_WALLET = "whale_wallet"
    BLOCK_TRADE = "block_trade"
    OPTIONS = "options"

class AlphaSignal(BaseModel):
    source: AlphaSource
    symbol: str
    size: float
    price: float
    timestamp: datetime
    confidence: float
    description: str

class AlphaSyncEngine:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.signal_thresholds = {
            AlphaSource.THIRTEF: 10000000,  # $10M
            AlphaSource.WHALE_WALLET: 500000,  # $500K
            AlphaSource.BLOCK_TRADE: 1000000,  # $1M
            AlphaSource.OPTIONS: 10000  # 10K contracts
        }
        
    async def detect_alpha_signals(self) -> List[AlphaSignal]:
        """
        Detect alpha signals from various sources
        """
        try:
            signals = []
            
            # Check all sources
            for source in AlphaSource:
                new_signals = await self.check_source(source)
                signals.extend(new_signals)
            
            # Filter and score signals
            filtered_signals = []
            for signal in signals:
                if signal.size >= self.signal_thresholds[signal.source]:
                    signal.confidence = self.calculate_confidence(signal)
                    filtered_signals.append(signal)
            
            # Store signals
            for signal in filtered_signals:
                await self.redis_pool.rpush(
                    "alpha_signals",
                    signal.json()
                )
            
            return filtered_signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting alpha signals: {str(e)}"
            )
    
    async def check_source(self, source: AlphaSource) -> List[AlphaSignal]:
        """
        Check specific alpha source
        """
        try:
            if source == AlphaSource.THIRTEF:
                return await self.check_13f()
            elif source == AlphaSource.WHALE_WALLET:
                return await self.check_whale_wallet()
            elif source == AlphaSource.BLOCK_TRADE:
                return await self.check_block_trades()
            else:
                return await self.check_options()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking source {source.value}: {str(e)}"
            )
    
    async def check_13f(self) -> List[AlphaSignal]:
        """
        Check 13F filings
        """
        try:
            # Get recent filings
            filings = await self.get_recent_filings()
            
            signals = []
            for filing in filings:
                if filing['change'] > 0:
                    signals.append(AlphaSignal(
                        source=AlphaSource.THIRTEF,
                        symbol=filing['symbol'],
                        size=filing['amount'],
                        price=filing['price'],
                        timestamp=filing['timestamp'],
                        confidence=0.8,
                        description=f"Institutional buying detected"
                    ))
            
            return signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking 13F: {str(e)}"
            )
    
    async def check_whale_wallet(self) -> List[AlphaSignal]:
        """
        Check whale wallet movements
        """
        try:
            # Get recent wallet movements
            movements = await self.get_wallet_movements()
            
            signals = []
            for movement in movements:
                if movement['size'] > self.signal_thresholds[AlphaSource.WHALE_WALLET]:
                    signals.append(AlphaSignal(
                        source=AlphaSource.WHALE_WALLET,
                        symbol=movement['symbol'],
                        size=movement['size'],
                        price=movement['price'],
                        timestamp=movement['timestamp'],
                        confidence=0.7,
                        description=f"Whale wallet movement detected"
                    ))
            
            return signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking whale wallet: {str(e)}"
            )
    
    async def check_block_trades(self) -> List[AlphaSignal]:
        """
        Check block trades
        """
        try:
            # Get recent block trades
            trades = await self.get_block_trades()
            
            signals = []
            for trade in trades:
                if trade['size'] > self.signal_thresholds[AlphaSource.BLOCK_TRADE]:
                    signals.append(AlphaSignal(
                        source=AlphaSource.BLOCK_TRADE,
                        symbol=trade['symbol'],
                        size=trade['size'],
                        price=trade['price'],
                        timestamp=trade['timestamp'],
                        confidence=0.9,
                        description=f"Block trade detected"
                    ))
            
            return signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking block trades: {str(e)}"
            )
    
    async def check_options(self) -> List[AlphaSignal]:
        """
        Check unusual options activity
        """
        try:
            # Get recent options activity
            activity = await self.get_options_activity()
            
            signals = []
            for trade in activity:
                if trade['volume'] > self.signal_thresholds[AlphaSource.OPTIONS]:
                    signals.append(AlphaSignal(
                        source=AlphaSource.OPTIONS,
                        symbol=trade['symbol'],
                        size=trade['volume'],
                        price=trade['price'],
                        timestamp=trade['timestamp'],
                        confidence=0.6,
                        description=f"Unusual options activity detected"
                    ))
            
            return signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking options: {str(e)}"
            )
    
    def calculate_confidence(self, signal: AlphaSignal) -> float:
        """
        Calculate confidence score for signal
        """
        base_confidence = {
            AlphaSource.THIRTEF: 0.8,
            AlphaSource.WHALE_WALLET: 0.7,
            AlphaSource.BLOCK_TRADE: 0.9,
            AlphaSource.OPTIONS: 0.6
        }
        
        # Adjust based on size
        size_factor = min(1.0, signal.size / self.signal_thresholds[signal.source])
        
        return base_confidence[signal.source] * size_factor
    
    async def get_recent_filings(self) -> List[Dict]:
        """
        Get recent 13F filings
        """
        # Implementation depends on data source
        return []
    
    async def get_wallet_movements(self) -> List[Dict]:
        """
        Get whale wallet movements
        """
        # Implementation depends on data source
        return []
    
    async def get_block_trades(self) -> List[Dict]:
        """
        Get recent block trades
        """
        # Implementation depends on data source
        return []
    
    async def get_options_activity(self) -> List[Dict]:
        """
        Get unusual options activity
        """
        # Implementation depends on data source
        return []
    
    async def get_alpha_signals(self) -> List[AlphaSignal]:
        """
        Get all stored alpha signals
        """
        try:
            signals = []
            raw_signals = await self.redis_pool.lrange("alpha_signals", 0, -1)
            
            for signal in raw_signals:
                signals.append(AlphaSignal.parse_raw(signal))
            
            return signals
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting alpha signals: {str(e)}"
            )
    
    async def clear_old_signals(self, days: int = 30) -> None:
        """
        Clear signals older than X days
        """
        try:
            signals = await self.get_alpha_signals()
            current_time = datetime.now()
            
            for signal in signals:
                if (current_time - signal.timestamp).days > days:
                    await self.redis_pool.lrem(
                        "alpha_signals",
                        0,
                        signal.json()
                    )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error clearing old signals: {str(e)}"
            )
