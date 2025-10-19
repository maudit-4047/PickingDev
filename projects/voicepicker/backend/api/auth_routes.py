from fastapi import APIRouter, HTTPException, status, Body, Query
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.auth import create_worker as create_worker_logic, get_workers as get_workers_logic, get_worker as get_worker_logic, update_worker as update_worker_logic, delete_worker as delete_worker_logic, login_worker as login_worker_logic

router = APIRouter()

class WorkerCreate(BaseModel):
    name: str
    team_id: Optional[int] = None
    pin: int
    voice_ref: Optional[str] = None
    role: Optional[str] = 'picker'

class WorkerOut(BaseModel):
    id: int
    name: str
    team_id: Optional[int]
    pin: int
    voice_ref: Optional[str]
    status: str
    role: str
    created_at: Optional[str]
    updated_at: Optional[str]

class LoginRequest(BaseModel):
    name: str
    pin: int

class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    team_id: Optional[int] = None
    pin: Optional[int] = None
    voice_ref: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

@router.post('/workers', response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def create_worker(worker: WorkerCreate):
    try:
        return create_worker_logic(worker.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/workers', response_model=List[WorkerOut])
def get_workers(team_id: Optional[int] = Query(None)):
    try:
        if team_id is not None:
            return get_workers_logic(team_id=team_id)
        return get_workers_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/workers/{worker_id}', response_model=WorkerOut)
def get_worker(worker_id: int):
    try:
        return get_worker_logic(worker_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch('/workers/{worker_id}', response_model=WorkerOut)
def update_worker(worker_id: int, worker: WorkerUpdate):
    try:
        return update_worker_logic(worker_id, worker.dict(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete('/workers/{worker_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int):
    try:
        delete_worker_logic(worker_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/login')
def login(request: LoginRequest = Body(...)):
    try:
        token = login_worker_logic(request.name, request.pin)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get('/workers/pin/{pin}', response_model=WorkerOut)
def get_worker_by_pin(pin: int):
    try:
        return get_worker_logic(pin=pin)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch('/workers/pin/{pin}', response_model=WorkerOut)
def update_worker_by_pin(pin: int, worker: WorkerUpdate):
    try:
        return update_worker_logic(pin=pin, data=worker.dict(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete('/workers/pin/{pin}', status_code=status.HTTP_204_NO_CONTENT)
def delete_worker_by_pin(pin: int):
    try:
        delete_worker_logic(pin=pin)
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
