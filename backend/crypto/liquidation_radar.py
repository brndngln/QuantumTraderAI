import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum
import json

class LiquidationType(Enum):
    SHORT = "short"
    LONG = "long"
    BOTH = "both"

class LiquidationCluster(BaseModel):
    timestamp: datetime
    symbol: str
    type: LiquidationType
    size: float
    price: float
    volume: float
    impact: float
    confidence: float

class LiquidationRadar:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.thresholds = {
            'volume': 1000000,  # 1M USD
            'price_impact': 0.05,  # 5%
            'cluster_size': 5,
            'time_window': 300  # 5 minutes
        }
        
    async def detect_liquidations(self, symbol: str) -> List[LiquidationCluster]:
        """
        Detect liquidation clusters
        """
        try:
            # Get recent trades
            trades = await self.get_recent_trades(symbol)
            
            # Detect clusters
            clusters = self.detect_clusters(trades)
            
            # Filter and score clusters
            valid_clusters = []
            for cluster in clusters:
                if self.is_valid_cluster(cluster):
                    cluster.confidence = self.calculate_confidence(cluster)
                    valid_clusters.append(cluster)
            
            # Store clusters
            for cluster in valid_clusters:
                await self.redis_pool.rpush(
                    f"liquidations:{symbol}",
                    cluster.json()
                )
            
            return valid_clusters
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error detecting liquidations: {str(e)}"
            )
    
    def detect_clusters(self, trades: List[Dict]) -> List[LiquidationCluster]:
        """
        Detect liquidation clusters in trades
        """
        clusters = []
        current_cluster = None
        
        for trade in trades:
            if current_cluster is None:
                current_cluster = self.create_cluster(trade)
            else:
                if self.is_same_cluster(trade, current_cluster):
                    self.update_cluster(trade, current_cluster)
                else:
                    clusters.append(current_cluster)
                    current_cluster = self.create_cluster(trade)
        
        if current_cluster:
            clusters.append(current_cluster)
            
        return clusters
    
    def is_same_cluster(self, trade: Dict, cluster: LiquidationCluster) -> bool:
        """
        Check if trade belongs to same cluster
        """
        time_diff = (trade['timestamp'] - cluster.timestamp).total_seconds()
        price_diff = abs(trade['price'] - cluster.price) / cluster.price
        
        return (
            time_diff < self.thresholds['time_window'] and
            price_diff < self.thresholds['price_impact']
        )
    
    def create_cluster(self, trade: Dict) -> LiquidationCluster:
        """
        Create new liquidation cluster
        """
        return LiquidationCluster(
            timestamp=trade['timestamp'],
            symbol=trade['symbol'],
            type=self.determine_type(trade),
            size=trade['size'],
            price=trade['price'],
            volume=trade['volume'],
            impact=self.calculate_impact(trade),
            confidence=0.0  # Will be calculated later
        )
    
    def update_cluster(self, trade: Dict, cluster: LiquidationCluster) -> None:
        """
        Update existing cluster with new trade
        """
        cluster.size += trade['size']
        cluster.volume += trade['volume']
        cluster.price = (cluster.price * cluster.volume + trade['price'] * trade['volume']) / (cluster.volume + trade['volume'])
        cluster.impact = self.calculate_impact(cluster)
    
    def determine_type(self, trade: Dict) -> LiquidationType:
        """
        Determine liquidation type
        """
        if trade['side'] == 'sell' and trade['price'] < trade['entry_price']:
            return LiquidationType.LONG
        elif trade['side'] == 'buy' and trade['price'] > trade['entry_price']:
            return LiquidationType.SHORT
        return LiquidationType.BOTH
    
    def calculate_impact(self, cluster: LiquidationCluster) -> float:
        """
        Calculate price impact of cluster
        """
        # Implementation depends on market data
        return 0.0
    
    def is_valid_cluster(self, cluster: LiquidationCluster) -> bool:
        """
        Check if cluster meets criteria
        """
        return (
            cluster.volume >= self.thresholds['volume'] and
            cluster.impact >= self.thresholds['price_impact'] and
            cluster.size >= self.thresholds['cluster_size']
        )
    
    def calculate_confidence(self, cluster: LiquidationCluster) -> float:
        """
        Calculate confidence score for cluster
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust for volume
        confidence += min(0.3, cluster.volume / self.thresholds['volume'])
        
        # Adjust for impact
        confidence += min(0.2, cluster.impact / self.thresholds['price_impact'])
        
        return min(1.0, confidence)
    
    async def get_recent_trades(self, symbol: str) -> List[Dict]:
        """
        Get recent trades from exchange
        """
        try:
            # Implementation depends on exchange API
            return []
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting trades: {str(e)}"
            )
    
    async def get_liquidation_clusters(self, symbol: str) -> List[LiquidationCluster]:
        """
        Get all stored liquidation clusters
        """
        try:
            clusters = []
            raw_clusters = await self.redis_pool.lrange(f"liquidations:{symbol}", 0, -1)
            
            for cluster in raw_clusters:
                clusters.append(LiquidationCluster.parse_raw(cluster))
            
            return clusters
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting clusters: {str(e)}"
            )
    
    async def clear_old_clusters(self, days: int = 1) -> None:
        """
        Clear clusters older than X days
        """
        try:
            clusters = await self.get_liquidation_clusters()
            current_time = datetime.now()
            
            for cluster in clusters:
                if (current_time - cluster.timestamp).days > days:
                    await self.redis_pool.lrem(
                        f"liquidations:{symbol}",
                        0,
                        cluster.json()
                    )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error clearing old clusters: {str(e)}"
            )
    
    async def analyze_market_impact(self, symbol: str) -> Dict:
        """
        Analyze market impact of liquidations
        """
        try:
            clusters = await self.get_liquidation_clusters(symbol)
            
            if not clusters:
                return {
                    'impact': 0.0,
                    'confidence': 0.0,
                    'recommendation': 'neutral'
                }
            
            # Calculate total impact
            total_impact = sum(c.impact * c.confidence for c in clusters)
            avg_impact = total_impact / len(clusters)
            
            # Determine recommendation
            recommendation = 'neutral'
            if avg_impact > 0.1:
                recommendation = 'caution'
            elif avg_impact < -0.1:
                recommendation = 'opportunity'
            
            return {
                'impact': avg_impact,
                'confidence': sum(c.confidence for c in clusters) / len(clusters),
                'recommendation': recommendation,
                'clusters': len(clusters)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing impact: {str(e)}"
            )
