from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from pick_locations import (
    get_all_zones as get_zones_logic,
    get_pick_locations as get_locations_logic,
    get_location_by_code as get_location_logic,
    search_locations as search_locations_logic,
    get_locations_by_aisle as get_aisle_locations_logic,
    get_location_inventory as get_inventory_logic,
    update_location_inventory as update_inventory_logic,
    get_location_activity as get_activity_logic,
    report_location_issue as report_issue_logic,
    get_location_issues as get_issues_logic,
    get_location_utilization_stats as get_stats_logic,
    get_aisle_summary as get_aisle_summary_logic,
    find_items_in_locations as find_items_logic,
    get_picker_locations as get_picker_locations_logic,
    get_forklift_locations as get_forklift_locations_logic,
    get_section_summary as get_section_summary_logic
)

router = APIRouter()

class LocationZoneOut(BaseModel):
    id: int
    zone_code: str
    zone_name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

class PickLocationOut(BaseModel):
    id: int
    location_code: str
    zone_id: int
    section: str
    aisle: str
    bay: str
    level: Optional[str]
    subsection: Optional[str]
    check_digit: int
    location_type: str
    is_complex_aisle: bool
    capacity: int
    current_occupancy: int
    is_active: bool
    is_pickable: bool
    access_equipment: Optional[str]
    safety_notes: Optional[str]
    last_picked_at: Optional[str]
    created_at: str
    updated_at: str
    # Additional computed fields
    voice_friendly: Optional[str] = None
    equipment_required: Optional[str] = None
    parsed_components: Optional[Dict] = None

class LocationInventoryOut(BaseModel):
    id: int
    location_id: int
    item_code: str
    quantity: int
    last_replenished_at: Optional[str]
    last_picked_at: Optional[str]
    created_at: str
    updated_at: str

class InventoryUpdate(BaseModel):
    location_code: str
    item_code: str
    quantity_change: int
    activity_type: str  # 'pick', 'replenish', 'count', 'move'
    worker_id: Optional[int] = None
    work_queue_id: Optional[int] = None

class LocationActivityOut(BaseModel):
    id: int
    location_id: int
    worker_id: Optional[int]
    activity_type: str
    item_code: Optional[str]
    quantity_before: Optional[int]
    quantity_after: Optional[int]
    work_queue_id: Optional[int]
    notes: Optional[str]
    timestamp: str

class LocationIssueCreate(BaseModel):
    location_code: str
    worker_id: int
    issue_type: str  # 'damage', 'blocked', 'unsafe', 'mislabeled'
    description: str
    severity: Optional[str] = 'medium'  # 'low', 'medium', 'high', 'critical'

class LocationIssueOut(BaseModel):
    id: int
    location_id: int
    reported_by: int
    issue_type: str
    severity: str
    description: str
    status: str
    resolved_by: Optional[int]
    resolved_at: Optional[str]
    created_at: str
    updated_at: str

class LocationStats(BaseModel):
    total_locations: int
    occupied_locations: int
    recent_pick_activities: int
    utilization_rate: float

class AisleSummary(BaseModel):
    aisle: str
    location_count: int

# Get all zones
@router.get('/locations/zones', response_model=List[LocationZoneOut])
def get_location_zones():
    """Get all location zones"""
    try:
        return get_zones_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get pick locations
@router.get('/locations', response_model=List[PickLocationOut])
def get_pick_locations(
    zone_id: Optional[int] = Query(None, description="Filter by zone ID"),
    section: Optional[str] = Query(None, description="Filter by section (H, L, M, B, A)"),
    aisle: Optional[str] = Query(None, description="Filter by aisle"),
    level: Optional[str] = Query(None, description="Filter by level (0, B, C, D, E, F)"),
    is_active: bool = Query(True, description="Filter by active status")
):
    """Get pick locations with optional filters"""
    try:
        return get_locations_logic(zone_id=zone_id, aisle=aisle, is_active=is_active, section=section, level=level)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get location by code
@router.get('/locations/{location_code}', response_model=PickLocationOut)
def get_location_by_code(location_code: str):
    """Get a specific location by its code"""
    try:
        return get_location_logic(location_code)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Search locations
@router.get('/locations/search/{search_term}', response_model=List[PickLocationOut])
def search_locations(search_term: str):
    """Search locations by code, aisle, or description"""
    try:
        return search_locations_logic(search_term)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get locations by aisle
@router.get('/locations/aisle/{aisle}', response_model=List[PickLocationOut])
def get_locations_by_aisle(
    aisle: str,
    section: Optional[str] = Query(None, description="Filter by section")
):
    """Get all locations in a specific aisle"""
    try:
        return get_aisle_locations_logic(aisle, section)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get location inventory
@router.get('/locations/{location_code}/inventory', response_model=List[LocationInventoryOut])
def get_location_inventory(location_code: str):
    """Get inventory for a specific location"""
    try:
        return get_inventory_logic(location_code=location_code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update location inventory
@router.post('/locations/inventory/update', response_model=LocationInventoryOut)
def update_location_inventory(update: InventoryUpdate):
    """Update inventory at a location"""
    try:
        return update_inventory_logic(
            update.location_code,
            update.item_code,
            update.quantity_change,
            update.activity_type,
            update.worker_id,
            update.work_queue_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get location activity
@router.get('/locations/activity', response_model=List[LocationActivityOut])
def get_location_activity(
    location_code: Optional[str] = Query(None, description="Filter by location code"),
    worker_id: Optional[int] = Query(None, description="Filter by worker ID"),
    limit: int = Query(50, description="Limit results")
):
    """Get location activity history"""
    try:
        return get_activity_logic(location_code=location_code, worker_id=worker_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Report location issue
@router.post('/locations/issues', response_model=LocationIssueOut, status_code=status.HTTP_201_CREATED)
def report_location_issue(issue: LocationIssueCreate):
    """Report an issue with a location"""
    try:
        return report_issue_logic(
            issue.location_code,
            issue.worker_id,
            issue.issue_type,
            issue.description,
            issue.severity
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get location issues
@router.get('/locations/issues', response_model=List[LocationIssueOut])
def get_location_issues(
    location_code: Optional[str] = Query(None, description="Filter by location code"),
    status: str = Query('open', description="Filter by status")
):
    """Get location issues"""
    try:
        return get_issues_logic(location_code=location_code, status=status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get location statistics
@router.get('/locations/stats', response_model=LocationStats)
def get_location_stats():
    """Get location utilization statistics"""
    try:
        return get_stats_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get aisle summary
@router.get('/locations/aisles/summary', response_model=List[AisleSummary])
def get_aisle_summary():
    """Get summary of all aisles with their location counts"""
    try:
        return get_aisle_summary_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Find items in locations
@router.get('/locations/items/{item_code}', response_model=List[LocationInventoryOut])
def find_items_in_locations(item_code: str):
    """Find all locations where an item is stored"""
    try:
        return find_items_logic(item_code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get picker-only locations (level 0)
@router.get('/locations/picker', response_model=List[PickLocationOut])
def get_picker_locations(
    section: Optional[str] = Query(None, description="Filter by section"),
    aisle: Optional[str] = Query(None, description="Filter by aisle")
):
    """Get only picker-accessible locations (level 0)"""
    try:
        return get_picker_locations_logic(section=section, aisle=aisle)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get forklift-only locations (levels B-F)
@router.get('/locations/forklift', response_model=List[PickLocationOut])
def get_forklift_locations(
    section: Optional[str] = Query(None, description="Filter by section"),
    aisle: Optional[str] = Query(None, description="Filter by aisle")
):
    """Get only forklift-accessible locations (levels B-F)"""
    try:
        return get_forklift_locations_logic(section=section, aisle=aisle)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SectionSummary(BaseModel):
    section: LocationZoneOut
    total_locations: int
    picker_locations: int
    forklift_locations: int

# Get section summary
@router.get('/locations/sections/summary', response_model=List[SectionSummary])
def get_section_summary():
    """Get summary of all warehouse sections with their statistics"""
    try:
        return get_section_summary_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))