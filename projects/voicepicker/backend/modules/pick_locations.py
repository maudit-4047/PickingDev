from typing import Optional, List, Dict
from database.db_cofig import supabase
from datetime import datetime
from location_utils import (
    validate_location_code, 
    generate_location_code, 
    generate_check_digit,
    get_voice_friendly_location,
    get_equipment_required,
    is_complex_aisle
)

# Pick Locations Management Module

def get_all_zones() -> List[Dict]:
    """Get all location zones"""
    response = supabase.table('location_zones').select('*').eq('is_active', True).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def get_pick_locations(zone_id: int = None, aisle: str = None, is_active: bool = True, section: str = None, level: str = None) -> List[Dict]:
    """Get pick locations with optional filters"""
    query = supabase.table('pick_locations').select('*, location_zones(zone_name)')
    
    if is_active is not None:
        query = query.eq('is_active', is_active)
    if zone_id is not None:
        query = query.eq('zone_id', zone_id)
    if aisle is not None:
        query = query.eq('aisle', aisle)
    if section is not None:
        query = query.eq('section', section)
    if level is not None:
        query = query.eq('level', level)
    
    query = query.order('location_code')
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Add voice-friendly format and equipment info
    for location in response.data:
        location['voice_friendly'] = get_voice_friendly_location(location['location_code'])
        location['equipment_required'] = get_equipment_required(location['location_code'])
    
    return response.data

def get_location_by_code(location_code: str) -> Dict:
    """Get a specific location by its code"""
    # Validate location code format first
    try:
        parsed = validate_location_code(location_code)
    except ValueError as e:
        raise Exception(f"Invalid location code: {str(e)}")
    
    response = supabase.table('pick_locations').select('*, location_zones(zone_name)').eq('location_code', location_code).single().execute()
    if hasattr(response, 'error') and response.error:
        raise Exception('Location not found')
    
    location = response.data
    location['voice_friendly'] = get_voice_friendly_location(location['location_code'])
    location['equipment_required'] = get_equipment_required(location['location_code'])
    location['parsed_components'] = parsed
    
    return location

def search_locations(search_term: str) -> List[Dict]:
    """Search locations by code, section, aisle, or description"""
    query = supabase.table('pick_locations').select('*, location_zones(zone_name)')
    # Use ilike for case-insensitive search across multiple fields
    search_conditions = [
        f'location_code.ilike.%{search_term}%',
        f'section.ilike.%{search_term}%',
        f'aisle.ilike.%{search_term}%'
    ]
    query = query.or_(','.join(search_conditions))
    query = query.eq('is_active', True).order('location_code')
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Add voice-friendly format
    for location in response.data:
        location['voice_friendly'] = get_voice_friendly_location(location['location_code'])
        location['equipment_required'] = get_equipment_required(location['location_code'])
    
    return response.data

def get_locations_by_aisle(aisle: str, section: str = None) -> List[Dict]:
    """Get all locations in a specific aisle"""
    if section:
        return get_pick_locations(aisle=aisle, section=section)
    else:
        return get_pick_locations(aisle=aisle)

def get_location_inventory(location_id: int = None, location_code: str = None) -> List[Dict]:
    """Get inventory for a specific location"""
    if location_code:
        # First get location ID from code
        location = get_location_by_code(location_code)
        location_id = location['id']
    
    if not location_id:
        raise Exception('Location ID or code is required')
    
    response = supabase.table('location_inventory').select('*').eq('location_id', location_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def update_location_inventory(location_code: str, item_code: str, quantity_change: int, activity_type: str, worker_id: int = None, work_queue_id: int = None) -> Dict:
    """Update inventory at a location and log the activity"""
    # Get location
    location = get_location_by_code(location_code)
    location_id = location['id']
    
    # Get current inventory
    current_inv_response = supabase.table('location_inventory').select('*').eq('location_id', location_id).eq('item_code', item_code).execute()
    
    current_quantity = 0
    if current_inv_response.data:
        current_quantity = current_inv_response.data[0]['quantity']
    
    new_quantity = max(0, current_quantity + quantity_change)
    
    # Update or insert inventory record
    inventory_data = {
        'location_id': location_id,
        'item_code': item_code,
        'quantity': new_quantity,
        'updated_at': datetime.now().isoformat()
    }
    
    if activity_type == 'pick':
        inventory_data['last_picked_at'] = datetime.now().isoformat()
    elif activity_type == 'replenish':
        inventory_data['last_replenished_at'] = datetime.now().isoformat()
    
    if current_inv_response.data:
        # Update existing
        inv_response = supabase.table('location_inventory').update(inventory_data).eq('location_id', location_id).eq('item_code', item_code).execute()
    else:
        # Insert new
        inventory_data['created_at'] = datetime.now().isoformat()
        inv_response = supabase.table('location_inventory').insert(inventory_data).execute()
    
    if hasattr(inv_response, 'error') and inv_response.error:
        raise Exception(inv_response.error.message)
    
    # Log the activity
    log_location_activity(location_id, worker_id, activity_type, item_code, current_quantity, new_quantity, work_queue_id)
    
    # Update location's last picked timestamp if it was a pick
    if activity_type == 'pick':
        supabase.table('pick_locations').update({'last_picked_at': datetime.now().isoformat()}).eq('id', location_id).execute()
    
    return inv_response.data[0] if inv_response.data else inventory_data

def log_location_activity(location_id: int, worker_id: int, activity_type: str, item_code: str = None, quantity_before: int = None, quantity_after: int = None, work_queue_id: int = None, notes: str = None):
    """Log activity at a location"""
    activity_data = {
        'location_id': location_id,
        'worker_id': worker_id,
        'activity_type': activity_type,
        'item_code': item_code,
        'quantity_before': quantity_before,
        'quantity_after': quantity_after,
        'work_queue_id': work_queue_id,
        'notes': notes,
        'timestamp': datetime.now().isoformat()
    }
    
    # Remove None values
    activity_data = {k: v for k, v in activity_data.items() if v is not None}
    
    response = supabase.table('location_activity').insert(activity_data).execute()
    if hasattr(response, 'error') and response.error:
        print(f"Warning: Failed to log location activity: {response.error.message}")

def get_location_activity(location_code: str = None, worker_id: int = None, limit: int = 50) -> List[Dict]:
    """Get location activity history"""
    query = supabase.table('location_activity').select('*, pick_locations(location_code), workers(name)')
    
    if location_code:
        location = get_location_by_code(location_code)
        query = query.eq('location_id', location['id'])
    
    if worker_id:
        query = query.eq('worker_id', worker_id)
    
    query = query.order('timestamp', desc=True).limit(limit)
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def report_location_issue(location_code: str, worker_id: int, issue_type: str, description: str, severity: str = 'medium') -> Dict:
    """Report an issue with a location"""
    location = get_location_by_code(location_code)
    
    issue_data = {
        'location_id': location['id'],
        'reported_by': worker_id,
        'issue_type': issue_type,
        'description': description,
        'severity': severity,
        'status': 'open',
        'created_at': datetime.now().isoformat()
    }
    
    response = supabase.table('location_issues').insert(issue_data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    return response.data[0]

def get_location_issues(location_code: str = None, status: str = 'open') -> List[Dict]:
    """Get location issues"""
    query = supabase.table('location_issues').select('*, pick_locations(location_code), workers!location_issues_reported_by_fkey(name)')
    
    if location_code:
        location = get_location_by_code(location_code)
        query = query.eq('location_id', location['id'])
    
    if status:
        query = query.eq('status', status)
    
    query = query.order('created_at', desc=True)
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def get_location_utilization_stats() -> Dict:
    """Get location utilization statistics"""
    # Get total locations
    total_locations = supabase.table('pick_locations').select('id', count='exact').eq('is_active', True).execute()
    
    # Get locations with inventory
    occupied_locations = supabase.table('location_inventory').select('location_id', count='exact').gt('quantity', 0).execute()
    
    # Get pick activity in last 24 hours
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    recent_picks = supabase.table('location_activity').select('id', count='exact').eq('activity_type', 'pick').gt('timestamp', yesterday).execute()
    
    return {
        'total_locations': total_locations.count or 0,
        'occupied_locations': len(set([item['location_id'] for item in occupied_locations.data])) if occupied_locations.data else 0,
        'recent_pick_activities': recent_picks.count or 0,
        'utilization_rate': round((len(set([item['location_id'] for item in occupied_locations.data])) / (total_locations.count or 1)) * 100, 2) if total_locations.count else 0
    }

def get_aisle_summary() -> List[Dict]:
    """Get summary of all aisles with their location counts"""
    response = supabase.table('pick_locations').select('aisle').eq('is_active', True).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Group by aisle
    aisles = {}
    for location in response.data:
        aisle = location['aisle']
        if aisle not in aisles:
            aisles[aisle] = 0
        aisles[aisle] += 1
    
    return [{'aisle': aisle, 'location_count': count} for aisle, count in sorted(aisles.items())]

def find_items_in_locations(item_code: str) -> List[Dict]:
    """Find all locations where an item is stored"""
    query = supabase.table('location_inventory').select('*, pick_locations(location_code, section, aisle, bay, level)')
    query = query.eq('item_code', item_code).gt('quantity', 0)
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Add voice-friendly format for each location
    for item in response.data:
        if item.get('pick_locations'):
            location_code = item['pick_locations']['location_code']
            item['voice_friendly'] = get_voice_friendly_location(location_code)
            item['equipment_required'] = get_equipment_required(location_code)
    
    return response.data

def get_picker_locations(section: str = None, aisle: str = None) -> List[Dict]:
    """Get only picker-accessible locations (level 0 or no level specified)"""
    query = supabase.table('pick_locations').select('*, location_zones(zone_name)')
    query = query.eq('is_active', True).eq('is_pickable', True)
    
    # Filter for picker levels (level 0 or NULL)
    query = query.or_('level.is.null,level.eq.0')
    
    if section:
        query = query.eq('section', section)
    if aisle:
        query = query.eq('aisle', aisle)
    
    query = query.order('location_code')
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Add voice-friendly format
    for location in response.data:
        location['voice_friendly'] = get_voice_friendly_location(location['location_code'])
        location['equipment_required'] = 'manual'  # All picker locations are manual
    
    return response.data

def get_forklift_locations(section: str = None, aisle: str = None) -> List[Dict]:
    """Get only forklift-accessible locations (levels B-F)"""
    query = supabase.table('pick_locations').select('*, location_zones(zone_name)')
    query = query.eq('is_active', True)
    
    # Filter for forklift levels (B, C, D, E, F)
    query = query.in_('level', ['B', 'C', 'D', 'E', 'F'])
    
    if section:
        query = query.eq('section', section)
    if aisle:
        query = query.eq('aisle', aisle)
    
    query = query.order('location_code')
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Add voice-friendly format
    for location in response.data:
        location['voice_friendly'] = get_voice_friendly_location(location['location_code'])
        location['equipment_required'] = 'forklift'
    
    return response.data

def get_section_summary() -> List[Dict]:
    """Get summary of all warehouse sections with their statistics"""
    sections_response = supabase.table('location_zones').select('*').eq('is_active', True).execute()
    if hasattr(sections_response, 'error') and sections_response.error:
        raise Exception(sections_response.error.message)
    
    summary = []
    for section in sections_response.data:
        # Get location count for this section
        locations_response = supabase.table('pick_locations').select('id', count='exact').eq('zone_id', section['id']).eq('is_active', True).execute()
        
        # Get picker locations count (level 0)
        picker_response = supabase.table('pick_locations').select('id', count='exact').eq('zone_id', section['id']).or_('level.is.null,level.eq.0').execute()
        
        # Get forklift locations count (levels B-F)
        forklift_response = supabase.table('pick_locations').select('id', count='exact').eq('zone_id', section['id']).in_('level', ['B', 'C', 'D', 'E', 'F']).execute()
        
        summary.append({
            'section': section,
            'total_locations': locations_response.count or 0,
            'picker_locations': picker_response.count or 0,
            'forklift_locations': forklift_response.count or 0
        })
    
    return summary