import pytest
import asyncio
import aioredis
import json
from datetime import datetime
from service_mesh.service_mesh import ServiceMesh, ServiceMeshConfig
from service_mesh.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from service_mesh.load_balancer import LoadBalancer, LoadBalancerConfig
from service_mesh.monitoring import Monitoring, MonitoringConfig
from service_mesh.security import SecurityManager

@pytest.fixture
def mock_security_manager():
    class MockSecurityManager:
        async def verify_token(self, token: str):
            return True
            
        async def generate_token(self, user_id: str):
            return "test-token"
            
        async def revoke_token(self, token: str):
            pass
            
    return MockSecurityManager()

@pytest.fixture
def mock_rate_limiter():
    class MockRateLimiter:
        async def rate_limit(self, request):
            return True
            
    return MockRateLimiter()

@pytest.fixture
def service_mesh_with_security(service_mesh_config, mock_redis_pool, mock_security_manager, mock_rate_limiter):
    mesh = ServiceMesh(service_mesh_config)
    mesh.redis_pool = mock_redis_pool
    mesh.security_manager = mock_security_manager
    mesh.rate_limiter = mock_rate_limiter
    return mesh

class TestAdditionalFeatures:
    @pytest.mark.asyncio
    async def test_security_integration(self, service_mesh_with_security):
        """Test security integration"""
        token = await service_mesh_with_security.security_manager.generate_token("test-user")
        assert token == "test-token"
        assert await service_mesh_with_security.security_manager.verify_token(token)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, service_mesh_with_security, mock_rate_limiter):
        """Test rate limiting"""
        mock_rate_limiter.rate_limit = lambda *args: False
        service_mesh_with_security.rate_limiter = mock_rate_limiter
        
        response = await service_mesh_with_security.route_request(
            "test-service",
            "/api/endpoint",
            {"method": "GET"}
        )
        assert response[1] == 429
        assert "Rate limit exceeded" in response[0]["error"]

    @pytest.mark.asyncio
    async def test_token_revocation(self, service_mesh_with_security):
        """Test token revocation"""
        token = await service_mesh_with_security.security_manager.generate_token("test-user")
        await service_mesh_with_security.security_manager.revoke_token(token)
        assert not await service_mesh_with_security.security_manager.verify_token(token)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, service_mesh_with_security):
        """Test concurrent request handling"""
        async def make_request():
            return await service_mesh_with_security.route_request(
                "test-service",
                "/api/endpoint",
                {"method": "GET"}
            )
            
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        assert all(result[1] == 200 for result in results)

    @pytest.mark.asyncio
    async def test_load_balancer_strategies(self, service_mesh_with_security):
        """Test different load balancing strategies"""
        # Test round-robin
        service_mesh_with_security.load_balancer.config.strategy = "round_robin"
        response = await service_mesh_with_security.route_request(
            "test-service",
            "/api/endpoint",
            {"method": "GET"}
        )
        assert response[1] == 200
        
        # Test weighted round-robin
        service_mesh_with_security.load_balancer.config.strategy = "weighted_round_robin"
        response = await service_mesh_with_security.route_request(
            "test-service",
            "/api/endpoint",
            {"method": "GET"}
        )
        assert response[1] == 200
        
        # Test random
        service_mesh_with_security.load_balancer.config.strategy = "random"
        response = await service_mesh_with_security.route_request(
            "test-service",
            "/api/endpoint",
            {"method": "GET"}
        )
        assert response[1] == 200

    @pytest.mark.asyncio
    async def test_monitoring_metrics(self, service_mesh_with_security):
        """Test monitoring metrics collection"""
        await service_mesh_with_security.monitoring.collect_metrics()
        metrics = await service_mesh_with_security.monitoring.get_metrics_history("system", 3600)
        assert len(metrics) > 0
        assert "cpu" in metrics[0]
        assert "memory" in metrics[0]
        assert "disk" in metrics[0]

    @pytest.mark.asyncio
    async def test_alert_thresholds(self, service_mesh_with_security):
        """Test alert thresholds"""
        # Set high CPU usage to trigger alert
        service_mesh_with_security.monitoring.config.alert_thresholds["cpu"]["warning"] = 10
        
        await service_mesh_with_security.monitoring.check_thresholds({
            "cpu": 20,
            "memory": 50,
            "disk": 30
        })
        
        alerts = await service_mesh_with_security.monitoring.get_alert_history(3600)
        assert len(alerts) > 0
        assert "WARNING: cpu" in alerts[0]["message"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, service_mesh_with_security):
        """Test circuit breaker recovery"""
        # Open circuit
        await service_mesh_with_security.circuit_breaker.update_state("test-service", "latest", False)
        assert await service_mesh_with_security.circuit_breaker.is_circuit_open("test-service")
        
        # Wait for recovery
        await asyncio.sleep(service_mesh_with_security.circuit_breaker.config.reset_timeout + 1)
        
        # Test half-open state
        response = await service_mesh_with_security.route_request(
            "test-service",
            "/api/endpoint",
            {"method": "GET"}
        )
        assert response[1] == 200
        
        # Verify circuit closed
        assert not await service_mesh_with_security.circuit_breaker.is_circuit_open("test-service")
