import logging
from typing import Dict, Any, Optional
from redis import asyncio as aioredis
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import json

class FailsafeStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"

class FailsafeEvent(BaseModel):
    timestamp: datetime
    event_type: str
    severity: FailsafeStatus
    details: Dict[str, Any]
    action_taken: Optional[str] = None

class FailsafeSystem:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.logger = logging.getLogger(__name__)
        self._initialize_redis()

    async def _initialize_redis(self):
        """
        Initialize Redis connection and set up required structures
        """
        try:
            await self.redis.ping()
            self.logger.info("Redis connection initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {str(e)}")
            raise

    async def record_event(self, event: FailsafeEvent) -> None:
        """
        Record a failsafe event in Redis
        """
        try:
            event_data = event.dict()
            await self.redis.rpush('failsafe_events', json.dumps(event_data))
            self.logger.info(f"Recorded failsafe event: {event.event_type}")
        except Exception as e:
            self.logger.error(f"Failed to record failsafe event: {str(e)}")
            raise

    async def get_recent_events(self, limit: int = 100) -> list[FailsafeEvent]:
        """
        Get recent failsafe events
        """
        try:
            raw_events = await self.redis.lrange('failsafe_events', -limit, -1)
            events = []
            for raw in raw_events:
                event_data = json.loads(raw)
                events.append(FailsafeEvent(**event_data))
            return events
        except Exception as e:
            self.logger.error(f"Failed to get recent events: {str(e)}")
            raise

    async def trigger_alert(self, event_type: str, details: Dict[str, Any], severity: FailsafeStatus) -> None:
        """
        Trigger a failsafe alert
        """
        try:
            event = FailsafeEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                severity=severity,
                details=details
            )
            await self.record_event(event)
            self.logger.warning(f"Triggered {severity.value} alert: {event_type}")
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {str(e)}")
            raise

    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall system health
        """
        try:
            health = {
                'redis_status': await self.redis.ping(),
                'event_count': await self.redis.llen('failsafe_events'),
                'last_event': None
            }
            
            # Get last event if any
            last_event = await self.redis.lindex('failsafe_events', -1)
            if last_event:
                event_data = json.loads(last_event)
                health['last_event'] = FailsafeEvent(**event_data)
            
            return health
        except Exception as e:
            self.logger.error(f"Failed to check system health: {str(e)}")
            raise
