from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from work_queue import (
    create_work_task as create_work_task_logic,
    get_work_queue as get_work_queue_logic,
    assign_work_to_worker as assign_work_logic,
    start_work_task as start_work_logic,
    complete_work_task as complete_work_logic,
    get_next_work_for_worker as get_next_work_logic,
    get_worker_current_work as get_current_work_logic,
    cancel_work_task as cancel_work_logic,
    get_work_queue_stats as get_stats_logic,
    get_work_by_role as get_work_by_role_logic
)

router = APIRouter()

class WorkTaskCreate(BaseModel):
    order_id: Optional[int] = None
    item_code: str
    location_code: str
    quantity_requested: int
    priority: Optional[int] = 5
    task_type: Optional[str] = 'pick'
    required_role: Optional[str] = 'picker'  # Role required for this task
    estimated_time: Optional[int] = 0
    notes: Optional[str] = None

class WorkTaskOut(BaseModel):
    id: int
    order_id: Optional[int]
    worker_pin: Optional[int]  # Use PIN instead of worker_id
    worker_name: Optional[str]  # Include worker name for display
    item_code: str
    location_code: str
    quantity_requested: int
    quantity_picked: int
    priority: int
    status: str
    task_type: str
    required_role: Optional[str]  # Role required for this task
    assigned_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_time: int
    actual_time: int
    notes: Optional[str]
    created_at: str
    updated_at: str

class WorkAssignment(BaseModel):
    work_queue_id: int
    worker_pin: int  # Use PIN instead of worker_id

class WorkCompletion(BaseModel):
    work_queue_id: int
    worker_pin: int  # Use PIN instead of worker_id
    quantity_picked: int
    notes: Optional[str] = None

class WorkByRole(BaseModel):
    role: str  # Get work for specific role (picker, packer, etc.)

class WorkStats(BaseModel):
    pending: int
    assigned: int
    picking: int
    completed: int
    total: int

# Create work task
@router.post('/work-queue', response_model=WorkTaskOut, status_code=status.HTTP_201_CREATED)
def create_work_task(task: WorkTaskCreate):
    """Create a new work task in the queue"""
    try:
        return create_work_task_logic(task.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get work queue
@router.get('/work-queue', response_model=List[WorkTaskOut])
def get_work_queue(
    worker_pin: Optional[int] = Query(None, description="Filter by worker PIN"),
    role: Optional[str] = Query(None, description="Filter by required role (picker, packer, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (pending, assigned, picking, completed)"),
    priority_order: bool = Query(True, description="Order by priority")
):
    """Get work queue items with optional filters"""
    try:
        return get_work_queue_logic(worker_pin=worker_pin, role=role, status=status, priority_order=priority_order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Assign work to worker
@router.post('/work-queue/assign', response_model=WorkTaskOut)
def assign_work_to_worker(assignment: WorkAssignment):
    """Assign a work task to a worker"""
    try:
        return assign_work_logic(assignment.work_queue_id, assignment.worker_pin)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Start work task
@router.post('/work-queue/start', response_model=WorkTaskOut)
def start_work_task(assignment: WorkAssignment):
    """Start working on an assigned task"""
    try:
        return start_work_logic(assignment.work_queue_id, assignment.worker_pin)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Complete work task
@router.post('/work-queue/complete', response_model=WorkTaskOut)
def complete_work_task(completion: WorkCompletion):
    """Complete a work task"""
    try:
        return complete_work_logic(
            completion.work_queue_id, 
            completion.worker_pin, 
            completion.items_picked, 
            completion.notes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get work by role
@router.get('/work-queue/by-role/{role}', response_model=List[WorkTaskOut])
def get_work_by_role(role: str, priority_order: bool = Query(True)):
    """Get available work tasks for a specific role"""
    try:
        return get_work_by_role_logic(role=role, priority_order=priority_order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get next work for worker
@router.get('/work-queue/next/{worker_pin}', response_model=Optional[WorkTaskOut])
def get_next_work_for_worker(worker_pin: int):
    """Get the next work task for a worker (auto-assigns if available)"""
    try:
        result = get_next_work_logic(worker_pin)
        if result is None:
            raise HTTPException(status_code=404, detail="No work available")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get worker's current work
@router.get('/work-queue/worker/{worker_pin}', response_model=List[WorkTaskOut])
def get_worker_current_work(worker_pin: int):
    """Get all current work items for a worker"""
    try:
        return get_current_work_logic(worker_pin)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Cancel work task
@router.patch('/work-queue/{work_queue_id}/cancel', response_model=WorkTaskOut)
def cancel_work_task(work_queue_id: int, reason: Optional[str] = Query(None, description="Cancellation reason")):
    """Cancel a work task"""
    try:
        return cancel_work_logic(work_queue_id, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get work queue statistics
@router.get('/work-queue/stats', response_model=WorkStats)
def get_work_queue_stats():
    """Get work queue statistics"""
    try:
        return get_stats_logic()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get work task by ID
@router.get('/work-queue/{work_queue_id}', response_model=WorkTaskOut)
def get_work_task(work_queue_id: int):
    """Get a specific work task by ID"""
    try:
        from work_queue import supabase
        response = supabase.table('work_queue').select('*').eq('id', work_queue_id).single().execute()
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=404, detail="Work task not found")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))