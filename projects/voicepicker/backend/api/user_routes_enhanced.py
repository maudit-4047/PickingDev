"""
Enhanced User Management System with 2FA
Upgrades the existing user system with industry-standard security features
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import json

# Enhanced security imports
from passlib.context import CryptContext
import pyotp
import qrcode
from io import BytesIO
import base64
import jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database.db_cofig import supabase
import os

router = APIRouter(prefix="/api/users", tags=["Enhanced User Management"])
security = HTTPBearer()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Enhanced password context with Argon2 (more secure than bcrypt)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # Argon2 preferred, bcrypt fallback for existing passwords
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB memory cost
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=1,      # 1 thread
)

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
    totp_token: Optional[str] = None  # For 2FA

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class Setup2FAResponse(BaseModel):
    secret: str
    qr_code_data_url: str
    backup_codes: List[str]
    message: str

class Verify2FARequest(BaseModel):
    token: str

class Enable2FARequest(BaseModel):
    password: str

# Enhanced helper functions
def hash_password(password: str) -> str:
    """Hash password using Argon2 (industry standard)"""
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash (supports both Argon2 and bcrypt)"""
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create JWT access token"""
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

# 2FA helper functions
def generate_totp_secret() -> str:
    """Generate TOTP secret for 2FA"""
    return pyotp.random_base32()

def generate_qr_code(user_email: str, secret: str) -> str:
    """Generate QR code data URL for 2FA setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name="VoicePicker Warehouse System"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    qr_data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{qr_data}"

def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 30s window

def generate_backup_codes() -> List[str]:
    """Generate backup codes for 2FA recovery"""
    import secrets
    return [f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" for _ in range(8)]

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    
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

# Enhanced API Endpoints

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Rate limiting: 5 attempts per minute
async def enhanced_login(request: Request, login_data: UserLogin):
    """Enhanced login with 2FA support and rate limiting"""
    
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
        # Increment failed attempts
        failed_attempts = user.get('failed_login_attempts', 0) + 1
        supabase.table('users').update({
            'failed_login_attempts': failed_attempts
        }).eq('id', user['id']).execute()
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            lock_until = datetime.utcnow() + timedelta(minutes=15)
            supabase.table('users').update({
                'locked_until': lock_until.isoformat()
            }).eq('id', user['id']).execute()
            
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed attempts. Try again in 15 minutes."
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is locked
    if user.get('locked_until'):
        lock_until = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
        if datetime.utcnow() < lock_until.replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked. Try again later."
            )
    
    # Check 2FA if enabled
    if user.get('is_2fa_enabled', False):
        if not login_data.totp_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA token required"
            )
        
        totp_secret = user.get('totp_secret')
        if not totp_secret or not verify_totp(totp_secret, login_data.totp_token):
            # Check backup codes
            backup_codes = user.get('backup_codes', '')
            if backup_codes and login_data.totp_token in backup_codes.split(','):
                # Remove used backup code
                remaining_codes = [code for code in backup_codes.split(',') if code != login_data.totp_token]
                supabase.table('users').update({
                    'backup_codes': ','.join(remaining_codes)
                }).eq('id', user['id']).execute()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA token"
                )
    
    # Successful login - reset failed attempts and update last login
    supabase.table('users').update({
        'last_login': datetime.utcnow().isoformat(),
        'failed_login_attempts': 0,
        'locked_until': None
    }).eq('id', user['id']).execute()
    
    # Create access token
    access_token = create_access_token(user['id'], user['username'], user['role'])
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=UserResponse(**{**user, 'is_2fa_enabled': user.get('is_2fa_enabled', False)})
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Register new user with enhanced password security"""
    
    # Check if username or email exists
    existing_user = supabase.table('users').select('id').or_(f'username.eq.{user_data.username},email.eq.{user_data.email}').execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Hash password with Argon2
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
        "is_verified": True,
        "is_2fa_enabled": False
    }
    
    response = supabase.table('users').insert(user_dict).execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {response.error.message}"
        )
    
    return UserResponse(**{**response.data[0], 'is_2fa_enabled': False})

# 2FA Endpoints

@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    request_data: Enable2FARequest,
    current_user: dict = Depends(get_current_user)
):
    """Setup 2FA for current user"""
    
    # Verify current password
    if not verify_password(request_data.password, current_user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Generate TOTP secret and QR code
    secret = generate_totp_secret()
    qr_code_data_url = generate_qr_code(current_user['email'], secret)
    backup_codes = generate_backup_codes()
    
    # Store secret and backup codes (not enabled yet)
    supabase.table('users').update({
        'totp_secret': secret,
        'backup_codes': ','.join(backup_codes)
    }).eq('id', current_user['id']).execute()
    
    return Setup2FAResponse(
        secret=secret,
        qr_code_data_url=qr_code_data_url,
        backup_codes=backup_codes,
        message="Scan QR code with your authenticator app, then verify with a token to enable 2FA"
    )

@router.post("/2fa/verify")
async def verify_and_enable_2fa(
    request_data: Verify2FARequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify TOTP token and enable 2FA"""
    
    totp_secret = current_user.get('totp_secret')
    if not totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /2fa/setup first"
        )
    
    # Verify token
    if not verify_totp(totp_secret, request_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP token"
        )
    
    # Enable 2FA
    supabase.table('users').update({
        'is_2fa_enabled': True
    }).eq('id', current_user['id']).execute()
    
    return {
        "message": "2FA enabled successfully",
        "backup_codes": current_user.get('backup_codes', '').split(','),
        "warning": "Save these backup codes in a secure location. You won't see them again."
    }

@router.post("/2fa/disable")
async def disable_2fa(
    request_data: Enable2FARequest,
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA for current user"""
    
    # Verify password
    if not verify_password(request_data.password, current_user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Disable 2FA
    supabase.table('users').update({
        'is_2fa_enabled': False,
        'totp_secret': None,
        'backup_codes': None
    }).eq('id', current_user['id']).execute()
    
    return {"message": "2FA disabled successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**{**current_user, 'is_2fa_enabled': current_user.get('is_2fa_enabled', False)})

@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(require_warehouse_manager)):
    """List all users"""
    
    response = supabase.table('users').select('*').order('role, username').execute()
    if hasattr(response, 'error') and response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {response.error.message}"
        )
    
    return [UserResponse(**{**user, 'is_2fa_enabled': user.get('is_2fa_enabled', False)}) for user in response.data]

# Health check
@router.get("/health")
async def health_check():
    """Health check for enhanced user management"""
    return {
        "status": "healthy",
        "service": "enhanced_user_management",
        "features": ["argon2_passwords", "2fa_totp", "rate_limiting", "account_locking"]
    }