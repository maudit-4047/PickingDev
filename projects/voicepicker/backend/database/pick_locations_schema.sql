-- PostgreSQL Schema for Pick Locations Management
-- Manages warehouse locations, zones, and picking areas

CREATE TABLE location_zones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    zone_code VARCHAR(10) UNIQUE NOT NULL,           -- H, L, M, B, A (warehouse sections)
    zone_name VARCHAR(50) NOT NULL,                  -- "Heavy Items", "Light Items", "Medium Items", etc.
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pick_locations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_code VARCHAR(30) UNIQUE NOT NULL,       -- LA-045, AE-055.0.1, AE-055.B, etc.
    zone_id BIGINT REFERENCES location_zones(id),
    section VARCHAR(5) NOT NULL,                     -- H, L, M, B, A (warehouse section)
    aisle VARCHAR(5) NOT NULL,                       -- A, B, C, ..., Z, AA, AB, etc.
    bay VARCHAR(10) NOT NULL,                        -- 001-099
    level VARCHAR(5),                                -- 0 (default/picker), B, C, D, E, F (levels 1-5)
    subsection VARCHAR(5),                           -- 1, 3, 7 (for level 0 in complex aisles)
    check_digit INT NOT NULL,                        -- 1-37 unique per location
    location_type VARCHAR(20) DEFAULT 'pick',        -- pick, reserve, dock, stage
    is_complex_aisle BOOLEAN DEFAULT FALSE,          -- TRUE for AM-AE aisles with subdivisions
    capacity INT DEFAULT 100,                        -- max items that can fit
    current_occupancy INT DEFAULT 0,                 -- current items in location
    is_active BOOLEAN DEFAULT TRUE,
    is_pickable BOOLEAN DEFAULT TRUE,                -- can items be picked from here
    access_equipment VARCHAR(30),                    -- 'manual' (level 0), 'forklift' (B-F)
    safety_notes TEXT,                               -- height restrictions, weight limits, etc.
    last_picked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Location assignments - what items are in which locations
CREATE TABLE location_inventory (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id BIGINT REFERENCES pick_locations(id),
    item_code VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 0,
    last_replenished_at TIMESTAMP,
    last_picked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(location_id, item_code)
);

-- Pick location activity log
CREATE TABLE location_activity (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id BIGINT REFERENCES pick_locations(id),
    worker_id BIGINT REFERENCES workers(id),
    activity_type VARCHAR(30) NOT NULL,              -- 'pick', 'replenish', 'count', 'move'
    item_code VARCHAR(100),
    quantity_before INT,
    quantity_after INT,
    work_queue_id BIGINT,                            -- link to work queue task
    notes TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Location maintenance and issues
CREATE TABLE location_issues (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id BIGINT REFERENCES pick_locations(id),
    reported_by BIGINT REFERENCES workers(id),
    issue_type VARCHAR(30) NOT NULL,                 -- 'damage', 'blocked', 'unsafe', 'mislabeled'
    severity VARCHAR(20) DEFAULT 'medium',           -- 'low', 'medium', 'high', 'critical'
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open',               -- 'open', 'in_progress', 'resolved', 'closed'
    resolved_by BIGINT REFERENCES workers(id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Default zones (warehouse sections)
INSERT INTO location_zones (zone_code, zone_name, description) VALUES
    ('H', 'Heavy Items Section', 'HA aisle - Heavy items storage'),
    ('L', 'Light Items Section', 'LA-LZ aisles - Light items storage (26 aisles)'),
    ('M', 'Medium Items Section', 'MA-MF aisles - Medium items storage (6 aisles)'),
    ('B', 'B Section', 'BA-BE aisles - B section storage (5 aisles)'),
    ('A', 'A Section', 'AA-AZ aisles - A section storage (26 aisles)')
ON CONFLICT (zone_code) DO NOTHING;

-- Note: Pick locations will be created dynamically through the warehouse designer
-- Users can design their own warehouse layout using the API endpoints

-- Indexes for performance
CREATE INDEX idx_pick_locations_zone ON pick_locations(zone_id);
CREATE INDEX idx_pick_locations_section ON pick_locations(section);
CREATE INDEX idx_pick_locations_aisle ON pick_locations(aisle);
CREATE INDEX idx_pick_locations_level ON pick_locations(level);
CREATE INDEX idx_pick_locations_active ON pick_locations(is_active, is_pickable);
CREATE INDEX idx_pick_locations_complex ON pick_locations(is_complex_aisle);
CREATE INDEX idx_pick_locations_check_digit ON pick_locations(check_digit);
CREATE INDEX idx_location_inventory_item ON location_inventory(item_code);
CREATE INDEX idx_location_activity_location ON location_activity(location_id);
CREATE INDEX idx_location_activity_worker ON location_activity(worker_id);
CREATE INDEX idx_location_issues_status ON location_issues(status);