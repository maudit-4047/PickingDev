"""
Warehouse Location Seeding Script
Generates all location codes based on your warehouse structure
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

from typing import List
from database.db_cofig import supabase
from modules.location_utils import (
    generate_location_code, 
    generate_check_digit, 
    is_complex_aisle,
    get_voice_friendly_location,
    get_equipment_required
)
import random

# Your warehouse configuration
WAREHOUSE_SECTIONS = {
    'H': {
        'aisles': ['A'],
        'zone_name': 'Heavy Items Section',
        'description': 'HA aisle - Heavy items storage'
    },
    'L': {
        'aisles': [chr(i) for i in range(ord('A'), ord('Z')+1)],  # LA-LZ
        'zone_name': 'Light Items Section', 
        'description': 'LA-LZ aisles - Light items storage (26 aisles)'
    },
    'M': {
        'aisles': [chr(i) for i in range(ord('A'), ord('F')+1)],  # MA-MF
        'zone_name': 'Medium Items Section',
        'description': 'MA-MF aisles - Medium items storage (6 aisles)'
    },
    'B': {
        'aisles': ['A', 'B', 'C', 'D', 'E'],  # BA-BE
        'zone_name': 'B Section',
        'description': 'BA-BE aisles - B section storage (5 aisles)'
    },
    'A': {
        'aisles': [chr(i) for i in range(ord('A'), ord('Z')+1)],  # AA-AZ
        'zone_name': 'A Section',
        'description': 'AA-AZ aisles - A section storage (26 aisles)'
    }
}

# Complex aisles (AM-AE in section A) that have subdivisions at level 0
COMPLEX_AISLES_A = [chr(i) for i in range(ord('M'), ord('Z')+1)] + ['A', 'B', 'C', 'D', 'E']  # AM-AZ + AA-AE

# Level 0 subsections for complex aisles
LEVEL_0_SUBSECTIONS = ['1', '3', '7']

# Levels for all aisles
LEVELS = ['0', 'B', 'C', 'D', 'E', 'F']  # Level 0 = picker, B-F = forklift

def create_zones():
    """Create warehouse zones in database"""
    print("Creating warehouse zones...")
    
    for section_code, config in WAREHOUSE_SECTIONS.items():
        zone_data = {
            'zone_code': section_code,
            'zone_name': config['zone_name'],
            'description': config['description'],
            'is_active': True
        }
        
        try:
            response = supabase.table('location_zones').upsert(zone_data, on_conflict=['zone_code']).execute()
            print(f"✓ Created/updated zone {section_code}: {config['zone_name']}")
        except Exception as e:
            print(f"✗ Error creating zone {section_code}: {str(e)}")

def get_zone_id(section_code: str) -> int:
    """Get zone ID for a section"""
    response = supabase.table('location_zones').select('id').eq('zone_code', section_code).single().execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Zone not found for section {section_code}")
    return response.data['id']

def generate_check_digits(total_locations: int) -> List[int]:
    """Generate unique check digits for all locations"""
    # Since we have more locations than 37 check digits, we'll cycle through them
    check_digits = []
    for i in range(total_locations):
        check_digits.append((i % 37) + 1)  # 1-37
    
    # Shuffle to randomize assignment
    random.shuffle(check_digits)
    return check_digits

def create_locations_for_section(section_code: str, aisles: List[str], zone_id: int, check_digits: List[int]) -> int:
    """Create all locations for a warehouse section"""
    print(f"\nCreating locations for section {section_code}...")
    
    locations_created = 0
    check_digit_index = 0
    
    for aisle in aisles:
        print(f"  Processing aisle {section_code}{aisle}...")
        
        # Generate locations for all bay positions (001-099)
        for bay_num in range(1, 100):
            bay = f"{bay_num:03d}"
            
            if section_code == 'A' and aisle in COMPLEX_AISLES_A:
                # Complex aisle: Level 0 with subsections
                for subsection in LEVEL_0_SUBSECTIONS:
                    location_code = generate_location_code(section_code, aisle, bay, '0', subsection)
                    
                    location_data = {
                        'location_code': location_code,
                        'zone_id': zone_id,
                        'section': section_code,
                        'aisle': aisle,
                        'bay': bay,
                        'level': '0',
                        'subsection': subsection,
                        'check_digit': check_digits[check_digit_index % len(check_digits)],
                        'location_type': 'pick',
                        'is_complex_aisle': True,
                        'capacity': 100,
                        'current_occupancy': 0,
                        'is_active': True,
                        'is_pickable': True,
                        'access_equipment': 'manual'
                    }
                    
                    try:
                        supabase.table('pick_locations').upsert(location_data, on_conflict=['location_code']).execute()
                        locations_created += 1
                        check_digit_index += 1
                    except Exception as e:
                        print(f"    ✗ Error creating {location_code}: {str(e)}")
                
                # Upper levels (B-F) for complex aisles - no subsections
                for level in ['B', 'C', 'D', 'E', 'F']:
                    location_code = generate_location_code(section_code, aisle, bay, level)
                    
                    location_data = {
                        'location_code': location_code,
                        'zone_id': zone_id,
                        'section': section_code,
                        'aisle': aisle,
                        'bay': bay,
                        'level': level,
                        'subsection': None,
                        'check_digit': check_digits[check_digit_index % len(check_digits)],
                        'location_type': 'pick',
                        'is_complex_aisle': True,
                        'capacity': 100,
                        'current_occupancy': 0,
                        'is_active': True,
                        'is_pickable': True,
                        'access_equipment': 'forklift'
                    }
                    
                    try:
                        supabase.table('pick_locations').upsert(location_data, on_conflict=['location_code']).execute()
                        locations_created += 1
                        check_digit_index += 1
                    except Exception as e:
                        print(f"    ✗ Error creating {location_code}: {str(e)}")
            
            else:
                # Simple aisle: All levels (0, B, C, D, E, F)
                for level in LEVELS:
                    location_code = generate_location_code(section_code, aisle, bay, level)
                    
                    location_data = {
                        'location_code': location_code,
                        'zone_id': zone_id,
                        'section': section_code,
                        'aisle': aisle,
                        'bay': bay,
                        'level': level if level != '0' else None,  # Store NULL for level 0
                        'subsection': None,
                        'check_digit': check_digits[check_digit_index % len(check_digits)],
                        'location_type': 'pick',
                        'is_complex_aisle': False,
                        'capacity': 100,
                        'current_occupancy': 0,
                        'is_active': True,
                        'is_pickable': True,
                        'access_equipment': 'manual' if level == '0' else 'forklift'
                    }
                    
                    try:
                        supabase.table('pick_locations').upsert(location_data, on_conflict=['location_code']).execute()
                        locations_created += 1
                        check_digit_index += 1
                    except Exception as e:
                        print(f"    ✗ Error creating {location_code}: {str(e)}")
        
        print(f"  ✓ Completed aisle {section_code}{aisle}")
    
    print(f"✓ Created {locations_created} locations for section {section_code}")
    return locations_created

def estimate_total_locations() -> int:
    """Estimate total number of locations to be created"""
    total = 0
    
    for section_code, config in WAREHOUSE_SECTIONS.items():
        for aisle in config['aisles']:
            if section_code == 'A' and aisle in COMPLEX_AISLES_A:
                # Complex: (99 bays * 3 subsections) + (99 bays * 5 levels) = 792 per aisle
                total += 99 * (3 + 5)
            else:
                # Simple: 99 bays * 6 levels = 594 per aisle
                total += 99 * 6
    
    return total

def seed_warehouse():
    """Main function to seed the entire warehouse"""
    print("🏭 Starting warehouse location seeding...")
    print(f"Estimated locations to create: {estimate_total_locations():,}")
    
    # Step 1: Create zones
    create_zones()
    
    # Step 2: Generate check digits
    total_locations = estimate_total_locations()
    check_digits = generate_check_digits(total_locations)
    print(f"Generated {len(check_digits)} check digits")
    
    # Step 3: Create locations for each section
    total_created = 0
    
    for section_code, config in WAREHOUSE_SECTIONS.items():
        try:
            zone_id = get_zone_id(section_code)
            created = create_locations_for_section(section_code, config['aisles'], zone_id, check_digits)
            total_created += created
        except Exception as e:
            print(f"✗ Error processing section {section_code}: {str(e)}")
    
    print(f"\n🎉 Warehouse seeding completed!")
    print(f"Total locations created: {total_created:,}")
    
    # Display summary
    print("\n📊 Warehouse Summary:")
    for section_code, config in WAREHOUSE_SECTIONS.items():
        aisles_count = len(config['aisles'])
        print(f"  {section_code} Section: {aisles_count} aisles ({config['zone_name']})")

def clear_all_locations():
    """Clear all existing locations (use with caution!)"""
    confirm = input("⚠️  This will delete ALL locations. Type 'CONFIRM' to proceed: ")
    if confirm == 'CONFIRM':
        try:
            supabase.table('pick_locations').delete().neq('id', 0).execute()
            print("✓ All locations cleared")
        except Exception as e:
            print(f"✗ Error clearing locations: {str(e)}")
    else:
        print("Operation cancelled")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Warehouse Location Seeding Script')
    parser.add_argument('--seed', action='store_true', help='Seed the warehouse with locations')
    parser.add_argument('--clear', action='store_true', help='Clear all existing locations')
    parser.add_argument('--estimate', action='store_true', help='Show estimated location count')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_all_locations()
    elif args.estimate:
        total = estimate_total_locations()
        print(f"Estimated total locations: {total:,}")
    elif args.seed:
        seed_warehouse()
    else:
        print("Use --seed to create locations, --clear to remove all, or --estimate to see counts")
        print("Example: python seed_warehouse.py --seed")