from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from warehouse_designer import (
    create_custom_zone as create_zone_logic,
    create_custom_location as create_location_logic,
    bulk_create_locations as bulk_create_logic,
    get_warehouse_layout_summary as get_layout_logic,
    create_warehouse_template as create_template_logic,
    delete_warehouse_layout as delete_layout_logic,
    update_location_properties as update_location_logic,
    validate_warehouse_design as validate_design_logic
)

router = APIRouter()

class CustomZone(BaseModel):
    zone_code: str
    zone_name: str
    description: Optional[str] = None

class CustomLocation(BaseModel):
    location_code: str
    zone_code: str
    aisle: Optional[str] = None
    bay: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    location_type: str = 'pick'
    capacity: int = 100
    access_equipment: str = 'manual'
    safety_notes: Optional[str] = None

class AisleConfig(BaseModel):
    aisle: str
    zone_code: str
    bays: List[str] = ['01']
    levels: List[str] = ['1']
    positions: List[str] = ['A']
    location_type: str = 'pick'
    capacity: int = 100
    access_equipment: str = 'manual'

class WarehouseDesign(BaseModel):
    warehouse_name: str
    zones: List[CustomZone]
    aisles: List[AisleConfig]

class LocationUpdate(BaseModel):
    capacity: Optional[int] = None
    access_equipment: Optional[str] = None
    safety_notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_pickable: Optional[bool] = None
    location_type: Optional[str] = None

class WarehouseLayoutSummary(BaseModel):
    total_zones: int
    total_locations: int
    zones: List[Dict[str, str]]
    layout: Dict[str, Any]

class ValidationResult(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, int]

class BulkCreateResult(BaseModel):
    warehouse_name: str
    zones_created: int
    locations_created: int
    created_zones: List[Dict[str, Any]]
    created_locations: List[Dict[str, Any]]

# Create custom zone
@router.post('/warehouse-designer/zones', status_code=status.HTTP_201_CREATED)
def create_custom_zone(zone: CustomZone):
    """Create a custom warehouse zone"""
    try:
        return create_zone_logic(zone.zone_code, zone.zone_name, zone.description)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create custom location
@router.post('/warehouse-designer/locations', status_code=status.HTTP_201_CREATED)
def create_custom_location(location: CustomLocation):
    """Create a custom pick location"""
    try:
        return create_location_logic(
            location.location_code,
            location.zone_code,
            location.aisle,
            location.bay,
            location.level,
            location.position,
            location.location_type,
            location.capacity,
            location.access_equipment,
            location.safety_notes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Validate warehouse design
@router.post('/warehouse-designer/validate', response_model=ValidationResult)
def validate_warehouse_design(design: WarehouseDesign):
    """Validate a warehouse design before creating it"""
    try:
        return validate_design_logic(design.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create warehouse from design
@router.post('/warehouse-designer/create', response_model=BulkCreateResult)
def create_warehouse_from_design(design: WarehouseDesign):
    """Create an entire warehouse layout from a design"""
    try:
        # Validate first
        validation = validate_design_logic(design.dict())
        if not validation['valid']:
            raise HTTPException(
                status_code=400, 
                detail=f"Design validation failed: {', '.join(validation['errors'])}"
            )
        
        return bulk_create_logic(design.dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create from template
@router.post('/warehouse-designer/templates/{template_name}', response_model=BulkCreateResult)
def create_warehouse_from_template(template_name: str):
    """Create warehouse layout from a predefined template"""
    try:
        return create_template_logic(template_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get available templates
@router.get('/warehouse-designer/templates')
def get_available_templates():
    """Get list of available warehouse templates"""
    return {
        'templates': [
            {
                'name': 'small_warehouse',
                'description': 'Small warehouse with 2 aisles, 2 bays each, 2 levels',
                'estimated_locations': 16
            },
            {
                'name': 'medium_warehouse', 
                'description': 'Medium warehouse with 4 aisles (A-D), 5 bays each, 3 levels',
                'estimated_locations': 120
            },
            {
                'name': 'large_warehouse',
                'description': 'Large warehouse with 6 aisles (A-F), 10 bays each, 4 levels',
                'estimated_locations': 480
            }
        ]
    }

# Get warehouse layout summary
@router.get('/warehouse-designer/layout', response_model=WarehouseLayoutSummary)
def get_warehouse_layout():
    """Get current warehouse layout summary"""
    try:
        return get_layout_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update location properties
@router.patch('/warehouse-designer/locations/{location_code}')
def update_location_properties(location_code: str, updates: LocationUpdate):
    """Update properties of an existing location"""
    try:
        update_data = updates.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        return update_location_logic(location_code, update_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete entire warehouse layout (dangerous!)
@router.delete('/warehouse-designer/layout')
def delete_warehouse_layout(confirm: bool = Query(False, description="Must be true to confirm deletion")):
    """Delete the entire warehouse layout - USE WITH CAUTION"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to delete warehouse layout"
        )
    
    try:
        return delete_layout_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Export warehouse design
@router.get('/warehouse-designer/export')
def export_warehouse_design():
    """Export current warehouse design as JSON for backup/sharing"""
    try:
        from datetime import datetime
        from database.db_cofig import supabase
        
        # Import from the modules we can access
        zones_response = supabase.table('location_zones').select('*').eq('is_active', True).execute()
        locations_response = supabase.table('pick_locations').select('*').eq('is_active', True).execute()
        
        if hasattr(zones_response, 'error') and zones_response.error:
            raise Exception(zones_response.error.message)
        if hasattr(locations_response, 'error') and locations_response.error:
            raise Exception(locations_response.error.message)
        
        zones = zones_response.data
        locations = locations_response.data
        
        # Group locations by aisle for easier reconstruction
        aisles = {}
        for location in locations:
            aisle = location.get('aisle', 'NO_AISLE')
            if aisle not in aisles:
                aisles[aisle] = {
                    'aisle': aisle,
                    'zone_code': next((z['zone_code'] for z in zones if z['id'] == location['zone_id']), 'UNKNOWN'),
                    'locations': []
                }
            aisles[aisle]['locations'].append(location)
        
        return {
            'warehouse_name': 'Exported Warehouse',
            'export_date': str(datetime.now()),
            'zones': zones,
            'aisles': list(aisles.values()),
            'total_locations': len(locations)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Preview warehouse design
@router.post('/warehouse-designer/preview')
def preview_warehouse_design(design: WarehouseDesign):
    """Preview what a warehouse design would create without actually creating it"""
    try:
        validation = validate_design_logic(design.dict())
        
        # Generate preview of location codes
        location_codes = []
        for aisle_config in design.aisles:
            aisle = aisle_config.aisle
            for bay in aisle_config.bays:
                for level in aisle_config.levels:
                    for position in aisle_config.positions:
                        location_codes.append(f"{aisle}{bay}{level}{position}")
        
        return {
            'validation': validation,
            'preview': {
                'warehouse_name': design.warehouse_name,
                'zones_to_create': [z.zone_code for z in design.zones],
                'sample_location_codes': location_codes[:20],  # First 20 as sample
                'total_locations': len(location_codes),
                'aisles_summary': [
                    {
                        'aisle': a.aisle,
                        'zone': a.zone_code,
                        'locations_in_aisle': len(a.bays) * len(a.levels) * len(a.positions)
                    } for a in design.aisles
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))