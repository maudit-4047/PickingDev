CREATE TABLE tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    worker_id BIGINT REFERENCES workers(id),
    task_type VARCHAR(20) DEFAULT 'pick',
    order_id BIGINT,                           -- FK to orders
    item_id BIGINT,                            -- FK to inventory
    location_id BIGINT,                        -- FK to locations
    status VARCHAR(20) DEFAULT 'pending',      -- pending, in_progress, completed
    assigned_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    confirmation_method VARCHAR(20),           -- voice, scan, manual
    exception_reason TEXT
);
