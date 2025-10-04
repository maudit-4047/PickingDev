CREATE TABLE shifts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    worker_id BIGINT REFERENCES workers(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    shift_type VARCHAR(20),                   -- 4hr, 6hr, 8hr, OT
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE breaks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_id BIGINT REFERENCES shifts(id) ON DELETE CASCADE,
    break_start TIMESTAMP NOT NULL,
    break_end TIMESTAMP,
    break_type VARCHAR(20) DEFAULT 'regular', -- lunch, tea, extra
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE delays (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    worker_id BIGINT REFERENCES workers(id),
    shift_id BIGINT REFERENCES shifts(id),
    delay_type VARCHAR(50),                   -- supervisor, incident, battery
    delay_start TIMESTAMP NOT NULL,
    delay_end TIMESTAMP,
    approved_by BIGINT REFERENCES workers(id),
    approval_status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
