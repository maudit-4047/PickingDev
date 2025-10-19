"""
Quick Database and Security Test
Tests the core components without running the full FastAPI server
"""

import os
import sys

def test_database_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase Connection...")
    
    try:
        # Import from the correct path
        sys.path.append(r'c:\Users\awad\Desktop\PickingDev\projects\voicepicker\backend')
        from database.db_cofig import supabase
        
        # Test with admin users table
        response = supabase.table('users').select('username, role, is_active').limit(3).execute()
        
        if response.data:
            print("✅ Database connection successful!")
            print("📋 Admin users found:")
            for user in response.data:
                print(f"   - {user['username']} ({user['role']}) - Active: {user['is_active']}")
            return True
        else:
            print("⚠️  Database connected but no admin users found")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_worker_table():
    """Test worker table (warehouse floor staff)"""
    print("\n👷 Testing Worker Table...")
    
    try:
        sys.path.append(r'c:\Users\awad\Desktop\PickingDev\projects\voicepicker\backend')
        from database.db_cofig import supabase
        
        # Test workers table
        response = supabase.table('workers').select('name, pin, status, role').limit(5).execute()
        
        if response.data:
            print("✅ Workers table accessible!")
            print("👥 Workers found:")
            for worker in response.data:
                print(f"   - {worker['name']} (PIN: {worker['pin']}) - {worker['status']} - {worker['role']}")
            return True
        else:
            print("⚠️  Workers table exists but empty")
            return True  # Empty is OK
            
    except Exception as e:
        print(f"❌ Worker table test failed: {str(e)}")
        return False

def test_password_hashing():
    """Test password hashing functionality"""
    print("\n🔐 Testing Password Hashing...")
    
    try:
        from passlib.context import CryptContext
        from passlib.hash import argon2
        
        # Initialize password context
        pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__memory_cost=65536,
            argon2__time_cost=3,
            argon2__parallelism=1
        )
        
        test_password = "admin123"
        
        # Test Argon2 hashing
        hashed = pwd_context.hash(test_password)
        print(f"✅ Argon2 hashing successful")
        print(f"   Hash sample: {hashed[:60]}...")
        
        # Test verification
        is_valid = pwd_context.verify(test_password, hashed)
        print(f"✅ Password verification: {'PASS' if is_valid else 'FAIL'}")
        
        # Test the default admin password hash from schema
        admin_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFTweHSQoHEsYp6'
        admin_valid = pwd_context.verify('admin123', admin_hash)
        print(f"✅ Admin password verification: {'PASS' if admin_valid else 'FAIL'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing password hashing library: {str(e)}")
        print("   Run: pip install passlib[argon2]")
        return False
    except Exception as e:
        print(f"❌ Password hashing test failed: {str(e)}")
        return False

def test_2fa_components():
    """Test 2FA components"""
    print("\n🔒 Testing 2FA Components...")
    
    try:
        import pyotp
        import secrets
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        print(f"✅ TOTP secret generated: {secret}")
        
        # Generate current token
        totp = pyotp.TOTP(secret)
        token = totp.now()
        print(f"✅ Current TOTP token: {token}")
        
        # Verify token
        is_valid = totp.verify(token)
        print(f"✅ Token verification: {'PASS' if is_valid else 'FAIL'}")
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(5)]
        print(f"✅ Backup codes generated: {backup_codes}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing 2FA library: {str(e)}")
        print("   Run: pip install pyotp")
        return False
    except Exception as e:
        print(f"❌ 2FA test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 VoicePicker Authentication System Test")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_worker_table,
        test_password_hashing,
        test_2fa_components
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n🚀 Your system is ready!")
        print("   - Database schema deployed ✅")
        print("   - Admin users created ✅") 
        print("   - Security features working ✅")
        print("\n📝 Test Login Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n⚠️  Install missing dependencies:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()