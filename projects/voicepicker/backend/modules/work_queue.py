from typing import Optional, List, Dict
from database.db_cofig import supabase
from datetime import datetime

# Work Queue Management Module

def create_work_task(data: Dict) -> Dict:
    """Create a new work task in the queue"""
    # Set default values
    data['status'] = 'pending'
    data['created_at'] = datetime.now().isoformat()
    data['updated_at'] = datetime.now().isoformat()
    
    response = supabase.table('work_queue').insert(data).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data[0]

def get_work_queue(worker_id: int = None, status: str = None, priority_order: bool = True) -> List[Dict]:
    """Get work queue items, optionally filtered by worker or status"""
    query = supabase.table('work_queue').select('*')
    
    if worker_id is not None:
        query = query.eq('worker_id', worker_id)
    if status is not None:
        query = query.eq('status', status)
    
    # Order by priority (1=highest) then by created time
    if priority_order:
        query = query.order('priority').order('created_at')
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def assign_work_to_worker(work_queue_id: int, worker_id: int) -> Dict:
    """Assign a work task to a worker"""
    # Update work queue item
    update_data = {
        'worker_id': worker_id,
        'status': 'assigned',
        'assigned_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    response = supabase.table('work_queue').update(update_data).eq('id', work_queue_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Create work assignment record
    assignment_data = {
        'worker_id': worker_id,
        'work_queue_id': work_queue_id,
        'status': 'active'
    }
    
    assignment_response = supabase.table('work_assignments').insert(assignment_data).execute()
    if hasattr(assignment_response, 'error') and assignment_response.error:
        raise Exception(assignment_response.error.message)
    
    # Log the action
    log_work_action(work_queue_id, worker_id, 'assigned', 'pending', 'assigned')
    
    return response.data[0]

def start_work_task(work_queue_id: int, worker_id: int) -> Dict:
    """Mark a work task as started"""
    update_data = {
        'status': 'picking',
        'started_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    response = supabase.table('work_queue').update(update_data).eq('id', work_queue_id).eq('worker_id', worker_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Log the action
    log_work_action(work_queue_id, worker_id, 'started', 'assigned', 'picking')
    
    return response.data[0]

def complete_work_task(work_queue_id: int, worker_id: int, quantity_picked: int, notes: str = None) -> Dict:
    """Complete a work task"""
    # Calculate actual time if started_at exists
    work_item = supabase.table('work_queue').select('*').eq('id', work_queue_id).single().execute()
    if hasattr(work_item, 'error') and work_item.error:
        raise Exception('Work item not found')
    
    actual_time = 0
    if work_item.data.get('started_at'):
        start_time = datetime.fromisoformat(work_item.data['started_at'])
        actual_time = int((datetime.now() - start_time).total_seconds())
    
    update_data = {
        'status': 'completed',
        'quantity_picked': quantity_picked,
        'completed_at': datetime.now().isoformat(),
        'actual_time': actual_time,
        'updated_at': datetime.now().isoformat()
    }
    
    if notes:
        update_data['notes'] = notes
    
    response = supabase.table('work_queue').update(update_data).eq('id', work_queue_id).eq('worker_id', worker_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Update work assignment to completed
    supabase.table('work_assignments').update({'status': 'completed'}).eq('work_queue_id', work_queue_id).eq('worker_id', worker_id).execute()
    
    # Log the action
    log_work_action(work_queue_id, worker_id, 'completed', 'picking', 'completed', 
                   work_item.data.get('quantity_picked', 0), quantity_picked)
    
    return response.data[0]

def get_next_work_for_worker(worker_id: int) -> Optional[Dict]:
    """Get the next highest priority work item for a worker"""
    # First check if worker has any assigned work
    assigned_work = get_work_queue(worker_id=worker_id, status='assigned')
    if assigned_work:
        return assigned_work[0]
    
    # Get next unassigned work by priority
    unassigned_work = get_work_queue(status='pending')
    if unassigned_work:
        # Auto-assign the first one
        next_work = unassigned_work[0]
        return assign_work_to_worker(next_work['id'], worker_id)
    
    return None

def get_worker_current_work(worker_id: int) -> List[Dict]:
    """Get all current work items for a worker"""
    statuses = ['assigned', 'picking']
    query = supabase.table('work_queue').select('*').eq('worker_id', worker_id).in_('status', statuses)
    
    response = query.execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def log_work_action(work_queue_id: int, worker_id: int, action: str, old_status: str = None, 
                   new_status: str = None, quantity_before: int = None, quantity_after: int = None, notes: str = None):
    """Log work queue actions for audit trail"""
    log_data = {
        'work_queue_id': work_queue_id,
        'worker_id': worker_id,
        'action': action,
        'old_status': old_status,
        'new_status': new_status,
        'quantity_before': quantity_before,
        'quantity_after': quantity_after,
        'notes': notes,
        'created_at': datetime.now().isoformat()
    }
    
    # Remove None values
    log_data = {k: v for k, v in log_data.items() if v is not None}
    
    response = supabase.table('work_queue_history').insert(log_data).execute()
    if hasattr(response, 'error') and response.error:
        print(f"Warning: Failed to log work action: {response.error.message}")

def cancel_work_task(work_queue_id: int, reason: str = None) -> Dict:
    """Cancel a work task"""
    update_data = {
        'status': 'cancelled',
        'updated_at': datetime.now().isoformat()
    }
    
    if reason:
        update_data['notes'] = reason
    
    response = supabase.table('work_queue').update(update_data).eq('id', work_queue_id).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    
    # Update any active assignments
    supabase.table('work_assignments').update({'status': 'completed'}).eq('work_queue_id', work_queue_id).execute()
    
    return response.data[0]

def get_work_queue_stats() -> Dict:
    """Get work queue statistics"""
    # Count by status
    pending = supabase.table('work_queue').select('id', count='exact').eq('status', 'pending').execute()
    assigned = supabase.table('work_queue').select('id', count='exact').eq('status', 'assigned').execute()
    picking = supabase.table('work_queue').select('id', count='exact').eq('status', 'picking').execute()
    completed = supabase.table('work_queue').select('id', count='exact').eq('status', 'completed').execute()
    
    return {
        'pending': pending.count or 0,
        'assigned': assigned.count or 0,
        'picking': picking.count or 0,
        'completed': completed.count or 0,
        'total': (pending.count or 0) + (assigned.count or 0) + (picking.count or 0) + (completed.count or 0)
    }