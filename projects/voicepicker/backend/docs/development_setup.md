# VoicePicker Development Setup Guide

## 🖥️ Desktop Setup Instructions

### 1. Clone/Pull Latest Changes

```bash
git clone https://github.com/maudit-4047/PickingDev.git
# OR if already cloned:
git pull origin main
```

### 2. Navigate to Backend

```bash
cd PickingDev/projects/voicepicker/backend
```

### 3. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Mac/Linux
```

### 4. Install Dependencies

```bash
pip install -r req.txt
```

### 5. Setup Environment Variables

Create `.env` file in the backend directory:

```env
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

### 6. Run the Server

```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test the API

- **Interactive Docs:** http://localhost:8000/docs
- **Base API:** http://localhost:8000

## 🗄️ Database Setup (Supabase)

### Create Tables (Run these in Supabase SQL Editor):

1. **System Config & Auth:**

```sql
-- Run: backend/database/system_config.sql
-- Run: backend/database/auth_schema.sql
```

2. **Work Queue System:**

```sql
-- Run: backend/database/work_queue_schema.sql
```

3. **Pick Locations:**

```sql
-- Run: backend/database/pick_locations_schema.sql
```

### Quick Database Test:

```bash
# Create a worker via API
curl -X POST "http://localhost:8000/workers" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Worker", "pin": 1234}'
```

## 🎯 Feature Development Workflow

### Work with Work Queue:

1. Create warehouse layout (use template or custom)
2. Create workers
3. Create work tasks
4. Assign tasks to workers
5. Track completion and performance

### Work with Locations:

1. Design warehouse using designer API
2. Add inventory to locations
3. Create picking tasks
4. Track location activity
5. Report issues

### Work with Warehouse Designer:

1. Use templates for quick setup
2. Create custom designs for specific needs
3. Validate before creating
4. Export/import designs for backup

## 🧪 Testing Endpoints

### Use Postman Collection (Import this):

```json
{
  "info": { "name": "VoicePicker API" },
  "item": [
    {
      "name": "Create Worker",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/workers",
        "body": {
          "raw": "{\"name\": \"John Doe\", \"pin\": 1234}",
          "options": { "raw": { "language": "json" } }
        }
      }
    },
    {
      "name": "Create Warehouse Template",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/warehouse-designer/templates/small_warehouse"
      }
    }
  ],
  "variable": [{ "key": "base_url", "value": "http://localhost:8000" }]
}
```

## 📁 Project Structure Understanding

```
backend/
├── api/                     # FastAPI routes
│   ├── main.py             # Main app with router includes
│   ├── auth_routes.py      # Worker authentication
│   ├── work_queue_routes.py # Task management
│   ├── pick_locations_routes.py # Location management
│   └── warehouse_designer_routes.py # Warehouse design
├── database/               # Database schemas
│   ├── auth_schema.sql     # Workers and teams
│   ├── work_queue_schema.sql # Work tasks and assignments
│   ├── pick_locations_schema.sql # Locations and inventory
│   └── system_config.sql   # Configuration
├── modules/                # Business logic
│   ├── auth.py            # Worker management logic
│   ├── work_queue.py      # Task management logic
│   ├── pick_locations.py  # Location management logic
│   └── warehouse_designer.py # Warehouse design logic
└── docs/                  # Documentation
    ├── api_docs.md        # Complete API documentation
    └── quick_reference.md # Quick reference guide
```

## 🔧 Development Tips

### Debugging:

- Use `--reload` flag for auto-restart on code changes
- Check logs in terminal for errors
- Use interactive docs at `/docs` for testing
- Validate data with Pydantic models

### Database Work:

- Use Supabase dashboard for data viewing
- Test queries in Supabase SQL editor
- Check foreign key constraints
- Monitor API response times

### API Development:

- Follow FastAPI patterns established in existing routes
- Use proper HTTP status codes
- Include comprehensive error handling
- Document new endpoints in api_docs.md

## 🚀 Next Development Areas

### High Priority:

1. **Voice Interface** - Implement speech-to-text/text-to-speech
2. **Performance Dashboard** - Worker and system metrics
3. **Order Management** - Full order processing workflow
4. **Mobile Interface** - Worker mobile app

### Medium Priority:

1. **Real-time Updates** - WebSocket connections
2. **Reporting System** - Advanced analytics
3. **Integration APIs** - SAP/ERP connections
4. **Security Enhancements** - JWT tokens, permissions

### Low Priority:

1. **Multi-language Support** - Internationalization
2. **Themes/Customization** - UI customization
3. **Advanced Routing** - Pick path optimization
4. **IoT Integration** - Sensor data integration

---

**Last Updated:** October 12, 2025  
**Commit:** ef57d73  
**Author:** VoicePicker Development Team
