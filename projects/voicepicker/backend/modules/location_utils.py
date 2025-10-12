"""
Location utilities for warehouse management system
Handles location code validation, generation, and voice optimization
"""

import re
from typing import Dict, List, Optional, Tuple
import random

# Warehouse configuration
WAREHOUSE_SECTIONS = {
    'H': {'aisles': ['A'], 'description': 'Heavy items'},
    'L': {'aisles': [chr(i) for i in range(ord('A'), ord('Z')+1)], 'description': 'Light items'},
    'M': {'aisles': [chr(i) for i in range(ord('A'), ord('F')+1)], 'description': 'Medium items'},
    'B': {'aisles': ['A', 'B', 'C', 'D', 'E'], 'description': 'B section'},
    'A': {'aisles': [chr(i) for i in range(ord('A'), ord('Z')+1)], 'description': 'A section'}
}

# Complex aisles that have subdivisions at level 0
COMPLEX_AISLES = {
    'A': [chr(i) for i in range(ord('M'), ord('Z')+1)] + ['A'] + [chr(i) for i in range(ord('A'), ord('F')+1)]
}

# Level mappings
LEVEL_MAPPINGS = {
    '0': 'Level 0 (Picker)',
    'B': 'Level 1',
    'C': 'Level 2', 
    'D': 'Level 3',
    'E': 'Level 4',
    'F': 'Level 5'
}

# Subsections for level 0 in complex aisles
LEVEL_0_SUBSECTIONS = ['1', '3', '7']

def is_complex_aisle(section: str, aisle: str) -> bool:
    """Check if an aisle has complex subdivisions"""
    if section == 'A' and aisle in COMPLEX_AISLES['A']:
        return True
    return False

def validate_location_code(location_code: str) -> Dict:
    """
    Validate and parse a location code
    Returns parsed components or raises exception
    """
    # Pattern 1: Simple format (LA-045, LA-045.B)
    simple_pattern = r'^([HLMBA])([A-Z]+)-(\d{3})(?:\.([BCDEF]))?$'
    
    # Pattern 2: Complex format with subsection (AE-055.0.1, AE-055.0.3, AE-055.0.7)
    complex_pattern = r'^([HLMBA])([A-Z]+)-(\d{3})\.0\.([137])$'
    
    simple_match = re.match(simple_pattern, location_code)
    complex_match = re.match(complex_pattern, location_code)
    
    if simple_match:
        section, aisle, bay, level = simple_match.groups()
        return {
            'section': section,
            'aisle': aisle,
            'bay': bay,
            'level': level or '0',
            'subsection': None,
            'is_complex': False,
            'format_type': 'simple'
        }
    
    elif complex_match:
        section, aisle, bay, subsection = complex_match.groups()
        return {
            'section': section,
            'aisle': aisle,
            'bay': bay,
            'level': '0',
            'subsection': subsection,
            'is_complex': True,
            'format_type': 'complex'
        }
    
    else:
        raise ValueError(f"Invalid location code format: {location_code}")

def generate_location_code(section: str, aisle: str, bay: str, level: str = '0', subsection: str = None) -> str:
    """Generate a location code from components"""
    base_code = f"{section}{aisle}-{bay.zfill(3)}"
    
    # Check if this should be a complex aisle
    if is_complex_aisle(section, aisle) and level == '0' and subsection:
        return f"{base_code}.0.{subsection}"
    
    # Simple format
    if level == '0':
        return base_code
    else:
        return f"{base_code}.{level}"

def generate_check_digit() -> int:
    """Generate a random check digit between 1-37"""
    return random.randint(1, 37)

def get_voice_friendly_location(location_code: str) -> str:
    """
    Convert location code to voice-friendly format
    LA-045 -> "L A dash zero four five"
    AE-055.0.1 -> "A E dash zero five five dot zero dot one"
    LA-045.B -> "L A dash zero four five dot B"
    """
    parsed = validate_location_code(location_code)
    
    # Convert to voice-friendly format
    section_voice = f"{parsed['section']}"
    aisle_voice = " ".join(list(parsed['aisle']))
    bay_voice = " ".join(list(parsed['bay']))
    
    voice_parts = [section_voice, aisle_voice, "dash", bay_voice]
    
    if parsed['format_type'] == 'complex':
        voice_parts.extend(["dot", "zero", "dot", parsed['subsection']])
    elif parsed['level'] != '0':
        voice_parts.extend(["dot", parsed['level']])
    
    return " ".join(voice_parts)

def get_equipment_required(location_code: str) -> str:
    """Determine equipment required for location"""
    parsed = validate_location_code(location_code)
    
    if parsed['level'] == '0':
        return 'manual'
    else:
        return 'forklift'

def get_all_locations_for_aisle(section: str, aisle: str) -> List[str]:
    """Generate all possible location codes for an aisle"""
    locations = []
    
    # Generate all bay positions (001-099)
    for bay_num in range(1, 100):
        bay = f"{bay_num:03d}"
        
        if is_complex_aisle(section, aisle):
            # Complex aisle: Level 0 with subsections + levels B-F
            for subsection in LEVEL_0_SUBSECTIONS:
                locations.append(generate_location_code(section, aisle, bay, '0', subsection))
            
            # Upper levels (B-F)
            for level in ['B', 'C', 'D', 'E', 'F']:
                locations.append(generate_location_code(section, aisle, bay, level))
        else:
            # Simple aisle: Level 0 (implied) + levels B-F
            locations.append(generate_location_code(section, aisle, bay, '0'))
            
            for level in ['B', 'C', 'D', 'E', 'F']:
                locations.append(generate_location_code(section, aisle, bay, level))
    
    return locations

def get_picker_locations_for_aisle(section: str, aisle: str) -> List[str]:
    """Get only picker-accessible locations (level 0) for an aisle"""
    locations = []
    
    for bay_num in range(1, 100):
        bay = f"{bay_num:03d}"
        
        if is_complex_aisle(section, aisle):
            # Complex aisle: Level 0 with subsections
            for subsection in LEVEL_0_SUBSECTIONS:
                locations.append(generate_location_code(section, aisle, bay, '0', subsection))
        else:
            # Simple aisle: Level 0 only
            locations.append(generate_location_code(section, aisle, bay, '0'))
    
    return locations

def validate_warehouse_structure() -> Dict:
    """Validate the entire warehouse structure and return statistics"""
    stats = {
        'total_sections': len(WAREHOUSE_SECTIONS),
        'total_aisles': 0,
        'complex_aisles': 0,
        'estimated_locations': 0
    }
    
    for section, config in WAREHOUSE_SECTIONS.items():
        aisles_count = len(config['aisles'])
        stats['total_aisles'] += aisles_count
        
        for aisle in config['aisles']:
            if is_complex_aisle(section, aisle):
                stats['complex_aisles'] += 1
                # Complex: (99 bays * 3 subsections) + (99 bays * 5 levels) = 792 locations per aisle
                stats['estimated_locations'] += 99 * (3 + 5)
            else:
                # Simple: 99 bays * 6 levels (0, B, C, D, E, F) = 594 locations per aisle
                stats['estimated_locations'] += 99 * 6
    
    return stats

def search_locations(search_term: str, location_codes: List[str]) -> List[str]:
    """Search location codes by term"""
    search_term = search_term.upper()
    results = []
    
    for location in location_codes:
        if search_term in location:
            results.append(location)
    
    return results