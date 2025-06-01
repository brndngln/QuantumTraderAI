import time
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime
from enum import Enum
import statistics

class BrokerStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

class BrokerMetrics(BaseModel):
    broker_id: str
    latency_ms: float
    cost_per_execution: float
    execution_time_ms: float
    success_rate: float
    last_heartbeat: datetime
    status: BrokerStatus

class BrokerHealthMonitor:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.latency_thresholds = {
            BrokerStatus.HEALTHY: 100.0,
            BrokerStatus.DEGRADED: 200.0,
            BrokerStatus.CRITICAL: 500.0
        }
        self.execution_thresholds = {
            'execution_time': 1000.0,  # 1 second
            'cost_per_execution': 0.01,  # 1% of trade value
            'success_rate': 0.95  # 95% success rate
        }
        
    async def monitor_broker(self, broker_id: str, metrics: Dict) -> BrokerStatus:
        """
        Monitor broker health and update status
        """
        try:
            # Create metrics object
            broker_metrics = BrokerMetrics(
                broker_id=broker_id,
                latency_ms=metrics['latency_ms'],
                cost_per_execution=metrics['cost_per_execution'],
                execution_time_ms=metrics['execution_time_ms'],
                success_rate=metrics['success_rate'],
                last_heartbeat=datetime.now(),
                status=self.calculate_broker_status(metrics)
            )
            
            # Store in Redis
            await self.redis_pool.hset(
                f"broker_metrics:{broker_id}",
                mapping=broker_metrics.dict()
            )
            
            # Update broker status
            await self.redis_pool.hset(
                f"broker_status:{broker_id}",
                mapping={
                    'status': broker_metrics.status.value,
                    'last_update': datetime.now().isoformat()
                }
            )
            
            return broker_metrics.status
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error monitoring broker: {str(e)}"
            )
    
    def calculate_broker_status(self, metrics: Dict) -> BrokerStatus:
        """
        Calculate broker status based on metrics
        """
        # Check latency
        if metrics['latency_ms'] > self.latency_thresholds[BrokerStatus.CRITICAL]:
            return BrokerStatus.CRITICAL
            
        # Check execution time
        if metrics['execution_time_ms'] > self.execution_thresholds['execution_time']:
            return BrokerStatus.DEGRADED
            
        # Check cost
        if metrics['cost_per_execution'] > self.execution_thresholds['cost_per_execution']:
            return BrokerStatus.DEGRADED
            
        # Check success rate
        if metrics['success_rate'] < self.execution_thresholds['success_rate']:
            return BrokerStatus.DEGRADED
            
        return BrokerStatus.HEALTHY
    
    async def get_broker_status(self, broker_id: str) -> Optional[BrokerMetrics]:
        """
        Get current broker status
        """
        try:
            data = await self.redis_pool.hgetall(f"broker_metrics:{broker_id}")
            if data:
                return BrokerMetrics.parse_obj(data)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting broker status: {str(e)}"
            )
    
    async def get_all_broker_status(self) -> List[BrokerMetrics]:
        """
        Get status for all brokers
        """
        try:
            # Get all broker IDs
            broker_keys = await self.redis_pool.keys("broker_metrics:*")
            
            metrics = []
            for key in broker_keys:
                data = await self.redis_pool.hgetall(key)
                if data:
                    metrics.append(BrokerMetrics.parse_obj(data))
            
            return metrics
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting all broker status: {str(e)}"
            )
    
    async def calculate_broker_metrics(self, broker_id: str) -> Dict:
        """
        Calculate broker metrics
        """
        try:
            # Get historical data
            metrics = await self.get_historical_metrics(broker_id)
            
            # Calculate statistics
            latency_stats = statistics.mean(metrics['latency'])
            cost_stats = statistics.mean(metrics['cost'])
            execution_stats = statistics.mean(metrics['execution_time'])
            success_rate = sum(metrics['success']) / len(metrics['success'])
            
            return {
                'latency_ms': latency_stats,
                'cost_per_execution': cost_stats,
                'execution_time_ms': execution_stats,
                'success_rate': success_rate
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating metrics: {str(e)}"
            )
    
    async def get_historical_metrics(self, broker_id: str) -> Dict:
        """
        Get historical metrics for broker
        """
        try:
            # Get last N executions
            executions = await self.redis_pool.lrange(
                f"broker_executions:{broker_id}",
                0,
                100  # Last 100 executions
            )
            
            # Parse metrics
            metrics = {
                'latency': [],
                'cost': [],
                'execution_time': [],
                'success': []
            }
            
            for execution in executions:
                data = json.loads(execution)
                metrics['latency'].append(data['latency_ms'])
                metrics['cost'].append(data['cost'])
                metrics['execution_time'].append(data['execution_time_ms'])
                metrics['success'].append(data['success'])
            
            return metrics
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting historical metrics: {str(e)}"
            )
    
    async def route_trade(self, trade: Dict) -> str:
        """
        Route trade to optimal broker based on health
        """
        try:
            # Get all brokers
            brokers = await self.get_all_broker_status()
            
            # Filter healthy brokers
            healthy_brokers = [b for b in brokers if b.status == BrokerStatus.HEALTHY]
            
            if not healthy_brokers:
                healthy_brokers = [b for b in brokers if b.status == BrokerStatus.DEGRADED]
                
            if not healthy_brokers:
                raise HTTPException(
                    status_code=500,
                    detail="No healthy brokers available"
                )
            
            # Sort by latency
            healthy_brokers.sort(key=lambda b: b.latency_ms)
            
            # Return best broker
            return healthy_brokers[0].broker_id
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error routing trade: {str(e)}"
            )
