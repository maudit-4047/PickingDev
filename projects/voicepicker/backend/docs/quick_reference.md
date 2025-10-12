# VoicePicker Quick Reference Guide

## 🚀 Server Setup
```bash
cd c:\Users\azwad\Documents\PickingDev\projects\voicepicker\backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`

## 🎯 Key Endpoints by Feature

### Authentication & Workers
```bash
POST /workers                    # Create worker
GET  /workers                    # List workers  
POST /login                      # Worker login
GET  /workers/{id}               # Get worker by ID
GET  /workers/pin/{pin}          # Get worker by PIN
```

### Work Queue (Task Management)
```bash
POST /work-queue                 # Create work task
GET  /work-queue                 # List work tasks (with filters)
POST /work-queue/assign          # Assign task to worker
POST /work-queue/start           # Start working on task
POST /work-queue/complete        # Complete task
GET  /work-queue/next/{worker_id} # Get next task for worker
GET  /work-queue/stats           # Queue statistics
```

### Pick Locations
```bash
GET  /locations                  # List all locations
GET  /locations/{location_code}  # Get specific location (e.g., LA01)
GET  /locations/aisle/{aisle}    # Get locations by aisle (A, B, C, D)
GET  /locations/search/{term}    # Search locations
POST /locations/inventory/update # Update location inventory
GET  /locations/activity         # Location activity history
POST /locations/issues           # Report location issues
```

### Warehouse Designer  
```bash
POST /warehouse-designer/templates/{name}    # Create from template
POST /warehouse-designer/create              # Create custom warehouse
POST /warehouse-designer/validate            # Validate design
POST /warehouse-designer/preview             # Preview design
GET  /warehouse-designer/layout              # View current layout
GET  /warehouse-designer/export              # Export as JSON
```

## 🏗️ Warehouse Templates
- `small_warehouse` - 2 aisles, basic layout (16 locations)
- `medium_warehouse` - 4 aisles A-D, 5 bays each (120 locations)  
- `large_warehouse` - 6 aisles A-F, 10 bays each (480 locations)

## 📋 Work Task Status Flow
```
pending → assigned → picking → completed
     ↓        ↓         ↓
  cancelled cancelled cancelled
```

## 📍 Location Code Examples
- **LA01** = Aisle L, Bay A, Position 01
- **BIN-A-1-LEFT** = Custom naming scheme
- **PICK-001** = Sequential numbering
- **A01-1-A** = Aisle A, Bay 01, Level 1, Position A

## 🔧 Environment Setup
Create `.env` file in backend directory:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

## 📊 Database Tables Created
- `workers`, `teams` - Worker management
- `work_queue`, `work_assignments`, `work_queue_history` - Task management
- `location_zones`, `pick_locations`, `location_inventory` - Location management
- `location_activity`, `location_issues` - Activity tracking
- `system_config` - Configuration

## 🧪 Quick Test Commands

### Create Worker & Work Flow
```bash
# Create worker
curl -X POST "http://localhost:8000/workers" -H "Content-Type: application/json" -d '{"name": "Test Worker", "pin": 1234}'

# Create warehouse from template
curl -X POST "http://localhost:8000/warehouse-designer/templates/small_warehouse"

# Create work task
curl -X POST "http://localhost:8000/work-queue" -H "Content-Type: application/json" -d '{"item_code": "ITEM001", "location_code": "A011A", "quantity_requested": 10}'

# Get next work for worker  
curl -X GET "http://localhost:8000/work-queue/next/1"

# Complete workflow
curl -X POST "http://localhost:8000/work-queue/start" -H "Content-Type: application/json" -d '{"work_queue_id": 1, "worker_id": 1}'
curl -X POST "http://localhost:8000/work-queue/complete" -H "Content-Type: application/json" -d '{"work_queue_id": 1, "worker_id": 1, "quantity_picked": 10}'
```

### Location Management
```bash
# View all locations
curl -X GET "http://localhost:8000/locations"

# Get locations in aisle A
curl -X GET "http://localhost:8000/locations/aisle/A"

# Update inventory (simulate pick)
curl -X POST "http://localhost:8000/locations/inventory/update" -H "Content-Type: application/json" -d '{"location_code": "A011A", "item_code": "ITEM001", "quantity_change": -5, "activity_type": "pick", "worker_id": 1}'
```

## 💡 Development Tips
1. **Always use interactive docs** at `/docs` for testing
2. **Validate warehouse designs** before creating them
3. **Check work queue stats** to monitor system load
4. **Use location search** to find specific areas
5. **Track activity logs** for debugging and auditing
6. **Export warehouse designs** for backup/sharing

## 🎯 Real Warehouse Integration
- Use exact location codes from your workplace
- Configure zones to match your warehouse layout  
- Set realistic capacities and access equipment types
- Use priority levels (1=urgent, 10=low) for task management
- Track performance metrics for productivity analysis

---
*Last updated: October 12, 2025 - Session commit ef57d73*