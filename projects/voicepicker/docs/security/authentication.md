# Authentication & Security Documentation

## Overview
VoicePicker implements enterprise-grade security with industry-standard practices including Argon2 password hashing, two-factor authentication (2FA), rate limiting, and account protection.

## Security Features

### 🔐 Password Security
- **Argon2**: Industry-standard password hashing (NSA/NIST recommended)
- **bcrypt fallback**: Supports existing passwords during migration
- **Memory cost**: 64MB (65536 KB)
- **Time cost**: 3 iterations
- **Parallelism**: 1 thread

### 🛡️ Two-Factor Authentication (2FA)
- **TOTP**: Time-based One-Time Passwords
- **Google Authenticator compatible**
- **QR code setup**: Easy user onboarding
- **Backup codes**: 8 recovery codes per user
- **30-second token window**: Standard TOTP timing

### 🚦 Rate Limiting & Protection
- **Login attempts**: 5 per minute per IP
- **Account locking**: 15 minutes after 5 failed attempts
- **Automatic unlock**: Time-based recovery
- **Failed attempt tracking**: Per-user counters

### 🔒 Security Headers
- **CORS**: Cross-Origin Resource Sharing protection
- **CSP**: Content Security Policy
- **HSTS**: HTTP Strict Transport Security
- **X-Frame-Options**: Clickjacking protection

## User Roles & Permissions

### Admin
- Full system access
- User management
- Warehouse configuration
- System settings

### Warehouse Manager  
- Warehouse layout configuration
- Template management
- Location zone management
- Operational oversight

### Supervisor
- Basic warehouse management
- Worker oversight
- Operational monitoring

## Authentication Flow

### Standard Login
1. User provides username/password
2. Password verified with Argon2
3. JWT token generated (24-hour expiry)
4. User authenticated

### 2FA Login
1. Standard login steps 1-2
2. System requests TOTP token
3. User provides 6-digit code from authenticator app
4. Token verified (30-second window)
5. JWT token generated
6. User authenticated

### 2FA Setup Process
1. User requests 2FA setup
2. System generates TOTP secret
3. QR code created for easy setup
4. User scans QR code with authenticator app
5. User provides test token to verify setup
6. System generates backup codes
7. 2FA enabled for user account

## API Endpoints

### Authentication
- `POST /api/users/login` - Enhanced login with 2FA support
- `GET /api/users/me` - Get current user profile
- `POST /api/users/register` - Create new user (admin only)

### 2FA Management
- `POST /api/users/2fa/setup` - Initialize 2FA setup
- `POST /api/users/2fa/verify` - Verify and enable 2FA
- `POST /api/users/2fa/disable` - Disable 2FA

### User Management
- `GET /api/users/` - List all users
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Soft delete user

## Database Schema

### Users Table
```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'warehouse_manager',
    
    -- Standard fields
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    
    -- 2FA fields
    totp_secret VARCHAR(32),
    is_2fa_enabled BOOLEAN DEFAULT false,
    backup_codes TEXT,
    
    -- Audit fields
    password_changed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Security Best Practices

### For Administrators
1. **Enable 2FA**: Always enable 2FA for admin accounts
2. **Strong passwords**: Minimum 12 characters with complexity
3. **Regular audits**: Review user access monthly
4. **Backup codes**: Store backup codes securely offline

### For Users
1. **Unique passwords**: Don't reuse passwords from other systems
2. **Authenticator apps**: Use Google Authenticator, Authy, or similar
3. **Backup codes**: Save backup codes in secure location
4. **Regular login**: Tokens expire after 24 hours

### For Developers
1. **Environment variables**: Never hardcode secrets
2. **JWT secrets**: Use strong, random JWT signing keys
3. **HTTPS only**: Always use HTTPS in production
4. **Security headers**: Ensure all security middleware is enabled

## Future Enhancements

### Planned Features
- **OAuth2/Social login**: Google, Microsoft integration
- **Email verification**: Account verification workflow
- **Password reset**: Secure password recovery
- **Session management**: Redis-based session storage
- **Audit logging**: Comprehensive security event logging

### Upgrade Path
The current system is designed for easy migration to more advanced authentication frameworks like FastAPI-Users or Authlib when needed.

## Troubleshooting

### Common Issues
1. **2FA setup fails**: Check system time synchronization
2. **Account locked**: Wait 15 minutes or contact admin
3. **Token expired**: Re-login to get new token
4. **Backup codes**: Use backup codes if authenticator unavailable

### Error Codes
- `401`: Invalid credentials or expired token
- `423`: Account locked due to failed attempts
- `400`: Invalid 2FA token or setup error
- `403`: Insufficient permissions for action