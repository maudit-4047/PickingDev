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
