import pytest
import asyncio
import aioredis
import json
from datetime import datetime
from service_mesh.service_mesh import ServiceMesh, ServiceMeshConfig
from service_mesh.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from service_mesh.load_balancer import LoadBalancer, LoadBalancerConfig
from service_mesh.monitoring import Monitoring, MonitoringConfig

@pytest.fixture
def mock_redis_pool():
    class MockRedisPool:
        async def ping(self):
            return True
            
        async def hset(self, *args, **kwargs):
            pass
            
        async def hgetall(self, *args, **kwargs):
            return {}
            
        async def keys(self, *args, **kwargs):
            return []
            
        async def delete(self, *args, **kwargs):
            pass
            
        async def close(self):
            pass
            
    return MockRedisPool()

@pytest.fixture
def mock_circuit_breaker():
    class MockCircuitBreaker:
        async def is_circuit_open(self, *args, **kwargs):
            return False
            
        async def start_cleanup(self):
            pass
            
        async def shutdown(self):
            pass
            
    return MockCircuitBreaker()

@pytest.fixture
def mock_load_balancer():
    class MockLoadBalancer:
        async def route_request(self, *args, **kwargs):
            return ({"status": 200, "body": "OK"}, 200)
            
        async def start_health_checking(self):
            pass
            
        async def shutdown(self):
            pass
            
    return MockLoadBalancer()

@pytest.fixture
def mock_monitoring():
    class MockMonitoring:
        async def start_monitoring(self):
            pass
            
        async def collect_metrics(self):
            return {}
            
        async def shutdown(self):
            pass
            
    return MockMonitoring()

@pytest.fixture
def service_mesh_config():
    return ServiceMeshConfig(
        redis_url="redis://localhost:6379",
        circuit_breaker_config={
            "failure_threshold": 5,
            "reset_timeout": 60
        },
        load_balancer_config={
            "strategy": "weighted_round_robin",
            "max_concurrent_requests": 100
        },
        monitoring_config={
            "metrics_interval": 30,
            "alert_thresholds": {
                "cpu": {"warning": 80, "critical": 90},
                "memory": {"warning": 80, "critical": 90}
            }
        }
    )

@pytest.fixture
def service_mesh(service_mesh_config, mock_redis_pool, mock_circuit_breaker, mock_load_balancer, mock_monitoring):
    mesh = ServiceMesh(service_mesh_config)
    mesh.redis_pool = mock_redis_pool
    mesh.circuit_breaker = mock_circuit_breaker
    mesh.load_balancer = mock_load_balancer
    mesh.monitoring = mock_monitoring
    return mesh

class TestServiceMesh:
    @pytest.mark.asyncio
    async def test_route_request_success(self, service_mesh):
        """Test successful request routing"""
        response = await service_mesh.route_request("test-service", "/health", {"method": "GET"})
        assert response[1] == 200
        assert response[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_route_request_circuit_open(self, service_mesh, mock_circuit_breaker):
        """Test request routing when circuit is open"""
        mock_circuit_breaker.is_circuit_open = lambda *args: True
        service_mesh.circuit_breaker = mock_circuit_breaker
        
        response = await service_mesh.route_request("test-service", "/health", {"method": "GET"})
        assert response[1] == 503
        assert "Service unavailable" in response[0]["error"]

    @pytest.mark.asyncio
    async def test_get_service_status(self, service_mesh):
        """Test getting service status"""
        status = await service_mesh.get_service_status("test-service")
        assert "name" in status
        assert "timestamp" in status
        assert "load_balancer" in status
        assert "circuit_breaker" in status

    @pytest.mark.asyncio
    async def test_get_mesh_status(self, service_mesh):
        """Test getting mesh status"""
        status = await service_mesh.get_mesh_status()
        assert "timestamp" in status
        assert "services" in status
        assert "metrics" in status
        assert "alerts" in status

    @pytest.mark.asyncio
    async def test_update_config(self, service_mesh, service_mesh_config):
        """Test updating configuration"""
        new_config = {
            "circuit_breaker": {"failure_threshold": 10},
            "load_balancer": {"strategy": "random"},
            "monitoring": {"metrics_interval": 60}
        }
        
        await service_mesh.update_config(new_config)
        
        assert service_mesh_config.circuit_breaker_config["failure_threshold"] == 10
        assert service_mesh_config.load_balancer_config["strategy"] == "random"
        assert service_mesh_config.monitoring_config["metrics_interval"] == 60

    @pytest.mark.asyncio
    async def test_start_stop(self, service_mesh):
        """Test start and stop operations"""
        await service_mesh.start()
        await service_mesh.stop()

    @pytest.mark.asyncio
    async def test_monitoring_integration(self, service_mesh):
        """Test monitoring integration"""
        await service_mesh.monitoring.collect_metrics()
        status = await service_mesh.get_mesh_status()
        assert "metrics" in status

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, service_mesh):
        """Test circuit breaker integration"""
        await service_mesh.circuit_breaker.start_cleanup()
        assert not await service_mesh.circuit_breaker.is_circuit_open("test-service")

    @pytest.mark.asyncio
    async def test_load_balancer_integration(self, service_mesh):
        """Test load balancer integration"""
        await service_mesh.load_balancer.start_health_checking()
        response = await service_mesh.route_request("test-service", "/health", {"method": "GET"})
        assert response[1] == 200
