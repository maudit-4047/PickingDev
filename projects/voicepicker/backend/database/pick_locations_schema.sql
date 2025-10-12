-- PostgreSQL Schema for Pick Locations Management
-- Manages warehouse locations, zones, and picking areas

CREATE TABLE location_zones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    zone_code VARCHAR(10) UNIQUE NOT NULL,           -- L (for locations), R (reserve), etc.
    zone_name VARCHAR(50) NOT NULL,                  -- "Pick Locations", "Reserve", "Dock"
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pick_locations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_code VARCHAR(20) UNIQUE NOT NULL,       -- LA01, LB05, LC12, LD03, etc.
    zone_id BIGINT REFERENCES location_zones(id),
    aisle VARCHAR(10),                               -- A, B, C, D, etc.
    bay VARCHAR(10),                                 -- 01, 02, 03, etc.
    level VARCHAR(10),                               -- 1, 2, 3, 4 (shelf levels)
    position VARCHAR(10),                            -- A, B (left/right positions)
    location_type VARCHAR(20) DEFAULT 'pick',        -- pick, reserve, dock, stage
    capacity INT DEFAULT 100,                        -- max items that can fit
    current_occupancy INT DEFAULT 0,                 -- current items in location
    is_active BOOLEAN DEFAULT TRUE,
    is_pickable BOOLEAN DEFAULT TRUE,                -- can items be picked from here
    access_equipment VARCHAR(30),                    -- 'reach_truck', 'forklift', 'manual', 'order_picker'
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

-- Default zones (can be customized by users)
INSERT INTO location_zones (zone_code, zone_name, description) VALUES
    ('PICK', 'Pick Locations', 'Main picking areas for order fulfillment'),
    ('RESERVE', 'Reserve Storage', 'Bulk storage for replenishment'),
    ('DOCK', 'Dock Areas', 'Loading and receiving docks'),
    ('STAGE', 'Staging Areas', 'Order staging and consolidation'),
    ('QC', 'Quality Control', 'QC and inspection areas')
ON CONFLICT (zone_code) DO NOTHING;

-- Note: Pick locations will be created dynamically through the warehouse designer
-- Users can design their own warehouse layout using the API endpoints

-- Indexes for performance
CREATE INDEX idx_pick_locations_zone ON pick_locations(zone_id);
CREATE INDEX idx_pick_locations_aisle ON pick_locations(aisle);
CREATE INDEX idx_pick_locations_active ON pick_locations(is_active, is_pickable);
CREATE INDEX idx_location_inventory_item ON location_inventory(item_code);
CREATE INDEX idx_location_activity_location ON location_activity(location_id);
CREATE INDEX idx_location_activity_worker ON location_activity(worker_id);
CREATE INDEX idx_location_issues_status ON location_issues(status);