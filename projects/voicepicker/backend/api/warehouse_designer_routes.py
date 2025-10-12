"""
Warehouse Designer API Routes
Provides CRUD operations for warehouse layout management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from database.db_cofig import supabase
from modules.warehouse_templates import WarehouseTemplateManager
import json

router = APIRouter(prefix="/warehouse-designer", tags=["warehouse-designer"])

# Request/Response Models
class WarehouseConfigCreate(BaseModel):
    warehouse_name: str = Field(..., min_length=1, max_length=255)
    location_naming_pattern: str = Field(default="{section}{aisle}-{bay:03d}")
    check_digit_min: int = Field(default=1, ge=1)
    check_digit_max: int = Field(default=37, le=99)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WarehouseConfigUpdate(BaseModel):
    warehouse_name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_naming_pattern: Optional[str] = None
    check_digit_min: Optional[int] = Field(None, ge=1)
    check_digit_max: Optional[int] = Field(None, le=99)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WarehouseSectionCreate(BaseModel):
    section_code: str = Field(..., min_length=1, max_length=10)
    section_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sort_order: int = Field(default=0)

class WarehouseSectionUpdate(BaseModel):
    section_code: Optional[str] = Field(None, min_length=1, max_length=10)
    section_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class WarehouseAisleCreate(BaseModel):
    aisle_code: str = Field(..., min_length=1, max_length=10)
    aisle_name: str = Field(..., min_length=1, max_length=255)
    bay_range_start: int = Field(default=1, ge=1)
    bay_range_end: int = Field(default=99, ge=1)
    is_complex: bool = Field(default=False)
    description: Optional[str] = None
    sort_order: int = Field(default=0)

class WarehouseAisleUpdate(BaseModel):
    aisle_code: Optional[str] = Field(None, min_length=1, max_length=10)
    aisle_name: Optional[str] = Field(None, min_length=1, max_length=255)
    bay_range_start: Optional[int] = Field(None, ge=1)
    bay_range_end: Optional[int] = Field(None, ge=1)
    is_complex: Optional[bool] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class WarehouseLevelCreate(BaseModel):
    level_code: str = Field(..., min_length=1, max_length=10)
    level_name: str = Field(..., min_length=1, max_length=255)
    equipment_required: str = Field(default="manual")
    height_feet: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    sort_order: int = Field(default=0)

class WarehouseLevelUpdate(BaseModel):
    level_code: Optional[str] = Field(None, min_length=1, max_length=10)
    level_name: Optional[str] = Field(None, min_length=1, max_length=255)
    equipment_required: Optional[str] = None
    height_feet: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class WarehouseSubsectionCreate(BaseModel):
    subsection_code: str = Field(..., min_length=1, max_length=10)
    subsection_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sort_order: int = Field(default=0)

class WarehouseSubsectionUpdate(BaseModel):
    subsection_code: Optional[str] = Field(None, min_length=1, max_length=10)
    subsection_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

# Warehouse Configuration Endpoints
@router.get("/warehouses")
async def list_warehouses():
    """List all warehouses"""
    try:
        response = supabase.table('warehouse_config').select('*').order('created_at').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        return {"warehouses": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: int):
    """Get warehouse details with full structure"""
    try:
        # Get warehouse config
        warehouse_response = supabase.table('warehouse_config').select('*').eq('id', warehouse_id).single().execute()
        if hasattr(warehouse_response, 'error') and warehouse_response.error:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        warehouse = warehouse_response.data
        
        # Get sections
        sections_response = supabase.table('warehouse_sections').select('*').eq('warehouse_id', warehouse_id).order('sort_order').execute()
        if hasattr(sections_response, 'error') and sections_response.error:
            raise HTTPException(status_code=400, detail=sections_response.error.message)
        
        sections = sections_response.data
        
        # Get aisles for each section
        for section in sections:
            aisles_response = supabase.table('warehouse_aisles').select('*').eq('section_id', section['id']).order('sort_order').execute()
            if hasattr(aisles_response, 'error') and aisles_response.error:
                continue
            
            aisles = aisles_response.data
            
            # Get levels for each aisle
            for aisle in aisles:
                levels_response = supabase.table('warehouse_levels').select('*').eq('aisle_id', aisle['id']).order('sort_order').execute()
                if hasattr(levels_response, 'error') and levels_response.error:
                    aisle['levels'] = []
                    continue
                
                levels = levels_response.data
                
                # Get subsections for each level
                for level in levels:
                    subsections_response = supabase.table('warehouse_subsections').select('*').eq('level_id', level['id']).order('sort_order').execute()
                    if hasattr(subsections_response, 'error') and subsections_response.error:
                        level['subsections'] = []
                        continue
                    
                    level['subsections'] = subsections_response.data
                
                aisle['levels'] = levels
            
            section['aisles'] = aisles
        
        warehouse['sections'] = sections
        
        return {"warehouse": warehouse}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses")
async def create_warehouse(warehouse: WarehouseConfigCreate):
    """Create a new warehouse"""
    try:
        response = supabase.table('warehouse_config').insert(warehouse.dict()).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"warehouse": response.data[0], "message": "Warehouse created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: int, warehouse: WarehouseConfigUpdate):
    """Update warehouse configuration"""
    try:
        # Remove None values
        update_data = {k: v for k, v in warehouse.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table('warehouse_config').update(update_data).eq('id', warehouse_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        return {"warehouse": response.data[0], "message": "Warehouse updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(warehouse_id: int):
    """Delete a warehouse (soft delete by setting is_active=false)"""
    try:
        response = supabase.table('warehouse_config').update({"is_active": False}).eq('id', warehouse_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        return {"message": "Warehouse deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Section Endpoints
@router.get("/warehouses/{warehouse_id}/sections")
async def list_sections(warehouse_id: int):
    """List sections for a warehouse"""
    try:
        response = supabase.table('warehouse_sections').select('*').eq('warehouse_id', warehouse_id).order('sort_order').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"sections": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/sections")
async def create_section(warehouse_id: int, section: WarehouseSectionCreate):
    """Create a new section"""
    try:
        section_data = section.dict()
        section_data['warehouse_id'] = warehouse_id
        
        response = supabase.table('warehouse_sections').insert(section_data).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"section": response.data[0], "message": "Section created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.put("/warehouses/{warehouse_id}/sections/{section_id}")
async def update_section(warehouse_id: int, section_id: int, section: WarehouseSectionUpdate):
    """Update a section"""
    try:
        update_data = {k: v for k, v in section.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table('warehouse_sections').update(update_data).eq('id', section_id).eq('warehouse_id', warehouse_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Section not found")
        
        return {"section": response.data[0], "message": "Section updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/warehouses/{warehouse_id}/sections/{section_id}")
async def delete_section(warehouse_id: int, section_id: int):
    """Delete a section"""
    try:
        response = supabase.table('warehouse_sections').update({"is_active": False}).eq('id', section_id).eq('warehouse_id', warehouse_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Section not found")
        
        return {"message": "Section deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Aisle Endpoints
@router.get("/warehouses/{warehouse_id}/sections/{section_id}/aisles")
async def list_aisles(warehouse_id: int, section_id: int):
    """List aisles for a section"""
    try:
        response = supabase.table('warehouse_aisles').select('*').eq('section_id', section_id).order('sort_order').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"aisles": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/sections/{section_id}/aisles")
async def create_aisle(warehouse_id: int, section_id: int, aisle: WarehouseAisleCreate):
    """Create a new aisle"""
    try:
        aisle_data = aisle.dict()
        aisle_data['section_id'] = section_id
        
        # Validate bay range
        if aisle_data['bay_range_start'] > aisle_data['bay_range_end']:
            raise HTTPException(status_code=400, detail="Bay range start must be less than or equal to bay range end")
        
        response = supabase.table('warehouse_aisles').insert(aisle_data).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"aisle": response.data[0], "message": "Aisle created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/warehouses/{warehouse_id}/sections/{section_id}/aisles/{aisle_id}")
async def update_aisle(warehouse_id: int, section_id: int, aisle_id: int, aisle: WarehouseAisleUpdate):
    """Update an aisle"""
    try:
        update_data = {k: v for k, v in aisle.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Validate bay range if both are provided
        if 'bay_range_start' in update_data and 'bay_range_end' in update_data:
            if update_data['bay_range_start'] > update_data['bay_range_end']:
                raise HTTPException(status_code=400, detail="Bay range start must be less than or equal to bay range end")
        
        response = supabase.table('warehouse_aisles').update(update_data).eq('id', aisle_id).eq('section_id', section_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Aisle not found")
        
        return {"aisle": response.data[0], "message": "Aisle updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/warehouses/{warehouse_id}/sections/{section_id}/aisles/{aisle_id}")
async def delete_aisle(warehouse_id: int, section_id: int, aisle_id: int):
    """Delete an aisle"""
    try:
        response = supabase.table('warehouse_aisles').update({"is_active": False}).eq('id', aisle_id).eq('section_id', section_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Aisle not found")
        
        return {"message": "Aisle deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Level Endpoints
@router.get("/warehouses/{warehouse_id}/aisles/{aisle_id}/levels")
async def list_levels(warehouse_id: int, aisle_id: int):
    """List levels for an aisle"""
    try:
        response = supabase.table('warehouse_levels').select('*').eq('aisle_id', aisle_id).order('sort_order').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"levels": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/aisles/{aisle_id}/levels")
async def create_level(warehouse_id: int, aisle_id: int, level: WarehouseLevelCreate):
    """Create a new level"""
    try:
        level_data = level.dict()
        level_data['aisle_id'] = aisle_id
        
        response = supabase.table('warehouse_levels').insert(level_data).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"level": response.data[0], "message": "Level created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/warehouses/{warehouse_id}/aisles/{aisle_id}/levels/{level_id}")
async def update_level(warehouse_id: int, aisle_id: int, level_id: int, level: WarehouseLevelUpdate):
    """Update a level"""
    try:
        update_data = {k: v for k, v in level.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table('warehouse_levels').update(update_data).eq('id', level_id).eq('aisle_id', aisle_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Level not found")
        
        return {"level": response.data[0], "message": "Level updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/warehouses/{warehouse_id}/aisles/{aisle_id}/levels/{level_id}")
async def delete_level(warehouse_id: int, aisle_id: int, level_id: int):
    """Delete a level"""
    try:
        response = supabase.table('warehouse_levels').update({"is_active": False}).eq('id', level_id).eq('aisle_id', aisle_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Level not found")
        
        return {"message": "Level deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Subsection Endpoints
@router.get("/warehouses/{warehouse_id}/levels/{level_id}/subsections")
async def list_subsections(warehouse_id: int, level_id: int):
    """List subsections for a level"""
    try:
        response = supabase.table('warehouse_subsections').select('*').eq('level_id', level_id).order('sort_order').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"subsections": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/levels/{level_id}/subsections")
async def create_subsection(warehouse_id: int, level_id: int, subsection: WarehouseSubsectionCreate):
    """Create a new subsection"""
    try:
        subsection_data = subsection.dict()
        subsection_data['level_id'] = level_id
        
        response = supabase.table('warehouse_subsections').insert(subsection_data).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"subsection": response.data[0], "message": "Subsection created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/warehouses/{warehouse_id}/levels/{level_id}/subsections/{subsection_id}")
async def update_subsection(warehouse_id: int, level_id: int, subsection_id: int, subsection: WarehouseSubsectionUpdate):
    """Update a subsection"""
    try:
        update_data = {k: v for k, v in subsection.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table('warehouse_subsections').update(update_data).eq('id', subsection_id).eq('level_id', level_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Subsection not found")
        
        return {"subsection": response.data[0], "message": "Subsection updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/warehouses/{warehouse_id}/levels/{level_id}/subsections/{subsection_id}")
async def delete_subsection(warehouse_id: int, level_id: int, subsection_id: int):
    """Delete a subsection"""
    try:
        response = supabase.table('warehouse_subsections').update({"is_active": False}).eq('id', subsection_id).eq('level_id', level_id).execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Subsection not found")
        
        return {"message": "Subsection deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Template Management Endpoints
@router.get("/templates")
async def list_templates():
    """List all warehouse templates"""
    try:
        response = supabase.table('warehouse_templates').select('*').order('created_at').execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)
        
        return {"templates": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/{template_id}/create-warehouse")
async def create_warehouse_from_template(template_id: int, warehouse_name: str):
    """Create a warehouse from a template"""
    try:
        template_manager = WarehouseTemplateManager()
        warehouse_id = template_manager.create_warehouse_from_template(template_id, warehouse_name)
        
        return {
            "warehouse_id": warehouse_id,
            "message": f"Warehouse '{warehouse_name}' created successfully from template"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}/export")
async def export_warehouse_as_template(warehouse_id: int):
    """Export warehouse configuration as a template"""
    try:
        template_manager = WarehouseTemplateManager()
        template_data = template_manager.export_warehouse_as_template(warehouse_id)
        
        return {"template": template_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/import")
async def import_template(template_name: str, template_data: Dict[str, Any]):
    """Import a template from JSON data"""
    try:
        template_manager = WarehouseTemplateManager()
        template_id = template_manager.import_template(template_name, template_data)
        
        return {
            "template_id": template_id,
            "message": f"Template '{template_name}' imported successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Utility Endpoints
@router.get("/warehouses/{warehouse_id}/statistics")
async def get_warehouse_statistics(warehouse_id: int):
    """Get warehouse statistics and validation report"""
    try:
        from modules.location_utils_dynamic import validate_warehouse_structure
        stats = validate_warehouse_structure(warehouse_id)
        return {"statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}/preview-locations")
async def preview_locations(warehouse_id: int, section_code: str = None, aisle_code: str = None, limit: int = 100):
    """Preview generated location codes for a warehouse"""
    try:
        from modules.location_utils_dynamic import get_warehouse_config, get_all_locations_for_aisle, get_picker_locations_for_aisle
        
        config = get_warehouse_config(warehouse_id)
        locations = []
        
        if section_code and aisle_code:
            # Preview specific aisle
            locations = get_picker_locations_for_aisle(section_code, aisle_code, warehouse_id)[:limit]
        else:
            # Preview all sections
            for section in config.sections[:5]:  # Limit to first 5 sections
                aisles = config.get_aisles(section['id'])
                for aisle in aisles[:3]:  # Limit to first 3 aisles per section
                    aisle_locations = get_picker_locations_for_aisle(section['section_code'], aisle['aisle_code'], warehouse_id)
                    locations.extend(aisle_locations[:10])  # First 10 locations per aisle
                    if len(locations) >= limit:
                        break
                if len(locations) >= limit:
                    break
        
        return {
            "locations": locations[:limit],
            "total_shown": len(locations[:limit]),
            "warehouse_id": warehouse_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))