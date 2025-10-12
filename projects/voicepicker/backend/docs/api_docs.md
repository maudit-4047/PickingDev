# VoicePicker API Documentation

> **Base URL:** `http://localhost:8000`  
> **Interactive Docs:** `http://localhost:8000/docs`

## 🔐 Authentication & Workers

### Create Worker

- **POST** `/workers`
- **Body:**
  ```json
  {
    "name": "string",
    "team_id": "int (optional)",
    "pin": "int",
    "voice_ref": "string (optional)",
    "role": "string (optional, default: 'picker')"
  }
  ```
- **Response:** Worker object
- **Description:** Creates a new worker. If `team_id` or `pin` are not provided, they are auto-assigned.

### Get All Workers

- **GET** `/workers?team_id={team_id}`
- **Response:** List of Worker objects
- **Description:** Returns all workers, optionally filtered by team.

### Get Worker by ID

- **GET** `/workers/{worker_id}`
- **Response:** Worker object

### Update Worker by ID

- **PATCH** `/workers/{worker_id}`
- **Body:** Any updatable worker fields
- **Response:** Updated Worker object

### Delete Worker by ID

- **DELETE** `/workers/{worker_id}`
- **Response:** 204 No Content

### Get Worker by Pin

- **GET** `/workers/pin/{pin}`
- **Response:** Worker object

### Update Worker by Pin

- **PATCH** `/workers/pin/{pin}`
- **Body:** Any updatable worker fields
- **Response:** Updated Worker object

### Login

- **POST** `/login`
- **Body:**
  ```json
  {
    "name": "string",
    "pin": "int"
  }
  ```
- **Response:** `{"token": "worker_data"}`

---

## 📋 Work Queue System

### Create Work Task

- **POST** `/work-queue`
- **Body:**
  ```json
  {
    "order_id": "int (optional)",
    "item_code": "string",
    "location_code": "string",
    "quantity_requested": "int",
    "priority": "int (1-10, default: 5)",
    "task_type": "string (default: 'pick')",
    "estimated_time": "int (seconds, default: 0)",
    "notes": "string (optional)"
  }
  ```
- **Response:** Work task object
- **Description:** Creates a new work task in the queue

### Get Work Queue

- **GET** `/work-queue?worker_id={id}&status={status}&priority_order={bool}`
- **Query Parameters:**
  - `worker_id` (optional): Filter by worker ID
  - `status` (optional): Filter by status (pending, assigned, picking, completed)
  - `priority_order` (default: true): Order by priority
- **Response:** List of work task objects

### Assign Work to Worker

- **POST** `/work-queue/assign`
- **Body:**
  ```json
  {
    "work_queue_id": "int",
    "worker_id": "int"
  }
  ```
- **Response:** Updated work task object
- **Description:** Assigns a pending task to a worker

### Start Work Task

- **POST** `/work-queue/start`
- **Body:**
  ```json
  {
    "work_queue_id": "int",
    "worker_id": "int"
  }
  ```
- **Response:** Updated work task object
- **Description:** Marks an assigned task as started (picking)

### Complete Work Task

- **POST** `/work-queue/complete`
- **Body:**
  ```json
  {
    "work_queue_id": "int",
    "worker_id": "int",
    "quantity_picked": "int",
    "notes": "string (optional)"
  }
  ```
- **Response:** Completed work task object
- **Description:** Completes a work task with actual quantity picked

### Get Next Work for Worker

- **GET** `/work-queue/next/{worker_id}`
- **Response:** Work task object or 404 if no work available
- **Description:** Gets and auto-assigns the next highest priority task

### Get Worker's Current Work

- **GET** `/work-queue/worker/{worker_id}`
- **Response:** List of current work tasks (assigned + picking)
- **Description:** Returns all active work for a specific worker

### Cancel Work Task

- **PATCH** `/work-queue/{work_queue_id}/cancel?reason={reason}`
- **Response:** Cancelled work task object
- **Description:** Cancels a work task with optional reason

### Get Work Queue Statistics

- **GET** `/work-queue/stats`
- **Response:**
  ```json
  {
    "pending": "int",
    "assigned": "int",
    "picking": "int",
    "completed": "int",
    "total": "int"
  }
  ```

### Get Work Task by ID

- **GET** `/work-queue/{work_queue_id}`
- **Response:** Work task object

---

## 📍 Pick Locations Management

### Get Location Zones

- **GET** `/locations/zones`
- **Response:** List of location zones
- **Description:** Returns all warehouse zones (PICK, RESERVE, DOCK, etc.)

### Get Pick Locations

- **GET** `/locations?zone_id={id}&aisle={aisle}&is_active={bool}`
- **Query Parameters:**
  - `zone_id` (optional): Filter by zone
  - `aisle` (optional): Filter by aisle (A, B, C, etc.)
  - `is_active` (default: true): Filter by active status
- **Response:** List of pick location objects

### Get Location by Code

- **GET** `/locations/{location_code}`
- **Response:** Pick location object
- **Example:** `GET /locations/LA01`

### Search Locations

- **GET** `/locations/search/{search_term}`
- **Response:** List of matching locations
- **Example:** `GET /locations/search/LA` (finds all LA locations)

### Get Locations by Aisle

- **GET** `/locations/aisle/{aisle}`
- **Response:** List of locations in the aisle
- **Example:** `GET /locations/aisle/A`

### Get Location Inventory

- **GET** `/locations/{location_code}/inventory`
- **Response:** List of items in the location
- **Example:** `GET /locations/LA01/inventory`

### Update Location Inventory

- **POST** `/locations/inventory/update`
- **Body:**
  ```json
  {
    "location_code": "string",
    "item_code": "string",
    "quantity_change": "int (negative for picks)",
    "activity_type": "string (pick, replenish, count, move)",
    "worker_id": "int (optional)",
    "work_queue_id": "int (optional)"
  }
  ```
- **Response:** Updated inventory record
- **Description:** Updates inventory and logs activity

### Get Location Activity

- **GET** `/locations/activity?location_code={code}&worker_id={id}&limit={num}`
- **Query Parameters:**
  - `location_code` (optional): Filter by location
  - `worker_id` (optional): Filter by worker
  - `limit` (default: 50): Limit results
- **Response:** List of location activity records

### Report Location Issue

- **POST** `/locations/issues`
- **Body:**
  ```json
  {
    "location_code": "string",
    "worker_id": "int",
    "issue_type": "string (damage, blocked, unsafe, mislabeled)",
    "description": "string",
    "severity": "string (low, medium, high, critical)"
  }
  ```
- **Response:** Location issue record

### Get Location Issues

- **GET** `/locations/issues?location_code={code}&status={status}`
- **Response:** List of location issues

### Get Location Statistics

- **GET** `/locations/stats`
- **Response:**
  ```json
  {
    "total_locations": "int",
    "occupied_locations": "int",
    "recent_pick_activities": "int",
    "utilization_rate": "float"
  }
  ```

### Get Aisle Summary

- **GET** `/locations/aisles/summary`
- **Response:** List of aisles with location counts

### Find Items in Locations

- **GET** `/locations/items/{item_code}`
- **Response:** List of locations containing the item

---

## 🏗️ Warehouse Designer

### Create Custom Zone

- **POST** `/warehouse-designer/zones`
- **Body:**
  ```json
  {
    "zone_code": "string",
    "zone_name": "string",
    "description": "string (optional)"
  }
  ```
- **Response:** Created zone object

### Create Custom Location

- **POST** `/warehouse-designer/locations`
- **Body:**
  ```json
  {
    "location_code": "string",
    "zone_code": "string",
    "aisle": "string (optional)",
    "bay": "string (optional)",
    "level": "string (optional)",
    "position": "string (optional)",
    "location_type": "string (default: 'pick')",
    "capacity": "int (default: 100)",
    "access_equipment": "string (default: 'manual')",
    "safety_notes": "string (optional)"
  }
  ```

### Validate Warehouse Design

- **POST** `/warehouse-designer/validate`
- **Body:** Warehouse design object (see Create Warehouse)
- **Response:** Validation result with errors/warnings

### Create Warehouse from Design

- **POST** `/warehouse-designer/create`
- **Body:**
  ```json
  {
    "warehouse_name": "string",
    "zones": [
      {
        "zone_code": "string",
        "zone_name": "string",
        "description": "string (optional)"
      }
    ],
    "aisles": [
      {
        "aisle": "string",
        "zone_code": "string",
        "bays": ["string array"],
        "levels": ["string array"],
        "positions": ["string array"],
        "location_type": "string (default: 'pick')",
        "capacity": "int (default: 100)",
        "access_equipment": "string (default: 'manual')"
      }
    ]
  }
  ```
- **Response:** Creation result with counts and created objects

### Create from Template

- **POST** `/warehouse-designer/templates/{template_name}`
- **Templates:** `small_warehouse`, `medium_warehouse`, `large_warehouse`
- **Response:** Creation result

### Get Available Templates

- **GET** `/warehouse-designer/templates`
- **Response:** List of available templates with descriptions

### Get Warehouse Layout

- **GET** `/warehouse-designer/layout`
- **Response:** Current warehouse layout summary

### Update Location Properties

- **PATCH** `/warehouse-designer/locations/{location_code}`
- **Body:**
  ```json
  {
    "capacity": "int (optional)",
    "access_equipment": "string (optional)",
    "safety_notes": "string (optional)",
    "is_active": "bool (optional)",
    "is_pickable": "bool (optional)",
    "location_type": "string (optional)"
  }
  ```

### Delete Warehouse Layout

- **DELETE** `/warehouse-designer/layout?confirm=true`
- **Response:** Deletion summary
- **⚠️ WARNING:** This deletes ALL locations and zones!

### Export Warehouse Design

- **GET** `/warehouse-designer/export`
- **Response:** Complete warehouse design as JSON

### Preview Warehouse Design

- **POST** `/warehouse-designer/preview`
- **Body:** Warehouse design object
- **Response:** Preview of what would be created without actually creating it

---

## 📊 Common Response Formats

### Work Task Object

```json
{
  "id": "int",
  "order_id": "int (optional)",
  "worker_id": "int (optional)",
  "item_code": "string",
  "location_code": "string",
  "quantity_requested": "int",
  "quantity_picked": "int",
  "priority": "int (1-10)",
  "status": "string (pending, assigned, picking, completed, cancelled)",
  "task_type": "string",
  "assigned_at": "timestamp (optional)",
  "started_at": "timestamp (optional)",
  "completed_at": "timestamp (optional)",
  "estimated_time": "int (seconds)",
  "actual_time": "int (seconds)",
  "notes": "string (optional)",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Pick Location Object

```json
{
  "id": "int",
  "location_code": "string",
  "zone_id": "int",
  "aisle": "string",
  "bay": "string",
  "level": "string",
  "position": "string",
  "location_type": "string",
  "capacity": "int",
  "current_occupancy": "int",
  "is_active": "bool",
  "is_pickable": "bool",
  "access_equipment": "string",
  "safety_notes": "string",
  "last_picked_at": "timestamp",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## 🚀 Quick Start Examples

### Create a Worker and Assign Work

```bash
# 1. Create worker
curl -X POST "http://localhost:8000/workers" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Picker", "pin": 1234}'

# 2. Create work task
curl -X POST "http://localhost:8000/work-queue" \
  -H "Content-Type: application/json" \
  -d '{"item_code": "ITEM001", "location_code": "LA01", "quantity_requested": 10, "priority": 1}'

# 3. Get next work for worker
curl -X GET "http://localhost:8000/work-queue/next/1"

# 4. Start the work
curl -X POST "http://localhost:8000/work-queue/start" \
  -H "Content-Type: application/json" \
  -d '{"work_queue_id": 1, "worker_id": 1}'

# 5. Complete the work
curl -X POST "http://localhost:8000/work-queue/complete" \
  -H "Content-Type: application/json" \
  -d '{"work_queue_id": 1, "worker_id": 1, "quantity_picked": 10}'
```

### Design a Small Warehouse

```bash
# Create from template
curl -X POST "http://localhost:8000/warehouse-designer/templates/small_warehouse"

# Or design custom warehouse
curl -X POST "http://localhost:8000/warehouse-designer/create" \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_name": "My Warehouse",
    "zones": [{"zone_code": "PICK", "zone_name": "Pick Area"}],
    "aisles": [{
      "aisle": "A",
      "zone_code": "PICK",
      "bays": ["01", "02"],
      "levels": ["1", "2"],
      "positions": ["A", "B"]
    }]
  }'
```

---

## 🔧 Error Handling

All endpoints return standard HTTP status codes:

- **200**: Success
- **201**: Created
- **204**: No Content (for deletes)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized
- **404**: Not Found
- **500**: Internal Server Error

Error response format:

```json
{
  "detail": "Error message description"
}
```
