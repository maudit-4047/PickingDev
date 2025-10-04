CREATE TABLE picker_performance (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    worker_id BIGINT REFERENCES workers(id),
    shift_id BIGINT REFERENCES shifts(id),
    total_picks INT DEFAULT 0,
    avg_pick_time NUMERIC(10,2),
    error_count INT DEFAULT 0,
    insufficient_stock_count INT DEFAULT 0,
    total_break_time INTERVAL,
    total_delay_time INTERVAL,
    last_pick_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
