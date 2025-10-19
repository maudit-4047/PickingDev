"""
Administrative User Management API Routes
Handles authentication and management for system administrators and warehouse managers
Note: This is separate from workers (who use PIN-based authentication for voice picking)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
from database.db_cofig import supabase
import os

router = APIRouter(prefix="/api/users", tags=["User Management"])
security = HTTPBearer()

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "warehouse_manager"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT access token"""
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    
    # Get user from database
    response = supabase.table('users').select('*').eq('id', user_id).eq('is_active', True).single().execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return response.data

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

async def require_warehouse_manager(current_user: dict = Depends(get_current_user)):
    """Require warehouse manager or admin role"""
    if current_user['role'] not in ['admin', 'warehouse_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Warehouse manager or admin role required"
        )
    return current_user

# API Endpoints

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Register a new user (admin only)"""
    
    # Check if username or email already exists
    existing_user = supabase.table('users').select('id').or_(f'username.eq.{user_data.username},email.eq.{user_data.email}').execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "role": user_data.role,
        "is_active": True,
        "is_verified": True
    }
    
    response = supabase.table('users').insert(user_dict).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {response.error.message}"
        )
    
    return UserResponse(**response.data[0])

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Authenticate user and return access token"""
    
    # Get user by username
    response = supabase.table('users').select('*').eq('username', login_data.username).eq('is_active', True).single().execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = response.data
    
    # Verify password
    if not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Update last login
    supabase.table('users').update({'last_login': datetime.utcnow().isoformat()}).eq('id', user['id']).execute()
    
    # Create access token
    access_token = create_access_token(user['id'], user['username'], user['role'])
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=UserResponse(**user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(require_warehouse_manager)):
    """List all users (warehouse manager or admin only)"""
    
    response = supabase.table('users').select('*').order('role, username').execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {response.error.message}"
        )
    
    return [UserResponse(**user) for user in response.data]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(require_admin)):
    """Update user (admin only)"""
    
    # Prepare update data
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )
    
    # Update user
    response = supabase.table('users').update(update_data).eq('id', user_id).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {response.error.message}"
        )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**response.data[0])

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    
    # Soft delete by setting is_active to False
    response = supabase.table('users').update({'is_active': False}).eq('id', user_id).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {response.error.message}"
        )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.get("/{user_id}/permissions")
async def get_user_permissions(user_id: str, current_user: dict = Depends(require_warehouse_manager)):
    """Get user permissions"""
    
    response = supabase.table('user_permissions').select('*').eq('user_id', user_id).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch permissions: {response.error.message}"
        )
    
    return response.data

@router.post("/{user_id}/permissions")
async def grant_permission(
    user_id: str, 
    permission: str, 
    resource: str, 
    resource_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Grant permission to user (admin only)"""
    
    permission_data = {
        "user_id": user_id,
        "permission": permission,
        "resource": resource,
        "resource_id": resource_id,
        "granted_by": current_user['id']
    }
    
    response = supabase.table('user_permissions').insert(permission_data).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {response.error.message}"
        )
    
    return response.data[0]

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for user management system"""
    return {"status": "healthy", "service": "user_management"}