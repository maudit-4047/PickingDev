"""
Test script for the new warehouse location system
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

from modules.location_utils import (
    validate_location_code,
    generate_location_code,
    get_voice_friendly_location,
    get_equipment_required,
    is_complex_aisle,
    estimate_total_locations,
    get_all_locations_for_aisle,
    get_picker_locations_for_aisle
)

def test_location_validation():
    """Test location code validation"""
    print("🧪 Testing Location Code Validation...")
    
    test_cases = [
        # Simple locations
        ("LA-045", True, "Simple picker location"),
        ("LA-045.B", True, "Simple forklift location"),
        ("HA-001", True, "Heavy section picker"),
        ("MF-099.F", True, "Medium section top level"),
        
        # Complex locations  
        ("AE-055.0.1", True, "Complex picker subsection 1"),
        ("AE-055.0.3", True, "Complex picker subsection 3"),
        ("AE-055.0.7", True, "Complex picker subsection 7"),
        ("AZ-001.B", True, "Complex forklift level B"),
        
        # Invalid locations
        ("LA", False, "Missing bay"),
        ("LA-045.0.2", False, "Invalid subsection"),
        ("XY-045", False, "Invalid section"),
        ("LA-045.G", False, "Invalid level"),
    ]
    
    passed = 0
    for location_code, should_pass, description in test_cases:
        try:
            result = validate_location_code(location_code)
            if should_pass:
                print(f"  ✓ {location_code}: {description}")
                print(f"    Parsed: {result}")
                passed += 1
            else:
                print(f"  ✗ {location_code}: Should have failed but passed")
        except Exception as e:
            if not should_pass:
                print(f"  ✓ {location_code}: Correctly failed - {description}")
                passed += 1
            else:
                print(f"  ✗ {location_code}: Should have passed but failed - {str(e)}")
    
    print(f"Validation tests: {passed}/{len(test_cases)} passed\n")

def test_voice_friendly_format():
    """Test voice-friendly location formatting"""
    print("🎤 Testing Voice-Friendly Formatting...")
    
    test_locations = [
        "LA-045",
        "LA-045.B", 
        "AE-055.0.1",
        "AE-055.0.3",
        "HA-001",
        "MF-099.F"
    ]
    
    for location in test_locations:
        try:
            voice_format = get_voice_friendly_location(location)
            equipment = get_equipment_required(location)
            print(f"  {location} → '{voice_format}' ({equipment})")
        except Exception as e:
            print(f"  ✗ {location}: Error - {str(e)}")
    
    print()

def test_location_generation():
    """Test location code generation"""
    print("🏗️ Testing Location Generation...")
    
    test_cases = [
        # (section, aisle, bay, level, subsection, expected)
        ("L", "A", "045", "0", None, "LA-045"),
        ("L", "A", "045", "B", None, "LA-045.B"),
        ("A", "E", "055", "0", "1", "AE-055.0.1"),
        ("A", "E", "055", "0", "3", "AE-055.0.3"),
        ("H", "A", "001", "0", None, "HA-001"),
    ]
    
    passed = 0
    for section, aisle, bay, level, subsection, expected in test_cases:
        try:
            result = generate_location_code(section, aisle, bay, level, subsection)
            if result == expected:
                print(f"  ✓ {section}{aisle}-{bay} (L{level}, S{subsection}) → {result}")
                passed += 1
            else:
                print(f"  ✗ Expected {expected}, got {result}")
        except Exception as e:
            print(f"  ✗ Error generating location: {str(e)}")
    
    print(f"Generation tests: {passed}/{len(test_cases)} passed\n")

def test_complex_aisle_detection():
    """Test complex aisle detection"""
    print("🔍 Testing Complex Aisle Detection...")
    
    test_cases = [
        # (section, aisle, should_be_complex)
        ("A", "E", True),    # AE is complex
        ("A", "Z", True),    # AZ is complex
        ("A", "M", True),    # AM is complex
        ("L", "A", False),   # LA is simple
        ("H", "A", False),   # HA is simple
        ("B", "A", False),   # BA is simple
    ]
    
    passed = 0
    for section, aisle, should_be_complex in test_cases:
        result = is_complex_aisle(section, aisle)
        if result == should_be_complex:
            status = "complex" if result else "simple"
            print(f"  ✓ {section}{aisle}: {status}")
            passed += 1
        else:
            expected_status = "complex" if should_be_complex else "simple"
            actual_status = "complex" if result else "simple"
            print(f"  ✗ {section}{aisle}: Expected {expected_status}, got {actual_status}")
    
    print(f"Complex aisle tests: {passed}/{len(test_cases)} passed\n")

def test_aisle_location_generation():
    """Test generating all locations for specific aisles"""
    print("📋 Testing Aisle Location Generation...")
    
    # Test simple aisle
    print("  Testing simple aisle LA:")
    la_locations = get_all_locations_for_aisle("L", "A")
    la_picker_locations = get_picker_locations_for_aisle("L", "A")
    print(f"    Total locations: {len(la_locations)}")
    print(f"    Picker locations: {len(la_picker_locations)}")
    print(f"    Sample locations: {la_locations[:5]}")
    
    # Test complex aisle
    print("  Testing complex aisle AE:")
    ae_locations = get_all_locations_for_aisle("A", "E")
    ae_picker_locations = get_picker_locations_for_aisle("A", "E")
    print(f"    Total locations: {len(ae_locations)}")
    print(f"    Picker locations: {len(ae_picker_locations)}")
    print(f"    Sample picker locations: {ae_picker_locations[:5]}")
    print(f"    Sample forklift locations: {[loc for loc in ae_locations if '.B' in loc or '.C' in loc][:3]}")
    
    print()

def test_warehouse_statistics():
    """Test warehouse statistics calculation"""
    print("📊 Testing Warehouse Statistics...")
    
    from modules.location_utils import validate_warehouse_structure
    
    try:
        stats = validate_warehouse_structure()
        print(f"  Total sections: {stats['total_sections']}")
        print(f"  Total aisles: {stats['total_aisles']}")
        print(f"  Complex aisles: {stats['complex_aisles']}")
        print(f"  Estimated locations: {stats['estimated_locations']:,}")
        print("  ✓ Statistics calculation successful")
    except Exception as e:
        print(f"  ✗ Statistics calculation failed: {str(e)}")
    
    print()

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Warehouse Location System Tests\n")
    
    test_location_validation()
    test_voice_friendly_format()
    test_location_generation()
    test_complex_aisle_detection()
    test_aisle_location_generation()
    test_warehouse_statistics()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests()