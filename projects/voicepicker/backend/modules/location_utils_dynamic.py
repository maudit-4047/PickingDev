"""
Configuration-driven location utilities for warehouse management system
Reads warehouse structure from database instead of hardcoded values
"""

import re
from typing import Dict, List, Optional, Tuple
from database.db_cofig import supabase
import random

class WarehouseConfig:
    """Warehouse configuration manager"""
    
    def __init__(self, warehouse_id: int):
        self.warehouse_id = warehouse_id
        self._config = None
        self._sections = None
        self._aisles = None
        self._levels = None
        self._subsections = None
    
    @property
    def config(self) -> Dict:
        if self._config is None:
            response = supabase.table('warehouse_config').select('*').eq('id', self.warehouse_id).single().execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Warehouse config not found: {response.error.message}")
            self._config = response.data
        return self._config
    
    @property
    def sections(self) -> List[Dict]:
        if self._sections is None:
            response = supabase.table('warehouse_sections').select('*').eq('warehouse_id', self.warehouse_id).eq('is_active', True).order('sort_order').execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Error loading sections: {response.error.message}")
            self._sections = response.data
        return self._sections
    
    def get_section(self, section_code: str) -> Optional[Dict]:
        """Get section by code"""
        return next((s for s in self.sections if s['section_code'] == section_code), None)
    
    def get_aisles(self, section_id: int) -> List[Dict]:
        """Get aisles for a section"""
        if self._aisles is None:
            self._aisles = {}
        
        if section_id not in self._aisles:
            response = supabase.table('warehouse_aisles').select('*').eq('section_id', section_id).eq('is_active', True).order('sort_order').execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Error loading aisles: {response.error.message}")
            self._aisles[section_id] = response.data
        
        return self._aisles[section_id]
    
    def get_aisle(self, section_code: str, aisle_code: str) -> Optional[Dict]:
        """Get specific aisle"""
        section = self.get_section(section_code)
        if not section:
            return None
        
        aisles = self.get_aisles(section['id'])
        return next((a for a in aisles if a['aisle_code'] == aisle_code), None)
    
    def get_levels(self, aisle_id: int) -> List[Dict]:
        """Get levels for an aisle"""
        if self._levels is None:
            self._levels = {}
        
        if aisle_id not in self._levels:
            response = supabase.table('warehouse_levels').select('*').eq('aisle_id', aisle_id).eq('is_active', True).order('sort_order').execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Error loading levels: {response.error.message}")
            self._levels[aisle_id] = response.data
        
        return self._levels[aisle_id]
    
    def get_subsections(self, level_id: int) -> List[Dict]:
        """Get subsections for a level"""
        if self._subsections is None:
            self._subsections = {}
        
        if level_id not in self._subsections:
            response = supabase.table('warehouse_subsections').select('*').eq('level_id', level_id).eq('is_active', True).order('sort_order').execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Error loading subsections: {response.error.message}")
            self._subsections[level_id] = response.data
        
        return self._subsections[level_id]
    
    def is_complex_aisle(self, section_code: str, aisle_code: str) -> bool:
        """Check if an aisle has complex subdivisions"""
        aisle = self.get_aisle(section_code, aisle_code)
        return aisle['is_complex'] if aisle else False
    
    def get_location_pattern(self) -> str:
        """Get location naming pattern"""
        return self.config.get('location_naming_pattern', '{section}{aisle}-{bay:03d}')
    
    def get_check_digit_range(self) -> Tuple[int, int]:
        """Get check digit range"""
        return (self.config.get('check_digit_min', 1), self.config.get('check_digit_max', 37))

# Global warehouse configurations cache
_warehouse_configs = {}

def get_warehouse_config(warehouse_id: int) -> WarehouseConfig:
    """Get warehouse configuration (cached)"""
    if warehouse_id not in _warehouse_configs:
        _warehouse_configs[warehouse_id] = WarehouseConfig(warehouse_id)
    return _warehouse_configs[warehouse_id]

def get_default_warehouse_id() -> int:
    """Get the default warehouse ID (first active warehouse)"""
    response = supabase.table('warehouse_config').select('id').eq('is_active', True).limit(1).execute()
    if hasattr(response, 'error') and response.error or not response.data:
        raise Exception("No active warehouse found. Please create a warehouse first.")
    return response.data[0]['id']

def validate_location_code(location_code: str, warehouse_id: int = None) -> Dict:
    """
    Validate and parse a location code based on warehouse configuration
    """
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    
    # Try different patterns based on warehouse configuration
    patterns = [
        # Simple format (LA-045, LA-045.B)
        r'^([A-Z]+)([A-Z]+)-(\d{3})(?:\.([A-Z0-9]+))?$',
        # Complex format with subsection (AE-055.0.1)
        r'^([A-Z]+)([A-Z]+)-(\d{3})\.([A-Z0-9]+)\.([A-Z0-9]+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, location_code)
        if match:
            groups = match.groups()
            
            if len(groups) == 4:  # Simple format
                section, aisle, bay, level = groups
                return {
                    'section': section,
                    'aisle': aisle,
                    'bay': bay,
                    'level': level or '0',
                    'subsection': None,
                    'is_complex': config.is_complex_aisle(section, aisle),
                    'format_type': 'simple',
                    'warehouse_id': warehouse_id
                }
            elif len(groups) == 5:  # Complex format
                section, aisle, bay, level, subsection = groups
                return {
                    'section': section,
                    'aisle': aisle,
                    'bay': bay,
                    'level': level,
                    'subsection': subsection,
                    'is_complex': True,
                    'format_type': 'complex',
                    'warehouse_id': warehouse_id
                }
    
    raise ValueError(f"Invalid location code format: {location_code}")

def generate_location_code(section: str, aisle: str, bay: str, level: str = '0', subsection: str = None, warehouse_id: int = None) -> str:
    """Generate a location code from components based on warehouse configuration"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    pattern = config.get_location_pattern()
    
    # Format bay number
    bay_formatted = f"{int(bay):03d}" if bay.isdigit() else bay
    
    # Check if this should be a complex format
    if config.is_complex_aisle(section, aisle) and level == '0' and subsection:
        return f"{section}{aisle}-{bay_formatted}.{level}.{subsection}"
    
    # Simple format
    if level == '0' or level is None:
        return f"{section}{aisle}-{bay_formatted}"
    else:
        return f"{section}{aisle}-{bay_formatted}.{level}"

def generate_check_digit(warehouse_id: int = None) -> int:
    """Generate a check digit based on warehouse configuration"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    min_digit, max_digit = config.get_check_digit_range()
    return random.randint(min_digit, max_digit)

def get_voice_friendly_location(location_code: str, warehouse_id: int = None) -> str:
    """
    Convert location code to voice-friendly format based on warehouse configuration
    """
    parsed = validate_location_code(location_code, warehouse_id)
    
    # Convert to voice-friendly format
    section_voice = f"{parsed['section']}"
    aisle_voice = " ".join(list(parsed['aisle']))
    bay_voice = " ".join(list(parsed['bay']))
    
    voice_parts = [section_voice, aisle_voice, "dash", bay_voice]
    
    if parsed['format_type'] == 'complex':
        voice_parts.extend(["dot", parsed['level'], "dot", parsed['subsection']])
    elif parsed['level'] != '0':
        voice_parts.extend(["dot", parsed['level']])
    
    return " ".join(voice_parts)

def get_equipment_required(location_code: str, warehouse_id: int = None) -> str:
    """Determine equipment required for location based on warehouse configuration"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    parsed = validate_location_code(location_code, warehouse_id)
    config = get_warehouse_config(warehouse_id)
    
    # Get aisle configuration
    aisle = config.get_aisle(parsed['section'], parsed['aisle'])
    if not aisle:
        return 'manual'  # Default
    
    # Get level configuration
    levels = config.get_levels(aisle['id'])
    level_config = next((l for l in levels if l['level_code'] == parsed['level']), None)
    
    if level_config:
        return level_config['equipment_required']
    
    # Fallback to default logic
    return 'manual' if parsed['level'] == '0' else 'forklift'

def get_all_locations_for_aisle(section: str, aisle: str, warehouse_id: int = None) -> List[str]:
    """Generate all possible location codes for an aisle based on warehouse configuration"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    locations = []
    
    # Get aisle configuration
    aisle_config = config.get_aisle(section, aisle)
    if not aisle_config:
        return []
    
    # Get bay range
    bay_start = aisle_config.get('bay_range_start', 1)
    bay_end = aisle_config.get('bay_range_end', 99)
    
    # Get levels
    levels = config.get_levels(aisle_config['id'])
    
    for bay_num in range(bay_start, bay_end + 1):
        bay = f"{bay_num:03d}"
        
        for level_config in levels:
            level_code = level_config['level_code']
            
            if aisle_config['is_complex'] and level_code == '0':
                # Complex aisle: Level 0 with subsections
                subsections = config.get_subsections(level_config['id'])
                for subsection_config in subsections:
                    subsection_code = subsection_config['subsection_code']
                    locations.append(generate_location_code(section, aisle, bay, level_code, subsection_code, warehouse_id))
            else:
                # Simple format or upper levels
                locations.append(generate_location_code(section, aisle, bay, level_code, None, warehouse_id))
    
    return locations

def get_picker_locations_for_aisle(section: str, aisle: str, warehouse_id: int = None) -> List[str]:
    """Get only picker-accessible locations (level 0) for an aisle"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    locations = []
    
    # Get aisle configuration
    aisle_config = config.get_aisle(section, aisle)
    if not aisle_config:
        return []
    
    # Get bay range
    bay_start = aisle_config.get('bay_range_start', 1)
    bay_end = aisle_config.get('bay_range_end', 99)
    
    # Get level 0 configuration
    levels = config.get_levels(aisle_config['id'])
    level_0 = next((l for l in levels if l['level_code'] == '0'), None)
    
    if not level_0:
        return []
    
    for bay_num in range(bay_start, bay_end + 1):
        bay = f"{bay_num:03d}"
        
        if aisle_config['is_complex']:
            # Complex aisle: Level 0 with subsections
            subsections = config.get_subsections(level_0['id'])
            for subsection_config in subsections:
                subsection_code = subsection_config['subsection_code']
                locations.append(generate_location_code(section, aisle, bay, '0', subsection_code, warehouse_id))
        else:
            # Simple aisle: Level 0 only
            locations.append(generate_location_code(section, aisle, bay, '0', None, warehouse_id))
    
    return locations

def validate_warehouse_structure(warehouse_id: int = None) -> Dict:
    """Validate warehouse structure and return statistics"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    
    stats = {
        'warehouse_id': warehouse_id,
        'warehouse_name': config.config['warehouse_name'],
        'total_sections': len(config.sections),
        'total_aisles': 0,
        'complex_aisles': 0,
        'estimated_locations': 0,
        'sections': []
    }
    
    for section in config.sections:
        aisles = config.get_aisles(section['id'])
        section_stats = {
            'section_code': section['section_code'],
            'section_name': section['section_name'],
            'aisle_count': len(aisles),
            'complex_aisles': 0,
            'estimated_locations': 0
        }
        
        for aisle in aisles:
            stats['total_aisles'] += 1
            section_stats['aisle_count'] += 1
            
            if aisle['is_complex']:
                stats['complex_aisles'] += 1
                section_stats['complex_aisles'] += 1
            
            # Estimate locations for this aisle
            bay_count = aisle['bay_range_end'] - aisle['bay_range_start'] + 1
            levels = config.get_levels(aisle['id'])
            
            if aisle['is_complex']:
                # Complex: level 0 with subsections + upper levels
                level_0 = next((l for l in levels if l['level_code'] == '0'), None)
                if level_0:
                    subsections = config.get_subsections(level_0['id'])
                    aisle_locations = bay_count * (len(subsections) + len(levels) - 1)
                else:
                    aisle_locations = bay_count * len(levels)
            else:
                # Simple: all levels
                aisle_locations = bay_count * len(levels)
            
            section_stats['estimated_locations'] += aisle_locations
            stats['estimated_locations'] += aisle_locations
        
        stats['sections'].append(section_stats)
    
    return stats

def search_locations(search_term: str, location_codes: List[str]) -> List[str]:
    """Search location codes by term"""
    search_term = search_term.upper()
    results = []
    
    for location in location_codes:
        if search_term in location:
            results.append(location)
    
    return results

def get_warehouse_summary(warehouse_id: int = None) -> Dict:
    """Get a summary of warehouse configuration"""
    if warehouse_id is None:
        warehouse_id = get_default_warehouse_id()
    
    config = get_warehouse_config(warehouse_id)
    
    summary = {
        'warehouse': config.config,
        'sections': config.sections,
        'location_pattern': config.get_location_pattern(),
        'check_digit_range': config.get_check_digit_range(),
        'statistics': validate_warehouse_structure(warehouse_id)
    }
    
    return summary