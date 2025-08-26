"""
Authentication service
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from .models import User, UserCreate, UserLogin, UserRole, UserStatus, Token
from .security import (
    get_password_hash, verify_password, 
    create_access_token, create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

class AuthService:
    """Authentication service"""
    
    def __init__(self):
        # In production, this would use a real database
        self.users_db: Dict[str, Dict[str, Any]] = {}
        self.users_by_email: Dict[str, str] = {}
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_id = str(uuid.uuid4())
        admin_data = {
            "id": admin_id,
            "email": "admin@astro-aa.com",
            "username": "admin",
            "full_name": "System Administrator",
            "password_hash": get_password_hash("admin123"),
            "role": UserRole.ADMIN.value,
            "status": UserStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "email_verified": True,
            "preferences": {}
        }
        
        self.users_db[admin_id] = admin_data
        self.users_by_email["admin@astro-aa.com"] = admin_id
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        # Check if email already exists
        if user_data.email in self.users_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        for user in self.users_db.values():
            if user["username"] == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create user
        user_id = str(uuid.uuid4())
        user_dict = {
            "id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "password_hash": get_password_hash(user_data.password),
            "role": UserRole.BASIC.value,
            "status": UserStatus.PENDING_VERIFICATION.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "email_verified": False,
            "preferences": {}
        }
        
        self.users_db[user_id] = user_dict
        self.users_by_email[user_data.email] = user_id
        
        return User(**{k: v for k, v in user_dict.items() if k != "password_hash"})
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Authenticate user with email and password"""
        user_id = self.users_by_email.get(login_data.email)
        if not user_id:
            return None
        
        user_data = self.users_db.get(user_id)
        if not user_data:
            return None
        
        if not verify_password(login_data.password, user_data["password_hash"]):
            return None
        
        # Update last login
        user_data["last_login"] = datetime.utcnow().isoformat()
        
        return User(**{k: v for k, v in user_data.items() if k != "password_hash"})
    

    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = self.users_db.get(user_id)
        if not user_data:
            return None
        
        return User(**{k: v for k, v in user_data.items() if k != "password_hash"})
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self.users_by_email.get(email)
        if not user_id:
            return None
        
        return await self.get_user_by_id(user_id)
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user data"""
        if user_id not in self.users_db:
            return None
        
        user_data = self.users_db[user_id]
        
        # Update allowed fields
        allowed_fields = ["full_name", "preferences", "status", "role", "email_verified"]
        for field, value in update_data.items():
            if field in allowed_fields:
                user_data[field] = value
        
        return User(**{k: v for k, v in user_data.items() if k != "password_hash"})
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user_data = self.users_db.get(user_id)
        if not user_data:
            return False
        
        if not verify_password(old_password, user_data["password_hash"]):
            return False
        
        user_data["password_hash"] = get_password_hash(new_password)
        return True
    
    async def verify_email(self, user_id: str) -> bool:
        """Verify user email"""
        user_data = self.users_db.get(user_id)
        if not user_data:
            return False
        
        user_data["email_verified"] = True
        user_data["status"] = UserStatus.ACTIVE.value
        return True
    
    async def login(self, login_data: UserLogin) -> Token:
        """Login user and return tokens"""
        user = await self.authenticate_user(login_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token
        )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token"""
        from .security import verify_token
        
        try:
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user = await self.get_user_by_id(user_id)
            
            if not user or user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new access token
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email, "role": user.role.value}
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics (admin only)"""
        total_users = len(self.users_db)
        active_users = len([u for u in self.users_db.values() if u["status"] == UserStatus.ACTIVE.value])
        pending_users = len([u for u in self.users_db.values() if u["status"] == UserStatus.PENDING_VERIFICATION.value])
        
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = len([u for u in self.users_db.values() if u["role"] == role.value])
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "role_distribution": role_counts,
            "recent_registrations": len([
                u for u in self.users_db.values()
                if datetime.fromisoformat(u["created_at"]) > datetime.utcnow() - timedelta(days=7)
            ])
        }