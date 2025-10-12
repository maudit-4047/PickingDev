"""
Warehouse Template Management System
Handles creation, loading, and management of warehouse layout templates
"""

import json
from typing import Dict, List, Optional
from database.db_cofig import supabase

class WarehouseTemplate:
    def __init__(self, template_data: Dict):
        self.data = template_data
    
    @property
    def name(self) -> str:
        return self.data.get('warehouse_name', 'Unnamed Warehouse')
    
    @property
    def sections(self) -> List[Dict]:
        return self.data.get('sections', [])
    
    @property
    def levels(self) -> List[str]:
        return self.data.get('levels', ['1', '2', '3'])
    
    @property
    def location_pattern(self) -> str:
        return self.data.get('location_naming_pattern', '{section}{aisle}-{bay:03d}')
    
    def estimate_locations(self) -> int:
        """Estimate total number of locations this template will create"""
        total = 0
        default_bays = 99
        default_levels = len(self.levels)
        
        for section in self.sections:
            aisles = section.get('aisles', [])
            section_total = 0
            
            for aisle_config in aisles:
                aisle_code = aisle_config.get('code', 'A')
                is_complex = aisle_config.get('complex', False)
                
                # Parse aisle range (e.g., "A-Z" = 26 aisles)
                aisle_count = self._parse_aisle_count(aisle_code)
                
                if is_complex:
                    subsections = aisle_config.get('subsections', ['1', '3', '7'])
                    # Complex: (bays * subsections) + (bays * upper_levels)
                    section_total += aisle_count * default_bays * (len(subsections) + (default_levels - 1))
                else:
                    # Simple: bays * all_levels
                    section_total += aisle_count * default_bays * default_levels
            
            total += section_total
        
        return total
    
    def _parse_aisle_count(self, aisle_code: str) -> int:
        """Parse aisle code to count number of aisles"""
        if '-' in aisle_code:
            # Range like "A-Z" or "A-F"
            start, end = aisle_code.split('-')
            if len(start) == 1 and len(end) == 1:
                return ord(end) - ord(start) + 1
            return 1
        elif ',' in aisle_code:
            # List like "A,B,C,D,E"
            return len(aisle_code.split(','))
        else:
            # Single aisle
            return 1

class WarehouseTemplateManager:
    
    @staticmethod
    def get_all_templates() -> List[Dict]:
        """Get all available warehouse templates"""
        response = supabase.table('warehouse_templates').select('*').eq('is_public', True).order('category, template_name').execute()
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error.message)
        
        # Add computed fields
        for template in response.data:
            template_obj = WarehouseTemplate(template['template_data'])
            template['estimated_locations'] = template_obj.estimate_locations()
            template['sections_count'] = len(template_obj.sections)
            template['levels_count'] = len(template_obj.levels)
        
        return response.data
    
    @staticmethod
    def get_template_by_id(template_id: int) -> Dict:
        """Get a specific template by ID"""
        response = supabase.table('warehouse_templates').select('*').eq('id', template_id).single().execute()
        if hasattr(response, 'error') and response.error:
            raise Exception('Template not found')
        return response.data
    
    @staticmethod
    def get_templates_by_category(category: str) -> List[Dict]:
        """Get templates filtered by category"""
        response = supabase.table('warehouse_templates').select('*').eq('category', category).eq('is_public', True).execute()
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error.message)
        return response.data
    
    @staticmethod
    def create_warehouse_from_template(template_id: int, warehouse_name: str, user_id: str) -> int:
        """Create a new warehouse from a template"""
        # Get template
        template = WarehouseTemplateManager.get_template_by_id(template_id)
        template_data = template['template_data']
        
        # Create warehouse config
        warehouse_config = {
            'warehouse_name': warehouse_name,
            'description': f"Created from template: {template['template_name']}",
            'layout_type': 'template',
            'location_naming_pattern': template_data.get('location_naming_pattern', '{section}{aisle}-{bay:03d}'),
            'created_by': user_id
        }
        
        warehouse_response = supabase.table('warehouse_config').insert(warehouse_config).execute()
        if hasattr(warehouse_response, 'error') and warehouse_response.error:
            raise Exception(warehouse_response.error.message)
        
        warehouse_id = warehouse_response.data[0]['id']
        
        # Create sections from template
        WarehouseTemplateManager._create_sections_from_template(warehouse_id, template_data)
        
        # Link user to warehouse
        user_warehouse = {
            'user_id': user_id,
            'warehouse_id': warehouse_id,
            'is_default': True,
            'role': 'owner'
        }
        supabase.table('user_warehouses').insert(user_warehouse).execute()
        
        return warehouse_id
    
    @staticmethod
    def _create_sections_from_template(warehouse_id: int, template_data: Dict):
        """Create warehouse sections, aisles, and levels from template data"""
        sections = template_data.get('sections', [])
        default_levels = template_data.get('levels', ['1', '2', '3'])
        level_names_array = template_data.get('level_names', [])
        equipment_map = template_data.get('equipment', {})
        
        # Convert level_names array to dictionary if needed
        if isinstance(level_names_array, list):
            level_names = {default_levels[i]: level_names_array[i] for i in range(min(len(default_levels), len(level_names_array)))}
        else:
            level_names = level_names_array or {}
        
        for i, section_data in enumerate(sections):
            # Create section
            section = {
                'warehouse_id': warehouse_id,
                'section_code': section_data['code'],
                'section_name': section_data['name'],
                'description': section_data.get('description', ''),
                'color_code': section_data.get('color', '#4ECDC4'),
                'sort_order': i
            }
            
            section_response = supabase.table('warehouse_sections').insert(section).execute()
            if hasattr(section_response, 'error') and section_response.error:
                raise Exception(f"Error creating section: {section_response.error.message}")
            section_id = section_response.data[0]['id']
            
            # Create aisles for this section
            aisles = section_data.get('aisles', [])
            for j, aisle_config in enumerate(aisles):
                aisle_codes = WarehouseTemplateManager._parse_aisle_codes(aisle_config['code'])
                
                for k, aisle_code in enumerate(aisle_codes):
                    aisle = {
                        'section_id': section_id,
                        'aisle_code': aisle_code,
                        'aisle_name': f"Aisle {section_data['code']}{aisle_code}",
                        'is_complex': aisle_config.get('complex', False),
                        'bay_range_start': 1,
                        'bay_range_end': 99,
                        'sort_order': k
                    }
                    
                    aisle_response = supabase.table('warehouse_aisles').insert(aisle).execute()
                    if hasattr(aisle_response, 'error') and aisle_response.error:
                        raise Exception(f"Error creating aisle: {aisle_response.error.message}")
                    aisle_id = aisle_response.data[0]['id']
                    
                    # Create levels for this aisle
                    for l, level_code in enumerate(default_levels):
                        level_name = level_names.get(level_code, f"Level {level_code}")
                        equipment = WarehouseTemplateManager._get_equipment_for_level(level_code, equipment_map)
                        
                        level = {
                            'aisle_id': aisle_id,
                            'level_code': level_code,
                            'level_name': level_name,
                            'level_type': 'picker' if level_code == '0' else 'forklift',
                            'equipment_required': equipment,
                            'sort_order': l
                        }
                        
                        level_response = supabase.table('warehouse_levels').insert(level).execute()
                        if hasattr(level_response, 'error') and level_response.error:
                            raise Exception(f"Error creating level: {level_response.error.message}")
                        level_id = level_response.data[0]['id']
                        
                        # Create subsections if complex aisle and level 0
                        if aisle_config.get('complex', False) and level_code == '0':
                            subsections = aisle_config.get('subsections', ['1', '3', '7'])
                            for m, subsection_code in enumerate(subsections):
                                subsection = {
                                    'level_id': level_id,
                                    'subsection_code': subsection_code,
                                    'subsection_name': f"Subsection {subsection_code}",
                                    'sort_order': m
                                }
                                subsection_response = supabase.table('warehouse_subsections').insert(subsection).execute()
                                if hasattr(subsection_response, 'error') and subsection_response.error:
                                    raise Exception(f"Error creating subsection: {subsection_response.error.message}")
    
    @staticmethod
    def _parse_aisle_codes(aisle_code: str) -> List[str]:
        """Parse aisle code pattern into individual codes"""
        if '-' in aisle_code and len(aisle_code) == 3:  # e.g., "A-Z"
            start, end = aisle_code.split('-')
            return [chr(i) for i in range(ord(start), ord(end) + 1)]
        elif ',' in aisle_code:  # e.g., "A,B,C,D,E"
            return aisle_code.split(',')
        else:  # Single aisle
            return [aisle_code]
    
    @staticmethod
    def _get_equipment_for_level(level_code: str, equipment_map: Dict) -> str:
        """Get required equipment for a level"""
        # Check direct mapping
        if level_code in equipment_map:
            return equipment_map[level_code]
        
        # Check range mapping (e.g., "B-F": "forklift")
        for key, equipment in equipment_map.items():
            if '-' in key:
                start, end = key.split('-')
                if start <= level_code <= end:
                    return equipment
        
        # Default equipment
        return 'manual' if level_code == '0' else 'forklift'
    
    @staticmethod
    def save_as_template(warehouse_id: int, template_name: str, description: str, category: str = 'custom', user_id: str = None) -> int:
        """Save an existing warehouse as a new template"""
        # Get warehouse configuration
        warehouse_data = WarehouseTemplateManager._export_warehouse_config(warehouse_id)
        
        # Create template
        template = {
            'template_name': template_name,
            'description': description,
            'template_data': warehouse_data,
            'category': category,
            'is_public': False,  # Custom templates are private by default
            'created_by': user_id
        }
        
        response = supabase.table('warehouse_templates').insert(template).execute()
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error.message)
        
        return response.data[0]['id']
    
    @staticmethod
    def _export_warehouse_config(warehouse_id: int) -> Dict:
        """Export warehouse configuration to template format"""
        # Get warehouse
        warehouse = supabase.table('warehouse_config').select('*').eq('id', warehouse_id).single().execute().data
        
        # Get sections
        sections = supabase.table('warehouse_sections').select('*').eq('warehouse_id', warehouse_id).order('sort_order').execute().data
        
        template_data = {
            'warehouse_name': warehouse['warehouse_name'],
            'location_naming_pattern': warehouse['location_naming_pattern'],
            'sections': []
        }
        
        for section in sections:
            section_data = {
                'code': section['section_code'],
                'name': section['section_name'],
                'description': section['description'],
                'color': section['color_code'],
                'aisles': []
            }
            
            # Get aisles for this section
            aisles = supabase.table('warehouse_aisles').select('*').eq('section_id', section['id']).order('sort_order').execute().data
            
            # Group aisles by complexity and create ranges
            section_data['aisles'] = WarehouseTemplateManager._group_aisles_for_export(aisles)
            
            template_data['sections'].append(section_data)
        
        return template_data
    
    @staticmethod
    def _group_aisles_for_export(aisles: List[Dict]) -> List[Dict]:
        """Group aisles into ranges for export"""
        # Simple implementation - could be enhanced to detect patterns
        aisle_groups = []
        
        simple_aisles = [a for a in aisles if not a['is_complex']]
        complex_aisles = [a for a in aisles if a['is_complex']]
        
        if simple_aisles:
            codes = [a['aisle_code'] for a in simple_aisles]
            aisle_groups.append({
                'code': WarehouseTemplateManager._create_aisle_range(codes),
                'complex': False
            })
        
        if complex_aisles:
            codes = [a['aisle_code'] for a in complex_aisles]
            # Get subsections from first complex aisle
            first_complex = complex_aisles[0]
            levels = supabase.table('warehouse_levels').select('*').eq('aisle_id', first_complex['id']).execute().data
            level_0 = next((l for l in levels if l['level_code'] == '0'), None)
            subsections = []
            if level_0:
                subsections_data = supabase.table('warehouse_subsections').select('*').eq('level_id', level_0['id']).execute().data
                subsections = [s['subsection_code'] for s in subsections_data]
            
            aisle_groups.append({
                'code': WarehouseTemplateManager._create_aisle_range(codes),
                'complex': True,
                'subsections': subsections
            })
        
        return aisle_groups
    
    @staticmethod
    def _create_aisle_range(codes: List[str]) -> str:
        """Create aisle range string from list of codes"""
        if len(codes) == 1:
            return codes[0]
        elif len(codes) > 1:
            # Check if it's a continuous range
            sorted_codes = sorted(codes)
            if len(sorted_codes) > 2 and ord(sorted_codes[-1]) - ord(sorted_codes[0]) == len(sorted_codes) - 1:
                return f"{sorted_codes[0]}-{sorted_codes[-1]}"
            else:
                return ",".join(sorted_codes)
        return "A"

# Predefined template data for quick setup
QUICK_TEMPLATES = {
    'simple': {
        'name': 'Simple Warehouse',
        'description': 'Basic single-section warehouse perfect for getting started',
        'data': {
            'warehouse_name': 'Simple Warehouse',
            'sections': [
                {
                    'code': 'A',
                    'name': 'Main Storage',
                    'description': 'Primary storage area',
                    'color': '#4ECDC4',
                    'aisles': [{'code': 'A-Z', 'complex': False}]
                }
            ],
            'levels': ['1', '2', '3', '4'],
            'equipment': {'1': 'manual', '2-4': 'forklift'}
        }
    },
    'ecommerce': {
        'name': 'E-commerce Fulfillment',
        'description': 'Optimized for e-commerce order fulfillment with fast-pick zones',
        'data': {
            'warehouse_name': 'E-commerce Fulfillment Center',
            'sections': [
                {'code': 'F', 'name': 'Fast Pick', 'aisles': [{'code': 'A-J', 'complex': False}]},
                {'code': 'S', 'name': 'Standard Pick', 'aisles': [{'code': 'A-Z', 'complex': False}]},
                {'code': 'B', 'name': 'Bulk Storage', 'aisles': [{'code': 'A-L', 'complex': False}]}
            ],
            'levels': ['0', 'B', 'C', 'D'],
            'equipment': {'0': 'manual', 'B-D': 'forklift'}
        }
    }
}