from typing import Optional, List, Dict
from database.db_cofig import supabase
from datetime import datetime

# Warehouse Designer Module - Allows users to design their own warehouse layouts

def create_custom_zone(zone_code: str, zone_name: str, description: str = None) -> Dict:
    """Create a custom warehouse zone"""
    zone_data = {
        'zone_code': zone_code.upper(),
        'zone_name': zone_name,
        'description': description,
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    response = supabase.table('location_zones').insert(zone_data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]

def create_custom_location(location_code: str, zone_code: str, aisle: str = None, bay: str = None, 
                          level: str = None, position: str = None, location_type: str = 'pick',
                          capacity: int = 100, access_equipment: str = 'manual', 
                          safety_notes: str = None) -> Dict:
    """Create a custom pick location"""
    # Get zone ID
    zone_response = supabase.table('location_zones').select('id').eq('zone_code', zone_code.upper()).single().execute()
    if hasattr(zone_response, 'error') and zone_response.error:
        raise Exception(f'Zone {zone_code} not found')
    
    location_data = {
        'location_code': location_code.upper(),
        'zone_id': zone_response.data['id'],
        'aisle': aisle.upper() if aisle else None,
        'bay': bay,
        'level': level,
        'position': position.upper() if position else None,
        'location_type': location_type,
        'capacity': capacity,
        'current_occupancy': 0,
        'is_active': True,
        'is_pickable': True,
        'access_equipment': access_equipment,
        'safety_notes': safety_notes,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    response = supabase.table('pick_locations').insert(location_data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]

def bulk_create_locations(warehouse_design: Dict) -> Dict:
    """
    Create multiple locations from a warehouse design configuration
    
    warehouse_design format:
    {
        "warehouse_name": "My Warehouse",
        "zones": [
            {"zone_code": "PICK", "zone_name": "Pick Area", "description": "Main picking"}
        ],
        "aisles": [
            {
                "aisle": "A",
                "zone_code": "PICK",
                "bays": ["01", "02", "03"],
                "levels": ["1", "2", "3"],
                "positions": ["A", "B"],
                "location_type": "pick",
                "capacity": 50,
                "access_equipment": "manual"
            }
        ]
    }
    """
    created_zones = []
    created_locations = []
    
    try:
        # Create zones first
        for zone in warehouse_design.get('zones', []):
            try:
                created_zone = create_custom_zone(
                    zone['zone_code'],
                    zone['zone_name'],
                    zone.get('description')
                )
                created_zones.append(created_zone)
            except Exception as e:
                # Zone might already exist, continue
                print(f"Zone {zone['zone_code']} might already exist: {e}")
        
        # Create locations
        for aisle_config in warehouse_design.get('aisles', []):
            aisle = aisle_config['aisle']
            zone_code = aisle_config['zone_code']
            bays = aisle_config.get('bays', ['01'])
            levels = aisle_config.get('levels', ['1'])
            positions = aisle_config.get('positions', ['A'])
            location_type = aisle_config.get('location_type', 'pick')
            capacity = aisle_config.get('capacity', 100)
            access_equipment = aisle_config.get('access_equipment', 'manual')
            
            for bay in bays:
                for level in levels:
                    for position in positions:
                        # Generate location code: {aisle}{bay}{level}{position}
                        location_code = f"{aisle}{bay}{level}{position}"
                        
                        try:
                            created_location = create_custom_location(
                                location_code=location_code,
                                zone_code=zone_code,
                                aisle=aisle,
                                bay=bay,
                                level=level,
                                position=position,
                                location_type=location_type,
                                capacity=capacity,
                                access_equipment=access_equipment
                            )
                            created_locations.append(created_location)
                        except Exception as e:
                            print(f"Failed to create location {location_code}: {e}")
        
        return {
            'warehouse_name': warehouse_design.get('warehouse_name', 'Custom Warehouse'),
            'zones_created': len(created_zones),
            'locations_created': len(created_locations),
            'created_zones': created_zones,
            'created_locations': created_locations
        }
    
    except Exception as e:
        raise Exception(f"Failed to create warehouse design: {e}")

def get_warehouse_layout_summary() -> Dict:
    """Get a summary of the current warehouse layout"""
    # Get zones
    zones = supabase.table('location_zones').select('*').eq('is_active', True).execute()
    
    # Get locations grouped by zone and aisle
    locations = supabase.table('pick_locations').select('*, location_zones(zone_name)').eq('is_active', True).order('aisle', 'bay', 'level', 'position').execute()
    
    if hasattr(zones, 'error') and zones.error:
        raise Exception(zones.error.message)
    if hasattr(locations, 'error') and locations.error:
        raise Exception(locations.error.message)
    
    # Group locations by zone and aisle
    layout = {}
    for location in locations.data:
        zone_name = location['location_zones']['zone_name'] if location.get('location_zones') else 'Unknown'
        aisle = location.get('aisle', 'No Aisle')
        
        if zone_name not in layout:
            layout[zone_name] = {}
        if aisle not in layout[zone_name]:
            layout[zone_name][aisle] = []
        
        layout[zone_name][aisle].append({
            'location_code': location['location_code'],
            'bay': location.get('bay'),
            'level': location.get('level'),
            'position': location.get('position'),
            'capacity': location.get('capacity'),
            'current_occupancy': location.get('current_occupancy', 0),
            'access_equipment': location.get('access_equipment')
        })
    
    return {
        'total_zones': len(zones.data),
        'total_locations': len(locations.data),
        'zones': [{'zone_code': z['zone_code'], 'zone_name': z['zone_name']} for z in zones.data],
        'layout': layout
    }

def create_warehouse_template(template_name: str) -> Dict:
    """Create predefined warehouse templates"""
    templates = {
        'small_warehouse': {
            'warehouse_name': 'Small Warehouse Template',
            'zones': [
                {'zone_code': 'PICK', 'zone_name': 'Pick Area', 'description': 'Main picking area'},
                {'zone_code': 'DOCK', 'zone_name': 'Dock', 'description': 'Loading dock'}
            ],
            'aisles': [
                {
                    'aisle': 'A',
                    'zone_code': 'PICK',
                    'bays': ['01', '02'],
                    'levels': ['1', '2'],
                    'positions': ['A', 'B'],
                    'location_type': 'pick',
                    'capacity': 50,
                    'access_equipment': 'manual'
                },
                {
                    'aisle': 'B',
                    'zone_code': 'PICK',
                    'bays': ['01', '02'],
                    'levels': ['1', '2'],
                    'positions': ['A', 'B'],
                    'location_type': 'pick',
                    'capacity': 50,
                    'access_equipment': 'manual'
                }
            ]
        },
        'medium_warehouse': {
            'warehouse_name': 'Medium Warehouse Template',
            'zones': [
                {'zone_code': 'PICK', 'zone_name': 'Pick Area', 'description': 'Main picking area'},
                {'zone_code': 'RESERVE', 'zone_name': 'Reserve', 'description': 'Reserve storage'},
                {'zone_code': 'DOCK', 'zone_name': 'Dock', 'description': 'Loading dock'}
            ],
            'aisles': [
                {
                    'aisle': aisle,
                    'zone_code': 'PICK',
                    'bays': [f'{i:02d}' for i in range(1, 6)],  # 01-05
                    'levels': ['1', '2', '3'],
                    'positions': ['A', 'B'],
                    'location_type': 'pick',
                    'capacity': 75,
                    'access_equipment': 'manual'
                } for aisle in ['A', 'B', 'C', 'D']
            ]
        },
        'large_warehouse': {
            'warehouse_name': 'Large Warehouse Template',
            'zones': [
                {'zone_code': 'PICK', 'zone_name': 'Pick Area', 'description': 'Main picking area'},
                {'zone_code': 'RESERVE', 'zone_name': 'Reserve', 'description': 'Reserve storage'},
                {'zone_code': 'DOCK', 'zone_name': 'Dock', 'description': 'Loading dock'},
                {'zone_code': 'STAGE', 'zone_name': 'Staging', 'description': 'Order staging'}
            ],
            'aisles': [
                {
                    'aisle': aisle,
                    'zone_code': 'PICK',
                    'bays': [f'{i:02d}' for i in range(1, 11)],  # 01-10
                    'levels': ['1', '2', '3', '4'],
                    'positions': ['A', 'B'],
                    'location_type': 'pick',
                    'capacity': 100,
                    'access_equipment': 'reach_truck' if aisle in ['A', 'B'] else 'manual'
                } for aisle in ['A', 'B', 'C', 'D', 'E', 'F']
            ]
        }
    }
    
    if template_name not in templates:
        raise Exception(f"Template '{template_name}' not found. Available: {list(templates.keys())}")
    
    return bulk_create_locations(templates[template_name])

def delete_warehouse_layout() -> Dict:
    """Delete all locations and zones (careful!)"""
    # Delete in reverse order due to foreign keys
    locations_deleted = supabase.table('pick_locations').delete().neq('id', 0).execute()
    zones_deleted = supabase.table('location_zones').delete().neq('id', 0).execute()
    
    return {
        'message': 'Warehouse layout cleared',
        'locations_deleted': len(locations_deleted.data) if locations_deleted.data else 0,
        'zones_deleted': len(zones_deleted.data) if zones_deleted.data else 0
    }

def update_location_properties(location_code: str, updates: Dict) -> Dict:
    """Update properties of an existing location"""
    allowed_updates = ['capacity', 'access_equipment', 'safety_notes', 'is_active', 'is_pickable', 'location_type']
    
    # Filter to only allowed updates
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
    
    if not filtered_updates:
        raise Exception('No valid updates provided')
    
    filtered_updates['updated_at'] = datetime.now().isoformat()
    
    response = supabase.table('pick_locations').update(filtered_updates).eq('location_code', location_code.upper()).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    if not response.data:
        raise Exception(f'Location {location_code} not found')
    
    return response.data[0]

def validate_warehouse_design(warehouse_design: Dict) -> Dict:
    """Validate a warehouse design before creating it"""
    errors = []
    warnings = []
    
    # Check required fields
    if 'zones' not in warehouse_design:
        errors.append('zones field is required')
    if 'aisles' not in warehouse_design:
        errors.append('aisles field is required')
    
    # Validate zones
    zone_codes = set()
    for zone in warehouse_design.get('zones', []):
        if 'zone_code' not in zone or 'zone_name' not in zone:
            errors.append('Each zone must have zone_code and zone_name')
        elif zone['zone_code'] in zone_codes:
            errors.append(f"Duplicate zone code: {zone['zone_code']}")
        else:
            zone_codes.add(zone['zone_code'])
    
    # Validate aisles
    location_codes = set()
    total_locations = 0
    
    for aisle_config in warehouse_design.get('aisles', []):
        if 'aisle' not in aisle_config or 'zone_code' not in aisle_config:
            errors.append('Each aisle must have aisle and zone_code')
            continue
        
        if aisle_config['zone_code'] not in zone_codes:
            errors.append(f"Zone {aisle_config['zone_code']} referenced but not defined")
        
        # Calculate locations for this aisle
        bays = aisle_config.get('bays', ['01'])
        levels = aisle_config.get('levels', ['1'])
        positions = aisle_config.get('positions', ['A'])
        
        aisle_locations = len(bays) * len(levels) * len(positions)
        total_locations += aisle_locations
        
        # Check for duplicate location codes
        aisle = aisle_config['aisle']
        for bay in bays:
            for level in levels:
                for position in positions:
                    location_code = f"{aisle}{bay}{level}{position}"
                    if location_code in location_codes:
                        errors.append(f"Duplicate location code: {location_code}")
                    else:
                        location_codes.add(location_code)
    
    # Warnings
    if total_locations > 1000:
        warnings.append(f'Large number of locations ({total_locations}) - consider breaking into phases')
    
    if total_locations == 0:
        errors.append('No locations would be created with this design')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'summary': {
            'total_zones': len(zone_codes),
            'total_locations': total_locations,
            'unique_aisles': len(set(a['aisle'] for a in warehouse_design.get('aisles', [])))
        }
    }