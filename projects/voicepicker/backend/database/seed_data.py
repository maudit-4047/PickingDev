"""
Dynamic Database Seeding Script
Generates warehouse configurations and pick locations based on warehouse templates
"""

import sys
import os
from typing import Dict, List, Optional
import random
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_cofig import supabase
from modules.warehouse_templates import WarehouseTemplateManager
from modules.location_utils_dynamic import get_warehouse_config, get_all_locations_for_aisle, generate_check_digit

def create_sample_users():
    """Create sample users for testing"""
    print("Creating sample users...")
    
    users = [
        {
            'username': 'picker1',
            'email': 'picker1@warehouse.com',
            'password_hash': 'hashed_password_123',  # In real app, this would be properly hashed
            'role': 'picker',
            'first_name': 'John',
            'last_name': 'Picker',
            'is_active': True
        },
        {
            'username': 'admin1',
            'email': 'admin1@warehouse.com',
            'password_hash': 'hashed_password_456',
            'role': 'admin',
            'first_name': 'Jane',
            'last_name': 'Admin',
            'is_active': True
        },
        {
            'username': 'supervisor1',
            'email': 'supervisor1@warehouse.com',
            'password_hash': 'hashed_password_789',
            'role': 'supervisor',
            'first_name': 'Bob',
            'last_name': 'Supervisor',
            'is_active': True
        }
    ]
    
    created_users = []
    for user in users:
        try:
            response = supabase.table('users').insert(user).execute()
            if hasattr(response, 'error') and response.error:
                print(f"Error creating user {user['username']}: {response.error.message}")
            else:
                created_users.append(response.data[0])
                print(f"Created user: {user['username']}")
        except Exception as e:
            print(f"Error creating user {user['username']}: {str(e)}")
    
    return created_users

def create_sample_warehouse_from_template(warehouse_name: str = "Sample Warehouse"):
    """Create a sample warehouse from existing template"""
    print(f"Creating warehouse '{warehouse_name}' from existing template...")
    
    try:
        # Get the first available template
        response = supabase.table('warehouse_templates').select('*').limit(1).execute()
        if hasattr(response, 'error') and response.error or not response.data:
            print("No templates found. Using template ID 1 (Multi-Zone Voice Picking Layout)")
            template_id = 1
        else:
            template_id = response.data[0]['id']
            print(f"Using template: {response.data[0]['template_name']}")
        
        template_manager = WarehouseTemplateManager()
        warehouse_id = template_manager.create_warehouse_from_template(template_id, warehouse_name, "system")
        print(f"Created warehouse '{warehouse_name}' with ID: {warehouse_id}")
        return warehouse_id
    except Exception as e:
        print(f"Error creating warehouse from template: {str(e)}")
        return None

def generate_pick_locations_for_warehouse(warehouse_id: int):
    """Generate pick_locations entries for a warehouse based on its configuration"""
    print(f"Generating pick locations for warehouse {warehouse_id}...")
    
    try:
        config = get_warehouse_config(warehouse_id)
        locations_created = 0
        
        # Get or create location zones first
        zones = {}
        for section in config.sections:
            zone_data = {
                'zone_code': section['section_code'],
                'zone_name': section['section_name'],
                'zone_type': 'pick',
                'description': section.get('description', ''),
                'is_active': True
            }
            
            # Check if zone exists
            zone_response = supabase.table('location_zones').select('*').eq('zone_code', zone_data['zone_code']).execute()
            if hasattr(zone_response, 'error') and zone_response.error:
                continue
                
            if zone_response.data:
                zones[section['section_code']] = zone_response.data[0]['id']
            else:
                # Create zone
                create_response = supabase.table('location_zones').insert(zone_data).execute()
                if hasattr(create_response, 'error') and create_response.error:
                    print(f"Error creating zone {zone_data['zone_code']}: {create_response.error.message}")
                    continue
                zones[section['section_code']] = create_response.data[0]['id']
                print(f"Created zone: {zone_data['zone_code']}")
        
        # Generate locations for each section/aisle
        for section in config.sections:
            section_code = section['section_code']
            zone_id = zones.get(section_code)
            
            if not zone_id:
                continue
                
            aisles = config.get_aisles(section['id'])
            
            for aisle in aisles:
                aisle_code = aisle['aisle_code']
                
                # Generate all locations for this aisle
                all_locations = get_all_locations_for_aisle(section_code, aisle_code, warehouse_id)
                
                for location_code in all_locations:
                    # Parse location components
                    try:
                        from modules.location_utils_dynamic import validate_location_code
                        parsed = validate_location_code(location_code, warehouse_id)
                        
                        # Determine capacity and equipment based on level
                        equipment_required = 'manual'
                        capacity = 100
                        
                        if parsed['level'] != '0':
                            # Upper levels typically require equipment
                            levels = config.get_levels(aisle['id'])
                            level_config = next((l for l in levels if l['level_code'] == parsed['level']), None)
                            if level_config:
                                equipment_required = level_config.get('equipment_required', 'manual')
                                # Adjust capacity based on level type
                                if level_config['level_name'].lower().find('case') >= 0:
                                    capacity = 50  # Case levels have less capacity
                                elif level_config['level_name'].lower().find('bin') >= 0:
                                    capacity = 200  # Bin levels have more capacity
                        
                        location_data = {
                            'location_code': location_code,
                            'zone_id': zone_id,
                            'section': section_code,
                            'aisle': aisle_code,
                            'bay': parsed['bay'],
                            'level': parsed['level'],
                            'subsection': parsed.get('subsection'),
                            'location_type': 'pick',
                            'is_complex_aisle': aisle.get('is_complex', False),
                            'capacity': capacity,
                            'current_occupancy': 0,
                            'access_equipment': equipment_required,
                            'check_digit': random.randint(1, 37),
                            'is_active': True,
                            'is_pickable': True
                        }
                        
                        # Insert location
                        response = supabase.table('pick_locations').insert(location_data).execute()
                        if hasattr(response, 'error') and response.error:
                            print(f"Error creating location {location_code}: {response.error.message}")
                        else:
                            locations_created += 1
                            
                    except Exception as e:
                        print(f"Error processing location {location_code}: {str(e)}")
                        continue
                
                print(f"Created {len(all_locations)} locations for aisle {section_code}{aisle_code}")
        
        print(f"Total locations created: {locations_created}")
        return locations_created
        
    except Exception as e:
        print(f"Error generating pick locations: {str(e)}")
        return 0

def create_sample_inventory_items():
    """Create sample inventory items"""
    print("Creating sample inventory items...")
    
    items = [
        {
            'item_code': 'ITEM001',
            'item_name': 'Widget A',
            'description': 'Standard widget type A',
            'category': 'Widgets',
            'unit_of_measure': 'EA',
            'barcode': '123456789012',
            'is_active': True
        },
        {
            'item_code': 'ITEM002',
            'item_name': 'Gadget B',
            'description': 'Premium gadget type B',
            'category': 'Gadgets',
            'unit_of_measure': 'EA',
            'barcode': '123456789013',
            'is_active': True
        },
        {
            'item_code': 'ITEM003',
            'item_name': 'Tool C',
            'description': 'Multi-purpose tool C',
            'category': 'Tools',
            'unit_of_measure': 'EA',
            'barcode': '123456789014',
            'is_active': True
        }
    ]
    
    created_items = []
    for item in items:
        try:
            response = supabase.table('inventory_items').insert(item).execute()
            if hasattr(response, 'error') and response.error:
                print(f"Error creating item {item['item_code']}: {response.error.message}")
            else:
                created_items.append(response.data[0])
                print(f"Created item: {item['item_code']}")
        except Exception as e:
            print(f"Error creating item {item['item_code']}: {str(e)}")
    
    return created_items

def populate_inventory_at_locations(warehouse_id: int, items: List[Dict]):
    """Place inventory items at random locations"""
    print("Populating inventory at locations...")
    
    try:
        # Get all active pick locations
        locations_response = supabase.table('pick_locations').select('*').eq('is_active', True).limit(100).execute()
        if hasattr(locations_response, 'error') and locations_response.error:
            print(f"Error getting locations: {locations_response.error.message}")
            return
        
        locations = locations_response.data
        if not locations:
            print("No locations found to populate")
            return
        
        inventory_records = []
        for item in items:
            # Place each item in 3-5 random locations
            num_locations = random.randint(3, 5)
            selected_locations = random.sample(locations, min(num_locations, len(locations)))
            
            for location in selected_locations:
                quantity = random.randint(10, 200)
                
                inventory_record = {
                    'item_id': item['id'],
                    'location_id': location['id'],
                    'quantity': quantity,
                    'reserved_quantity': 0,
                    'last_updated': datetime.utcnow().isoformat()
                }
                inventory_records.append(inventory_record)
        
        # Bulk insert inventory records
        if inventory_records:
            response = supabase.table('inventory').insert(inventory_records).execute()
            if hasattr(response, 'error') and response.error:
                print(f"Error creating inventory records: {response.error.message}")
            else:
                print(f"Created {len(inventory_records)} inventory records")
    
    except Exception as e:
        print(f"Error populating inventory: {str(e)}")

def create_sample_orders():
    """Create sample pick orders for testing"""
    print("Creating sample orders...")
    
    try:
        # Get some inventory records to create orders from
        inventory_response = supabase.table('inventory').select('*, inventory_items(*), pick_locations(*)').limit(10).execute()
        if hasattr(inventory_response, 'error') and inventory_response.error:
            print(f"Error getting inventory: {inventory_response.error.message}")
            return
        
        inventory_records = inventory_response.data
        if not inventory_records:
            print("No inventory found to create orders")
            return
        
        # Create 2 sample orders
        for order_num in range(1, 3):
            order_data = {
                'order_number': f'ORD-00{order_num}',
                'customer_name': f'Customer {order_num}',
                'order_date': datetime.utcnow().isoformat(),
                'status': 'pending',
                'priority': 'normal' if order_num == 1 else 'high',
                'due_date': datetime.utcnow().isoformat(),
                'total_items': 0
            }
            
            # Create order
            order_response = supabase.table('orders').insert(order_data).execute()
            if hasattr(order_response, 'error') and order_response.error:
                print(f"Error creating order: {order_response.error.message}")
                continue
            
            order = order_response.data[0]
            
            # Create order lines from random inventory
            lines_to_create = random.randint(2, 4)
            selected_inventory = random.sample(inventory_records, min(lines_to_create, len(inventory_records)))
            
            total_items = 0
            for inv_record in selected_inventory:
                qty_to_pick = random.randint(1, min(5, inv_record['quantity']))
                total_items += qty_to_pick
                
                line_data = {
                    'order_id': order['id'],
                    'item_id': inv_record['item_id'],
                    'location_id': inv_record['location_id'],
                    'quantity_ordered': qty_to_pick,
                    'quantity_picked': 0,
                    'status': 'pending'
                }
                
                line_response = supabase.table('order_lines').insert(line_data).execute()
                if hasattr(line_response, 'error') and line_response.error:
                    print(f"Error creating order line: {line_response.error.message}")
            
            # Update order with total items
            supabase.table('orders').update({'total_items': total_items}).eq('id', order['id']).execute()
            print(f"Created order {order['order_number']} with {total_items} items")
    
    except Exception as e:
        print(f"Error creating sample orders: {str(e)}")

def main():
    """Main seeding function"""
    print("Starting database seeding...")
    print("=" * 50)
    
    try:
        # Skip users creation for now (users table doesn't exist)
        print("Skipping user creation (users table not found)")
        users = []  # Empty list for summary
        print()
        
        # Create sample warehouse from existing template
        warehouse_id = create_sample_warehouse_from_template("Demo Distribution Center")
        if not warehouse_id:
            print("Failed to create warehouse. Exiting.")
            return
        print()
        
        # Generate pick locations for warehouse
        locations_count = generate_pick_locations_for_warehouse(warehouse_id)
        print()
        
        # Create sample inventory items
        items = create_sample_inventory_items()
        print()
        
        # Populate inventory at locations
        if items and locations_count > 0:
            populate_inventory_at_locations(warehouse_id, items)
            print()
        
        # Create sample orders
        create_sample_orders()
        print()
        
        print("=" * 50)
        print("Database seeding completed successfully!")
        print(f"Created:")
        print(f"  - {len(users)} users (skipped)")
        print(f"  - 1 warehouse configuration") 
        print(f"  - {locations_count} pick locations")
        print(f"  - {len(items)} inventory items")
        print(f"  - Sample inventory placements")
        print(f"  - Sample pick orders")
        
    except Exception as e:
        print(f"Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
