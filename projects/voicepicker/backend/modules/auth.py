
from typing import Optional, List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_cofig import supabase
from modules.config import get_config_value
import random

# Business logic for workers

def generate_unique_pin():
    pin_min = get_config_value('pin_min', 1000)
    pin_max = get_config_value('pin_max', 9999)
    used_pins_response = supabase.table('workers').select('pin').execute()
    if hasattr(used_pins_response, 'error') and used_pins_response.error:
        raise Exception(used_pins_response.error.message)
    used_pins = {w['pin'] for w in used_pins_response.data if w.get('pin') is not None}
    for pin in range(pin_min, pin_max + 1):
        if pin not in used_pins:
            return pin
    raise Exception('No available pins in the configured range')

def get_or_create_team():
    team_max_members = get_config_value('team_size_cap', 50)
    # Find a team with less than team_max_members
    teams_response = supabase.table('teams').select('id').execute()
    if hasattr(teams_response, 'error') and teams_response.error:
        raise Exception(teams_response.error.message)
    for team in teams_response.data:
        count_response = supabase.table('workers').select('id', count='exact').eq('team_id', team['id']).execute()
        if hasattr(count_response, 'error') and count_response.error:
            raise Exception(count_response.error.message)
        if count_response.count is not None and count_response.count < team_max_members:
            return team['id']
    # If all teams are full, create a new team
    new_team_name = f"Team {len(teams_response.data) + 1}"
    create_team_response = supabase.table('teams').insert({'name': new_team_name}).execute()
    if hasattr(create_team_response, 'error') and create_team_response.error:
        raise Exception(create_team_response.error.message)
    return create_team_response.data[0]['id']

def create_worker(data: Dict) -> Dict:
    data['status'] = 'active'
    if 'pin' not in data or data['pin'] is None:
        data['pin'] = generate_unique_pin()
    if 'team_id' not in data or data['team_id'] is None:
        data['team_id'] = get_or_create_team()
    response = supabase.table('workers').insert(data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]


def get_workers(team_id: int = None) -> List[Dict]:
    query = supabase.table('workers').select('*')
    if team_id is not None:
        query = query.eq('team_id', team_id)
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data


def get_worker(worker_id: int = None, pin: int = None) -> Dict:
    query = supabase.table('workers').select('*')
    if worker_id is not None:
        query = query.eq('id', worker_id)
    elif pin is not None:
        query = query.eq('pin', pin)
    else:
        raise Exception('Must provide worker_id or pin')
    response = query.single().execute()
    if hasattr(response, 'error') and response.error:
        raise Exception('Worker not found')
    return response.data


def update_worker(worker_id: int = None, pin: int = None, data: Dict = None) -> Dict:
    query = supabase.table('workers')
    if worker_id is not None:
        query = query.update(data).eq('id', worker_id)
    elif pin is not None:
        query = query.update(data).eq('pin', pin)
    else:
        raise Exception('Must provide worker_id or pin')
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]


def delete_worker(worker_id: int = None, pin: int = None) -> None:
    query = supabase.table('workers')
    if worker_id is not None:
        query = query.delete().eq('id', worker_id)
    elif pin is not None:
        query = query.delete().eq('pin', pin)
    else:
        raise Exception('Must provide worker_id or pin')
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return None


def login_worker(name: str, pin: str) -> dict:
    response = supabase.table('workers').select('*').eq('name', name).eq('pin', pin).single().execute()
    if hasattr(response, 'error') and response.error or not response.data:
        raise Exception('Invalid credentials')
    return response.data
