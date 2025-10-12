-- Warehouse Configuration Schema
-- Allows users to define custom warehouse layouts dynamically

-- Main warehouse configuration
CREATE TABLE warehouse_config (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_name VARCHAR(100) NOT NULL,
    description TEXT,
    layout_type VARCHAR(20) DEFAULT 'custom',        -- 'simple', 'complex', 'mixed', 'custom'
    location_naming_pattern VARCHAR(50) DEFAULT '{section}{aisle}-{bay:03d}',
    check_digit_min INT DEFAULT 1,
    check_digit_max INT DEFAULT 37,
    default_bay_range_start INT DEFAULT 1,
    default_bay_range_end INT DEFAULT 99,
    default_capacity INT DEFAULT 100,
    voice_optimized BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Warehouse sections (replaces hardcoded H,L,M,B,A)
CREATE TABLE warehouse_sections (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_id BIGINT REFERENCES warehouse_config(id) ON DELETE CASCADE,
    section_code VARCHAR(10) NOT NULL,               -- H, L, M, B, A, or any custom codes
    section_name VARCHAR(50) NOT NULL,               -- "Heavy Items", "Light Items", etc.
    description TEXT,
    color_code VARCHAR(7),                           -- Hex color for UI visualization
    sort_order INT DEFAULT 0,                        -- Display order
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(warehouse_id, section_code)
);

-- Aisle patterns for each section
CREATE TABLE warehouse_aisles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    section_id BIGINT REFERENCES warehouse_sections(id) ON DELETE CASCADE,
    aisle_code VARCHAR(10) NOT NULL,                 -- A, B, C, etc.
    aisle_name VARCHAR(50),                          -- "Main Aisle A", etc.
    is_complex BOOLEAN DEFAULT FALSE,                -- Has subdivisions at level 0
    bay_range_start INT DEFAULT 1,
    bay_range_end INT DEFAULT 99,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(section_id, aisle_code)
);

-- Level definitions for aisles
CREATE TABLE warehouse_levels (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aisle_id BIGINT REFERENCES warehouse_aisles(id) ON DELETE CASCADE,
    level_code VARCHAR(5) NOT NULL,                  -- 0, B, C, D, E, F or 1, 2, 3, etc.
    level_name VARCHAR(50),                          -- "Ground Level", "Level 1", etc.
    level_type VARCHAR(20) DEFAULT 'standard',       -- 'picker', 'forklift', 'standard'
    equipment_required VARCHAR(30) DEFAULT 'manual', -- 'manual', 'forklift', 'reach_truck'
    height_meters DECIMAL(4,2),                      -- Physical height for safety
    weight_limit_kg INT,                             -- Weight restrictions
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(aisle_id, level_code)
);

-- Subsection patterns for complex aisles
CREATE TABLE warehouse_subsections (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    level_id BIGINT REFERENCES warehouse_levels(id) ON DELETE CASCADE,
    subsection_code VARCHAR(5) NOT NULL,             -- 1, 3, 7 or A, B, C, etc.
    subsection_name VARCHAR(50),                     -- "Left", "Center", "Right", etc.
    position_description TEXT,                       -- "Left side of bay", etc.
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(level_id, subsection_code)
);

-- Predefined warehouse templates
CREATE TABLE warehouse_templates (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    template_data JSONB NOT NULL,                    -- Store complete warehouse structure
    preview_image_url VARCHAR(255),
    category VARCHAR(50) DEFAULT 'general',          -- 'general', 'ecommerce', 'manufacturing', etc.
    difficulty_level VARCHAR(20) DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced'
    estimated_locations INT,
    is_public BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User's warehouse selections (links users to their warehouse configs)
CREATE TABLE user_warehouses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,                    -- User identifier
    warehouse_id BIGINT REFERENCES warehouse_config(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT FALSE,                -- Default warehouse for user
    role VARCHAR(20) DEFAULT 'owner',                -- 'owner', 'admin', 'viewer'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, warehouse_id)
);

-- Location generation rules (advanced customization)
CREATE TABLE location_generation_rules (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_id BIGINT REFERENCES warehouse_config(id) ON DELETE CASCADE,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(30) NOT NULL,                  -- 'naming', 'capacity', 'equipment', 'validation'
    conditions JSONB,                                -- When to apply this rule
    actions JSONB,                                   -- What to do when conditions match
    priority INT DEFAULT 0,                         -- Rule priority (higher = first)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert your current warehouse as the first template
INSERT INTO warehouse_templates (
    template_name, 
    description, 
    template_data, 
    category,
    estimated_locations,
    created_by
) VALUES (
    'Multi-Zone Voice Picking Layout',
    'Advanced warehouse layout with heavy, light, medium, and specialized sections. Optimized for voice picking with complex aisle subdivisions.',
    '{
        "warehouse_name": "Multi-Zone Voice Picking Warehouse",
        "location_naming_pattern": "{section}{aisle}-{bay:03d}",
        "sections": [
            {
                "code": "H",
                "name": "Heavy Items Section", 
                "description": "HA aisle - Heavy items storage",
                "color": "#FF6B6B",
                "aisles": [{"code": "A", "complex": false, "bays": "001-099"}]
            },
            {
                "code": "L",
                "name": "Light Items Section",
                "description": "LA-LZ aisles - Light items storage (26 aisles)", 
                "color": "#4ECDC4",
                "aisles": [{"code": "A-Z", "complex": false, "bays": "001-099"}]
            },
            {
                "code": "M", 
                "name": "Medium Items Section",
                "description": "MA-MF aisles - Medium items storage (6 aisles)",
                "color": "#45B7D1", 
                "aisles": [{"code": "A-F", "complex": false, "bays": "001-099"}]
            },
            {
                "code": "B",
                "name": "B Section", 
                "description": "BA-BE aisles - B section storage (5 aisles)",
                "color": "#96CEB4",
                "aisles": [{"code": "A-E", "complex": false, "bays": "001-099"}]
            },
            {
                "code": "A",
                "name": "A Section",
                "description": "AA-AZ aisles - A section storage with complex subdivisions",
                "color": "#FFEAA7", 
                "aisles": [
                    {"code": "A-L", "complex": false, "bays": "001-099"},
                    {"code": "M-Z", "complex": true, "bays": "001-099", "subsections": ["1", "3", "7"]}
                ]
            }
        ],
        "levels": ["0", "B", "C", "D", "E", "F"],
        "level_names": ["Picker Level", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
        "equipment": {
            "0": "manual",
            "B-F": "forklift"
        }
    }',
    'ecommerce',
    38000,
    'system'
);

-- Insert basic templates
INSERT INTO warehouse_templates (template_name, description, template_data, category, estimated_locations) VALUES
(
    'Simple Grid Layout',
    'Basic warehouse with single section and simple aisle structure. Perfect for small to medium warehouses.',
    '{
        "warehouse_name": "Simple Grid Warehouse",
        "sections": [
            {
                "code": "A", 
                "name": "Main Storage",
                "aisles": [{"code": "A-Z", "complex": false}]
            }
        ],
        "levels": ["1", "2", "3", "4"]
    }',
    'general',
    6336
),
(
    'Zone-Based Layout', 
    'Warehouse organized by product zones with different storage requirements.',
    '{
        "warehouse_name": "Zone-Based Warehouse",
        "sections": [
            {"code": "R", "name": "Receiving", "aisles": [{"code": "A-C"}]},
            {"code": "P", "name": "Picking", "aisles": [{"code": "A-Z"}]}, 
            {"code": "S", "name": "Shipping", "aisles": [{"code": "A-E"}]}
        ],
        "levels": ["1", "2", "3"]
    }',
    'general',
    10000
);

-- Indexes for performance
CREATE INDEX idx_warehouse_sections_warehouse ON warehouse_sections(warehouse_id);
CREATE INDEX idx_warehouse_aisles_section ON warehouse_aisles(section_id);
CREATE INDEX idx_warehouse_levels_aisle ON warehouse_levels(aisle_id);
CREATE INDEX idx_warehouse_subsections_level ON warehouse_subsections(level_id);
CREATE INDEX idx_user_warehouses_user ON user_warehouses(user_id);
CREATE INDEX idx_warehouse_templates_category ON warehouse_templates(category);
CREATE INDEX idx_location_generation_rules_warehouse ON location_generation_rules(warehouse_id);

-- Update the existing location_zones table to link to warehouse_config
ALTER TABLE location_zones ADD COLUMN warehouse_id BIGINT REFERENCES warehouse_config(id);
CREATE INDEX idx_location_zones_warehouse ON location_zones(warehouse_id);

-- Update pick_locations to include warehouse reference
ALTER TABLE pick_locations ADD COLUMN warehouse_id BIGINT REFERENCES warehouse_config(id);
CREATE INDEX idx_pick_locations_warehouse ON pick_locations(warehouse_id);