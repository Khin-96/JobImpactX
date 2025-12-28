from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import time
from app.auth.security import verify_token
from app.db.session import SessionLocal
from app.db.models import AuditLog
import uuid

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Extract and verify JWT token from requests."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/auth/token"]:
            return await call_next(request)
        
        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"}
            )
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
            
            payload = verify_token(token)
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role", "Viewer")
            
        except Exception as e:
            logger.warning(f"Auth error: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        
        return await call_next(request)

class AuditMiddleware:
    """Log all actions to audit trail."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Log audit entry (async, don't block response)
        if hasattr(request.state, 'user_id'):
            try:
                self._log_audit(request, response, time.time() - start_time)
            except Exception as e:
                logger.error(f"Audit logging failed: {e}")
        
        return response
    
    def _log_audit(self, request: Request, response, duration: float):
        """Log to audit table."""
        db = SessionLocal()
        try:
            audit_log = AuditLog(
                id=uuid.uuid4(),
                user_id=getattr(request.state, 'user_id', None),
                action=self._get_action(request),
                resource_type=self._get_resource_type(request),
                status="success" if 200 <= response.status_code < 300 else "failure",
                ip_address=request.client.host if request.client else None,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000)
                }
            )
            db.add(audit_log)
            db.commit()
        finally:
            db.close()
    
    def _get_action(self, request: Request) -> str:
        """Determine action from request."""
        path = request.url.path
        if "/assess" in path:
            return "assessment"
        elif "/explain" in path:
            return "explain"
        elif "/scenario" in path:
            return "scenario"
        else:
            return "unknown"
    
    def _get_resource_type(self, request: Request) -> str:
        """Determine resource type from request."""
        if "/assess" in request.url.path:
            return "Assessment"
        elif "/explain" in request.url.path:
            return "Explanation"
        return None