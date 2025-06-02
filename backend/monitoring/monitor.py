from typing import Dict, List, Optional, Any
import logging
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from datetime import datetime, timedelta
import numpy as np
from pydantic import BaseModel
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class AlertConfig(BaseModel):
    threshold: float
    frequency: str  # 'daily', 'hourly', 'realtime'
    notification_channels: List[str]  # 'email', 'slack', 'sms'
    cooldown_minutes: int = 30

class PerformanceMetrics(BaseModel):
    timestamp: datetime
    metrics: Dict[str, float]
    alerts: List[str]
    status: str

class MonitoringSystem:
    def __init__(self, db_url: str, redis_url: str):
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.redis = redis.Redis.from_url(redis_url)
        self.alert_configs = {
            'performance': AlertConfig(
                threshold=0.8,
                frequency='hourly',
                notification_channels=['email', 'slack']
            ),
            'risk': AlertConfig(
                threshold=0.95,
                frequency='realtime',
                notification_channels=['email', 'sms']
            ),
            'data_quality': AlertConfig(
                threshold=0.9,
                frequency='daily',
                notification_channels=['email', 'slack']
            )
        }
        self.last_alerts = {}
    
    async def monitor_system(self) -> None:
        """
        Main monitoring loop
        """
        while True:
            try:
                # Check all monitoring aspects
                metrics = await self._collect_metrics()
                alerts = self._detect_alerts(metrics)
                
                # Send notifications if needed
                await self._send_notifications(alerts)
                
                # Update last check time
                self.redis.set('last_monitor_check', datetime.now().isoformat())
                
                # Wait based on most frequent monitoring requirement
                min_frequency = min(
                    config.frequency for config in self.alert_configs.values()
                )
                await asyncio.sleep(self._get_frequency_seconds(min_frequency))
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _collect_metrics(self) -> Dict:
        """
        Collect all system metrics
        """
        metrics = {
            'performance': await self._collect_performance_metrics(),
            'risk': await self._collect_risk_metrics(),
            'data_quality': await self._collect_data_quality_metrics()
        }
        
        return metrics
    
    async def _collect_performance_metrics(self) -> Dict:
        """
        Collect performance metrics
        """
        session = self.Session()
        try:
            # Query performance data
            df = pd.read_sql("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100", self.engine)
            
            return {
                'win_rate': df['profit'].gt(0).mean(),
                'avg_profit': df['profit'].mean(),
                'max_drawdown': df['profit'].cumsum().min(),
                'sharpe_ratio': df['profit'].mean() / df['profit'].std()
            }
            
        finally:
            session.close()
    
    async def _collect_risk_metrics(self) -> Dict:
        """
        Collect risk metrics
        """
        session = self.Session()
        try:
            # Query risk data
            df = pd.read_sql("SELECT * FROM risk_metrics ORDER BY timestamp DESC LIMIT 100", self.engine)
            
            return {
                'volatility': df['volatility'].mean(),
                'value_at_risk': df['value_at_risk'].mean(),
                'position_exposure': df['position_exposure'].sum()
            }
            
        finally:
            session.close()
    
    async def _collect_data_quality_metrics(self) -> Dict:
        """
        Collect data quality metrics
        """
        session = self.Session()
        try:
            # Query data quality
            df = pd.read_sql("SELECT * FROM data_quality ORDER BY timestamp DESC LIMIT 100", self.engine)
            
            return {
                'validity_score': df['validity_score'].mean(),
                'latency': df['latency'].mean(),
                'consistency': df['consistency'].mean()
            }
            
        finally:
            session.close()
    
    def _detect_alerts(self, metrics: Dict) -> List[str]:
        """
        Detect potential alerts based on metrics
        """
        alerts = []
        current_time = datetime.now()
        
        for metric_type, config in self.alert_configs.items():
            if metric_type not in metrics:
                continue
                
            # Check if we're within cooldown period
            last_alert = self.last_alerts.get(metric_type)
            if last_alert and (current_time - last_alert).total_seconds() < config.cooldown_minutes * 60:
                continue
                
            # Check metrics against thresholds
            for metric, value in metrics[metric_type].items():
                if value < config.threshold:
                    alerts.append(f"{metric_type}_{metric}_below_threshold")
                    self.last_alerts[metric_type] = current_time
        
        return alerts
    
    async def _send_notifications(self, alerts: List[str]) -> None:
        """
        Send notifications for detected alerts
        """
        if not alerts:
            return
            
        for alert in alerts:
            alert_config = self.alert_configs.get(alert.split('_')[0])
            if not alert_config:
                continue
                
            for channel in alert_config.notification_channels:
                await self._send_notification(channel, alert)
    
    async def _send_notification(self, channel: str, alert: str) -> None:
        """
        Send notification through specified channel
        """
        try:
            if channel == 'email':
                await self._send_email(alert)
            elif channel == 'slack':
                await self._send_slack_message(alert)
            elif channel == 'sms':
                await self._send_sms(alert)
        except Exception as e:
            self.logger.error(f"Error sending {channel} notification: {str(e)}")
    
    async def _send_email(self, alert: str) -> None:
        """
        Send email notification
        """
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SMTP_FROM_EMAIL')
        msg['To'] = os.getenv('SMTP_TO_EMAIL')
        msg['Subject'] = f"Quantum Trader Alert: {alert}"
        
        body = f"Alert detected: {alert}\n\nTime: {datetime.now()}"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT')) as server:
                server.starttls()
                server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
                server.send_message(msg)
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
    
    async def _send_slack_message(self, alert: str) -> None:
        """
        Send Slack notification
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                os.getenv('SLACK_WEBHOOK_URL'),
                json={
                    'text': f"*Quantum Trader Alert*: {alert}\n\nTime: {datetime.now()}"
                }
            )
            response.raise_for_status()
    
    async def _send_sms(self, alert: str) -> None:
        """
        Send SMS notification
        """
        # Implementation depends on SMS provider
        pass
    
    def _get_frequency_seconds(self, frequency: str) -> int:
        """
        Convert frequency string to seconds
        """
        if frequency == 'realtime':
            return 1
        elif frequency == 'hourly':
            return 3600
        elif frequency == 'daily':
            return 86400
        return 3600  # Default to hourly
    
    def get_system_health(self) -> Dict:
        """
        Get overall system health status
        """
        metrics = self._collect_metrics()
        alerts = self._detect_alerts(metrics)
        
        return {
            'status': 'healthy' if not alerts else 'warning',
            'metrics': metrics,
            'alerts': alerts,
            'last_check': datetime.now().isoformat(),
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> float:
        """
        Calculate system uptime
        """
        last_check = self.redis.get('last_monitor_check')
        if not last_check:
            return 0.0
            
        last_check_time = datetime.fromisoformat(last_check.decode())
        uptime = (datetime.now() - last_check_time).total_seconds()
        return uptime
