from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import asyncio
import aioredis
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
import psutil
import socket
import platform
import aiohttp
from .monitoring import Monitoring

class AdvancedMonitoringConfig(BaseModel):
    redis_url: str = "redis://localhost:6379"
    metrics_interval: int = 30  # seconds
    alert_thresholds: Dict = {
        "cpu": {"warning": 80, "critical": 90},
        "memory": {"warning": 80, "critical": 90},
        "disk": {"warning": 80, "critical": 90},
        "network": {"warning": 10000000, "critical": 50000000},  # bytes per second
        "response_time": {"warning": 200, "critical": 500}  # milliseconds
    }
    alert_channels: Dict = {
        "email": {"enabled": True, "smtp_server": "smtp.gmail.com", "port": 587},
        "slack": {"enabled": True, "webhook_url": ""},
        "discord": {"enabled": True, "webhook_url": ""}
    }
    visualization_config: Dict = {
        "enabled": True,
        "update_interval": 60,  # seconds
        "dashboard_url": "http://localhost:3000"
    }

class AdvancedMonitoring(Monitoring):
    def __init__(self, config: AdvancedMonitoringConfig):
        super().__init__(config)
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.initialize_redis()
        self.alert_history = []
        self.metrics_history = []
        self.service_topology = {}
        self.traffic_patterns = {}
        
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def collect_advanced_metrics(self) -> Dict:
        """Collect advanced system metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu": psutil.cpu_percent(percpu=True),
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk": psutil.disk_usage('/')._asdict(),
                    "network": self._get_network_metrics(),
                    "load": psutil.getloadavg(),
                    "processes": len(psutil.pids()),
                    "uptime": self._get_uptime()
                },
                "services": await self._get_service_metrics(),
                "security": await self._get_security_metrics(),
                "performance": await self._get_performance_metrics()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            return {}
    
    def _get_network_metrics(self) -> Dict:
        """Get network metrics"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "error_in": net_io.errin,
            "error_out": net_io.errout,
            "drop_in": net_io.dropin,
            "drop_out": net_io.dropout
        }
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds"""
        return int(time.time() - psutil.boot_time())
    
    async def _get_service_metrics(self) -> Dict:
        """Get service-specific metrics"""
        services = await self.redis_pool.keys("service:*")
        metrics = {}
        
        for service in services:
            service_name = service.split(':')[1]
            service_data = await self.redis_pool.hgetall(service)
            metrics[service_name] = {
                "status": service_data.get("status", "unknown"),
                "response_time": float(service_data.get("response_time", 0)),
                "requests": int(service_data.get("requests", 0)),
                "errors": int(service_data.get("errors", 0)),
                "last_update": service_data.get("last_update", "")
            }
        
        return metrics
    
    async def _get_security_metrics(self) -> Dict:
        """Get security-related metrics"""
        return {
            "failed_attempts": await self.redis_pool.get("security:failed_attempts") or 0,
            "locked_accounts": await self.redis_pool.get("security:locked_accounts") or 0,
            "active_sessions": await self.redis_pool.get("security:active_sessions") or 0,
            "rate_limit_hits": await self.redis_pool.get("security:rate_limit_hits") or 0
        }
    
    async def _get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            "average_response_time": await self.redis_pool.get("perf:avg_response_time") or 0,
            "request_throughput": await self.redis_pool.get("perf:request_throughput") or 0,
            "error_rate": await self.redis_pool.get("perf:error_rate") or 0,
            "concurrent_requests": await self.redis_pool.get("perf:concurrent_requests") or 0
        }
    
    async def check_advanced_thresholds(self, metrics: Dict) -> None:
        """Check advanced thresholds and trigger alerts"""
        try:
            alerts = []
            
            # Check CPU thresholds
            cpu_usage = metrics["system"]["cpu"]
            for i, core in enumerate(cpu_usage):
                if core >= self.config.alert_thresholds["cpu"]["warning"]:
                    alerts.append({
                        "type": "WARNING",
                        "metric": f"cpu_core_{i}",
                        "value": core,
                        "threshold": self.config.alert_thresholds["cpu"]["warning"]
                    })
                if core >= self.config.alert_thresholds["cpu"]["critical"]:
                    alerts.append({
                        "type": "CRITICAL",
                        "metric": f"cpu_core_{i}",
                        "value": core,
                        "threshold": self.config.alert_thresholds["cpu"]["critical"]
                    })
            
            # Check memory thresholds
            memory_usage = metrics["system"]["memory"]["percent"]
            if memory_usage >= self.config.alert_thresholds["memory"]["warning"]:
                alerts.append({
                    "type": "WARNING",
                    "metric": "memory",
                    "value": memory_usage,
                    "threshold": self.config.alert_thresholds["memory"]["warning"]
                })
            if memory_usage >= self.config.alert_thresholds["memory"]["critical"]:
                alerts.append({
                    "type": "CRITICAL",
                    "metric": "memory",
                    "value": memory_usage,
                    "threshold": self.config.alert_thresholds["memory"]["critical"]
                })
            
            # Check disk thresholds
            disk_usage = metrics["system"]["disk"]["percent"]
            if disk_usage >= self.config.alert_thresholds["disk"]["warning"]:
                alerts.append({
                    "type": "WARNING",
                    "metric": "disk",
                    "value": disk_usage,
                    "threshold": self.config.alert_thresholds["disk"]["warning"]
                })
            if disk_usage >= self.config.alert_thresholds["disk"]["critical"]:
                alerts.append({
                    "type": "CRITICAL",
                    "metric": "disk",
                    "value": disk_usage,
                    "threshold": self.config.alert_thresholds["disk"]["critical"]
                })
            
            # Check network thresholds
            network_bytes = metrics["system"]["network"]["bytes_sent"]
            if network_bytes >= self.config.alert_thresholds["network"]["warning"]:
                alerts.append({
                    "type": "WARNING",
                    "metric": "network",
                    "value": network_bytes,
                    "threshold": self.config.alert_thresholds["network"]["warning"]
                })
            if network_bytes >= self.config.alert_thresholds["network"]["critical"]:
                alerts.append({
                    "type": "CRITICAL",
                    "metric": "network",
                    "value": network_bytes,
                    "threshold": self.config.alert_thresholds["network"]["critical"]
                })
            
            # Check service response times
            for service, data in metrics["services"].items():
                if data["response_time"] >= self.config.alert_thresholds["response_time"]["warning"]:
                    alerts.append({
                        "type": "WARNING",
                        "metric": f"service_{service}_response_time",
                        "value": data["response_time"],
                        "threshold": self.config.alert_thresholds["response_time"]["warning"]
                    })
                if data["response_time"] >= self.config.alert_thresholds["response_time"]["critical"]:
                    alerts.append({
                        "type": "CRITICAL",
                        "metric": f"service_{service}_response_time",
                        "value": data["response_time"],
                        "threshold": self.config.alert_thresholds["response_time"]["critical"]
                    })
            
            # Send alerts if any
            if alerts:
                await self.send_alerts(alerts)
                
        except Exception as e:
            self.logger.error(f"Threshold checking failed: {str(e)}")
    
    async def send_alerts(self, alerts: List[Dict]) -> None:
        """Send alerts through configured channels"""
        try:
            for alert in alerts:
                # Email alerts
                if self.config.alert_channels["email"]["enabled"]:
                    await self._send_email_alert(alert)
                
                # Slack alerts
                if self.config.alert_channels["slack"]["enabled"]:
                    await self._send_slack_alert(alert)
                
                # Discord alerts
                if self.config.alert_channels["discord"]["enabled"]:
                    await self._send_discord_alert(alert)
                
                # Store in history
                self.alert_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "alert": alert
                })
                
                # Store in Redis
                await self.redis_pool.rpush("alerts:history", json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "alert": alert
                }))
                
        except Exception as e:
            self.logger.error(f"Failed to send alerts: {str(e)}")
    
    async def _send_email_alert(self, alert: Dict) -> None:
        """Send email alert"""
        try:
            # Implementation using SMTP
            pass
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")
    
    async def _send_slack_alert(self, alert: Dict) -> None:
        """Send Slack alert"""
        try:
            async with aiohttp.ClientSession() as session:
                webhook_url = self.config.alert_channels["slack"]["webhook_url"]
                data = {
                    "text": f"*ALERT*: {alert['type']} - {alert['metric']} value {alert['value']} exceeded threshold {alert['threshold']}"
                }
                async with session.post(webhook_url, json=data) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")
    
    async def _send_discord_alert(self, alert: Dict) -> None:
        """Send Discord alert"""
        try:
            async with aiohttp.ClientSession() as session:
                webhook_url = self.config.alert_channels["discord"]["webhook_url"]
                data = {
                    "content": f"**ALERT**: {alert['type']} - {alert['metric']} value {alert['value']} exceeded threshold {alert['threshold']}"
                }
                async with session.post(webhook_url, json=data) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to send Discord alert: {response.status}")
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {str(e)}")
    
    async def update_visualization(self) -> None:
        """Update visualization data"""
        try:
            # Get latest metrics
            metrics = await self.collect_advanced_metrics()
            
            # Update service topology
            self.service_topology = await self._get_service_topology()
            
            # Update traffic patterns
            self.traffic_patterns = await self._get_traffic_patterns()
            
            # Send to visualization dashboard
            if self.config.visualization_config["enabled"]:
                async with aiohttp.ClientSession() as session:
                    url = self.config.visualization_config["dashboard_url"]
                    data = {
                        "metrics": metrics,
                        "topology": self.service_topology,
                        "traffic": self.traffic_patterns,
                        "timestamp": datetime.now().isoformat()
                    }
                    async with session.post(url, json=data) as response:
                        if response.status != 200:
                            self.logger.error(f"Failed to update visualization: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update visualization: {str(e)}")
    
    async def _get_service_topology(self) -> Dict:
        """Get service topology information"""
        try:
            services = await self.redis_pool.keys("service:*")
            topology = {}
            
            for service in services:
                service_name = service.split(':')[1]
                service_data = await self.redis_pool.hgetall(service)
                topology[service_name] = {
                    "dependencies": json.loads(service_data.get("dependencies", "[]")),
                    "dependents": json.loads(service_data.get("dependents", "[]")),
                    "status": service_data.get("status", "unknown"),
                    "health": float(service_data.get("health", 0))
                }
            
            return topology
            
        except Exception as e:
            self.logger.error(f"Failed to get service topology: {str(e)}")
            return {}
    
    async def _get_traffic_patterns(self) -> Dict:
        """Get traffic patterns"""
        try:
            traffic = {}
            keys = await self.redis_pool.keys("traffic:*")
            
            for key in keys:
                service = key.split(':')[1]
                traffic_data = await self.redis_pool.hgetall(key)
                traffic[service] = {
                    "requests": int(traffic_data.get("requests", 0)),
                    "errors": int(traffic_data.get("errors", 0)),
                    "response_times": json.loads(traffic_data.get("response_times", "[]")),
                    "traffic_sources": json.loads(traffic_data.get("traffic_sources", "{}"))
                }
            
            return traffic
            
        except Exception as e:
            self.logger.error(f"Failed to get traffic patterns: {str(e)}")
            return {}
    
    async def start_monitoring(self) -> None:
        """Start monitoring with visualization updates"""
        while True:
            try:
                # Collect metrics
                metrics = await self.collect_advanced_metrics()
                
                # Check thresholds
                await self.check_advanced_thresholds(metrics)
                
                # Update visualization
                await self.update_visualization()
                
                # Store metrics history
                self.metrics_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                })
                
                # Store in Redis
                await self.redis_pool.rpush("metrics:history", json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                }))
                
                await asyncio.sleep(self.config.metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop failed: {str(e)}")
                await asyncio.sleep(5)
    
    async def get_metrics_history(self, service: str, duration: int = 3600) -> List[Dict]:
        """Get metrics history for a service"""
        try:
            history = []
            keys = await self.redis_pool.keys(f"metrics:history:{service}:*")
            
            for key in keys:
                data = await self.redis_pool.get(key)
                if data:
                    history.append(json.loads(data))
            
            # Filter by duration
            now = datetime.now()
            history = [h for h in history 
                       if (now - datetime.fromisoformat(h["timestamp"])) <= timedelta(seconds=duration)]
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics history: {str(e)}")
            return []
    
    async def get_alert_history(self, duration: int = 86400) -> List[Dict]:
        """Get alert history"""
        try:
            history = []
            keys = await self.redis_pool.keys("alerts:history:*")
            
            for key in keys:
                data = await self.redis_pool.get(key)
                if data:
                    history.append(json.loads(data))
            
            # Filter by duration
            now = datetime.now()
            history = [h for h in history 
                       if (now - datetime.fromisoformat(h["timestamp"])) <= timedelta(seconds=duration)]
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get alert history: {str(e)}")
            return []
    
    async def get_visualization_data(self) -> Dict:
        """Get visualization data"""
        try:
            return {
                "topology": self.service_topology,
                "traffic": self.traffic_patterns,
                "metrics": await self.collect_advanced_metrics(),
                "alerts": await self.get_alert_history(3600),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get visualization data: {str(e)}")
            return {}
