-- PostgreSQL Schema for Work Queue System
-- Manages picking tasks and work assignments

CREATE TABLE work_queue (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id) ON DELETE CASCADE,
    worker_id BIGINT REFERENCES workers(id) ON DELETE SET NULL,
    item_code VARCHAR(100) NOT NULL,
    location_code VARCHAR(50) NOT NULL,          -- BIN-123, PICK-A1, etc.
    quantity_requested INT NOT NULL,
    quantity_picked INT DEFAULT 0,
    priority INT DEFAULT 5,                      -- 1=highest, 10=lowest
    status VARCHAR(20) DEFAULT 'pending',        -- pending, assigned, picking, completed, cancelled
    task_type VARCHAR(30) DEFAULT 'pick',        -- pick, replenish, count, move
    assigned_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    estimated_time INT DEFAULT 0,               -- estimated time in seconds
    actual_time INT DEFAULT 0,                  -- actual time taken in seconds
    notes TEXT,                                 -- special instructions or issues
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Work queue assignments - tracks which worker is working on what
CREATE TABLE work_assignments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    worker_id BIGINT REFERENCES workers(id) ON DELETE CASCADE,
    work_queue_id BIGINT REFERENCES work_queue(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',        -- active, paused, completed
    UNIQUE(worker_id, work_queue_id)
);

-- Work queue history - audit trail of task changes
CREATE TABLE work_queue_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    work_queue_id BIGINT REFERENCES work_queue(id) ON DELETE CASCADE,
    worker_id BIGINT REFERENCES workers(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,                -- assigned, started, completed, cancelled, picked_partial
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    quantity_before INT,
    quantity_after INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_work_queue_status ON work_queue(status);
CREATE INDEX idx_work_queue_worker ON work_queue(worker_id);
CREATE INDEX idx_work_queue_priority ON work_queue(priority, created_at);
CREATE INDEX idx_work_assignments_worker ON work_assignments(worker_id);
CREATE INDEX idx_work_queue_location ON work_queue(location_code);