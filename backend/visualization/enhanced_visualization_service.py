from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import asyncio
import aioredis
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib
import secrets
import json
from fastapi import Request, Response, HTTPException, status
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
import seaborn as sns
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes

class VisualizationConfig(BaseModel):
    redis_url: str = "redis://localhost:6379"
    update_interval: int = 60  # seconds
    visualization_types: List[str] = [
        "topology",
        "traffic",
        "performance",
        "anomaly",
        "correlation"
    ]
    anomaly_threshold: float = 3.0  # standard deviations
    correlation_threshold: float = 0.8
    prediction_window: int = 300  # seconds
    encryption_key: str = "your-encryption-key"
    rsa_key_size: int = 2048
    max_history: int = 1000
    max_correlations: int = 10

class EnhancedVisualizationService:
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis()
        self.rsa_keys = {}
        self.initialize_rsa_keys()
        self.service_graph = nx.Graph()
        self.metrics = {}
        self.anomalies = {}
        self.correlations = {}
        self.update_task = None
        
    def initialize_redis(self) -> None:
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
    
    def initialize_rsa_keys(self) -> None:
        """Initialize RSA keys for encryption"""
        try:
            # Generate RSA keys if not exist
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.config.rsa_key_size
            )
            public_key = private_key.public_key()
            
            self.rsa_keys['private'] = private_key
            self.rsa_keys['public'] = public_key
            
            # Store keys in Redis
            async with self.redis_pool as redis:
                await redis.set(
                    "visualization:public_key",
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode()
                )
                await redis.set(
                    "visualization:private_key",
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ).decode()
                )
            
        except Exception as e:
            self.logger.error(f"RSA key initialization failed: {str(e)}")
            raise
    
    async def start_update_loop(self) -> None:
        """Start periodic update loop"""
        async def update():
            while True:
                try:
                    await self.update_visualizations()
                    await asyncio.sleep(self.config.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Update loop failed: {str(e)}")
                    await asyncio.sleep(30)
        
        self.update_task = asyncio.create_task(update())
    
    async def update_visualizations(self) -> None:
        """Update all visualizations"""
        try:
            # Get metrics
            metrics = await self.collect_metrics()
            
            # Generate visualizations
            for vis_type in self.config.visualization_types:
                if vis_type == "topology":
                    await self.generate_topology(metrics)
                elif vis_type == "traffic":
                    await self.generate_traffic_patterns(metrics)
                elif vis_type == "performance":
                    await self.generate_performance_metrics(metrics)
                elif vis_type == "anomaly":
                    await self.generate_anomaly_detection(metrics)
                elif vis_type == "correlation":
                    await self.generate_correlation_analysis(metrics)
            
        except Exception as e:
            self.logger.error(f"Visualization update failed: {str(e)}")
    
    async def collect_metrics(self) -> Dict:
        """Collect comprehensive metrics"""
        try:
            metrics = {}
            
            # Get service metrics
            services = await self.redis_pool.keys("service:*")
            for service in services:
                service_name = service.split(':')[1]
                metrics[service_name] = {
                    "requests": await self.redis_pool.get(f"service:{service_name}:requests") or 0,
                    "errors": await self.redis_pool.get(f"service:{service_name}:errors") or 0,
                    "latency": await self.redis_pool.get(f"service:{service_name}:latency") or 0.0,
                    "concurrent": await self.redis_pool.get(f"service:{service_name}:concurrent") or 0
                }
            
            # Get network metrics
            connections = await self.redis_pool.keys("network:*")
            for conn in connections:
                parts = conn.split(':')
                src = parts[1]
                dst = parts[2]
                metrics[f"{src}->{dst}"] = {
                    "latency": await self.redis_pool.get(f"network:{src}:{dst}:latency") or 0.0,
                    "errors": await self.redis_pool.get(f"network:{src}:{dst}:errors") or 0,
                    "bandwidth": await self.redis_pool.get(f"network:{src}:{dst}:bandwidth") or 0.0
                }
            
            # Get system metrics
            metrics["system"] = {
                "cpu": await self.redis_pool.get("system:cpu_usage") or 0.0,
                "memory": await self.redis_pool.get("system:memory_usage") or 0.0,
                "disk": await self.redis_pool.get("system:disk_usage") or 0.0,
                "load": await self.redis_pool.get("system:load_average") or 0.0
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            return {}
    
    async def generate_topology(self, metrics: Dict) -> str:
        """Generate service topology visualization"""
        try:
            # Build graph
            self.service_graph.clear()
            
            # Add nodes and edges
            for service, data in metrics.items():
                if service == "system":
                    continue
                    
                self.service_graph.add_node(
                    service,
                    health=self.calculate_service_health(data),
                    requests=data["requests"],
                    errors=data["errors"]
                )
                
                # Add connections
                connections = await self.redis_pool.keys(f"service:{service}:connections:*")
                for conn in connections:
                    parts = conn.split(':')
                    target = parts[-1]
                    self.service_graph.add_edge(
                        service,
                        target,
                        weight=data["latency"]
                    )
            
            # Generate visualization
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(self.service_graph)
            
            # Get node colors based on health
            node_colors = []
            for node in self.service_graph.nodes():
                health = self.service_graph.nodes[node]["health"]
                if health >= 90:
                    node_colors.append('green')
                elif health >= 70:
                    node_colors.append('yellow')
                else:
                    node_colors.append('red')
            
            # Draw graph
            nx.draw(
                self.service_graph,
                pos,
                with_labels=True,
                node_color=node_colors,
                node_size=3000,
                font_size=10,
                font_weight='bold',
                edge_color='gray',
                width=1.0
            )
            
            # Add edge labels
            edge_labels = {
                (u, v): f"{d['weight']}ms"
                for u, v, d in self.service_graph.edges(data=True)
            }
            nx.draw_networkx_edge_labels(
                self.service_graph,
                pos,
                edge_labels=edge_labels,
                font_size=8
            )
            
            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            
            # Convert to base64
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            self.logger.error(f"Topology visualization failed: {str(e)}")
            return ""
    
    async def generate_traffic_patterns(self, metrics: Dict) -> str:
        """Generate traffic pattern visualization"""
        try:
            # Create DataFrame
            df = pd.DataFrame()
            for conn, data in metrics.items():
                if "->" in conn:
                    df = df.append({
                        "connection": conn,
                        "latency": float(data["latency"]),
                        "bandwidth": float(data["bandwidth"]),
                        "errors": int(data["errors"])
                    }, ignore_index=True)
            
            # Create figure
            fig = go.Figure()
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=df["connection"],
                y=df["latency"],
                mode='markers',
                marker=dict(
                    size=df["bandwidth"] / 1000000,  # Scale bandwidth
                    color=df["errors"],
                    colorscale='Viridis',
                    showscale=True
                ),
                hovertemplate=
                'Connection: %{x}<br>' +
                'Latency: %{y}ms<br>' +
                'Bandwidth: %{marker.size}Mbps<br>' +
                'Errors: %{marker.color}<extra></extra>'
            ))
            
            # Add anomaly indicators
            anomalies = await self.detect_anomalies(df)
            for anomaly in anomalies:
                fig.add_annotation(
                    x=anomaly["connection"],
                    y=anomaly["latency"],
                    text="Anomaly",
                    showarrow=True,
                    arrowhead=2
                )
            
            # Update layout
            fig.update_layout(
                title='Traffic Patterns',
                xaxis_title='Connections',
                yaxis_title='Latency (ms)',
                width=1200,
                height=800
            )
            
            # Convert to base64
            buffer = BytesIO()
            fig.write_image(buffer, format='png')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            self.logger.error(f"Traffic visualization failed: {str(e)}")
            return ""
    
    async def generate_performance_metrics(self, metrics: Dict) -> str:
        """Generate performance metrics visualization"""
        try:
            # Create DataFrame
            df = pd.DataFrame()
            for service, data in metrics.items():
                if service == "system":
                    continue
                    
                df = df.append({
                    "service": service,
                    "latency": float(data["latency"]),
                    "requests": int(data["requests"]),
                    "errors": int(data["errors"]),
                    "concurrent": int(data["concurrent"])
                }, ignore_index=True)
            
            # Create figure
            fig = go.Figure()
            
            # Add bar chart for latency
            fig.add_trace(go.Bar(
                x=df["service"],
                y=df["latency"],
                name='Latency',
                marker_color='blue'
            ))
            
            # Add line chart for requests
            fig.add_trace(go.Scatter(
                x=df["service"],
                y=df["requests"],
                name='Requests',
                mode='lines+markers',
                yaxis='y2',
                marker_color='red'
            ))
            
            # Add anomaly indicators
            anomalies = await self.detect_anomalies(df)
            for anomaly in anomalies:
                fig.add_annotation(
                    x=anomaly["service"],
                    y=anomaly["latency"],
                    text="Anomaly",
                    showarrow=True,
                    arrowhead=2
                )
            
            # Update layout
            fig.update_layout(
                title='Performance Metrics',
                xaxis_title='Services',
                yaxis_title='Latency (ms)',
                yaxis2=dict(
                    title='Requests',
                    overlaying='y',
                    side='right'
                ),
                width=1200,
                height=800
            )
            
            # Convert to base64
            buffer = BytesIO()
            fig.write_image(buffer, format='png')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            self.logger.error(f"Performance visualization failed: {str(e)}")
            return ""
    
    async def generate_anomaly_detection(self, metrics: Dict) -> str:
        """Generate anomaly detection visualization"""
        try:
            # Create DataFrame
            df = pd.DataFrame()
            for metric_type, data in metrics.items():
                if metric_type == "system":
                    continue
                    
                df = df.append({
                    "metric": metric_type,
                    "value": float(data["latency"]),
                    "type": "latency"
                }, ignore_index=True)
                
                df = df.append({
                    "metric": metric_type,
                    "value": float(data["requests"]),
                    "type": "requests"
                }, ignore_index=True)
            
            # Calculate anomalies
            anomalies = await self.detect_anomalies(df)
            
            # Create figure
            fig = go.Figure()
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=df["metric"],
                y=df["value"],
                mode='markers',
                marker=dict(
                    color=df["type"].map({
                        "latency": 'blue',
                        "requests": 'red'
                    }),
                    size=10
                ),
                name='Metrics'
            ))
            
            # Add anomaly points
            anomaly_df = pd.DataFrame(anomalies)
            fig.add_trace(go.Scatter(
                x=anomaly_df["metric"],
                y=anomaly_df["value"],
                mode='markers',
                marker=dict(
                    color='red',
                    size=20,
                    symbol='x'
                ),
                name='Anomalies'
            ))
            
            # Update layout
            fig.update_layout(
                title='Anomaly Detection',
                xaxis_title='Metrics',
                yaxis_title='Value',
                width=1200,
                height=800
            )
            
            # Convert to base64
            buffer = BytesIO()
            fig.write_image(buffer, format='png')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            self.logger.error(f"Anomaly visualization failed: {str(e)}")
            return ""
    
    async def generate_correlation_analysis(self, metrics: Dict) -> str:
        """Generate correlation analysis visualization"""
        try:
            # Create DataFrame
            df = pd.DataFrame()
            for service, data in metrics.items():
                if service == "system":
                    continue
                    
                df = df.append({
                    "service": service,
                    "latency": float(data["latency"]),
                    "requests": int(data["requests"]),
                    "errors": int(data["errors"]),
                    "concurrent": int(data["concurrent"])
                }, ignore_index=True)
            
            # Calculate correlations
            corr_matrix = df.corr()
            
            # Create heatmap
            plt.figure(figsize=(12, 8))
            sns.heatmap(
                corr_matrix,
                annot=True,
                cmap='coolwarm',
                center=0,
                linewidths=0.5
            )
            
            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            
            # Convert to base64
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            self.logger.error(f"Correlation visualization failed: {str(e)}")
            return ""
    
    def calculate_service_health(self, metrics: Dict) -> float:
        """Calculate service health score"""
        try:
            # Calculate error rate
            error_rate = float(metrics["errors"] / (metrics["requests"] + 1))
            
            # Calculate latency score
            latency_score = 100 - (float(metrics["latency"]) / 1000)
            
            # Calculate concurrent score
            concurrent_score = 100 - (float(metrics["concurrent"]) / 100)
            
            # Calculate overall health
            health = (
                (1 - error_rate) * 0.4 +
                latency_score * 0.3 +
                concurrent_score * 0.3
            )
            
            return min(max(health, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Health calculation failed: {str(e)}")
            return 50
    
    async def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect anomalies in metrics"""
        try:
            anomalies = []
            
            # Calculate z-scores
            z_scores = stats.zscore(df["value"])
            
            # Find anomalies
            for i, z in enumerate(z_scores):
                if abs(z) > self.config.anomaly_threshold:
                    anomalies.append({
                        "metric": df.iloc[i]["metric"],
                        "value": df.iloc[i]["value"],
                        "type": df.iloc[i]["type"],
                        "score": z
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            return []
