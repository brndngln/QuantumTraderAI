from typing import Dict, Any, Optional, List, Callable, Awaitable
import logging
import asyncio
import aioredis
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

class MonitoringConfig(BaseModel):
    redis_url: str = "redis://localhost:6379"
    metrics_interval: int = 30  # seconds
    alert_thresholds: Dict[str, Dict[str, Any]] = {
        "cpu": {"warning": 80, "critical": 90},
        "memory": {"warning": 80, "critical": 90},
        "disk": {"warning": 80, "critical": 90},
        "response_time": {"warning": 500, "critical": 1000},  # milliseconds
        "error_rate": {"warning": 0.05, "critical": 0.1}  # percentage
    }
    email_config: Dict = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "monitoring@quantumtrader.ai",
        "sender_password": "your-password"
    }
    webhook_urls: Dict[str, str] = {
        "slack": "https://slack.com/api/chat.postMessage",
        "discord": "https://discord.com/api/webhooks/..."
    }

class Alert:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def send_email(self, subject: str, message: str, recipients: List[str]) -> None:
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email_config']['sender_email']
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(
                self.config['email_config']['smtp_server'],
                self.config['email_config']['smtp_port']
            )
            server.starttls()
            server.login(
                self.config['email_config']['sender_email'],
                self.config['email_config']['sender_password']
            )
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")
            raise
    
    async def send_slack(self, message: str, channel: str) -> None:
        """Send Slack alert"""
        try:
            payload = {
                "channel": channel,
                "text": message
            }
            
            response = requests.post(
                self.config['webhook_urls']['slack'],
                json=payload
            )
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")
            raise
    
    async def send_discord(self, message: str, channel: str) -> None:
        """Send Discord alert"""
        try:
            payload = {
                "content": message
            }
            
            response = requests.post(
                self.config['webhook_urls']['discord'],
                json=payload
            )
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {str(e)}")
            raise
    
    async def notify(self, alert_type: str, message: str, severity: str = "critical") -> None:
        """Send alerts through all configured channels"""
        try:
            # Send email
            await self.send_email(
                f"[QuantumTrader] {severity.upper()} Alert - {alert_type}",
                message,
                ["ops@quantumtrader.ai"]
            )
            
            # Send Slack
            await self.send_slack(
                f"*{severity.upper()} Alert - {alert_type}*
                ```
                {message}
                ```",
                "#alerts"
            )
            
            # Send Discord
            await self.send_discord(
                f"**{severity.upper()} Alert - {alert_type}**
                ```
                {message}
                ```",
                "#alerts"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send alerts: {str(e)}")
            raise

class Monitoring:
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.alert = Alert(config)
        self.metrics_task = None
        self.initialize_redis()
    
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
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': self._get_cpu_usage(),
                'memory': self._get_memory_usage(),
                'disk': self._get_disk_usage(),
                'response_time': self._get_response_time(),
                'error_rate': self._get_error_rate()
            }
            
            await self.redis_pool.hset(
                "metrics:system",
                mapping=metrics
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            return {'error': str(e)}
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            with open("/proc/stat") as f:
                cpu = f.readline()
                cpu_data = cpu.split()
                total = float(cpu_data[1]) + float(cpu_data[2]) + float(cpu_data[3]) + float(cpu_data[4])
                idle = float(cpu_data[4])
                return 100 * (1 - idle / total)
                
        except Exception as e:
            self.logger.error(f"Failed to get CPU usage: {str(e)}")
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            with open("/proc/meminfo") as f:
                mem_total = float(f.readline().split()[1]) * 1024
                mem_free = float(f.readline().split()[1]) * 1024
                return 100 * (1 - mem_free / mem_total)
                
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {str(e)}")
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return 100 * (disk.used / disk.total)
            
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {str(e)}")
            return 0.0
    
    def _get_response_time(self) -> float:
        """Get average response time"""
        try:
            # Get last 100 response times from Redis
            times = await self.redis_pool.lrange("metrics:response_times", 0, 100)
            if not times:
                return 0.0
                
            return sum(float(t) for t in times) / len(times)
            
        except Exception as e:
            self.logger.error(f"Failed to get response time: {str(e)}")
            return 0.0
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage"""
        try:
            # Get last 100 requests from Redis
            requests = await self.redis_pool.lrange("metrics:requests", 0, 100)
            if not requests:
                return 0.0
                
            errors = sum(1 for r in requests if json.loads(r).get('status') >= 500)
            return 100 * (errors / len(requests))
            
        except Exception as e:
            self.logger.error(f"Failed to get error rate: {str(e)}")
            return 0.0
    
    async def check_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against thresholds and trigger alerts if needed"""
        try:
            for metric, value in metrics.items():
                if metric == 'timestamp':
                    continue
                    
                thresholds = self.config.alert_thresholds.get(metric, {})
                if not thresholds:
                    continue
                    
                warning = thresholds.get('warning', 0)
                critical = thresholds.get('critical', 0)
                
                if value >= critical:
                    await self.alert.notify(
                        metric,
                        f"CRITICAL: {metric} is at {value:.2f}% (threshold: {critical}%)",
                        "critical"
                    )
                elif value >= warning:
                    await self.alert.notify(
                        metric,
                        f"WARNING: {metric} is at {value:.2f}% (threshold: {warning}%)",
                        "warning"
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to check thresholds: {str(e)}")
            raise
    
    async def start_monitoring(self) -> None:
        """Start periodic monitoring"""
        if self.metrics_task:
            self.metrics_task.cancel()
            
        self.metrics_task = asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self) -> None:
        """Periodic monitoring loop"""
        while True:
            try:
                metrics = await self.collect_metrics()
                await self.check_thresholds(metrics)
                await asyncio.sleep(self.config.metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def get_metrics_history(self, metric: str, duration: int = 3600) -> List[Dict]:
        """Get historical metrics"""
        try:
            keys = await self.redis_pool.keys(f"metrics:{metric}:*")
            metrics = []
            
            for key in keys:
                data = await self.redis_pool.hgetall(key)
                if data:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - timestamp <= timedelta(seconds=duration):
                        metrics.append(data)
            
            return sorted(metrics, key=lambda x: x['timestamp'])
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics history: {str(e)}")
            return []
    
    async def get_alert_history(self, duration: int = 86400) -> List[Dict]:
        """Get alert history"""
        try:
            keys = await self.redis_pool.keys("alerts:*")
            alerts = []
            
            for key in keys:
                data = await self.redis_pool.hgetall(key)
                if data:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - timestamp <= timedelta(seconds=duration):
                        alerts.append(data)
            
            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get alert history: {str(e)}")
            return []
    
    async def shutdown(self) -> None:
        """Shutdown monitoring"""
        try:
            if self.metrics_task:
                self.metrics_task.cancel()
            if self.redis_pool:
                await self.redis_pool.close()
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
