"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from ..auth.models import UserCreate, UserLogin, Token, User, UserUpdate
from ..auth.service import AuthService
from ..auth.dependencies import (
    get_current_active_user, require_admin, rate_limit
)
from ..auth.security import security

router = APIRouter()

# Singleton auth service
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    _: bool = Depends(rate_limit(limit=5, window=3600))  # 5 registrations per hour
):
    """Register new user"""
    return await get_auth_service().create_user(user_data)

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    _: bool = Depends(rate_limit(limit=10, window=900))  # 10 login attempts per 15 minutes
):
    """User login"""
    return await get_auth_service().login(login_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Refresh access token"""
    refresh_token = credentials.credentials
    return await get_auth_service().refresh_token(refresh_token)

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user information"""
    updated_user = await get_auth_service().update_user(
        current_user.id, 
        update_data.dict(exclude_unset=True)
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""
    success = await get_auth_service().change_password(
        current_user.id, old_password, new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    return {"message": "Password changed successfully"}

@router.post("/verify-email/{user_id}")
async def verify_email(
    user_id: str,
    _: User = Depends(require_admin())
):
    """Verify user email (admin only)"""
    success = await get_auth_service().verify_email(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Email verified successfully"}

@router.get("/users")
async def list_users(
    _: User = Depends(require_admin())
):
    """List all users (admin only)"""
    stats = await get_auth_service().get_user_stats()
    return stats

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """User logout"""
    # In a real implementation, you would invalidate the token
    # For now, just return success (client should discard token)
    return {"message": "Logged out successfully"}