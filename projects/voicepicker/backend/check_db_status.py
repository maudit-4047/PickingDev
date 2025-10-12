import os
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file

# Supabase API config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
from supabase import create_client, Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Checking database status...")
print("=" * 50)

# Check if warehouse config tables exist
try:
    response = supabase.table('warehouse_config').select('*').limit(1).execute()
    if hasattr(response, 'error') and response.error:
        print("❌ Warehouse config tables: NOT CREATED")
        print(f"   Error: {response.error.message}")
    else:
        print("✅ Warehouse config tables: EXIST")
        print(f"   Found {len(response.data)} warehouse configurations")
except Exception as e:
    print(f"❌ Warehouse config tables: ERROR - {str(e)}")

# Check warehouse templates
try:
    response = supabase.table('warehouse_templates').select('*').execute()
    if hasattr(response, 'error') and response.error:
        print("❌ Warehouse templates: NOT CREATED")
        print(f"   Error: {response.error.message}")
    else:
        templates = response.data
        print(f"✅ Warehouse templates: {len(templates)} found")
        for template in templates:
            print(f"   - {template['template_name']}: {template.get('description', 'No description')}")
except Exception as e:
    print(f"❌ Warehouse templates: ERROR - {str(e)}")

# Check existing pick locations
try:
    response = supabase.table('pick_locations').select('*').limit(5).execute()
    if hasattr(response, 'error') and response.error:
        print("❌ Pick locations: ERROR")
        print(f"   Error: {response.error.message}")
    else:
        locations = response.data
        print(f"📦 Pick locations: {len(locations)} found (showing first 5)")
        for loc in locations[:5]:
            print(f"   - {loc.get('location_code', 'NO_CODE')} (Zone: {loc.get('zone_id', 'N/A')})")
except Exception as e:
    print(f"❌ Pick locations: ERROR - {str(e)}")

print("=" * 50)
print("Summary:")
print("To use the flexible warehouse system, you need to:")
print("1. Run warehouse_config_schema.sql in Supabase")
print("2. Run python database/seed_data.py to create templates")