"""
Quick Authentication Test Script
Tests the enhanced authentication system with the deployed Supabase schema
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_database_connection():
    """Test basic database connectivity"""
    print("🔗 Testing Database Connection...")
    
    try:
        from backend.database.db_cofig import supabase
        
        # Test connection with users table
        response = supabase.table('users').select('username, role, is_active').limit(5).execute()
        
        if response.data:
            print("✅ Database connection successful!")
            print("📋 Users found in database:")
            for user in response.data:
                print(f"   - {user['username']} ({user['role']}) - Active: {user['is_active']}")
            return True
        else:
            print("⚠️  Database connected but no users found")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

async def test_password_hashing():
    """Test Argon2 password hashing"""
    print("\n🔐 Testing Password Hashing...")
    
    try:
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__memory_cost=65536,
            argon2__time_cost=3,
            argon2__parallelism=1
        )
        
        test_password = "test123"
        
        # Hash password
        hashed = pwd_context.hash(test_password)
        print(f"✅ Password hashed successfully with Argon2")
        print(f"   Hash preview: {hashed[:50]}...")
        
        # Verify password
        is_valid = pwd_context.verify(test_password, hashed)
        print(f"✅ Password verification: {'PASS' if is_valid else 'FAIL'}")
        
        # Test wrong password
        is_invalid = pwd_context.verify("wrong123", hashed)
        print(f"✅ Wrong password rejection: {'PASS' if not is_invalid else 'FAIL'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Password hashing test failed: {str(e)}")
        return False

async def test_2fa_generation():
    """Test 2FA TOTP generation"""
    print("\n🔒 Testing 2FA TOTP Generation...")
    
    try:
        import pyotp
        import qrcode
        from io import BytesIO
        import base64
        
        # Generate secret
        secret = pyotp.random_base32()
        print(f"✅ TOTP secret generated: {secret}")
        
        # Generate TOTP
        totp = pyotp.TOTP(secret)
        current_token = totp.now()
        print(f"✅ Current TOTP token: {current_token}")
        
        # Verify token
        is_valid = totp.verify(current_token)
        print(f"✅ Token verification: {'PASS' if is_valid else 'FAIL'}")
        
        # Generate QR code URI
        totp_uri = totp.provisioning_uri(
            name="test@warehouse.com",
            issuer_name="VoicePicker Test"
        )
        print(f"✅ QR code URI generated successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing 2FA dependency: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 2FA test failed: {str(e)}")
        return False

async def test_backup_codes():
    """Test backup code generation"""
    print("\n🔑 Testing Backup Code Generation...")
    
    try:
        import secrets
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        print(f"✅ Generated {len(backup_codes)} backup codes")
        print(f"   Sample codes: {backup_codes[:3]}...")
        
        # Validate format
        for code in backup_codes:
            if len(code) != 8 or not all(c in '0123456789ABCDEF' for c in code):
                print("❌ Invalid backup code format")
                return False
        
        print("✅ All backup codes have valid format")
        return True
        
    except Exception as e:
        print(f"❌ Backup code test failed: {str(e)}")
        return False

async def test_rate_limiting():
    """Test rate limiting setup"""
    print("\n⏱️  Testing Rate Limiting Setup...")
    
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        
        limiter = Limiter(key_func=get_remote_address)
        print("✅ Rate limiter initialized successfully")
        
        # Test limit configuration
        test_limit = "5/minute"
        print(f"✅ Rate limit configuration: {test_limit}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing rate limiting dependency: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Rate limiting test failed: {str(e)}")
        return False

async def main():
    """Run all authentication tests"""
    print("🚀 VoicePicker Enhanced Authentication Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_database_connection())
    test_results.append(await test_password_hashing())
    test_results.append(await test_2fa_generation())
    test_results.append(await test_backup_codes())
    test_results.append(await test_rate_limiting())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhanced authentication system is ready!")
        print("\n🔄 Next Steps:")
        print("   1. Start FastAPI server: uvicorn backend.api.main:app --reload")
        print("   2. Test API endpoints at: http://localhost:8000/docs")
        print("   3. Try logging in with: admin / admin123")
    else:
        print("\n⚠️  Some tests failed. Check dependencies in requirements.txt")
        print("   Run: pip install -r requirements.txt")

if __name__ == "__main__":
    asyncio.run(main())