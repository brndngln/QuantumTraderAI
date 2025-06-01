from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import jwt
from datetime import datetime, timedelta
import os
from enum import Enum
from pydantic import BaseModel

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityMetrics(BaseModel):
    risk_score: float
    confidence: float
    anomalies_detected: int
    threat_level: SecurityLevel
    last_scan: datetime

class SecurityMiddleware:
    def __init__(self):
        self.security_levels = {
            SecurityLevel.LOW: 0.3,
            SecurityLevel.MEDIUM: 0.6,
            SecurityLevel.HIGH: 0.8,
            SecurityLevel.CRITICAL: 1.0
        }
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secure-secret')
        self.bearer_scheme = HTTPBearer()
        
    async def __call__(self, request: Request, call_next) -> Response:
        try:
            # Check for security headers
            self._validate_security_headers(request)
            
            # Check for HTTPS
            self._require_https(request)
            
            # Validate JWT token
            credentials = await self._validate_jwt(request)
            
            # Perform security scan
            security_metrics = self._perform_security_scan(request)
            
            # Check threat level
            if security_metrics.threat_level == SecurityLevel.CRITICAL:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Critical security threat detected"
                )
            
            # Add security metrics to request state
            request.state.security_metrics = security_metrics
            
            # Call next middleware
            response = await call_next(request)
            
            # Add security headers to response
            self._add_security_headers(response)
            
            return response
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Security error: {str(e)}"
            )
    
    def _validate_security_headers(self, request: Request) -> None:
        """
        Validate security-related headers
        """
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        for header in required_headers:
            if header not in request.headers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing security header: {header}"
                )
    
    def _require_https(self, request: Request) -> None:
        """
        Require HTTPS for all requests
        """
        if not request.url.scheme == 'https':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HTTPS required"
            )
    
    async def _validate_jwt(self, request: Request) -> HTTPAuthorizationCredentials:
        """
        Validate JWT token
        """
        credentials = await self.bearer_scheme(request)
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=['HS256']
            )
            return credentials
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
            
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def _perform_security_scan(self, request: Request) -> SecurityMetrics:
        """
        Perform security scan on request
        """
        # Initialize metrics
        metrics = {
            'risk_score': 0.0,
            'confidence': 1.0,
            'anomalies_detected': 0
        }
        
        # Check for suspicious patterns
        if self._detect_suspicious_patterns(request):
            metrics['risk_score'] += 0.5
            metrics['anomalies_detected'] += 1
            
        # Check for rate limiting
        if self._check_rate_limit(request):
            metrics['risk_score'] += 0.3
            metrics['anomalies_detected'] += 1
            
        # Check for known threats
        if self._check_known_threats(request):
            metrics['risk_score'] += 0.7
            metrics['anomalies_detected'] += 1
            
        # Determine threat level
        threat_level = self._determine_threat_level(metrics['risk_score'])
        
        return SecurityMetrics(
            risk_score=metrics['risk_score'],
            confidence=metrics['confidence'],
            anomalies_detected=metrics['anomalies_detected'],
            threat_level=threat_level,
            last_scan=datetime.now()
        )
    
    def _detect_suspicious_patterns(self, request: Request) -> bool:
        """
        Detect suspicious patterns in request
        """
        suspicious_patterns = [
            r'union.*select',
            r'drop.*table',
            r'insert.*into',
            r'update.*set',
            r'delete.*from'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, request.url.path, re.IGNORECASE):
                return True
                
        return False
    
    def _check_rate_limit(self, request: Request) -> bool:
        """
        Check rate limiting
        """
        # Implementation depends on rate limiting strategy
        return False
    
    def _check_known_threats(self, request: Request) -> bool:
        """
        Check against known threat patterns
        """
        # Implementation depends on threat database
        return False
    
    def _determine_threat_level(self, risk_score: float) -> SecurityLevel:
        """
        Determine threat level based on risk score
        """
        if risk_score >= self.security_levels[SecurityLevel.CRITICAL]:
            return SecurityLevel.CRITICAL
        elif risk_score >= self.security_levels[SecurityLevel.HIGH]:
            return SecurityLevel.HIGH
        elif risk_score >= self.security_levels[SecurityLevel.MEDIUM]:
            return SecurityLevel.MEDIUM
        return SecurityLevel.LOW
    
    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to response
        """
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
    def create_jwt(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """
        Create JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm='HS256')
        return encoded_jwt
