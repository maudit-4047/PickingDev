from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from modules.config import get_config_value
from database.db_cofig import supabase

router = APIRouter()

@router.get('/config')
def get_config():
    """Get current system configuration values."""
    return {
        'team_size_cap': get_config_value('team_size_cap', 50),
        'pin_min': get_config_value('pin_min', 1000),
        'pin_max': get_config_value('pin_max', 9999)
    }

class ConfigUpdate(BaseModel):
    team_size_cap: int = None
    pin_min: int = None
    pin_max: int = None

@router.patch('/config')
def update_config(update: ConfigUpdate = Body(...)):
    updates = update.dict(exclude_unset=True)
    allowed_keys = ['team_size_cap', 'pin_min', 'pin_max']
    for key, value in updates.items():
        if key not in allowed_keys:
            continue
        resp = supabase.table('system_config').upsert({
            'key': key,
            'value': str(value)
        }, on_conflict=['key']).execute()
        if hasattr(resp, 'error') and resp.error:
            raise HTTPException(status_code=400, detail=f"Failed to update {key}: {resp.error.message}")
    return {"message": "Config updated", "updated": updates}
