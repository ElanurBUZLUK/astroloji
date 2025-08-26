"""
Authentication dependencies for FastAPI
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .security import verify_token, rate_limiter
from .models import User, UserRole, UserStatus, TokenData
from .service import AuthService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")
    exp = payload.get("exp")
    iat = payload.get("iat")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return TokenData(
        user_id=user_id,
        email=email,
        role=UserRole(role),
        exp=exp,
        iat=iat
    )

async def get_current_active_user(
    token_data: TokenData = Depends(get_current_user)
) -> User:
    """Get current active user"""
    from ..api.auth import get_auth_service
    auth_service = get_auth_service()
    user = await auth_service.get_user_by_id(token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user

def require_role(required_role: UserRole):
    """Dependency to require specific user role"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        from .security import auth_manager
        
        if not auth_manager.has_permission(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role.value}"
            )
        
        return current_user
    
    return role_checker

def require_admin():
    """Dependency to require admin role"""
    return require_role(UserRole.ADMIN)

def require_premium():
    """Dependency to require premium role or higher"""
    return require_role(UserRole.PREMIUM)

def rate_limit(limit: int = 100, window: int = 3600):
    """Rate limiting dependency"""
    def rate_limit_checker(request: Request):
        client_ip = request.client.host
        
        if not rate_limiter.is_allowed(client_ip, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return True
    
    return rate_limit_checker

# Optional authentication (for public endpoints that can benefit from user context)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        token_data = TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=UserRole(payload.get("role")),
            exp=payload.get("exp"),
            iat=payload.get("iat")
        )
        from ..api.auth import get_auth_service
        auth_service = get_auth_service()
        user = await auth_service.get_user_by_id(token_data.user_id)
        return user if user and user.status == UserStatus.ACTIVE else None
    except:
        return None