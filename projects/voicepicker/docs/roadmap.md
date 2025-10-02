
# Project Folder Structure

```text
voicepicker-ai/
├── backend/
│   ├── database/
│   │   ├── auth_schema.sql
│   │   ├── inventory_schema.sql
│   │   ├── orders_schema.sql
│   │   ├── dispatch_schema.sql     
│   │   ├── init_db.sql
│   │   └── db_config.py
│   │
│   ├── modules/
│   │   ├── auth.py
│   │   ├── inventory.py
│   │   ├── orders.py
│   │   ├── dispatch.py             
│   │   └── utils.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── auth_routes.py
│   │   ├── inventory_routes.py
│   │   ├── order_routes.py
│   │   └── dispatch_routes.py      
│   │
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_inventory.py
│   │   ├── test_orders.py
│   │   └── test_dispatch.py        
│   │
│   └── requirements.txt
│
├── picker-interface/
│   ├── login_flow.py
│   ├── job_flow.py
│   ├── stt_tts.py
│   └── pallet_confirm.py           
│
├── dashboard/
│   ├── pages/index.js
│   ├── pages/team.js
│   ├── pages/orders.js
│   ├── pages/inventory.js
│   └── pages/dispatch.js           
│
├── docs/
│   ├── roadmap.md
│   ├── schema_diagram.png
│   └── api_docs.md
│
└── README.md
```

# Modular Database Schema Plan (SAP EWM-aligned, Expandable)

## Core Tables (for Voice Picker MVP)
- **workers**: picker details (id, name, role, team, pin, voice_ref, status, timestamps)
- **shifts**: shift records (worker, start/end, type)
- **breaks**: break logs (shift, start/end, type)
- **tasks**: picking tasks (worker, type, order/item/location, status, timestamps, confirmation, exceptions)
- **delays**: delay logs (worker, shift, type, start/end, approval, notes)
- **picker_performance**: metrics (worker, shift, total picks, avg pick time, errors, insufficient stock count, break/delay time, last pick)

## Inventory & Order Management (for future expansion)
- **inventory**: item/location/quantity tracking
- **locations**: bin/zone/dock definitions
- **orders**: order headers (customer, status, timestamps)
- **order_items**: order line items (order, item, qty, picked qty, status)

## Multi-Role Support (future)
- Add new roles to `workers` (forklift, loader, cycle_counter, etc.)
- Create role-specific activity tables (e.g., `forklift_activity`, `loader_activity`, `cycle_count_activity`)

## Best Practices
- Modular, normalized tables for easy expansion
- Track all actions, confirmations, exceptions, and approvals
- Aligns with SAP EWM structure for industry compatibility

> Start with voice picker tables and logic. Expand to other roles/functions as you learn more from real warehouse operations.





