import time
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
import redis
from redis import asyncio as aioredis
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging
from fastapi import HTTPException
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Define monitoring intervals
MONITOR_INTERVALS = {
    'latency': timedelta(seconds=5),
    'execution': timedelta(seconds=10),
    'health': timedelta(minutes=1)
}

# Define alert thresholds
ALERT_THRESHOLDS = {
    'latency': {
        'warning': 150.0,  # ms
        'critical': 300.0
    },
    'execution_time': {
        'warning': 500.0,  # ms
        'critical': 1000.0
    },
    'cost': {
        'warning': 0.02,  # 2% of trade value
        'critical': 0.05
    },
    'success_rate': {
        'warning': 0.90,  # 90% success rate
        'critical': 0.85
    }
}

@dataclass
class Alert:
    """Data class for broker alerts"""
    broker_id: str
    metric: str
    value: float
    threshold: float
    status: str
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            'broker_id': self.broker_id,
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

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
        self.alerts = []
        self.monitor_tasks = {}
        self.last_alerts = {}
        
    async def start_monitoring(self, broker_id: str) -> None:
        """
        Start monitoring a broker
        
        Args:
            broker_id: ID of the broker to monitor
        """
        if broker_id not in self.monitor_tasks:
            self.monitor_tasks[broker_id] = asyncio.create_task(
                self._monitor_broker_loop(broker_id)
            )
            logger.info(f"Started monitoring broker {broker_id}")
            
    async def stop_monitoring(self, broker_id: str) -> None:
        """
        Stop monitoring a broker
        
        Args:
            broker_id: ID of the broker to stop monitoring
        """
        if broker_id in self.monitor_tasks:
            self.monitor_tasks[broker_id].cancel()
            del self.monitor_tasks[broker_id]
            logger.info(f"Stopped monitoring broker {broker_id}")
            
    async def _monitor_broker_loop(self, broker_id: str) -> None:
        """
        Continuous monitoring loop for a broker
        
        Args:
            broker_id: ID of the broker to monitor
        """
        while True:
            try:
                # Get latest metrics
                metrics = await self._get_latest_metrics(broker_id)
                if not metrics:
                    continue
                    
                # Update status
                status = self.calculate_broker_status(metrics)
                await self._update_broker_status(broker_id, status)
                
                # Check for alerts
                alerts = self._check_alerts(broker_id, metrics)
                if alerts:
                    await self._handle_alerts(alerts)
                    
                # Wait for next interval
                await asyncio.sleep(MONITOR_INTERVALS['health'].total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broker monitoring loop: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loop
                
    async def _get_latest_metrics(self, broker_id: str) -> Optional[Dict]:
        """
        Get latest metrics from Redis
        
        Args:
            broker_id: ID of the broker
            
        Returns:
            Dict of latest metrics or None if not found
        """
        try:
            metrics = await self.redis_pool.hgetall(f"broker_metrics:{broker_id}")
            if metrics:
                return {
                    'latency_ms': float(metrics['latency_ms']),
                    'cost_per_execution': float(metrics['cost_per_execution']),
                    'execution_time_ms': float(metrics['execution_time_ms']),
                    'success_rate': float(metrics['success_rate'])
                }
            return None
        except Exception as e:
            logger.error(f"Error getting metrics for {broker_id}: {str(e)}")
            return None
            
    async def _update_broker_status(self, broker_id: str, status: BrokerStatus) -> None:
        """
        Update broker status in Redis
        
        Args:
            broker_id: ID of the broker
            status: New status
        """
        try:
            await self.redis_pool.hset(
                f"broker_status:{broker_id}",
                mapping={
                    'status': status.value,
                    'last_update': datetime.now().isoformat()
                }
            )
            logger.info(f"Updated status for {broker_id}: {status.value}")
        except Exception as e:
            logger.error(f"Error updating status for {broker_id}: {str(e)}")
            
    def _check_alerts(self, broker_id: str, metrics: Dict) -> List[Alert]:
        """
        Check metrics against thresholds and generate alerts
        
        Args:
            broker_id: ID of the broker
            metrics: Current metrics
            
        Returns:
            List of new alerts
        """
        alerts = []
        current_time = datetime.now()
        
        # Check each metric
        for metric, threshold in ALERT_THRESHOLDS.items():
            value = metrics.get(metric, 0.0)
            
            # Check warning threshold
            if value > threshold['warning']:
                alert_status = 'warning'
                if value > threshold['critical']:
                    alert_status = 'critical'
                    
                # Create alert if not already triggered
                alert_key = f"{broker_id}_{metric}_{alert_status}"
                if (alert_key not in self.last_alerts or 
                    (current_time - self.last_alerts[alert_key]) > timedelta(minutes=5)):
                    alert = Alert(
                        broker_id=broker_id,
                        metric=metric,
                        value=value,
                        threshold=threshold[alert_status],
                        status=alert_status,
                        timestamp=current_time
                    )
                    alerts.append(alert)
                    self.last_alerts[alert_key] = current_time
                    
        return alerts
        
    async def _handle_alerts(self, alerts: List[Alert]) -> None:
        """
        Handle new alerts
        
        Args:
            alerts: List of new alerts
        """
        for alert in alerts:
            # Store in Redis
            await self.redis_pool.rpush(
                'broker_alerts',
                json.dumps(alert.to_dict())
            )
            
            # Log the alert
            logger.warning(f"Broker alert: {alert.broker_id} - {alert.metric}:")
            logger.warning(f"Value: {alert.value} > Threshold: {alert.threshold}")
            
            # Add to recent alerts
            self.alerts.append(alert)
            if len(self.alerts) > 100:  # Keep last 100 alerts
                self.alerts.pop(0)
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
        
    async def get_broker_status(self, broker_id: str) -> Tuple[BrokerStatus, List[Alert]]:
        """
        Get current broker status and recent alerts
        
        Args:
            broker_id: ID of the broker
            
        Returns:
            Tuple containing:
            - BrokerStatus: Current status
            - List[Alert]: Recent alerts
        """
        try:
            # Get status from Redis
            status_data = await self.redis_pool.hgetall(f"broker_status:{broker_id}")
            if not status_data:
                return BrokerStatus.OFFLINE, []
                
            # Get recent alerts
            alerts = []
            for alert in self.alerts:
                if alert.broker_id == broker_id:
                    alerts.append(alert)
                    
            return BrokerStatus(status_data['status']), alerts
            
        except Exception as e:
            logger.error(f"Error getting broker status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting broker status: {str(e)}"
            )

    async def get_recent_alerts(self, broker_id: Optional[str] = None) -> List[Dict]:
        """
        Get recent alerts for a broker or all brokers
        
        Args:
            broker_id: Optional broker ID to filter alerts
            
        Returns:
            List of alert dictionaries
        """
        try:
            alerts = []
            for alert in self.alerts:
                if broker_id is None or alert.broker_id == broker_id:
                    alerts.append(alert.to_dict())
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting alerts: {str(e)}"
            )
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
