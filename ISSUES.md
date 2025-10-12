# Database Schema and Seeding Issues

## Summary
After implementing the flexible warehouse configuration system, we're encountering several database-related issues that prevent the seeding script from working properly.

## Issues Encountered

### 1. Database Schema Mismatch
**Problem**: The `pick_locations` table schema doesn't match what the seeding script expects.

**Error Message**: 
```
'current_quantity' column of 'pick_locations' in the schema cache", 'code': 'PGRST204'
```

**Details**: 
- The seeding script tries to insert `current_quantity` field
- The actual `pick_locations` table likely has `current_occupancy` instead
- Need to align the seeding script with the actual database schema

### 2. Missing Python Dependencies
**Problem**: Required packages not installed in virtual environment.

**Missing packages**:
- `python-dotenv` 
- `supabase`
- Previously had SQLAlchemy imports that weren't needed

**Impact**: Cannot run database operations or seeding scripts.

### 3. User Creation Functionality
**Problem**: User creation is being skipped in seeding script.

**Current behavior**: 
- Script assumes `users` table doesn't exist
- Users creation is commented out with "users table not found"
- Need to verify if users table exists and fix user creation

### 4. Template Data Format Issues (Resolved)
**Problem**: Template data format mismatch between database storage and parsing logic.

**Solution applied**: 
- Fixed `level_names` array to dictionary conversion in `WarehouseTemplateManager._create_sections_from_template()`
- Added proper error handling for database operations

## Files Affected

### New Files Created:
- `database/warehouse_config_schema.sql` - Complete schema for flexible warehouses
- `modules/warehouse_templates.py` - Template management system
- `modules/location_utils_dynamic.py` - Configuration-driven location utilities  
- `api/warehouse_designer_routes.py` - REST API endpoints
- `check_db_status.py` - Database state checker

### Modified Files:
- `database/seed_data.py` - Updated for dynamic location generation
- `database/db_cofig.py` - Had unused SQLAlchemy imports

## Recommended Next Steps

### Immediate Actions:
1. **Install missing dependencies**:
   ```bash
   pip install python-dotenv supabase
   ```

2. **Database schema audit**:
   - Check current Supabase table schemas
   - Identify mismatches with seeding script expectations
   - Consider fresh database setup vs. incremental fixes

3. **Fix seeding script**:
   - Align `pick_locations` insertion with actual schema
   - Verify and fix user creation functionality
   - Test database connection and operations

### Decision Point: Database Strategy
**Option A: Fresh Start (Recommended)**
- Delete all tables in Supabase
- Run all SQL scripts fresh for clean schema
- Ensures consistency across all tables

**Option B: Incremental Fix**
- Audit each table schema individually
- Fix only problematic tables
- Risk of lingering inconsistencies

## System Architecture Implemented

The flexible warehouse system now supports:
- ✅ Any warehouse layout through templates
- ✅ Database-driven location validation  
- ✅ Template import/export functionality
- ✅ REST API for warehouse management
- ✅ Multi-level, multi-section configurations
- ✅ Equipment and complexity specifications

## Test Data Requirements

When seeding is working, the system will generate:
- Warehouse configurations based on templates
- Thousands of location codes following patterns
- Zone mappings for each section
- Sample inventory and orders
- User accounts with proper roles

## Environment Setup Checklist

- [ ] Virtual environment activated
- [ ] Python dependencies installed (`supabase`, `python-dotenv`)
- [ ] `.env` file with Supabase credentials
- [ ] Database schema aligned with code expectations
- [ ] Seeding script tested and working

---

**Priority**: High - Blocking further development and testing
**Complexity**: Medium - Mostly configuration and schema alignment
**Estimated Time**: 2-3 hours to resolve all issues