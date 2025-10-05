from typing import Optional, List, Dict
from database.db_cofig import supabase

# Business logic for workers

def create_worker(data: Dict) -> Dict:
    data['status'] = 'active'
    response = supabase.table('workers').insert(data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]


def get_workers() -> List[Dict]:
    response = supabase.table('workers').select('*').execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data


def get_worker(worker_id: int) -> Dict:
    response = supabase.table('workers').select('*').eq('id', worker_id).single().execute()
    if hasattr(response, 'error') and response.error:
        raise Exception('Worker not found')
    return response.data


def update_worker(worker_id: int, data: Dict) -> Dict:
    response = supabase.table('workers').update(data).eq('id', worker_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]


def delete_worker(worker_id: int) -> None:
    response = supabase.table('workers').delete().eq('id', worker_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return None


def login_worker(name: str, pin: str) -> dict:
    response = supabase.table('workers').select('*').eq('name', name).eq('pin', pin).single().execute()
    if hasattr(response, 'error') and response.error or not response.data:
        raise Exception('Invalid credentials')
    return response.data
