-- system_config.sql
-- Stores global or per-site configuration for the voice picker backend

CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(64) UNIQUE NOT NULL,
    value VARCHAR(255) NOT NULL,
    description TEXT
);

-- Example initial values:
INSERT INTO system_config (key, value, description) VALUES
    ('team_size_cap', '50', 'Maximum number of workers per team'),
    ('pin_min', '1000', 'Minimum worker pin'),
    ('pin_max', '9999', 'Maximum worker pin')
ON CONFLICT (key) DO NOTHING;
