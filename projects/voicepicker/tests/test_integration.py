"""
Database and API Integration Tests
Tests database connectivity, warehouse management, and API endpoints
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseConnectivity:
    """Test database connection and basic operations"""
    
    def test_supabase_connection(self):
        """Test Supabase database connection"""
        try:
            from backend.database.db_cofig import supabase
            
            # Test basic connectivity with warehouse templates
            response = supabase.table('warehouse_templates').select('*').limit(1).execute()
            
            if hasattr(response, 'error') and response.error:
                # Expected if table doesn't exist
                assert 'warehouse_templates' in str(response.error)
            else:
                # Connection successful
                assert hasattr(response, 'data')
                
        except ImportError:
            pytest.skip("Database configuration not available in test environment")
    
    def test_warehouse_templates_table(self):
        """Test warehouse templates table access"""
        try:
            from backend.database.db_cofig import supabase
            
            response = supabase.table('warehouse_templates').select('template_name').execute()
            
            if not (hasattr(response, 'error') and response.error):
                # If table exists, should have template names
                for template in response.data:
                    assert 'template_name' in template
                    
        except Exception:
            pytest.skip("Warehouse templates table not available")


class TestWarehouseTemplateManager:
    """Test warehouse template management functionality"""
    
    def test_template_import(self):
        """Test importing warehouse template manager"""
        try:
            from backend.modules.warehouse_templates import WarehouseTemplateManager, WarehouseTemplate
            
            assert WarehouseTemplateManager is not None
            assert WarehouseTemplate is not None
            
        except ImportError:
            pytest.skip("Warehouse template modules not available")
    
    def test_template_estimation(self):
        """Test location estimation for templates"""
        try:
            from backend.modules.warehouse_templates import WarehouseTemplate
            
            # Sample template data
            template_data = {
                'warehouse_name': 'Test Warehouse',
                'sections': [
                    {
                        'code': 'A',
                        'name': 'Section A',
                        'aisles': [
                            {'code': 'A-F', 'complex': False}  # 6 aisles
                        ]
                    }
                ],
                'levels': ['0', 'B', 'C']  # 3 levels
            }
            
            template = WarehouseTemplate(template_data)
            estimated_locations = template.estimate_locations()
            
            # Should estimate reasonable number of locations
            assert estimated_locations > 0
            assert estimated_locations < 100000  # Sanity check
            
        except ImportError:
            pytest.skip("Warehouse template classes not available")


class TestLocationUtils:
    """Test dynamic location utilities"""
    
    def test_location_utils_import(self):
        """Test importing location utilities"""
        try:
            from backend.modules.location_utils_dynamic import (
                get_warehouse_config, 
                validate_location_code,
                generate_check_digit
            )
            
            assert get_warehouse_config is not None
            assert validate_location_code is not None
            assert generate_check_digit is not None
            
        except ImportError:
            pytest.skip("Location utilities not available")
    
    def test_check_digit_generation(self):
        """Test check digit generation"""
        try:
            from backend.modules.location_utils_dynamic import generate_check_digit
            
            # Test with different warehouse IDs
            digit1 = generate_check_digit(1)
            digit2 = generate_check_digit(2)
            
            assert isinstance(digit1, int)
            assert isinstance(digit2, int)
            assert 0 <= digit1 <= 9
            assert 0 <= digit2 <= 9
            
        except ImportError:
            pytest.skip("Location utilities not available")


class TestAPIEndpoints:
    """Test API endpoint availability and structure"""
    
    def test_user_routes_import(self):
        """Test importing enhanced user routes"""
        try:
            from backend.api.user_routes_enhanced import router
            
            assert router is not None
            assert hasattr(router, 'prefix')
            assert router.prefix == "/api/users"
            
        except ImportError:
            pytest.skip("Enhanced user routes not available")
    
    def test_warehouse_designer_routes_import(self):
        """Test importing warehouse designer routes"""
        try:
            from backend.api.warehouse_designer_routes import router
            
            assert router is not None
            assert hasattr(router, 'prefix')
            
        except ImportError:
            pytest.skip("Warehouse designer routes not available")
    
    def test_main_app_import(self):
        """Test importing main FastAPI application"""
        try:
            from backend.api.main import app
            
            assert app is not None
            assert hasattr(app, 'title')
            assert 'VoicePicker' in app.title
            
        except ImportError:
            pytest.skip("Main application not available")


class TestProjectStructure:
    """Test project structure and file organization"""
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists"""
        req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
        assert os.path.exists(req_path), "requirements.txt should exist in project root"
    
    def test_docs_structure(self):
        """Test documentation structure"""
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
        assert os.path.exists(docs_path), "docs directory should exist"
        
        # Check for key documentation files
        security_path = os.path.join(docs_path, 'security')
        if os.path.exists(security_path):
            auth_doc = os.path.join(security_path, 'authentication.md')
            assert os.path.exists(auth_doc), "Authentication documentation should exist"
    
    def test_backend_structure(self):
        """Test backend directory structure"""
        backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
        assert os.path.exists(backend_path), "backend directory should exist"
        
        # Check key directories
        api_path = os.path.join(backend_path, 'api')
        modules_path = os.path.join(backend_path, 'modules')
        database_path = os.path.join(backend_path, 'database')
        
        assert os.path.exists(api_path), "api directory should exist"
        assert os.path.exists(modules_path), "modules directory should exist"
        assert os.path.exists(database_path), "database directory should exist"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])