from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
from db_cofig import supabase

router = APIRouter()

class WorkerCreate(BaseModel):
    name: str
    team_id: Optional[int] = None
    pin: str
    voice_ref: Optional[str] = None
    role: Optional[str] = 'picker'

class WorkerOut(BaseModel):
    id: int
    name: str
    team_id: Optional[int]
    pin: str
    voice_ref: Optional[str]
    status: str
    role: str
    created_at: Optional[str]
    updated_at: Optional[str]

@router.post('/workers', response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def create_worker(worker: WorkerCreate):
    data = worker.dict()
    data['status'] = 'active'
    response = supabase.table('workers').insert(data).execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data[0]

@router.get('/workers', response_model=List[WorkerOut])
def get_workers():
    response = supabase.table('workers').select('*').execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data

@router.get('/workers/{worker_id}', response_model=WorkerOut)
def get_worker(worker_id: int):
    response = supabase.table('workers').select('*').eq('id', worker_id).single().execute()
    if response.error:
        raise HTTPException(status_code=404, detail='Worker not found')
    return response.data

@router.patch('/workers/{worker_id}', response_model=WorkerOut)
def update_worker(worker_id: int, worker: WorkerCreate):
    data = worker.dict(exclude_unset=True)
    response = supabase.table('workers').update(data).eq('id', worker_id).execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data[0]

@router.delete('/workers/{worker_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int):
    response = supabase.table('workers').delete().eq('id', worker_id).execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return None
