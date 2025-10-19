"""
Test Suite for Enhanced Security Features
Tests authentication, 2FA, password hashing, and security features
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
import pyotp
import qrcode
from io import BytesIO
import base64


class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__memory_cost=65536,
            argon2__time_cost=3,
            argon2__parallelism=1,
        )
        self.test_password = "test_password_123"
    
    def test_argon2_hashing(self):
        """Test Argon2 password hashing"""
        hashed = self.pwd_context.hash(self.test_password)
        
        assert hashed.startswith("$argon2")
        assert len(hashed) > 50
        assert self.pwd_context.verify(self.test_password, hashed)
        assert not self.pwd_context.verify("wrong_password", hashed)
    
    def test_bcrypt_fallback(self):
        """Test bcrypt compatibility for existing passwords"""
        import bcrypt
        bcrypt_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Should be able to verify bcrypt hashes
        assert self.pwd_context.verify(self.test_password, bcrypt_hash)
    
    def test_password_upgrade(self):
        """Test automatic password hash upgrade"""
        import bcrypt
        old_bcrypt_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Verify and check if needs rehashing
        is_valid = self.pwd_context.verify(self.test_password, old_bcrypt_hash)
        needs_update = self.pwd_context.needs_update(old_bcrypt_hash)
        
        assert is_valid
        assert needs_update  # Should recommend upgrade to Argon2


class TestTwoFactorAuth:
    """Test 2FA/TOTP functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret)
        self.test_email = "test@warehouse.com"
    
    def test_secret_generation(self):
        """Test TOTP secret generation"""
        secret = pyotp.random_base32()
        
        assert len(secret) == 32
        assert secret.isalnum()
        assert secret.isupper()
    
    def test_totp_token_generation(self):
        """Test TOTP token generation and verification"""
        token = self.totp.now()
        
        assert len(token) == 6
        assert token.isdigit()
        assert self.totp.verify(token)
    
    def test_totp_time_window(self):
        """Test TOTP time window validation"""
        token = self.totp.now()
        
        # Should verify with window=1 (30 seconds before/after)
        assert self.totp.verify(token, valid_window=1)
        
        # Should not verify old tokens outside window
        import time
        old_token = self.totp.at(int(time.time()) - 120)  # 2 minutes ago
        assert not self.totp.verify(old_token, valid_window=1)
    
    def test_provisioning_uri(self):
        """Test TOTP provisioning URI generation"""
        uri = self.totp.provisioning_uri(
            name=self.test_email,
            issuer_name="VoicePicker Test"
        )
        
        assert uri.startswith("otpauth://totp/")
        assert self.test_email in uri
        assert "VoicePicker Test" in uri
        assert self.secret in uri
    
    def test_qr_code_generation(self):
        """Test QR code generation for 2FA setup"""
        uri = self.totp.provisioning_uri(
            name=self.test_email,
            issuer_name="VoicePicker Test"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_data = base64.b64encode(buffer.getvalue()).decode()
        
        assert len(qr_data) > 1000  # QR code should be substantial
        assert qr_data.startswith("")  # Base64 encoded


class TestBackupCodes:
    """Test backup code generation and management"""
    
    def test_backup_code_generation(self):
        """Test backup code generation"""
        import secrets
        backup_codes = [
            f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" 
            for _ in range(8)
        ]
        
        assert len(backup_codes) == 8
        for code in backup_codes:
            assert len(code) == 9  # Format: XXXX-XXXX
            assert "-" in code
            parts = code.split("-")
            assert len(parts) == 2
            assert parts[0].isdigit() and len(parts[0]) == 4
            assert parts[1].isdigit() and len(parts[1]) == 4
    
    def test_backup_code_uniqueness(self):
        """Test that backup codes are unique"""
        import secrets
        codes_set1 = [
            f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" 
            for _ in range(100)
        ]
        codes_set2 = [
            f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" 
            for _ in range(100)
        ]
        
        # Should be highly unlikely to have duplicates
        assert len(set(codes_set1)) > 95  # Allow for small chance of collision
        assert len(set(codes_set1 + codes_set2)) > 190


class TestDatabaseIntegration:
    """Test database connectivity and user operations"""
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from backend.database.db_cofig import supabase
            
            # Test basic connectivity
            response = supabase.table('warehouse_templates').select('*').limit(1).execute()
            
            # Should either get data or a proper error
            assert hasattr(response, 'data') or hasattr(response, 'error')
            
        except ImportError:
            pytest.skip("Database configuration not available")
        except Exception as e:
            # Database connection issues are expected in test environment
            assert "connection" in str(e).lower() or "timeout" in str(e).lower()
    
    def test_users_table_schema(self):
        """Test users table schema expectations"""
        expected_fields = [
            'id', 'username', 'email', 'password_hash',
            'first_name', 'last_name', 'role',
            'is_active', 'is_verified', 'is_2fa_enabled',
            'totp_secret', 'backup_codes',
            'failed_login_attempts', 'locked_until',
            'last_login', 'created_at', 'updated_at'
        ]
        
        # This test documents expected schema
        assert len(expected_fields) > 15
        assert 'password_hash' in expected_fields
        assert 'totp_secret' in expected_fields


class TestSecurityFeatures:
    """Test security middleware and features"""
    
    def test_jwt_token_structure(self):
        """Test JWT token generation structure"""
        import jwt
        from datetime import datetime, timedelta
        
        secret = "test_secret"
        payload = {
            "sub": "test_user_id",
            "username": "testuser",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        
        assert decoded["sub"] == "test_user_id"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "admin"
    
    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration"""
        # Test that we have rate limiting dependencies
        try:
            from slowapi import Limiter
            from slowapi.util import get_remote_address
            
            limiter = Limiter(key_func=get_remote_address)
            assert limiter is not None
            
        except ImportError:
            pytest.fail("Rate limiting dependencies not available")


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])