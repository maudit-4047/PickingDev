# 🚀 Quick Start Guide - VoicePicker Backend

## What You Have Built

A complete warehouse management backend with:
- ✅ Enterprise auth (Argon2, 2FA/TOTP, backup codes, rate limiting)
- ✅ Role-based work queue (PIN assignment for picker/packer/receiver roles)
- ✅ Full warehouse operations (inventory, orders, locations, dispatch)
- ✅ Comprehensive API docs and database schemas

---

## Database Setup Status

### ✅ Already in Supabase:
- `workers` table (with `pin`, `role`, `name` - perfect for PIN-based assignment!)
- `orders`, `order_items`, `inventory`, `locations`, `pick_locations`
- `users` (admin auth with 2FA fields)
- `shifts`, `breaks`, `delays`, `picker_performance`
- Full warehouse designer tables (sections, aisles, levels, zones)

### ⚠️ Need to Add:
- `work_queue` table (role-based with worker_pin)
- `work_assignments` table
- `work_queue_history` table (audit trail)

**Action Required:**
Run `backend/database/work_queue_schema.sql` in Supabase SQL Editor to create these tables.

---

## Quick Start (5 minutes)

### 1. Activate Environment
```cmd
cd c:\Users\awad\Desktop\PickingDev\projects\voicepicker
venv\Scripts\activate
```

### 2. Verify Environment Variables
Make sure you have (in `.env` or system environment):
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Run Work Queue Schema
- Open Supabase SQL Editor
- Copy/paste contents of `backend/database/work_queue_schema.sql`
- Execute

### 4. Start API Server
```cmd
python backend\api\main.py
```

Server will start on: http://localhost:8000
Swagger docs: http://localhost:8000/docs

---

## Testing Path (via Swagger UI)

### Phase 1: Auth (5 min)
1. **POST /auth/register**
   ```json
   {
     "username": "admin",
     "email": "admin@warehouse.com",
     "password": "SecurePass123!@#"
   }
   ```

2. **POST /auth/login**
   ```json
   {
     "username": "admin",
     "password": "SecurePass123!@#"
   }
   ```
   → Copy the `access_token` from response

3. **Click "Authorize" button** in Swagger
   - Paste token: `Bearer <your_access_token>`
   - Now you can test protected endpoints!

### Phase 2: Work Queue - Role-Based (10 min)

**Prerequisites:** Ensure you have at least one worker with PIN in database.

4. **Check existing workers:**
   - Query Supabase: `SELECT * FROM workers;`
   - Note a worker's PIN and role (e.g., PIN=1234, role='picker')

5. **POST /work-queue** - Create a task
   ```json
   {
     "task_type": "picking",
     "order_id": 1,
     "required_role": "picker",
     "item_code": "ITEM001",
     "location_code": "A1-001",
     "quantity_requested": 10,
     "priority": 1,
     "notes": "Test task"
   }
   ```

6. **GET /work-queue/by-role/picker**
   - Should show the task you just created

7. **POST /work-queue/assign** - Assign to worker
   ```json
   {
     "work_queue_id": 1,
     "worker_pin": 1234
   }
   ```

8. **POST /work-queue/start** - Start working
   ```json
   {
     "work_queue_id": 1,
     "worker_pin": 1234
   }
   ```

9. **POST /work-queue/complete** - Complete task
   ```json
   {
     "work_queue_id": 1,
     "worker_pin": 1234,
     "items_picked": 10,
     "notes": "All done!"
   }
   ```

10. **GET /work-queue/stats**
    - See counts by status

### Phase 3: Other Modules (as needed)
- Inventory: `/inventory/items`
- Orders: `/orders`
- Locations: `/locations`
- Warehouse Designer: `/warehouse-designer/layouts`

---

## Key API Endpoints by Category

### 🔐 Auth
- POST `/auth/register` - Create admin user
- POST `/auth/login` - Get token
- POST `/auth/setup-2fa` - Enable 2FA
- POST `/auth/verify-2fa` - Verify TOTP code

### 📦 Work Queue (Role-Based, PIN-Tracked)
- GET `/work-queue` - List tasks (filter by role, PIN, status)
- POST `/work-queue` - Create task (requires `required_role`)
- GET `/work-queue/by-role/{role}` - Tasks for specific role
- GET `/work-queue/next/{worker_pin}` - Auto-assign next task
- GET `/work-queue/worker/{worker_pin}` - Worker's current tasks
- POST `/work-queue/assign` - Assign task to PIN
- POST `/work-queue/start` - Start task
- POST `/work-queue/complete` - Complete task
- GET `/work-queue/stats` - Queue statistics

### 📋 Inventory
- GET/POST `/inventory/items`
- POST `/inventory/adjust` - Stock adjustment
- POST `/inventory/move` - Move between locations

### 🛒 Orders
- GET/POST `/orders`
- POST `/orders/{id}/pick` - Create pick tasks
- POST `/orders/{id}/complete`

### 🏗️ Warehouse Designer
- GET/POST `/warehouse-designer/layouts`
- GET/POST `/warehouse-designer/zones`

---

## Troubleshooting

### Can't connect to database?
- Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Verify Supabase project is active

### 401 Unauthorized?
- Make sure you clicked "Authorize" in Swagger with Bearer token
- Token format: `Bearer <token>` (note the space)

### 404 on work queue endpoints?
- Run `work_queue_schema.sql` in Supabase first
- Check that tables were created: `SELECT * FROM work_queue;`

### Worker PIN not found?
- Insert test worker: 
  ```sql
  INSERT INTO workers (name, pin, role, status) 
  VALUES ('Test Picker', 1234, 'picker', 'active');
  ```

---

## Next Steps Options

1. **Test everything** - Go through all API endpoints systematically
2. **Build PO module** - Implement purchase order management we designed
3. **Add Blue Yonder integration** - Connect to existing WMS
4. **Deploy** - Containerize with Docker and deploy to cloud
5. **Build frontend** - React/Vue dashboard for visual management

---

## Useful Files

- **API Guide**: `docs/api/COMPREHENSIVE_API_GUIDE.md`
- **PO Design**: `docs/api/PO_MANAGEMENT_DESIGN.md`
- **Schemas**: `backend/database/*.sql`
- **Main App**: `backend/api/main.py`
- **Work Queue Logic**: `backend/modules/work_queue.py`

---

Ready to test! Start with auth, then move to work queue role-based assignment. 🚀
